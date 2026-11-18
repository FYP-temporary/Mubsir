# Notebook 05 — Source-of-Truth & Final Validation

UTC: 2026-11-07T19:55:48.649447+00:00

**PASS — all implemented checks completed.**

- Source User-Day rows: 1,394,010
- Eligible Future User-Day rows: 387,437
- Future feature rows: 387,162
- Documented missing feature keys: 275
- Candidate User-Day / feature days: 103,395
- Candidate users: 995
- Window-level records: 472,667
- Compatible windows: 288,486
- Compatible users: 936
- Implemented validation assertions: 211

## Documented source discrepancy
{'CDE1846': 105, 'MBG3183': 105, 'CMP2946': 65}

## Scope caveats
- Source/feature alignment verified; exact switching re-evaluated independently from User-Day.
- User-Day is a processed source, not an independent raw event reconstruction.
- These checks do not verify stealth/payload, final schedules, or model outcomes.
- SHA-256 checksums establish current fingerprints, not proof that historical files were unchanged.

## Inventory
| File | Rows | Columns | SHA-256 |
|---|---:|---:|---|
| natural_window_switching_audit.parquet | 472,667 | 20 | `d58036cf021b6591ad45876f796cf20be5bafe8a406d7a80f62d9d3aea408ef2` |
| natural_window_switching_enriched.parquet | 472,667 | 30 | `60787619f988d31530fafeb8383fa8cd69465a4435525d947596dd72d66b9557` |
| switching_rule_integer_feasibility.parquet | 1,788 | 11 | `a4ea0e39692acc330748b48898826e7f60209137561fe8817b2a78a6e804f2e5` |
| switching_full_density_capacity_screen.parquet | 72 | 10 | `5583042bcf08549422a0451288cc1c4b7c3b4fc59299a518543e0ef748c81926` |
| switching_range_comparison.csv | 4 | 6 | `d2d5e913cfaff1bfb5770d5a537d97f0759d8eb23a082ec062e39e7e6e4c7c64` |
| same_day_multichannel_window_audit.parquet | 472,667 | 12 | `a1efc85c5e51d001bab8d008f9b6350dc6222b030da81ded65df845624a4870c` |
| same_day_multichannel_rule_comparison.csv | 30 | 6 | `707da3e2b52c573ec630204d45dea824f3dfe00e05434067f9c156ce9385f5df` |
| offday_window_capacity_audit.parquet | 472,667 | 19 | `e31ea5d0ad81c5a5b8868432df3791d7a238aa39f881444b760bf33f7fa4e5b8` |
| offday_v1_15_quota_comparison.csv | 15 | 7 | `9940418fca84ec80fae770476f8c2ec6314181358663892085778096afe8f544` |
| offday_v1_vs_v2_summary.csv | 6 | 8 | `7fa711db2f6b106e114e08fffaf909e42794e52a701aea404835fcbf3ed88168` |
| offday_forced_only_density_window_audit.parquet | 472,667 | 14 | `bbf834065c5c91f5b172b03bbc8d483b6036a72760524d4e990ad9459d19a4cf` |
| offday_forced_only_density_comparison.csv | 6 | 14 | `2a4635449e7d53e7cde272ee3410ff9580098fb9727da01e60ae67dd8f6b00fe` |
| integrated_structural_window_audit.parquet | 472,667 | 30 | `69ed23eb022caadc78ca3ee4a227a7261956d72b78d4c174fb7aa21beedd4151` |
| integrated_structural_summary.csv | 6 | 8 | `e730b437e4daaab140d23076fc660d1ed72f20b497c11233e0f63ca70b1ab96f` |
| integrated_switching_level_coverage.csv | 18 | 4 | `e46df1936549af2537f4ba43705c62329b0335a464e9f6558f1a529afd7c0094` |
| integrated_multichannel_options.csv | 6 | 6 | `5844df89367380d1bd3621d578c0df6b85e3f90e4579805955fb5956b8d8a4ae` |
| integrated_five_day_exception.csv | 3 | 5 | `162c3609238a51d2e2fc14a3855642c0716765e25541bd12ca27558722721ece` |

## Source SHA-256
- User-Day: `bd988e53112cd5a4b328eb6fde5ada78d2962d5b9303575e5917dc1a64724ef7`
- Features: `364e3b2fd38874b5589dca2d0224a3fb395a316df628a8c6ff741229ddfea05b`

## Validation checks
- PASS: Source exists: user_day_r62_v1.parquet
- PASS: Source exists: behavior_features_r62_v1.parquet
- PASS: Source exists: integrated_structural_window_audit.parquet
- PASS: Output available: natural_window_switching_audit.parquet
- PASS: Output schema/count: natural_window_switching_audit.parquet
- PASS: Output available: natural_window_switching_enriched.parquet
- PASS: Output schema/count: natural_window_switching_enriched.parquet
- PASS: Output available: switching_rule_integer_feasibility.parquet
- PASS: Output schema/count: switching_rule_integer_feasibility.parquet
- PASS: Output available: switching_full_density_capacity_screen.parquet
- PASS: Output schema/count: switching_full_density_capacity_screen.parquet
- PASS: Output available: switching_range_comparison.csv
- PASS: Output schema/count: switching_range_comparison.csv
- PASS: Output available: same_day_multichannel_window_audit.parquet
- PASS: Output schema/count: same_day_multichannel_window_audit.parquet
- PASS: Output available: same_day_multichannel_rule_comparison.csv
- PASS: Output schema/count: same_day_multichannel_rule_comparison.csv
- PASS: Output available: offday_window_capacity_audit.parquet
- PASS: Output schema/count: offday_window_capacity_audit.parquet
- PASS: Output available: offday_v1_15_quota_comparison.csv
- PASS: Output schema/count: offday_v1_15_quota_comparison.csv
- PASS: Output available: offday_v1_vs_v2_summary.csv
- PASS: Output schema/count: offday_v1_vs_v2_summary.csv
- PASS: Output available: offday_forced_only_density_window_audit.parquet
- PASS: Output schema/count: offday_forced_only_density_window_audit.parquet
- PASS: Output available: offday_forced_only_density_comparison.csv
- PASS: Output schema/count: offday_forced_only_density_comparison.csv
- PASS: Output available: integrated_structural_window_audit.parquet
- PASS: Output schema/count: integrated_structural_window_audit.parquet
- PASS: Output available: integrated_structural_summary.csv
- PASS: Output schema/count: integrated_structural_summary.csv
- PASS: Output available: integrated_switching_level_coverage.csv
- PASS: Output schema/count: integrated_switching_level_coverage.csv
- PASS: Output available: integrated_multichannel_options.csv
- PASS: Output schema/count: integrated_multichannel_options.csv
- PASS: Output available: integrated_five_day_exception.csv
- PASS: Output schema/count: integrated_five_day_exception.csv
- PASS: No unclassified outputs: []
- PASS: Expected source and feature populations
- PASS: Nonmissing keys: ['user', 'day']
- PASS: Unique keys: ['user', 'day']
- PASS: Nonmissing keys: ['user', 'day']
- PASS: Unique keys: ['user', 'day']
- PASS: Valid primary weekend flags
- PASS: Primary logon counts present
- PASS: Primary weekend flags match calendar
- PASS: Eligible Future User-Day rows = 387,437
- PASS: Feature days all eligible Future workdays
- PASS: Nonmissing keys: ['user', 'day']
- PASS: Unique keys: ['user', 'day']
- PASS: No feature keys outside primary eligible Future
- PASS: Exactly 275 previously documented missing feature rows
- PASS: Every feature day found in User-Day
- PASS: Exact primary-feature equality: is_weekend
- PASS: Exact primary-feature equality: logon_count
- PASS: Exact primary-feature equality: external_email_count
- PASS: Exact primary-feature equality: usb_copy_count
- PASS: Exact primary-feature equality: www_upload_count
- PASS: Integrated scope: 995 users and 472,667 windows
- PASS: Nonmissing keys: ['user', 'window_workdays', 'window_start']
- PASS: Unique keys: ['user', 'window_workdays', 'window_start']
- PASS: Candidate primary/feature scope: 103,395 days
- PASS: Nonmissing keys: ['user', 'day']
- PASS: Unique keys: ['user', 'day']
- PASS: Nonmissing keys: ['user', 'day']
- PASS: Unique keys: ['user', 'day']
- PASS: No source-to-feature key gaps for 995 candidates
- PASS: Nonmissing keys: ['user', 'window_workdays', 'window_start']
- PASS: Unique keys: ['user', 'window_workdays', 'window_start']
- PASS: Exact window population: natural_window_switching_audit.parquet
- PASS: Nonmissing keys: ['user', 'window_workdays', 'window_start']
- PASS: Unique keys: ['user', 'window_workdays', 'window_start']
- PASS: Exact window population: natural_window_switching_enriched.parquet
- PASS: Nonmissing keys: ['user', 'window_workdays', 'window_start']
- PASS: Unique keys: ['user', 'window_workdays', 'window_start']
- PASS: Exact window population: offday_window_capacity_audit.parquet
- PASS: Nonmissing keys: ['user', 'window_workdays', 'window_start']
- PASS: Unique keys: ['user', 'window_workdays', 'window_start']
- PASS: Exact window population: offday_forced_only_density_window_audit.parquet
- PASS: All 472,667 window boundaries and daily counts independently reconciled
- PASS: 30 independent brute-force window checks
- PASS: Exact DP bitmasks independently rebuilt from primary User-Day (ALL windows)
- PASS: DP rotation matches saved support flags
- PASS: Bitmask option counts
- PASS: Bitmask minimum switch counts
- PASS: Bitmask maximum switch counts
- PASS: Window duration reconciles against forced Off-Days
- PASS: Approved Off-Day limits
- PASS: Off-Day pass flags
- PASS: Injection density holds for qualifying windows
- PASS: Exact Low switching
- PASS: Exact Medium switching
- PASS: Exact High switching
- PASS: Any exact switching level
- PASS: Joint structural pass
- PASS: Compatible-level count
- PASS: Optional two-plus flag
- PASS: Optional three-channel flag
- PASS: Integrated exclusion reason per window
- PASS: Expected 288,486 windows / 936 users
- PASS: Unique integrated summary D=5
- PASS: Integrated summary 5/All_windows
- PASS: Integrated summary 5/Rotation_windows
- PASS: Integrated summary 5/OffDay_pass_windows
- PASS: Integrated summary 5/Exact_compatible_windows
- PASS: Integrated summary 5/OffDay_pass_but_no_level
- PASS: Integrated summary 5/Compatible_users
- PASS: Integrated percentage D=5
- PASS: Level summary 5/Low
- PASS: Level summary 5/Medium
- PASS: Level summary 5/High
- PASS: Unique Multichannel summary D=5
- PASS: Multichannel summary D=5/Compatible_windows
- PASS: Multichannel summary D=5/With_2plus_channel_option
- PASS: Multichannel summary D=5/With_3channel_option
- PASS: Multichannel summary D=5/Users_with_2plus_option
- PASS: Multichannel summary D=5/Users_with_3channel_option
- PASS: Off-Day summary D=5
- PASS: Unique integrated summary D=10
- PASS: Integrated summary 10/All_windows
- PASS: Integrated summary 10/Rotation_windows
- PASS: Integrated summary 10/OffDay_pass_windows
- PASS: Integrated summary 10/Exact_compatible_windows
- PASS: Integrated summary 10/OffDay_pass_but_no_level
- PASS: Integrated summary 10/Compatible_users
- PASS: Integrated percentage D=10
- PASS: Level summary 10/Low
- PASS: Level summary 10/Medium
- PASS: Level summary 10/High
- PASS: Unique Multichannel summary D=10
- PASS: Multichannel summary D=10/Compatible_windows
- PASS: Multichannel summary D=10/With_2plus_channel_option
- PASS: Multichannel summary D=10/With_3channel_option
- PASS: Multichannel summary D=10/Users_with_2plus_option
- PASS: Multichannel summary D=10/Users_with_3channel_option
- PASS: Off-Day summary D=10
- PASS: Unique integrated summary D=20
- PASS: Integrated summary 20/All_windows
- PASS: Integrated summary 20/Rotation_windows
- PASS: Integrated summary 20/OffDay_pass_windows
- PASS: Integrated summary 20/Exact_compatible_windows
- PASS: Integrated summary 20/OffDay_pass_but_no_level
- PASS: Integrated summary 20/Compatible_users
- PASS: Integrated percentage D=20
- PASS: Level summary 20/Low
- PASS: Level summary 20/Medium
- PASS: Level summary 20/High
- PASS: Unique Multichannel summary D=20
- PASS: Multichannel summary D=20/Compatible_windows
- PASS: Multichannel summary D=20/With_2plus_channel_option
- PASS: Multichannel summary D=20/With_3channel_option
- PASS: Multichannel summary D=20/Users_with_2plus_option
- PASS: Multichannel summary D=20/Users_with_3channel_option
- PASS: Off-Day summary D=20
- PASS: Unique integrated summary D=30
- PASS: Integrated summary 30/All_windows
- PASS: Integrated summary 30/Rotation_windows
- PASS: Integrated summary 30/OffDay_pass_windows
- PASS: Integrated summary 30/Exact_compatible_windows
- PASS: Integrated summary 30/OffDay_pass_but_no_level
- PASS: Integrated summary 30/Compatible_users
- PASS: Integrated percentage D=30
- PASS: Level summary 30/Low
- PASS: Level summary 30/Medium
- PASS: Level summary 30/High
- PASS: Unique Multichannel summary D=30
- PASS: Multichannel summary D=30/Compatible_windows
- PASS: Multichannel summary D=30/With_2plus_channel_option
- PASS: Multichannel summary D=30/With_3channel_option
- PASS: Multichannel summary D=30/Users_with_2plus_option
- PASS: Multichannel summary D=30/Users_with_3channel_option
- PASS: Off-Day summary D=30
- PASS: Unique integrated summary D=40
- PASS: Integrated summary 40/All_windows
- PASS: Integrated summary 40/Rotation_windows
- PASS: Integrated summary 40/OffDay_pass_windows
- PASS: Integrated summary 40/Exact_compatible_windows
- PASS: Integrated summary 40/OffDay_pass_but_no_level
- PASS: Integrated summary 40/Compatible_users
- PASS: Integrated percentage D=40
- PASS: Level summary 40/Low
- PASS: Level summary 40/Medium
- PASS: Level summary 40/High
- PASS: Unique Multichannel summary D=40
- PASS: Multichannel summary D=40/Compatible_windows
- PASS: Multichannel summary D=40/With_2plus_channel_option
- PASS: Multichannel summary D=40/With_3channel_option
- PASS: Multichannel summary D=40/Users_with_2plus_option
- PASS: Multichannel summary D=40/Users_with_3channel_option
- PASS: Off-Day summary D=40
- PASS: Unique integrated summary D=50
- PASS: Integrated summary 50/All_windows
- PASS: Integrated summary 50/Rotation_windows
- PASS: Integrated summary 50/OffDay_pass_windows
- PASS: Integrated summary 50/Exact_compatible_windows
- PASS: Integrated summary 50/OffDay_pass_but_no_level
- PASS: Integrated summary 50/Compatible_users
- PASS: Integrated percentage D=50
- PASS: Level summary 50/Low
- PASS: Level summary 50/Medium
- PASS: Level summary 50/High
- PASS: Unique Multichannel summary D=50
- PASS: Multichannel summary D=50/Compatible_windows
- PASS: Multichannel summary D=50/With_2plus_channel_option
- PASS: Multichannel summary D=50/With_3channel_option
- PASS: Multichannel summary D=50/Users_with_2plus_option
- PASS: Multichannel summary D=50/Users_with_3channel_option
- PASS: Off-Day summary D=50
- PASS: Five-day Low exception summary
- PASS: Five-day Medium exception summary
- PASS: Five-day High exception summary
