"""
HSpacer provides a horizontal spacer widget locked to a set width, but free
to expand vertically as needed.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QSize

from PySide6.QtWidgets import QSizePolicy, QWidget

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.utilities import maybe

if TYPE_CHECKING:  # pragma: no cover
  pass


class HSpacer(QWidget):
  """
  HSpacer provides a horizontal spacer widget locked to a set width, but free
  to expand vertically as needed.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_width__ = 20

  #  Private Variables
  __fixed_width__ = None

  #  Public Variables
  fixedWidth = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @fixedWidth.GET
  def _getFixedWidth(self) -> int:
    return maybe(self.__fixed_width__, self.__fallback_width__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, parent: QWidget, width: int) -> None:
    super().__init__(parent)
    self.__fixed_width__ = width
    HPol = QSizePolicy.Policy.Fixed
    VPol = QSizePolicy.Policy.MinimumExpanding
    self.setSizePolicy(QSizePolicy(HPol, VPol))
    self.setFixedWidth(self.__fixed_width__)
    self.setMinimumHeight(20)
