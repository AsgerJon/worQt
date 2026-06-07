"""
The 'worQt.utils.geom' package provides plain geometric value types -
'Point2D', 'Size' and 'Rect' - backed by Qt's value classes but built on
'BaseObject' with overloaded constructors. ('Point' is an alias of
'Point2D'.) Further types (insets, rounded rects, colors) are added here as
they are needed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._point_2d import Point2D
from ._vector_2d import Vector2D
from ._size import Size
from ._rect import Rect
from ._rounded_rect import RoundedRect
from ._in_sets import InSets
from .._color import Color
from ._box_dims import BoxDims
from ._box_model import BoxModel
from ._box_color import BoxColor

Point = Point2D

__all__ = [
  'Point2D',
  'Point',
  'Vector2D',
  'Size',
  'Rect',
  'RoundedRect',
  'InSets',
  'Color',
  'BoxDims',
  'BoxModel',
  'BoxColor',
]
