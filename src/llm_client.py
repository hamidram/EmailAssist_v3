"""Compatibility exports; application code lives in :mod:`email_assist.llm_client`."""

from email_assist.llm_client import LLMClient, LLMResponse, OpenAIClient, parse_json_object

__all__ = ["LLMClient", "LLMResponse", "OpenAIClient", "parse_json_object"]