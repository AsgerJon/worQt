"""
FontWeightNum enumerates font weights. Values match QFont.Weight values.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self


class FontWeightNum(KeeNum):
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
  def __class_resolve__(cls, weight: Any) -> Self:
    """
    The '__class_resolve__' hook resolves a member from its 'QFont.Weight',
    which is what 'QFont.weight()' returns. Anything else is left to the
    normal resolution.
    """
    for member in cls:
      if member.value == weight:
        return member
    return NotImplemented

  def apply(self, font: QFont) -> None:
    """The 'apply' method sets this weight on 'font'. A plain method, not
    an '@overload': the dispatcher caches a bound method on the instance
    via 'setattr', which a frozen 'KeeNum' member rejects with
    'KeeWriteOnceError'."""
    font.setWeight(self.value)
