# MUBSIR inference bundle (stage 1, FINAL75)

Files: `SHA256SUMS.txt` + `verify_bundle.py` (integrity check), `manifest.json` (feature order per window, calibration, thresholds), `lgbm_w{5,10,20}.txt` (LightGBM native models), `mubsir_infer.py` (scoring + SHAP), `example_input.parquet` (3 test users, 77 input columns).
Dependencies: numpy, pandas, lightgbm. No pickles, no scalers/encoders (trees; NaN is handled natively).

```python
from mubsir_infer import MubsirScorer
import pandas as pd
sc   = MubsirScorer()                                  # bundle directory = this folder
X    = pd.read_parquet("example_input.parquet")        # user, day + the 77 feature columns
rows = sc.score(X)                                     # risk_5/10/20, level_* (Low/Medium/High), risk (max), level, alert (= High), alert_windows
users= sc.score_users(rows)                            # per-user peak risk, level (Low/Medium/High), first_alert_day
why  = sc.explain(X.iloc[[100]], window=10, top_k=5)   # top SHAP contributions (log-odds) for that prediction
print(sc.explain_text(X.iloc[[100]], 10, 4))
```
CLI: `python mubsir_infer.py example_input.parquet --explain 4`

## Contract
- **Input**: one row per user-workday with the columns in `manifest["input_columns_all"]` (77 = 74 agreed features + `nr_gap_alt_2_{5,10,20}wd`; each window model uses its own 75). Column order is irrelevant (re-ordered by the manifest); extra columns ignored; missing columns raise an error; NaN allowed. Features must come from the project's causal feature pipeline (rolling windows over the user's workday history, 2010 baseline percentiles).
- **Score**: raw = model probability; `risk_h = 100*sigmoid(platt_coef*logit(raw)+platt_intercept)`.
- **Risk and levels**: `risk` is a calibrated probability x 100 that the user-day lies inside an exfiltration window (not a direct deviation magnitude; deviation enters via the features, mainly `cumulative_deviation_*`). Fixed thresholds **60 and 85**: Low `risk <= 60`; Medium `60 < risk <= 85`; High `risk > 85`; alert = High. A user's level uses his peak risk over the period (max over windows). On the 199 held-out users, High rows are true attack rows 98-99% of the time, Low rows 3-6%, Medium 72-78%.
- **SHAP**: TreeSHAP in log-odds of the raw score; positive = raises risk.
- **Limits**: models trained on 796 development users of the simulated CERT r6.2 data; the 199 test users were never used for training, calibration or thresholds. Not validated on other datasets.

## Integrity (run before loading)
`python verify_bundle.py --root-hash <pinned sha256>` checks every file in this folder against `SHA256SUMS.txt` and fails on a missing, modified or unlisted file; `from verify_bundle import verify_bundle; verify_bundle("model", expected_root_sha256=...)` does the same in code. The root hash (sha256 of `SHA256SUMS.txt`) must be stored where the writers of the model files cannot edit it (deployment config, signed tag, approval ticket): a `version` field in `manifest.json` or a hash list next to the files proves nothing on its own. Hashes of this release: `../docs/RELEASE_HASHES.md`.
