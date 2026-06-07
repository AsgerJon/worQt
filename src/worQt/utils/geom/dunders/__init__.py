"""
The 'worQt.utils.geom.dunders' package provides type hints for dunder
methods. Because of how terrible 'typing' actually is at the edges,
we contain these in their own subpackage.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from ._typing_gymnastics import *

Bases = object()
DimDict = object()
DimTuple = object()
Dims = object()
Scalar = object()
CLS = object()
Cls = object()
INIT = object()
ITER = object()

__all__ = [
  'Bases',
  'DimDict',
  'DimTuple',
  'Dims',
  'Scalar',
  'CLS',
  'Cls',
  'INIT',
  'ITER',
]
