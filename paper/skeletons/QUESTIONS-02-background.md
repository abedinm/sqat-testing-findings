# §2 Background and Related Work — answer these out loud

470 words, six short labelled paragraphs.

## Read this part first

**This is the only section you cannot write purely from what you already know.** It is
about other people's work, and neither of us has read those papers in full. That's a real
weakness and it's the section a viva question would target.

Before writing, spend 40 minutes reading **abstracts only** for these four. Abstracts are
short and free:

| Ref | Read this | Why |
|---|---|---|
| `[4]` | Dean & Barroso, "The Tail at Scale" | Your headline citation. Know what it argues. |
| `[7]` | Schroeder et al., "Open versus closed" | Directly underpins §5.8 |
| `[10]` | Hoefler & Belli, SC'15 | Underpins §4.3 |
| `[11]` | Mytkowicz et al., ASPLOS'09 | Underpins §7 |

Links are in the References section of the paper. Forty minutes of abstracts buys you more
defensibility than anything else left on the list.

Keep every citation marker exactly where it sits.

---

## Paragraph 1 — Tail latency `[4]` (~80 words)

1. What do Dean and Barroso argue happens in large services made of many components?
2. Their concern is *variability*, not slowness. Why does that distinction matter so much
   to your paper? (it's your central axis)

---

## Paragraph 2 — Percentiles as indicators `[3]` (~90 words)

3. What does Google's SRE practice recommend instead of averages?
4. Keep the two quotations exactly as printed — they're verbatim and verified. In your own
   words around them: what does a high percentile show you that a median doesn't?
5. There's a second SRE point about user studies and response-time variance. Why does that
   one land on variance again rather than on speed?

---

## Paragraph 3 — Coordinated omission `[5]` `[6]` `[7]` (~110 words)

6. Tene's critique: when a load generator's request rate is coupled to the system's
   responses, what happens to the requests that *would* have been sent during a slow spell?
7. So which direction does that push the percentiles?
8. The k6 documentation says the same in tool-specific terms. Keep those quotations verbatim.
9. Schroeder, Wierman and Harchol-Balter `[7]` establish it experimentally. What did they
   show about open versus closed models? (read the abstract)
10. One sentence: what do you do about it, and where? (§5.8)

---

## Paragraph 4 — Queueing `[8]` (~50 words)

11. State Little's Law: L = λW. What does each term mean?
12. What do you use it for in this paper? (separating real server saturation from a load
    generator artefact — §4.4 and §5.3)

Short paragraph. Two or three sentences.

---

## Paragraph 5 — Standards `[1]` `[2]` (~70 words)

13. ISO/IEC 25010 defines performance efficiency; *time behaviour* covers response time and
    throughput. ISO/IEC 25023 defines mean response time as the measure against it.
14. So if the standard's measure is the mean, what is the question this paper is asking?

---

## Paragraph 6 — The gap (~70 words)

15. How does the practitioner literature mostly make its case? (argument, plus observational
    data from production systems)
16. What's missing in production data? (nobody controls the cause of the degradation)
17. So what does this study vary deliberately? Name the four: queue depth, dataset size,
    response-time variance, load shedding.
18. And the sentence that makes the paper honest: it reports where the mean **succeeds** as
    well as where it fails.

---

## Do not claim

- **Not** "extensive research has shown" or "a growing body of literature" — you have
  eleven references and haven't read most of them in full.
- **Not** "no prior work has examined" — you didn't run a systematic search, and §5.7's
  result was already partly in `[3]`.
- **Not** a summary of a paper you've only seen the title of. If you didn't read the
  abstract, don't characterise the paper beyond what your own sentence needs.
