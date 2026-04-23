"""
WMenu subclasses "QMenu" and "MenusMixin" providing the base menu class
used by the menu implementations provided by the 'worQt.windows.menus'
package.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QMenu, QMenuBar
from icecream import ic
from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from . import MenusMixin, WAction, ActionMixin
from ...utils import WFont

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, Type, TypeAlias

  IntBox: TypeAlias = Union[AttriBox, int]


class WMenu(QMenu, ActionMixin):
  """
  WMenu subclasses "QMenu" and "MenusMixin" providing the base menu class
  used by the menu implementations provided by the 'worQt.windows.menus'
  package.
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

  def __init__(self, *args, **kwargs, ) -> None:
    super().__init__(*args, **kwargs)

  def addAction(self, *args, ) -> None:
    action, *_ = (*args, None)
    if not isinstance(action, QAction):
      raise TypeException('action', action, QAction)
    if isinstance(action, WAction):
      WAction.initUI(action)
      return QMenu.addAction(self, action)
    return QMenu.addAction(self, *args, )

  def sizeHint(self, ) -> QSize:
    baseSize = QMenu.sizeHint(self, )
    width = max(self.minWidth, baseSize.width())
    height = max(self.minHeight, baseSize.height())
    newSize = QSize(width, height)
    return newSize

  minimumSizeHint = sizeHint

  def initUI(self, ) -> None:
    name = self.fieldBox.getFieldName()
    name = str.replace(str.capitalize(name), '_', ' ')
    QMenu.setTitle(self, name)
    QMenu.setToolTip(self, self.tip)
