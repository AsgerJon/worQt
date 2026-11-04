"""
MainWindow subclasses 'LayoutWindow' and provides the business logic of
the application.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import LayoutWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MainWindow(LayoutWindow):
  """
  MainWindow subclasses 'LayoutWindow' and provides the business logic of
  the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initLogic(self, ) -> None:
    """
    This method should implement the business logic of the application and
    connect signals and slots.
    """
    #  self.this.connect(self.that)
