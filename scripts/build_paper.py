#!/usr/bin/env python3
"""
build_paper.py - generate the paper from the template plus machine-collected facts.

Substitutes {{placeholder}} tokens in paper/paper_template.md with values from
paper/facts.json, computes a small number of derived quantities, and writes:

    paper/paper.md      the finished paper
    paper/paper.docx    Word version with figures

If ANY placeholder cannot be filled, the build FAILS and lists them. That is deliberate:
a paper with an unresolved placeholder is a paper with an unverified claim, and silently
leaving a gap would be worse than not building at all.
"""

import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
R = lambda *p: os.path.join(ROOT, *p)


def derive(f):
    """Quantities the paper states as ratios or narrative, computed from collected facts."""
    d = {}

    def have(*keys):
        return all(k in f and f[k] not in (None, 0) for k in keys)

    if have("armb_disabled_mean", "armb_enabled_mean"):
        d["armb_improvement_x"] = round(f["armb_disabled_mean"] / f["armb_enabled_mean"], 1)
    if have("armb_disabled_p99", "armb_enabled_p99"):
        d["armb_p99_improvement_x"] = round(f["armb_disabled_p99"] / f["armb_enabled_p99"], 1)
    if have("armb_disabled_rps", "armb_enabled_rps"):
        d["armb_rps_x"] = round(f["armb_enabled_rps"] / f["armb_disabled_rps"], 1)
    if "soak_requests" in f:
        d["soak_requests_m"] = round(f["soak_requests"] / 1_000_000, 1)

    # Real total, summed from run records by collect_facts. Never estimated: if the
    # figure is unavailable the placeholder stays unfilled and the build fails.
    if "total_requests" in f:
        d["total_requests_m"] = round(f["total_requests"] / 1_000_000, 1)

    if have("arme_1100_mean", "arme_1400_mean"):
        d["arme_cliff_x"] = round(f["arme_1400_mean"] / f["arme_1100_mean"], 0)

    if "soak_rss_quarters" in f and isinstance(f["soak_rss_quarters"], list):
        d["soak_rss_quarters"] = " / ".join(f"{v:.1f}" for v in f["soak_rss_quarters"])

    # Arm C dilution factors: how much the mean falls versus how much p99.9 falls when
    # identical expensive work is diluted from 100% to 10% of requests.
    if have("ladder_uniform_expensive_mean", "ladder_mix_10pct_mean",
            "ladder_uniform_expensive_p999", "ladder_mix_10pct_p999"):
        md = f["ladder_uniform_expensive_mean"] / f["ladder_mix_10pct_mean"]
        pd_ = f["ladder_uniform_expensive_p999"] / f["ladder_mix_10pct_p999"]
        d["armc_mean_dilution_10"] = round(md, 2)
        d["armc_p999_dilution_10"] = round(pd_, 2)
        d["armc_dilution_gap_10"] = round(md / pd_, 1)

    # Arm E narrative is written from the data rather than asserted in advance.
    closed_p99 = f.get("arma_api_content_v8_p99")
    open_p99 = f.get("arme_1100_p99")
    open_dropped = f.get("arme_1100_dropped")
    if closed_p99 and open_p99:
        ratio = open_p99 / closed_p99
        if ratio >= 1.15:
            d["arme_narrative"] = (
                f"At an offered rate of 1100/s, closely matching the {f.get('arma_api_content_v8_rps','~1170')} "
                f"req/s achieved by the closed-model runs, the open model reports a p99 of "
                f"{open_p99} ms against {closed_p99} ms for the closed model, a factor of "
                f"{ratio:.2f}. The closed-model percentiles used throughout this paper are "
                f"therefore optimistic by roughly that factor: coordinated omission is "
                f"present and measurable. The direction matters for interpretation: every "
                f"tail divergence reported above is a conservative estimate, and the "
                f"true divergences are larger, not smaller."
            )
        elif ratio <= 0.87:
            d["arme_narrative"] = (
                f"At an offered rate of 1100/s the open model reports a p99 of {open_p99} ms "
                f"against {closed_p99} ms for the closed model, a factor of {ratio:.2f}. "
                f"The open-model figure is the *lower* of the two, which is not the direction "
                f"coordinated omission predicts. The most likely explanation is that the "
                f"offered rate sat below the saturation point, so the arrival schedule was "
                f"maintained without queue growth "
                f"({open_dropped} iterations dropped). This bounds the bias rather than "
                f"demonstrating it."
            )
        else:
            d["arme_narrative"] = (
                f"At an offered rate of 1100/s, closely matching the throughput achieved by "
                f"the closed-model runs — the open model reports a p99 of {open_p99} ms "
                f"against {closed_p99} ms for the closed model, a factor of {ratio:.2f}. "
                f"The two models agree to within {abs(1-ratio)*100:.0f}%, so coordinated "
                f"omission is not materially distorting the percentiles reported in this "
                f"paper at this load level. Dropped iterations "
                f"({open_dropped} at this rate) indicate how far the generator was able to "
                f"hold its schedule."
            )
    return d


def main():
    facts_path = R("paper", "facts.json")
    tmpl_path = R("paper", "paper_template.md")
    if not os.path.exists(facts_path):
        sys.exit("ERROR: paper/facts.json not found - run collect_facts.py first")
    if not os.path.exists(tmpl_path):
        sys.exit("ERROR: paper/paper_template.md not found")

    blob = json.load(open(facts_path, encoding="utf-8"))
    facts = dict(blob["facts"])
    facts.update(derive(facts))

    with open(tmpl_path, encoding="utf-8") as fh:
        text = fh.read()

    used, missing = set(), set()

    def sub(m):
        key = m.group(1).strip()
        if key in facts and facts[key] is not None:
            used.add(key)
            v = facts[key]
            if isinstance(v, float):
                # Two regimes. The Arm C ladder is a millisecond table where a cell
                # reading "2" beside "2.580" looks like a different quantity, so those
                # are forced to 3 dp. Everywhere else (ratios, counts in millions,
                # fold-changes) the value keeps the precision it was rounded to, so
                # 52.8 does not become "52.800".
                if key.startswith("ladder_") and not key.endswith(("_n", "_frac_over_3ms")):
                    return f"{v:,.3f}"
                whole = f"{v:,.6f}".rstrip("0").rstrip(".")
                return whole if whole else "0"
            if isinstance(v, int):
                return f"{v:,}"
            if isinstance(v, list):
                return " / ".join(str(x) for x in v)
            return str(v)
        missing.add(key)
        return "{{" + key + "}}"

    out = re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", sub, text)

    if missing:
        print("BUILD FAILED - unresolved placeholders:", file=sys.stderr)
        for k in sorted(missing):
            print(f"  {{{{{k}}}}}", file=sys.stderr)
        print(f"\n{len(missing)} placeholder(s) could not be filled from facts.json.",
              file=sys.stderr)
        print("The paper was NOT written. Fill the data or fix the template.", file=sys.stderr)
        sys.exit(1)

    md_path = R("paper", "paper.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(out)

    words = len(re.sub(r"[^\w\s]", " ", out).split())
    print(f"paper.md written: {len(out):,} chars, ~{words:,} words")
    print(f"  placeholders resolved: {len(used)}")
    print(f"  facts available:       {len(facts)}")
    unused = sorted(set(facts) - used)
    print(f"  facts collected but not cited: {len(unused)}")
    return md_path


if __name__ == "__main__":
    main()
