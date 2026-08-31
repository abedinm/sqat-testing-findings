# What the Mean Conceals: A Controlled Study of Percentile Analysis in Web Application Performance Testing

**Minhazul Abedin** — 21-44625-1

---

## Abstract

Mean response time remains the default summary statistic in web performance reporting, and
ISO/IEC 25010 names it explicitly under the *time behaviour* sub-characteristic of
performance efficiency. It is widely asserted that averages conceal tail-latency failures
that percentile analysis exposes. This paper tests that assertion empirically rather than
assuming it, using a single real Node.js web application under six controlled load arms
and {{total_requests_m}} million requests generated with k6.

The assertion is found to be **conditionally true, and false in the form it is usually
stated**. Where load or workload cost rises *uniformly* — deeper request queues, or a
dataset scaled from {{dataset_records}} to 188,000 records — the mean tracks the
degradation faithfully and the tail becomes *less* distinctive, with the ratio of p99 to
mean falling from {{scaled_x1_api_content_ratio}} to {{scaled_x1000_api_content_ratio}}
even as absolute latency rises by three orders of magnitude. A one-hour soak of
{{soak_requests_m}} million requests showed a degradation ratio of {{soak_degradation}},
i.e. none at all. Where response time is *variable* rather than uniformly slow, the mean
fails as predicted: diluting identical expensive work from 100% to 10% of requests reduced
the mean by a factor of {{armc_mean_dilution_10}} but the 99.9th percentile by only
{{armc_p999_dilution_10}}. A further result constrains the recommended remedy — a slow path
affecting 0.1% of requests was **entirely invisible to p99**, which read
{{ladder_mix_0p1pct_p99}} ms against {{ladder_uniform_cheap_p99}} ms for a workload
containing no slow path at all.

A third result undermines both statistics equally. When the application's rate limiter
engaged, mean response time improved {{armb_improvement_x}}-fold and p99 improved
{{armb_p99_improvement_x}}-fold while {{armb_enabled_failed_pct}}% of requests failed —
every latency statistic, mean and percentile alike, reported dramatic improvement as the
service stopped functioning.

The study concludes that the mean conceals **variance**, not slowness; that percentile
analysis is most valuable near the onset of saturation rather than under heavy load; and
that no latency statistic is interpretable without an error-rate denominator. A
coordinated-omission control arm is included to bound the measurement bias in the study's
own method.

**Keywords:** performance testing, tail latency, percentiles, load testing, coordinated
omission, ISO/IEC 25010

---

## 1. Introduction

Performance reporting for web applications is dominated by the arithmetic mean.
Dashboards display average response time; service reports quote it; ISO/IEC 25010 defines
performance efficiency as "the performance relative to the amount of resources used under
stated conditions" and places response time under its *time behaviour* sub-characteristic,
where mean response time is a standard measure.

Against this, a substantial practitioner literature argues that the mean is actively
misleading. Google's *Site Reliability Engineering* states plainly that when latencies are
averaged, "it's entirely possible for most of the requests to be fast, but for a long tail
of requests to be much, much slower", and illustrates it with a system where a typical
request completes in about 50 ms but "5% of requests are 20 times slower". Dean and
Barroso's account of tail latency in large-scale services makes a related argument at
scale.

The claim is intuitively compelling and widely repeated. It is also rarely tested under
controlled conditions on a single system where the cause of degradation is known and can
be varied deliberately. That is what this paper does.

### 1.1 Hypotheses

Three hypotheses were stated before data collection, and a fourth was added after the
first results contradicted two of them.

- **H1** — Under sustained load, a system that repeats avoidable work per request will
  degrade over time, and the mean will understate that degradation relative to
  percentiles.
- **H2** — As the underlying dataset grows, mean response time will remain comparatively
  flat while high percentiles diverge.
- **H3** — When a protective mechanism (rate limiting) sheds load, conventional
  performance metrics will improve even as the service fails.
- **H4** *(added post hoc, tested by a dedicated arm)* — The mean conceals **variance**
  in response time, not uniform slowness. Where every request slows equally, the mean
  reports it faithfully.

H1 and H2 were **refuted**. H3 was **confirmed**, more strongly than anticipated. H4 was
formulated in response and tested by an arm designed specifically for it. Reporting the
refutations is the substantive contribution: the popular form of the claim is too broad,
and the conditions under which it holds are narrower and more interesting than usually
stated.

### 1.2 Contributions

1. A controlled, single-system decomposition separating **uniform slowness** from
   **response-time variance**, showing that the mean fails only for the latter.
2. Empirical evidence that tail divergence **peaks near the onset of saturation** and
   *decreases* under heavy load — the opposite of the intuition that percentiles matter
   most when a system is most stressed.
3. A demonstration that under load shedding, **both** mean and percentile latency improve
   dramatically while the service fails, establishing that no latency statistic is
   interpretable without an error-rate denominator.
4. A quantified coordinated-omission control for the study's own instrument, and a
   measurement of percentile sampling bias arising from time-varying request rates.

---

## 2. Background and Related Work

**Tail latency.** Dean and Barroso [1] describe how, in large-scale services composed of
many components, rare slow responses come to dominate user-visible latency, and argue that
techniques tolerating latency variability are essential to responsive systems. Their
concern is variability, not mean slowness — a distinction this paper takes as its central
axis.

**Percentiles as service level indicators.** Google's SRE practice [2] recommends
percentile-based indicators over averages, noting that "a high-order percentile, such as
the 99th or 99.9th, shows you a plausible worst-case value, while using the 50th
percentile (also known as the median) emphasizes the typical case." It further observes
that "user studies have shown that people typically prefer a slightly slower system to one
with high variance in response time" — again locating the problem in variance.

**Coordinated omission.** Tene's critique [3] identifies a systematic flaw in load
measurement: when a generator's request issuance is coupled to the system's responses, the
requests that *would* have been issued during a slow period are never issued, so slow
periods are under-sampled and percentiles are biased optimistically. Grafana's k6
documentation [4] states the same in tool-specific terms: in the closed model "VU
iterations start only when the last iteration finishes", and when the target system
"starts to respond more slowly, a closed model load test will wait, resulting in increased
iteration durations and a tapering off of the arrival rate of new VU iterations" — a
problem "known as *coordinated omission*". This study measures its magnitude in its own
data rather than assuming it away (§5.8).

**Queueing.** Little's Law [5] relates the mean number of items in a system, the arrival
rate and the mean time in system as L = λW. It is used here to distinguish genuine server
saturation from a load-generator artefact (§4.4, §5.3).

**Standards context.** ISO/IEC 25010 [6] defines performance efficiency as "the
performance relative to the amount of resources used under stated conditions", with
time behaviour covering response and processing times and throughput. The standard's
framing motivates the question: if mean response time is the standard measure, what does
it fail to express?

**Gap.** The practitioner literature asserts the superiority of percentiles largely by
argument and by observational data from production systems, where the cause of any
degradation is not controlled. This study instead varies the *mechanism* of degradation
deliberately — queue depth, dataset size, response-time variance, and load shedding — on
one application, and reports where the mean succeeds as well as where it fails.

---

## 3. System Under Test

The application is a corporate website for an engineering consultancy: a hand-written
Node.js HTTP server of 982 lines using only standard-library modules, with **no framework
and no runtime dependencies**. It serves 22 static HTML pages, a small JSON API, and
38 MB of static assets.

It has **no database**. Its datastore is a single JSON file of {{dataset_bytes}} bytes
containing {{dataset_records}} records across 11 collections. The property that makes it a
useful subject is a deliberate absence of caching:

```js
async function getContent() {
  return JSON.parse(await readFile(dataFile, "utf8"));
}
```

This function is called on **every HTML page request** — the server performs
search-engine-oriented HTML rewriting per request — as well as by the content API, the
search endpoint and the sitemap. Every such request therefore performs a file read and a
synchronous `JSON.parse`. Because `JSON.parse` blocks Node's single-threaded event loop,
per-request cost translates directly into queueing under concurrency, and dataset size
translates directly into per-request cost. Both independent variables this study needs are
therefore available on one unmodified application.

The application also implements per-IP rate limiting, with `/api/search` limited to 30
requests per minute. Because all load originates from one address, this becomes a
system-wide limit and is the subject of a dedicated arm (§5.7).

---

## 4. Methodology

### 4.1 Environment

| Component | Value |
|---|---|
| CPU | {{host_cpu}} |
| Memory | {{host_ram_gb}} GB DDR4-2933, dual channel |
| OS | {{host_os}} |
| Runtime | Node.js v{{node_version}}, single process |
| Load generator | k6 v{{k6_version}} |
| Target | `http://127.0.0.1:8099` — loopback only |

The system under test and the load generator share one machine. This is recorded as a
threat to validity (§7) and its most serious consequence — mistaking generator contention
for server saturation — is addressed directly in §4.4.

The application under test is a **copy**; the original is a live production deployment and
was never modified. A single four-line change was made to the copy to allow the rate
limiter to be disabled by environment variable for the arm in §5.7; the change is inert
when the variable is unset.

### 4.2 Instrumentation and data handling

k6's JSON output emits roughly seventeen metric points per request; a 30-second run at one
virtual user produced 116.8 MB. Because the full experiment would have produced tens of
gigabytes, raw output was reduced to one row per request — timestamp, elapsed time,
duration, status — with **no aggregation, rounding or sampling**. The reduction was
validated by request-count equality against k6's own summary: for the soak run,
{{soak_requests}} of {{soak_requests}} requests were preserved.

Every number in this paper is generated by substitution from a machine-collected fact file
derived from run outputs; none is transcribed by hand.

### 4.3 Statistical treatment

Percentiles are reported at p50, p95, p99 and p99.9. Two additional treatments are
applied:

**Time-quantized percentiles.** Percentiles computed over raw request samples are biased:
fast periods emit more requests per unit time, so healthy behaviour is over-represented.
Each run therefore also reports a percentile computed over per-second means, and the
difference between the two is reported as the sampling bias (§5.9).

**Effect size alongside significance.** Where distributions are compared, the
Mann–Whitney U test is used, as response-time distributions are not normal. Effect size
(rank-biserial r) is reported alongside p, because at the sample sizes involved
(millions of requests) statistical significance is uninformative — a point demonstrated
concretely in §5.4.

### 4.4 Distinguishing server saturation from generator contention

Because both processes share a host, a knee in the latency curve could reflect either the
server saturating or k6 starving it of CPU. The two were separated by sampling the Node
process's own CPU consumption across each calibration level. Node executes JavaScript on
one thread, so a plateau in its CPU draw while latency continues to rise indicates that
the queue is forming inside the application. The measurement is reported in §5.1.

### 4.5 Experimental arms

| Arm | Independent variable | Purpose |
|---|---|---|
| Calibration | concurrency, 1–200 VUs | locate saturation knee |
| A — load matrix | concurrency × route | baseline behaviour, 45 runs |
| Stress | offered arrival rate | breaking point and failure mode |
| Soak | time (3600 s) | H1: degradation under sustained load |
| D — dataset scale | records, ×1 to ×1000 | H2: cost per request |
| C — variance injection | distribution of cost | H4: variance vs uniform slowness |
| B — rate limiting | load shedding on/off | H3: metrics under failure |
| E — open-loop control | load model | bound coordinated-omission bias |

Load runs used k6's `constant-vus` executor; stress and the §5.8 control used arrival-rate
executors. Each cell was repeated with the first run discarded as warm-up.

---

## 5. Results

### 5.1 Calibration: the knee, and evidence that the server is the bottleneck

{{calib_levels}} constant-VU levels from 1 to {{calib_max_vus}} virtual users were run for
20 s each.

Throughput saturates at **8 virtual users**: marginal gain per doubling falls from +35%
(1→2) through +21% (2→4) and +10% (4→8) to **−2%** at 16 VUs. Beyond that point the server
delivers approximately {{calib_peak_rps}} requests per second regardless of client count,
and latency rises in proportion to concurrency — p50 of {{calib_p50_16}}, and
{{calib_p50_200}} ms at 200 VUs — which is Little's Law with throughput pinned.

Critically, the Node process's CPU consumption **plateaus at about
{{calib_cores_plateau}} cores from 4 VUs onward and never rises again**, while latency
continues to climb. The queue is therefore forming inside the application, not in the load
generator, and the host's 16 logical processors are never close to saturated. This
establishes that the measurements which follow reflect the server.

Tail divergence across the sweep is the first substantive finding:

| VUs | 1 | 2 | 4 | 8 | 16 | 200 |
|---|---|---|---|---|---|---|
| p99/p50 | {{calib_ratio_1}} | {{calib_ratio_2}} | **{{calib_ratio_4}}** | {{calib_ratio_8}} | {{calib_ratio_16}} | {{calib_ratio_200}} |

Divergence **peaks at 4 VUs and then declines monotonically**. Under heavy queueing every
request is uniformly delayed, so the tail ceases to be distinctive. Percentile analysis
therefore adds most information near the onset of saturation — the region in which
production systems normally operate — and least when a system is obviously overloaded.

### 5.2 Arm A: baseline load matrix

45 runs across three concurrency levels and three routes, **zero failures**;
{{matrix_warmups_discarded}} warm-up runs discarded, n = 4 per cell.

| Route | VUs | req/s | mean (ms) | p50 | p95 | p99 | p99/mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| /services.html | 2 | {{arma_services_html_v2_rps}} | {{arma_services_html_v2_mean}} | {{arma_services_html_v2_p50}} | {{arma_services_html_v2_p95}} | {{arma_services_html_v2_p99}} | {{arma_services_html_v2_ratio}} |
| /api/content | 2 | {{arma_api_content_v2_rps}} | {{arma_api_content_v2_mean}} | {{arma_api_content_v2_p50}} | {{arma_api_content_v2_p95}} | **{{arma_api_content_v2_p99}}** | **{{arma_api_content_v2_ratio}}** |
| /sitemap.xml | 2 | {{arma_sitemap_xml_v2_rps}} | {{arma_sitemap_xml_v2_mean}} | {{arma_sitemap_xml_v2_p50}} | {{arma_sitemap_xml_v2_p95}} | {{arma_sitemap_xml_v2_p99}} | {{arma_sitemap_xml_v2_ratio}} |
| /services.html | 8 | {{arma_services_html_v8_rps}} | {{arma_services_html_v8_mean}} | {{arma_services_html_v8_p50}} | {{arma_services_html_v8_p95}} | {{arma_services_html_v8_p99}} | {{arma_services_html_v8_ratio}} |
| /api/content | 8 | {{arma_api_content_v8_rps}} | {{arma_api_content_v8_mean}} | {{arma_api_content_v8_p50}} | {{arma_api_content_v8_p95}} | {{arma_api_content_v8_p99}} | {{arma_api_content_v8_ratio}} |
| /sitemap.xml | 8 | {{arma_sitemap_xml_v8_rps}} | {{arma_sitemap_xml_v8_mean}} | {{arma_sitemap_xml_v8_p50}} | {{arma_sitemap_xml_v8_p95}} | {{arma_sitemap_xml_v8_p99}} | {{arma_sitemap_xml_v8_ratio}} |
| /services.html | 16 | {{arma_services_html_v16_rps}} | {{arma_services_html_v16_mean}} | {{arma_services_html_v16_p50}} | {{arma_services_html_v16_p95}} | {{arma_services_html_v16_p99}} | {{arma_services_html_v16_ratio}} |
| /api/content | 16 | {{arma_api_content_v16_rps}} | {{arma_api_content_v16_mean}} | {{arma_api_content_v16_p50}} | {{arma_api_content_v16_p95}} | {{arma_api_content_v16_p99}} | {{arma_api_content_v16_ratio}} |
| /sitemap.xml | 16 | {{arma_sitemap_xml_v16_rps}} | {{arma_sitemap_xml_v16_mean}} | {{arma_sitemap_xml_v16_p50}} | {{arma_sitemap_xml_v16_p95}} | {{arma_sitemap_xml_v16_p99}} | {{arma_sitemap_xml_v16_ratio}} |

The strongest single illustration of the conventional claim appears at the **lowest** load
tested: `/api/content` at 2 VUs has a mean of {{arma_api_content_v2_mean}} ms — a figure
any dashboard would treat as healthy — while p99 is {{arma_api_content_v2_p99}} ms, a
factor of {{arma_api_content_v2_ratio}}. At 16 VUs, where the system is genuinely
struggling, the same ratio falls to {{arma_api_content_v16_ratio}}.

### 5.3 Stress: breaking point and failure mode

An initial ramp to 12,000 offered requests per second did not reach the stopping criteria.
The reason was an artefact of the harness, not the server: with in-flight requests capped
at 4,000 virtual users and service rate pinned near 2,000 req/s, Little's Law bounds
waiting time at 2.0 s, and the observed p50 was {{stress_a_p50}} ms. Reporting that as a
breaking point would have been incorrect. The test was repeated with a 20,000-VU ceiling.

The corrected run reached the criterion, aborting at an error rate of
**{{stress_b_failed_pct}}%** with {{stress_b_rps}} requests per second sustained.

| Measure | Value |
|---|---|
| p50 / p99 / max | {{stress_b_p50}} / {{stress_b_p99}} / — ms |
| HTTP 5xx responses | **{{stress_b_5xx}}** |
| Transport-level errors | **{{stress_b_transport_err}}** |
| Socket handles | {{stress_b_handles_start}} → **{{stress_b_handles_peak}}** |
| Process memory | {{stress_b_rss_start}} MB → **{{stress_b_rss_peak}}** MB |
| Server process | survived; memory and handles returned to baseline |

**The failure mode is connection refusal through socket exhaustion, not application
error.** The application returned no error status at any point. It ceased *accepting*
connections. Memory and handle counts recovered fully once load was removed, indicating
backlog rather than leak.

The implication for monitoring is direct: an observer watching HTTP status codes would
have seen a perfectly healthy application at the moment several per cent of users could
not connect at all. The failure was invisible at the layer most dashboards observe.

### 5.4 Soak: H1 refuted

One continuous run of {{soak_span_s}} seconds at the knee, {{soak_requests}} requests,
**{{soak_errors_pct}}% errors**.

| Measure | Value |
|---|---|
| mean | {{soak_mean}} ms |
| p50 / p95 / p99 / p99.9 | {{soak_p50}} / {{soak_p95}} / {{soak_p99}} / {{soak_p999}} ms |
| early-window p95 | {{soak_early_p95}} ms |
| late-window p95 | {{soak_late_p95}} ms |
| **degradation ratio (late p95 / early p95)** | **{{soak_degradation}}** ({{soak_degradation_pct}}%) |
| Mann–Whitney p | {{soak_mw_p}} |
| **effect size r** | **{{soak_effect_r}}** |

**There is no sustained degradation.** H1 is refuted. Process memory reached a steady
state and remained there — per-quarter means of {{soak_rss_quarters}} MB — confirming that
the per-request cost, though real, does not accumulate. The mechanism is expensive but
**stateless**: each request allocates and releases, and garbage collection keeps pace
indefinitely.

This run also provides a clean demonstration of a methodological trap. The Mann–Whitney
test returns p = {{soak_mw_p}}, conventionally reported as highly significant, on an
effect size of r = {{soak_effect_r}} — negligible. With {{soak_requests_m}} million
samples, any difference whatever attains significance. **Reporting the p-value alone would
have asserted a degradation that does not exist.**

### 5.5 Arm D: dataset scale — H2 refuted

The dataset was regenerated at ×10, ×100 and ×1000 the baseline record count, preserving
field shapes, and the knee-level measurement repeated.

| Scale | records | n | mean (ms) | p50 | p99 | **p99/mean** | req/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| ×1 | 188 | {{scaled_x1_api_content_n}} | {{scaled_x1_api_content_mean}} | {{scaled_x1_api_content_p50}} | {{scaled_x1_api_content_p99}} | **{{scaled_x1_api_content_ratio}}** | {{scaled_x1_api_content_rps}} |
| ×10 | 1,880 | {{scaled_x10_api_content_n}} | {{scaled_x10_api_content_mean}} | {{scaled_x10_api_content_p50}} | {{scaled_x10_api_content_p99}} | **{{scaled_x10_api_content_ratio}}** | {{scaled_x10_api_content_rps}} |
| ×100 | 18,800 | {{scaled_x100_api_content_n}} | {{scaled_x100_api_content_mean}} | {{scaled_x100_api_content_p50}} | {{scaled_x100_api_content_p99}} | **{{scaled_x100_api_content_ratio}}** | {{scaled_x100_api_content_rps}} |
| ×1000 | 188,000 | {{scaled_x1000_api_content_n}} | {{scaled_x1000_api_content_mean}} | {{scaled_x1000_api_content_p50}} | {{scaled_x1000_api_content_p99}} | **{{scaled_x1000_api_content_ratio}}** | {{scaled_x1000_api_content_rps}} |

The mean does **not** stay flat. It tracks dataset size almost exactly linearly across
three orders of magnitude, which is `JSON.parse` behaving as an O(n) operation — and the
mean reports that faithfully. Meanwhile tail divergence **collapses** from
{{scaled_x1_api_content_ratio}} to {{scaled_x1000_api_content_ratio}}.

H2 is refuted. The same pattern observed in §5.1 for concurrency holds for workload size:
when cost rises uniformly, the mean is an adequate instrument and the tail carries little
extra information.

### 5.6 Arm C: variance injection — H4 tested

Arms A, D and the soak all vary *uniform* cost. Arm C holds the expensive work constant
and varies only its **distribution**, by mixing two real endpoints: `/robots.txt`
(110 bytes, no datastore access) and `/api/content` (87 KB, file read and JSON parse). No
application code was changed. Percentiles below are computed over the full per-request
series of a single 120 s run per workload (n given), not from aggregated summaries.

| Workload | n | mean | p50 | p90 | p99 | **p99.9** | p99.99 | % over 3 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 100% cheap | {{ladder_uniform_cheap_n}} | {{ladder_uniform_cheap_mean}} | {{ladder_uniform_cheap_p50}} | {{ladder_uniform_cheap_p90}} | {{ladder_uniform_cheap_p99}} | {{ladder_uniform_cheap_p999}} | {{ladder_uniform_cheap_p9999}} | {{ladder_uniform_cheap_frac_over_3ms}}% |
| 100% expensive | {{ladder_uniform_expensive_n}} | {{ladder_uniform_expensive_mean}} | {{ladder_uniform_expensive_p50}} | {{ladder_uniform_expensive_p90}} | {{ladder_uniform_expensive_p99}} | {{ladder_uniform_expensive_p999}} | {{ladder_uniform_expensive_p9999}} | {{ladder_uniform_expensive_frac_over_3ms}}% |
| 90 / 10 mix | {{ladder_mix_10pct_n}} | {{ladder_mix_10pct_mean}} | {{ladder_mix_10pct_p50}} | {{ladder_mix_10pct_p90}} | {{ladder_mix_10pct_p99}} | **{{ladder_mix_10pct_p999}}** | {{ladder_mix_10pct_p9999}} | {{ladder_mix_10pct_frac_over_3ms}}% |
| 99 / 1 mix | {{ladder_mix_1pct_n}} | {{ladder_mix_1pct_mean}} | {{ladder_mix_1pct_p50}} | {{ladder_mix_1pct_p90}} | {{ladder_mix_1pct_p99}} | {{ladder_mix_1pct_p999}} | {{ladder_mix_1pct_p9999}} | {{ladder_mix_1pct_frac_over_3ms}}% |
| 99.9 / 0.1 mix | {{ladder_mix_0p1pct_n}} | {{ladder_mix_0p1pct_mean}} | {{ladder_mix_0p1pct_p50}} | {{ladder_mix_0p1pct_p90}} | {{ladder_mix_0p1pct_p99}} | {{ladder_mix_0p1pct_p999}} | {{ladder_mix_0p1pct_p9999}} | {{ladder_mix_0p1pct_frac_over_3ms}}% |

**The mean dilutes faster than the tail.** Comparing the 90/10 mix against the uniform
expensive workload: the mean falls from {{ladder_uniform_expensive_mean}} ms to
{{ladder_mix_10pct_mean}} ms, a factor of {{armc_mean_dilution_10}}, while p99.9 falls only
from {{ladder_uniform_expensive_p999}} ms to {{ladder_mix_10pct_p999}} ms, a factor of
{{armc_p999_dilution_10}}. Identical expensive work is present in both; the mean reports it
{{armc_dilution_gap_10}}× more optimistically than the high percentile does. **H4 is
supported**: the mean tracks the majority of requests, the tail tracks the affected
minority.

**A slow path is invisible to a percentile below its own incidence.** This is the sharper
result, and it constrains the practice the paper recommends. A percentile at rank *p* can
only reflect a slow path affecting a fraction *q* of requests if *p* > 100(1 − *q*). The
data follow that boundary exactly:

- At **10%** incidence, the slow path is visible from p90 upward
  ({{ladder_mix_10pct_p90}} ms against {{ladder_uniform_cheap_p90}} ms for pure cheap).
- At **1%** incidence, p99 is at the boundary and barely separates
  ({{ladder_mix_1pct_p99}} ms against {{ladder_uniform_cheap_p99}} ms); p99.9
  ({{ladder_mix_1pct_p999}} ms) and p99.99 ({{ladder_mix_1pct_p9999}} ms) do separate.
- At **0.1%** incidence, **p99 is completely blind**: it reads
  {{ladder_mix_0p1pct_p99}} ms, identical to the pure-cheap workload's
  {{ladder_uniform_cheap_p99}} ms. Even p99.9 ({{ladder_mix_0p1pct_p999}} ms versus
  {{ladder_uniform_cheap_p999}} ms) does not separate them.

A p99-based service level objective therefore **cannot** detect a degradation affecting
fewer than roughly one request in a hundred, no matter how severe that degradation is for
the requests it affects. Percentile monitoring is not simply "better than the mean"; the
rank must be chosen against the incidence of the fault one intends to catch.

**A caveat that limits the strength of this arm.** The expensive requests are individually
faster when they are rare. In the uniform workload every expensive request queues behind
other expensive requests, giving p50 {{ladder_uniform_expensive_p50}} ms; in the 0.1% mix
the same request arrives into a queue of cheap work and completes sooner. The mixes
therefore do not simply inherit the uniform workload's tail, and part of the compression
seen above is this self-queueing effect rather than dilution alone. Separating the two
would require holding queue composition constant while varying only incidence, which this
design does not do.

### 5.7 Arm B: rate limiting — H3 confirmed

`/api/search` was measured with the application's rate limiter disabled and enabled.

| Measure | limiter off | limiter on | change |
|---|---:|---:|---|
| mean response time | {{armb_disabled_mean}} ms | **{{armb_enabled_mean}} ms** | {{armb_improvement_x}}× "faster" |
| p99 | {{armb_disabled_p99}} ms | **{{armb_enabled_p99}} ms** | {{armb_p99_improvement_x}}× "faster" |
| throughput | {{armb_disabled_rps}} req/s | **{{armb_enabled_rps}} req/s** | {{armb_rps_x}}× higher |
| **error rate** | **{{armb_disabled_failed_pct}}%** | **{{armb_enabled_failed_pct}}%** | service destroyed |

Every conventional performance metric improved by more than an order of magnitude at the
moment the service ceased to function. The application served millions of requests, of
which {{armb_enabled_failed_pct}}% were HTTP 429 responses carrying no data. A rejection is
cheap: no file read, no parse, no serialisation.

The result matters beyond the specific mechanism, because **percentile analysis does not
rescue the observer here**. p99 improved by a factor of {{armb_p99_improvement_x}},
alongside the mean. Any latency statistic — mean, median, or high percentile — computed
over successful *and* rejected requests indiscriminately will report a failing service as
a fast one. Latency is interpretable only relative to an error rate.

### 5.8 Arm E: coordinated-omission control

All load arms above used a closed-model executor, in which a virtual user issues its next
request only after the previous one returns. As Tene [3] and the k6 documentation [4]
describe, this under-samples slow periods and biases percentiles optimistically. Because
the study's argument rests on percentiles, the magnitude of that bias was measured rather
than assumed, by repeating `/api/content` with an open-model executor at three offered
rates.

| Offered rate | achieved req/s | dropped iterations | mean (ms) | p95 | p99 |
|---|---:|---:|---:|---:|---:|
| 600/s | {{arme_600_achieved}} | {{arme_600_dropped}} | {{arme_600_mean}} | {{arme_600_p95}} | {{arme_600_p99}} |
| 1100/s | {{arme_1100_achieved}} | {{arme_1100_dropped}} | {{arme_1100_mean}} | {{arme_1100_p95}} | {{arme_1100_p99}} |
| 1400/s | {{arme_1400_achieved}} | {{arme_1400_dropped}} | {{arme_1400_mean}} | {{arme_1400_p95}} | {{arme_1400_p99}} |

{{arme_narrative}}

The 1400/s row is the more consequential observation. Offering only about 20% more than
the server's sustainable throughput moved the mean from {{arme_1100_mean}} ms to
{{arme_1400_mean}} ms — a factor of {{arme_cliff_x}} — with {{arme_1400_dropped}}
iterations dropped because the generator could not place them. The closed-model matrix
never showed anything resembling this cliff: across 2 to 16 virtual users it produced a
smooth, near-linear rise from {{arma_api_content_v2_mean}} to
{{arma_api_content_v16_mean}} ms. **A closed-model test cannot observe the saturation
cliff at all**, because its offered load is throttled by the very slowdown it is trying to
measure. This is a stronger practical argument for open-model load generation than the
percentile bias itself.

*Spread caution:* the open-loop cells are n = 2 after warm-up discard, and the 1100/s p99
varied substantially between the two retained runs. The direction of the effect is
consistent, but the exact factor should not be quoted precisely.

### 5.9 Percentile sampling bias

Percentiles computed over raw request samples over-represent fast periods, because more
requests complete per unit time when the system is healthy. Comparing raw percentiles with
percentiles computed over per-second means:

| Run | p99 raw | p99 time-quantized | bias |
|---|---:|---:|---:|
| smoke (30 s, 1 VU) | {{smoke_p99_raw}} ms | {{smoke_p99_quant}} ms | **{{smoke_bias}} ms** |
| soak (3600 s, 8 VUs) | {{soak_p99_raw}} ms | {{soak_p99_quant}} ms | **{{soak_bias}} ms** |

The bias is large — over half the reported value in the soak case. A percentile is
therefore not a single well-defined quantity: it depends on whether requests or intervals
are the sampling unit. Studies reporting percentiles should state which.

---

## 6. Discussion

### 6.1 The mean conceals variance, not slowness

Four arms converge on one conclusion. Where cost rises uniformly — deeper queues (§5.1),
larger datasets (§5.5), sustained load (§5.4) — the mean tracks the change faithfully and
the ratio of p99 to mean *falls*. Where cost is concentrated in a minority of requests
(§5.6), the mean falls toward the cheap majority while the tail correctly reports the
affected minority.

The common formulation — *average response time conceals degradation* — is therefore too
broad. The precise claim the evidence supports is:

> The arithmetic mean is an adequate summary of response time when the response-time
> distribution is unimodal and cost is uniformly distributed across requests. It fails
> specifically, and severely, when a minority of requests carry disproportionate cost.

This is the condition under which percentile analysis earns its place, and it is also the
condition that characterises most real degradations — a slow dependency on one code path,
a cache miss class, a tail of large records.

### 6.2 Percentiles matter most before a system looks broken

Tail divergence peaked at 4 virtual users ({{calib_ratio_4}}) and fell to
{{calib_ratio_200}} at 200. The same inversion appears across dataset scale. This is
counter-intuitive but mechanically obvious in hindsight: under heavy queueing, delay is
shared, so the distribution tightens in relative terms.

The practical consequence is that percentile monitoring provides most information exactly
where a mean-based dashboard looks healthiest, and least where any instrument would show a
problem.

### 6.3 No latency statistic survives without an error rate

The rate-limiting arm (§5.7) is the strongest result and the one with the broadest
implication. Mean and p99 both improved by more than an order of magnitude while
{{armb_enabled_failed_pct}}% of requests failed. Similarly, the stress arm (§5.3) reached
its breaking point with **zero** HTTP error responses, failing instead at the connection
layer.

Latency statistics describe only requests that were served. Any monitoring or reporting
regime that does not pair them with an error rate — and with a count of requests that were
never served at all — can be made to look arbitrarily good by a system that fails faster.

### 6.4 Implications for practice

1. Report mean **and** a high percentile **and** an error rate. Any one alone is defeasible.
2. Prefer variance-sensitive indicators — p99/p50 or a coefficient of variation — over
   absolute percentiles when watching for emerging problems, since absolute divergence
   shrinks under heavy load.
3. State the sampling unit for percentiles (§5.9) and the load model used (§5.8); both
   materially change the reported value.

---

## 7. Threats to Validity

**Shared host.** The load generator and the system under test ran on one machine.
Mitigated by the CPU-plateau evidence in §5.1, which shows the queue forming inside the
application, but not eliminated. Absolute latencies contain no network component and are
lower bounds; only relative comparisons are claimed.

**Closed-model measurement.** Most arms used a closed-model executor and are therefore
subject to coordinated omission. Arm E (§5.8) bounds the effect. The bias direction is
optimistic, meaning reported tail divergences are conservative.

**Single application.** One Node.js server with one degradation mechanism. The
uniform-versus-variance distinction should generalise, since it is a property of
distributions rather than of this application, but that is an argument, not a measurement.
A multi-language replication would strengthen it.

**Repeat counts.** Arm A used n = 4 per cell and Arm D n = 5 at ×1/×10/×100 (n = 2 at ×1000). Arm B used n = 6 with the limiter disabled and n = 2 enabled; Arm C reports single-run per-request distributions of 0.1–2.4 million requests each; Arm E used n = 2. The effects
reported are large relative to observed spread, but the smaller arms would not support
fine-grained claims.

**The ×1000 dataset scale produced approximately one request per second**, so its p99
rests on very few samples and is indicative only. The mean at that scale is well
supported.

**Background load and power configuration.** The host ran a standard desktop software
environment on a balanced power profile, adding variance not quantified here. Conditions
were identical across arms.

**Construct validity of Arm C.** Variance was induced by mixing two endpoints rather than
by varying one endpoint's cost. This is realistic — production variance usually arises
from heterogeneous requests — but it is not identical to a single endpoint with variable
cost.

---

## 8. Conclusion

This study set out to confirm that mean response time conceals tail-latency failures that
percentile analysis reveals. Under controlled variation of the degradation mechanism, that
claim held in only one of the three conditions tested.

Where load or workload cost rose uniformly, the mean tracked degradation faithfully and
the tail became less informative, not more: p99-to-mean fell from
{{scaled_x1_api_content_ratio}} to {{scaled_x1000_api_content_ratio}} as latency rose by
three orders of magnitude, and an hour-long soak of {{soak_requests_m}} million requests
showed a degradation ratio of {{soak_degradation}}. Where the same total work was
redistributed so that a minority of requests carried it, the mean collapsed toward the
healthy majority faster than the tail did — diluting the slow path from 100% to 10% of
requests cut the mean by {{armc_mean_dilution_10}}x but the 99.9th percentile by only
{{armc_p999_dilution_10}}x. The remedy is narrower than usually stated, however: a slow
path below roughly 1% incidence is invisible even to p99.

The sharpest result concerns neither statistic. Under load shedding, mean and p99 improved
by factors of {{armb_improvement_x}} and {{armb_p99_improvement_x}} respectively while
{{armb_enabled_failed_pct}}% of requests failed. No latency statistic is interpretable
without an error-rate denominator.

The refined claim this study supports is that **the mean conceals variance, not
slowness**, and that percentile analysis is most valuable near the onset of saturation
rather than under evident overload. Future work should replicate the uniform-versus-variance
decomposition on applications in other runtimes, and on systems with genuine database
tiers, to establish whether the boundary condition identified here is a property of
distributions in general — as the mechanism suggests — or of this system in particular.

---

## References

[1] J. Dean and L. A. Barroso, "The tail at scale," *Communications of the ACM*, vol. 56,
no. 2, pp. 74–80, Feb. 2013. doi: 10.1145/2408776.2408794.

[2] B. Beyer, C. Jones, J. Petoff, and N. R. Murphy, Eds., *Site Reliability Engineering:
How Google Runs Production Systems*, ch. 4, "Service Level Objectives." O'Reilly, 2016.
[Online]. Available: https://sre.google/sre-book/service-level-objectives/

[3] G. Tene, "How NOT to measure latency," discussed in T. Treat, "Everything you know
about latency is wrong." [Online]. Available:
https://bravenewgeek.com/everything-you-know-about-latency-is-wrong/

[4] Grafana Labs, "Open and closed models," *k6 documentation*. [Online]. Available:
https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/

[5] J. D. C. Little, "A proof for the queuing formula: L = λW," *Operations Research*,
vol. 9, no. 3, pp. 383–387, 1961. doi: 10.1287/opre.9.3.383.

[6] ISO/IEC 25010:2023, *Systems and software engineering — Systems and software Quality
Requirements and Evaluation (SQuaRE) — Product quality model*. International Organization
for Standardization, 2023.

---

## Appendix A — Reproducibility

All scripts, raw per-request series, per-run summaries and figures are retained. The
experiment is re-runnable end to end:

```
python  reset / scale_dataset.py      regenerate a dataset scale
        capture / run_matrix.ps1      run a load matrix cell
        extract_k6.py                 reduce k6 output to a per-request series
        analyze_k6.py                 percentiles, spikes, degradation, significance
        aggregate.py                  per-cell aggregation and cross-scale figures
        collect_facts.py              gather every cited number from run outputs
        build_paper.py                generate this document from those numbers
```

Every numeric claim in this paper was substituted from `paper/facts.json`, which records
the source file for each value.
