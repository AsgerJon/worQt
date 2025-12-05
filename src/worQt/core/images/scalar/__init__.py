"""
The 'worQt.core.images.scalar' provides mappings from image tensors to
scalar fields.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._base_scalar import BaseScalar
from ._red import Red
from ._green import Green
from ._blue import Blue

__all__ = [
    'BaseScalar',
    'Red',
    'Green',
    'Blue',
]
