"""Render the README's cost–utility plot from the archived experiment overview."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "reports/2026-10-29-completed-experiments/overview.csv"
OUTPUT = ROOT / "docs/assets/research-showcase/worker-tradeoff.svg"

# Names, colors, shapes and offsets affect presentation only.
STYLES = {
    "F": ("F · On demand", "#12698e", "o", (12, 0), "left"),
    "W": ("W · Fixed two", "#08745f", "s", (12, 0), "left"),
    "flash16k_adaptive": ("Native adaptive", "#566578", "D", (-12, 0), "right"),
}


def main():
    with SOURCE.open(encoding="utf-8", newline="") as source:
        runs = {row["run"]: row for row in csv.DictReader(source)}

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.labelcolor": "#26364b",
        "xtick.color": "#45556a",
        "ytick.color": "#45556a",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#9aabc0",
        "svg.hashsalt": "manta-agentdojo-readme-tradeoff",
    })
    figure, axes = plt.subplots(figsize=(7.8, 3.4), layout="constrained")
    axes.set_xlabel("Total tokens, Clean + Attack (millions)", labelpad=9)
    axes.set_ylabel("Attack Utility", labelpad=9)
    axes.set_xlim(0, 32)
    axes.set_ylim(79, 97)
    axes.set_xticks(range(0, 33, 4))
    axes.set_yticks(range(80, 97, 4))
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    axes.grid(axis="both", color="#dce5ef", linewidth=0.75)
    axes.set_axisbelow(True)
    axes.tick_params(length=0, pad=7)
    for key, (name, color, marker, offset, alignment) in STYLES.items():
        row = runs[key]
        tokens = int(row["total_tokens"]) / 1_000_000
        utility = int(row["attack_successful_tasks"]) / int(row["attack_n"]) * 100
        axes.scatter(tokens, utility, s=82, c=color, marker=marker, edgecolors="white", linewidths=0.8, zorder=3)
        axes.annotate(name, (tokens, utility), xytext=offset, textcoords="offset points",
                      color=color, fontweight="bold", ha=alignment, va="center")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, metadata={"Date": None, "Description": "AgentDojo Flash 16K configuration comparison"})
    # Matplotlib leaves spaces at line endings inside SVG path data.
    svg = OUTPUT.read_text(encoding="utf-8")
    OUTPUT.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n", encoding="utf-8", newline="\n")
    plt.close(figure)


if __name__ == "__main__":
    main()
