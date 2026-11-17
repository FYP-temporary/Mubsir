# Mubsir

**Detecting channel-rotating, low-and-slow data exfiltration with UEBA (CERT r6.2).**
King Khalid University (KKU) graduation project, Digital Forensics track.

For every (user, workday) the model outputs three risk scores in 0–100 (windows of 5, 10 and 20 workdays), a level (Low / Medium / High, fixed thresholds 60 and 85), and a SHAP explanation. One LightGBM model per window, 75 features each. Inference needs only `numpy`, `pandas` and `lightgbm`.

## Quick start

```bash
pip install -r model/requirements.txt pytest
python -m pytest -q tests                                  # 14 tests (11 contract + 3 integrity), no training data needed
cd model && python mubsir_infer.py example_input.parquet --explain 4
```

```python
import sys; sys.path.insert(0, "model")
from mubsir_infer import MubsirScorer
sc    = MubsirScorer("model")                  # load once at service start-up
rows  = sc.score(features_df)                  # per (user, day): risk_5/10/20, level_*, risk, level, alert, alert_windows
users = sc.score_users(rows)                   # per user: risk_peak, level, peak_day, first_alert_day
why   = sc.explain(features_df.iloc[[0]], window=10, top_k=5)   # top SHAP contributions
```

## Results (199 held-out users: 134 attackers + 65 normal; simulated data)

| User level, High (> 85) | TP / FN / FP / TN | Recall | Precision | FPR |
|---|---|---|---|---|
| any window | 130 / 4 / 1 / 64 | 0.970 | 0.992 | 0.015 (1 of 65) |
| window 5 | 129 / 5 / 1 / 64 | 0.963 | 0.992 | 0.015 |
| window 10 | 127 / 7 / 1 / 64 | 0.948 | 0.992 | 0.015 |
| window 20 | 124 / 10 / 1 / 64 | 0.925 | 0.992 | 0.015 |

Row level (user-workday), window 10, LightGBM: PR-AUC 0.958, Recall 0.833 at FPR 1%. Details: `docs/MUBSIR_QA_REPORT.md`.

**Caveat:** the test set has 67% attackers and comes from simulated CERT r6.2 data; precision does not transfer to a low-prevalence production environment, and the models were not validated on other datasets.

## Repository layout

| Path | Content |
|---|---|
| `model/` | **Deployable bundle**: 3 LightGBM boosters, `manifest.json` (feature order, calibration, thresholds), `mubsir_infer.py`, example input |
| `pipeline/` | Scripts, results and the verification script that rebuild the model (training data excluded, see `pipeline/data/README.md`) |
| `tests/` | `pytest` contract tests for the bundle |
| `docs/` | `INTEGRATION_GUIDE.md` (embedding the model + dashboard outputs), `FEATURE_GENERATION_CONTRACT.md` + `golden_feature_cases.json` (how the 27 added features are computed), `RELEASE_HASHES.md` (SHA-256 of the bundle, models, data and logs, with the root hash to pin), `MUBSIR_QA_REPORT.md`, `FEATURE_DEFINITIONS_ROTATION.md`, `VERIFICATION.md` + raw logs, figures (confusion matrices) |

## Verification

All checks and their outputs are in [`docs/VERIFICATION.md`](docs/VERIFICATION.md): 14/14 tests (11 model-contract + 3 bundle-integrity), 30/30 data-dependent checks (split integrity, no label leakage, confusion matrices recomputed from the bundle), and a clean-room re-derivation of the calibration that reproduced `manifest.json` byte for byte. What was **not** verified is listed there too.

## Limitations

- Input is the daily **feature table**, not raw logs; the raw-log feature extractor is not part of this repository and must reproduce the training features exactly. The 27 of the 77 input columns that are not in the team's tables are specified in [`docs/FEATURE_GENERATION_CONTRACT.md`](docs/FEATURE_GENERATION_CONTRACT.md) (with a reference implementation and golden test cases); the 36 team-computed columns still need the team's code.
- `unique_usb_extensions` (all zero in the team data because of a regex bug) is **not** a model input; an extractor does not need to produce it.
- Risk is a calibrated probability (×100) that the user-day lies inside an exfiltration window, not a measure of deviation magnitude.
- No license is set yet; choose one before making the repository public.
