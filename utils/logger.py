"""
Unified logger for Auto-SLR Pipeline with dual output:
1. File logging to logs/slr_pipeline.log
2. In-memory buffer for Streamlit UI streaming
"""

import logging
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional


class SLRLogger:
    """Singleton logger with file and UI buffer outputs."""

    _instance: Optional['SLRLogger'] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.ui_buffer = deque(maxlen=50)  # Keep last 50 logs for UI
        self.buffer_lock = Lock()

        # Setup file logger
        self._setup_file_logger()

    def _setup_file_logger(self):
        """Configure file logging."""
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "slr_pipeline.log"

        # Create logger
        self.logger = logging.getLogger("slr_pipeline")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler (optional, for debugging)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _add_to_ui_buffer(self, level: str, message: str):
        """Add log entry to UI buffer."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted = f"[{timestamp}] {level.upper()}: {message}"

        with self.buffer_lock:
            self.ui_buffer.append(formatted)

    def info(self, message: str):
        """Log info level message."""
        self.logger.info(message)
        self._add_to_ui_buffer("info", message)

    def warning(self, message: str):
        """Log warning level message."""
        self.logger.warning(message)
        self._add_to_ui_buffer("warning", message)

    def error(self, message: str, exc_info: bool = False):
        """Log error level message."""
        self.logger.error(message, exc_info=exc_info)
        self._add_to_ui_buffer("error", message)

    def debug(self, message: str):
        """Log debug level message."""
        self.logger.debug(message)
        # Don't add debug to UI buffer to reduce noise

    def agent_thinking(self, agent_name: str, thinking: str):
        """Log agent thinking process (special format for UI)."""
        message = f"🤖 {agent_name}: {thinking}"
        self.logger.info(message)
        self._add_to_ui_buffer("agent", message)

    def get_ui_logs(self) -> list:
        """Get all logs from UI buffer (thread-safe)."""
        with self.buffer_lock:
            return list(self.ui_buffer)

    def clear_ui_buffer(self):
        """Clear UI buffer (useful for new sessions)."""
        with self.buffer_lock:
            self.ui_buffer.clear()


# Singleton accessor
_logger_instance = None

def get_logger() -> SLRLogger:
    """Get the singleton logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SLRLogger()
    return _logger_instance


# Test the logger
if __name__ == "__main__":
    logger = get_logger()
    logger.info("Logger initialized successfully")
    logger.agent_thinking("Test Agent", "Testing logger functionality")
    logger.warning("This is a warning")
    logger.error("This is an error")

    print("\n--- UI Buffer Contents ---")
    for log in logger.get_ui_logs():
        print(log)
