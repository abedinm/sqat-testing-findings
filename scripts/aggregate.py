#!/usr/bin/env python3
"""
aggregate.py - roll per-run summaries up into per-cell statistics and cross-arm figures.

Reads a matrix index.csv (written by run_matrix.ps1), discards run 1 of every cell as
warm-up, and reports mean +/- spread across the surviving repeats.

Also produces the figure this paper is built around: mean response time versus p99 as the
dataset grows. If the thesis holds, the mean line stays comparatively flat while p99
diverges.

Usage:
    python aggregate.py results/matrix/index.csv --out results/matrix/aggregate.json
    python aggregate.py results/scaled/index.csv --out results/scaled/aggregate.json --scale-figure
"""

import argparse
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(index_csv):
    df = pd.read_csv(index_csv)
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("index_csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale-figure", action="store_true",
                    help="treat the tag column as a dataset scale and plot mean vs p99")
    ap.add_argument("--figdir", default=None)
    args = ap.parse_args()

    if not os.path.exists(args.index_csv):
        sys.exit(f"ERROR: {args.index_csv} not found")

    df = load(args.index_csv)
    total_rows = len(df)
    ok = df[df["status"] == "OK"].copy()
    failed = df[df["status"] != "OK"]

    if ok.empty:
        sys.exit(f"ERROR: no rows with status OK in {args.index_csv} "
                 f"({total_rows} rows, {len(failed)} failed). Nothing to aggregate.")

    kept = ok[ok["is_warmup"].astype(str).str.lower() != "true"].copy()
    discarded = len(ok) - len(kept)

    num_cols = ["requests", "rps", "failed_rate", "p50_ms", "avg_ms",
                "p90_ms", "p95_ms", "p99_ms", "max_ms", "cores_used"]
    for c in num_cols:
        if c in kept:
            kept[c] = pd.to_numeric(kept[c], errors="coerce")

    cells = []
    for (tag, route, vus), g in kept.groupby(["tag", "route", "vus"], sort=False):
        cell = {
            "tag": tag, "route": route, "vus": int(vus),
            "runs_kept": int(len(g)),
            "total_requests": int(g["requests"].sum()),
            "max_failed_rate": float(g["failed_rate"].max()),
        }
        for c in ["rps", "p50_ms", "avg_ms", "p90_ms", "p95_ms", "p99_ms", "max_ms", "cores_used"]:
            vals = g[c].dropna().values
            if len(vals):
                cell[f"{c}_mean"] = round(float(vals.mean()), 4)
                cell[f"{c}_min"] = round(float(vals.min()), 4)
                cell[f"{c}_max"] = round(float(vals.max()), 4)
                cell[f"{c}_sd"] = round(float(vals.std(ddof=1)), 4) if len(vals) > 1 else 0.0
        if cell.get("avg_ms_mean"):
            cell["p99_over_mean"] = round(cell["p99_ms_mean"] / cell["avg_ms_mean"], 4)
        if cell.get("p50_ms_mean"):
            cell["p99_over_p50"] = round(cell["p99_ms_mean"] / cell["p50_ms_mean"], 4)
        cells.append(cell)

    result = {
        "source": args.index_csv,
        "rows_total": total_rows,
        "rows_ok": int(len(ok)),
        "rows_failed": int(len(failed)),
        "warmup_runs_discarded": int(discarded),
        "cells": cells,
    }
    if len(failed):
        result["failures"] = failed.to_dict(orient="records")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(f"{args.index_csv}")
    print(f"  rows {total_rows}  ok {len(ok)}  failed {len(failed)}  warmups discarded {discarded}")
    print()
    hdr = f"  {'tag':<14} {'route':<16} {'vus':>4} {'n':>2} {'rps':>8} {'mean':>9} {'p50':>9} {'p95':>9} {'p99':>9} {'p99/mean':>9}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for c in cells:
        print(f"  {c['tag']:<14} {c['route']:<16} {c['vus']:>4} {c['runs_kept']:>2} "
              f"{c.get('rps_mean', float('nan')):>8.0f} {c.get('avg_ms_mean', float('nan')):>9.3f} "
              f"{c.get('p50_ms_mean', float('nan')):>9.3f} {c.get('p95_ms_mean', float('nan')):>9.3f} "
              f"{c.get('p99_ms_mean', float('nan')):>9.3f} {c.get('p99_over_mean', float('nan')):>9.2f}")
    if len(failed):
        print()
        print(f"  {len(failed)} FAILED run(s) recorded in the aggregate under 'failures'")

    # ---- mean vs p99 across dataset scale --------------------------------
    if args.scale_figure:
        figdir = args.figdir or os.path.join(os.path.dirname(os.path.abspath(args.out)), "figures")
        os.makedirs(figdir, exist_ok=True)
        by_route = {}
        for c in cells:
            m = re.search(r"x(\d+)", c["tag"])
            if not m:
                continue
            by_route.setdefault(c["route"], []).append((int(m.group(1)), c))
        made = []
        for route, items in by_route.items():
            items.sort(key=lambda t: t[0])
            scales = [i[0] for i in items]
            means = [i[1].get("avg_ms_mean") for i in items]
            p50s = [i[1].get("p50_ms_mean") for i in items]
            p99s = [i[1].get("p99_ms_mean") for i in items]
            if len(scales) < 2:
                continue
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.plot(scales, means, "o-", lw=2, color="#2b6cb0", label="mean")
            ax.plot(scales, p50s, "s--", lw=1.4, color="#38a169", label="p50")
            ax.plot(scales, p99s, "^-", lw=2, color="#e53e3e", label="p99")
            ax.set_xscale("log"); ax.set_yscale("log")
            ax.set_xlabel("Dataset scale (x baseline records)")
            ax.set_ylabel("Response time (ms, log)")
            ax.set_title(f"Mean vs p99 as dataset grows — {route}")
            ax.grid(alpha=0.3, which="both"); ax.legend()
            fig.tight_layout()
            slug = re.sub(r"[^a-z0-9]+", "_", route.lower()).strip("_")
            p = os.path.join(figdir, f"mean_vs_p99_{slug}.png")
            fig.savefig(p, dpi=150); plt.close(fig); made.append(p)

            # divergence ratio on its own axis
            fig, ax = plt.subplots(figsize=(8, 3.6))
            ratios = [i[1].get("p99_over_mean") for i in items]
            ax.plot(scales, ratios, "o-", lw=2, color="#805ad5")
            ax.set_xscale("log")
            ax.set_xlabel("Dataset scale (x baseline records)")
            ax.set_ylabel("p99 / mean")
            ax.set_title(f"Tail divergence vs dataset scale — {route}")
            ax.grid(alpha=0.3, which="both")
            fig.tight_layout()
            p = os.path.join(figdir, f"divergence_{slug}.png")
            fig.savefig(p, dpi=150); plt.close(fig); made.append(p)
        for p in made:
            print(f"  figure -> {p}")

    print()
    print(f"  aggregate -> {args.out}")


if __name__ == "__main__":
    main()
