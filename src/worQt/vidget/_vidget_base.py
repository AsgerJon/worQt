"""
VidgetBase subclasses 'PaintedWidget' and holds what a 'Vidget' edits.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QSize
from PySide6.QtGui import QFont, QTextLayout, QTextOption
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet

from ..paint_ops import PaintBoxModel
from ..utils import WFont, Color
from ..utils.font_nums import GenericFamilyNum, FontWeightNum
from ..utils.geom import InSets, Size
from ..widgets import PaintedWidget
from . import PaintStatusLine, PaintLineNumbers, PaintViText

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias

  from PySide6.QtGui import QMouseEvent, QFocusEvent, QWheelEvent

  State: TypeAlias = tuple[str, int]  # the text and the cursor
  States: TypeAlias = list[State]

_LINE_SEPARATOR = ' '  # what 'QTextLayout' breaks a line on


class VidgetBase(PaintedWidget):
  """
  VidgetBase subclasses 'PaintedWidget' and holds what a 'Vidget' edits:
  the text, the cursor in it, the history 'undo' and 'redo' walk, and
  the register cut text goes into. It provides the editing primitives
  the Vi commands are made of, lays the text out and scrolls it, and
  paints through four operations: the box model, the status line along
  the bottom of the content, the line numbers down the left of what
  remains, and the text with its cursor beside them.

  It is dark by default, as a terminal Vi is, and monospaced: text in
  light grey on near-black paper, a darker gutter and status line, and
  the cursor's line number brighter than the rest.

  Two hooks shape the text. 'accepts' tells whether a character may go
  into it: by default any printable character and the line break. The
  'shownText' getter returns the text as shown: by default as written. A
  subclass may show it otherwise, but letter for letter, so a position
  in the one is the same position in the other.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(2, 2, 2, 2)
  __fallback_borders_dims__ = InSets(1, 1, 1, 1)
  __fallback_paddings_dims__ = InSets(4, 4, 4, 4)
  __fallback_margins_color__ = Color(24, 25, 27)
  __fallback_borders_color__ = Color(58, 61, 65)
  __fallback_paddings_color__ = Color(30, 31, 34)  # the paper
  __fallback_status_color__ = Color(43, 45, 49)
  __fallback_block_color__ = Color(212, 212, 212, 110)
  __fallback_bar_color__ = Color(230, 230, 230, 255)
  __fallback_bar_width__ = 2
  __fallback_gutter_color__ = Color(35, 36, 40)
  __fallback_number_color__ = Color(92, 99, 112)
  __fallback_current_number_color__ = Color(200, 204, 212)
  __fallback_gutter_inset__ = 8  # between the numbers and the text
  __fallback_number_digits__ = 3  # the fewest digits the gutter fits
  __fallback_columns__ = 80  # the text is never narrower than this
  __fallback_min_rows__ = 4
  __wheel_lines__ = 3  # rows one notch of the mouse wheel scrolls

  #  Private Variables
  __vidget_text__: Optional[str] = None
  __cursor_index__: Optional[int] = None
  __undo_states__: Optional[States] = None
  __redo_states__: Optional[States] = None
  __register_text__: Optional[str] = None
  __scroll_top__: Optional[int] = None  # the first laid out row in view

  #  Public Variables
  boxModelOp = PaintBoxModel()
  statusOp = PaintStatusLine()
  numbersOp = PaintLineNumbers()
  textOp = PaintViText()
  font = AttriBox[WFont](
    GenericFamilyNum.MONO,
    FontWeightNum.NORMAL,
    12,
    Color(212, 212, 212),
  )
  modified = AttriBox[bool](False)
  registerLines = AttriBox[bool](False)  # the register holds whole lines
  text: Field[str] = Field()
  cursor: Field[int] = Field()
  scrollTop: Field[int] = Field()

  #  Virtual Variables
  columns: Field[int] = Field()
  shownText: Field[str] = Field()
  register: Field[str] = Field()
  blockCursor: Field[bool] = Field()
  cursorColor: Field[Color] = Field()
  statusLeft: Field[str] = Field()
  statusRight: Field[str] = Field()
  statusHeight: Field[int] = Field()
  statusColor: Field[Color] = Field()
  gutterWidth: Field[int] = Field()
  gutterInset: Field[int] = Field()
  gutterColor: Field[Color] = Field()
  numberColor: Field[Color] = Field()
  currentNumberColor: Field[Color] = Field()

  #  Signals
  modifiedChanged = Signal(bool)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.GET
  def _getText(self, ) -> str:
    """The 'text' getter returns the text, as written."""
    if self.__vidget_text__ is None:
      return ''
    if isinstance(self.__vidget_text__, str):
      return self.__vidget_text__
    raise TypeException('__vidget_text__', self.__vidget_text__, str)

  @cursor.GET
  def _getCursor(self, ) -> int:
    """
    The 'cursor' getter returns the position of the cursor in 'text',
    from 0 before the first character to 'len(text)' after the last.
    """
    if self.__cursor_index__ is None:
      return 0
    return min(max(self.__cursor_index__, 0), len(self.text))

  @columns.GET
  def _getColumns(self, ) -> int:
    """The 'columns' getter returns how many characters wide the text
    is at the least: 80, as in a terminal."""
    return self.__fallback_columns__

  @shownText.GET
  def _getShownText(self, ) -> str:
    """The 'shownText' getter returns the text as shown: as written."""
    return self.text

  @register.GET
  def _getRegister(self, ) -> str:
    """The 'register' getter returns the text last cut, or nothing."""
    return '' if self.__register_text__ is None else self.__register_text__

  @blockCursor.GET
  def _getBlockCursor(self, ) -> bool:
    """The 'blockCursor' getter tells whether the cursor is a block on
    its character rather than a bar between characters."""
    return False

  @cursorColor.GET
  def _getCursorColor(self, ) -> Color:
    if self.blockCursor:
      return self.__fallback_block_color__
    return self.__fallback_bar_color__

  @statusLeft.GET
  def _getStatusLeft(self, ) -> str:
    """The 'statusLeft' getter returns what the status line tells on the
    left: nothing, here."""
    return ''

  @statusRight.GET
  def _getStatusRight(self, ) -> str:
    """The 'statusRight' getter returns the line and column of the
    cursor, counted from 1, as Vi's ruler shows them."""
    line = self.lineNumberAt(self.cursor) + 1
    column = self.cursor - self.lineStartAt(self.cursor) + 1
    return '%d,%d' % (line, column)

  @statusHeight.GET
  def _getStatusHeight(self, ) -> int:
    return int(math.ceil(self.font.metricsF.height())) + 4

  @statusColor.GET
  def _getStatusColor(self, ) -> Color:
    return self.__fallback_status_color__

  @scrollTop.GET
  def _getScrollTop(self, ) -> int:
    """The 'scrollTop' getter returns the first laid out row in view,
    counted from 0."""
    return 0 if self.__scroll_top__ is None else self.__scroll_top__

  @gutterWidth.GET
  def _getGutterWidth(self, ) -> int:
    """The 'gutterWidth' getter returns how wide the line numbers'
    gutter is: room for the digits of the last line number, with an
    inset either side."""
    digits = max(len(str(self.lineCount())), self.__fallback_number_digits__)
    digitWidth = self.font.metricsF.horizontalAdvance('0')
    return int(math.ceil(digitWidth * digits)) + self.gutterInset * 2

  @gutterInset.GET
  def _getGutterInset(self, ) -> int:
    return self.__fallback_gutter_inset__

  @gutterColor.GET
  def _getGutterColor(self, ) -> Color:
    return self.__fallback_gutter_color__

  @numberColor.GET
  def _getNumberColor(self, ) -> Color:
    return self.__fallback_number_color__

  @currentNumberColor.GET
  def _getCurrentNumberColor(self, ) -> Color:
    return self.__fallback_current_number_color__

  def _getRequiredSize(self, ) -> Size:
    """
    The content size for the box model: the whole view, less the box
    model insets, so the vidget fills the space it is given.
    """
    width, height = self.paintView.width, self.paintView.height
    for insets in (self.marginsDims, self.bordersDims, self.paddingsDims):
      width -= insets.left + insets.right
      height -= insets.top + insets.bottom
    return Size(max(width, 0), max(height, 0))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.SET
  def _setText(self, value: str) -> None:
    """
    The 'text' setter replaces the text, puts the cursor at its start and
    forgets the history. Setting the text is not editing it, so it leaves
    'modified' alone; what the vidget does not accept is refused.
    """
    if not isinstance(value, str):
      raise TypeException('text', value, str)
    self._refuseUnacceptable(value)
    self.__vidget_text__ = value
    self.__cursor_index__ = 0
    self.__scroll_top__ = 0
    self.__undo_states__, self.__redo_states__ = [], []
    self.updateGeometry()
    self.update()

  @cursor.SET
  def _setCursor(self, index: int) -> None:
    """The 'cursor' setter moves the cursor, kept within the text."""
    if not isinstance(index, int):
      raise TypeException('cursor', index, int)
    self.__cursor_index__ = min(max(index, 0), len(self.text))
    self.update()

  @scrollTop.SET
  def _setScrollTop(self, row: int) -> None:
    """The 'scrollTop' setter scrolls so 'row' is the first in view,
    never above the first row."""
    if not isinstance(row, int):
      raise TypeException('scrollTop', row, int)
    self.__scroll_top__ = max(row, 0)
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @modified.preSet
  def _preSetModified(self, value: bool) -> None:
    if (True if value else False) is self.modified:
      raise SkipSet

  @modified.onSet
  def _onSetModified(self, value: bool) -> None:
    """The notifier emits 'modifiedChanged' whenever 'modified'
    changes."""
    self.modifiedChanged.emit(True if value else False)

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

  # \_______________________
  #  What the text holds  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def accepts(self, char: str) -> bool:
    """
    The 'accepts' method tells whether 'char' may go into the text: here,
    any printable character and the line break.
    """
    if len(char) != 1:
      return False
    return True if char == '\n' or str.isprintable(char) else False

  def _refuseUnacceptable(self, text: str) -> None:
    for char in text:
      if not self.accepts(char):
        infoSpec = """'%s' cannot hold '%s'!"""
        info = infoSpec % (type(self).__name__, char)
        raise ValueError(textFmt(info))

  # \_____________
  #  Lines    ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨

  def lineStartAt(self, index: int) -> int:
    """The 'lineStartAt' method returns where the line holding 'index'
    starts."""
    return str.rfind(self.text, '\n', 0, index) + 1

  def lineEndAt(self, index: int) -> int:
    """The 'lineEndAt' method returns where the line holding 'index'
    ends: at its line break, or at the end of the text."""
    end = str.find(self.text, '\n', index)
    return len(self.text) if end < 0 else end

  def lineNumberAt(self, index: int) -> int:
    """The 'lineNumberAt' method returns the number of the line holding
    'index', counted from 0."""
    return str.count(self.text, '\n', 0, index)

  def lineCount(self, ) -> int:
    """The 'lineCount' method returns the number of lines."""
    return str.count(self.text, '\n') + 1

  def startOfLine(self, number: int) -> int:
    """The 'startOfLine' method returns where line 'number' starts,
    counted from 0 and kept within the lines there are."""
    number = min(max(number, 0), self.lineCount() - 1)
    start = 0
    for _ in range(number):
      start = self.lineEndAt(start) + 1
    return start

  # \_______________
  #  Editing    ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def splice(self, start: int, end: int, insert: str) -> str:
    """
    The 'splice' method replaces the text from 'start' to 'end' with
    'insert', leaves the cursor after it and returns what it replaced.
    Nothing goes in that the vidget does not accept.
    """
    self._refuseUnacceptable(insert)
    text, digits = self.text, len(str(self.lineCount()))
    start = min(max(start, 0), len(text))
    end = min(max(end, start), len(text))
    removed = text[start:end]
    self.__vidget_text__ = text[:start] + insert + text[end:]
    self.__cursor_index__ = start + len(insert)
    if removed or insert:
      self.modified = True
    if len(str(self.lineCount())) != digits:
      self.updateGeometry()  # the gutter grew or shrank
    self.update()
    return removed

  def insertText(self, text: str) -> None:
    """The 'insertText' method writes 'text' at the cursor, as typing
    does."""
    self.splice(self.cursor, self.cursor, text)

  def deleteBackward(self, ) -> None:
    """The 'deleteBackward' method deletes the character before the
    cursor, as Backspace does."""
    if self.cursor:
      self.splice(self.cursor - 1, self.cursor, '')

  def deleteForward(self, ) -> None:
    """The 'deleteForward' method deletes the character after the
    cursor, as Delete does."""
    if self.cursor < len(self.text):
      self.splice(self.cursor, self.cursor + 1, '')

  def keep(self, text: str, lines: bool) -> None:
    """The 'keep' method puts 'text' in the register, 'lines' telling
    whether it is whole lines."""
    self.__register_text__ = text
    self.registerLines = lines

  # \_______________
  #  History    ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _states(self, ) -> tuple[States, States]:
    if self.__undo_states__ is None:
      self.__undo_states__ = []
    if self.__redo_states__ is None:
      self.__redo_states__ = []
    return self.__undo_states__, self.__redo_states__

  def remember(self, ) -> None:
    """
    The 'remember' method records the text and the cursor as they are,
    as the state the next 'undo' returns to, and forgets what 'redo'
    could have brought back.
    """
    undoStates, redoStates = self._states()
    undoStates.append((self.text, self.cursor))
    redoStates.clear()

  def _restore(self, state: State) -> None:
    self.__vidget_text__, self.__cursor_index__ = state
    self.modified = True
    self.update()

  def undo(self, count: int = 1) -> None:
    """The 'undo' method goes back 'count' remembered states."""
    undoStates, redoStates = self._states()
    for _ in range(count):
      if not undoStates:
        return
      redoStates.append((self.text, self.cursor))
      self._restore(undoStates.pop())

  def redo(self, count: int = 1) -> None:
    """The 'redo' method goes forward again 'count' undone states."""
    undoStates, redoStates = self._states()
    for _ in range(count):
      if not redoStates:
        return
      undoStates.append((self.text, self.cursor))
      self._restore(redoStates.pop())

  # \_______________
  #  Layout     ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def textLayout(self, width: int) -> QTextLayout:
    """
    The 'textLayout' method returns the shown text laid out in lines no
    wider than 'width', in the vidget's font.
    """
    shown = str.replace(self.shownText, '\n', _LINE_SEPARATOR)
    #  No ligatures: '...' or '->' drawn as one glyph would take the
    #  cursor's place from the characters inside it.
    font = QFont(self.font)
    font.setStyleStrategy(QFont.StyleStrategy.PreferNoShaping)
    layout = QTextLayout(shown, font)
    option = QTextOption()
    option.setWrapMode(QTextOption.WrapMode.WordWrap)
    layout.setTextOption(option)
    layout.beginLayout()
    height, line = 0.0, layout.createLine()
    while line.isValid():
      line.setLineWidth(width)
      line.setPosition(QPointF(0, height))
      height += line.height()
      line = layout.createLine()
    layout.endLayout()
    return layout

  def _laidOut(self, ) -> Optional[QTextLayout]:
    """
    The '_laidOut' method returns the text laid out as last painted, or
    'None' before the vidget was first painted.
    """
    view = self.paintView
    return None if view is None else self.textLayout(view.width)

  # \_______________
  #  Scrolling  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def scrollOffset(self, layout: QTextLayout) -> float:
    """The 'scrollOffset' method returns how far 'layout' is scrolled
    up: the height of the rows above the first in view."""
    if self.scrollTop < layout.lineCount():
      return layout.lineAt(self.scrollTop).y()
    return 0.0

  def rowsInView(self, layout: QTextLayout, height: float) -> int:
    """The 'rowsInView' method returns how many rows of 'layout' fit in
    'height' from the first in view, at least one."""
    rows, used = 0, 0.0
    for row in range(self.scrollTop, layout.lineCount()):
      used += layout.lineAt(row).height()
      if used > height:
        break
      rows += 1
    return max(rows, 1)

  def cursorRow(self, layout: QTextLayout) -> int:
    """The 'cursorRow' method returns the laid out row the cursor is
    on."""
    line = layout.lineForTextPosition(self.cursor)
    return line.lineNumber() if line.isValid() else 0

  def _followCursor(self, layout: QTextLayout, height: float) -> None:
    """Scroll as little as it takes to bring the cursor's row into
    view."""
    row = self.cursorRow(layout)
    if row < self.scrollTop:
      self.__scroll_top__ = row
    while row >= self.scrollTop + self.rowsInView(layout, height):
      self.__scroll_top__ = self.scrollTop + 1
    lastRow = max(layout.lineCount() - 1, 0)
    self.__scroll_top__ = min(self.scrollTop, lastRow)

  def viewLayout(self, width: int, height: float) -> QTextLayout:
    """
    The 'viewLayout' method returns the text laid out 'width' wide, first
    scrolling so the cursor is in view of 'height'. Every paint operation
    of the text asks for it, and gets the same rows.
    """
    layout = self.textLayout(width)
    self._followCursor(layout, height)
    return layout

  def scrollBy(self, rows: int) -> None:
    """
    The 'scrollBy' method scrolls 'rows' rows down (up when negative),
    taking the cursor along where it would leave the view, as Vi does.
    """
    layout, view = self._laidOut(), self.paintView
    if layout is None:
      return
    lastRow = max(layout.lineCount() - 1, 0)
    self.scrollTop = min(max(self.scrollTop + rows, 0), lastRow)
    shown = self.rowsInView(layout, view.height)
    row = self.cursorRow(layout)
    target = min(max(row, self.scrollTop), self.scrollTop + shown - 1)
    if target != row:
      x, _ = layout.lineAt(row).cursorToX(self.cursor)
      self.cursor = layout.lineAt(min(target, lastRow)).xToCursor(x)

  def cursorRect(self, layout: QTextLayout) -> QRectF:
    """
    The 'cursorRect' method returns where the cursor is drawn in
    'layout': a block over its character, or a bar before it.
    """
    index = self.cursor
    line = layout.lineForTextPosition(index)
    if not line.isValid():
      return QRectF()
    x, _ = line.cursorToX(index)
    width = float(self.__fallback_bar_width__)
    if self.blockCursor:
      width = self.font.metricsF.averageCharWidth()
      if index < len(self.text) and self.text[index] != '\n':
        nextX, _ = line.cursorToX(index + 1)
        width = nextX - x if nextX > x else width
    return QRectF(x, line.y(), width, line.height())

  def showsCursor(self, ) -> bool:
    """The 'showsCursor' method tells whether the cursor is drawn: while
    the vidget has the keyboard focus."""
    return self.hasFocus()

  def indexAt(self, x: float, y: float) -> int:
    """
    The 'indexAt' method returns the position in the text nearest the
    point '(x, y)' on the widget.
    """
    layout, view = self._laidOut(), self.paintView
    if layout is None or not layout.lineCount():
      return self.cursor
    x, y = x - view.left, y - view.top + self.scrollOffset(layout)
    for number in range(layout.lineCount()):
      line = layout.lineAt(number)
      if y < line.y() + line.height():
        return line.xToCursor(x)
    return layout.lineAt(layout.lineCount() - 1).xToCursor(x)

  # \_____________________________
  #  Moving as the text is laid out  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def cursorLeft(self, ) -> None:
    self.cursor = self.cursor - 1

  def cursorRight(self, ) -> None:
    self.cursor = self.cursor + 1

  def _lineSteps(self, steps: int) -> None:
    """
    The '_lineSteps' method moves the cursor 'steps' lines down (up when
    negative) as laid out, keeping as close to its horizontal place as
    the line allows.
    """
    layout = self._laidOut()
    if layout is None:
      return
    line = layout.lineForTextPosition(self.cursor)
    target = line.lineNumber() + steps
    if line.isValid() and 0 <= target < layout.lineCount():
      x, _ = line.cursorToX(self.cursor)
      self.cursor = layout.lineAt(target).xToCursor(x)

  def cursorUp(self, ) -> None:
    self._lineSteps(-1)

  def cursorDown(self, ) -> None:
    self._lineSteps(1)

  def _laidOutLineEnds(self, ) -> tuple[int, int]:
    """
    The '_laidOutLineEnds' method returns where the line the cursor is on,
    as laid out, starts and ends, the line break or the space ending it
    not included.
    """
    layout = self._laidOut()
    if layout is None:
      return self.lineStartAt(self.cursor), self.lineEndAt(self.cursor)
    line = layout.lineForTextPosition(self.cursor)
    if not line.isValid():
      return self.cursor, self.cursor
    start = line.textStart()
    end = start + line.textLength()
    if start < end and self.text[end - 1] in ' \n':
      end -= 1
    return start, end

  def cursorHome(self, ) -> None:
    self.cursor = self._laidOutLineEnds()[0]

  def cursorEnd(self, ) -> None:
    self.cursor = self._laidOutLineEnds()[1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A click takes the focus and puts the cursor where it landed."""
    self.setFocus()
    point = event.position()
    self.cursor = self.indexAt(point.x(), point.y())
    event.accept()

  def _insetWidth(self, ) -> int:
    width = 0
    for insets in (self.marginsDims, self.bordersDims, self.paddingsDims):
      width += insets.left + insets.right
    return width

  def _insetHeight(self, ) -> int:
    height = 0
    for insets in (self.marginsDims, self.bordersDims, self.paddingsDims):
      height += insets.top + insets.bottom
    return height

  def minimumSizeHint(self, ) -> QSize:
    """
    The vidget is never narrower than it takes to show 'columns'
    characters a row beside the line numbers, the cursor bar included,
    nor lower than a few rows over the status line.
    """
    metrics = self.font.metricsF
    textWidth = metrics.horizontalAdvance('0' * self.columns)
    width = math.ceil(textWidth) + self.__fallback_bar_width__ + 2
    width += self.gutterWidth + self._insetWidth()
    rows = metrics.lineSpacing() * self.__fallback_min_rows__
    height = math.ceil(rows) + self.statusHeight + self._insetHeight()
    return QSize(width, height)

  def sizeHint(self, ) -> QSize:
    """The vidget would be as wide as its 'columns', and tall."""
    least = self.minimumSizeHint()
    return QSize(least.width(), max(least.height(), 600))

  def wheelEvent(self, event: QWheelEvent) -> None:
    """The wheel scrolls, a few rows a notch."""
    notches = event.angleDelta().y() / 120
    self.scrollBy(-int(round(notches * self.__wheel_lines__)))
    event.accept()

  def focusInEvent(self, event: QFocusEvent) -> None:
    PaintedWidget.focusInEvent(self, event)
    self.update()

  def focusOutEvent(self, event: QFocusEvent) -> None:
    PaintedWidget.focusOutEvent(self, event)
    self.update()
