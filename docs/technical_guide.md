# Technical guide (plain English)

Read this top to bottom once. Every idea a judge might ask about is here, explained without jargon first and
with the proper term second.

## The project in one breath
Banks use AI to guess which small-business loans will go bad. That AI learns from old loans. When the world changes,
the AI can quietly become wrong, and the bank only finds out years later when loans fail. I built a **second AI that
notices when today's borrowers no longer look like the ones the first AI learned from**, and I tested it in hindsight
on real SBA loans approved in the years before the 2008 financial crisis.

## 1. The ideas

**Supervised machine learning.** You show a computer many examples *with the answer attached* ("this loan was repaid",
"this one defaulted") and it finds patterns that connect the details to the answer. Then it can guess the answer for
new examples. "Supervised" means the answers were supplied during learning.

**Classification.** A kind of supervised learning where the answer is a category: here, *default* or *repaid*. My
model outputs a probability ("23% chance of default"). Turning that into a yes/no flag needs a cut-off, which I
call the threshold.

**How the default model learns (gradient boosting).** It builds hundreds of tiny decision trees, each a short
flowchart like "Is the loan over $150k? Is the business new?". Each new tree focuses on the loans the previous trees
got most wrong. The final guess adds up all the trees. It is a strong, standard method for tables of data.
**Logistic regression** is the simpler comparison: it gives each feature one weight, like a weighted checklist.

**Baseline.** The dumbest reasonable guess, so I can see how much the AI adds. Mine: (a) give every loan the same
risk, the training average; (b) look up the industry's past default rate.

**ROC-AUC ("AUC").** Pick one loan that defaulted and one that was repaid at random. AUC is how often the model gave
the defaulted one the higher risk score. 0.5 = coin flip, 1.0 = perfect. It measures **ranking**, not whether the
percentages are right.

**Precision and recall.** Of the loans the model *flagged*, precision is the share that really defaulted. Of the loans
that *really defaulted*, recall is the share the model flagged. They trade off: flag more loans and you catch more
defaults (recall up) but also flag more good loans (precision down).

**Brier score.** The average of (predicted probability − what happened)². Lower is better. It punishes confident wrong
guesses, so it checks **both** ranking and whether the percentages are right.

**Calibration.** Whether the percentages mean what they say. If the model says 15% for a group of loans and 15% of
them default, it is calibrated. I report **actual ÷ expected**: 1.0 is perfect, and 2.0 means twice as many defaults
as the model expected. For a bank this matters a lot, because it decides how much money to hold back for losses.

**Data drift.** The *inputs* change: this year's borrowers have different loan sizes, programs or industries than
before. **Concept drift** is different: the *link* between inputs and default changes. For example, the same kind of
business becomes riskier because the economy turned. Drift in inputs is visible on approval day. Concept drift
usually only shows up when loans fail.

**PSI (Population Stability Index).** The bank industry's standard drift check, done one feature at a time. Split a
feature into bins (for example 10 loan-size ranges), compare the share of loans in each bin now vs. then, and add up
the differences in a particular way: PSI = Σ (now% − then%) × ln(now% / then%). 0 = identical. People often say above
0.25 is a big shift. That is a habit, not a scientific law.

**Adversarial validation (my drift detector).** Mix old applications (label "old") with this year's (label "new"),
hide the labels, and train a classifier to guess which is which. If it can't do better than a coin flip (AUC ≈ 0.5),
the two groups look the same. If it can easily (AUC near 1), this year's borrowers look unlike anything the risk model
learned from. **This is a machine-learning model itself**: it learns patterns across *all features at once*, which
PSI cannot. And it never sees whether loans defaulted.

**Why drift does not automatically mean failure.** A change can be harmless. For example, the SBA renamed a program,
so a code changed, but borrowers are just as safe. And a model can fail with little drift, if the economy changes
while the borrowers look the same. So the alarm means "**review the model**", not "**the model is broken**".

## 2. How I tested it fairly
- **Time split.** Learn from FY2001–2002, tune on FY2003, then test each year from FY2004 to FY2010 separately. The
  model never sees the future.
- **Alarm threshold set from normal years only.** I measured how different the normal years (2001, 2002, 2003) were from
  *each other*. The alarm fires only if a new year is more different than that. Nothing after 2003 was used.
- **"Did the model really get worse?"** I decide this in hindsight, using how the loans actually turned out:
  deteriorated = more than 25% more defaults than expected, or AUC down by 0.05 or more.
- **Compared with a simpler alarm.** A bank could also just count how many loans from 2 years ago have already
  defaulted (the "label monitor"). My alarm has to be at least as useful as that.
- **Robustness.** Other training windows, removing suspicious fields, changing thresholds, three random seeds: the
  conclusions did not change.

## 3. What the results show, and what they don't
**Shows:**
- The AI risk model was better than simple rules in every judged year (FY2004–07). By FY2010 it was no better than
  the industry lookup table.
- Its ranking stayed fairly stable (AUC 0.68 → 0.62), but its risk estimates were far too low: it expected 15–17.5%
  defaults while 18–43% happened.
- The drift alarm was on in every year the model had deteriorated (2005, 2006, 2007) and off in 2004, without ever
  using a default. The simpler checks (PSI and counting early defaults) also first fired in 2005.
- The detector says *what* changed: guarantee share, coding of credit lines, the end of the LowDoc program, loan size.

**Does not show:**
- That the alarm is *earlier* than watching early defaults. In this data both fired in FY2005.
- That drift *caused* the defaults. Correlation in one crisis is not cause.
- That the alarm line is reliable. It comes from only three reference years, so the false-alarm rate is unknown, and
  FY2004 fell just under it.
- That the loan-term field is a proven leak. It is a suspected recording problem; I removed it to be safe.
- That this works for other banks, countries or decades. It is one case study.
- Fairness for protected groups. The data has no demographic information.

## 3b. Two numbers judges will ask about
**The dollar figure.** For each loan: model's default probability × loan amount × 57%, the share of a defaulted loan
that was recorded as charged off in 2001–02. Add these up and you get the charge-offs the model "expected". For
FY2004–07 that was $2.76B, while $5.66B was recorded as charged off. These are gross charge-offs: before any money
recovered later, and split between the lender and the SBA guarantee. They are not final losses. Sanity check:
in FY2003 the same sum came out *higher* than reality (0.82×), so the method isn't rigged to show a gap.

**The example loan.** I didn't pick a loan that makes a good story. The rule: of all FY2006 defaults the model did
*not* flag, take the one in the middle (median) of the model's risk scores. Same rule every year, and the code applies
it.

## 4. Why it matters
If a bank's model says "15% of these loans will fail" and 35% do, the bank has set aside too little money for losses
and may keep lending into a bubble. Small businesses get loans priced wrongly. And once the bank panics, good
businesses can get cut off too. A cheap, outcome-free alarm that says "your borrowers have changed, check your model"
is a safety habit, like a smoke detector. It does not put out fires, but it tells a person to look.

## 5. The code, piece by piece
| File | What it does | Why it's needed | Takes in | Produces |
|---|---|---|---|---|
| `src/sma/config.py` | All settings: years, features, thresholds | One place to see and change every choice | – | constants |
| `src/sma/data.py` | Loads the CSV, cleans it, builds features and the target | Raw data has dollar signs, 2-digit years, odd codes | `SBAnational.csv` | clean table |
| `src/sma/audit.py` | Data checks: suspicious Term field, outcome maturity, recording changes | Decides what I may trust before modelling | clean table | `results/audit.json`, `cohorts.csv` |
| `src/sma/models.py` | AI model #1 + baselines, calibration, threshold | The thing being monitored | FY2001–03 loans | fitted models |
| `src/sma/drift.py` | PSI and adversarial validation (AI model #2) | The alarm | two groups of applications | drift scores, top features |
| `src/sma/evaluate.py` | AUC, precision, recall, Brier, calibration, bootstrap intervals | Honest scoring | true answers + predictions | metrics |
| `src/sma/pipeline.py` | Runs experiments E4–E10 and saves everything (E9 = dollars, E10 = example loans) | Reproducibility | all of the above | `results/results.json` |
| `src/sma/figures.py` | README charts | Communication | results | PNGs |
| `dashboard/` | Interactive page built from results | Demo | results | `index.html` |
| `tests/` | 13 automatic checks | Catches mistakes (e.g. a leak creeping back in) | – | pass/fail |

**Bootstrap confidence interval.** I re-draw the test loans at random, with replacement, 200 times and recompute the
metric each time. The middle 95% of the results is the interval. With 70,000 loans per year the intervals are narrow
(about ±0.005 AUC), so the year-to-year changes are not noise. The bigger uncertainty is that there is only one crisis.
