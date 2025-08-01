"""
The 'worQt.nums' module provides enumerations of various enum types
used across the worQt library.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._resolve_qt_num import resolveQtNum
from ._mouse_button_state_num import MouseButtonStateNum
from ._key_num import KeyNum
from ._modifier import KeyMod
from ._font_families import FontFamilies
from ._font_family_num import FontFamilyNum
from ._horizontal_alignum import HorizontalAlignum
from ._vertical_alignum import VerticalAlignum
from ._alignum import Alignum
from ._mouse_button_num import MouseButtonNum

__all__ = [
    'resolveQtNum',
    'KeyNum',
    'KeyMod',
    'FontFamilies',
    'FontFamilyNum',
    'HorizontalAlignum',
    'VerticalAlignum',
    'Alignum',
    'MouseButtonNum',
    'MouseButtonStateNum',
]
