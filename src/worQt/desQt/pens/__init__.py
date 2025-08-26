"""
The 'worQt.desQt.pens' module provides 'QPen' instances through the
descriptor protocol.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._empty_pen import EmptyPen
from ._empty_brush import EmptyBrush

__all__ = [
    'EmptyPen',
    'EmptyBrush',
]
