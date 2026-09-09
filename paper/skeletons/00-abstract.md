# Abstract — skeleton

Target: ~330 words, four paragraphs, plus the keyword line.

**Write this LAST.** It summarises everything else, and it is far easier once §3, §6 and
§8 are in your own words. Much of it is a compression of §8 — say the same things, shorter,
without the cross-references.

Keep every `{{placeholder}}` exactly as written.

---

## Para 1 — setup and method  (~70 words)

- mean response time is the default summary statistic in web performance reporting
- ISO/IEC 25010 names it under the *time behaviour* sub-characteristic of performance
  efficiency (keep *time behaviour* in italics)
- practitioner literature widely asserts averages conceal tail-latency failures that
  percentiles expose
- this paper tests that assertion empirically rather than assuming it
- one real Node.js web application, six controlled load arms,
  `{{total_requests_m}}` million requests, k6

---

## Para 2 — the main finding  (~120 words)

Lead with the verdict: **conditionally true, and false in the form it is usually stated.**

Uniform cost rise — mean tracks it faithfully, tail becomes less distinctive:

- deeper request queues, or dataset scaled from `{{dataset_records}}` to 188,000 records
- p99/mean falls from `{{scaled_x1_api_content_ratio}}` to `{{scaled_x1000_api_content_ratio}}`
- absolute latency rises three orders of magnitude
- one-hour soak, `{{soak_requests_m}}` million requests, degradation ratio
  `{{soak_degradation}}` — i.e. none

Variable rather than uniformly slow — mean fails as predicted:

- diluting identical expensive work 100% → 10% of requests
- mean falls by `{{armc_mean_dilution_10}}`x, p99.9 by only `{{armc_p999_dilution_10}}`x

Then the constraint on the remedy:

- a slow path affecting 0.1% of requests was **entirely invisible to p99**
- p99 read `{{ladder_mix_0p1pct_p99}}` ms against `{{ladder_uniform_cheap_p99}}` ms for a
  workload containing no slow path at all

---

## Para 3 — the result that breaks both statistics  (~60 words)

- when the rate limiter engaged: mean improved `{{armb_improvement_x}}`-fold,
  p99 improved `{{armb_p99_improvement_x}}`-fold
- while `{{armb_enabled_failed_pct}}`% of requests failed
- mean and percentile alike reported dramatic improvement as the service stopped
  functioning

---

## Para 4 — conclusions  (~60 words)

Three, in this order:

1. the mean conceals variance, not slowness
2. percentile analysis is most valuable near the onset of saturation, not under heavy load
3. no latency statistic is interpretable without an error-rate denominator

Then one line: a coordinated-omission control arm is included to bound the measurement
bias in the study's own method.

---

## Keywords line — leave exactly as-is

```
Keywords: performance testing, tail latency, percentiles, load testing, coordinated
omission, ISO/IEC 25010
```

---

## Do not claim

- **No citations in an abstract.** ISO/IEC 25010 by name is fine; `[3]` is not.
- **No numbers that don't appear in §5.**
- **Not** "this paper presents..." or "in this paper we...". Start with the subject:
  mean response time.
- **Not** "novel", "significant", "comprehensive". The results are interesting on their
  own; adjectives make them look weaker.
- Keep the verdict in para 2 blunt. "Conditionally true, and false in the form it is
  usually stated" is the strongest sentence in the abstract — do not hedge it.
