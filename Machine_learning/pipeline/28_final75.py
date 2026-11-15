"""Step 28 (derived from step 22): FINAL75 = FINAL74 + nr_gap_alt_2 of the model's own window. Outputs prefixed final75_. Original docstring follows.
Step 22: final agreed feature set (74 features) -- same protocol as step 19 (template-grouped split, 5x3 CV, 199-user untouched test, full metric set).
Sets: FINAL74 (agreed list) | NO_NR (FINAL74 minus the 21 nr_* rotation features = what rotation adds) | NO_UUF (FINAL74 minus unique_usb_files) | REF87 (previous model).
Extras: gain share + permutation importance (drop in Recall@1%FPR on the untouched test) for every FINAL74 feature."""
import time, numpy as np, pandas as pd, joblib
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve, log_loss
from common import *
from models import fit_predict, fit_final

t0 = time.time()
df = pd.read_parquet(PREPARED).sort_values(["user", "day"]).reset_index(drop=True)
F87 = select_features(df, "nostatic"); assert len(F87) == 87
EVF = pd.read_parquet(WORK / "evidence_features.parquet"); NEWF = pd.read_parquet(WORK / "final_changed_features.parquet")
for X_ in (EVF, NEWF): assert (X_.user.values == df.user.values).all() and (X_.day.values == df.day.values).all()
EVF = EVF.drop(columns=["user", "day"] + [c for c in NEWF.columns if c in EVF.columns]); NEWF = NEWF.drop(columns=["user", "day"])
df = pd.concat([df, EVF, NEWF], axis=1)
W3 = (5, 10, 20); W4 = (5, 10, 20, 30)
BASE = (["email_event_count", "external_email_count"] + [f"external_email_count_{w}wd" for w in W4] + [f"email_active_days_{w}wd" for w in W3] + ["email_count_to_p95_ratio", "email_count_to_p90_ratio"]
        + ["usb_copy_count"] + [f"usb_copy_count_{w}wd" for w in W4] + [f"usb_active_days_{w}wd" for w in W3] + ["file_event_count", "unique_usb_files", "usb_copy_to_p95_ratio", "usb_copy_to_p90_ratio"]
        + ["http_event_count", "www_visit_count", "www_upload_count"] + [f"http_upload_count_{w}wd" for w in W4] + [f"http_active_days_{w}wd" for w in W3] + ["http_upload_to_p95_ratio", "http_upload_to_p90_ratio"]
        + ["unique_external_recipients", "unique_external_domains", "unique_upload_domains", "unique_domains", "emails_with_attachments", "attachment_count"])
ACC = [f"{n}_{w}wd" for n in ("cumulative_deviation", "consecutive_elevated_days", "channel_distribution_shift") for w in W4]
NR = [f"{n}_{w}wd" for n in ("nr_m", "nr_entropy", "nr_excl_days", "nr_overlap_days", "nr_alt", "nr_handoff", "nr_stealth_acc") for w in W3]
FINAL = BASE + ACC + NR
assert len(BASE) == 41 and len(ACC) == 12 and len(NR) == 21 and len(FINAL) == 74 and len(set(FINAL)) == 74 and all(c in df.columns for c in FINAL), [c for c in FINAL if c not in df.columns]
GAP = pd.read_parquet(WORK / "gap_alt_features.parquet"); assert (GAP.user.values == df.user.values).all() and (GAP.day.values == df.day.values).all()
df = pd.concat([df, GAP.drop(columns=["user", "day"])], axis=1)
F75 = lambda h: FINAL + [f"nr_gap_alt_2_{h}wd"]                     # each per-window model: the 74 agreed features + nr_gap_alt_2 of ITS OWN window = 75
assert all(f"nr_gap_alt_2_{h}wd" in df.columns for h in (5, 10, 20))
SETS = {"FINAL74": FINAL, "FINAL75": F75}
GROUP_OF = {**{f: "base" for f in BASE}, **{f: "accumulation_shift" for f in ACC}, **{f: "rotation_nr" for f in NR}, **{f"nr_gap_alt_2_{w}wd": "gap_alt" for w in (5, 10, 20)}}
print({k: (len(v) if not callable(v) else len(v(5))) for k, v in SETS.items()}, flush=True)

# ---------------------------------------------------------------- template-grouped split
sp = pd.read_csv(SPLIT).set_index("user"); users = df.user.unique(); asg = pd.read_parquet(ASSIGN).set_index("user")
meta = sp.loc[users, ["group", "stealth"]].copy(); meta["scn"] = asg.loc[users, "scenario_id"].values
strat = (meta.group + "_" + meta.stealth.astype(str)).values; scn = dict(zip(users, meta.scn.values)); is_inj = dict(zip(users, (meta.group != "control").values))
tr_i, te_i = next(StratifiedGroupKFold(5, shuffle=True, random_state=SEED).split(users, strat, meta.scn.values))
dev_users, test_users = users[tr_i], users[te_i]
print(f"dev users {len(dev_users)} (inj {sum(is_inj[u] for u in dev_users)}) | test users {len(test_users)} (inj {sum(is_inj[u] for u in test_users)}, ctrl {sum(not is_inj[u] for u in test_users)}) | shared scenarios dev/test: {len(set(map(scn.get, dev_users)) & set(map(scn.get, test_users)))}", flush=True)
dev = df[df.user.isin(dev_users)].reset_index(drop=True); tst = df[df.user.isin(test_users)].reset_index(drop=True)
gu = pd.read_parquet(GT_USERS).set_index("user")
strat_dev = (meta.loc[meta.index.isin(dev_users)].group + "_" + meta.loc[meta.index.isin(dev_users)].stealth.astype(str)); strat_dev = pd.Series(strat[tr_i], index=dev_users)
dev_scn = np.array([scn[u] for u in dev_users])


def es_users(tr_users, rng):
    g = pd.Series(list(tr_users)).groupby([scn[u] for u in tr_users]).apply(list); need = int(0.15 * len(tr_users)); es = []
    for k in rng.permutation(len(g)):
        if len(es) >= need: break
        es += g.iloc[k]
    return set(es)


def ece(y, p, bins=10):
    b = np.minimum((p * bins).astype(int), bins - 1); return float(sum(abs(y[b == k].mean() - p[b == k].mean()) * (b == k).mean() for k in range(bins) if (b == k).any()))


def prf(y, s, fpr):
    thr = np.quantile(s[y == 0], 1 - fpr); pred = s >= thr; tp = (pred & (y == 1)).sum(); fp = (pred & (y == 0)).sum(); fn = ((~pred) & (y == 1)).sum()
    pr = tp / max(tp + fp, 1); rc = tp / max(tp + fn, 1); return pr, (2 * pr * rc / max(pr + rc, 1e-12))


def platt(s_oof, y_oof):
    lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    m = LogisticRegression(C=1e6, max_iter=1000).fit(lg(s_oof)[:, None], y_oof); return lambda s: m.predict_proba(lg(s)[:, None])[:, 1]


def peaks(d, s):
    p = pd.DataFrame({"user": d.user.values, "s": s}).groupby("user").s.max(); return p


def user_cls(p, thr):
    inj = np.array([is_inj[u] for u in p.index]); pred = p.values >= thr
    tp = int((pred & inj).sum()); fn = int((~pred & inj).sum()); fp = int((pred & ~inj).sum()); tn = int((~pred & ~inj).sum())
    rec = tp / max(tp + fn, 1); fpr = fp / max(fp + tn, 1); prec = tp / max(tp + fp, 1)
    return dict(TP=tp, FN=fn, FP=fp, TN=tn, recall=rec, FPR=fpr, precision=prec, F1=2 * prec * rec / max(prec + rec, 1e-12), accuracy=(tp + tn) / len(p), balanced_acc=(rec + 1 - fpr) / 2)


cv_rows, store = [], {}
for h in WINDOWS:
    yd = dev[f"y_{h}"].values.astype(int); yt = tst[f"y_{h}"].values.astype(int); u_dev = dev.user.values
    for S, feats0 in SETS.items():
        feats = feats0(h) if callable(feats0) else feats0
        Xd = dev[feats].astype("float32").values; Xt = tst[feats].astype("float32").values; iters = []; oof0 = None
        for rep in range(3):
            oof = np.full(len(dev), np.nan); rng = np.random.default_rng(SEED + rep)
            for k, (a, b) in enumerate(StratifiedGroupKFold(5, shuffle=True, random_state=SEED + rep).split(dev_users, strat_dev.values, dev_scn)):
                tr_u, va_u = dev_users[a], dev_users[b]; es = es_users(tr_u, rng)
                in_es = np.isin(u_dev, list(es)); tr = np.isin(u_dev, tr_u) & ~in_es; va = np.isin(u_dev, va_u)
                s, nit = fit_predict("LightGBM", Xd[tr], yd[tr], Xd[va], Xd[in_es], yd[in_es], seed=SEED + rep); oof[va] = s; iters.append(nit)
                m = row_metrics(yd[va], s); m.update(set=S, window=h, kind="fold", rep=rep, fold=k); cv_rows.append(m)
            m = row_metrics(yd, oof); pk = peaks(dev, oof); lab = np.array([is_inj[u] for u in pk.index])
            m.update(set=S, window=h, kind="pooled", rep=rep, fold=-1, user_auc=roc_auc_score(lab, pk.values),
                     user_detect_at5FA=float((pk[lab] >= np.quantile(pk[~lab], 0.95)).mean())); cv_rows.append(m)
            if rep == 0: oof0 = oof.copy()
        mdl = fit_final("LightGBM", Xd, yd, int(np.mean(iters)), seed=SEED); st = mdl.predict_proba(Xt)[:, 1]
        store[(S, h)] = dict(oof0=oof0, test=st, model=mdl, n_iter=int(np.mean(iters)), feats=feats)
        print(f"[{time.time()-t0:5.0f}s] h={h} {S:8s} CV pooled R@1%={np.mean([r['rec_fpr1'] for r in cv_rows if r['set']==S and r['window']==h and r['kind']=='pooled']):.3f}"
              f" | TEST R@1%={recall_at_fpr(yt, st, .01):.3f} PR={average_precision_score(yt, st):.3f}", flush=True)
pd.DataFrame(cv_rows).to_csv(RES / "final75_cv.csv", index=False)

# ---------------------------------------------------------------- test metrics
row_out, user_out, tier_rows, lat_rows, stealth_rows = [], [], [], [], []
thr_cache = {}
for (S, h), d in store.items():
    yd = dev[f"y_{h}"].values.astype(int); yt = tst[f"y_{h}"].values.astype(int); s = d["test"]
    pf = platt(d["oof0"], yd); sc = pf(s); m = row_metrics(yt, s)
    for f_, nm in ((0.01, "1"), (0.05, "5")): m[f"precision_fpr{nm}"], m[f"f1_fpr{nm}"] = prf(yt, s, f_)
    m.update(brier_platt=float(np.mean((sc - yt) ** 2)), logloss_platt=float(log_loss(yt, np.clip(sc, 1e-6, 1 - 1e-6))), ece_platt=ece(yt, sc), set=S, window=h, n_iter=d["n_iter"], n_features=len(d["feats"]))
    row_out.append(m)
    po = peaks(dev, d["oof0"]); ctrl = po[[not is_inj[u] for u in po.index]]
    thrD, thrW = float(np.quantile(ctrl, 0.95)), float(np.quantile(ctrl, 0.85)); thr_cache[(S, h)] = (thrD, thrW)
    pt = peaks(tst, s); lab = np.array([is_inj[u] for u in pt.index]); auc_u = roc_auc_score(lab, pt.values)
    for tier, thr in (("Dangerous(5%FA thr)", thrD), ("Watch+(15%FA thr)", thrW)):
        r = user_cls(pt, thr); r.update(set=S, window=h, threshold_name=tier, threshold=thr, user_auc=auc_u); user_out.append(r)
    # stealth subgroup + latency (alert = row score >= thrD)
    inj_users = [u for u in pt.index if is_inj[u]]
    for st_lv in ("Low", "Medium", "High"):
        us = [u for u in inj_users if gu.loc[u, "stealth_level"] == st_lv]
        stealth_rows.append(dict(set=S, window=h, stealth=st_lv, n=len(us), detect=float(np.mean([pt[u] >= thrD for u in us]))))
    gi = tst.groupby("user").indices; lats, pre = [], 0
    for u in inj_users:
        ix = gi[u]; dd = pd.to_datetime(tst.day.values[ix]); sc_u = s[ix]; a0 = np.searchsorted(dd, pd.Timestamp(gu.loc[u, "attack_start"]))
        pre += int((sc_u[:a0] >= thrD).any()); hit = np.flatnonzero(sc_u[a0:] >= thrD); lats.append(hit[0] if len(hit) else np.nan)
    lats = np.array(lats, float); det = ~np.isnan(lats)
    lat_rows.append(dict(set=S, window=h, n_injected=len(lats), detected=int(det.sum()), median_latency=float(np.nanmedian(lats)) if det.any() else np.nan, mean_latency=float(np.nanmean(lats)) if det.any() else np.nan,
                         within0=float((lats[det] <= 0).sum() / len(lats)), within3=float((lats[det] <= 3).sum() / len(lats)), within5=float((lats[det] <= 5).sum() / len(lats)),
                         within10=float((lats[det] <= 10).sum() / len(lats)), alert_before_start=float(pre / len(lats))))
for S in SETS:   # tiers over the three windows
    pk = {h: peaks(tst, store[(S, h)]["test"]) for h in WINDOWS}; idx = pk[5].index; tier = pd.Series("Normal", index=idx)
    for h in WINDOWS: tier[pk[h] >= thr_cache[(S, h)][1]] = np.where(tier[pk[h] >= thr_cache[(S, h)][1]] == "Dangerous", "Dangerous", "Watch")
    for h in WINDOWS: tier[pk[h] >= thr_cache[(S, h)][0]] = "Dangerous"
    for g_ in ("injected", "control"):
        us = [u for u in idx if (is_inj[u]) == (g_ == "injected")]; vc = tier[us].value_counts()
        tier_rows.append(dict(set=S, group=g_, n=len(us), Dangerous=int(vc.get("Dangerous", 0)), Watch=int(vc.get("Watch", 0)), Normal=int(vc.get("Normal", 0))))
R_, U_ = pd.DataFrame(row_out), pd.DataFrame(user_out); L_, T_, S_ = pd.DataFrame(lat_rows), pd.DataFrame(tier_rows), pd.DataFrame(stealth_rows)
R_.to_csv(RES / "final75_test_rows.csv", index=False); U_.to_csv(RES / "final75_test_users.csv", index=False); L_.to_csv(RES / "final75_latency.csv", index=False)
T_.to_csv(RES / "final75_tiers.csv", index=False); S_.to_csv(RES / "final75_stealth.csv", index=False)

# ---------------------------------------------------------------- bootstrap CI (users) for main sets
rng = np.random.default_rng(1); gi = tst.groupby("user").indices; tu = np.array(list(gi.keys())); boot = []
for S in ("FINAL74", "FINAL75"):
    for h in WINDOWS:
        yt = tst[f"y_{h}"].values.astype(int); s = store[(S, h)]["test"]; thrD = thr_cache[(S, h)][0]; pt = peaks(tst, s); res = []
        for _ in range(300):
            bu = rng.choice(tu, len(tu)); ix = np.concatenate([gi[u] for u in bu]); y, sc = yt[ix], s[ix]
            f, t, _ = roc_curve(y, sc); inj = np.array([is_inj[u] for u in bu]); pb = pt[bu].values
            res.append((average_precision_score(y, sc), np.interp(.01, f, t), np.interp(.05, f, t), (pb[inj] >= thrD).mean(), (pb[~inj] >= thrD).mean()))
        res = np.array(res); lo, hi = np.percentile(res, 2.5, axis=0), np.percentile(res, 97.5, axis=0)
        for j, nm in enumerate(("pr_auc", "rec_fpr1", "rec_fpr5", "user_detect", "user_FA")): boot.append(dict(set=S, window=h, metric=nm, lo=lo[j], hi=hi[j]))
B_ = pd.DataFrame(boot); B_.to_csv(RES / "final75_bootstrap_ci.csv", index=False)

# ---------------------------------------------------------------- importance by evidence group (FULL) + save models
imp = []
for h in WINDOWS:
    d = store[("FINAL75", h)]; g = pd.Series(d["model"].booster_.feature_importance("gain"), index=d["feats"]); g /= g.sum()
    for grp_, v in g.groupby(g.index.map(GROUP_OF)).sum().items(): imp.append(dict(window=h, group=grp_, gain_share=float(v)))
    for f, v in g.sort_values(ascending=False).head(8).items(): imp.append(dict(window=h, group="top_feature:" + f, gain_share=float(v)))
pd.DataFrame(imp).to_csv(RES / "final75_importance.csv", index=False)
for S in ("FINAL75",):
    for h in WINDOWS:
        joblib.dump(dict(model=store[(S, h)]["model"], features=store[(S, h)]["feats"], thr_dangerous=thr_cache[(S, h)][0], thr_watch=thr_cache[(S, h)][1]), RES / "models" / f"final75_{S}_w{h}.joblib")

# ---------------------------------------------------------------- print
pd.set_option("display.width", 260, "display.max_columns", 40, "display.max_rows", 400)
order = list(SETS)
cvt = pd.DataFrame(cv_rows); cvp = cvt[cvt.kind == "pooled"].groupby(["window", "set"])[["pr_auc", "roc_auc", "rec_fpr1", "rec_fpr5", "brier", "user_auc", "user_detect_at5FA"]].mean()
print("\n===== CV (template-grouped 5x3, pooled OOF) ====="); print(cvp.reindex(pd.MultiIndex.from_product([WINDOWS, order])).round(3).to_string())
print("\n===== TEST rows ====="); print(R_.set_index(["window", "set"]).reindex(pd.MultiIndex.from_product([WINDOWS, order]))[["n_features", "pr_auc", "roc_auc", "rec_fpr1", "rec_fpr5", "precision_fpr1", "f1_fpr1", "precision_fpr5", "f1_fpr5", "brier", "brier_platt", "logloss_platt", "ece_platt", "prevalence"]].round(3).to_string())
print("\n===== TEST users (peak), two operating points ====="); print(U_.set_index(["window", "set", "threshold_name"])[["TP", "FN", "FP", "TN", "recall", "FPR", "precision", "F1", "accuracy", "balanced_acc", "user_auc"]].round(3).to_string())
print("\n===== TIERS (max over 3 windows) ====="); print(T_.to_string(index=False))
print("\n===== latency ====="); print(L_.round(3).to_string(index=False))
print("\n===== stealth detection (Dangerous thr) ====="); print(S_.pivot_table(index=["window", "set"], columns="stealth", values="detect").round(3).to_string())
print("\n===== bootstrap 95% CI ====="); print(B_.round(3).to_string(index=False))
print("\n===== FINAL74 gain share by group ====="); print(pd.DataFrame(imp).query("not group.str.startswith('top')").pivot(index="group", columns="window", values="gain_share").round(3).to_string())

# ---------------------------------------------------------------- per-feature weights for FINAL74: gain share + permutation (drop in Recall@1%FPR and PR-AUC on the untouched test)
rngp = np.random.default_rng(7); pw = []
for h in WINDOWS:
    d = store[("FINAL75", h)]; yt = tst[f"y_{h}"].values.astype(int); Xt = tst[F75(h)].astype("float32").values; base_r = recall_at_fpr(yt, d["model"].predict_proba(Xt)[:, 1], .01); base_p = average_precision_score(yt, d["model"].predict_proba(Xt)[:, 1])
    gain = pd.Series(d["model"].booster_.feature_importance("gain"), index=F75(h)); gain /= gain.sum()
    for j, f in enumerate(F75(h)):
        dr, dp = [], []
        for _ in range(3):
            Xp = Xt.copy(); Xp[:, j] = rngp.permutation(Xp[:, j]); sp_ = d["model"].predict_proba(Xp)[:, 1]; dr.append(base_r - recall_at_fpr(yt, sp_, .01)); dp.append(base_p - average_precision_score(yt, sp_))
        pw.append(dict(window=h, feature=f, group=GROUP_OF[f], gain_share=float(gain[f]), perm_drop_recall1=float(np.mean(dr)), perm_drop_prauc=float(np.mean(dp))))
PW = pd.DataFrame(pw); PW.to_csv(RES / "final75_feature_weights.csv", index=False)
pv = PW.pivot_table(index=["group", "feature"], columns="window", values=["gain_share", "perm_drop_recall1"]); pv["gain_mean"] = pv["gain_share"].mean(axis=1); pv["perm_mean"] = pv["perm_drop_recall1"].mean(axis=1)
print("\n===== FINAL74 weights (gain share per window, permutation drop in Recall@1%FPR), sorted by mean gain ====="); print(pv.sort_values("gain_mean", ascending=False).round(4).to_string())
print("\n===== weight by group (sum of gain share) ====="); print(PW.groupby(["window", "group"]).gain_share.sum().unstack().round(3).to_string())
print("done", flush=True)
