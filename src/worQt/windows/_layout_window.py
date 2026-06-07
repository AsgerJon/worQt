"""
LayoutWindow subclasses 'BaseWindow' and provides the layouts of the main
application window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from . import BaseWindow
from ..layouts import BaseLayout
from ..widgets import AbstractWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class LayoutWindow(BaseWindow):
  """
  LayoutWindow subclasses 'BaseWindow' and provides the layouts of the main
  application window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  baseWidget = AttriBox[AbstractWidget](THIS)
  baseLayout = AttriBox[BaseLayout]()  # No THIS!

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    #  self.baseLayout.addWidget(...)
    self.baseWidget.setLayout(self.baseLayout)
    self.setCentralWidget(self.baseWidget)
