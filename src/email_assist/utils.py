from .safety import extract_urls_from_text


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    *,
    input_cost_per_million: float = 0.15,
    output_cost_per_million: float = 0.60,
) -> float:
    if min(
        prompt_tokens,
        completion_tokens,
        input_cost_per_million,
        output_cost_per_million,
    ) < 0:
        raise ValueError("Token counts and token prices must be non-negative.")
    return (
        prompt_tokens * input_cost_per_million
        + completion_tokens * output_cost_per_million
    ) / 1_000_000
