# Two-minute demo script

Follows the official structure: problem 15 s · demo 60 s · how it works 30 s · next steps 15 s.
About 270 spoken words; read at a steady 135 words a minute. Every number is in `results/results.json` and visible on
the dashboard at the moment it is spoken.

**Before recording:** open
https://mihirheera.github.io/stale-model-alarm/dashboard/index.html?fy=2004 in Chrome (window at least 1,280 px wide,
100% zoom) and wait for the charts to load. The year buttons and the section menu stay pinned to the top.

| Time | On screen (exact action) | Voiceover |
|---|---|---|
| 0:00–0:15 **Problem** | Top of the page, FY2004 selected. Do not click. | "A community bank's credit-risk analyst relies on a model trained on past loans. But defaults only show up years later, so the model can go out of date unnoticed. Stale Model Alarm helps the analyst check." |
| 0:15–0:32 **Demo** | Move the pointer along the intro line under the header, then the header text "risk model trained FY2001–2002". | "This dashboard replays real SBA small-business loans. Model one, trained on 2001 and 2002, predicts each loan's default risk. Model two compares application forms only: do this year's applicants still resemble the ones model one was built from?" |
| 0:32–0:46 | Click **FY2005**. The status panel turns red (CRITICAL). Point at the **Drift score 0.816** cell ("threshold 0.695; above by 0.121"). | "I select fiscal year 2005. The status turns critical: the drift score is 0.816, above the 0.695 alarm line set from earlier years only. No repayment data was needed." |
| 0:46–0:54 | Point at **Predicted default rate 16.4%**, then **Observed default rate 25.3%**. | "Years later, the outcomes arrived: the model predicted 16.4 percent would default; 25.3 percent did." |
| 0:54–1:06 | Click **Evidence** in the menu. Point at "Applicant characteristics that changed": SBA guarantee share, Revolving-credit flag. | "The evidence shows what changed most: the SBA guarantee share and how credit lines were recorded. That is a reason to review the model, not proof of higher risk." |
| 1:06–1:15 | Click **Loans**. Point at the left card: $50,000, MODEL PREDICTION 12.6%, HISTORICAL OUTCOME Charged off. | "One real loan: fifty thousand dollars, scored 12.6 percent, not flagged. It was charged off." |
| 1:15–1:45 **How it works** | Click **Performance**: point at the AUC chart (dark model line above the grey industry-rule line, FY2004–07). At "Model two", click **Drift** to show the two method panels. | "Model one is gradient boosting on thirteen application details. On years it never saw, 2004 to 2007, it ranked loans better than both simple baselines: AUC 0.62 to 0.66, against about 0.53 for an industry lookup table and 0.5 for the average rate. But its percentages fell far behind. Model two is a second classifier, checked against the standard PSI test and a simple count of early defaults." |
| 1:45–2:00 **Next steps** | Click **Limitations**. Leave "No earlier warning has been shown" and "The alert threshold is preliminary" on screen. | "The main limitation: that simple default count also first fired in 2005, so my alarm was not earlier, and its threshold rests on three reference years. Next, I would test newer SBA data. This is a prototype, not financial advice." |

**If it runs long:** drop "and 0.5 for the average rate" (about 3 seconds).

## Fact check
| Spoken claim | Source in `results/results.json` | Value |
|---|---|---|
| Trained on 2001 and 2002 | `config.train_years` | [2001, 2002]; 81,624 loans |
| FY2005 status critical | `E6_early_warning.table` | "Drift detected, performance has deteriorated" |
| Drift score 0.816; alarm line 0.695 | `E5_drift.test_years.2005.adv_auc`; `E5_drift.adv_threshold` | 0.816; 0.695 (largest of FY2001 0.671, FY2002 0.586, FY2003 0.695) |
| Predicted 16.4%, observed 25.3% | `E6` table, FY2005 | 0.164; 0.253 |
| What changed most | `E5_drift.test_years.2005.top_features` | SBA guarantee share 0.162, revolving-credit flag 0.115 |
| $50,000 loan, 12.6%, not flagged, charged off | `E10_examples.by_year.2005.missed_default` | $50,000; 0.126 (cut-off 0.170) |
| Thirteen application details | `config.features` | 13 |
| AUC 0.62–0.66 vs. about 0.53 and 0.5 | `E4_models` FY2004–07 | model 0.618–0.664; industry rule 0.525–0.543; average rate 0.500 |
| Percentages fell far behind | `E6` table `calib_ratio` | 1.21 → 2.44 |
| Default count also first fired in 2005 | `E6.summary` | drift 2005; label monitor 2005; PSI 2005 |
| Three reference years | `E5_drift.normal_years` | FY2001, FY2002, FY2003 |

## What not to say
- "Early warning", "predicted the crisis", "prevents losses": none of these is supported.
- "The alarm beat PSI": PSI and the alarm fired in exactly the same years.
- "$5.7B was lost": that figure is gross charged-off principal, before recoveries.

## Finals (5 minutes + Q&A)
Same structure, with more time on: the loan-term field (0.96 vs. 0.64 AUC, and why it is only *suspected*
contamination), the threshold derivation and its uncertainty (Drift section), and the Limitations section. Keep
`dashboard/index.html` open locally as a backup: the numbers, examples and tables work offline; only charts need internet.
