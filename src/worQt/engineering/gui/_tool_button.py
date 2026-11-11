"""
ToolButton subclasses 'PaintedWidget' and is a button saying what it
does.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from ...paint_ops import PaintBoxModel
from ...utils import WFont, Color
from ...utils.font_nums import GenericFamilyNum, FontWeightNum
from ...utils.geom import InSets, Size
from ...widgets import PaintedWidget
from ._paint_field import PaintFieldBox, PaintButtonText

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QMouseEvent
  from PySide6.QtCore import QEvent


class ToolButton(PaintedWidget):
  """
  ToolButton subclasses 'PaintedWidget' and is a button saying what it
  does in its 'text'. A click on it emits 'clicked', unless it is
  disabled, when it is drawn dim. It lights up under the mouse and
  darkens while pressed; a 'checked' button is drawn with an accented
  frame, as the chosen one of a few. It takes no focus: a click on it is
  for doing, and the keyboard stays where it was.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(43, 45, 49)
  __fallback_face_color__ = Color(52, 55, 60)
  __fallback_hover_face_color__ = Color(66, 70, 77)
  __fallback_pressed_face_color__ = Color(35, 36, 40)
  __fallback_frame_color__ = Color(70, 74, 80)
  __fallback_checked_frame_color__ = Color(229, 192, 123)
  __fallback_ink_color__ = Color(212, 212, 212)
  __fallback_dim_ink_color__ = Color(100, 104, 112)

  #  Private Variables
  __button_text__: str | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  boxOp = PaintFieldBox()
  textOp = PaintButtonText()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(212, 212, 212),
  )
  checked = AttriBox[bool](False)
  hovered = AttriBox[bool](False)
  pressed = AttriBox[bool](False)

  #  Virtual Variables
  text: Field[str] = Field()
  faceColor: Field[Color] = Field()
  frameColor: Field[Color] = Field()
  inkColor: Field[Color] = Field()

  #  Signals
  clicked = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.GET
  def _getText(self, ) -> str:
    """The 'text' getter returns what the button says it does."""
    return '' if self.__button_text__ is None else self.__button_text__

  @faceColor.GET
  def _getFaceColor(self, ) -> Color:
    """The face darkens while pressed and lights up under the mouse."""
    if self.isEnabled() and self.pressed:
      return self.__fallback_pressed_face_color__
    if self.isEnabled() and self.hovered:
      return self.__fallback_hover_face_color__
    return self.__fallback_face_color__

  @frameColor.GET
  def _getFrameColor(self, ) -> Color:
    if self.checked:
      return self.__fallback_checked_frame_color__
    return self.__fallback_frame_color__

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

  @text.SET
  def _setText(self, text: str) -> None:
    if not isinstance(text, str):
      raise TypeException('text', text, str)
    self.__button_text__ = text
    self.updateGeometry()
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    metrics = self.font.metrics
    width = metrics.horizontalAdvance(self.text) + 28
    return QSize(width, metrics.height() + 14)

  def minimumSizeHint(self, ) -> QSize:
    return self.sizeHint()

  def enterEvent(self, event: QEvent) -> None:
    self.hovered = True
    self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.hovered, self.pressed = False, False
    self.update()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    if event.button() != Qt.MouseButton.LeftButton:
      return event.ignore()
    self.pressed = True
    self.update()
    event.accept()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """A press let go on the button is a click."""
    if not self.pressed:
      return event.ignore()
    self.pressed = False
    self.update()
    if self.rect().contains(event.position().toPoint()):
      self.clicked.emit()
    event.accept()

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
    self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.setCursor(Qt.CursorShape.PointingHandCursor)
