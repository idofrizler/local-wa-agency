# Padel Match Tracker - GUI Application

A specialized WhatsApp group monitor that finds padel game invitations matching your preferences and displays them in an interactive Hebrew RTL GUI.

## Features

- **Smart Matching**: AI-powered analysis of WhatsApp messages to find padel game invites
- **User Preferences**: Filter matches by skill level, time window, and player count
- **Hebrew RTL GUI**: Beautiful interface with right-to-left support
- **Confidence Levels**: Visual indicators (HIGH/MEDIUM/LOW) for match quality
- **Privacy Protection**: Toggle to hide/show sender names and phone numbers
- **Two Modes**: Historical scanning and live monitoring

## Running

### Historical Scan Mode

Scan past messages from configured groups:

```bash
python -m test_apps.padel.main scan-history --scrolls 5
```

This will:
1. Load historical messages by scrolling up in the chat
2. Analyze each message for padel game invites
3. Display matches in a GUI window with confidence indicators

### Live Monitoring Mode

Monitor groups for new messages in real-time:

```bash
python -m test_apps.padel.main monitor-live --interval 60
```

This will:
1. Check for new messages every 60 seconds
2. Analyze new messages as they arrive
3. Update the GUI window with new matches

## Configuration

### Scenario Configuration

The padel scenario is configured in `scenarios/padel.json`:

```json
{
  "prompt": "AI agent instructions...",
  "groups": ["Your Padel Group 1", "Your Padel Group 2"],
  "response_schema": { ... }
}
```

### User Preferences

Edit `test_apps/padel/__init__.py` to configure your personal preferences:

```python
@dataclass
class UserPreferences:
    level: str = "C1/4"                          # Your skill level
    acceptable_levels: List[str] = [...]         # Levels you'll play with
    time_window: tuple = (18, 22)                # Hours: 18:00-22:00
    players_needed: tuple = (1, 2)               # Need 1-2 players
```

## GUI Features

### Match Table Columns

- **רמת התאמה** (Confidence): HIGH ✓ / MEDIUM ~ / LOW ✗
- **תאריך ושעה** (Date & Time): When the game is scheduled
- **מיקום** (Location): Where the game will be played
- **טלפון** (Phone): Sender's phone number (toggle privacy)
- **שולח** (Sender): Message sender name (toggle privacy)
- **קבוצה** (Group): WhatsApp group name
- **שעת שליחה** (Sent Time): When the message was sent

### Privacy Toggle

Click "הצג שמות וטלפונים" (Show names and phones) to toggle between:
- **Hidden**: Shows `***` for privacy
- **Visible**: Shows actual names and phone numbers

### Message Details

Click any row to see:
- Full original message text
- AI reasoning for the match
- Breakdown of preference matches (level, time, player count)

## Architecture

```
test_apps/padel/
├── __init__.py           # Models (Match, UserPreferences)
├── main.py              # Entry point with CLI
├── gui_display.py       # Hebrew RTL GUI window
├── match_tracker.py     # Match tracking and console display
└── README.md           # This file
```

## Match Analysis

The AI agent evaluates messages based on:

1. **Is it a game invite?** - Not just chat or logistics
2. **Level match** - Does skill level align with your preferences?
3. **Time match** - Is it within your time window?
4. **Player count match** - Do they need the right number of players?

Confidence levels:
- **HIGH**: All criteria match strongly
- **MEDIUM**: Most criteria match or some uncertainty
- **LOW**: Weak match or missing information

## Requirements

- Python 3.11+
- Ollama running locally with a compatible model
- WhatsApp account (QR code login on first run)
- tkinter (usually included with Python)

## Example Usage

```bash
# Quick scan of recent messages
python -m test_apps.padel.main scan-history --scrolls 3

# Deep scan of history
python -m test_apps.padel.main scan-history --scrolls 10

# Live monitoring (check every minute)
python -m test_apps.padel.main monitor-live --interval 60

# Live monitoring (check every 30 seconds)
python -m test_apps.padel.main monitor-live --interval 30
```

## Customization

To create your own scenario-specific GUI app:

1. Copy this package as a template
2. Define your models in `__init__.py`
3. Create your GUI in a separate file
4. Build your `main.py` with CLI arguments
5. Configure your scenario in `scenarios/your_scenario.json`

The generic framework (`src/`) provides all the WhatsApp scanning and AI analysis - you just need to add your domain-specific UI!
