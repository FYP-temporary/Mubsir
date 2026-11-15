"""Shared config + helpers for the Mubsir v2 pipeline (r6.2, 995-user pool)."""
import os
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss, roc_curve

PKG = Path(__file__).resolve().parent
_CANDIDATES = [PKG / "data" / "Clear_Attack_Simulation", PKG.parents[1] / "Clear_Attack_Simulation"]   # local copy, or the team's folder at the repository root
ROOT = Path(os.environ.get("MUBSIR_DATA") or next((c for c in _CANDIDATES if c.exists()), _CANDIDATES[0]))   # source data (override with MUBSIR_DATA)
WORK = Path(os.environ.get("MUBSIR_WORK", PKG / "data" / "work"))                      # derived feature tables (override with MUBSIR_WORK)
MODEL = PKG.parent / "model"                                                           # deployable bundle (manifest + boosters + mubsir_infer.py)
RES = PKG / "results"
WORK.mkdir(parents=True, exist_ok=True); RES.mkdir(parents=True, exist_ok=True)

ML_FINAL = ROOT / "data/final/behavior_features_r62_ml_final.parquet"
GT_USERS = ROOT / "data/ground_truth/ground_truth_users.parquet"
GT_USER_DAYS = ROOT / "data/ground_truth/ground_truth_user_days.parquet"
ASSIGN = ROOT / "data/stages_output/validated_scenario_assignments_r62.parquet"
POOL = PKG / "inputs/pool_995_roles_r62.csv"
PREPARED = WORK / "prepared_995.parquet"
SPLIT = RES / "user_split.csv"

WINDOWS = [5, 10, 20]
SEED = 42
# 23 per-user constant baseline columns (computed on 2010 only)
STATIC = (["baseline_workdays"]
          + [f"email_{k}" for k in ["active_days", "active_rate", "count_p50", "count_p90", "count_p95", "count_mad",
                                    "bytes_p50", "bytes_p90", "bytes_p95", "bytes_mad"]]
          + [f"usb_{k}" for k in ["active_days", "active_rate", "copy_p50", "copy_p90", "copy_p95", "copy_mad"]]
          + [f"http_upload_{k}" for k in ["active_days", "active_rate", "p50", "p90", "p95", "mad"]])
NON_FEATURES = ["user", "day", "first_logon", "last_logoff", "is_weekend", "y", "group", "stealth", "scenario_id", "part"] \
               + [f"y_{h}" for h in WINDOWS] + [f"yf_{h}" for h in WINDOWS]


def feature_cols(df, include_static=True, static_only=False):
    cols = [c for c in df.columns if c not in NON_FEATURES]
    if static_only:
        return [c for c in cols if c in STATIC]
    if not include_static:
        cols = [c for c in cols if c not in STATIC]
    return cols


def select_features(df, mode):
    return feature_cols(df, include_static=(mode == "full"), static_only=(mode == "static"))


def recall_at_fpr(y, s, fpr):
    f, t, _ = roc_curve(y, s)
    return float(np.interp(fpr, f, t))


def row_metrics(y, s):
    y = np.asarray(y); s = np.asarray(s)
    return dict(pr_auc=average_precision_score(y, s), roc_auc=roc_auc_score(y, s),
                rec_fpr1=recall_at_fpr(y, s, 0.01), rec_fpr5=recall_at_fpr(y, s, 0.05),
                brier=brier_score_loss(y, np.clip(s, 0, 1)), prevalence=float(y.mean()))
