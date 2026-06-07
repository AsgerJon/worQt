"""
BaseWindow subclasses 'AbstractWindow' and provides the base of the main
window class responsible for implementing the menus and the menubar.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class BaseWindow(AbstractWindow):
  """
  BaseWindow subclasses 'AbstractWindow' and provides the base of the main
  window class responsible for implementing the menus and the menubar.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initMenus(self, ) -> None:
    """
    This method builds the menubar, menus and statusbar. It is implemented
    by the 'BaseWindow' class. Subclasses can extend or override as
    appropriate.
    """
    raise NotImplementedError

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
