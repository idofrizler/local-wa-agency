"""
Data models for the WhatsApp Padel Match Tracker.
"""
from dataclasses import dataclass
from typing import Literal, List
from enum import Enum
from pydantic import BaseModel, Field


class PadelGameAnalysis(BaseModel):
    """Structured analysis of a padel game invite message."""
    
    is_game_invite: bool = Field(
        description="Whether this is a padel game invite (true/false)"
    )
    level_match: bool = Field(
        description="Whether the game level matches user's level C1/4 (accepts 3.5-4, B2-C1, C, C1, C1-C2, level 4, 4+, 'רמה 4')"
    )
    time_match: bool = Field(
        description="Whether the game time is in evening (18:00-22:00)"
    )
    player_count_match: bool = Field(
        description="Whether they need 1-2 players"
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Overall match confidence level"
    )
    reasoning: str = Field(
        description="Brief explanation of the analysis (1-2 sentences)"
    )
    match_date: str = Field(
        default="",
        description="The date of the match (e.g., 'today', 'tomorrow', '10/11/2025', 'Sunday'). Infer from context if not explicit."
    )
    match_time: str = Field(
        default="",
        description="The time or time range of the match (e.g., '18:00', '18:00-20:00', 'evening', 'afternoon')"
    )
    location: str = Field(
        default="",
        description="The location/court where the match will be played (e.g., 'Canada Center', 'פאדלון', 'Ramat Aviv')"
    )


@dataclass
class Match:
    """Represents a potential padel game match."""
    timestamp: str
    group_name: str
    sender: str
    phone_number: str
    message: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    analysis: PadelGameAnalysis


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


class ScanMode(Enum):
    """Scanning mode for WhatsApp groups."""
    HISTORY = "history"
    LIVE = "live"
