# Notebook 05 — Simulation Rules Feasibility & Selection

## Purpose
Evaluate structural feasibility of prospective low-and-slow, multi-channel exfiltration attacks on naturally eligible user-workdays. No injection, attack-user assignment, or stealth estimation is performed in this notebook.

## Approved structural rules (verified from this notebook)

- **Duration:** D ∈ {5, 10, 20, 30, 40, 50} eligible workdays; windows follow each user's eligible-day order, not calendar-day intervals.
- **Target channels:** Email = external_email_count > 0; USB = usb_copy_count > 0; HTTP = www_upload_count > 0. Natural channel activity is not replaced or deleted.
- **Primary-Channel Switching:** Range C selected. Low 10–25%, Medium 30–45%, High 50–65%. For A proposed active days, T=A−1 transitions; valid integer switches S satisfy ceil(T×min_rate) ≤ S ≤ floor(T×max_rate). Cell 12 uses bitset dynamic programming to test exact S under available daily channels.
- **Five-day exception:** D=5 requires all 5 eligible days active and allows exact switching counts Low=1, Medium=2, High=3, overriding general Range C integer feasibility.
- **Off-Days:** Forced-only: O = D − available_channel_days; no optional Off-Days. D=5 requires O=0; otherwise O≤floor(D/3), equivalently 2O≤A. Candidate windows also require supports_2step and at least two active days.
- **Same-day multichannel:** Optional, including zero days. Natural exact-two masks {EU,EH,UH} and all-three mask {EUH} are audited; multichannel opportunity does not block otherwise viable windows.
- **Structural pass:** new_rule_not_excluded AND (exact_low OR exact_medium OR exact_high). This is feasibility only, not an injected schedule.

## Final validated results

- Candidate users: **995**
- Actual windows checked: **472,667**
- Structurally feasible windows: **288,486**
- Users with ≥1 structurally feasible window: **936**
- Source-of-truth Cell 13: **PASS** after revalidation of retained outputs (see `final_validation_report.md` for current check and file counts).
- Reconciled source discrepancy: 275 eligible Future user-days in processed User-Day but absent from Features, distributed across 3 user IDs (`CDE1846`:105, `MBG3183`:105, `CMP2946`:65). None of the 995 simulation candidates are affected. The discrepancy and candidate impact were tested; causal explanation and original CERT label confirmation belong to upstream Ground Truth/Data Engineering sources.

## Handoff

Primary output: `integrated_structural_window_audit.parquet`; key: `user + window_workdays + window_start`. **Keep this file in the report root** after Cell 15.

All other dimension outputs are stored in numbered dimension folders. Individual dictionaries follow the same folder structure under `data_dictionaries/`.

### Column documentation coverage

- Output datasets documented: **17**
- Actual output columns documented: **210**
- Columns with source-backed prose definitions: **210**
- Columns flagged for targeted review: **0**
- The deprecated exploratory `natural_switching_level_screen.parquet` was intentionally excluded from final deliverables and dictionaries; it is not a dependency of structural feasibility.

## Scope limits

Results verify structural eligibility against processed User-Day and derived Features only. They do not establish payload stealth, exact injection volumes, complete channel scheduling, or classification metrics.

Generated UTC: 2026-11-07T19:55:49.804709+00:00
