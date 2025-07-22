"""
The 'worQt.widgets.paintMeLike' package provides modular painting
operations implemented as descriptors allowing widgets to build up their
painting operation. Painting operations may allow custom values to be set
during instantiations. They might also read certain attributes from the
owning widgets.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._abstract_paint_me_like import AbstractPaintMeLike

__all__ = [
    'AbstractPaintMeLike',
]
