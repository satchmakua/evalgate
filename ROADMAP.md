# Roadmap

Planned work for llm-eval-harness, roughly in priority order, with the known
limitations that motivate it.

## Known limitations

- **No end-to-end test against a live provider.** Unit coverage is broad
  (graders, gate, pricing, reporting, suite loading, the `provider:model`
  parser, retry/backoff, runner, and CLI), but nothing exercises a real model
  call end to end.
- **Single-sample judging.** The LLM judge scores once with one model; score
  variance is not measured, and small-N pass rates carry no confidence interval.
- **Partial `seed` support.** Only the OpenAI adapter forwards `seed`, so
  cross-provider reproducibility is best-effort.

## Near term

- An end-to-end test against a stub HTTP server.

## Medium term

- Judge ensembling / repeated sampling to quantify score variance.
- Confidence intervals on small-N pass rates.

## Later

- Additional providers (e.g. Google Gemini, Amazon Bedrock).
- Judge ensembling / repeated sampling to quantify score variance.
- An HTML dashboard over the JSON results.
