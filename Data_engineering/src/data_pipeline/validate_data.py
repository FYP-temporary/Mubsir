from pathlib import Path
import duckdb
import pandas as pd

from config import (
    BEHAVIOR_FEATURES_FILE,
    USER_BASELINE_FILE,
    GROUND_TRUTH_PARQUET,
    DATA_QUALITY_REPORT,
)


# ============================================================
# HELPERS
# ============================================================

def db_path(path):
    """Return an absolute path compatible with DuckDB."""
    return Path(path).resolve().as_posix()


def fetch_one_dict(con, query):
    """Return one DuckDB row as a dictionary."""
    cursor = con.execute(query)
    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def count_rows(con, query):
    """Return a single COUNT(*) result."""
    return int(con.execute(query).fetchone()[0])


def check_inputs():
    """Verify that all validation inputs exist."""
    required = {
        "Behavior features": BEHAVIOR_FEATURES_FILE,
        "User baseline": USER_BASELINE_FILE,
        "Ground truth": GROUND_TRUTH_PARQUET,
    }

    missing = [
        f"{name}: {path}"
        for name, path in required.items()
        if not Path(path).exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing required validation files:\n"
            + "\n".join(missing)
        )

    print("✓ Required validation files found.")


def add_check(
    checks,
    name,
    result,
    expected,
    passed,
    severity="ERROR",
):
    """Append one validation result."""
    checks.append(
        {
            "Check": name,
            "Result": result,
            "Expected": expected,
            "Status": "PASS" if passed else "FAIL",
            "Severity": severity,
        }
    )


# ============================================================
# VALIDATION
# ============================================================

def run_validation(con):
    checks = []

    behavior = db_path(BEHAVIOR_FEATURES_FILE)
    baseline = db_path(USER_BASELINE_FILE)
    ground_truth = db_path(GROUND_TRUTH_PARQUET)

    # ========================================================
    # 1. DATASET SUMMARY
    # ========================================================

    summary = fetch_one_dict(
        con,
        f"""
        SELECT
            COUNT(*) AS rows,
            COUNT(DISTINCT user) AS users,
            MIN(day) AS first_day,
            MAX(day) AS last_day
        FROM read_parquet('{behavior}')
        """
    )

    print("\n[1/13] Dataset structure")
    print(f"      Rows       : {summary['rows']:,}")
    print(f"      Users      : {summary['users']:,}")
    print(
        f"      Date range : "
        f"{summary['first_day']} → {summary['last_day']}"
    )

    add_check(
        checks,
        "Unique users",
        int(summary["users"]),
        "1000",
        int(summary["users"]) == 1000,
    )

    add_check(
        checks,
        "Dataset contains rows",
        int(summary["rows"]),
        "> 0",
        int(summary["rows"]) > 0,
    )

    # ========================================================
    # 2. USER-DAY UNIQUENESS
    # ========================================================

    duplicates = count_rows(
        con,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT user, day
            FROM read_parquet('{behavior}')
            GROUP BY user, day
            HAVING COUNT(*) > 1
        )
        """
    )

    add_check(
        checks,
        "Duplicate user-day records",
        duplicates,
        "0",
        duplicates == 0,
    )

    print("[2/13] User-day uniqueness checked.")

    # ========================================================
    # 3. CRITICAL NULLS
    # ========================================================

    critical_columns = [
        "user",
        "day",
        "email_count",
        "external_email_events",
        "usb_connect_count",
        "files_copied_to_usb",
        "http_request_count",
        "unique_domains",
        "logon_count",
        "baseline_workdays",
        "usb_files_p95",
        "external_email_p95",
        "http_requests_p95",
    ]

    for col in critical_columns:
        null_count = count_rows(
            con,
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{behavior}')
            WHERE "{col}" IS NULL
            """
        )

        add_check(
            checks,
            f"Null values: {col}",
            null_count,
            "0",
            null_count == 0,
        )

    print("[3/13] Critical nulls checked.")

    # ========================================================
    # 4. NON-NEGATIVE FEATURES
    # ========================================================

    non_negative_columns = [
        "email_count",
        "external_email_events",
        "total_email_bytes",
        "attachment_count",
        "usb_connect_count",
        "usb_disconnect_count",
        "files_copied_to_usb",
        "unique_file_extensions",
        "http_request_count",
        "unique_domains",
        "logon_count",
        "early_logon_minutes",
        "late_logoff_minutes",
        "daily_abnormal_feature_count",
        "external_emails_7d",
        "usb_files_7d",
        "http_requests_7d",
        "abnormal_days_7d",
        "external_emails_14d",
        "usb_files_14d",
        "http_requests_14d",
        "abnormal_days_14d",
        "usb_files_30d",
        "external_emails_30d",
        "abnormal_days_30d",
    ]

    for col in non_negative_columns:
        negative_count = count_rows(
            con,
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{behavior}')
            WHERE "{col}" < 0
            """
        )

        add_check(
            checks,
            f"Negative values: {col}",
            negative_count,
            "0",
            negative_count == 0,
        )

    print("[4/13] Non-negative features checked.")

    # ========================================================
    # 5. LOGICAL CONSISTENCY
    # ========================================================

    logical_checks = [
        (
            "External email <= total email",
            "external_email_events > email_count",
        ),
        (
            "Unique file extensions <= copied files",
            "unique_file_extensions > files_copied_to_usb",
        ),
        (
            "Weekend flag validity",
            "is_weekend NOT IN (0, 1) OR is_weekend IS NULL",
        ),
    ]

    for name, condition in logical_checks:
        invalid = count_rows(
            con,
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{behavior}')
            WHERE {condition}
            """
        )

        add_check(
            checks,
            name,
            invalid,
            "0 invalid rows",
            invalid == 0,
        )

    print("[5/13] Logical consistency checked.")

    # ========================================================
    # 6. BINARY FLAGS
    # ========================================================

    flag_columns = [
        "email_above_p95",
        "external_email_above_p95",
        "usb_connect_above_p95",
        "usb_files_above_p95",
        "http_above_p95",
        "domains_above_p95",
        "abnormal_day",
    ]

    for col in flag_columns:
        invalid = count_rows(
            con,
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{behavior}')
            WHERE "{col}" NOT IN (0, 1)
               OR "{col}" IS NULL
            """
        )

        add_check(
            checks,
            f"Binary flag validity: {col}",
            invalid,
            "0 invalid rows",
            invalid == 0,
        )

    print("[6/13] Binary flags checked.")

    # ========================================================
    # 7. BASELINE QUALITY
    # ========================================================

    baseline_summary = fetch_one_dict(
        con,
        f"""
        SELECT
            COUNT(*) AS users,
            MIN(baseline_workdays) AS min_days,
            MEDIAN(baseline_workdays) AS median_days,
            MAX(baseline_workdays) AS max_days
        FROM read_parquet('{baseline}')
        """
    )

    add_check(
        checks,
        "Baseline users",
        int(baseline_summary["users"]),
        "1000",
        int(baseline_summary["users"]) == 1000,
    )

    add_check(
        checks,
        "Minimum baseline history",
        int(baseline_summary["min_days"]),
        ">= 20 workdays",
        int(baseline_summary["min_days"]) >= 20,
    )

    print("[7/13] Baseline quality checked.")

    # ========================================================
    # 8. GROUND TRUTH
    # ========================================================

    gt = fetch_one_dict(
        con,
        f"""
        SELECT
            COUNT(*) AS incidents,
            COUNT(DISTINCT user) AS malicious_users,

            SUM(
                CASE
                    WHEN exfiltration_relevant = 1
                    THEN 1
                    ELSE 0
                END
            ) AS exfiltration_incidents

        FROM read_parquet('{ground_truth}')
        """
    )

    add_check(
        checks,
        "Ground-truth incidents",
        int(gt["incidents"]),
        "70",
        int(gt["incidents"]) == 70,
    )

    add_check(
        checks,
        "Unique malicious users",
        int(gt["malicious_users"]),
        "70",
        int(gt["malicious_users"]) == 70,
    )

    add_check(
        checks,
        "Exfiltration-relevant incidents",
        int(gt["exfiltration_incidents"]),
        "60",
        int(gt["exfiltration_incidents"]) == 60,
    )

    print("[8/13] Ground truth checked.")

    # ========================================================
    # 9. GROUND-TRUTH USERS EXIST
    # ========================================================

    missing_attack_users = count_rows(
        con,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT g.user

            FROM read_parquet('{ground_truth}') g

            LEFT JOIN (
                SELECT DISTINCT user
                FROM read_parquet('{behavior}')
            ) b
            USING (user)

            WHERE b.user IS NULL
        )
        """
    )

    add_check(
        checks,
        "Ground-truth users present in behavioral dataset",
        missing_attack_users,
        "0 missing users",
        missing_attack_users == 0,
    )

    print("[9/13] Ground-truth users checked.")

    # ========================================================
    # 10. ATTACK DATE RANGE
    # ========================================================

    invalid_attack_dates = count_rows(
        con,
        f"""
        WITH bounds AS (
            SELECT
                MIN(day) AS first_day,
                MAX(day) AS last_day
            FROM read_parquet('{behavior}')
        )

        SELECT COUNT(*)

        FROM read_parquet('{ground_truth}'),
             bounds

        WHERE CAST(attack_start AS DATE) < first_day
           OR CAST(attack_end AS DATE) > last_day
        """
    )

    add_check(
        checks,
        "Attack dates within dataset period",
        invalid_attack_dates,
        "0 outside range",
        invalid_attack_dates == 0,
    )

    print("[10/13] Attack-date range checked.")

    # ========================================================
    # 11. EMAIL SANITY
    # ========================================================

    email_check = fetch_one_dict(
        con,
        f"""
        SELECT
            SUM(email_count) AS total_emails,
            SUM(external_email_events) AS external_emails,

            ROUND(
                100.0 * SUM(external_email_events)
                / NULLIF(SUM(email_count), 0),
                2
            ) AS percentage

        FROM read_parquet('{behavior}')
        """
    )

    email_percentage = float(
        email_check["percentage"]
    )

    add_check(
        checks,
        "External email percentage",
        email_percentage,
        "Between 0% and 100%",
        0 < email_percentage < 100,
    )

    print(
        "[11/13] Email sanity checked "
        f"({email_percentage}%)."
    )

    # ========================================================
    # 12. KNOWN CERT CASE
    # ========================================================

    known_case = fetch_one_dict(
        con,
        f"""
        SELECT
            files_copied_to_usb,
            usb_files_p95,

            ROUND(
                usb_files_p95_ratio,
                2
            ) AS usb_ratio,

            usb_files_above_p95

        FROM read_parquet('{behavior}')

        WHERE user = 'AAF0535'
          AND day = DATE '2010-08-10'
        """
    )

    known_case_ok = (
        known_case is not None
        and int(known_case["files_copied_to_usb"]) == 11
        and float(known_case["usb_files_p95"]) == 5.0
        and int(known_case["usb_files_above_p95"]) == 1
    )

    add_check(
        checks,
        "Known malicious behavior sanity check",
        "AAF0535 / 2010-08-10",
        "11 files, P95=5, above_p95=1",
        known_case_ok,
    )

    print("[12/13] Known CERT case checked.")

    # ========================================================
    # 13. BASELINE CONSISTENCY
    # ========================================================

    baseline_consistency = fetch_one_dict(
        con,
        f"""
        WITH cutoff AS (

            SELECT
                CAST(MIN(attack_start) AS DATE)
                    AS baseline_cutoff

            FROM read_parquet('{ground_truth}')
        ),

        calculated AS (

            SELECT
                MEDIAN(external_email_events)
                    AS calculated_external_median,

                QUANTILE_CONT(
                    external_email_events,
                    0.95
                ) AS calculated_external_p95,

                MEDIAN(files_copied_to_usb)
                    AS calculated_usb_median,

                QUANTILE_CONT(
                    files_copied_to_usb,
                    0.95
                ) AS calculated_usb_p95

            FROM read_parquet('{behavior}'),
                 cutoff

            WHERE user = 'AAF0535'
              AND day < baseline_cutoff
              AND is_weekend = 0
              AND logon_count > 0
        ),

        saved AS (

            SELECT
                external_email_median,
                external_email_p95,
                usb_files_median,
                usb_files_p95

            FROM read_parquet('{baseline}')

            WHERE user = 'AAF0535'
        )

        SELECT *
        FROM calculated, saved
        """
    )

    baseline_matches = (
        float(
            baseline_consistency[
                "calculated_external_median"
            ]
        )
        == float(
            baseline_consistency[
                "external_email_median"
            ]
        )

        and abs(
            float(
                baseline_consistency[
                    "calculated_external_p95"
                ]
            )
            - float(
                baseline_consistency[
                    "external_email_p95"
                ]
            )
        ) < 0.0001

        and float(
            baseline_consistency[
                "calculated_usb_median"
            ]
        )
        == float(
            baseline_consistency[
                "usb_files_median"
            ]
        )

        and abs(
            float(
                baseline_consistency[
                    "calculated_usb_p95"
                ]
            )
            - float(
                baseline_consistency[
                    "usb_files_p95"
                ]
            )
        ) < 0.0001
    )

    add_check(
        checks,
        "Baseline consistent with current behavioral data",
        "AAF0535 baseline values",
        "Calculated values = saved baseline values",
        baseline_matches,
    )

    print("[13/13] Baseline consistency checked.")

    return pd.DataFrame(checks)


# ============================================================
# SAVE + FINAL STATUS
# ============================================================

def save_report(report):
    Path(DATA_QUALITY_REPORT).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report.to_csv(
        DATA_QUALITY_REPORT,
        index=False,
    )


def main():

    print("=" * 70)
    print("FINAL DATA QUALITY VALIDATION")
    print("=" * 70)

    check_inputs()

    con = duckdb.connect()

    try:
        report = run_validation(con)
    finally:
        con.close()

    save_report(report)

    failed = report[
        report["Status"] == "FAIL"
    ]

    passed = int(
        (report["Status"] == "PASS").sum()
    )

    print("\n" + "=" * 70)
    print("FINAL DATA QUALITY REPORT")
    print("=" * 70)

    print(f"Total checks : {len(report)}")
    print(f"Passed       : {passed}")
    print(f"Failed       : {len(failed)}")

    if failed.empty:
        print("\n✅ DATA QUALITY STATUS: PASS")
        print("Dataset is ready for handoff.")

    else:
        print("\n❌ DATA QUALITY STATUS: REVIEW REQUIRED")

        print("\nFailed checks:")
        print(
            failed[
                [
                    "Check",
                    "Result",
                    "Expected",
                    "Severity",
                ]
            ].to_string(index=False)
        )

    print(f"\nReport saved to:\n{DATA_QUALITY_REPORT}")

    # Fail the pipeline when any validation fails.
    if not failed.empty:
        raise RuntimeError(
            f"Data quality validation failed: "
            f"{len(failed)} check(s) failed."
        )


if __name__ == "__main__":
    main()