#!/usr/bin/env python3
"""
add_refs.py - strengthen the reference base and renumber in IEEE first-citation order.

Adds five verified sources at points where they actually support a claim, replaces the
weak secondary-source citation of Tene's talk with the talk itself, then renumbers every
citation by order of first appearance and rewrites the reference list to match.

Every added source was checked against its publisher or the conference proceedings before
being cited. Nothing here is cited from memory.
"""

import os
import re
import sys
import textwrap

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = os.path.join(ROOT, "paper", "paper_template.md")
text = open(P, encoding="utf-8").read()
before = text
failed = []


def edit(old, new):
    global text
    pat = re.compile(r"\s+".join(re.escape(w).replace(r"\-", r"\-\s*") for w in old.split()))
    if len(pat.findall(text)) != 1:
        failed.append(old[:70])
        return
    text = pat.sub(lambda m: textwrap.fill(" ".join(new.split()), width=90), text, count=1)


# ---- placeholders for the new keys; renumbered at the end -------------------
SCHROEDER, HOEFLER, GEORGES, MYTKOWICZ, ISO25023 = "[@S]", "[@H]", "[@G]", "[@M]", "[@I]"

# 1. ISO/IEC 25023 defines mean response time as a measure. This restores the claim
#    removed during the 25010 fix, now attributed to the standard that actually makes it.
edit('and places response time under its *time behaviour* sub-characteristic. Mean '
     'response time is the measure conventionally reported against it.',
     'and places response time under its *time behaviour* sub-characteristic. The companion '
     f'measurement standard ISO/IEC 25023 {ISO25023} defines mean response time as a '
     'quality measure against that sub-characteristic.')

edit('Where mean response time is the measure reported against that sub-characteristic, '
     'the question this paper asks is what the measure fails to express.',
     f'ISO/IEC 25023 {ISO25023} defines mean response time as a measure against that '
     'sub-characteristic. The question this paper asks is what that measure fails to '
     'express.')

# 2. Schroeder et al. is the primary experimental result on open vs closed models.
edit('This study measures its magnitude in its own data rather than assuming it away '
     '(§5.8).',
     f'Schroeder, Wierman and Harchol-Balter {SCHROEDER} establish the same point '
     'experimentally, showing that open and closed workload models produce substantially '
     'different behaviour in real systems and that the choice between them changes the '
     'conclusions a study reaches. This paper measures the magnitude of the bias in its own '
     'data rather than assuming it away (§5.8).')

# 3. Reporting practice: effect size alongside significance.
edit('Effect size (rank-biserial r) is reported alongside p, because at the sample sizes '
     'involved (millions of requests) statistical significance is uninformative, a point '
     'demonstrated concretely in §5.4.',
     'Effect size (rank-biserial r) is reported alongside p, because at the sample sizes '
     'involved (millions of requests) statistical significance is uninformative, a point '
     f'demonstrated concretely in §5.4. This follows the practice argued for by Georges et '
     f'al. {GEORGES} for performance evaluation and by Hoefler and Belli {HOEFLER} for '
     'benchmarking generally; both surveys find that systems papers routinely report '
     'results without the statistical basis needed to interpret them.')

# 4. Measurement bias, in Threats to Validity.
edit('Background load and power configuration. The host ran a standard desktop software '
     'environment on a balanced power profile, adding variance not quantified here. '
     'Conditions were identical across arms.',
     'Background load and power configuration. The host ran a standard desktop software '
     'environment on a balanced power profile, adding variance not quantified here. '
     'Conditions were identical across arms. Mytkowicz et al. '
     f'{MYTKOWICZ} show that incidental features of an experimental setup can bias systems '
     'measurements enough to reverse a conclusion, so identical conditions across arms '
     'bound the risk of a differential effect without eliminating a common one.')

# ---- reference list ---------------------------------------------------------
NEW_ENTRIES = {
    SCHROEDER: ('B. Schroeder, A. Wierman, and M. Harchol-Balter, "Open versus closed: a '
                'cautionary tale," in *Proc. 3rd USENIX Symp. Networked Systems Design and '
                'Implementation (NSDI \'06)*, San Jose, CA, May 2006. [Online]. Available: '
                'https://www.usenix.org/legacy/event/nsdi06/tech/full_papers/schroeder/schroeder.pdf'),
    HOEFLER:   ('T. Hoefler and R. Belli, "Scientific benchmarking of parallel computing '
                'systems: twelve ways to tell the masses when reporting performance '
                'results," in *Proc. Int. Conf. High Performance Computing, Networking, '
                'Storage and Analysis (SC \'15)*, Austin, TX, Nov. 2015, art. 73, pp. 1-12. '
                'doi: 10.1145/2807591.2807644.'),
    GEORGES:   ('A. Georges, D. Buytaert, and L. Eeckhout, "Statistically rigorous Java '
                'performance evaluation," in *Proc. 22nd ACM SIGPLAN Conf. Object-Oriented '
                'Programming Systems, Languages and Applications (OOPSLA \'07)*, Montreal, '
                'QC, Oct. 2007, pp. 57-76. doi: 10.1145/1297027.1297033.'),
    MYTKOWICZ: ('T. Mytkowicz, A. Diwan, M. Hauswirth, and P. F. Sweeney, "Producing wrong '
                'data without doing anything obviously wrong!," in *Proc. 14th Int. Conf. '
                'Architectural Support for Programming Languages and Operating Systems '
                '(ASPLOS \'09)*, Washington, DC, Mar. 2009, pp. 265-276. '
                'doi: 10.1145/1508284.1508275.'),
    ISO25023:  ('ISO/IEC 25023:2016, *Systems and software engineering, Systems and software '
                'Quality Requirements and Evaluation (SQuaRE), Measurement of system and '
                'software product quality*. International Organization for Standardization, '
                '2016.'),
}

# Tene: cite the talk itself rather than a blog summary of it.
edit('[3] G. Tene, "How NOT to measure latency," conference presentation. Cited here via '
     'the secondary account in T. Treat, "Everything you know about latency is wrong." '
     '[Online]. Available: '
     'https://bravenewgeek.com/everything-you-know-about-latency-is-wrong/',
     '[3] G. Tene, "How NOT to measure latency," presented at QCon San Francisco, San '
     'Francisco, CA, Nov. 2015. [Online]. Available: '
     'https://www.infoq.com/presentations/latency-response-time/')

if failed:
    print("DID NOT MATCH:", file=sys.stderr)
    for f in failed:
        print("  " + f, file=sys.stderr)
    sys.exit(1)

# ---- collect existing entries, append new ones, renumber by first appearance -
body, sep, reflist = text.partition("## References")
old_entries = dict(re.findall(r"^\[(\d+)\]\s(.+?)(?=\n\[\d+\]|\n---|\Z)", reflist,
                              re.S | re.M))
old_entries = {f"[{k}]": " ".join(v.split()) for k, v in old_entries.items()}
entries = {**old_entries, **NEW_ENTRIES}

order, seen = [], set()
for m in re.finditer(r"\[(?:\d+|@[A-Z])\]", body):
    k = m.group(0)
    if k not in seen:
        seen.add(k)
        order.append(k)

missing = [k for k in order if k not in entries]
if missing:
    sys.exit(f"ABORT: cited but no entry: {missing}")
uncited = [k for k in entries if k not in seen]
if uncited:
    sys.exit(f"ABORT: entry never cited: {uncited}")

mapping = {old: f"[{i}]" for i, old in enumerate(order, 1)}
body = re.sub(r"\[(?:\d+|@[A-Z])\]", lambda m: mapping[m.group(0)], body)

lines = ["## References", ""]
for old in order:
    lines.append(textwrap.fill(f"{mapping[old]} {entries[old]}", width=90,
                               subsequent_indent=""))
    lines.append("")
tail = reflist.split("---", 1)
lines.append("---" + (tail[1] if len(tail) > 1 else ""))
text = body + "\n".join(lines)

for name, pat in (("placeholders", r"\{\{[a-zA-Z0-9_]+\}\}"), ("figures", r"\[\[FIGURE:"),
                  ("tables", r"\[\[TABLE:"), ("rows", r"(?m)^\|")):
    a, b = len(re.findall(pat, before)), len(re.findall(pat, text))
    if a != b:
        sys.exit(f"ABORT: {name} {a} -> {b}")
    print(f"  OK {name:14} {a}")

open(P, "w", encoding="utf-8", newline="\n").write(text)
print(f"\nreferences: {len(old_entries)} -> {len(entries)}, renumbered in citation order")
print("  order:", " ".join(mapping[o] for o in order))
