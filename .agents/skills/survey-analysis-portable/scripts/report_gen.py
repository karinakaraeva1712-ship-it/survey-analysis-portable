#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_gen.py — dependency-free base HTML report from survey.json + results.json.

Usage:
  python report_gen.py --survey survey.json --results results.json --out report.html
                       [--title "Title"] [--outcome-label "label"]

Output: one self-contained HTML file. Charts are pure-CSS bars (no JS libraries,
no network, renders in any browser/webview). This is the BASE skeleton: the AI
customizes a copy — narrative, translations (QTRAN/TRANSL), quotes, hypotheses,
recommendations — and re-runs. All numbers come from the data files.
"""
import argparse
import json
import re
import statistics
from collections import Counter

# --- translations: AI fills these for the report language (EN default).
# Key = RU source text (option label / question text), value = report-language text.
QTRAN = {}
TRANSL = {}

def tr(text):
    t = str(text).strip()
    if t in TRANSL:
        return TRANSL[t]
    for k, v in TRANSL.items():
        if k.strip() == t:
            return v
    return t

def shorten(label, n=38):
    if len(label) <= n:
        return label
    cut = label[: n - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "…"

def load(path):
    return json.load(open(path, encoding="utf-8"))

def pct(x, base):
    return round(100.0 * x / base, 1) if base else 0

def flag_rate(rows, code, outcome):
    base = [r for r in rows if r.get(code) is not None]
    n1 = sum(1 for r in base if r.get(code) == 1)
    if n1 == 0 or n1 == len(base):
        return None
    r1 = 100.0 * sum(1 for r in base if r.get(code) == 1 and r.get(outcome) == 1) / n1
    r0 = 100.0 * sum(1 for r in base if r.get(code) == 0 and r.get(outcome) == 1) / (len(base) - n1)
    return {"base": len(base), "n1": n1, "with": round(r1, 1), "without": round(r0, 1)}

CSS = """
:root{--blue:#1f5fea;--ink:#101828;--mut:#5b6472;--line:#e5e9f2;--bg:#f6f8fc}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.55}
.sidebar{position:fixed;top:0;left:0;bottom:0;width:240px;background:#0e1a33;color:#c9d4ea;padding:20px 14px;overflow-y:auto}
.sidebar a{display:block;color:#aebcda;font-size:12.5px;padding:6px 10px;border-radius:8px;text-decoration:none}
.sidebar a:hover{background:#1c335c;color:#fff}
.main{margin-left:240px;padding-bottom:60px}
.hero{background:linear-gradient(135deg,#101828,#1c335c 60%,#2b4a8f);color:#fff;padding:48px 44px 36px}
.hero h1{font-size:28px;margin:0 0 12px;max-width:820px}
.hero p.lead{color:#c9d4ea;font-size:15px;max-width:760px;margin:0}
.hero .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:26px}
.hero .stat{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:14px;padding:14px 16px}
.hero .stat-val{color:#fff;font-size:24px;font-weight:800}
.hero .stat-label{font-size:12px;color:#c9d4ea;margin-top:4px}
.section{max-width:1080px;margin:0 auto;padding:40px 44px 8px}
.section h2{font-size:21px;margin:0 0 10px}
.section h3{font-size:15.5px;margin:24px 0 8px}
.muted{color:var(--mut);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:16px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.card h4{margin:0 0 6px;font-size:14px}
.card p{font-size:12.5px;color:var(--mut);margin:0}
.chart-card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 20px;margin:14px 0}
.chart-card .title{font-size:14px;font-weight:700}
.chart-card .base{font-size:11.5px;color:var(--mut);margin:2px 0 12px}
.bar-row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:12.5px}
.bar-row .lab{width:34%;text-align:right;color:#39424f;font-weight:600}
.bar-row .track{flex:1;background:#eef1f7;border-radius:6px;height:14px;overflow:hidden}
.bar-row .fill{height:100%;background:var(--blue);border-radius:6px}
.bar-row .val{width:70px;font-variant-numeric:tabular-nums}
.donut-row{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.donut{width:150px;height:150px;border-radius:50%;position:relative}
.legend{font-size:12.5px}
.legend .li{display:flex;align-items:center;gap:8px;margin:4px 0}
.legend .sw{width:12px;height:12px;border-radius:3px}
.decision-note{font-size:12.5px;color:var(--mut);background:#f2f6ff;border-left:3px solid var(--blue);padding:8px 12px;border-radius:0 8px 8px 0;margin-top:12px}
.sowhat{background:#eefaf4;border:1px solid #c9f0dd;border-radius:12px;padding:14px 16px;margin:18px 0;font-size:13.5px}
.sowhat b{color:#067647}
.quote{background:#fff;border:1px solid var(--line);border-left:4px solid #b9c7e8;border-radius:10px;padding:12px 16px;margin:10px 0}
.quote p{margin:0;font-size:13.5px}
.quote .who{font-size:11px;color:var(--mut);margin-top:6px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;font-size:13px;margin:14px 0}
th,td{border-bottom:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
th{background:#f2f6ff;font-size:11.5px;text-transform:uppercase;color:#3c4a6b}
details{background:#fff;border:1px solid var(--line);border-radius:12px;margin:10px 0;padding:8px 16px}
details summary{cursor:pointer;font-size:13.5px;font-weight:600;padding:8px 0}
.footer{max-width:1080px;margin:26px auto;padding:0 44px;color:var(--mut);font-size:12px}
@media(max-width:900px){.sidebar{display:none}.main{margin-left:0}.hero{padding:32px 20px}.hero .stats{grid-template-columns:repeat(2,1fr)}.section{padding:26px 18px}.cards{grid-template-columns:1fr}}
"""

def bar_rows(opts, base, color="#1f5fea"):
    mx = max((o["count"] for o in opts), default=1)
    html = []
    for o in opts:
        w = 100.0 * o["count"] / mx
        html.append(
            '<div class="bar-row"><div class="lab">%s</div>'
            '<div class="track"><div class="fill" style="width:%s%%;background:%s"></div></div>'
            '<div class="val">%s · %s%%</div></div>'
            % (shorten(tr(o["label"]), 34), round(w, 1), color, o["count"], o["pct"]))
    return "\n".join(html)

def donut(labels, values, colors):
    total = sum(values)
    pctv = [100.0 * v / total for v in values] if total else []
    segs = []
    acc = 0.0
    for v, c in zip(pctv, colors):
        segs.append("%s %s%% %s%%" % (c, round(acc, 2), round(acc + v, 2)))
        acc += v
    leg = "".join(
        '<div class="li"><span class="sw" style="background:%s"></span>%s — %s (%s%%)</div>'
        % (c, lab, val, pct(val, total))
        for lab, val, c in zip(labels, values, colors))
    return ('<div class="donut-row"><div class="donut" style="background:conic-gradient(%s)"></div>'
            '<div class="legend">%s</div></div>' % (",".join(segs), leg))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--survey", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="report.html")
    ap.add_argument("--title", default="Survey report")
    ap.add_argument("--outcome-label", default="outcome")
    args = ap.parse_args()

    sv = load(args.survey)
    res = load(args.results)
    rows = sv["data"]
    questions = sv["questions"]
    options = sv["options"]
    n = res["n"]
    outcome = res.get("outcome")
    rate = res["segments"].get("outcome_rate") if res.get("segments") else None
    meta = res.get("meta", {})
    med_s = meta.get("completion_s_median")
    med_min = round(med_s / 60) if med_s else None

    # hero stats
    hero = [("n=%d" % n, "completed interviews"),
            ("%s%%" % rate, args.outcome_label) if rate is not None else ("—", args.outcome_label),
            ("%d" % len(res["questions"]), "questions analysed"),
            ("~%s min" % med_min, "median completion") if med_min else ("—", "median completion")]

    # methodology cards
    dev = Counter(str(r.get("meta_4")) for r in rows)
    sex = Counter(str(r.get("Q_2")) for r in rows if r.get("Q_2"))
    osd = Counter(str(r.get("meta_5")) for r in rows)
    met_html = []
    if sex:
        met_html.append(donut([tr(k) for k, v in sex.most_common()], [v for _, v in sex.most_common()],
                              ["#2563eb", "#93c5fd"]))
    if dev:
        met_html.append(donut([tr(k) for k, v in dev.most_common()], [v for _, v in dev.most_common()],
                              ["#1f5fea", "#93c5fd", "#cbd5e1"]))
    if osd:
        met_html.append(donut([tr(k) for k, v in osd.most_common()], [v for _, v in osd.most_common()],
                              ["#1f5fea", "#60a5fa", "#93c5fd", "#cbd5e1", "#94a3b8", "#a8b8d0"]))
    methodology = '<div class="cards">%s</div><div class="cards">%s</div>' % (
        '<div class="card"><h4>Sample</h4><p>n=%d; devices, OS and sex computed from metadata.</p></div>' % n,
        '<div class="card"><h4>Outcome</h4><p>%s%s. Correlations use this flag; bases follow routing.</p></div>'
        % (outcome or "—", (" (%.1f%%)" % rate) if rate is not None else ""))
    if met_html:
        methodology += '<div class="cards">%s</div>' % "".join(
            '<div class="chart-card">%s</div>' % h for h in met_html)

    # per-question charts
    q_html = []
    for q in sorted(questions.keys()):
        it = res["questions"][q]
        title = QTRAN.get(q, tr(it["text"]))
        if it["type"] == "Open text":
            body = '<div class="muted">n=%d · free-text answers (see Open answers).</div>' % it["n"]
        else:
            opts = sorted(it["options"], key=lambda d: -(d.get("count") or 0))
            opts = [o for o in opts if not str(o["label"]).strip().endswith("(text)")]
            if it["type"] == "Multiple select":
                opts = opts[:8]
            else:
                opts = opts[:8]
            body = bar_rows(opts, it["n"])
        q_html.append('<div class="chart-card"><div class="title">%s</div>'
                      '<div class="base">%s · n=%d · %s</div>%s</div>'
                      % (title, shorten(tr(it["text"]), 90), it["n"], it["type"], body))
    questions_html = "\n".join(q_html)

    # correlations
    corr_rows = []
    for c in sorted(res["correlations"].get("with_outcome", []), key=lambda x: -abs(x["r"]))[:15]:
        fr = flag_rate(rows, c["code"], outcome)
        if fr:
            corr_rows.append("<tr><td>%s</td><td>%+.3f</td><td>%.4f</td>"
                             "<td>%s%%</td><td>%s%%</td></tr>"
                             % (shorten(tr(c["label"]), 60), c["r"], c["p"], fr["with"], fr["without"]))
    cr_rows = "".join("<tr><td>%s</td><td>%+.3f</td><td>%.4f</td></tr>"
                      % (shorten(QTRAN.get(c["q"], tr(c["label"])), 60), c["v"], c["p"])
                      for c in sorted(res["correlations"].get("cramers", []), key=lambda x: -x["v"]))
    correlations = (
        '<h3>Flags vs outcome</h3><p class="muted">r — point-biserial; with/without — outcome rate among respondents '
        'with/without the flag (base = respondents of that question only).</p>'
        '<table><tr><th>Factor</th><th>r</th><th>p</th><th>outcome with</th><th>outcome without</th></tr>%s</table>'
        % ("".join(corr_rows)))
    if cr_rows:
        correlations += ('<h3>Cramér\'s V (single-select vs outcome)</h3>'
                         '<table><tr><th>Question</th><th>V</th><th>p</th></tr>%s</table>' % cr_rows)

    # segments: outcome rate by single-select value
    seg_html = []
    for q, items in res["correlations"].get("choice_by_outcome", {}).items():
        rows_h = "".join("<tr><td>%s</td><td>%d</td><td>%s%%</td></tr>"
                         % (shorten(tr(v["value"]), 60), v["n"], v["rate"]) for v in items)
        seg_html.append('<details><summary>%s — outcome rate by value</summary>'
                        '<table><tr><th>Value</th><th>n</th><th>Outcome rate</th></tr>%s</table></details>'
                        % (QTRAN.get(q, tr(questions[q]["text"])), rows_h))
    segments = "\n".join(seg_html) if seg_html else '<p class="muted">No outcome provided.</p>'

    # open answers
    open_html = []
    for q, items in res.get("open", {}).items():
        texts = "".join("<li>%s</li>" % (str(it.get("text"))[:400]) for it in items[:50])
        open_html.append('<details><summary>%s — n=%d</summary><ul>%s</ul></details>'
                         % (QTRAN.get(q, tr(questions[q]["text"])), len(items), texts))
    open_section = "\n".join(open_html)

    # appendix
    app_html = []
    for q in sorted(questions.keys()):
        it = res["questions"][q]
        if it["type"] == "Open text":
            inner = '<div class="muted">n=%d free-text answers</div>' % it["n"]
        else:
            opts = sorted(it["options"], key=lambda d: -(d.get("count") or 0))
            inner = bar_rows(opts, it["n"])
        app_html.append('<details><summary>%s — n=%d</summary>%s</details>'
                        % (QTRAN.get(q, tr(it["text"])), it["n"], inner))
    appendix = "\n".join(app_html)

    nav_items = [("cover", "Cover"), ("method", "Methodology"), ("questions", "Questions"),
                 ("corr", "Correlations"), ("segments", "Segments"), ("open", "Open answers"),
                 ("appendix", "Appendix")]
    nav = "".join('<a href="#%s">%s</a>' % i for i in nav_items)

    html = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title><style>%(css)s</style></head>
<body>
<nav class="sidebar">%(nav)s</nav>
<div class="main">
<div class="hero" id="cover"><h1>%(title)s</h1>
<p class="lead">Base report generated by survey-analysis-portable. The AI adds findings, quotes, hypotheses and recommendations.</p>
<div class="stats">%(hero)s</div></div>
<section class="section" id="method"><h2>Methodology &amp; sample</h2>%(methodology)s</section>
<section class="section" id="questions"><h2>Question distributions</h2>%(questions_html)s</section>
<section class="section" id="corr"><h2>Correlations</h2>%(correlations)s</section>
<section class="section" id="segments"><h2>Segments</h2>%(segments)s</section>
<section class="section" id="open"><h2>Open answers</h2>%(open_section)s</section>
<section class="section" id="appendix"><h2>Appendix</h2>%(appendix)s</section>
<div class="footer">Numbers computed from the survey export; quotes are verbatim.</div>
</div></body></html>""" % {
        "title": args.title, "css": CSS, "nav": nav,
        "hero": "".join('<div class="stat"><div class="stat-val">%s</div><div class="stat-label">%s</div></div>'
                        % (v, l) for v, l in hero),
        "methodology": methodology, "questions_html": questions_html,
        "correlations": correlations, "segments": segments,
        "open_section": open_section, "appendix": appendix,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote %s (%d bytes)" % (args.out, len(html)))


if __name__ == "__main__":
    main()
