"""
The 'worQt.core' package provides core functionality for the worQt library.
These are used throughout the library without relying on other packages.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._parent import Parent
from ._shortcut import Shortcut
from ._rgba import RGBA
from ._font import Font

__all__ = [
    'Parent',
    'Shortcut',
    'RGBA',
    'Font',
]
