"""Step 35: write the release hash files. Run from pipeline/ after every other step (and after the logs in ../docs are final):  python 35_write_release_hashes.py
  ../model/SHA256SUMS.txt     hashes of every file in the deployable bundle (what verify_bundle.py checks before loading)
  ../docs/RELEASE_HASHES.md   record of what was approved: bundle + root hash, the model checkpoints and result tables the verification used, the data inputs, the logs."""
import hashlib, json, platform, sys
from pathlib import Path
from common import *

sys.path.insert(0, str(MODEL)); from verify_bundle import sha256_file, SUMS, IGNORED
DOCS = PKG.parent / "docs"
bundle = sorted(p.relative_to(MODEL).as_posix() for p in MODEL.rglob("*") if p.is_file() and p.name != SUMS and not (set(p.relative_to(MODEL).parts) & IGNORED))
(MODEL / SUMS).write_text("".join(f"{sha256_file(MODEL / n)}  {n}\n" for n in bundle))
root = sha256_file(MODEL / SUMS); man = json.loads((MODEL / "manifest.json").read_text())


def table(rows):
    return "| File | SHA-256 | Bytes |\n|---|---|---|\n" + "".join(f"| `{n}` | `{sha256_file(p)}` | {p.stat().st_size:,} |\n" for n, p in rows)


purpose = {"lgbm_w5.txt": "LightGBM booster, 5-workday window", "lgbm_w10.txt": "LightGBM booster, 10-workday window", "lgbm_w20.txt": "LightGBM booster, 20-workday window",
           "manifest.json": "feature order per window, Platt calibration, thresholds 60/85, input columns", "mubsir_infer.py": "scoring + SHAP code",
           "verify_bundle.py": "integrity check (run before loading)", "example_input.parquet": "3-user example used by the tests", "requirements.txt": "inference dependencies", "README.md": "bundle contract"}
data_sums = [l.split(None, 1) for l in (PKG / "data" / "SHA256SUMS.txt").read_text().splitlines() if l.strip()]
results = ["fixed_bands_users.csv", "fixed_bands_rows.csv", "final_split.csv", "final75_test_rows.csv", "final75_bootstrap_ci.csv", "cv75_fixed_bands_LightGBM.csv", "cv75_fixed_bands_XGBoost.csv"]
logs = ["pytest_log.txt", "verify_release_log.txt", "reproducibility_log.txt"]
import lightgbm, numpy, pandas, sklearn
md = f"""# Release hashes — {man['name']} v{man['version']}

Every hash below was computed by `pipeline/35_write_release_hashes.py` on the files as they are in this repository; nothing was typed by hand.
Verification (`docs/VERIFICATION.md`, `tests/`, `pipeline/verify_release.py`) was run against exactly these files.
Environment: Python {platform.python_version()}, lightgbm {lightgbm.__version__}, numpy {numpy.__version__}, pandas {pandas.__version__}, scikit-learn {sklearn.__version__}.

## 1. Deployable bundle (`model/`) — what the dashboard system loads
**Root hash (sha256 of `model/SHA256SUMS.txt`): `{root}`**

Pin this value in the deployment configuration or the approval ticket, i.e. somewhere the people who can replace model files cannot also edit. `SHA256SUMS.txt` alone is not enough: whoever swaps a model can swap the list. `version` inside `manifest.json` is a label, not proof.

{table([(n, MODEL / n) for n in bundle])}
Check before loading: `python model/verify_bundle.py --root-hash {root}` (exit code 0 = intact; also fails on a missing, modified or unlisted file). In code: `verify_bundle("model", expected_root_sha256=...)`.
Purpose of each file: {"; ".join(f"`{n}` {purpose.get(n, '')}" for n in bundle)}.

## 2. Model checkpoints used by the verification (`pipeline/results/models/`)
These are scikit-learn pickles (`joblib`): used only to prove that the native boosters in `model/` give identical scores (max difference 0.0 on 20,634 test rows). They are **not** loaded in production; never load a pickle you cannot hash-check.

{table([(f"pipeline/results/models/final75_FINAL75_w{h}.joblib", RES / "models" / f"final75_FINAL75_w{h}.joblib") for h in WINDOWS])}
## 3. Result tables behind the published metrics (`pipeline/results/`)
{table([(f"pipeline/results/{n}", RES / n) for n in results])}
## 4. Data inputs (not in the repository; `pipeline/data/SHA256SUMS.txt`)
The verification and the derived feature tables were produced from exactly these files (`verify_release.py` check 1 recomputes these hashes).

| File | SHA-256 |
|---|---|
""" + "".join(f"| `{n.strip()}` | `{h}` |\n" for h, n in data_sums) + f"""
## 5. Verification logs (`docs/`)
{table([(f"docs/{n}", DOCS / n) for n in logs])}
## 6. Feature-generation reference (`docs/FEATURE_GENERATION_CONTRACT.md`)
{table([("docs/FEATURE_GENERATION_CONTRACT.md", DOCS / "FEATURE_GENERATION_CONTRACT.md"), ("docs/golden_feature_cases.json", DOCS / "golden_feature_cases.json"), ("pipeline/verify_feature_contract.py", PKG / "verify_feature_contract.py")])}
## How to use this record at approval time
1. Re-run `python model/verify_bundle.py` and compare the printed root hash with section 1; record the root hash in the approval ticket / deployment config.
2. At every deployment and service start, call `verify_bundle(..., expected_root_sha256=<pinned value>)` before `MubsirScorer(...)`.
3. A new model version = new files = new root hash = a new record; never edit files in place under the same version.
"""
(DOCS / "RELEASE_HASHES.md").write_text(md)
print(f"{len(bundle)} bundle files hashed; root hash {root}")
