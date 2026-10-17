from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_base_url: str | None
    model: str
    safe_browsing_api_key: str | None
    input_cost_per_million: float
    output_cost_per_million: float
    safe_browsing_timeout: float = 10.0

    @classmethod
    def from_environment(cls, env_file: Path | None = None) -> "Settings":
        load_dotenv(dotenv_path=env_file, override=False)
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Copy .env.example to .env and set it."
            )

        model = os.getenv("EMAIL_ASSIST_MODEL", "gpt-4o-mini").strip()
        if not model:
            raise ValueError("EMAIL_ASSIST_MODEL must not be blank.")

        return cls(
            openai_api_key=api_key,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "").strip() or None,
            model=model,
            safe_browsing_api_key=os.getenv(
                "GOOGLE_SAFE_BROWSING_API_KEY", ""
            ).strip()
            or None,
            input_cost_per_million=_read_nonnegative_float(
                "EMAIL_ASSIST_INPUT_COST_PER_MILLION", 0.15
            ),
            output_cost_per_million=_read_nonnegative_float(
                "EMAIL_ASSIST_OUTPUT_COST_PER_MILLION", 0.60
            ),
        )


def _read_nonnegative_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a non-negative number.") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a non-negative number.")
    return value
