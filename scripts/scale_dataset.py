#!/usr/bin/env python3
"""
scale_dataset.py - generate a scaled content.json for the Stage 6 dataset arm.

Multiplies the record count of every array in content.json by a factor, preserving the
exact field shape of the real records: same keys, same types, and string lengths drawn
from the real values rather than invented. Slugs and ids are made unique so the app's
lookups still behave (detail pages resolve by slug).

SAFETY: refuses to write anywhere outside perf-web/sut/. The live repo's data directory
must never receive synthetic records.

Usage:
    python scale_dataset.py --factor 10  --out sut/data/content.scaled10.json
    python scale_dataset.py --factor 1   --out sut/data/content.scaled1.json   (identity copy)
"""

import argparse
import json
import os
import random
import sys

SAFE_PREFIX = os.path.normcase(os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "sut")))


def clone_record(rec, i, rng):
    """Copy a record, making identity-ish fields unique so lookups stay well-defined."""
    if not isinstance(rec, dict):
        return rec
    out = {}
    for k, v in rec.items():
        lk = k.lower()
        if isinstance(v, str):
            if lk in ("slug", "id"):
                out[k] = f"{v}-s{i}"
            elif lk in ("name", "title"):
                out[k] = f"{v} {i}"
            else:
                # keep the real string: field shape and length distribution are preserved
                out[k] = v
        elif isinstance(v, list):
            out[k] = list(v)
        elif isinstance(v, dict):
            out[k] = dict(v)
        else:
            out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor", type=int, required=True)
    ap.add_argument("--src", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=1234)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    src = args.src or os.path.join(root, "sut", "data", "content.json")
    out = os.path.abspath(args.out if os.path.isabs(args.out) else os.path.join(root, args.out))

    if not os.path.normcase(out).startswith(SAFE_PREFIX):
        sys.exit(f"REFUSING: output path is outside perf-web/sut/\n  {out}")
    if not os.path.exists(src):
        sys.exit(f"ERROR: source {src} not found")

    rng = random.Random(args.seed)
    with open(src, encoding="utf-8") as fh:
        content = json.load(fh)

    scaled = {}
    counts_before, counts_after = {}, {}
    for key, val in content.items():
        if isinstance(val, list) and val and isinstance(val[0], dict):
            counts_before[key] = len(val)
            grown = []
            for rep in range(args.factor):
                for j, rec in enumerate(val):
                    grown.append(rec if rep == 0 else clone_record(rec, rep * len(val) + j, rng))
            scaled[key] = grown
            counts_after[key] = len(grown)
        else:
            scaled[key] = val

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(scaled, fh, ensure_ascii=False, separators=(",", ":"))

    src_size = os.path.getsize(src)
    out_size = os.path.getsize(out)
    total_before = sum(counts_before.values())
    total_after = sum(counts_after.values())

    print(f"scaled x{args.factor}  ->  {out}")
    print(f"  records {total_before:,} -> {total_after:,}")
    print(f"  bytes   {src_size:,} -> {out_size:,} ({out_size/src_size:.1f}x)")
    for k in counts_before:
        print(f"    {k:<24} {counts_before[k]:>7,} -> {counts_after[k]:>9,}")


if __name__ == "__main__":
    main()
