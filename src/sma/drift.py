"""AI model #2 and its baseline: is this year's group of borrowers different from the training group?

Neither method ever looks at whether loans defaulted. They only compare application details.

PSI (Population Stability Index) - the banking industry's standard check, one feature at a time.
    Split a feature into bins, compare the share of loans in each bin now vs. in the reference period.
    PSI = sum over bins of (now% - ref%) * ln(now% / ref%).  0 = identical.
    Rules of thumb used in industry (heuristics, not laws): < 0.10 small, 0.10-0.25 moderate, > 0.25 large.

Adversarial validation - a machine-learning classifier looks at ALL features together.
    It is shown a mix of reference-period applications (label 0) and this year's applications (label 1)
    and must guess which is which. If it can't (AUC about 0.5) the populations look the same. If it can
    easily (AUC near 1), this year's borrowers look unlike anything the risk model learned from.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from . import config


# ---------------------------------------------------------------- PSI
def psi_numeric(ref: pd.Series, cur: pd.Series, bins: int = config.PSI_BINS) -> float:
    """Bins are deciles of the REFERENCE data, so the reference has ~10% of loans in each bin."""
    edges = np.unique(np.nanquantile(ref.dropna(), np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    r = pd.cut(ref, edges).value_counts(normalize=True, sort=False).to_numpy()
    c = pd.cut(cur, edges).value_counts(normalize=True, sort=False).to_numpy()
    return _psi(r, c)


def psi_categorical(ref: pd.Series, cur: pd.Series) -> float:
    """Each category is a bin. Categories never seen in the reference share one 'new' bin."""
    cats = list(ref.astype(str).unique())
    r = ref.astype(str).value_counts(normalize=True).reindex(cats).fillna(0).to_numpy()
    cur = cur.astype(str)
    c = cur.value_counts(normalize=True).reindex(cats).fillna(0).to_numpy()
    new_share = float((~cur.isin(cats)).mean())
    return _psi(np.append(r, 0.0), np.append(c, new_share))


def _psi(r: np.ndarray, c: np.ndarray) -> float:
    """Empty bins get a tiny share (epsilon) so log(0) never happens."""
    r = np.clip(r, config.PSI_EPSILON, None)
    c = np.clip(c, config.PSI_EPSILON, None)
    return float(np.sum((c - r) * np.log(c / r)))


def psi_all(ref: pd.DataFrame, cur: pd.DataFrame) -> dict:
    out = {f: psi_numeric(ref[f], cur[f]) for f in config.NUMERIC_FEATURES}
    out.update({f: psi_categorical(ref[f], cur[f]) for f in config.CATEGORICAL_FEATURES})
    return out


# ---------------------------------------------------------------- adversarial validation
def adversarial_auc(ref: pd.DataFrame, cur: pd.DataFrame, features=None, n_per_side: int = 15000,
                    importance: bool = True, seed: int = config.SEED) -> dict:
    """Train a classifier to tell `ref` rows from `cur` rows; report held-out AUC + top features.

    Equal sample sizes from both sides mean a coin-flip guess scores exactly AUC 0.5 (the baseline).
    """
    features = list(features or config.FEATURES)
    n = min(n_per_side, len(ref), len(cur))
    a = ref.sample(n, random_state=seed)[features].assign(_t=0)
    b = cur.sample(n, random_state=seed)[features].assign(_t=1)
    d = pd.concat([a, b], ignore_index=True)
    cats = [f for f in features if f in config.CATEGORICAL_FEATURES]
    for f in cats:
        d[f] = d[f].astype("category")
    X, y = d[features], d["_t"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.4, stratify=y, random_state=seed)
    clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, categorical_features="from_dtype",
                                         random_state=seed).fit(Xtr, ytr)
    auc = float(roc_auc_score(yte, clf.predict_proba(Xte)[:, 1]))
    out = {"auc": auc, "n_per_side": int(n)}
    if importance:
        pi = permutation_importance(clf, Xte, yte, scoring="roc_auc", n_repeats=3, random_state=seed)
        imp = pd.Series(pi.importances_mean, index=features).sort_values(ascending=False)
        out["top_features"] = {k: round(float(v), 4) for k, v in imp.head(5).items()}
    return out
