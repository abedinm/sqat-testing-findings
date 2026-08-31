# SQAT Final Term — Testing Data & Findings

Minhazul Abedin · 21-44625-1 · AIUB

**→ [FINDINGS.md](FINDINGS.md) — every result from both pieces of testing work.**

Two projects:

1. **Web application performance study** — controlled experiment on whether mean
   response time conceals tail-latency failures. Six arms, 37M+ requests, k6.
2. **Selenium functional test suite** — 40 automated cases against a PHP/MySQL
   web app. Suite itself lives at `abedinm/skillbank-selenium-tests`.

## Layout

| Path | What |
|---|---|
| `FINDINGS.md` | All results. Start here. |
| `paper/` | The paper (PDF + markdown source) |
| `data/facts.json` | Every collected value, each with its source file path |
| `data/runs/` | Reduced per-run summaries and logs |
| `figures/` | All charts and diagrams |
| `scripts/` | Load scripts, extraction, analysis, paper build |
| `docs/` | Working notes, decision log, environment, calibration |

## Not here

- **The application under test.** A client's commercial website, copied locally for
  testing and never modified. Not mine to publish.
- **Raw k6 output** (~1.3 GB). Reduced summaries are included.

All load testing ran against `127.0.0.1` only. No deployed site was ever a target.

## PRIVATE

`docs/environment.md`, `docs/sut.md` and `docs/overnight_report.md` name the client.
Redact those before this repo is ever made public.

## Raw k6 output — not in this repo

About 1.3 GB across 10 files, the largest 345 MB. GitHub rejects any file over
100 MB, and putting this in git history would make the repo unclonable.

Every published number derives from the reduced data that *is* here
(`data/runs/*/summary.json`, `metrics.json`, `aggregate.json`). The raw files are the
original per-request measurements and stay on the machine that produced them.

| File | Size |
|---|---|
| `results/soak/raw.json.gz` | 345 MB |
| `results/soak/requests.csv` | 252 MB |
| `results/mixed/uniform_cheap_run2/requests.csv` | 137 MB |
| `results/mixed/mix_0p1pct_run2/requests.csv` | 126 MB |
| `results/mixed/mix_1pct_run2/requests.csv` | 109 MB |
| + 5 more | ~310 MB |

## Load generator

k6 v2.2.0 (windows-amd64), downloaded from grafana/k6 releases. The binary is not
committed — install it rather than cloning 94 MB of it.
