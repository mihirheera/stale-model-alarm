"""AI model #1: predict the probability that a small-business loan will default.

Models (all trained on FY2001-2002 loans only):
  - majority baseline : predicts the training default rate for every loan ("everyone looks average")
  - industry rule     : predicts each industry's historical default rate (a simple lookup table)
  - logistic regression: an interpretable statistical model
  - gradient boosting : many small decision trees, each fixing the previous ones' mistakes

FY2003 is used only to (a) calibrate the probabilities and (b) choose the alarm threshold for
"flag this loan as high risk". FY2004+ are never touched while building the models.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from . import config


# ---------------------------------------------------------------- baselines
class MajorityBaseline:
    """Gives every loan the same probability: the default rate seen in training."""

    def fit(self, X, y):
        self.rate_ = float(np.mean(y))
        return self

    def predict_proba(self, X):
        p = np.full(len(X), self.rate_)
        return np.column_stack([1 - p, p])


class IndustryRule:
    """A lookup table: 'restaurants defaulted 15% of the time in training, so predict 15%'."""

    def fit(self, X, y):
        d = pd.DataFrame({"sector": X["sector"].values, "y": np.asarray(y)})
        self.overall_ = float(d["y"].mean())
        g = d.groupby("sector")["y"].agg(["mean", "size"])
        self.table_ = g.loc[g["size"] >= 50, "mean"].to_dict()   # ignore tiny industries
        return self

    def predict_proba(self, X):
        p = X["sector"].map(self.table_).fillna(self.overall_).to_numpy(dtype=float)
        return np.column_stack([1 - p, p])


# ---------------------------------------------------------------- machine-learning models
def logistic_regression() -> Pipeline:
    pre = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
         config.NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), config.CATEGORICAL_FEATURES),
    ])
    return Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=3000, C=1.0))])


def gradient_boosting() -> Pipeline:
    """No class weights: I want honest probabilities, and the threshold handles the imbalance."""
    n_num = len(config.NUMERIC_FEATURES)
    pre = ColumnTransformer([
        ("num", "passthrough", config.NUMERIC_FEATURES),
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                               encoded_missing_value=-1), config.CATEGORICAL_FEATURES),
    ])
    cat_mask = [False] * n_num + [True] * len(config.CATEGORICAL_FEATURES)
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
                                           min_samples_leaf=100, categorical_features=cat_mask,
                                           random_state=config.SEED)
    return Pipeline([("prep", pre), ("model", model)])


# ---------------------------------------------------------------- calibration + threshold
class Calibrated:
    """Wraps a fitted model and maps its raw scores to calibrated probabilities.

    The mapping (isotonic regression) is learned on FY2003 only, so it uses no future information.
    """

    def __init__(self, model, X_val, y_val):
        self.model = model
        raw = model.predict_proba(X_val)[:, 1]
        self.iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(raw, y_val)

    def predict_proba(self, X):
        p = self.iso.predict(self.model.predict_proba(X)[:, 1])
        return np.column_stack([1 - p, p])


def choose_threshold(y_val, p_val) -> float:
    """Pick the probability cut-off that maximises F1 on the validation year (FY2003)."""
    grid = np.unique(np.quantile(p_val, np.linspace(0.5, 0.995, 120)))
    scores = [f1_score(y_val, p_val >= t) for t in grid]
    return float(grid[int(np.argmax(scores))])


def train_all(train: pd.DataFrame, val: pd.DataFrame) -> dict:
    """Fit every model on `train`; calibrate and set thresholds on `val`. Returns name -> (model, threshold)."""
    X, y = train[config.FEATURES], train["y"].to_numpy()
    Xv, yv = val[config.FEATURES], val["y"].to_numpy()
    fitted = {
        "Majority baseline": MajorityBaseline().fit(X, y),
        "Industry rule": IndustryRule().fit(X, y),
        "Logistic regression": Calibrated(logistic_regression().fit(X, y), Xv, yv),
        "Gradient boosting": Calibrated(gradient_boosting().fit(X, y), Xv, yv),
    }
    out = {}
    for name, m in fitted.items():
        p_val = m.predict_proba(Xv)[:, 1]
        # A constant predictor cannot rank loans, so its "flag" rule is: flag nobody.
        thr = choose_threshold(yv, p_val) if np.ptp(p_val) > 0 else 1.01
        out[name] = (m, thr)
    return out
