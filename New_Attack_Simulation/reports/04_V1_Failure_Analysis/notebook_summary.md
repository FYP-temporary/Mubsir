# Notebook 04 — V1 Failure Analysis

## 1. Objective

Investigate why the previous MUBSIR attack simulation
reached only 670 simulated users out of 995 approved
scenario assignments.

This notebook is a standalone historical analysis.
Its outputs are not inputs to any subsequent notebook.

## 2. Data Scope

**Previous simulation:** Clear_Attack_Simulation (V1)

**Current reference:** New_Attack_Simulation

**Analyzed population:**
- V1 approved assignments: 995 users
- V1 simulated users: 670
- V1 non-simulated users: 325
- Current multi-channel candidates: 995

The V1 and current candidate populations have identical
user identities.

**Evidence sources:**
- V1 approved scenario catalog and assignments
- V1 scheduling notebook and saved execution reports
- V1 user-level Ground Truth
- Current candidate identity profile

All original sources were read without modification.

## 3. Key Findings

### 3.1 Overall Simulation Outcome

- Assigned users: 995
- Simulated users: 670
- Non-simulated users: 325
- Simulation completion rate: 67.3%

### 3.2 Final Losses by Stage

| Stage | Final Loss | Share of 325 |
|---|---:|---:|
| Preliminary feasibility | 70 | 21.5% |
| Window feasibility | 176 | 54.2% |
| Exact switching/scheduling | 79 | 24.3% |
| **Total** | **325** | **100.0%** |

Window feasibility accounted for the largest final
population loss.

### 3.3 Preliminary Feasibility

- Initial failures: 80
- Alternative recoveries: 10
- Final deferred users: 70
- Three-channel capacity failures: 62
- Multichannel capacity failures: 24
- Active-day capacity failures: 6

Preliminary failure conditions can overlap.

### 3.4 Window Feasibility

- Users evaluated: 925
- Initial window failures: 222
- Alternative recoveries: 46
- Final unresolved users: 176
- Initial window failures involving active-day capacity:
  206

The strict activity requirements inside predefined
windows were a major source of initial failure.

### 3.5 Channel Switching

- Users evaluated: 749
- Initial switching failures: 205
- Alternative and exact-search recoveries:
  126
- Final scheduling losses: 79

Initial switching failure types:
- Insufficient possible switches: 94
- Too many unavoidable switches: 71
- Unreachable target within bounds: 40

Final exact scheduling outcomes:
- Infeasible under V1 rules: 78
- Incomplete: 1

### 3.6 Scenario Design Findings

V1 predefined:
- Durations: 5, 10, 20, 30, 40, 50 workdays
- Switching targets based on fixed Low/Medium/High ranges
- Fixed active/off-day and same-day channel requirements

A total of 289 assigned users had long-duration
scenarios (40 or 50 days) requiring three-channel
activity on at least one common day.

Descriptively, simulation success was:
- Without same-day three-channel requirement: 71.4%
- With same-day three-channel requirement: 57.4%

This association does not establish independent
causality because scenario requirements and
durations were linked.

### 3.7 Lessons Learned

1. Derive feasible scenarios from observed user activity
   before assigning attack configurations.
2. Test durations against feasible user-specific windows.
3. Avoid unnecessary simultaneous multichannel requirements.
4. Derive achievable channel-switching patterns from
   observed activity instead of imposing fixed targets.
5. Preserve no-injection off-days without unnecessary
   predefined quotas.
6. Evaluate frequency/count-based stealth rules separately.
7. Preserve benign multi-channel users to reduce
   shortcut-learning risk.

These are design lessons, not proof that proposed
changes will succeed.

## 4. Validation

**Result:** PASS — 16/16 checks.

Validated:
- Population identities and counts
- Stage-level population losses
- Initial failures and recoveries
- Final scheduling reconciliation
- Duration and switching-level outcomes
- Consistency of the documented failure totals

No old injection notebook was executed.
No original source data was modified.

## 5. Final Deliverables

- `04_V1_Failure_Analysis.ipynb`
- `reports/04_V1_Failure_Analysis/notebook_summary.md`

No Parquet or CSV files are generated.

Notebook 04 remains independent and is not required
by subsequent notebooks.

## 6. Limitations & Next Step

**Limitations:**
- Aggregate stage losses do not prove the individual
  causal reason for every non-simulated user.
- Preliminary rule failures may overlap.
- A V1 infeasibility result applies to its original
  constraints, not necessarily to redesigned scenarios.
- The incomplete scheduling case is not a proven
  infeasible case.
- No V2 simulation improvement has been demonstrated
  by this documentation notebook.

**Next Step:**

Proceed independently to Notebook 05 —
Simulation Rules Feasibility.

Notebook 05 will use original data and the validated
outputs of Notebooks 00–03, not Notebook 04 artifacts.

The provisional V2 population target is 400 malicious
users selected from 995 multi-channel candidates,
subject to feasibility and subsequent ML evaluation.

Historical Baseline remains immutable, and simulation
focus remains on event frequency/counts only.
