"""
LayoutWindow subclasses BaseWindow and provides organization of widgets
and layouts within the main application window, but does not handle
signals and slots.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from icecream import ic
from worktoy.core.sentinels import THIS
from worktoy.desc import Field, AttriBox
from worktoy.lorem_ipsum import Paragraph

from . import BaseWindow
from ..layouts import BaseLayout, LayoutIndex, GridLayout
from ..widgets import (AbstractWidget,
  LabelWidget,
  ListWidget,
  PushButton, TextWidget)

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Optional, TypeAlias

  MaybeLayout: TypeAlias = Optional[BaseLayout]
  LayoutField: TypeAlias = Union[BaseLayout, Field]

  MaybeWidget: TypeAlias = Optional[AbstractWidget]
  WidgetField: TypeAlias = Union[AbstractWidget, Field]

LONG_TEXT: str = str(Paragraph(300))


class LayoutWindow(BaseWindow):
  """
  LayoutWindow subclasses BaseWindow and provides organization of widgets
  and layouts within the main application window, but does not handle
  signals and slots.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  baseWidget = AttriBox[AbstractWidget](THIS, )
  baseLayout = AttriBox[GridLayout]()
  # --- #  Indices
  welcomeIndex = AttriBox[LayoutIndex](0, 0, 1, 2)
  testButtonIndex = AttriBox[LayoutIndex](1, 0, 1, 1)
  infoLabelIndex = AttriBox[LayoutIndex](1, 1, 1, 1)
  resetButtonIndex = AttriBox[LayoutIndex](0, 2, 2, 1)
  textWidgetIndex = AttriBox[LayoutIndex](2, 0, 1, 3)
  # --- #  Widgets
  welcomeLabel = AttriBox[LabelWidget](THIS, """Welcome to worQt!""")
  testButton = AttriBox[PushButton](THIS, """Click Me!""")
  infoLabel = AttriBox[LabelWidget](THIS, """Ready!""")
  resetButton = AttriBox[PushButton](THIS, """Reset""")
  textWidget = AttriBox[TextWidget](THIS, LONG_TEXT)

  # textLabelIndex = AttriBox[LayoutIndex](2, 0, 1, 2)
  # textLabel = AttriBox[TextWidget](textLabelIndex)

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    Sets up menubar, menus and statusbar. Subclasses should override
    this method to add further widgets and layouts.
    """
    BaseWindow.initUI(self, )
    self.baseLayout.reset()
    self.baseLayout[self.welcomeIndex] = self.welcomeLabel
    self.baseLayout[self.testButtonIndex] = self.testButton
    self.baseLayout[self.infoLabelIndex] = self.infoLabel
    self.baseLayout[self.resetButtonIndex] = self.resetButton
    self.baseLayout[self.textWidgetIndex] = self.textWidget
    self.baseLayout.initUI()
    QWidget.setLayout(self.baseWidget, self.baseLayout)
    self.setCentralWidget(self.baseWidget)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DEBUG FUNCTIONS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
