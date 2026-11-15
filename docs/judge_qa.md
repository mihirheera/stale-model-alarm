# Judge Q&A: hard questions, honest answers

All numbers come from `results/results.json`. If you don't know something, say "I don't know; here's how I'd find out."

**1. How do you know there's no data leakage?**
We listed every column and asked whether a bank knows it on approval day ([feature audit](feature_audit.md)). We
removed the charge-off date, charge-off amount and current balance, which only exist after the outcome. We also
checked for a hidden leak: loan term. In fully matured loans, round terms defaulted 0.8% and odd terms 29.6%, which is
impossible for a contract set on day one, so we removed it. With it, AUC was ~0.96; without it, ~0.64. Our test suite
checks that none of these columns is a feature. The model never sees the year, and test years are never used in
training or calibration.

**2. Why this dataset?**
It is large (899,164 real loans), public (CC BY 4.0, published in a statistics journal), about small businesses (the
track's own words), and it spans a real, dated crisis. That lets us test a monitoring idea against what actually
happened.

**3. Why not a neural network?**
For tables of mixed numbers and categories, gradient-boosted trees are usually as good or better, train in seconds on
a laptop, and are easier to inspect. Our question is about *monitoring*, not squeezing out accuracy. A fancier model
would be just as exposed to a changing world.

**4. Why is PSI useful if you built something better?**
PSI is what banks already use, so it is the fair baseline. It is simple and explainable per feature. Its weakness: it
looks at one feature at a time and its thresholds are rules of thumb. Here PSI and our detector flagged the same
years, so we don't claim ours beats PSI at *detection*. Ours adds a single all-feature score and shows which features
matter together.

**5. Data drift vs. concept drift?**
Data drift = the inputs change (more SBA Express loans, smaller guarantees). Concept drift = the link between inputs
and default changes (the same kind of business becomes riskier because the economy turned). Our detector only sees
data drift. In 2005–07 both seem to have happened; we can't fully separate them.

**6. Can a model drift without losing accuracy?**
Yes. That's why our alarm says "review", not "broken". FY2009–10 show rising drift while the (incomplete) default rate
falls. Part of the drift is also program or coding changes (LowDoc ended, credit-line codes changed), which need not
change risk.

**7. Can performance get worse without obvious drift?**
Yes. FY2004 had 21% more defaults than expected while the drift score (0.677) stayed under the threshold (0.695).
Under a stricter definition of "deteriorated" that is a miss. If the economy changes but applicants look the same, an
input-drift alarm can't see it. That's why it should sit next to outcome monitoring, not replace it.

**8. How do you know the alert is genuinely early?**
We don't claim it is. A simple monitor counting early defaults among loans from two years before *also* first fired in
FY2005. What we can say: our alarm needs no outcome data at all, it is available on approval day, and it explains what
changed. Proving lead time needs more downturns, e.g. the COVID era in newer SBA data.

**9. What if the detector raises a false alarm?**
A person reviews the model, which costs some analyst time and no loans are blocked. Among the normal years, a
leave-one-year-out check gave 1 false alarm in 3, so false alarms are realistic. That's acceptable for a "please
check" signal, not for an automatic action.

**10. How would a real bank use it?**
Every quarter or year, run the detector on new applications against the model's training data. If the alarm is on,
the model-risk team reviews it: recalibrate, retrain, or add a human check for the shifted segment (the detector says
which features moved). It never touches individual loan decisions.

**11. How did you set the threshold, and could you have tuned it to look good?**
It is the largest drift seen *between the normal years themselves* (FY2001–03), computed before looking at 2004+. We
also tried margins of +0.02, +0.05 and +0.10 above it: the same years alarm in every case.

**12. Your model's AUC is only ~0.64. Isn't that weak?**
It's modest, and honest. Small-business default is hard to predict from a few application fields, with no credit
scores or financial statements. It still clearly beats the baselines in FY2004–07 (0.53–0.54 industry rule, 0.50 average rate),
and its Brier score is lower than both in those years. By FY2010 it no longer beats the industry rule (AUC 0.50 vs.
0.55), which is another sign it had gone stale. The leaky version scored 0.96, which is exactly the "too good to be
true" warning the judges mention.

**13. Is the jump in defaults real or an artefact?**
Partly an artefact. The file only contains loans whose outcome was known by 2014, so late cohorts look worse. We
checked against official SBA counts: even if every missing FY2007 loan was repaid, at least 30.8% defaulted, vs.
11.8% in training. The jump is real; its exact size isn't certain. FY2008–10 are labelled "outcome-incomplete" and not
judged.

**14. Are the year-to-year differences statistically meaningful?**
Each year has 17,000–77,000 loans. 95% bootstrap intervals are narrow (AUC about ±0.005; calibration ratio about
±0.02), so the trends aren't sampling noise. We avoided piles of p-values. The big uncertainty isn't sample size;
it's that we have one crisis (n = 1).

**15. Does drift *cause* defaults?**
We don't claim that. Drift tells you the model is being used on unfamiliar borrowers. One plausible story: more
SBA Express-style loans (smaller guarantees, lighter paperwork) were made just before the recession. That is a
hypothesis we haven't tested.

**16. Is it fair? Does it hurt some groups more?**
The data has no race, gender or age fields, so a protected-group audit isn't possible, and we don't guess them from
names or places. Across the groups we *can* check, under-prediction hit everyone, but unevenly: Florida 2.69×
expected defaults, Ohio 1.36×. In professional services and health care, the model caught only 26% and 15% of
defaults. A bank should check segments like these when the alarm fires.

**17. What's the difference between your two AI models?**
Model 1 answers "will *this loan* default?" and learns from outcomes. Model 2 answers "do *this year's borrowers* look
like the ones model 1 learned from?" and never sees outcomes.

**18. Your training labels come from outcomes up to 2014. Isn't that cheating?**
It's generous *to the model*. A real bank in 2004 couldn't know how 2001–03 loans would end. So our model had an
advantage a real one wouldn't, and it still went badly wrong. That makes the finding stronger, not weaker.

**19. What did you do vs. what did the AI tool do?**
[Answer honestly in your own words.] Claude Code wrote most of the code and ran the analysis; we chose the question
and the user, reviewed every decision in the decision log, and checked the results make sense. Be ready to explain
any file in the technical guide's code table.

**20. What would you do with more time or data?**
Run the same test on the SBA's newer data (2010–present, including COVID) to see if the alarm ever gives real lead
time. Then test whether recalibrating when the alarm fires actually closes the gap between expected and actual defaults.

**21. Where does the "$2.8B expected vs. $5.7B actual" come from?**
For each FY2004–07 loan we multiplied the model's default probability by the loan amount and by 57%, the share of a
defaulted loan's amount charged off in the training years. Summed, that is $2.76B. The data's charge-off column sums to
$5.66B for the same loans. In FY2003, the calibration year, the same method *over*-estimated (0.82×), so it doesn't
create a gap by itself. Caveats: later years are inflated by the missing unfinished loans, and the lender's share is an
approximation using each loan's guarantee percentage.

**22. Show us one example your model gets wrong. Did you pick it to look good?**
No. The rule is in the code: among the FY2006 defaults the model did not flag, take the one with the median predicted
risk. It's a $165,000 franchise loan with a 75% guarantee, scored 12.6% (cut-off 17.0%), and it was charged off. Loans
with that guarantee defaulted 11.8% in training and 30.4% in FY2006. The dashboard shows the same rule's examples for
every year. No names or IDs are shown.
