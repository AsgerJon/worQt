"""
DiagramsPanel subclasses 'PaintedWidget' and shows the part of a frame
selected, as numbers to type over and buttons, or the frame and what
holds it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

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
from .. import Analysis, Frame, LineLoad, Member, Node, PointLoad
from .. import Support

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap
#  Each kind's rows of numbers: the field, its name, unit, decimals,
#  step, least and greatest
_ROWS = {
  'frame' : (),
  'node'  : (
    ('xField', 'x', 'm', 2, 0.1, -1000, 1000),
    ('yField', 'y', 'm', 2, 0.1, -1000, 1000),
  ),
  'member': (
    ('eiField', 'EI', 'kNm²', 0, 1000, 1, 1e9),
    ('eaField', 'EA', 'kN', 0, 10000, 1, 1e10),
  ),
  'support': (),
  'point' : (
    ('atField', 'At', 'm', 2, 0.1, 0, 1000),
    ('downField', 'Down', 'kN', 1, 1, -1e6, 1e6),
    ('rightField', 'Right', 'kN', 1, 1, -1e6, 1e6),
  ),
  'line'  : (
    ('fromField', 'From', 'm', 2, 0.1, 0, 1000),
    ('toField', 'To', 'm', 2, 0.1, 0, 1000),
    ('firstField', 'At start', 'kN/m', 1, 1, -1e6, 1e6),
    ('lastField', 'At end', 'kN/m', 1, 1, -1e6, 1e6),
  ),
  'moment': (
    ('momentAtField', 'At', 'm', 2, 0.1, 0, 1000),
    ('momentField', 'Moment', 'kNm', 1, 1, -1e6, 1e6),
  ),
}
#  Each kind's rows of buttons: the row's name, its buttons and their
#  words
_BUTTONS = {
  'member' : (
    ('Hinged at', ('startButton', 'endButton'), ('Start', 'End')),
  ),
  'support': (
    ('Kind', ('pinButton', 'rollerButton', 'fixedButton'),
     ('Pin', 'Roller', 'Fixed')),
  ),
  'line'   : (
    ('Pushes', ('downButton', 'rightButton'), ('Down', 'Right')),
  ),
}
_HEADING = 28  # pixels a heading takes
_ROW = 32  # pixels a row takes


def _number(value: float) -> str:
  """'value' written to a hundredth, without a needless minus."""
  return '%.2f' % (value + 0.0)


class PaintDiagramsPanel(AbstractPaintOp):
  """
  PaintDiagramsPanel subclasses 'AbstractPaintOp' and paints the words
  of a 'DiagramsPanel': its heading, the name of each row beside it,
  what is shown said in words, and the note.
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


class DiagramsPanel(PaintedWidget):
  """
  DiagramsPanel subclasses 'PaintedWidget' and shows, as numbers to type
  over and buttons, the part of the frame selected: a node's place; a
  member's stiffness, EI and EA, and its hinges; a support's kind; a
  point load's place along its member and its force, down and right; a
  line load's stretch, its intensity at either end and which way it
  pushes; a moment's place and size. With nothing selected, it says how
  indeterminate the frame is and what each support pushes with.

  Each number taken, and each button, emits 'frameEdited' with the
  frame so; what the frame cannot take is given up, the note saying
  why.
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
  __shown_analysis__: Analysis | None = None
  __shown_part__: tuple[str, int] | None = None
  __panel_note__: str = ''

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  wordsOp = PaintDiagramsPanel()
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
  eiField = AttriBox[NumberField](THIS)
  eaField = AttriBox[NumberField](THIS)
  atField = AttriBox[NumberField](THIS)
  downField = AttriBox[NumberField](THIS)
  rightField = AttriBox[NumberField](THIS)
  fromField = AttriBox[NumberField](THIS)
  toField = AttriBox[NumberField](THIS)
  firstField = AttriBox[NumberField](THIS)
  lastField = AttriBox[NumberField](THIS)
  momentAtField = AttriBox[NumberField](THIS)
  momentField = AttriBox[NumberField](THIS)
  startButton = AttriBox[ToolButton](THIS)
  endButton = AttriBox[ToolButton](THIS)
  pinButton = AttriBox[ToolButton](THIS)
  rollerButton = AttriBox[ToolButton](THIS)
  fixedButton = AttriBox[ToolButton](THIS)
  downButton = AttriBox[ToolButton](THIS)
  rightButton = AttriBox[ToolButton](THIS)

  #  Virtual Variables
  analysis: Field[Analysis] = Field()
  frame: Field[Frame] = Field()
  part: Field[tuple[str, int]] = Field()
  kind: Field[str] = Field()
  note: Field[str] = Field()
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()
  noteColor: Field[Color] = Field()

  #  Signals
  frameEdited = Signal(object)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @analysis.GET
  def _getAnalysis(self, ) -> Analysis:
    """The 'analysis' getter returns the frame shown, reckoned."""
    if self.__shown_analysis__ is None:
      self.__shown_analysis__ = Analysis(Frame())
    return self.__shown_analysis__

  @frame.GET
  def _getFrame(self, ) -> Frame:
    """The 'frame' getter returns the frame shown."""
    return self.analysis.frame

  @part.GET
  def _getPart(self, ) -> tuple[str, int] | None:
    """The 'part' getter returns the part shown, or 'None'."""
    return self.__shown_part__

  @kind.GET
  def _getKind(self, ) -> str:
    """The 'kind' getter returns what is shown: 'node', 'member',
    'support', 'point', 'line', 'moment', or 'frame' when nothing is
    selected."""
    if self.part is None:
      return 'frame'
    kind, index = self.part
    if kind != 'load':
      return kind
    load = self.frame.loads[index]
    if isinstance(load, PointLoad):
      return 'point'
    return 'line' if isinstance(load, LineLoad) else 'moment'

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
    self.showAnalysis(self.analysis, None)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showAnalysis(self, analysis: Analysis,
                   part: tuple[str, int] | None) -> None:
    """The 'showAnalysis' method shows the frame reckoned, 'analysis',
    and the part selected, 'part', or the frame for 'None'."""
    if analysis is not self.__shown_analysis__:
      self.__panel_note__ = ''
    self.__shown_analysis__ = analysis
    self.__shown_part__ = part
    shown = [row[0] for row in _ROWS[self.kind]]
    shown += [name for _, names, _ in _BUTTONS.get(self.kind, ())
              for name in names]
    for name in self._editorNames():
      getattr(self, name).setVisible(True if name in shown else False)
    self._fill()
    self._place()
    self.update()

  def showNote(self, note: str) -> None:
    """The 'showNote' method says 'note' at the bottom."""
    self.__panel_note__ = note
    self.update()

  def title(self, ) -> str:
    """The 'title' method names what is shown."""
    kind = self.kind
    if kind == 'frame':
      return 'Frame'
    index = self.part[1]
    names = {'node'  : 'Node N%d', 'member': 'Member M%d',
             'support': 'Support at N%d', 'point': 'Point load %d',
             'line'  : 'Line load %d', 'moment': 'Moment %d'}
    if kind == 'support':
      return names[kind] % (self.frame.supports[index].node + 1)
    return names[kind] % (index + 1)

  def words(self, ) -> str:
    """The 'words' method says what is shown, or how to show more."""
    kind, frame = self.kind, self.frame
    if kind == 'frame':
      return self._frameWords()
    index = self.part[1]
    if kind == 'node':
      return ('Drag it to move it, to the decimetre. Ctrl+click another '
              'node, then Add member, to join them.')
    if kind == 'member':
      member = frame.members[index]
      return ('From N%d to N%d, %.2f m long. A hinged end takes no '
              'moment.' % (member.first + 1, member.second + 1,
                           frame.length(index)))
    if kind == 'support':
      return ('A pin holds the frame along x and y, a roller along y, a '
              'fixed end turning too.')
    load = frame.loads[index]
    where = 'On M%d, measured from N%d.' % (
      load.member + 1, frame.members[load.member].first + 1)
    if kind == 'moment':
      return '%s Anticlockwise positive.' % where
    return '%s Drag it along its member.' % where

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
    return QRectF(margin, top, self.width() - 2 * margin,
                  self.height() - top - 100)

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
    """Every field and button."""
    names = [row[0] for rows in _ROWS.values() for row in rows]
    return names + [name for rows in _BUTTONS.values()
                    for _, buttons, _ in rows for name in buttons]

  def _frameWords(self, ) -> str:
    """How indeterminate the frame is, and what each support pushes
    with."""
    analysis, frame = self.analysis, self.frame
    if analysis.held:
      return 'Not held: %s.' % analysis.held
    count = frame.indeterminacy()
    lines = ['Statically determinate.' if count == 0 else
             'Statically indeterminate %d times.' % count, '',
             'Reactions, up and right positive, moments anticlockwise:']
    for support, (rx, ry, turning) in zip(frame.supports,
                                          analysis.reactions):
      words = 'N%d: Rx %s kN, Ry %s kN' % (support.node + 1,
                                           _number(rx), _number(ry))
      if support.kind == 'fixed':
        words += ', M %s kNm' % _number(turning)
      lines.append(words)
    lines += ['', 'Click a part to set it here.']
    return '\n'.join(lines)

  def _fill(self, ) -> None:
    """Puts the numbers of what is shown in its fields, and checks its
    buttons."""
    kind, frame = self.kind, self.frame
    if kind == 'frame':
      return
    index = self.part[1]
    if kind == 'node':
      node = frame.nodes[index]
      self.xField.value, self.yField.value = node.x, node.y
    elif kind == 'member':
      member = frame.members[index]
      self.eiField.value, self.eaField.value = member.EI, member.EA
      self._checkButtons(('startButton', 'endButton'),
                         (member.startHinge, member.endHinge))
    elif kind == 'support':
      support = frame.supports[index]
      self._checkButtons(('pinButton', 'rollerButton', 'fixedButton'),
                         [support.kind == k for k in Support.kinds()])
    elif kind == 'point':
      load = frame.loads[index]
      self.atField.value = load.at
      self.downField.value, self.rightField.value = load.down, load.right
    elif kind == 'line':
      load = frame.loads[index]
      self.fromField.value, self.toField.value = load.start, load.end
      self.firstField.value, self.lastField.value = load.first, load.last
      self._checkButtons(('downButton', 'rightButton'),
                         (load.direction == 'down',
                          load.direction == 'right'))
    else:
      load = frame.loads[index]
      self.momentAtField.value = load.at
      self.momentField.value = load.moment

  def _checkButtons(self, names: tuple, checks: tuple | list) -> None:
    """Checks the buttons of 'names' as 'checks' says."""
    for name, checked in zip(names, checks):
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

  def _fieldEdited(self, name: str, value: float) -> None:
    """A number taken edits the frame, unless it cannot take it, when
    the panel shows it as it is and says why."""
    try:
      frame = self._edited(name, value)
    except (ValueError, IndexError) as exception:
      return self._refuse(exception)
    self._take(frame)

  def _clicked(self, name: str) -> None:
    """A button clicked edits the frame: a member's hinge, a support's
    kind, a line load's way; unless it cannot take it."""
    frame, index = self.frame, self.part[1]
    try:
      if name in ('startButton', 'endButton'):
        member = frame.members[index]
        start = member.startHinge != (name == 'startButton')
        end = member.endHinge != (name == 'endButton')
        frame = frame.withMember(index, member.hinged(start, end))
      elif name in ('pinButton', 'rollerButton', 'fixedButton'):
        kind = name[:-len('Button')]
        support = frame.supports[index]
        frame = frame.withSupport(index, Support(support.node, kind))
      else:
        load = frame.loads[index]
        way = name[:-len('Button')]
        frame = frame.withLoad(index, LineLoad(*load[:5], way))
    except ValueError as exception:
      return self._refuse(exception)
    self._take(frame)

  def _edited(self, name: str, value: float) -> Frame:
    """The frame with the number 'value' taken in the field 'name'."""
    frame, index = self.frame, self.part[1]
    if name in ('xField', 'yField'):
      node = frame.nodes[index]
      moved = Node(value, node.y) if name == 'xField' else Node(node.x,
                                                                value)
      return frame.withNode(index, moved)
    if name in ('eiField', 'eaField'):
      member = frame.members[index]
      values = [*member]
      values[2 if name == 'eiField' else 3] = value
      return frame.withMember(index, Member(*values))
    load = frame.loads[index]
    values = [*load]
    spot = {'atField'      : 1, 'downField': 2, 'rightField': 3,
            'fromField'    : 1, 'toField': 2, 'firstField': 3,
            'lastField'    : 4, 'momentAtField': 1,
            'momentField'  : 2}[name]
    values[spot] = value
    return frame.withLoad(index, type(load)(*values))

  def _refuse(self, exception: Exception) -> None:
    """Shows the frame as it is, the note saying why."""
    words = str(exception)
    self.__panel_note__ = '%s%s.' % (words[:1].upper(), words[1:])
    self.showAnalysis(self.analysis, self.part)

  def _take(self, frame: Frame) -> None:
    """Emits 'frame', to be shown."""
    self.__panel_note__ = ''
    self.frameEdited.emit(frame)
