# pipeline/data — training data

**The original source data is in the team repository:** branch `remas-mushabbab-attacks-generator`, folder `Clear_Attack_Simulation/` (work of Remas). The six original files below are **byte-for-byte identical** to what the model was trained on (compared by SHA-256), so there is no need to copy them here. `pipeline/common.py` picks up the folder automatically if `Clear_Attack_Simulation/` exists in the repository root, or through the variable `MUBSIR_DATA`.
The files in `work/` are derived by our scripts (`01`, `18`, `21` and `25`) and are regenerated, so they do not need to be uploaded.

The folders `Clear_Attack_Simulation/` and `work/` are excluded in `.gitignore`: they are simulated data derived from CERT r6.2 (63 MB), and their ownership and licence are decided by the project owner. **The model (`../../model`) and the tests (`../../tests`) do not need them.** Only the `pipeline/` scripts and `verify_release.py` need them.

Place the following files at exactly these paths (or point `MUBSIR_DATA` and `MUBSIR_WORK` to their locations). To check their integrity: `sha256sum -c SHA256SUMS.txt` from this folder.

| File (relative to this folder) | SHA-256 (first 16) |
|---|---|
| `Clear_Attack_Simulation/data/final/behavior_features_r62_ml_final.parquet` | `1aaa189471fb4f57` |
| `Clear_Attack_Simulation/data/final/user_day_injected_r62.parquet` | `d0f960c97b7cbe17` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_channel_days.parquet` | `52ae9eb047a7d9b5` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_user_days.parquet` | `4741e719274b81da` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_users.parquet` | `f0d4aeaa74762724` |
| `Clear_Attack_Simulation/data/stages_output/validated_scenario_assignments_r62.parquet` | `039c15f15d6a8bad` |
| `work/evidence_features.parquet` | `094886ac17710eb3` |
| `work/final_changed_features.parquet` | `a787f3f1267cffc3` |
| `work/gap_alt_features.parquet` | `689baa59b3611ccd` |
| `work/prepared_995.parquet` | `aa49c759e42f2c17` |

The files in `work/` are produced by `01_prepare.py`, `18`, `21` and `25`; the rest are the original simulation inputs of the team.
