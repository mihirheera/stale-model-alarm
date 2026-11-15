"""Project-wide settings. Every important research choice lives here so it is easy to find and explain.

If you change a value here, re-run the pipeline: every number in results/ and the dashboard is
regenerated from these settings.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

# Kaggle mirror of the SBA dataset published with Li, Mickel & Taylor (2018).
KAGGLE_DATASET = "mirbektoktogaraev/should-this-loan-be-approved-or-denied"
CSV_NAME = "SBAnational.csv"

# ---------------------------------------------------------------- reproducibility
SEED = 42

# ---------------------------------------------------------------- time design
# SBA fiscal years run 1 October to 30 September (FY2004 = Oct 2003 - Sep 2004).
# Why start in FY2001? Before FY2001 the industry code (NAICS) is missing for 41-57% of loans and the
# urban/rural flag is "undefined" for 62-99%. Recording became consistent from FY2001 (decision D4).
TRAIN_YEARS = range(2001, 2003)        # FY2001-FY2002: the model learns from these loans (81,624 loans)
VALIDATION_YEAR = 2003                 # FY2003: used ONLY to pick the decision threshold and calibrate
REFERENCE_YEARS = range(2001, 2004)    # FY2001-FY2003: the "normal" population the drift detector compares against
TEST_YEARS = range(2004, 2011)         # FY2004-FY2010: each year is tested separately, never trained on

# Outcome maturity. The dataset only contains loans whose outcome was known by the data's end (2014).
# Cohorts approved after this year have too little follow-up for their default rate to be trusted
# (see docs/decision_log.md, decision D3). They are still shown, but flagged "outcome-incomplete".
LAST_MATURE_YEAR = 2007

# ---------------------------------------------------------------- features
# Only information a bank has on the day it approves the loan. See docs/feature_audit.md.
NUMERIC_FEATURES = ["log_amount", "sba_share", "no_emp", "create_job", "retained_job"]
CATEGORICAL_FEATURES = ["new_business", "franchise", "urban_rural", "revline", "lowdoc",
                        "sector", "state", "same_state"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# ---------------------------------------------------------------- drift / alarm
PSI_BINS = 10            # numeric features are cut into 10 bins using reference-period quantiles
PSI_EPSILON = 1e-4       # stops log(0) when a bin is empty in one period

# Two-digit NAICS sector names (U.S. Census Bureau), used only for display.
SECTOR_NAMES = {
    "11": "Agriculture, forestry & fishing", "21": "Mining, oil & gas", "22": "Utilities", "23": "Construction",
    "31": "Manufacturing", "32": "Manufacturing", "33": "Manufacturing", "42": "Wholesale trade",
    "44": "Retail trade", "45": "Retail trade", "48": "Transportation & warehousing",
    "49": "Transportation & warehousing", "51": "Information", "52": "Finance & insurance",
    "53": "Real estate & rental", "54": "Professional, scientific & technical services",
    "55": "Management of companies", "56": "Administrative & support services", "61": "Educational services",
    "62": "Health care & social assistance", "71": "Arts, entertainment & recreation",
    "72": "Accommodation & food services", "81": "Other services", "92": "Public administration",
    "00": "Not recorded",
}
