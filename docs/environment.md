# Test environment

Captured **2026-08-24**, at the start of the unattended run. Every value below was read
from the machine by the command shown — none is estimated.

---

## 1. Host

| | |
|---|---|
| OS | Microsoft Windows 11 Pro, 25H2, build **26200.9168** |
| CPU | **Intel Core i7-10700**, 8 cores / 16 threads, base 2.90 GHz (turbo 4.80 GHz, vendor spec) |
| RAM | **32 GB** (31.91 GB usable), DDR4 **2933 MT/s**, dual channel (`ChannelA-DIMM2` + `ChannelB-DIMM2`) |
| Free RAM at capture | 13.25 GB |
| Disk (C:) | 19 GB free — see §6, this constrains raw-output retention |
| Power plan at capture | **Balanced** — see threat T4 |

```powershell
Get-CimInstance Win32_Processor, Win32_ComputerSystem, Win32_OperatingSystem
Get-CimInstance Win32_PhysicalMemory ; powercfg /getactivescheme
```

## 2. System under test

| | |
|---|---|
| Application | Deltadesh corporate website |
| Location | `C:\Users\USER\perf-web\sut\` (a **copy**; see §5) |
| Runtime | **Node.js v24.15.0** (npm 11.12.1) |
| Server | `serve.mjs`, 982 lines, hand-rolled `node:http`. **No framework. Zero runtime dependencies.** |
| Process model | **Single process, single-threaded event loop.** No cluster, no worker threads |
| Listening on | `http://127.0.0.1:8099` (`PORT=8099`) |
| Start command | `PORT=8099 node serve.mjs` (working dir `perf-web/sut`) |

### Database

**None.** There is no database of any kind. The datastore is one JSON file:

| | |
|---|---|
| File | `sut/data/content.json` |
| Size | **88,826 bytes** |
| Records | **188** array items across 11 top-level keys |
| Access pattern | `JSON.parse(await readFile(...))` — **no caching**, executed per request |

Record counts per key (the "rows per table" equivalent):

| Key | Records |
|---|---|
| clients | 70 |
| people | 41 |
| projects | 38 |
| services | 12 |
| sectors | 6 |
| gallery | 6 |
| insights | 5 |
| testimonials_unverified | 4 |
| awards_unverified | 4 |
| news | 2 |
| company | object (9 keys) |

`.env.example` references PostgreSQL/Supabase, but `serve.mjs` imports no database client
and opens no connection. That is groundwork for a future migration, not the running system.
**No DB version to report, because there is no DB.**

Static assets: 38 MB across 253 image files, served with
`Cache-Control: public, max-age=31536000, immutable`. HTML/CSS/JS are served `no-cache` by
deliberate choice in the source.

## 3. Load generator

| | |
|---|---|
| Tool | **k6 v2.2.0** (commit `00a9a1b7f5`, go1.26.5, windows/amd64) |
| Install | Downloaded from `grafana/k6` GitHub release, extracted to `perf-web/tools/`. No system install, no admin |
| Target | `127.0.0.1` only, hard-coded default in every script |
| Analysis | Python 3.13.13 with pandas 3.0.3, numpy 2.4.5, matplotlib 3.10.9, scipy 1.17.1 |

## 4. Threats to validity

**T1 — SUT and load generator share one machine (the big one).**
k6 and Node run on the same 8-core host. They compete for CPU, and k6 is itself
CPU-hungry at high VU counts. Consequences:

- Measured response times include **no network latency at all**. Absolute numbers are not
  comparable to any real deployment; only *relative* behaviour across load levels and
  dataset scales is meaningful. That relative framing is what this study argues about, so
  the design survives, but every absolute figure must be read as a lower bound.
- At high VU counts, some observed latency will be **k6 waiting for CPU**, not the server
  being slow. This is the most likely source of a false "knee". Mitigation: watch whether
  Node's own CPU saturates (single core ~100%) before the knee appears; if the knee arrives
  while Node is well under saturation, suspect the generator.
- There is no way to eliminate this without a second machine. It is recorded, not solved.

**T2 — Node is single-threaded; the host has 16 logical processors.**
The SUT can use at most ~1 core for JavaScript. The remaining 15 are available to k6, so
the generator will not starve — but it also means the server saturates long before the
machine does. Host-level CPU will look idle at the moment the SUT is fully saturated.
Reading host CPU as "spare capacity" would be wrong.

**T3 — No client caching.**
k6 does not implement a browser cache, and the app sends `no-cache` for HTML/CSS/JS
anyway. Every request pays full cost. Real browser traffic would be cheaper. Results are
pessimistic relative to real users, which is the safe direction for this study.

**T4 — Power plan is Balanced, not High Performance.**
Recorded as found. Under Balanced, CPU frequency scaling may add variance between runs.
Not changed, because changing it mid-study would make later runs incomparable with the
smoke run already collected, and because the study's claims are about *relative*
percentile behaviour rather than absolute throughput. Flagged as a real source of
run-to-run variance.

**T5 — A service worker (`sw.js`) exists in the app.**
Irrelevant to k6 (no browser involved) but it means browser-observed behaviour will differ
from what is measured here.

**T6 — Rate limiter is per-IP and all load originates from 127.0.0.1.**
Every virtual user shares one bucket. This is the subject of Arm B rather than a defect,
but it makes several routes untestable in Arm A. See `sut.md` §6.

## 5. Isolation from the live site

The original at `C:\Users\USER\Documents\deltadesh-website-render` is the deploy source for
the live client site (`deltadesh.com`, Render/Frankfurt, git remote
`abedinm/deltadesh-website`).

- The SUT here is a **copy** made with `robocopy /E`, **excluding `.git`**, so the copy has
  no git remote and cannot push anywhere.
- 335 files, 39.1 MB copied.
- The original is treated as read-only for the entire study. Only `git status` (read-only)
  is run against it, and only to verify it stayed clean.
- All synthetic dataset generation happens in `perf-web/sut/` only.

## 6. Raw-output handling

k6's `--out json` emits ~17 metric points per request. The 30-second single-VU smoke run
produced **116.8 MB across 515,467 lines** for 30,317 requests. The full matrix would run
to tens of gigabytes against 19 GB of free space on C:.

`scripts/extract_k6.py` reduces raw output to the measurement this study is about —
one row per request, `ts_iso, elapsed_s, duration_ms, status, expected_response` — with
**no aggregation, rounding or sampling**. Measured on the smoke run: 116.8 MB → 1.74 MB
(1.5%), 30,317 of 30,317 requests preserved.

Raw JSON is deleted only *after* a successful extraction; the extractor refuses to delete
if it found zero points. Every retained per-request series lives in
`results/<label>/requests.csv`.
