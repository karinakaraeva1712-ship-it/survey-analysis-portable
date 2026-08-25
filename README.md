# survey-analysis-portable

A portable skill that turns a survey export (`.xlsx`) into a full analytical HTML report: distributions, correlations, cross-segments, open answers, hypotheses and recommendations — in one pass, in any AI.

Works in **ChatGPT/GPTs, Claude Code, Cursor and Chengxiaobang** — no platform-specific skill loader required: the skill is a self-contained document that any LLM can follow, with environment detection (shell / code interpreter / no-code) and graceful degradation.

## Repository contents

```
.
├── .agents/skills/survey-analysis-portable/   # skill directory for agent systems
│   ├── SKILL.md                               # instructions (triggers + workflow + rules)
│   └── scripts/
│       ├── parse_survey.py                    # xlsx → survey.json (contract-based)
│       ├── analyze.py                         # statistics + correlations → results.json
│       └── report_gen.py                      # dependency-free base HTML report (CSS bars, no JS)
├── survey-analysis-portable.md                # single-file bundle (skill + scripts inline) for ChatGPT/attachments
└── chatgpt-instructions.txt                   # compact snippet for custom GPT Instructions (~1.4 KB)
```

## Quick start

1. Attach the skill (either `survey-analysis-portable.md` or the folder) together with your survey `.xlsx` to the AI.
2. Say: *"Read survey-analysis-portable.md fully and follow it strictly, no clarifying questions."*
3. The AI parses the export (adapting to its format), computes distributions, correlations and segments, classifies open answers, and returns a single HTML report you can share.

## Installation (agent systems)

- **Claude Code / Cursor:** copy `.agents/skills/survey-analysis-portable/` into your project (or `~/.agents/skills/`, or `~/.cursor/rules`).
- **Chengxiaobang:** install the skill folder (frontmatter is recognized).
- **Custom GPT:** paste `chatgpt-instructions.txt` into Instructions and upload `survey-analysis-portable.md` to Knowledge.

## Key rules the skill enforces

- All numbers in the report come only from the data; quotes are verbatim (typos preserved).
- Report language is English by default (Russian on request; 0 Cyrillic in the EN version).
- Question bases respect survey routing; percentages are computed per base.
- Report structure: cover → key findings → methodology → thematic sections → correlations → segments → open answers → hypotheses → recommendations → appendix (per-question distributions in `<details>`).

## Notes

- **No survey data is stored in this repository** — no `.xlsx` exports, no `survey.json`/`results.json`, no example reports with respondent data. Data and reports stay out of git.
- The bundled scripts were tested end-to-end on a real 728-respondent survey export.

## Tests

- Simple: "make a report from this survey" + `.xlsx` → parse + analyze + HTML in any environment.
- Complex: + questionnaire design + example report → full report with segments and open-answer classification.
- Must not trigger: "write a sales report" without survey data.
