"""
MainWindow provides the top level window class responsible for the
business logic of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import LayoutWindow

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

  def initUi(self) -> None:
    """
    Initialize the user interface of the main window.
    This method sets up the main menu bar and status bar for the window.
    """
    LayoutWindow.initUi(self)
