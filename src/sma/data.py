"""Load the SBA loan file and turn it into a clean table the models can use.

What goes in : the raw SBAnational.csv (899,164 loans, 27 columns).
What comes out: one row per loan with
    - `fy`      approval fiscal year (int)
    - `y`       the target: 1 = charged off (default), 0 = paid in full
    - the application-time features listed in config.FEATURES
    - a few audit-only columns (term, dates) that are NEVER given to the models
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from . import config


def find_csv() -> Path:
    """Return the path to SBAnational.csv.

    Uses the SMA_DATA_PATH environment variable if set, otherwise downloads the public Kaggle copy
    with `kagglehub` (no login needed for this public dataset at the time of writing).
    """
    env = os.environ.get("SMA_DATA_PATH")
    if env:
        return Path(env)
    import kagglehub  # imported here so tests can run without it

    folder = Path(kagglehub.dataset_download(config.KAGGLE_DATASET))
    return folder / config.CSV_NAME


def load_raw(path: Path | None = None) -> pd.DataFrame:
    """Read the CSV exactly as published (all columns as text where ambiguous)."""
    path = path or find_csv()
    return pd.read_csv(path, low_memory=False, dtype={"Zip": str, "NAICS": str, "ApprovalFY": str})


def _money(s: pd.Series) -> pd.Series:
    """'$60,000.00 ' -> 60000.0"""
    return pd.to_numeric(s.astype(str).str.replace(r"[$,\s]", "", regex=True), errors="coerce")


def _date(s: pd.Series) -> pd.Series:
    """'28-Feb-97' -> Timestamp.

    Two-digit years are ambiguous: pandas reads '68' as 2068. The data ends in 2014, so any date
    after 2015 must really be in the 1900s and is moved back 100 years.
    """
    d = pd.to_datetime(s, format="%d-%b-%y", errors="coerce")
    too_late = d.dt.year > 2015
    d.loc[too_late] = d.loc[too_late] - pd.DateOffset(years=100)
    return d


def _yes_no(s: pd.Series) -> pd.Series:
    """Y -> 'Y', N -> 'N', anything else (0, 1, T, C, S, blanks...) -> 'unknown'.

    The paper (Li et al. 2018) says the other codes are data-entry errors, so we do not guess.
    """
    s = s.astype(str).str.strip().str.upper()
    return s.where(s.isin(["Y", "N"]), "unknown")


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Build the analysis table. Every rule here is listed in docs/feature_audit.md."""
    df = pd.DataFrame(index=raw.index)
    df["loan_id"] = raw["LoanNr_ChkDgt"]

    # ---- time
    df["fy"] = pd.to_numeric(raw["ApprovalFY"].str.extract(r"(\d{4})")[0], errors="coerce")
    df["approval_date"] = _date(raw["ApprovalDate"])
    df["disbursement_date"] = _date(raw["DisbursementDate"])
    df["chgoff_date"] = _date(raw["ChgOffDate"])          # audit / label-based monitor only

    # ---- target: 1 = charged off, 0 = paid in full, missing stays missing (never assumed repaid)
    status = raw["MIS_Status"].astype(str).str.strip()
    df["y"] = np.where(status == "CHGOFF", 1.0, np.where(status == "P I F", 0.0, np.nan))

    # ---- application-time features
    amount = _money(raw["GrAppv"])
    df["log_amount"] = np.log1p(amount.clip(lower=0))
    df["sba_share"] = (_money(raw["SBA_Appv"]) / amount.replace(0, np.nan)).clip(0, 1)
    df["no_emp"] = np.log1p(raw["NoEmp"].clip(lower=0))
    df["create_job"] = np.log1p(raw["CreateJob"].clip(lower=0))
    df["retained_job"] = np.log1p(raw["RetainedJob"].clip(lower=0))

    df["new_business"] = raw["NewExist"].map({1.0: "existing", 2.0: "new"}).fillna("unknown")
    df["franchise"] = np.where(raw["FranchiseCode"].isin([0, 1]), "no", "yes")
    df["urban_rural"] = raw["UrbanRural"].map({0: "undefined", 1: "urban", 2: "rural"}).fillna("undefined")
    df["revline"] = _yes_no(raw["RevLineCr"])
    df["lowdoc"] = _yes_no(raw["LowDoc"])
    naics = raw["NAICS"].astype(str).str.strip()
    df["sector"] = np.where(naics.str.len() >= 2, naics.str[:2], "00")
    df["sector"] = df["sector"].replace({"0": "00"})          # NAICS == 0 means "not recorded"
    df["state"] = raw["State"].fillna("unknown")
    df["same_state"] = np.where(raw["State"] == raw["BankState"], "yes", "no")

    # ---- audit-only columns (NOT model features; see feature audit)
    df["term"] = raw["Term"]
    df["amount"] = amount
    df["chgoff_amount"] = _money(raw["ChgOffPrinGr"])
    return df


def analysis_table(df: pd.DataFrame) -> pd.DataFrame:
    """Rows usable for supervised learning: known outcome and a fiscal year from 1990 on.

    Pre-1990 cohorts are tiny (about 2,000 loans a year) and show implausible 40-49% default rates,
    which suggests the old records were kept selectively (decision D2 in docs/decision_log.md).
    """
    return df[df["y"].notna() & (df["fy"] >= 1990)].copy()
