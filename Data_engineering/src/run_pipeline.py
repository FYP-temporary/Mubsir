from pathlib import Path
import argparse
import importlib.util
import os
import subprocess
import sys

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


# =========================================================
# PROJECT PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "data" / "raw" / "r6.2"
PROCESSED = ROOT / "data" / "processed"
FEATURES = ROOT / "data" / "features"
NOTEBOOKS = ROOT / "notebooks"
RESULTS = ROOT / "results"

os.environ["DATA_ENGINEERING_R62_ROOT"] = str(ROOT)

KERNEL_NAME = "data-engineering-r62"


# =========================================================
# PIPELINE STAGES
# =========================================================

STAGES = {
    1: (
        "01_build_daily_channels.ipynb",
        [
            PROCESSED / "email_daily_r62.parquet",
            PROCESSED / "usb_daily_r62.parquet",
            PROCESSED / "http_daily_r62.parquet",
            PROCESSED / "logon_daily_r62.parquet",
        ],
    ),

    2: (
        "02_build_user_day_r62.ipynb",
        [
            PROCESSED / "user_day_r62_v1.parquet",
        ],
    ),

    3: (
        "03_build_baseline_r62.ipynb",
        [
            FEATURES / "user_baseline_r62_v1.parquet",
        ],
    ),

    4: (
        "04_build_behavior_features_r62.ipynb",
        [
            FEATURES / "behavior_features_r62_v1.parquet",
        ],
    ),

    5: (
        "05_clean_ground_truth_r62.ipynb",
        [
            PROCESSED / "ground_truth_users_r62.parquet",
            PROCESSED / "ground_truth_events_r62.parquet",
        ],
    ),

    6: (
        "06_build_malicious_pre_attack_baseline_r62.ipynb",
        [
            FEATURES / "malicious_pre_attack_baseline_r62.parquet",
        ],
    ),

    7: (
        "07_build_feature_dictionary_r62.ipynb",
        [
            RESULTS / "feature_dictionary_r62.csv",
        ],
    ),

    8: (
        "08_final_data_engineering_qa.ipynb",
        [
            FEATURES / "attack_host_eligibility_r62.parquet",
            RESULTS / "schema_dictionary_r62.csv",
            RESULTS / "dataset_inventory_r62.csv",
        ],
    ),

    9: (
        "09_final_validation.ipynb",
        [],
    ),
}


AUDIT_NOTEBOOK = "00_r62_feasibility_audit.ipynb"


# =========================================================
# RAW INPUT REQUIREMENTS
# =========================================================

DAILY_RAW_FILES = [
    RAW / "email.csv",
    RAW / "file.csv",
    RAW / "http.csv",
    RAW / "logon.csv",
    RAW / "device.csv",
]


GROUND_TRUTH_RAW_FILES = [
    RAW / "answers" / "insiders.csv",
    RAW / "answers" / "r6.2-1.csv",
    RAW / "answers" / "r6.2-2.csv",
    RAW / "answers" / "r6.2-3.csv",
    RAW / "answers" / "r6.2-4.csv",
    RAW / "answers" / "r6.2-5.csv",
]


PACKAGES = [
    "pandas",
    "duckdb",
    "pyarrow",
    "nbformat",
    "nbconvert",
    "ipykernel",
]


# =========================================================
# JUPYTER KERNEL
# =========================================================

def ensure_kernel():

    subprocess.run(
        [
            sys.executable,
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            KERNEL_NAME,
            "--display-name",
            "Python (DATA_ENGINEERING_R62)",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    print(
        f"✅ Jupyter kernel ready: {KERNEL_NAME}"
    )


# =========================================================
# DETERMINE SELECTED STAGES
# =========================================================

def get_stage_numbers(args):

    if args.only_stage is not None:

        return [
            args.only_stage
        ]

    return list(
        range(
            args.from_stage,
            10
        )
    )


# =========================================================
# DETERMINE REQUIRED RAW FILES
# =========================================================

def get_required_raw_files(
    stage_numbers,
    with_audit=False
):

    required = []


    # Stage 00 feasibility audit needs raw data
    if with_audit:

        required.extend(
            DAILY_RAW_FILES
        )

        required.extend(
            GROUND_TRUTH_RAW_FILES
        )


    # Stage 01 builds daily channel datasets
    if 1 in stage_numbers:

        required.extend(
            DAILY_RAW_FILES
        )


    # Stage 05 builds official ground truth
    if 5 in stage_numbers:

        required.extend(
            GROUND_TRUTH_RAW_FILES
        )


    # Remove duplicates while preserving order
    return list(
        dict.fromkeys(
            required
        )
    )


# =========================================================
# PREFLIGHT
# =========================================================

def preflight(
    stage_numbers,
    with_audit=False
):

    print("=" * 90)
    print("CERT r6.2 DATA ENGINEERING PIPELINE — PREFLIGHT")
    print("=" * 90)

    print(f"Project root : {ROOT}")
    print(f"Python       : {sys.version.split()[0]}")
    print(f"Environment  : {sys.executable}")

    errors = []


    # -----------------------------------------------------
    # CORE DIRECTORIES
    # -----------------------------------------------------

    required_dirs = [
        PROCESSED,
        FEATURES,
        NOTEBOOKS,
        RESULTS,
    ]


    for path in required_dirs:

        if not path.is_dir():

            errors.append(
                f"Missing directory: {path}"
            )


    # -----------------------------------------------------
    # SELECTED NOTEBOOKS
    # -----------------------------------------------------

    for number in stage_numbers:

        notebook_name = STAGES[number][0]

        notebook_path = (
            NOTEBOOKS
            / notebook_name
        )

        if not notebook_path.is_file():

            errors.append(
                f"Missing Stage {number:02d}: "
                f"{notebook_name}"
            )


    # -----------------------------------------------------
    # OPTIONAL AUDIT NOTEBOOK
    # -----------------------------------------------------

    if with_audit:

        audit_path = (
            NOTEBOOKS
            / AUDIT_NOTEBOOK
        )

        if not audit_path.is_file():

            errors.append(
                f"Missing audit notebook: "
                f"{AUDIT_NOTEBOOK}"
            )


    # -----------------------------------------------------
    # RAW INPUTS
    # -----------------------------------------------------

    required_raw_files = (
        get_required_raw_files(
            stage_numbers,
            with_audit
        )
    )


    if required_raw_files:

        print("\nRaw data required for selected stages: YES")

        if not RAW.is_dir():

            errors.append(
                f"Missing raw directory: {RAW}"
            )

        else:

            for path in required_raw_files:

                if not path.is_file():

                    errors.append(
                        f"Missing raw file: {path}"
                    )

    else:

        print("\nRaw data required for selected stages: NO")


    # -----------------------------------------------------
    # PYTHON PACKAGES
    # -----------------------------------------------------

    for package in PACKAGES:

        if importlib.util.find_spec(
            package
        ) is None:

            errors.append(
                f"Missing package: {package}"
            )


    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    if errors:

        print("\n❌ PREFLIGHT FAILED")

        for error in errors:

            print(
                " -",
                error
            )

        raise SystemExit(1)


    ensure_kernel()


    print(
        "\n✅ SUCCESS — PIPELINE ENVIRONMENT IS READY"
    )


# =========================================================
# EXECUTE NOTEBOOK
# =========================================================

def execute_notebook(filename):

    path = (
        NOTEBOOKS
        / filename
    )


    print("\n" + "=" * 90)
    print(f"RUNNING: {filename}")
    print("=" * 90)


    with path.open(
        "r",
        encoding="utf-8"
    ) as file:

        notebook = nbformat.read(
            file,
            as_version=4
        )


    executor = ExecutePreprocessor(
        timeout=None,
        kernel_name=KERNEL_NAME,
        allow_errors=False,
    )


    executor.preprocess(
        notebook,
        {
            "metadata": {
                "path": str(ROOT)
            }
        },
    )


    print(
        f"✅ SUCCESS — {filename}"
    )


# =========================================================
# VALIDATE OUTPUTS
# =========================================================

def validate_outputs(outputs):

    for path in outputs:

        if not path.exists():

            raise RuntimeError(
                f"Missing expected output: "
                f"{path.relative_to(ROOT)}"
            )


        if path.stat().st_size == 0:

            raise RuntimeError(
                f"Empty expected output: "
                f"{path.relative_to(ROOT)}"
            )


        print(
            f"✅ Output verified: "
            f"{path.relative_to(ROOT)}"
        )


# =========================================================
# RUN STAGE
# =========================================================

def run_stage(number):

    notebook, outputs = (
        STAGES[number]
    )


    print(
        f"\nSTAGE {number:02d}/09"
    )


    execute_notebook(
        notebook
    )


    validate_outputs(
        outputs
    )


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "CERT r6.2 Data Engineering Pipeline"
        )
    )


    parser.add_argument(
        "--check-only",
        action="store_true",
        help=(
            "Validate the environment without "
            "executing notebooks."
        ),
    )


    parser.add_argument(
        "--with-audit",
        action="store_true",
        help=(
            "Run Stage 00 feasibility audit "
            "before the selected stages."
        ),
    )


    parser.add_argument(
        "--from-stage",
        type=int,
        choices=range(1, 10),
        default=1,
        help=(
            "Start pipeline execution from "
            "the selected stage."
        ),
    )


    parser.add_argument(
        "--only-stage",
        type=int,
        choices=range(1, 10),
        help=(
            "Run only one specific stage."
        ),
    )


    args = parser.parse_args()


    # -----------------------------------------------------
    # SELECT STAGES
    # -----------------------------------------------------

    stage_numbers = (
        get_stage_numbers(
            args
        )
    )


    # -----------------------------------------------------
    # PREFLIGHT
    # -----------------------------------------------------

    preflight(
        stage_numbers,
        with_audit=args.with_audit
    )


    if args.check_only:

        print(
            "\n✅ SUCCESS — CHECK-ONLY MODE COMPLETE"
        )

        return


    # -----------------------------------------------------
    # OPTIONAL STAGE 00
    # -----------------------------------------------------

    if args.with_audit:

        print(
            "\nSTAGE 00"
        )

        execute_notebook(
            AUDIT_NOTEBOOK
        )


    # -----------------------------------------------------
    # MAIN PIPELINE
    # -----------------------------------------------------

    for number in stage_numbers:

        run_stage(
            number
        )


    # -----------------------------------------------------
    # COMPLETE
    # -----------------------------------------------------

    print("\n" + "=" * 90)

    print(
        "✅ SUCCESS — DATA ENGINEERING PIPELINE COMPLETE"
    )

    print("=" * 90)


if __name__ == "__main__":

    main()