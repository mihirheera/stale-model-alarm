# Rubric mapping

How the submission shows each judging criterion. The official Briefs list four unweighted criteria (technical quality,
impact, creativity, clarity) plus "What every project should show" and the Finance-track requirements. The weights
below are the ones we were told judges will use.

| Criterion | What judges look for | Where we show it | Remaining weakness |
|---|---|---|---|
| **Technical execution (30)** | It works and is well built | One command reruns everything from public data (`python -m sma.pipeline`). 13 automated tests, including leakage guards. Time-based split: train FY01–02, calibrate FY03, test FY04–10. Calibrated probabilities. Bootstrap intervals. The dashboard is generated from `results.json` (no hand-typed numbers) and works offline. "A real input producing a result": dashboard **Real examples** card. Build diagram: README appendix. | Model 1's AUC is modest (0.62–0.66) because the data has no credit scores or financials |
| **Originality (20)** | Fresh take, not a tutorial | Own question (can a model tell it's gone stale?), own data (899k SBA loans across the 2008 crisis), own user (bank model-risk analyst). A second AI audits the first. Alarm threshold set only from normal years. A leak (loan term) found and removed. README "What we added" | Drift detection is a known ML area; the novelty is the application and the honest test against a real crisis |
| **Impact & track fit (20)** | Real problem; safer money decision; beats a simple rule | Dollars: $2.76B expected vs. $5.66B charged off FY2004–07; lenders' own share $0.91B vs. $1.97B (README "The problem", full write-up E9, dashboard tile). Beats the average-rate and industry-rule baselines on AUC, PR-AUC and Brier. Human-in-the-loop: it never decides a loan | Who benefits most is the lender and the SBA (taxpayers); the benefit to borrowers is argued, not measured |
| **Testing & honesty (15)** | Measured it; knows where it fails | Precision and recall for the model and baselines; calibration; a label-monitor comparison; robustness checks (windows, features, thresholds, seeds). Failures stated up front: no lead time, 1/3 false alarms, FY2004 miss, ~40% of defaults missed, FY2010 worse than the rule, group gaps. One wrong example chosen by a fixed rule, with why | One crisis (n = 1); no protected-attribute data |
| **Communication (15)** | Clear write-up and video | README follows the official template, with one bold takeaway and a single results table; details are in `docs/full_writeup.md`. Dashboard with plain-language statuses. 2-minute script in the official 15/60/30/15 structure. Technical guide and 22-question Q&A for finals | The video isn't recorded yet; the README is a bit over one page |

## Official checklist
| Requirement (source) | Met? | Where |
|---|---|---|
| Who is it for? (Briefs §3) | Yes | README "What we built": community-bank credit-risk analyst |
| A real input producing a result (§3) | Yes | Dashboard "Real examples"; README "One loan it got wrong" |
| Beats a simple baseline, both reported (§3, Finance) | Yes | README results table |
| At least one example it gets wrong, and why (§3) | Yes | README "Where it fails"; `results.json` E10 |
| A measure that fits; precision/recall (Finance) | Yes | README table: AUC, precision/recall; full write-up: PR-AUC, Brier |
| Dated data → train earlier, test later (Finance) | Yes | `config.py`, tests |
| "This project is a prototype and is not financial advice." | Yes | README top, dashboard |
| Cite every dataset, tool, AI tool | Yes | README "Sources" (Claude Code included) |
| Write-up of about one page, in the template | Yes, slightly long | README |
| Video ≤ 2 min (optional, recommended) | **To do** | `docs/demo_script.md` |
| Code link viewable by anyone | **To do** | Push to a public GitHub repo |
