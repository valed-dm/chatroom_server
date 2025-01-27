import logging
import logging.config
from pathlib import Path

import tomllib  # For Python 3.11+. Use `toml` package if older.


def setup_logging_from_pyproject():
    """Set up logging configuration from pyproject.toml."""
    with Path.open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    # Extract logging settings
    logging_config = config.get("tool", {}).get("logging", {})
    log_level = logging_config.get("level", "INFO")
    log_format = logging_config.get(
        "log_format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(
        logging_config.get("console_handler", {}).get("level", "INFO"),
    )
    console_handler.setFormatter(logging.Formatter(log_format))

    # File handler
    file_handler = None
    if logging_config.get("file_handler", {}).get("enabled", False):
        filename = logging_config.get("file_handler", {}).get("filename", "app.log")
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(
            logging_config.get("file_handler", {}).get("level", "INFO"),
        )
        file_handler.setFormatter(logging.Formatter(log_format))

    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)

    logging.info("Logging setup complete.")
