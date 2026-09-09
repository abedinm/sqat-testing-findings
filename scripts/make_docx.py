#!/usr/bin/env python3
"""
make_docx.py - render paper/paper.md as a two-column conference paper.

IEEE-style layout: full-width title block, then two columns of 10 pt Times New Roman.
Wide content (figures, and tables with more than four columns) breaks out to span both
columns via continuous section breaks, the same way \\figure* and \\table* work in LaTeX.

Section numbering stays Arabic rather than Roman. The paper carries 22 internal
cross-references of the form "§5.7"; converting to "§V-G" would have to rewrite every one
of them, and a broken cross-reference costs more than a numbering convention.

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
BODY = "Times New Roman"
BODY_PT = 9.8
WIDE_TABLE_COLS = 0          # every table spans both columns; in two columns a
                             # table that fits still gets split across the column break

AUTHOR = "Minhazul Abedin"
STUDENT_ID = "21-44625-1"
DEPT = "Department of Computer Science"
FACULTY = "Faculty of Science and Technology"
UNIVERSITY = "American International University-Bangladesh (AIUB)"
CITY = "Dhaka, Bangladesh"
COURSE = "Software Quality Assurance and Testing (SQAT) [A] - Final Term Assignment 2"


def set_cols(section, n, space_twips=340):
    sectPr = section._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sectPr.append(cols)
    cols.set(qn("w:num"), str(n))
    cols.set(qn("w:space"), str(space_twips))
    cols.set(qn("w:equalWidth"), "1")


def new_section(doc, ncols):
    s = doc.add_section(WD_SECTION.CONTINUOUS)
    s.top_margin = s.bottom_margin = Inches(0.72)
    s.left_margin = s.right_margin = Inches(0.62)
    set_cols(s, ncols)
    return s


def find_figure(name):
    for d in FIGDIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def shade(cell, hexc):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hexc)
    tcPr.append(shd)


INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)")


def add_runs(par, text, size=BODY_PT, bold=False, italic=False, color=None, caps=False):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.font.name = "Consolas"
            r.font.size = Pt(size - 1.3)
            continue
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.italic = True
        else:
            r = par.add_run(part.upper() if caps else part)
        r.font.size = Pt(size)
        r.font.name = BODY
        if bold:
            r.bold = True
        if italic:
            r.italic = True
        if color is not None:
            r.font.color.rgb = color


def title_block(doc, title):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(9)
    r = p.add_run(title); r.font.size = Pt(19); r.font.name = BODY

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(AUTHOR); r.font.size = Pt(12); r.font.name = BODY

    for line in (f"Student ID: {STUDENT_ID}", DEPT, FACULTY, UNIVERSITY, CITY):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(line); r.font.size = Pt(9.5); r.font.name = BODY
        r.italic = line in (DEPT, FACULTY)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(7); p.paragraph_format.space_after = Pt(11)
    r = p.add_run(COURSE); r.font.size = Pt(8.8); r.italic = True
    r.font.name = BODY; r.font.color.rgb = GREY


def add_figure(doc, spec, number, width):
    name, _, caption = spec.partition("|")
    path = find_figure(name.strip())
    if not path:
        print(f"  MISSING FIGURE: {name}", file=sys.stderr)
        return False
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(7); p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Inches(width))
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(9)
    r = c.add_run(f"Fig. {number}.  "); r.font.size = Pt(8.2); r.font.name = BODY
    r2 = c.add_run(caption.strip()); r2.font.size = Pt(8.2); r2.font.name = BODY
    return True


def add_table_caption(doc, caption, number):
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_before = Pt(8); c.paragraph_format.space_after = Pt(2)
    c.paragraph_format.keep_with_next = True
    r = c.add_run(f"TABLE {number}.  "); r.font.size = Pt(8.2); r.font.name = BODY
    r2 = c.add_run(caption.upper() if len(caption) < 60 else caption)
    r2.font.size = Pt(8.2); r2.font.name = BODY


def is_row(l):
    s = l.strip()
    return s.startswith("|") and s.endswith("|")


def split_row(l):
    return [c.strip() for c in l.strip().strip("|").split("|")]


def main():
    md = R("paper", "paper.md")
    lines = open(md, encoding="utf-8").read().split("\n")
    title = next(l[2:].strip() for l in lines if l.startswith("# "))

    doc = Document()
    s0 = doc.sections[0]
    s0.top_margin = s0.bottom_margin = Inches(0.72)
    s0.left_margin = s0.right_margin = Inches(0.62)
    set_cols(s0, 1)
    st = doc.styles["Normal"]
    st.font.name = BODY
    st.font.size = Pt(BODY_PT)

    title_block(doc, title)
    new_section(doc, 2)
    ncols = [2]                      # current column count, mutable across helpers

    def want(n):
        if ncols[0] != n:
            new_section(doc, n)
            ncols[0] = n

    fign = tabn = 0
    pending = None
    i = 0
    in_code, buf_code = False, []
    saw_title = False

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if s.startswith("```"):
            if in_code:
                par = doc.add_paragraph()
                r = par.add_run("\n".join(buf_code))
                r.font.name = "Consolas"; r.font.size = Pt(7.4)
                par.paragraph_format.left_indent = Inches(0.1)
                par.paragraph_format.space_after = Pt(8)
                buf_code, in_code = [], False
            else:
                in_code = True
            i += 1; continue
        if in_code:
            buf_code.append(line); i += 1; continue

        if not s or (s.startswith("---") and set(s) <= set("- ")):
            i += 1; continue

        m = re.match(r"^\[\[FIGURE:(.+)\]\]$", s)
        if m:
            fign += 1
            want(1)
            if not add_figure(doc, m.group(1), fign, 6.3):
                fign -= 1
            want(2)
            i += 1; continue

        m = re.match(r"^\[\[TABLE:(.+)\]\]$", s)
        if m:
            tabn += 1
            pending = (m.group(1), tabn)
            i += 1; continue

        if is_row(line) and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i+1].strip()):
            header = split_row(line)
            wide = len(header) > WIDE_TABLE_COLS   # currently always true
            want(1 if wide else 2)
            if pending:
                add_table_caption(doc, pending[0], pending[1]); pending = None
            i += 2
            body = []
            while i < len(lines) and is_row(lines[i]):
                body.append(split_row(lines[i])); i += 1
            fs = 7.4 if wide else 8.2
            t = doc.add_table(rows=len(body) + 1, cols=len(header))
            t.style = "Table Grid"
            t.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for c, h in enumerate(header):
                cell = t.rows[0].cells[c]; cell.text = ""
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(cell.paragraphs[0], h, size=fs, bold=True)
                shade(cell, "E9EEF4")
            for ri, row in enumerate(body, start=1):
                for c in range(len(header)):
                    cell = t.rows[ri].cells[c]; cell.text = ""
                    add_runs(cell.paragraphs[0], row[c] if c < len(row) else "", size=fs)
            doc.add_paragraph().paragraph_format.space_after = Pt(7)
            want(2)
            continue

        m = re.match(r"^(#{1,4}) (.*)$", s)
        if m:
            lvl, txt = len(m.group(1)), m.group(2)
            if lvl == 1 and not saw_title:
                saw_title = True; i += 1; continue
            want(2)
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(9); h.paragraph_format.space_after = Pt(3)
            if lvl == 2:
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(h, txt, size=9.8, caps=True)
            else:
                add_runs(h, txt, size=9.8, italic=True)
            i += 1; continue

        want(2)

        if s.startswith(">"):
            b = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                b.append(lines[i].strip().lstrip(">").strip()); i += 1
            par = doc.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.16)
            par.paragraph_format.right_indent = Inches(0.08)
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            par.paragraph_format.space_before = Pt(4); par.paragraph_format.space_after = Pt(7)
            add_runs(par, " ".join(b), size=9.3, italic=True)
            continue

        # List items wrap across source lines. Continuation lines start no new block, so
        # gather them into the same item; otherwise the tail of every wrapped bullet is
        # emitted as a stray body paragraph.
        def continuation(j):
            if j >= len(lines):
                return False
            n = lines[j].strip()
            return bool(n) and not (
                n.startswith(("#", "|", ">", "- ", "* ", "```", "[["))
                or re.match(r"^\d+\.\s", n)
                or (n.startswith("---") and set(n) <= set("- ")))

        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m or s.startswith(("- ", "* ")):
            item = [m.group(2) if m else s[2:]]
            i += 1
            while continuation(i):
                item.append(lines[i].strip()); i += 1
            par = doc.add_paragraph(style="List Number" if m else "List Bullet")
            par.paragraph_format.space_after = Pt(2)
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_runs(par, " ".join(item))
            continue

        b = [s]; i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", "|", ">", "- ", "* ", "```", "[["))
                    or re.match(r"^\d+\.\s", nxt)
                    or (nxt.startswith("---") and set(nxt) <= set("- "))):
                break
            b.append(nxt); i += 1
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        par.paragraph_format.space_after = Pt(5)
        par.paragraph_format.first_line_indent = Inches(0.16)
        add_runs(par, " ".join(b))

    if pending:
        sys.exit(f"ABORT: table caption {pending[1]} ({pending[0][:50]}...) was never "
                 f"followed by a table. A [[TABLE:]] marker wrapped across two lines will "
                 f"do this - keep captions on one line.")

    out = R("paper", "paper.docx")
    doc.save(out)
    print(f"paper.docx written: {os.path.getsize(out)/1024:.0f} KB  (two-column)")
    print(f"  figures: {fign}   tables: {tabn}   sections: {len(doc.sections)}")


if __name__ == "__main__":
    main()
