# LSF-Notifier

A Python application that monitors the LSF (Lehre, Studium, Forschung) system for changes in grades and notifies the user with a sound alert when changes are detected.

## Features

- Automatically logs into the LSF system
- Navigates to the grades page
- Periodically checks for changes in grades
- Plays a sound alert when changes are detected
- Graceful error handling and recovery
- Configurable monitoring interval and sound settings

## Requirements

- Python 3.6+
- Chrome browser
- ChromeDriver (automatically installed by webdriver-manager)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/LSF-Notifier.git
   cd LSF-Notifier
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example environment file and fill in your values:
   ```
   copy .env.example .env
   ```
   Then edit `.env` and set `USERNAME_LSF`, `PASSWORD_LSF`, and `LSF_LOGIN_PAGE`.

## Configuration

Configuration parameters (including credentials and the login URL) are centralized in `config.py`. Values are read from your `.env` file at runtime; nothing is hard-coded.

Notes:
- Keep your `.env` file out of version control.
- The app validates that `USERNAME_LSF`, `PASSWORD_LSF`, and `LSF_LOGIN_PAGE` are present at startup and will exit with a clear message if any are missing.
 - A sample `.env.example` is provided; copy it to `.env` and fill in your values.

The following parameters can be configured in the `.env` file:

- `USERNAME_LSF`: Your LSF username
- `PASSWORD_LSF`: Your LSF password
- `LSF_LOGIN_PAGE`: The URL of the LSF login page
- `CHECK_INTERVAL`: Time between checks in seconds (default: 30)
- `SOUND_FREQUENCY`: Frequency of the alert sound in Hz (default: 2500)
- `SOUND_DURATION`: Duration of the alert sound in milliseconds (default: 10000)
- `WAIT_TIMEOUT`: Maximum time to wait for elements to load in seconds (default: 10)
- `LOGIN_MAX_WAIT`: Maximum time to wait for post-login completion (MFA/redirects) in seconds (default: 300)

## Usage

1. Edit your `.env` file with your credentials and login page:
   ```
   USERNAME_LSF=your_username
   PASSWORD_LSF=your_password
   LSF_LOGIN_PAGE='https://lsf.your-university.de/qisserver/rds?state=user&type=0'
   ```

2. (Optional) Adjust other settings in `.env` (e.g., `CHECK_INTERVAL`, `SOUND_FREQUENCY`, `LOGIN_MAX_WAIT`).

3. Activate your virtual environment (if not already active):
   ```
   .venv\Scripts\activate
   ```

4. Run the script:
   ```
   python monitor_lsf.py
   ```

After starting, the script will:
1. Open a Chrome browser window
2. Log into the LSF system (handles MFA/redirects automatically up to `LOGIN_MAX_WAIT`)
3. Navigate to the grades page
4. Start monitoring for changes
5. Play a sound alert when changes are detected

To stop the script, press `Ctrl+C` in the terminal.

## Troubleshooting

If you encounter any issues:

1. Check your LSF credentials in the `.env` file
2. Ensure you have a stable internet connection
3. Check the console output for error messages
4. Make sure Chrome is installed and up to date

## License

This project is licensed under the MIT License - see the LICENSE file for details.