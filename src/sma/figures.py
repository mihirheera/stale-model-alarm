"""Make the static figures used in the README and write-up, from results/results.json.

Run:  python -m sma.figures
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import config  # noqa: E402

BLUE, GREY, RED = "#2563eb", "#9ca3af", "#b91c1c"


def _style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb")
    ax.axvspan(2007.5, 2010.5, color="#f3f4f6", zorder=0)
    ax.text(2009, ax.get_ylim()[1] * 0.97, "outcome-incomplete\n(interpret with care)", ha="center",
            va="top", fontsize=8, color="#6b7280")


def main():
    r = json.loads((config.RESULTS_DIR / "results.json").read_text())
    t = r["E6_early_warning"]["table"]
    yrs = [x["fy"] for x in t]
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. actual vs predicted default rate
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(yrs, [100 * x["actual_rate"] for x in t], "-o", color=BLUE, lw=2.5, label="Actual (loans in file)")
    lb = [(x["fy"], 100 * x["actual_rate_lower_bound"]) for x in t if x["actual_rate_lower_bound"]]
    ax.plot([a for a, _ in lb], [b for _, b in lb], "v", color=BLUE, ms=8, mfc="white",
            label="Actual, conservative lower bound")
    ax.plot(yrs, [100 * x["predicted_rate"] for x in t], "-o", color=GREY, lw=2, label="Model predicted")
    ax.set_ylim(0, 50)
    _style(ax, "The model kept expecting ~15-17% defaults while far more happened", "Default rate (%)")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "default_rates.png", dpi=160)

    # 2. AUC for model vs baselines
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for name, color, style in [("Gradient boosting", BLUE, "-o"), ("Logistic regression", "#60a5fa", "--o"),
                               ("Industry rule", GREY, "-s"), ("Majority baseline", "#d1d5db", ":")]:
        by = r["E4_models"][name]["by_year"]
        ax.plot(yrs, [by[str(y)]["auc"] for y in yrs], style, color=color, lw=2, label=name)
    ax.set_ylim(0.45, 0.75)
    _style(ax, "Ranking quality (AUC) declined slowly; both ML models beat the baselines", "ROC-AUC")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "auc.png", dpi=160)

    # 3. drift score with threshold
    fig, ax = plt.subplots(figsize=(8, 4.2))
    thr = r["E5_drift"]["adv_threshold"]
    ax.plot(yrs, [x["adv_auc"] for x in t], "-o", color=BLUE, lw=2.5, label="Drift score (adversarial AUC)")
    ax.axhline(thr, color=RED, ls="--", lw=1.2)
    ax.text(2004, thr + 0.01, f"alarm threshold {thr:.3f} (set from FY2001-03 only)", color=RED, fontsize=8)
    ax.axhline(0.5, color=GREY, ls=":", lw=1)
    ax.text(2004, 0.51, "0.5 = no detectable difference", color="#6b7280", fontsize=8)
    ax.set_ylim(0.45, 1.0)
    _style(ax, "This year's applicants vs. the training years: how different?", "Adversarial-validation AUC")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "drift.png", dpi=160)
    print("saved figures to", config.FIGURES_DIR)


if __name__ == "__main__":
    main()
