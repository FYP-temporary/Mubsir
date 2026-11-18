# Notebook 10 — Attack Injection Pipeline

## Status
COMPLETE — INDEPENDENT VALIDATION APPROVED

## Original Population
- Users: 4,000
- User-Day rows: 1,394,010
- Columns: 34

## Approved Attack Simulation
- Attackers: 400
- Active attack User-Days: 9,080
- Forced Off-Days: 1,670
- Channel-actions: 10,124
- Additional attack events: 29,007

## Event Increments
- EMAIL: 17,791
- USB: 4,920
- HTTP: 6,296

## Injection Method
Formula A: I = max(1, ceil(m * historical_P95))

- High Stealth: 0.25
- Medium Stealth: 0.50
- Low Stealth: 0.75

Existing user-channel P95 references were reused without
historical baseline recalculation.

## Modified User-Day Fields
- external_email_count
- email_send_count
- email_event_count
- usb_copy_count
- file_copy_count
- file_event_count
- www_upload_count
- http_event_count

The other 26 columns retain their original values.

## Validation
- Count-consistency QA: 7/7 PASS
- Independent end-to-end QA: 43/43 PASS
- Original source matched the on-disk Parquet by exact values.
- Baseline remained unchanged.
- All 3,600 benign users remained unchanged.
- All forced off-days remained unchanged.
- All eight target fields matched independent reconstruction.
- All 26 non-targeted fields remained unchanged.
- Original Data Engineering logical relationships were preserved.

## Scope
Count-based injection only.

No Ground Truth was generated.
No behavioral feature engineering was performed.
No original source files were modified.

## Handoff
Notebook 11: Ground Truth and Quality Validation.

Notebook 12: Injected Feature Engineering and Validation.

The exported injected User-Day is a full-population,
count-level intermediate dataset.
