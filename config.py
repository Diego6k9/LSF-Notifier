import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Centralized configuration parameters
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))  # seconds
SOUND_FREQUENCY = int(os.getenv("SOUND_FREQUENCY", "2500"))  # Hz
SOUND_DURATION = int(os.getenv("SOUND_DURATION", "10000"))  # milliseconds
WAIT_TIMEOUT = int(os.getenv("WAIT_TIMEOUT", "10"))  # seconds
LOGIN_MAX_WAIT = int(os.getenv("LOGIN_MAX_WAIT", "300"))  # seconds to wait for post-login completion

# Credentials and URLs (sourced from environment / .env)
USERNAME = os.getenv("USERNAME_LSF")
PASSWORD = os.getenv("PASSWORD_LSF")
LOGIN_PAGE = os.getenv("LSF_LOGIN_PAGE")


def validate_required_settings() -> None:
    """
    Validates that all required settings are present and raises an error if any are missing.

    This function checks if specific environment variables defined in the
    application's configuration are populated. If any required variables are
    missing, it throws a `ValueError` indicating the missing keys.

    :raises ValueError: Indicates that one or more required settings are missing
        and specifies the missing keys from the environment.
    """
    required = {
        "USERNAME_LSF": USERNAME,
        "PASSWORD_LSF": PASSWORD,
        "LSF_LOGIN_PAGE": LOGIN_PAGE,
    }
    missing = [key for key, val in required.items() if not val]
    if missing:
        raise ValueError(
            "Missing required settings in .env: " + ", ".join(missing)
        )
