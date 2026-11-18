# Notebook 09 — Pre-Injection Dry Run

## Purpose

Prepare and independently validate an attack-channel schedule
for the 400 approved attacker scenarios.

## Inputs

- Approved Notebook 08 scenario assignments
- Original processed user-day activity
- Validated daily channel availability
- Selected synchronization targets
- Independently validated daily channel schedules

## Approved Results

| Metric | Value |
|---|---:|
| Approved attackers | 400 |
| Window user-workdays | 10,750 |
| Active user-workdays | 9,080 |
| Forced off-days | 1,670 |
| Exactly-two-channel days | 970 |
| Three-channel days | 37 |
| Primary channel switches | 3,116 |
| Consolidated QA checks | 47/47 PASS |

## Methodology

1. Verify approved inputs and scenario assignments.
2. Reconstruct daily attack windows and natural availability.
3. Analyze natural synchronization opportunities.
4. Establish joint switching-synchronization feasibility.
5. Select duration-rule-based synchronization targets.
6. Reconstruct feasible daily Primary Channel sequences.
7. Independently validate schedules against original user-day
   counts and approved scenario constraints.
8. Export validated plans and integrity evidence.

## Synchronization Selection

The selected targets follow Table B.3 with approved
two-channel-only and zero-synchronization fallbacks.

Alternative jointly feasible configurations are selected
deterministically without always preferring the minimum.

## Switching

A switch occurs when the Primary Channel changes between
consecutive active days.

Forced off-days are excluded from switching transitions.

## Scope and Limitations

This notebook produces a planned attack schedule only.

It does not inject attack events, alter event counts,
modify original user-day data, or generate final injected
ground-truth labels.

The subsequent injection stage must independently validate
the planned actions against its generated event-count changes.

## Integrity

Every exported artifact is listed in export_manifest.json
with its SHA-256 checksum.

The manifest is not self-hashed.

Original source datasets and Notebook 08 outputs remain
unchanged.
