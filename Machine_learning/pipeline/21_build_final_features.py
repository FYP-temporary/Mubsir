"""Step 21: features whose definition was changed/added in the final feature agreement (causal, warm-started from 2010 like step 18).
 nr_alt_{w}wd        : switches of the dominant channel between CONSECUTIVE workdays (d-1,d) that both have a deviation, / number of such valid consecutive pairs inside the window; 0 if no valid pair.
                       No compression of quiet days, no transition across a quiet day.
 nr_alt_pairs_{w}wd  : the valid-pair count itself (diagnostic, NOT used unless requested).
 nr_stealth_acc_{w}wd: per-channel independent: sum over window days and channels c with E_c>0 and x_c <= P95_c of E_c  (a channel exceeding P95 only removes itself).
 *_to_p90_ratio      : external_email_count/email_count_p90, usb_copy_count/usb_copy_p90, www_upload_count/http_upload_p90 ; NaN when p90 missing or <=0 (same rule as the p95 ratios).
"""
import time, numpy as np, pandas as pd
from common import *

t0 = time.time(); WS = (5, 10, 20)
df = pd.read_parquet(PREPARED).sort_values(["user", "day"]).reset_index(drop=True)
users = df.user.unique()
ud = pd.read_parquet(GT_USER_DAYS.parent.parent / "final" / "user_day_injected_r62.parquet", columns=["user", "day", "is_weekend", "logon_count", "external_email_count", "usb_copy_count", "www_upload_count"])
ud["day"] = pd.to_datetime(ud.day); ud = ud[ud.user.isin(users)]
ud10 = ud[(ud.day < "2011-01-01") & (ud.is_weekend == 0) & (ud.logon_count > 0)].sort_values(["user", "day"])
CH = [("external_email_count", "email_count_p50", "email_count_p95"), ("usb_copy_count", "usb_copy_p50", "usb_copy_p95"), ("www_upload_count", "http_upload_p50", "http_upload_p95")]
cols = {f"{n}_{w}wd": np.full(len(df), np.nan) for w in WS for n in ("nr_alt", "nr_alt_pairs", "nr_stealth_acc")}
uidx = df.groupby("user").indices; u10 = {u: g for u, g in ud10.groupby("user")}


def window_features(X, p50, p95, n10):
    """returns dict[w] -> (alt, pairs, stealth) arrays over all n days (valid from index w-1)"""
    E = np.nan_to_num(np.clip(X - p50, 0, None) / np.maximum(1, p95 - p50)); tot = E.sum(1); dev = tot > 0
    dom = np.where(dev, E.argmax(1), -1)
    stl = (E * (np.nan_to_num(X) <= p95)).sum(1)                       # per-channel independent
    n = len(X); valid = np.zeros(n); sw = np.zeros(n)
    for d in range(1, n):
        if dev[d] and dev[d - 1]: valid[d] = 1; sw[d] = float(dom[d] != dom[d - 1])
    cs = lambda v: np.concatenate([[0.0], np.cumsum(v)]); cV, cS, cT = cs(valid), cs(sw), cs(stl)
    out = {}
    for w in WS:
        t = np.arange(n); lo = np.maximum(t - w + 2, 1)             # pairs (d-1,d) with both days inside the window  -> d in [t-w+2, t]
        v = cV[t + 1] - cV[lo]; s = cS[t + 1] - cS[lo]; v = np.where(t - w + 2 > t, 0, v); s = np.where(t - w + 2 > t, 0, s)
        out[w] = (np.where(v > 0, s / np.maximum(v, 1), 0.0), v, cT[t + 1] - cT[np.maximum(t + 1 - w, 0)])
    return out


for k, u in enumerate(users):
    ix = uidx[u]; d11 = df.iloc[ix]; g10 = u10[u]; n10 = len(g10)
    X = np.vstack([g10[[c[0] for c in CH]].to_numpy(float), d11[[c[0] for c in CH]].to_numpy(float)])
    p50 = d11[[c[1] for c in CH]].iloc[0].to_numpy(float); p95 = d11[[c[2] for c in CH]].iloc[0].to_numpy(float)
    res = window_features(X, p50, p95, n10)
    for w in WS:
        a, v, s = res[w]; cols[f"nr_alt_{w}wd"][ix] = a[n10:]; cols[f"nr_alt_pairs_{w}wd"][ix] = v[n10:]; cols[f"nr_stealth_acc_{w}wd"][ix] = s[n10:]
    if k % 250 == 0: print(f"[{time.time()-t0:4.0f}s] users {k}/{len(users)}", flush=True)
NEW = pd.DataFrame(cols)
for nm, x, p in (("email_count_to_p90_ratio", "external_email_count", "email_count_p90"), ("usb_copy_to_p90_ratio", "usb_copy_count", "usb_copy_p90"), ("http_upload_to_p90_ratio", "www_upload_count", "http_upload_p90")):
    NEW[nm] = np.where(df[p].values > 0, df[x].values / np.where(df[p].values > 0, df[p].values, 1), np.nan)

# ---------------- brute-force verification on a sample of users (plain loops, definition written literally)
rng = np.random.default_rng(0); bad = 0; chk = 0
for u in rng.choice(users, 25, replace=False):
    ix = uidx[u]; d11 = df.iloc[ix]; g10 = u10[u]; n10 = len(g10)
    X = np.vstack([g10[[c[0] for c in CH]].to_numpy(float), d11[[c[0] for c in CH]].to_numpy(float)])
    p50 = d11[[c[1] for c in CH]].iloc[0].to_numpy(float); p95 = d11[[c[2] for c in CH]].iloc[0].to_numpy(float)
    for w in WS:
        for j in range(len(ix)):
            t = n10 + j; days = range(t - w + 1, t + 1); sw = pr = 0; st = 0.0
            def Ec(d): return np.nan_to_num(np.clip(X[d] - p50, 0, None) / np.maximum(1, p95 - p50))
            for d in days:
                e = Ec(d)
                for c in range(3):
                    if e[c] > 0 and np.nan_to_num(X[d, c]) <= p95[c]: st += e[c]
                if d - 1 in days:
                    e0 = Ec(d - 1)
                    if e.sum() > 0 and e0.sum() > 0: pr += 1; sw += int(e.argmax() != e0.argmax())
            alt = sw / pr if pr else 0.0; chk += 1
            if not (np.isclose(alt, cols[f"nr_alt_{w}wd"][ix[j]]) and np.isclose(st, cols[f"nr_stealth_acc_{w}wd"][ix[j]]) and pr == cols[f"nr_alt_pairs_{w}wd"][ix[j]]): bad += 1
print(f"brute-force check: {chk} (user,day,window) cells, mismatches = {bad}")
print(NEW.describe().T[["count", "mean", "min", "max"]].round(3).to_string())
print("zero share nr_alt:", {w: round(float((NEW[f'nr_alt_{w}wd'] == 0).mean()), 3) for w in WS}, "| NaN share p90 ratios:", NEW[[c for c in NEW if 'p90' in c]].isna().mean().round(3).to_dict())
assert bad == 0
pd.concat([df[["user", "day"]], NEW], axis=1).to_parquet(WORK / "final_changed_features.parquet", index=False); print(f"saved in {time.time()-t0:.0f}s")
