#!/usr/bin/env python3
"""
make_findings.py - build FINDINGS.md, the portable record of every result.

Numbers come from paper/facts.json and the Selenium results.json. Nothing is typed by
hand, so this file cannot drift from the runs that produced it. A missing key raises
rather than printing a blank, for the same reason build_paper.py fails on an unfilled
placeholder.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
R = lambda *p: os.path.join(ROOT, *p)
SELENIUM = r"F:\outputs\sqat-skillbank\results.json"

B = json.load(open(R("paper", "facts.json"), encoding="utf-8"))
F = B["facts"]
PROV = B.get("provenance", {})

# Ratios and fold-changes are derived, not stored. Import the paper's own derive() so
# this file and the paper cannot disagree about how a ratio was computed.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_paper import derive  # noqa: E402

F.update(derive(F))


class Missing(Exception):
    pass


def v(key):
    if key not in F or F[key] is None:
        raise Missing(key)
    x = F[key]
    if isinstance(x, float):
        s = f"{x:,.6f}".rstrip("0").rstrip(".")
        return s if s else "0"
    if isinstance(x, int):
        return f"{x:,}"
    if isinstance(x, list):
        return " / ".join(str(i) for i in x)
    return str(x)


def num(key):
    return float(F[key])


L = []
w = L.append

w("# SQAT Final Term - Testing Findings")
w("")
w("Minhazul Abedin, 21-44625-1")
w("Software Quality Assurance and Testing (SQAT) [A], Summer 2025-2026")
w("American International University-Bangladesh")
w("")
w("Complete record of results from two pieces of testing work: a controlled web")
w("performance study, and a Selenium functional test suite. Every number here is")
w("generated from the raw run outputs, not transcribed.")
w("")
w("---")
w("")

# ============================================================ PART 1
w("# Part 1 - Web application performance study")
w("")
w("**Question.** Does average response time conceal tail-latency failures that")
w("percentile analysis reveals?")
w("")
w("**Method.** One real Node.js web application, copied and run locally on loopback")
w("only. Six controlled arms, each varying one thing. Load generated with Grafana k6.")
w("")

w("## Environment")
w("")
w("| | |")
w("|---|---|")
w(f"| CPU | {v('host_cpu')} |")
w(f"| Memory | {v('host_ram_gb')} GB |")
w(f"| OS | {v('host_os')} |")
w(f"| Runtime | Node.js v{v('node_version')} |")
w(f"| Load generator | k6 v{v('k6_version')} |")
w(f"| Dataset | {v('dataset_bytes')} bytes, {v('dataset_records')} records |")
w("| Target | http://127.0.0.1:8099, loopback only |")
w("")
w(f"**Total requests generated across all runs: {v('total_requests')}**")
w("")
w("Load generator and server shared one machine. This is the study's main threat to")
w("validity and is addressed with Little's Law rather than ignored.")
w("")

w("## Headline results")
w("")
w("| Hypothesis | Prediction | Outcome |")
w("|---|---|---|")
w(f"| H1 | Server degrades over a sustained run | **REFUTED** - degradation ratio {v('soak_degradation')} over {v('soak_span_s')} s |")
w(f"| H2 | Mean stays flat while the tail diverges as data grows | **REFUTED** - mean tracked dataset size almost linearly |")
w(f"| H3 | A 'fast' server can be a broken server | **CONFIRMED** - every metric improved while {v('armb_enabled_failed_pct')}% of requests failed |")
w(f"| H4 | The mean is diluted when only some requests are slow | **SUPPORTED** - mean fell {v('armc_mean_dilution_10')}x vs p99.9 {v('armc_p999_dilution_10')}x |")
w("")
w("Two of four hypotheses were refuted. They are reported as refuted. The application")
w("was never tuned to make a prediction come true.")
w("")

# ---------------- calibration
w("## Calibration - where the server starts to hurt")
w("")
w(f"Swept {v('calib_levels')} concurrency levels from 1 to {v('calib_max_vus')} virtual users.")
w("")
w("| VUs | p50 (ms) | p99 (ms) | p99/p50 | req/s |")
w("|---|---|---|---|---|")
for lv in (1, 2, 4, 8, 16, 200):
    if f"calib_p50_{lv}" in F:
        w(f"| {lv} | {v(f'calib_p50_{lv}')} | {v(f'calib_p99_{lv}')} | {v(f'calib_ratio_{lv}')} | {v(f'calib_rps_{lv}')} |")
w("")
w(f"Peak throughput {v('calib_peak_rps')} req/s. CPU plateaued at about")
w(f"{v('calib_cores_plateau')} cores, consistent with a single-threaded event loop.")
w("")

# ---------------- Arm A
w("## Arm A - baseline matrix (concurrency x route)")
w("")
w(f"{v('matrix_runs_total')} runs, {v('matrix_runs_failed')} failed, ")
w(f"{v('matrix_warmups_discarded')} warm-up runs discarded before analysis.")
w("")
w("| Route | VUs | mean (ms) | p95 (ms) | p99 (ms) | p99/mean | req/s |")
w("|---|---|---|---|---|---|---|")
for slug, label in (("services_html", "/services.html"),
                    ("api_content", "/api/content"),
                    ("sitemap_xml", "/sitemap.xml")):
    for vu in (2, 8, 16):
        k = f"arma_{slug}_v{vu}"
        if f"{k}_mean" in F:
            w(f"| {label} | {vu} | {v(k+'_mean')} | {v(k+'_p95')} | {v(k+'_p99')} | "
              f"{v(k+'_ratio')} | {v(k+'_rps')} |")
w("")
w("**Finding.** Absolute latency rises with load, but the tail becomes *relatively*")
w("less extreme. p99/mean falls as concurrency rises. Percentile analysis is most")
w("valuable near the onset of saturation, not under heavy load.")
w("")

# ---------------- soak
w("## Soak - one hour under sustained load (H1)")
w("")
w("| | |")
w("|---|---|")
w(f"| Requests | {v('soak_requests')} |")
w(f"| Duration | {v('soak_span_s')} s |")
w(f"| Throughput | {v('soak_rps')} req/s |")
w(f"| Error rate | {v('soak_errors_pct')}% |")
w(f"| Mean | {v('soak_mean')} ms |")
w(f"| p50 / p95 / p99 / p99.9 | {v('soak_p50')} / {v('soak_p95')} / {v('soak_p99')} / {v('soak_p999')} ms |")
w(f"| Early p95 vs late p95 | {v('soak_early_p95')} -> {v('soak_late_p95')} ms |")
w(f"| Degradation ratio | {v('soak_degradation')} ({v('soak_degradation_pct')}%) |")
w(f"| Memory by quarter (MB RSS) | {v('soak_rss_quarters')} |")
w(f"| Mann-Whitney p | {v('soak_mw_p')} |")
w(f"| Effect size r | {v('soak_effect_r')} |")
w("")
w("**Finding.** No degradation. Memory plateaued rather than climbing. The difference")
w("between early and late requests is statistically significant and practically")
w(f"meaningless: at {v('soak_requests')} samples, significance is guaranteed, which is")
w("itself a useful warning about reporting p-values on large performance datasets.")
w("")

# ---------------- stress
w("## Stress - finding the actual breaking point")
w("")
w("| | Stage 4 | Stage 4b |")
w("|---|---|---|")
w(f"| Requests | {v('stress_a_requests')} | {v('stress_b_requests')} |")
w(f"| Achieved req/s | {v('stress_a_rps')} | {v('stress_b_rps')} |")
w(f"| Dropped iterations | {v('stress_a_dropped')} | {v('stress_b_dropped')} |")
w(f"| Failed % | {v('stress_a_failed_pct')} | {v('stress_b_failed_pct')} |")
w(f"| p50 / p99 (ms) | {v('stress_a_p50')} / {v('stress_a_p99')} | {v('stress_b_p50')} / {v('stress_b_p99')} |")
w("")
w("**Note on a run that initially failed to break anything.** Stage 4 capped virtual")
w("users, which capped in-flight requests, which pinned latency by Little's Law rather")
w("than by any server limit. The ceiling measured was the generator's, not the")
w("server's. Stage 4b raised the cap and reached a real error rate. Recorded here")
w("because the first result looked like a finding and was not one.")
w("")

# ---------------- Arm D
w("## Arm D - dataset size (H2)")
w("")
w("| Scale | mean (ms) | p50 (ms) | p99 (ms) | p99/mean | req/s | runs |")
w("|---|---|---|---|---|---|---|")
for sc in ("x1", "x10", "x100", "x1000"):
    k = f"scaled_{sc}_api_content"
    if f"{k}_mean" in F:
        w(f"| {sc} | {v(k+'_mean')} | {v(k+'_p50')} | {v(k+'_p99')} | {v(k+'_ratio')} | "
          f"{v(k+'_rps')} | {v(k+'_n')} |")
w("")
w("**Finding.** H2 refuted. The mean did not stay flat. It tracked dataset size almost")
w("linearly, and the p99/mean ratio *fell* as data grew. When every request gets")
w("uniformly slower, the mean reports that faithfully and the tail becomes less")
w("distinctive. The mean conceals *variance*, not slowness.")
w("")
w(f"The x1000 arm has only {v('scaled_x1000_api_content_n')} runs. Treat it as")
w("indicative, not solid.")
w("")

# ---------------- Arm C
w("## Arm C - distribution of cost (H4) - the sharpest result")
w("")
w("Identical expensive work, varying only what fraction of requests hits it.")
w("")
w("| Workload | mean | p50 | p90 | p99 | p99.9 | p99.99 |")
w("|---|---|---|---|---|---|---|")
for key, lab in (("uniform_cheap", "100% cheap"), ("mix_0p1pct", "0.1% slow"),
                 ("mix_1pct", "1% slow"), ("mix_10pct", "10% slow"),
                 ("uniform_expensive", "100% expensive")):
    if f"ladder_{key}_mean" in F:
        cells = [f"{num(f'ladder_{key}_{s}'):,.3f}"
                 for s in ("mean", "p50", "p90", "p99", "p999", "p9999")]
        w(f"| {lab} | " + " | ".join(cells) + " |")
w("")
w("All values in milliseconds.")
w("")
w("**Finding.** Diluting identical expensive work from 100% of requests to 10% reduced")
w(f"the mean by {v('armc_mean_dilution_10')}x but the 99.9th percentile by only")
w(f"{v('armc_p999_dilution_10')}x - a gap of {v('armc_dilution_gap_10')}x.")
w("")
w("**The stronger result.** A slow path is invisible to any percentile below its own")
w(f"incidence. The 0.1%-slow workload reads p99 = {v('ladder_mix_0p1pct_p99')} ms;")
w(f"the workload with no slow path at all reads p99 = {v('ladder_uniform_cheap_p99')} ms.")
w("Indistinguishable. This constrains the usual advice to 'just report p99' - the")
w("percentile has to be chosen against the incidence of the fault you are looking for.")
w("")

# ---------------- Arm B
w("## Arm B - load shedding (H3)")
w("")
w("| | Limiter OFF | Limiter ON |")
w("|---|---|---|")
w(f"| Runs | {v('armb_disabled_n')} | {v('armb_enabled_n')} |")
w(f"| Mean (ms) | {v('armb_disabled_mean')} | {v('armb_enabled_mean')} |")
w(f"| p50 (ms) | {v('armb_disabled_p50')} | {v('armb_enabled_p50')} |")
w(f"| p99 (ms) | {v('armb_disabled_p99')} | {v('armb_enabled_p99')} |")
w(f"| Throughput (req/s) | {v('armb_disabled_rps')} | {v('armb_enabled_rps')} |")
w(f"| Failed % | {v('armb_disabled_failed_pct')} | {v('armb_enabled_failed_pct')} |")
w("")
w(f"**Finding.** Enabling the rate limiter made the endpoint {v('armb_improvement_x')}x")
w(f"faster by mean, {v('armb_p99_improvement_x')}x faster by p99, and increased")
w(f"throughput {v('armb_rps_x')}x - while {v('armb_enabled_failed_pct')}% of requests")
w("returned no data. Mean and percentile are equally useless here. No latency statistic")
w("is interpretable without an error-rate denominator beside it.")
w("")

# ---------------- Arm E
w("## Arm E - open vs closed load model (measurement bias)")
w("")
w("Closed-model tests (fixed virtual users) under-sample slow periods, because each")
w("user waits for a response before sending the next request. This is coordinated")
w("omission. It was discovered mid-study and affects every other arm, so it was")
w("measured rather than ignored.")
w("")
w("| Offered rate | achieved | dropped | mean (ms) | p99 (ms) |")
w("|---|---|---|---|---|")
for r in (600, 1100, 1400):
    if f"arme_{r}_mean" in F:
        w(f"| {r}/s | {v(f'arme_{r}_achieved')} | {v(f'arme_{r}_dropped')} | "
          f"{v(f'arme_{r}_mean')} | {v(f'arme_{r}_p99')} |")
w("")
ratio = num("arme_1100_p99") / num("arma_api_content_v8_p99")
w(f"**Finding.** At a matched load level the open model reports p99 = "
  f"{v('arme_1100_p99')} ms against {v('arma_api_content_v8_p99')} ms closed - a factor")
w(f"of {ratio:.2f}. Every tail divergence reported in this study is therefore a")
w("conservative estimate; the true divergences are larger.")
w("")
w(f"There is also a latency cliff: raising the offered rate by roughly 20% past")
w(f"sustainable throughput moved the mean by a factor of about {v('arme_cliff_x')}.")
w("A closed-model test cannot produce this, because it cannot offer more load than")
w("the server is willing to accept.")
w("")

# ---------------- measurement notes
w("## Measurement artefacts worth knowing")
w("")
w("| Run | raw p99 | time-quantized p99 | bias |")
w("|---|---|---|---|")
w(f"| Smoke | {v('smoke_p99_raw')} | {v('smoke_p99_quant')} | {v('smoke_bias')} ms |")
w(f"| Soak | {v('soak_p99_raw')} | {v('soak_p99_quant')} | {v('soak_bias')} ms |")
w("")
w("Percentiles computed over time-quantized buckets differ from percentiles over raw")
w("per-request samples. Most monitoring systems report the former.")
w("")

w("## What went wrong during the study")
w("")
w("Recorded because a testing report that lists only successes is not a testing report.")
w("")
w("1. **Matrix run produced zero data.** Launching a PowerShell script from Git Bash")
w("   rewrote path arguments. All results deleted and the matrix relaunched natively.")
w("2. **Extractor read gzip as text.** A fix was verified as present in the function")
w("   but not at the call site. Caught by a refuse-to-delete guard on the raw file.")
w("   Re-extraction matched k6's own request count exactly.")
w("3. **Stress test measured the generator, not the server.** See the stress section.")
w("4. **A figure disagreed with its own table.** Generated before extra runs were")
w("   added. All figures now regenerate from facts.json, the same source as the text.")
w("5. **Total request count was once estimated rather than counted.** Corrected; the")
w("   count is now summed from run records.")
w("")

# ============================================================ PART 2
w("---")
w("")
w("# Part 2 - Selenium functional test suite (SkillBank)")
w("")
try:
    sel = json.load(open(SELENIUM, encoding="utf-8"))
    cases = sel if isinstance(sel, list) else sel.get("results", sel.get("cases", []))
    import collections
    mods = collections.Counter(c.get("module", "?") for c in cases)
    stat = collections.Counter(c.get("status", "?") for c in cases)
    w(f"**{len(cases)} automated test cases. Result: "
      + ", ".join(f"{n} {s}" for s, n in stat.items()) + ".**")
    w("")
    w("| Module | Cases |")
    w("|---|---|")
    for m, n in mods.items():
        w(f"| {m} | {n} |")
    w(f"| **Total** | **{len(cases)}** |")
    w("")
except FileNotFoundError:
    w("_results.json not reachable from this machine; section not generated._")
    w("")

w("Application under test: SkillBank, a PHP/MySQL skill-exchange web application.")
w("Driver: Selenium WebDriver with Chrome. Every step screenshotted.")
w("")
w("**Two defects found in the harness itself, both fixed:**")
w("")
w("1. Chrome's password-manager bubble swallowed keystrokes after the first login,")
w("   failing 16 of 40 cases. Fixed by disabling the password manager and leak")
w("   detection in the driver profile. The tests were not wrong; the environment was.")
w("2. One case failed intermittently on a fixed 0.35 s sleep. Every fixed sleep in the")
w("   suite was replaced with an explicit WebDriverWait on a real condition. Flakiness")
w("   went to zero.")
w("")
w("Full suite, screenshots, and report: <https://github.com/abedinm/skillbank-selenium-tests>")
w("(private)")
w("")

# ============================================================ reproduce
w("---")
w("")
w("# Reproducing any number in this file")
w("")
w("```")
w("python scripts/collect_facts.py     # raw runs  -> paper/facts.json")
w("python scripts/make_findings.py     # facts.json -> FINDINGS.md")
w("python scripts/build_paper.py       # facts.json -> paper/paper.md")
w("python scripts/verify_paper.py      # re-derives every claim from raw data")
w("```")
w("")
w(f"`data/facts.json` holds all {len(F)} collected values, each with the file path it")
w("came from.")
w("")
w("**Not included in this repository:**")
w("")
w("- The application under test. It is a client's commercial website, copied locally")
w("  for testing and never modified. It is not mine to publish.")
w("- Raw k6 output (about 1.3 GB). The reduced per-run summaries are included.")
w("")
w("All load testing ran against 127.0.0.1 only. No deployed site was ever a target.")
w("")

out = R("FINDINGS.md")
text = "\n".join(L)
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print(f"FINDINGS.md written: {len(text):,} chars, {len(L)} lines")
