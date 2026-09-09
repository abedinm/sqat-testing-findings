# Abstract — answer these out loud

~330 words, four paragraphs, plus the keyword line.

**Write this last.** It is a compression of §8 plus a sentence of setup. Once §3, §6 and
§8 are in your own words this takes twenty minutes, because you will already have said
every one of these things once.

Keep every `{{placeholder}}` exactly as written.

---

## Para 1 — setup and method (~70 words)

**Numbers:** six controlled load arms, `{{total_requests_m}}` million requests, k6.

1. What statistic does everyone report for web performance? Where do you see it?

2. Which standard names it, and under which sub-characteristic? (ISO/IEC 25010, *time
   behaviour* — keep the italics)

3. What does the practitioner literature widely claim about averages and percentiles?

4. What did you do about that claim — assume it, or test it? Say how: one real application,
   how many arms, how many requests, what tool.

---

## Para 2 — the main finding (~120 words)

**Numbers:** p99/mean fell `{{scaled_x1_api_content_ratio}}` → `{{scaled_x1000_api_content_ratio}}`;
dataset scaled from `{{dataset_records}}` to 188,000 records; soak `{{soak_requests_m}}`
million requests, degradation ratio `{{soak_degradation}}`; Arm C mean fell
`{{armc_mean_dilution_10}}`x versus p99.9 `{{armc_p999_dilution_10}}`x; 0.1% workload p99
`{{ladder_mix_0p1pct_p99}}` ms against `{{ladder_uniform_cheap_p99}}` ms for no slow path
at all.

5. **Lead with the verdict.** Is the claim true, false, or something more specific?
   The answer is: conditionally true, and false in the form it is usually stated.
   Say that in the first sentence of this paragraph — do not build up to it.

6. Where cost rose uniformly — what did the mean do, and what happened to the tail?
   Give the ratio numbers and the soak result.

7. Where response time was *variable* instead of uniformly slow — what did the mean do?
   Give both dilution factors.

8. Then the constraint on the fix: what happened to p99 for the 0.1% workload?
   Give both numbers. They are identical — say so.

---

## Para 3 — the result that breaks both (~60 words)

**Numbers:** mean `{{armb_improvement_x}}`-fold, p99 `{{armb_p99_improvement_x}}`-fold,
`{{armb_enabled_failed_pct}}`% failed.

9. When the rate limiter engaged, what happened to mean and p99?

10. What was happening to the service at the same moment?

11. Say the sentence that makes it land: both statistics reported dramatic improvement as
    the service stopped working.

---

## Para 4 — conclusions (~60 words)

12. Three conclusions, in this order:
    - what does the mean conceal (variance, not slowness)
    - when is percentile analysis most valuable (near the onset of saturation, not under
      heavy load)
    - what is no latency statistic interpretable without

13. One closing sentence: a coordinated-omission control arm is included to bound the
    measurement bias in the study's own method.

That last sentence matters. It tells a reviewer you measured the weakness of your own
instrument instead of hoping nobody asked.

---

## Keywords — leave exactly as is

```
Keywords: performance testing, tail latency, percentiles, load testing, coordinated
omission, ISO/IEC 25010
```

---

## Do not claim

- **No citation markers in an abstract.** Naming ISO/IEC 25010 is fine; `[6]` is not.
- **No numbers that are not in §5.**
- **Do not open with "This paper presents..."** or "In this paper we...". Start with the
  subject: mean response time.
- **No adjectives.** Not "novel", not "comprehensive", not "significant". The results are
  interesting without help; adjectives make them look weaker, not stronger.
- **Do not hedge question 5.** "Conditionally true, and false in the form it is usually
  stated" is the strongest sentence in the abstract. Leave it blunt.

---

## Final build

```
python scripts/build_paper.py
python scripts/make_docx.py
python scripts/verify_paper.py
python scripts/verify_all_numbers.py
```

Then export the PDF and check the filename still matches the title exactly.
