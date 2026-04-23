"""
TextPaintOp subclasses 'AbstractPaintOp' and provides the painting
operation responsible for text. Please note, that this operation is
intended for short labels, rather than paragraphs of text. For this case,
use 'textComposeOp' instead.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PySide6.QtGui import QPen, QColor, QFont
from worktoy.desc import Field
from worktoy.waitaminute import MissingVariable, TypeException, \
  VariableNotNone

from worQt.paint_ops import AbstractPaintOp
from worQt.utils.geom import Color

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union

  Color: TypeAlias = Union[QColor, Color, QPen]


class TextPaintOp(AbstractPaintOp):
  """
  TextPaintOp subclasses 'AbstractPaintOp' and provides the painting
  operation responsible for text. Please note, that this operation is
  intended for short labels, rather than paragraphs of text. For this case,
  use 'textComposeOp' instead.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_text__ = ''
  __fallback_font__ = None
  __fallback_color__ = 0, 0, 0, 255

  #  Private Variables
  __text_getter_key__ = None
  __color_getter_key__ = None
  __font_getter_key__ = None
  __cached_text__ = None

  #  Public Variables
  text = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getTextGetterKey(self, ) -> str:
    """
    This method returns the key for the text getter.
    """
    if self.__text_getter_key__ is None:
      raise MissingVariable(self, '__text_getter_key__', str)
    if isinstance(self.__text_getter_key__, str):
      return self.__text_getter_key__
    name, value = '__text_getter_key__', self.__text_getter_key__
    raise TypeException(name, value, str)

  def _getColorGetterKey(self, ) -> str:
    """
    This method returns the key for the text color getter.
    """
    if self.__color_getter_key__ is None:
      raise MissingVariable(self, '__color_getter_key__', str)
    if isinstance(self.__color_getter_key__, str):
      return self.__color_getter_key__
    name, value = '__color_getter_key__', self.__color_getter_key__
    raise TypeException(name, value, str)

  def _getFontGetterKey(self, ) -> str:
    """
    This method returns the key for the text font getter.
    """
    if self.__font_getter_key__ is None:
      raise MissingVariable(self, '__font_getter_key__', str)
    if isinstance(self.__font_getter_key__, str):
      return self.__font_getter_key__
    name, value = '__font_getter_key__', self.__font_getter_key__
    raise TypeException(name, value, str)

  def _getTextGetterFunc(self, ) -> Callable:
    """
    This method returns the text getter function from the field owner.
    """
    key = self._getTextGetterKey()
    if self.widgetType is None:
      raise RuntimeError("""Cannot get text before __set_name__!""")
    try:
      getterFunc = getattr(self.widgetType, key)
    except AttributeError as attributeError:
      raise RuntimeError from attributeError
    else:
      if not callable(getterFunc):
        name, value = key, getterFunc
        raise TypeException(name, value, Callable)
      return getterFunc

  def _getColorGetterFunc(self, ) -> Callable:
    """
    This method returns the text color getter function from the field owner.
    """
    key = self._getColorGetterKey()
    if self.widgetType is None:
      raise RuntimeError("""Cannot get text color before __set_name__!""")
    try:
      getterFunc = getattr(self.widgetType, key)
    except AttributeError as attributeError:
      raise RuntimeError from attributeError
    else:
      if not callable(getterFunc):
        name, value = key, getterFunc
        raise TypeException(name, value, Callable)
      return getterFunc

  def _getFontGetterFunc(self, ) -> Callable:
    """
    This method returns the text font getter function from the field owner.
    """
    key = self._getFontGetterKey()
    if self.widgetType is None:
      raise RuntimeError("""Cannot get text font before __set_name__!""")
    try:
      getterFunc = getattr(self.widgetType, key)
    except AttributeError as attributeError:
      raise RuntimeError from attributeError
    else:
      if not callable(getterFunc):
        name, value = key, getterFunc
        raise TypeException(name, value, Callable)
      return getterFunc

  def _getText(self, ) -> str:
    """
    This method returns the text from the text getter function.
    """
    if self.widget is None:
      if self.__cached_text__ is None:
        raise RuntimeError("""Cannot get text before __set_name__!""")
      if not isinstance(self.__cached_text__, str):
        name, value = '__cached_text__', self.__cached_text__
        raise TypeException(name, value, str)
      return self.__cached_text__
    getterFunc = self._getTextGetterFunc()
    text = getterFunc(self.widget)
    if not isinstance(text, str):
      raise TypeException('text', text, str)
    return self._updateText(text)

  def _getColor(self, ) -> Color:
    """
    This method returns the text color from the text color getter function.
    """
    getterFunc = self._getColorGetterFunc()
    color = getterFunc(self.widget)
    if isinstance(color, Color):
      return color
    try:
      wColor = Color(color)
    except Exception as exception:
      raise TypeException('color', color, Color) from exception
    else:
      return wColor

  def _getFont(self, ) -> QFont:
    """
    This method returns the text font from the text font getter function.
    """
    getterFunc = self._getFontGetterFunc()
    font = getterFunc(self.widget)
    if not isinstance(font, QFont):
      name, value = 'font', font
      raise TypeException(name, value, QFont)
    return font

  def _updateText(self, text: str) -> str:
    """
    This method updates the cached text and returns the text.
    """
    if self.__cached_text__ == text:
      return text
    self.__cached_text__ = text
    return text

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setTextGetterKey(self, key: str) -> None:
    """
    This method sets the key for the text getter.
    """
    if not isinstance(key, str):
      name, value = '__text_getter_key__', key
      raise TypeException(name, value, str)
    if self.__text_getter_key__ is not None:
      raise VariableNotNone('__text_getter_key__', self.__text_getter_key__)
    self.__text_getter_key__ = key

  def _setColorGetterKey(self, key: str) -> None:
    """
    This method sets the key for the text color getter.
    """
    if not isinstance(key, str):
      name, value = '__color_getter_key__', key
      raise TypeException(name, value, str)
    if self.__color_getter_key__ is not None:
      name, value = '__color_getter_key__', self.__color_getter_key__
      raise VariableNotNone(name, value)
    self.__color_getter_key__ = key

  def _setFontGetterKey(self, key: str) -> None:
    """
    This method sets the key for the text font getter.
    """
    if not isinstance(key, str):
      name, value = '__font_getter_key__', key
      raise TypeException(name, value, str)
    if self.__font_getter_key__ is not None:
      raise VariableNotNone('__font_getter_key__', self.__font_getter_key__)
    self.__font_getter_key__ = key

  def TEXT(self, func: Callable[..., str]) -> Callable[..., str]:
    """
    This method is a decorator for setting the text getter. Decorate the
    method on the owning widget type specifying the current text to
    paint_ops.
    """
    self._setTextGetterKey(func.__name__)
    return func

  def COLOR(self, func: Callable[..., Color]) -> Callable[..., Color]:
    """
    This method is a decorator for setting the text color getter. Decorate
    the method on the owning widget type specifying the current text color
    to paint_ops.
    """
    self._setColorGetterKey(func.__name__)
    return func

  def FONT(self, func: Callable[..., QFont]) -> Callable[..., QFont]:
    """
    This method is a decorator for setting the text font getter. Decorate
    the method on the owning widget type specifying the current text font
    to paint_ops.
    """
    self._setFontGetterKey(func.__name__)
    return func
