"""
BaseWindow subclasses 'AbstractWindow' and provides the base of the main
window class responsible for implementing the menus and the menubar.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from . import AbstractWindow
from .menus import MainMenuBar

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class BaseWindow(AbstractWindow):
  """
  BaseWindow subclasses 'AbstractWindow' and provides the base of the main
  window class responsible for implementing the menus and the menubar.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  mainMenuBar = AttriBox[MainMenuBar](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initMenus(self, ) -> None:
    """
    This method builds the menubar and installs it on the main window. It is
    implemented by the 'BaseWindow' class. Subclasses can extend or override
    as appropriate.
    """
    self.setMenuBar(self.mainMenuBar)
    self.mainMenuBar.initUI()

  def initUI(self, ) -> None:
    """
    The subclass responsible for organizing the widget layouts should
    implement this method.
    """  # LayoutWindow implements this method.

  def initLogic(self, ) -> None:
    """
    The subclass responsible for implementing the business logic and
    connecting signals and slots should implement this method.
    """  # MainWindow implements this method.

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def show(self) -> None:
    """
    This method runs the three initializing methods before the super call.
    Subclasses should generally not need to override this method
    specifically.
    """
    self.initMenus()
    self.initUI()
    self.initLogic()
    super().show()
