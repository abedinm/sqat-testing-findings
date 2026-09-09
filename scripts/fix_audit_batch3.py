#!/usr/bin/env python3
"""
fix_audit_batch3.py - three substantive corrections.

1. MISLABELLED MECHANISM (§4.3, §5.9, Contribution 4). The paper attributes the whole
   raw-versus-quantized percentile gap to sampling bias from time-varying request rates.
   That mechanism predicts the time-weighted figure should be HIGHER than the per-request
   one, because fast periods contribute more samples and so flatter the tail. The measured
   values go the other way and by a wide margin: soak p99 17.436 ms per-request against
   7.260 ms per-second-mean. analyze_k6.quantized_series() takes one MEAN per bucket, so
   within-bucket variance is destroyed before the percentile is taken; that effect swamps
   the sampling one. The design does not separate them, so the quantity is renamed for
   what it is. The practical conclusion survives intact and is arguably stronger, since
   per-interval aggregation is what monitoring systems actually store.

2. OVERGENERALISED CONTROL (§5.8). A correction factor from n = 2 runs that disagree with
   each other is applied to "the closed-model percentiles used throughout this paper".

3. PREMISE STATED AS FACT (§5.6). "Identical expensive work is present in both" is
   contradicted by the paper's own self-queueing caveat four paragraphs later.
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
        failed.append(f"{n} matches: {old[:64]}")
        return
    text = pat.sub(lambda m: textwrap.fill(" ".join(new.split()), width=90), text, count=1)


# ---- 1a. §4.3 --------------------------------------------------------------
edit("Time-quantized percentiles. Percentiles computed over raw request samples are "
     "biased. Fast periods emit more requests per unit time, so healthy behaviour is "
     "over-represented. Each run therefore also reports a percentile computed over "
     "per-second means, and the gap between the two is reported as the sampling bias "
     "(§5.9).",
     "Sampling unit. Percentiles here are computed over per-request samples. Each run also "
     "reports a percentile recomputed over per-second mean response times, which is the "
     "form produced by a monitoring system that retains one summary per interval rather "
     "than every request. The two are compared in §5.9. The difference is an aggregation "
     "effect and this design does not decompose it into contributing mechanisms.")

# ---- 1b. §5.9 --------------------------------------------------------------
edit("Percentiles computed over raw request samples over-represent fast periods, because "
     "more requests complete per unit time when the system is healthy. Comparing raw "
     "percentiles with percentiles computed over per-second means:",
     "A monitoring system rarely retains every request. It commonly stores one aggregate "
     "per interval and computes percentiles over those aggregates. That is a different "
     "quantity from a percentile over requests, and the two were measured on the same runs "
     "by recomputing p99 over per-second mean response times:")

edit("The bias is large, over half the reported value in the soak case. A percentile is "
     "therefore not one well-defined quantity. It depends on whether requests or intervals "
     "are the sampling unit, and studies reporting percentiles should say which they used.",
     "The per-interval figure is far the lower of the two, by {{soak_bias}} ms in the soak "
     "run, more than half the per-request value.\n\n"
     "The direction deserves stating plainly, because it contradicts the mechanism this "
     "comparison was set up to measure. Unequal sampling should make a per-request "
     "percentile optimistic: fast periods complete more requests per unit time, so healthy "
     "stretches contribute more samples, and weighting by time instead of by request ought "
     "to raise the tail. The observed effect runs the opposite way and is much larger. "
     "Taking a mean within each interval removes all within-interval variance before the "
     "percentile is computed, and where the tail lives inside individual seconds rather "
     "than across them, that removal outweighs the sampling effect entirely. The two "
     "mechanisms are not separated by this design, so the difference should be read as the "
     "combined effect of interval aggregation rather than as a measurement of sampling "
     "bias.\n\n"
     "The practical consequence holds whichever mechanism dominates. A percentile is not "
     "one well-defined quantity: computed over requests and computed over per-interval "
     "averages it differs here by more than a factor of two, and the second is what many "
     "monitoring stacks actually store. Any reported percentile should carry its sampling "
     "unit with it.")

edit("### 5.9 Percentile sampling bias",
     "### 5.9 Percentiles over requests versus over per-interval means")

edit("[[TABLE:Percentile sampling bias: raw request samples against time-quantized samples.]]",
     "[[TABLE:The same p99 computed over per-request samples and over per-second mean response times.]]")

edit("4. A quantified coordinated-omission control for the study's own instrument, and a "
     "measurement of percentile sampling bias arising from time-varying request rates. "
     "Neither mechanism is new; both are measured here on the study's own data rather than "
     "assumed away.",
     "4. A quantified coordinated-omission control for the study's own instrument, and a "
     "measurement of how far a percentile moves when the sampling unit changes from the "
     "request to the time interval. Neither mechanism is new; both are measured here on "
     "the study's own data rather than assumed away.")

# ---- 2. handled in build_paper.derive(), see below ------------------------

# ---- 3. §5.6 premise --------------------------------------------------------
edit("Identical expensive work is present in both; the mean reports it "
     "{{armc_dilution_gap_10}}× more optimistically than the high percentile does.",
     "The same expensive endpoint is exercised in both, though not under identical "
     "queueing conditions, as the caveat below sets out; the mean reports it "
     "{{armc_dilution_gap_10}}× more optimistically than the high percentile does.")

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
print("\n3 substantive corrections applied")
