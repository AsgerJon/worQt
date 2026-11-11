"""
ProgramEditor subclasses 'PaintedWidget' and shows the sixteen words of
a ROM's program, each instruction and operand chosen from a menu.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPoint, QRectF, QSize, Signal
from PySide6.QtWidgets import QMenu, QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from .. import ISA, decoded

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtCore import QEvent
  from PySide6.QtGui import QMouseEvent, QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_ROW = 19  # pixels a word's row takes
_CELLS = (0.0, 28.0, 86.0, 120.0)  # pixels: address, opcode, operand, end


def operandText(word: tuple[int, int]) -> str:
  """The 'operandText' function returns the operand of a word as it is
  written: a number or an address as it is, a register as 'R3', nothing
  for an instruction that takes none."""
  op, arg = word
  operand = decoded(op, arg).operand
  if operand == 'r':
    return 'R%d' % arg
  return '%d' % arg if operand == 'n' else ''


def said(word: tuple[int, int]) -> str:
  """The 'said' function returns a word as it is written: its mnemonic,
  and its operand where it takes one."""
  mnemonic = decoded(*word).mnemonic
  operand = operandText(word)
  return '%s %s' % (mnemonic, operand) if operand else mnemonic


class PaintProgramEditor(AbstractPaintOp):
  """
  PaintProgramEditor subclasses 'AbstractPaintOp' and paints a
  'ProgramEditor': a row a word, its address, its mnemonic and its
  operand, where it takes one, the row under the mouse lit, the word at
  the address shown accented.
  """

  #  Annotations
  widget: ProgramEditor

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the rows."""
    widget = self.widget
    painter.setFont(widget.font)
    for row, (op, arg) in enumerate(widget.program):
      box = widget.rowRect(row)
      if row == widget.address:
        painter.fillRect(box, widget.markColor.Q)
      elif row == widget.hovered and widget.isEnabled():
        painter.fillRect(box, widget.hoverColor.Q)
      cells = [QRectF(box.left() + a, box.top(), b - a - 6.0, box.height())
               for a, b in zip(_CELLS[:-1], _CELLS[1:])]
      painter.setPen(widget.dimColor.Q)
      painter.drawText(cells[0], _RIGHT, '%d' % row)
      painter.setPen(widget.font.color.Q)
      painter.drawText(cells[1], _LEFT, decoded(op, arg).mnemonic)
      painter.drawText(cells[2], _LEFT, operandText((op, arg)))
    return rect


class ProgramEditor(PaintedWidget):
  """
  ProgramEditor subclasses 'PaintedWidget' and shows the sixteen words
  of a ROM's 'program', each an opcode and an operand: a click on a
  word's mnemonic opens a menu of the 'instructions' the computer
  carries out, all of 'ISA' unless set, a click on its operand, where
  it takes one, a menu of the numbers or the registers, each choice
  emitting 'programEdited' with the program so. 'address' is the word
  the computer reads now, marked. Greyed out, it only shows.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_mark_color__ = Color(70, 62, 44)
  __fallback_hover_color__ = Color(48, 50, 56)
  __fallback_dim_color__ = Color(110, 114, 122)

  #  Private Variables
  __shown_program__: tuple = ((0, 0),) * 16
  __shown_address__: int | None = None
  __hovered_row__: int | None = None
  __program_menu__: QMenu | None = None
  __shown_instructions__: tuple = ISA

  #  Public Variables
  boxModelOp = PaintBoxModel()
  editorOp = PaintProgramEditor()
  font = AttriBox[WFont](
      GenericFamilyNum.MONO,
      FontWeightNum.NORMAL,
      10,
      Color(212, 212, 212),
  )

  #  Virtual Variables
  program: Field[tuple] = Field()
  address: Field[int] = Field()
  hovered: Field[int] = Field()
  menu: Field[QMenu] = Field()
  instructions: Field[tuple] = Field()
  markColor: Field[Color] = Field()
  hoverColor: Field[Color] = Field()
  dimColor: Field[Color] = Field()

  #  Signals
  programEdited = Signal(object)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @program.GET
  def _getProgram(self, ) -> tuple:
    """The 'program' getter returns the sixteen words shown, each an
    opcode and an operand."""
    return self.__shown_program__

  @address.GET
  def _getAddress(self, ) -> int | None:
    """The 'address' getter returns the word marked, or 'None'."""
    return self.__shown_address__

  @hovered.GET
  def _getHovered(self, ) -> int | None:
    """The 'hovered' getter returns the row under the mouse, or
    'None'."""
    return self.__hovered_row__

  @menu.GET
  def _getMenu(self, ) -> QMenu | None:
    """The 'menu' getter returns the menu the last click opened, or
    'None'."""
    return self.__program_menu__

  @instructions.GET
  def _getInstructions(self, ) -> tuple:
    """The 'instructions' getter returns the instructions the menu
    offers."""
    return self.__shown_instructions__

  @instructions.SET
  def _setInstructions(self, instructions: tuple) -> None:
    """The 'instructions' setter sets the instructions the menu
    offers."""
    self.__shown_instructions__ = (*instructions,)

  @markColor.GET
  def _getMarkColor(self, ) -> Color:
    return self.__fallback_mark_color__

  @hoverColor.GET
  def _getHoverColor(self, ) -> Color:
    return self.__fallback_hover_color__

  @dimColor.GET
  def _getDimColor(self, ) -> Color:
    return self.__fallback_dim_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(240, 16 * _ROW + 4)

  def minimumSizeHint(self, ) -> QSize:
    return self.sizeHint()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A click on a word's mnemonic opens the menu of instructions, on
    its operand the menu of numbers."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    where = event.position()
    row = self.rowAt(where.y())
    if row is None:
      return
    operand = where.x() >= _CELLS[2]
    menu = self.menuFor(row, operand)
    menu.popup(self.mapToGlobal(QPoint(int(where.x()), int(where.y()))))

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """Lights the row under the mouse."""
    row = self.rowAt(event.position().y())
    if row != self.__hovered_row__:
      self.__hovered_row__ = row
      self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.__hovered_row__ = None
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
    self.setMouseTracking(True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showProgram(self, program: tuple, address: int | None) -> None:
    """The 'showProgram' method shows the sixteen words of 'program',
    the word at 'address' marked."""
    self.__shown_program__ = (*program,)
    self.__shown_address__ = address
    self.update()

  def rowRect(self, row: int) -> QRectF:
    """The 'rowRect' method returns where the row of 'row' is."""
    return QRectF(0.0, 2.0 + row * _ROW, float(self.width()), _ROW - 1.0)

  def rowAt(self, y: float) -> int | None:
    """The 'rowAt' method returns the row at 'y', or 'None'."""
    row = int((y - 2.0) // _ROW)
    return row if 0 <= row < 16 else None

  def menuFor(self, row: int, operand: bool) -> QMenu:
    """The 'menuFor' method returns the menu of the word of 'row': of the
    numbers or the registers for its operand, if it takes one, else of
    the instructions, each choice rewriting the word, keeping its
    operand where the new instruction takes one too."""
    menu = self.__program_menu__ = QMenu(self)
    op, arg = self.program[row]
    kind = decoded(op, arg).operand
    if operand and kind in ('n', 'r'):
      for number in range(16):
        text = 'R%d' % number if kind == 'r' else '%d' % number
        action = menu.addAction(text)
        action.triggered.connect(self._writer(row, op, number))
      return menu
    for instruction in self.instructions:
      action = menu.addAction('%s, %s' % (instruction.mnemonic,
                                          instruction.words))
      kept = arg if kind in ('n', 'r') else 0
      written = kept if instruction.takes else instruction.operand
      action.triggered.connect(self._writer(row, instruction.op, written))
    return menu

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _writer(self, row: int, op: int, arg: int) -> object:
    """What writes the word 'op' and 'arg' at the row of 'row', emitting
    'programEdited'."""

    def write(*_) -> None:
      program = [*self.program]
      program[row] = (op, arg)
      self.__shown_program__ = (*program,)
      self.update()
      self.programEdited.emit((*program,))

    return write
