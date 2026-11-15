"""Step 24: hyper-parameter tuning of the per-window LightGBM on the FINAL 74 features.
Agreed design: objective = mean PR-AUC over 5 template-grouped inner folds on the DEV users only (test users never touched); 60 Optuna-TPE trials per window (default params enqueued as trial 0);
each window tuned separately; tuning folds use different seeds (SEED+100) from the evaluation CV (SEED+rep). Adoption rule (decided before running):
tuned params replace the default only if the standard 5x3 CV shows Recall@1%FPR >= default + 0.005 AND PR-AUC >= default. Test split is reported for both, but plays no part in the decision.
usage: python 24_tune_lightgbm.py <window>"""
import sys, json, time, numpy as np, pandas as pd, optuna, lightgbm as lgb
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import average_precision_score, roc_auc_score
from common import *
from models import fit_predict

H = int(sys.argv[1]); t0 = time.time(); optuna.logging.set_verbosity(optuna.logging.WARNING); NT = 60
df = pd.read_parquet(PREPARED).sort_values(["user", "day"]).reset_index(drop=True)
EVF = pd.read_parquet(WORK / "evidence_features.parquet"); NEWF = pd.read_parquet(WORK / "final_changed_features.parquet")
EVF = EVF.drop(columns=["user", "day"] + [c for c in NEWF.columns if c in EVF.columns]); NEWF = NEWF.drop(columns=["user", "day"]); df = pd.concat([df, EVF, NEWF], axis=1)
W3, W4 = (5, 10, 20), (5, 10, 20, 30)
BASE = (["email_event_count", "external_email_count"] + [f"external_email_count_{w}wd" for w in W4] + [f"email_active_days_{w}wd" for w in W3] + ["email_count_to_p95_ratio", "email_count_to_p90_ratio"]
        + ["usb_copy_count"] + [f"usb_copy_count_{w}wd" for w in W4] + [f"usb_active_days_{w}wd" for w in W3] + ["file_event_count", "unique_usb_files", "usb_copy_to_p95_ratio", "usb_copy_to_p90_ratio"]
        + ["http_event_count", "www_visit_count", "www_upload_count"] + [f"http_upload_count_{w}wd" for w in W4] + [f"http_active_days_{w}wd" for w in W3] + ["http_upload_to_p95_ratio", "http_upload_to_p90_ratio"]
        + ["unique_external_recipients", "unique_external_domains", "unique_upload_domains", "unique_domains", "emails_with_attachments", "attachment_count"])
ACC = [f"{n}_{w}wd" for n in ("cumulative_deviation", "consecutive_elevated_days", "channel_distribution_shift") for w in W4]
NR = [f"{n}_{w}wd" for n in ("nr_m", "nr_entropy", "nr_excl_days", "nr_overlap_days", "nr_alt", "nr_handoff", "nr_stealth_acc") for w in W3]
FINAL = BASE + ACC + NR; assert len(FINAL) == 74 and len(set(FINAL)) == 74

# same user split as step 22
sp = pd.read_csv(SPLIT).set_index("user"); users = df.user.unique(); asg = pd.read_parquet(ASSIGN).set_index("user")
meta = sp.loc[users, ["group", "stealth"]].copy(); meta["scn"] = asg.loc[users, "scenario_id"].values
strat = (meta.group + "_" + meta.stealth.astype(str)).values; scn = dict(zip(users, meta.scn.values))
tr_i, te_i = next(StratifiedGroupKFold(5, shuffle=True, random_state=SEED).split(users, strat, meta.scn.values))
dev_users, test_users = users[tr_i], users[te_i]; strat_dev = pd.Series(strat[tr_i], index=dev_users); dev_scn = np.array([scn[u] for u in dev_users])
dev = df[df.user.isin(dev_users)].reset_index(drop=True); tst = df[df.user.isin(test_users)].reset_index(drop=True)
yd = dev[f"y_{H}"].values.astype(int); yt = tst[f"y_{H}"].values.astype(int); Xd = dev[FINAL].astype("float32").values; Xt = tst[FINAL].astype("float32").values; u_dev = dev.user.values


def es_users(tr_users, rng):
    g = pd.Series(list(tr_users)).groupby([scn[u] for u in tr_users]).apply(list); need = int(0.15 * len(tr_users)); es = []
    for k in rng.permutation(len(g)):
        if len(es) >= need: break
        es += g.iloc[k]
    return set(es)


def folds(seed, rep):
    rng = np.random.default_rng(seed); out = []
    for a, b in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(dev_users, strat_dev.values, dev_scn):
        es = es_users(dev_users[a], rng); in_es = np.isin(u_dev, list(es)); tr = np.isin(u_dev, dev_users[a]) & ~in_es; va = np.isin(u_dev, dev_users[b]); out.append((tr, in_es, va))
    return out


DEFAULT = dict(learning_rate=0.05, num_leaves=31, max_depth=-1, min_child_samples=50, subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, reg_alpha=0.0, min_split_gain=0.0)


def fit(P, tr, es, seed):
    m = lgb.LGBMClassifier(n_estimators=2000, subsample_freq=1, n_jobs=2, random_state=seed, verbose=-1, **P)
    m.fit(Xd[tr], yd[tr], eval_set=[(Xd[es], yd[es])], eval_metric="average_precision", callbacks=[lgb.early_stopping(30, verbose=False)])
    return m


TUNE_FOLDS = folds(SEED + 100, 0)


def objective(trial):
    P = dict(learning_rate=trial.suggest_float("learning_rate", 0.02, 0.1, log=True), num_leaves=trial.suggest_int("num_leaves", 8, 128, log=True),
             max_depth=trial.suggest_categorical("max_depth", [-1, 4, 6, 8, 12]), min_child_samples=trial.suggest_int("min_child_samples", 10, 300, log=True),
             subsample=trial.suggest_float("subsample", 0.5, 1.0), colsample_bytree=trial.suggest_float("colsample_bytree", 0.3, 1.0),
             reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 50, log=True), reg_alpha=trial.suggest_float("reg_alpha", 0.0, 10.0), min_split_gain=trial.suggest_float("min_split_gain", 0.0, 0.5))
    sc = []
    for tr, es, va in TUNE_FOLDS:
        m = fit(P, tr, es, SEED); sc.append(average_precision_score(yd[va], m.predict_proba(Xd[va])[:, 1]))
    trial.set_user_attr("std", float(np.std(sc))); return float(np.mean(sc))


st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED)); st.enqueue_trial(dict(DEFAULT))
def cb(s, t):
    if t.number % 10 == 9 or t.number == 0: print(f"[{time.time()-t0:5.0f}s] h={H} trial {t.number+1}/{NT} best PR-AUC {s.best_value:.4f} (trial {s.best_trial.number}) | this {t.value:.4f}", flush=True)
st.optimize(objective, n_trials=NT, callbacks=[cb])
df_trials = st.trials_dataframe(); df_trials.to_csv(RES / f"tune_lgbm_w{H}_trials.csv", index=False)
BEST = {k: st.best_params[k] for k in DEFAULT}; d0 = st.trials[0].value
print(f"h={H} default tuning-CV PR-AUC {d0:.4f} | best {st.best_value:.4f} | params {BEST}", flush=True)
print("top-5 trials:", df_trials.sort_values("value", ascending=False).head(5)[["number", "value"] + [c for c in df_trials if c.startswith("params_")]].round(4).to_string(index=False), flush=True)

# ---------------- independent evaluation: the SAME 5x3 CV as every earlier comparison (seeds SEED+rep), default vs tuned
rows = []; oof = {}; iters = {}
for name, P in (("default", DEFAULT), ("tuned", BEST)):
    its = []
    for rep in range(3):
        o = np.full(len(dev), np.nan)
        for k, (tr, es, va) in enumerate(folds(SEED + rep, rep)):
            m = fit(P, tr, es, SEED + rep); s = m.predict_proba(Xd[va])[:, 1]; o[va] = s; its.append(m.best_iteration_ or 2000)
            r = row_metrics(yd[va], s); r.update(variant=name, rep=rep, fold=k, kind="fold"); rows.append(r)
        r = row_metrics(yd, o); r.update(variant=name, rep=rep, fold=-1, kind="pooled"); rows.append(r)
    iters[name] = int(np.mean(its))
cv = pd.DataFrame(rows); cv.to_csv(RES / f"tune_lgbm_w{H}_cv.csv", index=False)
pool = cv[cv.kind == "pooled"].groupby("variant")[["pr_auc", "roc_auc", "rec_fpr1", "rec_fpr5", "brier"]].mean(); print(pool.round(4).to_string(), flush=True)
fo = cv[cv.kind == "fold"].pivot_table(index=["rep", "fold"], columns="variant", values=["pr_auc", "rec_fpr1"]); dd = fo["rec_fpr1"]["tuned"] - fo["rec_fpr1"]["default"]; dp = fo["pr_auc"]["tuned"] - fo["pr_auc"]["default"]
gain_r1 = float(pool.loc["tuned", "rec_fpr1"] - pool.loc["default", "rec_fpr1"]); gain_pr = float(pool.loc["tuned", "pr_auc"] - pool.loc["default", "pr_auc"])
adopt = bool(gain_r1 >= 0.005 and gain_pr >= 0)
print(f"h={H} CV gain: Recall@1% {gain_r1:+.4f} (folds: mean {dd.mean():+.4f} sd {dd.std():.4f}, tuned wins {(dd>0).sum()}/15) | PR-AUC {gain_pr:+.4f} (wins {(dp>0).sum()}/15) -> ADOPT={adopt}", flush=True)
# ---------------- test (reported for both; not used in the decision)
out = dict(window=H, adopt=adopt, best=BEST, default=DEFAULT, iters=iters, cv_gain_rec1=gain_r1, cv_gain_prauc=gain_pr)
for name, P in (("default", DEFAULT), ("tuned", BEST)):
    m = lgb.LGBMClassifier(n_estimators=max(iters[name], 20), subsample_freq=1, n_jobs=2, random_state=SEED, verbose=-1, **P).fit(Xd, yd); s = m.predict_proba(Xt)[:, 1]
    r = row_metrics(yt, s); out[f"test_{name}"] = {k: float(v) for k, v in r.items() if isinstance(v, (int, float, np.floating))}
    print(f"h={H} TEST {name}: PR-AUC {r['pr_auc']:.4f} ROC {r['roc_auc']:.4f} R@1% {r['rec_fpr1']:.4f} R@5% {r['rec_fpr5']:.4f} Brier {r['brier']:.4f}", flush=True)
json.dump(out, open(RES / f"tune_lgbm_w{H}.json", "w"), indent=1); print("done", flush=True)
