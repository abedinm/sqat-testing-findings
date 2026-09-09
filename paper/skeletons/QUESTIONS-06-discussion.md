# §6 Discussion — answer these out loud

Four subsections, ~370 words total. Every number you need is here, so you never have to
open `paper.md` and see my sentences.

Keep the four subsection headings. Keep the `{{placeholders}}` exactly as written where
shown — the build fills them.

---

## 6.1 The mean conceals variance, not slowness (~110 words)

The most important paragraph in the paper. This is your actual finding.

1. You changed cost in two different ways across the study. What were the two ways?
   (uniform — everything gets slower together; concentrated — only some requests get slower)

2. When everything slowed down together, what did the mean do? Did it lie or not?

3. And what happened to the gap between p99 and the mean as things got worse?
   You saw this three separate times: deeper queues (§5.1), bigger dataset (§5.5),
   long soak (§5.4).

4. When only a minority of requests were slow, what did the mean do instead?

5. So what's wrong with saying "averages hide degradation"? Why is that too broad?

6. Say the precise version. When is the mean fine, and when exactly does it fail?

Then restate this as a block quote (keep the `>`), in your words:

> The mean is an adequate summary when cost is spread evenly across requests.
> It fails specifically, and badly, when a minority of requests carry most of the cost.

7. Last question: is that rare in real systems, or common? Give two or three real examples
   of a minority of requests being expensive.

---

## 6.2 Percentiles matter most before a system looks broken (~90 words)

**Numbers you need:** divergence peaked at 4 VUs at `{{calib_ratio_4}}`, and fell to
`{{calib_ratio_200}}` at 200 VUs. Same inversion in the dataset arm: `2.55` down to `1.13`.

1. Where was the tail most extreme — at light load or heavy load? Say the two numbers.

2. That's backwards from what people expect. Why does it happen? Think about what
   queueing does to *every* request when the server is swamped.

3. Now the practical part: a dashboard showing averages — when does it look healthiest?
   And when is percentile monitoring telling you the most?

4. Where do production systems normally sit on that curve?

---

## 6.3 No latency statistic survives without an error rate (~80 words)

**Numbers you need:** in §5.7 the mean improved `{{armb_improvement_x}}`x and p99 improved
`{{armb_p99_improvement_x}}`x while `{{armb_enabled_failed_pct}}`% of requests failed.
In §5.3 the stress test broke with **zero** HTTP 5xx responses.

1. In the rate-limiter arm, what happened to the mean and to p99? And what happened to the
   service at the same time?

2. In the stress arm, how many HTTP error responses did the server return when it broke?
   So where did the failure actually show up?

3. What do latency statistics actually measure? Which requests are in that number, and
   which requests are missing from it entirely?

4. So what can a system do to make its latency numbers look arbitrarily good?

This is the one that undermines percentiles too, not just the mean. Say that plainly.

---

## 6.4 Implications for practice (~90 words)

Keep this as a numbered list, three items. One or two sentences each.

1. What three things should someone report together, and why is any one of them alone
   defeatable?

2. If you're watching for a problem *starting*, should you watch absolute p99, or the
   ratio between percentiles? Why? (tie it back to 6.2 — absolute divergence shrinks under
   heavy load)

3. Two things a paper or a dashboard must state about how a percentile was computed,
   or the number can't be compared to anyone else's. (§5.9 sampling unit, §5.8 load model)

---

## Do not claim

- **Not** that this applies to all web applications. One app, one runtime. §7 says so.
- **Not** that percentiles beat the mean. Your §5.7 result kills both equally — that's
  the sharper point and it's yours.
- **Not** that practitioners are wrong to use averages. Your finding is that the usual
  claim is *too broad*, not false. That distinction is the contribution.
- Avoid "it is important to note", "this highlights", "it should be emphasised". Say it.

---

## When you have written it

Paste it into `paper/paper_template.md`, replacing the §6 block, then:

```
python scripts/build_paper.py
python scripts/verify_paper.py
```

Send it to me and I'll check it against the data. I won't touch your sentences.
