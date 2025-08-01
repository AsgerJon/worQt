"""
MainWindow provides the top level window class responsible for the
business logic of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Slot, QEvent

from worQt.windows import LayoutWindow

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


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
    self.menus.help.debug.triggered.connect(self.debug01)
    self.menus.file.exitAction.triggered.connect(self.close)
    self.welcome.eventType.connect(self.debug06)

  def debug01(self, *args: Any) -> None:
    for i, (key, value) in enumerate(self.welcome.settings.items()):
      if self.__debug_counter__ == i:
        infoSpec = """%s: %s"""
        info = infoSpec % (key, value)
        self.status.showMessage(info)
        self.__debug_counter__ += 1
        break
    else:
      self.__debug_counter__ = 0
      self.status.showMessage('No more debug messages!')

  def debug02(self, ) -> None:
    self.status.showMessage('Moving!')

  def debug03(self, *args: Any) -> None:
    self.status.showMessage('Exiting!')

  def debug04(self, *args: Any) -> None:
    self.status.showMessage('%f' % self.welcome.mouseVel)

  def debug05(self, *args: Any) -> None:
    self.status.showMessage(str(self.welcome.mousePos))

  @Slot(str)
  def debug06(self, item: str) -> None:
    self.status.showMessage(item)
