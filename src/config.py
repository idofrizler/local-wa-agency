"""
Configuration management for WhatsApp Padel Match Tracker.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from src.models import UserPreferences

# Load environment variables
load_dotenv()

class Config:
    """Configuration loader and manager."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.groups_file = self.base_dir / "config" / "groups.txt"
        self.session_dir = self.base_dir / "whatsapp_session"
        
        # Ollama configuration
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'gpt-oss:20b')
        
        # User preferences
        self.user_preferences = UserPreferences()
        
        # Scanning configuration
        self.default_scroll_count = 5
        self.default_monitor_interval = 60  # seconds
    
    def load_groups(self) -> List[str]:
        """Load WhatsApp group names from groups.txt file."""
        if not self.groups_file.exists():
            raise FileNotFoundError(
                f"Groups file not found: {self.groups_file}\n"
                f"Please create {self.groups_file} and add group names (one per line)."
            )
        
        groups = []
        with open(self.groups_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    groups.append(line)
        
        if not groups:
            raise ValueError(
                f"No groups found in {self.groups_file}\n"
                f"Please add at least one group name."
            )
        
        return groups
    
    def get_agent_instructions(self) -> str:
        """Get instructions for the AI agent based on user preferences."""
        prefs = self.user_preferences
        
        return f"""You are an expert padel game analyzer.

Your job is to analyze WhatsApp messages from padel groups and determine if they match a user's preferences.

USER PREFERENCES:
- Level: {prefs.level} (will accept: {', '.join(prefs.acceptable_levels)})
- Time: Evening games (or {prefs.time_window[0]}:00-{prefs.time_window[1]}:00 / {prefs.time_window[0] % 12 or 12} PM - {prefs.time_window[1] % 12 or 12} PM, if specific hours are mentioned)
- Players needed: {prefs.players_needed[0]}-{prefs.players_needed[1]} players

ANALYSIS STEPS:
1. First, determine if this is a padel game invite at all
2. Check if the level mentioned matches or is close to user's level
3. Check if the time is in the evening window
4. Check if they need {prefs.players_needed[0]}-{prefs.players_needed[1]} players
5. Extract the match date (today, tomorrow, specific date, or day of week). If not explicitly mentioned, infer from context (default to "today" if unclear)
6. Extract the match time or time range (specific time, time range, or time of day like "evening")
7. Extract the location/court name if mentioned (e.g., "Canada Center", "פאדלון", "Ramat Aviv", "בקאנדה")
8. Provide overall confidence: HIGH (all criteria match), MEDIUM (some match), LOW (few/none match)

Be thorough but concise in your reasoning.

IMPORTANT: Always extract match_date, match_time, and location even if not explicitly stated. Use context clues and reasonable defaults."""

# Global config instance
config = Config()
