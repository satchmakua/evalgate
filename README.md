# evalgate

A small, provider-agnostic harness for **evaluating LLMs the way you'd test any
other system**: define task suites, grade outputs with deterministic checks and
an LLM judge, gate regressions in CI, and track cost and latency per model.

> **Why this exists.** Shipping with LLMs without evals is shipping on vibes.
> An *eval harness* is the testing layer for model-backed systems: it turns
> "does the new prompt/model feel better?" into a number you can diff, gate a
> pull request on, and watch over time. This repo is a compact, readable
> reference implementation of that idea.

## Why this and not promptfoo / Inspect AI / Braintrust?

Those are all good tools — and all heavier than many projects need. promptfoo
brings a Node toolchain; Inspect AI is a full research framework; Braintrust is
a SaaS with an account and a data pipeline. This harness occupies a deliberately
small lane: a **dependency-light, self-hostable, vendor-neutral Python harness
you can read end-to-end in an afternoon and gate CI on** — three runtime
dependencies (`requests`, `pyyaml`, `jsonschema`), no SaaS, no Node, no account,
no telemetry. Local models via Ollama are first-class (free, key-less), hosted
providers are uniform raw-HTTP adapters (including a hand-rolled, test-vectored
AWS SigV4 signer for Bedrock), and every artifact it produces is a plain file
you can diff and commit. If you need distributed eval infrastructure, use the
big tools; if you need honest numbers on a model swap wired into CI by this
afternoon, this is the one.

*(Not affiliated with EleutherAI's `lm-evaluation-harness` — that project is a
benchmark battery for academic evals; this is a CI regression harness for your
own product's tasks.)*

## A real run

Every bundled suite, two local models and one hosted model, one command
(hosted spend: ~$0.001):

```bash
evalgate run --models ollama:llama3.1:8b ollama:qwen2.5:7b-instruct anthropic:claude-haiku-4-5
```

| suite | model | pass (95% CI) | judge | cost | p50 |
| --- | --- | --- | --- | --- | --- |
| classification | anthropic:claude-haiku-4-5 | 1.00 [0.44–1.00] | — | $0.0002 | 0.78s |
| classification | ollama:llama3.1:8b | 1.00 [0.44–1.00] | — | $0 | 2.26s |
| classification | ollama:qwen2.5:7b-instruct | 1.00 [0.44–1.00] | — | $0 | 2.18s |
| structured-output | anthropic:claude-haiku-4-5 | 0.50 [0.09–0.91] | — | $0.0006 | 1.26s |
| structured-output | ollama:llama3.1:8b | 0.50 [0.09–0.91] | — | $0 | 2.80s |
| structured-output | ollama:qwen2.5:7b-instruct | 0.50 [0.09–0.91] | — | $0 | 2.63s |
| summarization | anthropic:claude-haiku-4-5 | 1.00 [0.21–1.00] | 4.0 | $0.0002 | 0.81s |
| summarization | ollama:llama3.1:8b | 1.00 [0.21–1.00] | 4.0 | $0 | 2.71s |
| summarization | ollama:qwen2.5:7b-instruct | 1.00 [0.21–1.00] | 4.0 | $0 | 2.54s |

**What it caught.** All three models failed the same `structured-output` task
in the same way — each returned valid JSON with an invented container key
(`details`, `details`, `parameters`), because the task demanded
schema-conformant JSON without stating the required shape (`params`). A
three-way identical failure is the signature of an under-specified *task*, not
a bad model. The suite was fixed to name the expected keys, all three models
pass the corrected task, and the committed [`baselines/default.json`](baselines/default.json)
snapshots the post-fix pass rates that CI now gates against.

Full artifacts from this run — the report, the browsable HTML dashboard, and
the per-task transcripts, failures included — are committed in
[`docs/example-run/`](docs/example-run/).

## Features

- **Task suites** — eval cases grouped by capability, defined in plain YAML
  (`suites/*.yaml`). No code needed to add a test.
- **Two kinds of graders**
  - *Deterministic*: `exact`, `contains`, `regex`, `json_schema`. Reproducible,
    free, and safe to run in CI.
  - *LLM-as-judge*: a second model (or several, ensembled) scores the output 1-5
    against a rubric, for subjective qualities (faithfulness, tone) that string
    matching can't see.
- **Regression gating** — snapshot a baseline, then fail a run (non-zero exit)
  if any suite's pass rate drops below the baseline (with optional tolerance) or
  an absolute floor. Wired into GitHub Actions.
- **Cost & latency tracking** — token counts, USD cost per model (from an
  editable pricing table), and p50/p95 latency, aggregated per suite and model.
- **Provider-agnostic** — one interface, five adapters: **Ollama** (local,
  zero-config, free), **OpenAI**, **Anthropic**, **Google Gemini**, and **Amazon
  Bedrock** (Anthropic models, SigV4-signed). Models are addressed as
  `provider:model`, e.g. `ollama:llama3.1:8b` or `openai:gpt-4o-mini`.

## How it fits together

```
suites/*.yaml ─► suite loader ─► runner ─► providers (ollama|openai|anthropic|gemini|bedrock)
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
ollama pull qwen2.5:7b-instruct

evalgate run                       # run every suite against the config defaults
evalgate run --only classification # just one suite
evalgate run --models ollama:qwen2.5:7b-instruct
```

Each run prints a summary table (pass rate with a 95% Wilson confidence
interval, mean judge score, cost, and p50/p95 latency) and writes five artifacts
to `results/`: a machine-readable `run-*.json`, `summary-*.csv` and
`summary-*.md`, a `transcripts-*.jsonl` with one self-contained record per task
(the exact input sent, the model output, and the grades), and a self-contained
`dashboard-*.html` you can open in a browser to scan and filter every result.
The `summary-*.md` also carries a **Failures** section listing each failing task
with its prompt/output preview and the specific graders that failed. When tasks
carry tags (set per-task or per-suite in the YAML), the reports add a **Tags**
breakdown — pass rate per (tag, model) across suites, so you can see how a model
does on, say, all `reasoning` tasks.

## Regression gating

```bash
# 1. record where you stand today
evalgate baseline --name default

# 2. later -- after a prompt edit, model swap, dependency bump -- gate against it
evalgate gate --name default                 # fails (exit 1) on any pass-rate drop
evalgate gate --name default --tolerance 0.1 # allow up to a 10-point drop
evalgate gate --only classification --min-pass-rate 0.8
```

In CI (`.github/workflows/evals.yml`) the `test` job always runs the unit tests.
The `gate` job runs the deterministic suites against a cheap hosted model and
fails the build on a regression — but only if an `OPENAI_API_KEY` repo secret is
configured, so forks and key-less runs skip it cleanly. LLM-judge graders are
left out of CI (`--deterministic-only`) because they aren't reproducible enough
to gate on; run those locally or on a schedule.

## Providers and cost

| provider    | id prefix     | cost        | needs                |
|-------------|---------------|-------------|----------------------|
| Ollama      | `ollama:`     | free        | local server         |
| OpenAI      | `openai:`     | per token   | `OPENAI_API_KEY`     |
| Anthropic   | `anthropic:`  | per token   | `ANTHROPIC_API_KEY`  |
| Gemini      | `gemini:`     | per token   | `GEMINI_API_KEY`     |
| Bedrock     | `bedrock:`    | per token   | AWS creds + region (env) |

Cost is computed from `evalgate/pricing.py`, which ships current OpenAI, Anthropic,
Google Gemini, and Amazon Bedrock (Anthropic) rates (verified 2026-06-27 against
each provider's pricing page; Bedrock matches first-party Anthropic list price).
Provider pricing drifts over time, so re-check it periodically. Any model not
listed there — including every local Ollama model — is counted as $0.

LLM-judge calls are priced too: each judge invocation (including every member of
an ensemble) is added to the task's cost, so `--max-cost` and the reported
totals account for judge spend. The `judge_cost_usd` column breaks it out.

Pass `--max-cost <USD>` to any command to cap spend: the run stops before
starting the next task once cumulative cost reaches the budget. It's a soft cap
(actual spend can exceed it by at most the one task that crosses the line, or by
up to `--concurrency` tasks when running in parallel), and free local models
never trip it.

Pass `--concurrency <N>` to run up to N tasks in parallel (default 1). Each task
is a single HTTP call, so this is I/O-bound work that parallelizes well;
results are still reported in a stable suite/model/task order.

Pass `--repeat <N>` to run each task N times; the verdict becomes a majority
vote across the runs, and the report shows each task's pass fraction and flags
any whose result flips. Set a non-zero `temperature` in config for this to
surface real variance — at `temperature: 0` the runs are identical.

Pass `--cache` to reuse the result of any identical (model, prompt, options)
call within a run instead of paying for it twice — useful when the same prompt
recurs across suites. Cached tasks report $0 cost and ~0 latency and are marked
`cached`; the cache is skipped under `--repeat` (repeated sampling must make
real calls to measure variance). Dedup is exact when running sequentially; under
`--concurrency` it's best-effort.

Pass `--cache-dir DIR` to persist that cache to disk, so re-running a suite
after editing one task skips re-paying for all the unchanged ones. The key is
`(model, messages, options)`: editing a task's prompt/system or swapping the
model forces a real call, editing a grader does not (grading re-runs on the
cached output). Entries are one JSON file per key, written atomically; a
fully-cached re-run costs $0.

## Adding a suite

Drop a YAML file in `suites/`:

```yaml
name: my-suite
description: what this checks
models: [ollama:llama3.1:8b]      # optional; falls back to config defaults
tags: [smoke]                     # optional; applied to every task in the suite
tasks:
  - id: my-task
    tags: [reasoning]             # optional; merged with the suite's tags
    system: optional system prompt
    prompt: the user turn
    graders:
      - type: contains
        any_of: ["expected", "word"]
        ignorecase: true
      - type: llm_judge
        judge_model: ollama:llama3.1:8b   # or a list to ensemble: [modelA, modelB]
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
| `pairwise`    | a judge prefers the output over a `reference` in **both** orderings (position-bias-controlled) |

`llm_judge` takes either a single `judge_model` or a list via `judge_models`;
with several, each scores independently and the task passes on the **mean**
score — judge ensembling, to reduce single-model bias.

`pairwise` compares the output against a fixed `reference` answer and runs the
comparison **both ways** (output first, then reference first); a preference only
counts if it survives the swap, so a position-biased judge collapses to a *tie*
rather than a spurious win. `require: win` demands a strict preference; the
default (`tie`) passes unless the output is judged *worse* than the reference.
Like `llm_judge` it's non-reproducible and excluded from CI gating. Any judge
grader's model is swappable at run time with `--judge-model` (no YAML edit).

## The bundled suites

The suites in `suites/` are meant to show *what's worth measuring*, not just
that grading runs. Each pairs a deterministic guardrail (reproducible, gate-able
in CI) with a judge where the real question is subjective.

| suite | what it actually measures | grading |
|---|---|---|
| `classification` | single-label sentiment/intent | deterministic — **gates CI** |
| `structured-output` | strict JSON conforming to a schema | deterministic (`json_schema`) — **gates CI** |
| `summarization` | faithful, concise summaries | LLM judge |
| `faithfulness` | RAG grounding: **abstain** when the answer isn't in the context; follow the context over parametric priors on **counterfactual** input | judge + a deterministic abstention/grounding check |
| `tool-use` | correct tool **selection** + argument grounding; **decline** when no tool fits; **ask** when a required arg is missing | `json_schema` (`const` pins the right tool) on the calls — **gate-able**; judge on the decline/clarify cases |
| `red-team` | refuse genuinely harmful / jailbreak-framed asks **and** *don't* over-refuse benign lookalikes (`kill` a process, SQLi *for defense*) | LLM judge, tagged `refuse` vs `over-refusal` |
| `preference` | is the output at least as good as a reference answer? | `pairwise` LLM judge, position-swap-controlled |

The design bias throughout: **deterministic where a failure is cheaply and
reproducibly checkable, LLM-judge only where it genuinely isn't** — and CI gates
only on the deterministic graders (`--deterministic-only`), because a judge's
score isn't reproducible enough to fail a pull request on. The judge suites are
for local or scheduled runs; the harmful `red-team` prompts describe disallowed
categories generically and contain no operational detail (a passing model
produces nothing harmful — the suite tests the *guardrail*).

Running these against three models made the point concrete: re-grading the *same
faithfulness outputs* with a stronger judge (`--judge-model`) **flipped which
model looked worst** (qwen under a local 8B judge, llama under Claude) — the weak
judge even failed a demonstrably correct answer that the deterministic grader
passed. That's why the judge is swappable and why CI trusts only deterministic
graders. Write-up and artifacts: [`docs/example-run/hard-suites.md`](docs/example-run/hard-suites.md).

## Understanding the codebase

**Read the files in this order.**

1. `evalgate/types.py` — the five dataclasses everything else passes around
   (`Task`, `Suite`, `Completion`, `GradeResult`, `TaskResult`). The whole repo
   is functions over these. Note `TaskResult.verdict`: the pass/fail rule.
2. `evalgate/cli.py` — the three subcommands (`run`, `baseline`, `gate`) and how a
   run is wired together. This is the front door.
3. `evalgate/runner.py` — the core loop: every (suite × model × task) becomes one
   `TaskResult`. The single most important file.
4. `evalgate/providers/` — `base.py` is the one-method interface; `ollama.py`,
   `openai.py`, `anthropic.py`, `gemini.py`, `bedrock.py` are uniform raw-HTTP
   adapters (hosted ones retry transient failures via `_http.py`; Bedrock adds
   SigV4 signing); `__init__.py` holds the registry and the `provider:model`
   id parser.
5. `evalgate/graders/` — `deterministic.py` (`exact`, `contains`, `regex`,
   `json_schema`) and `llm_judge.py` (a second model scores 1–5 against a rubric).
6. `evalgate/report.py` then `evalgate/gate.py` — aggregation into per-(suite, model)
   summaries, then comparison against a committed baseline.
7. `evalgate/pricing.py` — the token→USD table and the `$0` fallback.

**The one path that matters (a `run`).** Config + `suites/*.yaml` are loaded into
`Suite`/`Task` objects → `runner` iterates suites × models × tasks → for each
task, `parse_model_id` picks the provider, `provider.complete()` returns a
`Completion` (text + token counts + latency), each grader scores the text (an
`llm_judge` grader is handed a `judge_fn` that calls a second model),
`cost_usd` prices the tokens, and it all lands in a `TaskResult`.
`report.summarize()` then groups results by (suite, model) into pass rate, mean
judge score, token/cost sums, and p50/p95 latency; `gate` compares those pass
rates to a baseline and sets the process exit code.

**Concepts worth understanding:**

- **`provider:model` addressing.** Models are `openai:gpt-4o-mini`,
  `ollama:llama3.1:8b`, etc. A bare id uses `default_provider`. The parser is
  careful about the *tag* colon: `llama3.1:8b` splits to provider + `8b` only if
  `llama3.1` is a registered provider (it isn't), so the tag survives intact.
- **Two grader families.** Deterministic graders are reproducible and free, so
  they gate CI. The LLM judge captures subjective quality (faithfulness, tone)
  but isn't reproducible — which is why CI runs `--deterministic-only`.
- **The verdict rule.** A task passes only if *every* deciding grader passes;
  it's `None` when no grader produced a definite verdict, and `False` on error.
  Pass rate is computed over deciding tasks only.
- **Two ways the gate fails.** A relative drop below the baseline (beyond an
  optional `--tolerance`), or falling under an absolute `--min-pass-rate` floor.
  A (suite, model) with no baseline entry is reported but never fails the gate.
- **Cost model.** Local Ollama models and any model not in the pricing table are
  counted as `$0` rather than guessed. `temperature: 0` keeps runs as
  reproducible as the providers allow.

## Roadmap & status

Planned work and known limitations are tracked in [`ROADMAP.md`](ROADMAP.md);
the current implementation status is in [`PROGRESS.md`](PROGRESS.md).

## Layout

```
evalgate/        the package (providers, graders, runner, report, gate, cli)
suites/        eval suites in YAML
baselines/     committed baseline snapshots for gating
tests/         pytest unit tests + a stubbed-HTTP end-to-end test
.github/       CI workflow
```

## License

MIT — see `LICENSE`.
