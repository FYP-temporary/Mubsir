# MUBSIR — Clear Attack Simulation

**Dataset:** CERT r6.2  
**Component:** Multi-Channel Attack Simulation  
**Status:** Stage 3.5 Validated  
**Approved Injection Formula:** B_Natural_Addition

## 1. Project Overview

MUBSIR investigates low-and-slow data exfiltration
across Email, USB, and HTTP channels.

The Attack Simulation component models synthetic
exfiltration behavior by increasing aggregated daily
event counts according to validated attack schedules.

The simulation does not create raw synthetic events,
individual event identifiers, or payload bytes.

This folder contains the organized project notebooks,
simulation datasets, Ground Truth, documentation,
and independent QA evidence.

## 2. Project Directory Structure

```text
Clear_Attack_Simulation/
├── data/
│   ├── final/
│   │   ├── behavior_features_r62_ml_final.parquet
│   │   └── user_day_injected_r62.parquet
│   ├── ground_truth/
│   │   ├── ground_truth_channel_days.parquet
│   │   ├── ground_truth_user_days.parquet
│   │   └── ground_truth_users.parquet
│   └── stages_output/
│       ├── approved_attack_scenarios_r62.csv
│       ├── approved_scenario_catalog_r62.parquet
│       ├── approved_switching_ranges.csv
│       ├── behavior_features_injected_final.parquet
│       ├── stage2_assignment_validation_manifest_r62.json
│       └── validated_scenario_assignments_r62.parquet
├── documentation/
│   ├── dictionary/
│   │   ├── feature_dictionary_attack_simulation_r62.csv
│   │   ├── ground_truth_dictionary_attack_simulation_r62.csv
│   │   ├── new_features_dictionary_30_r62.csv
│   │   └── schema_dictionary_attack_simulation_r62.csv
│   ├── dataset_inventory_attack_simulation_r62.csv
│   ├── MUBSIR_Injection_Formula_Selection_AR.docx
├── notebooks/
│   ├── 01_scenario_rules_and_feasibility.ipynb
│   ├── 02_user_eligibility_and_assignment.ipynb
│   ├── 03_attack_scheduling_and_injection.ipynb
│   ├── 04_independent_end_to_end_validation.ipynb
│   └── Reconstruct Injected User-Day.ipynb
├── validation_inputs/
│   └── validated_schedule_339.parquet
├── validation_reports/
│   └── Stage_3_5_QA_20261026T132721Z_9ee5d80e/
│       ├── MUBSIR_Stage3_5_File_Manifest.csv
│       ├── MUBSIR_Stage3_5_Independent_QA_Report.html
│       ├── MUBSIR_Stage3_5_QA_Checks.csv
│       └── MUBSIR_Stage3_5_QA_Summary.json
└── README.md
```

## 3. Simulation Workflow

### Stage 1 — Scenario Design and Feasibility

Notebook: `notebooks/01_scenario_rules_and_feasibility.ipynb`

Defines attack scenarios, duration constraints,
Off days, channel combinations, and switching rules.

Approved attack scenarios: **1,143**.

### Stage 2 — User Eligibility and Assignment

Notebook: `notebooks/02_user_eligibility_and_assignment.ipynb`

Evaluates candidate users and assigns scenarios.

Preliminary assigned users: **995**.

The preliminary assignments must not be confused
with the final 670 users who received validated schedules.

### Stage 3 — Attack Scheduling and Injection

Notebook: `notebooks/03_attack_scheduling_and_injection.ipynb`

Constructs validated attack schedules, evaluates
injection quantity formulas A, B, and C,
and applies the selected Formula B.

Final simulated users: **670**.

Produces injected behavioral features and
three Ground Truth datasets.

### Stage 3.5 — Independent QA

Notebook: `notebooks/04_independent_end_to_end_validation.ipynb`

Independently validates injection calculations,
schedule consistency, reconstructed features,
Ground Truth, historical baseline preservation,
and saved file integrity.

### Additional User-Day Reconstruction

Notebook: `notebooks/Reconstruct Injected User-Day.ipynb`

Additional reconstruction work associated with
the organized project.

This notebook is documented separately from the
original Stage 1–3.5 execution sequence.
Its exact outputs should be interpreted from its
own code and execution results.

## 4. Dataset Inventory

All dimensions below were read directly
from the available Parquet metadata.

| Dataset | Relative Path | Rows | Columns |
|---|---|---:|---:|
| Final ML Features | `data/final/behavior_features_r62_ml_final.parquet` | 387,162 | 116 |
| Injected User-Day | `data/final/user_day_injected_r62.parquet` | 1,394,010 | 34 |
| GT Channel-Days | `data/ground_truth/ground_truth_channel_days.parquet` | 14,375 | 11 |
| GT User-Days | `data/ground_truth/ground_truth_user_days.parquet` | 69,634 | 13 |
| GT Users | `data/ground_truth/ground_truth_users.parquet` | 670 | 12 |
| Stage 3 Injected Features | `data/stages_output/behavior_features_injected_final.parquet` | 69,634 | 115 |
| Approved Scenario Catalog | `data/stages_output/approved_scenario_catalog_r62.parquet` | 1,143 | 15 |
| Validated Scenario Assignments | `data/stages_output/validated_scenario_assignments_r62.parquet` | 995 | 9 |
| Validated Schedule | `validation_inputs/validated_schedule_339.parquet` | 15,010 | 12 |

### Dataset Organization

**data/stages_output/** contains approved scenario
artifacts, preliminary user assignments, and
the Stage 3 injected behavioral features.

**data/ground_truth/** contains user-level,
user-day-level, and channel-day-level
synthetic attack Ground Truth.

**data/final/** contains two additional datasets:
the ML final feature file and injected User-Day file.

These datasets have a broader row scope than the
670-user Stage 3 simulation output. Their file
dimensions alone do not establish equivalent
validation coverage.

## 5. Injection Method

Selected formula: **Formula B — Natural Activity Addition**

```text
Injected Count = max(1, ceil(Natural Count × Multiplier))
Final Count = Natural Count + Injected Count
```

Stealth multipliers:

- High Stealth: 0.5
- Medium Stealth: 1.0
- Low Stealth: 1.5

Synthetic event counts are added only to channels
with existing natural activity on the same user-day.

Original historical baseline values and
byte-related measurements remain preserved.

## 6. Validated Attack Schedule

File: `validation_inputs/validated_schedule_339.parquet`

The schedule is an approved planning and
validation input.

It records scheduled attack and Off days
and planned channel activity.

- Attack days: **12,636**
- Off days: **2,374**

This file is not intended as an ML predictor.

## 7. Ground Truth and ML Guidance

Stage 3 feature dataset:

`data/stages_output/behavior_features_injected_final.parquet`

Daily labels:

`data/ground_truth/ground_truth_user_days.parquet`

For the original Stage 3 daily detection task,
join these files on `(user, day)`.

The binary target is `is_attack_day`.

Do not use Ground Truth or scenario metadata
as training predictors.

An `is_attack_day=0` label indicates no
synthetic injection on that user-day.
It does not establish that all underlying
source activity was benign.

The five original malicious CERT users
were excluded from the synthetic attack cohort.

The additional datasets in `data/final/`
should be assessed independently before
selecting ML training inputs.

## 8. Independent Validation Results

Source: `MUBSIR_Stage3_5_QA_Summary.json`

| Metric | Verified Result |
|---|---:|
| Simulated Users | 670 |
| Attack Days | 12,636 |
| Off Days | 2,374 |
| Injected Channel-Days | 14,375 |
| Injected Event Counts | 42,095 |
| Original Feature Columns | 85 |
| Newly Engineered Features | 30 |
| Final Feature Columns | 115 |
| Compared Values | 8,756,986 |
| Unexplained Mismatches | 0 |
| Mandatory Checks Passed | 19/19 |

The original Stage 3.5 audit completed
**19/19 mandatory checks successfully**.

These results apply to the original audited
simulation outputs. They do not automatically
certify the additional final datasets.

## 9. File Integrity and QA Reports

The QA report directory contains:

- `MUBSIR_Stage3_5_File_Manifest.csv`
  — file paths, sizes, and SHA-256 integrity records.

- `MUBSIR_Stage3_5_Independent_QA_Report.html`
  — detailed visual QA report.

- `MUBSIR_Stage3_5_QA_Checks.csv`
  — individual mandatory quality checks.

- `MUBSIR_Stage3_5_QA_Summary.json`
  — compact machine-readable QA summary.

The updated File Manifest records nine historical
file integrity matches and two additional final
datasets marked outside the original QA scope.

## 10. Documentation

**documentation/dictionary/** contains the
feature, new-feature, Ground Truth, and schema dictionaries.

**documentation/dataset_inventory_attack_simulation_r62.csv**
records the six main Parquet datasets,
their verified dimensions, and current paths.

**documentation/MUBSIR_Injection_Formula_Selection_AR.docx**
documents the formula evaluation and selection.


## 11. Execution Warning

The notebooks retain historical execution logic.
Some original paths may reference the previous
Attack_Simulation working directory.

Do not run all cells without checking
source paths and output destinations.

The existing exported datasets and QA reports
must be preserved unless an intentional
reconstruction or validation run is required.

## 12. Validation Scope

The Stage 3 synthetic simulation and its
independent Stage 3.5 validation are complete.

The additional datasets inside `data/final/`
are documented as part of the organized project,
but their broader contents are not automatically
covered by the original Stage 3.5 QA results.
