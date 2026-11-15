"""Step 1: filter ML-final to the 995 pool, build window labels y_5/y_10/y_20 (ongoing attack in the last h workdays)."""
import numpy as np, pandas as pd
from common import *

ml = pd.read_parquet(ML_FINAL)
pool = pd.read_csv(POOL)
gu = pd.read_parquet(GT_USERS)
ud = pd.read_parquet(GT_USER_DAYS, columns=["user", "day", "is_attack_day"])

df = ml[ml.user.isin(pool.user)].merge(pool, on="user", how="left")
df = df.merge(gu[["user", "stealth_level", "scenario_id"]].rename(columns={"stealth_level": "stealth"}), on="user", how="left")
df["stealth"] = df["stealth"].fillna("control")
df = df.sort_values(["user", "day"]).reset_index(drop=True)

# --- check daily y against ground truth is_attack_day
chk = df[["user", "day", "y"]].merge(ud, on=["user", "day"], how="left")
assert chk.is_attack_day.notna().sum() == (df.group == "injected").sum(), "GT day coverage mismatch"
m = chk.dropna(subset=["is_attack_day"])
assert (m.y.values == m.is_attack_day.values).all(), "y != GT is_attack_day"
assert df.loc[df.group == "control", "y"].sum() == 0
print("daily y == GT is_attack_day on all injected rows: OK")

# --- window labels.  FINAL definition (user decision): ONGOING attack in the LAST h workdays, including day t:
#     y_h(t) = 1 iff any daily attack day occurs in workdays t-h+1 .. t   (rows of the user in ml_final).
#     Early rows use the shorter available history (no attack exists before the data starts). All rows are valid.
#     The previous forward-looking label (t .. t+h-1) is kept as yf_h for reference only.
g = df.groupby("user", sort=False)
c = g["y"].cumsum()
for h in WINDOWS:
    back = c - c.groupby(df["user"]).shift(h).fillna(0)          # sum of y over rows i-h+1..i
    df[f"y_{h}"] = (back > 0).astype(float)
    endf = c.groupby(df["user"]).shift(-(h - 1)); prev = c - df["y"]
    validf = g.cumcount(ascending=False) >= (h - 1)
    df[f"yf_{h}"] = np.where(validf, ((endf - prev) > 0).astype(float), np.nan)
    print(f"y_{h} (backward): rows {len(df):,}  positives {int(df[f'y_{h}'].sum()):,}  rate {df[f'y_{h}'].mean():.3f}   | old forward yf_{h} rate {np.nanmean(df[f'yf_{h}']):.3f}")

# --- brute-force verification on a random sample of users
rng = np.random.default_rng(0)
for u in rng.choice(df.user.unique(), 60, replace=False):
    d = df[df.user == u]; yy = d.y.values
    for h in WINDOWS:
        exp = np.array([yy[max(0, i - h + 1):i + 1].max() for i in range(len(yy))])
        assert np.array_equal(exp, d[f"y_{h}"].values), (u, h)
print("backward window labels verified against brute force on 60 users: OK")
# --- sanity: positives are only attack days or the h-1 days following them; none before attack start
inj = df[df.group == "injected"]
a0 = pd.to_datetime(inj.user.map(gu.set_index("user").attack_start))
for h in WINDOWS:
    assert (inj.loc[inj[f"y_{h}"] == 1, "day"] >= a0[inj[f"y_{h}"] == 1]).all()
assert (df.loc[df.group == "control", [f"y_{h}" for h in WINDOWS]].values == 0).all()
print("no positives before attack start; controls all 0: OK")

df.to_parquet(PREPARED, index=False)
print(df.shape, df.user.nunique(), df.group.value_counts().to_dict())
print("features(all/no-static):", len(feature_cols(df)), len(feature_cols(df, False)))
