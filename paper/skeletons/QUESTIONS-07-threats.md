# §7 Threats to Validity — answer these out loud

338 words, seven short labelled paragraphs. Each is two or three sentences.

This section is where honesty scores marks. A reviewer who finds a weakness you already
admitted thinks better of you, not worse. Do not soften any of these.

---

1. **Shared host.** What ran on one machine? What evidence limits the damage (§5.1's CPU
   plateau)? Does that eliminate the problem or just bound it? And what does it mean for
   your absolute latency numbers — are they upper or lower bounds? What do you actually
   claim as a result: absolute values, or relative comparisons?

2. **Closed-model measurement.** Which arms used a closed-model executor, and what are they
   therefore subject to? Which arm bounds it? Which direction is the bias — does it make
   your reported tail divergences too big or too small? (optimistic bias means your
   divergences are conservative)

3. **Single application.** One Node.js server, one degradation mechanism. You believe the
   uniform-versus-variance split generalises because it's a property of distributions rather
   than of your app. Say that — and then say plainly that it is an argument, not a
   measurement. What would settle it?

4. **Repeat counts.** Go arm by arm and give the honest n for each: Arm A, Arm D at each
   scale, Arm B on and off, Arm C, Arm E. Then the fair summary: the effects are large
   relative to the spread you saw, but what would the smaller arms not support?

5. **The ×1000 scale.** At that dataset size, roughly how many requests per second did you
   get? So how many samples is its p99 resting on? Which figure at that scale is well
   supported and which is indicative only?

6. **Background load and power.** What kind of software environment and power profile did
   the host run? Was that variance quantified? Was it identical across arms? Then cite
   Mytkowicz et al. `[11]` — what did they show about incidental features of a setup? Why
   does "identical across arms" bound a differential effect but not a common one?

7. **Construct validity of Arm C.** How did you induce variance — by varying one endpoint's
   cost, or by mixing two endpoints? Why is that realistic? And why is it still not the same
   thing as a single endpoint with variable cost?

---

## Do not claim

- **Not** "however, these limitations do not affect our conclusions." They do. That sentence
  undoes the whole section.
- **Not** a closing sentence that reassures. End on the last threat and stop.
- Keep every `[11]` and `§x.y` marker exactly as written.
