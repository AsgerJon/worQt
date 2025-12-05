"""
The 'worQt.core.geometry' package provides classes related to geometries.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._base_dim import BaseDim
from ._two_dim import TwoDim
from ._four_dim import FourDim
from ._point import Point
from ._size import Size
from ._rect import Rect
from ._margins import Margins
from ._box_model import BoxModel

__all__ = [
    'BaseDim',
    'TwoDim',
    'FourDim',
    'Point',
    'Size',
    'Rect',
    'Margins',
    'BoxModel',
]
