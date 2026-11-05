"""
TabBar subclasses 'PaintedWidget' and shows a row of tabs to choose
between.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QSize, QRectF
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from ..paint_ops import PaintBoxModel
from ..utils import WFont, Color
from ..utils.font_nums import GenericFamilyNum, FontWeightNum
from ..utils.geom import InSets, Size
from ..widgets import PaintedWidget
from . import PaintTabBar

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional

  from PySide6.QtGui import QMouseEvent


class TabBar(PaintedWidget):
  """
  TabBar subclasses 'PaintedWidget' and shows a row of tabs, each with a
  title and a mark of unsaved changes: a dot where its contents are
  modified, a cross to close it otherwise. The tabs share the width,
  each no wider than it needs, their titles shortened where they must
  be.

  A click on a tab makes it the current one and emits 'currentChanged'
  with its index; a click on its cross, or a middle click anywhere on
  it, emits 'closeRequested' instead. The bar decides nothing: what a
  tab shows, and whether it closes, is for its owner.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(24, 25, 27)
  __fallback_tab_color__ = Color(35, 36, 40)
  __fallback_current_color__ = Color(30, 31, 34)
  __fallback_accent_color__ = Color(229, 192, 123)
  __fallback_text_color__ = Color(140, 144, 152)
  __fallback_current_text_color__ = Color(212, 212, 212)
  __fallback_tab_padding__ = 10  # pixels either side of a title
  __fallback_max_tab_width__ = 200
  __fallback_row_spacing__ = 10  # pixels above and below the titles

  #  Private Variables
  __tab_titles__: Optional[list[str]] = None
  __tab_modified__: Optional[list[bool]] = None
  __current_tab__: Optional[int] = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  tabsOp = PaintTabBar()
  font = AttriBox[WFont](
    GenericFamilyNum.SANS,
    FontWeightNum.NORMAL,
    10,
    Color(212, 212, 212),
  )
  currentIndex: Field[int] = Field()

  #  Virtual Variables
  count: Field[int] = Field()
  tabPadding: Field[int] = Field()
  tabColor: Field[Color] = Field()
  currentColor: Field[Color] = Field()
  accentColor: Field[Color] = Field()
  textColor: Field[Color] = Field()
  currentTextColor: Field[Color] = Field()

  #  Signals
  currentChanged = Signal(int)
  closeRequested = Signal(int)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _titles(self, ) -> list[str]:
    if self.__tab_titles__ is None:
      self.__tab_titles__ = []
    return self.__tab_titles__

  def _modified(self, ) -> list[bool]:
    if self.__tab_modified__ is None:
      self.__tab_modified__ = []
    return self.__tab_modified__

  @count.GET
  def _getCount(self, ) -> int:
    """The 'count' getter returns how many tabs there are."""
    return len(self._titles())

  @currentIndex.GET
  def _getCurrentIndex(self, ) -> int:
    """The 'currentIndex' getter returns the index of the current tab, or
    -1 when there are none."""
    if not self.count:
      return -1
    index = 0 if self.__current_tab__ is None else self.__current_tab__
    return min(max(index, 0), self.count - 1)

  @tabPadding.GET
  def _getTabPadding(self, ) -> int:
    return self.__fallback_tab_padding__

  @tabColor.GET
  def _getTabColor(self, ) -> Color:
    return self.__fallback_tab_color__

  @currentColor.GET
  def _getCurrentColor(self, ) -> Color:
    return self.__fallback_current_color__

  @accentColor.GET
  def _getAccentColor(self, ) -> Color:
    return self.__fallback_accent_color__

  @textColor.GET
  def _getTextColor(self, ) -> Color:
    return self.__fallback_text_color__

  @currentTextColor.GET
  def _getCurrentTextColor(self, ) -> Color:
    return self.__fallback_current_text_color__

  def titleAt(self, index: int) -> str:
    """The 'titleAt' method returns the title of tab 'index'."""
    return self._titles()[index]

  def isModified(self, index: int) -> bool:
    """The 'isModified' method tells whether tab 'index' is marked as
    holding unsaved changes."""
    return self._modified()[index]

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @currentIndex.SET
  def _setCurrentIndex(self, index: int) -> None:
    """The 'currentIndex' setter makes tab 'index' the current one,
    without announcing it: 'currentChanged' is for clicks."""
    if not isinstance(index, int):
      raise TypeException('currentIndex', index, int)
    self.__current_tab__ = index
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  @overload.finalize
  def __init__(self, *args) -> None:
    #  A click on a tab is for choosing, not for typing: the focus stays
    #  where it is.
    self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addTab(self, title: str) -> int:
    """The 'addTab' method adds a tab titled 'title' at the end, and
    returns its index."""
    self._titles().append(title)
    self._modified().append(False)
    self.update()
    return self.count - 1

  def removeTab(self, index: int) -> None:
    """The 'removeTab' method removes tab 'index'; the current tab stays
    current, or its neighbour takes over if it was the one removed."""
    current = self.currentIndex
    del self._titles()[index]
    del self._modified()[index]
    if index < current or current >= self.count:
      current -= 1
    self.__current_tab__ = max(current, 0)
    self.update()

  def setTitle(self, index: int, title: str) -> None:
    self._titles()[index] = title
    self.update()

  def setModified(self, index: int, modified: bool) -> None:
    self._modified()[index] = True if modified else False
    self.update()

  def _tabWidth(self, ) -> float:
    if not self.count or self.paintView is None:
      return float(self.__fallback_max_tab_width__)
    share = self.paintView.width / self.count
    return min(share, float(self.__fallback_max_tab_width__))

  def tabRect(self, index: int) -> QRectF:
    """The 'tabRect' method returns where tab 'index' is on the
    widget."""
    view, width = self.paintView, self._tabWidth()
    left = 0 if view is None else view.left
    top = 0 if view is None else view.top
    height = self.height() if view is None else view.height
    return QRectF(left + width * index, top, width, height)

  def closeRect(self, tabRect: QRectF) -> QRectF:
    """The 'closeRect' method returns where the cross, or the dot, is on
    the tab at 'tabRect': a square at its right end."""
    side = min(tabRect.height(), 2 * self.tabPadding + 8)
    left = tabRect.right() - side - 2
    top = tabRect.top() + (tabRect.height() - side) / 2
    return QRectF(left, top, side, side)

  def tabAt(self, x: float, y: float) -> Optional[int]:
    """The 'tabAt' method returns the index of the tab at '(x, y)' on the
    widget, or 'None' where there is none."""
    for index in range(self.count):
      if self.tabRect(index).contains(x, y):
        return index
    return None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    height = self.font.metrics.height() + self.__fallback_row_spacing__
    return QSize(self.__fallback_max_tab_width__, height)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(0, self.sizeHint().height())

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A click makes a tab current; one on its cross, or a middle click,
    asks to close it."""
    point = event.position()
    index = self.tabAt(point.x(), point.y())
    if index is None:
      return event.ignore()
    middle = event.button() == Qt.MouseButton.MiddleButton
    onClose = self.closeRect(self.tabRect(index)).contains(point)
    if middle or onClose:
      self.closeRequested.emit(index)
    else:
      self.currentIndex = index
      self.currentChanged.emit(index)
    event.accept()
