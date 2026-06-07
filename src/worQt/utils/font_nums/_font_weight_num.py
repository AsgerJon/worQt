"""
FontWeightNum enumerates font weights. Values match QFont.Weight values.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from worktoy.dispatch import overload
from worktoy.keenum import Kee
from worktoy.waitaminute.keenum import KeeResolveError

# from ...paint_ops import TextPaintOp
from . import FontMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class FontWeightNum(FontMeta.keeNum):
  """
  FontWeightNum enumerates font weights. Values match QFont.Weight values.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ENUMERATED MEMBERS   # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  THIN = Kee[QFont.Weight](QFont.Weight.Thin)
  EXTRA_LIGHT = Kee[QFont.Weight](QFont.Weight.ExtraLight)
  LIGHT = Kee[QFont.Weight](QFont.Weight.Light)
  NORMAL = Kee[QFont.Weight](QFont.Weight.Normal)
  MEDIUM = Kee[QFont.Weight](QFont.Weight.Medium)
  DEMI_BOLD = Kee[QFont.Weight](QFont.Weight.DemiBold)
  BOLD = Kee[QFont.Weight](QFont.Weight.Bold)
  EXTRA_BOLD = Kee[QFont.Weight](QFont.Weight.ExtraBold)
  BLACK = Kee[QFont.Weight](QFont.Weight.Black)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_resolve__(cls, weight: Any) -> FontWeightNum:
    for member in cls:
      if member.value == weight:
        return member
    raise KeeResolveError(cls, weight)

  @overload(QFont)
  def apply(self, font: QFont) -> None:
    font.setWeight(self.value)
