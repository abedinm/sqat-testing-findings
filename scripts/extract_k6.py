#!/usr/bin/env python3
"""
extract_k6.py - reduce k6 raw JSON output to a compact per-request time series.

k6's --out json emits ~17 metric points per HTTP request. A 30 s single-VU run against
this SUT produced 122 MB / 515,467 lines. The full load matrix would run to tens of
gigabytes, most of it metrics this study never uses (tls_handshaking, data_sent, vus...).

This extracts ONLY http_req_duration points - which IS the measurement this study is
about - losslessly, into:

    ts_iso, elapsed_s, duration_ms, status, expected_response

Nothing is aggregated, rounded away or sampled: one output row per request. The raw file
can then be deleted, which the caller does explicitly and logs.

Usage:
    python extract_k6.py <raw.json> <out.csv> [--keep-raw]
"""

import argparse
import csv
import gzip
import json
import os
import sys
from datetime import datetime


def open_maybe_gzip(path):
    """k6 writes gzipped JSON when the output filename ends in .gz."""
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def parse_ts(s):
    # k6 emits RFC3339 with variable fractional digits and a timezone offset.
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        # fall back: trim fractional seconds to 6 digits
        if "." in s:
            head, rest = s.split(".", 1)
            digits = ""
            i = 0
            while i < len(rest) and rest[i].isdigit():
                digits += rest[i]
                i += 1
            return datetime.fromisoformat(f"{head}.{digits[:6]}{rest[i:]}")
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("out")
    ap.add_argument("--keep-raw", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.raw):
        sys.exit(f"ERROR: {args.raw} not found")

    raw_size = os.path.getsize(args.raw)
    t0 = None
    n = 0
    lines_seen = 0
    bad = 0

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open_maybe_gzip(args.raw) as fh, \
         open(args.out, "w", newline="", encoding="utf-8") as ofh:
        w = csv.writer(ofh)
        w.writerow(["ts_iso", "elapsed_s", "duration_ms", "status", "expected_response"])
        for line in fh:
            lines_seen += 1
            # cheap prefilter before paying for json.loads
            if '"http_req_duration"' not in line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if rec.get("type") != "Point" or rec.get("metric") != "http_req_duration":
                continue
            d = rec.get("data", {})
            try:
                ts = parse_ts(d["time"])
            except (KeyError, ValueError):
                bad += 1
                continue
            if t0 is None:
                t0 = ts
            tags = d.get("tags", {}) or {}
            w.writerow([
                d["time"],
                round((ts - t0).total_seconds(), 6),
                round(float(d.get("value", 0.0)), 6),
                tags.get("status", ""),
                tags.get("expected_response", ""),
            ])
            n += 1

    if n == 0:
        sys.exit(f"ERROR: no http_req_duration points found in {args.raw} "
                 f"({lines_seen:,} lines scanned). Nothing was extracted - "
                 f"NOT deleting the raw file.")

    out_size = os.path.getsize(args.out)
    print(f"extracted {n:,} requests  ({lines_seen:,} raw lines scanned)")
    print(f"  {raw_size/1048576:.1f} MB raw  ->  {out_size/1048576:.2f} MB csv "
          f"({100.0*out_size/raw_size:.1f}% of original)")
    if bad:
        print(f"  {bad:,} unparseable line(s) skipped")

    if not args.keep_raw:
        os.remove(args.raw)
        print(f"  raw file deleted (measurements preserved in {args.out})")


if __name__ == "__main__":
    main()
