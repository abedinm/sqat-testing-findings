#!/usr/bin/env python3
"""
make_diagrams.py - the two schematic figures the paper needs but had only as prose.

Request path: where the per-request cost is incurred. The study rests on getContent()
running on every request, which was previously described in words only.
Experimental design: what each arm holds constant and what it varies.

Drawn with matplotlib so they regenerate alongside every other figure.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "results", "figures")
os.makedirs(OUT, exist_ok=True)

INK, BLUE, RED, GREEN, PURPLE, LGREY = ("#1a202c", "#2b6cb0", "#c53030",
                                        "#2f855a", "#6b46c1", "#edf2f7")


def box(ax, x, y, w, h, text, fc="white", ec=INK, fs=8.5, bold=False, lw=1.1):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.012,rounding_size=0.02",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=INK, zorder=3, fontweight="bold" if bold else "normal",
                linespacing=1.45)


def arrow(ax, p1, p2, color=INK, lw=1.1):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11,
                                 color=color, lw=lw, shrinkA=2, shrinkB=2, zorder=1))


# ------------------------------------------------------------- request path
fig, ax = plt.subplots(figsize=(9.6, 3.4))
ax.set_xlim(0, 10.6)
ax.set_ylim(0, 3.2)
ax.axis("off")

box(ax, 0.10, 1.30, 1.35, 0.70, "k6\nvirtual user", fc=LGREY)
box(ax, 1.95, 1.30, 1.55, 0.70, "serve.mjs\nrouter", bold=True)
box(ax, 4.05, 2.25, 2.30, 0.62, "JSON API handler\n/api/content, /api/search", fs=8.0)
box(ax, 4.05, 0.35, 2.30, 0.62, "static HTML handler\n22 pages", fs=8.0)
box(ax, 4.05, 1.32, 2.30, 0.62, "injectSEO()\nrewrites the HTML", fc="#fff5f5", ec=RED,
    fs=8.0)
box(ax, 7.00, 1.30, 2.15, 0.70, "getContent()\nreadFile + JSON.parse", fc="#fff5f5",
    ec=RED, bold=True, fs=8.2)
box(ax, 9.45, 1.30, 1.05, 0.70, "content.json\n88,826 B", fc=LGREY, fs=7.6)

arrow(ax, (1.45, 1.65), (1.95, 1.65))
arrow(ax, (3.50, 1.80), (4.05, 2.45))
arrow(ax, (3.50, 1.50), (4.05, 0.75))
arrow(ax, (5.20, 0.97), (5.20, 1.32), color=RED)
arrow(ax, (6.35, 2.45), (7.00, 1.95), color=RED)
arrow(ax, (6.35, 1.63), (7.00, 1.63), color=RED)
arrow(ax, (9.15, 1.65), (9.45, 1.65))

ax.text(8.07, 1.05, "no cache: repeated on every request", ha="center", fontsize=7.6,
        color=RED, style="italic")
ax.text(5.30, 2.98, "Both request classes converge on the same uncached read and parse.",
        ha="center", fontsize=8.4, color=INK)
fig.tight_layout()
p1 = os.path.join(OUT, "fig_request_path.png")
fig.savefig(p1, dpi=170, bbox_inches="tight")
plt.close(fig)

# -------------------------------------------------------- experimental design
fig, ax = plt.subplots(figsize=(9.4, 4.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4.9)
ax.axis("off")

box(ax, 3.30, 4.10, 3.40, 0.58, "One application, one host\nsix controlled arms",
    bold=True, fc=LGREY, fs=8.6)

arms = [
    (0.10, 2.55, "Calibration", "concurrency\n1 to 200 VUs", "locate the knee", BLUE),
    (2.55, 2.55, "Arm A", "concurrency x route", "baseline, 45 runs", BLUE),
    (5.00, 2.55, "Stress", "offered arrival rate", "breaking point", RED),
    (7.45, 2.55, "Soak", "time, 3600 s", "H1: degradation", GREEN),
    (0.10, 0.95, "Arm D", "dataset size\nx1 to x1000", "H2: uniform cost", GREEN),
    (2.55, 0.95, "Arm C", "distribution of cost\n0.1% to 100%", "H4: variance", GREEN),
    (5.00, 0.95, "Arm B", "load shedding\non / off", "H3: metrics vs failure", RED),
    (7.45, 0.95, "Arm E", "load model\nopen vs closed", "bounds measurement bias", PURPLE),
]
for x, y, name, var, purpose, col in arms:
    box(ax, x, y, 2.35, 1.20, "", ec=col, lw=1.3)
    ax.text(x + 1.175, y + 0.96, name, ha="center", fontsize=9, fontweight="bold", color=col)
    ax.text(x + 1.175, y + 0.58, var, ha="center", fontsize=7.7, color=INK, linespacing=1.45)
    ax.text(x + 1.175, y + 0.17, purpose, ha="center", fontsize=7.3, color="#4a5568",
            style="italic")
    arrow(ax, (5.00, 4.10), (x + 1.175, y + 1.20), color="#cbd5e0", lw=0.7)

ax.text(5.00, 0.50, "Calibration, Arm A, Stress, Soak and Arm D all vary uniform cost. "
                    "Only Arm C varies how that cost is distributed.",
        ha="center", fontsize=8.2, color=INK)
ax.text(5.00, 0.20, "Arm E measures the bias of the instrument the other arms rely on.",
        ha="center", fontsize=8.2, color=INK, style="italic")
fig.tight_layout()
p2 = os.path.join(OUT, "fig_experimental_design.png")
fig.savefig(p2, dpi=170, bbox_inches="tight")
plt.close(fig)

print("diagrams written:")
for p in (p1, p2):
    print("  ", os.path.relpath(p, ROOT))
