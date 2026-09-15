# Data Directory

This directory contains the raw, processed, and engineered datasets used by the Data Engineering pipeline.

The data follows this general flow:

```text
CERT r4.2 Raw Data
        ↓
Daily Activity Aggregation
        ↓
User-Day Dataset
        ↓
User-Specific Baseline
        ↓
Behavioral Features
```

Directory structure:

```text
data/
├── raw/
├── processed/
├── features/
└── README.md
```

---

## Dataset Source

The original data used in this project comes from the:

**CERT Insider Threat Test Dataset — release r4.2**

The dataset was developed for insider-threat research by the **CERT Division of Carnegie Mellon University's Software Engineering Institute (SEI)** in collaboration with **ExactData, LLC**, with support from **DARPA I2O**.

The CERT dataset is **synthetic**.

It does not contain real employee activity from a real organization.

Instead, it simulates an enterprise environment containing:

- normal user activity,
- malicious insider activity,
- organizational context,
- and known attack ground truth.

This allows researchers to evaluate insider-threat detection methods in a controlled environment where malicious users and attack periods are already known.

---

# 1. Raw Data

The original CERT r4.2 files are stored locally under:

```text
data/raw/cert_r4.2 dataset/
```

Expected structure:

```text
raw/
└── cert_r4.2 dataset/
    ├── answers/
    ├── LDAP/
    ├── device.csv
    ├── email.csv
    ├── file.csv
    ├── http.csv
    ├── logon.csv
    ├── psychometric.csv
    ├── license.txt
    └── readme.txt
```

The raw dataset is not stored directly in Git because of its large size and because it is distributed externally.

---

## Main Raw Activity Sources

### `email.csv`

Contains synthetic email activity.

Typical fields include:

- timestamp,
- user,
- computer,
- recipients,
- sender,
- email size,
- attachments,
- message content.

Used to derive features such as:

- daily email volume,
- external email activity,
- email size,
- attachment activity.

---

### `device.csv`

Contains removable-device events.

Main activity types:

- Connect
- Disconnect

Used to measure USB/removable-device usage.

---

### `file.csv`

Contains synthetic file activity associated with users and computers.

Typical information includes:

- timestamp,
- user,
- computer,
- filename,
- generated file-content representation.

In this project, it is mainly used to measure file-copy activity associated with removable media.

---

### `http.csv`

Contains synthetic web activity.

Typical information includes:

- timestamp,
- user,
- computer,
- URL,
- generated web-content representation.

Used to derive:

- HTTP request volume,
- unique domains,
- temporal web-activity behavior.

---

### `logon.csv`

Contains user authentication activity.

Main event types:

- Logon
- Logoff

Used to derive:

- daily logon counts,
- first logon time,
- last logoff time,
- unusual working-time behavior.

---

### `psychometric.csv`

Contains synthetic psychometric information associated with users.

It is preserved as part of the original CERT dataset but is not currently a primary input to the project's main behavioral feature pipeline.

---

### `LDAP/`

Contains synthetic organizational and personnel-related directory information.

It provides additional organizational context but is not currently required by the main Data Engineering pipeline.

---

## Ground-Truth Answers

The `answers/` directory contains CERT's known malicious activity.

The main file used by this project is:

```text
answers/insiders.csv
```

It identifies information such as:

- malicious user,
- scenario,
- attack start,
- attack end,
- incident-detail file.

For r4.2:

| Scenario | Incidents | Project Relevance |
|---|---:|---|
| Scenario 1 | 30 | Exfiltration-relevant |
| Scenario 2 | 30 | Exfiltration-relevant |
| Scenario 3 | 10 | Preserved, not primary exfiltration scope |

Total:

- **70 malicious incidents**
- **70 unique malicious users**
- **60 exfiltration-relevant incidents**

---

# 2. Processed Data

The `processed/` directory contains intermediate and cleaned outputs generated from the raw CERT data.

```text
processed/
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

---

## Daily Aggregates

The following files contain activity aggregated by user and calendar day:

```text
device_daily.parquet
email_daily.parquet
file_daily.parquet
http_daily.parquet
logon_daily.parquet
```

These intermediate datasets are combined to build the common User-Day representation.

---

## User-Day Dataset

### `user_day_aggregated_v1.parquet`

This is the integrated daily activity dataset.

Each record represents:

**one user + one calendar day**

It combines:

- Email
- USB / Device
- File
- HTTP
- Logon / Logoff

Current size:

- **464,687 User-Day records**
- **1,000 users**

This common daily representation allows behavior from different activity channels to be analyzed over the same time scale.

---

## User Baseline

### `user_baseline_v1.parquet`

Contains one historical behavioral profile for each user.

The baseline is built using:

- activity before the first known malicious CERT r4.2 incident,
- weekdays only,
- days with actual user logon activity.

It contains statistics such as:

- median activity,
- 95th-percentile thresholds,
- early logon thresholds,
- late logoff thresholds.

The purpose is to compare a user's current behavior with that user's **own historical behavior**, rather than applying the same global threshold to every user.

---

## Ground Truth

### `ground_truth_r42.parquet`
### `ground_truth_r42.csv`

These files contain the cleaned CERT r4.2 malicious incident information.

Fields include:

- `user`
- `scenario`
- `scenario_name`
- `details`
- `attack_start`
- `attack_end`
- `duration_days`
- `exfiltration_relevant`
- `source`
- `is_synthetic`

Original CERT incidents use:

```text
source = CERT_r4.2
is_synthetic = 0
```

The CERT dataset itself is synthetic.

Within this project, `is_synthetic = 0` only means:

**this record comes from the original CERT ground truth and was not generated later by our own attack-simulation stage.**

---

# 3. Behavioral Feature Data

The `features/` directory contains the final engineered behavioral dataset.

```text
features/
└── user_day_behavior_features_v1.parquet
```

### `user_day_behavior_features_v1.parquet`

This dataset extends the User-Day data with behavioral and temporal features.

The current version contains **73 columns**.

Feature groups include:

- daily activity measurements,
- user-specific baseline values,
- P95 behavioral ratios,
- above-baseline flags,
- unusual working-time indicators,
- Email / USB / HTTP activity flags,
- daily abnormality indicators,
- 7-day rolling features,
- 14-day rolling features,
- 30-day rolling features,
- recent channel diversity.

This dataset is intended to become one of the main inputs to the later detection and machine-learning stages.

---

## Channel Diversity

The feature:

```text
activity_channel_diversity_7d
```

measures how many of the following channels were active within the recent observation window:

- Email
- USB
- HTTP

A value of:

```text
1 = one channel active
2 = two channels active
3 = all three channels active
```

This feature measures **channel diversity only**.

It does not identify deliberate ordered switching between channels.

Explicit channel-rotation features will be introduced later after controlled cross-channel attack scenarios are generated.

---

# Supporting Outputs

Files that describe or evaluate the datasets are intentionally stored outside the `data/` directory.

## Documentation

```text
docs/
├── data_dictionary.xlsx
└── data_quality_report.csv
```

- `data_dictionary.xlsx` documents the feature and ground-truth schemas.
- `data_quality_report.csv` contains the full results of the final 61 validation checks.

## Analysis Results

```text
results/
└── incident_event_audit.csv
```

`incident_event_audit.csv` is an exploratory incident-level audit generated from the CERT malicious incident files.

It summarizes event-type activity for each malicious incident and is used for analysis and inspection.

It is not part of the main model input dataset.

---

# Data Quality

The final behavioral dataset is validated before handoff.

The current validation pipeline performs **61 automated checks** covering:

- dataset structure,
- duplicate User-Day records,
- critical missing values,
- invalid negative values,
- logical consistency,
- binary flag validity,
- baseline quality,
- ground-truth integrity,
- malicious-user coverage,
- attack-date coverage,
- known CERT cases,
- baseline reproducibility.

The complete validation report is stored in:

```text
docs/data_quality_report.csv
```

Feature definitions are documented in:

```text
docs/data_dictionary.xlsx
```