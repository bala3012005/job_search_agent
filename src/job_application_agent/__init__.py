"""
Offline AI-Powered Job Application Agent for Java Backend Developers
"""

__version__ = "1.0.0"
__author__ = "Developer"
__description__ = "Offline AI-Powered Job Application Agent for Java Backend Developers"

from .core.agent import JobApplicationAgent
from .core.config import Config, UserProfile

__all__ = ["JobApplicationAgent", "Config", "UserProfile"]
