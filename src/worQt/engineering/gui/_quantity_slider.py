"""
QuantitySlider subclasses 'Slider' and sets a quantity between a least
and a greatest, shown in its unit.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Signal
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from . import Slider


class QuantitySlider(Slider):
  """
  QuantitySlider subclasses 'Slider' and sets a quantity: its 'quantity'
  runs from 'low' to 'high' as its share goes from nought to all, shown
  in its 'unit' to as many 'decimals' as 'setScale' gives it, and kept
  between them. 'quantityChanged' tells of each change, in its unit.
  Set by 'setLogScale', it runs there 'logScale', by equal factors: a
  quantity from 0.01 to 1 is 0.1 halfway.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __scale_low__: float = 0.0
  __scale_high__: float = 1.0
  __scale_unit__: str = ''
  __scale_decimals__: int = 2

  #  Virtual Variables
  low: Field[float] = Field()
  high: Field[float] = Field()
  unit: Field[str] = Field()
  quantity: Field[float] = Field()

  #  Signals
  quantityChanged = Signal(float)

  #  Public Variables
  logScale = AttriBox[bool](False)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @low.GET
  def _getLow(self, ) -> float:
    """The 'low' getter returns the least the quantity may be."""
    return self.__scale_low__

  @high.GET
  def _getHigh(self, ) -> float:
    """The 'high' getter returns the greatest the quantity may be."""
    return self.__scale_high__

  @unit.GET
  def _getUnit(self, ) -> str:
    """The 'unit' getter returns the unit the quantity is shown in."""
    return self.__scale_unit__

  @quantity.GET
  def _getQuantity(self, ) -> float:
    """The 'quantity' getter returns the quantity the slider is at."""
    if self.logScale:
      return self.low * (self.high / self.low) ** self.value
    return self.low + self.value * (self.high - self.low)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @quantity.SET
  def _setQuantity(self, quantity: float) -> None:
    """The 'quantity' setter moves the slider to 'quantity', kept between
    the least and the greatest."""
    if not self.logScale:
      self.value = (float(quantity) - self.low) / (self.high - self.low)
    elif quantity <= self.low:
      self.value = 0.0
    else:
      self.value = math.log(quantity / self.low) / math.log(
        self.high / self.low)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    Slider.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    Slider.__init__(self, )

  @overload.finalize
  def __init__(self, *args) -> None:
    self.valueChanged.connect(self._tellQuantity)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setScale(self, low: float, high: float, unit: str,
               decimals: int, ) -> None:
    """The 'setScale' method sets the least and the greatest the quantity
    may be, its unit, and how many decimals it is shown to."""
    if high <= low:
      raise ValueError('the greatest must be more than the least')
    self.__scale_low__, self.__scale_high__ = float(low), float(high)
    self.__scale_unit__, self.__scale_decimals__ = unit, int(decimals)
    self.logScale = False
    self.update()

  def setLogScale(self, low: float, high: float, unit: str,
                  decimals: int, ) -> None:
    """The 'setLogScale' method sets the scale as 'setScale' does, but
    run by equal factors, not equal steps: the least must be more than
    nought."""
    if low <= 0.0:
      raise ValueError('the least must be more than nought')
    self.setScale(low, high, unit, decimals)
    self.logScale = True
    self.update()

  def valueText(self, ) -> str:
    """The 'valueText' method says the quantity, in its unit."""
    return self._textOf(self.quantity)

  def valueRect(self, ) -> QRectF:
    """The 'valueRect' method returns where the quantity is written, room
    for the widest it may be."""
    metrics = self.font.metrics
    widest = max(metrics.horizontalAdvance(self._textOf(self.low)),
                 metrics.horizontalAdvance(self._textOf(self.high)))
    return self._valueRectOf(float(widest) + 4.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _textOf(self, quantity: float) -> str:
    """'quantity' as the slider would show it."""
    text = '%.*f' % (self.__scale_decimals__, quantity)
    return '%s %s' % (text, self.unit) if self.unit else text

  def _tellQuantity(self, *_) -> None:
    """Tells of a change of the quantity."""
    self.quantityChanged.emit(self.quantity)
