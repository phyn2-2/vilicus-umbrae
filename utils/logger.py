"""Unified logging utility for Vilicus."""
import logging
import os

class VilicusLogger:
    """Smart logger with file and console output."""
    def __init__(self, config):
        self.log_level = config.get("steward", {}).get("log_level", "INFO")
        self.logger = logging.getLogger("vilicus")
        self.logger.setLevel(getattr(logging, self.log_level))

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level))
        console_format = logging.Formatter(
            '%(levelname)s | %(message)s'
        )
        console_handler.setFormatter(console_format)

        # File handler
        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/vilicus.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def critical(self, msg):
        self.logger.critical(msg)

# Singleton instance
_logger_instance = None

def get_logger(config=None):
    """Get or create logger instance."""
    global _logger_instance
    if _logger_instance is None and config is not None:
        _logger_instance = VilicusLogger(config)
    return _logger_instance



