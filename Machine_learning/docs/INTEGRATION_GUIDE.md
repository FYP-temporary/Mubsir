# Integration guide: the trained model inside the system + its outputs for the dashboard

Everything in this guide is based on the actual files in `model/` and on an actual run of them from a clean copy (316 rows of `example_input.parquet` in 0.018 seconds).

---

## Part 1: How to place the model as a pre-trained model in the system

### What the "model file" is
The whole `model/` folder is one unit (3.4 MB):

| File | Role |
|---|---|
| `lgbm_w5.txt` / `lgbm_w10.txt` / `lgbm_w20.txt` | Three LightGBM models in their native text format (no pickle, no joblib) |
| `manifest.json` | The version, **the order of the 75 features of each model**, the calibration coefficients (Platt), the 60/85 thresholds |
| `mubsir_infer.py` | The class `MubsirScorer`: loads the above and produces the scores, levels and SHAP |

Dependencies: only numpy, pandas and lightgbm (`model/requirements.txt`, tested with versions 2.5.3 / 3.0.5 / 4.7.0). There is no scaler and no encoder because trees do not need them, and NaN is handled internally.

### Steps

1. **Copy `model/` to the analysis service** (for example `/opt/mubsir/model`) and install the requirements.
2. **Verify the integrity of the files, then load the model once when the service starts**, not on every request (the value `PINNED_ROOT_HASH` is stored in the deployment configuration or the approval ticket, and it is recorded in `docs/RELEASE_HASHES.md`; the presence of `version` in the manifest alone does not prove integrity):
   ```python
   import sys; sys.path.insert(0, "/opt/mubsir/model")
   from verify_bundle import verify_bundle
   verify_bundle("/opt/mubsir/model", expected_root_sha256=PINNED_ROOT_HASH)   # raises BundleIntegrityError on any missing, modified or extra file
   from mubsir_infer import MubsirScorer
   scorer = MubsirScorer("/opt/mubsir/model")      # reads the manifest + the three models
   ```
3. **Prepare the input:** one table with one row per (user, workday) containing the columns `user` and `day` and the 77 columns listed in `manifest["input_columns_all"]` (each model uses 75 of them). The order does not matter, extra columns are ignored, and a missing column raises a clear error.
4. **Call:**
   ```python
   rows  = scorer.score(features_df)               # (user, day) level
   users = scorer.score_users(rows)                # user level (peak)
   why   = scorer.explain(features_df.iloc[[i]], window=10, top_k=5)   # SHAP for one row
   ```
5. **Write the results to the database** (the mapping is in Part 2), and store the model version with every prediction; it can be built from `manifest["version"]` and the window number (for example `mubsir-1.0-w10`).
6. **When the model is replaced later:** put a new folder with the same interface; the thresholds, the calibration and the feature order all come from `manifest.json`, so do not modify the code.

### Conditions without which the model does not work

| Condition | Why |
|---|---|
| **The features must be computed in the same way as in training** (rolling windows over the last 30 workdays, and the P50/P90/P95 baseline from 2010) | The model sees only the numbers; a feature computed differently gives a meaningless score with no visible error |
| **A feature extractor from the raw logs** | It is not part of this delivery. The 27 features I added are precisely defined in `FEATURE_GENERATION_CONTRACT.md` with a reference implementation (`pipeline/verify_feature_contract.py`) and golden test cases (`docs/golden_feature_cases.json`); the team's 36 features need their code. The extractor is tested by comparing its output with the stored feature values |
| Workdays | The features depend on the sequence of workdays (logon), so the extractor must know them |
| `unique_usb_extensions` | **Not a model input** (always zero in the team's data because of a regex bug, and it was excluded), so the extractor does not need it |
| Validity limits | Trained on CERT r6.2 simulation data (796 users), and not tested on other data |

---

## Part 2: Model outputs that can be passed to the dashboard

### A) (user, day) level: `scorer.score(...)`

| Column | Meaning | Suggested use in the dashboard |
|---|---|---|
| `user`, `day` | The identifiers | Row key |
| `risk_5`, `risk_10`, `risk_20` | The risk 0–100 for each window | Risk curve over time for each window |
| `level_5`, `level_10`, `level_20` | Low / Medium / High for each window | A badge for each window |
| `score_raw_5/10/20` | The raw probability before calibration | For auditing only |
| `risk` | The highest risk among the windows | The main number for the day |
| `level` | The level of the day | Row color |
| `alert` | True if `risk > 85` | Generates an alert |
| `alert_windows` | The windows that raised the alarm, such as `5,10,20` | Shows which time horizon triggered the alert |

### B) User level: `scorer.score_users(rows)`

| Column | Meaning |
|---|---|
| `risk_5_peak`, `risk_10_peak`, `risk_20_peak`, `risk_peak` | The user's highest risk for each window and overall |
| `level`, `alert` | The user's level and whether the user was alerted |
| `peak_day` | The peak day |
| `first_alert_day` | The first High day, which is the most important field for investigation (empty if the user was never alerted) |
| `n_days` | The number of evaluated days |

A real example from `example_input.parquet`: user NVH3726 has a peak of 99.9 and a first alert on 2011-01-31, and user SHB3512 has a peak of 53.7 (Low) with no alert.

### C) Explanation: `scorer.explain(...)` (SHAP)
One row per (prominent feature, window): `rank`, `feature`, `family`, `value`, `shap` (in log-odds units, positive raises the risk), `effect` ("raises risk" / "lowers risk"), and `base_logodds`, `logodds` and `risk`.
- In the real example: the highest contribution for NVH3726 was `cumulative_deviation_10wd = 11.3` with a contribution of +4.43, then `email_event_count = 17` (+1.60).
- `explain_text()` gives a readable line ready for display.
- Display advice: show the top 3–5 contributions with `family` (email / USB / HTTP / accumulation-shift / rotation), and see `FEATURE_DEFINITIONS_ROTATION.md` to turn the feature names into understandable sentences.

### D) Fixed information about the model (does not change with each run)
- `scorer.thresholds()`: the two thresholds 60 and 85 on the risk scale and their raw equivalents for each window.
- `manifest.json`: the version, the creation date and the algorithm.
- An optional "About the model" page from the files: the global SHAP importance (`pipeline/results/shap75/shap_families.csv`), the confusion matrices (`docs/figures/`), and the fixed-threshold metrics (`pipeline/results/fixed_bands_*.csv`).

### How the risk is read (important for the dashboard)
The risk is the **calibrated probability × 100** that the user is inside an exfiltration window; it is not the size of the deviation. The composition of the levels on the test data (199 users, LightGBM, measured):

| Level | Rows (window 10) | Share of actual attack in the rows | Users (any window) | Of which attackers |
|---|---|---|---|---|
| Low (≤60) | 83.0% of the rows | 3.9% | 65 | 2 |
| Medium (60–85) | 2.4% | 73.8% | 3 | 2 |
| High (>85) | 14.6% | 98.7% | 131 | 130 |

That is, High is very reliable, Medium is a review zone (about three of every four rows in it are an actual attack), and Low is not an absolute guarantee (it includes two attackers out of 134).

### Mapping the outputs to the current database schema (without modifying it)

| Table / column | What is written |
|---|---|
| `behavior_features.feature_values_jsonb` | The 75 features of the window model, one row per window (`window_workdays` = 5, 10 or 20) |
| `model_prediction_outputs.model_version` | For example `mubsir-1.0-w10` |
| `…risk_score` | `risk_h` (0–100) |
| `…risk_classification` | `level_h` (Low/Medium/High) |
| `…shap_explanation_jsonb` | `score_raw`, `base_logodds` and the top 5 contributions |
| `security_alerts` | A row when `alert = True`; grouping consecutive days into an incident is done in code |
| User summary | Computed by a query or by `score_users`, and does not need a new table |
