"""
BoxColor provides a parallel to 'BoxModel' that instead of providing
dimensions, provides colors.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QColor
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.desc import Field
from worktoy.waitaminute import TypeException

from worQt.utils._color import Color
from ..qee_num import BoxNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union

  ColorLike: TypeAlias = Union[Color, QColor, str]
  WColorField: TypeAlias = Union[Color, Field]


class BoxColor(BaseObject):
  """
  BoxColor provides a parallel to 'BoxModel' that instead of providing
  dimensions, provides colors.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_margin_color__ = 255, 255, 255
  __fallback_border_color__ = 0, 0, 0
  __fallback_padding_color__ = 255, 255, 255

  #  Private Variables
  __margins_color__ = None
  __borders_color__ = None
  __paddings_color__ = None

  #  Public Variables
  marginColor: WColorField = Field()
  borderColor: WColorField = Field()
  paddingColor: WColorField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createMarginColor(self) -> None:
    try:
      fallback = self.__widget_type__.__fallback_margin_color__
    except AttributeError:
      fallback = self.__fallback_margin_color__
    self.__margins_color__ = Color(*fallback, )

  @marginColor.GET
  def _getMarginColor(self, **kwargs) -> Color:
    if self.__margins_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMarginColor()
      return self._getMarginColor(_recursion=True, )
    if isinstance(self.__margins_color__, Color):
      return self.__margins_color__
    name, value = '__margins_color__', self.__margins_color__
    raise TypeException(name, value, Color)

  def _createBorderColor(self) -> None:
    try:
      fallback = self.__widget_type__.__fallback_border_color__
    except AttributeError:
      fallback = self.__fallback_border_color__
    self.__borders_color__ = Color(*fallback, )

  @borderColor.GET
  def _getBorderColor(self, **kwargs) -> Color:
    if self.__borders_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBorderColor()
      return self._getBorderColor(_recursion=True, )
    if isinstance(self.__borders_color__, Color):
      return self.__borders_color__
    name, value = '__borders_color__', self.__borders_color__
    raise TypeException(name, value, Color)

  def _createPaddingColor(self) -> None:
    try:
      fallback = self.__widget_type__.__fallback_padding_color__
    except AttributeError:
      fallback = self.__fallback_padding_color__
    self.__paddings_color__ = Color(*fallback, )

  @paddingColor.GET
  def _getPaddingColor(self, **kwargs) -> Color:
    if self.__paddings_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPaddingColor()
      return self._getPaddingColor(_recursion=True, )
    if isinstance(self.__paddings_color__, Color):
      return self.__paddings_color__
    name, value = '__paddings_color__', self.__paddings_color__
    raise TypeException(name, value, Color)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(BoxNum)
  def __getitem__(self, boxNum: BoxNum) -> Color:
    if boxNum == BoxNum.MARGIN:
      return self.marginColor
    elif boxNum == BoxNum.BORDER:
      return self.borderColor
    elif boxNum == BoxNum.PADDING:
      return self.paddingColor
    else:
      raise KeyError(boxNum)

  @overload(str)
  def __getitem__(self, boxName: str) -> Color:
    if str.startswith(boxName, 'margin'):
      return self.marginColor
    elif str.startswith(boxName, 'border'):
      return self.borderColor
    elif str.startswith(boxName, 'padding'):
      return self.paddingColor
    else:
      raise KeyError(boxName)

  @overload(slice)
  def __getitem__(self, boxNums: slice) -> ColorLike:
    boxNum = boxNums.start
    type_ = boxNums.step
    color = self[boxNum]
    if type_ is None:
      return color
    if type_ is Color:
      return color
    if type_ is QColor:
      return color.Q
    if type_ is str:
      return color.hex
    name, value = 'boxNums', boxNums
    raise TypeException(name, value, QColor, Color, str)
