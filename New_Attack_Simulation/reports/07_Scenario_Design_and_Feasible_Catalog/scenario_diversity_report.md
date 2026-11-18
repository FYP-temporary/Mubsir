# MUBSIR — Notebook 07
## Scenario Diversity Coverage Report

### 1. Objective

Analyze the availability and diversity of validated scenario
options to support the selection of 400 distinct attackers
in Notebook 08.

All numerical findings are reused from Section 7.6.

### 2. Validated Catalog Overview

- **Catalog options:** 2,360,793
- **Supported scenario types:** 213
- **Theoretical scenario types:** 216
- **Distinct candidate users:** 936
- **Catalog QA:** 33/33 PASS
- **Attack durations:** 5, 10, 20, 30, 40, 50 workdays
- **Channel configurations:** E+U, E+H, U+H, E+U+H
- **Switching levels:** Low, Medium, High
- **Stealth levels:** High, Medium, Low
- **Injection rule:** Formula A + Balanced

### 3. Overall Diversity Findings

- **Minimum supporting users per type:** 4
- **Median supporting users per type:** 261.0
- **Maximum supporting users per type:** 634
- **Types with fewer than 50 users:** 36
- **Types with fewer than 100 users:** 45

The availability of scenario types is uneven.

Distinct supporting users are the main availability measure
because overlapping windows do not represent independent attackers.

### 4. Figure 1 — User Coverage by Duration and Channel Set

| Duration | E+U | E+H | U+H | E+U+H |
| --- | --- | --- | --- | --- |
| 5 | 629 | 475 | 151 | 264 |
| 10 | 653 | 480 | 102 | 278 |
| 20 | 589 | 411 | 43 | 261 |
| 30 | 548 | 348 | 36 | 248 |
| 40 | 486 | 304 | 27 | 235 |
| 50 | 447 | 272 | 22 | 232 |

**Interpretation**

- E+U has broad availability across all six durations.
- E+H and E+U+H are also represented throughout.
- U+H has the lowest availability, especially for long attacks.
- Supporting-user counts overlap across configurations.

### 5. Figure 2 — Two-Channel vs. Three-Channel Support

| Duration | Two Channels | Three Channels |
| --- | --- | --- |
| 5 | 888 | 264 |
| 10 | 926 | 278 |
| 20 | 831 | 261 |
| 30 | 799 | 248 |
| 40 | 745 | 235 |
| 50 | 699 | 232 |

**Interpretation**

- Both two-channel and three-channel scenarios remain available
  across all six durations.
- Two-channel scenarios have a larger supporting population.
- Users may qualify for both channel-count categories.

### 6. Figure 3 — Distribution of User Support

Scenario-type availability ranges from 4
to 634 distinct users.

The median is 261.0 users per type.

There are 36 types supported by fewer than
50 users and 45 types supported by fewer
than 100 users.

**Interpretation**

The catalog provides broad diversity, but some scenario types
are much more constrained than others.

Selection should account for the availability of distinct users,
not only the number of user-window alternatives.

### 7. Figure 4 — Fifteen Rarest Scenario Types

| Scenario Type | Duration | Channels | Switching | Stealth | Supporting Users | Available Options |
| --- | --- | --- | --- | --- | --- | --- |
| 205 | 50 | U+H | High | High | 4 | 72 |
| 206 | 50 | U+H | High | Low | 4 | 72 |
| 207 | 50 | U+H | High | Medium | 4 | 72 |
| 169 | 40 | U+H | High | High | 7 | 81 |
| 170 | 40 | U+H | High | Low | 7 | 81 |
| 171 | 40 | U+H | High | Medium | 7 | 81 |
| 133 | 30 | U+H | High | High | 13 | 145 |
| 134 | 30 | U+H | High | Low | 13 | 145 |
| 135 | 30 | U+H | High | Medium | 13 | 145 |
| 211 | 50 | U+H | Medium | High | 18 | 717 |
| 212 | 50 | U+H | Medium | Low | 18 | 717 |
| 213 | 50 | U+H | Medium | Medium | 18 | 717 |
| 208 | 50 | U+H | Low | High | 22 | 1037 |
| 209 | 50 | U+H | Low | Low | 22 | 1037 |
| 210 | 50 | U+H | Low | Medium | 22 | 1037 |

**Interpretation**

The rarest supported scenarios concentrate on long-duration
U+H configurations, particularly High Switching.

Repeated stealth variants can depend on the same supporting
users and must not be treated as independent user populations.

These rare combinations deserve consideration during
diversity-aware attacker assignment.

### 8. Figure 5 — Switching-Level Coverage

| Channel Configuration | Low | Medium | High |
| --- | --- | --- | --- |
| E+U | 636 | 645 | 606 |
| E+H | 475 | 485 | 475 |
| U+H | 120 | 138 | 134 |
| E+U+H | 230 | 271 | 280 |

**Interpretation**

Low, Medium, and High Switching are represented in all four
channel configurations across the overall catalog.

The main limitation arises from specific combinations of
duration, channel configuration, and switching intensity.

### 9. Unsupported Theoretical Scenario Types

Three theoretical scenario types are unsupported:

- 5 days + E+U+H + Low Switching + High Stealth
- 5 days + E+U+H + Low Switching + Medium Stealth
- 5 days + E+U+H + Low Switching + Low Stealth

A three-channel attack requires at least two switches,
whereas the five-day Low Switching exception requires
exactly one switch.

### 10. Implications for Notebook 08

The selection stage should:

1. Select 400 distinct users from the approved candidate pool.
2. Preserve diversity across all six attack durations.
3. Represent different two-channel combinations.
4. Represent three-channel scenarios.
5. Represent Low, Medium, and High Switching.
6. Distribute the approved stealth levels.
7. Consider rare supported scenario types during assignment.
8. Avoid counting the same user as multiple attackers.
9. Prefer fewer forced Off-Days when suitable alternatives exist.
10. Preserve all previously approved feasibility constraints.

These are assignment objectives, not completed assignments.

### 11. Interpretation Boundaries

- Scenario options are not finalized attacks.
- Multiple options can belong to the same user.
- Coverage does not guarantee simultaneous representation
  of all 213 scenario types among 400 attackers.
- Exact switch counts and daily channel schedules
  remain unassigned.
- No injection or detection-performance evaluation
  was performed in Notebook 07.
- The five visualizations remain in the Jupyter notebook;
  this report records their numerical findings and interpretation.

### 12. Handoff Decision

The validated catalog, scenario-type definitions,
diversity coverage, comprehensive dictionary, and
previously approved QA reports are prepared for Notebook 08.

**Catalog QA: PASS**

**Attacker assignment: NOT STARTED**

**Injection: NOT PERFORMED**

No original source data or historical Baseline was modified.
