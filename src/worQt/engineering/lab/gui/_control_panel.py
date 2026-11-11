"""
ControlPanel subclasses 'PaintedWidget' and shows the rig's control loop
and the part of the rig selected, as numbers to type over.
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
from .. import Actuator, RCBeam, Rig, Support
from ._beam_view import BeamView

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap
#  The control's rows: the field, its name, unit, decimals, step, least,
#  greatest and the control's field it sets
_CONTROL_ROWS = (
  ('transducerField', 'Reads T', '', 0, 1, 1, 99, 'transducer'),
  ('actuatorField', 'Drives A', '', 0, 1, 1, 99, 'actuator'),
  ('rateField', 'Rate', 'mm/s', 3, 0.01, -10, 10, 'rate'),
  ('limitField', 'To', 'mm', 1, 1, -500, 500, 'limit'),
  ('stepField', 'Step', '', 4, 0.0005, 0.0001, 1, 'step'),
  ('kpField', 'Kp', '1/s', 3, 0.05, 0, 100, 'kp'),
  ('kiField', 'Ki', '1/s²', 3, 0.01, 0, 100, 'ki'),
  ('kdField', 'Kd', '', 3, 0.01, 0, 100, 'kd'),
  ('speedField', 'Top speed', 'mm/s', 2, 0.1, 0.01, 100, 'speed'),
)
#  The part's rows, alike
_PART_ROWS = (
  ('atField', 'At', 'mm', 0, 10, 0, 20000),
  ('followsField', 'Follows A', '', 0, 1, 1, 99),
  ('shareField', 'Share', '×', 2, 0.05, -10, 10),
  ('gapFromField', 'From', 'mm', 0, 10, 0, 20000),
  ('gapToField', 'To', 'mm', 0, 10, 0, 20000),
)
_HEADING = 28  # pixels a heading takes
_ROW = 32  # pixels a row takes


class PaintControlPanel(AbstractPaintOp):
  """
  PaintControlPanel subclasses 'AbstractPaintOp' and paints the words of
  a 'ControlPanel': each heading, the name of each row shown beside its
  field, what the part selected is, and the note under them.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the words of the panel."""
    widget = self.widget
    for box, text, heading in widget.words():
      font = widget.headingFont if heading else widget.font
      painter.setFont(font)
      painter.setPen(font.color.Q)
      painter.drawText(box, _LEFT, text)
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    painter.drawText(widget.partWordsRect(), _WRAP, widget.partWords())
    if widget.note:
      painter.setFont(widget.font)
      painter.setPen(widget.noteColor.Q)
      painter.drawText(widget.noteRect(), _WRAP, widget.note)
    return rect


class ControlPanel(PaintedWidget):
  """
  ControlPanel subclasses 'PaintedWidget' and shows, as numbers to type
  over, the rig's control loop: the transducer it reads and the
  actuator it drives, by their numbers; its command, a ramp at a rate
  to a limit, up positive as the transducer reads, so below nought for
  a ramp down; its step, the share of the ramp each step of OpenSees
  takes, so 0.001 is a thousand steps to the limit; its PID gains and
  the actuator's top speed. Under it,
  the part of the rig selected: where it is, and for a support whether
  it is a pin, a roller or fixed, by its buttons; for an actuator not
  driven, which it follows and the share of its force it pushes with.

  'showRig' shows a rig and the part selected on it. Each number taken,
  and each button, emits 'rigEdited' with the rig so; driving another
  actuator has the one driven before follow it. What the rig or the
  beam cannot take is given up, the note under the rows saying why;
  'showNote' says something there. 'setStage' shows how far the test
  has come: in 'setup', everything may be changed; in 'testing', only
  the control's ramp, gains and top speed, as a servo controller is
  retuned as it runs, each number taken emitting 'controlTuned' with
  the control so; once 'tested', nothing. The note says which. A new
  limit turns the rate's sign to head for it, so 'To' 0 under test
  unloads the beam.
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
  __fallback_panel_width__ = 270
  __fallback_side_margin__ = 16
  __fallback_label_width__ = 104
  __fallback_top__ = 10

  __fallback_testing_note__ = ('Under test: the ramp, the gains and the '
                               'top speed change as it runs; the rest '
                               'waits for New beam.')
  __fallback_tested_note__ = ('Tested. New beam casts the beam afresh, '
                              'to change the rig.')

  #  Private Variables
  __shown_setup__: tuple[RCBeam, Rig] | None = None
  __shown_part__: tuple[str, int] | None = None
  __panel_note__: str = ''
  __panel_stage__: str = 'setup'

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  wordsOp = PaintControlPanel()
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
  transducerField = AttriBox[NumberField](THIS)
  actuatorField = AttriBox[NumberField](THIS)
  rateField = AttriBox[NumberField](THIS)
  limitField = AttriBox[NumberField](THIS)
  stepField = AttriBox[NumberField](THIS)
  kpField = AttriBox[NumberField](THIS)
  kiField = AttriBox[NumberField](THIS)
  kdField = AttriBox[NumberField](THIS)
  speedField = AttriBox[NumberField](THIS)
  atField = AttriBox[NumberField](THIS)
  followsField = AttriBox[NumberField](THIS)
  shareField = AttriBox[NumberField](THIS)
  gapFromField = AttriBox[NumberField](THIS)
  gapToField = AttriBox[NumberField](THIS)
  pinButton = AttriBox[ToolButton](THIS)
  rollerButton = AttriBox[ToolButton](THIS)
  fixedButton = AttriBox[ToolButton](THIS)

  #  Virtual Variables
  beam: Field[RCBeam] = Field()
  rig: Field[Rig] = Field()
  part: Field[tuple[str, int]] = Field()
  stage: Field[str] = Field()
  note: Field[str] = Field()
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()
  noteColor: Field[Color] = Field()

  #  Signals
  rigEdited = Signal(object)
  beamEdited = Signal(object)
  controlTuned = Signal(object)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getSetup(self, ) -> tuple[RCBeam, Rig]:
    if self.__shown_setup__ is None:
      beam = RCBeam()
      self.__shown_setup__ = (beam, Rig.standard(beam))
    return self.__shown_setup__

  @beam.GET
  def _getBeam(self, ) -> RCBeam:
    """The 'beam' getter returns the beam the rig is for."""
    return self._getSetup()[0]

  @rig.GET
  def _getRig(self, ) -> Rig:
    """The 'rig' getter returns the rig shown."""
    return self._getSetup()[1]

  @part.GET
  def _getPart(self, ) -> tuple[str, int] | None:
    """The 'part' getter returns the part of the rig shown, or
    'None'."""
    return self.__shown_part__

  @stage.GET
  def _getStage(self, ) -> str:
    """The 'stage' getter returns how far the test has come: 'setup',
    'testing' or 'tested'."""
    return self.__panel_stage__

  @note.GET
  def _getNote(self, ) -> str:
    """The 'note' getter returns what the note under the rows says:
    why a number was given up, or else what may be changed now."""
    if self.__panel_note__:
      return self.__panel_note__
    if self.stage == 'testing':
      return self.__fallback_testing_note__
    if self.stage == 'tested':
      return self.__fallback_tested_note__
    return ''

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
    return QSize(self.__fallback_panel_width__, 600)

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
    rows = [row[:7] for row in _CONTROL_ROWS] + [*_PART_ROWS]
    for name, _, unit, decimals, step, least, most in rows:
      field = getattr(self, name)
      field.unit = unit
      field.decimals = decimals
      field.step = step
      field.minimum = least
      field.maximum = most
      field.valueEdited.connect(partial(self._fieldEdited, name))
    for button, kind in self._kindButtons():
      button.text = kind.capitalize()
      button.clicked.connect(partial(self._setKind, kind))
    self.showRig(self.beam, self.rig, None)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showRig(
      self, beam: RCBeam, rig: Rig,
      part: tuple[str, int] | None
      ) -> None:
    """The 'showRig' method shows the control of 'rig' on 'beam', and
    'part' of it, or none for 'None'."""
    self.__shown_setup__ = (beam, rig)
    self.__shown_part__ = part
    control = rig.control
    self.transducerField.value = control.transducer + 1
    self.actuatorField.value = control.actuator + 1
    for name, *_, key in _CONTROL_ROWS[2:]:
      getattr(self, name).value = getattr(control, key)
    shown = self.partRows()
    for name, *_ in _PART_ROWS:
      getattr(self, name).setVisible(True if name in shown else False)
    kind, index = part if part is not None else ('', 0)
    if kind == 'support':
      self.atField.value = rig.supports[index].at
    elif kind == 'actuator':
      actuator = rig.actuators[index]
      self.atField.value = actuator.at
      self.followsField.value = max(actuator.follows, 0) + 1
      self.shareField.value = actuator.share
    elif kind == 'transducer':
      self.atField.value = rig.transducers[index]
    elif kind == 'gap':
      start, end = beam.stirrups.gaps[index]
      self.gapFromField.value = start
      self.gapToField.value = end
    for button, name in self._kindButtons():
      button.setVisible(True if kind == 'support' else False)
      if kind == 'support':
        button.checked = rig.supports[index].kind == name
        button.update()
    self._place()
    self.update()

  def showNote(self, note: str) -> None:
    """The 'showNote' method says 'note' under the rows."""
    self.__panel_note__ = note
    self.update()

  def setStage(self, stage: str) -> None:
    """The 'setStage' method shows how far the test has come, 'setup',
    'testing' or 'tested', freeing what may be changed then and locking
    the rest."""
    if stage not in ('setup', 'testing', 'tested'):
      raise ValueError('no such stage: %s' % stage)
    if stage != self.__panel_stage__:
      self.__panel_note__ = ''
    self.__panel_stage__ = stage
    tuning = [getattr(self, row[0]) for row in _CONTROL_ROWS[2:]]
    for widget in self._editors():
      if stage == 'setup':
        widget.setEnabled(True)
      elif stage == 'testing':
        widget.setEnabled(True if widget in tuning else False)
      else:
        widget.setEnabled(False)
    self.update()

  def partRows(self, ) -> list[str]:
    """The 'partRows' method returns the part's rows shown: where it is,
    and for an actuator not driven, what it follows and its share."""
    part = self.part
    if part is None:
      return []
    kind, index = part
    if kind == 'gap':
      return ['gapFromField', 'gapToField']
    if kind == 'actuator' and index != self.rig.driven:
      return ['atField', 'followsField', 'shareField']
    return ['atField']

  def partTitle(self, ) -> str:
    """The 'partTitle' method names the part shown."""
    part = self.part
    if part is None:
      return 'Nothing selected'
    kind, index = part
    names = {
      'support'   : 'Support %d', 'actuator': 'Actuator A%d',
      'transducer': 'Transducer T%d', 'gap': 'Gap %d in the stirrups'
    }
    return names[kind] % (index + 1)

  def partWords(self, ) -> str:
    """The 'partWords' method says what the part shown does, or how to
    show one."""
    part, rig = self.part, self.rig
    if part is None:
      return ('Click a support, an actuator, a transducer or a gap in '
              'the stirrups to set it here.')
    kind, index = part
    if kind == 'actuator' and index == rig.driven:
      return ('The control drives it: it moves as the control says, '
              'pushing as hard as that takes.')
    if kind == 'actuator':
      return 'It pushes its share of the force of the one it follows.'
    if kind == 'transducer' and index == rig.control.transducer:
      return 'The control reads it.'
    if kind == 'gap':
      return ('The beam has no stirrups here. Drag it along the beam, '
              'or Delete to fill it.')
    return ''

  def words(self, ) -> list[tuple[QRectF, str, bool]]:
    """The 'words' method returns the words painted: each heading and
    each row's name, where it goes, and whether it is a heading."""
    margin = self.__fallback_side_margin__
    width = self.width() - 2 * margin
    labels = self.__fallback_label_width__
    out = [
      (
        QRectF(
          margin, self.transducerField.y() - _HEADING + 4, width,
          _HEADING - 6
          ), 'Control', True
      )
    ]
    for name, label, *_ in _CONTROL_ROWS:
      field = getattr(self, name)
      out.append(
          (
            QRectF(margin, field.y(), labels, field.height()),
            label, False
          )
          )
    top = self._partTop()
    out.append(
        (
          QRectF(margin, top - _HEADING + 4, width, _HEADING - 6),
          self.partTitle(), True
        )
        )
    for name, label, *_ in _PART_ROWS:
      field = getattr(self, name)
      if name in self.partRows():
        out.append(
            (
              QRectF(margin, field.y(), labels, field.height()),
              label, False
            )
            )
    return out

  def partWordsRect(self, ) -> QRectF:
    """The 'partWordsRect' method returns where what the part does is
    said, under its rows and buttons."""
    margin = self.__fallback_side_margin__
    top = self._partTop() + len(self.partRows()) * _ROW
    if self.part is not None and self.part[0] == 'support':
      top += _ROW
    return QRectF(margin, top + 4, self.width() - 2 * margin, 48)

  def noteRect(self, ) -> QRectF:
    """The 'noteRect' method returns where the note goes."""
    margin = self.__fallback_side_margin__
    box = self.partWordsRect()
    return QRectF(margin, box.bottom() + 8, self.width() - 2 * margin, 64)

  def dividerLine(self, ) -> tuple[QPointF, QPointF]:
    """The 'dividerLine' method returns the divider along the right,
    facing the views."""
    right = self.width() - 0.5
    return QPointF(right, 0.0), QPointF(right, float(self.height()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _kindButtons(self, ) -> list[tuple[ToolButton, str]]:
    """The buttons of the kinds of support, each with its kind."""
    return [
      (self.pinButton, 'pin'), (self.rollerButton, 'roller'),
      (self.fixedButton, 'fixed')
    ]

  def _editors(self, ) -> list[QWidget]:
    """Every field and button."""
    names = [row[0] for row in _CONTROL_ROWS + _PART_ROWS]
    buttons = [button for button, _ in self._kindButtons()]
    return [getattr(self, name) for name in names] + buttons

  def _partTop(self, ) -> int:
    """Where the part's first row is."""
    return (self.__fallback_top__ + _HEADING + len(_CONTROL_ROWS) * _ROW
            + _HEADING + 8)

  def _place(self, ) -> None:
    """Places the fields under their headings, beside their names, and
    the buttons of the kinds of support under the part's rows."""
    margin = self.__fallback_side_margin__
    left = margin + self.__fallback_label_width__
    width = max(self.width() - left - margin, 40)
    top = self.__fallback_top__ + _HEADING
    for name, *_ in _CONTROL_ROWS:
      getattr(self, name).setGeometry(left, top, width, _ROW - 4)
      top += _ROW
    top = self._partTop()
    for name in self.partRows():
      getattr(self, name).setGeometry(left, top, width, _ROW - 4)
      top += _ROW
    third = (self.width() - 2 * margin - 12) // 3
    for column, (button, _) in enumerate(self._kindButtons()):
      button.setGeometry(
        margin + column * (third + 6), top, third,
        _ROW - 4
        )

  def _fieldEdited(self, name: str, value: float) -> None:
    """A number taken edits the rig, unless it cannot take it, when the
    panel shows it as it is and says why; under test, it retunes the
    control."""
    if self.stage == 'testing':
      for field, *_, key in _CONTROL_ROWS:
        if field == name:
          self.__panel_note__ = ''
          self.controlTuned.emit(self.rig.control.changed(key, value))
      return
    if name == 'limitField':
      control = self.rig.control.changed('limit', value).towards(0.0)
      return self._takeIf(self.rig.withControl(control))
    if name in ('gapFromField', 'gapToField'):
      return self._gapEdited()
    try:
      rig = self._edited(name, value)
    except (ValueError, IndexError) as exception:
      return self._refuse(exception)
    self._takeIf(rig)

  def _gapEdited(self, ) -> None:
    """The gap shown, from and to where the fields say, unless the beam
    cannot take it, when the panel says why."""
    beam, (_, index) = self.beam, self.part
    try:
      stirrups = beam.stirrups.withGapAt(index, self.gapFromField.value,
                                         self.gapToField.value)
      edited = beam.withStirrups(stirrups)
    except ValueError as exception:
      return self._refuse(exception)
    self.__panel_note__ = ''
    self.showRig(edited, self.rig, self.part)
    self.beamEdited.emit(edited)

  def _takeIf(self, rig: Rig) -> None:
    """Takes 'rig' if it fits the beam, else says why not."""
    try:
      rig.check(self.beam)
    except ValueError as exception:
      return self._refuse(exception)
    self._take(rig)

  def _setKind(self, kind: str) -> None:
    """A button of a kind of support makes the support shown that
    kind."""
    part, rig = self.part, self.rig
    if part is None or part[0] != 'support':
      return
    supports = [*rig.supports]
    supports[part[1]] = Support(supports[part[1]].at, kind)
    try:
      edited = rig.withSupports(*supports)
      edited.check(self.beam)
    except ValueError as exception:
      return self._refuse(exception)
    self._take(edited)

  def _refuse(self, exception: Exception) -> None:
    """Shows the rig as it is, the note saying why it is."""
    words = str(exception)
    self.__panel_note__ = '%s%s.' % (words[:1].upper(), words[1:])
    self.showRig(self.beam, self.rig, self.part)

  def _take(self, rig: Rig) -> None:
    """Shows 'rig' and emits it."""
    self.__panel_note__ = ''
    self.showRig(self.beam, rig, self.part)
    self.rigEdited.emit(rig)

  def _edited(self, name: str, value: float) -> Rig:
    """The rig with the number 'value' taken in the field 'name'."""
    rig = self.rig
    control = rig.control
    if name == 'actuatorField':
      return rig.driving(int(value) - 1)
    if name == 'transducerField':
      index = int(value) - 1
      if not 0 <= index < len(rig.transducers):
        raise ValueError('there is no transducer T%d' % (index + 1))
      return rig.withControl(control.changed('transducer', index))
    for field, *_, key in _CONTROL_ROWS:
      if field == name:
        return rig.withControl(control.changed(key, value))
    _, index = self.part
    if name == 'atField':
      return BeamView.movedTo(rig, self.part, value)
    actuators = [*rig.actuators]
    old = actuators[index]
    if name == 'followsField':
      actuators[index] = Actuator(old.at, int(value) - 1, old.share)
    else:
      actuators[index] = Actuator(old.at, old.follows, value)
    return rig.withActuators(*actuators)
