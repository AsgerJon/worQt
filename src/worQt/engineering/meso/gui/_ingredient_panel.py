"""
IngredientPanel subclasses 'PaintedWidget' and is the panel of sliders
setting what the stones, the paste and the bond are.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import QuantitySlider
from .. import PhaseMaterial

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

#  Each slider: its name, its group, its words, least, greatest, unit,
#  decimals and where it starts, as the lattice's own materials are.
_SLIDERS = (
  ('stoneStiffness', 0, 'Stiffness', 20.0, 100.0, 'GPa', 0, 70.0),
  ('stoneTension', 0, 'Strength', 2.0, 20.0, 'MPa', 1, 10.0),
  ('stoneToughness', 0, 'Toughness', 20.0, 300.0, 'N/m', 0, 100.0),
  ('pasteStiffness', 1, 'Stiffness', 5.0, 50.0, 'GPa', 0, 25.0),
  ('pasteTension', 1, 'Strength', 1.0, 10.0, 'MPa', 1, 4.0),
  ('pasteToughness', 1, 'Toughness', 10.0, 200.0, 'N/m', 0, 60.0),
  ('pasteCohesion', 1, 'Cohesion', 1.0, 30.0, 'MPa', 1, 8.0),
  ('pasteFriction', 1, 'Friction', 0.1, 1.2, '', 2, 0.6),
  ('bondTension', 2, 'Strength', 0.5, 6.0, 'MPa', 1, 2.0),
  ('bondToughness', 2, 'Toughness', 5.0, 100.0, 'N/m', 0, 25.0),
)
_HEADINGS = ('Stone', 'Paste', 'Bond')


class PaintIngredients(AbstractPaintOp):
  """
  PaintIngredients subclasses 'AbstractPaintOp' and paints the panel of
  an 'IngredientPanel': its background, its divider and the heading of
  each group of sliders.
  """

  #  Annotations
  widget: IngredientPanel

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the background, the divider on the left
    and the headings."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setPen(widget.dividerColor.solidPen)
    painter.drawLine(0, 0, 0, widget.height())
    painter.setFont(widget.headingFont)
    painter.setPen(widget.headingFont.color.Q)
    for text, place in zip(widget.headings(), widget.headingRects()):
      painter.drawText(place, _LEFT, text)
    return rect


class IngredientPanel(PaintedWidget):
  """
  IngredientPanel subclasses 'PaintedWidget' and is the panel of sliders
  setting what the concrete is made of: the stones' stiffness, strength
  and toughness; the paste's the same, and its cohesion and friction;
  and the bond's strength and toughness, where the paste meets a stone.
  They start at the lattice's own materials. 'materials' are the stone,
  the paste and the bond as the sliders show them: each slider's
  quantity to the decimals it shows; the cohesion of the stone and of the
  bond twice its strength, as the paste's is about; the friction of all
  the paste's; the shear toughness of each ten times its toughness; and
  the bond as stiff as the paste, its stiffness the stone and the paste
  in series. 'materialsChanged' tells of any change; 'setLocked' greys
  them all out, while a test runs.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_divider_color__ = Color(58, 61, 65)
  __fallback_row_height__ = 30  # pixels
  __fallback_heading_height__ = 30  # pixels
  __fallback_label_width__ = 74.0  # pixels: the sliders' names
  __fallback_value_width__ = 70.0  # pixels: the sliders' quantities
  __fallback_panel_width__ = 330  # pixels

  #  Public Variables
  boxModelOp = PaintBoxModel()
  ingredientsOp = PaintIngredients()
  headingFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      11,
      Color(212, 212, 212),
  )
  stoneStiffness = AttriBox[QuantitySlider](THIS)
  stoneTension = AttriBox[QuantitySlider](THIS)
  stoneToughness = AttriBox[QuantitySlider](THIS)
  pasteStiffness = AttriBox[QuantitySlider](THIS)
  pasteTension = AttriBox[QuantitySlider](THIS)
  pasteToughness = AttriBox[QuantitySlider](THIS)
  pasteCohesion = AttriBox[QuantitySlider](THIS)
  pasteFriction = AttriBox[QuantitySlider](THIS)
  bondTension = AttriBox[QuantitySlider](THIS)
  bondToughness = AttriBox[QuantitySlider](THIS)

  #  Virtual Variables
  dividerColor: Field[Color] = Field()

  #  Signals
  materialsChanged = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    rows = len(_SLIDERS) * self.__fallback_row_height__
    rows += len(_HEADINGS) * self.__fallback_heading_height__
    return QSize(self.__fallback_panel_width__, rows + 16)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(260, self.sizeHint().height())

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
    for name, _, words, low, high, unit, decimals, start in _SLIDERS:
      slider = getattr(self, name)
      slider.text = words
      slider.setLabelWidth(self.__fallback_label_width__)
      slider.setValueWidth(self.__fallback_value_width__)
      slider.setScale(low, high, unit, decimals)
      slider.quantity = start
      slider.quantityChanged.connect(self._tellChange)
    self._place()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def headings(self, ) -> tuple[str, ...]:
    """The 'headings' method returns the names of the groups."""
    return _HEADINGS

  def sliders(self, ) -> tuple[QuantitySlider, ...]:
    """The 'sliders' method returns every slider, group by group."""
    return (*[getattr(self, row[0]) for row in _SLIDERS],)

  def headingRects(self, ) -> list[QRectF]:
    """The 'headingRects' method returns where each heading is written:
    above its group."""
    out, top, group = [], 8.0, -1
    for row in _SLIDERS:
      if row[1] != group:
        group = row[1]
        out.append(
          QRectF(
            14.0, top, self.width() - 28.0,
            float(self.__fallback_heading_height__)
            )
          )
        top += self.__fallback_heading_height__
      top += self.__fallback_row_height__
    return out

  def materials(self, ) -> tuple[PhaseMaterial, PhaseMaterial,
  PhaseMaterial]:
    """The 'materials' method returns the stone, the paste and the bond as
    the sliders show them."""
    shown = {row[0]: round(getattr(self, row[0]).quantity, row[6])
             for row in _SLIDERS}
    friction = shown['pasteFriction']
    stone = PhaseMaterial(
        shown['stoneStiffness'] * 1000.0, shown['stoneTension'],
        shown['stoneToughness'] / 1000.0, 2.0 * shown['stoneTension'],
        friction, 10.0 * shown['stoneToughness'] / 1000.0
    )
    paste = PhaseMaterial(
        shown['pasteStiffness'] * 1000.0, shown['pasteTension'],
        shown['pasteToughness'] / 1000.0, shown['pasteCohesion'],
        friction, 10.0 * shown['pasteToughness'] / 1000.0
    )
    bond = PhaseMaterial(
        shown['pasteStiffness'] * 1000.0, shown['bondTension'],
        shown['bondToughness'] / 1000.0, 2.0 * shown['bondTension'],
        friction, 10.0 * shown['bondToughness'] / 1000.0
    )
    return stone, paste, bond

  def setLocked(self, locked: bool) -> None:
    """The 'setLocked' method greys every slider out, or none."""
    for slider in self.sliders():
      slider.setEnabled(False if locked else True)
      slider.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _place(self, ) -> None:
    """Places the sliders under their headings, a row each."""
    top, group = 8, -1
    rows = self.__fallback_row_height__
    for row in _SLIDERS:
      if row[1] != group:
        group = row[1]
        top += self.__fallback_heading_height__
      slider = getattr(self, row[0])
      slider.setGeometry(6, top, self.width() - 12, rows)
      top += rows

  def _tellChange(self, *_) -> None:
    """Tells of a change of a material."""
    self.materialsChanged.emit()
