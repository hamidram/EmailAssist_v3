from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from .config import Settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMClient(Protocol):
    def complete(
        self, system_prompt: str, user_prompt: str, *, json_mode: bool = False
    ) -> LLMResponse: ...


class OpenAIClient:
    def __init__(self, settings: Settings) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The OpenAI SDK is not installed. Install the project with "
                "`pip install -e .`."
            ) from exc

        client_options: dict[str, str] = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_options["base_url"] = settings.openai_base_url
        self._client = OpenAI(**client_options)
        self._model = settings.model

    def complete(
        self, system_prompt: str, user_prompt: str, *, json_mode: bool = False
    ) -> LLMResponse:
        options: dict[str, object] = {}
        if json_mode:
            options["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            **options,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("The LLM returned an empty response.")
        usage = response.usage
        return LLMResponse(
            content=content.strip(),
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )


def parse_json_object(content: str) -> dict[str, object]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) < 3 or not lines[-1].strip().startswith("```"):
            raise ValueError("The LLM returned an unterminated JSON code fence.")
        cleaned = "\n".join(lines[1:-1]).strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("The LLM returned invalid JSON.") from exc
    if not isinstance(value, dict):
        raise ValueError("The LLM response must be a JSON object.")
    return value
