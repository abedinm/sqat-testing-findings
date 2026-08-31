# Overnight run — report

**Run window:** 2026-08-24, 18:45 → 23:45 (approx. 5 h, unattended)
**SUT:** Deltadesh corporate website, copy at `perf-web/sut/`, served on `127.0.0.1:8099`
**Load generator:** k6 v2.2.0, same machine

> **Headline:** the study works, and it produced a **stronger and different** result than
> the hypothesis predicted. One of the three predictions was confirmed spectacularly; **two
> were refuted by the data.** The refutations are the more interesting findings and they
> point at a sharper thesis. Details in §4, §5 and §6 — please read those before writing
> anything up.

---

## 1. What ran

| Stage | Status | Evidence |
|---|---|---|
| 1 — stand up SUT, environment, smoke | **Complete, verified** | `docs/sut.md`, `docs/environment.md`, `results/smoke/` |
| 2 — calibration | **Complete** | `docs/calibration.md`, `results/calibration/` |
| 3 — load matrix (Arm A) | **Complete — 45/45 runs, zero failures** | `results/matrix/` |
| 4 — stress | **Complete, but first attempt did not reach a breaking point** | `results/stress/` |
| 4b — stress, corrected | **Complete — breaking point reached** | `results/stress_b/` |
| 5 — soak, 3600 s | **Complete — 4,221,421 requests, 0 errors** | `results/soak/` |
| 6 — scaled dataset arm | **Complete — 24/24 runs, 4 scales** | `results/scaled/` |
| 7 — rate limiter arm (Arm B) | **Complete — 6 runs** | `results/armb/` |
| 8 — analysis and figures | **Complete** | `results/*/metrics.json`, `results/*/figures/` |

**Nothing was skipped.** Two things were *reduced* in scope and one was *added*; both are
in §2.

Total: **37,177,720 requests** across all stages, summed from the run records (not estimated — see `paper/facts.json`, key `total_requests`). An earlier draft of this report stated "~7.2 million"; that was an estimate and it was wrong. The figure above is counted.

---

## 2. Every default I applied

Full reasoning for each is in `docs/decision_log.md` (D1–D15). Condensed:

| # | Decision | Why |
|---|---|---|
| D1 | Copied the SUT to `perf-web/sut/`, excluding `.git` | The original is the live client site's deploy source with a production git remote. Stages 6 and 7 require modifying the app; doing that in place was not safe |
| D2 | Port 8099 | 8080/8083/8085/8139/8003 all in use by other projects |
| D3 | Server started with `Start-Process`, not the preview tool | The preview tool resolves servers from `.claude/launch.json`, which is **outside `perf-web/`**; the safety rail wins |
| D4 | k6 raw JSON extracted then discarded | 116.8 MB per 30 s at 1 VU. Extraction is lossless for `http_req_duration` — verified 30,317 of 30,317 preserved |
| D5 | Smoke route `/services.html` | Exercises the `injectSEO → getContent → JSON.parse` path, and is on no rate-limit bucket |
| D6 | Power plan left on **Balanced** | Smoke was already collected under it; switching mid-study would break comparability. Logged as threat T4 |
| D7 | Discord / Razer Cortex / NVIDIA Overlay left running | Outside `perf-web/`; not mine to change while you slept. Constant across all runs |
| D8 | **Failure:** first matrix launch produced no data; relaunched | See §7 |
| D10 | Stage order 3→4→**5**→**7**→**6**→8 | The scaled arm is the only stage that can be trimmed without losing a headline result, so it went last |
| D11 | **Stage 6 reduced** — 1 level × 2 routes × 3 repeats × 120 s per scale | The full matrix at 4 scales would be ~9 h. The claim being tested is a cross-scale comparison at fixed load, so extra levels add breadth, not evidence |
| D12 | Watchdog to chain stages automatically | So the night proceeded without needing me re-invoked |
| D13 | **Added Stage 4b** | Stage 4 never reached a breaking point — the limit was my own `maxVUs`, not the app. See §4 |
| D14 | No CPU-heavy analysis during the soak | A matplotlib render would appear in the series as a latency excursion and could be mistaken for the effect being measured |
| D15 | **Failure:** soak extraction bug, caught and fixed | See §7 |

---

## 3. Calibration — the knee is 8 VUs

Ten short constant-VU runs, 1 → 200 VUs. Full table in `docs/calibration.md`.

Two independent signals agree on **8 VUs**:

- **Throughput saturates.** +35%, +21%, +10% per doubling to 8 VUs, then **−2%** at 16.
  Past 8 VUs the server delivers ~1,950–2,100 req/s regardless of client count.
- **Latency becomes linear in concurrency** from 16 VUs up: p50 = 7.85, 15.58, 30.16,
  46.09, 72.07, 94.35 ms for 16, 32, 64, 100, 150, 200 VUs. Little's Law with throughput
  pinned.

**The server is the bottleneck, not k6** — this is the measurement that makes everything
else trustworthy. Node's CPU draw plateaus at **~1.40 cores** from 4 VUs onward and never
rises again, while latency keeps climbing. The queue is forming inside the SUT. The host's
16 logical processors were never close to saturated. Threat T1 (shared machine) is
therefore not fatal, though absolute numbers still contain no network latency.

Levels used for the matrix: **low = 2, knee = 8, 2× knee = 16**.

---

## 4. Breaking point and failure mode

### Stage 4 did not reach one — and that was my harness, not the app

The first stress ramp completed all seven stages without tripping either stop condition:
359,743 requests, 547,714 dropped iterations, 1,698 req/s achieved against 12,000 offered,
**0.593% errors**, p50 **2,066 ms**, p99 2,228 ms. Server survived.

`maxVUs` was 4,000, which caps in-flight requests at 4,000. With service rate pinned near
2,000 req/s, Little's Law gives W = 4000/2000 = **2.0 s** — and observed p50 was 2,066 ms.
**The latency ceiling was imposed by the load generator, not the server.** Reporting that
2 s as a breaking point would have been wrong.

### Stage 4b, with `maxVUs=20000`, reached it

k6 aborted on the error threshold at 23:37:51.

| | |
|---|---|
| **Breaking point** | error rate **5.856%** (threshold 5%), at ~**1,504 req/s** sustained |
| Requests before abort | 141,665 |
| p50 / p99 / max | 15 ms / **2,478 ms** / 3,921 ms |
| **HTTP 5xx** | **0** |
| **HTTP 429** | **0** |
| **Transport-level errors** | **8,296** |
| Server process | **Survived**, recovered fully |
| Handles (sockets) | 301 → **peak 8,679** → 247 after |
| RSS | 69 MB → **peak 779 MB** → 119 MB after |

**Failure mode: connection refusal through socket exhaustion — not application error.**

The application never returned a single error status. It stopped *accepting* connections.
Sockets accumulated 29× (301 → 8,679), memory ballooned 11× as request backlog queued,
and the OS-level accept path began refusing. When load stopped, memory and handles
returned to baseline — **no leak, pure backlog**.

This matters for your argument: a monitoring system watching HTTP status codes would have
seen **a perfectly healthy application** at the exact moment 5.9% of users could not
connect at all. The failure was invisible at the layer most dashboards observe.

---

## 5. Soak — degradation ratio **0.9944**. The hypothesis is refuted.

3,600 s at the knee (8 VUs) against `/api/content`. **4,221,421 requests, 0.0000% errors.**

| | |
|---|---|
| mean | 6.814 ms |
| p50 / p95 / p99 / p99.9 | 6.348 / 8.895 / **17.436** / 19.769 ms |
| **degradation ratio (late p95 ÷ early p95)** | **0.9944× (−0.56%)** |
| degradation ratio (mean) | 1.0057× (+0.57%) |
| Mann-Whitney p | 0.000 (significant) |
| **effect size r** | **0.0417 (negligible)** |

**There is no sustained degradation.** The prediction that the no-cache JSON re-parse would
degrade over an hour is **not supported**. Corroborated independently by server memory:
RSS reached a steady state and stayed there — per-quarter means **242.8 / 245.2 / 246.7 /
246.4 MB** — with handles flat (238 → 225).

The mechanism is expensive but **stateless**: every request allocates and frees, and V8's
GC keeps pace indefinitely. Cost per request, not accumulating cost.

> **Methodological point worth a paragraph in the paper.** Mann-Whitney returns
> p = 0.000 — "highly significant" — on an effect size of **r = 0.042**, which is nothing.
> With 4.2 million samples, any difference whatsoever becomes statistically significant.
> Reporting the p-value alone here would assert degradation that does not exist. The effect
> size is what carries the meaning. This is a clean, real example of significance ≠
> importance, produced by your own data.

---

## 6. The two results that reframe the thesis

### 6.1 Scaled dataset — the mean does **not** stay flat

Prediction: mean flat, p99 climbs. **Refuted.** `/api/content`, knee load, 4 scales:

| Scale | records | mean | p50 | p99 | **p99/mean** | req/s |
|---|---:|---:|---:|---:|---:|---:|
| ×1 | 188 | 6.53 ms | 6.11 | 16.53 | **2.53** | 1,224 |
| ×10 | 1,880 | 55.48 ms | 53.94 | 74.95 | **1.35** | 144 |
| ×100 | 18,800 | 534.19 ms | 533.08 | 598.91 | **1.12** | 15 |
| ×1000 | 188,000 | 5,397.27 ms | 5,482.25 | 6,107.60 | **1.13** | 1 |

The mean tracks dataset size **almost exactly linearly** — 6.5 → 55 → 534 → 5,397 ms, a
clean 10× per 10×. That is `JSON.parse` being O(n), and the mean reports it **faithfully**.
Meanwhile tail divergence **collapses** from 2.53× to 1.13×.

`/services.html` shows the same shape: 3.77 → 23.36 → 224.57 → 2,279.71 ms, divergence
3.06 → 1.53 → 1.36 → 1.39.

### 6.2 The same pattern appears in concurrency

From calibration, p99 ÷ p50 against load:

| VUs | 1 | 2 | **4** | 8 | 16 | 32 | 64 | 100 | 150 | 200 |
|---|---|---|---|---|---|---|---|---|---|---|
| p99/p50 | 1.95 | 2.18 | **3.84** | 3.48 | 2.32 | 1.70 | 1.41 | 1.35 | 1.23 | 1.17 |

Divergence **peaks near saturation onset and falls away** under heavy load.

### 6.3 What both results actually say

**The mean hides variance, not slowness.** When every request slows by the same factor —
a bigger dataset, a deeper queue — the mean moves with them and reports the problem
honestly. The mean fails specifically when *most* requests are fast and *some* are not.

That is a sharper, more defensible thesis than "average response time conceals
degradation", and your own data supports it in two independent dimensions (dataset size
and concurrency). The strongest single illustration in Arm A: **`/api/content` at 2 VUs —
mean 1.935 ms, p99 8.952 ms, a 4.63× divergence on a system that looks completely healthy
by its average.** At 16 VUs, where the system is genuinely struggling, divergence drops to
1.66×.

---

## 7. The 429 effect — the hypothesis confirmed, dramatically

`/api/search?q=delta`, knee load, 120 s, 3 runs each (run 1 discarded).

| | limiter **off** | limiter **on** | change |
|---|---:|---:|---|
| mean response time | 19.625 ms | **0.353 ms** | **55× "better"** |
| p99 | 41.214 ms | **1.505 ms** | **27× "better"** |
| throughput | 408 req/s | **20,128 req/s** | **49× higher** |
| **error rate** | **0.000%** | **99.998%** | service destroyed |

**Every conventional performance metric improved enormously at the exact moment the
service stopped working.** Mean, p99, and throughput all say the system got dramatically
faster. It served 2.4 million requests in 120 seconds — and 99.998% of them were HTTP 429
carrying no data. A 429 costs nothing: no file read, no `JSON.parse`, no serialisation.

Only the error rate reveals it. **Percentile analysis does not save you here either** —
p99 improved 27×, right alongside the mean. This is the strongest result in the study and
it argues something broader than your original thesis: *no* latency statistic, mean or
percentile, is safe without an error-rate denominator.

Figure: `results/figures/armb_429_effect.png`.

---

## 8. Arm A load matrix (reference)

45 runs, zero failures, run 1 of each cell discarded as warm-up (n = 4 kept).

| Route | VUs | req/s | mean | p50 | p95 | p99 | p99/mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| /services.html | 2 | 1,493 | 1.313 | 1.233 | 1.749 | 2.254 | 1.72 |
| /api/content | 2 | 1,031 | 1.935 | 1.788 | 2.442 | **8.952** | **4.63** |
| /sitemap.xml | 2 | 1,878 | 0.962 | 0.902 | 1.486 | 2.341 | 2.43 |
| /services.html | 8 | 1,946 | 4.073 | 3.823 | 5.090 | 12.115 | 2.97 |
| /api/content | 8 | 1,174 | 6.809 | 6.415 | 8.910 | 15.097 | 2.22 |
| /sitemap.xml | 8 | 2,267 | 3.497 | 3.265 | 4.254 | 11.200 | 3.20 |
| /services.html | 16 | 1,917 | 8.304 | 7.920 | 13.707 | 15.573 | 1.88 |
| /api/content | 16 | 1,178 | 13.577 | 12.840 | 20.900 | 22.542 | 1.66 |
| /sitemap.xml | 16 | 2,269 | 7.024 | 6.646 | 9.478 | 14.850 | 2.11 |

Reproducibility was good: the three `/services.html` 2-VU repeats gave p50 = 1.238, 1.253,
1.228 ms.

---

## 9. Percentile sampling bias — measured, not assumed

`analyze.py`'s time-quantization argument carries over to web load, and the bias is large:

| Run | p99 raw | p99 time-quantized | bias |
|---|---:|---:|---:|
| smoke (30 s, 1 VU) | 1.888 ms | 1.041 ms | **0.847 ms (45%)** |
| soak (3600 s, 8 VUs) | 17.436 ms | 7.260 ms | **10.176 ms (58%)** |

Fast periods emit more requests per unit time, so healthy behaviour is over-represented in
a raw percentile. Both figures are reported in every `metrics.json`.

---

## 10. Failures during the run — both mine, both caught

**F1 — first matrix launch produced zero measurements (D8).** I invoked the PowerShell
runner from Git Bash. MSYS rewrote `/services.html` into
`C:/Program Files/Git/services.html`, and `-Levels 2,8,16` collapsed to `2816`. The script
reported "total runs: 5" and every run failed. **No data was generated.** It failed loudly
rather than silently. Deleted `results/matrix/` entirely and relaunched via PowerShell.
**Retries: 1. Nothing from the failed attempt was kept or used.**

**F2 — soak extraction silently read a gzip file as text (D15).** I added gzip support to
`extract_k6.py`, verified the *function* existed, but never verified the **call site** was
replaced — a `str.replace` that didn't match had reported success. The extractor read
361 MB of compressed binary as text, scanned 1.56 M garbage "lines", and found zero points.
**The extractor's own guard — refuse to delete the raw file when zero points are
extracted — is what saved the data.** Fixed the call site, verified it by `grep`, re-ran:
**4,221,421 requests extracted, exactly matching the k6 summary's request count.**
**Retries: 1.**

Both are logged in `docs/decision_log.md` with full detail.

---

## 11. Safety verification

| Rail | Result |
|---|---|
| Work confined to `perf-web/` | **Verified.** Only `C:\Users\USER\.claude.json` changed outside it — that is the Claude Code CLI's own config, written by the harness, not by any script here |
| Original repo read-only | **Verified clean.** `git status --short` returns **0 modified files**; HEAD still `758b422`. Only read-only `git status` was ever run in it |
| localhost only | **Verified.** Every script hard-defaults to `http://127.0.0.1:8099`. No public hostname was resolved or contacted. `deltadesh.com` was never touched |
| Outbound network | Only k6 v2.2.0 from the `grafana/k6` GitHub release |
| Synthetic data confined to `perf-web/sut/` | **Verified.** `scale_dataset.py` refuses any output path outside `sut/`. Baseline `content.json` restored — 188 records, byte-identical size to `content.json.base` |
| F: drive untouched | **Verified.** Nothing on F: was read or written |

---

## 12. What I am unsure about — read this before citing anything

1. **Absolute numbers are loopback-only.** No network stack beyond localhost, no TLS, no
   real client. Sub-millisecond medians are not achievable in any real deployment. **Only
   relative comparisons are defensible.**
2. **SUT and load generator share one machine.** Mitigated by the CPU evidence in §3, but
   not eliminated. A second machine would settle it.
3. **The scaled arm has only n = 2 kept repeats per cell** (D11). The trend is enormous —
   three orders of magnitude — so it is not in doubt, but the per-cell spread is thin.
4. **The ×1000 scale produced ~1 req/s**, so roughly 120 requests per run. p99 at that
   scale rests on ~2 samples per run. **Treat ×1000 p99 as indicative only.** The mean at
   that scale is solid.
5. **Power plan was Balanced, not High Performance** (D6). Frequency scaling adds
   run-to-run variance I did not quantify.
6. **Background software was running throughout** (D7) — Discord, Razer Cortex, NVIDIA
   Overlay. Constant across all runs, so relative comparisons hold, but absolute
   throughput is depressed by an unknown amount.
7. **The 5.856% breaking point is a threshold crossing, not a cliff.** Errors climbed
   through the ramp; 5% is where k6 was told to stop. The *mode* (socket exhaustion,
   zero 5xx) is the robust finding; the exact percentage is an artefact of where the
   threshold was set.
8. **`/api/search` was only tested in Arm B**, because the limiter makes it untestable in
   Arm A. So its unlimited behaviour has 2 kept runs, and those showed high variance
   (232 → 433 req/s across three runs). Worth more repeats before citing.
9. **I did not test HTTP keep-alive behaviour, response-body size effects, or concurrent
   mixed-route load.** All three could change the picture.

---

## 13. Suggested next steps

1. **Re-frame the thesis** around §6.3 — "the mean hides variance, not slowness" — and use
   the scaled-dataset and concurrency results as the two supporting dimensions.
2. **Lead the paper with Arm B (§7).** It is the strongest result, and it generalises: it
   shows that *both* mean and percentile latency fail without an error-rate denominator.
3. **Repeat the scaled arm with more repeats** at ×1 / ×10 / ×100, dropping ×1000 to a
   single illustrative point.
4. **Run the load generator from a second machine** to remove threat T1 for the numbers you
   actually cite.
5. Consider adding a **variance-injection arm** — e.g. a route where 1 in 100 requests does
   extra work — to demonstrate the "mean hides variance" claim directly rather than only
   inferentially.

---

## 14. Where everything is

```
perf-web/
  docs/     sut.md  environment.md  calibration.md  decision_log.md  overnight_report.md
  scripts/  smoke.js  const_load.js  stress.js  calibrate.ps1  run_matrix.ps1
            run_remaining.ps1  chain_after_matrix.ps1
            extract_k6.py  analyze_k6.py  aggregate.py  scale_dataset.py
  results/  smoke/  calibration/  matrix/  stress/  stress_b/  soak/  scaled/  armb/  figures/
  sut/      the copy under test (+ serve.mjs.orig, the pristine server source)
  tools/    k6 v2.2.0
```

Figures: `results/soak/figures/` (response-time series, distribution, degradation curve),
`results/scaled/figures/` (mean-vs-p99 and divergence per route),
`results/figures/` (divergence vs concurrency, Arm B 429 effect).


---

## 15. Update — the paper is written (2026-08-25)

This report covered the overnight data collection. Two further arms were added the next
morning, and the paper is complete.

**Added after this report:**

- **Arm C (variance injection)** — the reframed thesis in §6.3 was supported only
  inferentially by the overnight data. Arm C tests it directly by mixing two real
  endpoints, holding the expensive work identical and varying only how many requests carry
  it. It confirmed the claim and produced a sharper one: **a slow path affecting 0.1% of
  requests is invisible to p99**, which reads 1.506 ms — identical to a workload with no
  slow path at all.
- **Arm E (coordinated-omission control)** — the literature review found a flaw in *this
  study's own method*: every overnight arm used a closed-model executor, which k6's
  documentation confirms biases percentiles optimistically. Arm E re-measured open-loop.
  The bias is real (p99 2.43× higher open-loop), which means every tail divergence in this
  report is **conservative**. It also produced an unexpected result: offering 20% more than
  sustainable throughput moved the mean by a factor of ~500, a cliff the closed-model
  matrix could not see at all.
- **Thin cells thickened** — scaled arm now n = 5 at ×1/×10/×100; unlimited `/api/search`
  now n = 6.

**Deliverables:** `paper/paper.docx`, `paper/paper.pdf` (15 pages, ~5,300 words),
`paper/paper.md`, and `paper/facts.json`, which records the source file for every number
cited. `scripts/verify_paper.py` re-derives the key figures from raw outputs and passes
29/29 checks.
