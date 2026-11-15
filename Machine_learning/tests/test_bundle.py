"""Contract tests for the MUBSIR inference bundle (model/). No training data needed: run `pytest -q` from the repository root.
Covers: manifest integrity, feature-leakage guard, level thresholds, input contract, SHAP additivity, and fixed expected outputs on model/example_input.parquet."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, pytest

MODEL = Path(__file__).resolve().parents[1] / "model"
sys.path.insert(0, str(MODEL))
from mubsir_infer import MubsirScorer  # noqa: E402

STATIC_BASELINE = (["baseline_workdays"] + [f"email_{k}" for k in ["active_days", "active_rate", "count_p50", "count_p90", "count_p95", "count_mad", "bytes_p50", "bytes_p90", "bytes_p95", "bytes_mad"]]
                   + [f"usb_{k}" for k in ["active_days", "active_rate", "copy_p50", "copy_p90", "copy_p95", "copy_mad"]] + [f"http_upload_{k}" for k in ["active_days", "active_rate", "p50", "p90", "p95", "mad"]])
FORBIDDEN = {"user", "day", "first_logon", "last_logoff", "is_weekend", "y", "group", "stealth", "scenario_id", "part", "is_attack_day", "is_scheduled", "day_status", "planned_channels", "stealth_level"}


@pytest.fixture(scope="module")
def sc():
    return MubsirScorer(MODEL)


@pytest.fixture(scope="module")
def X():
    return pd.read_parquet(MODEL / "example_input.parquet")


@pytest.fixture(scope="module")
def rows(sc, X):
    return sc.score(X)


# ------------------------------------------------------------------ manifest
def test_manifest_structure(sc):
    m = sc.man
    assert sorted(int(h) for h in m["windows"]) == [5, 10, 20]
    sets = {}
    for h, w in m["windows"].items():
        assert w["n_features"] == 75 == len(w["features"]) == len(set(w["features"]))
        assert (MODEL / w["model_file"]).exists()
        assert sc.booster[int(h)].num_feature() == 75
        assert sc.booster[int(h)].num_trees() == w["n_trees"], "n_trees in manifest differs from the saved booster"
        assert w["platt_coef"] > 0, "calibration must be monotonic increasing"
        assert f"nr_gap_alt_2_{h}wd" in w["features"]
        sets[h] = set(w["features"])
    common = sets["5"] & sets["10"] & sets["20"]
    assert len(common) == 74
    assert len(set(m["input_columns_all"])) == len(m["input_columns_all"]) == 77 == len(sets["5"] | sets["10"] | sets["20"])
    assert m["risk_bands"]["low_max"] == 60.0 and m["risk_bands"]["medium_max"] == 85.0 and m["risk_bands"]["alert_level"] == "High"


def test_no_label_or_static_baseline_columns_used_as_features(sc):
    used = set(sc.man["input_columns_all"])
    assert not (used & FORBIDDEN), used & FORBIDDEN
    assert not (used & set(STATIC_BASELINE)), "per-user static baseline columns must not be features"
    assert not any(c.startswith(("injected_", "yf_", "y_")) for c in used)


# ------------------------------------------------------------------ levels
def test_level_boundaries(sc):
    assert list(sc.level_of([0, 60, 60.0001, 85, 85.0001, 100])) == [0, 0, 1, 1, 2, 2]


def test_thresholds_map_back_to_risk_scale(sc):
    t = sc.thresholds()
    assert (t.low_max_risk == 60).all() and (t.medium_max_risk == 85).all()
    for h, lo_raw, hi_raw in zip(t.window, t.low_max_raw, t.medium_max_raw):
        assert abs(sc._risk(np.array([lo_raw]), int(h))[0] - 60) < 1e-6 and abs(sc._risk(np.array([hi_raw]), int(h))[0] - 85) < 1e-6


# ------------------------------------------------------------------ scoring contract
def test_score_shape_ranges_and_consistency(rows, X):
    assert len(rows) == len(X) == 316
    for h in (5, 10, 20):
        r = rows[f"risk_{h}"]; assert r.between(0, 100).all() and rows[f"score_raw_{h}"].between(0, 1).all()
        exp = np.where(r > 85, "High", np.where(r > 60, "Medium", "Low")); assert (rows[f"level_{h}"].values == exp).all()
    assert np.allclose(rows.risk, rows[["risk_5", "risk_10", "risk_20"]].max(axis=1))
    assert (rows.alert == (rows.risk > 85)).all()
    assert (rows.alert_windows.str.len() > 0).equals(rows.alert)


def test_expected_user_results_on_example(sc, rows):
    u = sc.score_users(rows)
    assert u.loc["NVH3726", "level"] == "High" and 99.8 < u.loc["NVH3726", "risk_peak"] <= 100 and str(u.loc["NVH3726", "first_alert_day"].date()) == "2011-01-31"
    assert u.loc["DBF3582", "level"] == "High" and str(u.loc["DBF3582", "first_alert_day"].date()) == "2011-05-23"
    assert u.loc["SHB3512", "level"] == "Low" and not u.loc["SHB3512", "alert"] and 53 < u.loc["SHB3512", "risk_peak"] < 54 and pd.isna(u.loc["SHB3512", "first_alert_day"])


def test_column_order_and_extra_columns_do_not_matter(sc, X, rows):
    cols = list(X.columns); rng = np.random.default_rng(0); rng.shuffle(cols)
    Y = X[cols].copy(); Y["unrelated_column"] = 1.0
    out = sc.score(Y)
    assert np.allclose(out[["risk_5", "risk_10", "risk_20"]].values, rows[["risk_5", "risk_10", "risk_20"]].values, atol=1e-12)


def test_missing_column_raises(sc, X):
    with pytest.raises(ValueError, match="missing"):
        sc.score(X.drop(columns=["cumulative_deviation_10wd"]))


def test_nan_is_accepted(sc, X):
    Y = X.copy(); Y.loc[Y.index[:5], "email_event_count"] = np.nan
    assert np.isfinite(sc.score(Y)[["risk_5", "risk_10", "risk_20"]].values).all()


# ------------------------------------------------------------------ SHAP
def test_shap_additivity_and_risk_match(sc, X, rows):
    idx = [0, 50, 146, 250]
    e = sc.explain(X.iloc[idx], window=10, top_k=75)
    assert e.groupby("row").size().eq(75).all()
    for i, g in e.groupby("row"):
        assert abs(g.shap.sum() + g.base_logodds.iloc[0] - g.logodds.iloc[0]) < 1e-9
        assert abs(g.risk.iloc[0] - rows.risk_10.iloc[idx[i]]) < 1e-6


def test_explain_empty_input(sc, X):
    assert len(sc.explain(X.iloc[0:0], window=10)) == 0
