"""Step 30: export a self-contained inference bundle for the FINAL75 per-window LightGBM models (no retraining of the models).
The trained models are the ones saved by 28_final75.py (fit on the 796 development users). What is (re)derived here:
  * Platt calibration (risk 0-100) = LogisticRegression on logit(raw) fitted on the pooled OUT-OF-FOLD scores of CV repeat 0 (exactly as in step 22/28);
  * reference percentile thresholds: Dangerous = 95th pct, Watch = 85th pct of the OOF control-user peaks (kept for reference; the product levels are the fixed 60/85 bands). They are RE-DERIVED and must equal the thresholds stored in the joblib files (checked);
  * the booster of every model in LightGBM's native text format + a JSON manifest (feature order, calibration, thresholds, definitions).
"""
import json, shutil, time, numpy as np, pandas as pd, joblib, lightgbm as lgb
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from common import *
from models import fit_predict

t0 = time.time()
src = open("28_final75.py").read(); exec(src.split("cv_rows, store")[0])          # data, split, es_users, platt, peaks ...
OUT = MODEL; OUT.mkdir(exist_ok=True)
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
sig = lambda z: 1 / (1 + np.exp(-z))
man = dict(name="MUBSIR stage-1 detector (FINAL75)", version="1.0", created=time.strftime("%Y-%m-%d"), algorithm="LightGBM (default parameters; Optuna tuning not adopted)",
           label="y_h = 1 when the user is on an attack day within the last h workdays (today included)", windows={}, notes=[
               "Input = the project's daily feature table (one row per user-workday). No scaling/encoding is applied: trees are scale-free and NaN is handled natively by LightGBM.",
               "Features must come from the project's causal feature pipeline (rolling windows over the user's workday history, 2010 baseline percentiles P50/P90/P95).",
               "Raw score = model probability. risk_0_100 = 100 * sigmoid(platt_coef * logit(raw) + platt_intercept): a CALIBRATED PROBABILITY (x100) that the user-day lies inside an exfiltration window; it is not a direct measure of deviation magnitude (deviation enters through the features, mainly cumulative_deviation_*).",
               "Risk levels use FIXED project thresholds 60 and 85 on the 0-100 risk scale: Low: risk <= 60; Medium: 60 < risk <= 85; High: risk > 85. Alert = High. User level = peak risk over the monitored period (max over windows).",
               "The per-window percentile thresholds (thr_*_raw / thr_*_risk: 95th / 85th percentile of out-of-fold control-user peaks) are kept for reference only and are NOT used for the levels."])
man["risk_bands"] = dict(low_max=60.0, medium_max=85.0, labels=["Low", "Medium", "High"], rule="Low: risk <= 60 | Medium: 60 < risk <= 85 | High: risk > 85", alert_level="High")
for h in WINDOWS:
    M = joblib.load(RES / "models" / f"final75_FINAL75_w{h}.joblib"); mdl, feats = M["model"], M["features"]; assert len(feats) == 75 and feats == F75(h)
    yd = dev[f"y_{h}"].values.astype(int); Xd = dev[feats].astype("float32").values; u_dev = dev.user.values
    oof = np.full(len(dev), np.nan); rng = np.random.default_rng(SEED)
    for k, (a, b) in enumerate(StratifiedGroupKFold(5, shuffle=True, random_state=SEED).split(dev_users, strat_dev.values, dev_scn)):
        tr_u, va_u = dev_users[a], dev_users[b]; es = es_users(tr_u, rng); in_es = np.isin(u_dev, list(es)); tr = np.isin(u_dev, tr_u) & ~in_es; va = np.isin(u_dev, va_u)
        s, _ = fit_predict("LightGBM", Xd[tr], yd[tr], Xd[va], Xd[in_es], yd[in_es], seed=SEED); oof[va] = s
    po = peaks(dev, oof); ctrl = po[[not is_inj[u] for u in po.index]]; thrD, thrW = float(np.quantile(ctrl, .95)), float(np.quantile(ctrl, .85))
    assert abs(thrD - M["thr_dangerous"]) < 1e-9 and abs(thrW - M["thr_watch"]) < 1e-9, (h, thrD, M["thr_dangerous"], thrW, M["thr_watch"])
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(lg(oof)[:, None], yd); coef, icpt = float(lr.coef_[0, 0]), float(lr.intercept_[0])
    risk = lambda raw: 100 * sig(coef * lg(np.asarray(raw)) + icpt)
    booster = mdl.booster_; booster.save_model(str(OUT / f"lgbm_w{h}.txt"))
    b2 = lgb.Booster(model_file=str(OUT / f"lgbm_w{h}.txt")); Xt = tst[feats].astype("float32").values
    assert np.allclose(b2.predict(Xt), mdl.predict_proba(Xt)[:, 1], atol=1e-12), "native-model roundtrip differs"
    man["windows"][str(h)] = dict(model_file=f"lgbm_w{h}.txt", n_features=75, features=feats, n_trees=int(mdl.n_estimators), platt_coef=coef, platt_intercept=icpt,
                                  thr_dangerous_raw=thrD, thr_watch_raw=thrW, thr_dangerous_risk=float(risk(thrD)), thr_watch_risk=float(risk(thrW)),
                                  threshold_rule="REFERENCE ONLY (not used). Dangerous = 95th percentile, Watch = 85th percentile of the out-of-fold per-user peak scores of control users (development users)")
    print(f"[{time.time()-t0:4.0f}s] w{h}: thrD raw {thrD:.4f} (=stored) risk {risk(thrD):.1f} | thrW raw {thrW:.4f} risk {risk(thrW):.1f} | platt {coef:.3f}x+{icpt:.3f} | native roundtrip OK", flush=True)
man["input_columns_all"] = sorted({f for w in man["windows"].values() for f in w["features"]})
json.dump(man, open(OUT / "manifest.json", "w"), indent=1)
shutil.copy("mubsir_infer.py", OUT / "mubsir_infer.py") if (PKG / "mubsir_infer.py").exists() else None
# small demo input: 3 representative test users (all their days), only identifiers + the 77 input columns
keep = ["user", "day"] + man["input_columns_all"]; demo_users = ["NVH3726", "SHB3512", "DBF3582"]
tst[tst.user.isin(demo_users)][keep].to_parquet(OUT / "example_input.parquet", index=False)
print("saved bundle to", OUT, "| input columns:", len(man["input_columns_all"]), f"| {time.time()-t0:.0f}s")
