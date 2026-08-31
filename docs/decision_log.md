# Decision log — unattended run, 2026-08-24

Every point where I would normally have stopped to ask, with the default applied and the
reasoning. Chronological.

---

### D1 — Use a copy at `perf-web/sut/`, not the original
**When:** before Stage 1.
**Question left open from Task 1:** run the live repo in place, or copy it.
**Decision:** copied to `perf-web/sut/` via `robocopy /E /XD .git node_modules .github .vscode .claude`.
**Reasoning:** the original is the deploy source for a live client site with a git remote
pointing at production. Stages 6 and 7 *require* modifying the app (synthetic datasets,
disabling the rate limiter), which is impossible to do safely in place. Excluding `.git`
means the copy has no remote and cannot push anywhere even by accident. The safety rail
"work only inside perf-web/" makes this the only compliant option.
**Verified:** 335 files, 39.1 MB, `.git` absent, `serve.mjs` and `data/content.json`
present. Original `git status` clean.

### D2 — Port 8099
**Decision:** run the SUT on `127.0.0.1:8099`.
**Reasoning:** 8080 (app default), 8083 (`start-server.bat`), 8085, 8139, 8003 are all
used by other projects' configs on this machine. 8099 was confirmed free before starting.

### D3 — Server started via `Start-Process`, not the preview tool
**Decision:** launched with PowerShell `Start-Process node serve.mjs`.
**Reasoning:** the harness's preview mechanism resolves servers from
`C:\Users\USER\.claude\launch.json`, which is **outside `perf-web/`**. Adding an entry
there would violate the "work only inside perf-web/" rail. The rail wins. Lifecycle is
controlled explicitly: PID recorded to `data/server.pid`, stdout/stderr captured to
`data/server_*.log`, process stopped between arms.

### D4 — Discard k6 raw JSON after lossless extraction
**When:** after the smoke run produced 116.8 MB for 30 seconds at 1 VU.
**Decision:** keep `--out json` only where a time series is needed; immediately extract
`http_req_duration` points to `requests.csv` and delete the raw file.
**Reasoning:** ~17 metric points per request. The full matrix would need tens of GB
against 19 GB free on C:. The extraction is lossless for the measured quantity — one row
per request, no aggregation or sampling — verified at 30,317 of 30,317 requests preserved,
116.8 MB → 1.74 MB. The extractor refuses to delete if it extracts zero points.
**Risk accepted:** metrics other than `http_req_duration` (tls handshake, data_sent, vus)
are not retained per-request. They are not used by this study. Aggregates for all metrics
survive in each run's `summary.json`.

### D5 — Smoke route = `/services.html`
**Decision:** single-route smoke against `/services.html`.
**Reasoning:** Task 4 specifies one route. An HTML page is the most representative choice
because every HTML serve passes through `injectSEO()` → `getContent()` → `readFile` +
`JSON.parse`, which is the mechanism this study is about. It is also on no rate-limit
bucket, so the smoke result is not contaminated by 429s.

### D6 — Power plan left on Balanced
**Decision:** not changed.
**Reasoning:** the smoke run was already collected under Balanced. Switching mid-study
would make subsequent runs incomparable with it. The study's claims are about relative
percentile behaviour, not absolute throughput. Recorded as threat T4 in
`environment.md`; it is a genuine source of run-to-run variance.

### D7 — Overlay/background software left running
**Decision:** Discord, Razer Cortex and NVIDIA Overlay were left running.
**Reasoning:** they are outside `perf-web/` and stopping them alters machine state the
user did not authorise me to change while asleep. They add background CPU noise, which is
recorded as a threat rather than silently removed. All runs share the same background
conditions, so relative comparisons remain valid.

<!-- LOG CONTINUES BELOW AS THE RUN PROGRESSES -->

### D8 — Stage 3 matrix relaunched after a harness bug (FAILURE, logged)
**When:** first launch of `run_matrix.ps1`.
**What happened:** I launched the PowerShell matrix runner *from Git Bash*. Two things
broke silently:
1. MSYS path conversion rewrote the route `/services.html` into
   `C:/Program Files/Git/services.html`.
2. `-Levels 2,8,16` was passed as a single token and became the integer `2816`.

The script reported "total runs: 5" and every run failed with `K6_FAILED_EXIT_`, producing
an index of five bogus rows. **No load was generated and no measurement was taken** — the
failure was loud (drive-not-found errors) rather than silent, which is why it was caught
immediately.
**Action:** deleted `results/matrix/` and `data/stage3.log` entirely, relaunched via the
PowerShell tool where array parameters and leading-slash paths parse correctly. Verified
the relaunch printed `levels=2,8,16 routes=/services.html,/api/content,/sitemap.xml` and
`total runs: 45`, and that a k6 process was actually running.
**Retry count:** 1. No results from the failed attempt were kept or used.
**Rule applied for the rest of the run:** never invoke a PowerShell script with path-like
or array arguments from Bash.

### D9 — Rate-limiter toggle added to the copy (Stage 7 prerequisite)
**Decision:** added four lines to `perf-web/sut/serve.mjs`:
```js
if (process.env.DISABLE_RATE_LIMIT === "true") return true;
```
at the top of `applyRateLimit()`, with `serve.mjs.orig` kept alongside as the pristine copy.
**Reasoning:** Stage 7 explicitly requires running the app with the limiter disabled and
then re-enabled. An env-var toggle does that without two divergent copies of the source,
and **default behaviour is completely unchanged** when the variable is unset — so Arm A is
unaffected. This is not tuning for better numbers; it removes an artificial gate so the
application underneath can be measured, which is the stated purpose of Arm B.
**Verified:** `diff` against the pristine copy shows exactly the 4 added lines and nothing
else; `node --check` passes. Applied to the copy only — the original repo is untouched.
**Note:** the file's line endings changed CRLF → LF as a side effect of the patch script.
Functionally irrelevant to Node; recorded for completeness.
**Note:** the server process serving Stage 3 was started *before* this patch, so Arm A ran
on the pristine code. Because the toggle defaults to off, the two are behaviourally
identical.

### D10 — Stage order changed: soak (5) runs before the scaled arm (6)
**Decision:** execution order is Stage 3 → 4 → **5** → **7** → **6** → 8, not 3→4→5→6→7→8.
**Reasoning:** total run time was budgeted against the 5–7 h window. Stage 3 alone is
45 × 180 s ≈ 137 min and Stage 5 is a fixed 60 min. The scaled-dataset arm (Stage 6) is
the only stage whose scope can be reduced without losing a headline deliverable, so it is
placed **last** — if the clock runs out, it degrades to fewer scales rather than costing
the degradation ratio or the 429 contrast. Stage 7 is cheap (~15 min) and produces a
headline result, so it precedes Stage 6 too.

### D11 — Stage 6 reduced from the full matrix
**Decision:** the scaled arm runs **1 level (knee = 8 VUs) x 2 routes x 3 repeats x 120 s**
per scale, across 4 scales (1x, 10x, 100x, 1000x) — not the full Stage 3 matrix at each
scale.
**Reasoning:** repeating Stage 3 in full at each of 4 scales would be
4 x 45 x 180 s ≈ 9 hours, which does not fit the window. The purpose of Stage 6 is the
**mean-versus-p99 divergence as dataset size grows**, and that is a comparison *across
scales at a fixed load level* — extra VU levels and routes add breadth, not evidence for
that specific claim. The knee is the level where calibration showed tail divergence is
largest, so it is the most informative single level. A 1x scale cell is included at the
same 120 s duration so all four points are directly comparable rather than being compared
against the 180 s Stage 3 runs.
**Cost:** 24 runs ≈ 50 min. **Consequence:** the scaled arm has 2 kept repeats per cell
after warm-up discard, not 4. Spread across repeats will be reported so the reader can see
how thin it is.

### D12 — Self-continuing watchdog
**Decision:** launched `chain_after_matrix.ps1`, which waits for the matrix to reach 45
rows (or to stall with no k6 process for 3 consecutive checks) and then runs
`run_remaining.ps1` automatically.
**Reasoning:** the instruction is to run unattended and never wait. Chaining the stages in
the background means the night proceeds on its own schedule rather than depending on me
being re-invoked at the right moment. The watchdog writes
`data/remaining_started.marker` so the stages cannot be started twice.

### D13 — Stage 4 did NOT reach the brief's breaking-point definition (limitation of my design)
**Result:** the stress ramp completed all seven stages without tripping either abort
threshold. Final numbers: 359,743 requests completed, **547,714 iterations dropped**,
achieved 1,698 req/s against an offered 12,000 req/s, error rate **0.593%**, zero 5xx,
zero 429, p50 **2,066 ms**, p99 2,228 ms, max 3,532 ms. Server survived. RSS grew
62.8 MB → **692.7 MB**.

**Why the 10 s threshold was never hit — and it is my harness, not the server.**
`maxVUs` was set to 4,000. In-flight requests are therefore capped at 4,000, and with
service rate pinned near 2,000 req/s Little's Law gives W = L/λ = 4000/2000 = **2.0 s**.
Observed p50 was 2,066 ms. The latency ceiling was imposed by the load generator's VU
cap, not by the application. To drive response time to 10 s the test would need roughly
20,000 in-flight requests.

**Consequence:** the "breaking point" in the brief's terms (>5% errors OR >10 s) was **not
reached**. What was measured is the saturation throughput and the failure *mode*, which is
arguably the more useful result — but the number must not be reported as a breaking point.
**Action:** a second stress run (Stage 4b) with `maxVUs=20000` is queued for after the
chain completes, to establish whether the app reaches 10 s latency, starts refusing
connections, or exhausts memory first. Not run now because the 3,600 s soak is in
progress and must not be perturbed.

### D14 — No CPU-intensive analysis during the soak
**Decision:** figure generation and any other heavy local work is deferred until the
3,600 s soak finishes.
**Reasoning:** the soak exists to detect *sustained degradation*. A matplotlib render or
a large file scan on the same machine would appear in the series as a latency excursion
and could be mistaken for the very effect being measured. Only trivial text writes happen
during the soak window.

### D15 — Soak extraction bug: gzip file read as text (FAILURE, logged)
**When:** Stage 8, extracting the soak time series.
**What happened:** when adding gzip support to `extract_k6.py` I used a `str.replace` that
did not match the call site (line-continuation whitespace differed). The script printed
"gzip support added" because `str.replace` silently no-ops on a miss, and I verified only
that the *function definition* existed — not that the **call site** used it. The extractor
opened 361 MB of gzip as UTF-8 text with `errors="replace"`, scanned 1,560,064 lines of
garbage, and found zero points.
**What saved it:** the extractor's own guard — *refuse to delete the raw file when zero
points are extracted*. The 361 MB raw file was untouched, so nothing was lost.
**Action:** replaced the call site with `open_maybe_gzip`, verified by `grep` that the call
site (not just the definition) changed, re-ran. Result: **4,221,421 requests extracted,
exactly matching the k6 summary's request count** — an independent cross-check that the
extraction is complete.
**Retry count:** 1.
**Lesson recorded:** verifying that a patch *applied* is not the same as verifying the
*call path* changed. `str.replace` failing silently is the trap.

---

# Phase 2 — paper preparation (2026-08-25)

### D16 — Arm C (variance injection) built from real routes, not a synthetic endpoint
**Decision:** the variance arm mixes two real endpoints in known proportions
(`/robots.txt` cheap, `/api/content` expensive) rather than adding a test-only route that
sleeps or burns CPU.
**Reasoning:** the overnight run left the reframed thesis — *the mean conceals variance,
not uniform slowness* — supported only inferentially. Every arm so far varied **uniform**
cost. Arm C holds the expensive work identical and varies only its **distribution**, which
is the actual condition the claim is about. Doing it by route mixing means **zero
modification to the application**, so the measured latencies are real application
behaviour rather than an artificial `sleep()`. Mixes: 100% cheap, 100% expensive, 90/10,
99/1, 99.9/0.1.
**Validated before committing:** a 15 s probe of the 99/1 mix gave mean 0.455 ms, p99
2.106 ms, **p99/mean = 4.63** against 2.22 for uniform expensive work — the predicted
direction, at a much lower mean.

### D17 — Arm E added: coordinated-omission control (found during the literature review)
**Decision:** added an open-loop arm using k6's `constant-arrival-rate` executor at three
offered rates (600 / 1100 / 1400 req/s) bracketing the closed-loop throughput.
**Reasoning:** the literature review surfaced a problem with **this study's own method**.
Stages 2, 3, 5, 6 and 7 all used `constant-vus`, a **closed model**. k6's own
documentation states that when a system "starts to respond more slowly, a closed model
load test will wait, resulting in increased iteration durations and a tapering off of the
arrival rate of new VU iterations", and that "in some testing literature, this problem is
known as *coordinated omission*." Coordinated omission biases percentiles
**optimistically** — slow periods are under-sampled because requests that would have
landed in them are never issued.

A paper whose central claim is *percentiles reveal what the mean hides* cannot leave that
unquantified: it undermines the exact statistic the argument rests on. Arm E measures the
size of the bias in this study's own numbers. Note the direction is favourable — if the
closed-loop tails are understated, the divergence findings are **conservative** — but that
has to be demonstrated, not asserted.
**Cost:** 9 runs x 120 s ≈ 20 min, chained to start when Phase 1 releases the machine.

### D18 — Citation policy: verified sources only
**Decision:** every reference in the paper must be a source I actually fetched and read.
Where a publisher blocked retrieval (ACM DL and CACM both returned HTTP 403), the
bibliographic record is cited from a verified secondary index and **no direct quotation is
attributed to it**.
**Reasoning:** an invented or misattributed citation would be a worse failure than a thin
reference list. Verified so far: Little (1961) *Operations Research* 9(3):383–387;
Dean & Barroso (2013) *CACM* 56(2):74–80; Google SRE Book ch. 4 (quotes verified);
Gil Tene's coordinated omission via a fetched technical write-up; Grafana k6 documentation
on open vs closed models (quotes verified); ISO/IEC 25010:2023 Performance Efficiency
definition (verified). ISO/IEC 25010's *Time Behaviour* sub-characteristic wording could
**not** be verified verbatim, so it is described, not quoted.

### D19 — Corrected an estimated figure in the overnight report
**Found:** the overnight report stated "~7.2 million requests across all stages". That was
an **estimate**, and it violated the run's own no-estimation rule. The true figure, summed
from every run index and summary, is **37,177,720**.
**Action:** corrected in `docs/overnight_report.md`, with the error acknowledged in place
rather than quietly overwritten. `collect_facts.py` now computes the total from run
records, and `build_paper.py` will fail the build rather than emit an estimated total.
**Lesson:** the reason the paper is generated by substitution from `facts.json` is exactly
this failure mode — a number typed by hand drifts from the data behind it.

### D20 — Arm C rewritten around what the data showed, not what the template predicted
**What happened:** the template for §5.6 was drafted expecting the p99/mean ratio to be the
headline statistic for the variance arm. The data did not support that framing: the
pure-cheap control has a *high* p99/mean ratio (4.33) purely because its mean sits at the
measurement floor and its p99 reflects timer granularity rather than work.
**Decision:** extracted the full per-request series for each mix (0.1–2.4 million requests
per workload) and rewrote the section around a **percentile ladder** instead — p50, p90,
p99, p99.9, p99.99 — which shows the effect without the floor artefact.
**What that revealed:** a sharper result than the one originally sought. A slow path is
invisible to any percentile below its own incidence. At 0.1% incidence, p99 reads
**1.506 ms — identical to a workload containing no slow path at all**. The verification
script asserts that equality literally rather than taking it on trust.
**Also recorded honestly:** part of the tail compression in the mixes is a self-queueing
effect (rare expensive requests do not queue behind each other), not dilution alone. That
caveat is stated in the section rather than omitted.

### D21 — Scaled arm repeats merged, raising n from 2 to 5
**Decision:** merged `results/scaled` with the additional repeats in
`results/scaled_extra` into `results/scaled_merged`, renumbering runs so exactly one
warm-up is discarded per cell.
**Result:** n = 5 at ×1/×10/×100 (n = 2 remains at ×1000, which runs at ~1 req/s). The
conclusions are unchanged — mean still linear in dataset size, divergence still falling —
but the cells flagged as too thin to cite in the overnight report now support citation.

### D22 — Number formatting: two regimes, after a real defect
**Defect found during review:** the first build printed "39.400 million requests" and
"52.800-fold" because the formatter forced three decimals everywhere.
**Decision:** the Arm C ladder — a millisecond table where a cell reading "2" beside
"2.580" would read as a different quantity — is forced to 3 dp. Every other value keeps the
precision it was rounded to at collection time.

### D23 — Independent verification rather than trusting the pipeline
**Decision:** `scripts/verify_paper.py` re-derives key numbers **directly from the raw run
outputs** and compares them against the paper text, rather than re-reading `facts.json`.
It also asserts the qualitative claims: that the "identical p99" statement is literally
true, that the mean dilutes faster than p99.9, that divergence falls as data grows, that
the stress failure produced zero 5xx, and that the paper reports its own
coordinated-omission limitation.
**Result: 29/29 checks pass.** A failure would exit non-zero, so the check is meaningful
rather than decorative.
