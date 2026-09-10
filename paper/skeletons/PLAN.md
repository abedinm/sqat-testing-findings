# Rewrite plan — meeting requirement 3

**Target: 4,800 of the paper's 5,998 prose words written by you.**

Every other requirement already passes, verified against the current PDF. This is the only
one left, and it is the only one I cannot do for you: anything I draft counts as the thing
being measured.

## Order of work

Do them in this order. It is not the order they appear in the paper — it starts with what
you can write fastest and ends with what needs the rest to exist first.

| # | Section | Words | Sheet | Why here |
|---|---|---:|---|---|
| 1 | §3 System Under Test | 204 | `QUESTIONS-03-...` | Your own app. Pure description. Warm-up. |
| 2 | §4 Methodology | 452 | `QUESTIONS-04-...` | What you did. No argument to make. |
| 3 | §5 Results | 2,459 | `QUESTIONS-05-...` | 41% of the paper. Ten sittings, one subsection each. |
| 4 | §7 Threats | 338 | `QUESTIONS-07-...` | Honesty, not analysis. Fast. |
| 5 | §6 Discussion | 421 | `QUESTIONS-06-...` | Interpretation. Needs §5 done. |
| 6 | §8 Conclusion | 262 | `QUESTIONS-08-...` | Compresses §5 and §6. |
| 7 | §1 Introduction | 549 | `QUESTIONS-01-...` | Easier once you know what you found. |
| 8 | §2 Background | 470 | `QUESTIONS-02-...` | Needs 40 min of abstract-reading first. |
| 9 | Abstract | 331 | `QUESTIONS-00-...` | Last. It is §8 compressed. |

Running total after §5: **3,115 words, 52%.** After §7 and §6: **3,874, 65%.**
After §8 and §1: **4,685, 78%.** Finish §2 and the abstract and you are at **5,486, 91%.**

You can stop after step 7 and be at 78%, which clears the threshold with room. §2 and the
abstract are the last two because they are the hardest and the least necessary.

## Method

1. Open the sheet. Open the PDF **to the tables and figures only**. Keep `paper.md` closed.
2. Answer the questions out loud, as if explaining to a classmate who missed the lecture.
3. Type what you said. Fix the grammar. Do not make it sound more academic — the structure
   and the numbers already carry the formality.
4. Paste into `paper/paper_template.md`, replacing that section. Leave every
   `{{placeholder}}`, `[[FIGURE:...]]`, `[[TABLE:...]]` and `[n]` marker exactly as it is.
5. Rebuild and check:

```
python scripts/build_paper.py
python scripts/verify_paper.py
python scripts/verify_all_numbers.py
```

`build_paper.py` fails loudly if you break a placeholder, so you cannot silently damage a
number.

6. Send me the section. I check it against `facts.json` for anything that contradicts the
   data and hand it straight back. I do not touch your sentences.

## Why tables and figures are safe to read

They were generated from your run outputs by `make_figures.py` and `make_docx.py`. They are
data, not written prose. Reading them while you write is not copying and is not what a
detector scores. That is what makes §5 tractable: you are not inventing 2,459 words, you are
explaining numbers that are already in front of you.

## Final build when everything is rewritten

```
python scripts/build_paper.py
python scripts/make_docx.py
python scripts/verify_paper.py
python scripts/verify_all_numbers.py
```

Then export the PDF and confirm the filename still matches the title exactly.

macOS, if you are on the MacBook:

```
soffice --headless --convert-to pdf paper/paper.docx
```

## What not to lose while rewriting

- Every `{{placeholder}}` — the build fails if one goes missing, which is the point.
- Every `[n]` citation marker — they are in first-appearance order and renumbering is
  automatic only if you leave them alone.
- The `[[FIGURE:...]]` and `[[TABLE:...]]` markers, each on **one line**. A marker wrapped
  across two lines silently drops a table; `make_docx.py` now aborts if that happens.
- The two verbatim quotation blocks in §1 and §2, and the one in §6.1. Those are real
  quotations from real sources. Rewriting a quotation falsifies it.
