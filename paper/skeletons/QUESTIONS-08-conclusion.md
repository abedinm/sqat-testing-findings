# §8 Conclusion — answer these out loud

Four paragraphs, ~260 words. Graders read this closely.

**No new results here.** Everything must already appear in §5. If you find yourself
introducing something new, it belongs in §5 or nowhere.

Keep every `{{placeholder}}` exactly as written.

---

## Para 1 — what you set out to test, and the verdict (~40 words)

1. What was the claim you set out to confirm? (that the mean hides tail-latency failures
   percentiles reveal)

2. You tested it under three different conditions. In how many did it hold?

Say it flatly. One in three. Do not soften it, do not apologise for it — a refuted
hypothesis reported honestly is worth more than a confirmed one reported loosely.

---

## Para 2 — uniform versus concentrated (~110 words)

**Numbers:** p99/mean fell from `{{scaled_x1_api_content_ratio}}` to
`{{scaled_x1000_api_content_ratio}}` while latency rose three orders of magnitude.
Soak: `{{soak_requests_m}}` million requests, degradation ratio `{{soak_degradation}}`.
Arm C: mean cut by `{{armc_mean_dilution_10}}`x, p99.9 by only `{{armc_p999_dilution_10}}`x.

3. When cost rose uniformly, did the mean track it or hide it?

4. What happened to the tail in that case — did it become more informative or less?
   Give the two ratio numbers.

5. What did the hour-long soak show? Give the request count and the degradation ratio.

6. Now the other condition: same total work, but redistributed so a minority of requests
   carried it. What did the mean do relative to the tail? Give both dilution factors.

7. **Then immediately narrow it.** Below roughly what incidence does a slow path become
   invisible even to p99?

Question 7 is the line reviewers will remember. Put it at the end of the paragraph, not
buried in the middle.

---

## Para 3 — the result that breaks both statistics (~50 words)

**Numbers:** mean improved `{{armb_improvement_x}}`x, p99 improved
`{{armb_p99_improvement_x}}`x, `{{armb_enabled_failed_pct}}`% of requests failed.

8. Open by saying this one concerns *neither* statistic — it breaks both. Why does that
   matter more than a result about just the mean?

9. Under load shedding, what happened to mean and p99, and what happened to the service?

10. So what is the one thing a latency number can never be interpreted without?

---

## Para 4 — refined claim and future work (~60 words)

11. State the refined claim in your own words. Two halves: what does the mean actually
    conceal (not slowness — what?), and when is percentile analysis most valuable?

12. Future work: name two specific things someone should replicate this on. Be concrete
    (other runtimes; systems with a real database tier), not vague.

13. End on the open question: is the boundary you found a property of *distributions in
    general*, which is what the mechanism suggests, or a property of *this system*?

Stop there. No closing flourish.

---

## Do not claim

- **No new numbers.** Everything must already be in §5.
- **"Future work should..."**, not "future work will" — you are not promising to do it.
- **No generic ending.** No "as systems grow more complex", no "this remains an important
  area of research". End on question 13 and stop typing.
- **No overstatement.** Three conditions, one application. Say three conditions, one
  application.

---

## When you have written it

```
python scripts/build_paper.py
python scripts/verify_paper.py
```
