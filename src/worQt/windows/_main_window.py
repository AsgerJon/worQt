"""
MainWindow provides the top level window class responsible for the
business logic of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initLogic(self) -> None:
    self.welcome.startedHolding.connect(self.debug01)
    self.welcome.cursorEnter.connect(self.debug02)
    self.welcome.cursorLeave.connect(self.debug03)
    self.welcome.stoppedHolding.connect(self.debug02)

  def debug01(self, *args: Any) -> None:
    self.status.showMessage('Holding!', )

  def debug02(self, ) -> None:
    self.status.showMessage('Moving!')

  def debug03(self, *args: Any) -> None:
    self.status.showMessage('Exiting!')
