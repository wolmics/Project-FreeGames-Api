"""Function to create a module wide logger with ntfy error handling."""

from os import makedirs
import logging
import requests
from config import Config


class NtfyHandler(logging.Handler):
    """Class to bind ntfy to the logging handler if an error occurs."""

    def __init__(self):
        super().__init__()
        ntfy_config = Config.get_ntfy()

        self.topic_url: str = ntfy_config.url
        self.token: str = ntfy_config.token

        self.enabled: bool = ntfy_config.url != ""

    def emit(self, record):
        log_entry = self.format(record)
        headers = {}

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = requests.post(
                self.topic_url,
                data=log_entry.encode("utf-8"),
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[Logger] Failed to send to ntfy: {e}")


def setup_logger(name: str) -> logging.Logger:
    """Setup logger with ntfy error handling and returns it."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )

        # Console handler (everything)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Ntfy handler (ERROR and above)
        ntfy_handler = NtfyHandler()
        if ntfy_handler.enabled:
            ntfy_handler.setLevel(logging.ERROR)
            ntfy_handler.setFormatter(formatter)
            logger.addHandler(ntfy_handler)

        # File handler (WARNING and above)
        log_folder = Config.get_destinations().output_folder

        makedirs(log_folder, exist_ok=True)
        file_handler = logging.FileHandler(log_folder / "error.log")
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
8