# MUBSIR — 02_Temporal_Window_Audit

## 1. Objective

Temporal Window Audit

## 2. Data Scope

Eligible Future workdays; natural channel rotation.

## 3. Key Findings

- 20,436,421 overlapping candidate window placements.
- Window lengths examined: 1–108 eligible workdays.
- 995 preliminary multi-channel candidates.
- Ordered rotation, recurrence, and cadence evaluated.
- Long rotations reconstructed from natural channel-day activity.

## 4. Validation

- Status: 12/12 PASS; 168/168 documented columns.
- Original source datasets remain unchanged.

## 5. Final Deliverables

- `notebook02_data_dictionary.csv`
- `rotation_feasibility_audit.parquet`
- `user_window_length_audit.parquet`

## 6. Limitations & Next Step

- Results describe completed analyses only.
- Attack injection feasibility is not yet proven.
- Final attack assignment and injection remain pending.
- Historical Baseline must remain immutable.
