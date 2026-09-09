#!/usr/bin/env python3
"""
fix_audit_batch2.py - three overclaims, all verified against sources.

1. PRIOR ART. Contribution 3 claims the study establishes that no latency statistic is
   interpretable without an error-rate denominator. Google's SRE book, cited by this paper
   as [3], already states it: "It's important to distinguish between the latency of
   successful requests and the latency of failed requests", and warns that a fast HTTP 500
   makes "factoring 500s into your overall latency ... result in misleading calculations"
   (ch. 6, Monitoring Distributed Systems). Verified against sre.google on 2026-09-10.
   The result survives as a measurement of the hazard's magnitude, not as its discovery.

2. DEFINITIONAL. The paper derives analytically that a percentile at rank p can only
   reflect a slow path of incidence q when p > 100(1-q), then reports measuring it. A
   bound proved from the definition of a quantile is not an empirical discovery; the
   contribution is the demonstration that a real system tracks the bound exactly.

3. SAMPLE SIZE. §5.10's coefficient-of-variation result inherits Arm C's single run per
   workload. §5.6 states that; §5.10 did not, and a recommendation was built on it.
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


def edit(old, new):
    global text
    pat = re.compile(r"\s+".join(re.escape(w).replace(r"\-", r"\-\s*") for w in old.split()))
    n = len(pat.findall(text))
    if n != 1:
        failed.append(f"{n} matches: {old[:66]}")
        return
    text = pat.sub(lambda m: textwrap.fill(" ".join(new.split()), width=90), text, count=1)


# ---- 1. Contribution 3: prior art ----------------------------------------
edit("3. A demonstration that under load shedding, both mean and percentile latency "
     "improve dramatically while the service fails, establishing that no latency statistic "
     "is interpretable without an error-rate denominator.",
     "3. A quantification of a hazard already stated qualitatively in the monitoring "
     "literature [3]: under load shedding, mean and p99 latency improve by factors of "
     "{{armb_improvement_x}} and {{armb_p99_improvement_x}} while "
     "{{armb_enabled_failed_pct}}% of requests fail. The principle that latency must be "
     "read beside an error rate is not new; the magnitude of the distortion on a real "
     "application, and the fact that percentile analysis fails here alongside the mean "
     "rather than correcting it, is what this arm contributes.")

# ---- §6.3 attribute the principle ----------------------------------------
edit("Latency statistics describe only the requests that were served. Any reporting regime "
     "that does not pair them with an error rate, and with a count of requests never served "
     "at all, can be made to look arbitrarily good by a system that fails faster.",
     "Latency statistics describe only the requests that were served. The principle is "
     "established: Google's monitoring guidance [3] states that it is important to "
     "distinguish the latency of successful requests from that of failed ones, and warns "
     "that a quickly-served error can make latency calculations misleading. What the "
     "measurements here add is the scale of the effect and its reach. Any reporting regime "
     "that does not pair latency with an error rate, and with a count of requests never "
     "served at all, can be made to look arbitrarily good by a system that fails faster, "
     "and no choice of percentile protects against it.")

# ---- 2. p99 bound is definitional ----------------------------------------
edit("which constrains the practice this paper recommends. A percentile at rank *p* can",
     "which constrains the practice this paper recommends. The bound is definitional "
     "rather than empirical, following from what a quantile is; what the measurements "
     "establish is that a real application tracks it exactly, with no softening from "
     "queueing, scheduling or measurement noise. A percentile at rank *p* can")

edit("4. A quantified coordinated-omission control for the study's own instrument, and a "
     "measurement of percentile sampling bias arising from time-varying request rates.",
     "4. A quantified coordinated-omission control for the study's own instrument, and a "
     "measurement of percentile sampling bias arising from time-varying request rates. "
     "Neither mechanism is new; both are measured here on the study's own data rather "
     "than assumed away.")

# ---- 3. §5.10 sample-size caveat ------------------------------------------
edit("This constrains a remedy the study would otherwise have recommended, and it fails in "
     "the same way as the statistics examined above: principled in derivation, misleading "
     "in use. Relative dispersion is unsafe wherever the mean sits near the measurement "
     "floor, which for a fast endpoint timed in milliseconds is the ordinary case rather "
     "than an edge one.",
     "This constrains a remedy the study would otherwise have recommended, and it fails in "
     "the same way as the statistics examined above: principled in derivation, misleading "
     "in use. Relative dispersion is unsafe wherever the mean sits near the measurement "
     "floor, which for a fast endpoint timed in milliseconds is the ordinary case rather "
     "than an edge one. Two limits apply. These values come from the single retained "
     "per-request series per workload described in §5.6, so the ordering is not replicated "
     "across runs; and the mechanism proposed for it, measurement noise dominating a small "
     "mean, is an interpretation of the arithmetic rather than something this design "
     "isolates. The direction of the effect is large and consistent across four incidence "
     "levels, but the exact values should not be quoted as stable.")

if failed:
    print("DID NOT MATCH:", file=sys.stderr)
    for f in failed:
        print("  " + f, file=sys.stderr)
    sys.exit(1)

kb = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", before))
ka = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", text))
if kb - ka:
    sys.exit(f"ABORT: placeholders removed: {sorted(kb - ka)}")
for name, pat in (("figure markers", r"\[\[FIGURE:"), ("table markers", r"\[\[TABLE:")):
    if len(re.findall(pat, before)) != len(re.findall(pat, text)):
        sys.exit(f"ABORT: {name} count changed")
print(f"  OK placeholder keys {len(kb)} -> {len(ka)} (0 lost)")
open(P, "w", encoding="utf-8", newline="\n").write(text)
print("\n3 overclaims corrected")
