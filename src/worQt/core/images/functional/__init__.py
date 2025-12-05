"""
The 'worQt.math.images.functional' module provides functional utilities for
image processing.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._pil_to_tensor import pilToTensor
from ._tensor_to_pil import tensorToPIL
from ._plane_conv import planeConv

__all__ = [
    'pilToTensor',
    'tensorToPIL',
    'planeConv',
]
