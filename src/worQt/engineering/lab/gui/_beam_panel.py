"""
BeamPanel subclasses 'PaintedWidget' and shows the beam as numbers to
type over.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import NumberField
from ...gui._paint_panel import PaintPanel
from .. import BarLayer, RCBeam, Stirrups

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap
#  Each heading over its rows: the field, its name, unit, decimals, step,
#  least and greatest
_ROWS = (
  (
    'Beam', (
    ('lengthField', 'Length', 'mm', 0, 100, 1000, 12000),
    ('heightField', 'Height', 'mm', 0, 10, 100, 1200),
    ('widthField', 'Width', 'mm', 0, 10, 80, 1000),
  )
  ),
  (
    'Concrete', (
    ('fcmField', 'fcm', 'MPa', 1, 1, 12, 100),
  )
  ),
  (
    'Bars', (
    ('fyField', 'fy', 'MPa', 0, 10, 200, 2000),
    ('esField', 'Es', 'MPa', 0, 1000, 100000, 250000),
  )
  ),
  (
    'Bottom bars', (
    ('bottomCountField', 'Count', '', 0, 1, 0, 12),
    ('bottomDiameterField', 'Ø', 'mm', 0, 2, 4, 40),
    ('bottomCoverField', 'Cover', 'mm', 0, 5, 10, 100),
  )
  ),
  (
    'Top bars', (
    ('topCountField', 'Count', '', 0, 1, 0, 12),
    ('topDiameterField', 'Ø', 'mm', 0, 2, 4, 40),
    ('topCoverField', 'Cover', 'mm', 0, 5, 10, 100),
  )
  ),
  (
    'Stirrups', (
    ('stirrupDiameterField', 'Ø', 'mm', 0, 2, 0, 20),
    ('stirrupSpacingField', 'Spacing', 'mm', 0, 10, 50, 1000),
  )
  ),
)
_HEADING = 28  # pixels a heading takes
_ROW = 32  # pixels a row takes


class PaintBeamPanel(AbstractPaintOp):
  """
  PaintBeamPanel subclasses 'AbstractPaintOp' and paints the words of a
  'BeamPanel': each heading, the name of each row beside its field, and
  the note under them.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the words of the panel."""
    widget = self.widget
    for box, text, heading in widget.words():
      font = widget.headingFont if heading else widget.font
      painter.setFont(font)
      painter.setPen(font.color.Q)
      painter.drawText(box, _LEFT, text)
    self._paintSection(painter)
    note = widget.note
    if note:
      painter.setFont(widget.font)
      painter.setPen(widget.noteColor.Q)
      painter.drawText(widget.noteRect(), _WRAP, note)
    return rect

  def _paintSection(self, painter: WPainter) -> None:
    """The beam's section to scale, with its bars, and what it is."""
    widget = self.widget
    beam = widget.beam
    room = widget.sectionRect()
    scale = min(
      room.height() / beam.height,
      room.width() * 0.4 / beam.width
      )
    left, top = room.left(), room.top()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(widget.edgeColor.Q, 1.0))
    painter.setBrush(widget.concreteColor.fillBrush)
    painter.drawRect(
      QRectF(
        left, top, beam.width * scale,
        beam.height * scale
        )
      )
    painter.setPen(self.emptyPen)
    painter.setBrush(widget.steelColor.fillBrush)
    for layer, depth in (
        (beam.bottom, beam.height - beam.bottom.depth),
        (beam.top, beam.top.depth)
    ):
      reach = beam.width / 2 - layer.cover - layer.diameter / 2
      for index in range(layer.count):
        share = 0.5 if layer.count == 1 else index / (layer.count - 1)
        x = beam.width / 2 - reach + 2 * reach * share
        radius = max(layer.diameter / 2 * scale, 1.5)
        painter.drawEllipse(
          QPointF(left + x * scale, top + depth * scale),
          radius, radius
          )
    painter.setBrush(self.emptyBrush)
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    text = QRectF(
      left + beam.width * scale + 12, top,
      room.right() - left - beam.width * scale - 12,
      room.height()
      )
    painter.drawText(text, _WRAP, '\n'.join(widget.sectionWords()))


class BeamPanel(PaintedWidget):
  """
  BeamPanel subclasses 'PaintedWidget' and shows the beam as numbers to
  type over, under headings: its length, height and width; its
  concrete's strength; its bars' yield strength and modulus; and the
  bottom and the top bars, each their count, diameter and cover; and
  its stirrups, their diameter, nought for none, and spacing, the gaps
  left without them made in the view. Under them, its section is drawn
  to scale with its bars, and said.

  'showBeam' shows a beam. Each number taken emits 'edited' with the
  beam so; a number the beam cannot take is given up, and the note
  under the rows says why. 'setLocked' locks the numbers while a test
  is on, the note saying so.
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
  __fallback_concrete_color__ = Color(120, 122, 126)
  __fallback_edge_color__ = Color(170, 172, 176)
  __fallback_steel_color__ = Color(86, 156, 214)
  __fallback_panel_width__ = 270
  __fallback_side_margin__ = 16
  __fallback_label_width__ = 104
  __fallback_top__ = 10
  __fallback_locked_note__ = ('The beam is tested as it is. New beam '
                              'casts it afresh, to change it.')

  #  Private Variables
  __shown_beam__: RCBeam | None = None
  __panel_note__: str = ''

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  wordsOp = PaintBeamPanel()
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
  lengthField = AttriBox[NumberField](THIS)
  heightField = AttriBox[NumberField](THIS)
  widthField = AttriBox[NumberField](THIS)
  fcmField = AttriBox[NumberField](THIS)
  fyField = AttriBox[NumberField](THIS)
  esField = AttriBox[NumberField](THIS)
  bottomCountField = AttriBox[NumberField](THIS)
  bottomDiameterField = AttriBox[NumberField](THIS)
  bottomCoverField = AttriBox[NumberField](THIS)
  topCountField = AttriBox[NumberField](THIS)
  topDiameterField = AttriBox[NumberField](THIS)
  topCoverField = AttriBox[NumberField](THIS)
  stirrupDiameterField = AttriBox[NumberField](THIS)
  stirrupSpacingField = AttriBox[NumberField](THIS)

  #  Virtual Variables
  beam: Field[RCBeam] = Field()
  note: Field[str] = Field()
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()
  noteColor: Field[Color] = Field()
  concreteColor: Field[Color] = Field()
  edgeColor: Field[Color] = Field()
  steelColor: Field[Color] = Field()

  #  Signals
  edited = Signal(object)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @beam.GET
  def _getBeam(self, ) -> RCBeam:
    """The 'beam' getter returns the beam shown, the standard one until
    another is shown."""
    if self.__shown_beam__ is None:
      self.__shown_beam__ = RCBeam()
    return self.__shown_beam__

  @note.GET
  def _getNote(self, ) -> str:
    """The 'note' getter returns what the note under the rows says."""
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

  @concreteColor.GET
  def _getConcreteColor(self, ) -> Color:
    return self.__fallback_concrete_color__

  @edgeColor.GET
  def _getEdgeColor(self, ) -> Color:
    return self.__fallback_edge_color__

  @steelColor.GET
  def _getSteelColor(self, ) -> Color:
    return self.__fallback_steel_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 720)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 560)

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
    for _, rows in _ROWS:
      for name, _, unit, decimals, step, least, most in rows:
        field = getattr(self, name)
        field.unit = unit
        field.decimals = decimals
        field.step = step
        field.minimum = least
        field.maximum = most
        field.valueEdited.connect(partial(self._fieldEdited, name))
    self.showBeam(self.beam)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showBeam(self, beam: RCBeam) -> None:
    """The 'showBeam' method shows 'beam'."""
    self.__shown_beam__ = beam
    values = {
      'lengthField'        : beam.length, 'heightField': beam.height,
      'widthField'         : beam.width, 'fcmField': beam.fcm,
      'fyField'            : beam.fy, 'esField': beam.Es,
      'bottomCountField'   : beam.bottom.count,
      'bottomDiameterField': beam.bottom.diameter,
      'bottomCoverField'   : beam.bottom.cover,
      'topCountField'      : beam.top.count,
      'topDiameterField'   : beam.top.diameter,
      'topCoverField'      : beam.top.cover,
      'stirrupDiameterField': beam.stirrups.diameter,
      'stirrupSpacingField': beam.stirrups.spacing,
    }
    for name, value in values.items():
      getattr(self, name).value = value
    self._place()
    self.update()

  def setLocked(self, locked: bool) -> None:
    """The 'setLocked' method locks the numbers while a test is on, the
    note saying so, or frees them."""
    for name in self._names():
      getattr(self, name).setEnabled(not locked)
    if locked:
      self.__panel_note__ = self.__fallback_locked_note__
    elif self.__panel_note__ == self.__fallback_locked_note__:
      self.__panel_note__ = ''
    self.update()

  def words(self, ) -> list[tuple[QRectF, str, bool]]:
    """The 'words' method returns the words painted: each heading and
    each row's name, where it goes, and whether it is a heading."""
    margin = self.__fallback_side_margin__
    width = self.width() - 2 * margin
    out = []
    for heading, rows in _ROWS:
      first = getattr(self, rows[0][0])
      out.append(
          (
            QRectF(
              margin, first.y() - _HEADING + 4, width,
              _HEADING - 6
              ), heading, True
          )
          )
      for name, label, *_ in rows:
        field = getattr(self, name)
        out.append(
            (
              QRectF(
                margin, field.y(),
                self.__fallback_label_width__,
                field.height()
                ), label, False
            )
            )
    return out

  def sectionRect(self, ) -> QRectF:
    """The 'sectionRect' method returns where the section is drawn,
    under the rows."""
    margin = self.__fallback_side_margin__
    top = self._rowsBottom() + 18
    return QRectF(margin, top, self.width() - 2 * margin, 110)

  def sectionWords(self, ) -> list[str]:
    """The 'sectionWords' method says what the section is: its size,
    its bars, and the bottom bars' area and share of the section to
    their depth."""
    beam = self.beam
    depth = beam.height - beam.bottom.depth
    ratio = 100 * beam.bottom.area / (beam.width * depth)
    return [
      '%g × %g mm' % (beam.height, beam.width),
      'bottom %s' % (beam.bottom,), 'top %s' % (beam.top,),
      'stirrups %s' % (beam.stirrups,),
      'As %.0f mm², ρ %.2f %%' % (beam.bottom.area, ratio)
    ]

  def noteRect(self, ) -> QRectF:
    """The 'noteRect' method returns where the note goes, under the
    section."""
    margin = self.__fallback_side_margin__
    top = self.sectionRect().bottom() + 12
    return QRectF(margin, top, self.width() - 2 * margin, 60)

  def dividerLine(self, ) -> tuple[QPointF, QPointF]:
    """The 'dividerLine' method returns the divider along the left,
    facing the views."""
    return QPointF(0.5, 0.0), QPointF(0.5, float(self.height()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _names() -> list[str]:
    """The fields, in order."""
    return [row[0] for _, rows in _ROWS for row in rows]

  def _place(self, ) -> None:
    """Places the fields under their headings, beside their names."""
    margin = self.__fallback_side_margin__
    left = margin + self.__fallback_label_width__
    width = max(self.width() - left - margin, 40)
    top = self.__fallback_top__
    for _, rows in _ROWS:
      top += _HEADING
      for name, *_ in rows:
        getattr(self, name).setGeometry(left, top, width, _ROW - 4)
        top += _ROW

  def _rowsBottom(self, ) -> float:
    """Where the last row ends."""
    last = getattr(self, self._names()[-1])
    return float(last.y() + last.height())

  def _fieldEdited(self, name: str, value: float) -> None:
    """A number taken edits the beam, unless it cannot take it, when the
    panel shows it as it is and says why."""
    try:
      beam = self._edited()
    except ValueError as exception:
      words = str(exception)
      self.__panel_note__ = '%s%s.' % (words[:1].upper(), words[1:])
      self.showBeam(self.beam)
      return
    self.__panel_note__ = ''
    self.showBeam(beam)
    self.edited.emit(beam)

  def _edited(self, ) -> RCBeam:
    """The beam as the fields have it."""
    bottom = BarLayer(
      int(self.bottomCountField.value),
      self.bottomDiameterField.value,
      self.bottomCoverField.value
      )
    top = BarLayer(
      int(self.topCountField.value),
      self.topDiameterField.value, self.topCoverField.value
      )
    stirrups = Stirrups(self.stirrupDiameterField.value,
                        self.stirrupSpacingField.value,
                        self.beam.stirrups.gaps)
    return RCBeam(
      self.lengthField.value, self.heightField.value,
      self.widthField.value, self.fcmField.value,
      self.fyField.value, self.esField.value, bottom, top, stirrups
      )
