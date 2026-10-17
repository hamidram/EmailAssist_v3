"""EmailAssist application package."""

from .constants import CATEGORIES
from .pipeline import EmailAssistPipeline

__all__ = ["CATEGORIES", "EmailAssistPipeline"]
