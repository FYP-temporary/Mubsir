"""Step 29: SHAP (FINAL75 models) (TreeSHAP, exact for LightGBM trees via pred_contrib) on the saved FINAL74 models, evaluated on the 199-user held-out test set.
Values are in log-odds of the raw model score (before Platt calibration). No refit, no change to the models.
Outputs (results/shap/): importance (mean|SHAP|), family-level grouped SHAP, direction (Spearman value vs SHAP), comparison with gain/permutation, beeswarm + family plots, 3 case studies."""
import time, numpy as np, pandas as pd, joblib, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt, shap
from scipy.stats import spearmanr
from common import *

t0 = time.time()
src = open("28_final75.py").read(); exec(src.split("def es_users")[0])          # df+features, same split -> tst (test users), is_inj, scn
OUT = RES / "shap75"; OUT.mkdir(exist_ok=True)
FW = pd.read_csv(RES / "final75_feature_weights.csv")


def family(f):
    if f.startswith("cumulative_deviation") or f.startswith("channel_distribution_shift") or f.startswith("consecutive_elevated_days"):
        return "accumulation_shift_" + ("cumdev" if f.startswith("cumulative") else "shift" if f.startswith("channel") else "consec")
    if f.startswith("nr_gap_alt"): return "gap_alt_experimental"
    if f.startswith("nr_"): return "rotation_nr"
    if f.startswith(("email", "external_email")): return "base_email"
    if f.startswith(("usb", "file_event", "unique_usb")): return "base_usb"
    if f.startswith(("http", "www")): return "base_http"
    return "base_content(domains/recipients/attachments)"


imp_all, fam_all, dir_all, cmp_all, cases = [], [], [], [], []
for h in WINDOWS:
    M = joblib.load(RES / "models" / f"final75_FINAL75_w{h}.joblib"); mdl, feats, thrD = M["model"], M["features"], M["thr_dangerous"]
    Xt = tst[feats].astype("float32").values; y = tst[f"y_{h}"].values.astype(int)
    C = mdl.booster_.predict(Xt, pred_contrib=True); V, base = C[:, :-1], C[:, -1]
    raw = mdl.predict(Xt, raw_score=True); err = float(np.abs(V.sum(1) + base - raw).max()); assert err < 1e-6, err        # additivity: sum(SHAP)+base == model log-odds
    p = mdl.predict_proba(Xt)[:, 1]; assert np.allclose(1 / (1 + np.exp(-raw)), p, atol=1e-6)
    A = np.abs(V); imp = pd.DataFrame(dict(window=h, feature=feats, family=[family(f) for f in feats], mean_abs_shap=A.mean(0), mean_abs_shap_attackrows=A[y == 1].mean(0), mean_signed_shap=V.mean(0)))
    imp["rank"] = imp.mean_abs_shap.rank(ascending=False).astype(int); imp["share"] = imp.mean_abs_shap / imp.mean_abs_shap.sum(); imp_all.append(imp)
    # grouped SHAP: |sum of the family's contributions| per row (cancellation inside a family is kept), then mean
    fam = pd.Series([family(f) for f in feats]); top = fam.map(lambda s: "accumulation_shift" if s.startswith("accumulation") else s.split("(")[0])
    for lvl, lab in ((fam, "fine"), (top, "coarse")):
        for g_ in sorted(lvl.unique()):
            cols = np.flatnonzero((lvl == g_).values); gs = V[:, cols].sum(1)
            fam_all.append(dict(window=h, level=lab, family=g_, n_features=len(cols), grouped_mean_abs=float(np.abs(gs).mean()), grouped_mean_abs_attackrows=float(np.abs(gs[y == 1]).mean()),
                                sum_of_feature_mean_abs=float(A[:, cols].mean(0).sum()), share_of_total=float(A[:, cols].mean(0).sum() / A.mean(0).sum())))
    # direction: Spearman(feature value, SHAP) on rows where the value is not NaN
    for j, f in enumerate(feats):
        ok = ~np.isnan(Xt[:, j])
        r = spearmanr(Xt[ok, j], V[ok, j])[0] if ok.sum() > 50 and np.nanstd(Xt[ok, j]) > 0 else np.nan
        dir_all.append(dict(window=h, feature=f, spearman_value_vs_shap=r, nan_share=float((~ok).mean())))
    # comparison with gain / permutation
    fw = FW[FW.window == h].set_index("feature").loc[feats]
    cm = pd.DataFrame(dict(window=h, feature=feats, shap=A.mean(0), gain_share=fw.gain_share.values, perm_drop_recall1=fw.perm_drop_recall1.values, perm_drop_prauc=fw.perm_drop_prauc.values))
    cmp_all.append(cm)
    rs = {k: spearmanr(cm.shap, cm[k])[0] for k in ("gain_share", "perm_drop_recall1", "perm_drop_prauc")}
    t10 = lambda c: set(cm.nlargest(10, c).feature); ov = {k: len(t10("shap") & t10(k)) for k in ("gain_share", "perm_drop_recall1", "perm_drop_prauc")}
    print(f"[{time.time()-t0:4.0f}s] w{h}: additivity max|err|={err:.1e} | rank corr of SHAP with gain {rs['gain_share']:.2f}, perm-Recall {rs['perm_drop_recall1']:.2f}, perm-PRAUC {rs['perm_drop_prauc']:.2f} | top-10 overlap {ov}", flush=True)
    # plots
    ex = shap.Explanation(values=V, base_values=np.full(len(V), base[0]), data=Xt, feature_names=feats)
    plt.figure(figsize=(9, 7)); shap.plots.beeswarm(ex, max_display=15, show=False); plt.title(f"SHAP beeswarm, window {h} workdays (test set, log-odds)"); plt.tight_layout(); plt.savefig(OUT / f"beeswarm_w{h}.png", dpi=160); plt.close()
    ft = pd.DataFrame([r for r in fam_all if r["window"] == h and r["level"] == "fine"]).sort_values("share_of_total")
    plt.figure(figsize=(8, 4)); plt.barh(ft.family, ft.share_of_total); plt.xlabel("share of total mean|SHAP|"); plt.title(f"SHAP by feature family, window {h}"); plt.tight_layout(); plt.savefig(OUT / f"families_w{h}.png", dpi=160); plt.close()
    # case studies at each user's peak-score day
    s = p; pk = pd.DataFrame({"user": tst.user.values, "s": s, "i": np.arange(len(s))}).sort_values("s").groupby("user").tail(1).set_index("user")
    inj = pk[[is_inj[u] for u in pk.index]]; ctl = pk[[not is_inj[u] for u in pk.index]]
    tp = inj[inj.s >= thrD].sort_values("s"); fn = inj[inj.s < thrD].sort_values("s", ascending=False); fp = ctl[ctl.s >= thrD].sort_values("s", ascending=False)
    pick = {"detected_attacker (median peak)": tp.iloc[len(tp) // 2] if len(tp) else None, "missed_attacker (highest-scoring miss)": fn.iloc[0] if len(fn) else None, "false_alarm_control (highest peak)": fp.iloc[0] if len(fp) else None}
    pickn = {"detected_attacker (median peak)": tp.index[len(tp) // 2] if len(tp) else None, "missed_attacker (highest-scoring miss)": fn.index[0] if len(fn) else None, "false_alarm_control (highest peak)": fp.index[0] if len(fp) else None}
    for k, r in pick.items():
        if r is None: continue
        i = int(r.i); order = np.argsort(-np.abs(V[i]))[:8]
        for f_i in order: cases.append(dict(window=h, case=k, user=pickn[k], day=str(tst.day.values[i])[:10], score=float(r.s), threshold=thrD, feature=feats[f_i], value=float(Xt[i, f_i]), shap=float(V[i, f_i]), base_logodds=float(base[i])))

pd.concat(imp_all).to_csv(OUT / "shap_importance.csv", index=False); pd.DataFrame(fam_all).to_csv(OUT / "shap_families.csv", index=False)
pd.DataFrame(dir_all).to_csv(OUT / "shap_direction.csv", index=False); pd.concat(cmp_all).to_csv(OUT / "shap_vs_gain_perm.csv", index=False); pd.DataFrame(cases).to_csv(OUT / "shap_cases.csv", index=False)
I = pd.concat(imp_all); pd.set_option("display.width", 220)
for h in WINDOWS: print(f"\n--- window {h}: top 12 by mean|SHAP| ---"); print(I[I.window == h].nlargest(12, "mean_abs_shap")[["feature", "family", "mean_abs_shap", "share", "mean_abs_shap_attackrows"]].round(4).to_string(index=False))
F = pd.DataFrame(fam_all); print("\n--- coarse families (share of total mean|SHAP|; grouped mean|sum|) ---"); print(F[F.level == "coarse"].pivot(index="family", columns="window", values="share_of_total").round(3).to_string())
print(F[F.level == "coarse"].pivot(index="family", columns="window", values="grouped_mean_abs").round(4).to_string())
print("\n--- fine families share ---"); print(F[F.level == "fine"].pivot(index="family", columns="window", values="share_of_total").round(3).to_string())
D = pd.DataFrame(dir_all); print("\n--- direction (Spearman value vs SHAP) for top-10 features of window 10 ---"); t = I[I.window == 10].nlargest(10, "mean_abs_shap").feature
print(D[(D.window == 10) & D.feature.isin(t)].round(3).to_string(index=False))
C_ = pd.DataFrame(cases); print("\n--- case studies, window 10 ---")
for k, g in C_[C_.window == 10].groupby("case"): print(f"\n{k}: user {g.user.iloc[0]} day {g.day.iloc[0]} score {g.score.iloc[0]:.3f} (Dangerous threshold {g.threshold.iloc[0]:.3f})"); print(g[["feature", "value", "shap"]].round(3).to_string(index=False))
print(f"\ndone {time.time()-t0:.0f}s")
