"""BaseWindow provides an abstract baseclass containing the basic
functionalities, menus and status bar. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from abc import abstractmethod

from PySide6.QtCore import QObject, QThread, QCoreApplication
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow
from worktoy.attr import Field, AttriBox
from worktoy.parse import maybe
from worktoy.static import THIS
from worktoy.text import typeMsg

from worQt.window.menus import MenuBar

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class _Deps:
  """Private class listing objects for import. """
  __imported_objects__ = [
      QObject,
      QCoreApplication,
      QApplication,
      QAction,
      QWidget,
      QMainWindow,
      QThread,
      maybe,
      typeMsg,
      Field,
  ]


class BaseWindow(QMainWindow):
  """BaseWindow provides an abstract baseclass containing the basic
  functionalities, menus and status bar. """

  mainMenu = AttriBox[MenuBar](THIS)
  statusBar = AttriBox[QWidget](THIS)

  def initMenus(self, ) -> None:
    """Initialize the UI."""
    self.mainMenu.initUi()
    self.setMenuBar(self.mainMenu)
    self.statusBar.initUi()
    self.setStatusBar(self.statusBar)
    self.mainMenu.help.aboutQt.triggered.connect(QApplication.aboutQt)

  @abstractmethod
  def initUi(self, ) -> None:
    """Initialize the UI. Subclasses must implement this method to set up
    the window and its contents. """

  @abstractmethod
  def initLogic(self, ) -> None:
    """Initialize the logic. Subclasses must implement this method to set up
    the logic and functionality of the window. """

  def show(self, ) -> None:
    """Show the window. This method is called when the window is shown."""
    self.initMenus()
    self.initUi()
    self.initLogic()
    QMainWindow.show(self)
