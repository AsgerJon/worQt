"""
WFont provides a subclass of 'QFont' supporting font related enumerations
and properties. The 'WPainter' class (subclass of 'QPainter') reimplements
the 'setFont' method to overload 'WFont' instances in addition. This
design pattern changes the text color from being an aspect of the 'QPen'
assigned to the painter to instead be an attribute provided by 'WFont'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from string import ascii_letters
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import (QFont,
  QFontMetricsF,
  QFontMetrics,
  QPaintDevice,
  QPen)
from icecream import ic
from worktoy.desc import Field, AttriBox
from worktoy.keenum import KeeBox
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet

from worQt.mixin import MixinBase
from worQt.utils import Color
from worQt.utils.font_nums import FontFamilyNum, FontStyleNum
from worQt.utils.font_nums import FontLineFlags, FontWeightNum
from worQt.utils.geom import Size
from worQt.utils.qee_num import ColorNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Any, Optional

  SizeField: TypeAlias = Union[Size, Field]
  MaybeInt: TypeAlias = Optional[int]
  IntField: TypeAlias = Union[int, Field]
  IntArgs: TypeAlias = tuple[Optional[int], tuple[Any, ...]]
  FamArgs: TypeAlias = tuple[Optional[FontFamilyNum], tuple[Any, ...]]
  WeightArgs: TypeAlias = tuple[Optional[FontWeightNum], tuple[Any, ...]]
  StyleArgs: TypeAlias = tuple[Optional[FontStyleNum], tuple[Any, ...]]
  LinesArgs: TypeAlias = tuple[Optional[FontLineFlags], tuple[Any, ...]]

  FamilyBox: TypeAlias = Union[FontFamilyNum, KeeBox]
  WeightBox: TypeAlias = Union[FontWeightNum, KeeBox]
  StyleBox: TypeAlias = Union[FontStyleNum, KeeBox]
  LinesBox: TypeAlias = Union[FontLineFlags, KeeBox]
  ColorBox: TypeAlias = Union[Color, AttriBox]
  BoolBox: TypeAlias = Union[bool, AttriBox]

  QFontField: TypeAlias = Union[QFont, Field]
  QMetricsField: TypeAlias = Union[QFontMetrics, Field]
  QMetricsFieldF: TypeAlias = Union[QFontMetricsF, Field]
  QPenField: TypeAlias = Union[QPen, Field]
  MaybePen: TypeAlias = Optional[QPen]


class WFont(QFont, MixinBase):
  """
  WFont provides a subclass of 'QFont' supporting font related enumerations
  and properties. The 'WPainter' class (subclass of 'QPainter') reimplements
  the 'setFont' method to overload 'WFont' instances in addition. This
  design pattern changes the text color from being an aspect of the 'QPen'
  assigned to the painter to instead be an attribute provided by 'WFont'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_family__: str = 'MONTSERRAT'
  __fallback_weight__: str = 'NORMAL'
  __fallback_style__: str = 'NORMAL'
  __fallback_underline__: bool = False
  __fallback_strikeout__: bool = False
  __fallback_overline__: bool = False
  __fallback_color__: Color = ColorNum.BLACK.value
  __fallback_size__: int = 20

  #  Private Variables
  __cached_pen__: MaybePen = None
  __font_size__: MaybeInt = None

  #  Public Variables
  familyNum: FamilyBox = KeeBox[FontFamilyNum](__fallback_family__)
  weightNum: WeightBox = KeeBox[FontWeightNum](__fallback_weight__, )
  styleNum: StyleBox = KeeBox[FontStyleNum](__fallback_style__, )
  underlineFlag: BoolBox = AttriBox[bool](__fallback_underline__, )
  strikeoutFlag: BoolBox = AttriBox[bool](__fallback_strikeout__, )
  overlineFlag: BoolBox = AttriBox[bool](__fallback_overline__, )
  color: ColorBox = AttriBox[Color](__fallback_color__, )
  fontSize: IntField = Field()

  #  Virtual Variables
  pen: QPenField = Field()
  metrics: QMetricsField = Field()
  metricsF: QMetricsFieldF = Field()
  charSize: SizeField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @color.onSet
  def _createPen(self, ) -> None:
    penObject = QPen()
    QPen.setColor(penObject, self.color.Q)
    QPen.setStyle(penObject, Qt.PenStyle.SolidLine)
    QPen.setWidth(penObject, 1)
    self.__cached_pen__ = penObject

  @pen.GET
  def _getPen(self, **kwargs) -> QPen:
    if self.__cached_pen__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPen()
      return self._getPen(_recursion=True)
    if isinstance(self.__cached_pen__, QPen):
      return self.__cached_pen__
    raise TypeException('__cached_pen__', self.__cached_pen__, QPen)

  @fontSize.GET
  def _getFontSize(self, **kwargs) -> int:
    if self.__font_size__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__font_size__ = self.__fallback_size__
      return self._getFontSize(_recursion=True)
    if isinstance(self.__font_size__, int):
      return self.__font_size__
    raise TypeException('__font_size__', self.__font_size__, int)

  @metrics.GET
  def _getMetrics(self, **kwargs) -> QFontMetrics:
    return QFontMetrics(self)

  @metricsF.GET
  def _getMetricsF(self, **kwargs) -> QFontMetricsF:
    return QFontMetricsF(self)

  @charSize.GET
  def _getCharSize(self, **kwargs) -> Size:
    widthSum = 0
    chars = ascii_letters
    for char in ascii_letters:
      widthSum += self.metricsF.horizontalAdvance(char)
    height = self.metricsF.height()
    return Size(int(round(widthSum / len(chars))), height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @fontSize.SET
  def _setFontSize(self, value: int, **kwargs) -> None:
    if not isinstance(value, int):
      raise TypeException('fontSize', value, int)
    self.__font_size__ = value
    QFont.setPointSize(self, value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @fontSize.preSet
  def _preSetFontSize(self, value: int, **kwargs) -> None:
    if value <= 0:
      raise ValueError('fontSize must be positive')
    cls = type(self)
    desc = getattr(cls, 'fontSize')
    try:
      existing = desc.__instance_get__(self, type(self, ), _recursion=True)
    except RecursionError:
      pass
    else:
      if value == existing:
        raise SkipSet

  @fontSize.onSet
  def _onSetFontSize(self, value: int, **kwargs) -> None:
    QFont.setPointSize(self, value)

  @weightNum.preSet
  def _onSetWeightNum(self, value: FontWeightNum, **kwargs) -> None:
    cls = type(self)
    try:
      desc = getattr(cls, 'weightNum')
      getKey = getattr(desc, '__get_key__')
      getter = getattr(cls, getKey)
      oldWeight = getter(self, _recursion=True)
    except RecursionError:
      pass
    else:
      if value == oldWeight:
        raise SkipSet

  @weightNum.onSet
  def _onSetWeightNum(self, value: FontWeightNum, **kwargs) -> None:
    QFont.setWeight(self, value.value)

  @styleNum.preSet
  def _onSetStyleNum(self, value: FontStyleNum, **kwargs) -> None:
    cls = type(self)
    try:
      desc = getattr(cls, 'styleNum')
      getKey = getattr(desc, '__get_key__')
      getter = getattr(cls, getKey)
      oldStyle = getter(self, _recursion=True)
    except RecursionError:
      pass
    else:
      if value == oldStyle:
        raise SkipSet

  @styleNum.onSet
  def _onSetStyleNum(self, value: FontStyleNum, **kwargs) -> None:
    QFont.setStyle(self, value.value)

  @familyNum.preSet
  def _onSetFamilyNum(self, value: FontFamilyNum, **kwargs) -> None:
    cls = type(self)
    try:
      desc = getattr(cls, 'familyNum')
      getKey = getattr(desc, '__get_key__')
      getter = getattr(cls, getKey)
      oldFamily = getter(self, _recursion=True)
    except RecursionError:
      pass
    else:
      if value == oldFamily:
        raise SkipSet

  @familyNum.onSet
  def _onSetFamilyNum(self, value: FontFamilyNum, **kwargs) -> None:
    QFont.setFamily(self, value.value)

  @underlineFlag.preSet
  def _onSetUnderlineFlag(self, value: bool, **kwargs) -> None:
    cls = type(self)
    try:
      desc = getattr(cls, 'underlineFlag')
      getKey = getattr(desc, '__get_key__')
      getter = getattr(cls, getKey)
      oldUnderline = getter(self, _recursion=True)
    except RecursionError:
      pass
    else:
      if value == oldUnderline:
        raise SkipSet

  @underlineFlag.onSet
  def _onSetUnderlineFlag(self, value: bool, **kwargs) -> None:
    QFont.setUnderline(self, value)

  @strikeoutFlag.preSet
  def _onSetStrikeoutFlag(self, value: bool, **kwargs) -> None:
    cls = type(self)
    try:
      desc = getattr(cls, 'strikeoutFlag')
      getKey = getattr(desc, '__get_key__')
      getter = getattr(cls, getKey)
      oldStrikeout = getter(self, _recursion=True)
    except RecursionError:
      pass
    else:
      if value == oldStrikeout:
        raise SkipSet

  @strikeoutFlag.onSet
  def _onSetStrikeoutFlag(self, value: bool, **kwargs) -> None:
    QFont.setStrikeOut(self, value)

  @overlineFlag.preSet
  def _onSetOverlineFlag(self, value: bool, **kwargs) -> None:
    cls = type(self)
    try:
      desc = getattr(cls, 'overlineFlag')
      getKey = getattr(desc, '__get_key__')
      getter = getattr(cls, getKey)
      oldOverline = getter(self, _recursion=True)
    except RecursionError:
      pass
    else:
      if value == oldOverline:
        raise SkipSet

  @overlineFlag.onSet
  def _onSetOverlineFlag(self, value: bool, **kwargs) -> None:
    QFont.setOverline(self, value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def boundingWidth(self, text: str, ) -> Size:
    """
    Returns the bounding size of the given text when rendered with this font.
    """
    metrics = self.metrics
    width = metrics.horizontalAdvance(text)
    height = metrics.height()
    return Size(width, height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def family(self, **kwargs) -> str:
    """
    Reimplementation ensuring agreement with the 'familyNum' descriptor.
    """
    superFamily = QFont.family(self)
    if superFamily == self.familyNum.value:
      return superFamily
    if kwargs.get('_recursion', False):
      raise RecursionError
    QFont.setFamily(self, self.familyNum.value)
    return self.family(_recursion=True)

  def weight(self, **kwargs) -> QFont.Weight:
    """
    Reimplementation ensuring agreement with the 'weightNum' descriptor.
    """
    superWeight = QFont.weight(self)
    if superWeight == self.weightNum.value:
      return superWeight
    if kwargs.get('_recursion', False):
      raise RecursionError
    QFont.setWeight(self, self.weightNum.value)
    return self.weight(_recursion=True)

  def style(self, **kwargs) -> QFont.Style:
    """
    Reimplementation ensuring agreement with the 'styleNum' descriptor.
    """
    superStyle = QFont.style(self)
    if superStyle == self.styleNum.value:
      return superStyle
    if kwargs.get('_recursion', False):
      raise RecursionError
    QFont.setStyle(self, self.styleNum.value)
    return self.style(_recursion=True)

  def pointSize(self, **kwargs) -> int:
    """
    Reimplementation ensuring agreement with the 'fontSize' descriptor.
    """
    superSize = QFont.pointSize(self)
    if superSize == self.fontSize:
      return superSize
    if kwargs.get('_recursion', False):
      raise RecursionError
    QFont.setPointSize(self, self.fontSize)
    return self.pointSize(_recursion=True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _parseFontFamily(*args, ) -> FamArgs:
    unusedArgs = []
    posArgs = [*reversed(args), ]
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, FontFamilyNum):
        list.extend(unusedArgs, posArgs)
        return arg, (*unusedArgs,)
      unusedArgs.append(arg)
    return None, (*unusedArgs,)

  @staticmethod
  def _parseFontWeight(*args, ) -> WeightArgs:
    unusedArgs = []
    posArgs = [*reversed(args), ]
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, FontWeightNum):
        list.extend(unusedArgs, posArgs)
        return arg, (*unusedArgs,)
      unusedArgs.append(arg)
    return None, (*unusedArgs,)

  @staticmethod
  def _parseFontStyle(*args, ) -> StyleArgs:
    unusedArgs = []
    posArgs = [*reversed(args), ]
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, FontStyleNum):
        list.extend(unusedArgs, posArgs)
        return arg, (*unusedArgs,)
      unusedArgs.append(arg)
    return None, (*unusedArgs,)

  @staticmethod
  def _parseFontLines(*args, ) -> LinesArgs:
    unusedArgs = []
    posArgs = [*reversed(args), ]
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, FontLineFlags):
        list.extend(unusedArgs, posArgs)
        return arg, (*unusedArgs,)
      unusedArgs.append(arg)
    return None, (*unusedArgs,)

  @staticmethod
  def _parseFontSize(*args, ) -> IntArgs:
    unusedArgs = []
    posArgs = [*reversed(args), ]
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, int):
        list.extend(unusedArgs, posArgs)
        return arg, (*unusedArgs,)
      unusedArgs.append(arg)
    return None, (*unusedArgs,)

  def __init__(self, *args, **kwargs) -> None:
    unusedArgs = []
    posArgs = [*reversed(args), ]
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, QFont):
        QFont.__init__(self, arg)
        list.extend(unusedArgs, posArgs)
        break
      unusedArgs.append(arg)
    else:
      QFont.__init__(self, )
    family, args = self._parseFontFamily(*unusedArgs)
    weight, args = self._parseFontWeight(*args)
    style, args = self._parseFontStyle(*args)
    lines, args = self._parseFontLines(*args)
    size, args = self._parseFontSize(*args)
    if family is not None:
      self.familyNum = family
    if weight is not None:
      self.weightNum = weight
    if style is not None:
      self.styleNum = style
    if lines is not None:
      self.underlineFlag = bool(lines & FontLineFlags.UNDERLINE)
      self.strikeoutFlag = bool(lines & FontLineFlags.STRIKEOUT)
      self.overlineFlag = bool(lines & FontLineFlags.OVERLINE)
    if size is not None:
      self.fontSize = size
    if self.fontSize != self.pointSize():
      raise ValueError
    if self.family() != self.familyNum.value:
      raise ValueError
    if self.weight() != self.weightNum.value:
      raise ValueError
    if self.style() != self.styleNum.value:
      raise ValueError
    QFont.setUnderline(self, True if self.underlineFlag else False)
    QFont.setStrikeOut(self, True if self.strikeoutFlag else False)
    QFont.setOverline(self, True if self.overlineFlag else False)
