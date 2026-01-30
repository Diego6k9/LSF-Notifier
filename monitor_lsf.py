import logging
import signal
import sys
import time
from typing import Optional
from urllib.parse import urlparse

import winsound
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException,
                                        WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from config import (
    CHECK_INTERVAL,
    SOUND_FREQUENCY,
    SOUND_DURATION,
    WAIT_TIMEOUT,
    LOGIN_MAX_WAIT,
    USERNAME,
    PASSWORD,
    LOGIN_PAGE,
    validate_required_settings,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure required settings are present early
try:
    validate_required_settings()
except Exception as e:
    logger.error(str(e))
    sys.exit(1)


# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """
    Handle a received signal and initiate a graceful shutdown.

    The function is invoked when the process receives specific signals (e.g.,
    SIGINT, SIGTERM). It logs a message indicating that a shutdown signal
    has been received and sets a global flag to stop the application's
    execution safely.

    :param signum: The number of the received signal.
    :type signum: int
    :param frame: The current stack frame when the signal was received.
    :type frame: FrameType
    :return: None
    """
    global running
    logger.info("Shutdown signal received. Exiting gracefully...")
    running = False


def setup_driver() -> WebDriver:
    """
    Sets up and initializes a Selenium WebDriver for Chrome with predefined configurations.

    The function configures the WebDriver with specific Chrome options to improve stability
    and compatibility, such as disabling extensions, GPU usage, and running the browser in
    a sandboxed environment. It also installs and uses the latest version of the ChromeDriver
    using `webdriver_manager`.

    :raises WebDriverException: If the WebDriver fails to initialize due to an error.

    :return: Configured Selenium WebDriver instance.
    :rtype: WebDriver
    """
    options = Options()
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)  # Set implicit wait timeout
        return driver
    except WebDriverException as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        sys.exit(1)


def wait_for_element(driver: WebDriver, by: By, value: str, timeout: int = WAIT_TIMEOUT):
    """
    Waits for a web element to be present in the DOM and visible on the page within the
    specified timeout period using the given locator strategy.

    :param driver: The WebDriver instance driving the browser.
    :param by: The locating mechanism to use for finding the element.
               Example: By.ID, By.CSS_SELECTOR, etc.
    :param value: The locator value to locate the desired element.
    :param timeout: The maximum number of seconds to wait for the element to appear.
                    Defaults to a predefined constant `WAIT_TIMEOUT`.
    :return: The web element once it is located and becomes present in the DOM.
    :rtype: WebElement
    """
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def wait_for_elements(driver: WebDriver, by: By, value: str, timeout: int = WAIT_TIMEOUT):
    """
    Waits for the presence of all elements matching the specified locator on the page
    within the given timeout period.

    This function uses explicit waits to ensure that all desired elements are located
    before proceeding, improving the reliability of interactions with web elements.

    :param driver: The WebDriver instance used to interact with the browser.
    :param by: The method used to locate elements, such as By.ID, By.XPATH, etc.
    :param value: The locator string used to identify the target elements.
    :param timeout: Optional; Maximum time (in seconds) to wait for the elements to appear.
                    Defaults to WAIT_TIMEOUT.
    :return: A list of WebElement instances representing the located elements.
    """
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((by, value))
    )


def _get_netloc(url: Optional[str]) -> Optional[str]:
    """
    Extracts the network location (netloc) from a given URL string.

    The function processes the input URL and extracts its netloc part after
    parsing. It gracefully handles invalid or empty URL inputs, returning None
    if the operation fails.

    :param url: The input URL string. If None or an empty string is provided,
        the function will attempt to process a default empty string.
    :type url: Optional[str]
    :return: The lowercase netloc part of the parsed URL, or None if extraction
        fails.
    :rtype: Optional[str]
    """
    try:
        return urlparse(url or "").netloc.lower()
    except Exception:
        return None


def _post_login_ready(driver: WebDriver, target_host: Optional[str]) -> bool:
    """
    Determines if the login process has completed successfully by checking either the target host in the
    current URL or the presence of specific known elements on the page.

    :param driver: WebDriver instance responsible for controlling the browser.
    :type driver: WebDriver
    :param target_host: Optional string indicating the expected host in the URL after login.
    :type target_host: Optional[str]
    :return: Boolean indicating whether login is complete successfully.
    :rtype: bool
    """
    # If Azure opened a new tab/window, switch to the newest one.
    try:
        handles = driver.window_handles
        if handles:
            driver.switch_to.window(handles[-1])
    except Exception:
        pass

    # Check URL host first
    try:
        current_url = driver.current_url or ""
    except Exception:
        current_url = ""

    if target_host and target_host in current_url:
        return True

    # Or check for known LSF page elements
    try:
        if (
            driver.find_elements(By.CLASS_NAME, 'auflistung') or
            driver.find_elements(By.CLASS_NAME, 'treelist') or
            driver.find_elements(By.CLASS_NAME, 'content')
        ):
            return True
    except Exception:
        pass

    return False


def wait_until_post_login_ready(driver: WebDriver, timeout: int = LOGIN_MAX_WAIT) -> None:
    """
    Waits for the post-login process to complete within a specified timeout period.

    This function blocks execution until post-login readiness is confirmed or the
    timeout is exceeded. It utilizes a WebDriver instance to monitor the state after
    authentication, such as multi-factor authentication completion or other post-login
    page readiness.

    :param driver: The WebDriver instance controlling the browser session.
    :type driver: WebDriver
    :param timeout: The maximum time, in seconds, to wait for post-login readiness.
    :type timeout: int
    :return: None
    """
    target_host = _get_netloc(LOGIN_PAGE)
    logger.info(f"Waiting for post-login to complete (timeout {timeout}s)...")
    print("\033[93m" + time.strftime("%d.%m.%Y %H:%M:%S") + f" - Waiting for login/MFA to finish (up to {timeout}s)..." + "\033[0m")

    WebDriverWait(driver, timeout, poll_frequency=1).until(
        lambda d: _post_login_ready(d, target_host)
    )

    logger.info("Post-login detected; proceeding.")
    print("\033[92m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - Post-login detected; continuing..." + "\033[0m")


def get_initial_content(driver: WebDriver) -> Optional[str]:
    """
    Extracts the initial page content post-login by automating navigation through the
    login process and subsequent menu interactions in a web application accessed via
    a web driver. The method handles browser automation, user authentication, and
    menu traversal to locate and retrieve the required content.

    :param driver: The WebDriver instance used to control the browser.
    :type driver: WebDriver

    :return: The content of the current page as a string or None if the required page
             content could not be retrieved.
    :rtype: Optional[str]
    """
    try:
        logger.info("Navigating to login page")
        driver.get(LOGIN_PAGE)

        wait_for_element(driver, By.CLASS_NAME, 'azure').click()

        logger.info("Logging in")
        wait_for_element(driver, By.ID, 'i0116').send_keys(USERNAME)
        wait_for_element(driver, By.ID, 'idSIButton9').click()

        time.sleep(1)
        wait_for_element(driver, By.ID, 'i0118').send_keys(PASSWORD)
        wait_for_element(driver, By.ID, 'idSIButton9').click()

        # Automatically wait for login/MFA/redirects to complete
        try:
            wait_until_post_login_ready(driver, LOGIN_MAX_WAIT)
        except TimeoutException:
            # As a last resort, allow manual confirmation from terminal
            logger.warning("Timed out waiting for post-login; manual confirmation may be required.")
            print("\033[93m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - If login is complete in the browser, press Enter in this terminal to continue..." + "\033[0m")
            try:
                input()
            except Exception:
                pass

        # Navigate to grades page
        link_elements = wait_for_elements(driver, By.CLASS_NAME, 'auflistung')

        if len(link_elements) >= 2:
            logger.info("Navigating through menu options")
            second_link = link_elements[1]
            second_link.click()

            link_elements = wait_for_elements(driver, By.CLASS_NAME, 'auflistung')

            for link in link_elements:
                if "Notenspiegel" in link.text:
                    link.click()
                    break

            treelist_element = wait_for_element(driver, By.CLASS_NAME, 'treelist')
            treelist_element.find_element(By.TAG_NAME, 'a').click()

            return get_current_content(driver)
        else:
            logger.error("Navigation menu not found after login")
            return None

    except (NoSuchElementException, TimeoutException) as e:
        logger.error(f"Error during navigation: {e}")
        return None


def get_current_content(driver: WebDriver) -> str:
    """
    Extracts the text content of an HTML element with the class name 'content' from the current
    browser instance.

    This function waits for the specified element to be available on the page before extracting
    its text. If the element is not found within the defined timeout or an error occurs during
    execution, an empty string is returned, and the error is logged.

    :param driver: The WebDriver instance representing the current browser session.
    :type driver: WebDriver
    :return: The textual content of the HTML element with the class name 'content'. Returns an
        empty string if the element is not found or an error occurs.
    :rtype: str
    """
    try:
        content_element = wait_for_element(driver, By.CLASS_NAME, 'content')
        return content_element.text
    except (NoSuchElementException, TimeoutException) as e:
        logger.error(f"Error getting page content: {e}")
        return ""


def play_sound():
    """
    Plays a sound using a beep with a specified frequency and duration.

    Tries to play a sound with specified parameters. If an exception occurs
    during the sound playback, the error is logged.

    :raises Exception: Logs the error if sound playback fails.
    """
    try:
        winsound.Beep(SOUND_FREQUENCY, SOUND_DURATION)
    except Exception as e:
        logger.error(f"Error playing sound: {e}")


def monitor_page():
    """
    Monitors a web page for changes in content with periodic refresh operations. The function uses a Selenium web
    driver to load and refresh the target page, detects content changes, and takes corresponding actions, such as
    logging the changes and playing a notification sound. The process runs continuously until interrupted or stopped.

    Registers handlers for SIGINT and SIGTERM signals to facilitate graceful shutdown. Handles WebDriver-related
    exceptions and recovers by reinitializing the web driver to ensure uninterrupted monitoring.

    :raises WebDriverException: Raised if there are issues during Selenium web driver operations. The function
                                 recovers automatically from this error.

    :raises Exception: Raised for any unexpected issues during execution. Such exceptions are logged,
                       and resources are cleaned up before shutdown.
    """
    driver = None
    try:
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("Starting LSF monitor")
        print("\033[96m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - Starting LSF monitor" + "\033[0m")
        driver = setup_driver()

        initial_content = get_initial_content(driver)
        if not initial_content:
            logger.error("Failed to get initial content. Exiting.")
            print("\033[91m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - Failed to get initial content. Exiting." + "\033[0m")
            return

        logger.info("Initial content retrieved. Monitoring for changes...")
        print("\033[96m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - Initial content retrieved. Monitoring for changes..." + "\033[0m")

        while running:
            try:
                start_time = time.time()

                logger.info("Refreshing page")
                print("\033[94m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - Refreshing page" + "\033[0m")
                driver.refresh()

                current_content = get_current_content(driver)

                if current_content != initial_content:
                    print("\033[92m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - Changes detected!" + "\033[0m")
                    logger.info("Changes detected!")
                    play_sound()
                    initial_content = current_content
                else:
                    print("\033[91m" + time.strftime("%d.%m.%Y %H:%M:%S") + " - No changes detected" + "\033[0m")
                    logger.info("No changes detected")

                # Calculate time elapsed and sleep only for the remaining time
                elapsed_time = time.time() - start_time
                sleep_time = max(0, CHECK_INTERVAL - elapsed_time)
                logger.info(f"Operations took {elapsed_time:.2f} seconds, sleeping for {sleep_time:.2f} seconds")
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except WebDriverException as e:
                logger.error(f"WebDriver error during monitoring: {e}")
                # Try to recover by reinitializing the driver
                if driver:
                    driver.quit()
                driver = setup_driver()
                initial_content = get_initial_content(driver)

                # Log recovery status with color
                print("\033[93m" + time.strftime("%d-%m-%Y %H:%M:%S") + " - Recovered from error, continuing monitoring" + "\033[0m")

                # Calculate time elapsed since start of this iteration and adjust sleep time
                elapsed_time = time.time() - start_time
                sleep_time = max(0, CHECK_INTERVAL - elapsed_time)
                logger.info(f"Recovery took {elapsed_time:.2f} seconds, sleeping for {sleep_time:.2f} seconds")
                if sleep_time > 0:
                    time.sleep(sleep_time)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down")
        if driver:
            driver.quit()


if __name__ == '__main__':
    try:
        monitor_page()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
