#!/usr/bin/env python3
"""
fix_audit_batch1.py - four objectively verified defects from the deep audit.

1. The paper describes "six" experimental arms; its own table lists eight.
2. Three direct quotations in §1 carry no citation marker, though the same sources are
   numbered in §2. Assignment requirement 8 says all sources must be properly cited.
3. Mann-Whitney is reported as "p = 0". A p-value is never exactly zero; SciPy underflowed
   at double precision. Printing 0 asserts something the test cannot return, and the
   correct statement makes the paper's own methodological point more sharply.
4. §5.1 quotes the 200-VU figure as the post-saturation plateau. That is the peak of the
   sweep, not the level held from the knee onward.
"""

import os
import re
import sys
import textwrap

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = os.path.join(ROOT, "paper", "paper_template.md")
text = open(P, encoding="utf-8").read()
before = text
failed = []


def edit(old, new, count=1):
    global text
    pat = re.compile(r"\s+".join(re.escape(w).replace(r"\-", r"\-\s*") for w in old.split()))
    n = len(pat.findall(text))
    if n != count:
        failed.append(f"{n} matches (expected {count}): {old[:66]}")
        return
    text = pat.sub(lambda m: textwrap.fill(" ".join(new.split()), width=90), text, count=count)


# ---- 1. six arms -> eight -------------------------------------------------
edit("using a single real Node.js web application under six controlled load arms and "
     "{{total_requests_m}} million requests generated with k6.",
     "using a single real Node.js web application under eight controlled load arms and "
     "{{total_requests_m}} million requests generated with k6.")

edit("[[TABLE:The six experimental arms and the variable each isolates.]]",
     "[[TABLE:The eight experimental arms and the variable each isolates.]]")

# ---- 2. citations for the quotations in §1 --------------------------------
edit('ISO/IEC 25010 defines performance efficiency as the degree to which a product '
     '"performs its functions within specified time and throughput parameters and is '
     'efficient in the use of resources" under specified conditions, and places response '
     'time under its *time behaviour* sub-characteristic. The companion measurement '
     'standard ISO/IEC 25023 [1] defines mean response time as a quality measure against '
     'that sub-characteristic.',
     'ISO/IEC 25010 [2] defines performance efficiency as the degree to which a product '
     '"performs its functions within specified time and throughput parameters and is '
     'efficient in the use of resources" under specified conditions, and places response '
     'time under its *time behaviour* sub-characteristic. The companion measurement '
     'standard ISO/IEC 25023 [1] defines mean response time as a quality measure against '
     'that sub-characteristic.')

edit("Against this, a substantial practitioner literature argues that the mean is actively "
     "misleading. Google's *Site Reliability Engineering* states plainly that when "
     "latencies are averaged,",
     "Against this, a substantial practitioner literature argues that the mean is actively "
     "misleading. Google's *Site Reliability Engineering* [3] states plainly that when "
     "latencies are averaged,")

edit('and illustrates it with a system where a typical request completes in about 50 ms '
     'but "5% of requests are 20 times slower". Dean and Barroso\'s account of tail latency '
     'in large-scale services makes a related argument at scale.',
     'and illustrates it with a system where a typical request completes in about 50 ms '
     'but "5% of requests are 20 times slower". Dean and Barroso [4] make a related '
     'argument at the scale of large fan-out services.')

# ---- 3. Mann-Whitney p = 0 ------------------------------------------------
edit("| Mann-Whitney p | {{soak_mw_p}} |",
     "| Mann-Whitney p | < 1e-308 (underflowed to {{soak_mw_p}} at double precision) |")

edit("The run also demonstrates a methodological trap. The Mann-Whitney test returns p = "
     "{{soak_mw_p}}, conventionally read as highly significant, on an effect size of r = "
     "{{soak_effect_r}}, which is negligible. At {{soak_requests_m}} million samples any "
     "difference at all attains significance. Reporting the p-value alone would have "
     "asserted a degradation that is not there.",
     "The run also demonstrates a methodological trap. The Mann-Whitney test returns a "
     "p-value that underflows double precision and is reported by SciPy as "
     "{{soak_mw_p}}; the true value is below 1e-308. It sits alongside an effect size of "
     "r = {{soak_effect_r}}, which is negligible. At {{soak_requests_m}} million samples "
     "any difference at all attains significance, and the p-value stops carrying "
     "information long before it stops being printed. Reporting it alone would have "
     "asserted a degradation that is not there.")

# ---- 4. plateau throughput, not the sweep peak ----------------------------
edit("Beyond that point the server delivers approximately {{calib_peak_rps}} requests per "
     "second regardless of client count, and latency rises in proportion to concurrency:",
     "Beyond that point throughput is flat in client count, holding between "
     "{{calib_plateau_lo}} and {{calib_plateau_hi}} requests per second from 8 virtual "
     "users to 200, averaging {{calib_plateau_rps}} and peaking at {{calib_peak_rps}}, "
     "while latency rises in proportion to concurrency:")

if failed:
    print("DID NOT MATCH:", file=sys.stderr)
    for f in failed:
        print("  " + f, file=sys.stderr)
    sys.exit(1)

keys_b = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", before))
keys_a = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", text))
lost = keys_b - keys_a
if lost:
    sys.exit(f"ABORT: placeholders removed: {sorted(lost)}")
for name, pat, delta in (("figure markers", r"\[\[FIGURE:", 0),
                         ("table markers", r"\[\[TABLE:", 0)):
    a, b = len(re.findall(pat, before)), len(re.findall(pat, text))
    if b - a != delta:
        sys.exit(f"ABORT: {name} {a} -> {b}")
print(f"  OK placeholder keys {len(keys_b)} -> {len(keys_a)} (0 lost)")

open(P, "w", encoding="utf-8", newline="\n").write(text)
print("\n4 verified defects fixed")
