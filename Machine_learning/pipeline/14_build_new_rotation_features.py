# Step 14b: BUILDER ONLY, extracted verbatim (lines 1-73) from 14_new_rotation_features.py; the evaluation half of that script is archived. Output feeds 18_build_evidence_features.py.
"""Step 14: NEW channel-rotation features, built causally from the daily per-channel counts and the 2010 baseline (P50/P95),
then trained/evaluated with the same protocol (LightGBM, user-grouped 5-fold x3 CV + held-out test).

Per channel c: excess E_c(d)=max(0,x_c(d)-P50_c)/max(1,P95_c-P50_c).  Over_c(d)=1[x_c(d)>P95_c].  Window W_t = last w workdays incl. t.
New features per w in {5,10,20,30} (prefix nr_):
  m            = #channels with positive total excess in W_t                              (windowed channel count m_W)
  share_max    = max_c S_c / sum S,  S_c=sum_{d in W_t} E_c(d)                            (concentration; 1 = single channel)
  entropy      = -sum p_c log p_c / log 3, p_c=S_c/sum S                                  (spread of the excess over channels)
  balance      = min_c S_c / max_c S_c                                                    (how evenly the channels share the load)
  sw           = #changes of the excess-dominant channel (argmax_c E_c) between consecutive excess days   (R_u on excess)
  alt          = sw / (#excess days - 1)                                                  (alternation rate)
  maxrun       = longest run of days with the same dominant channel                       (low = frequent rotation)
  excl_days    = #days with excess on exactly one channel; overlap_days = #days with >=2 channels
  handoff      = #times a channel becomes excess today that was not excess yesterday while another channel was   (lag-1 cross-channel hand-off)
  stealth_acc  = sum of total excess on days where NO channel exceeded its own P95        (sub-threshold accumulation)
  stealth_days = #such days
Experiments: D=core+X (reference, no R) | N1=D+NEW | N2=core+NEW (no X) | N3=NEW only | N4=D+NEW minus stealth_* (pure rotation) | N5=all87+NEW"""
import time, numpy as np, pandas as pd
from common import *
from models import fit_predict, fit_final

df = pd.read_parquet(PREPARED).sort_values(["user", "day"]).reset_index(drop=True)
sp = pd.read_csv(SPLIT).set_index("user")
F87 = select_features(df, "nostatic")
R = [c for c in F87 if c in ("active_channel_count", "multi_channel_days_10wd") or c.startswith(("dominant_channel_switches", "channel_distribution_shift", "cross_channel_deviation_days"))]
X_ = [c for c in F87 if c.startswith(("cumulative_deviation", "combined_channel_intensity", "consecutive_elevated_days"))]
CORE = [c for c in F87 if c not in R and c not in X_]
CH = [("external_email_count", "email_count_p50", "email_count_p95"), ("usb_copy_count", "usb_copy_p50", "usb_copy_p95"),
      ("www_upload_count", "http_upload_p50", "http_upload_p95")]
WS = (5, 10, 20, 30)
NAMES = ["m", "share_max", "entropy", "balance", "sw", "alt", "maxrun", "excl_days", "overlap_days", "handoff", "stealth_acc", "stealth_days"]


def build(df):
    N = len(df); out = {f"nr_{n}_{w}wd": np.full(N, np.nan) for n in NAMES for w in WS}
    X = np.stack([df[c[0]].values for c in CH], 1).astype(float)
    P50 = np.stack([df[c[1]].values for c in CH], 1).astype(float); P95 = np.stack([df[c[2]].values for c in CH], 1).astype(float)
    E = np.clip(X - P50, 0, None) / np.maximum(1, P95 - P50); E = np.nan_to_num(E)
    Over = np.nan_to_num((X > P95).astype(float)) > 0
    uid = df.user.values; bounds = np.flatnonzero(np.r_[True, uid[1:] != uid[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        e = E[a:b]; n = b - a; hasE = e > 0; nexc = hasE.sum(1); tot = e.sum(1)
        dom = np.where(tot > 0, e.argmax(1), -1)
        stealth_day = (~Over[a:b].any(1)) & (tot > 0); sval = tot * stealth_day
        hand = np.zeros(n)
        for d in range(1, n):
            if hasE[d - 1].any(): hand[d] = (hasE[d] & ~hasE[d - 1]).sum()
        for w in WS:
            for t in range(w - 1, n):
                s = slice(t - w + 1, t + 1); S = e[s].sum(0); T = S.sum(); lab = dom[s][dom[s] >= 0]; i = a + t
                out[f"nr_m_{w}wd"][i] = (S > 0).sum()
                if T > 0:
                    p = S / T; pp = p[p > 0]
                    out[f"nr_share_max_{w}wd"][i] = p.max(); out[f"nr_entropy_{w}wd"][i] = -(pp * np.log(pp)).sum() / np.log(3)
                    out[f"nr_balance_{w}wd"][i] = S.min() / S.max()
                else:
                    out[f"nr_share_max_{w}wd"][i] = 0; out[f"nr_entropy_{w}wd"][i] = 0; out[f"nr_balance_{w}wd"][i] = 0
                if len(lab) > 1:
                    ch = lab[1:] != lab[:-1]; sw = ch.sum(); out[f"nr_sw_{w}wd"][i] = sw; out[f"nr_alt_{w}wd"][i] = sw / (len(lab) - 1)
                    run = best = 1
                    for k in range(1, len(lab)):
                        run = run + 1 if lab[k] == lab[k - 1] else 1; best = max(best, run)
                    out[f"nr_maxrun_{w}wd"][i] = best
                else:
                    out[f"nr_sw_{w}wd"][i] = 0; out[f"nr_alt_{w}wd"][i] = 0; out[f"nr_maxrun_{w}wd"][i] = len(lab)
                out[f"nr_excl_days_{w}wd"][i] = (nexc[s] == 1).sum(); out[f"nr_overlap_days_{w}wd"][i] = (nexc[s] >= 2).sum()
                out[f"nr_handoff_{w}wd"][i] = hand[s].sum()
                out[f"nr_stealth_acc_{w}wd"][i] = sval[s].sum(); out[f"nr_stealth_days_{w}wd"][i] = stealth_day[s].sum()
    return pd.DataFrame(out)


t0 = time.time(); NEW = build(df); print(f"built {NEW.shape[1]} new features in {time.time()-t0:.0f}s", flush=True)
NEW.to_parquet(WORK / "new_rotation_features.parquet", index=False)
