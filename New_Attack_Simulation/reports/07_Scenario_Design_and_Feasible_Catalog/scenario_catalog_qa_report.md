# MUBSIR — Notebook 07
## Comprehensive Scenario Catalog QA Report

### 1. Objective

Validate the integrity, completeness, configuration consistency,
and source traceability of the newly constructed user-driven
scenario catalog before diversity coverage analysis.

### 2. Catalog Scope

- Catalog options: **2,360,793**
- Scenario types: **213**
- Distinct users: **936**
- Approved durations: 5, 10, 20, 30, 40, 50 eligible workdays
- Channel configurations: E+U, E+H, U+H, E+U+H
- Switching levels: Low, Medium, High
- Stealth levels: High, Medium, Low
- Injection formula: A — Historical P95-Based
- Multiplier configuration: Balanced

### 3. Validation Summary

- Total checks: **33**
- Passed: **33**
- Failed: **0**
- Final status: **PASS**

### 4. Detailed Validation Results

| # | Validation Check | Status | Details |
|---:|---|---|---|
| 1 | Catalog option count | PASS | Catalog=2,360,793; Source=2,360,793 |
| 2 | Scenario type count | PASS | Types=213 |
| 3 | User population preserved | PASS |  |
| 4 | Required fields present | PASS |  |
| 5 | No nulls in required catalog fields | PASS |  |
| 6 | Option IDs unique | PASS |  |
| 7 | Option IDs continuous | PASS |  |
| 8 | Type IDs unique | PASS |  |
| 9 | Type IDs continuous | PASS |  |
| 10 | No duplicate scenario options | PASS |  |
| 11 | No duplicate scenario types | PASS |  |
| 12 | Every type ID is referenced | PASS |  |
| 13 | Exact scenario type-ID mapping | PASS |  |
| 14 | Full source-to-catalog value preservation | PASS |  |
| 15 | Approved-window traceability and metadata | PASS |  |
| 16 | Approved durations only | PASS |  |
| 17 | Channel configuration/count mapping | PASS |  |
| 18 | Approved switching levels | PASS |  |
| 19 | Approved stealth levels | PASS |  |
| 20 | Formula A preserved | PASS |  |
| 21 | Balanced configuration preserved | PASS |  |
| 22 | Exact stealth multiplier mapping | PASS |  |
| 23 | Forced Off-Days nonnegative | PASS |  |
| 24 | Forced Off-Days within approved maximum | PASS |  |
| 25 | Five-day windows have zero forced Off-Days | PASS |  |
| 26 | Positive active days | PASS |  |
| 27 | Active days within duration | PASS |  |
| 28 | Window dates ordered | PASS |  |
| 29 | Exact switching evidence retained | PASS |  |
| 30 | Proof sources recognized | PASS |  |
| 31 | Exactly three theoretical types absent | PASS |  |
| 32 | Impossible five-day three-channel Low absent | PASS |  |
| 33 | Missing types match exact expected exception | PASS |  |

### 5. Scenario Type Coverage

- Theoretical configurations: **216**
- Supported configurations: **213**
- Unsupported configurations: **3**

The three unsupported configurations are:

- 5 workdays + E+U+H + Low Switching + High Stealth
- 5 workdays + E+U+H + Low Switching + Medium Stealth
- 5 workdays + E+U+H + Low Switching + Low Stealth

A three-channel attack requires at least two switches,
whereas the approved five-day Low Switching rule requires
exactly one switch.

### 6. Validation Boundaries

This report validates:

- Catalog completeness and unique identifiers.
- Scenario-type mapping and source traceability.
- Preservation of approved window metadata.
- Configuration integrity and rule consistency.
- Preservation of previously proven switching evidence.

This report does **not** independently revalidate the
underlying switching algorithm, prove a finalized daily
injection schedule, or establish model detection performance.

### 7. Final Decision

**CATALOG QA: PASS**

The catalog is approved for Notebook 07,
Section 7.6 — Scenario Diversity Coverage Analysis.

No original datasets were modified.
No attacker assignment or attack injection was performed.
