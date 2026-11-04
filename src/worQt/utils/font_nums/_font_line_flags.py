"""
FontLineFlags enumerates the combinations of line augmentations for
'QFont' objects. 'Line augmentation' refers to: 'underline', 'overline'
and 'strikeout' (or 'strikethrough').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from worktoy.keenum import KeeFlags, KeeFlag

if TYPE_CHECKING:  # pragma: no cover
  pass


class FontLineFlags(KeeFlags):
  """
  FontLineFlags enumerates the combinations of line augmentations for
  'QFont' objects. 'Line augmentation' refers to: 'underline', 'overline'
  and 'strikeout' (or 'strikethrough').
  """

  UNDERLINE = KeeFlag()
  STRIKEOUT = KeeFlag()
  OVERLINE = KeeFlag()

  def apply(self, font: QFont, ) -> QFont:
    """
    The 'apply' method gives 'font' exactly the lines in these flags -
    each of underline, strike-out and overline on or off - and returns it.
    A combination such as 'UNDERLINE | OVERLINE' sets both.
    """
    cls = type(self)
    QFont.setUnderline(font, True if self & cls.UNDERLINE else False)
    QFont.setStrikeOut(font, True if self & cls.STRIKEOUT else False)
    QFont.setOverline(font, True if self & cls.OVERLINE else False)
    return font
