"""
The 'worQt.events' module provides custom classes complementing the
default 'QEvent' system.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._abstract_event import AbstractEvent
from ._cursor_event import CursorEvent
from ._cursor_move import CursorMove
from ._cursor_press import CursorPress
from ._cursor_release import CursorRelease
from ._cursor_enter import CursorEnter
from ._cursor_leave import CursorLeave

__all__ = [
    'AbstractEvent',
    'CursorEvent',
    'CursorMove',
    'CursorPress',
    'CursorRelease',
    'CursorEnter',
    'CursorLeave',
]
