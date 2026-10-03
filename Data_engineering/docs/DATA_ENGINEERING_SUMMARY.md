# Data Engineering Summary

## Overview

This document summarizes the data engineering workflow developed for:

**AI-Based Detection of Cross-Channel Low-and-Slow Data Exfiltration Using UEBA**

The workflow transforms the CERT Insider Threat Dataset r6.2 into structured behavioral datasets suitable for user behavior analytics, synthetic low-and-slow attack generation, machine-learning experiments, and evaluation.

---

## Exfiltration Channels

The project focuses on three potential data-exfiltration channels:

- External Email
- USB / Removable Media
- HTTP Upload

Logon activity is also used to identify valid user workdays and provide temporal context.

---

## Processing Workflow

The data engineering process consists of the following stages:

```text
CERT r6.2 Raw Data
        ↓
Feasibility Audit
        ↓
Daily Channel Aggregation
        ↓
Unified User-Day Dataset
        ↓
Benign User Baselines
        ↓
Behavioral Feature Engineering
        ↓
Ground-Truth Preparation
        ↓
Malicious Pre-Attack Baselines
        ↓
Feature Documentation
        ↓
Final QA
        ↓
Final Integrity Validation
```

---

## Daily Channel Aggregation

Raw CERT activity is aggregated into daily user-level datasets for:

- Email
- USB/File activity
- HTTP activity
- Logon activity

This reduces the original event-level data into a more manageable behavioral representation.

---

## Unified User-Day Dataset

Daily channel datasets are combined into a unified user-day representation.

The resulting dataset contains:

- **1,394,010 user-day records**
- **4,000 users**
- **516 calendar days**

The dataset covers activity from January 2010 through June 2011.

---

## Benign Baseline Population

The project separates known malicious CERT users from the benign baseline population.

Population summary:

```text
Total users             : 4000
Known malicious users   : 5
Benign users            : 3995
```

The five known malicious users are excluded from normal behavioral baseline construction.

---

## Baseline Period

The primary benign baseline cutoff is:

```text
2011-01-01
```

Activity before this date is used to build user-specific behavioral baselines.

The future period is used for behavioral analysis, synthetic attack generation, and later evaluation.

---

## Behavioral Feature Dataset

The final behavioral feature dataset contains:

```text
Rows     : 387,162
Columns  : 85
Users    : 3,737
```

The features include:

- Daily channel activity
- User-specific baseline statistics
- Baseline-relative behavior
- Rolling 5-workday activity
- Rolling 10-workday activity
- Rolling 20-workday activity
- Cross-channel activity
- Multi-channel behavioral signals

The main dataset is:

```text
data/features/behavior_features_r62_v1.parquet
```

---

## Synthetic Attack Host Eligibility

Benign users are evaluated for suitability as hosts for later synthetic low-and-slow attack injection.

The strict eligibility criteria require sufficient historical activity across all three studied channels.

Final eligibility counts are:

```text
30-day threshold : 199 users
40-day threshold : 158 users
50-day threshold : 126 users
```

The strict 50-day group contains **126 eligible users**.

---

## Ground Truth

Official CERT r6.2 malicious-user information is cleaned and structured into two datasets:

```text
data/processed/ground_truth_users_r62.parquet
data/processed/ground_truth_events_r62.parquet
```

The final ground-truth event dataset contains:

```text
470 scenario-related events
420 primary malicious-actor events
50 contextual events
```

Five known malicious users are represented.

---

## Malicious Pre-Attack Baselines

Separate pre-attack behavioral baselines are created for each of the five known malicious users.

Only activity occurring before each user's official attack start is used.

This prevents malicious-period activity from contaminating the behavioral baseline.

---

## Final Outputs

### Processed Data

```text
email_daily_r62.parquet
usb_daily_r62.parquet
http_daily_r62.parquet
logon_daily_r62.parquet
user_day_r62_v1.parquet
ground_truth_users_r62.parquet
ground_truth_events_r62.parquet
```

### Feature Data

```text
user_baseline_r62_v1.parquet
behavior_features_r62_v1.parquet
attack_host_eligibility_r62.parquet
malicious_pre_attack_baseline_r62.parquet
```

### Documentation

```text
feature_dictionary_r62.csv
schema_dictionary_r62.csv
dataset_inventory_r62.csv
```

---

## Quality Assurance

The final workflow includes dedicated QA and integrity-validation stages.

The validation checks include:

- Dataset dimensions
- Channel event totals
- User counts
- Duplicate detection
- Missing critical values
- Date-range consistency
- Benign/malicious population separation
- Ground-truth consistency
- Baseline temporal leakage
- Feature documentation completeness
- Project path portability

The final validated build passed all integrity checks.

---

## Reproducibility

The data engineering workflow uses portable project-relative paths.

The complete workflow can be executed using:

```bash
python src/run_pipeline.py
```

Environment validation can be performed with:

```bash
python src/run_pipeline.py --check-only
```

The raw CERT r6.2 dataset is required only for stages that rebuild outputs directly from the original data.