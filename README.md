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
