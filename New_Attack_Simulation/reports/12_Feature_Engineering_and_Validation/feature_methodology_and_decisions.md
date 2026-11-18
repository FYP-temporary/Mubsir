# MUBSIR — Feature Methodology and Design Decisions

## 1. Dataset Overview

- Dataset: CERT r6.2, behavioral features following validated synthetic event-count injection.
- Granularity: One eligible user-workday per row.
- Users: 3,737.
- Records: 387,162.
- Columns: 143 (including the binary target).
- Original Data Engineering columns: 85.
- Additional behavioral features: 30.
- New Rotation features: 27.
- Binary target: `y`.

The dataset preserves user identifiers, temporal fields,
historical reference statistics, and behavioral measurements.
Not all columns are intended as model predictors.

## 2. Historical Baseline

The historical behavioral baseline is calculated from the
2010 reference period and remains immutable throughout
2011 feature generation and synthetic attack injection.

Historical percentile, active-rate, and related reference
statistics are reused without recalculation.

A missing historical statistic is not automatically replaced
with zero.

## 3. Workday and Rolling-Window Policy

An eligible workday has `is_weekend = 0` and
`logon_count > 0`.

Rolling windows use the last eligible workdays for each user,
including the current day.

The approved windows are:

- Original and additional engineered features: 5, 10, 20,
  and 30 eligible workdays where defined.
- New Rotation features: 5, 10, and 20 eligible workdays.

**Effective window policy:**

- Rolling history starts in 2011.
- Incomplete initial windows are calculated using available
  eligible workdays (`min_periods=1`).
- No activity from 2010 enters rolling-window calculations.
- No future activity is used.

The original source dictionaries may document an earlier
full-window startup policy. The effective policy above
supersedes that startup convention for this dataset.

The historical 2010 baseline remains unchanged.

## 4. Dominant Channel Definitions

The dataset uses two distinct operational definitions
of dominant channel. They describe different behavioral
measurements and must not be treated as interchangeable.

### Feature-specific definitions

| Feature | Dominant-channel definition |
|---|---|
| `dominant_channel_switches_5wd` | Dominant Activity Channel: argmax(Count_c/P95_c) among valid P95 channels. Inactive days and approximately tied maxima (np.isclose, rtol=1e-9, atol=1e-12) are excluded. |
| `dominant_channel_switches_10wd` | Dominant Activity Channel: argmax(Count_c/P95_c) among valid P95 channels. Inactive days and approximately tied maxima (np.isclose, rtol=1e-9, atol=1e-12) are excluded. |
| `dominant_channel_switches_20wd` | Dominant Activity Channel: argmax(Count_c/P95_c) among valid P95 channels. Inactive days and approximately tied maxima (np.isclose, rtol=1e-9, atol=1e-12) are excluded. |
| `dominant_channel_switches_30wd` | Dominant Activity Channel: argmax(Count_c/P95_c) among valid P95 channels. Inactive days and approximately tied maxima (np.isclose, rtol=1e-9, atol=1e-12) are excluded. |
| `nr_alt_5wd` | Dominant Deviation Channel: argmax(E_c), where E_c=max(0,Count_c-P50_c)/max(1,P95_c-P50_c). Ties resolve EMAIL, USB, HTTP. Days without deviation have no dominant channel. |
| `nr_alt_10wd` | Dominant Deviation Channel: argmax(E_c), where E_c=max(0,Count_c-P50_c)/max(1,P95_c-P50_c). Ties resolve EMAIL, USB, HTTP. Days without deviation have no dominant channel. |
| `nr_alt_20wd` | Dominant Deviation Channel: argmax(E_c), where E_c=max(0,Count_c-P50_c)/max(1,P95_c-P50_c). Ties resolve EMAIL, USB, HTTP. Days without deviation have no dominant channel. |
| `nr_gap_alt_2_5wd` | Dominant Deviation Channel: argmax(E_c), where E_c=max(0,Count_c-P50_c)/max(1,P95_c-P50_c). Ties resolve EMAIL, USB, HTTP. Days without deviation have no dominant channel. |
| `nr_gap_alt_2_10wd` | Dominant Deviation Channel: argmax(E_c), where E_c=max(0,Count_c-P50_c)/max(1,P95_c-P50_c). Ties resolve EMAIL, USB, HTTP. Days without deviation have no dominant channel. |
| `nr_gap_alt_2_20wd` | Dominant Deviation Channel: argmax(E_c), where E_c=max(0,Count_c-P50_c)/max(1,P95_c-P50_c). Ties resolve EMAIL, USB, HTTP. Days without deviation have no dominant channel. |

**Dominant Activity Channel**

The channel with the highest normalized activity
`Count_c / P95_c` among channels with valid P95.

Days without a positive normalized maximum and days
with approximately tied maxima are excluded from
the switching sequence.

Approximate equality uses `np.isclose` with
`rtol=1e-9` and `atol=1e-12`.

**Dominant Deviation Channel**

The channel with the highest positive deviation:

`E_c(d) = max(0, Count_c(d) - P50_c) / max(1, P95_c - P50_c)`

Missing count or baseline values produce `E=0`.
A historical `P50=0` is permitted when present.

Ties are resolved in the order EMAIL, USB, HTTP.
Days with no positive deviation have no dominant channel.

### Interpretation

The activity-based definition measures changes in the
channel showing the greatest relative activity.

The deviation-based definition measures changes in the
channel showing the greatest deviation from historical behavior.

These features provide different perspectives on temporal
channel changes. Their predictive usefulness must be
evaluated during model training.

## 5. Missing Historical Statistics

Missing P90 values were investigated independently.

| Channel | User-Day rows with missing P90 |
|---|---:|
| EMAIL | 0 |
| USB | 312,211 |
| HTTP | 328,257 |

The historical activity audit established that users
with missing P90 statistics in the examined channels
had zero recorded historical active days in those channels.

Daily P90 ratios are defined only when P90 is positive.
Otherwise, the ratio remains NaN.

Missing values are preserved for explicit handling
during model preprocessing, rather than automatically
being interpreted as zero activity in 2011.

## 6. Binary Label Definition

- `y=1`: Verified positive synthetic injection on the User-Day.
- `y=0`: No synthetic injection on the User-Day.

Labels are assigned through exact `(user, day)` matching
with approved User-Day Ground Truth.

A user's assigned attack status is not used to label
all of that user's days as attacks.

The label describes synthetic injection and does not
independently certify that all original activities
on non-injected days are benign.

## 7. Feature Selection and Leakage Considerations

- `y` is the target and must never be a predictor.
- Ground Truth, planned schedules, and execution
  metadata must not enter predictor columns.
- `user` and `day` require explicit model-input decisions.
- Historical reference columns are needed for feature
  engineering but are not automatically approved predictors.
- Constant columns, including `is_weekend` and
  `unique_usb_extensions`, require feature-selection review.
- Missing-value handling must be fitted using training
  data only, following the approved train/test protocol.

## 8. Implementation Boundaries

The dataset represents synthetic count-based injection
and behavioral feature construction, not real file transfers.

Successful QA confirms tested computational consistency;
it does not establish model detection performance,
attack realism, or complete absence of statistical leakage.

Production deployment in another environment requires
behavioral baseline recalibration.

## 9. Documentation Sources

- Original Data Engineering feature dictionary.
- Approved 30-feature calculation dictionary.
- Feature Generation Contract for the 27 additional features.
- Notebook 10 injection execution evidence.
- Notebook 11 validated User-Day Ground Truth.
- Notebook 12 feature generation and validation results.
