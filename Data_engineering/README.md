# Data Engineering Pipeline

This directory contains the **Data Engineering component** of the graduation project:

**AI-Based Detection of Cross-Channel Low-and-Slow Data Exfiltration Using UEBA**

The purpose of this component is to transform the raw CERT Insider Threat Dataset r4.2 into structured behavioral data that can later be used for attack simulation, machine-learning experiments, and insider-threat detection.

The pipeline performs raw-data aggregation, user-specific baseline construction, behavioral feature engineering, ground-truth preparation, documentation, and automated data-quality validation.

---

## Dataset Overview

This project uses the **CERT Insider Threat Test Dataset, release r4.2**.

The CERT dataset was developed for insider-threat research by the **CERT Division of Carnegie Mellon University's Software Engineering Institute (SEI)** in collaboration with **ExactData, LLC**, with support from **DARPA I2O**.

The dataset is **synthetic**.

It does not contain real employee logs from a real organization. Instead, it simulates activity inside an enterprise environment and includes:

- synthetic normal user behavior,
- synthetic malicious insider behavior,
- organizational information,
- and ground-truth records describing known malicious scenarios.

Synthetic datasets are particularly useful in insider-threat research because real organizational logs are difficult to obtain and distribute due to privacy, confidentiality, and security concerns.

The CERT dataset provides a controlled environment in which malicious users and malicious time periods are known, allowing detection methods to be evaluated against known ground truth.

---

## Main Data Sources

The main CERT r4.2 activity sources used in this project are:

| Source | Purpose |
|---|---|
| `email.csv` | Email activity, recipients, message size, attachments, and content |
| `device.csv` | USB/removable-device connect and disconnect activity |
| `file.csv` | File activity associated with removable media |
| `http.csv` | Web requests and accessed URLs |
| `logon.csv` | Logon and logoff activity |
| `answers/` | Ground-truth information for known malicious scenarios |

Additional CERT data such as `psychometric.csv` and `LDAP/` is preserved with the raw dataset but is not currently required by the main behavioral feature pipeline.

---

## Ground Truth

The CERT r4.2 ground truth used in this project contains:

- **70 malicious incidents**
- **70 unique malicious users**
- **30 Scenario 1 incidents**
- **30 Scenario 2 incidents**
- **10 Scenario 3 incidents**

For the current data-exfiltration scope:

- Scenario 1 is treated as exfiltration-relevant.
- Scenario 2 is treated as exfiltration-relevant.
- Scenario 3 is preserved but is not part of the primary exfiltration scope.

Therefore, **60 of the 70 original CERT incidents are marked as exfiltration-relevant**.

Original CERT incidents are stored with:

```text
source = CERT_r4.2
is_synthetic = 0
```

The `is_synthetic` field does **not** mean that CERT itself contains real-world data.

The entire CERT dataset is synthetic.

Within this project, `is_synthetic = 0` means that the incident comes from the original CERT ground truth rather than from a new attack scenario generated later by this project.

---

## Project Structure

```text
Data_engineering/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── features/
│   └── README.md
│
├── docs/
│   ├── data_dictionary.xlsx
│   └── data_quality_report.csv
│
├── notebooks/
│
├── results/
│   └── incident_event_audit.csv
│
├── src/
│   └── data_pipeline/
│       ├── build_user_day.py
│       ├── build_baseline.py
│       ├── build_behavior_features.py
│       ├── build_ground_truth.py
│       ├── config.py
│       ├── run_pipeline.py
│       └── validate_data.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Data Engineering Workflow

The pipeline contains five main stages.

### 1. Build User-Day Dataset

Raw activity from Email, USB, File, HTTP, and Logon sources is aggregated into a common **User-Day representation**.

Each User-Day record represents:

**one user + one calendar day**

Output:

```text
data/processed/user_day_aggregated_v1.parquet
```

---

### 2. Build User-Specific Baselines

A historical behavioral baseline is constructed separately for every user.

The baseline uses:

- activity before the first known malicious CERT r4.2 incident,
- weekdays only,
- days where the user had actual logon activity.

The baseline contains statistics such as:

- median activity,
- 95th-percentile thresholds,
- early logon thresholds,
- late logoff thresholds.

Behavioral areas include:

- Email
- External Email
- USB
- File Copy
- HTTP
- Unique Domains
- Logon Time
- Logoff Time

Output:

```text
data/processed/user_baseline_v1.parquet
```

---

### 3. Build Behavioral Features

The User-Day dataset is combined with each user's historical baseline.

The resulting feature set includes:

- user-specific baseline values,
- baseline-relative ratios,
- above-P95 flags,
- unusual working-time indicators,
- Email / USB / HTTP activity indicators,
- daily abnormality features,
- 7-day rolling features,
- 14-day rolling features,
- 30-day rolling features,
- recent channel diversity.

Output:

```text
data/features/user_day_behavior_features_v1.parquet
```

The current behavioral dataset contains **73 columns**.

---

### 4. Build Ground Truth

The original CERT r4.2 answer data is cleaned and converted into a consistent project format.

The resulting ground truth includes:

- malicious user,
- scenario,
- scenario description,
- attack start,
- attack end,
- duration,
- exfiltration relevance,
- source,
- original/project-generated indicator.

Outputs:

```text
data/processed/ground_truth_r42.parquet
data/processed/ground_truth_r42.csv
```

---

### 5. Final Data Quality Validation

The final stage verifies that the generated datasets are structurally and logically consistent.

The validation pipeline currently performs **61 automated checks** covering:

- dataset structure,
- User-Day uniqueness,
- critical missing values,
- invalid negative values,
- logical consistency,
- binary flag validity,
- baseline quality,
- ground-truth integrity,
- malicious-user coverage,
- attack-date coverage,
- known CERT behavioral cases,
- baseline reproducibility.

A successful run ends with:

```text
DATA QUALITY STATUS: PASS
Dataset is ready for handoff.
```

---

## Main Outputs

### Processed Data

```text
data/processed/
├── device_daily.parquet
├── email_daily.parquet
├── file_daily.parquet
├── http_daily.parquet
├── logon_daily.parquet
├── user_day_aggregated_v1.parquet
├── user_baseline_v1.parquet
├── ground_truth_r42.parquet
└── ground_truth_r42.csv
```

### Behavioral Features

```text
data/features/
└── user_day_behavior_features_v1.parquet
```

### Documentation

```text
docs/
├── data_dictionary.xlsx
└── data_quality_report.csv
```

`data_dictionary.xlsx` documents the behavioral features and ground-truth fields.

`data_quality_report.csv` stores the complete results of the final **61 automated validation checks**.

### Analysis Results

```text
results/
└── incident_event_audit.csv
```

`incident_event_audit.csv` is an exploratory incident-level analysis generated during the CERT incident audit.

It summarizes malicious incident activity by event type, including:

- Logon
- Device
- File
- HTTP
- Email
- Total Events
- First Event
- Last Event

This file is an **analysis result**, not a training dataset or pipeline input.

---

## Running the Pipeline

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Place the CERT r4.2 dataset under the raw-data structure described in:

```text
data/README.md
```

Then run:

```bash
python src/data_pipeline/run_pipeline.py
```

The pipeline automatically executes:

```text
1. Build User-Day Dataset
2. Build User Baseline
3. Build Behavior Features
4. Build Ground Truth
5. Final Data Quality Validation
```

If any stage fails, the pipeline stops immediately.

---

## Notebooks

The `notebooks/` directory provides an interactive and presentation-friendly record of the Data Engineering work.

The notebooks cover:

1. Raw dataset audit
2. HTTP data inspection
3. CERT incident inspection
4. Incident event analysis
5. User-Day construction
6. User baseline construction
7. Baseline and data validation
8. Behavioral feature engineering
9. Ground-truth construction
10. Data dictionary generation
11. Final data-quality validation

These notebooks make it possible to inspect the processing logic and outputs directly without relying only on terminal pipeline output.

---

## Channel Diversity vs. Channel Rotation

The current feature:

```text
activity_channel_diversity_7d
```

measures how many of the following channels were active within the recent observation window:

- Email
- USB
- HTTP

It represents **channel diversity**.

It does **not** yet represent deliberate sequential channel rotation.

Explicit cross-channel rotation will be introduced later during the attack-simulation stage, where controlled low-and-slow attacks will distribute activity across Email, USB, and HTTP over time.

---

## Current Status

**Data Engineering v1.0**

Completed:

- Raw-data preprocessing
- User-Day aggregation
- User-specific baseline construction
- Behavioral feature engineering
- CERT r4.2 ground-truth preparation
- Incident-level exploratory audit
- Data dictionary generation
- Final 61-check data-quality validation

The resulting data is ready for handoff to the next project stage.