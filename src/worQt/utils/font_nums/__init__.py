"""
The 'worQt.utils.font_nums' package provides the font vocabulary 'WFont' is
built from: the weight, style and line enumerations, the generic families
('SERIF', 'SANS', 'MONO') and the 'FontFamily' lookup of what is installed.
Nothing here touches Qt's font database at import time; families are found
when a font is built, once a 'QApplication' exists.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._font_family import FontFamily
from ._generic_family_num import GenericFamilyNum
from ._font_weight_num import FontWeightNum
from ._font_style_num import FontStyleNum
from ._font_line_flags import FontLineFlags

__all__ = [
  'FontFamily',
  'GenericFamilyNum',
  'FontWeightNum',
  'FontStyleNum',
  'FontLineFlags',
]
