#!/usr/bin/env python3
"""
add_cv_section.py - report the coefficient-of-variation result, and correct the
recommendation that contradicts it.

Arm C measured CV for all five workloads and the paper never reported it, while §6.4
recommended CV as a variance-sensitive indicator. The measured values run the other way:
CV is highest for the workload with no slow path at all and lowest for the uniformly
expensive one, so an operator watching CV would rank the healthy workload as the most
variable of the five. Reporting it turns a contradiction into a result, which is how this
study handled coordinated omission as well.
"""

import os
import re
import sys
import textwrap

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = os.path.join(ROOT, "paper", "paper_template.md")
text = open(P, encoding="utf-8").read()
before = text

SECTION = """
### 5.10 Coefficient of variation fails when the mean approaches the timer floor

The natural variance-sensitive summary is the coefficient of variation, the standard
deviation divided by the mean. Arm C measured it for all five workloads, which allows the
statistic to be tested against workloads whose variance structure is known by construction
rather than inferred.

[[TABLE:Coefficient of variation against slow-path incidence. The workload containing no slow path scores highest.]]
| Workload | mean (ms) | std (ms) | p99 (ms) | CV |
|---|---:|---:|---:|---:|
| 100% cheap | {{ladder_uniform_cheap_mean}} | {{ladder_uniform_cheap_std}} | {{ladder_uniform_cheap_p99}} | {{ladder_uniform_cheap_cv}} |
| 99.9 / 0.1 mix | {{ladder_mix_0p1pct_mean}} | {{ladder_mix_0p1pct_std}} | {{ladder_mix_0p1pct_p99}} | {{ladder_mix_0p1pct_cv}} |
| 99 / 1 mix | {{ladder_mix_1pct_mean}} | {{ladder_mix_1pct_std}} | {{ladder_mix_1pct_p99}} | {{ladder_mix_1pct_cv}} |
| 90 / 10 mix | {{ladder_mix_10pct_mean}} | {{ladder_mix_10pct_std}} | {{ladder_mix_10pct_p99}} | {{ladder_mix_10pct_cv}} |
| 100% expensive | {{ladder_uniform_expensive_mean}} | {{ladder_uniform_expensive_std}} | {{ladder_uniform_expensive_p99}} | {{ladder_uniform_expensive_cv}} |

CV falls monotonically as the slow path becomes more common: {{ladder_uniform_cheap_cv}}
where there is no slow path at all, then {{ladder_mix_0p1pct_cv}},
{{ladder_mix_1pct_cv}} and {{ladder_mix_10pct_cv}} as incidence rises, down to
{{ladder_uniform_expensive_cv}} when every request is expensive. That ordering is the
reverse of the one the statistic is supposed to supply. An operator watching CV would rank
the workload containing no slow path as the most variable of the five, and would rank the
workload in which a tenth of requests are an order of magnitude slower as calmer than the
healthy one.

The mechanism is arithmetic rather than mysterious. CV is the ratio of standard deviation
to mean, and for the cheap workload the median request completes below the timer's
resolution, giving p50 = {{ladder_uniform_cheap_p50}} ms against a mean of
{{ladder_uniform_cheap_mean}} ms. Scheduler and timer noise of a few hundred microseconds
is then a large fraction of that mean, so the ratio is large even though the distribution
contains no slow component. As the expensive path grows, the mean grows faster than the
standard deviation and the ratio falls.

This constrains a remedy the study would otherwise have recommended, and it fails in the
same way as the statistics examined above: principled in derivation, misleading in use.
Relative dispersion is unsafe wherever the mean sits near the measurement floor, which for
a fast endpoint timed in milliseconds is the ordinary case rather than an edge one.

"""

anchor = ("The bias is large, over half the reported value in the soak case. A percentile "
          "is therefore not one well-defined quantity. It depends on whether requests or "
          "intervals are the sampling unit, and studies reporting percentiles should say "
          "which they used.")
pat = re.compile(r"\s+".join(re.escape(w) for w in anchor.split()))
if len(pat.findall(text)) != 1:
    sys.exit(f"ABORT: anchor matched {len(pat.findall(text))} times")
m = pat.search(text)
text = text[:m.end()] + "\n" + SECTION.rstrip() + "\n" + text[m.end():]

# the recommendation this result contradicts
old_rec = ("2. Prefer variance-sensitive indicators, p99/p50 or a coefficient of variation, "
           "over absolute percentiles when watching for emerging problems, since absolute "
           "divergence shrinks under heavy load.")
new_rec = ("2. Prefer a ratio of percentiles, p99/p50, over absolute percentiles when "
           "watching for emerging problems, since absolute divergence shrinks under heavy "
           "load. Do not substitute the coefficient of variation for it: §5.10 shows CV "
           "ranking the healthiest of five workloads as the most variable, because relative "
           "dispersion is dominated by measurement noise wherever the mean sits near the "
           "timer floor.")
pat2 = re.compile(r"\s+".join(re.escape(w) for w in old_rec.split()))
if len(pat2.findall(text)) != 1:
    sys.exit("ABORT: §6.4 recommendation 2 not found exactly once")
text = pat2.sub(lambda _: textwrap.fill(new_rec, width=90, subsequent_indent="   "),
                text, count=1)

# The real invariant is that nothing was lost. A count delta would just be a magic
# number that has to be re-guessed every time the section is edited.
keys_before = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", before))
keys_after = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", text))
lost = keys_before - keys_after
if lost:
    sys.exit(f"ABORT: placeholders removed: {sorted(lost)}")
print(f"  OK placeholder keys  {len(keys_before)} -> {len(keys_after)} "
      f"(+{len(keys_after - keys_before)} new, 0 lost)")

for name, p, delta in (("figure markers", r"\[\[FIGURE:", 0),
                       ("table markers", r"\[\[TABLE:", 1),
                       ("citations", r"\[\d+\]", 0)):
    a, b = len(re.findall(p, before)), len(re.findall(p, text))
    if b - a != delta:
        sys.exit(f"ABORT: {name} moved {a} -> {b}, expected +{delta}")
    print(f"  OK {name:16} {a} -> {b}")

open(P, "w", encoding="utf-8", newline="\n").write(text)
print("\nadded §5.10 and corrected §6.4 recommendation 2")
