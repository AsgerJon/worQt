"""
BoxWidget subclasses 'BaseWidget' and provides a base class for widgets
that operate on the box model of layouting.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import ARGS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import joinWords
from worktoy.waitaminute import TypeException

from worQt.utils.geom import InSets
from . import BaseWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Type


class BoxWidget(BaseWidget):
  """
  BoxWidget subclasses 'BaseWidget' and provides a base class for widgets
  that operate on the box model of layouting.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  STATIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_margin_insets__: tuple[int, int, int, int] = 6, 6, 6, 6
  __fallback_margin_color__: tuple[int, int, int, int] = 255, 255, 255, 255
  __fallback_border_insets__: tuple[int, int, int, int] = 2, 2, 2, 2
  __fallback_border_color__: tuple[int, int, int, int] = 0, 0, 0, 255
  __fallback_padding_insets__: tuple[int, int, int, int] = 4, 4, 4, 4
  __fallback_padding_color__: tuple[int, int, int, int] = 255, 255, 255, 255

  #  Private Variables
  __margin_insets__: Optional[InSets] = None
  __margin_color__: Optional[QColor] = None
  __border_insets__: Optional[InSets] = None
  __border_color__: Optional[QColor] = None
  __padding_insets__: Optional[InSets] = None
  __padding_color__: Optional[QColor] = None

  #  Operational Variables
  __view_rect__: Optional[QRect] = None

  #  Public Variables
  marginInsets = Field[InSets]()
  marginColor = Field[QColor]()
  borderInsets = Field[InSets]()
  borderColor = Field[QColor]()
  paddingInsets = Field[InSets]()
  paddingColor = Field[QColor]()
  viewRect = Field[QRect]()

  #  Virtual Variables
  marginBrush: Field[QBrush] = Field()
  borderBrush: Field[QBrush] = Field()
  paddingBrush: Field[QBrush] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createMarginInsets(self, ) -> None:
    self.__margin_insets__ = InSets(*self.__fallback_margin_insets__)

  @marginInsets.GET
  def _getMarginInsets(self, **kwargs) -> InSets:
    if self.__margin_insets__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMarginInsets()
      return self._getMarginInsets(_recursion=True)
    if isinstance(self.__margin_insets__, InSets):
      return self.__margin_insets__
    name, value = '__margin_insets__', self.__margin_insets__
    raise TypeException(name, value, InSets)

  def _createMarginColor(self, ) -> None:
    self.__margin_color__ = QColor(*self.__fallback_margin_color__)

  @marginColor.GET
  def _getMarginColor(self, **kwargs) -> QColor:
    if self.__margin_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMarginColor()
      return self._getMarginColor(_recursion=True)
    if isinstance(self.__margin_color__, QColor):
      return self.__margin_color__
    name, value = '__margin_color__', self.__margin_color__
    raise TypeException(name, value, QColor)

  def _createBorderInsets(self, ) -> None:
    self.__border_insets__ = InSets(*self.__fallback_border_insets__)

  @borderInsets.GET
  def _getBorderInsets(self, **kwargs) -> InSets:
    if self.__border_insets__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBorderInsets()
      return self._getBorderInsets(_recursion=True)
    if isinstance(self.__border_insets__, InSets):
      return self.__border_insets__
    name, value = '__border_insets__', self.__border_insets__
    raise TypeException(name, value, InSets)

  def _createBorderColor(self, ) -> None:
    self.__border_color__ = QColor(*self.__fallback_border_color__)

  @borderColor.GET
  def _getBorderColor(self, **kwargs) -> QColor:
    if self.__border_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBorderColor()
      return self._getBorderColor(_recursion=True)
    if isinstance(self.__border_color__, QColor):
      return self.__border_color__
    name, value = '__border_color__', self.__border_color__
    raise TypeException(name, value, QColor)

  def _createPaddingInsets(self, ) -> None:
    self.__padding_insets__ = InSets(*self.__fallback_padding_insets__)

  @paddingInsets.GET
  def _getPaddingInsets(self, **kwargs) -> InSets:
    if self.__padding_insets__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPaddingInsets()
      return self._getPaddingInsets(_recursion=True)
    if isinstance(self.__padding_insets__, InSets):
      return self.__padding_insets__
    name, value = '__padding_insets__', self.__padding_insets__
    raise TypeException(name, value, InSets)

  @marginBrush.GET
  def _getMarginBrush(self, ) -> QBrush:
    brush: QBrush = QBrush()
    QBrush.setColor(brush, self.marginColor)
    QBrush.setStyle(brush, Qt.BrushStyle.SolidPattern)
    return brush

  @borderBrush.GET
  def _getBorderBrush(self, ) -> QBrush:
    brush: QBrush = QBrush()
    QBrush.setColor(brush, self.borderColor)
    QBrush.setStyle(brush, Qt.BrushStyle.SolidPattern)
    return brush

  @paddingBrush.GET
  def _getPaddingBrush(self, ) -> QBrush:
    brush: QBrush = QBrush()
    QBrush.setColor(brush, self.paddingColor)
    QBrush.setStyle(brush, Qt.BrushStyle.SolidPattern)
    return brush

  def _createViewRect(self, ) -> None:
    QWidget.geometry(self)
    self.__view_rect__ = self.geometry()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @marginInsets.SET
  @overload(InSets)
  def _setMarginInsets(self, value: InSets) -> None:
    self.__margin_insets__ = value

  @staticmethod
  def _castInSets(*args) -> InSets:
    if len(args) > 4:
      infoSpec: str = """expected at most 4 integers, 
      but received '%d' integers: <br><tab>%s"""
      argStr: str = joinWords(*[str(arg) for arg in args])
      info: str = infoSpec % (len(args), argStr)
      raise ValueError(info)
    if len(args) == 4:
      return InSets(*args)
    if len(args) == 3:
      return InSets(args[0], args[1], args[2], args[2])
    if len(args) == 2:
      return InSets(args[0], args[1], args[0], args[1])
    if len(args) == 1:
      return InSets(args[0], args[0], args[0], args[0])
    return InSets()

  @marginInsets.SET
  @overload(*ARGS[int], )
  def _setMarginInsets(self, *args) -> None:
    self.__margin_insets__ = self._castInSets(*args)

  @borderInsets.SET
  @overload(InSets)
  def _setBorderInsets(self, value: InSets) -> None:
    self.__border_insets__ = value

  @borderInsets.SET
  @overload(*ARGS[int], )
  def _setBorderInsets(self, *args) -> None:
    self.__border_insets__ = self._castInSets(*args)

  @paddingInsets.SET
  @overload(InSets)
  def _setPaddingInsets(self, value: InSets) -> None:
    self.__padding_insets__ = value

  @paddingInsets.SET
  @overload(*ARGS[int], )
  def _setPaddingInsets(self, *args) -> None:
    self.__padding_insets__ = self._castInSets(*args)

  @staticmethod
  def _castColor(*args) -> QColor:
    if len(args) > 4:
      infoSpec: str = """expected at most 4 integers, 
      but received '%d' integers: <br><tab>%s"""
      argStr: str = joinWords(*[str(arg) for arg in args])
      info: str = infoSpec % (len(args), argStr)
      raise ValueError(info)
    if len(args) == 4:
      return QColor(*args)
    if len(args) == 3:
      return QColor(args[0], args[1], args[2], 255)
    if len(args) == 2:
      return QColor(args[0], args[0], args[0], args[1])
    if len(args) == 1:
      return QColor(args[0], args[0], args[0], 255)
    return QColor(255, 255, 255, 255)

  @marginColor.SET
  @overload(QColor)
  def _setMarginColor(self, value: QColor) -> None:
    self.__margin_color__ = value

  @marginColor.SET
  @overload(*ARGS[int], )
  def _setMarginColor(self, *args) -> None:
    self.__margin_color__ = self._castColor(*args)

  @borderColor.SET
  @overload(QColor)
  def _setBorderColor(self, value: QColor) -> None:
    self.__border_color__ = value

  @borderColor.SET
  @overload(*ARGS[int], )
  def _setBorderColor(self, *args) -> None:
    self.__border_color__ = self._castColor(*args)

  @paddingColor.SET
  @overload(QColor)
  def _setPaddingColor(self, value: QColor) -> None:
    self.__padding_color__ = value

  @paddingColor.SET
  @overload(*ARGS[int], )
  def _setPaddingColor(self, *args) -> None:
    self.__padding_color__ = self._castColor(*args)
