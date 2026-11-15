"""Experiments E1-E3: check the data before trusting any model built on it.

Run:  python -m sma.audit
Writes results/audit.json and prints a readable summary.

E1  Data validation  - duplicates, missing outcomes, fiscal-year definition, end of data, cohort sizes.
E2  Term audit       - is `Term` a contract fact known at approval, or was it changed after the outcome?
E3  Outcome maturity - how long after approval do defaults appear, and which cohorts are mature?
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import config
from .data import clean, load_raw


def e1_validation(raw: pd.DataFrame, df: pd.DataFrame) -> dict:
    out = {
        "raw_rows": int(len(raw)),
        "raw_columns": int(raw.shape[1]),
        "duplicate_loan_ids": int(raw["LoanNr_ChkDgt"].duplicated().sum()),
        "mis_status_counts": raw["MIS_Status"].fillna("MISSING").value_counts().to_dict(),
        "rows_missing_fy": int(df["fy"].isna().sum()),
        "max_approval_date": str(df["approval_date"].max().date()),
        "max_disbursement_date": str(df["disbursement_date"].max().date()),
        "max_chgoff_date": str(df["chgoff_date"].max().date()),
    }
    # Fiscal-year check: US federal FY N runs Oct (N-1) to Sep N.
    d = df.dropna(subset=["approval_date", "fy"])
    d = d[d["approval_date"].dt.year.between(1995, 2013)]
    expected = d["approval_date"].dt.year + (d["approval_date"].dt.month >= 10).astype(int)
    out["fy_matches_oct_sep_rule_share"] = float((expected == d["fy"]).mean())
    # Charge-off date present for paid-in-full loans? (should be rare if labels are consistent)
    out["pif_with_chgoff_date"] = int(((df["y"] == 0) & df["chgoff_date"].notna()).sum())
    out["chgoff_without_chgoff_date"] = int(((df["y"] == 1) & df["chgoff_date"].isna()).sum())
    return out


def cohort_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per approval fiscal year: size, default rate and data-quality shares."""
    d = df[df["fy"].between(1985, 2014)]
    g = d.groupby("fy")
    t = pd.DataFrame({
        "loans_with_outcome": g["y"].count(),
        "loans_missing_outcome": g["y"].apply(lambda s: int(s.isna().sum())),
        "default_rate": g["y"].mean(),
        "share_term_ge_240": g["term"].apply(lambda s: float((s >= 240).mean())),
        "share_naics_unknown": g["sector"].apply(lambda s: float((s == "00").mean())),
        "share_urban_rural_undefined": g["urban_rural"].apply(lambda s: float((s == "undefined").mean())),
        "share_revline_unknown": g["revline"].apply(lambda s: float((s == "unknown").mean())),
        "share_lowdoc_yes": g["lowdoc"].apply(lambda s: float((s == "Y").mean())),
    })
    return t.round(4)


def e2_term_audit(df: pd.DataFrame) -> dict:
    """If Term is a contract fact set at approval, two loans with terms of 83 and 84 months should have
    similar default rates. If odd terms default far more often than round ones *within the same range*,
    Term was probably rewritten after the loan got into trouble (e.g. on restructuring or charge-off)."""
    # Use only old, fully mature cohorts so missing (unresolved) loans cannot explain the pattern.
    m = df[df["fy"].between(1990, 2000) & df["y"].notna() & df["term"].between(1, 239)].copy()
    m["round_term"] = (m["term"] % 12 == 0)
    buckets = pd.cut(m["term"], [0, 36, 60, 84, 120, 239])
    by = m.groupby([buckets, "round_term"], observed=True)["y"].agg(["size", "mean"]).round(3)
    by.index = [f"{b} | {'round (x12)' if r else 'odd'}" for b, r in by.index]

    # Do charged-off loans have a Term that matches how long they actually ran before charge-off?
    c = m[(m["y"] == 1) & m["chgoff_date"].notna() & m["disbursement_date"].notna()].copy()
    months_run = (c["chgoff_date"] - c["disbursement_date"]).dt.days / 30.44
    return {
        "cohorts_used": "FY1990-FY2000, terms 1-239 months",
        "n_loans": int(len(m)),
        "default_rate_round_terms": float(m.loc[m.round_term, "y"].mean()),
        "default_rate_odd_terms": float(m.loc[~m.round_term, "y"].mean()),
        "share_of_loans_with_odd_terms": float((~m.round_term).mean()),
        "by_bucket": {k: {"n": int(v["size"]), "default_rate": float(v["mean"])} for k, v in by.iterrows()},
        "default_rate_term_exactly_84": float(m.loc[m.term == 84, "y"].mean()),
        "default_rate_term_83": float(m.loc[m.term == 83, "y"].mean()) if (m.term == 83).any() else None,
        "n_term_83": int((m.term == 83).sum()),
        "chargeoffs_where_term_within_3m_of_months_run": float(((c["term"] - months_run).abs() <= 3).mean()),
        "corr_term_vs_months_run_chargeoffs": float(np.corrcoef(c["term"], months_run)[0, 1]),
    }


def e3_maturity(df: pd.DataFrame) -> dict:
    """How long after disbursement do charge-offs happen? Measured on mature cohorts (FY1995-2000)."""
    c = df[df["fy"].between(1995, 2000) & (df["y"] == 1)].dropna(subset=["chgoff_date", "disbursement_date"])
    years = (c["chgoff_date"] - c["disbursement_date"]).dt.days / 365.25
    years = years[years >= 0]
    qs = {f"p{int(q * 100)}": round(float(years.quantile(q)), 2) for q in (0.25, 0.5, 0.75, 0.8, 0.9)}
    within = {f"within_{k}y": round(float((years <= k).mean()), 3) for k in (1, 2, 3, 4, 5, 7)}
    return {"cohorts_used": "FY1995-FY2000 charge-offs", "n": int(len(years)),
            "years_from_disbursement_to_chargeoff": qs, "share_of_chargeoffs": within}


def main() -> None:
    raw = load_raw()
    df = clean(raw)
    res = {"E1_validation": e1_validation(raw, df), "E2_term_audit": e2_term_audit(df),
           "E3_maturity": e3_maturity(df)}
    cohorts = cohort_table(df)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cohorts.to_csv(config.RESULTS_DIR / "cohorts.csv")
    (config.RESULTS_DIR / "audit.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(res, indent=2, default=str))
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(cohorts)


if __name__ == "__main__":
    main()
