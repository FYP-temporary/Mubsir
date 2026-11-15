# Release hashes — MUBSIR stage-1 detector (FINAL75) v1.0

Every hash below was computed by `pipeline/35_write_release_hashes.py` on the files as they are in this repository; nothing was typed by hand.
Verification (`docs/VERIFICATION.md`, `tests/`, `pipeline/verify_release.py`) was run against exactly these files.
Environment: Python 3.13.18, lightgbm 4.7.0, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1.

## 1. Deployable bundle (`model/`) — what the dashboard system loads
**Root hash (sha256 of `model/SHA256SUMS.txt`): `b7853487da3820b312ddcdb4e343ab9ced474b49c473ac432b05c0926286922a`**

Pin this value in the deployment configuration or the approval ticket, i.e. somewhere the people who can replace model files cannot also edit. `SHA256SUMS.txt` alone is not enough: whoever swaps a model can swap the list. `version` inside `manifest.json` is a label, not proof.

| File | SHA-256 | Bytes |
|---|---|---|
| `README.md` | `a7d2f97bbf2150aa73e3714370ecf0739b165ce02e2cb0f374ba9fdfe21cec11` | 3,125 |
| `example_input.parquet` | `920d6757e0f6982f18a901c0c2e027dfade2cc1c7556e507bf41406f750aee41` | 82,254 |
| `lgbm_w10.txt` | `cef14308138ef141041afeadfecd88790a0193f40d71b27e6c6c23ea486e2d07` | 1,178,417 |
| `lgbm_w20.txt` | `9e72893c68b3730e66cfaff339ad5dae3833ae68490c59399df03b1f7261fd4b` | 1,009,129 |
| `lgbm_w5.txt` | `71017baf229811caf2026bd14499de66f34666ad31de0d78a6d5bf5c2f971714` | 1,146,453 |
| `manifest.json` | `81fbcc649a5aca1393b0557ea7795e32075ac4d3d1a3afbbffcf7d51b8b4e8b1` | 11,523 |
| `mubsir_infer.py` | `8c0996bd4baa574b60da56019860791f5dce7806e6169a46050930b4666b4685` | 9,175 |
| `requirements.txt` | `867ff197b7f66f7cf0dfa1fe0d058756f69dcbc2a0d80f9a5783eb5d7a53c622` | 102 |
| `verify_bundle.py` | `7b9a9588bc65031eba2dded803cee2945ab9221266d849cb0c8ddf303aa801bd` | 3,359 |

Check before loading: `python model/verify_bundle.py --root-hash b7853487da3820b312ddcdb4e343ab9ced474b49c473ac432b05c0926286922a` (exit code 0 = intact; also fails on a missing, modified or unlisted file). In code: `verify_bundle("model", expected_root_sha256=...)`.
Purpose of each file: `README.md` bundle contract; `example_input.parquet` 3-user example used by the tests; `lgbm_w10.txt` LightGBM booster, 10-workday window; `lgbm_w20.txt` LightGBM booster, 20-workday window; `lgbm_w5.txt` LightGBM booster, 5-workday window; `manifest.json` feature order per window, Platt calibration, thresholds 60/85, input columns; `mubsir_infer.py` scoring + SHAP code; `requirements.txt` inference dependencies; `verify_bundle.py` integrity check (run before loading).

## 2. Model checkpoints used by the verification (`pipeline/results/models/`)
These are scikit-learn pickles (`joblib`): used only to prove that the native boosters in `model/` give identical scores (max difference 0.0 on 20,634 test rows). They are **not** loaded in production; never load a pickle you cannot hash-check.

| File | SHA-256 | Bytes |
|---|---|---|
| `pipeline/results/models/final75_FINAL75_w5.joblib` | `d0aaa4add11d66542bddc267286c240363473d784f9f82a994aa27ecb6059af8` | 1,150,277 |
| `pipeline/results/models/final75_FINAL75_w10.joblib` | `d84947d4610887463aa49acb12e6e4589b0b505fd7f233210156ebf803304b33` | 1,182,246 |
| `pipeline/results/models/final75_FINAL75_w20.joblib` | `9f708e217f95fd48076a34787c765e708708c159c98e0273bc67bc2e4a256c42` | 1,012,950 |

## 3. Result tables behind the published metrics (`pipeline/results/`)
| File | SHA-256 | Bytes |
|---|---|---|
| `pipeline/results/fixed_bands_users.csv` | `d214da9bab192ece6af9e62efa86f450951b3a94e0e8c8e4c470fec2cdf7d13f` | 2,343 |
| `pipeline/results/fixed_bands_rows.csv` | `90f6cf6ca6877629e070d899463f652a11cbe33626eb742638598f07b71ba527` | 2,068 |
| `pipeline/results/final_split.csv` | `362664173b8d67b35955674c4d80e76b74561d6aeef6fd58870d74d80b9a0e29` | 35,935 |
| `pipeline/results/final75_test_rows.csv` | `8f71f48d26b428ae1c9ac13fc1b97db7445533f510b0df31f1e11d4f93a224e4` | 1,718 |
| `pipeline/results/final75_bootstrap_ci.csv` | `a128021c1eb5ad409c4bd0ffa671a3498ac7cfcb3e2aa463d8c22dc9f69d0e79` | 1,574 |
| `pipeline/results/cv75_fixed_bands_LightGBM.csv` | `f7566396d3a927537879f39cc5daa9514518a6ba882559bf82643007b4fe668a` | 32,758 |
| `pipeline/results/cv75_fixed_bands_XGBoost.csv` | `57e5fcb0885dcc3a63ffa78bc7a24d47ea63870e64b76d19133f759386834c71` | 32,348 |

## 4. Data inputs (not in the repository; `pipeline/data/SHA256SUMS.txt`)
The verification and the derived feature tables were produced from exactly these files (`verify_release.py` check 1 recomputes these hashes).

| File | SHA-256 |
|---|---|
| `Clear_Attack_Simulation/data/final/behavior_features_r62_ml_final.parquet` | `1aaa189471fb4f57db2dabce7685ca8eb8de8b3e1699d74ef4fede2f4a777d7a` |
| `Clear_Attack_Simulation/data/final/user_day_injected_r62.parquet` | `d0f960c97b7cbe172863f5b21da3e0d0513a2795c3f12bdf6b058b2f351eea11` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_channel_days.parquet` | `52ae9eb047a7d9b5d30908ba33131f0a2ceb5675854fa6ec1441f11c10206fd7` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_user_days.parquet` | `4741e719274b81da1ff8cce29ce6c52d4360d3742d7213d97a1bc5e0fb714420` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_users.parquet` | `f0d4aeaa74762724c7775d3b21b87707997c767b8848d2d6120c879810cd906d` |
| `Clear_Attack_Simulation/data/stages_output/validated_scenario_assignments_r62.parquet` | `039c15f15d6a8bad9010a35a91ead6fe6053e38664261ecbb712389c3462d8f2` |
| `work/evidence_features.parquet` | `094886ac17710eb302f51320a0dbfdde46dece32dcce04258c78b5134658113f` |
| `work/final_changed_features.parquet` | `a787f3f1267cffc3c49da10d36af6edc2dd9681b14cc978309ce8bd6d0c4c69d` |
| `work/gap_alt_features.parquet` | `689baa59b3611ccdae3768426501b82d361766f16d31060d56e67fb3b08fe401` |
| `work/prepared_995.parquet` | `aa49c759e42f2c17d3dd8109b1c4a22d7d95bb02cca4faee2b8602a112e1b026` |

## 5. Verification logs (`docs/`)
| File | SHA-256 | Bytes |
|---|---|---|
| `docs/pytest_log.txt` | `b7a73dbd5de837b9ed656686a494207c25259757da7b7b9a0cc984afa1ba5db1` | 1,343 |
| `docs/verify_release_log.txt` | `0207b05a8c8fa56301e581c1eeacb7781f819eacc34a3835148aa5836bbb954c` | 3,049 |
| `docs/reproducibility_log.txt` | `81be23ee09997640d846be99d139481835d516b6aedac90fc27a9e4ed24d90df` | 428 |

## 6. Feature-generation reference (`docs/FEATURE_GENERATION_CONTRACT.md`)
| File | SHA-256 | Bytes |
|---|---|---|
| `docs/FEATURE_GENERATION_CONTRACT.md` | `6b5182d590207b24297bbf9212031ad03e5b36f68a4f762683af461400403025` | 13,199 |
| `docs/golden_feature_cases.json` | `4bbedb846404298fcef66181bf40d27b9e84f4316061a6e05fb3170c5d049359` | 7,788 |
| `pipeline/verify_feature_contract.py` | `988ecfefbb590428d5e3063281ad719eebc39f774cbf887d4ab13323a85f806f` | 6,983 |

## How to use this record at approval time
1. Re-run `python model/verify_bundle.py` and compare the printed root hash with section 1; record the root hash in the approval ticket / deployment config.
2. At every deployment and service start, call `verify_bundle(..., expected_root_sha256=<pinned value>)` before `MubsirScorer(...)`.
3. A new model version = new files = new root hash = a new record; never edit files in place under the same version.
