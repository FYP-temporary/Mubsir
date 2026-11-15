"""Verifies docs/FEATURE_GENERATION_CONTRACT.md against the stored training features (needs pipeline/data/).  Run from pipeline/:  python verify_feature_contract.py
`rotation_features()` below is a literal, loop-based transcription of the contract for the 27 columns that are NOT in the team's ml_final table
(21 nr_* + 3 nr_gap_alt_2 + 3 *_to_p90_ratio). It must reproduce, on real users and on docs/golden_feature_cases.json, the values the model was trained on.
Exit code 0 only if every cell matches. Use it as the reference when writing the production extractor."""
import json, sys, numpy as np, pandas as pd
from common import *

CHANNELS = ["external_email_count", "usb_copy_count", "www_upload_count"]            # order matters: email < usb < http (tie-break + argmax)
BASELINE = [("email_count_p50", "email_count_p90", "email_count_p95"), ("usb_copy_p50", "usb_copy_p90", "usb_copy_p95"), ("http_upload_p50", "http_upload_p90", "http_upload_p95")]
GAP = 2


def deviation(X, p50, p95):
    """E[d,c] = max(0, x - P50) / max(1, P95 - P50); a missing value (or missing baseline) counts as no deviation."""
    with np.errstate(invalid="ignore"):
        return np.nan_to_num(np.clip(X - p50, 0, None) / np.maximum(1, p95 - p50))


def rotation_features(X, p50, p90, p95, t, w):
    """X: (n,3) daily counts of ALL the user's workdays in date order (weekday & logon_count>0), p*: per-user baseline (3,), t: index of the scored day, w: window in workdays.
    Needs days t-w .. t (w+1 days; the extra day is the one before the window, used by nr_handoff). Returns dict of the 9 values for this window."""
    E = deviation(X, p50, p95); win = range(t - w + 1, t + 1)
    dev = lambda d: E[d].sum() > 0
    dom = lambda d: int(E[d].argmax()) if dev(d) else -1                                 # argmax ties -> lowest index
    S = E[t - w + 1:t + 1].sum(0); St = S.sum()
    out = {"nr_m": float((S > 0).sum())}
    if St > 0:
        p = S[S > 0] / St; out["nr_entropy"] = float(-(p * np.log(p)).sum() / np.log(3))
    else: out["nr_entropy"] = 0.0
    n_dev = [(E[d] > 0).sum() for d in win]
    out["nr_excl_days"] = float(sum(k == 1 for k in n_dev)); out["nr_overlap_days"] = float(sum(k >= 2 for k in n_dev))
    out["nr_handoff"] = float(sum(((E[d] > 0) & ~(E[d - 1] > 0)).sum() for d in win if d >= 1 and (E[d - 1] > 0).any()))
    pairs = [(d - 1, d) for d in win if d - 1 >= t - w + 1 and dev(d) and dev(d - 1)]
    out["nr_alt"] = float(sum(dom(a) != dom(b) for a, b in pairs) / len(pairs)) if pairs else 0.0
    out["nr_stealth_acc"] = float(sum(E[d, c] for d in win for c in range(3) if E[d, c] > 0 and np.nan_to_num(X[d, c]) <= p95[c]))
    days = [d for d in win if dev(d)]
    el = [(a, b) for a, b in zip(days[:-1], days[1:]) if b - a - 1 <= GAP]
    out["nr_gap_alt_2"] = float(sum(dom(a) != dom(b) for a, b in el) / len(el)) if el else 0.0
    return out


def p90_ratios(x_today, p90):
    return {n: (x / p if p > 0 else np.nan) for n, x, p in zip(("email_count_to_p90_ratio", "usb_copy_to_p90_ratio", "http_upload_to_p90_ratio"), x_today, p90)}


def expected_columns(feats, w):
    return {f"{k}_{w}wd" if k != "nr_gap_alt_2" else f"nr_gap_alt_2_{w}wd": v for k, v in feats.items()}


def build_series():
    df = pd.read_parquet(PREPARED).sort_values(["user", "day"]).reset_index(drop=True)
    users = df.user.unique()
    ud = pd.read_parquet(ROOT / "data/final/user_day_injected_r62.parquet", columns=["user", "day", "is_weekend", "logon_count"] + CHANNELS)
    ud["day"] = pd.to_datetime(ud.day); ud = ud[ud.user.isin(users) & (ud.is_weekend == 0) & (ud.logon_count > 0)].sort_values(["user", "day"])
    return df, ud


def stored_features(df):
    ev = pd.read_parquet(WORK / "evidence_features.parquet"); fc = pd.read_parquet(WORK / "final_changed_features.parquet"); ga = pd.read_parquet(WORK / "gap_alt_features.parquet")
    for t in (ev, fc, ga): assert (t.user.values == df.user.values).all() and (t.day.values == df.day.values).all()
    S = pd.concat([fc.drop(columns=["user", "day"]), ev.drop(columns=["user", "day"] + [c for c in fc.columns if c in ev.columns]), ga.drop(columns=["user", "day"])], axis=1)
    return S                                                                                # nr_alt / nr_stealth_acc / p90 ratios come from step 21 (as in 28_final75.py)


def main():
    df, ud = build_series(); S = stored_features(df); ok = True; checked = bad = 0
    uidx = df.groupby("user").indices; series = {u: g for u, g in ud.groupby("user")}
    cols_27 = [f"{n}_{w}wd" for n in ("nr_m", "nr_entropy", "nr_excl_days", "nr_overlap_days", "nr_alt", "nr_handoff", "nr_stealth_acc") for w in (5, 10, 20)] \
        + [f"nr_gap_alt_2_{w}wd" for w in (5, 10, 20)] + ["email_count_to_p90_ratio", "usb_copy_to_p90_ratio", "http_upload_to_p90_ratio"]
    assert len(cols_27) == 27 and all(c in S.columns for c in cols_27)
    worst = {}
    for u in np.random.default_rng(7).choice(df.user.unique(), 60, replace=False):
        g = series[u].reset_index(drop=True); ix = uidx[u]; d11 = df.iloc[ix]; n10 = int((g.day < "2011-01-01").sum())
        assert len(g) == n10 + len(ix) and (g.day[n10:].values == d11.day.values).all(), u                    # series = 2010 workdays + the 2011 rows of ml_final
        X = g[CHANNELS].to_numpy(float); b = d11.iloc[0]
        p50, p90, p95 = (np.array([b[BASELINE[c][i]] for c in range(3)], float) for i in range(3))
        for j in range(len(ix)):
            t = n10 + j; row = S.iloc[ix[j]]; exp = dict(p90_ratios(X[t], p90))
            for w in (5, 10, 20): exp.update(expected_columns(rotation_features(X, p50, p90, p95, t, w), w))
            for c in cols_27:
                a, s = exp[c], row[c]; checked += 1
                same = (np.isnan(a) and np.isnan(s)) or np.isclose(a, s, atol=1e-9)
                if not same: bad += 1; worst.setdefault(c, (u, j, a, s))
    print(f"[{'PASS' if bad == 0 else 'FAIL'}] contract implementation == stored training features on 60 users: {checked} cells, mismatches = {bad}" + (f" | first mismatches: {worst}" if bad else ""))
    ok &= bad == 0
    gold = json.load(open(PKG.parent / "docs" / "golden_feature_cases.json")); gbad = 0
    for case in gold["cases"]:
        X = np.array(case["daily_counts"], float); p50, p90, p95 = (np.array(case["baseline"][k], float) for k in ("p50", "p90", "p95")); t = len(X) - 1
        exp = dict(p90_ratios(X[t], p90))
        for w in (5, 10, 20): exp.update(expected_columns(rotation_features(X, p50, p90, p95, t, w), w))
        for c, v in case["expected"].items():
            a = exp[c]; gbad += not ((v is None and np.isnan(a)) or (v is not None and np.isclose(a, v, atol=1e-9)))
    print(f"[{'PASS' if gbad == 0 else 'FAIL'}] golden cases in docs/golden_feature_cases.json: {len(gold['cases'])} cases x 27 columns, mismatches = {gbad}"); ok &= gbad == 0
    print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED"); sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
