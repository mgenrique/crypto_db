"""Top-level `src.api` package for API modules.

This file makes `src.api` a proper Python package so absolute imports
like `from src.api.v1 import router` work when executing from the
project root.
"""

__all__ = [
    "v1",
    "connectors",
]
