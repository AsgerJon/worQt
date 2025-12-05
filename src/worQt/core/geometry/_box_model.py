"""
BoxModel encapsulates the box-model geometric object. For padding, border
and margins, it has a 'Margins' object and a 'Color' object. It should
have a 'Rect' object assigned to it as the anchor. It then dynamically
computes the following 'Rect' objects:

- anchorRect: The assigned rectangle.
- borderRect: The rectangle including the border, but not the margins.
- paddedRect: The rectangle including the padding, but not the border.
- contentRect: The rectangle excluding the padding.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPaintDevice
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field, AttriBox
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt
from worktoy.waitaminute import VariableNotNone, MissingVariable
from worktoy.waitaminute.desc import WithoutException

from . import Margins, Rect
from .. import RougeVertBleu

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable, Self, Any, Never


class BoxModel(BaseObject):
  """
  BoxModel encapsulates the box-model geometric object. For padding, border
  and margins, it has a 'Margins' object and a 'Color' object. It should
  have a 'Rect' object assigned to it as the anchor. It then dynamically
  computes the following 'Rect' objects:

  - anchorRect: The assigned rectangle.
  - borderRect: The rectangle including the border, but not the margins.
  - paddedRect: The rectangle including the padding, but not the border.
  - contentRect: The rectangle excluding the padding.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __key_words__ = dict(
      margin=('margin', 'outer',),
      border=('border', 'stroke',),
      padding=('padding', 'inner',),
      marginColor=('marginColor', 'outerColor',),
      borderColor=('borderColor', 'strokeColor',),
      paddingColor=('paddingColor', 'innerColor',),
  )
  __key_variables__ = dict(
      margin='__margin_margins__',
      border='__border_margins__',
      padding='__padding_margins__',
      marginColor='__margin_color__',
      borderColor='__border_color__',
      paddingColor='__padding_color__',
  )
  __key_types__ = dict(
      margin=Margins,
      border=Margins,
      padding=Margins,
      marginColor=RougeVertBleu,
      borderColor=RougeVertBleu,
      paddingColor=RougeVertBleu,
  )

  #  Fallback Variables
  __fallback_margins__ = Margins(2, 2, 2, 2)
  __fallback_border__ = Margins(2, 2, 2, 2)
  __fallback_padding__ = Margins(2, 2, 2, 2)
  __fallback_margin_color__ = RougeVertBleu(255, 255, 255, 0)  # No alpha
  __fallback_border_color__ = RougeVertBleu(0, 0, 0, 255)  # Full alpha
  __fallback_padding_color__ = RougeVertBleu(255, 255, 255, 0)  # No alpha

  #  Private Variables
  __margin_margins__ = None
  __border_margins__ = None
  __padding_margins__ = None
  __margin_color__ = None
  __border_color__ = None
  __padding_color__ = None
  __anchor_callback__ = None
  __anchor_rect__ = None
  __last_owner__ = None
  __last_instance__ = None
  __paint_device__ = None

  #  Public Variables
  margin = Field()
  border = Field()
  padding = Field()
  marginColor = Field()
  borderColor = Field()
  paddingColor = Field()
  paintDevice = Field()

  #  Virtual Variables
  anchorRect = Field()
  borderRect = Field()
  paddedRect = Field()
  contentRect = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @margin.GET
  def _getMargin(self, **kwargs) -> Margins:
    if self.__margin_margins__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__margin_margins__ = self.__fallback_margins__
      return self._getMargin(_recursion=True)
    return self.__margin_margins__

  @border.GET
  def _getBorder(self, **kwargs) -> Margins:
    if self.__border_margins__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__border_margins__ = self.__fallback_border__
      return self._getBorder(_recursion=True)
    return self.__border_margins__

  @padding.GET
  def _getPadding(self, **kwargs) -> Margins:
    if self.__padding_margins__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__padding_margins__ = self.__fallback_padding__
      return self._getPadding(_recursion=True)
    return self.__padding_margins__

  @marginColor.GET
  def _getMarginColor(self, **kwargs) -> RougeVertBleu:
    if self.__margin_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__margin_color__ = self.__fallback_margin_color__
      return self._getMarginColor(_recursion=True)
    return self.__margin_color__

  @borderColor.GET
  def _getBorderColor(self, **kwargs) -> RougeVertBleu:
    if self.__border_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__border_color__ = self.__fallback_border_color__
      return self._getBorderColor(_recursion=True)
    return self.__border_color__

  @paddingColor.GET
  def _getPaddingColor(self, **kwargs) -> RougeVertBleu:
    if self.__padding_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__padding_color__ = self.__fallback_padding_color__
      return self._getPaddingColor(_recursion=True)
    return self.__padding_color__

  @paintDevice.GET
  def _getPaintDevice(self, **kwargs) -> QPaintDevice:
    if self.__paint_device__ is None:
      raise MissingVariable(self, '__paint_device__', QPaintDevice)
    return self.__paint_device__

  #  Virtual Getters

  @anchorRect.GET
  def _getAnchorRect(self, **kwargs) -> Rect:
    if isinstance(self.paintDevice, QWidget):
      return Rect(QWidget.rect(self.paintDevice))
    if isinstance(self.paintDevice, QPaintDevice):
      w, h = QPaintDevice.width(self.paintDevice), QPaintDevice.height()
      return Rect(0, 0, w, h)
    raise MissingVariable(self, 'paintDevice', QPaintDevice)

  @borderRect.GET
  def _getBorderRect(self, **kwargs) -> Rect:
    return self.anchorRect - self.margin

  @paddedRect.GET
  def _getPaddedRect(self, **kwargs) -> Rect:
    return self.borderRect - self.border

  @contentRect.GET
  def _getContentRect(self, **kwargs) -> Rect:
    return self.paddedRect - self.padding

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @margin.SET
  def _setMargin(self, value: Margins, **kwargs) -> None:
    if self.__margin_margins__ is not None:
      raise VariableNotNone('__margin_margins__', self.__margin_margins__)
    self.__margin_margins__ = Margins(value)

  @border.SET
  def _setBorder(self, value: Margins, **kwargs) -> None:
    if self.__border_margins__ is not None:
      raise VariableNotNone('__border_margins__', self.__border_margins__)
    self.__border_margins__ = Margins(value)

  @padding.SET
  def _setPadding(self, value: Margins, **kwargs) -> None:
    if self.__padding_margins__ is not None:
      raise VariableNotNone('__padding_margins__', self.__padding_margins__)
    self.__padding_margins__ = Margins(value)

  @marginColor.SET
  def _setMarginColor(self, value: RougeVertBleu, **kwargs) -> None:
    if self.__margin_color__ is not None:
      raise VariableNotNone('__margin_color__', self.__margin_color__)
    self.__margin_color__ = RougeVertBleu(value)

  @borderColor.SET
  def _setBorderColor(self, value: RougeVertBleu, **kwargs) -> None:
    if self.__border_color__ is not None:
      raise VariableNotNone('__border_color__', self.__border_color__)
    self.__border_color__ = RougeVertBleu(value)

  @paddingColor.SET
  def _setPaddingColor(self, value: RougeVertBleu, **kwargs) -> None:
    if self.__padding_color__ is not None:
      raise VariableNotNone('__padding_color__', self.__padding_color__)
    self.__padding_color__ = RougeVertBleu(value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __get__(self, instance: Any, owner: Any, **kwargs) -> Self:
    callback = getattr(owner, self.__anchor_callback__)
    self.__anchor_rect__ = callback(instance, )
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    """
    The 'BoxModel' colours and margins must be set with keyword arguments.
    A 'QWidget' object may be passed as a positional argument
    """
    for (key, words) in self.__key_words__.items():
      for word in words:
        if word in kwargs:
          varName = self.__key_variables__[key]
          if getattr(self, varName) is not None:
            raise VariableNotNone(varName, getattr(self, varName))
          cls = self.__key_types__[key]
          setattr(self, varName, cls(kwargs[word]))
          break
    for arg in args:
      if isinstance(arg, QPaintDevice):
        self.__paint_device__ = arg

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
