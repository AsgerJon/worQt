"""
WMenuBar subclasses 'QMenuBar' and 'BarMixin' and provides the menubar
used by the main application menu.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar
from icecream import ic
from worktoy.desc import AttriBox
from worktoy.dispatch import overload

from . import MenusMixin, WAction, BarMixin
from ...utils import WFont

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, Type, TypeAlias

  IntBox: TypeAlias = Union[AttriBox, int]


class WMenuBar(QMenuBar, BarMixin):
  """
  WMenuBar subclasses 'QMenuBar' and 'BarMixin' and provides the menubar
  used by the main application menu.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_height__: int = 22
  __fallback_width__: int = 0

  #  Public Variables
  minHeight: IntBox = AttriBox[int](__fallback_height__)
  minWidth: IntBox = AttriBox[int](__fallback_width__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    baseSize = super().sizeHint()
    width = max(self.minWidth, baseSize.width())
    height = max(self.minHeight, baseSize.height())
    return QSize(width, height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    pass
