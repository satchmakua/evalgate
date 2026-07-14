# Progress

Current implementation status of evalgate. Last updated 2026-07-13.

## Proven in a real run

On 2026-07-13 the harness ran every bundled suite against three models
(`ollama:llama3.1:8b`, `ollama:qwen2.5:7b-instruct`, live
`anthropic:claude-haiku-4-5`; ~$0.001 hosted spend). The run immediately caught
an under-specified task — all three models failed `action-object` identically
by inventing a container key the prompt never named — which was fixed; the
post-fix snapshot is committed as `baselines/default.json` and the run's
artifacts (report, dashboard, transcripts) live in `docs/example-run/`. The
full run → baseline → gate loop has been exercised for real.

## Implemented

- **Suite loading** — eval suites defined in YAML (`suites/*.yaml`), loaded into
  `Suite`/`Task` objects, with per-task and suite-level `tags` merged
  (`evalgate/suite.py`).
- **Bundled suites** — seven, chosen to show eval *taste*: `classification` and
  `structured-output` (deterministic, gate CI), `summarization`, `faithfulness`
  (RAG grounding — abstention + counterfactual grounding), `tool-use`
  (selection/arg-grounding via `json_schema`, plus decline/clarify), `red-team`
  (refuse-harmful **and** don't-over-refuse, both axes), and `preference`
  (pairwise vs. a reference with a position-swap).
- **Providers** — uniform raw-HTTP adapters for Ollama, OpenAI, Anthropic,
  Google Gemini, and Amazon Bedrock (Anthropic models, hand-rolled SigV4) behind
  a single interface, addressed as `provider:model`. Hosted adapters retry
  transient failures (HTTP 429 / 5xx, dropped connections) with exponential
  backoff (`evalgate/providers/`).
- **Graders** — deterministic (`exact`, `contains`, `regex`, `json_schema`), an
  LLM-as-judge grader that can ensemble across multiple judge models (mean
  score), and a `pairwise` preference grader that compares the output against a
  reference answer with a position-swap to control order bias (`evalgate/graders/`).
- **Runner** — executes every (suite × model × task) into a `TaskResult`, with
  per-task fault isolation, optional parallelism (`--concurrency`, results kept
  in stable order), optional repeated sampling (`--repeat`, majority-vote
  verdict + pass fraction), an optional in-run completion cache (`--cache`), an
  optional `--judge-model` override that swaps the judge for every `llm_judge`
  grader without editing suite YAML, and an optional `--max-cost` budget that
  stops a run before it overspends (`evalgate/runner.py`).
- **Reporting** — per-(suite, model) summaries with pass rate (and a 95% Wilson
  confidence interval), mean judge score, token/cost totals, and p50/p95 latency
  (JSON, CSV, a browsable self-contained HTML dashboard, and a Markdown report
  that lists each failing task with its output and the graders that failed,
  flags tasks that flip under `--repeat`, and breaks scores down per (tag,
  model)), plus a `transcripts-*.jsonl` with one
  self-contained record per task — input sent, model output, and grades — for
  debugging (`evalgate/report.py`).
- **Regression gating** — baseline snapshots plus relative-drop and absolute
  pass-rate floors, with a non-zero exit code on failure; wired into GitHub
  Actions (`evalgate/gate.py`, `.github/workflows/evals.yml`).
- **Cost tracking** — current OpenAI, Anthropic, Google Gemini, and Amazon
  Bedrock (Anthropic) token rates with a `$0` fallback for local and unlisted
  models; LLM-judge calls are priced and folded into each task's cost, broken
  out as `judge_cost_usd` (`evalgate/pricing.py`, `evalgate/runner.py`).

## Tested

- Deterministic and LLM-judge graders, including judge ensembling and the
  `pairwise` position-swap (`tests/test_graders.py`).
- Gate and baseline logic (`tests/test_gate.py`).
- Pricing calculations (`tests/test_pricing.py`).
- Report aggregation, pass-rate confidence intervals, transcript artifacts, tag
  breakdowns, and the HTML dashboard (`tests/test_report.py`).
- Suite loading and tag merging (`tests/test_suite.py`).
- Provider registry and the `provider:model` parser (`tests/test_providers.py`).
- HTTP retry/backoff helper (`tests/test_http_retry.py`).
- Runner, including the cost-budget guardrail, repeated-sampling vote,
  judge-cost tracking, in-run caching, and the `--judge-model` override
  (`tests/test_runner.py`).
- CLI subcommands and exit codes (`tests/test_cli.py`).
- End-to-end: the Anthropic, OpenAI, Gemini, and Bedrock adapters over a stub
  HTTP server, including retry/backoff and the SigV4 signer's known-answer
  vector (`tests/test_e2e.py`).

## Not yet done

Tracked in [`ROADMAP.md`](ROADMAP.md). Near-term: persisting the completion
cache to disk for cross-run skips. See `ROADMAP.md` for medium-term ideas.
