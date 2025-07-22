"""
Margin provides a dataclass for margins
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QMargins, QMarginsF
from worktoy.desc import Field
from worktoy.ezdata import EZData


class Margin(EZData):
  """Margin provides a dataclass for margins."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Slots
  left = 0
  top = 0
  right = 0
  bottom = 0

  #  Public Variables
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQMargins(self) -> QMargins:
    """Get the QMargins object."""
    return QMargins(self.left, self.top, self.right, self.bottom)

  @QF.GET
  def _getQMarginsF(self) -> QMarginsF:
    """Get the QMarginsF object."""
    return QMarginsF(self.left, self.top, self.right, self.bottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def fromQMargins(cls, margins: QMargins) -> Margin:
    """Create a Margin from QMargins."""
    return cls(
        margins.left(),
        margins.top(),
        margins.right(),
        margins.bottom()
    )

  @classmethod
  def fromQMarginsF(cls, margins: QMarginsF) -> Margin:
    """Create a Margin from QMarginsF."""
    return cls(
        margins.left(),
        margins.top(),
        margins.right(),
        margins.bottom()
    )
