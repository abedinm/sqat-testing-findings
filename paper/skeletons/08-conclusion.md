# §8 Conclusion — skeleton

Target: ~260 words, four paragraphs. Graders read this closely. No new results here —
everything must already appear in §5.

Keep every `{{placeholder}}` exactly as written.

---

## Para 1 — what you set out to test, and the verdict  (~40 words)

- the study set out to confirm: mean response time conceals tail-latency failures that
  percentile analysis reveals
- verdict: held in **one of three** conditions tested

Say it flatly. Do not soften it.

---

## Para 2 — the uniform case vs the variance case  (~110 words)

**Uniform cost rise — the claim failed:**

- mean tracked degradation faithfully
- tail became *less* informative, not more
- p99/mean fell from `{{scaled_x1_api_content_ratio}}` to `{{scaled_x1000_api_content_ratio}}`
- while absolute latency rose three orders of magnitude
- one-hour soak, `{{soak_requests_m}}` million requests, degradation ratio `{{soak_degradation}}`

**Same work redistributed to a minority — the claim held:**

- mean collapsed toward the healthy majority faster than the tail did
- diluting the slow path 100% → 10%: mean cut by `{{armc_mean_dilution_10}}`x,
  p99.9 by only `{{armc_p999_dilution_10}}`x

**Then immediately narrow the remedy:**

- a slow path below roughly 1% incidence is invisible even to p99

That last line is the part reviewers will remember. Do not bury it.

---

## Para 3 — the result that undermines both statistics  (~50 words)

- under load shedding: mean improved `{{armb_improvement_x}}`x, p99 improved
  `{{armb_p99_improvement_x}}`x
- while `{{armb_enabled_failed_pct}}`% of requests failed
- therefore: no latency statistic is interpretable without an error-rate denominator

Lead the paragraph by saying this one concerns *neither* statistic — it breaks both.

---

## Para 4 — refined claim + future work  (~60 words)

The refined claim, in your words:

- the mean conceals **variance**, not slowness
- percentile analysis is most valuable near the **onset of saturation**, not under evident
  overload

Future work — be specific, not generic:

- replicate the uniform-versus-variance decomposition on other runtimes
- and on systems with a genuine database tier
- open question: is the boundary condition a property of distributions in general (as the
  mechanism suggests) or of this system in particular?

---

## Do not claim

- **No new numbers.** Everything here must already be in §5.
- **Not** "future work will..." — you are not promising to do it. "Future work should..."
- **Not** a generic closing line. No "as systems grow more complex", no "this remains an
  important area". End on the open question and stop.
- **Not** overstatement: you tested three conditions on one application. Say three
  conditions on one application.
