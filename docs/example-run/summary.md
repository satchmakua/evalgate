# Eval run -- 20260713-151401

| suite | model | tasks | passed | pass_rate | pass_rate_lo | pass_rate_hi | mean_judge | prompt_tokens | completion_tokens | cost_usd | judge_cost_usd | p50_latency_s | p95_latency_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classification | anthropic:claude-haiku-4-5 | 3 | 3 | 1.0 | 0.4385 | 1.0 | None | 132 | 13 | 0.000197 | 0 | 0.784 | 0.875 |
| classification | ollama:llama3.1:8b | 3 | 3 | 1.0 | 0.4385 | 1.0 | None | 150 | 8 | 0.0 | 0 | 2.255 | 18.95 |
| classification | ollama:qwen2.5:7b-instruct | 3 | 3 | 1.0 | 0.4385 | 1.0 | None | 144 | 6 | 0.0 | 0 | 2.181 | 5.948 |
| structured-output | anthropic:claude-haiku-4-5 | 2 | 1 | 0.5 | 0.0945 | 0.9055 | None | 85 | 111 | 0.00064 | 0 | 1.261 | 1.478 |
| structured-output | ollama:llama3.1:8b | 2 | 1 | 0.5 | 0.0945 | 0.9055 | None | 95 | 84 | 0.0 | 0 | 2.8 | 2.889 |
| structured-output | ollama:qwen2.5:7b-instruct | 2 | 1 | 0.5 | 0.0945 | 0.9055 | None | 95 | 83 | 0.0 | 0 | 2.625 | 2.737 |
| summarization | anthropic:claude-haiku-4-5 | 1 | 1 | 1.0 | 0.2065 | 1.0 | 4.0 | 68 | 31 | 0.000223 | 0.0 | 0.812 | 0.812 |
| summarization | ollama:llama3.1:8b | 1 | 1 | 1.0 | 0.2065 | 1.0 | 4.0 | 70 | 31 | 0.0 | 0.0 | 2.707 | 2.707 |
| summarization | ollama:qwen2.5:7b-instruct | 1 | 1 | 1.0 | 0.2065 | 1.0 | 4.0 | 68 | 27 | 0.0 | 0.0 | 2.538 | 2.538 |

## Tags

| tag | model | tasks | pass | 95% CI |
| --- | --- | --- | --- | --- |
| classification | anthropic:claude-haiku-4-5 | 3 | 1.0 | [0.4385, 1.0] |
| classification | ollama:llama3.1:8b | 3 | 1.0 | [0.4385, 1.0] |
| classification | ollama:qwen2.5:7b-instruct | 3 | 1.0 | [0.4385, 1.0] |
| intent | anthropic:claude-haiku-4-5 | 1 | 1.0 | [0.2065, 1.0] |
| intent | ollama:llama3.1:8b | 1 | 1.0 | [0.2065, 1.0] |
| intent | ollama:qwen2.5:7b-instruct | 1 | 1.0 | [0.2065, 1.0] |
| sentiment | anthropic:claude-haiku-4-5 | 2 | 1.0 | [0.3424, 1.0] |
| sentiment | ollama:llama3.1:8b | 2 | 1.0 | [0.3424, 1.0] |
| sentiment | ollama:qwen2.5:7b-instruct | 2 | 1.0 | [0.3424, 1.0] |

## Failures

### structured-output :: action-object :: ollama:llama3.1:8b
- prompt: Schedule a meeting with Sam next Tuesday at 3pm about the budget.
- output: { "action": "Schedule a meeting", "details": { "date": "Next Tuesday", "time": "3pm", "topic": "Budget discussion", "attendee": "Sam" } }
- failed `json_schema`: schema: 'params' is a required property

### structured-output :: action-object :: ollama:qwen2.5:7b-instruct
- prompt: Schedule a meeting with Sam next Tuesday at 3pm about the budget.
- output: { "action": "schedule_meeting", "details": { "with": "Sam", "date": "next Tuesday", "time": "3pm", "purpose": "about the budget" } }
- failed `json_schema`: schema: 'params' is a required property

### structured-output :: action-object :: anthropic:claude-haiku-4-5
- prompt: Schedule a meeting with Sam next Tuesday at 3pm about the budget.
- output: ```json { "action": "schedule_meeting", "parameters": { "attendee": "Sam", "date": "next Tuesday", "time": "3pm", "subject": "budget" } } ```
- failed `json_schema`: schema: 'params' is a required property
