"""
BaseWindow class for worQt.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from worQt.menus import MainMenuBar, MainStatusBar
from worQt.windows import AbstractWindow

if TYPE_CHECKING:  # pragma: no cover
  pass


class BaseWindow(AbstractWindow):
  """BaseWindow class for worQt."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  menus = AttriBox[MainMenuBar](THIS)
  status = AttriBox[MainStatusBar](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self) -> None:
    """
    Initialize the user interface of the window.
    This method sets up the main menu bar and status bar for the window.
    """
    self.setMenuBar(self.menus)
    self.setStatusBar(self.status)

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
    Show the window.
    This method is overridden to ensure that the window is displayed
    correctly
    with the main menu bar and status bar.
    """
    self.initUi()
    self.initLogic()
    AbstractWindow.show(self)
