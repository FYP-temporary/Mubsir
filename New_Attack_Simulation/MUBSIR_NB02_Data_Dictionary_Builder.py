"""MUBSIR Notebook 02 | Build a fully documented 168-column Data Dictionary.

Run from an already initialized Notebook 02 environment (PROJECT_ROOT must exist).
Reads ONLY the two audited Parquet output files. Writes one dictionary CSV.
"""
from pathlib import Path
import pandas as pd
import numpy as np

if "PROJECT_ROOT" not in globals():
    raise NameError("PROJECT_ROOT must exist in the active Notebook 02 kernel.")

_REPORT = Path(PROJECT_ROOT) / "reports" / "02_Temporal_Window_Audit"
_F1 = "user_window_length_audit.parquet"
_F2 = "rotation_feasibility_audit.parquet"
_FILES = {_F1: _REPORT / _F1, _F2: _REPORT / _F2}
for _name, _path in _FILES.items():
    if not _path.is_file():
        raise FileNotFoundError(f"Missing validated export: {_path}")

_DICTIONARY = {}

def add(file, column, category, description, calculation, source,
        unit="count", valid_values="Nonnegative integer", missing_meaning="None expected",
        interpretation="Descriptive observed behavior; not approved attack injection"):
    key = (file, column)
    if key in _DICTIONARY:
        raise AssertionError(f"Duplicate documentation: {key}")
    _DICTIONARY[key] = dict(category=category, description=description,
                            calculation=calculation, source=source, unit=unit,
                            valid_values=valid_values,
                            missing_meaning=missing_meaning,
                            interpretation=interpretation)

def a(column, category, description, calculation, source, **kwargs):
    add(_F1, column, category, description, calculation, source, **kwargs)

def b(column, category, description, calculation, source, **kwargs):
    add(_F2, column, category, description, calculation, source, **kwargs)

_COMMON = {
    "user": ("Keys", "Unique identifier of a CERT r6.2 user.", "Copied from the source Future user-day key.", "future_daily / behavior_features_r62_v1.parquet", "identifier", "Nonempty user ID"),
    "window_workdays": ("Keys", "Length of a sliding candidate window, counted in eligible Future workdays (not calendar days).", "Number of ordered eligible user-days included in each sliding window.", "future_daily: eligible user-day order", "eligible workdays", "Positive integer"),
}
for _file in (_F1, _F2):
    for _col, (_cat, _desc, _calc, _src, _unit, _valid) in _COMMON.items():
        add(_file, _col, _cat, _desc, _calc, _src, unit=_unit, valid_values=_valid,
            interpretation="Grouping key; does not identify an approved attack schedule")

# ======================================================================
# OUTPUT 1: ALL FUTURE USERS × SUPPORTED WINDOW LENGTHS
# ======================================================================
a("eligible_windows", "Window availability", "Number of overlapping candidate sliding-window placements of this eligible-workday length for the user.",
  "n_eligible_user_days - window_workdays + 1, only when window_workdays <= n_eligible_user_days.", "window_length_capacity")
a("calendar_contiguous_windows", "Calendar continuity", "Candidate windows with no missing weekday between the first and last eligible user-day.",
  "Count candidate windows whose included user-days span exactly window_workdays successive calendar weekdays.", "window_length_capacity")
a("cross_gap_windows", "Calendar continuity", "Candidate windows crossing at least one weekday absent from the user's eligible-day records.",
  "eligible_windows - calendar_contiguous_windows.", "window_length_capacity")
a("has_calendar_contiguous_option", "Calendar continuity", "Whether at least one calendar-weekday-contiguous placement is available at this window length.",
  "calendar_contiguous_windows > 0.", "window_length_capacity", unit="boolean", valid_values="True / False")

_STATE_LABELS = {"NONE": "none of Email, USB or HTTP", "E": "Email only", "U": "USB only", "H": "HTTP only",
                 "EU": "Email and USB only", "EH": "Email and HTTP only", "UH": "USB and HTTP only",
                 "EUH": "Email, USB and HTTP"}
for _state, _meaning in _STATE_LABELS.items():
    a(f"windows_{_state}", "Observed channel combinations",
      f"Count of sliding windows whose union of naturally observed active exfiltration channels is exactly {_meaning}.",
      "For each placement, take the union of channels active on one or more eligible days; count this exact union.",
      "channel_window_capacity; future_daily channel-active flags")
for _col, _count, _meaning in [
    ("windows_one_observed_channel", ["E", "U", "H"], "exactly one"),
    ("windows_two_observed_channels", ["EU", "EH", "UH"], "exactly two"),
    ("windows_three_observed_channels", ["EUH"], "all three"),
    ("windows_2plus_observed_channels", ["EU", "EH", "UH", "EUH"], "at least two"),
    ("windows_any_observed_channel", ["E", "U", "H", "EU", "EH", "UH", "EUH"], "one or more"),
]:
    a(_col, "Observed channel combinations", f"Count of sliding windows with {_meaning} distinct naturally active channels anywhere inside the window.",
      " + ".join(f"windows_{x}" for x in _count), "channel_window_capacity")

for _col, _desc, _calc in [
    ("observed_2plus_windows", "Windows containing at least two distinct observed channels anywhere, regardless of whether they occur on distinct days.", "Equal to windows_2plus_observed_channels."),
    ("distinct_day_2plus_windows", "Windows allowing at least two different observed channels to be assigned to two distinct eligible days.", "Count placements satisfying a two-channel distinct-day matching of observed channel-day flags."),
    ("same_day_only_2plus_windows", "Windows with multiple observed channels that cannot be assigned to two separate eligible days.", "observed_2plus_windows - distinct_day_2plus_windows."),
    ("observed_three_windows", "Windows containing all three observed channel types somewhere, before testing distinct-day assignment.", "Equal to windows_EUH."),
    ("distinct_day_three_windows", "Windows permitting E, U and H to be assigned to three mutually distinct eligible dates.", "Count windows with a size-three matching between E/U/H and naturally active eligible days (Hall condition)."),
    ("three_without_assignment_windows", "Three-channel-observed windows without a valid three-distinct-day assignment.", "observed_three_windows - distinct_day_three_windows."),
    ("three_pair_constraint_fail_windows", "Windows whose three-channel distinct-day matching fails because a pair of channels cannot use two different eligible dates despite otherwise sufficient active days.",
     "Count size-three assignment failures caused by a violated two-channel Hall subset condition.")
]:
    a(_col, "Distinct-day assignment", _desc, _calc, "distinct_day_window_capacity")

_PAIRS = ["E_U", "E_H", "U_E", "U_H", "H_E", "H_U"]
_TRIPLES = ["E_U_E", "E_U_H", "E_H_E", "E_H_U", "U_E_U", "U_E_H",
            "U_H_E", "U_H_U", "H_E_U", "H_E_H", "H_U_E", "H_U_H"]
for _pattern in _PAIRS + _TRIPLES:
    _label = " → ".join(_pattern.split("_"))
    a(f"ordered_{_pattern}", "Flexible ordered motifs",
      f"Number of candidate windows supporting the chronological natural-channel subsequence {_label} on distinct eligible days.",
      "Count placements with an ordered matching of the motif to distinct days; intervening days are allowed and a matched day may have other active channels.",
      "ordered_window_capacity; observed user-day channel flags")

for _col, _desc, _calc in [
    ("windows_any_ordered_pair", "Windows supporting at least one two-step directed channel change on distinct eligible dates.", "Union over all six ordered two-channel motifs; count each window once."),
    ("windows_any_three_step_change", "Windows supporting at least one three-step sequence with adjacent selected channels different.", "Union over all twelve ordered three-step motifs; count each window once."),
    ("windows_three_distinct_order", "Windows supporting a three-step chronological sequence containing E, U and H each once.", "Union over six three-distinct-channel permutations; count each window once."),
    ("windows_return_pattern", "Windows supporting an A→B→A three-step sequence on three distinct eligible days.", "Union over six A→B→A return motifs; count each window once."),
    ("supported_pair_pattern_types", "Number of distinct two-step motif types observed in at least one candidate window at this length.", "Count of six ordered pair motifs whose respective window count is positive."),
    ("supported_three_step_pattern_types", "Number of distinct three-step motif types supported in at least one candidate window at this length.", "Count of twelve ordered triple motifs whose respective window count is positive."),
]:
    a(_col, "Flexible ordered motifs", _desc, _calc, "ordered_window_capacity",
      unit="pattern types" if "pattern_types" in _col else "windows",
      valid_values="Integer from 0 to 6" if _col == "supported_pair_pattern_types" else
                   "Integer from 0 to 12" if _col == "supported_three_step_pattern_types" else "Nonnegative integer")

for _pattern in _PAIRS + _TRIPLES:
    _label = " → ".join(_pattern.split("_"))
    a(f"exclusive_{_pattern}", "Exclusive-day ordered motifs",
      f"Number of candidate windows supporting {_label} on distinct days where each matched day has exactly its selected channel active among E/U/H.",
      "Count ordered motif matches using only natural eligible-day channel states E-only, U-only or H-only; unmatched days can have overlaps.",
      "exclusive_order_capacity; observed user-day channel flags",
      interpretation="Strict comparative diagnostic only; exclusive channel days are NOT mandatory for injection")
for _col, _desc, _calc in [
    ("exclusive_any_ordered_pair", "Windows with at least one exclusive-day ordered pair.", "Union over the six exclusive ordered pair patterns; count each window once."),
    ("exclusive_any_three_step_change", "Windows with at least one exclusive-day three-step change sequence.", "Union over twelve exclusive ordered three-step motifs; count each window once."),
    ("exclusive_three_distinct_order", "Windows with E, U and H on three separate exclusively active channel-days in chronological order.", "Union over six exclusive three-distinct-channel permutations; count each window once."),
    ("exclusive_return_pattern", "Windows supporting an exclusive-day A→B→A sequence.", "Union over six exclusive ordered return motifs; count each window once."),
]:
    a(_col, "Exclusive-day ordered motifs", _desc, _calc, "exclusive_order_capacity",
      interpretation="Strict comparative diagnostic only; exclusive channel days are NOT mandatory for injection")

_PCT_BASE = ["windows_any_ordered_pair", "windows_any_three_step_change", "windows_three_distinct_order",
             "windows_return_pattern", "exclusive_any_ordered_pair", "exclusive_any_three_step_change",
             "exclusive_three_distinct_order", "exclusive_return_pattern"]
for _col in _PCT_BASE:
    a(f"{_col}_pct", "Window support percentages", f"Percentage of this user's candidate windows of the given length supporting {_col}.",
      f"100 × {_col} / eligible_windows (0–100 percentage points).", "window_support_strength",
      unit="percent", valid_values="Float from 0 through 100 inclusive",
      interpretation="Denominator includes ALL windows for this user-length, not only qualifying windows")
a("pair_pattern_type_count", "Pattern diversity", "Number of two-step ordered motif types supported by this user at this length.",
  "Derived from the number of ordered pair motif columns with count > 0; corresponds to supported_pair_pattern_types.",
  "window_support_strength", unit="pattern types", valid_values="Integer 0–6")
a("three_step_pattern_type_count", "Pattern diversity", "Number of three-step ordered motif types supported by this user at this length.",
  "Derived from the number of ordered triple motif columns with count > 0; corresponds to supported_three_step_pattern_types.",
  "window_support_strength", unit="pattern types", valid_values="Integer 0–12")

for _col, _desc, _calc in [
    ("windows_2plus_observed", "Number of candidate windows in which at least two channels naturally appear somewhere.", "Equivalent to windows_2plus_observed_channels."),
    ("windows_3_observed", "Number of candidate windows in which all three channels naturally appear somewhere.", "Equivalent to windows_EUH."),
    ("windows_2plus_channels_each_2days", "Windows containing at least two distinct channels, each naturally active on at least two eligible days within the window.", "For each placement count channels with active-day occurrence count ≥2; accept if ≥2 channels."),
    ("windows_3_channels_each_2days", "Windows where all three channels are each naturally active on at least two eligible days.", "For each placement require E count≥2, U count≥2 and H count≥2."),
    ("windows_2plus_channels_each_3days", "Windows containing at least two distinct channels, each naturally active on at least three eligible days within the window.", "For each placement count channels with active-day occurrence count ≥3; accept if ≥2 channels."),
    ("windows_3_channels_each_3days", "Windows where all three channels are each naturally active on at least three eligible days.", "For each placement require E count≥3, U count≥3 and H count≥3."),
]:
    a(_col, "Channel recurrence", _desc, _calc, "channel_recurrence_capacity",
      interpretation="Overlapping natural channel-days may contribute to multiple channels; thresholds are descriptive, not imposed")
for _channel, _label in [("email", "Email"), ("usb", "USB"), ("http", "HTTP")]:
    a(f"{_channel}_active_day_occurrences", "Channel recurrence",
      f"Sum of {_label}-active eligible-day occurrences across all overlapping candidate windows for this user and length.",
      f"For every candidate placement count days with {_channel}_active==True, then sum these counts over placements; one actual day may be counted repeatedly.",
      "channel_recurrence_capacity; future_daily channel-active flags", unit="day-window occurrences",
      interpretation="NOT the number of unique active days; overlaps cause repeated counting")

_LONG_MISSING = "Not applicable for users who were not naturally multi-channel during eligible Future (null, not zero)"
for _col, _desc, _calc, _unit, _valid in [
    ("max_feasible_rotation_steps", "Longest valid alternating natural channel-day sequence in any candidate window of this length.",
     "Maximum across all placements of longest supported sequence; one naturally active channel per selected eligible day; adjacent selected channels differ.", "steps", "Integer-valued, from 0 to window_workdays"),
    ("max_feasible_switches", "Maximum possible count of switches in that longest user-length sequence.",
     "max(max_feasible_rotation_steps - 1, 0).", "switches", "Nonnegative integer-valued"),
    ("max_steps_using_3channels", "Maximum supported alternating sequence length that uses E, U and H at least once each.",
     "Across all placements maximize sequence length subject to all-three-channel usage; 0 when impossible.", "steps", "Integer-valued; 0 or at least 3"),
    ("mean_max_steps_across_windows", "Mean of each candidate placement's longest naturally supported alternating sequence.",
     "Arithmetic mean of per-placement maxima for the given user-length; rounded to 2 decimal places in the analysis.", "steps", "Nonnegative float"),
    ("example_window_end_position", "Zero-based position of the end eligible day of one window attaining the best sequence length.",
     "Chosen end index in the user's chronologically sorted eligible Future day sequence when a new maximum is found; example window start=end-position - window_workdays + 1.", "0-based index", "Nonnegative integer-valued"),
]:
    a(_col, "Long-rotation capacity", _desc, _calc, "long_rotation_capacity", unit=_unit,
      valid_values=_valid, missing_meaning=_LONG_MISSING,
      interpretation="Global user-length maximum, NOT a final injection sequence; long metrics apply only to natural multi-channel users")
for _k in [2, 3, 4, 5, 6, 8, 10, 15, 20, 30]:
    a(f"windows_supporting_{_k}steps", "Long-rotation capacity",
      f"Number of candidate placements with an alternating natural-channel-day sequence of at least {_k} steps.",
      f"Count windows where per-placement maximum supported sequence length ≥ {_k}.",
      "long_rotation_capacity", missing_meaning=_LONG_MISSING,
      interpretation="Threshold is diagnostic; not the approved attack length or mandatory switch count")
    if _k >= 3:
        a(f"windows_3channel_{_k}steps", "Long-rotation capacity",
          f"Number of candidate placements with an alternating sequence of at least {_k} steps that includes all E, U and H.",
          f"Count windows where the per-placement maximum alternating sequence using all three channels ≥ {_k}.",
          "long_rotation_capacity", missing_meaning=_LONG_MISSING,
          interpretation="All three channels must appear at least once; their contributions need not be balanced")
a("is_multichannel_candidate", "Eligibility scope", "Whether this user naturally uses at least two of E, U and H during the eligible Future period.",
  "True for user-length keys present in long_rotation_capacity (a user observed using ≥2 channels naturally); otherwise False.",
  "user_profile / long_rotation_capacity", unit="boolean", valid_values="True / False",
  interpretation="Preliminary scope only: does not certify that injection volume/stealth constraints can be satisfied")

# ======================================================================
# OUTPUT 2: REPRESENTATIVE USER × LENGTH × GAP × SEQUENCE VARIANT
# ======================================================================
b("minimum_interstep_offdays", "Keys", "Minimum number of unselected eligible workdays required BETWEEN successive selected injection-step candidates.",
  "Exploratory gap setting g ∈ {0,1,2}; consecutive selected positions must differ by at least g+1.",
  "rotation_cadence_capacity / rotation_structure_detail", unit="eligible workdays", valid_values="0, 1, or 2",
  interpretation="Exploratory analytical gap; NOT an approved attack cadence")
b("sequence_variant", "Keys", "Type of reconstructed sequence in a representative Gap-0-optimized user-length window.",
  "maximum_rotation chooses the longest sequence; three_channel_alternative chooses a longest sequence that includes E, U and H at least once in the SAME representative window.",
  "rotation_structure_detail", unit="category", valid_values="maximum_rotation; three_channel_alternative",
  interpretation="Only a selected example, not an enumeration of all windows or all optimal paths")
for _col, _title in [("window_start", "first"), ("window_end", "last")]:
    b(_col, "Representative window", f"Actual calendar date of the {_title} eligible user-day in the reconstructed representative window.",
      "Extracted from the user's sorted eligible Future dates using the Gap-0 maximum-sequence representative window placement.",
      "rotation_structure_detail / future_daily", unit="date", valid_values="Datetime in Future period",
      interpretation="Dates bound a window of eligible workdays; calendar-day span may exceed window_workdays")

_PATH_SPECS = [
    ("rotation_steps", "Number of selected, distinct, naturally supported channel-day assignments in this reconstructed path.", "len(selected_sequence).", "steps", "Integer 1..window_workdays"),
    ("channel_switches", "Number of changes between adjacent selected channels in this alternating sequence.", "rotation_steps - 1.", "switches", "Nonnegative integer"),
    ("used_channel_count", "Number of distinct channels actually selected at least once in this reconstructed path.", "Count channels with a positive step count.", "channels", "Integer 1..3"),
    ("email_steps", "Number of steps assigned to naturally active Email days in this path.", "Count E symbols in sequence_pattern.", "steps", "Nonnegative integer"),
    ("usb_steps", "Number of steps assigned to naturally active USB days in this path.", "Count U symbols in sequence_pattern.", "steps", "Nonnegative integer"),
    ("http_steps", "Number of steps assigned to naturally active HTTP days in this path.", "Count H symbols in sequence_pattern.", "steps", "Nonnegative integer"),
]
for _col, _desc, _calc, _unit, _valid in _PATH_SPECS:
    b(_col, "Reconstructed sequence", _desc, _calc, "rotation_structure_detail", unit=_unit, valid_values=_valid,
      interpretation="This is a representative feasible path; NOT an injected attack")
for _ch, _label in [("email", "Email"), ("usb", "USB"), ("http", "HTTP")]:
    b(f"observed_{_ch}_active_days", "Representative window", f"Number of eligible workdays inside the representative window where {_label} was naturally active, whether or not selected for the path.",
      f"Sum of the {_ch}_active flag across all eligible days in the chosen representative window.",
      "rotation_structure_detail / future_daily", unit="eligible days", valid_values="Integer 0..window_workdays",
      interpretation="Natural activity availability, not count of attack steps")

for _col, _desc, _calc, _unit, _valid in [
    ("dominant_channel_share", "Fraction of path steps assigned to the most frequent selected channel.", "max(email_steps, usb_steps, http_steps) / rotation_steps.", "proportion", "Float in (0,1]"),
    ("least_used_channel_steps", "Smallest count of steps among channels that appear at least once in this path.", "min of strictly positive email_steps, usb_steps, http_steps.", "steps", "Positive integer"),
    ("one_step_channel_present", "Whether any channel used by this path is selected exactly once.", "True if any strictly positive channel step count equals one.", "boolean", "True / False"),
    ("distinct_transition_types", "Number of different directed channel-switch types used by the reconstructed sequence.", "Count positive values across transitions_E_U, E_H, U_E, U_H, H_E, H_U.", "directed pair types", "Integer 0..6"),
    ("total_unselected_days", "Count of eligible workdays in the representative window not selected for attack-step candidates.", "window_workdays - rotation_steps.", "eligible days", "Nonnegative integer"),
    ("leading_unselected_days", "Unselected eligible days before the first chosen step in the representative window.", "First selected 0-based day position.", "eligible days", "Nonnegative integer"),
    ("internal_unselected_days", "Unselected eligible days strictly between consecutive selected steps.", "Sum over consecutive selected positions of (next_position - previous_position - 1).", "eligible days", "Nonnegative integer"),
    ("trailing_unselected_days", "Unselected eligible days after the last chosen step in the representative window.", "window_workdays - 1 - last selected 0-based position.", "eligible days", "Nonnegative integer"),
    ("median_internal_gap", "Median unselected eligible workdays between consecutive chosen steps (0 if just one step).", "Median of (successive selected positions difference minus one); default 0 when no pair exists.", "eligible days", "Nonnegative float"),
    ("longest_internal_gap", "Largest count of unselected eligible days between successive chosen steps (0 for a single step).", "Max of (successive selected positions difference minus one); default 0 when no pair exists.", "eligible days", "Nonnegative integer"),
    ("zero_gap_transitions", "Number of consecutive selected-step pairs separated by zero unselected eligible workdays.", "Count internal gap values equal to zero.", "transition pairs", "Nonnegative integer"),
    ("one_day_gap_transitions", "Number of consecutive selected-step pairs separated by exactly one unselected eligible workday.", "Count internal gap values equal to one.", "transition pairs", "Nonnegative integer"),
    ("two_plus_day_gap_transitions", "Number of consecutive selected-step pairs separated by two or more unselected eligible workdays.", "Count internal gap values greater than or equal to two.", "transition pairs", "Nonnegative integer"),
    ("global_best_steps", "Global maximum steps among ALL placements for this user, length, gap, and the relevant sequence variant.", "For maximum_rotation take maximum_rotation_steps; for three_channel_alternative take maximum_3channel_steps.", "steps", "Nonnegative integer"),
    ("matches_global_best", "Whether this reconstructed sequence reaches the global best for its variant across all candidate placements.", "rotation_steps == global_best_steps.", "boolean", "True / False"),
    ("sequence_pattern", "Concatenated E/U/H symbols for the path's selected channels in chronological order.", "Join selected channel labels in order; one character per selected eligible-day step.", "ordered channel string", "Nonempty string composed of E, U, H"),
    ("selected_day_positions", "Comma-separated 0-based eligible-day positions of selected steps within the representative window.", "Join chronologically ordered eligible-day indices (0 through window_workdays-1) separated by commas.", "0-based indices", "Comma-separated increasing nonnegative integers"),
]:
    b(_col, "Reconstructed sequence diagnostics", _desc, _calc, "rotation_structure_detail",
      unit=_unit, valid_values=_valid,
      interpretation=("0-based eligible-workday positions are NOT calendar-day offsets; recover exact dates from the user's eligible daily records" if _col=="selected_day_positions" else
                      "Global best may be larger than this representative-window path for Gap 1/2" if _col in ("global_best_steps", "matches_global_best") else
                      "Descriptive reconstruction only; not an approved injection schedule"))
for _left in "EUH":
    for _right in "EUH":
        if _left == _right:
            continue
        b(f"transitions_{_left}_{_right}", "Directed channel transitions",
          f"Number of {_left}→{_right} transitions between adjacent SELECTED path steps.",
          f"Count adjacent positions in sequence_pattern equal to {_left}{_right}.",
          "rotation_structure_detail", unit="switches", valid_values="Nonnegative integer",
          interpretation="Counts transitions between selected steps, which may be separated by unselected workdays")

_CADENCE_SPECS = [
    ("eligible_windows", "Number of candidate sliding windows for the given user and eligible-workday duration.", "n_user_eligible_days - window_workdays + 1.", "windows", "Positive integer"),
    ("maximum_rotation_steps", "Global best alternating sequence step count among ALL candidate windows for this user, duration and gap.", "max over placements of DP maximum respecting the specified minimum inter-step gap.", "steps", "Integer 1..window_workdays"),
    ("maximum_switches", "Maximum attainable number of changes between consecutive selected channels for the gap setting.", "max(maximum_rotation_steps - 1, 0).", "switches", "Nonnegative integer"),
    ("maximum_3channel_steps", "Global longest alternating sequence length using all three channels, subject to the specified gap.", "Max across all windows of longest matching sequence whose used-channel mask is E|U|H; 0 if impossible.", "steps", "0 or ≥3"),
    ("median_window_max_steps", "Median across all candidate windows of the maximum alternating sequence steps available in each window at this gap.", "Median of per-window DP maxima (not global best).", "steps", "Nonnegative float"),
    ("median_unselected_days_at_window_max", "Median across windows of unselected eligible days remaining if each window uses its own maximum supported steps.", "Median(window_workdays - per-window max steps).", "eligible days", "Nonnegative float"),
    ("unselected_days_at_user_best", "Number of unselected days if the global best number of steps is chosen in its best available window.", "window_workdays - maximum_rotation_steps.", "eligible days", "Nonnegative integer"),
]
for _col, _desc, _calc, _unit, _valid in _CADENCE_SPECS:
    b(_col, "Global cadence capacity", _desc, _calc, "rotation_cadence_capacity", unit=_unit,
      valid_values=_valid,
      interpretation="Global per-user-length-gap summary repeated across each available sequence variant; not necessarily attained in its representative window")
for _k in [2, 5, 10, 15]:
    b(f"windows_with_{_k}plus_steps", "Global cadence window thresholds",
      f"Number of sliding windows permitting at least {_k} alternating selected steps under this minimum inter-step gap.",
      f"Sum across windows of indicator(per-window maximum_rotation_steps ≥ {_k}).",
      "rotation_cadence_capacity", unit="windows",
      interpretation="Count of qualifying window placements; overlapping windows are not independent attack instances")
b("windows_with_3channel_rotation", "Global cadence window thresholds",
  "Number of candidate windows with a supported alternating sequence using all three channels at least once under this gap.",
  "Count placements with per-window maximum_3channel_steps ≥ 3.", "rotation_cadence_capacity", unit="windows")
for _k in [5, 10]:
    b(f"windows_with_3channel_{_k}plus_steps", "Global cadence window thresholds",
      f"Number of candidate windows supporting an all-three-channel alternating sequence of at least {_k} steps under the gap.",
      f"Count placements where per-window maximum_3channel_steps ≥ {_k}.",
      "rotation_cadence_capacity", unit="windows")

# ======================================================================
# VERIFY THAT DEFINITIONS COVER EACH PHYSICAL COLUMN EXACTLY ONCE
# ======================================================================
_expected_counts = {_F1: 116, _F2: 52}
_expected_rows = {_F1: 387162, _F2: 22296}
_observed_keys = []
_frames = {}
for _name, _path in _FILES.items():
    _df = pd.read_parquet(_path)
    _frames[_name] = _df
    if len(_df) != _expected_rows[_name]:
        raise AssertionError(f"Unexpected row count for {_name}: {len(_df)}")
    if len(_df.columns) != _expected_counts[_name] or not _df.columns.is_unique:
        raise AssertionError(f"Unexpected schema for {_name}")
    _observed_keys.extend((_name, _col) for _col in _df.columns)
_missing = sorted(set(_observed_keys) - set(_DICTIONARY))
_extra = sorted(set(_DICTIONARY) - set(_observed_keys))
if _missing or _extra:
    raise AssertionError(f"Data Dictionary coverage FAILED. Missing: {_missing} | Extra: {_extra}")
if len(_DICTIONARY) != 168:
    raise AssertionError(f"Expected 168 definitions; got {len(_DICTIONARY)}")

_long_colnames = [c for c in _frames[_F1].columns if c.startswith("windows_supporting_")
                 or c.startswith("windows_3channel_")]
_long_colnames += ["max_feasible_rotation_steps", "max_feasible_switches", "max_steps_using_3channels",
                   "mean_max_steps_across_windows", "example_window_end_position"]
_scope = _frames[_F1]["is_multichannel_candidate"].astype(bool)
if int(_scope.sum()) != 103395:
    raise AssertionError("Unexpected multichannel record count")
if _frames[_F1].loc[_scope, _long_colnames].isna().any().any():
    raise AssertionError("Candidate long rotation metrics are missing")
if not _frames[_F1].loc[~_scope, _long_colnames].isna().all().all():
    raise AssertionError("Noncandidate long rotation metrics should be N/A")
if _frames[_F2].isna().any().any():
    raise AssertionError("Unexpected nulls in rotation-feasibility output")

# ======================================================================
# PROFILE ACTUAL STORED VALUES AND WRITE SINGLE DICTIONARY FILE
# ======================================================================

def _pretty(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(pd.Timestamp(value))
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.8g}"
    if isinstance(value, (bool, np.bool_)):
        return "True" if value else "False"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)

_records = []
for _name, _df in _frames.items():
    _grain = ("user + window_workdays" if _name == _F1 else
              "user + window_workdays + minimum_interstep_offdays + sequence_variant")
    for _col in _df.columns:
        _spec = _DICTIONARY[(_name, _col)]
        _series = _df[_col]
        _non_null = _series.dropna()
        _null_count = int(_series.isna().sum())
        if _non_null.empty:
            _example = _minimum = _maximum = ""
        else:
            _example = _pretty(_non_null.iloc[0])
            if pd.api.types.is_numeric_dtype(_non_null) or pd.api.types.is_datetime64_any_dtype(_non_null):
                _minimum = _pretty(_non_null.min())
                _maximum = _pretty(_non_null.max())
            else:
                _minimum = _maximum = ""
        _records.append({
            "file": _name,
            "row_grain": _grain,
            "column": _col,
            "dtype": str(_series.dtype),
            "category": _spec["category"],
            "description": _spec["description"],
            "calculation": _spec["calculation"],
            "source": _spec["source"],
            "unit": _spec["unit"],
            "valid_values": _spec["valid_values"],
            "missing_meaning": _spec["missing_meaning"],
            "interpretation": _spec["interpretation"],
            "row_count": len(_df),
            "null_count": _null_count,
            "null_pct": round(100 * _null_count / len(_df), 4),
            "observed_min": _minimum,
            "observed_max": _maximum,
            "example_value": _example,
            "review_status": "DOCUMENTED"
        })

notebook02_data_dictionary = pd.DataFrame(_records)
assert len(notebook02_data_dictionary) == 168
assert not notebook02_data_dictionary.duplicated(["file", "column"]).any()
_required_documentation = ["description", "calculation", "source", "unit", "valid_values", "missing_meaning", "interpretation"]
assert notebook02_data_dictionary[_required_documentation].notna().all().all()
assert notebook02_data_dictionary[_required_documentation].apply(lambda s: s.str.strip().ne("").all()).all()
assert notebook02_data_dictionary["review_status"].eq("DOCUMENTED").all()

_OUTPUT = _REPORT / "notebook02_data_dictionary.csv"
notebook02_data_dictionary.to_csv(_OUTPUT, index=False, encoding="utf-8-sig")
_check = pd.read_csv(_OUTPUT, encoding="utf-8-sig", keep_default_na=False)
assert len(_check) == 168
assert _check[["file", "column"]].equals(notebook02_data_dictionary[["file", "column"]])
assert _check["review_status"].eq("DOCUMENTED").all()

print("=" * 78)
print("NOTEBOOK 02 — DATA DICTIONARY VALIDATION")
print("=" * 78)
for _name in (_F1, _F2):
    _part = notebook02_data_dictionary.loc[notebook02_data_dictionary["file"] == _name]
    print(f"PASS | {_name}: {len(_part)}/{_expected_counts[_name]} columns documented")
print(f"PASS | Complete definitions: {len(notebook02_data_dictionary)}/168")
print("PASS | Exact names, dtypes and null counts obtained from saved Parquet files")
print("PASS | Long-rotation missing values reconciled with noncandidate users")
print("PASS | Saved CSV round-trip verified")
print(f"SAVED: {_OUTPUT}")
print("Data Dictionary: PASS — 168/168 documented")
print("Baseline and source Future remain untouched")
