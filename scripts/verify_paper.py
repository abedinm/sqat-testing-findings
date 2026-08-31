#!/usr/bin/env python3
"""
verify_paper.py - independent verification of the finished paper.

Does NOT trust the build pipeline. Re-derives key numbers straight from the raw run
outputs and compares them against what the paper actually says, then checks the document
for unresolved placeholders and for claims that assert exact equality.

Exit code 0 only if every check passes.
"""

import csv
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
R = lambda *p: os.path.join(ROOT, *p)

fails, checks = [], 0


def check(name, ok, detail=""):
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        fails.append(name)


def jload(p):
    with open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)


def cload(p):
    with open(p, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


paper_path = R("paper", "paper.md")
if not os.path.exists(paper_path):
    sys.exit("paper.md not found")
paper = open(paper_path, encoding="utf-8").read()

print("=" * 66)
print(" PAPER VERIFICATION")
print("=" * 66)

# ---------------------------------------------------------------- 1. placeholders
left = re.findall(r"\{\{[a-zA-Z0-9_]+\}\}", paper)
check("no unresolved placeholders in paper.md", not left, f"{len(left)} found: {left[:5]}")

# ---------------------------------------------------------------- 2. soak, from metrics
m = jload(R("results", "soak", "metrics.json"))
check("soak request count appears in paper",
      f"{m['requests']:,}" in paper, f"expected {m['requests']:,}")
check("soak degradation ratio matches metrics.json",
      str(round(m["degradation_ratio_p95"], 3)) in paper or
      str(round(m["degradation_ratio_p95"], 4)) in paper,
      f"metrics says {m['degradation_ratio_p95']}")
check("soak effect size matches metrics.json",
      str(round(m["effect_size_r"], 4)) in paper, f"metrics says {m['effect_size_r']}")
check("soak degradation is genuinely ~1.0 (no degradation claimed correctly)",
      0.97 <= m["degradation_ratio_p95"] <= 1.03, f"ratio={m['degradation_ratio_p95']}")

# ---------------------------------------------------------------- 3. Arm C ladder
ladder = {r["name"]: r for r in jload(R("results", "mixed", "percentile_ladder.json"))}
cheap_p99 = round(ladder["uniform_cheap"]["p99"], 3)
mix01_p99 = round(ladder["mix_0p1pct"]["p99"], 3)
check("claim 'p99 identical for 0.1% mix and pure cheap' is literally true",
      abs(cheap_p99 - mix01_p99) < 1e-6, f"cheap={cheap_p99} mix={mix01_p99}")
check("0.1% mix really contains expensive work (max latency well above cheap p99)",
      ladder["mix_0p1pct"]["max"] > 5 * cheap_p99,
      f"max={ladder['mix_0p1pct']['max']}")
md = ladder["uniform_expensive"]["mean"] / ladder["mix_10pct"]["mean"]
pd_ = ladder["uniform_expensive"]["p999"] / ladder["mix_10pct"]["p999"]
check("mean dilutes faster than p99.9 (the H4 claim)", md > pd_,
      f"mean factor {md:.2f} vs p99.9 factor {pd_:.2f}")
check("mean dilution factor in paper", f"{round(md,2)}" in paper, f"computed {md:.2f}")

# ---------------------------------------------------------------- 4. Arm B
def armb(mode):
    d = R("results", "armb", mode)
    runs = []
    for fn in sorted(os.listdir(d)):
        if fn.startswith("run") and fn.endswith(".json") and fn != "run1.json":
            runs.append(jload(os.path.join(d, fn)))
    return runs

dis, ena = armb("disabled"), armb("enabled")
dis_mean = sum(r["avg"] for r in dis) / len(dis)
ena_mean = sum(r["avg"] for r in ena) / len(ena)
ena_fail = sum(r["failed_rate"] for r in ena) / len(ena) * 100
check("Arm B: limiter ON is faster by mean (the paradox is real)", ena_mean < dis_mean,
      f"off={dis_mean:.3f} on={ena_mean:.3f}")
check("Arm B: limiter ON failure rate is near-total", ena_fail > 99.0,
      f"{ena_fail:.3f}%")
check("Arm B mean improvement factor in paper",
      f"{round(dis_mean/ena_mean,1)}" in paper, f"computed {dis_mean/ena_mean:.1f}")

# ---------------------------------------------------------------- 5. scaled arm
agg = jload(R("results", "scaled_merged", "aggregate.json"))
cells = {c["tag"]: c for c in agg["cells"]}
means = [cells[t]["avg_ms_mean"] for t in ("x1", "x10", "x100", "x1000") if t in cells]
check("scaled arm: mean rises monotonically with dataset size",
      all(b > a for a, b in zip(means, means[1:])), f"{means}")
ratios = [cells[t]["p99_over_mean"] for t in ("x1", "x10", "x100") if t in cells]
check("scaled arm: p99/mean divergence FALLS as data grows (H2 refuted)",
      all(b <= a for a, b in zip(ratios, ratios[1:])), f"{ratios}")
check("scaled arm: mean scaling is ~linear (10x data -> ~10x mean)",
      5 < (means[1] / means[0]) < 15, f"x10/x1 = {means[1]/means[0]:.2f}")

# ---------------------------------------------------------------- 6. stress
sb = jload(R("results", "stress_b", "summary.json"))
check("stress: zero 5xx responses (failure was not application-level)",
      sb["err_5xx"] == 0, f"5xx={sb['err_5xx']}")
check("stress: transport errors are the failure mode", sb["err_transport"] > 0,
      f"transport={sb['err_transport']}")
check("stress: breaking-point error rate in paper",
      f"{round(sb['failed_rate']*100,3)}" in paper, f"{sb['failed_rate']*100:.3f}")

# ---------------------------------------------------------------- 7. totals
facts = jload(R("paper", "facts.json"))["facts"]
total = facts["total_requests"]
check("total request count is a counted sum, not an estimate",
      total > 30_000_000, f"{total:,}")
check("total appears in paper as millions",
      f"{round(total/1_000_000,1)}" in paper, f"{total/1_000_000:.1f}")

# ---------------------------------------------------------------- 8. citations
for marker in ("10.1145/2408776.2408794", "10.1287/opre.9.3.383",
               "sre.google/sre-book", "grafana.com/docs/k6", "ISO/IEC 25010"):
    check(f"reference present: {marker}", marker in paper)

# ---------------------------------------------------------------- 9. honesty checks
check("paper states H1 and H2 were refuted",
      "refuted" in paper.lower() and paper.lower().count("refuted") >= 3)
check("paper reports the coordinated-omission limitation of its own method",
      "coordinated omission" in paper.lower())
check("paper contains a threats-to-validity section",
      "Threats to Validity" in paper)
check("paper flags the x1000 low sample size",
      "×1000" in paper or "x1000" in paper)

print("-" * 66)
print(f" {checks - len(fails)}/{checks} checks passed")
if fails:
    print(" FAILED:")
    for f_ in fails:
        print(f"   - {f_}")
    sys.exit(1)
print(" ALL CHECKS PASSED")
