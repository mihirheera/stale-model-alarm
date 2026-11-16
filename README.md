# Stale Model Alarm

**Track:** Finance
**Team:** Mihir Heera

> This project is a prototype and is not financial advice.

**[Demo video (2 min)](https://youtu.be/Q_YpQ6imcLw)** · **[Live dashboard](https://mihirheera.github.io/stale-model-alarm/dashboard/index.html)** · [Full write-up](docs/full_writeup.md) (every detail, reproduction steps) · [FAQ](docs/faq.md)

**Main takeaway:** in a historical test on SBA small-business loans, a credit-risk model kept *ranking* borrowers
better than simple rules while badly *under-estimating* how many would default. A second model, reading only
application forms, flagged the same years without any repayment data. It was not earlier than a simple default count.

## The problem
A community bank's credit-risk analyst relies on a model trained on past loans, but whether a loan defaults is known
only years later. The model can go out of date while the bank still trusts it. In my test years (FY2004–07), the
model's probabilities implied about **$2.8B** of charge-offs; **$5.7B** of principal was recorded as charged off
(gross figures, before recoveries and shared with the SBA guarantee, so not final losses).

## What I built
A model-review aid for that analyst. It is a retrospective prototype, not a deployed bank system.
- **In:** a year's loan applications (amount, SBA guarantee share, employees, industry, state, ...).
- **Out:** a default probability for each loan (Model 1), and a yearly **drift status** (Model 2): do applicants still
  resemble the ones Model 1 was built from, and what changed?
- **[Dashboard](https://mihirheera.github.io/stale-model-alarm/dashboard/index.html):** replays FY2004–2010 one year at
  a time with the status, the evidence behind it, real example loans and suggested analyst actions.
- It never approves or rejects a loan. It gives a person a reason to review the model.

## What I added
My own idea; not one of the suggested projects.
- **Question:** can a model's owner tell it is going stale *without waiting for loans to fail*?
- **Two models:** a second classifier monitors the first, using application details only.
- **Two kinds of baseline, tested chronologically:** prediction baselines for Model 1 (average rate, industry lookup)
  and monitoring baselines for Model 2 (PSI, a simple count of early defaults).
- **A suspicious data field found and excluded** (loan term; below).

## How it works
**Data.** 899,164 SBA 7(a) loans (Li, Mickel & Taylor 2018, CC BY 4.0). Target: charged off (1) vs. paid in full (0).
Only details known on approval day are used ([feature audit](docs/feature_audit.md)). Data problems handled:
- **Loan term:** round terms (multiples of 12 months) defaulted 0.8%, odd terms 29.6%. The mechanism is unproven, so
  this is suspected outcome contamination, not proven leakage; the field is excluded as a precaution. With it, AUC
  would be about 0.96.
- **Incomplete outcomes:** the file keeps only loans resolved by 2014, so later years over-state default rates. Only
  FY2004–07 are judged.
- **Recording changes:** industry codes are missing for about half of loans before FY2001, so nothing earlier is used.

**Model 1 (default risk).** Gradient boosting on 13 application details, trained on FY2001–02 (81,624 loans),
calibrated on FY2003, tested on FY2004–10. *Why:* a strong, fast, inspectable choice for tables of mixed data; the goal
is monitoring, not maximum accuracy.

**Model 2 (drift).** A classifier tries to tell each year's applications from FY2001–03 applications (Model 1's
training and calibration years), using no outcomes. Its held-out AUC is the drift score: 0.5 means indistinguishable.
*Why:* PSI checks one detail at a time; this checks all of them together. The alarm threshold, **0.695**, is the
largest score among the reference years scored against each other (FY2001 0.671, FY2002 0.586, FY2003 0.695), fixed
before any later year was examined.

## Results
Every figure is for years never used in training or calibration.

| Year | Observed default | Model predicted | AUC: model / industry rule / average | Precision / recall | Drift score (alarm > 0.695) |
|---|---|---|---|---|---|
| FY2004 | 18.0% | 14.9% | 0.664 / 0.543 / 0.5 | 0.26 / 0.58 | 0.677 – |
| FY2005 | 25.3% | 16.4% | 0.640 / 0.536 / 0.5 | 0.33 / 0.61 | 0.816 **alarm** |
| FY2006 | 35.0% | 16.9% | 0.626 / 0.530 / 0.5 | 0.43 / 0.60 | 0.889 **alarm** |
| FY2007 | 42.8% (≥ 30.8%*) | 17.5% | 0.618 / 0.525 / 0.5 | 0.51 / 0.61 | 0.915 **alarm** |

\*If every FY2007 loan missing from the file (official count: 99,603 approvals) was repaid, the rate would be 30.8%.

- **Model 1 beat both prediction baselines** on AUC, PR-AUC and Brier score in every judged year. Its recall was
  slightly below the industry rule's in FY2004–06 because it flagged fewer loans.
- **Ranking held; percentages failed.** AUC fell only from 0.68 to 0.62, but by FY2007 2.4× as many loans defaulted as
  predicted.
- **Model 2's alarm was on in FY2005–07**, the three judged years in which Model 1 deteriorated, and off in FY2004.
  The biggest shifts were the SBA guarantee share, credit-line coding and the end of the LowDoc program: partly program
  and coding changes, not just riskier borrowers.

**Where it fails**
- **No earlier warning.** PSI and the simple default count also first fired in FY2005. Model 2's advantages are that
  it needs no outcomes and shows what changed.
- **Preliminary threshold.** It rests on three reference years, so its false-alarm rate is unknown. FY2004 (score
  0.677, 1.21× the predicted defaults) was a close call.
- **One loan it got wrong** (chosen by rule: the median-risk FY2006 default it did not flag): a $165,000 loan with a
  75% guarantee, scored 12.6% against a 17.0% cut-off, later charged off. Loans like it defaulted 11.8% in training and
  30.4% in FY2006.
- **Modest and decaying.** Model 1 misses about 4 in 10 defaults; by FY2010 (outcomes incomplete) its AUC was 0.50
  against 0.55 for the industry rule.
- **Drift is not risk.** Drift kept rising in FY2009–10 while recorded defaults fell.
- **Scope.** No demographic data, so this is not a fairness audit. One dataset, studied in hindsight: not evidence of
  how the method would perform at a real bank.

## What I'd do next
1. Repeat the test on the SBA's newer data (FY2010 onward, including COVID) to see whether the alarm ever leads
   outcome-based monitoring, and to estimate a false-alarm rate.
2. Test whether recalibrating Model 1 after an alarm narrows the gap between predicted and observed defaults.

## Sources
- Data: Li, M., Mickel, A., & Taylor, S. (2018). "Should This Loan be Approved or Denied?" *Journal of Statistics
  Education* 26(1). https://doi.org/10.1080/10691898.2018.1434342 (CC BY 4.0); Kaggle mirror:
  https://www.kaggle.com/datasets/mirbektoktogaraev/should-this-loan-be-approved-or-denied
- Official approval counts: U.S. SBA "Table 3 – Number of Approved Loans by Program",
  https://webharvest.gov/congress115th/20181203195802/https://www.sba.gov/sites/default/files/WDS_Table3_ApprovalCount_Report.pdf
- Methods: adversarial validation (Lopez-Paz & Oquab, ICLR 2017); PSI (credit-risk practice).
- Libraries: pandas, NumPy, scikit-learn, matplotlib, kagglehub, pytest, Chart.js.
- AI tool: Claude Code (Anthropic), https://claude.com/claude-code. Helped research the idea, write code, run analysis,
  and draft the documentation and dashboard, under my close direction and review.
  No pretrained models are used in the project's analysis.

---

**Reproduce** (from the repository root; about 3 minutes; deterministic, so a clean clone gives identical results):
```bash
pip install -r requirements.txt
cd src && python -m sma.audit && python -m sma.pipeline && python -m sma.figures
cd .. && python dashboard/build_dashboard.py && pytest -q    # 13 tests
```
Code: `src/sma/` · results: `results/` · dashboard: `dashboard/` · docs: [full write-up](docs/full_writeup.md),
[feature audit](docs/feature_audit.md), [decision log](docs/decision_log.md), [FAQ](docs/faq.md).
