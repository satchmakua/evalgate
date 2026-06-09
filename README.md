# llm-eval-harness

A small, provider-agnostic harness for **evaluating LLMs the way you'd test any
other system**: define task suites, grade outputs with deterministic checks and
an LLM judge, gate regressions in CI, and track cost and latency per model.

> **Why this exists.** Shipping with LLMs without evals is shipping on vibes.
> An *eval harness* is the testing layer for model-backed systems: it turns
> "does the new prompt/model feel better?" into a number you can diff, gate a
> pull request on, and watch over time. This repo is a compact, readable
> reference implementation of that idea.

## Features

- **Task suites** — eval cases grouped by capability, defined in plain YAML
  (`suites/*.yaml`). No code needed to add a test.
- **Two kinds of graders**
  - *Deterministic*: `exact`, `contains`, `regex`, `json_schema`. Reproducible,
    free, and safe to run in CI.
  - *LLM-as-judge*: a second model scores the output 1-5 against a rubric, for
    subjective qualities (faithfulness, tone) that string matching can't see.
- **Regression gating** — snapshot a baseline, then fail a run (non-zero exit)
  if any suite's pass rate drops below the baseline (with optional tolerance) or
  an absolute floor. Wired into GitHub Actions.
- **Cost & latency tracking** — token counts, USD cost per model (from an
  editable pricing table), and p50/p95 latency, aggregated per suite and model.
- **Provider-agnostic** — one interface, three adapters: **Ollama** (local,
  zero-config, free), **OpenAI**, and **Anthropic**. Models are addressed as
  `provider:model`, e.g. `ollama:llama3.1:8b` or `openai:gpt-4o-mini`.

## How it fits together

```
suites/*.yaml ─► suite loader ─► runner ─► providers (ollama|openai|anthropic)
                                   │
                                   ├─► graders (deterministic + llm-judge)
                                   ├─► pricing (tokens ─► USD)
                                   └─► results ─► report (md / csv / json)
                                                     │
                                                  gate (vs baselines/*.json) ─► exit code
```

## Quickstart (local, no API keys)

```bash
pip install -e ".[dev]"

# requires a local Ollama with the models pulled:
ollama serve
ollama pull llama3.1:8b
ollama pull qwen2.5:7b

lmeval run                       # run every suite against the config defaults
lmeval run --only classification # just one suite
lmeval run --models ollama:qwen2.5:7b
```

Each run prints a summary table and writes `results/run-*.json`,
`summary-*.csv`, and `summary-*.md`.

## Regression gating

```bash
# 1. record where you stand today
lmeval baseline --name default

# 2. later -- after a prompt edit, model swap, dependency bump -- gate against it
lmeval gate --name default                 # fails (exit 1) on any pass-rate drop
lmeval gate --name default --tolerance 0.1 # allow up to a 10-point drop
lmeval gate --only classification --min-pass-rate 0.8
```

In CI (`.github/workflows/evals.yml`) the `test` job always runs the unit tests.
The `gate` job runs the deterministic suites against a cheap hosted model and
fails the build on a regression — but only if an `OPENAI_API_KEY` repo secret is
configured, so forks and key-less runs skip it cleanly. LLM-judge graders are
left out of CI (`--deterministic-only`) because they aren't reproducible enough
to gate on; run those locally or on a schedule.

## Providers and cost

| provider    | id prefix     | cost        | needs            |
|-------------|---------------|-------------|------------------|
| Ollama      | `ollama:`     | free        | local server     |
| OpenAI      | `openai:`     | per token   | `OPENAI_API_KEY` |
| Anthropic   | `anthropic:`  | per token   | `ANTHROPIC_API_KEY` |

Cost is computed from `lmeval/pricing.py`. Those rates are **example values** —
update them against current provider pricing before trusting the dollar figures.
Local models are always counted as $0.

## Adding a suite

Drop a YAML file in `suites/`:

```yaml
name: my-suite
description: what this checks
models: [ollama:llama3.1:8b]      # optional; falls back to config defaults
tasks:
  - id: my-task
    system: optional system prompt
    prompt: the user turn
    graders:
      - type: contains
        any_of: ["expected", "word"]
        ignorecase: true
      - type: llm_judge
        judge_model: ollama:llama3.1:8b
        pass_threshold: 4
        rubric: |
          Score 1-5 ...
```

## Grader reference

| type          | passes when …                                              |
|---------------|------------------------------------------------------------|
| `exact`       | output equals `value` (optional `ignorecase`)              |
| `contains`    | output has `any_of` (or every `all_of`) substring          |
| `regex`       | `pattern` matches the output                               |
| `json_schema` | output is valid JSON, optionally matching `schema`         |
| `llm_judge`   | a judge model scores >= `pass_threshold` against `rubric`  |

## Layout

```
lmeval/        the package (providers, graders, runner, report, gate, cli)
suites/        eval suites in YAML
baselines/     committed baseline snapshots for gating
tests/         pytest unit tests (graders + gate logic)
.github/       CI workflow
```

## License

MIT — see `LICENSE`.
