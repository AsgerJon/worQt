"""
The 'worQt.geometry' module provides functionality for Euclidean geometry.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._point_2d import Point2D
from ._vector_2d import Vector2D
from ._line_2d import Line2D
from ._size import Size
from ._rect import Rect

__all__ = [
    'Point2D',
    'Vector2D',
    'Line2D',
    'Size',
    'Rect',
]
