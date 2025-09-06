"""
VSpacer provides a vertical spacer widget locked to a set height, but free
to expand horizontally as needed.
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


class VSpacer(QWidget):
  """
  VSpacer provides a vertical spacer widget locked to a set height, but free
  to expand horizontally as needed.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_height__ = 20

  #  Private Variables
  __fixed_height__ = None

  #  Public Variables
  fixedHeight = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @fixedHeight.GET
  def _getFixedHeight(self) -> int:
    return maybe(self.__fixed_height__, self.__fallback_height__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, parent: QWidget, height: int) -> None:
    super().__init__(parent)
    self.__fixed_height__ = height
    HPol = QSizePolicy.Policy.MinimumExpanding
    VPol = QSizePolicy.Policy.Fixed
    self.setSizePolicy(QSizePolicy(HPol, VPol))
    self.setFixedHeight(self.__fixed_height__)
    self.setMinimumWidth(20)
