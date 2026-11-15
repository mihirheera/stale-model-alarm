"""Build dashboard/index.html from results/results.json.

Run (from the project root):  python dashboard/build_dashboard.py
The page is one self-contained HTML file: open it in any browser, no server needed.
Every number on it is read from results.json - nothing is typed in by hand.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sma.config import SECTOR_NAMES  # noqa: E402

results = json.loads((ROOT / "results" / "results.json").read_text())

# Keep only what the page needs, so the file stays small.
data = {
    "table": results["E6_early_warning"]["table"],
    "summary": results["E6_early_warning"]["summary"],
    "adv_threshold": results["E5_drift"]["adv_threshold"],
    "normal_years": results["E5_drift"]["normal_years"],
    "drift": {fy: {"psi": v["psi"], "top": v["top_features"]} for fy, v in results["E5_drift"]["test_years"].items()},
    "auc": {name: {fy: v["auc"] for fy, v in m["by_year"].items()} for name, m in results["E4_models"].items()},
    "brier": {name: {fy: v["brier"] for fy, v in m["by_year"].items()} for name, m in results["E4_models"].items()},
    "ci": results["E4_models"]["Gradient boosting"]["by_year"],
    "label_monitor": results["label_monitor"]["lag2"]["by_monitor_year"],
    "term_leak": results["E7_robustness"]["term_leak_demo"],
    "config": results["config"],
    "impact": results["E9_financial_impact"],
    "examples": results["E10_examples"],
    "sectors": SECTOR_NAMES,
    "n_raw": json.loads((ROOT / "results" / "audit.json").read_text())["E1_validation"]["raw_rows"],
}

TEMPLATE = (Path(__file__).parent / "template.html").read_text()
html = TEMPLATE.replace("/*__DATA__*/null", json.dumps(data))
(Path(__file__).parent / "index.html").write_text(html)
print("wrote", Path(__file__).parent / "index.html", f"({len(html)//1024} KB)")
