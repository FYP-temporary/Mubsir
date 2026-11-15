"""Step 18: build the three-evidence feature set for channel-rotating low-and-slow detection (causal, warm-started from 2010).
Series per user = 2010 workdays (user_day_injected, weekday & logon_count>0)  +  2011 rows of ml_final.  Features only for the 2011 rows.
Per channel c in {email, usb, http}: E_c(d)=max(0,x_c-P50_c)/max(1,P95_c-P50_c);  S_c(W)=sum of E_c over the last w workdays;
surprisal s_c(d) = -ln((#{2010 workdays with x_c >= x_c(d)}+1)/(n2010+1))  (0 when x_c(d)=0)  -- ECDF-based rarity vs the user's own 2010 history.
T_* = per-user 95th percentile (floor 1.0) of the same rolling quantity over 2010 = the user's OWN alarm level for that window.
EVIDENCE 1 (abnormal accumulation):   e1_excess_sum, e1_surprisal_sum, e1_excess_alarm=S_tot/T_tot, e1_surprisal_alarm
EVIDENCE 2 (evasion of per-channel thresholds): e2_max_ch_alarm=max_c S_c/T_c, e2_evasion_gap=e1_excess_alarm-e2_max_ch_alarm,
        e2_evasion_ratio=S_tot/max_c S_c, e2_subthr_share=stealth_acc/S_tot, e2_ch_below_alarm=#{c: 0<S_c/T_c<1}, nr_stealth_acc
EVIDENCE 3 (rotation pattern): nr_m, nr_entropy, nr_excl_days, nr_overlap_days, nr_alt, nr_handoff   (+ team's channel_distribution_shift)"""
import time, numpy as np, pandas as pd
from common import *

t0 = time.time(); WS = (5, 10, 20)
df = pd.read_parquet(PREPARED).sort_values(["user", "day"]).reset_index(drop=True)
users = df.user.unique()
ud = pd.read_parquet(GT_USER_DAYS.parent.parent / "final" / "user_day_injected_r62.parquet",
                     columns=["user", "day", "is_weekend", "logon_count", "external_email_count", "usb_copy_count", "www_upload_count"])
ud["day"] = pd.to_datetime(ud.day); ud = ud[ud.user.isin(users)]
chk = ud[(ud.day >= "2011-01-01") & (ud.is_weekend == 0) & (ud.logon_count > 0)]
print(f"2011 workday rows in user_day for the pool: {len(chk)} | rows in ml_final (prepared): {len(df)}", flush=True)
ud10 = ud[(ud.day < "2011-01-01") & (ud.is_weekend == 0) & (ud.logon_count > 0)].sort_values(["user", "day"])
CH = [("external_email_count", "email_count_p50", "email_count_p95"), ("usb_copy_count", "usb_copy_p50", "usb_copy_p95"), ("www_upload_count", "http_upload_p50", "http_upload_p95")]
cols = {}
for w in WS:
    for n in ("e1_excess_sum", "e1_surprisal_sum", "e1_excess_alarm", "e1_surprisal_alarm", "e2_max_ch_alarm", "e2_evasion_gap", "e2_evasion_ratio", "e2_subthr_share", "e2_ch_below_alarm",
              "nr_stealth_acc", "nr_m", "nr_entropy", "nr_excl_days", "nr_overlap_days", "nr_alt", "nr_handoff"):
        cols[f"{n}_{w}wd"] = np.full(len(df), np.nan)
uidx = df.groupby("user").indices; u10 = {u: g for u, g in ud10.groupby("user")}


def roll(cs, t, w): return cs[t + 1] - cs[t + 1 - w]


for k, u in enumerate(users):
    ix = uidx[u]; d11 = df.iloc[ix]; g10 = u10[u]; n10 = len(g10); n = n10 + len(ix)
    X = np.vstack([g10[[c[0] for c in CH]].to_numpy(float), d11[[c[0] for c in CH]].to_numpy(float)])
    p50 = d11[[c[1] for c in CH]].iloc[0].to_numpy(float); p95 = d11[[c[2] for c in CH]].iloc[0].to_numpy(float)
    E = np.nan_to_num(np.clip(X - p50, 0, None) / np.maximum(1, p95 - p50)); tot = E.sum(1); hasE = E > 0; nexc = hasE.sum(1)
    over = np.nan_to_num((X > p95).astype(float)) > 0; stealth_day = (~over.any(1)) & (tot > 0); sval = tot * stealth_day
    dom = np.where(tot > 0, E.argmax(1), -1)
    # ECDF surprisal vs the user's own 2010 history
    SS = np.zeros_like(X)
    for c in range(3):
        a = np.sort(X[:n10, c]); cnt = n10 - np.searchsorted(a, X[:, c], side="left"); SS[:, c] = np.where(X[:, c] > 0, -np.log((cnt + 1) / (n10 + 1)), 0.0)
    sst = SS.sum(1)
    hand = np.zeros(n)
    for d in range(1, n):
        if hasE[d - 1].any(): hand[d] = (hasE[d] & ~hasE[d - 1]).sum()
    cs = lambda v: np.concatenate([[0.0], np.cumsum(v, axis=0)]) if v.ndim == 1 else np.vstack([np.zeros((1, v.shape[1])), np.cumsum(v, axis=0)])
    cE, cT, cSS, cStl, cEx, cOv, cH = cs(E), cs(tot), cs(sst), cs(sval), cs((nexc == 1).astype(float)), cs((nexc >= 2).astype(float)), cs(hand)
    for w in WS:
        # user's own alarm levels from the 2010 rolling distribution
        idx10 = np.arange(w - 1, n10)
        Tc = np.maximum(np.percentile(cE[idx10 + 1] - cE[idx10 + 1 - w], 95, axis=0), 1.0)
        Tt = max(np.percentile(cT[idx10 + 1] - cT[idx10 + 1 - w], 95), 1.0); Ts = max(np.percentile(cSS[idx10 + 1] - cSS[idx10 + 1 - w], 95), 1.0)
        for j, t in enumerate(range(n10, n)):
            i = ix[j]; Sc = roll(cE, t, w); St = Sc.sum(); Sss = roll(cSS, t, w); stl = roll(cStl, t, w)
            cols[f"e1_excess_sum_{w}wd"][i] = St; cols[f"e1_surprisal_sum_{w}wd"][i] = Sss
            ea = St / Tt; cols[f"e1_excess_alarm_{w}wd"][i] = ea; cols[f"e1_surprisal_alarm_{w}wd"][i] = Sss / Ts
            ca = Sc / Tc; mx = ca.max(); cols[f"e2_max_ch_alarm_{w}wd"][i] = mx; cols[f"e2_evasion_gap_{w}wd"][i] = ea - mx
            cols[f"e2_evasion_ratio_{w}wd"][i] = St / Sc.max() if St > 0 else 0.0
            cols[f"e2_subthr_share_{w}wd"][i] = stl / St if St > 0 else 0.0
            cols[f"e2_ch_below_alarm_{w}wd"][i] = ((ca > 0) & (ca < 1)).sum(); cols[f"nr_stealth_acc_{w}wd"][i] = stl
            cols[f"nr_m_{w}wd"][i] = (Sc > 0).sum()
            if St > 0:
                p = Sc / St; pp = p[p > 0]; cols[f"nr_entropy_{w}wd"][i] = -(pp * np.log(pp)).sum() / np.log(3)
            else: cols[f"nr_entropy_{w}wd"][i] = 0.0
            cols[f"nr_excl_days_{w}wd"][i] = roll(cEx, t, w); cols[f"nr_overlap_days_{w}wd"][i] = roll(cOv, t, w); cols[f"nr_handoff_{w}wd"][i] = roll(cH, t, w)
            lab = dom[t + 1 - w:t + 1]; lab = lab[lab >= 0]
            cols[f"nr_alt_{w}wd"][i] = (lab[1:] != lab[:-1]).sum() / (len(lab) - 1) if len(lab) > 1 else 0.0
    if k % 200 == 0: print(f"[{time.time()-t0:4.0f}s] users {k}/{len(users)}", flush=True)
EV = pd.DataFrame(cols); out = pd.concat([df[["user", "day"]], EV], axis=1)
# ---- sanity checks against earlier independent computations
ref = pd.read_parquet(WORK / "new_rotation_features.parquet")   # built on 2011-only windows, same sorted order
for w in WS:
    for n in ("nr_m", "nr_entropy", "nr_excl_days", "nr_overlap_days", "nr_alt", "nr_stealth_acc"):
        a, b = EV[f"{n}_{w}wd"].values, ref[f"{n}_{w}wd"].values; m = ~np.isnan(b)
        print(f"check {n}_{w}wd vs earlier (rows with full 2011-only window): {m.sum()} rows, share equal {np.isclose(a[m], b[m], atol=1e-6).mean():.4f}")
for w in WS:
    a, b = EV[f"e1_excess_sum_{w}wd"].values, df[f"cumulative_deviation_{w}wd"].values; m = ~np.isnan(b)
    print(f"check e1_excess_sum_{w}wd vs team's cumulative_deviation_{w}wd: share equal {np.isclose(a[m], b[m], atol=1e-6).mean():.4f}; corr {np.corrcoef(a[m], b[m])[0,1]:.4f}")
print("NaN share in new features:", float(EV.isna().mean().max()))
out.to_parquet(WORK / "evidence_features.parquet", index=False); print(f"saved {EV.shape[1]} features in {time.time()-t0:.0f}s")
