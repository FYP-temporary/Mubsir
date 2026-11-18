# MUBSIR — 00_Data_Inventory_and_Integrity

## 1. Objective

Data Inventory & Integrity

## 2. Data Scope

All original datasets; Baseline and Future integrity.

## 3. Key Findings

- 3,995 benign users with historical Baseline.
- 3,737 users with eligible Future activity.
- 387,162 eligible Future feature records.
- Processed-data integrity and source reconciliation completed.

## 4. Validation

- Status: 13/13 PASS
- Original source datasets remain unchanged.

## 5. Final Deliverables

- `00_channel_logical_consistency.csv`
- `00_channel_logical_violations.csv`
- `00_channel_source_metadata.csv`
- `00_channel_source_schema.csv`
- `00_channel_value_integrity.csv`
- `00_core_dataset_metadata.csv`
- `00_core_dataset_schema.csv`
- `00_data_inventory.csv`
- `00_final_qa_summary.csv`
- `00_first_logon_null_review.csv`
- `00_missing_feature_keys.csv`
- `00_missing_infinite_profile.csv`
- `00_missing_infinite_summary.csv`
- `00_null_semantics_checks.csv`
- `00_per_user_workday_consistency.csv`
- `00_population_relationships.csv`
- `00_primary_key_integrity.csv`
- `00_source_column_reconciliation.csv`
- `00_source_reconciliation_mismatches.csv`
- `00_source_reconciliation_summary.csv`
- `00_temporal_coverage.csv`
- `00_workday_count_mismatches.csv`
- `00_workday_key_reconciliation.csv`
- `00_workday_validation.csv`

## 6. Limitations & Next Step

- Results describe completed analyses only.
- Attack injection feasibility is not yet proven.
- Final attack assignment and injection remain pending.
- Historical Baseline must remain immutable.

## 7. Original Detailed Report

The original report is preserved below.

---

# MUBSIR — Data Inventory and Integrity Report

## 1. Assessment Overview

- Notebook: `00_Data_Inventory_and_Integrity`
- Dataset Version: CERT r6.2
- QA Status: **PASS**
- Checks Completed: 13
- Checks Passed: 13
- Checks Requiring Review: 0

## 2. Official Data Periods

- Baseline Start: 2010-01-02
- Baseline End: 2010-12-31
- Future Start: 2011-01-01
- Future End: 2011-06-01

## 3. Population Summary

- Benign Baseline Users: 3,995
- Users With Future Workdays: 3,737
- Users Without Future Workdays: 258
- Baseline Workday Records: 976,434
- Future Feature Records: 387,162

## 4. Validation Results

| Check | Status |
|---|---|
| Temporal Coverage | PASS |
| Baseline Period Boundaries | PASS |
| Workday Calendar Consistency | PASS |
| Behavior Feature Workdays | PASS |
| Per-User Workday Counts | PASS |
| Channel Numerical Integrity | PASS |
| Channel Logical Consistency | PASS |
| Missing Keys and Infinite Values | PASS |
| Baseline and Feature Null Semantics | PASS |
| First Logon Null Semantics | PASS |
| Primary Key Integrity | PASS |
| Population Relationships | PASS |
| Processed Source Reconciliation | PASS |

## 5. Findings Relevant to Attack Simulation

- Workdays require a weekday and positive logon activity.
- No attack eligibility threshold has been applied.
- Missing USB and HTTP baseline statistics are associated
  with zero historical activity in the corresponding channel.
- Missing baseline statistics must not be replaced with zero
  without explicit justification.
- Users without Future workdays remain documented.
- The original processed channel measurements match User-Day.
- Off-days in future attack scenarios will mean days without
  injection, not days without natural activity.

## 6. Validation Scope and Limitations

- Original raw event files are unavailable in the inspected
  Data Engineering raw directory.
- The checks validate processed-data integrity and consistency.
- All engineered feature formulas have not been independently
  recomputed.
- The absence of pre-existing malicious activity in every
  candidate user-day has not been independently established.
- Attack feasibility, switching, stealth, and scenario eligibility
  will be evaluated in subsequent notebooks.

## 7. Next Step

Proceed to `01_User_Population_Audit` if all required QA
checks pass.

The next notebook will analyze the available user population
without imposing the previous attack scenario constraints.

