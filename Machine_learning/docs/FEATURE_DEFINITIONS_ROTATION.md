# Mubsir – final feature set (75 features per window model)

Each per-window model (5, 10, 20 workdays) uses **75 features** = the 74 agreed features + `nr_gap_alt_2_{w}wd` of its own window. The 74 count every window-version of a feature as one feature. The previous content of this file (87-feature era ablation notes) is archived in `FEATURE_DEFINITIONS_ROTATION_REF87_archive.md`.

**Notation.** Channels c ∈ {email = `external_email_count`, usb = `usb_copy_count`, http = `www_upload_count`}; x_c(d) = daily count on workday d; P50_c, P90_c, P95_c = the user's 2010 baseline percentiles (unchanged team definitions); W_t = the last w workdays ending at day t (t included); workdays only; every feature is causal (uses days ≤ t only) and warm-started from the user's 2010 workdays.
**Deviation:** E_c(d) = max(0, x_c(d) − P50_c) / max(1, P95_c − P50_c). A missing value counts as no deviation. **Deviation day:** Σ_c E_c(d) > 0. **Dominant channel:** argmax_c E_c(d); ties resolved to the lowest index (email < usb < http).

## 1. Base features (41)
| Features | Definition |
|---|---|
| `email_event_count`, `external_email_count`, `http_event_count`, `www_visit_count`, `www_upload_count`, `usb_copy_count`, `file_event_count`, `unique_usb_files` | daily counts per channel (team columns) |
| `external_email_count_{5,10,20,30}wd`, `usb_copy_count_{5,10,20,30}wd`, `http_upload_count_{5,10,20,30}wd` | rolling sums of the channel count over the last w workdays |
| `email_active_days_{5,10,20}wd`, `usb_active_days_{5,10,20}wd`, `http_active_days_{5,10,20}wd` | number of days in W_t with x_c > 0 |
| `email_count_to_p95_ratio`, `usb_copy_to_p95_ratio`, `http_upload_to_p95_ratio` | x_c(d) / P95_c (NaN when P95 missing or ≤ 0) |
| `email_count_to_p90_ratio`, `usb_copy_to_p90_ratio`, `http_upload_to_p90_ratio` | x_c(d) / P90_c (NaN when P90 missing or ≤ 0; built in `21_build_final_features.py`) |
| `unique_external_recipients`, `unique_external_domains`, `unique_upload_domains`, `unique_domains`, `emails_with_attachments`, `attachment_count` | daily context counts (team columns) |

## 2. Accumulation and shift (12): `{cumulative_deviation, consecutive_elevated_days, channel_distribution_shift}_{5,10,20,30}wd`
- `cumulative_deviation_w` = Σ_{d∈W_t} Σ_c E_c(d)  (verified equal to the team column).
- `consecutive_elevated_days_w` = longest run of days in W_t with x_c > P50_c in at least one channel.
- `channel_distribution_shift_w` = total variation distance between the user's historical channel shares and the shares in W_t.

## 3. Rotation features `nr_*` (21 = 7 × {5,10,20}wd), `18_build_evidence_features.py` and `21_build_final_features.py`
| Feature | Definition |
|---|---|
| `nr_m` | number of channels with positive deviation summed over W_t (Σ_{d∈W_t} E_c > 0) |
| `nr_entropy` | normalised Shannon entropy (÷ ln 3) of the per-channel deviation shares in W_t; 0 when no deviation |
| `nr_excl_days` | days in W_t on which exactly one channel deviates |
| `nr_overlap_days` | days in W_t on which two or more channels deviate |
| `nr_alt` | switches of the dominant channel between **consecutive workdays that both deviate** ÷ number of such consecutive pairs in W_t; 0 if no pair. Quiet days are not compressed. |
| `nr_handoff` | per new channel: a channel that deviates today but did not deviate yesterday, counted only if some channel deviated yesterday; summed over W_t |
| `nr_stealth_acc` | Σ over days in W_t and channels with E_c > 0 and x_c ≤ P95_c of E_c (a channel above P95 only removes itself) |

## 4. Experimental addition (3 columns, one per window model): `nr_gap_alt_2_{5,10,20}wd`, `25_build_gap_alt.py`
Adjacent deviation days (p, d) inside W_t, i.e. consecutive in the sequence of deviation days, are an **eligible pair** when the number of quiet workdays between them, d − p − 1, is ≤ **G = 2** (longer gaps are discarded and never bridged to a farther deviation day).
`nr_gap_alt_2 = changed_pairs / eligible_pairs`, where `changed_pairs` counts eligible pairs whose dominant channel differs; 0 when there is no eligible pair; value in [0, 1].
`G = 0` is identical to `nr_alt`. Cross-validation over G ∈ {0,1,2,3} showed no gain beyond noise (best: G = 2, +0.0016 Recall@1%FPR at 20 days, below the 0.005 acceptance threshold); G = 2 was adopted by project decision, not by the acceptance rule. In the trained models its gain share is 0.08–0.30%.

## 5. Provenance
Model/evaluation scripts: `22_final_model.py` (74), `28_final75.py` (75, outputs `results/final75_*`, models `results/models/final75_FINAL75_w{5,10,20}.joblib`); gap experiment: `25_build_gap_alt.py`, `26_eval_gap_alt.py`, `results/gap_alt_*.csv`. Dropped/unused: `unique_usb_extensions` (all zero because of a regex over-escape in the team's daily-channel notebook), `combined_channel_intensity`, `dominant_channel_switches_30wd`, `email_bytes_to_p95_ratio`.
