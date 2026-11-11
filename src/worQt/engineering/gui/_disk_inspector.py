"""
DiskInspector subclasses 'PaintedWidget' and shows what is selected on a
'DiskWidget' as plain numbers to type over.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ...paint_ops import PaintBoxModel
from ...utils import WFont, Color
from ...utils.font_nums import GenericFamilyNum, FontWeightNum
from ...utils.geom import InSets, Size
from ...widgets import PaintedWidget
from .. import Disk, Support, Load, Rebar
from . import GripNum, DiskGrip, NumberField, ToolButton
from ._paint_panel import PaintPanel, PaintInspector

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent

_NONE = 1e9  # beyond any number a row would hold


class DiskInspector(PaintedWidget):
  """
  DiskInspector subclasses 'PaintedWidget' and shows what is selected on
  a 'DiskWidget' as plain numbers to type over, each row named and its
  unit beside it:

  - the disk: its length, height and thickness, in metres, and its
    materials fc, fy and E, in MPa;
  - a support: the edge it is on, the stretch from and to, and the
    buttons 'Roller' and 'Pin', the one it is checked, and 'Remove
    support';
  - a load: the edge it is on, the stretch from and to, its force Fx and
    Fy in kN, the force per metre below them, and 'Remove load';
  - reinforcement: the count of bars, their diameter in mm and where
    they start and end, their area and the force they yield at below
    them, and 'Remove reinforcement'.

  Each row keeps to what the disk allows: no side less than four
  thicknesses, no support over its neighbours. 'inspect' shows a disk
  and what is selected on it. Every number taken, and 'Roller' and
  'Pin', emit 'edited' with the disk edited so; 'Remove' emits
  'removeRequested'.
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
  __fallback_title_color__ = Color(212, 212, 212)
  __fallback_word_color__ = Color(140, 144, 152)
  __fallback_panel_width__ = 280
  __fallback_side_margin__ = 16
  __fallback_label_width__ = 84
  __fallback_row_height__ = 40
  __fallback_rows_top__ = 68

  #  Private Variables
  __inspected_part__: tuple[Disk, DiskGrip] | None = None
  __row_names__: tuple[str, ...] | None = None
  __panel_note__: str | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  wordsOp = PaintInspector()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(140, 144, 152),
  )
  titleFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      13,
      Color(212, 212, 212),
  )
  firstField = AttriBox[NumberField](THIS)
  secondField = AttriBox[NumberField](THIS)
  thirdField = AttriBox[NumberField](THIS)
  fourthField = AttriBox[NumberField](THIS)
  fifthField = AttriBox[NumberField](THIS)
  sixthField = AttriBox[NumberField](THIS)
  rollerButton = AttriBox[ToolButton](THIS)
  pinButton = AttriBox[ToolButton](THIS)
  removeButton = AttriBox[ToolButton](THIS)

  #  Virtual Variables
  fields: Field[tuple[NumberField, ...]] = Field()
  rowNames: Field[tuple[str, ...]] = Field()
  title: Field[str] = Field()
  subtitle: Field[str] = Field()
  note: Field[str] = Field()
  margin: Field[int] = Field()
  labelWidth: Field[int] = Field()
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()
  titleColor: Field[Color] = Field()
  wordColor: Field[Color] = Field()

  #  Signals
  edited = Signal(object)
  removeRequested = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _allFields(self, ) -> tuple[NumberField, ...]:
    return (
      self.firstField, self.secondField, self.thirdField,
      self.fourthField, self.fifthField, self.sixthField
    )

  @fields.GET
  def _getFields(self, ) -> tuple[NumberField, ...]:
    """The 'fields' getter returns the fields shown, one a row."""
    return self._allFields()[:len(self.rowNames)]

  @rowNames.GET
  def _getRowNames(self, ) -> tuple[str, ...]:
    """The 'rowNames' getter returns the names of the rows shown."""
    return () if self.__row_names__ is None else self.__row_names__

  @title.GET
  def _getTitle(self, ) -> str:
    """The 'title' getter returns what is shown: 'Disk', 'Support' or
    'Load'."""
    grip = self._grip()
    if grip is None:
      return ''
    titles = {
      GripNum.SUPPORT: 'Support', GripNum.LOAD: 'Load',
      GripNum.REBAR  : 'Reinforcement'
    }
    return titles.get(grip.kind, 'Disk')

  @subtitle.GET
  def _getSubtitle(self, ) -> str:
    """The 'subtitle' getter returns which edge a support or a load is
    on."""
    grip = self._grip()
    if grip is None or grip.edge is None:
      return ''
    return 'on the %s edge' % grip.edge.value

  @note.GET
  def _getNote(self, ) -> str:
    """The 'note' getter returns what is said below the rows: a load's
    force per metre."""
    return '' if self.__panel_note__ is None else self.__panel_note__

  @margin.GET
  def _getMargin(self, ) -> int:
    return self.__fallback_side_margin__

  @labelWidth.GET
  def _getLabelWidth(self, ) -> int:
    return self.__fallback_label_width__

  @panelColor.GET
  def _getPanelColor(self, ) -> Color:
    return self.__fallback_panel_color__

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  @titleColor.GET
  def _getTitleColor(self, ) -> Color:
    return self.__fallback_title_color__

  @wordColor.GET
  def _getWordColor(self, ) -> Color:
    return self.__fallback_word_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  def _grip(self, ) -> DiskGrip | None:
    part = self.__inspected_part__
    return None if part is None else part[1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 480)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 320)

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
    for row, field in enumerate(self._allFields()):
      field.valueEdited.connect(partial(self._fieldEdited, row))
      field.hide()
    self.rollerButton.text, self.pinButton.text = 'Roller', 'Pin'
    self.rollerButton.clicked.connect(partial(self._turn, False))
    self.pinButton.clicked.connect(partial(self._turn, True))
    self.removeButton.clicked.connect(self.removeRequested.emit)
    for button in (self.rollerButton, self.pinButton, self.removeButton):
      button.hide()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def inspect(self, disk: Disk, grip: DiskGrip) -> None:
    """The 'inspect' method shows 'disk', and the part of it 'grip'
    selects."""
    self.__inspected_part__ = (disk, grip)
    self.__panel_note__ = None
    if grip.kind is GripNum.SUPPORT:
      self._showSupport(disk, grip.index)
    elif grip.kind is GripNum.LOAD:
      self._showLoad(disk, grip.index)
    elif grip.kind is GripNum.REBAR:
      self._showRebar(disk, grip.index)
    else:
      self._showDisk(disk)
    self._place()
    self.update()

  def titleRect(self, ) -> QRectF:
    """The 'titleRect' method returns where the title is."""
    return QRectF(self.margin, 12.0, self.width() - 2 * self.margin, 26.0)

  def subtitleRect(self, ) -> QRectF:
    """The 'subtitleRect' method returns where the edge is named."""
    return QRectF(self.margin, 38.0, self.width() - 2 * self.margin, 20.0)

  def noteRect(self, ) -> QRectF:
    """The 'noteRect' method returns where the note is, below the
    rows."""
    top = self._rowsBottom()
    return QRectF(self.margin, top, self.width() - 2 * self.margin, 24.0)

  def dividerLine(self, ) -> tuple[QPointF, QPointF]:
    """The 'dividerLine' method returns the divider along the side facing
    the drawing."""
    return QPointF(0.5, 0.0), QPointF(0.5, float(self.height()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # \_____________
  #  Rows shown  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _rows(self, *rows: tuple) -> None:
    """Shows one row a tuple of a name, a value, a unit, decimals, a
    step and the least and the most the value may be."""
    self.__row_names__ = tuple(row[0] for row in rows)
    for field, row in zip(self._allFields(), rows):
      name, value, unit, decimals, step, least, most = row
      field.minimum, field.maximum = least, most
      field.unit, field.decimals, field.step = unit, decimals, step
      field.value = value
    for index, field in enumerate(self._allFields()):
      field.setVisible(True if index < len(rows) else False)

  def _showDisk(self, disk: Disk) -> None:
    least, thickest = disk.leastSide, disk.greatestThickness
    self._rows(
        ('Length', disk.length, 'm', 2, 0.05, least, _NONE),
        ('Height', disk.height, 'm', 2, 0.05, least, _NONE),
        ('Thickness', disk.thickness, 'm', 2, 0.01, 0.05, thickest),
        ('fc', disk.fc, 'MPa', 0, 5.0, 1.0, _NONE),
        ('fy', disk.fy, 'MPa', 0, 50.0, 1.0, _NONE),
        ('E', disk.E, 'MPa', 0, 1000.0, 1.0, _NONE),
    )
    self.__panel_note__ = 'ν = %.2f, as 0.7 − fc / 200' % (
        0.7 - disk.fc / 200)
    self._buttons(False, False)

  def _showRebar(self, disk: Disk, index: int) -> None:
    rebar = disk.rebars[index]
    (x1, y1), (x2, y2) = rebar.start, rebar.end
    length, height = disk.length, disk.height
    self._rows(
        ('Bars', rebar.count, '', 0, 1.0, 1.0, 1000.0),
        ('Ø', rebar.diameter, 'mm', 0, 2.0, 1.0, 100.0),
        ('Start x', x1, 'm', 2, 0.01, 0.0, length),
        ('Start y', y1, 'm', 2, 0.01, 0.0, height),
        ('End x', x2, 'm', 2, 0.01, 0.0, length),
        ('End y', y2, 'm', 2, 0.01, 0.0, height),
    )
    force = rebar.area * disk.fy / 1000.0
    self.__panel_note__ = 'As = %.0f mm², As fy = %.0f kN' % (
      rebar.area,
      force
    )
    self.removeButton.text = 'Remove reinforcement'
    self._buttons(False, True)

  def _showSupport(self, disk: Disk, index: int) -> None:
    support = disk.supports[index]
    low, high = disk.supportRoom(index)
    self._rows(
        ('From', support.start, 'm', 2, 0.05, low, support.end - 0.05),
        ('To', support.end, 'm', 2, 0.05, support.start + 0.05, high),
    )
    both = True if support.setsX and support.setsY else False
    self.rollerButton.checked, self.pinButton.checked = not both, both
    self.removeButton.text = 'Remove support'
    self._buttons(True, True)

  def _showLoad(self, disk: Disk, index: int) -> None:
    load = disk.loads[index]
    length = disk.edgeLength(load.edge)
    self._rows(
        ('From', load.start, 'm', 2, 0.05, 0.0, load.end - 0.05),
        ('To', load.end, 'm', 2, 0.05, load.start + 0.05, length),
        ('Fx', load.fx, 'kN', 1, 10.0, -_NONE, _NONE),
        ('Fy', load.fy, 'kN', 1, 10.0, -_NONE, _NONE),
    )
    qx, qy = load.intensity
    self.__panel_note__ = 'q = %.4g kN/m' % math.hypot(qx, qy)
    self.removeButton.text = 'Remove load'
    self._buttons(False, True)

  def _buttons(self, kinds: bool, remove: bool) -> None:
    """Shows the roller and pin buttons, and the remove button."""
    self.rollerButton.setVisible(kinds)
    self.pinButton.setVisible(kinds)
    self.removeButton.setVisible(remove)

  def _rowsBottom(self, ) -> float:
    rows = len(self.rowNames)
    return self.__fallback_rows_top__ + rows * self.__fallback_row_height__

  def _place(self, ) -> None:
    """Places the rows' fields beside their names, and the buttons
    below them."""
    margin, width = self.margin, self.width()
    left = margin + self.labelWidth
    fieldWidth = max(width - left - margin, 40)
    for row, field in enumerate(self._allFields()):
      top = self.__fallback_rows_top__ + row * self.__fallback_row_height__
      field.setGeometry(left, top, fieldWidth, 30)
    top = int(self._rowsBottom() + (28 if self.note else 8))
    half = (width - 2 * margin - 8) // 2
    self.rollerButton.setGeometry(margin, top, half, 30)
    self.pinButton.setGeometry(margin + half + 8, top, half, 30)
    if self.rollerButton.isVisibleTo(self):
      top += 40
    self.removeButton.setGeometry(margin, top, width - 2 * margin, 30)

  # \_________
  #  Edits  ]
  # /¨¨¨¨¨¨¨¨

  def _fieldEdited(self, row: int, value: float) -> None:
    """A number taken in 'row' edits the disk, unless the disk cannot
    take it, when the panel shows the disk as it is."""
    disk, grip = self.__inspected_part__
    try:
      edited = self._edited(disk, grip, row)
    except ValueError:
      return self.inspect(disk, grip)
    self.edited.emit(edited)

  def _edited(self, disk: Disk, grip: DiskGrip, row: int) -> Disk:
    """The disk edited by the numbers shown."""
    values = [field.value for field in self.fields]
    if grip.kind is GripNum.DISK:
      if row < 3:
        return disk.resized(*values[:3])
      return disk.withMaterials(*values[3:])
    edited = Disk(disk)
    if grip.kind is GripNum.REBAR:
      count, diameter, *points = values
      bars = Rebar(*points, int(round(count)), diameter)
      edited.replaceRebar(grip.index, bars)
      return edited
    if grip.kind is GripNum.SUPPORT:
      old = disk.supports[grip.index]
      new = Support(old.edge, values[0], values[1], old.setsX, old.setsY)
      edited.replaceSupport(grip.index, new)
      return edited
    old = disk.loads[grip.index]
    edited.replaceLoad(grip.index, Load(old.edge, *values))
    return edited

  def _turn(self, pin: bool) -> None:
    """Makes the selected support a pin, or a roller holding the disk
    across its edge."""
    disk, grip = self.__inspected_part__
    support = disk.supports[grip.index]
    across = False if support.edge.horizontal else True
    setsX, setsY = (True, True) if pin else (across, not across)
    edited = Disk(disk)
    edited.replaceSupport(
      grip.index, Support(
        support.edge, support.start,
        support.end, setsX, setsY
        )
      )
    self.edited.emit(edited)
