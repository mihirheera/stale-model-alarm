# Demo video

**Video:** https://youtu.be/Q_YpQ6imcLw (1:59). Recorded voice-over by Mihir Heera; the dashboard walkthrough was
screen-recorded with Playwright, synced to the spoken words, and edited with FFmpeg. Captions file:
`video/stale_model_alarm_demo.srt` (kept outside the repository).

Structure follows the official guide: problem, demo, how it works, next steps.

| Time | On screen | Said |
|---|---|---|
| 0:00 | Full screen: Mihir, introduction (captions on) | "Hi, my name is Mihir Heera and I built the Stale Model Alarm. Now, modern day community banks use AI to predict whether small business loans will actually be repaid. But when the economy inevitably changes, new applicants may look very different from borrowers that the model is trained on. This can make the model's predictions way less reliable." |
| 0:21 | Dashboard, top of page, FY2004 selected; Mihir in the corner from here on | "Now this is Stale Model Alarm, a tool that helps financial analysts monitor changes in their credit risk models." |
| 0:28 | Cursor moves to FY2005 and clicks it; status turns CRITICAL | "First, let's look at fiscal year 2005. The dashboard compares the model's predicted loan defaults with the actual results." |
| 0:36 | Drift score cell (0.816) outlined | "It also checks whether the characteristics of new applicants have changed." |
| 0:39 | CRITICAL status panel outlined | "Here, our system detects a major shift in the applicant population and raises an alarm." |
| 0:45 | Evidence section: applicant characteristics that changed | "It also identifies which characteristics changed, helping analysts understand what may be affecting their model. For example, changes in loan size, credit line usage, and SBA guarantee percentages helped explain this shift." |
| 0:58 | Strength of the evidence panel (Link: not established) | "An alarm does not automatically mean borrowers are riskier." |
| 1:01 | Actions section: Critical row highlighted | "It just tells analysts that they should investigate whether their existing model is still reliable." |
| 1:07 | Method section: stream 1 (credit-risk model) | "We used historical US Small Business Administration loan data and we trained our credit risk model on earlier loans and tested it on later years that had never seen before." |
| 1:17 | Method section: stream 2 (population monitor) | "We also built a second machine learning model to detect changes in applicant characteristics." |
| 1:22 | Performance section: AUC chart, cursor over FY2004 to FY2007 | "From fiscal year 2004 to fiscal year 2007, our model achieved AUC scores of 0.62 to 0.66 compared with 0.53 and 0.54 for an industry-based baseline." |
| 1:35 | Limitations: "No earlier warning has been shown" | "Our system first raised an alarm in fiscal year 2005, the same year as a simpler default monitoring method. While we may not have shown an earlier warning, our approach adds a different signal," |
| 1:46 | Drift section: adversarial validation panel, then the SBA guarantee share comparison | "it detects changes in applicants and helps explain what is driving them." |
| 1:50 | Limitations: "Outcomes are incomplete", then "One dataset, in hindsight" | "One limitation is that historical loan outcomes are incomplete. And looking forward, we want to test our system with newer lending data and across different economic conditions." |

## Fact check of spoken claims
| Claim | Source in `results/results.json` | Value |
|---|---|---|
| FY2005: alarm raised | `E6_early_warning.table` | drift score 0.816 > threshold 0.695 |
| What changed: loan size, credit line, SBA guarantee share | `E5_drift.test_years.2005.top_features` | SBA guarantee share 0.162, revolving-credit flag 0.115, loan size 0.063 |
| Trained on earlier loans, tested on later unseen years | `config` | train FY2001–02, calibrate FY2003, test FY2004–10 |
| AUC 0.62 to 0.66 vs. 0.53 and 0.54 (industry rule), FY2004–07 | `E4_models` | model 0.618–0.664; industry rule 0.525–0.543 |
| First alarm in FY2005, same year as a simpler default monitor | `E6_early_warning.summary` | first drift alarm 2005; first label-monitor alarm 2005 |
| Historical loan outcomes are incomplete | `audit.json` E3; decision log D3 | file keeps only loans resolved by 2014 |

## What not to say in a live demo
- "Early warning", "predicted the crisis", "prevents losses": not supported.
- "The alarm beat PSI": PSI and the alarm fired in the same years.
- "$5.7B was lost": that figure is gross charged-off principal, before recoveries.

## Finals (5 minutes + Q&A)
Same structure, with more time on the loan-term field (suspected contamination, not proven leakage), the threshold
derivation and its uncertainty, and the Limitations section. Keep `dashboard/index.html` open locally as a backup:
numbers, examples and tables work offline; only charts need internet.
