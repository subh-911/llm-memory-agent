"""
LLM Memory Agent - Source Package

A production-ready LLM agent with sophisticated memory management.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .agent import SimpleMemoryAgent
from .models import MemoryItem, MemoryType, ConversationHistory
from .config import settings

__all__ = [
    "SimpleMemoryAgent",
    "MemoryItem",
    "MemoryType",
    "ConversationHistory",
    "settings",
]
