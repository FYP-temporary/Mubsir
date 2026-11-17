# pipeline — reproducing the final model (75 features, one LightGBM model per window)

Run from this folder. Default paths: `data/Clear_Attack_Simulation` (source) and `data/work` (derived feature tables); both can be changed with the environment variables `MUBSIR_DATA` and `MUBSIR_WORK`. The exported model is written to `../model`.

## Order of the final pipeline

| Step | Script | Output |
|---|---|---|
| 1 | `01_prepare.py` | `data/work/prepared_995.parquet` (995 users, labels y_5/y_10/y_20) |
| 2 | `02_split.py` (**legacy**) | `results/user_split.csv`: only `group` and `stealth` are read from it. Its `part` and `rep*` columns are an old random split that **the final pipeline does not use** |
| 3 | `14_build_new_rotation_features.py` | `data/work/new_rotation_features.parquet` (input of the next step; extracted from the old step 14) |
| 4 | `18_build_evidence_features.py` | `data/work/evidence_features.parquet`  |
| 5 | `21_build_final_features.py` | `data/work/final_changed_features.parquet` (nr_alt, nr_stealth_acc and the p90 ratios) |
| 6 | `25_build_gap_alt.py` | `data/work/gap_alt_features.parquet` (nr_gap_alt_G) |
| 7 | `28_final75.py` | `results/final75_*` and `results/models/final75_FINAL75_w{5,10,20}.joblib` |
| 8 | `29_shap75.py` | `results/shap75/` |
| 9 | `31_xgb75.py` (variable `ALGO`) | `results/xgb75_*` (XGBoost comparison under the same conditions) |
| 10 | `30_export_bundle.py` | rewrites `../model/` (calibration and reference thresholds) |
| 11 | `32_fixed_bands.py` | `results/fixed_bands_*` (fixed 60/85 thresholds on the test set) |
| 12 | `33_cv_fixed_bands.py` (variable `ALGO`) | `results/cv75_fixed_bands_*` (5×3 CV) |
| 13 | `34_save_final_split.py` | `results/final_split.csv`: **the actual split** (796 development / 199 test) defined in the code (`StratifiedGroupKFold` grouped by `scenario_id`, first of 5 folds, seed 42) |
| 14 | `verify_release.py` | full release checks (needs `data/`), see `../docs/VERIFICATION.md` |
| 15 | `verify_feature_contract.py` | checks that the definitions of the 27 added features (`../docs/FEATURE_GENERATION_CONTRACT.md`) reproduce the stored values (needs `data/`) |
| 16 | `35_write_release_hashes.py` | writes `../model/SHA256SUMS.txt` and `../docs/RELEASE_HASHES.md` (run last, after the records are fixed) |

Design-decision scripts (kept for reference): `22_final_model.py` (74-feature baseline), `24_tune_lightgbm.py` (Optuna, not adopted), `26_eval_gap_alt.py` (evaluation of nr_gap_alt).

## Verification
See `../docs/VERIFICATION.md` (the `pytest` tests in `../tests` need no data; `verify_release.py` needs `data/`).

Note: `20_build_event_stream.py` and `19_evidence_model.py` (evidence experiments) are outside this repository because the final pipeline does not depend on them.
