# §6 Discussion — skeleton

Target: ~370 words across four numbered subsections. Keep the subsection headings and
the block quote. This is where your voice matters most: it is the section that reads
most generically when it isn't yours.

Rules: keep every `{{placeholder}}` and every `(§5.x)` cross-reference exactly as written.

---

## 6.1 The mean conceals variance, not slowness  (~110 words)

The single most important paragraph in the paper. It is the refined claim.

Set up the contrast:

- **uniform cost rise** → mean tracks it faithfully, p99/mean *falls*
  - happens via deeper queues (§5.1), larger datasets (§5.5), sustained load (§5.4)
- **cost concentrated in a minority** → mean falls toward the cheap majority, tail
  correctly reports the affected minority (§5.6)

Then state that the common formulation ("average response time conceals degradation")
is too broad.

Keep this block quote as the precise claim — rewrite it in your words, keep the `>`:

> The arithmetic mean is an adequate summary of response time when the response-time
> distribution is unimodal and cost is uniformly distributed across requests. It fails
> specifically, and severely, when a minority of requests carry disproportionate cost.

Close by noting that condition describes most real degradations: a slow dependency on one
code path, a cache-miss class, a tail of large records.

---

## 6.2 Percentiles matter most before a system looks broken  (~90 words)

Facts:

- divergence peaked at 4 VUs: `{{calib_ratio_4}}`
- fell to `{{calib_ratio_200}}` at 200 VUs
- same inversion appears across dataset scale

The mechanism, in your own words: under heavy queueing, delay is *shared*, so the
distribution tightens in relative terms.

The consequence to land: percentile monitoring gives most information exactly where a
mean-based dashboard looks healthiest, and least where any instrument would show a
problem.

You are answering: *when is this actually worth doing?*

---

## 6.3 No latency statistic survives without an error rate  (~80 words)

Facts:

- §5.7: mean and p99 both improved by more than an order of magnitude
- while `{{armb_enabled_failed_pct}}`% of requests failed
- §5.3: stress arm hit its breaking point with **zero HTTP error responses** — it failed
  at the connection layer instead

The point: latency statistics describe only requests that were *served*. Any reporting
regime without an error rate, and without a count of requests never served at all, can be
made to look arbitrarily good by a system that fails faster.

---

## 6.4 Implications for practice  (~90 words)

Keep as a numbered list, three items:

1. report mean **and** a high percentile **and** an error rate — any one alone is defeasible
2. prefer variance-sensitive indicators (p99/p50, or coefficient of variation) over
   absolute percentiles when watching for emerging problems, because absolute divergence
   shrinks under heavy load
3. state the sampling unit for percentiles (§5.9) and the load model (§5.8) — both
   materially change the number reported

---

## Do not claim

- **Not** that this generalises to all web applications. One app, one runtime. §7 says so.
- **Not** that percentiles are "better" than the mean. Your §5.7 result kills both equally.
  The paper's position is that neither survives without an error rate.
- **Not** that practitioners are wrong to use averages. The finding is that the usual claim
  is *too broad*, not that it is false. That distinction is the contribution.
- Avoid "it is important to note", "it should be emphasised", "this highlights". Just say
  the thing.
