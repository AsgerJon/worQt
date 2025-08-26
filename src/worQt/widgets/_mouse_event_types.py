"""
This module provides event type groups.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QEvent

_press = QEvent.Type.MouseButtonPress
_doubleClick = QEvent.Type.MouseButtonDblClick
PRESS_TYPES = frozenset({_press, _doubleClick})
RELEASE_TYPES = frozenset({QEvent.Type.MouseButtonRelease, })
MOVE_TYPES = frozenset({QEvent.Type.MouseMove, })
ENTER_TYPES = frozenset({QEvent.Type.Enter, })
LEAVE_TYPES = frozenset({QEvent.Type.Leave, })

__all__ = [
    'PRESS_TYPES',
    'RELEASE_TYPES',
    'MOVE_TYPES',
    'ENTER_TYPES',
    'LEAVE_TYPES',
]
