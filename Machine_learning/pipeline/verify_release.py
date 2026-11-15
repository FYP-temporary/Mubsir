"""Release verification that needs the training data (pipeline/data/). Run from pipeline/:  python verify_release.py
Checks: (1) data file integrity, (2) split integrity / no leakage, (3) no label or ground-truth column among the model inputs,
(4) saved sklearn models == native boosters, (5) bundle confusion matrices re-derived from scratch == stored tables, (6) calibration/band sanity.
Exit code 0 only if every check passes."""
import hashlib, json, sys
import numpy as np, pandas as pd, joblib
from common import *
src = open("28_final75.py").read(); exec(src.split("def es_users")[0])            # df, F75, tst, dev_users, test_users, is_inj, scn ...
sys.path.insert(0, str(MODEL)); from mubsir_infer import MubsirScorer

ok_all = True
def check(name, cond, detail=""):
    global ok_all; ok_all &= bool(cond); print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  | {detail}" if detail else ""), flush=True)

# 1 -- data integrity
sums = PKG / "data" / "SHA256SUMS.txt"
if sums.exists():
    bad = []
    for line in sums.read_text().splitlines():
        h, p = line.split(None, 1); p = p.strip(); head, rest = p.split("/", 1)
        f = ROOT / rest if head == "Clear_Attack_Simulation" else WORK / rest if head == "work" else PKG / "data" / p      # resolves wherever the data actually lives
        if hashlib.sha256(f.read_bytes()).hexdigest() != h: bad.append(p)
    check("data files match SHA256SUMS.txt", not bad, f"{len(sums.read_text().splitlines())} files" if not bad else f"mismatch: {bad}")

# 2 -- split integrity
sp = pd.read_csv(SPLIT).set_index("user"); asg = pd.read_parquet(ASSIGN).set_index("user")
dev_set, test_set = set(dev_users), set(test_users)
check("dev/test users are disjoint", not (dev_set & test_set), f"dev {len(dev_set)} / test {len(test_set)}")
check("dev+test = 995 users", len(dev_set | test_set) == 995 == len(sp))
fs = pd.read_csv(RES / "final_split.csv").set_index("user")
check("derived split == saved results/final_split.csv", test_set == set(fs.index[fs.part == "test"]) and dev_set == set(fs.index[fs.part == "dev"]))
legacy = set(sp.index[sp.part == "test"]); print(f"[INFO] legacy user_split.csv `part` (02_split.py, not used by the final pipeline) overlaps the real test set in {len(legacy & test_set)}/199 users")
sd, st = {scn[u] for u in dev_set if is_inj[u]}, {scn[u] for u in test_set if is_inj[u]}
check("no attack scenario (template) shared between dev and test", not (sd & st), f"{len(sd)} dev scenarios / {len(st)} test scenarios")
check("test composition 134 injected / 65 controls", sum(is_inj[u] for u in test_set) == 134 and sum(not is_inj[u] for u in test_set) == 65)
dk = set(map(tuple, dev[["user", "day"]].values)) if "dev" in globals() else set(); tk = set(map(tuple, tst[["user", "day"]].values))
check("no (user, day) pair shared between dev and test", not (dk & tk), f"dev {len(dk)} / test {len(tk)} user-days")

# 3 -- model inputs
sc = MubsirScorer(MODEL); man = sc.man; used = set(man["input_columns_all"])
gt_cols = set(pd.read_parquet(GT_USER_DAYS).columns) | set(pd.read_parquet(GT_USERS).columns) | {"y", "group", "stealth", "scenario_id", "part"} | {f"y_{h}" for h in WINDOWS} | {f"yf_{h}" for h in WINDOWS}
check("no label / ground-truth column among the 77 model inputs", not (used & gt_cols), str(sorted(used & gt_cols)) if used & gt_cols else f"{len(used)} inputs vs {len(gt_cols)} forbidden names")
check("no per-user static baseline column among the inputs", not (used & set(STATIC)))
for h in WINDOWS: check(f"window {h}: manifest feature list == training F75({h})", man["windows"][str(h)]["features"] == F75(h))

# 4 -- saved sklearn model == native booster == bundle
rows = sc.score(tst[["user", "day"] + man["input_columns_all"]]); assert (rows.user.values == tst.user.values).all()
for h in WINDOWS:
    M = joblib.load(RES / "models" / f"final75_FINAL75_w{h}.joblib"); Xt = tst[M["features"]].astype("float32").values
    d = np.abs(M["model"].predict_proba(Xt)[:, 1] - rows[f"score_raw_{h}"].values).max()
    check(f"window {h}: joblib model == bundle booster on {len(tst)} test rows", d < 1e-12, f"max |diff| = {d:.2e}")

# 5 -- confusion matrices re-derived from scratch vs stored tables
stored_u = pd.read_csv(RES / "fixed_bands_users.csv"); stored_r = pd.read_csv(RES / "fixed_bands_rows.csv")
for tab in (stored_u, stored_r): tab["window"] = tab["window"].astype(str)
cm = lambda pos, y: (int((pos & (y == 1)).sum()), int((~pos & (y == 1)).sum()), int((pos & (y == 0)).sum()), int((~pos & (y == 0)).sum()))   # TP FN FP TN
pk = {h: rows.groupby("user")[f"risk_{h}"].max() for h in WINDOWS}; pk["any"] = pd.concat([pk[h] for h in WINDOWS], axis=1).max(axis=1)
inj = lambda idx: np.array([int(is_inj[u]) for u in idx])
print("\nUSER LEVEL (peak risk; positive = High > 85) - recomputed vs stored")
for w in [5, 10, 20, "any"]:
    for name, thr, lab in (("High", 85, "High (>85)"), ("Medium+High", 60, "Medium or High (>60)")):
        mine = cm((pk[w] > thr).values, inj(pk[w].index)); r = stored_u[(stored_u.model == "LightGBM-75") & (stored_u.window == str(w)) & (stored_u.positive == lab)].iloc[0]
        check(f"user level | window {w} | {name}: TP/FN/FP/TN = {mine}", mine == (r.TP, r.FN, r.FP, r.TN), f"recall {mine[0]/(mine[0]+mine[1]):.3f} precision {mine[0]/max(mine[0]+mine[2],1):.3f} FPR {mine[2]/(mine[2]+mine[3]):.4f}")
print("\nROW LEVEL (user-workday vs y_h) - recomputed vs stored")
for h in WINDOWS:
    y = tst[f"y_{h}"].values.astype(int)
    for name, thr, lab in (("High", 85, "High (>85)"), ("Medium+High", 60, "Medium or High (>60)")):
        mine = cm(rows[f"risk_{h}"].values > thr, y); r = stored_r[(stored_r.model == "LightGBM-75") & (stored_r.window == str(h)) & (stored_r.positive == lab)].iloc[0]
        check(f"row level | window {h} | {name}: TP/FN/FP/TN = {mine}", mine == (r.TP, r.FN, r.FP, r.TN))

# 6 -- calibration / band sanity (test)
print("\nBAND CONTENT (test rows, window 10)")
r10 = rows.risk_10.values; y10 = tst["y_10"].values.astype(int)
for b, m in (("Low", r10 <= 60), ("Medium", (r10 > 60) & (r10 <= 85)), ("High", r10 > 85)): print(f"   {b:6s} {m.mean():6.1%} of rows | attack rate {y10[m].mean():.3f}")
rate = [y10[(r10 <= 60)].mean(), y10[(r10 > 60) & (r10 <= 85)].mean(), y10[r10 > 85].mean()]
check("attack rate increases Low < Medium < High", rate[0] < rate[1] < rate[2])
print("\nALL CHECKS PASSED" if ok_all else "\nSOME CHECKS FAILED"); sys.exit(0 if ok_all else 1)
