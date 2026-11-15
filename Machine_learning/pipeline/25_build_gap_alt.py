"""Step 25: nr_gap_alt_{G}_{w}wd  (G in 0..3, w in 5/10/20 workdays) -- intermittent channel rotation. EXPERIMENTAL: not part of FINAL74.
Definition (per user, causal, workday sequence = same one used by step 21: 2010 warm-start workdays + 2011 rows):
  deviation day  : any channel has E_c > 0  (E_c = max(0, x_c - P50_c) / max(1, P95_c - P50_c), the project's existing deviation measure; NaN counts as no deviation, as in nr_alt)
  dominant       : argmax_c E_c  (ties -> lowest channel index: email < usb < http; deterministic)
  pair           : two ADJACENT deviation days (p, d) in the deviation-day sequence, both inside the window [t-w+1, t]
  eligible       : quiet workdays between them = d - p - 1 <= G   (longer gaps are dropped, never bridged to a farther deviation day)
  nr_gap_alt_G   = changed / eligible   (0 if eligible == 0)
Diagnostics saved (not model features): nr_gap_elig_{G}_{w}wd, nr_gap_chg_{G}_{w}wd.
"""
import time, numpy as np, pandas as pd
from common import *

WS = (5, 10, 20); GS = (0, 1, 2, 3)
CH = [("external_email_count", "email_count_p50", "email_count_p95"), ("usb_copy_count", "usb_copy_p50", "usb_copy_p95"), ("www_upload_count", "http_upload_p50", "http_upload_p95")]


def dominant(E):
    """E: (n,3) deviation matrix -> dom (-1 on quiet days, else argmax with ties to the lowest index)."""
    dev = E.sum(1) > 0
    return np.where(dev, E.argmax(1), -1)


def gap_alt(dom, ws=WS, gs=GS):
    """dom: array of dominant channel per workday (-1 = quiet). Returns {(G, w): (ratio, elig, chg)} arrays over all days (value at t uses days <= t only)."""
    n = len(dom); idx = np.arange(n); isdev = dom >= 0
    # p[d] = index of the previous deviation day strictly before d (-1 if none), only defined for deviation days
    last = np.full(n, -1); cur = -1
    for d in range(n):
        last[d] = cur
        if isdev[d]: cur = d
    out = {}
    for G in gs:
        pair = isdev & (last >= 0)
        elig = pair & ((idx - last - 1) <= G)
        chg = elig & (dom != dom[np.where(last >= 0, last, 0)])
        # a pair (p,d) is inside window t iff p >= t-w+1 and d <= t. p[d] is non-decreasing in d -> the valid d form a contiguous block (d0..t)
        pv = np.where(isdev, last, -1)                       # for non-deviation days p is irrelevant (never eligible)
        cE = np.concatenate([[0], np.cumsum(elig)]); cC = np.concatenate([[0], np.cumsum(chg)])
        # non-decreasing helper for searchsorted: running max of last over all days
        pm = np.maximum.accumulate(last)
        for w in ws:
            lo = idx - w + 1                                  # earliest day inside window
            d0 = np.searchsorted(pm, lo, side="left")         # first d with running-max(last) >= lo  (monotone surrogate)
            d0 = np.maximum(d0, 0)
            e = cE[idx + 1] - cE[np.minimum(d0, idx + 1)]; c = cC[idx + 1] - cC[np.minimum(d0, idx + 1)]
            out[(G, w)] = (np.where(e > 0, c / np.maximum(e, 1), 0.0), e, c)
    return out


def gap_alt_literal(dom, t, w, G):
    """brute force, written literally from the definition (used only for verification)."""
    days = [d for d in range(max(t - w + 1, 0), t + 1) if dom[d] >= 0]
    el = ch = 0
    for a, b in zip(days[:-1], days[1:]):
        if b - a - 1 <= G:
            el += 1; ch += int(dom[a] != dom[b])
    return (ch / el if el else 0.0), el, ch


if __name__ == "__main__":
    t0 = time.time()
    # ---------------- mandatory unit tests (sequence of dominant channels, quiet = -1; window = whole sequence)
    E_, U_, W_, Q = 0, 1, 2, -1
    def val(seq, G):
        r = gap_alt(np.array(seq), ws=(len(seq),), gs=(G,))[(G, len(seq))]; return float(r[0][-1]), int(r[1][-1]), int(r[2][-1])
    cases = [([E_, U_], 0, 1.0), ([E_, Q, U_], 0, 0.0), ([E_, Q, U_], 1, 1.0), ([E_, Q, Q, U_], 1, 0.0), ([E_, Q, Q, U_], 2, 1.0), ([E_, U_, W_], 0, 1.0),
             ([E_, E_, U_], 0, 0.5), ([E_, Q, E_], 1, 0.0), ([E_, Q, U_, Q, W_], 1, 1.0)]
    for seq, G, exp in cases:
        v, el, ch = val(seq, G); assert abs(v - exp) < 1e-12, (seq, G, v, exp)
    assert val([E_, Q, U_, Q, W_], 1)[1:] == (2, 2), "last example must count exactly two eligible transitions"
    # edge cases
    assert val([Q, Q, Q, Q], 3) == (0.0, 0, 0)                     # no deviation day
    assert val([Q, E_, Q, Q], 3) == (0.0, 0, 0)                    # single deviation day
    assert val([E_, E_, E_, E_], 2) == (0.0, 3, 0)                 # same dominant everywhere
    assert val([E_, Q, Q, Q, U_], 2) == (0.0, 0, 0)                # gap > G, not bridged
    assert val([E_, Q, Q, Q, U_, W_], 2) == (1.0, 1, 1)           # only the adjacent pair after the long gap is eligible; E->U is not linked to W
    # every random ratio lies in [0,1]; brute-force equality on random sequences incl. quiet runs and all windows/G
    rng = np.random.default_rng(1); mism = 0; cells = 0
    for _ in range(300):
        n = int(rng.integers(1, 80)); dom = rng.choice([-1, 0, 1, 2], size=n, p=[.45, .2, .2, .15]); res = gap_alt(dom)
        for (G, w), (r, e, c) in res.items():
            assert ((r >= 0) & (r <= 1)).all()
            for t in range(n):
                cells += 1; lr, le, lc = gap_alt_literal(dom, t, w, G)
                if not (np.isclose(r[t], lr) and e[t] == le and c[t] == lc): mism += 1
    assert mism == 0, mism
    # dominant(): multi-channel day, tie -> lowest index, quiet day
    Et = np.array([[0.5, 0.5, 0.2], [0, 0, 0], [0.1, 0.9, 0.9], [0, 0, 1.0], [0, 0.3, 0]]); assert dominant(Et).tolist() == [0, -1, 1, 2, 1]
    # tiny hand-checked windows: deviation days at 0 and 6 (gap 5): not eligible for G<=3 in any window; days 6,7: eligible
    d = np.array([0, -1, -1, -1, -1, -1, 1, 2]); r = gap_alt(d)
    assert r[(3, 20)][1][-1] == 1 and r[(3, 20)][2][-1] == 1 and r[(3, 5)][1][-1] == 1
    print(f"unit tests OK: 9 mandatory + edge cases + {cells} random (t,w,G) cells vs literal brute force, mismatches = 0")

    # ---------------- build on the project data (same workday sequence as step 21)
    df = pd.read_parquet(PREPARED).sort_values(["user", "day"]).reset_index(drop=True); users = df.user.unique()
    ud = pd.read_parquet(GT_USER_DAYS.parent.parent / "final" / "user_day_injected_r62.parquet", columns=["user", "day", "is_weekend", "logon_count", "external_email_count", "usb_copy_count", "www_upload_count"])
    ud["day"] = pd.to_datetime(ud.day); ud = ud[ud.user.isin(users)]
    ud10 = ud[(ud.day < "2011-01-01") & (ud.is_weekend == 0) & (ud.logon_count > 0)].sort_values(["user", "day"])
    uidx = df.groupby("user").indices; u10 = {u: g for u, g in ud10.groupby("user")}
    cols = {f"{p}_{G}_{w}wd": np.full(len(df), np.nan) for p in ("nr_gap_alt", "nr_gap_elig", "nr_gap_chg") for G in GS for w in WS}
    dom_store = {}
    for k, u in enumerate(users):
        ix = uidx[u]; d11 = df.iloc[ix]; g10 = u10[u]; n10 = len(g10)
        X = np.vstack([g10[[c[0] for c in CH]].to_numpy(float), d11[[c[0] for c in CH]].to_numpy(float)])
        p50 = d11[[c[1] for c in CH]].iloc[0].to_numpy(float); p95 = d11[[c[2] for c in CH]].iloc[0].to_numpy(float)
        E = np.nan_to_num(np.clip(X - p50, 0, None) / np.maximum(1, p95 - p50)); dom = dominant(E); dom_store[u] = (dom, n10)
        res = gap_alt(dom)
        for (G, w), (r, e, c) in res.items():
            cols[f"nr_gap_alt_{G}_{w}wd"][ix] = r[n10:]; cols[f"nr_gap_elig_{G}_{w}wd"][ix] = e[n10:]; cols[f"nr_gap_chg_{G}_{w}wd"][ix] = c[n10:]
        if k % 250 == 0: print(f"[{time.time()-t0:4.0f}s] users {k}/{len(users)}", flush=True)
    NEW = pd.DataFrame(cols)
    # brute-force check on real users (literal definition, all G and w)
    bad = chk = 0
    for u in np.random.default_rng(0).choice(users, 25, replace=False):
        ix = uidx[u]; dom, n10 = dom_store[u]
        for (G, w) in [(G, w) for G in GS for w in WS]:
            for j in range(len(ix)):
                lr, le, lc = gap_alt_literal(dom, n10 + j, w, G); chk += 1
                if not (np.isclose(lr, cols[f"nr_gap_alt_{G}_{w}wd"][ix[j]]) and le == cols[f"nr_gap_elig_{G}_{w}wd"][ix[j]] and lc == cols[f"nr_gap_chg_{G}_{w}wd"][ix[j]]): bad += 1
    print(f"real-data brute-force check: {chk} cells, mismatches = {bad}"); assert bad == 0
    # distribution report
    rows = []
    for G in GS:
        for w in WS:
            a = NEW[f"nr_gap_alt_{G}_{w}wd"]; e = NEW[f"nr_gap_elig_{G}_{w}wd"]; c = NEW[f"nr_gap_chg_{G}_{w}wd"]
            rows.append(dict(G=G, window=w, n_nan=int(a.isna().sum()), zero_share=round(float((a == 0).mean()), 3), no_eligible_share=round(float((e == 0).mean()), 3), mean=round(float(a.mean()), 4),
                             p50=round(float(a.quantile(.5)), 3), p95=round(float(a.quantile(.95)), 3), max=round(float(a.max()), 3), min=round(float(a.min()), 3),
                             mean_elig=round(float(e.mean()), 3), mean_chg=round(float(c.mean()), 3)))
    rep = pd.DataFrame(rows); rep.to_csv(RES / "gap_alt_distribution.csv", index=False); print(rep.to_string(index=False))
    assert NEW[[f"nr_gap_alt_{G}_{w}wd" for G in GS for w in WS]].apply(lambda s: s.between(0, 1).all()).all()
    pd.concat([df[["user", "day"]], NEW], axis=1).to_parquet(WORK / "gap_alt_features.parquet", index=False); print(f"saved in {time.time()-t0:.0f}s")
