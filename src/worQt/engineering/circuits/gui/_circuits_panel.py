"""
CircuitsPanel subclasses 'PaintedWidget' and shows the part of a
circuit selected, as numbers to type over, buttons and what it reads
now, or the circuit and where its energy goes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import NumberField, ToolButton
from ...gui._paint_panel import PaintPanel
from .. import Bit, Chip, Circuit, FIRST, ISA, Node, Run, Switch, program
from .. import remembered, words
from .._si import si
from . import ProgramEditor

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap
#  Each kind's rows of numbers: the field, its name, unit, decimals,
#  step, least and greatest
_ROWS = {
  'circuit'  : (),
  'node'     : (
    ('xField', 'x', '', 0, 1, -200, 200),
    ('yField', 'y', '', 0, 1, -200, 200),
  ),
  'wire'     : (),
  'source'   : (
    ('voltageField', 'Voltage', 'V', 2, 0.5, -1e4, 1e4),
    ('frequencyField', 'Frequency', 'Hz', 1, 1, 0, 1e6),
    ('internalField', 'Internal', 'Ω', 2, 0.5, 0, 1e6),
  ),
  'resistor' : (
    ('resistanceField', 'Resistance', 'Ω', 1, 10, 0.001, 1e9),
  ),
  'lamp'     : (
    ('ratedVoltageField', 'Made for', 'V', 1, 0.5, 0.1, 1e4),
    ('ratedPowerField', 'Power', 'W', 2, 0.1, 0.001, 1e5),
  ),
  'capacitor': (
    ('capacitanceField', 'Capacitance', 'µF', 2, 100, 0.001, 1e7),
  ),
  'coil'     : (
    ('inductanceField', 'Inductance', 'H', 3, 0.1, 0.001, 1e4),
  ),
  'switch'   : (),
  'ammeter'  : (),
  'voltmeter': (),
  'diode'    : (
    ('forwardField', 'Voltage', 'V', 2, 0.1, 0.01, 100),
  ),
  'led'      : (
    ('forwardField', 'Voltage', 'V', 2, 0.1, 0.01, 100),
    ('ratedCurrentField', 'Made for', 'mA', 1, 1, 0.1, 1e4),
  ),
  'transistor': (
    ('gainField', 'Gain β', '', 0, 10, 1, 1e4),
  ),
  'bit'      : (),
  'busin'    : (
    ('valueField', 'Value', '', 0, 1, 0, 15),
  ),
  'busprobe' : (),
  'probe'    : (),
  'clock'    : (
    ('tickField', 'Frequency', 'Hz', 2, 0.5, 0.01, 1e6),
  ),
  'chip'     : (),
}
#  Where each field's number goes in its part, and what it is multiplied
#  by to get there
_SPOTS = {
  'voltageField'     : (2, 1.0),
  'frequencyField'   : (3, 1.0),
  'internalField'    : (4, 1.0),
  'resistanceField'  : (2, 1.0),
  'ratedVoltageField': (2, 1.0),
  'ratedPowerField'  : (3, 1.0),
  'capacitanceField' : (2, 1e-6),
  'inductanceField'  : (2, 1.0),
  'forwardField'     : (2, 1.0),
  'ratedCurrentField': (3, 1e-3),
  'gainField'        : (3, 1.0),
  'tickField'        : (2, 1.0),
  'valueField'       : (2, 1.0),
}
_SWAP = ('Poles', ('swapButton',), ('Swap + and −',))
_TURN = ('Way', ('turnButton',), ('Turn round',))
#  The kinds named otherwise in a heading than by their class
_TITLES = {'led': 'Light emitting diode', 'bit': 'Input',
           'probe': 'Output', 'busin': 'Bus input', 'busprobe': 'Bus output'}
#  The buttons and fields that work on a part fixed by a quest
_LIVE = ('openButton', 'closedButton', 'lowButton', 'highButton',
         'valueField')
#  Each kind's rows of buttons: the row's name, its buttons and their
#  words
_BUTTONS = {
  'source'   : (_SWAP,),
  'switch'   : (('Switch', ('openButton', 'closedButton'),
                 ('Open', 'Closed')),),
  'ammeter'  : (_SWAP,),
  'voltmeter': (_SWAP,),
  'diode'    : (_TURN,),
  'led'      : (_TURN,),
  'bit'      : (('Level', ('lowButton', 'highButton'), ('Low', 'High')),),
}
_HEADING = 28  # pixels a heading takes
_ROW = 32  # pixels a row takes


def _value(bits: tuple) -> int:
  """The number 'bits' make, bit nought first."""
  return sum(int(bit) << k for k, bit in enumerate(bits))


def _machineWords(kind: str, memory: tuple) -> list[str]:
  """What a computer chip of 'kind' holds, in words: A, the carry, the
  counter and OUT; its register, or its stack and its sixteen."""
  machine = remembered(kind, memory)
  lines = ['A %d, C %d, counter %d, OUT %d' % (
    machine.a, int(machine.c), machine.pc, machine.out)]
  if kind == 'CPU':
    return lines + ['R0 %d' % machine.registers[0]]

  def listed(values: tuple) -> str:
    return ' '.join('%d' % value for value in values)

  return lines + ['Stack: %s' % listed(machine.stack),
                  'R0-R7: %s' % listed(machine.registers[:8]),
                  'R8-R15: %s' % listed(machine.registers[8:])]


class PaintCircuitsPanel(AbstractPaintOp):
  """
  PaintCircuitsPanel subclasses 'AbstractPaintOp' and paints the words
  of a 'CircuitsPanel': its heading, the name of each row beside it,
  what is shown and what it reads now, in words, and the note.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the words of the panel."""
    widget = self.widget
    for box, text, heading in widget.labels():
      font = widget.headingFont if heading else widget.font
      painter.setFont(font)
      painter.setPen(font.color.Q)
      painter.drawText(box, _LEFT, text)
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    painter.drawText(widget.wordsRect(), _WRAP, widget.words())
    if widget.note:
      painter.setPen(widget.noteColor.Q)
      painter.drawText(widget.noteRect(), _WRAP, widget.note)
    return rect


class CircuitsPanel(PaintedWidget):
  """
  CircuitsPanel subclasses 'PaintedWidget' and shows the part of the
  circuit selected: its numbers to type over, a source's voltage,
  frequency and internal resistance, a resistor's resistance, what a
  lamp is made for, a capacitor's capacitance, a coil's inductance, a
  diode's voltage, a transistor's gain, a node's place; its buttons, a
  switch open or closed, a source's or a meter's poles swapped, a
  diode turned round; and in words what it reads now, as the circuit
  runs, the voltage across it, the current through it, the power, a
  capacitor's charge. With nothing selected, it says how the circuit
  settles or swings of itself and where its energy has gone.

  Each number taken, and each button, emits 'circuitEdited' with the
  circuit so; what the circuit cannot take is given up, the note saying
  why. The first nodes and parts, as many as 'locked' says, are fixed:
  shown and read, greyed out, but a switch still opens and closes. A
  ROM's program, written word by word in its 'programEditor', emits
  'programWritten' after each word, the computer to start over.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_panel_color__ = Color(37, 38, 42)
  __fallback_divider_color__ = Color(58, 61, 65)
  __fallback_note_color__ = Color(229, 192, 123)
  __fallback_panel_width__ = 300
  __fallback_side_margin__ = 16
  __fallback_label_width__ = 104
  __fallback_button_label_width__ = 84
  __fallback_top__ = 10

  #  Private Variables
  __shown_run__: Run | None = None
  __shown_part__: tuple[str, int] | None = None
  __panel_note__: str = ''
  __locked_parts__: tuple[int, int] = (0, 0)

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  wordsOp = PaintCircuitsPanel()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(140, 144, 152),
  )
  headingFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      11,
      Color(212, 212, 212),
  )
  xField = AttriBox[NumberField](THIS)
  yField = AttriBox[NumberField](THIS)
  voltageField = AttriBox[NumberField](THIS)
  frequencyField = AttriBox[NumberField](THIS)
  internalField = AttriBox[NumberField](THIS)
  resistanceField = AttriBox[NumberField](THIS)
  ratedVoltageField = AttriBox[NumberField](THIS)
  ratedPowerField = AttriBox[NumberField](THIS)
  capacitanceField = AttriBox[NumberField](THIS)
  inductanceField = AttriBox[NumberField](THIS)
  forwardField = AttriBox[NumberField](THIS)
  ratedCurrentField = AttriBox[NumberField](THIS)
  gainField = AttriBox[NumberField](THIS)
  tickField = AttriBox[NumberField](THIS)
  valueField = AttriBox[NumberField](THIS)
  programEditor = AttriBox[ProgramEditor](THIS)
  swapButton = AttriBox[ToolButton](THIS)
  turnButton = AttriBox[ToolButton](THIS)
  openButton = AttriBox[ToolButton](THIS)
  closedButton = AttriBox[ToolButton](THIS)
  lowButton = AttriBox[ToolButton](THIS)
  highButton = AttriBox[ToolButton](THIS)

  #  Virtual Variables
  run: Field[Run] = Field()
  circuit: Field[Circuit] = Field()
  part: Field[tuple[str, int]] = Field()
  kind: Field[str] = Field()
  note: Field[str] = Field()
  locked: Field[tuple[int, int]] = Field()
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()
  noteColor: Field[Color] = Field()

  #  Signals
  circuitEdited = Signal(object)
  programWritten = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @run.GET
  def _getRun(self, ) -> Run:
    """The 'run' getter returns the circuit running, shown."""
    if self.__shown_run__ is None:
      self.__shown_run__ = Run(Circuit())
    return self.__shown_run__

  @circuit.GET
  def _getCircuit(self, ) -> Circuit:
    """The 'circuit' getter returns the circuit shown."""
    return self.run.circuit

  @part.GET
  def _getPart(self, ) -> tuple[str, int] | None:
    """The 'part' getter returns what is shown, ('node', index) or
    ('part', index), or 'None'."""
    return self.__shown_part__

  @kind.GET
  def _getKind(self, ) -> str:
    """The 'kind' getter returns what is shown: 'node', the kind of part
    in small letters, as 'resistor', or 'circuit' when nothing is
    selected."""
    if self.part is None:
      return 'circuit'
    kind, index = self.part
    if kind == 'node':
      return 'node'
    return type(self.circuit.parts[index]).__name__.lower()

  @locked.GET
  def _getLocked(self, ) -> tuple[int, int]:
    """The 'locked' getter returns how many of the first nodes and of the
    first parts are fixed: shown, not changed, but for a switch."""
    return self.__locked_parts__

  @locked.SET
  def _setLocked(self, locked: tuple[int, int]) -> None:
    """The 'locked' setter fixes the first nodes and parts, as many as
    'locked' says."""
    nodes, parts = locked
    self.__locked_parts__ = (int(nodes), int(parts))

  @note.GET
  def _getNote(self, ) -> str:
    """The 'note' getter returns why a number was given up, or
    nothing."""
    return self.__panel_note__

  @panelColor.GET
  def _getPanelColor(self, ) -> Color:
    return self.__fallback_panel_color__

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  @noteColor.GET
  def _getNoteColor(self, ) -> Color:
    return self.__fallback_note_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 640)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 480)

  def resizeEvent(self, event: QResizeEvent) -> None:
    PaintedWidget.resizeEvent(self, event)
    self._place()

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
    fields = set()
    for rows in _ROWS.values():
      for name, _, unit, decimals, step, least, most in rows:
        if name in fields:
          continue
        fields.add(name)
        field = getattr(self, name)
        field.unit = unit
        field.decimals = decimals
        field.step = step
        field.minimum = least
        field.maximum = most
        field.valueEdited.connect(partial(self._fieldEdited, name))
    wired = set()
    for rows in _BUTTONS.values():
      for _, names, words in rows:
        for name, text in zip(names, words):
          if name in wired:
            continue
          wired.add(name)
          button = getattr(self, name)
          button.text = text
          button.clicked.connect(partial(self._clicked, name))
    self.programEditor.programEdited.connect(self._programmed)
    self.showRun(self.run, None)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showRun(self, run: Run, part: tuple[str, int] | None) -> None:
    """The 'showRun' method shows the circuit running, 'run', and what is
    selected, 'part', or the circuit for 'None'."""
    if run.circuit is not self.run.circuit:
      self.__panel_note__ = ''
    self.__shown_run__ = run
    self.__shown_part__ = part
    shown = [row[0] for row in _ROWS[self.kind]]
    shown += [name for _, names, _ in _BUTTONS.get(self.kind, ())
              for name in names]
    fixed = self.isFixed()
    for name in self._editorNames():
      editor = getattr(self, name)
      editor.setVisible(True if name in shown else False)
      live = not fixed or name in _LIVE
      editor.setEnabled(True if live else False)
    rom = self.isRom()
    self.programEditor.setVisible(True if rom else False)
    self.programEditor.setEnabled(False if fixed else True)
    if rom:
      self.programEditor.instructions = self.instructions()
      self._showProgram()
    self._fill()
    self._place()
    self.update()

  def isFixed(self, ) -> bool:
    """The 'isFixed' method tells whether what is shown is fixed: one of
    the first nodes or parts, as many as 'locked' says."""
    if self.part is None:
      return False
    kind, index = self.part
    nodes, parts = self.locked
    return True if index < (nodes if kind == 'node' else parts) else False

  def follow(self, run: Run) -> None:
    """The 'follow' method shows what 'run', the circuit shown run on,
    reads now."""
    self.__shown_run__ = run
    if self.isRom():
      self._showProgram()
    self.update()

  def instructions(self, ) -> tuple:
    """The 'instructions' method returns the instructions a ROM's
    program may be written in: those the first computer carries out
    where it is the only computer, else all of them."""
    kinds = {part.kind for part in self.circuit.parts
             if isinstance(part, Chip)}
    if 'CPU' in kinds and 'MPU' not in kinds:
      return (*[i for i in ISA if i.mnemonic in FIRST],)
    return ISA

  def _showProgram(self, ) -> None:
    """Shows the program of the ROM shown, the word it gives now
    marked."""
    index = self.part[1]
    levels, memory = self.run.regions[index]
    address = _value(levels[0:4])
    self.programEditor.showProgram(words(memory), address)

  def _programmed(self, written: tuple) -> None:
    """A program written in the editor edits the ROM shown, then emits
    'programWritten', the computer to start it over."""
    if not self.isRom():
      return
    circuit, index = self.circuit, self.part[1]
    part = circuit.parts[index]
    self._take(circuit.withPart(index, Chip(part.kind, part.pins,
                                            program(written))))
    self.programWritten.emit()

  def showNote(self, note: str) -> None:
    """The 'showNote' method says 'note' at the bottom."""
    self.__panel_note__ = note
    self.update()

  def title(self, ) -> str:
    """The 'title' method names what is shown."""
    kind = self.kind
    if kind == 'circuit':
      return 'Circuit'
    index = self.part[1]
    if kind == 'node':
      return 'Node N%d' % (index + 1)
    name = _TITLES.get(kind, kind.capitalize())
    if kind == 'chip':
      return 'Chip %s, %s' % (self.circuit.label(index),
                              self.circuit.parts[index].kind)
    return '%s %s' % (name, self.circuit.label(index))

  def words(self, ) -> str:
    """The 'words' method says what is shown and what it reads now."""
    kind = self.kind
    if kind == 'circuit':
      return self._circuitWords()
    index = self.part[1]
    fixed = 'Fixed: it is part of the quest.\n\n' if self.isFixed() else ''
    if kind == 'node':
      return fixed + self._nodeWords(index)
    return fixed + '\n'.join(getattr(self, '_%sWords' % kind)(index))

  def labels(self, ) -> list[tuple[QRectF, str, bool]]:
    """The 'labels' method returns the words painted beside the rows:
    the heading and the rows' names, where each goes, and whether it is
    the heading."""
    margin = self.__fallback_side_margin__
    width = self.width() - 2 * margin
    top = self.__fallback_top__
    out = [(QRectF(margin, top + 4, width, _HEADING - 6), self.title(),
            True)]
    for name, label, *_ in _ROWS[self.kind]:
      field = getattr(self, name)
      out.append((QRectF(margin, field.y(), self.__fallback_label_width__,
                         field.height()), label, False))
    for label, names, _ in _BUTTONS.get(self.kind, ()):
      button = getattr(self, names[0])
      out.append((QRectF(margin, button.y(),
                         self.__fallback_button_label_width__,
                         button.height()), label, False))
    return out

  def wordsRect(self, ) -> QRectF:
    """The 'wordsRect' method returns where what is shown is said, under
    its rows."""
    margin = self.__fallback_side_margin__
    rows = len(_ROWS[self.kind]) + len(_BUTTONS.get(self.kind, ()))
    top = self.__fallback_top__ + _HEADING + rows * _ROW + 4
    if self.isRom():
      top += self.programEditor.sizeHint().height() + 8
    return QRectF(margin, top, self.width() - 2 * margin,
                  self.height() - top - 100)

  def isRom(self, ) -> bool:
    """The 'isRom' method tells whether a ROM is shown, its program to
    be written."""
    if self.kind != 'chip':
      return False
    return self.circuit.parts[self.part[1]].kind == 'ROM'

  def noteRect(self, ) -> QRectF:
    """The 'noteRect' method returns where the note goes, at the
    bottom."""
    margin = self.__fallback_side_margin__
    return QRectF(margin, self.height() - 80, self.width() - 2 * margin,
                  64)

  def dividerLine(self, ) -> tuple[QPointF, QPointF]:
    """The 'dividerLine' method returns the divider along the right,
    facing the views."""
    right = self.width() - 0.5
    return QPointF(right, 0.0), QPointF(right, float(self.height()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _editorNames() -> list[str]:
    """Every field and button, once."""
    names = []
    for rows in _ROWS.values():
      names += [row[0] for row in rows if row[0] not in names]
    for rows in _BUTTONS.values():
      for _, buttons, _ in rows:
        names += [name for name in buttons if name not in names]
    return names

  def _readings(self, index: int) -> tuple[float, float, float]:
    """The voltage across the part of 'index', the current through it
    and the power it takes, now."""
    run = self.run
    drop, current = run.drops[index], run.currents[index]
    return drop, current, drop * current

  def _flow(self, index: int) -> list[str]:
    """The voltage across the part of 'index', the current through it
    and the power it takes, in words."""
    drop, current, power = self._readings(index)
    part = self.circuit.parts[index]
    return ['Voltage across: %s' % si(drop, 'V'),
            'Current through: %s, from N%d to N%d' % (
              si(current, 'A'), part.first + 1, part.second + 1),
            'Power: %s' % si(power, 'W')]

  def _wireWords(self, index: int) -> list[str]:
    _, current, _ = self._readings(index)
    part = self.circuit.parts[index]
    return ['Current: %s, from N%d to N%d' % (si(current, 'A'),
                                             part.first + 1,
                                             part.second + 1), '',
            'A wire has no resistance: both its ends are at one '
            'voltage.', '',
            'Select a wire, then a part above, to put the part in its '
            'place.']

  def _sourceWords(self, index: int) -> list[str]:
    drop, current, _ = self._readings(index)
    part = self.circuit.parts[index]
    lines = ['Voltage at its poles: %s' % si(drop, 'V'),
             'Current out of its plus pole: %s' % si(-current, 'A'),
             'Power delivered: %s' % si(-drop * current, 'W'), '']
    if part.frequency > 0:
      lines += ['It alternates, %g times a second; its voltage is the '
                'peak, its effective voltage %s.' % (
                  part.frequency, si(part.voltage / math.sqrt(2), 'V')),
                '']
    else:
      lines += ['Steady, a battery. A frequency above nought makes it '
                'alternate.', '']
    lines.append('Its internal resistance takes R I of its voltage as '
                 'the current flows; nought for an ideal source.')
    return lines

  def _resistorWords(self, index: int) -> list[str]:
    return self._flow(index) + ['', "Ohm's law: U = R I."]

  def _lampWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    _, _, power = self._readings(index)
    share = power / part.power
    return self._flow(index) + [
      'Resistance: %s, U² / P' % si(part.resistance, 'Ω'), '',
      'It glows at %.0f %% of the power it is made for.' % (100 * share)]

  def _capacitorWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    drop, _, _ = self._readings(index)
    return self._flow(index) + [
      'Charge: %s, Q = C U' % si(part.capacitance * drop, 'C'),
      'Energy: %s, C U² / 2' % si(part.capacitance * drop * drop / 2,
                                   'J')]

  def _coilWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    _, current, _ = self._readings(index)
    return self._flow(index) + [
      'Energy: %s, L I² / 2' % si(part.inductance * current * current / 2,
                                   'J'),
      '', 'The voltage across it is L times how fast the current through '
          'it changes.']

  def _switchWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    lines = ['Closed: a wire.' if part.closed else 'Open: nothing gets '
                                                   'through.', '']
    return lines + self._flow(index)[:2]

  def _ammeterWords(self, index: int) -> list[str]:
    _, current, _ = self._readings(index)
    return ['Reads %s: the current in at its plus pole.' % si(current,
                                                               'A'), '',
            'It is ideal, a wire: put it in series, in the path of the '
            'current.']

  def _voltmeterWords(self, index: int) -> list[str]:
    drop, _, _ = self._readings(index)
    return ['Reads %s: its plus pole over its minus pole.' % si(drop,
                                                                 'V'), '',
            'It is ideal, taking no current: put it across what it '
            'measures.']

  def _diodeWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    lines = self._flow(index)
    state = ('On: it keeps %s across it.' % si(part.voltage, 'V')
             if self.run.regions[index] == 'on' else
             'Off: below %s, or turned the wrong way, nothing gets '
             'through.' % si(part.voltage, 'V'))
    return [state, ''] + lines + [
      '', 'It lets current through one way only, from the triangle to '
          'the bar, once the voltage across it reaches its own.']

  def _ledWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    _, current, _ = self._readings(index)
    return self._diodeWords(index)[:-1] + [
      'It glows at %.0f %% of the %s it is made for; give it a '
      'resistor in series, or it takes all it can.' % (
        100 * max(current, 0.0) / part.current, si(part.current, 'A'))]

  def _transistorWords(self, index: int) -> list[str]:
    run, part = self.run, self.circuit.parts[index]
    voltages = run.voltages
    base = run.bases[index]
    region = run.regions[index]
    states = {
      'off'      : 'Off: its base is below 0.7 V, nothing gets through.',
      'active'   : 'Active: the collector current is %g times the base '
                   'current; it amplifies.' % part.gain,
      'saturated': 'Fully on: as much as the circuit gives gets through, '
                   'less than %g times the base current.' % part.gain,
    }
    return [states[region], '',
            'Base current: %s' % si(base, 'A'),
            'Collector current: %s' % si(run.currents[index], 'A'),
            'Base to emitter: %s' % si(voltages[part.base]
                                       - voltages[part.second], 'V'),
            'Collector to emitter: %s' % si(run.drops[index], 'V'), '',
            'NPN: collector N%d, base N%d, emitter N%d. A small current '
            'into the base lets a large one from collector to emitter.' % (
              part.first + 1, part.base + 1, part.second + 1)]

  def _bitWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    return ['High: 5 V.' if part.high else 'Low: nought volts.', '',
            'A logic input: click Low or High to set it.']

  def _probeWords(self, index: int) -> list[str]:
    drop, _, _ = self._readings(index)
    return ['Reads %s: %s.' % ('1' if drop > 2.5 else '0',
                               si(drop, 'V')), '',
            'A logic output: high above 2.5 V, taking no current.']

  def _clockWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    region = self.run.regions[index]
    return ['%s now.' % ('High' if region == 'high' else 'Low'), '',
            'It ticks %g times a second, high the first half of each '
            'tick, low the second.' % part.frequency]

  def _chipWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    spec = part.spec
    levels, memory = self.run.regions[index]
    outputs = spec.logic(levels, memory)

    def said(ports: tuple, bits: tuple) -> str:
      words, at = [], 0
      for name, width in ports:
        words.append('%s %d' % (name, _value(bits[at:at + width])))
        at += width
      return ', '.join(words)

    lines = ['In: %s' % said(spec.ins, levels),
             'Out: %s' % said(spec.outs, outputs)]
    if part.kind in ('CPU', 'MPU'):
      lines += _machineWords(part.kind, memory)
    elif part.kind == 'ROM':
      lines.insert(0, 'Click a word to write it.')
    elif spec.memory:
      lines.append('Remembers: %s' % ' '.join(str(int(bit))
                                              for bit in memory))
    return lines + ['', spec.words, '',
                    'Its inputs read high above 2.5 V; its outputs '
                    'drive 5 V or nought from the ground. Drag its box '
                    'to move it.']

  def _businWords(self, index: int) -> list[str]:
    part = self.circuit.parts[index]
    return ['%d on the bus.' % part.value, '',
            'A bus input: four bits, bit nought the ones, set as a number '
            'from nought to fifteen.']

  def _busprobeWords(self, index: int) -> list[str]:
    value = self.run.values[self.circuit.parts[index].first]
    return ['Reads %s.' % ('?' if value is None else value), '',
            'A bus output: the number on four bits, bit nought the '
            'ones.']

  def _nodeWords(self, index: int) -> str:
    voltage = self.run.voltages[index]
    joined = len(self.circuit.joined(index))
    return '\n'.join([
      'Voltage: %s' % si(voltage, 'V'), '%d parts meet here.' % joined,
      '', 'Nought volts is the minus pole of the first source joined to '
          'it.', '',
      'Drag it to move it; drop it on another node to join them. Ctrl+'
      'click another node, then a part above, to join them by it.'])

  def _circuitWords(self, ) -> str:
    """How the circuit settles or swings of itself, and where its energy
    has gone."""
    run = self.run
    network = run.network
    if network.problem:
      return ('Short circuit: %s. Give the source an internal resistance,'
              ' or put a resistor in the way.' % network.problem)
    lines = ['How it settles or swings of itself:']
    modes = network.modes()
    for tau, frequency in modes:
      lines.append('  %s' % self._modeWords(tau, frequency))
    if not modes:
      lines.append('  at once: no capacitor or coil holds it back.')
    energies = run.energies
    lines += ['', 'Energy since it was switched on:',
              '  delivered by the sources: %s' % si(energies.delivered,
                                                   'J'),
              '  held by capacitors and coils: %s' % si(energies.stored,
                                                       'J'),
              '  turned to heat: %s' % si(energies.heat, 'J'), '',
              'Click a part to set it here.']
    return '\n'.join(lines)

  @staticmethod
  def _modeWords(tau: float, frequency: float) -> str:
    """A mode in words: its time constant, how fast it swings."""
    if frequency > 0:
      if math.isinf(tau):
        return 'swings at %s, never dying away' % si(frequency, 'Hz')
      return 'swings at %s, dying away, τ = %s' % (si(frequency, 'Hz'),
                                                    si(tau, 's'))
    if math.isinf(tau):
      return 'keeps what it holds'
    return 'settles, τ = %s' % si(tau, 's')

  def _fill(self, ) -> None:
    """Puts the numbers of what is shown in its fields, and checks its
    buttons."""
    kind, circuit = self.kind, self.circuit
    if kind == 'circuit':
      return
    index = self.part[1]
    if kind == 'node':
      node = circuit.nodes[index]
      self.xField.value, self.yField.value = node.x, node.y
      return
    part = circuit.parts[index]
    for name, *_ in _ROWS[kind]:
      spot, factor = _SPOTS[name]
      getattr(self, name).value = part[spot] / factor
    checks = ()
    if kind == 'switch':
      checks = (('openButton', not part.closed),
                ('closedButton', part.closed))
    if kind == 'bit':
      checks = (('lowButton', not part.high), ('highButton', part.high))
    if checks:
      for name, checked in checks:
        button = getattr(self, name)
        button.checked = True if checked else False
        button.update()

  def _place(self, ) -> None:
    """Places the fields and the rows of buttons beside their names."""
    margin = self.__fallback_side_margin__
    left = margin + self.__fallback_label_width__
    width = max(self.width() - left - margin, 40)
    top = self.__fallback_top__ + _HEADING
    for name, *_ in _ROWS[self.kind]:
      getattr(self, name).setGeometry(left, top, width, _ROW - 4)
      top += _ROW
    start = margin + self.__fallback_button_label_width__
    for _, names, _ in _BUTTONS.get(self.kind, ()):
      gaps = 4 * (len(names) - 1)
      share = (self.width() - start - margin - gaps) // len(names)
      for column, name in enumerate(names):
        getattr(self, name).setGeometry(start + column * (share + 4), top,
                                        share, _ROW - 4)
      top += _ROW
    hint = self.programEditor.sizeHint()
    self.programEditor.setGeometry(margin, top + 4,
                                   self.width() - 2 * margin, hint.height())

  def _fieldEdited(self, name: str, value: float) -> None:
    """A number taken edits the circuit, unless it cannot take it, when
    the panel shows it as it is and says why."""
    try:
      circuit = self._edited(name, value)
    except (ValueError, IndexError) as exception:
      return self._refuse(exception)
    self._take(circuit)

  def _clicked(self, name: str) -> None:
    """A button clicked edits the circuit: a source's or a meter's poles
    swapped, a switch opened or closed."""
    circuit, index = self.circuit, self.part[1]
    part = circuit.parts[index]
    if name in ('swapButton', 'turnButton'):
      swapped = type(part)(part.second, part.first, *part[2:])
      return self._take(circuit.withPart(index, swapped))
    if name in ('lowButton', 'highButton'):
      high = True if name == 'highButton' else False
      return self._take(circuit.withPart(index, Bit(
        part.first, part.second, high, part.name)))
    closed = True if name == 'closedButton' else False
    self._take(circuit.withPart(index, Switch(part.first, part.second,
                                              closed)))

  def _edited(self, name: str, value: float) -> Circuit:
    """The circuit with the number 'value' taken in the field 'name'."""
    circuit, index = self.circuit, self.part[1]
    if name in ('xField', 'yField'):
      node = circuit.nodes[index]
      moved = Node(value, node.y) if name == 'xField' else Node(node.x,
                                                                value)
      return circuit.withNode(index, moved)
    part = circuit.parts[index]
    values = [*part]
    spot, factor = _SPOTS[name]
    values[spot] = value * factor
    return circuit.withPart(index, type(part)(*values))

  def _refuse(self, exception: Exception) -> None:
    """Shows the circuit as it is, the note saying why."""
    words = str(exception)
    self.__panel_note__ = '%s%s.' % (words[:1].upper(), words[1:])
    self.showRun(self.run, self.part)

  def _take(self, circuit: Circuit) -> None:
    """Emits 'circuit', to be shown."""
    self.__panel_note__ = ''
    self.circuitEdited.emit(circuit)
