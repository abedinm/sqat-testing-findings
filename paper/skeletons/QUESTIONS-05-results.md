# §5 Results — answer these out loud

**2,459 words. 41% of the paper. This is the section that decides whether you clear 20%.**

## The trick that makes this tractable

**Tables and figures are data, not prose.** They were generated from your run outputs, not
written. You can look at every table and every figure in the paper as much as you like
while writing — that isn't copying, and it isn't what a detector scores.

So you are not writing 2,459 words from nothing. For each subsection you are answering:
*what did I change, what did the numbers do, and what does that mean?* The numbers are
already sitting in front of you in the table.

Open the PDF to the tables. Keep `paper.md` closed.

## How to work

Ten subsections, 5.1 to 5.10. Do one per sitting. Each is 150–400 words. After each one:

```
python scripts/build_paper.py
python scripts/verify_paper.py
```

Send it to me and I check it against `facts.json`. I will not touch your sentences.

---

## 5.1 Calibration — the knee (~330 words)

Supporting data: **Table 3** (tail divergence across the sweep), **Fig. 3**.

1. How many concurrency levels did you run, and from how many virtual users to how many?
2. At what VU count does throughput stop improving? Walk through the marginal gain per
   doubling — what happens between 1→2, 2→4, 4→8, and then at 16?
3. Past that point, what does throughput do as you keep adding clients? What does latency
   do instead?
4. Why is that Little's Law? (throughput pinned, so more clients means more waiting)
5. Now the CPU evidence. What did the Node process's CPU draw do from 4 VUs onward, while
   latency kept climbing? Why does that tell you the queue is inside the application and
   not in k6?
6. Look at Table 3. Where is p99/p50 highest? Where is it lowest?
7. That's backwards from what people expect. Why does heavy queueing make the tail *less*
   distinctive? (everyone waits, so the spread shrinks in relative terms)
8. Where do real production systems usually sit on that curve — near the knee, or far past
   it?

---

## 5.2 Arm A — the baseline matrix (~180 words)

Supporting data: **Table 4**, **Fig. 4**.

9. How many runs, across how many concurrency levels and how many routes? How many failed?
   How many warm-up runs did you throw away, and why throw away the first one?
10. Find the row with the *lowest* load in Table 4. What is the mean, and what is the p99?
    Would a dashboard showing that mean look healthy?
11. Now the highest-load row for the same route. What happened to the p99/mean ratio?
12. So what does this arm show about *when* the conventional claim looks most convincing?

---

## 5.3 Stress — breaking point and failure mode (~340 words)

Supporting data: **Table 5** (both stages side by side).

13. The first ramp went to 12,000 offered requests per second and did not trigger the
    stopping criteria. Why not? (in-flight requests capped at 4,000 VUs, service rate near
    2,000/s, so Little's Law bounds the wait at 2 s)
14. Why would reporting that as the server's breaking point have been wrong? Whose ceiling
    was it?
15. What did you change for stage 4b, and what error rate did it reach?
16. Look at the "iterations the generator could not place" row for both stages. What is the
    difference, and why is that the giveaway that stage 4 was a client-side limit?
17. When the server finally broke, how many HTTP 5xx responses did it return? So where did
    the failure actually happen?
18. Did memory and handles recover after load stopped? What does that rule out?
19. Final point: what would someone watching only HTTP status codes have seen at the moment
    several per cent of users could not connect?

---

## 5.4 Soak — H1 refuted (~290 words)

Supporting data: **Table 6**.

20. How long did it run, how many requests, at what concurrency, and what error rate?
21. Compare early-window p95 against late-window p95. What is the degradation ratio?
22. So what happened to H1? Say "refuted" plainly.
23. What did memory do across the four quarters? What does a plateau rule out?
24. Why is the per-request cost real but non-accumulating? (expensive but stateless — each
    request allocates and releases)
25. Now the statistical trap. The Mann-Whitney p-value underflowed double precision. The
    effect size r is negligible. At 4.2 million samples, what happens to *any* difference?
26. What would you have wrongly concluded if you had reported the p-value on its own?

---

## 5.5 Arm D — dataset scale, H2 refuted (~230 words)

Supporting data: **Table 7**, **Fig. 6**.

27. What did you do to the dataset, and at what scale factors?
28. Look at the mean column down the table. Is it flat? What shape is it?
29. Why is that shape exactly what you would predict from `JSON.parse` being O(n)?
30. Now look at p99/mean down the same table. Which direction does it move as the data gets
    bigger?
31. So what happened to H2? And what general rule does §5.1 plus §5.5 now support — when
    cost rises uniformly, is the mean adequate or not?
32. The ×1000 row has very few samples. Say so, and say which figure in that row you trust
    and which you don't.

---

## 5.6 Arm C — variance injection, H4 (~520 words, the most important)

Supporting data: **Table 8** (the percentile ladder), **Fig. 7**.

33. What do Arms A, D and the soak all have in common? (they all vary *uniform* cost)
34. So what does Arm C hold constant, and what does it vary instead?
35. Which two real endpoints did you mix, and why does using two real endpoints rather than
    an artificial delay matter?
36. Take the 90/10 mix against the 100% expensive workload. What factor did the mean fall
    by? What factor did p99.9 fall by? What's the gap between those two factors?
37. Same expensive work in both. So what is the mean doing that p99.9 isn't?
38. Now the sharper result. Look at the p99 column for the 0.1% mix and for 100% cheap.
    What do you notice?
39. State the rule: a percentile at rank p can only see a slow path of incidence q when
    p > 100(1−q). Say why that follows from what a percentile *is*. It's definitional — do
    not present it as a discovery.
40. Then say what the measurement actually adds: a real system tracked that bound exactly,
    with no softening from queueing or noise.
41. Walk the three incidence levels: at 10%, from which percentile is the slow path visible?
    At 1%? At 0.1%?
42. What does that mean for anyone running a p99-based SLO?
43. The caveat. Expensive requests are individually *faster* when they're rare, because they
    queue behind cheap work instead of behind each other. So how much of the compression is
    dilution and how much is self-queueing? Can this design separate them? Say no.

---

## 5.7 Arm B — rate limiting, H3 confirmed (~450 words)

Supporting data: **Table 9**, **Fig. 8**.

44. What limit does the app enforce on `/api/search`, and why does a per-IP limit become a
    system-wide limit in your test?
45. What exactly differed between the two conditions? What was held constant? How many runs
    each, after discarding warm-up?
46. Read the "limiter on" column of Table 9 as if you'd never seen the error rate. What
    would you conclude about the system?
47. Now the error rate. What fraction of requests failed?
48. Is the speed real or an artefact? Explain what a 429 actually costs versus what a real
    search costs — the read, the parse, rebuilding 174 searchable records, scanning them.
49. What happened to p99 — did it correct the mean, or move the same way for the same
    reason?
50. So what is the problem here? It isn't that the mean summarises badly. What is it?
51. Important attribution: Google's monitoring guidance already says to separate the latency
    of successful and failed requests. So what does *your* arm add that the guidance doesn't?
52. Last point, and be fair to the app: is the rate limiter broken? What is actually at
    fault — the application or the metrics?

---

## 5.8 Arm E — coordinated omission (~380 words)

Supporting data: **Table 10**, **Fig. 9**.

53. What does a closed-model executor do between requests? What does that mean for how many
    requests you send during a slow period?
54. So which direction does that bias your percentiles?
55. Why did you measure it rather than just declaring it a limitation?
56. At the matched rate (1100/s), what is the open-model p99 against the closed-model p99?
    What factor?
57. Be careful here: you have two retained runs and they disagree. So what can you claim,
    and what can you *not* claim? (direction and rough order, not a correction factor for
    the whole paper)
58. Now the cliff. Going from 1100/s to 1400/s — roughly 20% past sustainable throughput —
    what did the mean do?
59. Compare that to the closed-model matrix from 2 to 16 VUs. What shape was that?
60. Why can a closed-model test never produce that cliff? (its offered load is throttled by
    the very slowdown it's measuring)
61. Which is the stronger argument for open-model load generation — the percentile bias, or
    the cliff?

---

## 5.9 Percentiles over requests vs over per-interval means (~220 words)

Supporting data: **Table 11**.

62. What does a monitoring system usually store — every request, or one summary per
    interval?
63. So you recomputed p99 over per-second means. What did you get, against the per-request
    p99?
64. Now the honest part. You expected the time-weighted figure to be *higher*, because fast
    periods contribute more samples and flatter the tail. Which way did it actually go?
65. Why? (taking a mean inside each interval destroys all the within-interval variance
    before the percentile is computed, and your tail lives inside individual seconds)
66. Can this design separate the two mechanisms? Say no, and say what the number should
    therefore be called.
67. What survives regardless: a p99 over requests and a p99 over per-interval averages
    differ here by more than 2×. Which one do most monitoring stacks actually store?

---

## 5.10 Coefficient of variation (~320 words)

Supporting data: **Table 12**, **Fig. 10**.

68. What is the coefficient of variation, and why would anyone reach for it to detect
    variance?
69. Read the CV column down Table 12. Which workload scores highest? Which scores lowest?
70. Say plainly why that's the wrong way round.
71. What would an operator watching CV conclude about the workload with no slow path at all?
72. The mechanism: CV is σ/μ. For the cheap workload the median request completes below the
    timer's resolution. So what is a few hundred microseconds of scheduler noise as a
    *fraction* of a 0.337 ms mean?
73. What happens to the ratio as the expensive path grows?
74. Two limits you must state: how many runs is this per workload, and is the mechanism
    something this design isolates or an interpretation of the arithmetic?
75. Close it: what does this constrain in your own §6.4 recommendation?

---

## Rules for the whole section

- **Do not** claim any result generalises beyond one application on one host. §7 covers it.
- **Do not** call a refuted hypothesis a disappointment. H1 and H2 refuted, reported
  honestly, is the strongest thing in the paper.
- **Do not** use "significant" to mean "large" anywhere near a p-value.
- Every number you need is in a table. Do not retype numbers into the prose from memory —
  where the template has `{{a_placeholder}}`, leave it exactly as it is.
