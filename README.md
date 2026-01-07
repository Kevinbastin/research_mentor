# METIS: Mentoring Engine for Thoughtful Inquiry & Solutions

Code and evaluation artifacts for the preprint **“METIS: Mentoring Engine for Thoughtful Inquiry & Solutions”**.


## Abstract
Many students lack access to expert research mentorship. We ask whether an AI mentor can move undergraduates from an idea to a paper. We build **METIS**, a tool‑augmented, stage‑aware assistant with literature search, curated guidelines, methodology checks, and memory. We evaluate METIS against GPT‑5 and Claude Sonnet 4.5 across six writing stages using LLM‑as‑a‑judge pairwise preferences, student‑persona rubrics, short multi‑turn tutoring, and evidence/compliance checks.

## Key results (from the preprint)


## System overview

![METIS system diagram](AuthorKit26/CameraReady/LaTeX/System-Diagram.png)

## What this repo contains
- **OpenAI SDK-based tool calling** (compatible with OpenRouter/OpenAI): `src/academic_research_mentor/llm/` and `src/academic_research_mentor/agent/`.
- Tools (web search, guidelines retrieval, arXiv search, attachments): `src/academic_research_mentor/tools/` and `src/academic_research_mentor/attachments/`.
- Evaluation prompts + scripts: `evaluation/data/` and `evaluation/scripts/`.

## Setup
```bash
uv sync
```

## Environment
```bash
cp .example.env .env
```

Required (at least one):
- `OPENROUTER_API_KEY` (recommended)
- `OPENAI_API_KEY`

Optional (enables additional retrieval providers):
- `TAVILY_API_KEY`

## Run METIS (CLI)
This branch’s default entrypoint is the simplified CLI:

```bash
uv run arm
```

## Run METIS (server)
```bash
uv run uvicorn academic_research_mentor.server:app --host 0.0.0.0 --port 8000
```

## Reproduce evaluation runs

Run the stage A/B/C evaluation driver (writes a combined summary to `reports/evals/latest_run.json`):

```bash
uv run python evaluation/scripts/run_all_stages.py
```

Artifacts are written under:
- `evaluation/results/raw_logs/`
- `evaluation/results/analysis_reports/`

## Tests
```bash
uv run pytest -q
```

## Citation
If you use this code or evaluation setup, please cite the preprint:

```bibtex
@misc{metis2026,
  title        = {METIS: Mentoring Engine for Thoughtful Inquiry \& Solutions},
  author       = {Kumar, Abhinav Rajeev and Trehan, Dhruv and Chopra, Paras},
  year         = {2026},
  note         = {Preprint. Repository: https://github.com/lossfunk/ai-research-mentor}
}
```
