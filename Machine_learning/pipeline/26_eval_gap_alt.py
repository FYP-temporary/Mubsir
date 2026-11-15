"""Step 26: Baseline(74) vs Baseline + nr_gap_alt_G (G=0..3). Development users only -- the 199-user test set is NOT touched (not used to choose G).
Protocol identical to step 22: template-grouped StratifiedGroupKFold(5) x 3 repeats (seeds SEED+rep), es_users inner early-stopping split, LightGBM defaults.
Each candidate adds the three window versions (5/10/20wd) of the single G to the 74 features (each per-window model already uses all three nr_* windows)."""
import time, numpy as np, pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score
from common import *
from models import fit_predict, fit_final

t0 = time.time()
src = open("22_final_model.py").read()
pre = src.split("# ---------------------------------------------------------------- template-grouped split")[0]
exec(pre)                                              # df (with EVF/NEWF merged), BASE/ACC/NR/FINAL, SETS, W3/W4
GAP = pd.read_parquet(WORK / "gap_alt_features.parquet"); assert (GAP.user.values == df.user.values).all() and (GAP.day.values == df.day.values).all()
GS = (0, 1, 2, 3); W = (5, 10, 20)
df = pd.concat([df, GAP.drop(columns=["user", "day"])], axis=1)
CAND = {"BASE74": FINAL}
for G in GS: CAND[f"+G{G}"] = FINAL + [f"nr_gap_alt_{G}_{w}wd" for w in W]
assert all(c in df.columns for v in CAND.values() for c in v)
# ------------------------------------------------ same split as 22
sp = pd.read_csv(SPLIT).set_index("user"); users = df.user.unique(); asg = pd.read_parquet(ASSIGN).set_index("user")
meta = sp.loc[users, ["group", "stealth"]].copy(); meta["scn"] = asg.loc[users, "scenario_id"].values
strat = (meta.group + "_" + meta.stealth.astype(str)).values; scn = dict(zip(users, meta.scn.values)); is_inj = dict(zip(users, (meta.group != "control").values))
tr_i, te_i = next(StratifiedGroupKFold(5, shuffle=True, random_state=SEED).split(users, strat, meta.scn.values))
dev_users = users[tr_i]; dev = df[df.user.isin(dev_users)].reset_index(drop=True)
strat_dev = pd.Series(strat[tr_i], index=dev_users); dev_scn = np.array([scn[u] for u in dev_users])
cat = pd.read_parquet(GT_USER_DAYS.parent.parent / "stages_output" / "approved_scenario_catalog_r62.parquet").set_index("scenario_id")
intermittent = {u: bool(is_inj[u] and cat.loc[scn[u], "off_days"] > 0) for u in dev_users}      # attackers whose schedule contains off (quiet) days
rot = {u: bool(is_inj[u] and cat.loc[scn[u], "switching_level"] in ("Medium", "High")) for u in dev_users}
print(f"dev users {len(dev_users)} | injected {sum(is_inj[u] for u in dev_users)} | intermittent attackers {sum(intermittent.values())} | Medium/High switching {sum(rot.values())}", flush=True)


def es_users(tr_users, rng):
    g = pd.Series(list(tr_users)).groupby([scn[u] for u in tr_users]).apply(list); need = int(0.15 * len(tr_users)); es = []
    for k in rng.permutation(len(g)):
        if len(es) >= need: break
        es += g.iloc[k]
    return set(es)


def prec_at(y, s, fpr):
    thr = np.quantile(s[y == 0], 1 - fpr); pred = s >= thr; return (pred & (y == 1)).sum() / max(pred.sum(), 1)


u_dev = dev.user.values; inj_row = np.array([is_inj[u] for u in u_dev]); int_row = np.array([intermittent[u] for u in u_dev])
rows, oofs, gains = [], {}, []
for h in WINDOWS:
    yd = dev[f"y_{h}"].values.astype(int)
    for S, feats in CAND.items():
        Xd = dev[feats].astype("float32").values
        for rep in range(3):
            oof = np.full(len(dev), np.nan); rng = np.random.default_rng(SEED + rep)
            for k, (a, b) in enumerate(StratifiedGroupKFold(5, shuffle=True, random_state=SEED + rep).split(dev_users, strat_dev.values, dev_scn)):
                tr_u, va_u = dev_users[a], dev_users[b]; es = es_users(tr_u, rng)
                in_es = np.isin(u_dev, list(es)); tr = np.isin(u_dev, tr_u) & ~in_es; va = np.isin(u_dev, va_u)
                s, nit = fit_predict("LightGBM", Xd[tr], yd[tr], Xd[va], Xd[in_es], yd[in_es], seed=SEED + rep); oof[va] = s
                m = row_metrics(yd[va], s); m["precision_fpr1"] = prec_at(yd[va], s, .01)
                sub = va & (int_row | ~inj_row)                     # intermittent attackers + all controls of this fold
                m2 = row_metrics(yd[sub], oof[sub]); m.update(int_pr_auc=m2["pr_auc"], int_rec_fpr1=m2["rec_fpr1"]); m.update(set=S, window=h, kind="fold", rep=rep, fold=k); rows.append(m)
            m = row_metrics(yd, oof); m["precision_fpr1"] = prec_at(yd, oof, .01)
            pk = pd.DataFrame({"user": u_dev, "s": oof}).groupby("user").s.max(); lab = np.array([is_inj[u] for u in pk.index]); it = np.array([intermittent[u] for u in pk.index])
            thr = np.quantile(pk[~lab], 0.95)                                         # Dangerous threshold: 95th pct of OOF control peaks (as in 22)
            m.update(user_auc=roc_auc_score(lab, pk.values), user_recall_at5FA=float((pk[lab] >= thr).mean()), user_fpr_at_thr=float((pk[~lab] >= thr).mean()),
                     user_precision=float((pk[lab] >= thr).sum() / max((pk >= thr).sum(), 1)), user_recall_intermittent=float((pk[it] >= thr).mean()),
                     user_recall_nonintermittent=float((pk[lab & ~it] >= thr).mean()))
            sub = (int_row | ~inj_row); m2 = row_metrics(yd[sub], oof[sub]); m.update(int_pr_auc=m2["pr_auc"], int_rec_fpr1=m2["rec_fpr1"]); m.update(set=S, window=h, kind="pooled", rep=rep, fold=-1); rows.append(m)
        mdl = fit_final("LightGBM", Xd, yd, 300, seed=SEED); gi = pd.Series(mdl.booster_.feature_importance("gain"), index=feats); gi = gi / gi.sum()
        for f_ in feats:
            if "gap_alt" in f_: gains.append(dict(set=S, window=h, feature=f_, gain_share=float(gi[f_]), nr_alt_gain_share=float(gi[f"nr_alt_{h}wd"])))
        P = pd.DataFrame(rows); q = P[(P.set == S) & (P.window == h) & (P.kind == "pooled")]
        print(f"[{time.time()-t0:5.0f}s] h={h} {S:7s} pooled R@1%={q.rec_fpr1.mean():.4f} PR-AUC={q.pr_auc.mean():.4f} | intermittent-subset R@1%={q.int_rec_fpr1.mean():.4f} PR={q.int_pr_auc.mean():.4f}", flush=True)
P = pd.DataFrame(rows); P.to_csv(RES / "gap_alt_cv.csv", index=False); pd.DataFrame(gains).to_csv(RES / "gap_alt_gain.csv", index=False)

# ------------------------------------------------ paired fold-level comparison vs BASE74 + redundancy diagnostics
out = []
for h in WINDOWS:
    b = P[(P.set == "BASE74") & (P.window == h) & (P.kind == "fold")].set_index(["rep", "fold"])
    bp = P[(P.set == "BASE74") & (P.window == h) & (P.kind == "pooled")].set_index("rep")
    for S in CAND:
        if S == "BASE74": continue
        c = P[(P.set == S) & (P.window == h) & (P.kind == "fold")].set_index(["rep", "fold"]); cp = P[(P.set == S) & (P.window == h) & (P.kind == "pooled")].set_index("rep")
        r = dict(window=h, set=S)
        for mt in ("rec_fpr1", "pr_auc", "precision_fpr1", "int_rec_fpr1", "int_pr_auc"):
            d = (c[mt] - b[mt]).dropna(); r[f"d_{mt}"] = d.mean(); r[f"sd_{mt}"] = d.std(); r[f"wins_{mt}"] = int((d > 0).sum()); r["n_folds"] = len(d)
        for mt in ("user_recall_at5FA", "user_fpr_at_thr", "user_precision", "user_recall_intermittent", "user_recall_nonintermittent", "user_auc"):
            r[f"d_{mt}"] = float((cp[mt] - bp[mt]).mean())
        r["base_fold_sd_rec1"] = float(b.rec_fpr1.std()); out.append(r)
D = pd.DataFrame(out); D.to_csv(RES / "gap_alt_vs_base.csv", index=False)
red = []
for w in W:
    for G in GS:
        f = dev[f"nr_gap_alt_{G}_{w}wd"].values; a = dev[f"nr_alt_{w}wd"].values; y = dev[f"y_{w}"].values
        ac = pd.Series(f).corr(pd.Series(a), method="spearman")
        red.append(dict(window=w, G=G, spearman_with_nr_alt=ac, share_identical_to_nr_alt=float(np.isclose(f, a).mean()), univariate_auc=roc_auc_score(y, f), univariate_auc_nr_alt=roc_auc_score(y, a),
                        spearman_with_cum_dev=pd.Series(f).corr(dev[f"cumulative_deviation_{w}wd"], method="spearman"),
                        spearman_with_nr_m=pd.Series(f).corr(dev[f"nr_m_{w}wd"], method="spearman")))
pd.DataFrame(red).to_csv(RES / "gap_alt_redundancy.csv", index=False)
pd.set_option("display.width", 250); print(D[["window", "set", "d_rec_fpr1", "sd_rec_fpr1", "wins_rec_fpr1", "d_pr_auc", "wins_pr_auc", "d_int_rec_fpr1", "d_int_pr_auc", "d_user_recall_at5FA", "n_folds"]].round(4).to_string(index=False))
print(pd.DataFrame(red).round(3).to_string(index=False)); print(f"done {time.time()-t0:.0f}s")
