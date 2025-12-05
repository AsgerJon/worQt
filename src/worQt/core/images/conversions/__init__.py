"""
The 'worQt.core.images.conversions' provides conversions from the ground
truth RGB format to other color formats.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._linear_light import LinearLight
from ._ok_lab import OKLab

__all__ = [
    'LinearLight',
    'OKLab',
]
