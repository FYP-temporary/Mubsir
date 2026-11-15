"""Step 34: save the dev/test split that the FINAL pipeline actually uses (it is defined in code in 28_final75.py / 22 / 31 / 33, not read from a file).
Split = StratifiedGroupKFold(5, shuffle, seed 42), FIRST fold = test; groups = attack scenario (template) id; stratified by group x stealth level.
Output: results/final_split.csv (user, part, group, stealth, scenario_id). NOTE: results/user_split.csv `part`/`rep*` columns come from the LEGACY 02_split.py (random split) and are NOT this split."""
from common import *
src = open("28_final75.py").read(); exec(src.split("def es_users")[0])
out = pd.DataFrame(dict(user=users, part=np.where(np.isin(users, test_users), "test", "dev"), group=meta.group.values, stealth=meta.stealth.values, scenario_id=meta.scn.values))
out.to_csv(RES / "final_split.csv", index=False)
print(out.groupby(["part", "group"]).size().unstack(), "\nsaved", RES / "final_split.csv")
