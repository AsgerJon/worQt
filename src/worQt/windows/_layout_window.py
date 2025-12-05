"""
LayoutWindow provides the widgets and layouts for the main window of the
application. It subclasses 'BaseWindow' which provides the menus and bars,
and expects to be subclassed by the main window.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QGridLayout, QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from . import BaseWindow
from ..widgets import VSpacer, HSpacer, LabelWidget

if TYPE_CHECKING:  # pragma: no cover
  pass


class LayoutWindow(BaseWindow):
  """
  LayoutWindow provides the widgets and layouts for the main window of the
  application. It subclasses 'BaseWindow' which provides the menus and bars,
  and expects to be subclassed by the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  baseWidget = AttriBox[QWidget](THIS)
  baseLayout = AttriBox[QGridLayout]()
  welcomeLabel = AttriBox[LabelWidget]('Welcome to worQt!', THIS)
  topSpacer = AttriBox[VSpacer](THIS, 32)
  bottomSpacer = AttriBox[VSpacer](THIS, 32)
  leftSpacer = AttriBox[HSpacer](THIS, 32)
  rightSpacer = AttriBox[HSpacer](THIS, 32)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """
    Initialize the UI components of the LayoutWindow.
    This method sets up the base widget and layout for the main window.
    """
    super().initUi()
    self.baseWidget.setLayout(self.baseLayout)
    self.baseLayout.addWidget(self.topSpacer, 0, 1)
    self.baseLayout.addWidget(self.bottomSpacer, 3, 1)
    self.baseLayout.addWidget(self.leftSpacer, 1, 0, 2, 1)
    self.baseLayout.addWidget(self.rightSpacer, 1, 2, 2, 1)
    self.baseLayout.addWidget(self.welcomeLabel, 1, 1)
    self.setCentralWidget(self.baseWidget)
    self.setMinimumSize(QSize(1080, 720 + 64))

  def initLogic(self) -> None:
    """
    Initialize the logic components of the LayoutWindow.
    This method can be overridden by subclasses to add specific logic.
    """
    super().initLogic()
