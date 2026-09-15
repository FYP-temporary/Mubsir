from pathlib import Path
import subprocess
import sys
import time

from config import PROJECT_ROOT


# ============================================================
# PIPELINE CONFIGURATION
# ============================================================

PIPELINE_DIR = Path(__file__).resolve().parent

STEPS = [
    ("Build User-Day Dataset", "build_user_day.py"),
    ("Build User Baseline", "build_baseline.py"),
    ("Build Behavior Features", "build_behavior_features.py"),
    ("Build Ground Truth", "build_ground_truth.py"),
    ("Final Data Quality Validation", "validate_data.py"),
]


# ============================================================
# RUN ONE STEP
# ============================================================

def run_step(step_number, step_name, script_name):
    """Run one pipeline step and stop if it fails."""

    script_path = PIPELINE_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(
            f"Pipeline script not found:\n{script_path}"
        )

    print("\n" + "=" * 70)
    print(
        f"[{step_number}/{len(STEPS)}] "
        f"{step_name}"
    )
    print("=" * 70)
    print(f"Running: {script_name}\n")

    start = time.perf_counter()

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=PROJECT_ROOT,
    )

    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print("\n" + "=" * 70)
        print("❌ PIPELINE FAILED")
        print("=" * 70)
        print(f"Failed step : {step_name}")
        print(f"Script      : {script_name}")
        print(f"Return code : {result.returncode}")
        print(f"Elapsed     : {elapsed:.2f} seconds")

        sys.exit(result.returncode)

    print(
        f"\n✓ {step_name} completed "
        f"({elapsed:.2f} seconds)"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FYP DATA ENGINEERING PIPELINE")
    print("=" * 70)

    print(f"\nProject root     : {PROJECT_ROOT}")
    print(f"Python executable: {sys.executable}")

    print("\nPipeline order:")
    for i, (name, _) in enumerate(STEPS, start=1):
        print(f"  {i}. {name}")

    pipeline_start = time.perf_counter()

    for step_number, (step_name, script_name) in enumerate(
        STEPS,
        start=1,
    ):
        run_step(
            step_number,
            step_name,
            script_name,
        )

    total_elapsed = (
        time.perf_counter()
        - pipeline_start
    )

    print("\n" + "=" * 70)
    print("✅ DATA ENGINEERING PIPELINE: PASS")
    print("=" * 70)

    print(
        f"Completed {len(STEPS)} "
        "pipeline steps successfully."
    )

    print(
        f"Total elapsed time: "
        f"{total_elapsed:.2f} seconds"
    )

    print("\nCompleted steps:")
    for name, _ in STEPS:
        print(f"  ✓ {name}")

    print("\nDataset is ready for handoff.")
    print("=" * 70)


if __name__ == "__main__":
    main()