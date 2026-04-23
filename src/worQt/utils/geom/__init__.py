"""
The 'worQt.utils.geom' package provides geometric utilities for the 'worQt'
framework. It includes classes and functions for handling geometric shapes,
coordinates, and transformations.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from . import dunders, euclid
from ._point_2d import Point2D
from ._vector_2d import Vector2D
from ._size import Size
from ._line import Line
from ._segment import Segment
from ._rect import Rect
from ._rounded_rect import RoundedRect
from ._in_sets import InSets
from ._box_dims import BoxDims
from ._box_model import BoxModel
from worQt.utils._color import Color
from ._box_color import BoxColor

__all__ = [
  'dunders',
  'euclid',
  'Size',
  'Point2D',
  'Vector2D',
  'Line',
  'Segment',
  'Rect',
  'RoundedRect',
  'InSets',
  'BoxDims',
  'BoxModel',
  'Color',
  'BoxColor',
]
