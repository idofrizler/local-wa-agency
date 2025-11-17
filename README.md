# WhatsApp Padel Match Tracker

## Setup

1. Create and activate the virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Download the Playwright browsers (required before running the scanner):

```bash
playwright install
```

This step is intentionally separate from pip so Playwright can download the appropriate browser binaries for the host platform.

## Running

- Historical scan:

```bash
python main.py scan-history --scrolls <count>
```

- Live monitor:

```bash
python main.py monitor-live --interval <seconds>
