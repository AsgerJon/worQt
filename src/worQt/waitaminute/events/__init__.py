"""
The 'worQt.waitaminute.events' package provides custom exceptions raised
by widgets during the event loop which allows for specialized routing to
reach error handling on the application level.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._event_exception import EventException
from ._keyboard_exception import KeyboardException
from ._mouse_exception import MouseException
from ._paint_exception import PaintException
from ._invalid_size_policy import InvalidSizePolicy

__all__ = [
  'EventException',
  'KeyboardException',
  'MouseException',
  'PaintException',
  'InvalidSizePolicy',
]
