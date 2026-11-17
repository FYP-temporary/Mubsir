# Release Verification Report

Every number here comes from an actual run on 2026-11-15; the raw logs are in `docs/pytest_log.txt`, `docs/verify_release_log.txt`, `docs/reproducibility_log.txt` and `docs/feature_contract_log.txt`.

**Environment:** Linux x86_64, Python 3.13.18, lightgbm 4.7.0, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1, xgboost 3.4.1, pytest 9.1.1, two cores.

## Summary

| Check | Tool | Result |
|---|---|---|
| Model contract tests (11) and bundle integrity (3) | `pytest tests` (needs no data) | 14 / 14 passed |
| The definitions of the 27 added features match the stored values | `pipeline/verify_feature_contract.py` | 165,051 cells and 3 golden cases, 0 differences (see `FEATURE_GENERATION_CONTRACT.md` §7) |
| Hashes of the bundle, the models, the data and the logs | `pipeline/35_write_release_hashes.py` | `model/SHA256SUMS.txt` + `docs/RELEASE_HASHES.md` |
| Release checks with the data (30 checks) | `pipeline/verify_release.py` | 30 / 30 passed (also inside the team repository layout, item 6) |
| Re-deriving the calibration and thresholds from scratch in an isolated copy | `30_export_bundle.py` | Exact match (see 4) |
| Repository free of personal paths, emails and keys | Text search | Nothing found (see 5) |

## 1) Contract tests (`tests/test_bundle.py`)
- **Manifest integrity:** 3 windows, each model has 75 features with no duplicates, 74 shared, 77 distinct columns, and the number of trees in the manifest (328 / 337 / 288) equals the number in the saved model file, and the calibration coefficient is positive (monotonically increasing).
- **Leakage guard:** no label or ground-truth column (`is_attack_day`, `scenario_id`, `y_*`, `injected_*` …) and none of the 23 constant baseline columns is among the model inputs.
- **Thresholds:** 60 → Low, 60.0001 → Medium, 85 → Medium, 85.0001 → High, and the two thresholds convert from the risk scale to the raw scale and back to 60 and 85 with a precision better than 1e-6.
- **Contract:** the outputs are within [0, 100], the level matches the risk, `alert` equals (risk > 85), the column order has no effect (difference below 1e-12), extra columns are ignored, a missing column raises `ValueError`, and NaN is accepted.
- **SHAP:** the sum of the contributions + the base value = the log-odds of the raw score (below 1e-9), and the risk computed from SHAP matches `risk_10`.
- **Expected results on `example_input.parquet`:** NVH3726: High, peak > 99.8, first alert 2011-01-31; DBF3582: High, first alert 2011-05-23; SHB3512: Low with a peak of 53.7 and no alert.

## 1b) Bundle integrity tests (`tests/test_integrity.py`)
- All files of `model/` match `SHA256SUMS.txt`, and the list includes the three models, the manifest and the inference code.
- Modifying a single byte in the manifest, deleting a model, or adding an unlisted file: all are rejected (`BundleIntegrityError`).
- Replacing a model **while regenerating the hash list**: only pinning the root hash (the hash of the list itself) detects it, which is what the third test checks. Therefore the root hash must be kept outside the model folder.

## 2) `verify_release.py` checks (need `pipeline/data/`)

**Data and split integrity**
- The ten data files match `SHA256SUMS.txt`.
- The development users (796) and test users (199) are disjoint, and together they total 995.
- The split re-derived from the code = `results/final_split.csv`.
- No attack template (`scenario_id`) is shared between development and test (270 versus 67 templates).
- No (user, day) pair is shared between the two sets (82,761 versus 20,634 user-days).
- Test composition: 134 attackers + 65 normal users.

**Inputs:** none of the 31 forbidden columns (labels and ground truth) is among the 77 columns, and no constant baseline column; the feature list of each window in the manifest equals the training list `F75(h)` literally.

**Model equivalence:** the joblib model (sklearn) and the bundle model (the native booster) give the same scores on 20,634 test rows in the three windows (maximum difference = 0.0).

**Confusion matrices recomputed from the bundle and compared with the stored tables** (TP / FN / FP / TN, all matching):

| Level | Window | High (>85) | Medium + High (>60) |
|---|---|---|---|
| Users | 5 | 129 / 5 / 1 / 64 | 132 / 2 / 2 / 63 |
| Users | 10 | 127 / 7 / 1 / 64 | 131 / 3 / 1 / 64 |
| Users | 20 | 124 / 10 / 1 / 64 | 131 / 3 / 1 / 64 |
| Users | any window | **130 / 4 / 1 / 64** | 132 / 2 / 2 / 63 |
| Rows | 5 | 2602 / 804 / 50 / 17178 | 2929 / 477 / 174 / 17054 |
| Rows | 10 | 2976 / 1024 / 40 / 16594 | 3337 / 663 / 168 / 16466 |
| Rows | 20 | 3601 / 1469 / 43 / 15521 | 4096 / 974 / 181 / 15383 |

At High in any window: Recall = 130/134 = 0.970, Precision = 130/131 = 0.992, and FPR = 1/65 = 0.0154.

**Band content (test rows, window 10):** Low = 83.0% of the rows with an attack share of 3.9%; Medium = 2.4% with a share of 73.8%; High = 14.6% with a share of 98.7%.

## 3) A discovery during verification (corrected)
The check comparing the saved split with the split actually used failed. The cause: the `part` and `rep*` columns in `results/user_split.csv` come from the old `02_split.py` (a random split stratified by user, not by template), and they match the final pipeline's test set for **only 42 of 199 users**. The final pipeline (22, 28, 31 and 33) builds a split grouped by `scenario_id` in the code and does not read these columns, so **there is no effect on any reported result**. The correction:
- I added `34_save_final_split.py`, which saves the actual split to `results/final_split.csv`.
- I added a comment in `02_split.py` stating that it is legacy.
- I corrected the table in `pipeline/README.md`, which wrongly described `02_split.py` as producing the grouped split.
- I replaced the check with a comparison of the derived split against `final_split.csv`, and kept an INFO line documenting the old overlap.

## 4) Re-derivation from scratch (isolated copy)
I re-ran `30_export_bundle.py` in a temporary copy (60 seconds): it retrains 15 CV models (5 folds × 3 windows) and derives the calibration coefficients and the reference thresholds, and asserts that they equal the ones stored in the joblib files. The results:
- The assertions passed for all windows (the raw thresholds equal the stored ones to 1e-9).
- The resulting `manifest.json` is **byte-for-byte identical** to the one in `model/`: the coefficients `0.948 / 0.093`, `0.922 / 0.028` and `0.930 / −0.022` for windows 5, 10 and 20.
- This proves that the training is deterministic in this environment with seed 42.

## 5) The repository
A text search over all repository files (except binary files) for personal names, emails, Windows paths and the words `token/api_key/password/secret`: **no results**. The largest file uploaded to git: `cv75_oof_LightGBM.npz` (5.6 MB), and all are far below the GitHub limit (100 MB per file). The data files (63 MB) are excluded in `.gitignore`.

## 6) Upload and run test inside the team repository layout (`FYP-temporary/Mubsir`)
I inspected the public repository and copied it locally for reading, then tried the upload on a local copy of the `reef-ml` branch without pushing anything:
- **Data match:** the six original files that the pipeline reads exist in the branch `remas-mushabbab-attacks-generator` (folder `Clear_Attack_Simulation/`) and are **byte-for-byte identical** (SHA-256) to what the model was trained on.
- **Regeneration from the team's data:** from the data of that branch alone I regenerated the four derived tables (`01`, then `14b`, then `18`, then `21`, then `25`), and they came out **identical** to what the model was trained on (the same shapes, columns and values, and a SHA-256 match for all of them in `verify_release.py`).
- **Then `verify_release.py` without modification inside the layout `Machine_learning/` + `Clear_Attack_Simulation/` in one root:** 30 / 30 passed.
- **Discoveries during the trial (corrected):** (a) step 18 reads `new_rotation_features.parquet`, which is produced by `14_new_rotation_features.py`, and that was archived; I added `14_build_new_rotation_features.py` (extracted verbatim from lines 1–73, without the evaluation part). (b) The `.gitignore` at the repository root ignores `*.log`, so 6 log files would have been silently dropped on upload; I added an explicit exception for them in the folder's `.gitignore`. (c) `common.py` now picks up `Clear_Attack_Simulation/` from the repository root automatically.
- **Dry-run upload:** 127 files, no file among the ignored ones, the largest file 5.6 MB, no parquet data file outside `model/` and the evaluation results, and no modification to any file in the repository root or to the members' folders (no conflicts with their branches).

## What was not verified (for honesty)
1. **I did not re-run the full training** (`28_final75.py`, `31_xgb75.py` and `33_cv_fixed_bands.py`) after the reorganization; only the paths changed in them. Check 4 covers 15 models out of 45 in 28 and does retrain, but the `lgbm_w*.txt` files themselves are taken from the saved joblib and were not rewritten from a new training run.
2. **The original data source** (`behavior_features_r62_ml_final.parquet`) is a product of the team's notebook before this work; I verified the integrity of the files (SHA-256) and their consistency with the pipeline, not the correctness of building the first features from the raw CERT logs.
3. **The Recall@1%FPR metric** in the row tables is read from the ROC curve of the same set (an evaluation point, not a deployable threshold); the operational threshold is 85.
4. **I did not run the repository on GitHub itself** (no CI), and all my checking is local.
5. **The results are on simulated data** in which attackers are 67% of the test set, so Precision must not be generalized to an environment with lower prevalence.
6. **There is no licence** in the repository: choose a licence before public release.

## Re-verify yourself
```bash
pip install -r model/requirements.txt pytest
pytest -q tests                                   # no data needed
# With the data (place it in pipeline/data/ as in pipeline/data/README.md):
pip install -r pipeline/requirements.txt
cd pipeline && python verify_release.py           # exits with code 0 only if all checks pass
```
