# Two-minute demo script

Screen-record the dashboard (`dashboard/index.html`) with your voice over it. Follow the competition's structure:
problem 15 s · demo 60 s · how it works 30 s · next steps 15 s. Read it aloud once with a timer before recording.

| Time | On screen | Say (roughly) |
|---|---|---|
| 0:00–0:15 | Dashboard title | "Banks use AI to decide which small-business loans are risky. That AI learns from old loans. But when the economy changes, it can quietly go out of date, and the bank only finds out years later when loans fail. Our project asks: could the model have known it was going stale?" |
| 0:15–0:30 | Click **FY2004** | "This is a community-bank risk analyst's view. We trained a model on real SBA small-business loans from 2001 and 2002, and now we replay later years. In 2004 the status is green: this year's applicants look like the ones the model learned from." |
| 0:30–0:50 | Click **FY2006**, point at the red banner and KPI tiles | "In 2006 the alarm is on. Our second AI model, which never sees whether loans were repaid, can tell 2006 applicants apart from the training years with a score of 0.89. In hindsight it was right to worry: the model expected 17% of these loans to fail, and 35% did. In dollars, it implied $674 million of losses; $1.7 billion was charged off." |
| 0:50–1:05 | Scroll to **Real examples** | "Here's one real application going in. A $165,000 franchise loan; the model says 12.6% risk, under its cut-off, so not flagged. It defaulted. Loans like it defaulted 12% of the time in training and 30% in 2006. The model was using an out-of-date lesson." |
| 1:05–1:15 | "Why this status?" box | "The alarm also says *what* changed: guarantee share, credit-line coding, the end of LowDoc. Some of that is policy, not riskier borrowers, so it means 'review the model', not 'the model is broken'." |
| 1:15–1:45 | Defaults chart, then AUC chart | "How it works: model one is gradient boosting, and it beat both simple baselines in every year we could judge. Interestingly, its ranking barely dropped, AUC 0.68 to 0.62, while its probabilities fell apart. Model two is adversarial validation; its alarm threshold was set using only the normal years. We also caught a leak: one column made accuracy look like 0.96, so we removed it." |
| 1:45–2:00 | Methodology box | "Honest limits: a simple monitor that counts early defaults also fired in 2005, so we can't claim lead time. And this is one crisis. Next, we'd test it on the SBA's newer data, including COVID. This is a prototype, not financial advice." |

**One takeaway to land:** *A credit model can keep ranking borrowers well while badly underestimating risk. A cheap
alarm built only from application data flagged it as fast as waiting for defaults would have, and showed what changed.*

## Finals (5 minutes + Q&A)
Same structure, with more time on: the Term leak (show the 0.96 vs. 0.64 numbers), the year-by-year table, and the
"what we can't claim" section. Keep the dashboard open in two tabs and the README figures as a backup in case the
internet fails (the charts need Chart.js from the web; the numbers, examples and table still work offline).
