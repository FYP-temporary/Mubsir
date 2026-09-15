from pathlib import Path
import duckdb

from config import (
    USER_DAY_FILE,
    USER_BASELINE_FILE,
    INSIDERS_CSV,
)


# ============================================================
# HELPERS
# ============================================================

def db_path(path):
    """Return an absolute path compatible with DuckDB."""
    return Path(path).resolve().as_posix()


def fetch_one_dict(con, query):
    """Return one DuckDB result row as a dictionary."""
    cursor = con.execute(query)
    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def check_inputs():
    """Verify that the required input files exist."""
    required = {
        "User-Day dataset": USER_DAY_FILE,
        "CERT insiders file": INSIDERS_CSV,
    }

    missing = [
        f"{name}: {path}"
        for name, path in required.items()
        if not Path(path).exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing required input files:\n"
            + "\n".join(missing)
        )

    print("✓ Required input files found.")


# ============================================================
# BASELINE CUTOFF
# ============================================================

def get_baseline_cutoff(con):
    """Find the first malicious incident in CERT r4.2."""

    first_attack = con.execute(
        f"""
        SELECT
            MIN(
                strptime(
                    start,
                    '%m/%d/%Y %H:%M:%S'
                )
            )
        FROM read_csv(
            '{db_path(INSIDERS_CSV)}',
            header=true,
            all_varchar=true
        )
        WHERE TRY_CAST(dataset AS DOUBLE) = 4.2
        """
    ).fetchone()[0]

    if first_attack is None:
        raise ValueError(
            "Could not determine the first CERT r4.2 attack."
        )

    baseline_cutoff = first_attack.date()

    print("[1/3] Baseline cutoff detected.")
    print(f"      First malicious incident : {first_attack}")
    print(f"      Baseline cutoff          : {baseline_cutoff}")
    print(
        "      Rule                     : "
        f"day < {baseline_cutoff}, weekdays only, "
        "logon_count > 0"
    )

    return first_attack, baseline_cutoff


# ============================================================
# BUILD BASELINE
# ============================================================

def build_baseline(con, baseline_cutoff):
    """Build one historical behavioral baseline per user."""

    print("\n[2/3] Building per-user behavioral baseline...")

    user_day = db_path(USER_DAY_FILE)
    baseline_out = db_path(USER_BASELINE_FILE)

    query = f"""
        COPY (

            WITH baseline_days AS (

                SELECT
                    *,

                    (
                        EXTRACT(HOUR FROM first_logon) * 60
                        + EXTRACT(MINUTE FROM first_logon)
                    ) AS first_logon_minute,

                    (
                        EXTRACT(HOUR FROM last_logoff) * 60
                        + EXTRACT(MINUTE FROM last_logoff)
                    ) AS last_logoff_minute

                FROM read_parquet('{user_day}')

                WHERE day < DATE '{baseline_cutoff}'
                  AND is_weekend = 0
                  AND logon_count > 0
            )

            SELECT
                user,
                COUNT(*) AS baseline_workdays,

                -- Email
                MEDIAN(email_count)
                    AS email_count_median,

                QUANTILE_CONT(email_count, 0.95)
                    AS email_count_p95,

                MEDIAN(external_email_events)
                    AS external_email_median,

                QUANTILE_CONT(external_email_events, 0.95)
                    AS external_email_p95,

                MEDIAN(total_email_bytes)
                    AS email_bytes_median,

                QUANTILE_CONT(total_email_bytes, 0.95)
                    AS email_bytes_p95,

                MEDIAN(attachment_count)
                    AS attachment_median,

                QUANTILE_CONT(attachment_count, 0.95)
                    AS attachment_p95,

                -- USB / Device
                MEDIAN(usb_connect_count)
                    AS usb_connect_median,

                QUANTILE_CONT(usb_connect_count, 0.95)
                    AS usb_connect_p95,

                -- File activity
                MEDIAN(files_copied_to_usb)
                    AS usb_files_median,

                QUANTILE_CONT(files_copied_to_usb, 0.95)
                    AS usb_files_p95,

                -- HTTP
                MEDIAN(http_request_count)
                    AS http_requests_median,

                QUANTILE_CONT(http_request_count, 0.95)
                    AS http_requests_p95,

                MEDIAN(unique_domains)
                    AS unique_domains_median,

                QUANTILE_CONT(unique_domains, 0.95)
                    AS unique_domains_p95,

                -- Logon behavior
                MEDIAN(first_logon_minute)
                    AS first_logon_median,

                QUANTILE_CONT(first_logon_minute, 0.05)
                    AS first_logon_p05,

                QUANTILE_CONT(first_logon_minute, 0.95)
                    AS first_logon_p95,

                MEDIAN(last_logoff_minute)
                    AS last_logoff_median,

                QUANTILE_CONT(last_logoff_minute, 0.05)
                    AS last_logoff_p05,

                QUANTILE_CONT(last_logoff_minute, 0.95)
                    AS last_logoff_p95

            FROM baseline_days
            GROUP BY user
            ORDER BY user

        )
        TO '{baseline_out}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD,
            OVERWRITE_OR_IGNORE TRUE
        )
    """

    con.execute(query)

    print("      ✓ USER BASELINE complete.")


# ============================================================
# VALIDATION
# ============================================================

def validate_baseline(con, first_attack, baseline_cutoff):
    """Run integrity, regression, and known-user checks."""

    print("\n[3/3] Validating baseline...")

    baseline = db_path(USER_BASELINE_FILE)
    user_day = db_path(USER_DAY_FILE)

    # --------------------------------------------------------
    # Dataset summary
    # --------------------------------------------------------

    summary = fetch_one_dict(
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

    # --------------------------------------------------------
    # Duplicate users
    # --------------------------------------------------------

    duplicate_users = con.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT user
            FROM read_parquet('{baseline}')
            GROUP BY user
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    # --------------------------------------------------------
    # Critical nulls
    # --------------------------------------------------------

    nulls = fetch_one_dict(
        con,
        f"""
        SELECT
            SUM(CASE WHEN user IS NULL
                THEN 1 ELSE 0 END) AS null_user,

            SUM(CASE WHEN baseline_workdays IS NULL
                THEN 1 ELSE 0 END) AS null_baseline_workdays,

            SUM(CASE WHEN external_email_median IS NULL
                THEN 1 ELSE 0 END) AS null_external_email_median,

            SUM(CASE WHEN external_email_p95 IS NULL
                THEN 1 ELSE 0 END) AS null_external_email_p95,

            SUM(CASE WHEN usb_files_p95 IS NULL
                THEN 1 ELSE 0 END) AS null_usb_files_p95,

            SUM(CASE WHEN http_requests_p95 IS NULL
                THEN 1 ELSE 0 END) AS null_http_requests_p95

        FROM read_parquet('{baseline}')
        """
    )

    total_nulls = sum(int(value or 0) for value in nulls.values())

    # --------------------------------------------------------
    # Known user: AAF0535
    # --------------------------------------------------------

    aaf = fetch_one_dict(
        con,
        f"""
        SELECT *
        FROM read_parquet('{baseline}')
        WHERE user = 'AAF0535'
        """
    )

    # Recalculate selected baseline values directly
    calculated_aaf = fetch_one_dict(
        con,
        f"""
        SELECT
            COUNT(*) AS baseline_workdays,

            MEDIAN(external_email_events)
                AS external_email_median,

            QUANTILE_CONT(external_email_events, 0.95)
                AS external_email_p95,

            MEDIAN(files_copied_to_usb)
                AS usb_files_median,

            QUANTILE_CONT(files_copied_to_usb, 0.95)
                AS usb_files_p95

        FROM read_parquet('{user_day}')

        WHERE user = 'AAF0535'
          AND day < DATE '{baseline_cutoff}'
          AND is_weekend = 0
          AND logon_count > 0
        """
    )

    # --------------------------------------------------------
    # Clear output
    # --------------------------------------------------------

    print("\nBaseline summary")
    print(f"  Users                : {summary['users']:,}")
    print(f"  Minimum workdays     : {summary['min_days']}")
    print(f"  Median workdays      : {summary['median_days']}")
    print(f"  Maximum workdays     : {summary['max_days']}")

    print("\nIntegrity checks")
    print(f"  Duplicate users      : {duplicate_users}")
    print(f"  Critical null values : {total_nulls}")

    print("\nKnown-user check: AAF0535")

    if aaf is None:
        print("  ✗ User not found.")
    else:
        print(
            f"  Baseline workdays    : "
            f"{aaf['baseline_workdays']}"
        )
        print(
            f"  External email P95   : "
            f"{aaf['external_email_p95']}"
        )
        print(
            f"  USB files P95        : "
            f"{aaf['usb_files_p95']}"
        )
        print(
            f"  HTTP requests P95    : "
            f"{aaf['http_requests_p95']}"
        )

    # --------------------------------------------------------
    # Regression assertions
    # --------------------------------------------------------

    assert str(first_attack).startswith(
        "2010-06-10 07:54:10"
    ), f"Unexpected first attack: {first_attack}"

    assert summary["users"] == 1000, (
        f"Unexpected baseline user count: "
        f"{summary['users']}"
    )

    assert summary["min_days"] == 23, (
        f"Unexpected minimum baseline days: "
        f"{summary['min_days']}"
    )

    assert float(summary["median_days"]) == 111.0, (
        f"Unexpected median baseline days: "
        f"{summary['median_days']}"
    )

    assert summary["max_days"] == 113, (
        f"Unexpected maximum baseline days: "
        f"{summary['max_days']}"
    )

    assert duplicate_users == 0, (
        f"Duplicate baseline users found: "
        f"{duplicate_users}"
    )

    assert total_nulls == 0, (
        "Critical null values detected in baseline."
    )

    assert aaf is not None, (
        "AAF0535 baseline record not found."
    )

    # --------------------------------------------------------
    # Expected AAF0535 values
    # --------------------------------------------------------

    assert int(aaf["baseline_workdays"]) == 111
    assert float(aaf["external_email_median"]) == 1.0
    assert float(aaf["external_email_p95"]) == 3.0
    assert float(aaf["usb_files_median"]) == 2.0
    assert float(aaf["usb_files_p95"]) == 5.0
    assert float(aaf["http_requests_median"]) == 29.0
    assert float(aaf["http_requests_p95"]) == 29.0

    # --------------------------------------------------------
    # Source consistency
    # --------------------------------------------------------

    assert (
        int(calculated_aaf["baseline_workdays"])
        == int(aaf["baseline_workdays"])
    )

    assert (
        float(calculated_aaf["external_email_median"])
        == float(aaf["external_email_median"])
    )

    assert abs(
        float(calculated_aaf["external_email_p95"])
        - float(aaf["external_email_p95"])
    ) < 0.0001

    assert (
        float(calculated_aaf["usb_files_median"])
        == float(aaf["usb_files_median"])
    )

    assert abs(
        float(calculated_aaf["usb_files_p95"])
        - float(aaf["usb_files_p95"])
    ) < 0.0001

    print("\n✓ All baseline validation checks passed.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("BUILDING USER BEHAVIORAL BASELINE")
    print("=" * 60)

    check_inputs()

    Path(USER_BASELINE_FILE).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    con = duckdb.connect()

    try:
        first_attack, baseline_cutoff = (
            get_baseline_cutoff(con)
        )

        build_baseline(
            con,
            baseline_cutoff,
        )

        validate_baseline(
            con,
            first_attack,
            baseline_cutoff,
        )

    finally:
        con.close()

    print("\n" + "=" * 60)
    print("✅ BUILD USER BASELINE: PASS")
    print("=" * 60)

    print(f"\nSaved to:\n{USER_BASELINE_FILE}")


if __name__ == "__main__":
    main()