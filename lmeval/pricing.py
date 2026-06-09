"""Token pricing for cost tracking.

Rates are USD per 1,000,000 tokens, as (input, output). These are EXAMPLE
values for illustration -- check each provider's current pricing page and
update them before trusting the dollar figures. Local Ollama models are $0.
"""

# UPDATE THESE against current provider pricing.
PRICING = {
    "openai:gpt-4o-mini": (0.15, 0.60),
    "openai:gpt-4o": (2.50, 10.00),
    "anthropic:claude-haiku-4-5": (1.00, 5.00),
    "anthropic:claude-sonnet-4-5": (3.00, 15.00),
}


def cost_usd(model_id, prompt_tokens, completion_tokens):
    """Cost of one call given a normalized 'provider:model' id."""
    if model_id.startswith("ollama:") or ":" not in model_id:
        return 0.0  # local model => free
    rates = PRICING.get(model_id)
    if not rates:
        return 0.0  # unknown model => can't price; report 0 rather than guess
    per_in, per_out = rates
    return round(prompt_tokens / 1e6 * per_in + completion_tokens / 1e6 * per_out, 6)
