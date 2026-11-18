# MUBSIR — Dataset & Model Engineering Handoff

**Project:** Mubsir: AI-Based Detection of Channel-Rotating Low-and-Slow Insider Data Exfiltration  
**Dataset:** CERT r6.2 · New_Attack_Simulation · Final exported artifacts (November 2026)  
**Audience:** Model engineer and team members integrating the dataset with the detection model  
**Status:** Feature generation and source/label QA completed; model training and performance evaluation are separate tasks.

> **Start here:** Train on `behavior_features_r62_ml_final_new.parquet` from Notebook 12, using `y` as the target. Do **not** train directly on the complete injected User-Day file or treat either attack-only Ground Truth table as a complete negative/positive training dataset.

## 1. Dataset at a glance

| Dataset / measure | Verified size or count | Meaning |
|---|---:|---|
| Original and injected User-Day | **1,394,010 × 34** | Full population: **4,000 users**; count-level intermediate data |
| Final behavioral features | **387,162 × 143** | **3,737 users**, one eligible user-workday per row; includes `y` |
| Feature columns excluding target | **142** | **85** original Data Engineering columns + **30** additional behavioral + **27** rotation/deviation features |
| Injected attackers | **400 distinct users** | Each receives one approved, feasible scenario |
| Positive training rows (`y=1`) | **9,080 (2.345%)** | User-days with verified positive synthetic injection |
| Non-injected training rows (`y=0`) | **378,082 (97.655%)** | No synthetic injection on that user-day |
| Channel-day injection actions | **10,124** | User-day-channel records, not distinct user-days |
| Synthetic events added | **29,007** | Count increments, **not** full exfiltrated files or payloads |
| Forced off-days | **1,670** | Scheduled attack-window workdays with **no injection** |

**Channels:** EMAIL, USB, HTTP. **Task:** binary **User-Day** detection of verified simulated injection, with temporal and cross-channel behavioral information.

### Row granularity: understand the difference

- **Injected User-Day** (`1,394,010` rows): full original 4,000-user population, including baseline-period records and users/days that are **not** present in the ML feature population. It retains 34 columns; injection modifies specified count fields only.
- **Final behavioral feature table** (`387,162` rows): eligible user-workdays in the **2011 future period** with recalculated behavioral features and `y`. Eligibility is defined as `is_weekend == 0` **and** `logon_count > 0`. **Do not** attempt to join the two files by row index.
- **Ground Truth**: two **positive-only** tables, at User-Day (9,080 rows) and User-Day-Channel (10,124 rows) grain. They are auditing/explanation artifacts; neither includes negative observations or the final binary `y` column.

## 2. Attack construction and population

The pipeline first evaluated real activity, channel availability, valid user/day windows, switching feasibility, and stealth constraints, then selected **400 distinct** attackers from the feasible pool. It did **not** mark every eligible user as an attacker.

### Final assigned scenarios (Notebook 08)

| Dimension | Distribution |
|---|---|
| Selected channel sets | EMAIL+USB **117** · EMAIL+HTTP **117** · USB+HTTP **27** · EMAIL+USB+HTTP **139** |
| Attack-window duration | **5** workdays: 50 users; **10/20/30/40/50** workdays: **70 users each** |
| Switching level | Low **133** · Medium **134** · High **133** |
| Stealth level | Low **133** · Medium **133** · High **134** |

**Important distinction:** These are **assigned window/scenario properties**, not proof that every day is attacked or that every selected channel is used on every active day. A 40/50-workday *attack duration* is not the same thing as a 40/50-workday *feature window*; final rolling features use up to **30 eligible workdays**.

### Execution, not just planned scenarios (Notebooks 09–11)

| Actual injected outcome | Count |
|---|---:|
| Active attack user-days | 9,080 |
| Single-channel attack days | 8,073 |
| Two-channel attack days | 970 |
| Three-channel attack days | 37 |
| Primary-channel switches in planned active-day sequence | 3,116 |
| Forced off-days with no injection | 1,670 |

| Channel | Executed channel-day actions | Added synthetic events |
|---|---:|---:|
| EMAIL | 6,703 | 17,791 |
| USB | 1,935 | 4,920 |
| HTTP | 1,486 | 6,296 |
| **Total** | **10,124** | **29,007** |

A **primary-channel switch** is a change in the planned primary attack channel between consecutive **active attack days**; forced off-days do not count as switching transitions. This scheduling definition is **different** from the dominant-channel computations in the ML features.

### Count-injection rule (selected in Notebook 06)

For the active user/channel/day, the number of **additional** events is:

`I = max(1, ceil(m × historical_user_channel_P95))`

| Stealth | Multiplier `m` | Interpretation |
|---|---:|---|
| **High stealth** | **0.25** | Fewer additional events |
| **Medium stealth** | **0.50** | Intermediate count |
| **Low stealth** | **0.75** | More additional events |

The same rule applies to all three channels. It uses the user's **fixed historical, channel-specific P95**; the historical reference is **never recalculated after injection**. Events are added to applicable count fields, not represented as real transferred documents, bytes, or payloads.

**Only these eight source User-Day fields were injection targets:** `external_email_count`, `email_send_count`, `email_event_count`, `usb_copy_count`, `file_copy_count`, `file_event_count`, `www_upload_count`, `http_event_count`. The other **26** original fields stayed unchanged. All 3,600 non-attacker users and all forced off-days were unchanged in the injected source table.

## 3. Final behavioral features (Notebook 12)

**143 columns total** = 85 original engineered columns + 30 additional behavioral columns + 27 new rotation/deviation columns + 1 binary target `y`. The 142 non-target columns **are not all automatically approved as ML predictors**: they include identifiers, time fields, and fixed historical references. See `feature_dictionary_r62_final.csv` for every column's definition, source, calculation, time scope, data type, nullability, role, and effective window policy.

The derived features capture historical-relative volume/intensity, cumulative deviations, changes in channel distribution, channel dominance/switches, temporal alternation, channel overlap/exclusivity, handoffs, and related rotation/stealth patterns. **Do not infer formulas from feature names alone**: some similarly named features use different dominant-channel definitions.

### Fixed historical baseline vs. current rolling context

- **Historical baseline:** 2010 reference period; immutable. Historical P50/P90/P95 and related baseline/active-rate statistics remain tied to that historical behavior.
- **Attack/future feature period:** 2011 eligible workdays; daily and rolling features are rebuilt from injected daily counts where relevant.
- **Eligible workday:** `is_weekend == 0` and `logon_count > 0`.
- **Rolling windows:** use the **current and preceding eligible workdays for the same user**, with no future rows and **no 2010 activity** included in rolling calculations.
- **Start-of-2011 policy:** **partial windows are valid** (`min_periods=1`). A 20-workday statistic may initially be based on fewer than 20 eligible days. This effective rule supersedes any earlier full-window startup wording in historical source dictionaries.
- **Window lengths:** original/additional features use **5/10/20/30 eligible-workday** windows as defined; new rotation group uses **5/10/20**.

### Two noninterchangeable definitions of dominant channel

1. **Dominant activity channel** — used by `dominant_channel_switches_{5,10,20,30}wd`: highest `Count_c / P95_c` among channels with valid historical P95. Exclude days without positive relative activity and days with approximately tied maxima (`np.isclose` with `rtol=1e-9`, `atol=1e-12`).
2. **Dominant deviation channel** — used by `nr_alt_*` and `nr_gap_alt_2_*`: highest positive `E_c = max(0, Count_c - P50_c) / max(1, P95_c - P50_c)`. Missing counts or historical statistics give `E=0`; `P50=0` is valid if observed. Ties are resolved **EMAIL → USB → HTTP**; all-zero deviation days have no dominant channel.

**These definitions are not equivalent to the primary attack-schedule switching rule.** They measure behavioral signal, not a copied attack-plan label.

### Missing values are intentional, not a failed export

Missing historical P90 ratios often reflect the **absence of recorded historical active days in that channel**, rather than zero current activity. The investigation found missing historical P90 in **312,211** eligible User-Day rows for USB and **328,257** for HTTP (none for EMAIL). Ratios without a positive valid P90 remain `NaN`. The final feature QA identified **16 columns containing missing values**.

Also review the constant columns `is_weekend` (always 0 because only eligible weekdays remain) and `unique_usb_extensions` (always 0 in this feature population; matched source but upstream extraction usefulness was not independently established).

## 4. Binary target and Ground Truth — crucial for correct ML evaluation

`y = 1` **if and only if** `(user, day)` is present among verified **positive injected** User-Day Ground Truth records; otherwise `y = 0`.

- An attacker's **non-injected** days are still `y=0`. **Do not label all rows from the 400 assigned users as positive**.
- The positive class counts **9,080 executed User-Days**, not the 10,124 channel actions or the 29,007 added events.
- `y=0` means **no synthetic injection on that User-Day**; it does **not** guarantee that the original CERT source activity is benign in every real-world sense.
- Ground Truth tracks executed attacks at two grains: **User-Day** (one positive row per attacked day) and **Channel-Day** (one row per injected channel/day). No separate user-level Ground Truth table was exported.
- Ground Truth and scenario/assignment/schedule/execution metadata are **evaluation and audit references**, **not** training predictors.

## 5. Model engineering checklist / recommendations

1. **Load the final Notebook 12 Parquet**, select `y` as the target, and build an **explicit predictor allowlist** from the 143-column dictionary. Do not blindly pass every column to the estimator.
2. **Exclude target and provenance leakage:** never use `y` as a feature. Do not join Ground Truth, schedules, execution logs, injected event increments, assigned scenario labels, stealth levels, or other attack metadata into predictors.
3. **Decide how to handle `user` and `day`:** they are keys/temporal identifiers, not automatically suitable predictors. Watch for identity memorization and calendar shortcuts.
4. **Design train/validation/test separation before preprocessing:** assess user-wise and/or chronological isolation according to the desired generalization claim. Because rolling features use earlier eligible days, review **cross-split history and temporal dependence** deliberately. Do not report random-row splitting as evidence of generalization to unseen users.
5. **Fit imputation/scaling/feature selection on training only.** Preserve or explicitly model `NaN` as missing historical evidence; replacing all missing values with zero would change their meaning.
6. **Review constant/low-information features**, especially `is_weekend` and `unique_usb_extensions`. Fixed baseline columns are documented but require separate feature-selection judgment.
7. **Address class imbalance:** `9,080/387,162 ≈ 2.345%` positives. Report precision, recall, F1, and **PR-AUC**; use confusion matrices and appropriate threshold evaluation rather than accuracy alone.
8. **Evaluate at the correct grain:** row-level predictions are **User-Day predictions**. To claim detection of channel rotation, add analysis of attack users, sequences, switching configurations, and error patterns where Ground Truth supports it; a single-day binary score alone does not demonstrate full sequence-level effectiveness.
9. **Version and preserve the handoff:** retain the feature dictionary, methodology file, QA report, and manifests alongside the Parquet. The actual schema is authoritative; avoid reconstructing feature formulas from memory.
10. **Limit claims:** computational QA and label reconstruction succeeded, but this does not prove model accuracy, realistic exfiltration of actual content, freedom from all leakage, or readiness for production. A new environment would require behavioral baseline recalibration.

## 6. File map — relative to repository root

All paths below start at `New_Attack_Simulation/`.

### Primary dataset and labels

| Purpose | File path |
|---|---|
| **Full injected User-Day** (intermediate) | `New_Attack_Simulation/reports/10_Attack_Injection_Pipeline/user_day_injected_counts_r62.parquet` |
| **Final ML behavioral dataset + `y`** | `New_Attack_Simulation/reports/12_Feature_Engineering_and_Validation/behavior_features_r62_ml_final_new.parquet` |
| **Complete final feature dictionary** | `New_Attack_Simulation/reports/12_Feature_Engineering_and_Validation/feature_dictionary_r62_final.csv` |
| **Positive-only User-Day Ground Truth** | `New_Attack_Simulation/reports/11_Ground_Truth_and_Quality_Validation/ground_truth_user_days_r62.parquet` |
| **Positive-only Channel-Day Ground Truth** | `New_Attack_Simulation/reports/11_Ground_Truth_and_Quality_Validation/ground_truth_channel_days_r62.parquet` |
| **Shared Ground Truth dictionary** | `New_Attack_Simulation/reports/11_Ground_Truth_and_Quality_Validation/ground_truth_data_dictionary.csv` |

### Methodology, evidence, and audit trail

| Purpose | File path |
|---|---|
| **Feature definitions and decisions** | `New_Attack_Simulation/reports/12_Feature_Engineering_and_Validation/feature_methodology_and_decisions.md` |
| **Final feature validation report** | `New_Attack_Simulation/reports/12_Feature_Engineering_and_Validation/final_feature_qa_report.md` |
| **Feature export manifest + SHA-256** | `New_Attack_Simulation/reports/12_Feature_Engineering_and_Validation/export_manifest.json` |
| **Assigned 400 attacker scenarios** | `New_Attack_Simulation/reports/08_Attacker_Selection_and_Scenario_Assignment/approved_attacker_scenarios_r62.parquet` |
| **Daily attack schedule** | `New_Attack_Simulation/reports/09_PreInjection_Dry_Run/daily_attack_schedule_r62.parquet` |
| **Actual injection execution log** | `New_Attack_Simulation/reports/10_Attack_Injection_Pipeline/injection_execution_log_r62.parquet` |
| **Selected count rule** | `New_Attack_Simulation/reports/06_Stealth_and_Injection_Count_Feasibility/selected_injection_rule.json` |
| **Notebook 11 provenance and QA** | `New_Attack_Simulation/reports/11_Ground_Truth_and_Quality_Validation/notebook_summary.md` |

Additional notebooks and per-stage `notebook_summary.md` files explain upstream feasibility and auditing choices.

## 7. Evidence of dataset validation

| Validated item | Reported result |
|---|---|
| Injected User-Day independent end-to-end QA | **43/43 PASS** |
| Ground Truth source reconstruction | **10,124 channel actions; 29,007 events; 9,080 positive user-days**, zero key/event/label mismatches |
| Original feature dependency audit | **32,908,770 values**, zero mismatches |
| Additional 30-feature independent checks | **107,970 sampled values**, zero numerical/NaN mismatches |
| Additional 27 rotation-feature independent checks | **226,314 sampled values**, zero numerical/NaN mismatches |
| Comprehensive feature integrity | **108 checks**, zero failures |
| Feature documentation | **143/143 columns** included |
| Final export | SHA-256 checksums for four primary Notebook 12 artifacts in export manifest; independent post-export verification completed in Notebook 12 |

**Verification boundary:** The post-export full-frame check accounted for a Parquet datetime storage-unit difference in `day` (`datetime64[s]` versus `datetime64[ms]`) by normalizing the comparison copies only; the saved data was not modified. The final notebook run reported **32/32 post-export integrity checks passed**.

## 8. Quick-start example (illustrative; not a validated model pipeline)

```python
from pathlib import Path
import pandas as pd

root = Path('New_Attack_Simulation')  # set this to your local clone location
p = root / 'reports/12_Feature_Engineering_and_Validation'
features = pd.read_parquet(p / 'behavior_features_r62_ml_final_new.parquet')
dictionary = pd.read_csv(p / 'feature_dictionary_r62_final.csv')

assert features.shape == (387_162, 143)
assert features[['user', 'day']].duplicated().sum() == 0
assert features['y'].value_counts().to_dict() == {0: 378_082, 1: 9_080}

# Keep user/day as keys for grouping, time-aware splits, and evaluation.
# Choose predictor columns explicitly after reviewing the dictionary;
# never assume all columns except y are approved training features.
keys = features[['user', 'day']].copy()
y = features['y'].copy()
```

---

### What this handoff does **not** claim

This package documents a **synthetic event-count injection and behavioral feature engineering** experiment. It does **not** document transfer of real files, actual exfiltrated byte volumes, guaranteed real-world attack realism, or achieved predictive performance. Model training, holdout evaluation, threshold selection, and production adaptation remain the responsibility of the model-development phase.
