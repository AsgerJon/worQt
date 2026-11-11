"""
CheckBox subclasses 'PaintedWidget' and is a box ticked or not, with what
it means beside it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from ...paint_ops import PaintBoxModel
from ...utils import WFont, Color
from ...utils.font_nums import GenericFamilyNum, FontWeightNum
from ...utils.geom import InSets, Size
from ...widgets import PaintedWidget
from ._paint_check_box import PaintCheckBox

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QKeyEvent, QMouseEvent
  from PySide6.QtCore import QEvent


class CheckBox(PaintedWidget):
  """
  CheckBox subclasses 'PaintedWidget' and is a box ticked or not, with
  what it means, 'text', beside it. A click or Space ticks it or clears
  it; 'checked' is whether it is ticked, and 'toggled' tells of each
  change. Greyed out, it takes no clicks, and its text is dimmed.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_frame_color__ = Color(110, 114, 122)
  __fallback_hover_frame_color__ = Color(212, 212, 212)
  __fallback_tick_color__ = Color(229, 192, 123)
  __fallback_ink_color__ = Color(212, 212, 212)
  __fallback_dim_ink_color__ = Color(100, 104, 112)
  __fallback_box_size__ = 14.0  # pixels
  __fallback_gap__ = 8.0  # pixels between the box and the text

  #  Private Variables
  __box_checked__: bool = False
  __box_text__: str = ''

  #  Public Variables
  boxModelOp = PaintBoxModel()
  checkOp = PaintCheckBox()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(212, 212, 212),
  )
  hovered = AttriBox[bool](False)

  #  Virtual Variables
  checked: Field[bool] = Field()
  text: Field[str] = Field()
  frameColor: Field[Color] = Field()
  tickColor: Field[Color] = Field()
  inkColor: Field[Color] = Field()

  #  Signals
  toggled = Signal(bool)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @checked.GET
  def _getChecked(self, ) -> bool:
    """The 'checked' getter tells whether the box is ticked."""
    return self.__box_checked__

  @text.GET
  def _getText(self, ) -> str:
    """The 'text' getter returns what the box means."""
    return self.__box_text__

  @frameColor.GET
  def _getFrameColor(self, ) -> Color:
    if self.hovered and self.isEnabled():
      return self.__fallback_hover_frame_color__
    return self.__fallback_frame_color__

  @tickColor.GET
  def _getTickColor(self, ) -> Color:
    return self.__fallback_tick_color__

  @inkColor.GET
  def _getInkColor(self, ) -> Color:
    if self.isEnabled():
      return self.__fallback_ink_color__
    return self.__fallback_dim_ink_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @checked.SET
  def _setChecked(self, checked: bool) -> None:
    """The 'checked' setter ticks or clears the box, telling of it if it
    changed."""
    checked = True if checked else False
    if checked == self.__box_checked__:
      return
    self.__box_checked__ = checked
    self.update()
    self.toggled.emit(checked)

  @text.SET
  def _setText(self, text: str) -> None:
    """The 'text' setter says what the box means."""
    if not isinstance(text, str):
      raise TypeException('text', text, str)
    self.__box_text__ = text
    self.updateGeometry()
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    metrics = self.font.metrics
    width = self.__fallback_box_size__ + self.__fallback_gap__
    width += metrics.horizontalAdvance(self.text) + 8
    return QSize(round(width), metrics.height() + 14)

  def minimumSizeHint(self, ) -> QSize:
    return self.sizeHint()

  def enterEvent(self, event: QEvent) -> None:
    self.hovered = True
    self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.hovered = False
    self.update()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A press is taken, so the release is the box's."""
    if event.button() != Qt.MouseButton.LeftButton:
      return event.ignore()
    event.accept()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """A click on the box ticks it or clears it."""
    if event.button() != Qt.MouseButton.LeftButton:
      return event.ignore()
    if self.rect().contains(event.position().toPoint()):
      self.checked = not self.checked
    event.accept()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Space ticks the box or clears it."""
    if event.key() != Qt.Key.Key_Space:
      return PaintedWidget.keyPressEvent(self, event)
    self.checked = not self.checked
    event.accept()

  def changeEvent(self, event: QEvent) -> None:
    """Greying out redraws the box dimmed."""
    PaintedWidget.changeEvent(self, event)
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
    self.setCursor(Qt.CursorShape.PointingHandCursor)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def boxRect(self, ) -> QRectF:
    """The 'boxRect' method returns where the box is drawn."""
    size = self.__fallback_box_size__
    return QRectF(4.0, (self.height() - size) / 2, size, size)

  def textRect(self, ) -> QRectF:
    """The 'textRect' method returns where the text is written."""
    left = self.boxRect().right() + self.__fallback_gap__
    return QRectF(left, 0.0, self.width() - left, float(self.height()))
