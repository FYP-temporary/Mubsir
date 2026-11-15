"""The five algorithms (same data, same folds). Boosters use early stopping on an inner user-level split."""
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb, xgboost as xgb
from catboost import CatBoostClassifier

ALGOS = ["DecisionTree", "RandomForest", "LightGBM", "XGBoost", "CatBoost"]


def fit_predict(name, Xtr, ytr, Xva, Xes=None, yes=None, seed=42, threads=2):
    """Returns (scores on Xva, n_iter_used)."""
    if name == "DecisionTree":
        m = DecisionTreeClassifier(max_depth=8, min_samples_leaf=50, random_state=seed).fit(Xtr, ytr)
        return m.predict_proba(Xva)[:, 1], 1
    if name == "RandomForest":
        m = RandomForestClassifier(n_estimators=150, min_samples_leaf=20, max_features="sqrt", max_samples=0.5,
                                   n_jobs=threads, random_state=seed).fit(Xtr, ytr)
        return m.predict_proba(Xva)[:, 1], 150
    if name == "LightGBM":
        m = lgb.LGBMClassifier(n_estimators=800, learning_rate=0.05, num_leaves=31, min_child_samples=50,
                               subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                               n_jobs=threads, random_state=seed, verbose=-1)
        m.fit(Xtr, ytr, eval_set=[(Xes, yes)], eval_metric="average_precision",
              callbacks=[lgb.early_stopping(30, verbose=False)])
        return m.predict_proba(Xva)[:, 1], m.best_iteration_ or 800
    if name == "XGBoost":
        m = xgb.XGBClassifier(n_estimators=800, learning_rate=0.05, max_depth=6, min_child_weight=5, subsample=0.8,
                              colsample_bytree=0.8, tree_method="hist", eval_metric="aucpr",
                              early_stopping_rounds=30, n_jobs=threads, random_state=seed)
        m.fit(Xtr, ytr, eval_set=[(Xes, yes)], verbose=False)
        return m.predict_proba(Xva)[:, 1], m.best_iteration + 1
    if name == "CatBoost":
        m = CatBoostClassifier(iterations=800, learning_rate=0.08, depth=6, eval_metric="PRAUC",
                               early_stopping_rounds=30, thread_count=threads, random_seed=seed, verbose=0)
        m.fit(Xtr, ytr, eval_set=(Xes, yes))
        return m.predict_proba(Xva)[:, 1], m.get_best_iteration() + 1
    raise ValueError(name)


def fit_final(name, X, y, n_iter, seed=42, threads=2):
    """Refit on all development users with a fixed iteration count (from CV). Returns fitted model."""
    n_iter = int(max(n_iter, 20))
    if name == "DecisionTree":
        return DecisionTreeClassifier(max_depth=8, min_samples_leaf=50, random_state=seed).fit(X, y)
    if name == "RandomForest":
        return RandomForestClassifier(n_estimators=150, min_samples_leaf=20, max_features="sqrt", max_samples=0.5,
                                      n_jobs=threads, random_state=seed).fit(X, y)
    if name == "LightGBM":
        return lgb.LGBMClassifier(n_estimators=n_iter, learning_rate=0.05, num_leaves=31, min_child_samples=50,
                                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                                  n_jobs=threads, random_state=seed, verbose=-1).fit(X, y)
    if name == "XGBoost":
        return xgb.XGBClassifier(n_estimators=n_iter, learning_rate=0.05, max_depth=6, min_child_weight=5,
                                 subsample=0.8, colsample_bytree=0.8, tree_method="hist", n_jobs=threads,
                                 random_state=seed).fit(X, y, verbose=False)
    if name == "CatBoost":
        return CatBoostClassifier(iterations=n_iter, learning_rate=0.08, depth=6, thread_count=threads,
                                  random_seed=seed, verbose=0).fit(X, y)
    raise ValueError(name)
