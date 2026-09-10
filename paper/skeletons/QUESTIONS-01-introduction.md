# §1 Introduction — answer these out loud

549 words in three parts: the setup, §1.1 Hypotheses, §1.2 Contributions.

Write this **after** §3, §5 and §6. It reads like the opening but it's easier to write once
you know what the paper found.

Keep `{{total_requests_m}}` and every other `{{placeholder}}` exactly as written. Keep the
citation markers `[1]` through `[4]` where they are — they point at specific sources.

---

## The setup (~250 words)

1. What single statistic dominates web performance reporting? Where does a working
   developer actually see it? (dashboards, service reports)
2. ISO/IEC 25010 `[1]` defines performance efficiency and puts response time under *time
   behaviour*. Its companion ISO/IEC 25023 `[2]` defines mean response time as a measure
   against that. So the average isn't just a habit — what is it?
3. Against that, what does the practitioner literature say? Google's SRE book `[3]` says a
   long tail can hide behind an average; Dean and Barroso `[4]` argue the same at fan-out
   scale. Keep both quotations exactly as they appear — they're verbatim and verified.
4. Here's the pivot, and it's the reason the paper exists. The claim is repeated constantly.
   How often is it tested on **one system where you control the cause of the slowdown**?
5. So what does this paper do differently?

---

## §1.1 Hypotheses (~150 words)

Keep this as a bulleted list of four. Say up front that three were stated before data
collection and the fourth came after the first results contradicted two of them.

6. H1 — what did you expect a system doing avoidable per-request work to do over a long run?
7. H2 — what did you expect the mean to do as the dataset grew, versus the high percentiles?
8. H3 — what did you expect to happen to conventional metrics when a protective mechanism
   sheds load?
9. H4 — this one you wrote *after* seeing the data. What is it? (the mean hides variance,
   not uniform slowness)

Then the honest sentence: which were refuted, which confirmed, and why is reporting the
refutations the substantive part rather than an embarrassment?

---

## §1.2 Contributions (~150 words)

Numbered list of four. Each is one or two sentences. Be careful here — this is where a
reviewer looks for overclaiming, and two of these have already been corrected once for it.

10. Contribution 1 — separating uniform slowness from response-time variance on one system.
    What does that decomposition show about when the mean actually fails?
11. Contribution 2 — tail divergence peaks near saturation and *falls* under heavy load.
    Say what intuition that reverses.
12. Contribution 3 — **be careful**. The principle that latency needs an error rate is
    already in the monitoring literature `[3]`. So do not say you established it. Say what
    you measured: the size of the distortion on a real application, and that percentiles
    fail alongside the mean rather than correcting it.
13. Contribution 4 — the coordinated-omission control and the sampling-unit measurement.
    Again: neither mechanism is new. What did you do with them that studies usually don't?
    (measured them on your own data instead of assuming them away)

---

## Do not claim

- **Not** that this is the first study of tail latency. It isn't, and [3] and [4] are right
  there in your own reference list.
- **Not** "to the best of our knowledge" — you did not run a systematic literature search.
- **Not** that the results generalise. One application, one runtime, one host.
- No "In this paper we present..." opening. Start with the subject: mean response time.
