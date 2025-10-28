"""Simple background execution utilities."""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

executor = ThreadPoolExecutor(max_workers=2)
_application = None


def init_app(app) -> None:
    """Store application reference for background tasks."""
    global _application
    _application = app


def submit(func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """Submit a callable to run within the app context."""
    if _application is None:
        raise RuntimeError("Background task system not initialized.")

    def runner() -> None:
        with _application.app_context():
            func(*args, **kwargs)

    executor.submit(runner)
