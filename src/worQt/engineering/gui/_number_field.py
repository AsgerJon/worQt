"""
NumberField subclasses 'PaintedWidget' and holds one number with its
unit, the way a form field does.
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
from ._paint_field import PaintFieldBox, PaintFieldNumber

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QFocusEvent, QKeyEvent, QMouseEvent
  from PySide6.QtCore import QEvent

_KEY = Qt.Key
_TYPED = '0123456789.,-+eE'  # what may be typed into a number


class NumberField(PaintedWidget):
  """
  NumberField subclasses 'PaintedWidget' and holds one number with its
  unit, the way a form field does. It shows its 'value' to its
  'decimals', the 'unit' beside it. A click on it, or a key, starts a
  new number, which the first key typed replaces the old with; Enter, or
  leaving the field, takes the number typed, and Escape gives it up. The
  up and down arrow keys step the number by 'step'. A number beyond
  'minimum' and 'maximum' is taken as the nearest it may be, and what is
  no number is given up. 'valueEdited' tells of every number taken that
  differs from the one shown; setting 'value' tells of nothing.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(43, 45, 49)
  __fallback_face_color__ = Color(30, 31, 34)
  __fallback_frame_color__ = Color(70, 74, 80)
  __fallback_hover_frame_color__ = Color(110, 115, 125)
  __fallback_focus_frame_color__ = Color(229, 192, 123)
  __fallback_ink_color__ = Color(212, 212, 212)
  __fallback_unit_color__ = Color(140, 144, 152)
  __fallback_mark_color__ = Color(61, 111, 180)

  #  Private Variables
  __field_value__: float | None = None
  __field_unit__: str | None = None
  __field_limits__: tuple[float, float] | None = None
  __field_step__: float | None = None
  __field_decimals__: int | None = None
  __edit_text__: str | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  boxOp = PaintFieldBox()
  numberOp = PaintFieldNumber()
  font = AttriBox[WFont](
      GenericFamilyNum.MONO,
      FontWeightNum.NORMAL,
      11,
      Color(212, 212, 212),
  )
  replaceNext = AttriBox[bool](False)
  hovered = AttriBox[bool](False)

  #  Virtual Variables
  value: Field[float] = Field()
  unit: Field[str] = Field()
  minimum: Field[float] = Field()
  maximum: Field[float] = Field()
  step: Field[float] = Field()
  decimals: Field[int] = Field()
  editText: Field[str] = Field()
  shownText: Field[str] = Field()
  faceColor: Field[Color] = Field()
  frameColor: Field[Color] = Field()
  inkColor: Field[Color] = Field()
  unitColor: Field[Color] = Field()
  markColor: Field[Color] = Field()

  #  Signals
  valueEdited = Signal(float)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @value.GET
  def _getValue(self, ) -> float:
    """The 'value' getter returns the number shown."""
    return 0.0 if self.__field_value__ is None else self.__field_value__

  @unit.GET
  def _getUnit(self, ) -> str:
    """The 'unit' getter returns the unit shown beside the number."""
    return '' if self.__field_unit__ is None else self.__field_unit__

  def _getLimits(self, ) -> tuple[float, float]:
    if self.__field_limits__ is None:
      return float('-inf'), float('inf')
    return self.__field_limits__

  @minimum.GET
  def _getMinimum(self, ) -> float:
    """The 'minimum' getter returns the least number taken."""
    return self._getLimits()[0]

  @maximum.GET
  def _getMaximum(self, ) -> float:
    """The 'maximum' getter returns the greatest number taken."""
    return self._getLimits()[1]

  @step.GET
  def _getStep(self, ) -> float:
    """The 'step' getter returns how far an arrow key steps."""
    return 1.0 if self.__field_step__ is None else self.__field_step__

  @decimals.GET
  def _getDecimals(self, ) -> int:
    """The 'decimals' getter returns how many decimals are shown."""
    return 2 if self.__field_decimals__ is None else self.__field_decimals__

  @editText.GET
  def _getEditText(self, ) -> str | None:
    """The 'editText' getter returns what is typed, or 'None' while
    nothing is."""
    return self.__edit_text__

  @shownText.GET
  def _getShownText(self, ) -> str:
    """The 'shownText' getter returns what the field shows: what is
    typed, else the number to its decimals."""
    if self.__edit_text__ is not None:
      return self.__edit_text__
    return '%.*f' % (self.decimals, self.value)

  @faceColor.GET
  def _getFaceColor(self, ) -> Color:
    return self.__fallback_face_color__

  @frameColor.GET
  def _getFrameColor(self, ) -> Color:
    """The frame is accented while a number is typed, lighter on
    hover."""
    if self.__edit_text__ is not None:
      return self.__fallback_focus_frame_color__
    if self.hovered:
      return self.__fallback_hover_frame_color__
    return self.__fallback_frame_color__

  @inkColor.GET
  def _getInkColor(self, ) -> Color:
    return self.__fallback_ink_color__

  @unitColor.GET
  def _getUnitColor(self, ) -> Color:
    return self.__fallback_unit_color__

  @markColor.GET
  def _getMarkColor(self, ) -> Color:
    return self.__fallback_mark_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @value.SET
  def _setValue(self, value: float) -> None:
    """The 'value' setter shows 'value', giving up what is typed, and
    tells of nothing."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
      raise TypeException('value', value, float)
    self.__field_value__ = float(value)
    self.__edit_text__ = None
    self.update()

  @unit.SET
  def _setUnit(self, unit: str) -> None:
    if not isinstance(unit, str):
      raise TypeException('unit', unit, str)
    self.__field_unit__ = unit
    self.update()

  @minimum.SET
  def _setMinimum(self, minimum: float) -> None:
    self.__field_limits__ = (float(minimum), self.maximum)

  @maximum.SET
  def _setMaximum(self, maximum: float) -> None:
    self.__field_limits__ = (self.minimum, float(maximum))

  @step.SET
  def _setStep(self, step: float) -> None:
    self.__field_step__ = float(step)

  @decimals.SET
  def _setDecimals(self, decimals: int) -> None:
    self.__field_decimals__ = int(decimals)
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(130, self.font.metrics.height() + 14)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(80, self.sizeHint().height())

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A click starts a new number."""
    self.setFocus()
    self._begin()
    event.accept()

  def focusInEvent(self, event: QFocusEvent) -> None:
    self._begin()
    PaintedWidget.focusInEvent(self, event)

  def focusOutEvent(self, event: QFocusEvent) -> None:
    """Leaving the field takes what was typed."""
    self.commit()
    PaintedWidget.focusOutEvent(self, event)

  def enterEvent(self, event: QEvent) -> None:
    self.hovered = True
    self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.hovered = False
    self.update()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Keys type a number, take it, give it up or step it."""
    key, text = event.key(), event.text()
    if key in (_KEY.Key_Return, _KEY.Key_Enter):
      self.commit()
    elif key == _KEY.Key_Escape:
      self.revert()
    elif key in (_KEY.Key_Up, _KEY.Key_Down):
      self.commit()
      self._stepBy(1 if key == _KEY.Key_Up else -1)
    elif key == _KEY.Key_Backspace:
      self._type(None)
    elif text and all(char in _TYPED for char in text):
      self._type(text)
    else:
      return PaintedWidget.keyPressEvent(self, event)
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
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def commit(self, ) -> None:
    """The 'commit' method takes what is typed, kept between the limits,
    and tells of it if it differs from the number shown; what is no
    number is given up."""
    text = self.__edit_text__
    if text is None:
      return
    self.__edit_text__ = None
    try:
      number = float(str.replace(text, ',', '.'))
    except ValueError:
      return self.update()
    self._take(number)

  def revert(self, ) -> None:
    """The 'revert' method gives up what is typed."""
    self.__edit_text__ = None
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _begin(self, ) -> None:
    """Starts a new number, which the next key replaces the old with."""
    if self.__edit_text__ is None:
      self.__edit_text__ = self.shownText
      self.replaceNext = True
      self.update()

  def _type(self, text: str | None) -> None:
    """Types 'text', or takes back the last character for 'None'."""
    self._begin()
    typed = '' if self.replaceNext else self.__edit_text__
    if text is None:
      typed = typed[:-1]
    self.__edit_text__ = typed if text is None else typed + text
    self.replaceNext = False
    self.update()

  def _stepBy(self, steps: int) -> None:
    """Steps the number by 'steps' steps."""
    self._take(round(self.value + steps * self.step, 9))

  def _take(self, number: float) -> None:
    """Shows 'number', kept between the limits, telling of it if it
    differs from what was shown."""
    number = min(max(number, self.minimum), self.maximum)
    changed = True if abs(number - self.value) > 1e-12 else False
    self.__field_value__ = number
    self.update()
    if changed:
      self.valueEdited.emit(number)
