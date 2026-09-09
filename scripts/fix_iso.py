#!/usr/bin/env python3
"""
fix_iso.py - correct the ISO/IEC 25010 quotation.

The paper cited ISO/IEC 25010:2023 but quoted the 2011 definition of performance
efficiency, which the 2023 revision replaced. Same for the time behaviour gloss, which
used the 2011 wording ("response and processing times"); 2023 drops "processing".

Also removes the claim that 25010 establishes mean response time as a standard measure.
25010 defines the quality model; the measures live in ISO/IEC 25023. The paper does not
cite 25023, so the claim is stated as practice rather than attributed to the standard.
"""

import os
import re
import sys
import textwrap

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = os.path.join(ROOT, "paper", "paper_template.md")
text = open(P, encoding="utf-8").read()
before = text
applied, failed = 0, []


def edit(old, new):
    global text, applied
    pat = re.compile(r"\s+".join(re.escape(w) for w in old.split()))
    if len(pat.findall(text)) != 1:
        failed.append(old[:70])
        return
    text = pat.sub(lambda m: textwrap.fill(" ".join(new.split()), width=90), text, count=1)
    applied += 1


# --- Introduction
edit('ISO/IEC 25010 defines performance efficiency as "the performance relative to the '
     'amount of resources used under stated conditions" and places response time under '
     'its *time behaviour* sub-characteristic, where mean response time is a standard '
     'measure.',
     'ISO/IEC 25010 defines performance efficiency as the degree to which a product '
     '"performs its functions within specified time and throughput parameters and is '
     'efficient in the use of resources" under specified conditions, and places response '
     'time under its *time behaviour* sub-characteristic. Mean response time is the '
     'measure conventionally reported against it.')

# --- Background, standards context
edit('ISO/IEC 25010 [6] defines performance efficiency as "the performance relative to '
     'the amount of resources used under stated conditions", with time behaviour covering '
     'response and processing times and throughput. If mean response time is the standard '
     'measure, the question this paper asks is what that measure fails to express.',
     'ISO/IEC 25010 [6] defines performance efficiency as the degree to which a product '
     '"performs its functions within specified time and throughput parameters and is '
     'efficient in the use of resources" under specified conditions. Its *time behaviour* '
     'sub-characteristic covers the response time and throughput rates of a system '
     'performing its functions. Where mean response time is the measure reported against '
     'that sub-characteristic, the question this paper asks is what the measure fails to '
     'express.')

# --- Reference [3]: make the secondary-source relationship explicit
edit('[3] G. Tene, "How NOT to measure latency," discussed in T. Treat, "Everything you '
     'know about latency is wrong." [Online]. Available: '
     'https://bravenewgeek.com/everything-you-know-about-latency-is-wrong/',
     '[3] G. Tene, "How NOT to measure latency," conference presentation. Cited here via '
     'the secondary account in T. Treat, "Everything you know about latency is wrong." '
     '[Online]. Available: '
     'https://bravenewgeek.com/everything-you-know-about-latency-is-wrong/')

if failed:
    print("DID NOT MATCH:", file=sys.stderr)
    for f in failed:
        print("  " + f, file=sys.stderr)

for name, pat in (("placeholders", r"\{\{[a-zA-Z0-9_]+\}\}"), ("figure markers", r"\[\[FIGURE:"),
                  ("table markers", r"\[\[TABLE:"), ("table rows", r"(?m)^\|"),
                  ("citations", r"\[\d\]"), ("section refs", r"§\d")):
    a, b = len(re.findall(pat, before)), len(re.findall(pat, text))
    print(f"  {'OK ' if a == b else 'CHANGED'} {name:16} {a} -> {b}")
    if a != b:
        sys.exit("ABORT: structure changed")

# the 2011 wording must be gone
if "relative to the amount of resources used under stated conditions" in text:
    sys.exit("ABORT: 2011 ISO wording still present")

open(P, "w", encoding="utf-8", newline="\n").write(text)
print(f"\nedits applied: {applied}, failed: {len(failed)}")
