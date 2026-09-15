from pathlib import Path
import pandas as pd

from config import (
    INSIDERS_CSV,
    GROUND_TRUTH_PARQUET,
    GROUND_TRUTH_CSV,
)


# ============================================================
# SCENARIO METADATA
# ============================================================

SCENARIO_NAMES = {
    1: "After-hours + USB + Web exfiltration",
    2: "Long-term USB data theft before departure",
    3: "Keylogger + impersonation + disruptive email",
}

EXFILTRATION_RELEVANT = {
    1: 1,
    2: 1,
    3: 0,
}


# ============================================================
# HELPERS
# ============================================================

def check_input():
    """Verify that the CERT insider ground-truth file exists."""
    if not Path(INSIDERS_CSV).exists():
        raise FileNotFoundError(
            f"CERT insiders file not found:\n{INSIDERS_CSV}"
        )

    print("✓ CERT insiders file found.")


def load_ground_truth():
    """Load and prepare CERT r4.2 insider incidents."""

    print("[1/3] Loading CERT insider labels...")

    df = pd.read_csv(
        INSIDERS_CSV,
        dtype=str,
    )

    print(f"      Raw rows: {len(df):,}")

    print("\n[2/3] Building CERT r4.2 ground truth...")

    # Dataset identifier
    df["dataset_num"] = pd.to_numeric(
        df["dataset"],
        errors="coerce",
    )

    # Keep CERT r4.2 only
    gt = df[
        df["dataset_num"] == 4.2
    ].copy()

    # Scenario number
    gt["scenario"] = pd.to_numeric(
        gt["scenario"],
        errors="raise",
    ).astype(int)

    # CERT timestamps are MM/DD/YYYY HH:MM:SS
    gt["attack_start"] = pd.to_datetime(
        gt["start"],
        format="%m/%d/%Y %H:%M:%S",
        errors="raise",
    )

    gt["attack_end"] = pd.to_datetime(
        gt["end"],
        format="%m/%d/%Y %H:%M:%S",
        errors="raise",
    )

    # Attack duration in days
    gt["duration_days"] = (
        gt["attack_end"] - gt["attack_start"]
    ).dt.total_seconds() / 86400

    # Scenario metadata
    gt["scenario_name"] = gt["scenario"].map(
        SCENARIO_NAMES
    )

    gt["exfiltration_relevant"] = gt["scenario"].map(
        EXFILTRATION_RELEVANT
    )

    # Provenance
    gt["source"] = "CERT_r4.2"
    gt["is_synthetic"] = 0

    # Final schema
    gt = gt[
        [
            "user",
            "scenario",
            "scenario_name",
            "details",
            "attack_start",
            "attack_end",
            "duration_days",
            "exfiltration_relevant",
            "source",
            "is_synthetic",
        ]
    ].copy()

    # Stable ordering
    gt = gt.sort_values(
        by=[
            "scenario",
            "attack_start",
            "user",
        ]
    ).reset_index(drop=True)

    return gt


# ============================================================
# VALIDATION
# ============================================================

def validate_ground_truth(gt):
    """Validate structure and known CERT r4.2 counts."""

    print("\n[3/3] Validating ground truth...")

    scenario_counts = (
        gt["scenario"]
        .value_counts()
        .sort_index()
    )

    exfiltration_counts = (
        gt["exfiltration_relevant"]
        .value_counts()
        .sort_index(ascending=False)
    )

    duration_summary = (
        gt.groupby("scenario")["duration_days"]
        .agg(
            count="count",
            min="min",
            median="median",
            mean="mean",
            max="max",
        )
        .round(2)
    )

    missing_values = int(
        gt.isna().sum().sum()
    )

    duplicates = int(
        gt.duplicated().sum()
    )

    # --------------------------------------------------------
    # Clear output
    # --------------------------------------------------------

    print("\nGround-truth summary")
    print(f"  Total incidents          : {len(gt)}")
    print(f"  Unique malicious users   : {gt['user'].nunique()}")
    print(
        f"  Exfiltration relevant    : "
        f"{gt['exfiltration_relevant'].sum()}"
    )

    print("\nScenario counts")
    for scenario, count in scenario_counts.items():
        print(f"  Scenario {scenario}: {count}")

    print("\nIntegrity checks")
    print(f"  Missing values           : {missing_values}")
    print(f"  Duplicate rows           : {duplicates}")

    print("\nDuration by scenario")
    print(duration_summary.to_string())

    print("\nFirst incidents")
    print(gt.head().to_string(index=False))

    # --------------------------------------------------------
    # Assertions
    # --------------------------------------------------------

    assert len(gt) == 70, (
        f"Expected 70 incidents, found {len(gt)}"
    )

    assert gt["user"].nunique() == 70, (
        "Expected 70 unique malicious users."
    )

    assert scenario_counts.get(1, 0) == 30, (
        "Scenario 1 count should be 30."
    )

    assert scenario_counts.get(2, 0) == 30, (
        "Scenario 2 count should be 30."
    )

    assert scenario_counts.get(3, 0) == 10, (
        "Scenario 3 count should be 10."
    )

    assert gt["exfiltration_relevant"].sum() == 60, (
        "Expected 60 exfiltration-relevant incidents."
    )

    assert missing_values == 0, (
        "Ground truth contains missing values."
    )

    assert duplicates == 0, (
        "Ground truth contains duplicate rows."
    )

    assert (
        gt["attack_start"] <= gt["attack_end"]
    ).all(), (
        "Some attacks have start time after end time."
    )

    assert set(gt["scenario"].unique()) == {1, 2, 3}, (
        "Unexpected scenarios detected."
    )

    assert (
        gt["source"] == "CERT_r4.2"
    ).all()

    assert (
        gt["is_synthetic"] == 0
    ).all()

    print("\n✓ All ground-truth validation checks passed.")


# ============================================================
# SAVE
# ============================================================

def save_ground_truth(gt):
    """Save ground truth as Parquet and CSV."""

    Path(GROUND_TRUTH_PARQUET).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    gt.to_parquet(
        GROUND_TRUTH_PARQUET,
        index=False,
    )

    gt.to_csv(
        GROUND_TRUTH_CSV,
        index=False,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("BUILDING CERT R4.2 GROUND TRUTH")
    print("=" * 60)

    check_input()

    gt = load_ground_truth()

    validate_ground_truth(gt)

    save_ground_truth(gt)

    print("\n" + "=" * 60)
    print("✅ BUILD GROUND TRUTH: PASS")
    print("=" * 60)

    print("\nSaved to:")
    print(f"  {GROUND_TRUTH_PARQUET}")
    print(f"  {GROUND_TRUTH_CSV}")


if __name__ == "__main__":
    main()