"""
BaseWindow class for worQt.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import QApplication
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from . import AbstractWindow
from ..menus import MainMenuBar

if TYPE_CHECKING:  # pragma: no cover
  pass


class BaseWindow(AbstractWindow):
  """BaseWindow class for worQt."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  mainMenuBar = AttriBox[MainMenuBar](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    AbstractWindow.__init__(self, *args, **kwargs)
    self.setMenuBar(self.mainMenuBar)
    self.mainMenuBar.help.aboutQtAction.triggered.connect(
        QApplication.aboutQt
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self) -> None:
    """
    Initialize the user interface of the window.
    This method sets up the main menu bar and status bar for the window.
    """

  def initLogic(self) -> None:
    """
    Initialize the logic of the window.
    This method is called after the user interface is set up.
    It can be used to connect signals and slots or perform other logic.
    """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def show(self) -> None:
    """
    This method is overridden to ensure that the window is displayed
    correctly with the main menu bar and status bar.
    """
    self.initUi()
    AbstractWindow.show(self)
    self.initLogic()
