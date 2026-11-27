"""Build Forgettability_EPS_Presentation_v2.pptx from the v1 deck, following docs/pre_outline_v2.md."""
import copy
import sys

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

SRC, OUT = sys.argv[1], sys.argv[2]

NAVY, SLATE, SAND, CREAM, WHITE, INK = "253439", "7C898B", "B29E84", "F6F4F1", "FFFFFF", "1C191A"
ACCENT = "B4533C"  # new emphasis colour: terracotta, warm sibling of the sand tone
LINE = "DDD8D0"
FONT = "Times New Roman"

prs = Presentation(SRC)
S = list(prs.slides)


def rgb(h):
    return RGBColor.from_string(h)


def remove(shape):
    shape._element.getparent().remove(shape._element)


def by_name(slide, name):
    return [s for s in slide.shapes if s.name == name]


def by_text(slide, start):
    return next(s for s in slide.shapes if s.has_text_frame and s.text_frame.text.startswith(start))


def set_text(shape, text, size=None, color=None, bold=None, italic=None):
    """Replace text while keeping the first run's formatting."""
    tf = shape.text_frame
    p0 = tf.paragraphs[0]
    r0 = p0.runs[0]
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    for r in list(p0.runs)[1:]:
        r._r.getparent().remove(r._r)
    for br in p0._p.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}br"):
        p0._p.remove(br)
    r0.text = text
    if size:
        r0.font.size = Pt(size)
    if color:
        r0.font.color.rgb = rgb(color)
    if bold is not None:
        r0.font.bold = bold
    if italic is not None:
        r0.font.italic = italic


def text(slide, x, y, w, h, runs, size=20, color=INK, bold=False, italic=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=None):
    """runs: str, or list of paragraphs; each paragraph a str or list of (text, overrides) tuples."""
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing:
            p.space_after = Pt(spacing)
        parts = para if isinstance(para, list) else [(para, {})]
        for t, o in parts:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = rgb(o.get("color", color))
    return tb


def box(slide, x, y, w, h, fill=WHITE, line=None, rounded=True, radius=0.06):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Emu(x), Emu(y), Emu(w), Emu(h))
    if rounded:
        shp.adjustments[0] = radius
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(fill)
    if line:
        shp.line.color.rgb = rgb(line)
        shp.line.width = Pt(1)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def arrow(slide, x1, y1, x2, y2, color=SLATE, width=1.5):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    tail = ln.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd", {"type": "triangle"})
    ln.append(tail)
    return c


def style_chart(chart, size=16):
    chart.has_title = False
    chart.font.name = FONT
    chart.font.size = Pt(size)
    chart.font.color.rgb = rgb(INK)


def bar_chart(slide, x, y, w, h, cats, vals, colors, horizontal=True, fmt='0.00', maxv=1.0, size=16,
              label_colors=None, gap=60):
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("v", vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = slide.shapes.add_chart(kind, Emu(x), Emu(y), Emu(w), Emu(h), cd)
    ch = gf.chart
    style_chart(ch, size)
    ch.has_legend = False
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.vary_by_categories = False
    ser = plot.series[0]
    for i, c in enumerate(colors):
        pt = ser.points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = rgb(c)
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(size)
    dl.font.bold = True
    dl.font.name = FONT
    if label_colors:
        for i, c in enumerate(label_colors):
            tf = ser.points[i].data_label.text_frame
            ser.points[i].data_label.position = XL_LABEL_POSITION.OUTSIDE_END
            run = tf.paragraphs[0].add_run()
            run.text = format_val(vals[i], fmt)
            run.font.color.rgb = rgb(c)
            run.font.bold = True
            run.font.size = Pt(size)
            run.font.name = FONT
    va = ch.value_axis
    va.maximum_scale = maxv
    va.minimum_scale = 0
    va.has_major_gridlines = False
    va.visible = False
    ca = ch.category_axis
    ca.format.line.color.rgb = rgb(LINE)
    ca.tick_labels.font.size = Pt(size)
    ca.tick_labels.font.name = FONT
    ca.has_major_gridlines = False
    if horizontal:
        ca.reverse_order = True
    return ch


def format_val(v, fmt):
    if fmt.endswith("%"):
        return f"{round(v * 100)}%"
    if fmt == "0":
        return f"{v:.0f}"
    return f"{v:.2f}"


def copy_header(src_slide, dst_slide, title):
    """Copy the title textbox and the three-square motif from a content slide."""
    for sh in src_slide.shapes:
        if sh.name in ("TextBox 2", "Group 24", "Group 27", "Group 30"):
            dst_slide.shapes._spTree.append(copy.deepcopy(sh._element))
    set_text(by_name(dst_slide, "TextBox 2")[0], title)


def key_line(slide, y, t, color=NAVY, size=26):
    return text(slide, 1554480, y, 15179040, 640080, t, size=size, color=color, bold=True, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)


def label(slide, x, y, w, t, color=SAND, size=18):
    return text(slide, x, y, w, 365760, t, size=size, color=color, bold=True)


def move_slide(prs, old_index, new_index):
    lst = prs.slides._sldIdLst
    el = list(lst)[old_index]
    lst.remove(el)
    lst.insert(new_index, el)


def new_slide(bg=CREAM):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(bg)
    return s


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def snap(slide):
    return {sh.shape_id for sh in slide.shapes}


def since(slide, before):
    return [sh.shape_id for sh in slide.shapes if sh.shape_id not in before]


def ids_named(slide, names):
    return [sh.shape_id for sh in slide.shapes if sh.name in names]


def set_clicks(slide, groups):
    """Replace the slide's animations: one click per group, every shape in it fades in together."""
    from lxml import etree
    sld = slide._element
    for t in sld.findall(f"{{{P_NS}}}timing"):
        sld.remove(t)
    groups = [g for g in groups if g]
    if not groups:
        return
    n = [2]

    def nid():
        n[0] += 1
        return str(n[0])

    effects = []
    for g in groups:
        pars = []
        for k, spid in enumerate(g):
            kind = "clickEffect" if k == 0 else "withEffect"
            pars.append(
                f'<p:par><p:cTn id="{nid()}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="{kind}">'
                f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
                f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
                f'<p:to><p:strVal val="visible"/></p:to></p:set>'
                f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{nid()}" dur="500"/>'
                f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
                f'</p:childTnLst></p:cTn></p:par>')
        outer, inner = nid(), nid()
        effects.append(
            f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            + "".join(pars) + '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    xml = (f'<p:timing xmlns:p="{P_NS}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
           f'<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
           + "".join(effects) +
           '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
           '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
           '</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
    el = etree.fromstring(xml)
    tr = sld.find(f"{{{P_NS}}}transition")
    if tr is not None:
        tr.addnext(el)
    else:
        sld.find(f"{{{P_NS}}}clrMapOvr").addnext(el)


HEADER = ("TextBox 2", "Group 24", "Group 27", "Group 30", "Group 18")
IN = 914400
L, R = 1554480, 16733520  # content left / right edge
W = R - L

from pptx.oxml.ns import qn


def _border(cell, color=LINE, width=9525):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnB", "a:lnT", "a:lnR", "a:lnL"):
        for old in tcPr.findall(qn(tag)):
            tcPr.remove(old)
        ln = tcPr.makeelement(qn(tag), {"w": str(width), "cap": "flat", "cmpd": "sng", "algn": "ctr"})
        sf = ln.makeelement(qn("a:solidFill"), {})
        clr = sf.makeelement(qn("a:srgbClr"), {"val": color})
        sf.append(clr)
        ln.append(sf)
        tcPr.insert(0, ln)


def math_runs(p, parts, size=30, color=NAVY):
    """Typeset a formula: parts = (text, italic, subscript)."""
    for t, ital, sub in parts:
        r = p.add_run()
        r.text = t
        f = r.font
        f.name, f.size, f.italic, f.bold = "Cambria Math", Pt(size * 0.6 if sub else size), ital, False
        f.color.rgb = rgb(color)
        if sub:
            r._r.get_or_add_rPr().set("baseline", "-25000")


# ---------------------------------------------------------------- slide 2 · promise (fix the facts)
s2 = S[1]
set_text(by_text(s2, "EVER PHOTO APP"), "EVER PHOTO APP · WHAT USERS WERE TOLD")
set_text(by_text(s2, "“Deactivate"), "“…this will permanently delete all photos and videos stored on your account.”",
         size=44)
set_text(by_text(s2, "Photos deleted"), "Deactivated users whose photos were actually deleted, until at least October 2019")
set_text(by_text(s2, "Source:"), "Source: FTC v. Everalbum, Inc., complaint ¶20 (customer-support reply), ¶22 (2021)")

# ---------------------------------------------------------------- slide 4 · three links: footer
_f = next(sh for sh in S[3].shapes if sh.name == "TextBox 50")
_fp = _f.text_frame.paragraphs[0]
for _r in list(_fp.runs):
    _r._r.getparent().remove(_r._r)
math_runs(_fp, [("C", True, False), ("deletion", False, True), ("  =  min", False, False), ("(", False, False),
                ("T", True, False), (", ", False, False), ("D", True, False), (", ", False, False),
                ("M", True, False), (")", False, False)], size=32)
set_text(by_text(S[3], "A conceptual model"), "A conceptual model, not a scoring system. Next: we built a system to test each link.")
_d = by_text(S[3], "Can it be taken out")
_d.left, _d.width = Emu(_d.left - 457200), Emu(_d.width + 914400)

# ---------------------------------------------------------------- slide 5 (new) · mini-Ever + yardstick
n5 = new_slide()
copy_header(S[2], n5, "We Built a Mini-Ever to Test It")
text(n5, L, 1828800, W, 411480, "Not Ever’s real system — a small, honest replica of its pipeline, trained from scratch.",
     size=20, color=SLATE, italic=True)
k0 = snap(n5)
# left card: pipeline
cx, cy, cw, ch_ = L, 2560320, 9052560, 5303520
box(n5, cx, cy, cw, ch_)
label(n5, cx + 365760, cy + 274320, cw - 731520, "THE PIPELINE")
# source box
bx, by_, bw, bh = cx + 365760, cy + 1005840, 2743200, 2560320
box(n5, bx, by_, bw, bh, fill=CREAM, rounded=True)
text(n5, bx + 182880, by_ + 182880, bw - 365760, bh - 365760, [
    [("1,000", {"size": 40, "bold": True, "color": NAVY})],
    [("celebrities (CelebA)", {"size": 18, "color": INK})],
    [("600", {"size": 32, "bold": True, "color": NAVY})],
    [("of them app users", {"size": 18})],
    [("~40% of each person’s photos uploaded by friends", {"size": 16, "color": ACCENT, "bold": True})],
], align=PP_ALIGN.CENTER)
# main model
mx, my, mw, mh = bx + bw + 548640, by_ + 731520, 2286000, 1097280
box(n5, mx, my, mw, mh, fill=NAVY)
text(n5, mx, my, mw, mh, [[("Main model", {"size": 22, "bold": True, "color": WHITE})],
                          [("ResNet-50 + ArcFace", {"size": 16, "color": "C9D0D1"})]],
     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
arrow(n5, bx + bw + 45720, my + mh // 2, mx - 45720, my + mh // 2)
# four downstream boxes
dx = mx + mw + 548640
dw = cx + cw - 365760 - dx
dh = 502920
names = ["Face gallery", "Phone copy (INT8)", "Distilled student", "Old checkpoint"]
for i, nm in enumerate(names):
    yy = by_ + 91440 + i * (dh + 137160)
    box(n5, dx, yy, dw, dh, fill=WHITE, line=SLATE)
    text(n5, dx, yy, dw, dh, nm, size=17, color=NAVY, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow(n5, mx + mw + 45720, my + mh // 2, dx - 45720, yy + dh // 2, width=1.25)
text(n5, cx + 365760, cy + ch_ - 1188720, cw - 731520, 914400, [
    [("20 users ask to be deleted. ", {"bold": True, "color": NAVY}),
     ("We delete them, then check every box above.", {})],
    [("Model starts from ImageNet — no pre-trained face model, so it cannot already know these celebrities.",
      {"size": 16, "color": SLATE, "italic": True})],
], size=19)
k1 = snap(n5)
# right card: the metric (leakage), spelled out step by step
rx = cx + cw + 365760
rw = R - rx
box(n5, rx, cy, rw, ch_)
x0, wi = rx + 320040, rw - 640080
label(n5, x0, cy + 228600, wi, "THE METRIC · LEAKAGE")
steps5 = [("1", "Score", "each deleted person: how well the system matches a new photo of them to them."),
          ("2", "Repeat", "on a reference model trained without them — the “never saw them” baseline."),
          ("3", "Compare", "all deleted-vs-reference pairs. AUC = share where the deleted system scores higher.")]
for i, (n, h, b_) in enumerate(steps5):
    yy = cy + 640080 + i * 685800
    text(n5, x0, yy, 365760, 640080, n, size=24, bold=True, color=SAND)
    text(n5, x0 + 411480, yy + 22860, wi - 411480, 640080, [[(h + " ", {"bold": True, "color": NAVY}), (b_, {})]],
         size=15, color=INK)
ftb = text(n5, x0, cy + 2651760, wi, 548640, "", size=26, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
math_runs(ftb.text_frame.paragraphs[0], [("Leakage", False, False), (" = 2 · ", False, False), ("AUC", False, False),
                                         (" − 1", False, False)], size=26)
# scale bar
sx, sy, sw = x0 + 91440, cy + 3383280, wi - 182880
seg = sw // 3
for i, c in enumerate([SLATE, SAND, ACCENT]):
    box(n5, sx + i * seg, sy, seg, 118872, fill=c, rounded=False)
text(n5, sx - 45720, sy + 182880, 2194560, 640080, [[("0", {"bold": True, "color": SLATE, "size": 26})],
                                                     [("forgotten · coin flip", {"size": 15})]], size=14)
text(n5, sx + sw - 2148840, sy + 182880, 2194560, 640080, [[("1", {"bold": True, "color": ACCENT, "size": 26})],
                                                            [("always recognised", {"size": 15})]], size=14,
     align=PP_ALIGN.RIGHT)
text(n5, x0, cy + ch_ - 914400, wi, 777240, [
    [("Pass: ", {"bold": True, "color": NAVY}), ("whole 90% interval ≤ 0.1, threshold fixed in advance.", {})],
    [("System: ", {"bold": True, "color": NAVY}), ("its worst copy — that’s where an attacker looks.", {})],
], size=15, color=INK, spacing=2)
k2 = snap(n5)
key_line(n5, 8138160, "The test is not “can it still recognise them?” — it is “does it act like it never met them?”",
         size=24)
text(n5, L, 8869680, W, 411480,
     "Small model, celebrity photos, 20 people per test: it shows where the structure breaks — not how Ever would have scored.",
     size=17, color=SLATE, italic=True, align=PP_ALIGN.CENTER)

set_clicks(n5, [[i for i in since(n5, k0) if i in k1], [i for i in since(n5, k1) if i in k2], since(n5, k2)])

# ---------------------------------------------------------------- slide 6 · T with experiment 1
s5 = S[4]
set_text(by_text(s5, "T ·"), "T · Where Did the Photos Go?")
for sh in list(s5.shapes):
    nm = sh.name
    t = sh.text_frame.text if sh.has_text_frame else ""
    if nm in ("Rounded Rectangle 55", "Oval 56", "Icon TbSearch", "Rounded Rectangle 60") or \
            t.startswith(("EVIDENCE", "Researchers", "IF T BREAKS", "“We deleted")) or nm == "Key line":
        remove(sh)
for sh in s5.shapes:  # lift the data-chain row a little
    if sh.name not in ("TextBox 2", "Group 24", "Group 27", "Group 30"):
        sh.top = sh.top - 228600
set_text(by_text(s5, "Ever’s promise covered"), "Ever promised only this — and didn’t keep it")
# redraw the chain to match our framework: photos → main model → downstream copies (the nodes we measure)
_drop = ("Oval 40", "Icon TbDatabase", "TextBox 42", "Oval 48", "Icon TbBuildingSkyscraper", "TextBox 50",
         "Oval 36", "Icon TbFaceId", "TextBox 38", "Connector 35", "Connector 39", "Connector 43", "Connector 47")
for sh in list(s5.shapes):
    if sh.name in _drop:
        remove(sh)
_ph = next(sh for sh in s5.shapes if sh.name == "Oval 32")
_mo = next(sh for sh in s5.shapes if sh.name == "Oval 44")
_mi = next(sh for sh in s5.shapes if sh.name == "Icon TbCpu")
_ml = next(sh for sh in s5.shapes if sh.name == "TextBox 46")
_mx = 5212080
_mi.left = Emu(_mi.left + _mx - _mo.left)
_ml.left = Emu(_ml.left + _mx - _mo.left)
_mo.left = Emu(_mx)
cy_mid = _ph.top + _ph.height // 2
set_text(by_text(s5, "User photos"), "User photos")
set_text(_ml, "Main model")
for tb, tag in ((by_text(s5, "User photos"), "FTC §III.A"), (_ml, "FTC §III.C")):
    tb.height = Emu(822960)
    p2 = tb.text_frame.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = tag
    r2.font.name, r2.font.size, r2.font.bold = FONT, Pt(16), True
    r2.font.color.rgb = rgb(SAND)
arrow(s5, _ph.left + _ph.width + 91440, cy_mid, _mo.left - 91440, cy_mid)
# downstream copies: 2 × 2 grid
gx = 8138160
gw = (R - gx - 182880) // 2
gh = 594360
gy0 = cy_mid - gh - 91440
for i, nm in enumerate(["Face gallery (embeddings)", "Phone copy (INT8)", "Distilled student", "Old checkpoint"]):
    col, row = i % 2, i // 2
    bx_ = gx + col * (gw + 182880)
    by_ = gy0 + row * (gh + 182880)
    box(s5, bx_, by_, gw, gh, fill=ACCENT if i == 0 else WHITE, line=None if i == 0 else SLATE)
    text(s5, bx_, by_, gw, gh, nm, size=19, bold=True, color=WHITE if i == 0 else NAVY, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    if col == 0:
        arrow(s5, _mo.left + _mo.width + 91440, cy_mid, gx - 91440, by_ + gh // 2, width=1.25)
text(s5, gx, _ml.top, R - gx, 822960, [
    [("Downstream copies", {"bold": True, "color": NAVY, "size": 22})],
    [("FTC §III.B (embeddings) · §III.C (models)", {"bold": True, "color": SAND, "size": 16})],
], align=PP_ALIGN.CENTER)
set_text(by_text(s5, "Where the influence"),
         "Where the influence lives on — for Ever, all the way to Paravision’s customers")
t_chain =[sh.shape_id for sh in s5.shapes if sh.name not in HEADER]
t0 = snap(s5)
ty = 5303520
th = 2971800
lw = 9418320
box(s5, L, ty, lw, th)
label(s5, L + 320040, ty + 182880, lw - 640080, "WE DELETED ONLY THEIR PHOTOS · LEAKAGE BY NODE (0 = forgotten)")
bar_chart(s5, L + 182880, ty + 548640, lw - 365760, th - 640080,
          ["Photo store", "Face gallery", "Main model", "Phone copy", "Old checkpoint", "Distilled student"],
          [0.0, 1.0, 0.46, 0.46, 0.46, 0.04],
          [SLATE, ACCENT, NAVY, NAVY, NAVY, SLATE], maxv=1.18, size=16, gap=45)
t1 = snap(s5)
rx = L + lw + 365760
rw = R - rx
box(s5, rx, ty, rw, th)
label(s5, rx + 320040, ty + 182880, rw - 640080, "DELETE OWN UPLOADS, THEN RETRAIN")
bar_chart(s5, rx + 182880, ty + 548640, rw - 365760, th - 1325880,
          ["Delete nothing", "Own uploads deleted", "Never saw them"],
          [0.46, 0.16, 0.0], [NAVY, ACCENT, SLATE], maxv=0.6, size=16, gap=45)
text(s5, rx + 320040, ty + th - 777240, rw - 640080, 640080,
     [[("≈ ⅓ of the memory remains", {"bold": True, "color": ACCENT}),
       (" — friends uploaded photos of them too.", {})]], size=18)
t2 = snap(s5)
key_line(s5, 8458200, "Deleting an account is not forgetting a person.")

set_clicks(s5, [t_chain, [i for i in since(s5, t0) if i in t1], [i for i in since(s5, t1) if i in t2], since(s5, t2)])

# ---------------------------------------------------------------- D and M concept slides (copies of the v1 slides)
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SKIP_RELS = ("notesSlide", "slideLayout", "chart")


def duplicate(src):
    """Copy a slide (shapes, background, images, transition, animations, notes) to the end of the deck."""
    dst = prs.slides.add_slide(prs.slide_layouts[6])
    rid_map = {}
    for rid, rel in src.part.rels.items():
        if rel.reltype.split("/")[-1] in SKIP_RELS:
            continue
        rid_map[rid] = dst.part.relate_to(rel._target, rel.reltype)
    s_el, d_el = src._element, dst._element
    s_csld, d_csld = s_el.find(f"{{{P_NS}}}cSld"), d_el.find(f"{{{P_NS}}}cSld")
    bg = s_csld.find(f"{{{P_NS}}}bg")
    if bg is not None:
        old = d_csld.find(f"{{{P_NS}}}bg")
        if old is not None:
            d_csld.remove(old)
        d_csld.insert(0, copy.deepcopy(bg))
    tree = dst.shapes._spTree
    for el in list(tree)[2:]:
        tree.remove(el)
    for el in list(src.shapes._spTree)[2:]:
        tree.append(copy.deepcopy(el))
    anchor = d_el.find(f"{{{P_NS}}}clrMapOvr")
    for tag in ("transition", "timing"):
        el = s_el.find(f"{{{P_NS}}}{tag}")
        if el is not None:
            el = copy.deepcopy(el)
            anchor.addnext(el)
            anchor = el
    for node in d_el.iter():
        for attr in (f"{{{R_NS}}}embed", f"{{{R_NS}}}id", f"{{{R_NS}}}link"):
            v = node.get(attr)
            if v in rid_map:
                node.set(attr, rid_map[v])
    if src.has_notes_slide:
        dst.notes_slide.notes_text_frame.text = src.notes_slide.notes_text_frame.text
    return dst


# D concept: the v1 SISA thought-experiment slide, kept as the idea before the results
dC = duplicate(S[5])
_tr = by_text(dC, "Cheap to train")
_tr.text_frame.paragraphs[0].runs[0].text = "Recognition accuracy"
set_text(by_text(dC, "A thought experiment"),
         "The idea: SISA (Bourtoule et al., 2021). Ever’s real architecture is not public — so next, we test the idea itself.")

# M concept: only the standard (Guo et al.); the language-model counterexample is dropped
def prune_timing(slide):
    """Drop animation effects whose target shape no longer exists, and click groups left empty."""
    t = slide._element.find(f"{{{P_NS}}}timing")
    if t is None:
        return
    ids = {str(sh.shape_id) for sh in slide.shapes}
    for ctn in list(t.iter(f"{{{P_NS}}}cTn")):
        if ctn.get("presetClass") is None:
            continue
        tgts = {e.get("spid") for e in ctn.iter(f"{{{P_NS}}}spTgt")}
        if tgts and not tgts & ids:
            par = ctn.getparent()
            par.getparent().remove(par)
    bld = t.find(f"{{{P_NS}}}bldLst")
    if bld is not None:
        for b in list(bld):
            if b.get("spid") not in ids:
                bld.remove(b)
        if not len(bld):
            t.remove(bld)
    changed = True
    while changed:  # remove timing containers left with no children
        changed = False
        for ctn in list(t.iter(f"{{{P_NS}}}cTn")):
            kids = ctn.find(f"{{{P_NS}}}childTnLst")
            if kids is not None and len(kids) == 0 and ctn.get("nodeType") not in ("tmRoot", "mainSeq"):
                par = ctn.getparent()
                par.getparent().remove(par)
                changed = True
    main = next(c for c in t.iter(f"{{{P_NS}}}cTn") if c.get("nodeType") == "mainSeq")
    for group in list(main.find(f"{{{P_NS}}}childTnLst")):
        effects = [c for c in group.iter(f"{{{P_NS}}}cTn") if c.get("presetClass")]
        if not effects:
            group.getparent().remove(group)
        else:
            effects[0].set("nodeType", "clickEffect")


mC = duplicate(S[6])
for sh in list(mC.shapes):
    if sh.has_chart or sh.name in ("Rounded Rectangle 44", "TextBox 45", "TextBox 46", "TextBox 48", "Connector 43"):
        remove(sh)
card = next(sh for sh in mC.shapes if sh.name == "Rounded Rectangle 32")
shift = (L + W // 2) - (card.left + card.width // 2)
card.width = Emu(W)
for sh in mC.shapes:
    if sh.name in ("Oval 35", "Oval 37", "TextBox 39", "TextBox 40", "TextBox 41") or \
            (sh.shape_type == 13 and card.top < sh.top < card.top + card.height):
        sh.left = Emu(sh.left + shift)
    if sh.name in ("TextBox 33", "TextBox 34"):
        sh.width = Emu(W - 914400)
set_text(by_text(mC, "1 · THE STANDARD"), "THE STANDARD")
set_text(by_text(mC, "Guo et al."), "Guo et al., ICML 2020 — not “can it still recognise them?”: face models recognise strangers too.")
next(sh for sh in mC.shapes if sh.name == "TextBox 42").width = Emu(W - 914400)
set_text(by_text(mC, "One passed test is not proof."), "So we tested faces: six methods, five tests →")
set_text(next(sh for sh in mC.shapes if sh.name == "Key line"),
         "The benchmark is not silence. It’s the never-trained model.")
# bottom row: drop the v1 “IF M BREAKS” box; the bridge to the results spans the row
for sh in list(mC.shapes):
    if sh.name in ("Rounded Rectangle 49", "TextBox 50", "TextBox 51"):
        remove(sh)
    elif sh.name in ("Rounded Rectangle 52", "TextBox 53"):
        sh.left, sh.width = Emu(L), Emu(W)
prune_timing(mC)
_main = next(c for c in mC._element.find(f"{{{P_NS}}}timing").iter(f"{{{P_NS}}}cTn") if c.get("nodeType") == "mainSeq")
_groups = list(_main.find(f"{{{P_NS}}}childTnLst"))
_groups[-1].addnext(_groups[-2])  # key line before the bridge to the results slide


def bridge(slide, rect_name, text_name, drop_names, msg):
    """Turn a v1 'IF X BREAKS' card into a dark bridge box (keeps its shape ids, so its click stays)."""
    rect = next(sh for sh in slide.shapes if sh.name == rect_name)
    rect.fill.solid()
    rect.fill.fore_color.rgb = rgb(NAVY)
    rect.line.fill.background()
    tb = next(sh for sh in slide.shapes if sh.name == text_name)
    tb.left, tb.top, tb.width, tb.height = rect.left, rect.top, rect.width, rect.height
    tb.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    tb.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    set_text(tb, msg, size=26, color=WHITE, bold=True, italic=False)
    for sh in list(slide.shapes):
        if sh.name in drop_names:
            remove(sh)
    prune_timing(slide)


bridge(dC, "Rounded Rectangle 67", "TextBox 69", ("TextBox 68",), "So we ran it: one big model vs. 1–16 shards →")

# ---------------------------------------------------------------- slide 7 · D with experiment 2
s6 = S[5]
set_text(by_text(s6, "D ·"), "D · We Ran It: Shards vs. One Model")
keep6 = ("TextBox 2", "Group 24", "Group 27", "Group 30", "TextBox 32")
for sh in list(s6.shapes):
    if sh.name not in keep6:
        remove(sh)
set_text(by_text(s6, "A thought experiment"),
         "20 deletion requests arriving one by one — one big model vs. 1, 4, 8 and 16 shards (SISA).")
d0 = snap(s6)
ty, th = 2468880, 5669280
lw = 9418320
box(s6, L, ty, lw, th)
label(s6, L + 320040, ty + 182880, lw - 640080, "GPU SECONDS PER DELETION")
cd = CategoryChartData()
cd.categories = ["1 shard", "4 shards", "8 shards", "16 shards"]
cd.add_series("Retrain the model only", (65, 19, 12, 8))
cd.add_series("Whole chain (model + student + gallery + phone copy)", (143, 99, 115, 167))
gf = s6.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Emu(L + 182880), Emu(ty + 548640), Emu(lw - 365760),
                         Emu(th - 1371600), cd)
ch = gf.chart
style_chart(ch, 16)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(16)
for ser, c, wdt in zip(ch.plots[0].series, [NAVY, ACCENT], [3, 4]):
    ser.format.line.color.rgb = rgb(c)
    ser.format.line.width = Pt(wdt)
    ser.smooth = False
    ser.marker.style = XL_MARKER_STYLE.CIRCLE
    ser.marker.size = 10
    ser.marker.format.fill.solid()
    ser.marker.format.fill.fore_color.rgb = rgb(c)
    ser.marker.format.line.color.rgb = rgb(c)
pl = ch.plots[0]
pl.has_data_labels = True
pl.data_labels.position = XL_LABEL_POSITION.ABOVE
pl.data_labels.font.size = Pt(16)
pl.data_labels.font.bold = True
pl.data_labels.number_format = '0" s"'
pl.data_labels.number_format_is_linked = False
va = ch.value_axis
va.maximum_scale = 200
va.minimum_scale = 0
va.has_major_gridlines = False
va.visible = False
ch.category_axis.format.line.color.rgb = rgb(LINE)
ch.category_axis.tick_labels.font.size = Pt(16)
text(s6, L + 320040, ty + th - 777240, lw - 640080, 640080,
     [[("For comparison, one big model: ", {}), ("109 s", {"bold": True, "color": NAVY}),
       (" model only, ", {}), ("186 s", {"bold": True, "color": ACCENT}), (" whole chain.", {})]],
     size=17, color=INK)
d1 = snap(s6)
rx = L + lw + 365760
rw = R - rx
box(s6, rx, ty, rw, th)
label(s6, rx + 320040, ty + 182880, rw - 640080, "RECOGNITION ACCURACY (1:N SEARCH)")
bar_chart(s6, rx + 182880, ty + 548640, rw - 365760, th - 1554480,
          ["Big model", "1 shard", "4 shards", "8 shards", "16 shards"],
          [0.58, 0.43, 0.32, 0.29, 0.25], [NAVY, SLATE, SLATE, SLATE, ACCENT], horizontal=False, fmt='0%',
          maxv=0.7, size=16, gap=50)
text(s6, rx + 320040, ty + th - 960120, rw - 640080, 822960,
     [[("8× cheaper", {"bold": True, "color": NAVY}), (" to retrain the model — but ", {}),
       ("43% → 25%", {"bold": True, "color": ACCENT}), (" accuracy, and the whole chain costs about the same.", {})]],
     size=17)
d2 = snap(s6)
key_line(s6, 8412480, "Design sets the ceiling — and the ceiling has a price.")

set_clicks(s6, [[i for i in since(s6, d0) if i in d1], [i for i in since(s6, d1) if i in d2], since(s6, d2)])

# ---------------------------------------------------------------- slide 8 · M with experiment 3
s7 = S[6]
set_text(by_text(s7, "M ·"), "M · We Ran It: Six Methods, Five Tests")
keep7 = ("TextBox 2", "Group 24", "Group 27", "Group 30", "Rounded Rectangle 52", "TextBox 53", "Key line")
for sh in list(s7.shapes):
    if sh.name not in keep7:
        remove(sh)
text(s7, L, 1828800, W, 411480,
     "Six deletion methods, five tests each — every test compared with a model that never saw these people.",
     size=20, color=SLATE, italic=True)
# full grid: 6 methods (+ reference) × 5 tests. Cell = (value, status); status ∈ fake / fail / pass / na / ref
TESTS = [("L1", "Says the name?"), ("L2", "Attacker can tell?"), ("L3", "Still there after compression?"),
         ("L4", "Relearns faster?"), ("L5", "Marker fires?")]
GRID = [
    ("Hide the names", [("✓", "fake"), ("✗", "fail"), ("✗", "fail"), ("✗", "fail"), ("✗", "fail")], "1 / 5"),
    ("Fine-tune on the rest", [("✗", "fail"), ("✗", "fail"), ("✗", "fail"), ("✗", "fail"), ("✗", "fail")], "0 / 5"),
    ("NegGrad+", [("✗", "fail"), ("✗", "fail"), ("✗", "fail"), ("✗", "fail"), ("✓", "fake")], "1 / 5"),
    ("SCRUB", [("✗", "fail"), ("✗", "fail"), ("✗", "fail"), ("✗", "fail"), ("✓", "fake")], "1 / 5"),
    ("Full retrain", [("✓", "pass"), ("✓", "pass"), ("✓", "pass"), ("✓", "pass"), ("✓", "pass")], "5 / 5"),
    ("SISA retrain", [("✓", "pass"), ("✓", "pass"), ("✓", "pass"), ("n/a", "na"), ("n/a", "na")], "3 / 3"),
]
m0 = snap(s7)
ty_ = 2423160
row_h = [685800] + [548640] * len(GRID)
gft = s7.shapes.add_table(len(row_h), 8, Emu(L), Emu(ty_), Emu(W), Emu(sum(row_h)))
tbl = gft.table
tbl.first_row = False
tbl.horz_banding = False
tblPr = gft._element.graphic.graphicData.tbl.tblPr
for el in list(tblPr):
    if el.tag.endswith("tableStyleId"):
        tblPr.remove(el)
ct, c0, cl = 2194560, 2834640, 1280160
cw7 = (W - ct - c0 - cl) // 5
for i, wd in enumerate([ct, c0] + [cw7] * 5 + [W - ct - c0 - 5 * cw7]):
    tbl.columns[i].width = Emu(wd)
for i, hgt in enumerate(row_h):
    tbl.rows[i].height = Emu(hgt)


def _run(p, t, size, color, bold=False, italic=False):
    r = p.add_run()
    r.text = t
    r.font.name, r.font.size, r.font.bold, r.font.italic = FONT, Pt(size), bold, italic
    r.font.color.rgb = rgb(color)


def _cell(r, c, fill):
    cell = tbl.cell(r, c)
    cell.margin_left = cell.margin_right = Emu(118872)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.fill.solid()
    cell.fill.fore_color.rgb = rgb(fill)
    _border(cell, color="C9C3B8")
    p = cell.text_frame.paragraphs[0]
    cell.text_frame.word_wrap = True
    p.alignment = PP_ALIGN.LEFT if c <= 1 else PP_ALIGN.CENTER
    return cell, p


_, p = _cell(0, 0, NAVY)
_run(p, "Type", 18, WHITE, bold=True)
_, p = _cell(0, 1, NAVY)
_run(p, "Method", 18, WHITE, bold=True)
for j, (code, q) in enumerate(TESTS, 2):
    cell, p = _cell(0, j, NAVY)
    _run(p, code, 15, SAND, bold=True)
    p2 = cell.text_frame.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    _run(p2, q, 15, WHITE, bold=True)
_, p = _cell(0, 7, NAVY)
_run(p, "Passed", 18, WHITE, bold=True)
for r, (name, cells, passed) in enumerate(GRID, 1):
    ref = False
    _, p = _cell(r, 1, "ECE8E2" if ref else WHITE)
    _run(p, name, 18, SLATE if ref else NAVY, bold=not ref, italic=ref)
    for j, (val, st) in enumerate(cells, 2):
        fill = NAVY if st == "fake" else ("ECE8E2" if ref else WHITE)
        _, p = _cell(r, j, fill)
        if st == "fake":
            _run(p, "✓", 26, WHITE, bold=True)
            _run(p, "  passed", 16, SAND, bold=True)
        elif st == "fail":
            _run(p, "✗", 26, ACCENT, bold=True)
        elif st == "pass":
            _run(p, "✓", 26, NAVY, bold=True)
        else:
            _run(p, val, 18, SLATE, italic=True)
    _, p = _cell(r, 7, "ECE8E2" if ref else WHITE)
    _run(p, passed, 20, SLATE if ref else (NAVY if passed in ("5 / 5", "3 / 3") else ACCENT), bold=not ref, italic=ref)
# method type: merged cells down the first column
for (r0, r1), (kind, sub) in zip(((1, 1), (2, 4), (5, 6)),
                                 (("Shortcut", "outputs only"), ("Approximate", "edit the weights"),
                                  ("Exact", "retrain without them"))):
    if r1 > r0:
        tbl.cell(r0, 0).merge(tbl.cell(r1, 0))
    cell, p = _cell(r0, 0, "ECE8E2")
    _run(p, kind, 19, NAVY, bold=True)
    p2 = cell.text_frame.add_paragraph()
    _run(p2, sub, 14, SLATE, italic=True)
gft.name = "M results grid"
table_bottom = ty_ + sum(row_h)
# legend + what the numbers are
lgy = table_bottom + 118872
box(s7, L, lgy + 45720, 228600, 228600, fill=NAVY, rounded=False)
text(s7, L + 320040, lgy, 5029200, 365760, "Passes one test — looks deleted, but isn’t", size=16, color=INK)
box(s7, L + 5303520, lgy + 45720, 228600, 228600, fill=ACCENT, rounded=False)
text(s7, L + 5623560, lgy, 9418320, 365760, "Fails the test — memory still there", size=16, color=INK)
# bottom: note + dark box (re-positioned)
m1 = snap(s7)
text(s7, L + 10058400, lgy, W - 10058400, 365760,
     [[("Retraining: ", {"bold": True, "color": NAVY}), ("under 2× the cost (114 s vs 62–68 s)", {})]],
     size=16, color=INK, align=PP_ALIGN.RIGHT)
by2 = 7132320
note = box(s7, L, by2, 7406640, 1188720)
text(s7, L + 320040, by2 + 137160, 7406640 - 640080, 960120, [
    [("74%", {"bold": True, "color": ACCENT, "size": 24}),
     ("  Filter switched off: the weights still name them", {})],
    [("62–64%", {"bold": True, "color": ACCENT, "size": 24}),
     ("  NegGrad+ / SCRUB still name them — marker gone", {})],
], size=18, spacing=2)
for sh in s7.shapes:
    if sh.name in ("Rounded Rectangle 52", "TextBox 53"):
        sh.left, sh.top, sh.width, sh.height = Emu(9326880), Emu(by2), Emu(7406640), Emu(1188720)
    if sh.name == "Key line":
        sh.top = Emu(8595360)

set_clicks(s7, [[i for i in since(s7, m0) if i in m1], since(s7, m1) + ids_named(s7, ('Rounded Rectangle 52', 'TextBox 53')), ids_named(s7, ('Key line',))])

# ---------------------------------------------------------------- slide 9 · verdict + what happened
s8 = S[7]
for sh in list(s8.shapes):
    if sh.name in ("Rounded Rectangle 50", "TextBox 51", "TextBox 52", "Rounded Rectangle 53", "TextBox 54",
                   "TextBox 55", "Key line"):
        remove(sh)
set_text(by_text(s8, "FTC order"), "FTC order against Everalbum, 2021 — delete all three:")
v_top = [sh.shape_id for sh in s8.shapes if sh.name not in HEADER]
v0 = snap(s8)
tags = [(1645919, "Ever: 0 deleted"), (7132320, "Our mini-Ever: gallery leakage 1.0"),
        (12618720, "Our mini-Ever: models still at 0.46")]
for x, t in tags:
    text(s8, x, 4846320, 4023360, 365760, t, size=17, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
v1 = snap(s8)
cy8, ch8 = 5486400, 2651760
cw8 = (W - 2 * 274320) // 3
xs = [L + i * (cw8 + 274320) for i in range(3)]
box(s8, xs[0], cy8, cw8, ch8, fill=NAVY)
label(s8, xs[0] + 320040, cy8 + 228600, cw8 - 640080, "FTC COMMISSIONER ROHIT CHOPRA", size=16)
text(s8, xs[0] + 320040, cy8 + 685800, cw8 - 640080, 1737360,
     "The company must “forfeit the fruits of its deception.”", size=24, color=WHITE, italic=True)
box(s8, xs[1], cy8, cw8, ch8)
label(s8, xs[1] + 320040, cy8 + 228600, cw8 - 640080, "OUR READING · NOT THE FTC’S", size=16)
text(s8, xs[1] + 320040, cy8 + 685800, cw8 - 640080, 1737360,
     "Can’t trace, isolate or prove? Deleting the whole model is the only deletion that needs no further proof.",
     size=20, color=INK)
v2 = snap(s8)
box(s8, xs[2], cy8, cw8, ch8, line=ACCENT)
box(s8, xs[2], cy8, 91440, ch8, fill=ACCENT, rounded=False)
label(s8, xs[2] + 320040, cy8 + 228600, cw8 - 640080, "WHAT ACTUALLY HAPPENED", color=ACCENT, size=16)
text(s8, xs[2] + 320040, cy8 + 640080, cw8 - 548640, 1920240, [
    [("Aug 2020  ", {"bold": True, "color": NAVY}), ("Ever shuts itself down", {})],
    [("May 2021  ", {"bold": True, "color": NAVY}), ("FTC order final", {})],
    [("2022  ", {"bold": True, "color": NAVY}), ("Paravision: deletion confirmed by ", {}),
     ("sworn statements", {"bold": True, "color": ACCENT})],
    [("No technical test. No fine.", {"bold": True, "color": ACCENT})],
], size=18, spacing=4)
v3 = snap(s8)
key_line(s8, 8412480, "The only proof accepted was a sworn statement. No one tested the forgetting.")

set_clicks(s8, [v_top + [i for i in since(s8, v0) if i in v1], [i for i in since(s8, v1) if i in v2], [i for i in since(s8, v2) if i in v3], since(s8, v3)])

# ---------------------------------------------------------------- slide 10 · weakest link (dark) with experiment 4
s9 = S[8]
# compress the three verbs into a top band
moves = {
    "Oval 28": (2286000, 1874520, 822960), "Oval 34": (4206240, 1874520, 822960), "Oval 40": (6126480, 1874520, 822960),
}
for sh in list(s9.shapes):
    if sh.name in ("Connector 33", "Connector 39", "TextBox 31", "TextBox 37", "TextBox 43", "TextBox 32",
                   "TextBox 38", "TextBox 44", "TextBox 48") or sh.name == "Motif bar":
        remove(sh)
ovals = [s for s in s9.shapes if s.name in ("Oval 28", "Oval 34", "Oval 40")]
icons = [s for s in s9.shapes if s.shape_type == 13]
verbs = [by_text(s9, t) for t in ("Trace", "Isolate", "Prove")]
for i, (ov, ic, vb) in enumerate(zip(ovals, icons, verbs)):
    x = L + i * 5577840
    ov.left, ov.top, ov.width, ov.height = Emu(x), Emu(1965960), Emu(822960), Emu(822960)
    ic.left, ic.top, ic.width, ic.height = Emu(x + 182880), Emu(1965960 + 182880), Emu(457200), Emu(457200)
    vb.left, vb.top, vb.width, vb.height = Emu(x + 1005840), Emu(1965960), Emu(4206240), Emu(822960)
    vb.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    vb.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    for r in vb.text_frame.paragraphs[0].runs:
        r.font.size = Pt(48)
    sub = ["where the data went · T", "its influence · D", "that it’s gone · M"][i]
    text(s9, x + 1005840, 2788920, 4206240, 365760, sub, size=18, color=SAND)
set_text(by_text(s9, "EVER’S PROMISE"), "KEEPING EVER’S PROMISE TOOK THREE THINGS. WE TESTED THE WEAKEST LINK:")
w_top = [sh.shape_id for sh in s9.shapes if sh.name not in HEADER]
w0 = snap(s9)
cy9, ch9 = 3611880, 4480560
lw9 = 9601200
box(s9, L, cy9, lw9, ch9, fill="2E3F45")
label(s9, L + 320040, cy9 + 182880, lw9 - 640080, "SYSTEM B · MAIN MODEL RETRAINED PERFECTLY, OLD FACE GALLERY KEPT", size=16)
c9 = bar_chart(s9, L + 182880, cy9 + 640080, lw9 - 365760, 2286000,
               ["Average of the parts", "What an attacker sees"], [0.26, 1.0], [SLATE, ACCENT], maxv=1.2, size=20,
               gap=40)
c9.font.color.rgb = rgb(WHITE)
c9.category_axis.tick_labels.font.color.rgb = rgb(WHITE)
c9.plots[0].data_labels.font.color.rgb = rgb(WHITE)
text(s9, L + 320040, cy9 + 3017520, lw9 - 640080, 1280160, [
    [("Main model clean. Gallery forgotten. ", {"color": WHITE}),
     ("Person still found: 100%.", {"color": ACCENT, "bold": True})],
    [("Fixing the other parts did not move the total at all.", {"size": 17, "color": "C9D0D1", "italic": True})],
], size=22)
w1 = snap(s9)
rx9 = L + lw9 + 320040
rw9 = R - rx9
box(s9, rx9, cy9, rw9, ch9, fill="2E3F45")
label(s9, rx9 + 320040, cy9 + 182880, rw9 - 640080, "ALL FOUR SYSTEMS · LEAKAGE", size=16)
sysrows = [("A  Only photos deleted", "1.00", ACCENT), ("B  Model retrained, gallery kept", "1.00", ACCENT),
           ("C  Approximate unlearning", "0.35–0.49", ACCENT), ("D  Every node handled", "0–0.01", SAND)]
for i, (nm, v, c) in enumerate(sysrows):
    yy = cy9 + 685800 + i * 594360
    text(s9, rx9 + 320040, yy, rw9 - 1920240, 548640, nm, size=19, color=WHITE, bold=(i == 3), anchor=MSO_ANCHOR.MIDDLE)
    text(s9, rx9 + rw9 - 1737360, yy, 1417320, 548640, v, size=22, color=c, bold=True, align=PP_ALIGN.RIGHT,
         anchor=MSO_ANCHOR.MIDDLE)
text(s9, rx9 + 320040, cy9 + 3200400, rw9 - 640080, 1188720, [
    [("Tracing can’t be sloppy: ", {"bold": True, "color": WHITE}),
     ("missing ~1 photo per person left no trace (0.01); missing ~8 brought back 0.19.", {"color": "C9D0D1"})],
], size=17)
w2 = snap(s9)
for i, c in enumerate([SLATE, SAND, WHITE]):
    box(s9, 7223760 + [0, 960120, 1536192][i], 8366760, [960120, 576072, 2304288][i], 109728, fill=c, rounded=False)
text(s9, L, 8595360, W, 640080, "Credible deletion is only as strong as its weakest link.", size=30, color=WHITE,
     italic=True, align=PP_ALIGN.CENTER)

set_clicks(s9, [w_top, [i for i in since(s9, w0) if i in w1], [i for i in since(s9, w1) if i in w2], since(s9, w2)])

# ---------------------------------------------------------------- slide 12 · thank you (typo)
set_text(by_text(S[10], "Presented by"), "Presented by: Jinghan ZHAO, Qingyang LI")

# ---------------------------------------------------------------- slide 13 · references
refs = [
    "Bourtoule, L. et al. (2021). Machine Unlearning. IEEE Symposium on Security and Privacy.",
    "Chopra, R. (2021). Statement of Commissioner Rohit Chopra, In the Matter of Everalbum and Paravision. FTC.",
    "Deng, J. et al. (2019). ArcFace: Additive Angular Margin Loss for Deep Face Recognition. CVPR.",
    "European Data Protection Board (2024). Opinion 28/2024 on AI models.",
    "Federal Trade Commission (2021). In the Matter of Everalbum, Inc. — complaint and decision & order (C-4743).",
    "Guo, C. et al. (2020). Certified Data Removal from Machine Learning Models. ICML.",
    "Hayes, J. et al. (2025). Inexact Unlearning Needs More Careful Evaluations to Avoid a False Sense of Privacy. IEEE SaTML.",
    "Kurmanji, M. et al. (2023). Towards Unbounded Machine Unlearning (SCRUB). NeurIPS.",
    "Liu, Z. et al. (2015). Deep Learning Face Attributes in the Wild (CelebA). ICCV.",
    "Paravision, Inc. (2022). One-year compliance report to the FTC, Docket C-4743.",
    "Regulation (EU) 2016/679 (GDPR), Article 17 — Right to erasure.",
    "Personal Information Protection Law of the PRC (2021), Article 47.",
]
rtb = by_text(S[11], "Bourtoule")
tf = rtb.text_frame
proto = copy.deepcopy(tf.paragraphs[0]._p)
for p in list(tf.paragraphs):
    p._p.getparent().remove(p._p)
for r in refs:
    p = copy.deepcopy(proto)
    tf._txBody.append(p)
    para = tf.paragraphs[-1]
    for extra in para.runs[1:]:
        extra._r.getparent().remove(extra._r)
    para.runs[0].text = r
text(S[11], L, 9418320, W, 365760,
     "Experiments: Mini-Ever on CelebA (1,000 identities), ResNet-50/18, 3 forget groups × 20 people, 90% bootstrap intervals over people.",
     size=16, color=SLATE, italic=True)

# ---------------------------------------------------------------- appendix (for Q&A, no animations)
from pptx.oxml.ns import qn


def table(slide, x, y, w, rows, fracs, row_h=420624, size=16, accent=(), strong=(), muted_rows=(), header=True,
          first_left=True, head_size=None, left_cols=()):
    """Appendix table in the deck style. accent / strong: sets of (row, col)."""
    n_r, n_c = len(rows), len(rows[0])
    gf = slide.shapes.add_table(n_r, n_c, Emu(x), Emu(y), Emu(w), Emu(row_h * n_r))
    tbl = gf.table
    tbl.first_row = False
    tbl.horz_banding = False
    tblPr = gf._element.graphic.graphicData.tbl.tblPr
    for el in list(tblPr):
        if el.tag.endswith("tableStyleId"):
            tblPr.remove(el)
    tot = sum(fracs)
    ws = [int(w * f / tot) for f in fracs]
    ws[-1] = w - sum(ws[:-1])
    for i, wd in enumerate(ws):
        tbl.columns[i].width = Emu(wd)
    for i in range(n_r):
        tbl.rows[i].height = Emu(row_h)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = cell.margin_right = Emu(118872)
            cell.margin_top = cell.margin_bottom = Emu(27432)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            fill, color, bold, italic, sz = WHITE, INK, False, False, size
            if header and r == 0:
                fill, color, bold, sz = NAVY, WHITE, True, head_size or size
            elif r in muted_rows:
                fill, color, italic = "ECE8E2", SLATE, True
            if c == 0 and not (header and r == 0) and r not in muted_rows:
                color, bold = NAVY, True
            if (r, c) in accent:
                color, bold = ACCENT, True
            if (r, c) in strong:
                color, bold = NAVY, True
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(fill)
            _border(cell)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ((c == 0 and first_left) or c in left_cols) else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = str(val)
            f = run.font
            f.name, f.size, f.bold, f.italic = FONT, Pt(sz), bold, italic
            f.color.rgb = rgb(color)
    return gf


def flow(slide, x, y, w, h, steps, gap=320040, fills=None, size=16):
    """Horizontal numbered steps joined by arrows. steps: list of (title, body)."""
    n = len(steps)
    bw = (w - gap * (n - 1)) // n
    for i, (title, body) in enumerate(steps):
        bx = x + i * (bw + gap)
        fill = (fills or [WHITE] * n)[i]
        dark = fill == NAVY
        box(slide, bx, y, bw, h, fill=fill, line=None if dark else LINE)
        text(slide, bx + 137160, y + 91440, bw - 274320, h - 182880, [
            [(f"{i + 1}  ", {"bold": True, "color": SAND, "size": size + 2}),
             (title, {"bold": True, "color": WHITE if dark else NAVY, "size": size + 1})],
            [(body, {"size": size - 1, "color": "C9D0D1" if dark else INK})],
        ], size=size, spacing=2)
        if i < n - 1:
            arrow(slide, bx + bw + 45720, y + h // 2, bx + bw + gap - 45720, y + h // 2, color=SLATE, width=1.5)


def appendix_slide(code, title, sub):
    s = new_slide()
    copy_header(S[2], s, f"{code} · {title}")
    for sh in s.shapes:
        if sh.name == "TextBox 2":
            for r in sh.text_frame.paragraphs[0].runs:
                r.font.size = Pt(48)
    text(s, L, 1737360, W, 411480, sub, size=19, color=SLATE, italic=True)
    text(s, R - 2743200, 9692640, 2743200, 320040, "APPENDIX · FOR Q&A", size=13, color=SAND, bold=True,
         align=PP_ALIGN.RIGHT)
    return s


def note(slide, y, runs, size=16, h=640080):
    return text(slide, L, y, W, h, runs, size=size, color=INK)


TOP = 2286000  # content start under title + subtitle

# A0 · divider
a0 = new_slide(bg=NAVY)
text(a0, L, 2286000, W, 1463040, "Appendix", size=80, color=WHITE)
text(a0, L, 3749040, W, 548640, "Full experimental details, for questions.", size=26, color=SAND, italic=True)
for i, c in enumerate([SLATE, SAND, WHITE]):
    box(a0, L + [0, 960120, 1536192][i], 4572000, [960120, 576072, 2304288][i], 109728, fill=c, rounded=False)
toc = [("A1", "Setup: data, pipeline, training"), ("A2", "How we measure: score → leakage → verdict"),
       ("A3", "Experiment 0: is the yardstick reliable?"), ("A4", "Experiment 1: delete photos only"),
       ("A5", "Experiment 1b: account ≠ person"), ("A6", "Experiment 2: cost of deletion (SISA)"),
       ("A7", "Experiment 3: design (six methods, five tests)"), ("A8", "Experiment 3: full results"),
       ("A9", "Experiment 4: four systems, weakest link"), ("A10", "Experiment 4b: imperfect tracing"),
       ("A11", "Limits and deviations")]
for i, (code, t) in enumerate(toc):
    col, row = divmod(i, 6)
    x = L + col * 7772400
    y = 5120640 + row * 640080
    text(a0, x, y, 914400, 548640, code, size=22, color=SAND, bold=True)
    text(a0, x + 1005840, y, 6583680, 548640, t, size=22, color=WHITE)

# A1 · setup
a1 = appendix_slide("A1", "Setup: Data, Pipeline, Training",
                    "A small replica of a face-recognition pipeline, trained from scratch on CelebA.")
lw = 8229600
label(a1, L, TOP, lw, "DATA")
table(a1, L, TOP + 411480, lw, [
    ("Item", "Value"),
    ("Source", "CelebA (aligned faces), 1,000 identities drawn from 3,661 with ≥ 25 photos"),
    ("Pools", "400 public (never deleted) · 600 app users"),
    ("Forget groups", "3 groups × 20 users, drawn from the app users"),
    ("Photos", "29,097 total: 20,356 training · 2,899 enrolment · 5,842 audit"),
    ("Per person", "70% training · 10% enrolment (gallery) · 20% audit (never trained on)"),
    ("Uploaders", "User training photos: 61% own account, 39% two “friend” accounts"),
], [1.1, 3.4], row_h=685800, size=17, head_size=17, left_cols={1})
rx = L + lw + 457200
rw = R - rx
label(a1, rx, TOP, rw, "PIPELINE (EACH STEP IS A NODE WE TEST)")
steps = [("Stage 1 · public base", "ResNet-50 from ImageNet, trained on the 400 public people, 20 epochs."),
         ("Stage 2 · main model", "Public + user photos, 15 epochs. The model a deletion must fix."),
         ("Downstream copies", "Face gallery (enrolment photos embedded) · INT8 phone copy · ResNet-18 student "
                               "(10 epochs, no forget-group data) · old checkpoint.")]
for i, (t, b) in enumerate(steps):
    yy = TOP + 411480 + i * 1645920
    box(a1, rx, yy, rw, 1463040, fill=NAVY if i == 1 else WHITE, line=None if i == 1 else LINE)
    text(a1, rx + 228600, yy + 137160, rw - 457200, 1280160, [
        [(t, {"bold": True, "color": WHITE if i == 1 else NAVY, "size": 20})],
        [(b, {"size": 17, "color": "C9D0D1" if i == 1 else INK})]], spacing=2)
    if i < 2:
        arrow(a1, rx + rw // 2, yy + 1463040 + 22860, rx + rw // 2, yy + 1645920 - 22860)
note(a1, 7680960, [
    [("Training: ", {"bold": True, "color": NAVY}),
     ("SGD, lr 0.1, batch 128, embedding 512, ArcFace s = 32, m = 0.3 · seeds 1, 2, 3 · references use a derived seed.", {})],
    [("Why s = 32, m = 0.3: ", {"bold": True, "color": NAVY}),
     ("the textbook s = 64, m = 0.5 did not train at this scale (train accuracy 0.002 < chance 0.0025). "
      "Chosen only on “does it learn?”, without looking at Experiment 0.", {})],
    [("Frozen: ", {"bold": True, "color": NAVY}),
     ("config celeba_v1 (hash 9d1bbe65…), split hash 904b9a82…, margins and seeds fixed before any experiment.", {})],
], size=17, h=1737360)

# A2 · measurement
a2 = appendix_slide("A2", "How We Measure",
                    "Same pipeline for every node and every experiment: score → compare → leakage → interval → verdict.")
flow(a2, L, TOP, W, 1554480, [
    ("Score each person", "Audit photos only (never trained on). One score per person per node."),
    ("Compare with reference", "Same 20 people on a system that never saw them. All 20 × 20 pairs."),
    ("Leakage", "AUC = share of pairs where the deleted system scores higher. Leakage = max(0, 2·AUC − 1)."),
    ("Whole system", "Maximum over nodes — an attacker uses the weakest copy. Mean reported only for contrast."),
    ("Interval", "Resample the 20 people with replacement, 2,000×. Middle 90% = interval."),
    ("Verdict", "Compare the interval with the margin frozen in the config."),
], fills=[WHITE, WHITE, NAVY, WHITE, WHITE, NAVY], size=15)
cy = TOP + 1828800
cw = (W - 365760) // 2
box(a2, L, cy, cw, 3474720)
label(a2, L + 274320, cy + 182880, cw - 548640, "WHAT “SCORE” MEANS")
table(a2, L + 274320, cy + 594360, cw - 548640, [
    ("Node / test", "Score of one person"),
    ("Models (main, student, phone, archive)", "Mean cosine: audit photos vs. enrolment prototype"),
    ("Face gallery", "Best cosine in the gallery; −1 if not enrolled"),
    ("L1 output (Exp 3)", "Share of audit photos classified as this person"),
    ("L5 marker (Exp 3)", "Share of marked audit photos classified as the marker target"),
], [1.5, 2.2], row_h=502920, size=15, head_size=15, left_cols={1})
rx = L + cw + 365760
box(a2, rx, cy, cw, 3474720)
label(a2, rx + 274320, cy + 182880, cw - 548640, "VERDICT RULES · 90% INTERVAL VS. FROZEN MARGIN")
table(a2, rx + 274320, cy + 594360, cw - 548640, [
    ("Quantity", "Margin", "Pass", "Fail"),
    ("Leakage (all nodes)", "0.1", "upper ≤ 0.1", "lower > 0.1"),
    ("L1, L4, L5 differences", "± 0.1", "inside ± 0.1", "outside"),
    ("L2 U-LiRA (AUC − 0.5)", "± 0.05", "inside ± 0.05", "outside"),
    ("Exp 0 group differences", "± 0.1", "inside ± 0.1", "outside"),
], [1.8, 0.8, 1.1, 1.0], row_h=502920, size=14, head_size=14)
text(a2, rx + 274320, cy + 3200400 - 182880, cw - 548640, 365760,
     "Anything else is “uncertain” — not a pass, not a fail.", size=15, color=ACCENT, bold=True)
note(a2, 7680960, [
    [("Why pairs, not person-by-person: ", {"bold": True, "color": NAVY}),
     ("an attacker only sees the deleted system and must compare a score with unseen people in general. "
      "Leakage 0.1 = AUC 0.55: right 55 times in 100, vs. 50 for a coin.", {})],
], size=16, h=914400)

# A3 · experiment 0
a3 = appendix_slide("A3", "Experiment 0: Is the Yardstick Reliable?",
                    "Run before any user photo is used. Q1: did the start models already know these celebrities? Q2: can our test tell “seen” from “unseen”?")
flow(a3, L, TOP, W, 1188720, [
    ("Two start models", "ImageNet only (no faces) · public base (knows the 400 public people only)."),
    ("Two metrics", "1:1 TAR at FAR 0.001 · 1:N top-1. Enrol with enrolment photos, test with audit photos."),
    ("Comparison A", "Forget group (20) vs. other users (~580), same model. Want: equal."),
    ("Comparison B", "Positive control: public (seen) vs. users (unseen). Want: clearly different."),
], size=15)
y3 = TOP + 1463040
label(a3, L, y3, W, "POSITIVE CONTROL (PUBLIC BASE) · DETECTED IF THE WHOLE INTERVAL IS ABOVE 0.1")
table(a3, L, y3 + 411480, W, [
    ("Metric", "Public pool (seen)", "App users (unseen)", "Difference (90% interval)", "Result"),
    ("Verification TAR", "0.327", "0.170", "+0.157 (0.131 to 0.183)", "detected"),
    ("Retrieval top-1", "0.409", "0.209", "+0.200 (0.171 to 0.230)", "detected"),
], [1.4, 1, 1, 1.6, 0.9], row_h=457200, size=16, accent={(1, 3), (2, 3)})
y3b = y3 + 2011680
label(a3, L, y3b, W, "FORGET GROUP VS. OTHER USERS · PASS IF THE WHOLE INTERVAL IS INSIDE ± 0.1")
table(a3, L, y3b + 411480, W, [
    ("Start model · group", "TAR difference (90% interval)", "Top-1 difference (90% interval)", "Verdict"),
    ("ImageNet · groups 0, 1, 2", "+0.006 / +0.005 / +0.017 (all within ± 0.04)", "−0.007 / −0.024 / +0.052 (all within ± 0.1)", "pass × 6"),
    ("Public base · group 0", "−0.004 (−0.055 to 0.047)", "−0.007 (−0.088 to 0.075)", "pass"),
    ("Public base · group 1", "−0.077 (−0.121 to −0.024) · TAR 0.093 vs 0.170", "−0.136 (−0.199 to −0.066)", "uncertain — harder"),
    ("Public base · group 2", "+0.078 (−0.006 to 0.168) · TAR 0.242 vs 0.164", "+0.076 (−0.020 to 0.177)", "uncertain — easier"),
], [1.4, 2.2, 1.8, 1.1], row_h=457200, size=15, strong={(1, 3), (2, 3)}, accent={(3, 3), (4, 3)})
note(a3, 8869680, [[("Reading: ", {"bold": True, "color": NAVY}),
                    ("the public base never saw any user, so group 1/2 differences are photo difficulty, not familiarity "
                     "(and they point in opposite directions). Later experiments compare the same people on both sides, so this cancels.", {})]],
     size=15)

# A4 · experiment 1
a4 = appendix_slide("A4", "Experiment 1: Delete the Photos Only",
                    "Q: if Ever had deleted every photo, where would the person still be?")
flow(a4, L, TOP, W, 1097280, [
    ("Delete photos", "All training photos of the 20 people removed (411→0, 401→0, 410→0). Nothing else touched."),
    ("Score 6 nodes", "Each node vs. its matched reference: gallery without them, model / student / INT8 copy trained without them."),
    ("Leakage per node", "3 seeds averaged per person, then 2,000 resamples, margin 0.1."),
], size=15)
y4 = TOP + 1371600
table(a4, L, y4, W, [
    ("Node", "Group 0", "Group 1", "Group 2", "Verdict", "Why"),
    ("Face gallery", "1.00", "1.00", "1.00", "fail", "Records untouched; reference never enrolled them"),
    ("Main model", "0.50 (0.39–0.68)", "0.42 (0.31–0.57)", "0.46 (0.36–0.65)", "fail", "Weights unchanged"),
    ("Phone copy (INT8)", "0.49 (0.38–0.66)", "0.42 (0.31–0.57)", "0.46 (0.35–0.63)", "fail", "Compression is not deletion"),
    ("Old checkpoint", "0.50 (0.38–0.68)", "0.42 (0.30–0.59)", "0.46 (0.36–0.64)", "fail", "Nobody touched it"),
    ("Distilled student", "0.04 (0.00–0.13)", "0.06 (0.01–0.17)", "0.02 (0.00–0.11)", "uncertain", "Taught on data without them"),
    ("Whole system (max)", "1.00", "1.00", "1.00", "fail", "Weakest node: gallery"),
    ("Mean of nodes (contrast)", "0.50", "0.46", "0.48", "—", "Would understate the risk by half"),
], [1.5, 1.2, 1.2, 1.2, 0.8, 2.4], row_h=640080, size=17, left_cols={5},
    accent={(1, 1), (1, 2), (1, 3), (6, 1), (6, 2), (6, 3)}, muted_rows={7})
note(a4, 8869680, [
    [("In AUC terms: ", {"bold": True, "color": NAVY}),
     ("main model 0.42–0.50 = AUC 0.71–0.75 — in 71–75 of 100 comparisons, the system that “deleted” the photos knows the person better than one that never saw them.", {})],
], size=18, h=822960)

# A5 · experiment 1b
a5 = appendix_slide("A5", "Experiment 1b: Account ≠ Person",
                    "Q: if a careful company deletes everything the user uploaded and retrains exactly, is the person forgotten?")
flow(a5, L, TOP, W, 1188720, [
    ("Account reference", "Remove the user’s own uploads (≈ 61%), retrain exactly. Friends’ uploads (≈ 39%, ≈ 8 photos) stay."),
    ("Person reference", "Remove every photo of the person, whoever uploaded it. The true yardstick."),
    ("Leakage", "Account reference vs. person reference, main model, same scoring as A2."),
    ("Noise floor", "Person reference seed 1 vs. seed 2 — two models that never saw them."),
], size=15)
y5 = TOP + 1463040
table(a5, L, y5, W, [
    ("Group", "Delete nothing", "Account deleted + exact retrain", "Noise floor (ref vs. ref)", "Share remaining"),
    ("0", "0.50 (AUC 0.75)", "0.21 (0.11–0.36) · AUC 0.60", "0.07 (0.00–0.19)", "≈ 41%"),
    ("1", "0.42 (AUC 0.71)", "0.11 (0.03–0.22) · AUC 0.55", "0.00 (0.00–0.13)", "≈ 25%"),
    ("2", "0.46 (AUC 0.73)", "0.18 (0.11–0.30) · AUC 0.59", "0.10 (0.00–0.26)", "≈ 39%"),
    ("Mean", "0.46", "0.16", "—", "≈ one third"),
], [0.8, 1.4, 2.2, 1.7, 1.2], row_h=640080, size=18, accent={(1, 2), (2, 2), (3, 2), (4, 2), (4, 4)})
note(a5, y5 + 3474720, [
    [("Reading: ", {"bold": True, "color": NAVY}),
     ("groups 0 and 2 sit clearly above the noise floor (lower bound 0.11); group 1 is weaker and overlaps it — "
      "it was already the “harder” group in Experiment 0.", {})],
    [("Not an algorithm problem: ", {"bold": True, "color": NAVY}),
     ("the account reference is an exact retrain. The gap comes from defining deletion by account instead of by person.", {})],
    [("Tracing tool: ", {"bold": True, "color": NAVY}),
     ("our artifact manifest lists every model still containing the person — including the account reference, because friends’ photos remain.", {})],
], size=18, h=1828800)

# A6 · experiment 2
a6 = appendix_slide("A6", "Experiment 2: What Deletion Costs (SISA)",
                    "Q: does sharding make deletion cheap once the whole chain is rebuilt — and what does it cost in accuracy?")
flow(a6, L, TOP, W, 1188720, [
    ("Five designs", "One ResNet-50 · ResNet-18 with 1 (control), 4, 8, 16 shards. Users split by person; public pool not sharded."),
    ("20 requests", "Group 0, one person at a time, cumulative, whole-person deletion. Seed 1, single RTX 4090."),
    ("Two costs", "Model only: retrain affected model/shard. Whole chain: + re-distil student, rebuild gallery, re-quantise."),
    ("Utility", "1:N top-1 for remaining users in a 1,000-person gallery, before and after the 20 deletions."),
], size=15)
y6 = TOP + 1463040
table(a6, L, y6, W, [
    ("Design", "Model only (s)", "vs. 1 shard", "Whole chain (s)", "of which student (s)", "Top-1 before", "Top-1 after"),
    ("One big model (ResNet-50)", "109.4", "—", "186.4", "69.4", "58.0%", "57.2%"),
    ("1 shard (ResNet-18, control)", "65.0", "1×", "143.2", "68.9", "43.0%", "43.3%"),
    ("4 shards", "18.8", "3.5×", "99.0", "70.5", "32.3%", "31.2%"),
    ("8 shards", "12.2", "5.3×", "115.3", "93.0", "28.7%", "28.3%"),
    ("16 shards", "8.3", "7.8×", "166.8", "147.2", "25.2%", "25.7%"),
], [2.0, 1.1, 0.9, 1.1, 1.2, 1.0, 1.0], row_h=594360, size=18,
    accent={(5, 3), (5, 4), (5, 5), (5, 6)}, strong={(5, 1), (5, 2), (3, 3)})
note(a6, y6 + 3749040, [
    [("Over 20 requests: ", {"bold": True, "color": NAVY}),
     ("model-only cost 2,189 s (big model) vs. 166 s (16 shards) = −92%; whole chain 3,728 s vs. 3,336 s = only −11%.", {})],
    [("Why the chain gets dearer: ", {"bold": True, "color": NAVY}),
     ("distillation runs every teacher shard on every image — 16 shards, 16 passes.", {})],
    [("Two separate accuracy costs: ", {"bold": True, "color": NAVY}),
     ("smaller backbone −15 points (58 → 43); sharding −18 more (43 → 25). Deleting 20 people moves accuracy by ≤ 1.1 points.", {})],
], size=18, h=1645920)

# A7 · experiment 3 design
a7 = appendix_slide("A7", "Experiment 3: Design",
                    "Q: does passing one test mean the person is forgotten? Every test compares with the never-trained reference.")
hw = 8686800
label(a7, L, TOP, hw, "SIX DELETION METHODS · SETTINGS FROZEN BEFORE THE RUN")
table(a7, L, TOP + 411480, hw, [
    ("Method", "What it does", "Settings"),
    ("Output filter", "Weights untouched; the 20 names are blocked at the output", "—"),
    ("Fine-tune on the rest", "Keep training on remaining data only", "5 epochs, lr 0.01"),
    ("NegGrad+", "Learn the rest (0.99) + push away from the forget set (0.01)", "3 epochs, lr 0.01"),
    ("SCRUB", "Student stays close on the rest, moves away on the forget set", "3 epochs (1 “away”), α 0.1, T 4"),
    ("Full retrain", "Drop their photos, rerun stage 2 from the public base", "As the main model"),
    ("SISA retrain", "4 shards, retrain shards containing them (all 4 here)", "ResNet-18, own reference"),
], [1.3, 2.9, 1.5], row_h=640080, size=16, head_size=16, left_cols={1})
rx = L + hw + 365760
rw = R - rx
label(a7, rx, TOP, rw, "FIVE TESTS · DELETED MINUS REFERENCE")
table(a7, rx, TOP + 411480, rw, [
    ("Test", "Question / measure"),
    ("L1 output", "Can it still name them? Share of audit photos named correctly"),
    ("L2 membership", "Can an attacker tell they were trained on? Leakage (all cells); full U-LiRA (spot-check)"),
    ("L3 compression", "Repeat L1, L2 after INT8 and INT4 weight quantisation"),
    ("L4 relearning", "5 photos each, 50 steps, L1 every 10 steps; area under curve. Filter switched off"),
    ("L5 marker", "Marker on 20% of their training photos, labelled as a public person. Does it still fire?"),
], [1.0, 3.0], row_h=640080, size=16, head_size=16, left_cols={1})
note(a7, 7406640, [
    [("Scale: ", {"bold": True, "color": NAVY}),
     ("6 methods × 3 groups × 3 seeds = 54 cells. 90% intervals by person (U-LiRA by photo).", {})],
    [("Deviation: ", {"bold": True, "color": NAVY}),
     ("to meet the deadline the main L2 uses the simplified leakage (config celeba_v1_exp03_lite: shadow models 8 → 0). "
      "Full U-LiRA with the frozen config was run on 2 cells as spot-check and control (A8).", {})],
    [("Reference: ", {"bold": True, "color": NAVY}),
     ("never-trained model names none of them (L1 = 0) and ignores the marker (L5 = 0); SISA is compared with its own sharded reference.", {})],
], size=17, h=2011680)

# A8 · experiment 3 results
a8 = appendix_slide("A8", "Experiment 3: Full Results",
                    "Mean over 9 cells (3 groups × 3 seeds). L1, L4, L5: deleted minus reference. L2: leakage. Before deletion the main model named 74%.")
ok, bad = set(), set()
rows8 = [("Method", "L1 name", "L2 member", "L3 INT8 (L1/L2)", "L3 INT4 (L1/L2)", "L4 relearn", "L5 marker", "Seconds"),
         ("Output filter", "0.00 ✓", "0.44 ✗", "0.00 / ✗", "0.00 / ✗", "+0.21 ✗", "1.00 ✗", "0.003"),
         ("Fine-tune", "0.66 ✗", "0.36 ✗", "0.67 / 0.36 ✗", "0.60 / 0.25 ✗", "+0.20 ✗", "1.00 ✗", "65.6"),
         ("NegGrad+", "0.62 ✗", "0.39 ✗", "0.62 / 0.39 ✗", "0.56 / 0.31 ✗", "+0.18 ✗", "0.00 ✓", "62.0"),
         ("SCRUB", "0.64 ✗", "0.34 ✗", "0.64 / 0.33 ✗", "0.57 / 0.26 ✗", "+0.21 ✗", "0.00 ✓", "67.6"),
         ("Full retrain", "0.00 ✓", "0.01 ✓", "0.00 / 0.01 ✓", "0.00 / 0.03 ✓", "−0.00 ✓", "0.00 ✓", "114.1"),
         ("SISA retrain", "0.00 ✓", "0.02 ✓", "0.00 / 0.02 ✓", "0.00 / 0.03 ✓", "n/a", "n/a", "78.3")]
for r, row in enumerate(rows8[1:], 1):
    for c, v in enumerate(row):
        if "✗" in v:
            bad.add((r, c))
        elif "✓" in v:
            ok.add((r, c))
table(a8, L, TOP, W, rows8, [1.4, 0.9, 1.0, 1.3, 1.3, 1.0, 1.0, 0.8], row_h=457200, size=16,
      accent=bad, strong=ok)
yb = TOP + 457200 * 7 + 274320
cw = (W - 2 * 274320) // 3
xs8 = [L + i * (cw + 274320) for i in range(3)]
box(a8, xs8[0], yb, cw, 3017520)
label(a8, xs8[0] + 228600, yb + 137160, cw - 457200, "L1 · HOW MUCH WAS FORGOTTEN", size=15)
table(a8, xs8[0] + 228600, yb + 502920, cw - 457200, [
    ("", "Named", "Forgot"),
    ("Before deletion", "74%", "—"),
    ("Fine-tune", "66%", "≈ 10%"),
    ("NegGrad+", "62%", "≈ 16%"),
    ("SCRUB", "64%", "≈ 13%"),
], [1.4, 0.8, 0.8], row_h=420624, size=14, head_size=14, accent={(2, 2), (3, 2), (4, 2)})
box(a8, xs8[1], yb, cw, 3017520)
label(a8, xs8[1] + 228600, yb + 137160, cw - 457200, "L2 · FULL U-LIRA (GROUP 0, SEED 1)", size=15)
table(a8, xs8[1] + 228600, yb + 502920, cw - 457200, [
    ("", "NegGrad+", "Retrain"),
    ("AUC", "0.952", "0.509"),
    ("AUC − 0.5", "0.452", "0.009"),
    ("Accuracy", "87%", "51%"),
    ("Verdict (± 0.05)", "fail", "pass"),
], [1.3, 0.9, 0.9], row_h=420624, size=14, head_size=14, accent={(1, 1), (4, 1)}, strong={(1, 2), (4, 2)})
text(a8, xs8[1] + 228600, yb + 2667000 - 91440, cw - 457200, 365760,
     "8 + 8 shadow models; same 411 deleted photos. Control shows no false alarms.", size=13, color=SLATE, italic=True)
box(a8, xs8[2], yb, cw, 3017520)
label(a8, xs8[2] + 228600, yb + 137160, cw - 457200, "KEY READINGS", size=15)
text(a8, xs8[2] + 228600, yb + 548640, cw - 457200, 2377440, [
    [("Two shortcuts, two different passes: ", {"bold": True, "color": NAVY}), ("filter passes only L1; NegGrad+/SCRUB pass only L5.", {})],
    [("Marker ≠ identity: ", {"bold": True, "color": NAVY}), ("the marker lives on the forget photos and is erased first; identity is spread over all photos.", {})],
    [("Compression: ", {"bold": True, "color": NAVY}), ("no recovery — nothing was forgotten to recover.", {})],
], size=14, spacing=4)

# A9 · experiment 4
a9 = appendix_slide("A9", "Experiment 4: Four Systems, Weakest Link",
                    "Q: is the whole system as strong as its weakest link, or the average of its parts?")
table(a9, L, TOP, W, [
    ("System", "Main model", "Face gallery", "Student", "Phone copy", "Weak link"),
    ("A", "untouched", "untouched", "untouched", "untouched", "T: only photos deleted"),
    ("B", "exact retrain", "old gallery kept", "old student", "from new model", "T: gallery & student missed"),
    ("C", "NegGrad+ (approximate)", "they are removed", "re-distilled", "from new model", "M: method can’t prove it"),
    ("D", "exact retrain", "they are removed", "re-distilled", "from new model", "none: everything done"),
], [0.6, 1.4, 1.3, 1.1, 1.2, 1.9], row_h=502920, size=17, accent={(2, 2), (3, 1)})
y9 = TOP + 502920 * 5 + 274320
table(a9, L, y9, W, [
    ("Leakage · groups 0 / 1 / 2", "A", "B", "C", "D"),
    ("Face gallery", "1 / 1 / 1", "1 / 1 / 1", "0 / 0 / 0", "0 / 0 / 0"),
    ("Main model", "0.50 / 0.42 / 0.46", "0.01 / 0 / 0", "0.49 / 0.37 / 0.35", "0.01 / 0 / 0"),
    ("Student", "0.04 / 0.06 / 0.02", "0.04 / 0.06 / 0.02", "0.06 / 0.19 / 0", "0 / 0 / 0"),
    ("Phone copy", "0.49 / 0.42 / 0.46", "0.01 / 0 / 0", "0.49 / 0.37 / 0.35", "0.01 / 0 / 0"),
    ("Whole system (max)", "1.00", "1.00", "0.49 / 0.37 / 0.35", "0.01 / 0 / 0"),
    ("Mean of nodes (contrast)", "0.49", "0.26", "0.22", "0.001"),
], [1.6, 1.3, 1.3, 1.3, 1.3], row_h=502920, size=17,
    accent={(1, 1), (1, 2), (2, 1), (2, 3), (4, 1), (4, 3), (5, 1), (5, 2), (5, 3)}, strong={(5, 4)}, muted_rows={6})
note(a9, y9 + 502920 * 7 + 182880, [
    [("The evidence: ", {"bold": True, "color": NAVY}),
     ("“max” is a definition. What the run shows is that fixing non-weakest parts changes nothing (B: two nodes 0.5 → 0, total still 1.00) "
      "and only fixing the weakest one moves the total (C, D).", {})],
    [("C matches Experiment 3: ", {"bold": True, "color": NAVY}),
     ("same NegGrad+, main-model leakage ≈ 0.44 / 0.37 / 0.35 there. Group 1’s student (0.19) inherited the residue from its teacher.", {})],
    [("D: ", {"bold": True, "color": NAVY}),
     ("10 of 12 nodes pass; 2 sit exactly at 0.10 upper bound (uncertain). The yardstick reads 0 when everything is done.", {})],
], size=15, h=1371600)

# A10 · experiment 4b
a10 = appendix_slide("A10", "Experiment 4b: How Precise Must Tracing Be?",
                     "Start from system D, randomly leave some photos of each person in the training set, then retrain and rebuild everything.")
flow(a10, L, TOP, W, 1097280, [
    ("Miss r% of photos", "r = 0, 5, 20, 40% of each person’s ≈ 20 training photos. Nested: 40% includes the 20% set."),
    ("Rebuild everything", "Exact retrain on the rest; gallery always cleaned; student and phone copy regenerated."),
    ("Measure", "Whole-system leakage on audit photos (not the missed ones), 3 groups × 3 seeds."),
], size=15)
y10 = TOP + 1371600
table(a10, L, y10, W, [
    ("Missed", "Photos per person", "Group 0", "Group 1", "Group 2", "Mean"),
    ("0% (= D)", "0", "0.01 · uncertain", "0.00 · pass", "0.00 · pass", "0.003"),
    ("5%", "≈ 1", "0.04 (0.01–0.15) · uncertain", "0.00 · pass", "0.00 · pass", "0.01"),
    ("20%", "≈ 4", "0.14 (0.09–0.26) · uncertain", "0.01 (0.00–0.12) · uncertain", "0.00 (0.00–0.10) · uncertain", "0.05"),
    ("40%", "≈ 8", "0.21 (0.15–0.35) · fail", "0.14 (0.07–0.28) · uncertain", "0.21 (0.15–0.34) · fail", "0.19"),
], [0.9, 1.1, 1.9, 1.9, 1.9, 0.8], row_h=685800, size=18, accent={(4, 2), (4, 4), (4, 5)})
note(a10, y10 + 685800 * 5 + 365760, [
    [("Shape: ", {"bold": True, "color": NAVY}),
     ("flat, then steep — the threshold lies between ≈ 4 and ≈ 8 photos per person. (We had expected the opposite shape; the planned line “missing 5% brought it back” is not true.)", {})],
    [("Matches Experiment 1b: ", {"bold": True, "color": NAVY}),
     ("account deletion misses friends’ ≈ 39% → 0.16; random 40% → 0.19. What matters is how much is missed, not which photos.", {})],
], size=18, h=1645920)

# A11 · limits
a11 = appendix_slide("A11", "Limits and Deviations",
                     "What these numbers can and cannot support.")
table(a11, L, TOP, W, [
    ("Area", "Limit", "Effect on the claims"),
    ("Scale", "20 people per group, 3 groups, 3 seeds; 1,000 identities; Experiment 2 on 1 seed", "Wide intervals → many “uncertain”; Exp 2 accuracy has no interval"),
    ("Scores", "Node score is a diagnostic (audit vs. enrolment prototype), not a full attack", "Full U-LiRA on 2 cells agrees (NegGrad+ 0.95, retrain 0.51)"),
    ("Exp 3 config", "Main L2 uses the lite config (no shadow models); 2 server patches not in the recorded commit", "Documented in docs/exp03_analysis.md; conclusions match the spot-check"),
    ("Approximate methods", "One frozen setting each, not tuned", "Claim is “not forgotten at these settings” — and only a test can tell"),
    ("Compression", "Weight-only rounding, no calibration; nothing was forgotten to recover", "Language-model recovery effect remains open for faces"),
    ("Gallery 1.0 / 0", "Structural: record present or absent", "Shows records persist; needs no statistics"),
    ("“Max” rule", "A definition (attacker uses the weakest copy)", "Evidence is that fixing other parts doesn’t move it"),
    ("External", "No LFW; CelebA celebrities; not Ever’s system", "Shows where the structure breaks, not how Ever would score"),
], [1.1, 3.0, 2.8], row_h=777240, size=17, head_size=18, left_cols={1, 2})

# ---------------------------------------------------------------- order: new mini-Ever slide after slide 4
ids = [sl.slide_id for sl in prs.slides]
move_slide(prs, ids.index(n5.slide_id), 4)
for concept, result in ((dC, S[5]), (mC, S[6])):  # concept slide right before its results slide
    ids = [sl.slide_id for sl in prs.slides]
    move_slide(prs, ids.index(concept.slide_id), ids.index(result.slide_id))
prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides))
