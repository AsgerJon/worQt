"""
MainWindow provides the top level window class responsible for the
business logic of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Slot

from worQt.geometry import Rect
from worQt.nums import Alignum
from worQt.windows import LayoutWindow

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


class MainWindow(LayoutWindow):
  """
  MainWindow provides the top level window class responsible for the
  business logic of the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  __debug_counter__ = 0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initLogic(self) -> None:
    LayoutWindow.initLogic(self)
    self.menus.help.debugLeft.triggered.connect(self.debugLeftFunc)
    self.menus.help.debugRight.triggered.connect(self.debugRightFunc)
    self.menus.help.debug.triggered.connect(self.debugFunc)

  def initUi(self) -> None:
    """
    Initialize the user interface of the main window.
    This method sets up the main menu bar and status bar for the window.
    """
    LayoutWindow.initUi(self)

  def debugLeftFunc(self) -> None:
    self.welcome.alignmentFlag = Alignum.CENTER_LEFT
    self.status.showMessage('debug left', 5000)

  def debugRightFunc(self) -> None:
    self.welcome.alignmentFlag = Alignum.CENTER_RIGHT
    self.status.showMessage('debug right', 5000)

  def debugFunc(self) -> None:

    try:
      _ = Rect('sixty-nine', 'four-twenty', '1337', '80085')
    except Exception as exception:
      infoSpec = """Caught %s: %s"""
      excType = type(exception).__name__
      info = infoSpec % (excType, str(exception))
      self.status.showMessage(info)
    else:
      self.status.showMessage("""Expected an exception lmao""")
