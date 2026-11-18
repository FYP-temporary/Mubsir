# Notebook 11 — Ground Truth and Quality Validation

## Status

COMPLETE — INDEPENDENT VALIDATION APPROVED

## Ground Truth Datasets

### User-Day Ground Truth
- File: ground_truth_user_days_r62.parquet
- Records: 9,080
- Columns: 42
- Granularity: One executed attack User-Day

### Channel-Day Ground Truth
- File: ground_truth_channel_days_r62.parquet
- Records: 10,124
- Columns: 27
- Granularity: One executed User-Day-Channel action

## Approved Attack Population

- Attackers: 400
- Active attacked User-Days: 9,080
- Verified channel-actions: 10,124
- Additional injected attack events: 29,007
- Forced off-days excluded: 1,670

## Channel-Day Distribution

- EMAIL: 6,703 actions; 17,791 events
- USB: 1,935 actions; 4,920 events
- HTTP: 1,486 actions; 6,296 events

## User-Day Channel Distribution

- Single-channel days: 8,073
- Two-channel days: 970
- Three-channel days: 37

## QA Results

- Section 11.2: 35/35 PASS
- Section 11.3: 20/20 PASS
- Section 11.4: 27/27 PASS
- Section 11.5: 58/58 PASS

## Provenance

- Notebook 08: Approved attacker scenario assignments
- Notebook 09: Daily attack schedule
- Notebook 10: Verified injection execution evidence
- Notebook 11: Ground Truth construction and validation

## Data Boundaries

Both Ground Truth datasets contain executed attacks only.

No classification target y is included.

No User-Level Ground Truth is separately exported.

No behavioral features were calculated.

No source dataset was modified.

## Next Stage

Notebook 12 — Injected Feature Engineering and Validation.

The binary classification target y will be constructed
by matching Behavioral Features (user, day) against the
attack-only User-Day Ground Truth.
