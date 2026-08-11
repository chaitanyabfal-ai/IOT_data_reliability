"""Application package for IoT queuing project.

This file intentionally initializes the Python package for `app`.
"""

from .config import configure_logging

configure_logging()

__all__ = ["celery", "main", "tasks", "config"]
