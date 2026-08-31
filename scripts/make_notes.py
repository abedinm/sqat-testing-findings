#!/usr/bin/env python3
"""make_notes.py - the rough working notes for the testing plan, as a docx."""

import os
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.shared import Pt, RGBColor, Inches

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
doc = Document()
s = doc.sections[0]
s.top_margin = s.bottom_margin = Inches(0.8)
s.left_margin = s.right_margin = Inches(0.9)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(11)

RED = RGBColor(0xC0, 0x30, 0x20)
GREY = RGBColor(0x70, 0x70, 0x70)


def p(text="", size=11, bold=False, strike=False, hl=False, indent=0.0,
      color=None, italic=False, space=3):
    par = doc.add_paragraph()
    par.paragraph_format.space_after = Pt(space)
    par.paragraph_format.space_before = Pt(0)
    if indent:
        par.paragraph_format.left_indent = Inches(indent)
    r = par.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.strike = strike
    if hl:
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    if color is not None:
        r.font.color.rgb = color
    return par


def rule():
    p("-" * 62, size=9, color=GREY, space=8)


p("testing plan - rough notes", size=15, bold=True, space=1)
p("(SQAT final assignment. perf testing thing)", size=10, italic=True, color=GREY, space=10)

p("aug 18 ish", size=12, bold=True, space=4)
p("the idea:")
p("everyone reports AVERAGE response time. dashboards, SLA reports, all of it.", indent=0.25)
p("but the average hides the slow ones. if 1 request in 100 takes 2 seconds and the rest", indent=0.25)
p("take 5ms, the average still looks totally fine. the user who waited 2s does not care", indent=0.25)
p("about the average.", indent=0.25)
p("-> can I actually PROVE this with real measurements instead of just claiming it", indent=0.25, bold=True)
p()
p("thats the paper. percentiles vs mean. show the mean lying.")
p()

p("what do I test it ON?", size=12, bold=True, space=4)
p("the SkillBank php app", indent=0.25, strike=True)
p("already used it for the selenium assignment. want something different", indent=0.45, size=10, color=GREY)
p("upwork assistant", indent=0.25, strike=True)
p("no http server, its just a local script. nothing to load test", indent=0.45, size=10, color=GREY)
p("the deltadesh site -> YES. node.js, real client site, I built it myself", indent=0.25)
p()
p("BUT!! do not touch the live one. copy it. local only.", hl=True, indent=0.25)
p("127.0.0.1 ONLY. never point a load generator at a deployed site.", indent=0.25)
p("(put this in the paper too, under ethics or wherever it goes)", indent=0.25, size=10, color=GREY)
p()
rule()

p("aug 19-20", size=12, bold=True, space=4)
p("tools. what do I use to generate load")
p("- JMeter -> java, gui, heavy. everyone uses it but the output is a pain to parse")
p("- Locust -> python, would be easy for me, but not great at high rates on one box")
p("- k6 -> js scripts, json output per request, made for exactly this")
p("   picking k6. json output means I can do my own stats in pandas instead of", indent=0.2)
p("   trusting whatever the tool decides to show me", indent=0.2)
p()
p("^ this matters more than I first thought. most tools just PRINT the average and a", size=10, color=GREY)
p("  p95. if I want p99.9 I need the raw per-request numbers.", size=10, color=GREY)
p()

p("what to measure", size=12, bold=True, space=4)
p("mean, p50, p95, p99, p99.9", indent=0.25)
p("also throughput (req/s) and error rate, otherwise latency means nothing", indent=0.25)
p("^ a server that returns errors instantly looks FAST. need to catch that", indent=0.25, size=10, color=GREY)
p()
rule()

p("aug 21 - the actual test list", size=12, bold=True, space=4)
p("(this keeps growing. started with 3, now its 8)", size=10, italic=True, color=GREY, space=8)
p()
p("1. smoke - does it even work. 1 user, few seconds. sanity only")
p("2. calibration - ramp 1,2,4,8,16... find where it starts to hurt")
p("   need this FIRST or Im picking load levels at random", indent=0.2, size=10, color=GREY)
p("3. load matrix - concurrency x route. the baseline numbers")
p("4. stress - push till it breaks. find the actual ceiling")
p("5. soak - leave it running 1 hour. does it get worse over time (memory leak?)")
p("6. dataset size - make content.json bigger. x1 x10 x100 x1000")
p("7. rate limiter on vs off <- this one is interesting, see below")
p("8. mixed workload - most requests fast, SOME slow. the actual point of the paper")
p()

p("hypotheses (need these for the paper structure)", size=12, bold=True, space=4)
p("H1 - server degrades over a long run -> soak test", indent=0.25)
p("H2 - mean stays flat while tail blows up when data gets bigger -> dataset test", indent=0.25)
p("H3 - a fast server can be a broken server -> rate limiter test", indent=0.25)
p("H4 - mean gets diluted when only some requests are slow -> mixed workload", indent=0.25)
p()
p("if H1 or H2 come out wrong thats still a result. do NOT tune the app to make them", size=10, color=GREY)
p("come true. that would be cheating and also boring.", size=10, color=GREY)
p()
rule()

p("aug 22", size=12, bold=True, space=4)
p("H3 properly:")
p("the site has per-IP rate limiting. 30 req/min on /api/search.")
p("if I turn it ON and hammer it, it just returns 429 instantly to nearly everything.")
p("-> latency will look AMAZING. throughput will look amazing.")
p("-> and the service is returning nothing useful.")
p("thats the point. every metric improves while the thing stops working.", hl=True)
p()
p("must log error rate alongside or the result is meaningless")
p()

p("H4:", size=12, bold=True, space=4)
p("this is the real one I think.")
p("workload where 99.9% of requests are cheap and 0.1% hit a slow path.")
p("then 1%, then 10%, then 100%.")
p("watch what the mean does vs what p99 / p99.9 does.")
p("prediction: mean barely moves at 0.1%. p99.9 moves a lot.")
p()
p("?? what if p99 ALSO doesnt move at 0.1%. 0.1% of requests sits below p99 by", size=10, color=GREY)
p("   definition doesnt it. need to think about this properly. might be a sharper", size=10, color=GREY)
p("   result than the one I planned for.", size=10, color=GREY)
p()
rule()

p("things that went wrong (keeping track)", size=12, bold=True, space=4)
p("- launched the matrix from git bash, the path arguments got mangled, 0 rows out.")
p("  deleted the whole results dir and started over. run it from powershell only.")
p("- k6 raw output is HUGE. gigabytes. need to reduce to one row per request and")
p("  check the row count against k6s own summary so I know nothing was lost")
p("- stress test didnt actually break the server?? just sat flat at ~2s.")
p("  think the load generator ran out of workers before the server did. raise maxVUs")
p("  a lot and rerun.")
p("- unicode arrow crashed the analysis script on windows. PYTHONIOENCODING=utf-8")
p()
rule()

p("aug 24 - PROBLEM", size=12, bold=True, color=RED, space=4)
p("was reading about load testing and found coordinated omission.")
p("basically: with a fixed number of virtual users, each one WAITS for its response")
p("before sending the next request. so when the server is slow I automatically send")
p("FEWER requests. which means I under-sample exactly the slow periods I care about.")
p()
p("=> my percentiles are optimistic. possibly by a lot.", hl=True)
p()
p("this affects every number I have already collected. not great.")
p()
p("options:")
p("a) redo everything with an open model (fixed arrival rate)", indent=0.25)
p("b) ignore it and hope nobody asks", indent=0.25, strike=True)
p("c) add ONE extra arm that measures how big the bias actually is, keep the rest,", indent=0.25)
p("   report the bias honestly as a limitation", indent=0.25)
p()
p("going with c. dont have time for a. b is not an option.")
p("-> arm E: same load level, constant-arrival-rate instead of constant-vus. compare p99.")
p()
p("actually this might make the paper better. it turns a flaw into a measurement.", size=10, italic=True, color=GREY)
p()
rule()

p("still to sort out", size=12, bold=True, space=4)
p("[ ] load generator and server on the SAME machine. they compete for cpu.")
p("    cant fix it, only have one pc. -> threats to validity section, and use")
p("    Littles Law to check whether a slowdown is the server or the generator")
p("[ ] how many repeats per cell? 1 is not enough. 3? and throw away the first (warmup)")
p("[ ] the x1000 dataset run is going to be slow. might only get a few samples.")
p("    if the sample is small SAY SO. dont present it like its solid.")
p("[x] restore content.json to the original after the scaling tests")
p("[ ] check the live site repo is still untouched at the end. git status must be clean")
p("[ ] ask sir if 6 references is enough or if he wants more")
p()

p("rules for myself", size=12, bold=True, space=4)
p("- never type a number into the paper by hand. pull it from the results files.")
p("- if a run fails, write down that it failed. dont quietly rerun until it looks nice.")
p("- if a result looks weird, say it looks weird. dont smooth it over.")
p("- degradation is the finding. dont optimise the app to get prettier graphs.")
p()
p("(that last one is tempting and I need to not do it)", size=10, italic=True, color=GREY)
p()
rule()
p("next: write up section 3 and 4 first, theyre just describing what I did.", size=10, color=GREY)
p("results is the big one. do it in chunks, one arm at a time.", size=10, color=GREY)

out = os.path.join(ROOT, "docs", "testing-plan-notes.docx")
doc.save(out)
print("written:", out, f"({os.path.getsize(out)/1024:.0f} KB)")
