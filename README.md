# Data Engineering Pipeline

This directory contains the **Data Engineering component** of the graduation project:

**AI-Based Detection of Cross-Channel Low-and-Slow Data Exfiltration Using UEBA**

The purpose of this component is to transform the raw CERT Insider Threat Dataset r4.2 into structured behavioral data that can later be used for attack simulation, machine-learning experiments, and insider-threat detection.

The pipeline performs raw-data aggregation, user-specific baseline construction, behavioral feature engineering, ground-truth preparation, and automated data-quality validation.

---

## Dataset Overview

This project uses the **CERT Insider Threat Test Dataset, release r4.2**.

The dataset was developed by the **CERT Division of Carnegie Mellon University's Software Engineering Institute (SEI)** in partnership with **ExactData, LLC**, with sponsorship from **DARPA I2O**.

It is important to note that the CERT dataset is **synthetic**.

It does not contain real employee activity from a real company. Instead, it was generated to simulate the behavior of users inside an enterprise environment, including both:

- normal background user activity, and
- malicious insider activity.

Synthetic insider-threat datasets are useful because real organizational security logs are difficult to obtain and share due to privacy, confidentiality, and security concerns.

The CERT dataset provides a controlled environment where malicious scenarios and the users involved are known, making it suitable for cybersecurity research and evaluation.

Official dataset identifier:

**DOI: 10.1184/R1/12841247.v1**

---

## What Does CERT r4.2 Contain?

The r4.2 release contains several types of simulated enterprise activity.

The main sources used in this project are:

| Source | Description |
|---|---|
| `email.csv` | User email activity including recipients, message size, attachments, and message content |
| `device.csv` | Removable-device connection and disconnection events |
| `file.csv` | File activity associated with removable media |
| `http.csv` | User web-browsing activity and accessed URLs |
| `logon.csv` | User logon and logoff activity |
| `psychometric.csv` | Synthetic psychometric information associated with users |
| `LDAP/` | Organizational and employee-related directory information |
| `answers/` | Ground-truth information describing known malicious users and attack scenarios |

The dataset therefore allows user behavior to be studied across multiple activity sources rather than analyzing a single log source in isolation.

This is particularly important for this project because the proposed detection approach focuses on **cross-channel behavior involving Email, USB, and HTTP activity over time**.

---

## Ground Truth

CERT also provides an answer set describing the malicious insider scenarios.

For r4.2, the ground truth used in this project contains:

- **70 malicious incidents**
- **70 unique malicious users**
- **30 Scenario 1 incidents**
- **30 Scenario 2 incidents**
- **10 Scenario 3 incidents**

For the current data-exfiltration scope:

- Scenario 1 is considered exfiltration-relevant.
- Scenario 2 is considered exfiltration-relevant.
- Scenario 3 is preserved in the dataset but is not treated as a primary exfiltration scenario.

Therefore:

**60 of the 70 original CERT incidents are marked as exfiltration-relevant.**

These records represent original CERT scenarios and are stored with:

`is_synthetic = 0`

within the project metadata.

This field does **not** mean that CERT itself is real-world data. The CERT dataset is synthetic. Instead, the field distinguishes original CERT incidents from the additional synthetic attack scenarios that will later be generated specifically by this project.

---

## Data Engineering Workflow

The pipeline contains five main stages.

### 1. Build User-Day Dataset

Raw Email, USB, File, HTTP, and Logon activity is aggregated into a common **User-Day representation**.

A User-Day record represents the activity of one user during one calendar day.

Output:

`data/processed/user_day_aggregated_v1.parquet`

---

### 2. Build User-Specific Baselines

A historical behavioral baseline is constructed separately for every user.

The baseline uses:

- activity before the first malicious CERT r4.2 incident,
- weekdays only,
- days where the user had actual logon activity.

Median and percentile-based statistics are calculated for behavior such as:

- email activity,
- external email activity,
- USB activity,
- file-copy activity,
- HTTP activity,
- unique domains,
- logon time,
- logoff time.

Output:

`data/processed/user_baseline_v1.parquet`

---

### 3. Build Behavioral Features

The User-Day dataset is combined with each user's historical baseline.

The resulting behavioral dataset includes:

- baseline-relative ratios,
- P95 threshold flags,
- unusual working-time features,
- daily channel activity indicators,
- daily abnormality indicators,
- 7-day rolling features,
- 14-day rolling features,
- 30-day rolling features,
- recent multi-channel activity diversity.

Output:

`data/features/user_day_behavior_features_v1.parquet`

The current behavioral dataset contains **73 columns**.

---

### 4. Build Ground Truth

The original CERT r4.2 answer data is cleaned and converted into a consistent project ground-truth format.

The resulting records include:

- user,
- scenario,
- scenario description,
- attack start,
- attack end,
- duration,
- exfiltration relevance,
- source,
- synthetic/original project indicator.

Outputs:

`data/processed/ground_truth_r42.parquet`

`data/processed/ground_truth_r42.csv`

---

### 5. Final Data Quality Validation

The final stage verifies that the generated data is internally consistent and suitable for handoff.

The validation pipeline currently performs **61 automated checks**, including:

- dataset structure,
- duplicate User-Day detection,
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

`DATA QUALITY STATUS: PASS`

and:

`Dataset is ready for handoff.`

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

## Running the Pipeline

Install the required packages:

```bash
pip install -r requirements.txt
```

Place the CERT r4.2 dataset inside the expected raw-data directory described in:

`data/README.md`

Then run:

```bash
python src/data_pipeline/run_pipeline.py
```

The pipeline executes the following stages automatically:

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

They allow the processing steps and results to be inspected without relying only on terminal pipeline output.

---

## Documentation

Two supporting documentation files are generated:

`docs/data_dictionary.xlsx`

Documents the behavioral features and ground-truth fields.

`docs/data_quality_report.csv`

Contains the complete results of the **61 final validation checks**.

---

## Important Note: Channel Diversity vs. Channel Rotation

The current feature:

`activity_channel_diversity_7d`

measures how many of the Email, USB, and HTTP channels were active within the recent observation window.

It represents **channel diversity**.

It does **not** yet represent deliberate channel rotation.

Explicit cross-channel rotation will be introduced during the later attack-simulation stage, where controlled low-and-slow attacks will distribute activity across Email, USB, and HTTP over time.

---

## Current Status

**Data Engineering v1.0**

The following stages are complete:

- raw-data preprocessing,
- User-Day aggregation,
- user-specific baseline construction,
- behavioral feature engineering,
- CERT r4.2 ground-truth preparation,
- data dictionary generation,
- final data-quality validation.

The resulting data is ready for handoff to the next project stage.
