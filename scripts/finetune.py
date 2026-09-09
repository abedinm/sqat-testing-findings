#!/usr/bin/env python3
"""
finetune.py - line-edit pass over paper_template.md.

Targeted replacements only. Each edit asserts it matched exactly once, so nothing changes
silently and no placeholder, marker, table or number can be touched by accident.
Whitespace in the patterns is matched flexibly because the source is hard-wrapped.
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


def edit(old, new, indent=""):
    """Replace one passage. old is matched with flexible whitespace."""
    global text, applied
    pat = re.compile(r"\s+".join(re.escape(w) for w in old.split()))
    hits = pat.findall(text)
    if len(hits) != 1:
        failed.append((len(hits), old[:60]))
        return
    wrapped = textwrap.fill(" ".join(new.split()), width=90,
                            initial_indent=indent, subsequent_indent=indent)
    text = pat.sub(lambda m: wrapped.replace("\\", "\\\\"), text, count=1)
    applied += 1


# ---------------------------------------------------------------- Abstract
edit("Mean response time remains the default summary statistic in web performance "
     "reporting, and ISO/IEC 25010 names it explicitly under the *time behaviour* "
     "sub-characteristic of performance efficiency.",
     "Mean response time is the default summary statistic in web performance reporting. "
     "ISO/IEC 25010 names it under the *time behaviour* sub-characteristic of performance "
     "efficiency.")

edit("Where workload cost rises uniformly, whether through deeper request queues or a "
     "dataset scaled from {{dataset_records}} to 188,000 records, the mean tracks the "
     "degradation faithfully and the tail becomes less distinctive, with the ratio of p99 "
     "to mean falling from {{scaled_x1_api_content_ratio}} to "
     "{{scaled_x1000_api_content_ratio}} even as absolute latency rises by three orders of "
     "magnitude.",
     "Where workload cost rises uniformly, whether through deeper request queues or a "
     "dataset scaled from {{dataset_records}} to 188,000 records, the mean tracks the "
     "degradation faithfully and the tail becomes less distinctive. The ratio of p99 to "
     "mean falls from {{scaled_x1_api_content_ratio}} to "
     "{{scaled_x1000_api_content_ratio}} even as absolute latency rises by three orders of "
     "magnitude.")

edit("A further result constrains the recommended remedy: a slow path affecting 0.1% of "
     "requests was entirely invisible to p99, which read {{ladder_mix_0p1pct_p99}} ms "
     "against {{ladder_uniform_cheap_p99}} ms for a workload containing no slow path at "
     "all.",
     "A further result constrains the recommended remedy. A slow path affecting 0.1% of "
     "requests was entirely invisible to p99, which read {{ladder_mix_0p1pct_p99}} ms "
     "against {{ladder_uniform_cheap_p99}} ms for a workload containing no slow path at "
     "all.")

# ---------------------------------------------------------------- Introduction
edit("Dashboards display average response time; service reports quote it; ISO/IEC 25010 "
     "defines performance efficiency as \"the performance relative to the amount of "
     "resources used under stated conditions\" and places response time under its *time "
     "behaviour* sub-characteristic, where mean response time is a standard measure.",
     "Dashboards display average response time and service reports quote it. ISO/IEC 25010 "
     "defines performance efficiency as \"the performance relative to the amount of "
     "resources used under stated conditions\" and places response time under its *time "
     "behaviour* sub-characteristic, where mean response time is a standard measure.")

edit("The claim is intuitively compelling and widely repeated. It is also rarely tested "
     "under controlled conditions on a single system where the cause of degradation is "
     "known and can be varied deliberately. This paper tests it under exactly those "
     "conditions.",
     "The claim is intuitively compelling and widely repeated. It is rarely tested on a "
     "single system where the cause of degradation is known and can be varied deliberately. "
     "This paper tests it under exactly those conditions.")

edit("H1 and H2 were refuted. H3 was confirmed, more strongly than anticipated. H4 was "
     "formulated in response and tested by an arm designed specifically for it. Reporting "
     "the refutations is the substantive contribution: the popular form of the claim is "
     "too broad, and the conditions under which it holds are narrower and more interesting "
     "than usually stated.",
     "H1 and H2 were refuted. H3 was confirmed, more strongly than anticipated. H4 was "
     "formulated in response and tested by an arm built for it. The refutations are the "
     "substantive contribution: the popular form of the claim is too broad, and the "
     "conditions under which it holds are narrower and more interesting than usually "
     "stated.")

# ---------------------------------------------------------------- Background
edit("The practitioner literature asserts the superiority of percentiles largely by "
     "argument and by observational data from production systems, where the cause of any "
     "degradation is not controlled. This study instead varies the mechanism of "
     "degradation deliberately (queue depth, dataset size, response-time variance and load "
     "shedding) on one application, and reports where the mean succeeds as well as where "
     "it fails.",
     "The practitioner literature argues for percentiles largely from first principles and "
     "from observational data on production systems, where the cause of any degradation is "
     "not controlled. This study varies the mechanism deliberately instead: queue depth, "
     "dataset size, response-time variance and load shedding, all on one application. It "
     "reports where the mean succeeds as well as where it fails.")

# ---------------------------------------------------------------- System Under Test
edit("Fig. 1 shows the request path. It has no database, and its datastore is a single "
     "JSON file of {{dataset_bytes}} bytes containing {{dataset_records}} records across "
     "11 collections. The property that makes it a useful subject is a deliberate absence "
     "of caching:",
     "Fig. 1 shows the request path. There is no database. The datastore is a single JSON "
     "file of {{dataset_bytes}} bytes holding {{dataset_records}} records across 11 "
     "collections. What makes the application a useful subject is a deliberate absence of "
     "caching:")

edit("The server rewrites HTML for search engines on every page request, so this function "
     "runs for each one, and it runs again for the content API, the search endpoint and "
     "the sitemap. Every such request therefore performs a file read and a synchronous "
     "`JSON.parse`. Because `JSON.parse` blocks Node's single-threaded event loop, "
     "per-request cost translates directly into queueing under concurrency, and dataset "
     "size translates directly into per-request cost. Both independent variables this study "
     "needs are therefore available on one unmodified application.",
     "The server rewrites HTML for search engines on every page request, so this function "
     "runs for each one. It runs again for the content API, the search endpoint and the "
     "sitemap. Every such request performs a file read and a synchronous `JSON.parse`, and "
     "`JSON.parse` blocks Node's single-threaded event loop. Per-request cost therefore "
     "becomes queueing under concurrency, while dataset size becomes per-request cost. Both "
     "independent variables this study needs are available on one unmodified application.")

# ---------------------------------------------------------------- Methodology
edit("k6's JSON output emits roughly seventeen metric points per request; a 30-second run "
     "at one virtual user produced 116.8 MB. Because the full experiment would have "
     "produced tens of gigabytes, raw output was reduced to one row per request holding "
     "timestamp, elapsed time, duration and status.",
     "k6's JSON output emits roughly seventeen metric points per request. A 30-second run "
     "at one virtual user produced 116.8 MB, so the full experiment would have run to tens "
     "of gigabytes. Raw output was reduced to one row per request holding timestamp, "
     "elapsed time, duration and status.")

edit("Percentiles computed over raw request samples are biased: fast periods emit more "
     "requests per unit time, so healthy behaviour is over-represented. Each run therefore "
     "also reports a percentile computed over per-second means, and the difference between "
     "the two is reported as the sampling bias (§5.9).",
     "Percentiles computed over raw request samples are biased. Fast periods emit more "
     "requests per unit time, so healthy behaviour is over-represented. Each run therefore "
     "also reports a percentile computed over per-second means, and the gap between the two "
     "is reported as the sampling bias (§5.9).")

edit("Because both processes share a host, a knee in the latency curve could reflect "
     "either the server saturating or k6 starving it of CPU. The two were separated by "
     "sampling the Node process's own CPU consumption across each calibration level.",
     "Because both processes share a host, a knee in the latency curve could mean either "
     "the server saturating or k6 starving it of CPU. The two were separated by sampling "
     "the Node process's own CPU consumption at each calibration level.")

# ---------------------------------------------------------------- Results
edit("The Node process's CPU consumption plateaus at about {{calib_cores_plateau}} cores "
     "from 4 VUs onward and never rises again, while latency continues to climb. The queue "
     "is therefore forming inside the application, not in the load generator, and the "
     "host's 16 logical processors are never close to saturated. This establishes that the "
     "measurements which follow reflect the server.",
     "The Node process's CPU draw plateaus at about {{calib_cores_plateau}} cores from 4 "
     "VUs onward and never rises again, while latency keeps climbing. The queue is forming "
     "inside the application, not in the load generator, and the host's 16 logical "
     "processors are never close to saturated. The measurements that follow therefore "
     "reflect the server.")

edit("Divergence peaks at 4 VUs and then declines monotonically (Fig. 3). Under heavy "
     "queueing every request is uniformly delayed, so the tail ceases to be distinctive. "
     "Percentile analysis therefore adds most information near the onset of saturation, "
     "the region in which production systems normally operate, and least when a system is "
     "obviously overloaded.",
     "Divergence peaks at 4 VUs and then declines monotonically (Fig. 3). Under heavy "
     "queueing every request is delayed alike, so the tail stops being distinctive. "
     "Percentile analysis adds most information near the onset of saturation, which is "
     "where production systems normally sit, and least when a system is obviously "
     "overloaded.")

edit("An initial ramp to 12,000 offered requests per second did not reach the stopping "
     "criteria. The reason was an artefact of the harness, not the server: with in-flight "
     "requests capped at 4,000 virtual users and service rate pinned near 2,000 req/s, "
     "Little's Law bounds waiting time at 2.0 s, and the observed p50 was "
     "{{stress_a_p50}} ms. Reporting that as a breaking point would have been incorrect. "
     "The test was repeated with a 20,000-VU ceiling.",
     "An initial ramp to 12,000 offered requests per second did not reach the stopping "
     "criteria. The reason was the harness, not the server. With in-flight requests capped "
     "at 4,000 virtual users and service rate pinned near 2,000 req/s, Little's Law bounds "
     "waiting time at 2.0 s, and the observed p50 was {{stress_a_p50}} ms. That is the "
     "generator's ceiling, not the application's, and reporting it as a breaking point "
     "would have been wrong. The test was repeated with a 20,000-VU ceiling.")

edit("The failure mode is connection refusal through socket exhaustion, not application "
     "error. The application returned no error status at any point. It ceased *accepting* "
     "connections.",
     "The failure mode is connection refusal through socket exhaustion, not application "
     "error. The application never returned an error status. It stopped *accepting* "
     "connections.")

edit("There is no sustained degradation (Fig. 5). H1 is refuted. Process memory reached a "
     "steady state and stayed there, with per-quarter means of {{soak_rss_quarters}} MB. "
     "The per-request cost is real but does not accumulate. The mechanism is expensive but "
     "stateless: each request allocates and releases, and garbage collection keeps pace "
     "indefinitely.",
     "There is no sustained degradation (Fig. 5). H1 is refuted. Process memory reached a "
     "steady state and stayed there, with per-quarter means of {{soak_rss_quarters}} MB. "
     "The per-request cost is real, but it does not accumulate. The mechanism is expensive "
     "and stateless: each request allocates and releases, and garbage collection keeps pace "
     "indefinitely.")

edit("This run also provides a clean demonstration of a methodological trap. The "
     "Mann-Whitney test returns p = {{soak_mw_p}}, conventionally reported as highly "
     "significant, on an effect size of r = {{soak_effect_r}}, negligible. With "
     "{{soak_requests_m}} million samples, any difference whatever attains significance. "
     "Reporting the p-value alone would have asserted a degradation that does not exist.",
     "The run also demonstrates a methodological trap. The Mann-Whitney test returns p = "
     "{{soak_mw_p}}, conventionally read as highly significant, on an effect size of r = "
     "{{soak_effect_r}}, which is negligible. At {{soak_requests_m}} million samples any "
     "difference at all attains significance. Reporting the p-value alone would have "
     "asserted a degradation that is not there.")

edit("The mean does not stay flat (Fig. 6). It tracks dataset size almost exactly linearly "
     "across three orders of magnitude, which is `JSON.parse` behaving as an O(n) "
     "operation, and the mean reports that faithfully. Meanwhile tail divergence collapses "
     "from {{scaled_x1_api_content_ratio}} to {{scaled_x1000_api_content_ratio}}.",
     "The mean does not stay flat (Fig. 6). It tracks dataset size almost exactly linearly "
     "across three orders of magnitude. That is `JSON.parse` behaving as an O(n) operation, "
     "and the mean reports it faithfully. Tail divergence, meanwhile, collapses from "
     "{{scaled_x1_api_content_ratio}} to {{scaled_x1000_api_content_ratio}}.")

edit("A p99-based service level objective therefore cannot detect a degradation affecting "
     "fewer than roughly one request in a hundred, no matter how severe that degradation "
     "is for the requests it affects. Percentile monitoring is not simply \"better than the "
     "mean\"; the rank must be chosen against the incidence of the fault one intends to "
     "catch.",
     "A p99-based service level objective cannot detect a degradation affecting fewer than "
     "roughly one request in a hundred, however severe that degradation is for the requests "
     "it hits. Percentile monitoring is not simply better than the mean. The rank has to be "
     "chosen against the incidence of the fault it is meant to catch.")

edit("One caveat limits the strength of this arm. The expensive requests are individually "
     "faster when they are rare.",
     "One caveat limits this arm. Expensive requests are individually faster when they are "
     "rare.")

edit("The speed is not a measurement artefact. A rejection really is cheaper to produce "
     "than a search: it is written from a fixed string and returns before the handler reads "
     "content.json, parses it, rebuilds 174 searchable records and scans them for the query "
     "term. The server became fast because it stopped doing the work it exists to do.",
     "The speed is not a measurement artefact. A rejection really is cheaper to produce "
     "than a search: it is written from a fixed string and returns before the handler reads "
     "content.json, parses it, rebuilds 174 searchable records and scans them for the query "
     "term. The server got fast by stopping the work it exists to do.")

edit("Percentile analysis fails here alongside the mean rather than correcting it. p99 fell "
     "from {{armb_disabled_p99}} ms to {{armb_enabled_p99}} ms, in the same direction and "
     "for the same reason as the mean. The difficulty is not that the mean summarises the "
     "distribution badly. It is that both statistics describe only the requests that "
     "received a response, and neither says anything about the requests that were refused.",
     "Percentile analysis fails here alongside the mean rather than correcting it. p99 fell "
     "from {{armb_disabled_p99}} ms to {{armb_enabled_p99}} ms, in the same direction and "
     "for the same reason as the mean. The problem is not that the mean summarises the "
     "distribution badly. It is that both statistics describe only the requests that got a "
     "response, and neither says anything about the requests that were refused.")

edit("Because the study's argument rests on percentiles, the magnitude of that bias was "
     "measured rather than assumed, by repeating `/api/content` with an open-model executor "
     "at three offered rates.",
     "The study's argument rests on percentiles, so the size of that bias was measured "
     "rather than assumed, by repeating `/api/content` with an open-model executor at three "
     "offered rates.")

edit("The bias is large, over half the reported value in the soak case. A percentile is "
     "therefore not a single well-defined quantity: it depends on whether requests or "
     "intervals are the sampling unit. Studies reporting percentiles should state which.",
     "The bias is large, over half the reported value in the soak case. A percentile is "
     "therefore not one well-defined quantity. It depends on whether requests or intervals "
     "are the sampling unit, and studies reporting percentiles should say which they used.")

# ---------------------------------------------------------------- Discussion
edit("That condition is where percentile analysis earns its place, and it also "
     "characterises most real degradations: a slow dependency on one code path, a "
     "cache-miss class, or a tail of large records.",
     "That condition is where percentile analysis earns its place. It also describes most "
     "real degradations: a slow dependency on one code path, a cache-miss class, a tail of "
     "large records.")

edit("This is counter-intuitive but mechanically obvious in hindsight: under heavy "
     "queueing, delay is shared, so the distribution tightens in relative terms.",
     "This is counter-intuitive, and mechanically obvious in hindsight. Under heavy "
     "queueing the delay is shared, so the distribution tightens in relative terms.")

edit("Latency statistics describe only requests that were served. Any monitoring or "
     "reporting regime that does not pair them with an error rate, and with a count of "
     "requests that were never served at all, can be made to look arbitrarily good by a "
     "system that fails faster.",
     "Latency statistics describe only the requests that were served. Any reporting regime "
     "that does not pair them with an error rate, and with a count of requests never served "
     "at all, can be made to look arbitrarily good by a system that fails faster.")

# ---------------------------------------------------------------- Threats
edit("Arm A used n = 4 per cell and Arm D n = 5 at ×1/×10/×100 (n = 2 at ×1000). Arm B "
     "used n = 6 with the limiter disabled and n = 2 enabled; Arm C reports single-run "
     "per-request distributions of 0.1 to 2.4 million requests each; Arm E used n = 2. The "
     "effects reported are large relative to observed spread, but the smaller arms would "
     "not support fine-grained claims.",
     "Arm A used n = 4 per cell. Arm D used n = 5 at ×1, ×10 and ×100, and n = 2 at ×1000. "
     "Arm B used n = 6 with the limiter disabled and n = 2 with it enabled. Arm C reports "
     "single-run per-request distributions of 0.1 to 2.4 million requests each, and Arm E "
     "used n = 2. The effects reported are large relative to the observed spread, but the "
     "smaller arms would not support fine-grained claims.")

edit("The uniform-versus-variance distinction should generalise, since it is a property of "
     "distributions rather than of this application, but that is an argument, not a "
     "measurement. A multi-language replication would strengthen it.",
     "The uniform-versus-variance distinction should generalise, being a property of "
     "distributions rather than of this application. That is an argument, not a "
     "measurement. A multi-language replication would settle it.")

# ---------------------------------------------------------------- Conclusion
edit("The refined claim this study supports is that the mean conceals variance, not "
     "slowness, and that percentile analysis is most valuable near the onset of saturation "
     "rather than under evident overload.",
     "The refined claim this study supports is that the mean conceals variance rather than "
     "slowness, and that percentile analysis is most valuable near the onset of saturation "
     "rather than under evident overload.")

# ---------------------------------------------------------------- report
if failed:
    print("EDITS THAT DID NOT MATCH EXACTLY ONCE:", file=sys.stderr)
    for n, frag in failed:
        print(f"  {n} matches: {frag}...", file=sys.stderr)

# safety: nothing structural may have changed
for name, pat in (("placeholders", r"\{\{[a-zA-Z0-9_]+\}\}"),
                  ("figure markers", r"\[\[FIGURE:"),
                  ("table markers", r"\[\[TABLE:"),
                  ("table rows", r"(?m)^\|"),
                  ("citations", r"\[\d\]"),
                  ("section refs", r"§\d")):
    a, b = len(re.findall(pat, before)), len(re.findall(pat, text))
    flag = "OK " if a == b else "CHANGED"
    print(f"  {flag} {name:16} {a} -> {b}")
    if a != b:
        sys.exit(f"ABORT: {name} count changed; not writing.")

open(P, "w", encoding="utf-8", newline="\n").write(text)
print(f"\nedits applied: {applied}, failed: {len(failed)}")
