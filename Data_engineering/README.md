# CERT r6.2 Data Engineering Pipeline

This directory contains the data engineering workflow developed for the graduation project:

**AI-Based Detection of Cross-Channel Low-and-Slow Data Exfiltration Using UEBA**

The pipeline processes the **CERT Insider Threat Dataset r6.2** and prepares structured datasets for behavioral analysis, synthetic attack generation, machine learning, and evaluation.

---

## Overview

The purpose of this pipeline is to transform the original CERT r6.2 activity logs into clean, structured, user-level behavioral datasets.

The workflow focuses on three data-exfiltration channels:

- External Email
- USB / Removable Media
- HTTP Upload

It also uses logon activity to define valid user workdays and the official CERT answer files to construct ground-truth information for known malicious users.

The resulting datasets support later stages of the project, including:

- User behavior baselining
- Cross-channel behavioral analysis
- Low-and-slow attack simulation
- Feature engineering
- Machine-learning model development
- Explainability and evaluation

---

## Project Structure

```text
DATA_ENGINEERING_R62/
│
├── data/
│   ├── raw/
│   │   └── r6.2/
│   │
│   ├── processed/
│   │
│   └── features/
│
├── notebooks/
│
├── results/
│
├── docs/
│
├── src/
│   └── run_pipeline.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

### `data/raw/`

Contains the original CERT r6.2 dataset.

The raw dataset is **not included in the Git repository** because of its large size. It must be obtained separately and placed under:

```text
data/raw/r6.2/
```

More information is available in:

```text
docs/DATASET_SOURCE.md
```

### `data/processed/`

Contains cleaned and aggregated intermediate datasets, including:

- Daily Email activity
- Daily USB/File activity
- Daily HTTP activity
- Daily Logon activity
- Unified User-Day dataset
- Ground-truth user and event datasets

### `data/features/`

Contains the main feature-level datasets used for behavioral analysis and later modeling stages, including:

- Benign user baselines
- Behavioral features
- Eligible synthetic attack hosts
- Malicious-user pre-attack baselines

### `notebooks/`

Contains the complete data engineering workflow in execution order:

```text
00_r62_feasibility_audit.ipynb
01_build_daily_channels.ipynb
02_build_user_day_r62.ipynb
03_build_baseline_r62.ipynb
04_build_behavior_features_r62.ipynb
05_clean_ground_truth_r62.ipynb
06_build_malicious_pre_attack_baseline_r62.ipynb
07_build_feature_dictionary_r62.ipynb
08_final_data_engineering_qa.ipynb
09_final_validation.ipynb
```

### `results/`

Contains documentation and metadata describing the generated datasets and features:

```text
dataset_inventory_r62.csv
feature_dictionary_r62.csv
schema_dictionary_r62.csv
```

### `docs/`

Contains supporting documentation for the data engineering stage:

```text
DATASET_SOURCE.md
DATA_ENGINEERING_SUMMARY.md
```

### `src/`

Contains the executable data engineering pipeline:

```text
run_pipeline.py
```

---

## Pipeline Workflow

The main data engineering workflow is:

```text
CERT r6.2 Raw Data
        ↓
Daily Channel Aggregation
        ↓
Unified User-Day Dataset
        ↓
User Behavioral Baselines
        ↓
Behavioral Feature Engineering
        ↓
Ground-Truth Preparation
        ↓
Malicious Pre-Attack Baselines
        ↓
Feature Documentation
        ↓
Final Data Engineering QA
        ↓
Final Integrity Validation
```

Stage `00` performs the initial dataset feasibility audit and is optional during normal pipeline execution.

---

## Environment Setup

A Python virtual environment is recommended.

Install the project dependencies using:

```bash
pip install -r requirements.txt
```

The pipeline has been validated using Python 3.12.

---

## Running the Pipeline

### Validate the environment only

```bash
python src/run_pipeline.py --check-only
```

### Run the complete data engineering pipeline

```bash
python src/run_pipeline.py
```

This executes Stages `01` through `09`.

### Run the feasibility audit before the main pipeline

```bash
python src/run_pipeline.py --with-audit
```

### Resume from a specific stage

For example, to continue from Stage 5:

```bash
python src/run_pipeline.py --from-stage 5
```

### Run one stage only

For example:

```bash
python src/run_pipeline.py --only-stage 7
```

The pipeline stops automatically if a notebook fails or if a required output is missing.

---

## Main Outputs

The primary datasets produced by this workflow include:

```text
data/processed/user_day_r62_v1.parquet

data/features/user_baseline_r62_v1.parquet
data/features/behavior_features_r62_v1.parquet
data/features/attack_host_eligibility_r62.parquet
data/features/malicious_pre_attack_baseline_r62.parquet

data/processed/ground_truth_users_r62.parquet
data/processed/ground_truth_events_r62.parquet
```

The main behavioral modeling dataset is:

```text
data/features/behavior_features_r62_v1.parquet
```

Feature definitions are documented in:

```text
results/feature_dictionary_r62.csv
```

---

## Data Integrity

The final workflow includes dedicated QA and integrity-validation stages.

These checks validate:

- Dataset dimensions
- User populations
- Channel-level activity totals
- Duplicate user-day records
- Baseline separation
- Malicious-user exclusion from benign training data
- Ground-truth consistency
- Feature documentation
- Project path portability

The current validated data engineering build passes all final integrity checks.

---

## Reproducibility

The project uses relative project paths rather than machine-specific absolute paths.

This allows the pipeline to be executed on another machine as long as:

1. The repository structure is preserved.
2. Required Python dependencies are installed.
3. The CERT r6.2 raw dataset is placed under `data/raw/r6.2/`.

The raw dataset and local Python virtual environment are intentionally excluded from version control.

---

## Additional Documentation

For dataset acquisition and raw-data requirements:

```text
docs/DATASET_SOURCE.md
```

For a detailed summary of the data engineering methodology and outputs:

```text
docs/DATA_ENGINEERING_SUMMARY.md
```

For feature-level definitions:

```text
results/feature_dictionary_r62.csv
```

For dataset schemas:

```text
results/schema_dictionary_r62.csv
```

For the final dataset inventory:

```text
results/dataset_inventory_r62.csv
```