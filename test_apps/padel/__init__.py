"""
Padel scenario package with GUI and tracking helpers.

This package contains padel-specific models and display logic.
"""
from dataclasses import dataclass
from typing import Literal, List
from pydantic import BaseModel

@dataclass
class Match:
    """Represents a potential padel game match."""
    timestamp: str
    group_name: str
    sender: str
    phone_number: str
    message: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    analysis: BaseModel  # Dynamically created PadelGameAnalysis model

@dataclass
class UserPreferences:
    """User's padel game preferences."""
    level: str = "C1/4"
    acceptable_levels: List[str] = None
    time_window: tuple = (18, 22)  # Evening: 18:00-22:00
    players_needed: tuple = (1, 2)
    
    def __post_init__(self):
        if self.acceptable_levels is None:
            self.acceptable_levels = [
                "3.5-4", "B2-C1", "C", "C1", "C1-C2", "רמה 4", "level 4", "4"
            ]

# Import these after defining Match to avoid circular imports
from .gui_display import MatchDisplayWindow
from .match_tracker import MatchTracker

__all__ = ["MatchDisplayWindow", "MatchTracker", "Match", "UserPreferences"]
