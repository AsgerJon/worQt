"""
The 'worQt.waitaminute' package provides custom exception classes used across
the worQt library.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._duplicate_connection_error import DuplicateConnectionError
from ._empty_layout_exception import EmptyLayoutException

__all__ = [
    'DuplicateConnectionError',
    'EmptyLayoutException',
]
