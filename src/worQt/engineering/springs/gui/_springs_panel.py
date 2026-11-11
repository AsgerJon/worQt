"""
SpringsPanel subclasses 'PaintedWidget' and shows the part of a system
of springs selected, as numbers to type over and buttons, or the system
and how it swings.
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
from .. import Damper, Point, Spring, SpringMassDamper, System

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap
#  Each kind's rows of numbers: the field, its name, unit, decimals, step,
#  least and greatest
_ROWS = {
  'system'   : (
    ('gravityField', 'Gravity', 'm/s²', 2, 0.1, 0, 100),
  ),
  'point'    : (
    ('massField', 'Mass', 'kg', 2, 0.1, 0.01, 1000),
    ('xField', 'x', 'm', 2, 0.05, -100, 100),
    ('yField', 'y', 'm', 2, 0.05, -100, 100),
    ('zField', 'z', 'm', 2, 0.05, -100, 100),
  ),
  'spring'   : (
    ('stiffnessField', 'Stiffness', 'N/m', 1, 5, 0.1, 1e6),
    ('restField', 'Rest length', 'm', 2, 0.05, 0, 100),
  ),
  'damper'   : (
    ('dampingField', 'Damping', 'N s/m', 2, 0.1, 0.01, 1e5),
  ),
  'component': (
    ('rodStiffnessField', 'Stiffness', 'N/m', 1, 5, 0.1, 1e6),
    ('rodDampingField', 'Damping', 'N s/m', 2, 0.1, 0, 1e5),
    ('rodRestField', 'Rest length', 'm', 2, 0.05, 0, 100),
  ),
}
#  Each kind's rows of buttons: the row's name, its buttons and their
#  words
_BUTTONS = {
  'point'    : (
    ('Moves along', ('moveXButton', 'moveYButton', 'moveZButton'),
     ('x', 'y', 'z')),
  ),
  'component': (
    ('Turns', ('fixedButton', 'hingeButton', 'freeButton'),
     ('Fixed', 'Hinge', 'Free')),
    ('About', ('aboutXButton', 'aboutYButton', 'aboutZButton'),
     ('x', 'y', 'z')),
  ),
}
_TURNINGS = ('fixed', 'hinge', 'free')
_AXES = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
_HEADING = 28  # pixels a heading takes
_ROW = 32  # pixels a row takes
_WORDS = 96  # pixels the words take


def counted(system: System) -> str:
  """
  The 'counted' function says how many points, springs, dampers and
  components 'system' has: '3 points, 2 springs, 1 damper, 0
  components'.
  """
  words = []
  for count, name in ((len(system.points), 'point'),
                      (len(system.springs), 'spring'),
                      (len(system.dampers), 'damper'),
                      (len(system.components), 'component')):
    words.append('%d %s%s' % (count, name, '' if count == 1 else 's'))
  return ', '.join(words)


class PaintSpringsPanel(AbstractPaintOp):
  """
  PaintSpringsPanel subclasses 'AbstractPaintOp' and paints the words of
  a 'SpringsPanel': its headings, the name of each row beside it, what
  is shown said in words, and the note.
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
    if widget.kind == 'system':
      painter.drawText(widget.modeWordsRect(), _WRAP, widget.modeWords())
    if widget.note:
      painter.setPen(widget.noteColor.Q)
      painter.drawText(widget.noteRect(), _WRAP, widget.note)
    return rect


class SpringsPanel(PaintedWidget):
  """
  SpringsPanel subclasses 'PaintedWidget' and shows, as numbers to type
  over and buttons, the part of the system selected: a point's mass and
  place, and the axes it moves along, an anchor none; a spring's
  stiffness and rest length; a damper's damping; a component's
  stiffness, damping and rest length, how it turns about its base,
  fixed, on a hinge or free, and the hinge's axis. With nothing
  selected, it shows the system's gravity and how it swings: a button
  for each of its slowest modes, saying its frequency, emitting
  'modePlucked' with the mode's index when clicked; or that it never
  comes to rest.

  Each number taken, and each button, emits 'systemEdited' with the
  system so; what the system cannot take is given up, the note saying
  why. As it moves, nothing may be changed but the mode it swings in,
  the note saying so.
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
  __fallback_moving_note__ = 'Moving. Reset to change the system.'

  #  Private Variables
  __shown_system__: System | None = None
  __shown_parts__: tuple = ()
  __shown_modes__: tuple | None = None
  __modes_of__: System | None = None
  __panel_editable__: bool = True
  __panel_note__: str = ''

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  wordsOp = PaintSpringsPanel()
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
  gravityField = AttriBox[NumberField](THIS)
  massField = AttriBox[NumberField](THIS)
  xField = AttriBox[NumberField](THIS)
  yField = AttriBox[NumberField](THIS)
  zField = AttriBox[NumberField](THIS)
  stiffnessField = AttriBox[NumberField](THIS)
  restField = AttriBox[NumberField](THIS)
  dampingField = AttriBox[NumberField](THIS)
  rodStiffnessField = AttriBox[NumberField](THIS)
  rodDampingField = AttriBox[NumberField](THIS)
  rodRestField = AttriBox[NumberField](THIS)
  moveXButton = AttriBox[ToolButton](THIS)
  moveYButton = AttriBox[ToolButton](THIS)
  moveZButton = AttriBox[ToolButton](THIS)
  fixedButton = AttriBox[ToolButton](THIS)
  hingeButton = AttriBox[ToolButton](THIS)
  freeButton = AttriBox[ToolButton](THIS)
  aboutXButton = AttriBox[ToolButton](THIS)
  aboutYButton = AttriBox[ToolButton](THIS)
  aboutZButton = AttriBox[ToolButton](THIS)
  mode1Button = AttriBox[ToolButton](THIS)
  mode2Button = AttriBox[ToolButton](THIS)
  mode3Button = AttriBox[ToolButton](THIS)
  mode4Button = AttriBox[ToolButton](THIS)
  mode5Button = AttriBox[ToolButton](THIS)
  mode6Button = AttriBox[ToolButton](THIS)

  #  Virtual Variables
  system: Field[System] = Field()
  parts: Field[tuple] = Field()
  kind: Field[str] = Field()
  modes: Field[tuple] = Field()
  editable: Field[bool] = Field()
  note: Field[str] = Field()
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()
  noteColor: Field[Color] = Field()

  #  Signals
  systemEdited = Signal(object)
  modePlucked = Signal(int)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @system.GET
  def _getSystem(self, ) -> System:
    """The 'system' getter returns the system shown."""
    if self.__shown_system__ is None:
      self.__shown_system__ = System()
    return self.__shown_system__

  @parts.GET
  def _getParts(self, ) -> tuple:
    """The 'parts' getter returns the parts selected, the last selected
    last."""
    return self.__shown_parts__

  @kind.GET
  def _getKind(self, ) -> str:
    """The 'kind' getter returns what is shown: 'point', 'spring',
    'damper', 'component', or 'system' when nothing is selected."""
    return self.parts[-1][0] if self.parts else 'system'

  @modes.GET
  def _getModes(self, ) -> tuple | None:
    """The 'modes' getter returns the system's modes: their frequencies,
    in Hz, and their shapes; or 'None' if it never comes to rest."""
    if self.__modes_of__ is not self.system:
      self.__modes_of__ = self.system
      self.__shown_modes__ = self.system.modes()
    return self.__shown_modes__

  @editable.GET
  def _getEditable(self, ) -> bool:
    """The 'editable' getter tells whether the system may be changed:
    as it is set up, not moving."""
    return self.__panel_editable__

  @note.GET
  def _getNote(self, ) -> str:
    """The 'note' getter returns what the note says: why a number was
    given up, or that the system moves."""
    if self.__panel_note__:
      return self.__panel_note__
    return '' if self.editable else self.__fallback_moving_note__

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
    for rows in _ROWS.values():
      for name, _, unit, decimals, step, least, most in rows:
        field = getattr(self, name)
        field.unit = unit
        field.decimals = decimals
        field.step = step
        field.minimum = least
        field.maximum = most
        field.valueEdited.connect(partial(self._fieldEdited, name))
    for rows in _BUTTONS.values():
      for _, names, words in rows:
        for name, text in zip(names, words):
          button = getattr(self, name)
          button.text = text
          button.clicked.connect(partial(self._clicked, name))
    for index, button in enumerate(self.modeButtons()):
      button.clicked.connect(partial(self.modePlucked.emit, index))
    self.showSystem(self.system, (), True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def modeButtons(self, ) -> tuple[ToolButton, ...]:
    """The 'modeButtons' method returns the buttons of the modes, the
    slowest first."""
    return (self.mode1Button, self.mode2Button, self.mode3Button,
            self.mode4Button, self.mode5Button, self.mode6Button)

  def buttonRows(self, ) -> list[tuple[str, tuple[str, ...]]]:
    """The 'buttonRows' method returns the rows of buttons shown: each
    its name and its buttons' names; the hinge's axis only for a
    component on a hinge."""
    rows = [(label, names) for label, names, _ in
            _BUTTONS.get(self.kind, ())]
    if self.kind == 'component' and self._shownPart().turning != 'hinge':
      rows = rows[:1]
    return rows

  def showSystem(self, system: System, parts: tuple,
                 editable: bool) -> None:
    """The 'showSystem' method shows 'system', the parts selected,
    'parts', and whether it may be changed, 'editable'."""
    if system is not self.__shown_system__ or not editable:
      self.__panel_note__ = ''
    self.__shown_system__ = system
    self.__shown_parts__ = (*parts,)
    self.__panel_editable__ = True if editable else False
    kind = self.kind
    shown = [row[0] for row in _ROWS[kind]]
    shown += [name for _, names in self.buttonRows() for name in names]
    for name in self._editorNames():
      editor = getattr(self, name)
      editor.setVisible(True if name in shown else False)
      editor.setEnabled(self.editable)
    self._fill(kind)
    self._showModes()
    self._place()
    self.update()

  def showNote(self, note: str) -> None:
    """The 'showNote' method says 'note' under the words."""
    self.__panel_note__ = note
    self.update()

  def title(self, ) -> str:
    """The 'title' method names what is shown."""
    kind = self.kind
    if kind == 'system':
      return 'System'
    index = self.parts[-1][1]
    if kind == 'point':
      pinned = self.system.points[index].pinned
      return '%s P%d' % ('Anchor' if pinned else 'Mass', index + 1)
    return '%s %s%d' % (kind.capitalize(), kind[0].upper(), index + 1)

  def words(self, ) -> str:
    """The 'words' method says what is shown, or how to show more."""
    system, kind = self.system, self.kind
    points = [i for k, i in self.parts if k == 'point']
    if len(points) >= 2:
      names = ' and '.join('P%d' % (i + 1) for i in points[-2:])
      return '%s selected: Add spring or Add damper joins them.' % names
    if kind == 'point':
      return ('Drag it to move it. Ctrl+click another point to join '
              'them by a spring or a damper.')
    if kind == 'component':
      return self._componentWords()
    if kind in ('spring', 'damper'):
      link = self._shownPart()
      between = 'Between P%d and P%d' % (link.first + 1, link.second + 1)
      if kind == 'damper':
        return '%s.' % between
      places = system.positions()
      long = float((places[link.second] - places[link.first]).norm())
      return '%s, %.3f m long set up.' % (between, long)
    return ('%s. Click a part to set it here; drag the space to turn '
            'it.' % counted(system))

  def modeWords(self, ) -> str:
    """The 'modeWords' method says how the system swings."""
    if self.modes is None:
      return 'It never comes to rest: something falls for ever.'
    return 'Click a mode to set the system swinging in it alone.'

  def labels(self, ) -> list[tuple[QRectF, str, bool]]:
    """The 'labels' method returns the words painted beside the rows:
    the headings and the rows' names, where each goes, and whether it is
    a heading."""
    margin = self.__fallback_side_margin__
    width = self.width() - 2 * margin
    labels = self.__fallback_label_width__
    top = self.__fallback_top__
    out = [(QRectF(margin, top + 4, width, _HEADING - 6), self.title(),
            True)]
    for name, label, *_ in _ROWS[self.kind]:
      field = getattr(self, name)
      out.append((QRectF(margin, field.y(), labels, field.height()), label,
                  False))
    for label, names in self.buttonRows():
      button = getattr(self, names[0])
      short = self.__fallback_button_label_width__
      out.append((QRectF(margin, button.y(), short, button.height()),
                  label, False))
    if self.kind == 'system':
      top = self._modesTop()
      out.append((QRectF(margin, top - _HEADING + 4, width, _HEADING - 6),
                  'Modes', True))
    return out

  def modeWordsRect(self, ) -> QRectF:
    """The 'modeWordsRect' method returns where how the system swings
    is said, under the heading of the modes."""
    margin = self.__fallback_side_margin__
    return QRectF(margin, self._modesTop(), self.width() - 2 * margin, 36)

  def wordsRect(self, ) -> QRectF:
    """The 'wordsRect' method returns where what is shown is said, under
    its rows."""
    margin = self.__fallback_side_margin__
    top = self._rowsBottom()
    return QRectF(margin, top + 4, self.width() - 2 * margin, _WORDS)

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
    """Every field and button of the parts."""
    names = [row[0] for rows in _ROWS.values() for row in rows]
    return names + [name for rows in _BUTTONS.values()
                    for _, buttons, _ in rows for name in buttons]

  def _shownPart(self, ) -> tuple:
    """The part shown."""
    kind, index = self.parts[-1]
    system = self.system
    return {'point'    : system.points, 'spring': system.springs,
            'damper'   : system.dampers,
            'component': system.components}[kind][index]

  def _componentWords(self, ) -> str:
    """What the component shown is and does."""
    rod = self._shownPart()
    turns = {
      'fixed': 'its mass moves only along it',
      'hinge': 'it turns about its hinge only',
      'free' : 'it turns any way about its base',
    }[rod.turning]
    return ('A rod from P%d to P%d, rigid but for its length, a spring '
            'and a damper inside: %s. Its mass is that of P%d.' % (
              rod.base + 1, rod.tip + 1, turns, rod.tip + 1))

  def _fill(self, kind: str) -> None:
    """Puts the numbers of what is shown in its fields, and checks its
    buttons."""
    if kind == 'system':
      self.gravityField.value = self.system.gravity
      return
    part = self._shownPart()
    if kind == 'point':
      self.massField.value = part.mass
      for field, value in zip((self.xField, self.yField, self.zField),
                              part.at):
        field.value = value
      self._checkButtons(_BUTTONS['point'][0][1],
                  [axis in part.moves for axis in 'xyz'])
    elif kind == 'spring':
      self.stiffnessField.value = part.stiffness
      self.restField.value = part.rest
    elif kind == 'damper':
      self.dampingField.value = part.damping
    else:
      self.rodStiffnessField.value = part.stiffness
      self.rodDampingField.value = part.damping
      self.rodRestField.value = part.rest
      turns, about = _BUTTONS['component']
      self._checkButtons(turns[1], [part.turning == t for t in _TURNINGS])
      self._checkButtons(about[1], [part.axis == axis for axis in _AXES])

  def _checkButtons(self, names: tuple, checks: list) -> None:
    """Checks the buttons of 'names' as 'checks' says."""
    for name, checked in zip(names, checks):
      button = getattr(self, name)
      button.checked = True if checked else False
      button.update()

  def _showModes(self, ) -> None:
    """Shows a button for each of the slowest modes, saying its
    frequency, while nothing is selected."""
    shown = self.kind == 'system' and self.modes is not None
    frequencies = self.modes[0] if shown else ()
    for index, button in enumerate(self.modeButtons()):
      visible = shown and index < len(frequencies)
      button.setVisible(visible)
      if visible:
        button.text = 'Mode %d · %.3f Hz' % (index + 1, frequencies[index])
        button.update()

  def _rowsBottom(self, ) -> int:
    """Where the rows of numbers and of buttons end."""
    count = len(_ROWS[self.kind]) + len(self.buttonRows())
    return self.__fallback_top__ + _HEADING + count * _ROW

  def _modesTop(self, ) -> int:
    """Where the modes' words are, under the system's words."""
    return self._rowsBottom() + 4 + _WORDS + _HEADING + 4

  def _place(self, ) -> None:
    """Places the fields and the rows of buttons beside their names, and
    the modes' buttons under their heading."""
    margin = self.__fallback_side_margin__
    left = margin + self.__fallback_label_width__
    width = max(self.width() - left - margin, 40)
    top = self.__fallback_top__ + _HEADING
    for name, *_ in _ROWS[self.kind]:
      getattr(self, name).setGeometry(left, top, width, _ROW - 4)
      top += _ROW
    start = margin + self.__fallback_button_label_width__
    third = (self.width() - start - margin - 8) // 3
    for _, names in self.buttonRows():
      for column, name in enumerate(names):
        getattr(self, name).setGeometry(start + column * (third + 4), top,
                                        third, _ROW - 4)
      top += _ROW
    top = self._modesTop() + 40
    for button in self.modeButtons():
      button.setGeometry(margin, top, self.width() - 2 * margin, _ROW - 4)
      top += _ROW

  def _fieldEdited(self, name: str, value: float) -> None:
    """A number taken edits the system, unless it cannot take it, when
    the panel shows it as it is and says why."""
    try:
      system = self._edited(name, value)
    except (ValueError, IndexError) as exception:
      return self._refuse(exception)
    self._take(system)

  def _clicked(self, name: str) -> None:
    """A button clicked edits the system: the point shown moving along
    an axis or not, the component shown turning so, or about an axis;
    unless it cannot take it, when the panel says why."""
    try:
      system = self._buttonEdited(name)
    except ValueError as exception:
      return self._refuse(exception)
    self._take(system)

  def _buttonEdited(self, name: str) -> System:
    """The system with the button 'name' clicked."""
    system, part = self.system, self._shownPart()
    index = self.parts[-1][1]
    moves, turns, about = (_BUTTONS['point'][0][1],
                           *[row[1] for row in _BUTTONS['component']])
    if name in moves:
      axis = 'xyz'[moves.index(name)]
      kept = ''.join(a for a in 'xyz' if (a in part.moves) != (a == axis))
      return system.withPoint(index, part.moving(kept))
    if name in turns:
      turning = _TURNINGS[turns.index(name)]
      rod = part.turned(turning)
      if turning == 'hinge':
        rod = rod.about(self._acrossAxis(rod))
      return system.withComponent(index, rod)
    return system.withComponent(index, part.about(_AXES[about.index(name)]))

  def _acrossAxis(self, rod: SpringMassDamper) -> tuple:
    """The axis 'rod' turns about on a hinge: its own if it is across
    the rod, else the axis most across it."""
    places = self.system.positions()
    along = (places[rod.tip] - places[rod.base]).tolist()
    size = math.sqrt(sum(v * v for v in along))

    def lean(axis: tuple) -> float:
      return abs(sum(a * b for a, b in zip(axis, along))) / size

    if lean(rod.axis) <= 0.99 * math.sqrt(sum(a * a for a in rod.axis)):
      return rod.axis
    _, best = min((lean(axis), axis) for axis in _AXES)
    return best

  def _edited(self, name: str, value: float) -> System:
    """The system with the number 'value' taken in the field 'name'."""
    system = self.system
    if name == 'gravityField':
      return system.withGravity(value)
    part, (_, index) = self._shownPart(), self.parts[-1]
    if name == 'massField':
      return system.withPoint(index, Point(part.at, value, part.moves))
    if name in ('xField', 'yField', 'zField'):
      at = [*part.at]
      at['xyz'.index(name[0])] = value
      return system.withPoint(index, part.movedTo((*at,)))
    if name.startswith('rod'):
      values = [*part]
      key = {'rodStiffnessField': 2, 'rodDampingField': 3,
             'rodRestField'     : 4}[name]
      values[key] = value
      return system.withComponent(index, SpringMassDamper(*values))
    if name in ('stiffnessField', 'restField'):
      springs = [*system.springs]
      stiffness, rest = part.stiffness, part.rest
      if name == 'stiffnessField':
        stiffness = value
      else:
        rest = value
      springs[index] = Spring(part.first, part.second, stiffness, rest)
      return system.withSprings(*springs)
    dampers = [*system.dampers]
    dampers[index] = Damper(part.first, part.second, value)
    return system.withDampers(*dampers)

  def _refuse(self, exception: Exception) -> None:
    """Shows the system as it is, the note saying why."""
    words = str(exception)
    self.__panel_note__ = '%s%s.' % (words[:1].upper(), words[1:])
    self.showSystem(self.system, self.parts, self.editable)

  def _take(self, system: System) -> None:
    """Shows 'system' and emits it."""
    self.showSystem(system, self.parts, self.editable)
    self.systemEdited.emit(system)
