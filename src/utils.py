"""Compatibility exports; application code lives in :mod:`email_assist.utils`."""

from email_assist.safety import extract_urls_from_text
from email_assist.utils import calculate_cost

__all__ = ["calculate_cost", "extract_urls_from_text"]