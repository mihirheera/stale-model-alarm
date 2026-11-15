"""Checks on the calculations everything else depends on. Run:  pytest -q   (from the project root)"""
import numpy as np
import pandas as pd
import pytest

from sma import config
from sma.data import _date, _money, _yes_no, clean
from sma.drift import adversarial_auc, psi_categorical, psi_numeric
from sma.evaluate import metrics


# ---------------------------------------------------------------- leakage guards
def test_no_outcome_or_term_columns_are_features():
    forbidden = {"y", "term", "chgoff_date", "chgoff_amount", "fy", "approval_date", "disbursement_date", "amount"}
    assert forbidden.isdisjoint(config.FEATURES)


def test_test_years_never_overlap_training_or_calibration():
    assert set(config.TEST_YEARS).isdisjoint(config.TRAIN_YEARS)
    assert config.VALIDATION_YEAR not in config.TEST_YEARS
    assert max(config.REFERENCE_YEARS) < min(config.TEST_YEARS)


# ---------------------------------------------------------------- cleaning
def test_money_parsing():
    assert _money(pd.Series(["$60,000.00 ", "$0.00"])).tolist() == [60000.0, 0.0]


def test_two_digit_year_fix():
    d = _date(pd.Series(["15-Mar-68", "01-Jan-04"]))
    assert d.dt.year.tolist() == [1968, 2004]


def test_yes_no_unknown():
    assert _yes_no(pd.Series(["Y", "N", "0", "T", None])).tolist() == ["Y", "N", "unknown", "unknown", "unknown"]


def _raw(status):
    return pd.DataFrame({
        "LoanNr_ChkDgt": [1, 2, 3], "ApprovalFY": ["2004", "2005", "2006"],
        "ApprovalDate": ["01-Jan-04"] * 3, "DisbursementDate": ["01-Feb-04"] * 3, "ChgOffDate": [None] * 3,
        "MIS_Status": status, "GrAppv": ["$100.00"] * 3, "SBA_Appv": ["$50.00"] * 3, "NoEmp": [1, 2, 3],
        "CreateJob": [0, 0, 0], "RetainedJob": [0, 0, 0], "NewExist": [1.0, 2.0, np.nan],
        "FranchiseCode": [0, 1, 5], "UrbanRural": [0, 1, 2], "RevLineCr": ["Y", "N", "T"],
        "LowDoc": ["N", "Y", "C"], "NAICS": ["722110", "0", "54"], "State": ["CA", "TX", "NY"],
        "BankState": ["CA", "CA", "NY"], "Term": [84, 60, 240], "ChgOffPrinGr": ["$0.00"] * 3,
    })


def test_missing_outcome_is_never_treated_as_repaid():
    df = clean(_raw(["CHGOFF", "P I F", np.nan]))
    assert df["y"].iloc[0] == 1 and df["y"].iloc[1] == 0 and np.isnan(df["y"].iloc[2])


def test_feature_values():
    df = clean(_raw(["CHGOFF", "P I F", "P I F"]))
    assert df["sector"].tolist() == ["72", "00", "54"]
    assert df["franchise"].tolist() == ["no", "no", "yes"]
    assert df["new_business"].tolist() == ["existing", "new", "unknown"]
    assert df["sba_share"].tolist() == [0.5, 0.5, 0.5]


# ---------------------------------------------------------------- drift
def test_psi_identical_is_zero_and_shift_is_positive():
    rng = np.random.default_rng(0)
    a = pd.Series(rng.normal(size=20000))
    assert psi_numeric(a, a) == pytest.approx(0, abs=1e-9)
    assert psi_numeric(a, a + 1.0) > 0.25


def test_psi_categorical_handles_new_category():
    ref = pd.Series(["a"] * 50 + ["b"] * 50)
    assert psi_categorical(ref, ref) == pytest.approx(0, abs=1e-9)
    assert psi_categorical(ref, pd.Series(["a"] * 50 + ["c"] * 50)) > 1


def test_adversarial_auc_near_half_for_same_population():
    rng = np.random.default_rng(1)
    n = 4000
    df = pd.DataFrame({f: rng.normal(size=n) for f in config.NUMERIC_FEATURES})
    for f in config.CATEGORICAL_FEATURES:
        df[f] = rng.choice(["x", "y"], size=n)
    res = adversarial_auc(df.iloc[:2000], df.iloc[2000:], importance=False)
    assert 0.4 < res["auc"] < 0.6


# ---------------------------------------------------------------- metrics
def test_metrics_basic():
    m = metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]), 0.5)
    assert m["auc"] == 1.0 and m["recall"] == 1.0 and m["precision"] == 1.0
    assert m["calib_ratio"] == pytest.approx(0.5 / 0.5)


# ---------------------------------------------------------------- financial impact and examples
class _ConstantModel:
    def __init__(self, p):
        self.p = p

    def predict_proba(self, X):
        p = np.full(len(X), self.p)
        return np.column_stack([1 - p, p])


def _toy_years():
    """Two loans per year, FY2001-2010: one repaid, one defaulted with half its $100 charged off."""
    rows = []
    for fy in range(2001, 2011):
        for y in (0, 1):
            rows.append({"fy": fy, "y": y, "amount": 100.0, "chgoff_amount": 50.0 * y, "log_amount": np.log1p(100),
                         "sba_share": 0.5, "no_emp": np.log1p(3), "create_job": 0.0, "retained_job": np.log1p(2),
                         "new_business": "existing", "franchise": "no", "urban_rural": "urban", "revline": "N",
                         "lowdoc": "N", "sector": "72", "state": "CA", "same_state": "yes"})
    return pd.DataFrame(rows)


def test_financial_impact_math():
    from sma.pipeline import MAIN, e9_financial_impact
    res = e9_financial_impact(_toy_years(), {MAIN: (_ConstantModel(0.1), 0.5)})
    assert res["loss_given_default_train"] == pytest.approx(0.5)          # $50 charged off / $100 lent
    r = res["by_year"][2004]
    assert r["implied_loss"] == pytest.approx(2 * 0.1 * 100 * 0.5)         # sum of P(default) x amount x LGD
    assert r["actual_loss"] == pytest.approx(50)
    assert r["actual_lender_loss"] == pytest.approx(25)                    # lender keeps the unguaranteed half


def test_examples_contain_no_identifiers_and_show_real_counts():
    from sma.pipeline import EXAMPLE_FIELDS, MAIN, e10_examples
    assert {"name", "city", "zip", "bank", "loan_nr", "chgoff_amount", "term"}.isdisjoint(EXAMPLE_FIELDS)
    res = e10_examples(_toy_years(), {MAIN: (_ConstantModel(0.1), 0.5)})   # 0.1 < 0.5, so every default is missed
    ex = res["by_year"][2004]["missed_default"]
    assert ex["defaulted"] and ex["no_emp"] == 3 and ex["retained_job"] == 2
    assert "caught_default" not in res["by_year"][2004]
