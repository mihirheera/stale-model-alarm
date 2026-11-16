"""Measure how well a model did on one group of loans, with bootstrap confidence intervals.

Plain-English meaning of each metric (see docs/technical_guide.md for more):
  auc            : if you pick one defaulted and one repaid loan at random, how often does the model give
                   the defaulted one the higher risk? 0.5 = coin flip, 1.0 = perfect ranking.
  pr_auc         : like AUC but focused on finding defaults; compare to the default rate (its chance level).
  precision      : of the loans the model flagged, the share that defaulted.
  recall         : of the loans that defaulted, the share the model flagged.
  f1             : one number balancing precision and recall.
  brier          : average squared gap between predicted probability and what happened (lower = better).
  predicted_rate : the average predicted default probability = how many defaults the model expects.
  actual_rate    : the share that defaulted.
  calib_ratio    : actual_rate / predicted_rate. 1.0 = the model expected the right number of defaults.
                   2.0 = twice as many loans defaulted as the model expected.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)

from . import config


def metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    flag = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, flag, labels=[0, 1]).ravel()
    ranks = np.ptp(p) > 0
    return {
        "n": int(len(y)),
        "actual_rate": float(y.mean()),
        "predicted_rate": float(p.mean()),
        "calib_ratio": float(y.mean() / p.mean()) if p.mean() > 0 else float("nan"),
        "auc": float(roc_auc_score(y, p)) if ranks else 0.5,
        "pr_auc": float(average_precision_score(y, p)) if ranks else float(y.mean()),
        "precision": float(precision_score(y, flag, zero_division=0)),
        "recall": float(recall_score(y, flag, zero_division=0)),
        "f1": float(f1_score(y, flag, zero_division=0)),
        "brier": float(brier_score_loss(y, p)),
        "flagged_rate": float(flag.mean()),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def bootstrap_ci(y, p, threshold, keys=("auc", "brier", "recall", "precision", "calib_ratio"),
                 n_boot: int = 200, seed: int = config.SEED) -> dict:
    """Resample the loans with replacement 200 times; the middle 95% of results is the interval."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    vals = {k: [] for k in keys}
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        m = metrics(y[i], p[i], threshold)
        for k in keys:
            vals[k].append(m[k])
    return {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] for k, v in vals.items()}
