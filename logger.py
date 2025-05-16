"""
Logging configuration for TeleSync application.
"""

import logging

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_logger(module_name):
    """
    Returns a configured logger specific to the calling module.

    Args:
        module_name (str): Name of the module requesting a logger

    Returns:
        logging.Logger: A configured logger
    """
    return logging.getLogger(f"telesync.{module_name}")
