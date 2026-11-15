"""MUBSIR inference: features -> risk score + classification (+ SHAP explanation). Needs only numpy, pandas, lightgbm. No training code, no pickles.

    from mubsir_infer import MubsirScorer
    sc = MubsirScorer()                                   # loads ./manifest.json + lgbm_w{5,10,20}.txt next to this file
    rows = sc.score(features_df)                          # one row per user-workday -> risk per window, level (Low/Medium/High), alert (= High)
    users = sc.score_users(rows)                          # per-user peak risk over the monitored period -> level
    why = sc.explain(features_df.iloc[[i]], top_k=5)      # top SHAP contributions for that prediction (per window)

Input: a DataFrame with the project's feature columns (see manifest["input_columns_all"], 77 columns; any order, extra columns ignored, NaN allowed).
Optional identifier columns `user` and `day` are carried through. Features must be produced by the project's causal feature pipeline.
Risk = calibrated probability (x100) that the user-day lies inside an exfiltration window. Levels (FIXED project thresholds 60 and 85): Low <= 60 < Medium <= 85 < High; alert = High.
SHAP values are TreeSHAP (exact for LightGBM) in log-odds of the RAW model score: sum(contributions) + base = logit(raw score).
"""
import json
from pathlib import Path
import numpy as np, pandas as pd, lightgbm as lgb

LEVELS = ["Low", "Medium", "High"]
_sig = lambda z: 1 / (1 + np.exp(-z))
_logit = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))


def feature_family(f):
    if f.startswith("nr_gap_alt"): return "rotation_gap (experimental)"
    if f.startswith(("cumulative_deviation", "channel_distribution_shift", "consecutive_elevated_days")): return "accumulation / shift"
    if f.startswith("nr_"): return "rotation (nr_*)"
    if f.startswith(("email", "external_email")): return "email"
    if f.startswith(("usb", "file_event", "unique_usb")): return "usb"
    if f.startswith(("http", "www")): return "http"
    return "context (domains / recipients / attachments)"


class MubsirScorer:
    def __init__(self, bundle_dir=None):
        self.dir = Path(bundle_dir) if bundle_dir else Path(__file__).resolve().parent
        self.man = json.load(open(self.dir / "manifest.json"))
        self.windows = sorted(int(h) for h in self.man["windows"])
        self.cfg = {h: self.man["windows"][str(h)] for h in self.windows}
        rb = self.man["risk_bands"]; self.lo, self.hi = float(rb["low_max"]), float(rb["medium_max"])           # fixed thresholds 60 / 85
        self.booster = {h: lgb.Booster(model_file=str(self.dir / self.cfg[h]["model_file"])) for h in self.windows}

    # ---------------------------------------------------------------- helpers
    def _matrix(self, X, h):
        feats = self.cfg[h]["features"]; miss = [f for f in feats if f not in X.columns]
        if miss: raise ValueError(f"window {h}: missing {len(miss)} feature column(s): {miss[:8]}{' ...' if len(miss) > 8 else ''}")
        return X[feats].astype("float32").values                                  # exact training column ORDER

    def _risk(self, raw, h):
        c = self.cfg[h]; return 100 * _sig(c["platt_coef"] * _logit(raw) + c["platt_intercept"])

    def level_of(self, risk):
        """risk (0-100, scalar or array) -> level index 0/1/2 : Low (<=60), Medium (60<risk<=85), High (>85)."""
        r = np.asarray(risk, float); return np.where(r > self.hi, 2, np.where(r > self.lo, 1, 0))

    def thresholds(self):
        """the two fixed thresholds on the 0-100 risk scale, plus their equivalent raw model scores per window (for reference)."""
        out = []
        for h, c in self.cfg.items():
            raw = lambda t: float(_sig((_logit(t / 100) - c["platt_intercept"]) / c["platt_coef"]))
            out.append(dict(window=h, low_max_risk=self.lo, medium_max_risk=self.hi, low_max_raw=raw(self.lo), medium_max_raw=raw(self.hi)))
        return pd.DataFrame(out)

    # ---------------------------------------------------------------- scoring
    def score(self, X, windows=None):
        """Row-level output: risk_{h} (0-100), level_{h}, and the overall risk (max over windows), level (Low/Medium/High), alert (= risk > 85 in any window)."""
        windows = windows or self.windows; out = X[[c for c in ("user", "day") if c in X.columns]].copy().reset_index(drop=True)
        lv = np.zeros((len(X), len(windows)), int)
        for j, h in enumerate(windows):
            raw = self.booster[h].predict(self._matrix(X, h)); r = self._risk(raw, h)
            out[f"score_raw_{h}"] = raw; out[f"risk_{h}"] = r
            lv[:, j] = self.level_of(r); out[f"level_{h}"] = [LEVELS[k] for k in lv[:, j]]
        out["risk"] = out[[f"risk_{h}" for h in windows]].max(axis=1); out["level"] = [LEVELS[k] for k in lv.max(axis=1)]
        out["alert"] = lv.max(axis=1) == 2; out["alert_windows"] = [",".join(str(h) for h, k in zip(windows, row) if k == 2) for row in lv]
        return out

    def score_users(self, scored):
        """Per-user result from the row-level output (needs a `user` column): peak risk per window and overall (max over windows) over the rows given -> level Low/Medium/High (alert = High)."""
        if "user" not in scored: raise ValueError("score_users needs a 'user' column")
        g = scored.groupby("user"); res = g[[c for c in scored if c.startswith("risk_")]].max().add_suffix("_peak")
        res["risk_peak"] = res[[f"risk_{h}_peak" for h in self.windows if f"risk_{h}_peak" in res]].max(axis=1); lv = self.level_of(res["risk_peak"].values)
        res["level"] = [LEVELS[k] for k in lv]; res["alert"] = lv == 2; res["n_days"] = g.size()
        if "day" in scored:
            i = scored.groupby("user").risk.idxmax(); res["peak_day"] = scored.loc[i].set_index("user").day; res["first_alert_day"] = scored[scored.alert].groupby("user").day.min()
        return res

    # ---------------------------------------------------------------- explanations
    def explain(self, X, window=None, top_k=5):
        """Top-k SHAP contributions per row and window (long format). `window` = one window, or None for all.
        columns: row, user, day, window, rank, feature, family, value, shap (log-odds, + raises risk), effect, base_logodds, logodds, risk."""
        rows = []
        if len(X) == 0: return pd.DataFrame(columns=["row", "user", "day", "window", "rank", "feature", "family", "value", "shap", "effect", "base_logodds", "logodds", "risk"])
        for h in ([window] if window else self.windows):
            M = self._matrix(X, h); feats = self.cfg[h]["features"]; C = self.booster[h].predict(M, pred_contrib=True); V, base = C[:, :-1], C[:, -1]
            logodds = V.sum(1) + base; risk = self._risk(_sig(logodds), h)
            for i in range(len(X)):
                for rk, j in enumerate(np.argsort(-np.abs(V[i]))[:top_k], 1):
                    rows.append(dict(row=i, user=X["user"].iloc[i] if "user" in X else None, day=X["day"].iloc[i] if "day" in X else None, window=h, rank=rk, feature=feats[j], family=feature_family(feats[j]),
                                     value=float(M[i, j]) if not np.isnan(M[i, j]) else np.nan, shap=float(V[i, j]), effect="raises risk" if V[i, j] > 0 else "lowers risk", base_logodds=float(base[i]), logodds=float(logodds[i]), risk=float(risk[i])))
        return pd.DataFrame(rows)

    def explain_text(self, X, window, top_k=5):
        """One readable line per row: 'risk 97.3 (window 10) <- cumulative_deviation_10wd=11.3 (+4.37), ...'."""
        e = self.explain(X, window, top_k); out = []
        for i, g in e.groupby("row"):
            out.append(f"risk {g.risk.iloc[0]:.1f} (window {window}) <- " + ", ".join(f"{r.feature}={r.value:.4g} ({r.shap:+.2f})" for r in g.itertuples()))
        return out


def score_features(features_df, bundle_dir=None):
    """convenience: rows + per-user tiers."""
    sc = MubsirScorer(bundle_dir); rows = sc.score(features_df); return rows, (sc.score_users(rows) if "user" in rows else None)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Score a feature table (parquet/csv) with the MUBSIR bundle")
    ap.add_argument("input"); ap.add_argument("--out", default=None); ap.add_argument("--explain", type=int, default=0, help="top-k SHAP features for the first alerts (window with highest risk)")
    a = ap.parse_args(); df = pd.read_parquet(a.input) if a.input.endswith(".parquet") else pd.read_csv(a.input, parse_dates=["day"] if "day" in pd.read_csv(a.input, nrows=1) else None)
    sc = MubsirScorer(); rows = sc.score(df); users = sc.score_users(rows) if "user" in rows else None
    print(sc.thresholds().round(2).to_string(index=False)); print(users.round(1).to_string() if users is not None else rows.head().to_string())
    if a.out: rows.to_csv(a.out, index=False)
    if a.explain:
        for i in np.flatnonzero(rows.alert.values)[:5]:
            h = int(max(sc.windows, key=lambda w: rows[f"risk_{w}"].iloc[i])); print(f"{rows.user.iloc[i] if 'user' in rows else i} {rows.day.iloc[i] if 'day' in rows else ''}: " + sc.explain_text(df.iloc[[i]], h, a.explain)[0])
