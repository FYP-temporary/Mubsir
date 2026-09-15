from pathlib import Path
import tempfile
import duckdb

from config import (
    EMAIL_CSV,
    DEVICE_CSV,
    FILE_CSV,
    HTTP_CSV,
    LOGON_CSV,
    EMAIL_DAILY,
    DEVICE_DAILY,
    FILE_DAILY,
    HTTP_DAILY,
    LOGON_DAILY,
    USER_DAY_FILE,
)


# ============================================================
# HELPERS
# ============================================================

def db_path(path):
    """Return a DuckDB-friendly absolute path."""
    return Path(path).resolve().as_posix()


def check_inputs():
    """Verify that all required raw CERT files exist."""
    inputs = {
        "email.csv": EMAIL_CSV,
        "device.csv": DEVICE_CSV,
        "file.csv": FILE_CSV,
        "http.csv": HTTP_CSV,
        "logon.csv": LOGON_CSV,
    }

    missing = [
        str(path)
        for path in inputs.values()
        if not Path(path).exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing required input files:\n"
            + "\n".join(missing)
        )

    print("✓ All required raw files found.")


def export_parquet(con, query, output_path):
    """Execute query and save result as compressed Parquet."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    con.execute(f"""
        COPY (
            {query}
        )
        TO '{db_path(output_path)}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD,
            OVERWRITE_OR_IGNORE TRUE
        )
    """)


def fetch_one_dict(con, query):
    """Return one DuckDB row as a dictionary."""
    cursor = con.execute(query)
    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


# ============================================================
# DAILY AGGREGATIONS
# ============================================================

def build_email_daily(con):
    print("[1/6] Processing EMAIL...")

    query = f"""
        WITH clean AS (
            SELECT
                strptime(date, '%m/%d/%Y %H:%M:%S') AS timestamp,
                user,
                TRY_CAST(size AS BIGINT) AS email_size,
                TRY_CAST(attachments AS INTEGER) AS attachments,
                lower(
                    concat_ws(
                        ';',
                        coalesce("to", ''),
                        coalesce(cc, ''),
                        coalesce(bcc, '')
                    )
                ) AS recipients
            FROM read_csv(
                '{db_path(EMAIL_CSV)}',
                header=true,
                all_varchar=true
            )
        ),

        classified AS (
            SELECT
                *,
                regexp_replace(
                    recipients,
                    '[^;]*@dtaa[.]com',
                    '',
                    'g'
                ) AS after_internal_removed
            FROM clean
        )

        SELECT
            user,
            CAST(timestamp AS DATE) AS day,
            COUNT(*) AS email_count,

            SUM(
                CASE
                    WHEN position('@' IN after_internal_removed) > 0
                    THEN 1
                    ELSE 0
                END
            ) AS external_email_events,

            SUM(coalesce(email_size, 0)) AS total_email_bytes,
            SUM(coalesce(attachments, 0)) AS attachment_count

        FROM classified
        GROUP BY user, CAST(timestamp AS DATE)
    """

    export_parquet(con, query, EMAIL_DAILY)
    print("      ✓ EMAIL complete.")


def build_device_daily(con):
    print("[2/6] Processing DEVICE / USB...")

    query = f"""
        WITH clean AS (
            SELECT
                strptime(date, '%m/%d/%Y %H:%M:%S') AS timestamp,
                user,
                activity
            FROM read_csv(
                '{db_path(DEVICE_CSV)}',
                header=true,
                all_varchar=true
            )
        )

        SELECT
            user,
            CAST(timestamp AS DATE) AS day,

            SUM(
                CASE WHEN activity = 'Connect'
                THEN 1 ELSE 0 END
            ) AS usb_connect_count,

            SUM(
                CASE WHEN activity = 'Disconnect'
                THEN 1 ELSE 0 END
            ) AS usb_disconnect_count

        FROM clean
        GROUP BY user, CAST(timestamp AS DATE)
    """

    export_parquet(con, query, DEVICE_DAILY)
    print("      ✓ DEVICE complete.")


def build_file_daily(con):
    print("[3/6] Processing FILE activity...")

    query = f"""
        WITH clean AS (
            SELECT
                strptime(date, '%m/%d/%Y %H:%M:%S') AS timestamp,
                user,
                filename
            FROM read_csv(
                '{db_path(FILE_CSV)}',
                header=true,
                all_varchar=true
            )
        )

        SELECT
            user,
            CAST(timestamp AS DATE) AS day,

            COUNT(*) AS files_copied_to_usb,

            COUNT(
                DISTINCT NULLIF(
                    lower(
                        regexp_extract(
                            filename,
                            '[.]([^.]+)$',
                            1
                        )
                    ),
                    ''
                )
            ) AS unique_file_extensions

        FROM clean
        GROUP BY user, CAST(timestamp AS DATE)
    """

    export_parquet(con, query, FILE_DAILY)
    print("      ✓ FILE complete.")


def build_http_daily(con):
    print("[4/6] Processing HTTP...")
    print("      HTTP is the largest source file; this may take longer.")

    query = f"""
        WITH clean AS (
            SELECT
                strptime(date, '%m/%d/%Y %H:%M:%S') AS timestamp,
                user,
                lower(
                    regexp_extract(
                        url,
                        'https?://([^/]+)',
                        1
                    )
                ) AS domain
            FROM read_csv(
                '{db_path(HTTP_CSV)}',
                header=true,
                all_varchar=true
            )
        )

        SELECT
            user,
            CAST(timestamp AS DATE) AS day,
            COUNT(*) AS http_request_count,
            COUNT(DISTINCT domain) AS unique_domains

        FROM clean
        GROUP BY user, CAST(timestamp AS DATE)
    """

    export_parquet(con, query, HTTP_DAILY)
    print("      ✓ HTTP complete.")


def build_logon_daily(con):
    print("[5/6] Processing LOGON...")

    query = f"""
        WITH clean AS (
            SELECT
                strptime(date, '%m/%d/%Y %H:%M:%S') AS timestamp,
                user,
                activity
            FROM read_csv(
                '{db_path(LOGON_CSV)}',
                header=true,
                all_varchar=true
            )
        )

        SELECT
            user,
            CAST(timestamp AS DATE) AS day,

            SUM(
                CASE WHEN activity = 'Logon'
                THEN 1 ELSE 0 END
            ) AS logon_count,

            MIN(
                CASE WHEN activity = 'Logon'
                THEN timestamp END
            ) AS first_logon,

            MAX(
                CASE WHEN activity = 'Logoff'
                THEN timestamp END
            ) AS last_logoff

        FROM clean
        GROUP BY user, CAST(timestamp AS DATE)
    """

    export_parquet(con, query, LOGON_DAILY)
    print("      ✓ LOGON complete.")


# ============================================================
# USER-DAY TABLE
# ============================================================

def build_user_day(con):
    print("[6/6] Building USER-DAY table...")

    email = db_path(EMAIL_DAILY)
    device = db_path(DEVICE_DAILY)
    file = db_path(FILE_DAILY)
    http = db_path(HTTP_DAILY)
    logon = db_path(LOGON_DAILY)

    query = f"""
        WITH all_activity AS (

            SELECT user, day FROM read_parquet('{email}')
            UNION
            SELECT user, day FROM read_parquet('{device}')
            UNION
            SELECT user, day FROM read_parquet('{file}')
            UNION
            SELECT user, day FROM read_parquet('{http}')
            UNION
            SELECT user, day FROM read_parquet('{logon}')

        ),

        bounds AS (
            SELECT
                user,
                MIN(day) AS first_day,
                MAX(day) AS last_day
            FROM all_activity
            GROUP BY user
        ),

        calendar AS (
            SELECT
                b.user,
                CAST(g.day AS DATE) AS day
            FROM bounds b,
            LATERAL generate_series(
                b.first_day,
                b.last_day,
                INTERVAL 1 DAY
            ) AS g(day)
        )

        SELECT
            c.user,
            c.day,

            dayofweek(c.day) AS day_of_week,

            CASE
                WHEN dayofweek(c.day) IN (0, 6)
                THEN 1
                ELSE 0
            END AS is_weekend,

            -- Email
            coalesce(e.email_count, 0) AS email_count,
            coalesce(e.external_email_events, 0)
                AS external_email_events,
            coalesce(e.total_email_bytes, 0)
                AS total_email_bytes,
            coalesce(e.attachment_count, 0)
                AS attachment_count,

            -- USB / Device
            coalesce(d.usb_connect_count, 0)
                AS usb_connect_count,
            coalesce(d.usb_disconnect_count, 0)
                AS usb_disconnect_count,

            -- File
            coalesce(f.files_copied_to_usb, 0)
                AS files_copied_to_usb,
            coalesce(f.unique_file_extensions, 0)
                AS unique_file_extensions,

            -- HTTP
            coalesce(h.http_request_count, 0)
                AS http_request_count,
            coalesce(h.unique_domains, 0)
                AS unique_domains,

            -- Logon
            coalesce(l.logon_count, 0)
                AS logon_count,
            l.first_logon,
            l.last_logoff

        FROM calendar c

        LEFT JOIN read_parquet('{email}') e
            USING (user, day)

        LEFT JOIN read_parquet('{device}') d
            USING (user, day)

        LEFT JOIN read_parquet('{file}') f
            USING (user, day)

        LEFT JOIN read_parquet('{http}') h
            USING (user, day)

        LEFT JOIN read_parquet('{logon}') l
            USING (user, day)

        ORDER BY c.user, c.day
    """

    export_parquet(con, query, USER_DAY_FILE)
    print("      ✓ USER-DAY complete.")


# ============================================================
# VALIDATION
# ============================================================

def validate_user_day(con):
    final_path = db_path(USER_DAY_FILE)

    print("\n" + "=" * 60)
    print("USER-DAY VALIDATION")
    print("=" * 60)

    summary = fetch_one_dict(
        con,
        f"""
        SELECT
            COUNT(*) AS rows,
            COUNT(DISTINCT user) AS users,
            MIN(day) AS first_day,
            MAX(day) AS last_day
        FROM read_parquet('{final_path}')
        """
    )

    email_check = fetch_one_dict(
        con,
        f"""
        SELECT
            SUM(email_count) AS total_emails,
            SUM(external_email_events) AS external_email_events,

            ROUND(
                100.0 * SUM(external_email_events)
                / NULLIF(SUM(email_count), 0),
                2
            ) AS external_percentage,

            SUM(
                CASE
                    WHEN external_email_events > email_count
                    THEN 1
                    ELSE 0
                END
            ) AS invalid_rows

        FROM read_parquet('{final_path}')
        """
    )

    duplicates = con.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT user, day
            FROM read_parquet('{final_path}')
            GROUP BY user, day
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    invalid_extensions = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{final_path}')
        WHERE unique_file_extensions > files_copied_to_usb
        """
    ).fetchone()[0]

    known_case = fetch_one_dict(
        con,
        f"""
        SELECT
            user,
            day,
            email_count,
            external_email_events,
            usb_connect_count,
            files_copied_to_usb,
            unique_file_extensions,
            http_request_count,
            logon_count

        FROM read_parquet('{final_path}')

        WHERE
            user = 'AAF0535'
            AND day = DATE '2010-08-10'
        """
    )

    # --------------------------------------------------------
    # Display summary
    # --------------------------------------------------------

    print("\nDataset summary")
    print(f"  Rows       : {summary['rows']:,}")
    print(f"  Users      : {summary['users']:,}")
    print(f"  Date range : {summary['first_day']} → {summary['last_day']}")

    print("\nEmail validation")
    print(f"  Total emails    : {email_check['total_emails']:,}")
    print(
        f"  External emails : "
        f"{email_check['external_email_events']:,}"
    )
    print(
        f"  External rate   : "
        f"{email_check['external_percentage']}%"
    )

    print("\nIntegrity checks")
    print(f"  Duplicate user-days : {duplicates}")
    print(f"  Invalid extensions  : {invalid_extensions}")

    print("\nKnown case")
    print(f"  AAF0535 / 2010-08-10 : {known_case}")

    # --------------------------------------------------------
    # Regression assertions
    # --------------------------------------------------------

    assert summary["rows"] == 464687, (
        f"Unexpected row count: {summary['rows']}"
    )

    assert summary["users"] == 1000, (
        f"Unexpected user count: {summary['users']}"
    )

    assert str(summary["first_day"]).startswith("2010-01-02"), (
        f"Unexpected first date: {summary['first_day']}"
    )

    assert str(summary["last_day"]).startswith("2011-05-17"), (
        f"Unexpected last date: {summary['last_day']}"
    )

    assert email_check["total_emails"] == 2629979, (
        f"Unexpected total email count: "
        f"{email_check['total_emails']}"
    )

    assert email_check["external_email_events"] == 1264049, (
        f"Unexpected external email count: "
        f"{email_check['external_email_events']}"
    )

    assert abs(
        float(email_check["external_percentage"]) - 48.06
    ) < 0.01, (
        f"Unexpected external email percentage: "
        f"{email_check['external_percentage']}"
    )

    assert email_check["invalid_rows"] == 0, (
        f"Invalid external email rows: "
        f"{email_check['invalid_rows']}"
    )

    assert duplicates == 0, (
        f"Duplicate user-day groups: {duplicates}"
    )

    assert invalid_extensions == 0, (
        f"Invalid extension rows: {invalid_extensions}"
    )

    assert known_case is not None, (
        "AAF0535 known case not found."
    )

    assert known_case["files_copied_to_usb"] == 11, (
        "AAF0535 expected 11 USB files on 2010-08-10."
    )

    print("\n✓ All validation checks passed.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("BUILDING USER-DAY DATASET")
    print("=" * 60)

    check_inputs()

    # Temporary DuckDB spill directory.
    # Automatically removed when processing finishes.
    with tempfile.TemporaryDirectory(
        prefix="cert_duckdb_"
    ) as temp_dir:

        con = duckdb.connect()

        try:
            con.execute("SET memory_limit='4GB'")
            con.execute("SET threads=4")
            con.execute(
                f"SET temp_directory='{db_path(temp_dir)}'"
            )

            build_email_daily(con)
            build_device_daily(con)
            build_file_daily(con)
            build_http_daily(con)
            build_logon_daily(con)
            build_user_day(con)

            validate_user_day(con)

        finally:
            con.close()

    print("\n" + "=" * 60)
    print("✅ BUILD USER-DAY: PASS")
    print("=" * 60)

    print(f"\nSaved to:\n{USER_DAY_FILE}")


if __name__ == "__main__":
    main()