"""Step 32: evaluation with FIXED risk bands (project decision): Low 0-60 | Medium 61-85 | High 86-100  (two thresholds, 60 and 85, on the calibrated 0-100 risk scale).
Convention: Low: risk <= 60; Medium: 60 < risk <= 85; High: risk > 85. Positive (alert) = High; 'Medium or High' = risk > 60.
Models: LightGBM-75 (saved bundle) and XGBoost-75 (step 31), same split, same Platt calibration protocol (pooled OOF of CV repeat 0). Test = the 199 untouched users; thresholds are fixed beforehand, nothing is tuned on test.
Row level: each user-workday vs y_h. User level: user risk = PEAK over the monitored period (per window; 'any window' = max over windows)."""
import json, sys, numpy as np, pandas as pd
from common import *
src = open("28_final75.py").read(); exec(src.split("def es_users")[0])                     # tst (test rows with y_h), is_inj
sys.path.insert(0, str(MODEL)); from mubsir_infer import MubsirScorer
LO, HI = 60.0, 85.0
sc = MubsirScorer(MODEL); man = json.load(open(MODEL / "manifest.json")); lg_ = sc.score(tst[["user", "day"] + man["input_columns_all"]])
assert (lg_.user.values == tst.user.values).all()
band = lambda r: np.where(r > HI, "High", np.where(r > LO, "Medium", "Low"))
prf = lambda tp, fp, fn, tn: dict(TP=tp, FN=fn, FP=fp, TN=tn, recall=tp / max(tp + fn, 1), precision=tp / max(tp + fp, 1), FPR=fp / max(fp + tn, 1),
                                  F1=2 * tp / max(2 * tp + fp + fn, 1), accuracy=(tp + tn) / max(tp + fp + fn + tn, 1))
rows_out, users_out, cal_out = [], [], []
for h in WINDOWS:
    y = tst[f"y_{h}"].values.astype(int); R = {"LightGBM-75": lg_[f"risk_{h}"].values}
    x = pd.read_parquet(RES / f"xgb75_test_scores_w{h}.parquet"); assert (x.user.values == tst.user.values).all() and (x.y.values == y).all(); R["XGBoost-75"] = x.risk.values
    for m, r in R.items():
        for name, pos in (("High (>85)", r > HI), ("Medium or High (>60)", r > LO)):
            tp, fp, fn, tn = int((pos & (y == 1)).sum()), int((pos & (y == 0)).sum()), int(((~pos) & (y == 1)).sum()), int(((~pos) & (y == 0)).sum())
            rows_out.append(dict(model=m, window=h, level="row", positive=name, **prf(tp, fp, fn, tn), share_flagged=float(pos.mean())))
        b = band(r)
        for bn in ("Low", "Medium", "High"):
            k = b == bn; cal_out.append(dict(model=m, window=h, unit="row", band=bn, n=int(k.sum()), share=float(k.mean()), attack_rate=float(y[k].mean()) if k.any() else np.nan, mean_risk=float(r[k].mean()) if k.any() else np.nan))
        pk = pd.DataFrame({"user": tst.user.values, "r": r}).groupby("user").r.max(); inj = np.array([is_inj[u] for u in pk.index])
        for name, pos in (("High (>85)", pk.values > HI), ("Medium or High (>60)", pk.values > LO)):
            users_out.append(dict(model=m, window=h, level="user", positive=name, **prf(int((pos & inj).sum()), int((pos & ~inj).sum()), int((~pos & inj).sum()), int((~pos & ~inj).sum()))))
        bu = band(pk.values)
        for bn in ("Low", "Medium", "High"):
            k = bu == bn; cal_out.append(dict(model=m, window=h, unit="user", band=bn, n=int(k.sum()), share=float(k.mean()), attack_rate=float(inj[k].mean()) if k.any() else np.nan, mean_risk=float(pk.values[k].mean()) if k.any() else np.nan))
    R_all = {m: None for m in R}
for m in ("LightGBM-75", "XGBoost-75"):                                                   # any-window user risk = max over windows of the user's peak
    pk = pd.concat([pd.DataFrame({"user": tst.user.values, "r": (lg_[f"risk_{h}"].values if m == "LightGBM-75" else pd.read_parquet(RES / f"xgb75_test_scores_w{h}.parquet").risk.values)}).groupby("user").r.max().rename(h) for h in WINDOWS], axis=1).max(axis=1)
    inj = np.array([is_inj[u] for u in pk.index])
    for name, pos in (("High (>85)", pk.values > HI), ("Medium or High (>60)", pk.values > LO)):
        users_out.append(dict(model=m, window="any", level="user", positive=name, **prf(int((pos & inj).sum()), int((pos & ~inj).sum()), int((~pos & inj).sum()), int((~pos & ~inj).sum()))))
    bu = band(pk.values)
    for bn in ("Low", "Medium", "High"):
        k = bu == bn; cal_out.append(dict(model=m, window="any", unit="user", band=bn, n=int(k.sum()), share=float(k.mean()), attack_rate=float(inj[k].mean()) if k.any() else np.nan, mean_risk=float(pk.values[k].mean()) if k.any() else np.nan))
A, B, C = pd.DataFrame(rows_out), pd.DataFrame(users_out), pd.DataFrame(cal_out)
A.to_csv(RES / "fixed_bands_rows.csv", index=False); B.to_csv(RES / "fixed_bands_users.csv", index=False); C.to_csv(RES / "fixed_bands_calibration.csv", index=False)
pd.set_option("display.width", 250, "display.max_columns", 40)
print("ROW LEVEL"); print(A.round(3).to_string(index=False)); print("\nUSER LEVEL (risk = peak)"); print(B.round(3).to_string(index=False)); print("\nBAND CONTENT (attack_rate = share of rows/users that are truly in an attack window / injected)"); print(C.round(3).to_string(index=False))
