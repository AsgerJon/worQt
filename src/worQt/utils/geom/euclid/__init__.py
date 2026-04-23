"""
The 'worQt.utils.geom.euclid' package provides the custom metaclass system
used by the EuclideanObject class. This system along with the 'Dimension'
descriptor  implementation provides an automatic and powerful creation of
geometric dimensional objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._dimension import Dimension
from ._dim_hook import DimHook
from ._euclidian_space import EuclidianSpace
from ._euclidian_metaclass import EuclidianMetaclass
from ._euclidean_object import EuclideanObject

__all__ = [
  'Dimension',
  'DimHook',
  'EuclidianSpace',
  'EuclidianMetaclass',
  'EuclideanObject',
]
