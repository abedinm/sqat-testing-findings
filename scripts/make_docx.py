#!/usr/bin/env python3
"""
make_docx.py - render paper/paper.md to a formatted academic paper.

Single-column journal style with a formal title block, numbered figures placed inline at
[[FIGURE:file|caption]] markers, and numbered tables captioned from [[TABLE:caption]]
markers. Figure and table numbering is assigned in document order, so inserting one
renumbers the rest automatically.

Usage: python make_docx.py
"""

import os
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
R = lambda *p: os.path.join(ROOT, *p)
FIGDIRS = [R("results", "figures"), R("results", "soak", "figures"),
           R("results", "scaled_merged", "figures")]

GREY = RGBColor(0x44, 0x4A, 0x52)
BODY_FONT = "Times New Roman"

TITLE = ("What the Mean Conceals: A Controlled Study of Percentile Analysis "
         "in Web Application Performance Testing")
AUTHOR = "Minhazul Abedin"
STUDENT_ID = "21-44625-1"
DEPT = "Department of Computer Science"
FACULTY = "Faculty of Science and Technology"
UNIVERSITY = "American International University-Bangladesh (AIUB)"
CITY = "Dhaka, Bangladesh"
COURSE = "Software Quality Assurance and Testing (SQAT) [A] — Final Term Assignment 2"


def find_figure(name):
    for d in FIGDIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def shade(cell, hex_colour):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_colour)
    tcPr.append(shd)


INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)")


def add_runs(par, text, size=10.5, bold=False, italic=False, color=None, font=None):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.font.name = "Consolas"
            r.font.size = Pt(size - 1.2); continue
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.italic = True
        else:
            r = par.add_run(part)
        r.font.size = Pt(size)
        r.font.name = font or BODY_FONT
        if bold:
            r.bold = True
        if italic:
            r.italic = True
        if color is not None:
            r.font.color.rgb = color


def title_block(doc):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(TITLE); r.bold = True; r.font.size = Pt(18); r.font.name = BODY_FONT

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(AUTHOR); r.font.size = Pt(12.5); r.font.name = BODY_FONT; r.bold = True

    for line, sz in ((f"Student ID: {STUDENT_ID}", 10.5), (DEPT, 10.5), (FACULTY, 10.5),
                     (UNIVERSITY, 10.5), (CITY, 10.5)):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(line); r.font.size = Pt(sz); r.font.name = BODY_FONT

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(14)
    r = p.add_run(COURSE); r.font.size = Pt(9.5); r.italic = True
    r.font.name = BODY_FONT; r.font.color.rgb = GREY

    bar = doc.add_paragraph(); bar.paragraph_format.space_after = Pt(12)
    pPr = bar._p.get_or_add_pPr(); pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:color", "888888")):
        bottom.set(qn(k), v)
    pbdr.append(bottom); pPr.append(pbdr)


def add_figure(doc, spec, number):
    name, _, caption = spec.partition("|")
    path = find_figure(name.strip())
    if not path:
        print(f"  MISSING FIGURE: {name}", file=sys.stderr)
        return False
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(3)
    p.add_run().add_picture(path, width=Inches(6.1))
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(12)
    r = c.add_run(f"Fig. {number}. "); r.bold = True; r.font.size = Pt(8.8)
    r.font.name = BODY_FONT
    r2 = c.add_run(caption.strip()); r2.font.size = Pt(8.8); r2.font.name = BODY_FONT
    r2.font.color.rgb = GREY
    return True


def add_table_caption(doc, caption, number):
    c = doc.add_paragraph()
    c.paragraph_format.space_before = Pt(9); c.paragraph_format.space_after = Pt(3)
    r = c.add_run(f"TABLE {number}. "); r.bold = True; r.font.size = Pt(8.8)
    r.font.name = BODY_FONT
    r2 = c.add_run(caption); r2.font.size = Pt(8.8); r2.font.name = BODY_FONT
    r2.font.color.rgb = GREY


def is_table_row(l):
    return l.strip().startswith("|") and l.strip().endswith("|")


def split_row(l):
    return [c.strip() for c in l.strip().strip("|").split("|")]


def main():
    md = R("paper", "paper.md")
    if not os.path.exists(md):
        sys.exit("paper.md not found; run build_paper.py first")
    lines = open(md, encoding="utf-8").read().split("\n")

    doc = Document()
    s = doc.sections[0]
    s.top_margin = s.bottom_margin = Inches(0.85)
    s.left_margin = s.right_margin = Inches(0.95)
    st = doc.styles["Normal"]
    st.font.name = BODY_FONT
    st.font.size = Pt(10.5)

    title_block(doc)

    fign = tabn = 0
    pending_caption = None
    i = 0
    in_code, code_buf = False, []
    skipped_title = False

    while i < len(lines):
        line = lines[i]
        st_ = line.strip()

        if st_.startswith("```"):
            if in_code:
                par = doc.add_paragraph()
                run = par.add_run("\n".join(code_buf))
                run.font.name = "Consolas"; run.font.size = Pt(8.3)
                par.paragraph_format.left_indent = Inches(0.28)
                par.paragraph_format.space_after = Pt(9)
                code_buf, in_code = [], False
            else:
                in_code = True
            i += 1; continue
        if in_code:
            code_buf.append(line); i += 1; continue

        if not st_ or (st_.startswith("---") and set(st_) <= set("- ")):
            i += 1; continue

        m = re.match(r"^\[\[FIGURE:(.+)\]\]$", st_)
        if m:
            fign += 1
            if not add_figure(doc, m.group(1), fign):
                fign -= 1
            i += 1; continue

        m = re.match(r"^\[\[TABLE:(.+)\]\]$", st_)
        if m:
            tabn += 1
            pending_caption = (m.group(1), tabn)
            i += 1; continue

        if is_table_row(line) and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i+1].strip()):
            if pending_caption:
                add_table_caption(doc, pending_caption[0], pending_caption[1])
                pending_caption = None
            header = split_row(line); i += 2
            body = []
            while i < len(lines) and is_table_row(lines[i]):
                body.append(split_row(lines[i])); i += 1
            t = doc.add_table(rows=len(body) + 1, cols=len(header))
            t.style = "Table Grid"
            for c, h in enumerate(header):
                cell = t.rows[0].cells[c]; cell.text = ""
                add_runs(cell.paragraphs[0], h, size=8.6, bold=True)
                shade(cell, "E9EEF4")
            for ri, row in enumerate(body, start=1):
                for c in range(len(header)):
                    cell = t.rows[ri].cells[c]; cell.text = ""
                    add_runs(cell.paragraphs[0], row[c] if c < len(row) else "", size=8.6)
            doc.add_paragraph().paragraph_format.space_after = Pt(8)
            continue

        m = re.match(r"^(#{1,4}) (.*)$", st_)
        if m:
            lvl, text = len(m.group(1)), m.group(2)
            if lvl == 1:
                if not skipped_title:      # title already rendered in the block above
                    skipped_title = True
                    i += 1; continue
            h = doc.add_heading(level=min(max(lvl, 2), 4)); h.text = ""
            h.paragraph_format.space_before = Pt(11); h.paragraph_format.space_after = Pt(4)
            add_runs(h, text, size={2: 12.5, 3: 11, 4: 10.5}.get(lvl, 11))
            i += 1; continue

        if st_.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            par = doc.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.35)
            par.paragraph_format.space_before = Pt(6); par.paragraph_format.space_after = Pt(9)
            add_runs(par, " ".join(buf), size=10.2, italic=True, color=GREY)
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", st_)
        if m:
            par = doc.add_paragraph(style="List Number")
            par.paragraph_format.space_after = Pt(3)
            add_runs(par, m.group(2)); i += 1; continue
        if st_.startswith(("- ", "* ")):
            par = doc.add_paragraph(style="List Bullet")
            par.paragraph_format.space_after = Pt(3)
            add_runs(par, st_[2:]); i += 1; continue

        buf = [st_]; i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", "|", ">", "- ", "* ", "```", "[["))
                    or re.match(r"^\d+\.\s", nxt)
                    or (nxt.startswith("---") and set(nxt) <= set("- "))):
                break
            buf.append(nxt); i += 1
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        par.paragraph_format.space_after = Pt(7)
        par.paragraph_format.line_spacing = 1.08
        add_runs(par, " ".join(buf))

    out = R("paper", "paper.docx")
    doc.save(out)
    print(f"paper.docx written: {os.path.getsize(out)/1024:.0f} KB")
    print(f"  figures placed inline: {fign}")
    print(f"  tables numbered:       {tabn}")


if __name__ == "__main__":
    main()
