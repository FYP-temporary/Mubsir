from pathlib import Path
import duckdb

from config import (
    USER_DAY_FILE,
    USER_BASELINE_FILE,
    BEHAVIOR_FEATURES_FILE,
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
    """Verify required input files exist."""
    required = {
        "User-Day dataset": USER_DAY_FILE,
        "User baseline": USER_BASELINE_FILE,
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
# BUILD BEHAVIOR FEATURES
# ============================================================

def build_behavior_features(con):
    print("[1/2] Building behavioral features...")

    user_day = db_path(USER_DAY_FILE)
    baseline = db_path(USER_BASELINE_FILE)
    output = db_path(BEHAVIOR_FEATURES_FILE)

    Path(BEHAVIOR_FEATURES_FILE).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    con.execute(f"""
        COPY (

            WITH joined AS (

                SELECT
                    d.*,
                    b.* EXCLUDE(user),

                    CASE
                        WHEN d.first_logon IS NOT NULL
                        THEN
                            EXTRACT(HOUR FROM d.first_logon) * 60
                            + EXTRACT(MINUTE FROM d.first_logon)
                    END AS first_logon_minute,

                    CASE
                        WHEN d.last_logoff IS NOT NULL
                        THEN
                            EXTRACT(HOUR FROM d.last_logoff) * 60
                            + EXTRACT(MINUTE FROM d.last_logoff)
                    END AS last_logoff_minute

                FROM read_parquet('{user_day}') d

                LEFT JOIN read_parquet('{baseline}') b
                    USING (user)
            ),

            daily AS (

                SELECT
                    *,

                    -- =========================================
                    -- BASELINE RATIOS
                    -- =========================================

                    email_count
                        / GREATEST(email_count_p95, 1)
                        AS email_p95_ratio,

                    external_email_events
                        / GREATEST(external_email_p95, 1)
                        AS external_email_p95_ratio,

                    usb_connect_count
                        / GREATEST(usb_connect_p95, 1)
                        AS usb_connect_p95_ratio,

                    files_copied_to_usb
                        / GREATEST(usb_files_p95, 1)
                        AS usb_files_p95_ratio,

                    http_request_count
                        / GREATEST(http_requests_p95, 1)
                        AS http_p95_ratio,

                    unique_domains
                        / GREATEST(unique_domains_p95, 1)
                        AS domains_p95_ratio,


                    -- =========================================
                    -- ABOVE-P95 FLAGS
                    -- =========================================

                    CASE
                        WHEN email_count > email_count_p95
                        THEN 1 ELSE 0
                    END AS email_above_p95,

                    CASE
                        WHEN external_email_events > external_email_p95
                        THEN 1 ELSE 0
                    END AS external_email_above_p95,

                    CASE
                        WHEN usb_connect_count > usb_connect_p95
                        THEN 1 ELSE 0
                    END AS usb_connect_above_p95,

                    CASE
                        WHEN files_copied_to_usb > usb_files_p95
                        THEN 1 ELSE 0
                    END AS usb_files_above_p95,

                    CASE
                        WHEN http_request_count > http_requests_p95
                        THEN 1 ELSE 0
                    END AS http_above_p95,

                    CASE
                        WHEN unique_domains > unique_domains_p95
                        THEN 1 ELSE 0
                    END AS domains_above_p95,


                    -- =========================================
                    -- UNUSUAL WORKING TIME
                    -- =========================================

                    CASE
                        WHEN first_logon_minute IS NOT NULL
                         AND first_logon_minute < first_logon_p05
                        THEN first_logon_p05 - first_logon_minute
                        ELSE 0
                    END AS early_logon_minutes,

                    CASE
                        WHEN last_logoff_minute IS NOT NULL
                         AND last_logoff_minute > last_logoff_p95
                        THEN last_logoff_minute - last_logoff_p95
                        ELSE 0
                    END AS late_logoff_minutes,


                    -- =========================================
                    -- DAILY CHANNEL ACTIVITY
                    -- =========================================

                    CASE
                        WHEN email_count > 0
                        THEN 1 ELSE 0
                    END AS email_active,

                    CASE
                        WHEN usb_connect_count > 0
                          OR files_copied_to_usb > 0
                        THEN 1 ELSE 0
                    END AS usb_active,

                    CASE
                        WHEN http_request_count > 0
                        THEN 1 ELSE 0
                    END AS http_active

                FROM joined
            ),

            with_flags AS (

                SELECT
                    *,

                    (
                        email_above_p95
                        + external_email_above_p95
                        + usb_connect_above_p95
                        + usb_files_above_p95
                        + http_above_p95
                        + domains_above_p95
                    ) AS daily_abnormal_feature_count,

                    CASE
                        WHEN (
                            email_above_p95
                            + external_email_above_p95
                            + usb_connect_above_p95
                            + usb_files_above_p95
                            + http_above_p95
                            + domains_above_p95
                        ) > 0
                        THEN 1
                        ELSE 0
                    END AS abnormal_day

                FROM daily
            )

            SELECT
                *,

                -- =============================================
                -- 7-DAY ROLLING FEATURES
                -- =============================================

                SUM(external_email_events) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) AS external_emails_7d,

                SUM(files_copied_to_usb) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) AS usb_files_7d,

                SUM(http_request_count) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) AS http_requests_7d,

                SUM(abnormal_day) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) AS abnormal_days_7d,


                -- =============================================
                -- 14-DAY ROLLING FEATURES
                -- =============================================

                SUM(external_email_events) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS external_emails_14d,

                SUM(files_copied_to_usb) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS usb_files_14d,

                SUM(http_request_count) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS http_requests_14d,

                SUM(abnormal_day) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS abnormal_days_14d,


                -- =============================================
                -- 30-DAY ROLLING FEATURES
                -- =============================================

                SUM(files_copied_to_usb) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS usb_files_30d,

                SUM(external_email_events) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS external_emails_30d,

                SUM(abnormal_day) OVER (
                    PARTITION BY user
                    ORDER BY day
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS abnormal_days_30d,


                -- =============================================
                -- CHANNEL ACTIVITY DIVERSITY
                -- =============================================
                -- Counts how many of Email / USB / HTTP were
                -- active during the previous 7 days.
                --
                -- This is NOT the final channel-rotation feature.
                -- Rotation will be calculated later from ordered
                -- attack / simulation events.

                (
                    MAX(email_active) OVER (
                        PARTITION BY user
                        ORDER BY day
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                    )
                    +
                    MAX(usb_active) OVER (
                        PARTITION BY user
                        ORDER BY day
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                    )
                    +
                    MAX(http_active) OVER (
                        PARTITION BY user
                        ORDER BY day
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                    )
                ) AS activity_channel_diversity_7d

            FROM with_flags

            ORDER BY user, day

        )
        TO '{output}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD,
            OVERWRITE_OR_IGNORE TRUE
        )
    """)

    print("      ✓ BEHAVIOR FEATURES complete.")


# ============================================================
# VALIDATION
# ============================================================

def validate_behavior_features(con):
    print("\n[2/2] Validating behavior dataset...")

    output = db_path(BEHAVIOR_FEATURES_FILE)

    # --------------------------------------------------------
    # Dataset summary
    # --------------------------------------------------------

    summary = fetch_one_dict(
        con,
        f"""
        SELECT
            COUNT(*) AS rows,
            COUNT(DISTINCT user) AS users,
            MIN(day) AS first_day,
            MAX(day) AS last_day
        FROM read_parquet('{output}')
        """
    )

    # --------------------------------------------------------
    # Column count
    # --------------------------------------------------------

    column_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            DESCRIBE
            SELECT *
            FROM read_parquet('{output}')
        )
        """
    ).fetchone()[0]

    # --------------------------------------------------------
    # Duplicate user-days
    # --------------------------------------------------------

    duplicates = con.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT user, day
            FROM read_parquet('{output}')
            GROUP BY user, day
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    # --------------------------------------------------------
    # Baseline join integrity
    # --------------------------------------------------------

    missing_baseline = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{output}')
        WHERE baseline_workdays IS NULL
        """
    ).fetchone()[0]

    # --------------------------------------------------------
    # Email consistency
    # --------------------------------------------------------

    email_check = fetch_one_dict(
        con,
        f"""
        SELECT
            SUM(email_count) AS total_emails,
            SUM(external_email_events)
                AS external_email_events,

            ROUND(
                100.0 * SUM(external_email_events)
                / NULLIF(SUM(email_count), 0),
                2
            ) AS external_percentage

        FROM read_parquet('{output}')
        """
    )

    # --------------------------------------------------------
    # Known baseline propagation
    # --------------------------------------------------------

    aaf_baseline = fetch_one_dict(
        con,
        f"""
        SELECT DISTINCT
            user,
            baseline_workdays,
            external_email_median,
            external_email_p95,
            usb_files_median,
            usb_files_p95

        FROM read_parquet('{output}')

        WHERE user = 'AAF0535'
        """
    )

    # --------------------------------------------------------
    # Known malicious case
    # --------------------------------------------------------

    known_case = fetch_one_dict(
        con,
        f"""
        SELECT
            day,
            files_copied_to_usb,
            usb_files_p95,

            ROUND(
                usb_files_p95_ratio,
                2
            ) AS usb_ratio,

            usb_files_above_p95,

            external_email_events,
            external_email_p95,

            usb_files_7d,
            usb_files_14d,

            abnormal_day,
            abnormal_days_7d

        FROM read_parquet('{output}')

        WHERE user = 'AAF0535'
          AND day = DATE '2010-08-10'
        """
    )

    # --------------------------------------------------------
    # Small inspection sample
    # --------------------------------------------------------

    sample = con.execute(
        f"""
        SELECT
            day,
            files_copied_to_usb,
            usb_files_p95,

            ROUND(
                usb_files_p95_ratio,
                2
            ) AS usb_ratio,

            usb_files_above_p95,
            external_email_events,
            usb_files_7d,
            usb_files_14d,
            abnormal_day,
            abnormal_days_7d

        FROM read_parquet('{output}')

        WHERE user = 'AAF0535'
          AND day BETWEEN
              DATE '2010-08-01'
              AND DATE '2010-08-20'

        ORDER BY day
        """
    ).df()

    # --------------------------------------------------------
    # Clear output
    # --------------------------------------------------------

    print("\nBehavior dataset summary")
    print(f"  Rows                 : {summary['rows']:,}")
    print(f"  Users                : {summary['users']:,}")
    print(
        f"  Date range           : "
        f"{summary['first_day']} → {summary['last_day']}"
    )
    print(f"  Total columns        : {column_count}")

    print("\nIntegrity checks")
    print(f"  Duplicate user-days  : {duplicates}")
    print(f"  Missing baselines    : {missing_baseline}")

    print("\nEmail consistency")
    print(
        f"  Total emails         : "
        f"{email_check['total_emails']:,}"
    )
    print(
        f"  External emails      : "
        f"{email_check['external_email_events']:,}"
    )
    print(
        f"  External rate        : "
        f"{email_check['external_percentage']}%"
    )

    print("\nKnown-user baseline: AAF0535")

    if aaf_baseline:
        print(
            f"  Baseline workdays    : "
            f"{aaf_baseline['baseline_workdays']}"
        )
        print(
            f"  External email P95   : "
            f"{aaf_baseline['external_email_p95']}"
        )
        print(
            f"  USB files P95        : "
            f"{aaf_baseline['usb_files_p95']}"
        )

    print("\nKnown behavior case: AAF0535 / 2010-08-10")
    print(f"  {known_case}")

    print("\nAAF0535 August sample")
    print(sample.to_string(index=False))

    # --------------------------------------------------------
    # Regression assertions
    # --------------------------------------------------------

    assert summary["rows"] == 464687, (
        f"Unexpected row count: {summary['rows']}"
    )

    assert summary["users"] == 1000, (
        f"Unexpected user count: {summary['users']}"
    )

    assert column_count == 73, (
        f"Expected 73 columns, found {column_count}"
    )

    assert duplicates == 0, (
        f"Duplicate user-day groups: {duplicates}"
    )

    assert missing_baseline == 0, (
        f"Rows missing baseline: {missing_baseline}"
    )

    assert email_check["total_emails"] == 2629979, (
        f"Unexpected email total: "
        f"{email_check['total_emails']}"
    )

    assert email_check["external_email_events"] == 1264049, (
        f"Unexpected external email total: "
        f"{email_check['external_email_events']}"
    )

    assert abs(
        float(email_check["external_percentage"]) - 48.06
    ) < 0.01, (
        f"Unexpected external email percentage: "
        f"{email_check['external_percentage']}"
    )

    assert aaf_baseline is not None, (
        "AAF0535 baseline values were not found."
    )

    assert int(aaf_baseline["baseline_workdays"]) == 111
    assert float(aaf_baseline["external_email_median"]) == 1.0
    assert float(aaf_baseline["external_email_p95"]) == 3.0
    assert float(aaf_baseline["usb_files_median"]) == 2.0
    assert float(aaf_baseline["usb_files_p95"]) == 5.0

    assert known_case is not None, (
        "Known AAF0535 case not found."
    )

    assert int(
        known_case["files_copied_to_usb"]
    ) == 11

    assert float(
        known_case["usb_files_p95"]
    ) == 5.0

    assert abs(
        float(known_case["usb_ratio"]) - 2.2
    ) < 0.01

    assert int(
        known_case["usb_files_above_p95"]
    ) == 1

    print("\n✓ All behavior-feature validation checks passed.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("BUILDING BEHAVIOR FEATURES")
    print("=" * 60)

    check_inputs()

    con = duckdb.connect()

    try:
        build_behavior_features(con)
        validate_behavior_features(con)

    finally:
        con.close()

    print("\n" + "=" * 60)
    print("✅ BUILD BEHAVIOR FEATURES: PASS")
    print("=" * 60)

    print(f"\nSaved to:\n{BEHAVIOR_FEATURES_FILE}")


if __name__ == "__main__":
    main()