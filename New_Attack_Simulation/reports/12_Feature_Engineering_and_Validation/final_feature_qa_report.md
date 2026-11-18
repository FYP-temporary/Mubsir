# MUBSIR — Final Feature Quality Assurance Report

## 1. Dataset Summary

| Metric | Verified result |
|---|---:|
| User-Day records | 387,162 |
| Users | 3,737 |
| Columns including target | 143 |
| Positive User-Days (`y=1`) | 9,080 |
| Non-injected User-Days (`y=0`) | 378,082 |
| Users with positive labels | 400 |
| Executed channel actions | 10,124 |
| Total added synthetic events | 29,007 |

## 2. Validated QA Evidence

| Validation | Scope | Result |
|---|---|---|
| 30 additional behavioral features | 30 features; 107,970 sampled values | 0 numerical/NaN mismatches |
| 27 rotation/deviation features | 27 features; 226,314 sampled values | 0 numerical/NaN mismatches |
| Original feature dependency audit | 85 columns; 32,908,770 values | 0 mismatches |
| Full dataset integrity | 108 checks | 0 rule failures |
| Independent label and source validation | 10 checks | All passed |
| Independent rolling-count verification | 12 features | 0 mismatches |
| Final feature dictionary | 143 documented columns | Complete schema coverage |

## 3. Ground Truth and Execution Reconciliation

The independent execution log was used to reconstruct
the positive User-Day population.

- Execution actions: 10,124.
- Injected synthetic events: 29,007.
- Reconstructed positive User-Days: 9,080.
- Ground Truth key mismatches: 0.
- Ground Truth event-count mismatches: 0.
- Binary label mismatches: 0.

The 142 pre-labeling columns were preserved during
binary target integration.

## 4. Historical Baseline and Missing Values

Historical reference fields remained unchanged.

Missing historical P90 values were investigated
against recorded historical active-day counts.

All examined missing-P90 users had zero recorded
historical active days in the corresponding channel.

Undefined ratios remain NaN.

Columns with at least one missing value:
16.

## 5. Constant-Column Review

The following columns were constant in the inspected
feature population:

- `is_weekend`: zero because only eligible weekdays
  are present.
- `unique_usb_extensions`: zero for every record
  in the current dataset.

The latter matched its approved source, but a
source match alone does not establish its usefulness
or independently validate upstream raw-event extraction.

Both columns require appropriate model feature-selection
decisions.

## 6. Leakage Validation

The tested checks found:

- No direct Ground Truth or attack-scheduling metadata
  columns within the feature dataset.
- No numerical feature exactly equal to `y` or `1-y`.
- No mismatches in the independently checked causal
  rolling-count features.
- No modifications to the original 142 columns
  during labeling.

**Limitation:** These tests do not prove the absence
of every possible form of statistical or temporal leakage.

Model development must also validate:

- Predictor selection and exclusion of identifiers
  where appropriate.
- Training, validation, and test split isolation.
- Preprocessing fitted on training data only.
- Handling of missing values and constant features.
- Class imbalance and appropriate evaluation metrics.

## 7. Class Distribution

The positive class constitutes approximately
2.345%
of User-Day records.

Model performance should therefore be evaluated using
appropriate metrics including precision, recall,
F1-score, and precision-recall AUC, rather than
accuracy alone.

## 8. Final Assessment

**Status: PASS — TESTED DATASET AND LABELING RULES VERIFIED.**

The validated dataset is ready for controlled final
export and independent post-export integrity checks.

This status applies to tested computational and data
integrity conditions, not to model detection accuracy,
real-world attack realism, or complete leakage elimination.

No files were exported by this documentation stage.
