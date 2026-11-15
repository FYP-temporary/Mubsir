"""Step 33: fixed risk bands (Low <=60 | Medium 60-85 | High >85) evaluated INSIDE the 5x3 template-grouped cross-validation (development users only; test set untouched).
usage: ALGO=LightGBM|XGBoost python 33_cv_fixed_bands.py     (features = FINAL75: the 74 agreed + nr_gap_alt_2 of the model's own window)
Calibration without leakage: for every fold k of a repeat, Platt scaling is fitted on the out-of-fold raw scores of the OTHER four folds of that repeat and applied to fold k.
Row level: each user-workday vs y_h. User level: user risk = peak over the fold's validation rows; 'any' = max over the three windows."""
import os, time, numpy as np, pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from common import *
from models import fit_predict

ALGO = os.environ["ALGO"]; t0 = time.time()
src = open("28_final75.py").read(); exec(src.split("cv_rows, store")[0])                      # dev, dev_users, strat_dev, dev_scn, es_users, F75, is_inj
LO, HI = 60.0, 85.0
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
u_dev = dev.user.values; REPS = 3
oof = {(h, r): np.full(len(dev), np.nan) for h in WINDOWS for r in range(REPS)}; fid = {r: np.full(len(dev), -1) for r in range(REPS)}
for h in WINDOWS:
    yd = dev[f"y_{h}"].values.astype(int); Xd = dev[F75(h)].astype("float32").values
    for rep in range(REPS):
        rng = np.random.default_rng(SEED + rep)
        for k, (a, b) in enumerate(StratifiedGroupKFold(5, shuffle=True, random_state=SEED + rep).split(dev_users, strat_dev.values, dev_scn)):
            tr_u, va_u = dev_users[a], dev_users[b]; es = es_users(tr_u, rng); in_es = np.isin(u_dev, list(es)); tr = np.isin(u_dev, tr_u) & ~in_es; va = np.isin(u_dev, va_u)
            s, _ = fit_predict(ALGO, Xd[tr], yd[tr], Xd[va], Xd[in_es], yd[in_es], seed=SEED + rep); oof[(h, rep)][va] = s; fid[rep][va] = k
    print(f"[{time.time()-t0:4.0f}s] {ALGO} window {h} done", flush=True)
np.savez_compressed(RES / f"cv75_oof_{ALGO}.npz", **{f"oof_w{h}_r{r}": v for (h, r), v in oof.items()}, **{f"fold_r{r}": v for r, v in fid.items()})

prf = lambda tp, fp, fn, tn: dict(TP=tp, FN=fn, FP=fp, TN=tn, recall=tp / max(tp + fn, 1), precision=tp / max(tp + fp, 1), FPR=fp / max(fp + tn, 1), F1=2 * tp / max(2 * tp + fp + fn, 1))
rows = []
for rep in range(REPS):
    f = fid[rep]; risk = {}
    for h in WINDOWS:
        yd = dev[f"y_{h}"].values.astype(int); o = oof[(h, rep)]; r = np.zeros(len(dev))
        for k in range(5):
            m = LogisticRegression(C=1e6, max_iter=1000).fit(lg(o[f != k])[:, None], yd[f != k]); r[f == k] = 100 * m.predict_proba(lg(o[f == k])[:, None])[:, 1]
        risk[h] = r
    for k in range(5):
        va = f == k; users_k = pd.Index(pd.unique(u_dev[va])); inj_k = np.array([is_inj[u] for u in users_k])
        for h in WINDOWS:
            y = dev[f"y_{h}"].values.astype(int)[va]; r = risk[h][va]
            for name, pos in (("High", r > HI), ("Medium+High", r > LO)):
                rows.append(dict(model=ALGO, rep=rep, fold=k, window=h, level="row", positive=name, **prf(int((pos & (y == 1)).sum()), int((pos & (y == 0)).sum()), int((~pos & (y == 1)).sum()), int((~pos & (y == 0)).sum()))))
            rows.append(dict(model=ALGO, rep=rep, fold=k, window=h, level="row", positive="band_attack_rate", **{f"{b}_n": int(m_.sum()) for b, m_ in zip(("Low", "Medium", "High"), (r <= LO, (r > LO) & (r <= HI), r > HI))},
                             **{f"{b}_attack_rate": float(y[m_].mean()) if m_.any() else np.nan for b, m_ in zip(("Low", "Medium", "High"), (r <= LO, (r > LO) & (r <= HI), r > HI))}))
        pk = {h: pd.Series(risk[h][va]).groupby(u_dev[va]).max().reindex(users_k).values for h in WINDOWS}; pk["any"] = np.max([pk[h] for h in WINDOWS], axis=0)
        for h in WINDOWS + ["any"]:
            for name, pos in (("High", pk[h] > HI), ("Medium+High", pk[h] > LO)):
                rows.append(dict(model=ALGO, rep=rep, fold=k, window=h, level="user", positive=name, **prf(int((pos & inj_k).sum()), int((pos & ~inj_k).sum()), int((~pos & inj_k).sum()), int((~pos & ~inj_k).sum()))))
R = pd.DataFrame(rows); R.to_csv(RES / f"cv75_fixed_bands_{ALGO}.csv", index=False)
print(f"saved {len(R)} rows | {time.time()-t0:.0f}s | done", flush=True)
