"""
FileBrowser subclasses 'PaintedWidget' and shows a folder as a tree of
its files and folders.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from ..paint_ops import PaintBoxModel
from ..utils import WFont, Color
from ..utils.font_nums import GenericFamilyNum, FontWeightNum
from ..utils.geom import InSets, Size
from ..widgets import PaintedWidget
from . import FileNode, PaintFileTree

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional

  from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent, QFocusEvent


class FileBrowser(PaintedWidget):
  """
  FileBrowser subclasses 'PaintedWidget' and shows a folder, its
  'rootPath', as a tree of its files and folders, the way the project
  view of an IDE does: slim, dark, folders first. Only files with one of
  its 'suffixes' are listed, when there are any.

  A click selects a row, and a click on a folder's arrow opens or closes
  it; a double click opens a folder or a file. The keys do the same,
  with Vi's as well: Up and Down or 'k' and 'j' move, Right or 'l' opens
  a folder, Left or 'h' closes it or goes to the folder above, Enter or
  'o' opens what is selected. Opening a file emits 'fileActivated' with
  its path, for the window to act on. The wheel scrolls.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __key_actions__ = {
    Qt.Key.Key_Up    : 'selectPrevious',
    Qt.Key.Key_Down  : 'selectNext',
    Qt.Key.Key_Right : 'openSelected',
    Qt.Key.Key_Left  : 'closeSelected',
    Qt.Key.Key_Return: 'activateSelected',
    Qt.Key.Key_Enter : 'activateSelected',
  }
  __letter_actions__ = {
    'k': 'selectPrevious',
    'j': 'selectNext',
    'l': 'openSelected',
    'h': 'closeSelected',
    'o': 'activateSelected',
  }
  __wheel_rows__ = 3  # rows one notch of the mouse wheel scrolls

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(2, 2, 2, 2)
  __fallback_borders_dims__ = InSets(1, 1, 1, 1)
  __fallback_paddings_dims__ = InSets(2, 4, 2, 4)
  __fallback_margins_color__ = Color(24, 25, 27)
  __fallback_borders_color__ = Color(58, 61, 65)
  __fallback_paddings_color__ = Color(35, 36, 40)
  __fallback_header_color__ = Color(43, 45, 49)
  __fallback_header_text_color__ = Color(200, 204, 212)
  __fallback_folder_color__ = Color(138, 170, 224)
  __fallback_file_color__ = Color(200, 200, 200)
  __fallback_marked_color__ = Color(229, 192, 123)
  __fallback_arrow_color__ = Color(140, 144, 152)
  __fallback_selection_color__ = Color(54, 59, 69)
  __fallback_dim_selection_color__ = Color(45, 48, 54)
  __fallback_indent__ = 14  # pixels per level of depth
  __fallback_row_spacing__ = 4  # pixels between the rows' text
  __fallback_min_width__ = 140
  __fallback_hint_width__ = 240

  #  Private Variables
  __root_node__: Optional[FileNode] = None
  __browser_suffixes__: Optional[tuple[str, ...]] = None
  __selected_path__: Optional[str] = None
  __marked_path__: Optional[str] = None
  __scroll_top__: Optional[int] = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  treeOp = PaintFileTree()
  font = AttriBox[WFont](
    GenericFamilyNum.SANS,
    FontWeightNum.NORMAL,
    10,
    Color(200, 200, 200),
  )
  rootPath: Field[str] = Field()
  suffixes: Field[tuple] = Field()
  selectedPath: Field[str] = Field()
  markedPath: Field[str] = Field()

  #  Virtual Variables
  rootName: Field[str] = Field()
  rows: Field[list] = Field()
  scrollTop: Field[int] = Field()
  rowHeight: Field[int] = Field()
  indent: Field[int] = Field()
  headerColor: Field[Color] = Field()
  headerTextColor: Field[Color] = Field()
  folderColor: Field[Color] = Field()
  fileColor: Field[Color] = Field()
  markedColor: Field[Color] = Field()
  arrowColor: Field[Color] = Field()
  selectionColor: Field[Color] = Field()
  dimSelectionColor: Field[Color] = Field()

  #  Signals
  fileActivated = Signal(str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _rootNode(self, ) -> FileNode:
    if self.__root_node__ is None:
      self.__root_node__ = FileNode(os.getcwd(), -1, self.suffixes)
    return self.__root_node__

  @rootPath.GET
  def _getRootPath(self, ) -> str:
    """The 'rootPath' getter returns the folder shown, by default the
    working directory."""
    return self._rootNode().path

  @rootName.GET
  def _getRootName(self, ) -> str:
    return self._rootNode().name

  @suffixes.GET
  def _getSuffixes(self, ) -> tuple[str, ...]:
    """The 'suffixes' getter returns the suffixes of the files listed,
    such as '.ezw', or nothing, listing every file."""
    suffixes = self.__browser_suffixes__
    return () if suffixes is None else suffixes

  @selectedPath.GET
  def _getSelectedPath(self, ) -> Optional[str]:
    return self.__selected_path__

  @markedPath.GET
  def _getMarkedPath(self, ) -> Optional[str]:
    """The 'markedPath' getter returns the file marked as the one open,
    or 'None'."""
    return self.__marked_path__

  @rows.GET
  def _getRows(self, ) -> list[FileNode]:
    """The 'rows' getter returns the files and folders that show, in
    order: the root's children, and theirs where they are open."""
    return [*self._rootNode().visible()]

  @scrollTop.GET
  def _getScrollTop(self, ) -> int:
    return 0 if self.__scroll_top__ is None else self.__scroll_top__

  @rowHeight.GET
  def _getRowHeight(self, ) -> int:
    height = self.font.metrics.height()
    return height + self.__fallback_row_spacing__

  @indent.GET
  def _getIndent(self, ) -> int:
    return self.__fallback_indent__

  @headerColor.GET
  def _getHeaderColor(self, ) -> Color:
    return self.__fallback_header_color__

  @headerTextColor.GET
  def _getHeaderTextColor(self, ) -> Color:
    return self.__fallback_header_text_color__

  @folderColor.GET
  def _getFolderColor(self, ) -> Color:
    return self.__fallback_folder_color__

  @fileColor.GET
  def _getFileColor(self, ) -> Color:
    return self.__fallback_file_color__

  @markedColor.GET
  def _getMarkedColor(self, ) -> Color:
    return self.__fallback_marked_color__

  @arrowColor.GET
  def _getArrowColor(self, ) -> Color:
    return self.__fallback_arrow_color__

  @selectionColor.GET
  def _getSelectionColor(self, ) -> Color:
    return self.__fallback_selection_color__

  @dimSelectionColor.GET
  def _getDimSelectionColor(self, ) -> Color:
    return self.__fallback_dim_selection_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view, less the box
    model insets, so the browser fills the space it is given."""
    width, height = self.paintView.width, self.paintView.height
    for insets in (self.marginsDims, self.bordersDims, self.paddingsDims):
      width -= insets.left + insets.right
      height -= insets.top + insets.bottom
    return Size(max(width, 0), max(height, 0))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @rootPath.SET
  def _setRootPath(self, path: str) -> None:
    """The 'rootPath' setter shows the folder at 'path' instead."""
    if not isinstance(path, str):
      raise TypeException('rootPath', path, str)
    self.__root_node__ = FileNode(path, -1, self.suffixes)
    self.__selected_path__, self.__scroll_top__ = None, 0
    self.update()

  @suffixes.SET
  def _setSuffixes(self, suffixes: tuple) -> None:
    """The 'suffixes' setter lists only files with one of 'suffixes',
    listing the root again."""
    if not isinstance(suffixes, tuple):
      raise TypeException('suffixes', suffixes, tuple)
    self.__browser_suffixes__ = suffixes
    self.rootPath = self.rootPath

  @selectedPath.SET
  def _setSelectedPath(self, path: Optional[str]) -> None:
    self.__selected_path__ = None if path is None else os.path.abspath(path)
    self.update()

  @markedPath.SET
  def _setMarkedPath(self, path: Optional[str]) -> None:
    self.__marked_path__ = None if path is None else os.path.abspath(path)
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
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def refresh(self, ) -> None:
    """The 'refresh' method lists the folders shown again, keeping which
    are open."""
    self._rootNode().refresh()
    self.update()

  def reveal(self, path: str) -> bool:
    """
    The 'reveal' method opens the folders down to 'path' and selects it,
    telling whether it is in the tree at all.
    """
    node = self._rootNode().find(path)
    if node is not None:
      self.selectedPath = node.path
    self.update()
    return False if node is None else True

  def _selectedIndex(self, ) -> Optional[int]:
    for index, node in enumerate(self.rows):
      if node.path == self.selectedPath:
        return index
    return None

  def _selected(self, ) -> Optional[FileNode]:
    index = self._selectedIndex()
    return None if index is None else self.rows[index]

  def _selectStep(self, step: int) -> None:
    rows, index = self.rows, self._selectedIndex()
    if not rows:
      return
    index = 0 if index is None else min(max(index + step, 0), len(rows) - 1)
    self.selectedPath = rows[index].path

  def selectPrevious(self, ) -> None:
    self._selectStep(-1)

  def selectNext(self, ) -> None:
    self._selectStep(1)

  def toggle(self, node: FileNode) -> None:
    """The 'toggle' method opens a closed folder and closes an open
    one."""
    if node.isDir:
      node.expanded = False if node.expanded else True
      self.update()

  def openSelected(self, ) -> None:
    """Right opens the selected folder, or steps into an open one."""
    node = self._selected()
    if node is None or not node.isDir:
      return
    if not node.expanded:
      return self.toggle(node)
    if node.children:
      self.selectedPath = node.children[0].path

  def closeSelected(self, ) -> None:
    """Left closes the selected folder, or steps out to the folder
    above."""
    node = self._selected()
    if node is None:
      return
    if node.isDir and node.expanded:
      return self.toggle(node)
    parent = os.path.dirname(node.path)
    if parent != self.rootPath:
      self.selectedPath = parent

  def activate(self, node: FileNode) -> None:
    """The 'activate' method opens 'node': a folder opens or closes, a
    file is announced through 'fileActivated'."""
    self.selectedPath = node.path
    if node.isDir:
      return self.toggle(node)
    self.fileActivated.emit(node.path)

  def activateSelected(self, ) -> None:
    node = self._selected()
    if node is not None:
      self.activate(node)

  def rowsInView(self, height: int) -> int:
    """The 'rowsInView' method returns how many rows fit in 'height'
    below the header, at least one."""
    return max(height // self.rowHeight - 1, 1)

  def followSelection(self, height: int) -> None:
    """Scroll as little as it takes to bring the selected row into
    view."""
    index, shown = self._selectedIndex(), self.rowsInView(height)
    if index is not None:
      top = min(self.scrollTop, index)
      self.__scroll_top__ = max(top, index - shown + 1)
    last = max(len(self.rows) - shown, 0)
    self.__scroll_top__ = min(max(self.scrollTop, 0), last)

  def nodeAt(self, y: float) -> Optional[FileNode]:
    """The 'nodeAt' method returns the file or folder in the row at
    height 'y' on the widget, or 'None' for the header or below the
    rows."""
    view = self.paintView
    if view is None:
      return None
    row = int((y - view.top) // self.rowHeight) - 1
    if row < 0:
      return None
    rows = self.rows
    index = self.scrollTop + row
    return rows[index] if index < len(rows) else None

  def _onArrow(self, node: FileNode, x: float) -> bool:
    view = self.paintView
    left = view.left + self.indent * node.depth
    return True if left <= x < left + self.indent else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(self.__fallback_hint_width__, 400)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(self.__fallback_min_width__, self.rowHeight * 3)

  def keyPressEvent(self, event: QKeyEvent) -> None:
    name = self.__key_actions__.get(event.key(), None)
    if name is None and event.modifiers() == Qt.KeyboardModifier.NoModifier:
      name = self.__letter_actions__.get(event.text(), None)
    if name is None:
      return PaintedWidget.keyPressEvent(self, event)
    getattr(self, name)()
    event.accept()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A click takes the focus and selects the row; on a folder's arrow
    it opens or closes the folder."""
    self.setFocus()
    point = event.position()
    node = self.nodeAt(point.y())
    if node is not None:
      self.selectedPath = node.path
      if node.isDir and self._onArrow(node, point.x()):
        self.toggle(node)
    event.accept()

  def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
    """A double click opens the folder or the file clicked."""
    node = self.nodeAt(event.position().y())
    if node is not None:
      self.activate(node)
    event.accept()

  def wheelEvent(self, event: QWheelEvent) -> None:
    """The wheel scrolls, a few rows a notch."""
    notches = event.angleDelta().y() / 120
    rows = -int(round(notches * self.__wheel_rows__))
    last = max(len(self.rows) - 1, 0)
    self.__scroll_top__ = min(max(self.scrollTop + rows, 0), last)
    self.update()
    event.accept()

  def focusInEvent(self, event: QFocusEvent) -> None:
    PaintedWidget.focusInEvent(self, event)
    self.update()

  def focusOutEvent(self, event: QFocusEvent) -> None:
    PaintedWidget.focusOutEvent(self, event)
    self.update()
