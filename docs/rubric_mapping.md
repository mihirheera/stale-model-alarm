# Rubric matrix

A self-assessment against the Round 1 rubric. Score ranges are realistic estimates, not guarantees.

| Category | What the project demonstrates | Evidence a judge can inspect | Remaining weaknesses | Final action | Estimated range |
|---|---|---|---|---|---|
| **Technical execution (30)** | Two working ML models; chronological split (train FY2001–02, calibrate FY2003, test FY2004–10); calibrated probabilities; fair baselines fitted on training years; bootstrap intervals; 13 automated tests; deterministic pipeline that a clean clone reproduces exactly; dashboard generated from results files | `src/sma/`, `tests/test_core.py`, `results/results.json`, README appendix, live dashboard | Model 1 is modest (AUC 0.62–0.66) and decays; alarm threshold from three reference years; no deployment-style validation | None required | 21–25 |
| **Originality (20)** | A monitoring question rather than a prediction one; a second classifier auditing the first; tested against both prediction and monitoring baselines; a suspicious field found and excluded | README "What I added"; `docs/decision_log.md` D1; Drift section of the dashboard | Drift monitoring and adversarial validation are known techniques; the novelty is the application and the test design. | None | 13–16 |
| **Impact and track fit (20)** | A named user (community-bank credit-risk analyst); a concrete review decision; scale shown with model-implied vs. recorded gross charge-offs; never decides a loan | README "The problem", dashboard overview and Actions section | Helps the lender, not the borrower directly; no earlier warning than a simple default count was shown; benefit of acting on an alarm not measured; gross charge-offs are not net losses | None; do not overstate in the video | 11–14 |
| **Testing and honesty (15)** | Baselines reported side by side; unseen test years; precision, recall, PR-AUC, Brier, calibration; robustness checks; an explicit failure example chosen by rule; limitations stated: no lead time, preliminary threshold, FY2004 close call, incomplete outcomes, FY2010 decay, suspected (not proven) contamination | README "Where it fails"; dashboard Limitations; `docs/full_writeup.md`; `docs/judge_qa.md` | One dataset and one downturn; false-alarm rate cannot be estimated | None | 12–14 |
| **Communication (15)** | README in the official template with one main takeaway; dashboard organised around the analyst's workflow; timed 2-minute script with storyboard and fact check; 28-question Q&A | README, dashboard, `docs/demo_script.md` | README is longer than one page; dashboard is dense; **video not yet recorded** | Record and upload the video | 10–13 (9–11 without a video) |

Overall: roughly 67–82 of 100, depending mostly on how judges weigh the modest model and the absence of a demonstrated
lead-time advantage against the testing and honesty.

## Official requirement checklist
| Requirement | Met? | Where |
|---|---|---|
| Names a specific user | Yes | README "What I built"; dashboard intro line |
| Real input producing a result | Yes | Dashboard "Loans" section; README "One loan it got wrong" |
| Compares with at least one simple baseline, both reported | Yes | README results table (model / industry rule / average) |
| Shows where it fails | Yes | README "Where it fails"; dashboard Limitations |
| Fitting measure; precision and recall | Yes | README table; `docs/full_writeup.md` has baseline precision/recall |
| Train on earlier data, test on later | Yes | `src/sma/config.py`; `tests/test_core.py` |
| "This project is a prototype and is not financial advice." | Yes | README line 6; dashboard footer |
| Cites datasets, tools and AI tools | Yes | README "Sources" |
| Code viewable by anyone | Yes | https://github.com/mihirheera/stale-model-alarm |
| Demo video, up to 2 minutes (optional, recommended) | **To do** | `docs/demo_script.md` |
