# MUBSIR — Notebook 06: Stealth and Injection Count Feasibility

## 1. Objective

Evaluate and select an event-count-based injection formula and stealth multipliers for MUBSIR's simulated channel-rotating low-and-slow insider data exfiltration.

The objective is to establish meaningful differences among High, Medium, and Low Stealth without automatically selecting the most aggressive or least detectable option.

This notebook evaluates hypothetical injection counts and behavioral effects. It does not perform final attacker assignment, attack scheduling, or actual injection.

## 2. Data Scope and Input Verification

- Dataset: CERT r6.2.
- Structurally compatible users: 936.
- Compatible structural windows inherited from Notebook 05: 288,486.
- Active User-Day-Channel observations: 100,585.
- Channels: EMAIL, USB, HTTP.
- Historical Baseline: immutable.
- Injection analysis: event counts/frequency only.
- Evaluation: hypothetical, not an executed attack.

### Channel Coverage

| Channel | Observations | Users | Median Natural Events |
| --- | --- | --- | --- |
| EMAIL | 57815 | 936 | 2.00 |
| USB | 29612 | 690 | 2.00 |
| HTTP | 13158 | 533 | 2.00 |

Input verification covered source schemas, primary keys, natural event counts, historical reference availability, missing values, date boundaries, and reconciliation with processed User-Day sources.

## 3. Key Findings and Selection Evidence

### 3.1 — Candidate Injection Formulas

**Formula A — Historical P95-Based**

`I = max(1, ceil(m × P95))`

Uses the user's historical channel-specific P95 event-count reference.

**Formula B — Natural Daily Count-Based**

`I = max(1, ceil(m × N))`

Uses the user's current natural daily event count in the evaluated channel.

Where:
- `I`: additional injected events.
- `m`: stealth multiplier.
- `P95`: historical user/channel event-count P95.
- `N`: natural daily event count.
- Minimum additional events: 1.

Both formulas were tested on the same verified observations to permit controlled comparisons.

### 3.2 — All Six Tested Multiplier Configurations

| Configuration | High | Medium | Low |
| --- | --- | --- | --- |
| Conservative | 0.10 | 0.25 | 0.50 |
| Balanced | 0.25 | 0.50 | 0.75 |
| Intermediate | 0.25 | 0.50 | 1.00 |
| V1-A | 0.25 | 0.75 | 1.25 |
| V1-B | 0.50 | 1.00 | 1.50 |
| V1-C | 0.50 | 1.25 | 2.00 |

Each of the six configurations was tested using both formulas, giving **12 formula/configuration combinations** and **36 formula/configuration/stealth-level cases**.

### 3.3 — Evaluation Criteria

The configurations were evaluated using:

1. **Strict Stealth Separation:** Percentage of observations satisfying `I_High < I_Medium < I_Low`.
2. **Low-Activity Separation:** Strict separation when natural activity is `N = 1`, including additional low-activity and MAD-related sensitivity checks.
3. **Daily Injection Impact:** Distribution and magnitude of additional event counts.
4. **Historical P95 Exposure:** Percentage newly crossing the historical P95 after hypothetical injection, distinguished from pre-existing exceedances.
5. **Cumulative Level Separation:** Non-overlap between feasible cumulative injection-count ranges within compatible windows.
6. **Temporal Behavioral Impact:** Controlled changes in rolling 7-, 14-, and 30-day event-count behavior.
7. **Cross-Channel Consistency:** Whether conclusions remain meaningful across EMAIL, USB, and HTTP.
8. **Realism Trade-off:** Preference for differentiated, measurable attacks without automatically choosing excessive behavioral exposure.

**Comparison method:** Formula A and Formula B were compared with the same multiplier configuration. Multiplier configurations were compared while keeping the formula fixed. The final two candidate configurations were also reviewed across channels, but differences between those finalists cannot be attributed solely to the formula because their multipliers differed.

### 3.4 — Complete Daily and Cumulative Comparison

All percentages below come from the evaluated notebook results.

| Formula | Configuration | Strict % | N=1 Strict % | Cumulative Non-overlap % | New P95 High % | New P95 Medium % | New P95 Low % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Conservative | 41.66 | 22.04 | 56.94 | 10.20 | 15.78 | 37.71 |
| A | Balanced | 91.01 | 81.38 | 85.61 | 15.78 | 37.71 | 74.45 |
| A | Intermediate | 92.11 | 83.28 | 94.35 | 15.78 | 37.71 | 96.34 |
| A | V1-A | 98.05 | 94.98 | 92.80 | 15.78 | 74.45 | 96.34 |
| A | V1-B | 98.06 | 94.99 | 88.46 | 37.71 | 96.34 | 96.34 |
| A | V1-C | 98.16 | 95.20 | 88.43 | 37.71 | 96.34 | 96.34 |
| B | Conservative | 14.54 | 0.00 | 52.02 | 10.16 | 12.63 | 23.18 |
| B | Balanced | 38.12 | 0.00 | 72.27 | 12.63 | 23.18 | 33.75 |
| B | Intermediate | 38.12 | 0.00 | 78.97 | 12.63 | 23.18 | 35.77 |
| B | V1-A | 61.68 | 0.00 | 85.53 | 12.63 | 33.75 | 54.89 |
| B | V1-B | 61.68 | 0.00 | 78.67 | 23.18 | 35.77 | 56.63 |
| B | V1-C | 61.68 | 0.00 | 64.89 | 23.18 | 54.89 | 60.92 |

**Column meanings:**
- `Strict %`: daily High < Medium < Low separation.
- `N=1 Strict %`: separation when natural count is exactly one.
- `Cumulative Non-overlap %`: separation of cumulative level ranges.
- `New P95`: newly introduced historical-threshold exceedances, measured across all evaluated active observations.

### 3.5 — Controlled 30-Day Behavioral Impact

Median percentage increase in rolling 30-day event counts under the common hypothetical evaluation pattern:

| Formula | Configuration | High 30d % | Medium 30d % | Low 30d % |
| --- | --- | --- | --- | --- |
| A | Conservative | 10.45 | 13.89 | 24.24 |
| A | Balanced | 13.89 | 24.24 | 36.36 |
| A | Intermediate | 13.89 | 24.24 | 44.44 |
| A | V1-A | 13.89 | 36.36 | 58.33 |
| A | V1-B | 24.24 | 44.44 | 68.57 |
| A | V1-C | 24.24 | 58.33 | 88.89 |
| B | Conservative | 10.42 | 11.43 | 15.09 |
| B | Balanced | 11.43 | 15.09 | 21.35 |
| B | Intermediate | 11.43 | 15.09 | 23.08 |
| B | V1-A | 11.43 | 21.35 | 35.00 |
| B | V1-B | 15.09 | 23.08 | 38.30 |
| B | V1-C | 15.09 | 35.00 | 46.15 |

The same controlled pattern was used for all candidates, so the comparison reflects the tested configuration rather than differences in attack scheduling. These are not finalized injected scenarios.

Additional notebook analyses examined rolling 7- and 14-day behavior, channel distribution, dominant-channel changes, cumulative injection bounds, and P95 exposure over compatible structural windows.

### 3.6 — Why Formula A Was Selected

With the **Balanced multipliers held constant**:

- A + Balanced daily strict separation: **91.01%**.
- B + Balanced daily strict separation: **38.12%**.
- A + Balanced separation at N=1: **81.38%**.
- A + Balanced cumulative non-overlap: **85.61%**.
- B + Balanced cumulative non-overlap: **72.27%**.

Formula A was preferred because its historical P95 reference preserved stronger differentiation among stealth levels, especially when natural daily activity was low.

Formula B was less effective at separating the three levels under N=1 because its minimum-count and rounding behavior often produces identical added-event counts.

This is a rule-selection rationale, **not proof that Formula A improves MUBSIR model accuracy**.

### 3.7 — Why the Balanced Multipliers Were Selected

Formula A was held constant when comparing multiplier configurations.

- A + Conservative strict separation: **41.66%**; cumulative non-overlap: **56.94%**.
- A + Balanced strict separation: **91.01%**; cumulative non-overlap: **85.61%**.
- A + Intermediate strict separation: **92.11%**; cumulative non-overlap: **94.35%**.
- A + V1-C strict separation: **98.16%**, but with higher-impact multipliers.

The Conservative configuration yielded weaker level separation.

More aggressive configurations sometimes achieved higher separation but also produced greater added-event counts and stronger P95 exposure. In particular, under Formula A, Intermediate raised Low Stealth's new-P95 exposure to **96.34%**, versus **74.45%** for Balanced.

**Balanced (0.25, 0.50, 0.75)** was selected as a compromise: strong differentiation, measurable behavioral impact, and avoidance of the highest injection levels. It was not the maximum-scoring configuration on every individual metric.

### 3.8 — Structural Window and Cumulative Feasibility

- Reused **288,486** passing structural windows for **936** users from Notebook 05.
- Reconciled compatible windows with actual User–Day timelines and natural channel activity.
- Evaluated candidate cumulative injection-count bounds and level separation.
- Examined cumulative P95 exposure and temporal impacts.
- No attack schedules were finalized and no injection was executed.

This notebook does not replace the switching, Off-Day, or duration eligibility rules approved in Notebook 05.

### 3.9 — Selected Rule Across All Channels

**Final configuration: Formula A + Balanced**

- High Stealth: **0.25**
- Medium Stealth: **0.50**
- Low Stealth: **0.75**

`I = max(1, ceil(m × historical_P95))`

The **same formula and multipliers** apply to EMAIL, USB, and HTTP. The resulting number of added events can differ by user and channel because their historical P95 values differ.

#### Verified Channel-Level Results

| Channel | Observations | Users | Strict % | N=1 Strict % | New P95 High % | New P95 Medium % | New P95 Low % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EMAIL | 57815 | 936 | 89.96 | 79.28 | 15.14 | 32.54 | 67.06 |
| USB | 29612 | 690 | 92.07 | 83.72 | 15.79 | 42.00 | 81.72 |
| HTTP | 13158 | 533 | 93.22 | 87.60 | 18.57 | 50.78 | 90.58 |

Overall:
- Strict daily separation: **91.01%**.
- All three levels identical: **1.94%**.
- Newly introduced P95 exceedances at Low Stealth: EMAIL **67.06%**, USB **81.72%**, HTTP **90.58%**.

These high Low-Stealth exceedance rates, especially for USB and HTTP, are an explicit limitation of the selected configuration.

## 4. Validation

Completed checks include:

- Source discovery and schema/key verification.
- Historical baseline coverage and natural event-count reconciliation.
- Formula definition and multiplier consistency.
- Low-activity and MAD-related sensitivity checks.
- Daily stealth-level ordering and separation.
- Structural window timeline reconciliation.
- Cumulative injection bounds and level-separation checks.
- P95 exposure consistency.
- Controlled temporal and cross-channel evaluation.
- Selected-rule verification across all three channels.
- Reconciliation with previous analysis results.
- Exported file read-back verification.
- Final validation data dictionary coverage.

**Final rule validation: PASS.**

This validates the documented calculations and exported configuration, not the effectiveness of an unexecuted attack or model detection.

## 5. Final Deliverables

All stored under:
`New_Attack_Simulation/reports/06_Stealth_and_Injection_Count_Feasibility/`

- `selected_injection_rule.json` — selected formula and multiplier configuration.
- `selected_stealth_validation.csv` — validated results by channel and level.
- `selected_stealth_validation_dictionary.csv` — output column definitions.
- `final_stealth_validation_report.md` — detailed validation results.
- `notebook_summary.md` — complete final notebook summary.

Intermediate analytical tables remain notebook results unless explicitly exported elsewhere.

## 6. Limitations & Next Step

- Hypothetical evaluations only; no actual attack injection was performed.
- No final attacker selection or assignment was performed.
- No completed channel-rotation schedule was generated.
- Low Stealth can produce substantial newly introduced P95 exceedances.
- Strict separation is not guaranteed for every observation.
- Statistical P95 exposure does not establish model detection.
- Historical Baseline must remain immutable.
- Deployment or model performance is not evaluated in this notebook.

**Next: Notebook 07 — Scenario Catalog Design.**

Carry forward:
- Structural eligibility and switching rules from Notebook 05.
- The unified Formula A + Balanced rule from Notebook 06.
- Forced-only Off-Day constraints.
- A preference for feasible windows with the **fewest forced Off-Days** during final window selection, without changing eligibility rules.
- Later user assignment, dry-run, injection, ground-truth generation, and final QA.

## 7. Conclusion

Notebook 06 compared **two formulas and six multiplier configurations**, evaluated daily and cumulative impacts, tested low-activity behavior, reconciled compatible windows, and assessed cross-channel consistency.

**Formula A + Balanced (High=0.25, Medium=0.50, Low=0.75)** was selected for its strong stealth-level differentiation and comparatively restrained impact relative to the more aggressive alternatives.

The selected rule is documented, validated, and exported for subsequent simulation stages. Its limitations are explicitly recorded.
