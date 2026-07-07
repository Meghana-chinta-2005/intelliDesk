import logging
import sys
from src.config.config import settings


def setup_logging():
    """
    Sets up the application-wide logging configuration.
    Logs to both a file (defined in settings) with UTF-8 encoding and to standard stdout.
    """
    # Get the root logger
    root_logger = logging.getLogger()

    # Determine log level
    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    root_logger.setLevel(log_level)

    # Clean up any existing handlers to prevent duplicates
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # File Handler (logs to file in UTF-8)
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Stream Handler (logs to console stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
