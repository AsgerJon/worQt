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
from worktoy.static import overload
from worktoy.text import typeMsg
from worktoy.waitaminute import MissingVariable, DispatchException

from moreworktoy.waitaminute import WriteOnceError
from ..widgets import BaseWidget
from . import LayoutIndex as LIndex
from . import LayoutSpan as LSpan
from . import LayoutRect as LRect

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

  outerMargins = Field()  # Outer margins of the layout
  nCols = Field()  # Horizontal widget resolution
  nRows = Field()  # Vertical widget resolution
  bottomCols = Field()  # Number of columns in the bottom row
  rightRows = Field()  # Number of rows in the right column

  def _getWidgetDict(self, **kwargs) -> WDict:
    """Getter-function for the widget dictionary. """
    widgetDict = maybe(self.__widget_dict__, dict())
    if not widgetDict:
      return widgetDict
    minRow = min([i.row for i in widgetDict.keys()])
    minCol = min([i.col for i in widgetDict.keys()])
    if not minRow ** 2 + minCol ** 2:
      return widgetDict
    if kwargs.get('_recursion', False):
      raise RecursionError
    newWidgetDict = {}
    for key, value in widgetDict.items():
      newKey = LIndex(key.col - minCol, key.row - minRow)
      newWidgetDict[newKey] = value
    self.__widget_dict__ = newWidgetDict
    return self._getWidgetDict(_recursion=True)

  def _getEmptyEdges(self, *args) -> list[LIndex]:
    """Returns a list of empty edges in the widget dictionary. """
    d = maybe([*args, None][0], 0)
    emptyEdges = []
    widgetDict = self._getWidgetDict()
    for row in range(d):
      for col in range(d):
        index = LIndex(d - col - 1, row)
        if index not in widgetDict:
          emptyEdges.append(index)
    if emptyEdges:
      return emptyEdges
    return self._getEmptyEdges(d + 1)

  def _getOuterEdges(self, *args) -> list[LIndex]:
    """Returns a list of outer edges in the widget dictionary. """
    d = maybe([*args, None][0], 1)
    outerEdges = []
    widgetDict = self._getWidgetDict()
    for row in range(d):
      for col in range(d):
        index = LIndex(d - col - 1, row)
        if index in widgetDict:
          return self._getOuterEdges(d + 1)
        outerEdges.append(index)
    return outerEdges

  def _nextIndex(self) -> LIndex:
    """Returns the next available index in the widget dictionary. """
    return self._getEmptyEdges()[0]

  @outerMargins.GET
  def _getOuterMargins(self) -> WMargins:
    """Getter-function for the WMargins object. """

  @overload(BaseWidget, LIndex)
  def _addItem(self, item: BaseWidget, index: LIndex) -> None:
    """Adds an item to the widget dictionary. """
    existing = self._getWidgetDict()
    self.__widget_dict__ = {**existing, index: item}

  @overload(BaseWidget, LRect)
  def _addItem(self, item: BaseWidget, rect: LRect) -> None:
    """Adds an item to the widget dictionary. """
    existing = self._getWidgetDict()
    for index in rect:
      self._addItem(item, index)

  def _fitRect(self, rect: LRect) -> LRect:
    """Creates a new LRect object having same size as given LRect object,
    but placed such that the bounding rect is smallest. """
    emptyEdges = self._getEmptyEdges()
    rects = []
    for edge in emptyEdges:
      rects.append(LRect(edge, rect))
    maxDims = [max([r.right, r.bottom]) for r in rects]
    return sorted(rects, key=lambda r: max([r.right, r.bottom]))[0]

  @nCols.GET
  def _getNCols(self) -> int:
    """Returns the number of columns in the layout. """
    return max([i.col for i in self._getWidgetDict().keys()])

  @nRows.GET
  def _getNRows(self, ) -> int:
    """Returns the number of rows in the layout"""
    return max([i.row for i in self._getWidgetDict().keys()])

  def addWidget(self, widget: BaseWidget, *args) -> None:
    """Adds a widget to the layout. """
    if not args:
      return self._addItem(widget, self._nextIndex())
    return self._addItem(widget, LRect(*args))

  @staticmethod
  def _resolveRect(other: Any) -> LRect:
    """Resolves other to LRect. """
    if isinstance(other, LRect):
      return other
    try:
      return LRect(other)
    except DispatchException:
      return NotImplemented

  @staticmethod
  def _resolveIndex(other: Any) -> LIndex:
    """Resolves other to LIndex. """
    if isinstance(other, LIndex):
      return other
    try:
      return LIndex(other)
    except DispatchException:
      return NotImplemented

  def _resolveOther(self, other: Any) -> Any:
    """Resolves other to LRect. """
    index = self._resolveIndex(other)
    if index is NotImplemented:
      rect = self._resolveRect(other)
      if rect is NotImplemented:
        return NotImplemented
      if isinstance(rect, LRect):
        return rect
      raise TypeError(typeMsg('other', other, LRect))
    if isinstance(index, LIndex):
      return index
    raise TypeError(typeMsg('other', other, LIndex))

  def __contains__(self, other: Any) -> bool:
    """Checks if the layout contains the given widget. """
    other = self._resolveOther(other)
    if other is NotImplemented:
      return False
    widgetDict = self._getWidgetDict()
    if isinstance(other, LIndex):
      return other in widgetDict
    if isinstance(other, LRect):
      if other.topLeft in widgetDict and other.bottomRight in widgetDict:
        return True
      return False
    return False

  def _getWidgets(self) -> list[BaseWidget]:
    """Returns a list of widgets in the layout. """
    widgetDict = self._getWidgetDict()
    return [*widgetDict.values()]

  def _getRectWidgets(self) -> dict[LRect, BaseWidget]:
    """Returns a dictionary of widgets in the layout. """
    rectWidgetDict = dict()
    itemWidgetDict = self._getWidgetDict()
    widgets = self._getWidgets()
    for widget in widgets:
      indices = []
      for index, item in itemWidgetDict.items():
        if item is widget:
          indices.append(index)
      else:
        rect = LRect.fromIndices(*indices)
        rectWidgetDict[rect] = widget
    return rectWidgetDict

  def build(self, ) -> QGridLayout:
    """Builds the layout. """
    rectWidgets = self._getRectWidgets()
    layout = QGridLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    for rect, widget in rectWidgets.items():
      if TYPE_CHECKING:
        assert isinstance(rect, LRect)
        assert isinstance(widget, BaseWidget)
        assert isinstance(rect.left, int)
        assert isinstance(rect.top, int)
        assert isinstance(rect.width, int)
        assert isinstance(rect.height, int)
      row, col, width, height = rect.top, rect.left, rect.width, rect.height
      widget.initUi()
      QGridLayout.addWidget(layout, widget, row, col, height, width)
    return layout
