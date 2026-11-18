# MUBSIR — 03_Channel_Behavior_Audit

## 1. Objective

Channel Behavior Audit

## 2. Data Scope

995 multi-channel candidates; natural Future event counts.

## 3. Key Findings

- 103,395 eligible Future user-days.
- 2,281 naturally active user-channel pairs.
- 102,626 active Future channel-days.
- 3,733 natural channel-days exceeded historical P95.
- 51 multi-channel days had simultaneous P95 exceedances.
- Historical Baseline statistics were used without recalculation.

## 4. Validation

- Status: 12/12 PASS; 47/47 documented columns.
- Original source datasets remain unchanged.

## 5. Final Deliverables

- `candidate_behavior_profile.parquet`
- `channel_behavior_data_dictionary.csv`
- `user_channel_frequency_comparison.parquet`

## 6. Limitations & Next Step

- Results describe completed analyses only.
- Attack injection feasibility is not yet proven.
- Final attack assignment and injection remain pending.
- Historical Baseline must remain immutable.

## 7. Original Detailed Report

The original report is preserved below.

---

# MUBSIR — Notebook 03: Channel Behavior Audit

## Scope

- Candidates: 995 naturally multi-channel users.
- Future: 2011-01-03 to 2011-06-01.
- Historical Baseline: existing read-only frequency reference.
- Analysis: natural event counts only.
- No injection or scenario assignment.

## Population and Coverage

- Candidate users: 995.
- Active user-channel pairs: 2,281.
- Eligible Future user-days: 103,395.
- Active Future channel-days: 102,626.

## Natural Frequency Deviations

- Natural channel-days above historical P95: 3,733.
- Users with at least one natural P95 exceedance: 867.
- Users with a simultaneous multi-channel P95 exceedance: 49.
- Multi-channel days with simultaneous P95 exceedances: 51.
- Users with at least one zero-MAD historical channel: 748.

## Channel-Level Results

| Channel | Active users | Active days | Days above P95 |
|---|---:|---:|---:|
| EMAIL | 995 | 58,710 | 2,045 |
| USB | 719 | 30,018 | 1,157 |
| HTTP | 567 | 13,898 | 531 |

## Main Findings

1. All naturally active Future user-channel pairs have usable historical frequency references.
2. Natural Future activity can exceed historical P95 without any injected attack.
3. Simultaneous natural P95 exceedances across channels are much less frequent than individual exceedances.
4. Zero historical MAD is common and requires explicit handling in future feasibility analysis.
5. Average monthly event frequency can remain relatively similar while individual users vary.

## Methodological Boundaries

- Historical Baseline was not recalculated or modified.
- Original Future data was not modified.
- P95 exceedance is not an attack label.
- Natural frequency differences are not approved injection budgets.
- Final injection feasibility and stealth rules have not yet been established.

## Quality Assurance

- Numerical and logical validation: 12/12 PASS.
- Parquet files exported and read back successfully.
- Data dictionary: 47/47 columns documented.

## Final Deliverables

- `candidate_behavior_profile.parquet`
- `user_channel_frequency_comparison.parquet`
- `channel_behavior_data_dictionary.csv`
- `channel_behavior_summary.md`

