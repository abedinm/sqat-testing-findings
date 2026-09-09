#!/usr/bin/env python3
"""
make_figures.py - regenerate every paper figure from current data.

Exists because one figure (Arm B) was generated before extra runs were added and then
disagreed with the table in the text it illustrated. Figures are rebuilt from
paper/facts.json, the same source the prose is substituted from, so text and figures
cannot drift apart again.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
R = lambda *p: os.path.join(ROOT, *p)
OUT = R("results", "figures")
os.makedirs(OUT, exist_ok=True)

F = json.load(open(R("paper", "facts.json"), encoding="utf-8"))["facts"]
BLUE, RED, GREEN, PURPLE, GREY = "#2b6cb0", "#c53030", "#2f855a", "#6b46c1", "#4a5568"
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.25,
                     "axes.spines.top": False, "axes.spines.right": False})
made = []


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=170, bbox_inches="tight")
    plt.close(fig)
    made.append(p)


# --------------------------------------------------- Arm B (regenerated, current data)
fig, axes = plt.subplots(1, 4, figsize=(11, 3.2))
panels = [("Mean response time (ms)", F["armb_disabled_mean"], F["armb_enabled_mean"]),
          ("p99 (ms)", F["armb_disabled_p99"], F["armb_enabled_p99"]),
          ("Throughput (req/s)", F["armb_disabled_rps"], F["armb_enabled_rps"]),
          ("Error rate (%)", F["armb_disabled_failed_pct"], F["armb_enabled_failed_pct"])]
for ax, (title, off, on) in zip(axes, panels):
    bars = ax.bar(["limiter\noff", "limiter\non"], [off, on], color=[BLUE, RED], width=0.6)
    ax.set_title(title, fontsize=9.5)
    for b, v in zip(bars, [off, on]):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.2f}" if v < 100 else f"{v:,.0f}",
                ha="center", va="bottom", fontsize=8.5)
    ax.set_ylim(0, max(off, on) * 1.3 if max(off, on) else 1)
fig.suptitle("Arm B: turning the rate limiter on improves every latency and throughput "
             "metric while the service stops returning data", fontsize=10)
save(fig, "fig_armb_rate_limiter.png")

# --------------------------------------------------- Arm C percentile ladder (NEW)
order = [("uniform_cheap", "100% cheap"), ("mix_0p1pct", "0.1% slow"),
         ("mix_1pct", "1% slow"), ("mix_10pct", "10% slow"),
         ("uniform_expensive", "100% expensive")]
# p50 is omitted: it is 0.000 ms for three of the five workloads (the median request
# completes below the timer's resolution) and cannot be placed on a log axis. The value
# appears in the table in the text.
stats = ["mean", "p90", "p99", "p999", "p9999"]
labels = ["mean", "p90", "p99", "p99.9", "p99.99"]
fig, ax = plt.subplots(figsize=(8.4, 4.4))
x = np.arange(len(stats))
for (key, lab), c, mk in zip(order, [GREY, GREEN, BLUE, PURPLE, RED], "os^Dv"):
    ys = [F.get(f"ladder_{key}_{s}") for s in stats]
    ax.plot(x, ys, marker=mk, lw=1.8, ms=5, color=c, label=lab)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_yscale("log")
ax.set_ylabel("Response time (ms, log scale)")
ax.set_xlabel("Statistic")
ax.set_title("Arm C: a slow path is invisible to any percentile below its own incidence")
ax.legend(title="workload", fontsize=8, title_fontsize=8.5)
ax.annotate("at p99 the 0.1% workload is\nindistinguishable from one\nwith no slow path at all",
            xy=(2, F["ladder_mix_0p1pct_p99"]), xytext=(0.05, 6.0),
            fontsize=8, color=GREY,
            arrowprops=dict(arrowstyle="->", color=GREY, lw=1,
                            connectionstyle="arc3,rad=-0.2"))
save(fig, "fig_armc_percentile_ladder.png")

# --------------------------------------------------- Arm E open vs closed (NEW)
rates = [600, 1100, 1400]
means = [F[f"arme_{r}_mean"] for r in rates]
p99s = [F[f"arme_{r}_p99"] for r in rates]
dropped = [F[f"arme_{r}_dropped"] for r in rates]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
a1.plot(rates, means, "o-", color=BLUE, lw=2, label="mean (open model)")
a1.plot(rates, p99s, "^-", color=RED, lw=2, label="p99 (open model)")
a1.axhline(F["arma_api_content_v8_mean"], ls="--", lw=1.2, color=GREY,
           label="mean (closed model, 8 VUs)")
a1.set_yscale("log"); a1.set_xlabel("Offered rate (req/s)")
a1.set_ylabel("Response time (ms, log)")
a1.set_title("Latency past the saturation point")
a1.legend(fontsize=7.5)
a1.axvspan(1174, 1450, color=RED, alpha=0.07)
a1.text(1180, max(p99s) * 0.5, "beyond\nsustainable\nthroughput", fontsize=7.5, color=GREY)
bars = a2.bar([str(r) for r in rates], dropped, color=[GREEN, GREEN, RED], width=0.55)
for b, v in zip(bars, dropped):
    a2.text(b.get_x() + b.get_width() / 2, v, f"{v:,}", ha="center", va="bottom", fontsize=8.5)
a2.set_xlabel("Offered rate (req/s)"); a2.set_ylabel("Iterations the generator could not place")
a2.set_title("Dropped iterations")
a2.set_ylim(0, max(dropped) * 1.25 if max(dropped) else 1)
fig.suptitle("Arm E: an open-model test reveals a saturation cliff that a closed-model "
             "test cannot produce", fontsize=10)
save(fig, "fig_arme_open_vs_closed.png")

# --------------------------------------------------- Arm A divergence by route (NEW)
routes = [("services_html", "/services.html"), ("api_content", "/api/content"),
          ("sitemap_xml", "/sitemap.xml")]
vus = [2, 8, 16]
fig, (b1, b2) = plt.subplots(1, 2, figsize=(10, 3.6))
w = 0.26
for i, (slug, lab) in enumerate(routes):
    m = [F[f"arma_{slug}_v{v}_mean"] for v in vus]
    p = [F[f"arma_{slug}_v{v}_p99"] for v in vus]
    xs = np.arange(len(vus)) + (i - 1) * w
    b1.bar(xs, m, width=w, label=lab)
    b2.plot(vus, [F[f"arma_{slug}_v{v}_ratio"] for v in vus], "o-", lw=1.8, label=lab)
b1.set_xticks(np.arange(len(vus))); b1.set_xticklabels([f"{v} VUs" for v in vus])
b1.set_ylabel("Mean response time (ms)"); b1.set_title("Mean by route and load")
b1.legend(fontsize=7.5)
b2.set_xlabel("Virtual users"); b2.set_ylabel("p99 / mean")
b2.set_title("Tail divergence falls as load rises")
b2.set_xticks(vus); b2.legend(fontsize=7.5)
fig.suptitle("Arm A: absolute latency rises with load while the tail becomes relatively "
             "less extreme", fontsize=10)
save(fig, "fig_arma_matrix.png")


# --------------------------------------------- Arm C: CV fails, the tail does not (NEW)
# Reported in §5.10. The coefficient of variation runs the wrong way against slow-path
# incidence, so it is plotted beside a statistic that does track, to make the contrast
# the point of the figure rather than an aside in the text.
ladder = [("uniform_cheap", "0%\n(none)"), ("mix_0p1pct", "0.1%"), ("mix_1pct", "1%"),
          ("mix_10pct", "10%"), ("uniform_expensive", "100%")]
x = np.arange(len(ladder))
cv = [F[f"ladder_{k}_cv"] for k, _ in ladder]
p999 = [F[f"ladder_{k}_p999"] for k, _ in ladder]

fig, (c1, c2) = plt.subplots(1, 2, figsize=(10, 3.6))
bars = c1.bar(x, cv, color=[RED] + [GREY] * 3 + [GREEN], width=0.6)
for b, v in zip(bars, cv):
    c1.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8.5)
c1.set_xticks(x); c1.set_xticklabels([l for _, l in ladder])
c1.set_xlabel("Fraction of requests on the slow path")
c1.set_ylabel("Coefficient of variation")
c1.set_title("CV: highest where there is no slow path")
c1.set_ylim(0, max(cv) * 1.28)
c1.annotate("healthiest workload,\nscored most variable",
            xy=(0, cv[0]), xytext=(1.15, cv[0] * 1.02), fontsize=8, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED, lw=1))

c2.plot(x, p999, "o-", color=BLUE, lw=2, ms=6)
for xi, v in zip(x, p999):
    c2.text(xi, v, f"  {v:.2f}", fontsize=8.5, va="center", ha="left", color=GREY)
c2.set_xticks(x); c2.set_xticklabels([l for _, l in ladder])
c2.set_xlabel("Fraction of requests on the slow path")
c2.set_ylabel("p99.9 (ms)")
c2.set_title("p99.9: rises with incidence, as expected")
c2.set_xlim(-0.35, len(ladder) - 0.35)

fig.suptitle("Arm C: the coefficient of variation runs backwards against slow-path "
             "incidence; a high percentile does not", fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.93])
save(fig, "fig_armc_cv_failure.png")

print(f"regenerated {len(made)} figures from current facts.json:")
for p in made:
    print("  ", os.path.relpath(p, ROOT))
