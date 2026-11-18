# MUBSIR — Notebook 07
## Scenario Design and Feasible Catalog
### Final Notebook Summary

---

## 1. Purpose

Notebook 07 constructs a validated, user-driven catalog
of feasible attack scenarios for MUBSIR:

**Mubsir: AI-Based Detection of Channel-Rotating
Low-and-Slow Insider Data Exfiltration**

The catalog combines previously approved temporal,
channel, switching, and stealth constraints.

Its purpose is to provide a structured pool of feasible
scenario alternatives for the selection of 400 distinct
attackers in Notebook 08.

**Notebook 07 does not select attackers or inject attacks.**

---

## 2. Previously Approved Inputs

### Structural Window Feasibility — Notebook 05

The notebook reuses previously approved structural
window results, including:

- Eligible user-window combinations
- Approved attack durations
- Proposed attack-active days
- Forced Off-Day counts
- Previously established structural feasibility
- Previously established switching evidence

The structural input contained 472,667 window records,
of which 288,486 passed the approved structural rules.

### Channel Availability — Notebook 05

Previously computed channel-activity summaries and
observed channel sets are reused to determine
supported Email (E), USB (U), and HTTP (H) combinations.

### Stealth Rule — Notebook 06

The selected injection-count rule is:

- Formula: **A — Historical User/Channel P95**
- Multiplier configuration: **Balanced**
- High Stealth: 0.25
- Medium Stealth: 0.50
- Low Stealth: 0.75

The approved injection-count expression is:

`I = max(1, ceil(m * P95))`

where m is the selected stealth multiplier.

This notebook records approved stealth configurations;
actual daily injection counts are not generated here.

---

## 3. Notebook Workflow

### 7.1 — Approved Inputs and Rules Loading

Loaded the approved structural window results,
channel summaries, and selected stealth-rule metadata.

Source artifacts were reused without modifying
the original datasets.

### 7.2 — Eligible Window Pool

Selected the 288,486 structurally approved user windows.

The selection preserved the metadata needed for
scenario feasibility and future assignment.

### 7.3 — Channel Configuration and Switching Compatibility

Evaluated the approved channel configurations:

- E+U
- E+H
- U+H
- E+U+H

Candidate channel subsets were assessed using
the approved window and channel evidence.

An exact selected-channel switching procedure
was applied where the original proof was not
sufficient for a particular channel subset.

The final result contained **360,466** feasible
channel-set and switching combinations.

The approved switching levels are:

- Low
- Medium
- High

The five-workday exception requires exactly
one, two, or three switches, respectively.

The catalog preserves attainable exact switch
counts using the selected-channel bitmask.

This is switching feasibility evidence, not a
finalized daily channel schedule.

### 7.4 — Stealth Expansion

Expanded the feasible channel/switching options
using the three approved stealth levels.

This produced **2,360,793** scenario options.

No real attack injection was performed.

### 7.5 — Scenario Catalog Construction

Constructed the scenario-option catalog and
the scenario-type reference table.

A scenario type is defined by:

- Attack duration
- Channel configuration
- Switching level
- Stealth level

A scenario option additionally represents a
specific user and eligible attack window.

The final catalog contains:

- **2,360,793 scenario options**
- **213 supported scenario types**
- **936 distinct candidate users**

### 7.5.1 — Comprehensive Catalog QA

The previously completed catalog QA reported:

- **33 checks performed**
- **33 checks passed**
- **0 checks failed**

The QA covered catalog construction integrity,
configuration consistency, and traceability to
approved upstream results.

It did not independently revalidate the underlying
switching algorithm or a finalized injection schedule.

### 7.6 — Scenario Diversity Analysis

Analyzed the validated catalog by counting
distinct supporting users and available options
for each scenario type.

Five Jupyter visualizations were generated:

1. User coverage by duration and channel set
2. Two-channel versus three-channel support
3. Distribution of user support across scenario types
4. Fifteen rarest supported scenario types
5. Switching-level support by channel configuration

A separate interpretation section documents
the findings of these figures.

### 7.7 — Final Catalog Export and Handoff

Exported the complete scenario catalog, type
definitions, coverage results, comprehensive
dictionary, and diversity report.

Previously approved QA reports were preserved.

The exported catalog and supporting documents
were checked for presence and readability.

---

## 4. Final Results

| Metric | Result |
|---|---:|
| Structurally approved windows | 288,486 |
| Feasible channel/switching combinations | 360,466 |
| Final scenario options | 2,360,793 |
| Supported scenario types | 213 |
| Theoretical scenario types | 216 |
| Candidate users | 936 |
| Catalog QA checks passed | 33 / 33 |
| Scenario types with fewer than 50 users | 36 |
| Scenario types with fewer than 100 users | 45 |
| Median users per scenario type | 261.0 |
| Minimum users per scenario type | 4 |
| Maximum users per scenario type | 634 |

### Unsupported Theoretical Configurations

Three theoretical scenario types are infeasible:

- 5 days + E+U+H + Low Switching + High Stealth
- 5 days + E+U+H + Low Switching + Medium Stealth
- 5 days + E+U+H + Low Switching + Low Stealth

Using all three channels requires at least
two channel switches, while five-day Low
Switching permits exactly one switch.

---

## 5. Main Diversity Findings

### Duration Coverage

All six approved durations are represented:

5, 10, 20, 30, 40, and 50 eligible workdays.

### Channel Coverage

Both two-channel and three-channel configurations
are represented across the six durations.

E+U generally provides broad user availability.

U+H is substantially less available,
especially in longer windows.

### Switching Coverage

Low, Medium, and High Switching are represented
across the supported channel configurations.

Availability becomes more constrained for some
specific duration/channel/switching combinations.

### Rare Configurations

The rarest supported configurations involve
long-duration U+H attacks with High Switching.

The 50-day U+H High-Switching configuration
has only four supporting users.

Stealth variants can share the same supporting
users and are not independent candidate groups.

### Interpretation

The catalog is diverse but unevenly distributed.

Distinct-user availability must be considered
alongside scenario-option counts during
the selection of 400 attackers.

---

## 6. Approved Rules and Constraints

The next stage must preserve the following:

1. Historical Baseline data remains unchanged.
2. Attack injection is restricted to the approved Future period.
3. Attack activity is restricted to eligible workdays.
4. Forced Off-Days contain no attack injection.
5. Optional Off-Days are not introduced by channel selection.
6. Only previously approved window durations are used.
7. Approved channel configurations are preserved.
8. Selected-channel switching feasibility is respected.
9. Formula A and the Balanced multipliers remain unchanged.
10. Scenario assignment must not duplicate attacker users.
11. Fewer forced Off-Days are preferred among otherwise
    suitable feasible assignments.

---

## 7. Deliverable Definitions

### feasible_scenario_catalog.parquet

Complete set of approved user-window-channel-switching-
stealth options.

Primary handoff input for Notebook 08.

### scenario_types.parquet

Reference definitions of the 213 supported scenario types.

### scenario_diversity_coverage.csv

Availability statistics for each scenario type,
including distinct supporting users and options.

### scenario_catalog_qa.csv

Detailed results of the 33 previously completed QA checks.

### scenario_catalog_qa_report.md

Narrative documentation of the QA results,
scope, limitations, and approval decision.

### scenario_diversity_report.md

Detailed numerical diversity findings,
interpretation, and attacker-selection considerations.

### scenario_catalog_dictionary.csv

Comprehensive descriptions of Notebook 07's output
artifacts and structured data columns.

### notebook_summary.md

Consolidated documentation of the methodology,
results, constraints, deliverables, and handoff.

### Section 7.6 — Jupyter Figures

Five visualizations stored as notebook outputs.
These are not separate exported image files.

---

## 8. Notebook Limitations

- The catalog contains alternatives, not finalized attacks.
- The final 400 attackers have not been selected.
- Each user may support multiple scenario alternatives.
- Exact daily switch counts remain unselected.
- Daily channel sequences have not been finalized.
- No attack injection has been performed.
- No ground-truth attack labels have been generated here.
- No model training or detection evaluation occurs here.
- Coverage does not guarantee simultaneous representation
  of all supported scenario types among 400 attackers.

---

## 9. Handoff to Notebook 08

**Next notebook: Attacker Selection & Scenario Assignment**

Notebook 08 should use the exported catalog to:

1. Select exactly 400 distinct eligible attackers.
2. Assign one feasible scenario option per selected user.
3. Preserve diversity across approved attack durations.
4. Preserve diversity across channel sets.
5. Preserve Low, Medium, and High Switching.
6. Distribute approved stealth levels.
7. Consider scarce scenario configurations.
8. Prefer fewer forced Off-Days where possible.
9. Preserve original approved feasibility constraints.

Daily attack scheduling and actual injection
are handled in later notebooks.

---

## 10. Final Status

**Catalog Construction: COMPLETE**

**Catalog QA: 33/33 PASS**

**Diversity Analysis: COMPLETE**

**Final Export: COMPLETE**

**Notebook 07: READY FOR HANDOFF**

**400-Attacker Assignment: NOT STARTED**

**Attack Injection: NOT PERFORMED**

No source datasets or historical baseline records
were modified during this final documentation step.
