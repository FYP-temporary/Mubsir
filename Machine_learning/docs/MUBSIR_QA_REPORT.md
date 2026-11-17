# Mubsir — Answers to the six questions: training, splitting, features, the saved model, inference and SHAP

**Context:** detection of low-and-slow data exfiltration that rotates between channels (Email / USB / HTTP) on the simulated CERT r6.2 data (995 users: 670 injected attackers and 325 normal users). One model per time window (5, 10 and 20 workdays). All numbers below are computed from the actual result files, and each place states whether it comes from the **test set** (199 users not used in any decision) or from **cross-validation** (5×3 CV on the development users).

**Basic definitions used in all sections:**
- **Risk score (risk 0–100):** the calibrated probability ×100 that the user on that day is inside an exfiltration window. It is not a linear measure of the size of the deviation; the deviation enters through the features (the strongest is `cumulative_deviation`).
- **Levels (two fixed thresholds, 60 and 85):** Low: risk ≤ 60 · Medium: 60 < risk ≤ 85 · High: risk > 85. Alert = High.
- **User risk** = the user's highest risk (peak) during the monitoring period, and the overall result = the maximum among the three windows.
- **PR-AUC:** the area under the Precision–Recall curve. **FPR:** the share of normal users who were alerted wrongly. **Recall@1%FPR:** the share of attack rows detected at a threshold that allows a false alarm for 1% of the normal users' rows.

---

## 1) Training & Evaluation — which models were trained, what are their results, and which is best?

### 1.1 The models that were trained
- **First stage (algorithm comparison):** five algorithms were trained: DecisionTree, RandomForest, LightGBM, XGBoost and CatBoost, on an earlier feature set (87 features). The single tree and the random forest were excluded from the report text, and the comparison with them was not repeated on the final set.
- **Final stage (fair comparison):** **LightGBM** and **XGBoost** on **the same feature set (75 features per window)**, with the same split, the same seeds, the same calibration protocol and their default settings. Three models per algorithm (windows 5, 10 and 20).
- **Hyperparameter tuning:** an Optuna search (60 trials per window, with PR-AUC as the objective) was run on LightGBM, and the improvement did not exceed the adoption threshold agreed in advance (≥ 0.005 in Recall@1% without a PR-AUC decline), so the **default parameters** were adopted. Note: an experimental second stage (predicting the continuation of the attack) exists in the project but is outside the scope of these answers.

### 1.2 Results on the test set (199 users: 134 attackers and 65 normal) — row level
The metrics at a threshold that allows FPR = 1% of the normal users' rows:

| Window | Model | PR-AUC | Recall | Precision | F1 |
|---|---|---|---|---|---|
| 5 | LightGBM | 0.962 | 0.860 | 0.944 | 0.900 |
| 5 | XGBoost | 0.963 | 0.859 | 0.944 | 0.900 |
| 10 | LightGBM | 0.958 | 0.833 | 0.952 | 0.889 |
| 10 | XGBoost | 0.958 | 0.831 | 0.952 | 0.887 |
| 20 | LightGBM | 0.952 | 0.800 | 0.963 | 0.874 |
| 20 | XGBoost | 0.952 | 0.798 | 0.963 | 0.873 |

### 1.3 Results using the two fixed thresholds 60/85 — test set
**User level** (alert = the user's maximum risk > 85; TP/FN/FP/TN out of 134 attackers and 65 normal users):

| Scope | Model | TP/FN/FP/TN | Recall | Precision | F1 | FPR |
|---|---|---|---|---|---|---|
| Max of windows | LightGBM | 130/4/1/64 | 0.970 | 0.992 | 0.981 | 0.015 |
| Max of windows | XGBoost | 129/5/1/64 | 0.963 | 0.992 | 0.977 | 0.015 |
| Window 5 | LightGBM | 129/5/1/64 | 0.963 | 0.992 | 0.977 | 0.015 |
| Window 10 | LightGBM | 127/7/1/64 | 0.948 | 0.992 | 0.969 | 0.015 |
| Window 20 | LightGBM | 124/10/1/64 | 0.925 | 0.992 | 0.958 | 0.015 |

When Medium and High are counted together (> 60) with the maximum of the windows: LightGBM gives 132/2/2/63 (Recall 0.985, Precision 0.985, F1 0.985, FPR 0.031), and XGBoost gives 131/3/3/62 (Recall 0.978, Precision 0.978, F1 0.978, FPR 0.046).

**Row level** (High): Precision 0.98–0.99 and FPR 0.2–0.3% but Recall 0.71–0.76 (the first days of an attack score lower; a user is usually detected before all of their days are detected).

### 1.4 Results in 5×3 cross-validation (development users, 15 folds)
| Window | Model | PR-AUC | Recall@1%FPR | Recall@5%FPR |
|---|---|---|---|---|
| 5 | LightGBM | 0.954 | 0.829 | 0.927 |
| 5 | XGBoost | 0.953 | 0.826 | 0.927 |
| 10 | LightGBM | 0.949 | 0.805 | 0.903 |
| 10 | XGBoost | 0.948 | 0.799 | 0.903 |
| 20 | LightGBM | 0.944 | 0.769 | 0.871 |
| 20 | XGBoost | 0.944 | 0.764 | 0.871 |

With the fixed thresholds in CV (user level, maximum of windows, High, mean ± deviation over 15 folds): LightGBM Recall 0.975 ± 0.023, Precision 0.989 ± 0.010, F1 0.982 ± 0.012, FPR 0.023 ± 0.021; XGBoost Recall 0.970 ± 0.023, Precision 0.990 ± 0.010, F1 0.979 ± 0.012, FPR 0.021 ± 0.020.

### 1.5 What each risk band means (band content, test set)
| Band | Rows (window 10) | Share of its rows that are actually in an attack | Users (max of windows) |
|---|---|---|---|
| Low ≤ 60 | 83% | 3.9% | 65 users (only 2 attackers = 3.1%) |
| Medium 61–85 | 2.4% | 73.8% | 3 users (2 attackers) |
| High > 85 | 14.6% | 98.7% | 131 users (130 attackers, 1 normal) |

The Medium band is very narrow because the distribution of the scores leans toward the two poles (near 0 or near 100).

### 1.6 Which model is best?
**LightGBM**, by a nominal margin that is not statistically significant:
- In the test and the CV, LightGBM leads on most metrics (Recall@1% by 0.003–0.005, PR-AUC by 0.0003–0.0009 in CV, and user-level Recall by +0.005 to +0.007), but the paired differences across the 15 folds are smaller than the standard deviation (0.001–0.012) and it won in only 8 of the 15 folds on the main user metric.
- Precision and FPR are nearly identical (0.99 and 1.5–2%).
- LightGBM is preferred for practical reasons: faster training (in our run, training the three windows took about half the time of XGBoost), native support for missing values, and storage in a simple text format without pickle.

### 1.7 Caveats
The test numbers rest on only 65 normal users, so one normal user changes the FPR by about 1.5 points; the confidence intervals (bootstrap) are wide (for example, Recall@1% for window 20 is between 0.74 and 0.84). All results are on simulated CERT r6.2 data and were not tested on operational data.

---

## 2) Data Splitting — how was the data split, and did we make sure there is no overlap?

### 2.1 The design
1. **Test:** 199 users (134 attackers + 65 normal) by `StratifiedGroupKFold` (the first of 5 folds) grouped by `scenario_id` and stratified by group × stealth level. This set was not used in training, calibration, thresholds, or the choice of model or features.
2. **Development:** 796 users (536 attackers + 260 normal).
3. **Validation:** 5×3 cross-validation (5 folds × 3 repetitions with different seeds) inside development, with the same grouping by scenario.
4. **Early stopping:** 15% of the training users of each fold (also grouped by scenario) are held out to stop training early, and they enter neither the training nor the validation.
5. **Calibration and reference thresholds:** from the out-of-fold scores of development only (Platt scaling).
6. **The final model** is retrained on all 796 development users with a number of trees = the average number of trees in CV.

### 2.2 Overlap checks (actually executed)
| Check | Result |
|---|---|
| Users shared between development and test | **0** |
| Scenarios shared between development and test | **0** |
| Shared (user, day) pairs | **0** |
| User overlap between training and validation in the 15 folds | **0** |
| Scenario overlap between training and validation in the 15 folds | **0** |
| Overlap of training with the early-stopping part (users and scenarios) | **0** |
| Use of test users in any development step | No |

**The importance of grouping by scenario:** 505 of the 995 users share duplicated attack templates (reused template); if the split were by user only, the same template would appear in training and test and the results would be inflated.

### 2.3 Time windows
- All rows of one user fall on one side only, so the training and test windows of a single user do not intersect.
- **Every feature is causal:** the value on day t uses the workdays up to t only, and the baseline (P50/P90/P95) is from 2010 only. I verified this with a literal implementation against the pipeline on thousands of cells (0 differences) for the features I built, and by matching `cumulative_deviation` with the team's column.
- **Target:** `y_h` = 1 if the user is on an attack day within the last h workdays (the current day included), so it uses no future information.
- **Explicit warning:** the split is **by user and not by time**. The development and test sets cover the same period (3 January–1 June 2011). There is no user overlap, but the results do not prove generalization to a later period.

---

## 3) Features & Labels — the data file and the columns

### 3.1 The adopted data file
- **The base:** `prepared_995.parquet` (103,395 rows × 125 columns; one row per user/workday, 995 users) built from `behavior_features_r62_ml_final`.
- **Additions built on top of it (by the key user+day):** the evidence features (`18_build_evidence_features.py`), the features of `21_build_final_features.py` (`nr_alt`, `nr_stealth_acc` and the P90 ratios), and the feature `nr_gap_alt_2` (`25_build_gap_alt.py`).
- The final inputs of the models: **77 columns** in total; each model uses **75** (the 74 agreed + `nr_gap_alt_2` of its window).

### 3.2 The features used (74 shared + 1 per window)
**Basic (41):**
`email_event_count`, `external_email_count`, `external_email_count_{5,10,20,30}wd`, `email_active_days_{5,10,20}wd`, `email_count_to_p95_ratio`, `email_count_to_p90_ratio`, `usb_copy_count`, `usb_copy_count_{5,10,20,30}wd`, `usb_active_days_{5,10,20}wd`, `file_event_count`, `unique_usb_files`, `usb_copy_to_p95_ratio`, `usb_copy_to_p90_ratio`, `http_event_count`, `www_visit_count`, `www_upload_count`, `http_upload_count_{5,10,20,30}wd`, `http_active_days_{5,10,20}wd`, `http_upload_to_p95_ratio`, `http_upload_to_p90_ratio`, `unique_external_recipients`, `unique_external_domains`, `unique_upload_domains`, `unique_domains`, `emails_with_attachments`, `attachment_count`.

**Accumulation and shift (12):** `cumulative_deviation_{5,10,20,30}wd`, `consecutive_elevated_days_{5,10,20,30}wd`, `channel_distribution_shift_{5,10,20,30}wd`.

**Rotation `nr_*` (21 = 7 × {5,10,20}wd):** `nr_m`, `nr_entropy`, `nr_excl_days`, `nr_overlap_days`, `nr_alt`, `nr_handoff`, `nr_stealth_acc`.

**The experimental feature (1 per model):** `nr_gap_alt_2_5wd`, `_10wd` or `_20wd` (the rate of change of the dominant channel between adjacent deviation days, provided they are separated by no more than two quiet workdays; its full definition is in `FEATURE_DEFINITIONS_ROTATION.md`).

### 3.3 The target
`y_5` for model 5, `y_10` for model 10, and `y_20` for model 20. The share of positives in development: 16.6%, 19.5% and 24.7%.

### 3.4 The excluded columns
| Excluded | Reason |
|---|---|
| `user`, `day`, `first_logon`, `last_logoff`, `is_weekend` | Identity/time, does not generalize |
| `y`, `y_5/10/20`, `yf_5/10/20` | Labels (the target or its future-looking derivatives) |
| `group`, `stealth`, `scenario_id` | Scenario/split data |
| 23 constant per-user baseline columns (such as `email_count_p50/p90/p95`, `usb_copy_p95`, `http_upload_p95`, `*_active_rate`, `*_mad`, `baseline_workdays`) | Constant values per user that allow "memorizing its identity"; only their ratios (to_p95_ratio) were kept |
| **Ground Truth:** `is_attack_day`, `is_scheduled`, `day_status`, `planned_channels`, `injected_channel_count`, `injected_email`, `injected_usb`, `injected_http`, `injected_events_total`, `stealth_level` | Ground truth; **did not enter any model** (I verified that none of them is among the 77 columns) |
| `unique_usb_extensions` | All zeros because of a regex bug (an extra escape) in the team's processing, no value |
| `combined_channel_intensity`, `dominant_channel_switches_30wd`, `email_bytes_to_p95_ratio` | Dropped by a design decision |

Note: the name `nr_stealth_acc` contains the word stealth, but it is computed from the behavior counters and P95 only, and has nothing to do with the stealth column in the ground truth.

---

## 4) Saved Model — the saved model

**The folder `model/` (3.4 MB, previously named mubsir_bundle):**
| File | Content |
|---|---|
| `lgbm_w5.txt`, `lgbm_w10.txt`, `lgbm_w20.txt` | The three models in the native LightGBM text format (no pickle; 328, 337 and 288 trees) |
| `manifest.json` | The **feature order** of each window (75 names), the calibration coefficients (Platt) of each window, the 60/85 thresholds, the 77 required columns, the target definition |
| `mubsir_infer.py` | The scoring and explanation function (needs only numpy, pandas and lightgbm) |
| `example_input.parquet` | An input example (3 users) |
| `README.md` | Usage and the contract |

**Preprocessing:** there is none. No normalization and no encoding; tree models are not affected by the scale of values, and LightGBM handles missing values (NaN) natively. All the bundle depends on is: **the column order** (applied automatically from the manifest) and the **calibration** coefficients.

**Verification of running without retraining:** the bundle was copied to a separate folder and run from a new Python process on the test features, and it returned exactly the same saved results (130/4/1/64 for the maximum of windows, and 129/5/1/64, 127/7/1/64 and 124/10/1/64 for the three windows), and the raw scores matched the original model.

**Limits:**
- The bundle receives **ready-made features**; building the features from the raw logs (scripts 18, 21 and 25 and the team's data) is not yet packaged and has not been tested on data from outside the project.
- The models are trained on 796 users (not all 995), and on simulated data.

---

## 5) Inference & Outputs — inference and outputs

**Usage:**
```python
from mubsir_infer import MubsirScorer
import pandas as pd
sc   = MubsirScorer("model")                 # loads the manifest + the models
X    = pd.read_parquet("example_input.parquet")      # user, day + the 77 columns
rows = sc.score(X)                                   # outputs for each day
users= sc.score_users(rows)                          # outputs for each user
```

**The row outputs of `score()`:** `user`, `day`, `score_raw_{5,10,20}` (the raw probability), `risk_{5,10,20}` (0–100), `level_{5,10,20}` (Low/Medium/High), `risk` (the maximum among the windows), `level`, `alert` (true when the risk of any window exceeds 85), `alert_windows` (the windows that raised the alert).

**The user outputs of `score_users()`:** `risk_{5,10,20}_peak`, `risk_peak` (the maximum), `level`, `alert`, `n_days`, `peak_day`, `first_alert_day`.

**The score formula:** `risk = 100 × sigmoid( a × logit(raw) + b )` where (a, b) are the Platt coefficients of each window (window 5: 0.948 and 0.093; window 10: 0.922 and 0.028; window 20: 0.930 and −0.022).

**The thresholds used for the alert:**
| Limit | Value (risk scale) | Level |
|---|---|---|
| Low | risk ≤ 60 | Low |
| Medium | 60 < risk ≤ 85 | Medium |
| High | risk > 85 | High — **issues an Alert** |

The limits 60 and 85 are fixed (a project decision) and are not tuned on any data. The thresholds taken from percentiles (95 and 85 of the normal users' scores) are stored in the manifest for reference only and are not used. The raw equivalents are used through `sc.thresholds()` when needed.

**Function behavior:** the column order does not matter, extra columns are ignored, a missing column raises an error that names the missing columns, and missing values are accepted.

---

## 6) SHAP — the explanation for each prediction

**The method:** TreeSHAP (exact for LightGBM models) via `pred_contrib` in the same library; the shap library is not needed for inference. The contributions are on the log-odds scale of the raw score: **the sum of the contributions + the base value = logit(the raw score)** (I verified the sum, maximum error 5×10⁻¹⁴). A positive value raises the risk and a negative one lowers it.

**Usage:**
```python
sc.explain(X.iloc[[i]], window=10, top_k=5)      # table: rank, feature, family, value, shap, effect, risk
sc.explain_text(X.iloc[[i]], 10, 5)              # a readable line
```
The output columns: `row`, `user`, `day`, `window`, `rank`, `feature`, `family`, `value`, `shap`, `effect` (raises/lowers the risk), `base_logodds`, `logodds`, `risk`.

**A real example — a correct alert (an attacker user, 2011-03-01, window 10, risk 99.9, High):**
| Rank | Feature | Value | Contribution |
|---|---|---|---|
| 1 | `cumulative_deviation_10wd` | 11.33 | +4.43 |
| 2 | `email_event_count` | 17 | +1.60 |
| 3 | `cumulative_deviation_5wd` | 8 | +1.53 |
| 4 | `cumulative_deviation_20wd` | 20.42 | +1.04 |
| 5 | `external_email_count_20wd` | 91 | +0.64 |

**A missed attack example (2011-04-12, risk 53.7, Low):** the top contributions are `http_event_count=95` (+0.97), `email_event_count=10` (+0.89), `unique_upload_domains=3` (−0.82), but the accumulated deviation was not enough to raise the risk above 60, which is the pattern of misses that we observed: short attacks on a single channel.

**Global explanation of the models (on the test set):**
- The share of the families in the total |SHAP|: accumulated deviation and shift 31% (window 5), 35% (10) and 40% (20); email 29%, 24% and 19%; the rotation features `nr_*` 13%, 16% and 17%; HTTP about 10–12%; USB 8–11%; the feature `nr_gap_alt_2` below 0.5%.
- **The accumulated deviation** is the strongest feature in the three windows (mean |SHAP| from 0.86 to 1.46).
- The rotation features add a small but consistent gain: removing them lowered the cross-validated Recall@1%FPR by 0.005 to 0.009 and the PR-AUC by 0.0016 to 0.0039, and the gain grows with the window length; the accumulated deviation features remain the main dependence of the models.
- Two features have the opposite direction to what is expected (`http_event_count` and `unique_usb_files`: higher values lower the risk); their likely explanation is that they act as a normalizing context; this has not yet been tested.
- SHAP explains the model's behavior, not the real mechanism of the attack.

**The files:** `results/shap75/` (the importance, the families, the direction, the cases and the plots), and `27_shap.py` and `29_shap75.py`.

---

## Appendix: the main files
`22_final_model.py` (74 features), `28_final75.py` (75 features), `31_xgb75.py` (XGBoost-75), `32_fixed_bands.py` and `33_cv_fixed_bands.py` (the fixed thresholds), `30_export_bundle.py` (the bundle), `model/`, and the results in `pipeline/results/final75_*`, `results/xgb75_*`, `results/fixed_bands_*` and `results/cv75_fixed_bands_*`.
