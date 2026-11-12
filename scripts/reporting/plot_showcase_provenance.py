"""Draw the README's Slack 07 provenance figure from the public trace."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as PlotPath

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "demo/data/case_slack_07.json"
OUTPUT = ROOT / "docs/assets/research-showcase/provenance-preview.png"

EDGE_STYLES = {
    "peer": ("#225aa8", "-", "智能体消息"),
    "read": ("#08756b", (0, (3.2, 2.4)), "读取外部网页"),
    "target": ("#ad5515", "-", "目标工具调用"),
}

# Paths and label positions use the figure coordinate system.
ROUTES = {
    "read_agent_0": ([(1.90, 2.32), (3.22, 2.32)], (2.55, 2.52)),
    "read_agent_1": ([(1.24, 2.66), (2.42, 4.13), (4.65, 4.48), (6.26, 3.94)], (4.03, 4.33)),
    "read_agent_2": ([(1.24, 1.98), (2.42, 0.51), (4.65, 0.16), (6.26, 0.70)], (4.03, 0.27)),
    "m_1": ([(4.91, 2.57), (5.32, 3.19), (5.54, 3.47), (6.03, 3.72)], (5.31, 3.44)),
    "m_3": ([(6.03, 3.39), (5.64, 3.14), (5.40, 2.91), (4.91, 2.43)], (5.74, 2.95)),
    "m_2": ([(4.91, 2.07), (5.32, 1.45), (5.54, 1.17), (6.03, 0.92)], (5.31, 1.20)),
    "m_4": ([(6.03, 1.25), (5.64, 1.50), (5.40, 1.73), (4.91, 2.21)], (5.74, 1.69)),
    "target_agent_0": ([(4.91, 2.32), (8.49, 2.32)], (6.87, 2.56)),
    "target_agent_2": ([(7.61, 1.04), (8.18, 1.04), (8.74, 1.60), (8.99, 1.98)], (8.44, 1.18)),
}

NODES = (
    ((1.05, 2.32), 1.70, "外部网页", "#e9f6f2", "#08756b"),
    ((4.065, 2.32), 1.69, "主 Agent", "#edf3fd", "#225aa8"),
    ((6.82, 3.60), 1.58, "Agent 1", "#edf3fd", "#225aa8"),
    ((6.82, 1.04), 1.58, "Agent 2", "#edf3fd", "#225aa8"),
    ((9.33, 2.32), 1.68, "目标调用", "#fff3e6", "#ad5515"),
)


def select_font():
    installed = {font.name for font in font_manager.fontManager.ttflist}
    for name in ("Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "SimHei"):
        if name in installed:
            return name
    raise RuntimeError("Install a Simplified Chinese font such as Noto Sans CJK SC.")


def draw_edge(axes, edge):
    points, label_position = ROUTES[edge["id"]]
    color, linestyle, _ = EDGE_STYLES[edge["kind"]]
    segments = [PlotPath.LINETO] if len(points) == 2 else [PlotPath.CURVE4] * 3
    path = PlotPath(points, [PlotPath.MOVETO, *segments])
    axes.add_patch(FancyArrowPatch(
        path=path, arrowstyle="-|>", mutation_scale=14, linewidth=2.0,
        color=color, linestyle=linestyle, zorder=1,
    ))
    label = edge["id"] if edge["kind"] == "peer" else " / ".join(f"#{n}" for n in edge["calls"])
    if edge["id"] == "target_agent_0":
        label += "  首次委派前"
    axes.text(*label_position, label, fontsize=13, color=color, ha="center", va="center", zorder=4)


def main():
    case = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert {edge["id"] for edge in case["edges"]} == ROUTES.keys(), "Unexpected Slack 07 edges"
    plt.switch_backend("Agg")
    plt.rcParams.update({"font.family": select_font(), "text.color": "#172d46"})
    figure = plt.figure(figsize=(10.4, 5.2), facecolor="white")
    axes = figure.add_axes((0, 0, 1, 1), xlim=(0, 10.4), ylim=(-0.57, 4.63))
    axes.set_axis_off()

    for edge in case["edges"]:
        draw_edge(axes, edge)
    for (x, y), width, label, fill, border in NODES:
        axes.add_patch(FancyBboxPatch(
            (x - width / 2, y - 0.34), width, 0.68,
            boxstyle="round,pad=0,rounding_size=0.12", facecolor=fill,
            edgecolor=border, linewidth=1.3, zorder=2,
        ))
        axes.text(x, y, label, fontsize=17, fontweight="bold", ha="center", va="center", zorder=3)

    for x, (color, linestyle, label) in zip((0.34, 3.42, 6.55), EDGE_STYLES.values(), strict=True):
        axes.plot((x, x + 0.48), (-0.27, -0.27), color=color, linestyle=linestyle, linewidth=2.3)
        axes.text(x + 0.63, -0.27, label, fontsize=14, va="center")

    figure.savefig(OUTPUT, dpi=300, metadata={"Title": "Slack 07 information provenance"})
    plt.close(figure)


if __name__ == "__main__":
    main()
