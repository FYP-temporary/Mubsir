from pathlib import Path

# =========================
# PROJECT PATHS
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"

DOCS_DIR = PROJECT_ROOT / "docs"
RESULTS_DIR = PROJECT_ROOT / "results"

# =========================
# CERT r4.2 RAW DATA
# =========================

CERT_DATASET_DIR = RAW_DIR / "cert_r4.2 dataset"

ANSWERS_DIR = CERT_DATASET_DIR / "answers"
INSIDERS_CSV = ANSWERS_DIR / "insiders.csv"
LDAP_DIR = CERT_DATASET_DIR / "LDAP"

DEVICE_CSV = CERT_DATASET_DIR / "device.csv"
EMAIL_CSV = CERT_DATASET_DIR / "email.csv"
FILE_CSV = CERT_DATASET_DIR / "file.csv"
HTTP_CSV = CERT_DATASET_DIR / "http.csv"
LOGON_CSV = CERT_DATASET_DIR / "logon.csv"
PSYCHOMETRIC_CSV = CERT_DATASET_DIR / "psychometric.csv"

# =========================
# PROCESSED OUTPUTS
# =========================

DEVICE_DAILY = PROCESSED_DIR / "device_daily.parquet"
EMAIL_DAILY = PROCESSED_DIR / "email_daily.parquet"
FILE_DAILY = PROCESSED_DIR / "file_daily.parquet"
HTTP_DAILY = PROCESSED_DIR / "http_daily.parquet"
LOGON_DAILY = PROCESSED_DIR / "logon_daily.parquet"

USER_DAY_FILE = PROCESSED_DIR / "user_day_aggregated_v1.parquet"
USER_BASELINE_FILE = PROCESSED_DIR / "user_baseline_v1.parquet"

GROUND_TRUTH_PARQUET = PROCESSED_DIR / "ground_truth_r42.parquet"
GROUND_TRUTH_CSV = PROCESSED_DIR / "ground_truth_r42.csv"

# =========================
# FEATURE OUTPUTS
# =========================

BEHAVIOR_FEATURES_FILE = (
    FEATURES_DIR / "user_day_behavior_features_v1.parquet"
)

# =========================
# DOCUMENTATION OUTPUTS
# =========================

DATA_DICTIONARY_FILE = DOCS_DIR / "data_dictionary.xlsx"
DATA_QUALITY_REPORT = DOCS_DIR / "data_quality_report.csv"

# Create output directories if missing
for folder in (
    PROCESSED_DIR,
    FEATURES_DIR,
    DOCS_DIR,
    RESULTS_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)