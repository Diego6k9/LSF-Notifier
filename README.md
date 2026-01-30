# LSF-Notifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python tool that monitors the LSF (Lehre, Studium, Forschung) system for grade changes and plays a sound alert when changes are detected.

## Features

- Logs into LSF and navigates to the grades page automatically
- Periodically checks for changes
- Plays a sound alert on detected changes
- Graceful error handling and recovery
- Configurable check interval and sound settings

## Requirements

- Python 3.6+
- Google Chrome
- ChromeDriver (installed automatically via `webdriver-manager`)

## Quick start

1. Clone and enter the project directory:
   ```
   git clone https://github.com/yourusername/LSF-Notifier.git
   cd LSF-Notifier
   ```
2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create your environment file from the example and fill in values:
   ```
   copy .env.example .env
   ```
5. Run the script:
   ```
   python monitor_lsf.py
   ```

## Configuration

Configuration is read from `.env` at runtime (see `config.py`). The app validates required values on startup.

- Required
  - `USERNAME_LSF`: LSF username
  - `PASSWORD_LSF`: LSF password
  - `LSF_LOGIN_PAGE`: LSF login URL
- Optional
  - `CHECK_INTERVAL`: Seconds between checks (default: 30)
  - `SOUND_FREQUENCY`: Alert frequency in Hz (default: 2500)
  - `SOUND_DURATION`: Alert duration in ms (default: 10000)
  - `WAIT_TIMEOUT`: Element wait timeout in seconds (default: 10)
  - `LOGIN_MAX_WAIT`: Max time to wait for post-login completion in seconds (default: 300)

Note: `.env.example` is provided. Keep your personal `.env` out of version control.

## Usage

1. Ensure `.env` is configured (see Configuration).
2. Activate the virtual environment (if not already active):
   ```
   .venv\Scripts\activate
   ```
3. Start monitoring:
   ```
   python monitor_lsf.py
   ```
4. Stop with `Ctrl+C` in the terminal.

## Troubleshooting

- Verify credentials and `LSF_LOGIN_PAGE` in `.env`
- Ensure a stable internet connection
- Check console output for error messages
- Make sure Chrome is installed and up to date

## License

MIT — see `LICENSE` for details.