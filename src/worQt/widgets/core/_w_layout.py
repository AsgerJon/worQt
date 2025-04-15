"""WLayout manages the layout of widgets across the 'worQt' library. It
organizes both the main application windows and widgets with multiple child
widgets. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QGridLayout
from worktoy.attr import Field
from worktoy.ezdata import EZData
from worktoy.mcls import BaseObject
from worktoy.parse import maybe
from worktoy.text import typeMsg
from worktoy.waitaminute import MissingVariable

from moreworktoy.waitaminute import WriteOnceError
from ..core import BaseWidget
from ..core import LayoutIndex as LIndex
from ..core import LayoutSpan as LSpan

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Callable, Self, TypeAlias

  WDict: TypeAlias = dict[LIndex, BaseWidget]


class WLayout(BaseObject):
  """WLayout manages the layout of widgets across the 'worQt' library. It
  organizes both the main application windows and widgets with multiple child
  widgets. """

  __iter_contents__ = None

  __widget_dict__ = None

  nCols = Field()  # Horizontal widget resolution
  nRows = Field()  # Vertical widget resolution
  bottomCols = Field()  # Number of columns in the bottom row
  rightRows = Field()  # Number of rows in the right column

  Q = Field()

  def _getWidgetDict(self, ) -> WDict:
    """Getter-function for the widget dictionary. """
    return maybe(self.__widget_dict__, dict())

  def _addItem(self, index: LIndex, item: Self, span: LSpan) -> None:
    """Adds an item to the widget dictionary. """
    existing = self._getWidgetDict()
    self.__widget_dict__ = {**existing, index: item}

  @Q.GET
  def _getQ(self) -> QGridLayout:
    """Creates a QGridLayout representation of the layout. """

  @nCols.GET
  def _getNCols(self) -> int:
    """Returns the number of columns in the layout. """

  def addWidget(self, widget: BaseWidget, *args) -> None:
    """Adds a widget to the layout. """
