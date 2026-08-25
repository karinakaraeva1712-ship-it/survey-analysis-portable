---
name: survey-analysis-portable
description: Создание аналитического отчёта по выгрузке опроса (xlsx): парсинг, распределения, корреляции, кросс-сегменты, открытые ответы, HTML-отчёт. Работает в любом ИИ — ChatGPT/GPTs, Claude Code, Cursor,程小帮. / Build an analytical report from a survey export (.xlsx): parsing, distributions, correlations, cross-segments, open answers, HTML report. Works in any AI — ChatGPT/GPTs, Claude Code, Cursor, Chengxiaobang.
---

# Analytical survey report — portable skill (survey-analysis-portable)

> The same skill works across different AIs because it **does not depend on any platform's skill loader**:
> it is a self-contained document with instructions and embedded scripts. Any LLM follows it once it receives
> this text (pasted into Instructions, attached to a project, installed as a skill, added to `.cursor/rules`, etc.).

## Execution (most important — don't ask, act)

- **Never ask clarifying questions or offer options.** Don't ask "full report or audit first?", "which language?", "what format?" — start right away.
- **By default run the full pipeline** (see "Workflow" for your environment) and deliver a ready HTML report in English (Russian only if explicitly requested).
- Receiving an xlsx together with this skill text is already an instruction to start: step 1 — read the export, step 2 — execute.
- Data-quality notes, sample limitations and ambiguous questions go **inside the report** ("Sample limitation" section), not into the chat.
- The only case where you may stop and ask — the file cannot be read at all (corrupted, wrong format, no data). Everything else is execution.
- In ChatGPT / code interpreter use Path B right away: run the scripts inline (install openpyxl/pandas/scipy via pip if missing). Skip shell/Chrome steps silently.
- At the end, write one short line in the chat about what you did and which checks passed.

## How to load in different AIs

- **Chengxiaobang / Claude Code / Cursor (agent systems):** install the `.agents/skills/survey-analysis-portable/` folder as a skill (frontmatter is recognized). Scripts are already in `scripts/`.
- **ChatGPT / GPTs / Projects:** paste the body of `survey-analysis-portable.md` (the bundle, scripts inside) into a custom GPT's Instructions, or attach it to a project and write "follow this skill". ChatGPT ignores the YAML frontmatter — that's fine.
- **Any other AI:** attach the file or text and ask it to follow the instructions.

## Input

1. Survey export xlsx (format: first row is the header; columns look like `2. Choice – text`, `5. Choice – question: option`, `17. Question – text`; multi-select values are `TRUE`/`FALSE`). If the format differs — adapt the parser, keeping the output contract.
2. Questionnaire design (optional) — for meaning and routing.
3. Example report (optional) — style reference.

## Detect the environment (pick a path)

- **Path A — shell available** (terminal, uv/python, chrome): full pipeline, see "Workflow A".
- **Path B — Python only** (ChatGPT code interpreter, Jupyter): run the scripts inline; if packages are missing — `pip install openpyxl pandas scipy`; skip the shell/Chrome steps.
- **Path C — no code execution:** read the export directly, compute distributions and correlations yourself, deliver the report as text/Markdown/HTML in the answer. The design and verification rules below apply the same.

## Workflow A (shell)

1. Save the scripts from `scripts/` (parse_survey.py, analyze.py, report_gen.py) into a working folder.
2. Parse:
   ```bash
   uv run --with openpyxl python parse_survey.py <export.xlsx> survey.json
   ```
   Contract: `{n, meta_columns, questions, options, scale_map, header, data}`.
3. Study the questionnaire design: routing (question bases are computed from data), question types, segments.
4. Analyze:
   ```bash
   uv run --with scipy python analyze.py survey.json --outcome <Q_N_X> --out results.json
   ```
   `--outcome` — code of the key outcome flag (e.g., a "used the product" flag). Result: distributions, correlations (r, phi, Cramér's V), outcome rate by segment, open answers with respondent IDs.
5. Build the report: run the base generator, then **edit its copy** — add narrative, translations (TRANSL), quotes, hypotheses, recommendations — and re-run:
   ```bash
   python report_gen.py --survey survey.json --results results.json --out report.html
   ```
   Report language — EN by default (RU on explicit request). Numbers — only from the data.
6. Verify and deliver: verbatim quotes (search the fragment in survey.json), tag balance, 0 Cyrillic in the EN version, labels ≤ 40 chars; headless Chrome render — if available (otherwise skip; the JS-free HTML opens everywhere). Declare the artifact.

## Report design (minimum required)

1. Cover: tags, title, 1-paragraph essence, 4 key metrics.
2. Key findings: 3 cards + P0/P1/P2 decision map + sample limitation.
3. Methodology & sample: n-cards, 2–3 charts (devices, segments), "how to read the evidence" (behavior > stated > claimed > concept).
4. Thematic sections (01…N): statistics → findings → quotes → "So what" block.
5. Correlations: result only — a compact table "Factor / what happens in practice / strength" (5–9 rows). Full tables go into a collapsed `<details>`.
6. Cross-segments: outcome rate by segment, grouped (high / medium / loss zones).
7. Open answers: theme cards (share bars) + "Strongest quotes" (verbatim, no duplicates in meaning).
8. Hypothesis check: table "Hypothesis / Strength / Product reading", verdicts by color: Confirmed — green, Partially — yellow, Rejected — red.
9. Recommendations: P0/P1/P2.
10. Appendix: every question in a `<details>` with a bar distribution.
11. Navigation — a left sticky sidebar only. No top tabs.
12. Under each chart — `<p class="decision-note"><b>How to read:</b> …` with numbers.
13. Each section ends with `<div class="sowhat"><b>So what</b> …`.

## Hard rules

- **Quotes verbatim** from the export: preserve typos and punctuation, don't "polish" the respondent's text. Verification — search the quote fragment in the data. Attribution (segment in the caption) — only if verified against that respondent's row; otherwise just write the question code.
- **Question bases** — routing gives different n; the base = rows where the respondent has a value in at least one column of the question. Shares are computed from the question base.
- **Flags are strings** (`"1"`/`"0"` or `TRUE`/`FALSE`); grid scales are stored as option IDs — without mapping, an "average of IDs" is meaningless.
- **Chart labels ≤ ~40 chars** (truncate at a word boundary with an ellipsis), the value goes into the label (`Label — 71%`), no more than 7 bars per chart.
- **0 Cyrillic in the EN version**, including the appendix; "Other[…]" branches collapse into "Other (free-text answers)".
- The final HTML must not contain raw literals like `{sowhat(` / `{quote_block(` — all section fragments are assembled with f-strings.
- Numbers in the report — only from the data, never from memory.

## Verification (degrades by environment)

- Verbatim quotes: `python -c` fragment search in `survey.json`.
- Tag balance: `<div>` opened = closed (regex over `<div[ >]` and `</div>`).
- 0 Cyrillic in EN: `grep -P '[а-яА-ЯёЁ]' report.html`.
- Labels: max length of lines containing "—" in chart data ≤ 40.
- Render (Path A only): `chrome --headless=new --screenshot …` — optional.

## Scripts

In the skill folder: `scripts/parse_survey.py`, `scripts/analyze.py`, `scripts/report_gen.py`.
They are also embedded in the single-file bundle `survey-analysis-portable.md` (for ChatGPT / attachments).
`report_gen.py` — base generator with no external dependencies (CSS bars instead of Chart.js): it produces the report skeleton; narrative, translations, quotes and hypotheses are added by the AI into a copy of the script.

## Tests

- Simple: "make a report from this survey" + xlsx → parser + analysis + HTML in any environment.
- Complex: + questionnaire design + example report → full report with segments and open-answer classification.
- Must not trigger: "write a sales report" without survey data.


---

# Embedded scripts (save into a working folder and run)

> For ChatGPT/GPTs/Projects: paste this whole file into Instructions or attach it to a project.
> For agent systems (Chengxiaobang/Claude Code/Cursor) use the .agents/skills/survey-analysis-portable/ folder.

## parse_survey.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse a survey export (xlsx) into survey.json.

Usage:
  uv run --with openpyxl python parse_survey.py <input.xlsx> [output.json]

Output contract:
  {n, meta_columns, questions, options, scale_map, header, data}

This export format (report sheet of the survey platform):
  - Header row is the FIRST row; first cell == 'Answer ID'.
  - Column headers embed the question structure:
      '2. Choice – <question text>'            single-select (value = option text)
      '2. Choice, other answers – <text>'      free-text 'other' of single-select
      '5. Choice – <question>: <option text>'  multiple-select flag column
      '17. Question – <question text>'         open-ended text question
  - Multi-select cells hold 'TRUE'/'FALSE' strings.
  - There are no dictionary rows and no grid/NPS questions in this export.
"""
import json
import re
import sys
from collections import Counter

from openpyxl import load_workbook

Q_RE = re.compile(r"^(\d+)\. (Choice|Question)(?:, other answers)? – (.*)$")


def s(v):
    if v is None:
        return None
    return str(v).strip()


def parse_question_code(header_text):
    """Classify one question column header."""
    m = Q_RE.match(header_text)
    if not m:
        return None
    num, kind, text = m.group(1), m.group(2), m.group(3)
    q = f"Q_{num}"
    if kind == "Question":
        return {"q": q, "type": "open", "text": text}
    if ", other answers" in header_text:
        return {"q": q, "type": "other", "text": text}
    if ": " in text:
        qtext, opt = text.split(": ", 1)
        return {"q": q, "type": "multi", "text": qtext, "opt": opt}
    return {"q": q, "type": "single", "text": text}


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: parse_survey.py <input.xlsx> [output.json]")
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "survey.json"

    wb = load_workbook(inp, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[0]

    meta_columns = []
    header = {}
    questions = {}
    options = {}
    multi_counter = Counter()
    single_raw = {}
    other_cols = {}

    for j, cell in enumerate(hdr):
        if cell is None or s(cell) == "":
            continue
        t = s(cell)
        if j < 13 or t == "Answer ID":
            meta_columns.append(t)
            header[j] = f"meta_{j}"
            continue
        info = parse_question_code(t)
        if info is None:
            meta_columns.append(t)
            header[j] = f"meta_{j}"
            continue
        q = info["q"]
        typ = info["type"]
        if typ == "open":
            header[j] = q
            questions[q] = {"type": "Open text", "text": info["text"]}
        elif typ == "multi":
            idx = multi_counter[q]
            code = f"{q}_{chr(ord('a') + idx)}"
            multi_counter[q] += 1
            header[j] = code
            options[code] = info["opt"]
            if q not in questions:
                questions[q] = {"type": "Multiple select", "text": info["text"]}
        elif typ == "single":
            header[j] = q
            questions[q] = {"type": "Single select", "text": info["text"]}
            single_raw[q] = code if False else q
        elif typ == "other":
            code = f"{q}_other"
            header[j] = code
            questions[q] = {"type": questions.get(q, {}).get("type", "Single select"),
                            "text": questions.get(q, {}).get("text", info["text"])}
            other_cols[q] = code

    data = []
    for r in rows[1:]:
        rec = {}
        for j, code in header.items():
            if j < len(r):
                v = r[j]
                if v is None:
                    continue
                if isinstance(v, str):
                    sv = v.strip()
                    if sv == "":
                        continue
                    if sv in ("TRUE", "FALSE"):
                        v = 1 if sv == "TRUE" else 0
                    else:
                        v = sv
                rec[code] = v
        if rec:
            data.append(rec)

    # synthetic one-hot flags for single-select questions (for correlation analysis);
    # only answered respondents get a flag (absent = question not routed to them)
    for q, code in single_raw.items():
        vals = Counter(r.get(code) for r in data if r.get(code) is not None)
        order = sorted(vals, key=lambda x: (-vals[x], x))
        for i, val in enumerate(order):
            flag_code = f"{q}_{chr(ord('a') + i)}"
            options[flag_code] = val
            for r in data:
                if r.get(code) is not None:
                    r[flag_code] = 1 if r.get(code) == val else 0

    result = {
        "n": len(data),
        "meta_columns": meta_columns,
        "questions": questions,
        "options": options,
        "scale_map": {},
        "header": {str(j): c for j, c in sorted(header.items())},
        "data": data,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"parsed: n={len(data)}, questions={len(questions)}, options={len(options)}, "
          f"multi_flag_cols={sum(multi_counter.values())}, "
          f"single_questions={len(single_raw)}, open={len([q for q,i in questions.items() if i['type']=='Open text'])}, "
          f"other_cols={len(other_cols)}, meta={len(meta_columns)}")


if __name__ == "__main__":
    main()
```

## analyze.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compute survey statistics and correlations from survey.json.

Usage:
  uv run --with pandas --with scipy python analyze.py <survey.json> [--outcome Q_8_g] [--out results.json]

--outcome: code of the key outcome flag (default Q_8_g = registered an on-site
shipment via Yandex Delivery at a pickup point in the last 3 months).
Output: results.json with distributions, correlations (point-biserial r, phi,
Cramer's V), outcome rate by segment (choice values), and open answers with
respondent IDs for verbatim quote attribution.
"""
import argparse
import json
import math
import re
from collections import Counter, defaultdict

from scipy import stats

FLAG_RE = re.compile(r"^Q_\d+_[a-z]$")
OTHER_RE = re.compile(r"^Q_\d+_other$")


def load(path):
    return json.load(open(path, encoding="utf-8"))


def pbis(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if isinstance(x, (int, float)) and isinstance(y, (int, float))]
    if len(pairs) < 20:
        return None, None, len(pairs)
    r = stats.pointbiserialr([p[0] for p in pairs], [p[1] for p in pairs])
    return float(r.statistic), float(r.pvalue), len(pairs)


def cramers_v(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 20:
        return None, None, len(pairs)
    ta = sorted(set(p[0] for p in pairs))
    tb = sorted(set(p[1] for p in pairs))
    tab = [[sum(1 for x, y in pairs if x == ai and y == bi) for bi in tb] for ai in ta]
    try:
        t = stats.chi2_contingency(tab)
    except ValueError:
        return None, None, len(pairs)
    k = min(len(tab), len(tab[0]) if tab else 0)
    if k <= 1:
        return None, None, len(pairs)
    return float(math.sqrt(t.statistic / (len(pairs) * (k - 1)))), float(t.pvalue), len(pairs)


def median(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return float(sorted(xs)[len(xs) // 2]) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("survey_json")
    ap.add_argument("--outcome", default="Q_8_g")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()

    sv = load(args.survey_json)
    rows = sv["data"]
    questions = sv["questions"]
    options = sv["options"]
    n = sv["n"]
    outcome = args.outcome

    flag_cols = sorted([c for c in options if FLAG_RE.match(c)])
    choice_cols = [q for q, m in questions.items() if m["type"] == "Single select"]
    open_cols = [q for q, m in questions.items() if m["type"] == "Open text"]
    other_cols = sorted({c for r in rows for c in r.keys() if OTHER_RE.match(c)})

    res = {"n": n, "outcome": outcome, "outcome_label": options.get(outcome, outcome),
           "questions": {}, "correlations": {}, "segments": {}, "open": {}, "meta": {}}

    # --- distributions per question ---
    for q, meta in questions.items():
        t = meta["type"]
        item = {"type": t, "text": meta["text"], "n": 0, "options": []}
        if t == "Multiple select":
            cols = [c for c in flag_cols if c.rsplit("_", 1)[0] == q]
            base = [r for r in rows if any(r.get(c) is not None for c in cols)]
            item["n"] = len(base)
            for c in cols:
                cnts = Counter(r.get(c) for r in base)
                item["options"].append({
                    "code": c, "label": options.get(c, c), "count": cnts.get(1, 0),
                    "pct": round(100 * cnts.get(1, 0) / len(base), 1) if base else None,
                })
        elif t == "Single select":
            raw_col = q
            base = [r for r in rows if r.get(raw_col) is not None]
            item["n"] = len(base)
            vals = Counter(r.get(raw_col) for r in base)
            for v, cnt in vals.most_common():
                item["options"].append({"code": None, "label": v, "count": cnt,
                                        "pct": round(100 * cnt / len(base), 1)})
        elif t == "Open text":
            base = [r for r in rows if r.get(q) is not None]
            item["n"] = len(base)
            res["open"][q] = [{"id": r.get("meta_0"), "text": r.get(q)} for r in base]
        res["questions"][q] = item

    # --- meta stats ---
    times = [r.get("meta_11") for r in rows]
    res["meta"]["completion_s_median"] = median(times)
    res["meta"]["device"] = Counter(r.get("meta_4") for r in rows)
    res["meta"]["os"] = Counter(r.get("meta_5") for r in rows)
    res["meta"]["browser"] = Counter(r.get("meta_6") for r in rows)
    res["meta"]["date"] = Counter(r.get("meta_12") for r in rows)
    res["meta"]["window"] = Counter(r.get("meta_7") for r in rows)

    # --- outcome correlations ---
    ok_rows = [r for r in rows if r.get(outcome) is not None]
    outcome_flag = [1 if r.get(outcome) == 1 else 0 for r in ok_rows]
    res["segments"] = {"base": len(ok_rows),
                       "outcome_rate": round(100 * sum(outcome_flag) / len(ok_rows), 1)}

    corr = {"with_outcome": [], "phi_pairs": [], "cramers": [], "choice_by_outcome": {}}
    for code in flag_cols:
        if code == outcome:
            continue
        vals = [r.get(code) for r in ok_rows]
        n1 = sum(1 for v in vals if v == 1)
        if n1 < 10 or n1 > len(ok_rows) - 10:
            continue
        r_, p_, nn = pbis(vals, outcome_flag)
        if r_ is not None:
            corr["with_outcome"].append({
                "code": code, "label": options.get(code, code), "r": round(r_, 3), "p": p_, "n_flag": n1,
                "out_rate_with": round(100 * sum(1 for v, o in zip(vals, outcome_flag) if v == 1 and o == 1) / n1, 1),
                "out_rate_without": round(100 * sum(1 for v, o in zip(vals, outcome_flag) if v == 0 and o == 1) / (len(ok_rows) - n1), 1),
            })

    # phi among frequent flags
    freq = {c: sum(1 for r in ok_rows if r.get(c) == 1) for c in flag_cols}
    top = [c for c in flag_cols if 20 <= freq.get(c, 0) <= len(ok_rows) - 20][:14]
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            a = [1 if r.get(top[i]) == 1 else 0 for r in ok_rows]
            b = [1 if r.get(top[j]) == 1 else 0 for r in ok_rows]
            n11 = sum(1 for x, y in zip(a, b) if x and y)
            if n11 < 15:
                continue
            try:
                t = stats.chi2_contingency([[n11, sum(a) - n11], [sum(b) - n11, len(a) - sum(a) - sum(b) + n11]])
            except ValueError:
                continue
            if t.pvalue < 0.05:
                corr["phi_pairs"].append({
                    "a": options.get(top[i], top[i]), "b": options.get(top[j], top[j]),
                    "phi": round(math.sqrt(t.statistic / len(a)), 3), "p": float(t.pvalue), "n11": n11,
                })

    # Cramer's V: single-select questions vs outcome
    for q in choice_cols:
        vals = [r.get(q) for r in ok_rows]
        cv, p_, nn = cramers_v(vals, outcome_flag)
        if cv is not None:
            corr["cramers"].append({"q": q, "label": questions.get(q, {}).get("text", q),
                                    "v": round(cv, 3), "p": p_})

    # outcome rate by choice value (cross-segment material)
    for q in choice_cols:
        rows_by_val = defaultdict(list)
        for r, o in zip(ok_rows, outcome_flag):
            v = r.get(q)
            if v is not None:
                rows_by_val[v].append(o)
        corr["choice_by_outcome"][q] = [
            {"value": v, "n": len(os_), "rate": round(100 * sum(os_) / len(os_), 1)}
            for v, os_ in rows_by_val.items()]

    res["correlations"] = corr
    res["segments"]["by_flag"] = sorted(corr["with_outcome"], key=lambda d: -abs(d["r"]))[:20]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    print(f"analyzed: n={n}, questions={len(res['questions'])}, open_q={len(res['open'])}")
    print(f"outcome={outcome} rate={res['segments']['outcome_rate']}% base={res['segments']['base']}")
    print(f"correlations: with_outcome={len(corr['with_outcome'])}, phi_pairs={len(corr['phi_pairs'])}, "
          f"cramers={len(corr['cramers'])}, choice_qs={len(corr['choice_by_outcome'])}")


if __name__ == "__main__":
    main()
```

## report_gen.py
```python
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
```
