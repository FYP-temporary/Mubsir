# MUBSIR — 01_User_Population_Audit

## 1. Objective

User Population Audit

## 2. Data Scope

All 3,995 users; natural Future behavior and channel use.

## 3. Key Findings

- 3,737 users with eligible Future workdays.
- 2,742 naturally single-channel users.
- 704 naturally two-channel users.
- 291 naturally three-channel users.
- 995 preliminary multi-channel candidates.

## 4. Validation

- Status: Completed population/profile validation.
- Original source datasets remain unchanged.

## 5. Final Deliverables

- `01_channel_monthly_activity.parquet`
- `01_channel_temporal_profile.parquet`
- `user_population_profile.parquet`
- `user_population_profile_dictionary.csv`

## 6. Limitations & Next Step

- Results describe completed analyses only.
- Attack injection feasibility is not yet proven.
- Final attack assignment and injection remain pending.
- Historical Baseline must remain immutable.

## 7. Original Detailed Report

The original report is preserved below.

---

# MUBSIR — User Population Audit

## Population

- Baseline users: 3,995
- Users with eligible Future workdays: 3,737
- Users without eligible Future workdays: 258
- Eligible Future user-days: 387,162
- Consolidated profile columns: 101

## Observed Channel Sets

observed_channel_set
E                          2742
EU                          428
EUH                         291
EH                          276
NO_ELIGIBLE_FUTURE_DAYS     258

## Channel Overlap Patterns

channel_overlap_pattern
Single channel                             2742
Same-day two-channel overlap                746
Same-day three-channel overlap              239
Multiple channels on separate days only      10

## Historical Channel Baseline Availability

- EMAIL: 3,994 users
- USB: 783 users
- HTTP: 615 users

Flags require historical channel activity and valid precomputed
P50, P95, and MAD statistics. A MAD value of zero is allowed.

## Included Behavioral Features

- User and historical baseline reference
- Future workday coverage
- Channel activity days and rates
- Exact daily channel combinations
- Same-day channel overlaps
- Activity intensities and Email bytes
- Calendar-weekday streaks
- Eligible-workday and calendar-workday activity gaps
- Natural channel transitions
- Monthly temporal characteristics
- Historical per-channel baseline availability

## Interpretation Notes

- Days with zero target-channel activity may still have other activity.
- A missing gap or intensity statistic is not equivalent to zero.
- Calendar-weekday streaks and eligible-workday gaps use different
  definitions of continuity.
- Channel availability within a month does not prove that a specific
  attack sequence is feasible within a shorter window.
- June 2011 is a partial month in the dataset.

## Simulation Design Principles

- User-first, data-driven scenario selection.
- Derive feasible patterns from each user's available dates and channels.
- Do not impose predefined switching sequences.
- Preserve the original historical Baseline.
- Restrict behavioral analysis and injection to the Future period.
- Off-days mean days without attack injection.
- Final feasibility must be tested using daily data.

## Status

Population behavioral audit complete.
No attack scenario or user eligibility decision has been imposed.

