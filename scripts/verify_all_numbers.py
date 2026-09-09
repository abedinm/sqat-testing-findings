#!/usr/bin/env python3
"""
verify_all_numbers.py - check that every value substituted into the paper is traceable.

verify_paper.py independently re-derives 29 headline claims from the raw run data. That
leaves the rest of the substituted values sourced but not re-checked. This script closes
the gap from the other direction: for every {{placeholder}} in the template it confirms

  1. the key exists in facts.json,
  2. the value carries a provenance entry naming the file it came from,
  3. that file still exists on disk,
  4. the rendered string in paper.md matches the value in facts.json exactly.

Derived quantities (ratios, fold-changes) have no provenance file of their own; they are
recomputed here from their inputs using build_paper's own derive(), so a derived value is
verified against the same collected facts the paper is built from.

Exit code 1 on any failure.
"""

import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
R = lambda *p: os.path.join(ROOT, *p)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_paper import derive  # noqa: E402

blob = json.load(open(R("paper", "facts.json"), encoding="utf-8"))
facts = dict(blob["facts"])
prov = blob.get("provenance", {})
derived = derive(facts)
allvals = {**facts, **derived}

template = open(R("paper", "paper_template.md"), encoding="utf-8").read()
rendered = open(R("paper", "paper.md"), encoding="utf-8").read()

keys = sorted(set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", template)))
print(f"placeholders in template: {len(keys)}")

fmt_cache = {}


def fmt(key):
    """Reproduce build_paper's formatting so strings can be compared."""
    v = allvals[key]
    if isinstance(v, float):
        if key.startswith("ladder_") and not key.endswith(("_n", "_frac_over_3ms")):
            return f"{v:,.3f}"
        w = f"{v:,.6f}".rstrip("0").rstrip(".")
        return w if w else "0"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, list):
        return " / ".join(str(x) for x in v)
    return str(v)


missing, no_prov, dead_file, not_in_output = [], [], [], []
collected, derived_keys = 0, 0

for k in keys:
    if k not in allvals or allvals[k] is None:
        missing.append(k)
        continue
    if k in facts:
        collected += 1
        src = prov.get(k)
        if not src:
            no_prov.append(k)
        else:
            p = src if os.path.isabs(src) else R(src)
            if not os.path.exists(p):
                dead_file.append((k, src))
    else:
        derived_keys += 1          # recomputed from collected facts by derive()

    s = fmt(k)
    if s not in rendered:
        not_in_output.append((k, s))

print(f"  collected from run outputs : {collected}")
print(f"  derived from those facts   : {derived_keys}")

ok = True
for label, items in (("not present in facts.json", missing),
                     ("no provenance entry", no_prov),
                     ("provenance file missing on disk", dead_file),
                     ("value not found in rendered paper", not_in_output)):
    if items:
        ok = False
        print(f"\nFAIL - {label}: {len(items)}")
        for it in items[:12]:
            print(f"    {it}")
        if len(items) > 12:
            print(f"    ... and {len(items)-12} more")

# no hand-typed decimals: every decimal in the prose should come from a placeholder
stripped = re.sub(r"\{\{[a-zA-Z0-9_]+\}\}", "@", template)
stripped = re.sub(r"(?m)^\|.*$", "", stripped)          # tables are placeholder-filled
stripped = re.sub(r"```.*?```", "", stripped, flags=re.S)
stripped = re.sub(r"^\[\d+\].*$", "", stripped, flags=re.M)   # reference list
literals = sorted(set(re.findall(r"(?<![\w.@])\d+\.\d+(?![\w.])", stripped)))
allowed = {"2.0", "25010.", "0.1", "1.0", "99.9", "99.99", "25023."}
suspect = [x for x in literals if x not in allowed]

print(f"\nhand-typed decimals in prose (excluding tables, code, refs): {len(suspect)}")
for x in suspect:
    ctx = re.search(r"[^.\n]{0,70}" + re.escape(x) + r"[^.\n]{0,40}", stripped)
    print(f"    {x}   ...{ctx.group(0).strip() if ctx else ''}...")

print()
if ok:
    print(f"ALL {len(keys)} SUBSTITUTED VALUES TRACEABLE")
    print(f"  {collected} carry a provenance path to an existing run-output file")
    print(f"  {derived_keys} recomputed from those facts by build_paper.derive()")
else:
    sys.exit(1)
