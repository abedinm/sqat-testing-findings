# SQAT Final Term - Testing Findings

Minhazul Abedin, 21-44625-1
Software Quality Assurance and Testing (SQAT) [A], Summer 2025-2026
American International University-Bangladesh

Complete record of results from two pieces of testing work: a controlled web
performance study, and a Selenium functional test suite. Every number here is
generated from the raw run outputs, not transcribed.

---

# Part 1 - Web application performance study

**Question.** Does average response time conceal tail-latency failures that
percentile analysis reveals?

**Method.** One real Node.js web application, copied and run locally on loopback
only. Six controlled arms, each varying one thing. Load generated with Grafana k6.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-10700 (8 cores / 16 threads, 2.90 GHz base) |
| Memory | 32 GB |
| OS | Windows 11 Pro, build 26200.9168 |
| Runtime | Node.js v24.15.0 |
| Load generator | k6 v2.2.0 |
| Dataset | 88,826 bytes, 188 records |
| Target | http://127.0.0.1:8099, loopback only |

**Total requests generated across all runs: 39,355,338**

Load generator and server shared one machine. This is the study's main threat to
validity and is addressed with Little's Law rather than ignored.

## Headline results

| Hypothesis | Prediction | Outcome |
|---|---|---|
| H1 | Server degrades over a sustained run | **REFUTED** - degradation ratio 0.9944 over 3,599 s |
| H2 | Mean stays flat while the tail diverges as data grows | **REFUTED** - mean tracked dataset size almost linearly |
| H3 | A 'fast' server can be a broken server | **CONFIRMED** - every metric improved while 99.998% of requests failed |
| H4 | The mean is diluted when only some requests are slow | **SUPPORTED** - mean fell 6.51x vs p99.9 1.47x |

Two of four hypotheses were refuted. They are reported as refuted. The application
was never tuned to make a prediction come true.

## Calibration - where the server starts to hurt

Swept 10 concurrency levels from 1 to 200 virtual users.

| VUs | p50 (ms) | p99 (ms) | p99/p50 | req/s |
|---|---|---|---|---|
| 1 | 0.89 | 1.72 | 1.95 | 1,087 |
| 2 | 1.24 | 2.7 | 2.18 | 1,470 |
| 4 | 2.04 | 7.84 | 3.85 | 1,772 |
| 8 | 3.78 | 13.14 | 3.47 | 1,951 |
| 16 | 7.85 | 18.23 | 2.32 | 1,917 |
| 200 | 94.35 | 109.93 | 1.17 | 2,116 |

Peak throughput 2,116 req/s. CPU plateaued at about
1.4 cores, consistent with a single-threaded event loop.

## Arm A - baseline matrix (concurrency x route)

45 runs, 0 failed, 
9 warm-up runs discarded before analysis.

| Route | VUs | mean (ms) | p95 (ms) | p99 (ms) | p99/mean | req/s |
|---|---|---|---|---|---|---|
| /services.html | 2 | 1.313 | 1.749 | 2.254 | 1.72 | 1,493 |
| /services.html | 8 | 4.073 | 5.09 | 12.115 | 2.97 | 1,945 |
| /services.html | 16 | 8.304 | 13.707 | 15.573 | 1.88 | 1,917 |
| /api/content | 2 | 1.935 | 2.442 | 8.952 | 4.63 | 1,030 |
| /api/content | 8 | 6.809 | 8.91 | 15.097 | 2.22 | 1,174 |
| /api/content | 16 | 13.577 | 20.9 | 22.542 | 1.66 | 1,177 |
| /sitemap.xml | 2 | 0.962 | 1.486 | 2.341 | 2.43 | 1,878 |
| /sitemap.xml | 8 | 3.497 | 4.254 | 11.2 | 3.2 | 2,266 |
| /sitemap.xml | 16 | 7.024 | 9.478 | 14.85 | 2.11 | 2,269 |

**Finding.** Absolute latency rises with load, but the tail becomes *relatively*
less extreme. p99/mean falls as concurrency rises. Percentile analysis is most
valuable near the onset of saturation, not under heavy load.

## Soak - one hour under sustained load (H1)

| | |
|---|---|
| Requests | 4,221,421 |
| Duration | 3,599 s |
| Throughput | 1,172 req/s |
| Error rate | 0% |
| Mean | 6.814 ms |
| p50 / p95 / p99 / p99.9 | 6.348 / 8.895 / 17.436 / 19.769 ms |
| Early p95 vs late p95 | 8.921 -> 8.871 ms |
| Degradation ratio | 0.9944 (-0.56%) |
| Memory by quarter (MB RSS) | 242.8 / 245.2 / 246.7 / 246.4 |
| Mann-Whitney p | 0 |
| Effect size r | 0.0417 |

**Finding.** No degradation. Memory plateaued rather than climbing. The difference
between early and late requests is statistically significant and practically
meaningless: at 4,221,421 samples, significance is guaranteed, which is
itself a useful warning about reporting p-values on large performance datasets.

## Stress - finding the actual breaking point

| | Stage 4 | Stage 4b |
|---|---|---|
| Requests | 359,743 | 141,665 |
| Achieved req/s | 1,698 | 1,504 |
| Dropped iterations | 547,714 | 8,001 |
| Failed % | 0.593 | 5.856 |
| p50 / p99 (ms) | 2,066.5 / 2,227.5 | 15 / 2,478 |

**Note on a run that initially failed to break anything.** Stage 4 capped virtual
users, which capped in-flight requests, which pinned latency by Little's Law rather
than by any server limit. The ceiling measured was the generator's, not the
server's. Stage 4b raised the cap and reached a real error rate. Recorded here
because the first result looked like a finding and was not one.

## Arm D - dataset size (H2)

| Scale | mean (ms) | p50 (ms) | p99 (ms) | p99/mean | req/s | runs |
|---|---|---|---|---|---|---|
| x1 | 6.47 | 6.02 | 16.51 | 2.55 | 1,236 | 5 |
| x10 | 54.57 | 52.98 | 73.83 | 1.35 | 146 | 5 |
| x100 | 528.75 | 527.54 | 597.01 | 1.13 | 15 | 5 |
| x1000 | 5,397.27 | 5,482.25 | 6,107.6 | 1.13 | 1 | 2 |

**Finding.** H2 refuted. The mean did not stay flat. It tracked dataset size almost
linearly, and the p99/mean ratio *fell* as data grew. When every request gets
uniformly slower, the mean reports that faithfully and the tail becomes less
distinctive. The mean conceals *variance*, not slowness.

The x1000 arm has only 2 runs. Treat it as
indicative, not solid.

## Arm C - distribution of cost (H4) - the sharpest result

Identical expensive work, varying only what fraction of requests hits it.

| Workload | mean | p50 | p90 | p99 | p99.9 | p99.99 |
|---|---|---|---|---|---|---|
| 100% cheap | 0.337 | 0.000 | 1.003 | 1.506 | 2.000 | 6.535 |
| 0.1% slow | 0.378 | 0.000 | 1.004 | 1.506 | 2.008 | 3.509 |
| 1% slow | 0.446 | 0.000 | 1.006 | 2.023 | 3.540 | 4.751 |
| 10% slow | 1.056 | 0.646 | 2.580 | 5.341 | 13.303 | 16.067 |
| 100% expensive | 6.874 | 6.386 | 7.561 | 17.177 | 19.561 | 21.439 |

All values in milliseconds.

**Finding.** Diluting identical expensive work from 100% of requests to 10% reduced
the mean by 6.51x but the 99.9th percentile by only
1.47x - a gap of 4.4x.

**The stronger result.** A slow path is invisible to any percentile below its own
incidence. The 0.1%-slow workload reads p99 = 1.506 ms;
the workload with no slow path at all reads p99 = 1.506 ms.
Indistinguishable. This constrains the usual advice to 'just report p99' - the
percentile has to be chosen against the incidence of the fault you are looking for.

## Arm B - load shedding (H3)

| | Limiter OFF | Limiter ON |
|---|---|---|
| Runs | 6 | 2 |
| Mean (ms) | 18.63 | 0.353 |
| p50 (ms) | 17.609 | 0 |
| p99 (ms) | 32.088 | 1.505 |
| Throughput (req/s) | 429 | 20,128 |
| Failed % | 0 | 99.998 |

**Finding.** Enabling the rate limiter made the endpoint 52.8x
faster by mean, 21.3x faster by p99, and increased
throughput 46.9x - while 99.998% of requests
returned no data. Mean and percentile are equally useless here. No latency statistic
is interpretable without an error-rate denominator beside it.

## Arm E - open vs closed load model (measurement bias)

Closed-model tests (fixed virtual users) under-sample slow periods, because each
user waits for a response before sending the next request. This is coordinated
omission. It was discovered mid-study and affects every other arm, so it was
measured rather than ignored.

| Offered rate | achieved | dropped | mean (ms) | p99 (ms) |
|---|---|---|---|---|
| 600/s | 600 | 0 | 1.104 | 10.274 |
| 1100/s | 1,099 | 0 | 4.544 | 36.685 |
| 1400/s | 1,158 | 26,226 | 2,276.513 | 2,735.002 |

**Finding.** At a matched load level the open model reports p99 = 36.685 ms against 15.097 ms closed - a factor
of 2.43. Every tail divergence reported in this study is therefore a
conservative estimate; the true divergences are larger.

There is also a latency cliff: raising the offered rate by roughly 20% past
sustainable throughput moved the mean by a factor of about 501.
A closed-model test cannot produce this, because it cannot offer more load than
the server is willing to accept.

## Measurement artefacts worth knowing

| Run | raw p99 | time-quantized p99 | bias |
|---|---|---|---|
| Smoke | 1.888 | 1.041 | 0.847 ms |
| Soak | 17.436 | 7.26 | 10.176 ms |

Percentiles computed over time-quantized buckets differ from percentiles over raw
per-request samples. Most monitoring systems report the former.

## What went wrong during the study

Recorded because a testing report that lists only successes is not a testing report.

1. **Matrix run produced zero data.** Launching a PowerShell script from Git Bash
   rewrote path arguments. All results deleted and the matrix relaunched natively.
2. **Extractor read gzip as text.** A fix was verified as present in the function
   but not at the call site. Caught by a refuse-to-delete guard on the raw file.
   Re-extraction matched k6's own request count exactly.
3. **Stress test measured the generator, not the server.** See the stress section.
4. **A figure disagreed with its own table.** Generated before extra runs were
   added. All figures now regenerate from facts.json, the same source as the text.
5. **Total request count was once estimated rather than counted.** Corrected; the
   count is now summed from run records.

---

# Part 2 - Selenium functional test suite (SkillBank)

**40 automated test cases. Result: 40 Pass.**

| Module | Cases |
|---|---|
| Registration | 10 |
| Login | 8 |
| Skill Offer Management | 8 |
| Session Booking | 7 |
| Admin Panel | 7 |
| **Total** | **40** |

Application under test: SkillBank, a PHP/MySQL skill-exchange web application.
Driver: Selenium WebDriver with Chrome. Every step screenshotted.

**Two defects found in the harness itself, both fixed:**

1. Chrome's password-manager bubble swallowed keystrokes after the first login,
   failing 16 of 40 cases. Fixed by disabling the password manager and leak
   detection in the driver profile. The tests were not wrong; the environment was.
2. One case failed intermittently on a fixed 0.35 s sleep. Every fixed sleep in the
   suite was replaced with an explicit WebDriverWait on a real condition. Flakiness
   went to zero.

Full suite, screenshots, and report: <https://github.com/abedinm/skillbank-selenium-tests>
(private)

---

# Reproducing any number in this file

```
python scripts/collect_facts.py     # raw runs  -> paper/facts.json
python scripts/make_findings.py     # facts.json -> FINDINGS.md
python scripts/build_paper.py       # facts.json -> paper/paper.md
python scripts/verify_paper.py      # re-derives every claim from raw data
```

`data/facts.json` holds all 276 collected values, each with the file path it
came from.

**Not included in this repository:**

- The application under test. It is a client's commercial website, copied locally
  for testing and never modified. It is not mine to publish.
- Raw k6 output (about 1.3 GB). The reduced per-run summaries are included.

All load testing ran against 127.0.0.1 only. No deployed site was ever a target.
