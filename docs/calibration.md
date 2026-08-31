# Stage 2 — Calibration

**Goal:** locate the concurrency at which p99 begins to climb, and pick three load levels
for the matrix.

**Method:** ten constant-VU runs, 20 s each, one route (`/services.html`), 3 s settle
between runs. Constant VUs rather than a ramp, because a ramp mixes warm-up with steady
state and blurs the knee. Node's process CPU time was sampled before and after each run to
distinguish genuine server saturation from load-generator contention (threat T1).

Raw data: `results/calibration/sweep.csv`, per-run summaries in
`results/calibration/vus<N>/summary.json`.

---

## Results

| VUs | req/s | p50 ms | p95 ms | p99 ms | max ms | fail | node cores used |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1088 | 0.88 | 1.51 | 1.72 | 8.18 | 0.00% | 0.898 |
| 2 | 1471 | 1.24 | 2.03 | 2.70 | 15.78 | 0.00% | 1.205 |
| **4** | 1773 | 2.04 | 3.02 | **7.84** | 16.65 | 0.00% | 1.377 |
| **8** | **1951** | 3.78 | 5.07 | 13.14 | 18.30 | 0.00% | 1.438 |
| 16 | 1917 | 7.85 | 13.72 | 18.23 | 23.35 | 0.00% | 1.385 |
| 32 | 1946 | 15.58 | 22.99 | 26.50 | 31.38 | 0.00% | 1.401 |
| 64 | 2020 | 30.16 | 39.49 | 42.65 | 51.80 | 0.00% | 1.393 |
| 100 | 2076 | 46.09 | 56.93 | 62.22 | 85.52 | 0.00% | 1.403 |
| 150 | 2075 | 72.07 | 82.61 | 88.81 | 103.95 | 0.00% | 1.429 |
| 200 | 2116 | 94.35 | 105.18 | 109.93 | 115.94 | 0.00% | 1.434 |

**No errors at any level, up to 200 VUs.** The sweep reached its 200-VU ceiling without
the app failing, so the stress boundary is elsewhere (Stage 4).

---

## The knee is at 8 VUs

Two independent signals agree.

**1. Throughput saturates.** Marginal gain per doubling:

| step | req/s gain |
|---|---|
| 1 → 2 | +35% |
| 2 → 4 | +21% |
| 4 → 8 | +10% |
| 8 → 16 | **−2%** |
| 16 → 200 | +10% total across 12× more concurrency |

Past 8 VUs the server delivers ~1,950–2,100 req/s no matter how many clients wait. Beyond
that point, added concurrency buys queue depth, not work.

**2. Latency becomes linear in concurrency.** From 16 VUs upward, p50 tracks VU count
almost exactly — 7.85, 15.58, 30.16, 46.09, 72.07, 94.35 ms for 16, 32, 64, 100, 150, 200
VUs. That is Little's Law with throughput pinned: with λ fixed, waiting time rises in
proportion to the number in the system. Textbook post-saturation queueing.

## The server is the bottleneck, not the load generator

This is the measurement that makes the rest trustworthy. Node's CPU consumption:

- 1 VU → **0.898 cores**
- 4 VUs → 1.377
- 8 VUs and beyond → **flat at ~1.40 cores**, never rising again

Node runs JavaScript on one thread; the excess above 1.0 is the libuv threadpool doing
`readFile`. The plateau at ~1.40 from 4 VUs onward means the SUT hits its own ceiling
early and stays there. Because latency keeps climbing while the server's CPU draw does
**not**, the queue is forming inside the SUT — not in k6, and not from the two processes
fighting for cores. The host has 16 logical processors and is nowhere near saturated at
any point.

Threat T1 (shared machine) is therefore not fatal here. It is still real for absolute
numbers, which include no network latency at all.

## What the tail actually does — the finding worth keeping

Tail divergence, p99 ÷ p50:

| VUs | p99/p50 |
|---:|---:|
| 1 | 1.95 |
| 2 | 2.18 |
| **4** | **3.84** |
| 8 | 3.48 |
| 16 | 2.32 |
| 32 | 1.70 |
| 64 | 1.41 |
| 100 | 1.35 |
| 150 | 1.23 |
| 200 | 1.17 |

**Divergence peaks at 4–8 VUs and then falls away.** Absolute p99 keeps rising, but the
tail stops being *distinctively* worse than the median, because under heavy queueing every
request is uniformly slow.

That has a direct bearing on the paper's argument, and it cuts slightly against the naive
version of it: percentile analysis reveals the most *versus* the mean **near the onset of
saturation**, not at extreme load. At 200 VUs, mean and p99 tell nearly the same story
(94 ms vs 110 ms). At 4 VUs they do not (2.0 ms vs 7.8 ms — the tail is nearly 4× the
median while the mean still looks healthy). A monitoring system watching averages would
be least trustworthy exactly in the region a real service normally operates in.

The absolute p99 jump from 2.70 ms (2 VUs) to 7.84 ms (4 VUs) — a 2.9× rise while p50 rose
only 1.6× — is the first point where the tail moves independently of the median.

## Levels chosen for the load matrix

Applying the stated default (low / knee / 2× knee):

| Level | VUs | Why |
|---|---|---|
| **low** | **2** | Unsaturated. Throughput still scaling (+35% over 1 VU), cores 1.21. Real concurrency, no queueing |
| **knee** | **8** | Throughput saturation point; last level with meaningful throughput gain |
| **2× knee** | **16** | First fully post-saturation level; queueing dominates, throughput flat |

1 VU was rejected for "low" because it has no concurrency at all — every request is
serialised, so it cannot show queue effects even in principle. 2 VUs is the smallest level
that is genuinely concurrent while still unsaturated.

## Caveats

- 20 s per level is short. It is adequate for locating a knee but the matrix uses 180 s
  runs for the numbers that go in the paper.
- Absolute latencies are loopback-only — no network stack beyond localhost, no TLS, no
  real client. Only relative comparisons are meaningful.
- Power plan was Balanced during the sweep (threat T4); frequency scaling adds variance.
- Every level ran zero errors, so the error-rate stopping rule never triggered.
