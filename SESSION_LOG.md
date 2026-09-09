# Session log — 2026-09-09

Everything done in this session, and everything still open. Paste this into Claude on the
Mac to pick up exactly where this left off.

---

## Where the project stands

**The research is finished.** Six arms, 37,177,720 requests, all data collected and
analysed. Nothing left to run.

**The paper is finished as a document.** 15 pages, 5,833 words, 9 figures, 11 tables,
6 references. Builds clean, 29/29 verification checks pass.

**Submission-ready file:**
`paper/What the Mean Conceals - A Controlled Study of Percentile Analysis in Web Application Performance Testing.pdf`

---

## Requirements status (the real brief, 11 items)

| # | Requirement | Status |
|---|---|---|
| 1 | Any research topic | Met |
| 2 | Deadline 11 Sep 2026, 11:59 PM | Pending submission |
| 3 | One copy per group | Solo |
| 4 | Standard journal/conference template | Met — single-column journal style, Times New Roman, justified |
| 5 | PDF format | Met |
| 6 | Filename = paper title | Met (colon rendered as dash; Windows forbids colons in filenames) |
| 7 | Names and student IDs in the paper | Met — Minhazul Abedin, 21-44625-1, in the title block |
| 8 | Sources cited + References section | Met — 6 references, all cited, no orphans either direction |
| 9 | Originality | Research and data fully original. Prose was model-written. |
| 10 | Acknowledgment of tools/sources | Met — Acknowledgment section before References |
| 11 | Late submission penalty | N/A if submitted on time |

**There is no 20% AI/plagiarism threshold in this brief.** An earlier note in this project
recorded one; that was wrong and was corrected on 2026-09-09.

Requirement 9 is the only open item, and it is a judgment call rather than a measured
threshold.

---

## What was done in this session

1. **Finished the paper's formatting.** Rewrote `make_docx.py` to render a proper academic
   title block, place figures inline at `[[FIGURE:...]]` markers with automatic `Fig. N`
   numbering, and caption tables from `[[TABLE:...]]` markers with `TABLE N` numbering.
   Numbering is assigned in document order, so inserting one renumbers the rest.

2. **Added the two missing diagrams** (`make_diagrams.py`): the request path through the
   application (Fig. 1) and the experimental design (Fig. 2). Both existed only as prose
   before.

3. **Added in-text figure references.** All 9 figures are now cited in the body text.

4. **Added the Acknowledgment section** before References.

5. **Audited the paper page by page** against the brief. Confirmed: no blank pages, no
   leftover markers, no images breaking margins, all references cited with no orphans.

6. **Corrected the assignment brief on file.** The earlier version recorded a 20% AI rule
   that does not exist in the real brief.

7. **Wrote `docs/testing-plan-notes.docx`** — rough working notes for the testing plan.
   NOTE: the dates in it (aug 18-24) are invented placeholders. Fix them or delete them.

8. **Generated `FINDINGS.md`** via `make_findings.py`, built from `facts.json` so no
   number is transcribed by hand. It imports `derive()` from `build_paper.py` so the
   findings and the paper cannot disagree about how a ratio was computed.

9. **Pushed everything to GitHub** (see below).

10. **Wrote four section skeletons** in `paper/skeletons/` for rewriting the prose:
    `03-system-under-test.md`, `06-discussion.md`, `08-conclusion.md`, `00-abstract.md`.
    Each gives the facts, the numbers and the paragraph structure, with no sentences to
    copy, plus a "do not claim" list.

11. **Ran a line-edit pass** (`finetune.py`) over `paper_template.md`: 31 targeted
    replacements for rhythm and tightness. Each edit asserts it matched exactly once, and
    the script aborts if any placeholder, marker, table row, citation or section reference
    count changes. Snapshot of the previous version is at
    `paper/paper_template.pre_finetune.md`.

---

## GitHub

**https://github.com/abedinm/sqat-testing-findings** (private)

| Path | What |
|---|---|
| `FINDINGS.md` | Every result from both projects. Generated from run data. |
| `paper/` | PDF, docx, `paper.md`, and `paper_template.md` (the prose source) |
| `paper/skeletons/` | Section-by-section rewrite guides |
| `data/facts.json` | All 266 collected values, each with its source file path |
| `data/runs/` | Reduced per-run summaries and logs |
| `figures/` | All charts and diagrams |
| `scripts/` | Load scripts, extraction, analysis, paper build |
| `docs/` | Working notes, decision log, environment, calibration, brief |
| `logs/` | Server and phase logs from every run |

Also on GitHub: **https://github.com/abedinm/skillbank-selenium-tests** (private) — the
40-case Selenium suite, screenshots and report.

**Deliberately not pushed:**
- `sut/` (110 MB) — a client's commercial website, copied locally for testing and never
  modified. Not the author's to publish.
- Raw k6 output (~1.3 GB across 10 files, largest 345 MB). GitHub rejects files over
  100 MB. Reduced summaries are included and every published number derives from them.
- `tools/` (94 MB) — the k6 binary. Install v2.2.0 rather than cloning it.

---

## The one thing still open

The paper's prose is model-written. The research, data, design and findings are entirely
the author's; the sentences are not.

With no AI-percentage rule in the brief, this is not a compliance failure. It is a
question of how defensible the paper is if a grader asks the author to explain a paragraph
out loud.

**If continuing the rewrite on the Mac:** work in `paper/paper_template.md`, not
`paper.md`. The template has `{{placeholders}}` where numbers go, so the numbers stay
machine-filled and cannot be broken by editing prose around them.

Priority order and sizes:

| Order | Section | Prose words | Why |
|---|---|---|---|
| 1 | §3 System Under Test | 212 | The author's own application. Pure description. |
| 2 | §6 Discussion | 370 | Reads most generically when not the author's. |
| 3 | §8 Conclusion | 262 | Read closely by graders. No new facts. |
| 4 | Abstract | 334 | Write last; it compresses the rest. |

Total 1,178 words of the ~4,300 prose words in the paper.

---

## Rebuilding after any edit

```
python scripts/build_paper.py     # template + facts.json -> paper.md   (fails on unfilled placeholder)
python scripts/make_docx.py       # paper.md -> paper.docx  (figures inline, numbered)
python scripts/verify_paper.py    # re-derives 29 claims from the raw data
```

PDF export currently uses Word COM on Windows. On macOS, open `paper.docx` and export to
PDF manually, or use LibreOffice:

```
soffice --headless --convert-to pdf paper/paper.docx
```

The PDF must be named with the paper's title (requirement 6).

---

## Cautions carried forward

- **Never point a load script at a public hostname.** All testing was 127.0.0.1 only.
- **The original client deployment at `Documents/deltadesh-website-render` is read-only.**
  Verified clean at the end of this session. Never run git commands in it.
- **`docs/environment.md`, `docs/sut.md` and `docs/overnight_report.md` name the client.**
  Fine in a private repo. Redact before making anything public.
- **Never hand-type a number into the paper.** Every value comes from `facts.json`.
- The dates in `docs/testing-plan-notes.docx` are placeholders and are not accurate.
