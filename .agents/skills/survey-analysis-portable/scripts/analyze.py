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
