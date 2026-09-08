# 🛠️ InsightForge — Agentic Data Analyst

A multi-agent data-analysis system: **Planner → Analyst → Critic → Reporter**, with
sandboxed code execution, adaptive retries, escalation, and a live reasoning trace
in a Streamlit dashboard.

Unlike a one-shot "chat with CSV" tool, InsightForge is a **loop**: the Critic judges
every code execution (pass / fail / unclear), failed steps are retried with simpler
code, and after `max_retries` the session **escalates to a human** instead of
hallucinating a result. Only critic-verified evidence ever reaches the report.

## Why this stands out

| Classmates' tools | InsightForge |
|---|---|
| One LLM call, one answer | Agentic loop with planning, execution, verification |
| Output unverifiable | Only critic-verified claims enter the report |
| Breaks on messy data | Retry loop visibly self-corrects (the best demo moment) |
| Black box | Full reasoning trace persisted to `sessions/<id>.json` |

## Quickstart

```bash
pip install -r requirements.txt
python make_sample_data.py          # creates data/sales.csv (intentionally messy)
streamlit run app.py
```

Select **Demo mode (no API key)** — a deterministic mock agent runs the full loop
(planning, sandbox execution, critic verdicts, retries, report) with zero cost.
Add an `ANTHROPIC_API_KEY` and switch to **Claude API** for real LLM planning,
code generation, and judging.

## Project structure

```
insightforge/
├── agents/
│   ├── planner.py       # goal -> ordered analysis steps (JSON)
│   ├── analyst.py       # step -> pandas/matplotlib code -> sandbox
│   ├── critic.py        # pass/fail/unclear verdicts (judgment, not hardcoded)
│   └── reporter.py      # verified findings -> markdown report
├── orchestrator.py      # the agentic loop + escalation
├── state.py             # single JSON state object per session (the backbone)
├── sandbox.py           # subprocess + import allowlist + timeout + output caps
├── llm.py               # Anthropic client wrapper + strict JSON extraction
├── app.py               # Streamlit dashboard (live trace, report download)
├── prompts/             # system prompts (also embedded in agents)
├── sessions/            # auto-saved per-run state JSON (reasoning trace)
└── data/                # sample messy datasets
```

## How the loop works

1. **Planner** decomposes the goal into 3–8 runnable steps.
2. **Analyst** writes one self-contained script per step and runs it in the sandbox
   (imports restricted to pandas/numpy/matplotlib; 20s timeout; capped output).
3. **Critic** judges whether the stdout actually supports the step. Fail → retry with
   fallback code; `max_retries=3` → **escalated** status, control returns to human.
4. **Reporter** compiles only verified findings into `report.md`.

All LLM responses go through strict JSON parsing; malformed responses are treated
as a failed attempt and retried — the demo never crashes on a bad completion.

## Suggested 7-week build plan

1. **Week 1** — sandbox + single-agent skeleton (this repo, minus critic).
2. **Week 2** — planner + manual Planner→Analyst chain.
3. **Week 3** — critic + retry loop; deliberately feed buggy data to watch self-correction.
4. **Week 4** — reporter + Streamlit UI (done here).
5. **Week 5** — hardening: 5–10 real Kaggle CSVs, guardrails, timed live demo rehearsal.

## Live demo script (2 minutes)

1. Open the app in **Demo mode**, upload `data/sales.csv`.
2. Goal: *"Find the main drivers of revenue and flag data-quality risks."*
3. Run — narrate the trace: plan appears → code executes → critic verifies → report.
4. Then run `data/employees.csv` with a goal like *"predict salary"* — retries and
   fallback summaries visibly trigger on the messier columns.
5. Show `sessions/<id>.json` as the full reasoning trace (this is what makes it look
   agentic rather than magical).

## Evaluation metrics

- Critic verdict accuracy vs. human judgment (sample 30 attempts).
- End-to-end completion rate across 10 diverse CSVs.
- Time-to-report; retry count distribution; escalation rate.
- Report usefulness rating by a domain person (1–5).

## Ethics & limits

- Sandbox is **not** a security boundary — it is import/timeout/output restriction,
  suitable for a class demo. Use Docker/E2B for real isolation.
- Demo mode uses fixed analysis templates; API mode is where the real reasoning lives.
- The system analyzes data; it does not certify correctness — the Critic raises the
  bar, humans still own the conclusions.
