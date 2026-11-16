# Frequently asked questions

Short answers to common questions about Stale Model Alarm. The [README](../README.md) has the main results and the
[full write-up](full_writeup.md) has every detail.

> This project is a prototype and is not financial advice.

**What is Stale Model Alarm?**
A research prototype that checks whether a bank's loan-default model may be going out of date. It replays real SBA
small-business loans from FY2004 to FY2010 and flags years when new applicants look different from the ones the model
was built from.

**Who is it for?**
A credit-risk analyst at a community bank who reviews the bank's loan model from time to time.

**Does it approve or reject loans?**
No. It never makes a lending decision. It gives a person a reason to review the model.

**What data does it use?**
899,164 public U.S. Small Business Administration 7(a) loans published by Li, Mickel & Taylor (2018) under CC BY 4.0.
Each loan is labelled as paid in full or charged off. No personal information is used, and business names are never
shown.

**What do the two models do?**
Model 1 predicts the chance that each loan will be charged off. Model 2 tries to tell one year's loan applications
apart from the applications Model 1 was built from. If it can do that easily, the applicants have changed. Model 2
uses application details only, never repayment outcomes.

**What is "drift"?**
A change in the kind of applicants a model sees, for example different loan sizes, industries or SBA guarantee levels.
It does not by itself mean borrowers are riskier.

**Does an alarm mean defaults will rise?**
No. An alarm means the model is being used on applicants unlike the ones it learned from, so it should be reviewed.
In this data the drift score kept rising in FY2009 and FY2010 while recorded default rates fell.

**What is AUC?**
A score for how well a model ranks risk. Pick one loan that defaulted and one that was repaid at random: AUC is how
often the model gave the defaulted loan the higher risk score. 0.5 means no better than a coin flip and 1.0 means
perfect. AUC only measures ranking, not whether the predicted percentages are right, so a model can have a decent
AUC and still underestimate how many loans will default. That is what happened here.

**How well does it work?**
On years it never saw (FY2004 to FY2007), Model 1 ranked loans better than two simple rules: AUC 0.62 to 0.66, against
about 0.53 to 0.54 for an industry lookup table and 0.5 for the average rate. But it badly underestimated how many loans
would default; in FY2005 it predicted 16.4% and 25.3% defaulted. Model 2's alarm was on in FY2005 to FY2007, the years
Model 1 deteriorated, and off in FY2004.

**Does it warn earlier than simply watching defaults?**
Not in this data. A simple check that counts early defaults also first fired in FY2005. What the drift alarm adds is
that it needs no repayment data and shows which applicant characteristics changed.

**Why are only FY2004 to FY2007 judged?**
The dataset only includes loans whose outcome was known by 2014. Later loans were often still running, so their default
rates are incomplete and cannot be judged fairly.

**Was anything left out of the model on purpose?**
Yes. The loan-term field behaves as if it may contain information recorded after loans went bad, so it was excluded as
a precaution. Fields that only exist after a loan's outcome, such as the charge-off date, are excluded too.

**Is it fair to all borrowers?**
That cannot be tested here. The data has no demographic information, and none is guessed from names or places.

**Could a real bank use it today?**
No. It is a retrospective study of one dataset. A bank would need to test it on its own data, over more time periods,
before relying on it.

**How can I run it myself?**
Follow the "Reproduce" steps at the bottom of the README. It takes about three minutes and gives identical results.

**Where can I see it?**
- Demo video: https://youtu.be/Q_YpQ6imcLw
- Live dashboard: https://mihirheera.github.io/stale-model-alarm/dashboard/index.html
