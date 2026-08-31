#!/usr/bin/env python3
"""
analyze_k6.py - percentile / degradation / significance analysis for one k6 run.

Ports the analytical approach of the existing analyze.py (frame-time study) onto web
response times:

  conventional      mean response time, throughput
  tail              p50 / p95 / p99 / p99.9, worst-1% and worst-0.1% mean, std, CV
  spikes            requests exceeding SPIKE_FACTOR x rolling median
  sampling bias     raw percentile vs TIME-QUANTIZED percentile
  degradation       late-window p95 / early-window p95, Mann-Whitney U, effect size

The time-quantization point carries over exactly: percentiles taken over raw samples are
biased because fast periods emit more requests per unit time, so healthy stretches are
over-represented. Reporting both the raw and the time-quantized percentile, and their
difference, shows the size of that bias instead of hiding it.

Input : results/<label>/requests.csv  (ts_iso, elapsed_s, duration_ms, status, expected_response)
Output: results/<label>/metrics.json  and  results/<label>/figures/*.png

Usage:
    python analyze_k6.py results/<label> [--soak] [--window 600]
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SPIKE_FACTOR = 2.0
ROLL_WINDOW = 51
QUANTIZE_MS = 1000.0     # 1 s buckets for unbiased percentiles


def worst_mean(vals, pct):
    """Mean of the slowest `pct` percent of requests (tail-focused summary)."""
    n = max(1, int(len(vals) * pct / 100.0))
    return float(np.sort(vals)[-n:].mean())


def quantized_series(df, bucket_ms=QUANTIZE_MS):
    """One mean-response-time value per fixed time bucket."""
    bucket_s = bucket_ms / 1000.0
    end = df["elapsed_s"].max()
    if not np.isfinite(end) or end <= 0:
        return np.array([])
    bins = np.arange(0, end + bucket_s, bucket_s)
    idx = np.digitize(df["elapsed_s"].values, bins)
    out = []
    for b in range(1, len(bins)):
        sel = df["duration_ms"].values[idx == b]
        if len(sel):
            out.append(sel.mean())
    return np.array(out)


def compute_metrics(df, soak=False, window_s=600):
    rt = df["duration_ms"].values.astype(float)
    n = len(rt)
    span = float(df["elapsed_s"].max() - df["elapsed_s"].min())

    rolling_med = pd.Series(rt).rolling(ROLL_WINDOW, center=True, min_periods=1).median().values
    spikes = rt > (SPIKE_FACTOR * rolling_med)

    q = quantized_series(df)

    ok = (df["expected_response"].astype(str).str.lower() == "true").sum() if "expected_response" in df else n
    status_counts = df["status"].value_counts().to_dict() if "status" in df else {}

    m = {
        "requests": int(n),
        "wall_span_s": round(span, 3),
        "throughput_rps": round(n / span, 2) if span > 0 else None,
        "error_rate_pct": round(100.0 * (1 - ok / n), 4) if n else None,
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},

        # conventional
        "mean_ms": round(float(rt.mean()), 4),
        "median_ms": round(float(np.median(rt)), 4),

        # tail
        "p50_ms": round(float(np.percentile(rt, 50)), 4),
        "p90_ms": round(float(np.percentile(rt, 90)), 4),
        "p95_ms": round(float(np.percentile(rt, 95)), 4),
        "p99_ms": round(float(np.percentile(rt, 99)), 4),
        "p99_9_ms": round(float(np.percentile(rt, 99.9)), 4),
        "max_ms": round(float(rt.max()), 4),
        "worst_1pct_mean_ms": round(worst_mean(rt, 1.0), 4),
        "worst_0p1pct_mean_ms": round(worst_mean(rt, 0.1), 4),
        "std_ms": round(float(rt.std(ddof=1)), 4) if n > 1 else 0.0,
        "cv": round(float(rt.std(ddof=1) / rt.mean()), 4) if n > 1 and rt.mean() else None,

        # the headline ratio for this paper
        "p99_over_mean": round(float(np.percentile(rt, 99) / rt.mean()), 4) if rt.mean() else None,
        "p99_over_p50": round(float(np.percentile(rt, 99) / np.percentile(rt, 50)), 4) if np.percentile(rt, 50) else None,

        # spikes
        "spike_count": int(spikes.sum()),
        "spike_rate_per_min": round(spikes.sum() / (span / 60.0), 2) if span > 0 else None,
        "spike_factor_used": SPIKE_FACTOR,
    }

    # sampling-bias check
    if len(q):
        m["p99_raw_ms"] = m["p99_ms"]
        m["p99_quantized_ms"] = round(float(np.percentile(q, 99)), 4)
        m["quantization_bias_ms"] = round(m["p99_raw_ms"] - m["p99_quantized_ms"], 4)

    if soak:
        t = df["elapsed_s"].values
        end_t = t.max()
        if end_t < 2 * window_s:
            window_s = max(10, int(end_t / 4))
            m["degradation_window_adjusted_to_s"] = window_s

        early = df[t <= window_s]["duration_ms"].values.astype(float)
        late = df[t >= (end_t - window_s)]["duration_ms"].values.astype(float)

        if len(early) > 10 and len(late) > 10:
            m["degradation_window_s"] = window_s
            m["early_mean_ms"] = round(float(early.mean()), 4)
            m["late_mean_ms"] = round(float(late.mean()), 4)
            m["early_p95_ms"] = round(float(np.percentile(early, 95)), 4)
            m["late_p95_ms"] = round(float(np.percentile(late, 95)), 4)
            m["early_p99_ms"] = round(float(np.percentile(early, 99)), 4)
            m["late_p99_ms"] = round(float(np.percentile(late, 99)), 4)
            # as specified: late-window p95 / early-window p95
            m["degradation_ratio_p95"] = round(float(np.percentile(late, 95) / np.percentile(early, 95)), 4)
            m["degradation_ratio_mean"] = round(float(late.mean() / early.mean()), 4)
            m["degradation_pct_p95"] = round(100.0 * (np.percentile(late, 95) / np.percentile(early, 95) - 1), 2)

            try:
                from scipy.stats import mannwhitneyu
                u, p = mannwhitneyu(early, late, alternative="two-sided")
                m["mannwhitney_u"] = float(u)
                m["mannwhitney_p"] = float(p)
                m["significant_at_0.05"] = bool(p < 0.05)
                m["effect_size_r"] = round(1 - (2.0 * u) / (len(early) * len(late)), 4)
            except ImportError:
                m["mannwhitney_note"] = "scipy unavailable"
        else:
            m["degradation_note"] = "insufficient samples in early/late windows"

    return m


def make_plots(df, run_dir, label, soak=False):
    outdir = os.path.join(run_dir, "figures")
    os.makedirs(outdir, exist_ok=True)
    paths = []
    rt = df["duration_ms"].values.astype(float)
    hi = float(np.percentile(rt, 99.9))

    # 1. response time over run
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.plot(df["elapsed_s"], rt, lw=0.3, color="#2b6cb0", alpha=0.8)
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Response time (ms)")
    ax.set_title(f"Response time over run — {label}")
    ax.grid(alpha=0.25)
    ax.set_ylim(0, hi * 1.6 if hi > 0 else 1)
    fig.tight_layout()
    p = os.path.join(outdir, "response_time_series.png")
    fig.savefig(p, dpi=150); plt.close(fig); paths.append(p)

    # 2. distribution with percentile markers
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(rt, bins=140, range=(0, hi * 1.3 if hi > 0 else 1), color="#2b6cb0", alpha=0.85)
    ax.axvline(rt.mean(), color="#000000", ls="-", lw=1.6, label=f"mean = {rt.mean():.2f} ms")
    for pc, c in [(50, "#38a169"), (95, "#dd6b20"), (99, "#e53e3e")]:
        v = np.percentile(rt, pc)
        ax.axvline(v, color=c, ls="--", lw=1.3, label=f"p{pc} = {v:.2f} ms")
    ax.set_xlabel("Response time (ms)"); ax.set_ylabel("Requests")
    ax.set_title(f"Response-time distribution — {label}")
    ax.legend(); ax.grid(alpha=0.25)
    fig.tight_layout()
    p = os.path.join(outdir, "distribution.png")
    fig.savefig(p, dpi=150); plt.close(fig); paths.append(p)

    # 3. degradation curve: binned mean and p99 over time
    end = df["elapsed_s"].max()
    bucket = max(1.0, end / 200.0)
    bins = np.arange(0, end + bucket, bucket)
    idx = np.digitize(df["elapsed_s"].values, bins)
    xs, means, p99s = [], [], []
    for b in range(1, len(bins)):
        sel = rt[idx == b]
        if len(sel) > 3:
            xs.append(bins[b - 1] + bucket / 2)
            means.append(sel.mean())
            p99s.append(np.percentile(sel, 99))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(xs, means, lw=1.6, color="#2b6cb0", label="mean")
    ax.plot(xs, p99s, lw=1.2, color="#e53e3e", alpha=0.85, label="p99")
    ax.set_xlabel("Elapsed time (s)"); ax.set_ylabel("Response time (ms)")
    ax.set_title(f"Performance over sustained load — {label}")
    ax.grid(alpha=0.25); ax.legend(loc="upper left")
    fig.tight_layout()
    p = os.path.join(outdir, "degradation_curve.png")
    fig.savefig(p, dpi=150); plt.close(fig); paths.append(p)

    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--soak", action="store_true")
    ap.add_argument("--window", type=int, default=600)
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()

    csv_path = os.path.join(args.run_dir, "requests.csv")
    if not os.path.exists(csv_path):
        sys.exit(f"ERROR: {csv_path} not found. Run extract_k6.py first.")

    df = pd.read_csv(csv_path)
    if df.empty:
        sys.exit(f"ERROR: {csv_path} has no rows.")
    label = os.path.basename(os.path.normpath(args.run_dir))

    m = compute_metrics(df, soak=args.soak, window_s=args.window)
    m["label"] = label

    out_json = os.path.join(args.run_dir, "metrics.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2)

    figs = [] if args.no_figures else make_plots(df, args.run_dir, label, soak=args.soak)

    print("=" * 64)
    print(f" {label}")
    print("=" * 64)
    print(f"  requests            {m['requests']:>12,}")
    print(f"  span                {m['wall_span_s']:>12.1f} s   ({m['throughput_rps']:,} req/s)")
    print(f"  error rate          {m['error_rate_pct']:>12.4f} %")
    print()
    print("  -- conventional --")
    print(f"  mean                {m['mean_ms']:>12.3f} ms")
    print()
    print("  -- what the mean hides --")
    print(f"  p50                 {m['p50_ms']:>12.3f} ms")
    print(f"  p95                 {m['p95_ms']:>12.3f} ms")
    print(f"  p99                 {m['p99_ms']:>12.3f} ms")
    print(f"  p99.9               {m['p99_9_ms']:>12.3f} ms")
    print(f"  max                 {m['max_ms']:>12.3f} ms")
    print(f"  worst 1% mean       {m['worst_1pct_mean_ms']:>12.3f} ms")
    print(f"  std / CV            {m['std_ms']:>12.3f} ms   {m['cv']}")
    print(f"  p99 / mean          {m['p99_over_mean']:>12.3f} x")
    print(f"  spikes (>2x median) {m['spike_count']:>12,}  ({m['spike_rate_per_min']}/min)")
    if "quantization_bias_ms" in m:
        print()
        print("  -- percentile sampling bias --")
        print(f"  p99 raw             {m['p99_raw_ms']:>12.3f} ms")
        print(f"  p99 time-quantized  {m['p99_quantized_ms']:>12.3f} ms")
        print(f"  bias                {m['quantization_bias_ms']:>12.3f} ms")
    if args.soak and "degradation_ratio_p95" in m:
        print()
        print("  -- sustained load --")
        print(f"  early p95           {m['early_p95_ms']:>12.3f} ms")
        print(f"  late  p95           {m['late_p95_ms']:>12.3f} ms")
        print(f"  degradation (p95)   {m['degradation_ratio_p95']:>12.4f} x  ({m['degradation_pct_p95']:+.2f} %)")
        print(f"  degradation (mean)  {m['degradation_ratio_mean']:>12.4f} x")
        if "mannwhitney_p" in m:
            sig = "YES" if m["significant_at_0.05"] else "no"
            print(f"  Mann-Whitney p      {m['mannwhitney_p']:>12.3e}  (significant: {sig})")
            print(f"  effect size r       {m['effect_size_r']:>12.4f}")
    print()
    print(f"  metrics.json -> {out_json}")
    for f in figs:
        print(f"  figure       -> {f}")


if __name__ == "__main__":
    main()
