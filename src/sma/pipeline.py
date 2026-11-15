"""Run every experiment end to end and save the results.

Run:  python -m sma.pipeline        (about 5-10 minutes on a laptop CPU)
Writes results/results.json (everything) and results/yearly_table.csv (the main table).

E4  Default model vs. baselines, year by year, with 95% bootstrap intervals
E5  Drift: PSI and adversarial validation, thresholds set only from the reference years
E6  Early-warning test: drift alarm vs. a label-based monitor vs. what actually happened
E7  Robustness: other training windows, recording-sensitive features removed, threshold choices, Term leak
E8  Group check: does the model fail more for some kinds of businesses?
E9  Financial impact: dollar losses the model implied vs. what was actually charged off
E10 Example loans: one real input -> output per year (a missed default and a caught one), chosen by a fixed rule
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from . import config
from .data import analysis_table, clean, load_raw
from .drift import adversarial_auc, psi_all
from .evaluate import bootstrap_ci, metrics
from .models import Calibrated, gradient_boosting, train_all

MAIN = "Gradient boosting"
RATIO_CUTOFF = 1.25        # "deteriorated" if 25%+ more loans defaulted than the model expected...
AUC_DROP = 0.05            # ...or if ranking quality (AUC) fell by 0.05+ from the validation year
INDUSTRY_PSI = 0.25        # common industry heuristic for "large" PSI shift
RECORDING_SENSITIVE = ["revline", "lowdoc", "urban_rural"]   # fields whose coding changed over time

# Official SBA 7(a) approval counts (SBA "Table 3 - Number of Approved Loans by Program", archived at
# webharvest.gov). Includes loans later cancelled, so dividing by it gives a LOWER bound on default rate.
OFFICIAL_APPROVALS = {2007: 99603, 2008: 69441, 2009: 41273, 2010: 46922}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def mature(fy: int) -> bool:
    return fy <= config.LAST_MATURE_YEAR


# ---------------------------------------------------------------- E4
def e4_models(df, models):
    out = {}
    for name, (m, thr) in models.items():
        rows = {}
        for fy in [config.VALIDATION_YEAR, *config.TEST_YEARS]:
            d = df[df.fy == fy]
            p = m.predict_proba(d[config.FEATURES])[:, 1]
            r = metrics(d["y"], p, thr)
            if name in (MAIN, "Logistic regression") and fy != config.VALIDATION_YEAR:
                r["ci"] = bootstrap_ci(d["y"], p, thr)
            rows[fy] = r
        out[name] = {"threshold": thr, "by_year": rows}
        log(f"E4 {name}: done")
    return out


# ---------------------------------------------------------------- E5
def e5_drift(df, features=None, importance=True, seed=config.SEED):
    """Drift of each test year vs. the reference years, plus 'normal' year-to-year drift inside the reference."""
    ref_years = list(config.REFERENCE_YEARS)
    ref = df[df.fy.isin(ref_years)]
    normal = {}
    for r in ref_years:      # leave-one-year-out: how different is a normal year from the other normal years?
        a = adversarial_auc(ref[ref.fy != r], ref[ref.fy == r], features, importance=False, seed=seed)
        p = psi_all(ref[ref.fy != r], ref[ref.fy == r])
        normal[r] = {"adv_auc": a["auc"], "max_psi": max(p.values())}
    test = {}
    for fy in config.TEST_YEARS:
        cur = df[df.fy == fy]
        a = adversarial_auc(ref, cur, features, importance=importance, seed=seed)
        p = psi_all(ref, cur)
        test[fy] = {"adv_auc": a["auc"], "top_features": a.get("top_features", {}),
                    "psi": {k: round(v, 4) for k, v in p.items()}, "max_psi": max(p.values()),
                    "max_psi_feature": max(p, key=p.get)}
    return {"normal_years": normal, "test_years": test,
            "adv_threshold": max(v["adv_auc"] for v in normal.values()),
            "psi_threshold_reference": max(v["max_psi"] for v in normal.values())}


# ---------------------------------------------------------------- label-based monitor (baseline for E6)
def early_default_rate(df, cohort, by_fy_end):
    """Share of a cohort's loans already charged off by 30 Sep of `by_fy_end` (knowable at that date)."""
    d = df[df.fy == cohort]
    cutoff = pd.Timestamp(f"{by_fy_end}-09-30")
    return float(((d.y == 1) & (d.chgoff_date <= cutoff)).mean())


def label_monitor(df, lag=2):
    """At the end of FY t a bank can see which loans approved in FY t-lag have already charged off."""
    ref = {c: early_default_rate(df, c, c + lag) for c in range(1998, 2001)}   # known before FY2003 ends
    thr = max(ref.values())
    test = {t: early_default_rate(df, t - lag, t) for t in config.TEST_YEARS}
    return {"lag_years": lag, "reference_cohorts": ref, "threshold": thr,
            "by_monitor_year": {t: {"cohort_checked": t - lag, "early_default_rate": v, "alarm": v > thr}
                                for t, v in test.items()}}


# ---------------------------------------------------------------- E6
def e6_early_warning(e4, e5, labmon):
    main = e4[MAIN]["by_year"]
    val_auc = main[config.VALIDATION_YEAR]["auc"]
    table = []
    for fy in config.TEST_YEARS:
        m, d = main[fy], e5["test_years"][fy]
        drift_alarm = d["adv_auc"] > e5["adv_threshold"]
        psi_alarm = d["max_psi"] > INDUSTRY_PSI
        if mature(fy):
            deteriorated = bool(m["calib_ratio"] > RATIO_CUTOFF or m["auc"] < val_auc - AUC_DROP)
            status = ("Drift detected, performance has deteriorated" if drift_alarm and deteriorated else
                      "Drift detected, performance appears stable" if drift_alarm else
                      "Performance deteriorated without a drift alarm" if deteriorated else
                      "No substantial drift detected")
        else:
            deteriorated = None
            status = "Insufficient evidence to assess performance" + (" (drift detected)" if drift_alarm else "")
        lb = OFFICIAL_APPROVALS.get(fy)
        table.append({
            "fy": fy, "outcome_mature": mature(fy), "n": m["n"],
            "actual_rate": m["actual_rate"], "predicted_rate": m["predicted_rate"],
            "calib_ratio": m["calib_ratio"], "auc": m["auc"], "precision": m["precision"],
            "recall": m["recall"], "brier": m["brier"],
            "max_psi": d["max_psi"], "max_psi_feature": d["max_psi_feature"], "adv_auc": d["adv_auc"],
            "drift_alarm": drift_alarm, "psi_alarm_0.25": psi_alarm,
            "label_monitor_alarm": labmon["by_monitor_year"][fy]["alarm"],
            "deteriorated": deteriorated, "status": status,
            "actual_rate_lower_bound": (m["actual_rate"] * m["n"] / lb) if lb else None,
        })
    first = lambda key: next((r["fy"] for r in table if r[key]), None)
    summary = {
        "first_drift_alarm": first("drift_alarm"), "first_psi_alarm": first("psi_alarm_0.25"),
        "first_label_monitor_alarm": first("label_monitor_alarm"),
        "first_deteriorated_cohort": first("deteriorated"),
        "mature_years": [r["fy"] for r in table if r["outcome_mature"]],
        "hits": sum(1 for r in table if r["outcome_mature"] and r["drift_alarm"] and r["deteriorated"]),
        "false_alarms": sum(1 for r in table if r["outcome_mature"] and r["drift_alarm"] and not r["deteriorated"]),
        "misses": sum(1 for r in table if r["outcome_mature"] and not r["drift_alarm"] and r["deteriorated"]),
        "validation_auc": val_auc,
    }
    # False alarms inside the reference period: each normal year judged against the other two.
    normal = e5["normal_years"]
    summary["reference_false_alarms"] = sum(
        1 for r, v in normal.items() if v["adv_auc"] > max(w["adv_auc"] for q, w in normal.items() if q != r))
    return {"table": table, "summary": summary}


# ---------------------------------------------------------------- E7
def e7_robustness(df, e4, e5, e6):
    out = {}
    # (a) drift without recording-sensitive fields
    feats = [f for f in config.FEATURES if f not in RECORDING_SENSITIVE]
    a = e5_drift(df, features=feats, importance=False)
    out["drift_without_recording_sensitive"] = {
        "features_removed": RECORDING_SENSITIVE, "threshold": a["adv_threshold"],
        "adv_auc": {fy: v["adv_auc"] for fy, v in a["test_years"].items()},
        "alarms": {fy: v["adv_auc"] > a["adv_threshold"] for fy, v in a["test_years"].items()}}
    log("E7a done")
    # (b) other training windows (gradient boosting only)
    windows = {"train FY2002 only": range(2002, 2003), "train FY1999-2002 (incl. poorly recorded years)": range(1999, 2003)}
    val = df[df.fy == config.VALIDATION_YEAR]
    out["training_windows"] = {}
    for label, yrs in windows.items():
        tr = df[df.fy.isin(yrs)]
        m = Calibrated(gradient_boosting().fit(tr[config.FEATURES], tr["y"]), val[config.FEATURES], val["y"])
        res = {}
        for fy in range(2004, 2008):
            d = df[df.fy == fy]
            p = m.predict_proba(d[config.FEATURES])[:, 1]
            r = metrics(d["y"], p, 0.5)
            res[fy] = {"auc": r["auc"], "calib_ratio": r["calib_ratio"], "predicted_rate": r["predicted_rate"]}
        out["training_windows"][label] = res
    log("E7b done")
    # (c) threshold sensitivity
    tab = e6["table"]
    out["thresholds"] = {
        "deterioration_ratio": {str(c): [r["fy"] for r in tab if r["outcome_mature"] and r["calib_ratio"] > c]
                                for c in (1.1, 1.25, 1.5, 2.0)},
        "drift_margin": {str(mg): [r["fy"] for r in tab if r["adv_auc"] > e5["adv_threshold"] + mg]
                         for mg in (0.0, 0.02, 0.05, 0.1)},
        "industry_psi": {str(c): [r["fy"] for r in tab if r["max_psi"] > c] for c in (0.1, 0.2, 0.25)},
    }
    # (d) leakage demonstration: add Term back
    tr = df[df.fy.isin(config.TRAIN_YEARS)]
    feats_t = config.FEATURES + ["term"]
    from sklearn.ensemble import HistGradientBoostingClassifier
    Xtr = tr[feats_t].copy()
    for f in config.CATEGORICAL_FEATURES:
        Xtr[f] = Xtr[f].astype("category")
    clf = HistGradientBoostingClassifier(max_iter=300, categorical_features="from_dtype",
                                         random_state=config.SEED).fit(Xtr, tr["y"])
    leak = {}
    for fy in range(2004, 2008):
        d = df[df.fy == fy][feats_t].copy()
        for f in config.CATEGORICAL_FEATURES:
            d[f] = pd.Categorical(d[f], categories=Xtr[f].cat.categories)
        from sklearn.metrics import roc_auc_score
        leak[fy] = {"auc_with_term": float(roc_auc_score(df[df.fy == fy]["y"], clf.predict_proba(d)[:, 1])),
                    "auc_without_term": e4[MAIN]["by_year"][fy]["auc"]}
    out["term_leak_demo"] = leak
    log("E7d done")
    # (e) drift seeds
    out["drift_seed_spread"] = {}
    for fy in range(2004, 2008):
        ref = df[df.fy.isin(config.REFERENCE_YEARS)]
        vals = [adversarial_auc(ref, df[df.fy == fy], importance=False, seed=s)["auc"] for s in (1, 2, 3)]
        out["drift_seed_spread"][fy] = {"min": min(vals), "max": max(vals)}
    log("E7e done")
    return out


# ---------------------------------------------------------------- E8
def e8_groups(df, models):
    m, thr = models[MAIN]
    d = df[df.fy.between(2004, config.LAST_MATURE_YEAR)].copy()
    d["p"] = m.predict_proba(d[config.FEATURES])[:, 1]
    top_sectors = d["sector"].value_counts().head(6).index
    top_states = d["state"].value_counts().head(6).index
    groupings = {
        "Business age": d["new_business"],
        "Location type": d["urban_rural"],
        "Franchise": d["franchise"],
        "Industry (largest 6)": d["sector"].where(d["sector"].isin(top_sectors)),
        "State (largest 6)": d["state"].where(d["state"].isin(top_states)),
    }
    out = {}
    for gname, col in groupings.items():
        rows = {}
        for val, g in d.groupby(col):
            if len(g) < 500:
                continue
            r = metrics(g["y"], g["p"], thr)
            rows[str(val)] = {k: r[k] for k in ("n", "actual_rate", "predicted_rate", "calib_ratio", "auc", "recall")}
        out[gname] = rows
    return out


# ---------------------------------------------------------------- E9
def e9_financial_impact(df, models):
    """Dollars: the losses the model's probabilities implied vs. what was actually charged off.

    implied loss = sum over loans of P(default) x loan amount x loss-given-default, where loss-given-default
    (share of a defaulted loan's amount that is charged off) is measured on the TRAINING years only.
    The lender's own share is approximated as (1 - SBA guarantee share) of each loss.
    """
    m, _ = models[MAIN]
    tr = df[df.fy.isin(config.TRAIN_YEARS)]
    d1 = tr[tr.y == 1]
    lgd = float(d1.chgoff_amount.fillna(0).sum() / d1.amount.sum())
    out = {"loss_given_default_train": lgd, "by_year": {}}
    for fy in [config.VALIDATION_YEAR, *config.TEST_YEARS]:
        d = df[df.fy == fy]
        p = m.predict_proba(d[config.FEATURES])[:, 1]
        own = 1 - d.sba_share.fillna(0)
        actual = d.chgoff_amount.fillna(0).where(d.y == 1, 0)
        implied = p * d.amount * lgd
        out["by_year"][fy] = {
            "outcome_mature": mature(fy), "lent": float(d.amount.sum()),
            "implied_loss": float(implied.sum()), "actual_loss": float(actual.sum()),
            "implied_lender_loss": float((implied * own).sum()), "actual_lender_loss": float((actual * own).sum()),
        }
        r = out["by_year"][fy]
        r["loss_ratio"] = r["actual_loss"] / r["implied_loss"]
        r["unexpected_loss"] = r["actual_loss"] - r["implied_loss"]
        r["unexpected_lender_loss"] = r["actual_lender_loss"] - r["implied_lender_loss"]
    judged = [out["by_year"][fy] for fy in range(2004, config.LAST_MATURE_YEAR + 1)]
    out["judged_total"] = {k: sum(r[k] for r in judged) for k in
                           ("lent", "implied_loss", "actual_loss", "implied_lender_loss", "actual_lender_loss")}
    return out


# ---------------------------------------------------------------- E10
EXAMPLE_FIELDS = ["amount", "sba_share", "no_emp", "new_business", "franchise", "urban_rural", "revline",
                  "lowdoc", "sector", "state", "same_state", "create_job", "retained_job"]


def e10_examples(df, models):
    """One real input -> output per year, chosen by a fixed rule (no hand-picking):
    the defaulted loan the model MISSED and the defaulted loan it CAUGHT whose predicted risk is closest to the
    median of that group. Business names, IDs, cities and banks are never included.
    For the missed loan we also compare loans with the same SBA guarantee share in training vs. this year."""
    m, thr = models[MAIN]
    train = df[df.fy.isin(config.TRAIN_YEARS)]
    out = {"threshold": thr, "by_year": {}}
    for fy in config.TEST_YEARS:
        d = df[df.fy == fy].copy()
        d["p"] = m.predict_proba(d[config.FEATURES])[:, 1]
        picks = {}
        for kind, mask in {"missed_default": (d.y == 1) & (d.p < thr),
                           "caught_default": (d.y == 1) & (d.p >= thr)}.items():
            g = d[mask]
            if g.empty:
                continue
            row = g.iloc[int(np.argsort((g.p - g.p.median()).abs().to_numpy(), kind="stable")[0])]
            ex = {f: (row[f].item() if hasattr(row[f], "item") else row[f]) for f in EXAMPLE_FIELDS}
            for f in ("no_emp", "create_job", "retained_job"):      # stored as log(1 + count); show the count
                ex[f] = int(round(np.expm1(ex[f])))
            ex.update(predicted_risk=float(row.p), defaulted=bool(row.y == 1), group_size=int(len(g)))
            if kind == "missed_default":
                same = lambda x: (x.sba_share - row.sba_share).abs() < 0.005
                ex["same_guarantee"] = {
                    "train_share_of_loans": float(same(train).mean()), "train_default_rate": float(train[same(train)].y.mean()),
                    "year_share_of_loans": float(same(d).mean()), "year_default_rate": float(d[same(d)].y.mean()),
                    "year_model_expected": float(d[same(d)].p.mean()),
                    "share_of_missed_defaults": float(same(g).mean())}
            picks[kind] = ex
        # The pattern behind the misses: which guarantee shares do the missed defaults have?
        missed = d[(d.y == 1) & (d.p < thr)]
        top = missed.sba_share.round(2).value_counts(normalize=True).head(3)
        picks["missed_by_guarantee"] = {
            f"{s:.2f}": {"share_of_missed_defaults": float(v),
                         "train_default_rate": float(train[train.sba_share.round(2) == s].y.mean()),
                         "train_share_of_loans": float((train.sba_share.round(2) == s).mean()),
                         "year_default_rate": float(d[d.sba_share.round(2) == s].y.mean()),
                         "year_model_expected": float(d[d.sba_share.round(2) == s].p.mean()),
                         "year_share_of_loans": float((d.sba_share.round(2) == s).mean())}
            for s, v in top.items()}
        picks["n_defaults"] = int((d.y == 1).sum())
        picks["n_missed"] = int(len(missed))
        out["by_year"][fy] = picks
    return out


def main():
    log("loading data")
    df = analysis_table(clean(load_raw()))
    train = df[df.fy.isin(config.TRAIN_YEARS)]
    val = df[df.fy == config.VALIDATION_YEAR]
    log(f"train n={len(train)} (rate {train.y.mean():.3f}), validation n={len(val)} (rate {val.y.mean():.3f})")
    models = train_all(train, val)
    e4 = e4_models(df, models)
    e5 = e5_drift(df)
    log("E5 done")
    labmon = {"lag2": label_monitor(df, 2), "lag3": label_monitor(df, 3)}
    e6 = e6_early_warning(e4, e5, labmon["lag2"])
    log("E6 done")
    e7 = e7_robustness(df, e4, e5, e6)
    e8 = e8_groups(df, models)
    log("E8 done")
    e9 = e9_financial_impact(df, models)
    e10 = e10_examples(df, models)
    log("E9, E10 done")
    res = {"config": {"train_years": list(config.TRAIN_YEARS), "validation_year": config.VALIDATION_YEAR,
                      "reference_years": list(config.REFERENCE_YEARS), "test_years": list(config.TEST_YEARS),
                      "last_mature_year": config.LAST_MATURE_YEAR, "features": config.FEATURES,
                      "ratio_cutoff": RATIO_CUTOFF, "auc_drop": AUC_DROP, "industry_psi": INDUSTRY_PSI,
                      "n_train": int(len(train)), "n_validation": int(len(val)),
                      "train_default_rate": float(train.y.mean())},
           "E4_models": e4, "E5_drift": e5, "label_monitor": labmon, "E6_early_warning": e6,
           "E7_robustness": e7, "E8_groups": e8, "E9_financial_impact": e9, "E10_examples": e10}
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.RESULTS_DIR / "results.json").write_text(json.dumps(res, indent=2, default=lambda o: o if not isinstance(o, (np.generic,)) else o.item()))
    pd.DataFrame(e6["table"]).to_csv(config.RESULTS_DIR / "yearly_table.csv", index=False)
    log("saved results/results.json and results/yearly_table.csv")


if __name__ == "__main__":
    main()
