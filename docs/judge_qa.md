# Judge Q&A: hard questions, candid answers

All numbers come from `results/results.json` and `results/audit.json`. If you don't know something, say "I don't know;
here is how I would find out."

## The idea

**1. What is this, in one sentence?**
A retrospective test of whether a bank's credit-risk analyst could tell that a loan model was going out of date using
only application forms, without waiting years for loans to default.

**2. How is this different from a normal default-prediction project?**
The default model is not the product; it is the thing being monitored. The contribution is the second model and the
test design: does a drift signal built without outcomes line up with later, measured model failure, and how does it
compare with simpler monitors?

**3. What is actually AI here, rather than ordinary statistics?**
Two machine-learning classifiers. Model 1 (gradient boosting) learns from 81,624 labelled loans to predict default.
Model 2 (also gradient boosting) learns to tell one year's applications from the reference years; its accuracy is the
drift score. PSI, by contrast, is ordinary statistics, and I use it as the baseline.

**4. Why are two models needed?**
They answer different questions. Model 1: "will this loan default?", which needs outcomes. Model 2: "do this year's
applicants still look like the ones Model 1 was built from?", which needs no outcomes and so is available immediately.

**5. Why adversarial validation and not just PSI?**
PSI looks at one application detail at a time with rule-of-thumb cut-offs. Adversarial validation combines all 13
details into one score and can pick up shifts in combinations. Candidly: in this data both flagged exactly the same
years (FY2005–10), so I cannot claim it detects more than PSI. It gave one combined score and a ranking of which
details mattered.

## The models and metrics

**6. What does AUC mean?**
Pick one loan that defaulted and one that was repaid. AUC is how often the model gave the defaulted one the higher
risk. 0.5 is chance, 1.0 is perfect. It measures ranking only.

**7. How can the model rank borrowers reasonably and still under-estimate defaults?**
Ranking (discrimination) and percentages (calibration) are different things. If every borrower's true risk doubles,
the order stays the same, so AUC barely moves, but every predicted percentage is now too low. That is what happened:
AUC went from 0.68 to 0.62, while observed defaults reached 2.4× the predicted rate by FY2007.

**8. An AUC of 0.62–0.66 is weak. Why should anyone care?**
It is modest, and the write-up says so. The data has no credit scores or financial statements, only 13 application
details. The model is a realistic test subject for monitoring, not something to lend with. A version including the
suspect loan-term field scored 0.96, which is the "too good to be true" pattern.

**9. Is the baseline fair?**
Yes. Both baselines are fitted on the same FY2001–02 training loans and evaluated on the same later years. The
average-rate baseline predicts 11.8% for everyone; the industry rule looks up each 2-digit industry's training default
rate. Neither uses future information.

**10. Does Model 1 beat the baselines on everything?**
No. In FY2004–07 it beats both on AUC, PR-AUC and Brier score, and has higher precision than the industry rule. Its
recall is slightly lower than the industry rule's in FY2004–06 (0.58–0.60 vs. 0.62–0.63) because it flags fewer loans.
In FY2010 (outcome-incomplete) its AUC is 0.50 against 0.55 for the industry rule, and logistic regression does better
than gradient boosting in FY2009–10.

**11. Why not a neural network?**
For small tables of mixed numbers and categories, gradient-boosted trees are a standard strong choice, train in
seconds and are easier to inspect. A more complex model would be exposed to the same drift.

**12. How do you know the test years are really unseen?**
Training uses FY2001–02 only; calibration and the flag cut-off use FY2003 only; FY2004–10 are never touched by either.
The fiscal year is never a feature. An automated test checks the year sets do not overlap. One caveat: training labels
are outcomes as known in 2014, which a real bank in 2003 would not yet have had in full. That favours the model, and it
still mis-estimated badly.

## Data problems

**13. Tell us about the loan-term field. Is it leakage?**
I cannot prove it is. In mature cohorts, loans with round terms defaulted 0.8% and odd terms 29.6%; 84 months 0.3%,
83 months 10.3%. That is hard to explain for a contract length fixed at approval. But the recorded term matches the
time to charge-off for only 4% of charged-off loans, so the simple "it was overwritten with time-to-default"
explanation is not supported. My hypothesis is that it was altered for some troubled loans. I treat it as suspected
contamination and exclude it. Including it would raise AUC to about 0.96, and I do not report that as a result.

**14. Are any other features unavailable at approval?**
The charge-off date, charge-off amount and outstanding balance exist only after the outcome and are excluded. The
disbursed amount comes slightly after approval, so I use the approved amount instead. The full list is in
`docs/feature_audit.md`.

**15. What about missing outcomes (right-censoring)?**
The file only contains loans resolved by 2014. Loans still running, mostly ones being repaid, are missing, so later
cohorts over-state default rates. That is why only FY2004–07 are judged, and FY2008–10 are shown as
outcome-incomplete.

**16. Why is FY2007's figure uncertain?**
42.8% is the default rate among the 71,649 FY2007 loans in the file. Official SBA counts show 99,603 approvals that
year. If every missing loan was repaid, the rate would be 30.8%. The truth lies between. Even the lower bound is well
above the 17.5% predicted.

## The alarm

**17. How was the 0.695 threshold set, and why from so few years?**
Each of the three reference years was scored against the other two: FY2001 0.671, FY2002 0.586, FY2003 0.695. The
threshold is the largest. Only three years are used because industry codes are missing for about half of loans before
FY2001. Three is too few to call this a validated threshold; it is preliminary.

**18. You report one false alarm in three normal years. Is that your false-alarm rate?**
No, and I corrected that wording. Leaving each reference year out in turn flags FY2003, but with a "largest value"
rule that check always flags exactly one year, whatever the data. The honest statement is that the false-alarm rate
cannot be estimated from three years. Estimating it needs more normal years, which the newer SBA data would provide.

**19. Did the alarm miss anything?**
FY2004 had 1.21× the predicted defaults and no alarm. Under my rule (more than 1.25×) that is not deterioration; under
a stricter rule it is a miss. FY2004's drift score was 0.677, and 0.677–0.694 under three other random seeds, against a
0.695 line. So FY2004 was a close call that could have gone either way.

**20. Is your alarm earlier than simply monitoring defaults?**
Not in this data. A monitor that counts defaults already seen among loans approved two years earlier also first fired
in FY2005. With a three-year lag it first fires in FY2006, but I report the two-year version because it is the harder
comparison. I do not claim an earlier warning.

**21. Then why would a bank bother with it?**
Two practical reasons. It needs no repayment data, so it works for a new product or portfolio with no outcome history.
And it says which application details changed, which tells the analyst where to look. Whether that is worth the false
alarms is not something this study establishes.

**22. Does drift mean higher risk?**
No. Drift scores keep rising in FY2009–10 while recorded default rates fall. Part of the measured drift is SBA program
and data-coding change, such as the end of the LowDoc program. Drift means the model is being used on unfamiliar
applicants; whether that hurts has to be checked separately.

**23. How do you know the drift is related to the model getting worse?**
I only know they coincided in three judged years. That is an association in one dataset, not a causal finding.

## Impact, fairness and deployment

**24. Where do the dollar figures come from, and are they losses?**
For each FY2004–07 loan: predicted probability × approved amount × 57% (the charged-off share of defaulted training
loans), summed: $2.76B. The recorded charged-off principal for the same loans sums to $5.66B. These are gross
charge-offs, before recoveries and shared between lenders and the SBA guarantee. They are not final losses. In the
calibration year the same method over-estimated (0.82×), so it does not manufacture a gap.

**25. Is it fair?**
I cannot say. The data has no race, sex or age fields, and I do not infer them from names or places. The only group
comparisons are descriptive: defaults were 2.69× predicted in Florida (17,547 loans) and 1.36× in Ohio (11,692).
Region is confounded with the housing market. This is not a protected-group fairness audit.

**26. Could a real bank use this today? What would be needed first?**
No. It is a retrospective prototype. Before any use it would need: the bank's own data and model; many more reference
periods to set and validate a threshold; a measured false-alarm rate; a test on at least one other downturn; a check
that recalibrating after an alarm actually helps; and the bank's own model-risk governance.

**27. What did you do, and what did Claude Code do?**
Claude Code (Anthropic) helped develop and research the idea, wrote the code, ran the analysis and drafted the
documentation and dashboard. I directed the work, made the decisions about what to pursue, repeatedly asked for audits that removed
claims the evidence did not support (for example "early warning" and "proven leakage"), set up the repository and the
published dashboard, recorded the demo, and studied the project so that I can explain each part. I did not write the
modelling code myself.

**28. What would you do with more time?**
Run the same test on the SBA's newer loan-level data (FY2010 onward, including COVID) to see whether the alarm ever
leads outcome-based monitoring and to estimate a false-alarm rate; then test whether recalibrating Model 1 after an
alarm narrows the gap between predicted and observed defaults.
