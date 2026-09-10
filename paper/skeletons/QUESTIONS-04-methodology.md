# §4 Methodology — answer these out loud

452 words across five subsections. This is description of what you did, so it should come
easily once you start. Do it early — right after §3.

Supporting data: **Table 1** (environment) and **Table 2** (the eight arms), **Fig. 2**.
Both are data. Look at them freely.

---

## 4.1 Environment (~130 words)

Table 1 carries the machine details, so don't retype them into the prose.

1. The load generator and the system under test ran on the same machine. Say so plainly.
   Why is that a problem, and where do you deal with it? (§7, and the specific fix in §4.4)
2. What is the worst thing that shared host could do to your conclusions? (make you mistake
   generator contention for server saturation)
3. The application under test is a copy. What happened to the original? Say clearly that it
   was never modified.
4. One four-line change was made to the copy. What does it do, and what happens when the
   environment variable is unset? (nothing — it's inert)

---

## 4.2 Instrumentation and data handling (~120 words)

5. Roughly how many metric points does k6 emit per request? What did a 30-second run at one
   virtual user produce in megabytes?
6. So what would the full experiment have produced? Why couldn't you keep it all?
7. What did you reduce each request down to? Name the four fields.
8. Critical: what did you NOT do to the data? (no aggregating, no rounding, no sampling)
9. How did you prove the reduction lost nothing? (request-count equality against k6's own
   summary — say the soak numbers matched exactly)
10. Last sentence: how does every number in the paper get there, and what does that rule out?

---

## 4.3 Statistical treatment (~110 words)

11. Which percentiles do you report?
12. Sampling unit: percentiles here are over per-request samples. What else does each run
    report, and what kind of monitoring system would produce that instead? Point at §5.9.
    Be careful — call it an aggregation effect, not a bias measurement.
13. Why Mann-Whitney rather than a t-test? (response-time distributions are not normal)
14. Why report effect size next to p? What happens to a p-value at millions of samples?
15. Whose practice are you following here? Georges et al. `[9]` for performance evaluation,
    Hoefler and Belli `[10]` for benchmarking. What did both find about how systems papers
    usually report results?

---

## 4.4 Distinguishing saturation from contention (~50 words)

16. Two processes, one host. A knee in the latency curve could mean two different things.
    What are they?
17. How did you tell them apart? (sample the Node process's own CPU draw at each level)
18. Node runs JavaScript on one thread. So what does a CPU plateau *with latency still
    rising* prove about where the queue is?

---

## 4.5 Experimental arms (~40 words)

Table 2 lists all eight arms and Fig. 2 draws them. The prose here is short — the table
does the work.

19. One sentence pointing at the figure.
20. Which executor did the load runs use? Which did stress and the §5.8 control use?
21. What did you do with the first run of every cell, and why?

---

## Do not claim

- **Not** that the shared host is fine. It isn't. You mitigated it, you didn't eliminate it.
- **Not** that the reduction is lossless in general — it's lossless *for the fields you
  kept*, verified by count.
- **Not** that n = 4 is a large sample. §7 already admits the smaller arms.
