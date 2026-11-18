# Feature generation contract — the 27 features we added to the model

**Purpose:** the model consumes 77 distinct columns. Of these, **27 columns do not exist in the team's data** (neither in the daily aggregation table nor in `behavior_features_r62_ml_final.parquet`); I added them. This document specifies exactly how they are computed, so that the production pipeline computes them with the same definitions the model was trained on.

**What this document covers and what it does not:**

| Source | Count | Where it is defined |
|---|---|---|
| Daily columns that exist in the aggregation table (`user_day_injected`) | 14 | The table itself |
| Team columns in `ml_final` (window sums, active days, `cumulative_deviation`, `consecutive_elevated_days`, `channel_distribution_shift`, p95 ratios) | 36 | Team code (I did not find it in the repository); Section 6 describes what I verified about them |
| **Columns I added — the subject of this document** | **27** | **Here** |

The 27 are: `nr_{m, entropy, excl_days, overlap_days, alt, handoff, stealth_acc}_{5,10,20}wd` (21) + `nr_gap_alt_2_{5,10,20}wd` (3) + `email_count_to_p90_ratio`, `usb_copy_to_p90_ratio` and `http_upload_to_p90_ratio` (3). Each window model uses all 21 `nr_*` columns (the versions of all three windows) and the three p90 ratios, plus only its own window's version of `nr_gap_alt_2` (75 = 74 shared + 1); therefore the extractor needs all 27 columns.

## 1) What the extractor needs as input

**a) The workday sequence of each user** (in chronological order):
- A workday = `is_weekend == 0` **and** `logon_count > 0`. A day without a logon is **not a quiet day**; it is not part of the sequence at all. This affects every window (a window is the last w workdays in the sequence, not w calendar days) and the distance between deviation days in `nr_gap_alt_2`.
- Everything is computed on the full sequence (2010 + 2011): in training, each user had 250–260 workdays from 2010 before the first row of 2011 (median 251), so no window starts incomplete.
- Computing day t requires days t−w … t (that is, **w+1 days**, 21 days for the largest window), because `nr_handoff` looks at the day before the first day of the window.

**b) Three daily count columns** in this fixed order (email < USB < HTTP, which is also the tie-breaking order): `external_email_count`, `usb_copy_count`, `www_upload_count`.

**c) The fixed per-user baseline** (from 2010 only, the same values for all days of a user; they exist as constant columns in `ml_final` (originating from the team's baseline), **to be loaded as they are and not recomputed**):

| Channel | P50 | P90 | P95 |
|---|---|---|---|
| email | `email_count_p50` | `email_count_p90` | `email_count_p95` |
| usb | `usb_copy_p50` | `usb_copy_p90` | `usb_copy_p95` |
| http | `http_upload_p50` | `http_upload_p90` | `http_upload_p95` |

These columns are **not model inputs** (forbidden by a check in `verify_release.py`), but they are needed to compute the features. Note that P95 (and P90) is zero or missing in 27.5% of the training rows for the USB channel and 43.0% for HTTP (and 0% for email); those rows give p90 ratios = NaN.

## 2) Notation

- `x_c(d)`: the count of channel c on workday d.
- **Deviation** `E_c(d) = max(0, x_c(d) − P50_c) / max(1, P95_c − P50_c)`. Any missing value (count or baseline) is treated as **no deviation** (E = 0).
- **Deviation day:** `Σ_c E_c(d) > 0`. The **dominant channel** on a deviation day: `argmax_c E_c(d)`, with ties broken toward the lowest index (email=0 < usb=1 < http=2). On days without deviation the dominant channel is "none" (−1).
- `W_t`: the last w workdays ending at day t (inclusive). Every feature is causal (it uses only days ≤ t).
- `S_c = Σ_{d∈W_t} E_c(d)` and `S = Σ_c S_c`.

## 3) Definitions (for each window w ∈ {5, 10, 20})

| Feature | Exact definition |
|---|---|
| `nr_m_{w}wd` | The number of channels with `S_c > 0` (0 to 3) |
| `nr_entropy_{w}wd` | If `S > 0`: `−Σ_{c: S_c>0} p_c·ln p_c / ln 3` where `p_c = S_c / S`; otherwise 0 |
| `nr_excl_days_{w}wd` | The number of days in W_t on which **exactly one channel** deviates (`E_c > 0` for one channel) |
| `nr_overlap_days_{w}wd` | The number of days in W_t on which **two or more channels** deviate |
| `nr_alt_{w}wd` | Pairs = (d−1, d) consecutive in the sequence, **both inside W_t and both deviation days**. The value = the number of pairs in which the dominant channel changes ÷ the number of pairs; 0 if there is no pair. A quiet day is neither compressed nor crossed |
| `nr_handoff_{w}wd` | For each day d in W_t: if **any** channel deviates on d−1, count the channels that deviate on d and did not deviate on d−1; the sum over W_t (d−1 may be the day before the window; on the first day of the sequence = 0) |
| `nr_stealth_acc_{w}wd` | `Σ_{d∈W_t} Σ_c E_c(d)` over the days and channels with `E_c(d) > 0` **and** `x_c(d) ≤ P95_c` (a channel that exceeds P95 excludes only itself) |
| `nr_gap_alt_2_{w}wd` | The deviation days inside W_t, in order; an **eligible pair** = two adjacent days in this list with `d − p − 1 ≤ 2` quiet workdays between them (a longer gap is ignored and is not bridged to a more distant day). The value = pairs whose dominant channel changed ÷ eligible pairs; 0 if there are none. G=0 equals `nr_alt` |
| `email_count_to_p90_ratio` | `external_email_count(d) / email_count_p90` if `p90 > 0`, otherwise **NaN** |
| `usb_copy_to_p90_ratio` | `usb_copy_count(d) / usb_copy_p90` if `p90 > 0`, otherwise NaN |
| `http_upload_to_p90_ratio` | `www_upload_count(d) / http_upload_p90` if `p90 > 0`, otherwise NaN |

(The three ratios are daily and do not depend on a window.)

A small example for `nr_alt` and `nr_gap_alt_2` on a sequence of dominant channels (E=email, U=usb, H=http, ·=quiet day): `E U · U H` → the consecutive deviating pairs of `nr_alt`: (E,U) change, (U·) invalid, (·U) invalid, (U,H) change ⇒ 2/2 = 1.0; whereas the pairs of `nr_gap_alt_2`: (E,U) gap 0, (U,U) across a quiet day gap 1, (U,H) gap 0 ⇒ change in 2 of 3 eligible pairs = 0.667.

## 4) Where the version of each feature is taken from (an ambiguity that exists in the scripts)

| Feature | Authoritative script |
|---|---|
| `nr_m`, `nr_entropy`, `nr_excl_days`, `nr_overlap_days`, `nr_handoff` | `18_build_evidence_features.py` |
| `nr_alt`, `nr_stealth_acc`, p90 ratios | `21_build_final_features.py` (**replaces** the versions of `nr_alt` and `nr_stealth_acc` from 18, which is what `28_final75.py` does) |
| `nr_gap_alt_2` | `25_build_gap_alt.py` (G = 2 by agreement with the team; G = 0/1/3 and `nr_alt_pairs` are experimental/diagnostic and are not inputs) |

Script 18 also generates the `e1_*` and `e2_*` columns (accumulation and evasion evidence): **the final model does not use them**, and you do not need them in production.

## 5) Intended edge cases

- A missing count (NaN) or a missing baseline → E = 0 (no deviation), not an error.
- `P95 − P50 ≤ 1` → the denominator is 1 (every count above P50 gives a deviation equal to the difference itself).
- `P95 = 0`: any positive count is above P95, so it never enters `nr_stealth_acc` (while `x ≤ P95` means x = 0 and E = 0).
- In training, the baselines were fixed per user (2010 only) and taken from the team's file; they are not updated daily and are not derived from live days.

## 6) What I found about the team's 36 columns while writing this document

When comparing the recomputed sums with the team's columns in `ml_final`, it turned out that the difference I had previously described as "unexplained" is caused by **two different start conventions**, not by a difference in the formula:

| Team columns | Behavior in the first w−1 workdays of 2011 | Afterwards |
|---|---|---|
| Count sums of 5 and 10 days | The sum of a **partial** window starting from 2011-01-03 (matches `rolling(w, min_periods=1)` exactly) | Exact match |
| Count sums of 20 and 30 days | **NaN** | Exact match (18,877 and 28,793 NaN rows) |
| `cumulative_deviation_{5,10,20,30}` | **NaN** (3,980 / 8,951 / 18,877 / 28,793 rows) | Exact match with our `Σ E`: 0 differences in 99,415 / 94,444 / 84,518 rows |

Our 27 features, however, start from 2010 (no NaN and no partial windows). Therefore:
- When testing the match against `ml_final` on 2011 rows, expect a difference in the first w−1 days of 2011 of every user in the team's columns (partial/NaN), not in ours.
- In production, with a continuous history, these incomplete windows will not appear; the model saw NaN in these rows during training (from 3.8% to 27.8% of the rows of the 995-user data, depending on the column), which has no effect on normal operation, but it means that the first w−1 days of any new user without history are not represented in training in the same way.

This also corrects the old sentence in `FEATURE_DEFINITIONS_ROTATION.md` ("identical to the team's column"), which was more absolute than warranted, and it has been amended.

## 7) Verification (`pipeline/verify_feature_contract.py`)

- I wrote a literal translation of the definitions above with simple loops (`rotation_features`) that shares no code with the original scripts 18, 21 and 25.
- I compared it with the stored values on which the model was trained, for 60 users (all their days and all windows): **165,051 cells (27 columns), 0 differences** (tolerance 1e-9, and NaN matching NaN in the p90 ratios).
- Golden test cases: `docs/golden_feature_cases.json` contains 3 cases (alternating attack, a day without deviation with a zero p90, exclusive and overlapping deviation days): each case has the counts of the last 21 workdays, the baseline, and the 27 expected values (taken from the stored tables, not from the reference implementation), and the reference implementation passes them with no difference.
- Run it with: `cd pipeline && python verify_feature_contract.py` (needs `pipeline/data/`, and exits 0 only if everything succeeds). The production extractor that you write is tested with the same golden cases (the file needs no data).
