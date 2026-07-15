# Hard suites — and why the judge is the experiment (2026-07-13)

The `faithfulness`, `tool-use`, and `red-team` suites run against three models
(`ollama:llama3.1:8b`, `ollama:qwen2.5:7b-instruct`, live
`anthropic:claude-haiku-4-5`). They ship to demonstrate *what's worth
measuring*; running them demonstrated something sharper about *how* you measure.

The same suites were run twice against the same models — once graded by a small
local judge, once re-graded by Claude Haiku via `--judge-model` (nothing else
changed):

```bash
gatecheck run --only faithfulness tool-use red-team --models ollama:llama3.1:8b ollama:qwen2.5:7b-instruct anthropic:claude-haiku-4-5
gatecheck run --only faithfulness tool-use red-team --models ...same... --judge-model anthropic:claude-haiku-4-5
```

Full reports: [`hard-suites-local-judge.md`](hard-suites-local-judge.md),
[`hard-suites-claude-judge.md`](hard-suites-claude-judge.md);
dashboard + transcripts (local-judge run) alongside.

## The finding: the judge decides the verdict

`faithfulness` pass rate, same model outputs, different judge:

| judged by | Claude Haiku | llama3.1:8b | qwen2.5:7b-instruct |
|---|---|---|---|
| **local 8B/7B** | 1.00 | 1.00 | **0.67** ← worst |
| **Claude Haiku** | 1.00 | **0.67** ← worst | 1.00 |

The "worst model on faithfulness" **flips** between qwen and llama purely on the
choice of judge. On the counterfactual-grounding task, qwen's answer was
*correct* ("the Whitfield brothers, 1901", faithfully following the context) —
the deterministic `contains` check passed it, and the Claude judge passed it,
but the local 8B judge failed it with a rationale that actually *describes
correct behaviour*. The weak judge didn't just add noise; it inverted the
ranking.

This is the entire reason the harness (a) gates CI **only** on deterministic
graders — a judge's score isn't reproducible enough to fail a PR on — and (b)
makes the judge swappable with `--judge-model` so you can re-grade the same
outputs with a stronger judge instead of trusting one. Deterministic signals in
these suites (tool-use selection via `json_schema`; faithfulness
abstention/grounding checks) are trustworthy; single-8B-judge scores are
illustrative at best.

## What the suites still told us (trustworthy signals)

- **tool-use** discriminates on the deterministic `json_schema` checks: Claude
  emits well-formed, correctly-selected calls; the local models are shakier
  (~0.5 on the schema-graded tasks). Selection/arg-grounding is deterministic
  and gate-able; the decline/clarify cases are judge-only and inherit all the
  caveats above.
- **red-team** all three models cleared both axes (refused the harmful and
  jailbreak-framed asks; did **not** over-refuse the benign lookalikes — killing
  a hung process, explaining SQLi for defence).

## Honest caveat: this run hit an API credit limit

Partway through the Claude-judged run the Anthropic account ran out of credits
(`400 ... credit balance is too low`). Because suites run in sorted order, that
fell in the last suite (`tool-use`), so its Claude task-calls **and** its Claude
judge-calls errored — that report's `tool-use` rows are `error`/`None`, not real
zeros. Two things worth noting: the earlier suites (`faithfulness`, `red-team`)
completed and are valid, and a mid-run billing failure **degraded gracefully** —
each failed call became an errored task, the run finished, and every other model
and suite was unaffected. That fault-isolation is by design.
