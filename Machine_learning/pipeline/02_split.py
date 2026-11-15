# LEGACY split (random, stratified by user). The final pipeline does NOT use its `part`/`rep*` columns: 22/28/31/33 build a scenario-grouped split in code;
# see 34_save_final_split.py -> results/final_split.csv. Only `group`/`stealth` from this file are still read by later scripts.
"""Step 2: user-level split. 20% final test (stratified by group x stealth); remaining 796 users
get 5-fold x 3-repeat stratified CV assignments. Whole users only -> no user ever in two parts."""
import pandas as pd, numpy as np
from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold
from common import *

df = pd.read_parquet(PREPARED, columns=["user", "group", "stealth", "scenario_id"]).drop_duplicates("user")
df["stratum"] = np.where(df.group == "control", "control", "inj_" + df.stealth)
dev, test = train_test_split(df, test_size=0.20, stratify=df.stratum, random_state=SEED)
df["part"] = np.where(df.user.isin(test.user), "test", "dev")
dev = df[df.part == "dev"].reset_index(drop=True)
rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
for i, (_, va) in enumerate(rskf.split(dev, dev.stratum)):
    dev.loc[va, f"rep{i // 5}"] = i % 5
out = df.merge(dev[["user"] + [f"rep{r}" for r in range(3)]], on="user", how="left")
out.to_csv(SPLIT, index=False)

# ---- assertions
assert out.user.is_unique and len(out) == 995
t = out[out.part == "test"]; d = out[out.part == "dev"]
assert set(t.user).isdisjoint(d.user)
for r in range(3):
    assert d[f"rep{r}"].notna().all() and d[f"rep{r}"].nunique() == 5
print(out.groupby(["part", "group"]).size().unstack())
print(out.groupby(["part", "stratum"]).size().unstack())
print("fold sizes rep0:", d.groupby("rep0").size().to_dict())
print(d.groupby(["rep0", "group"]).size().unstack())
