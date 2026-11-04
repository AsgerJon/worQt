"""
WFont is the font worQt paints text with: a 'QFont' that also carries the
text colour, so a widget's whole text style lives in one value and
'WPainter.setFont' sets the pen along with the font.

A 'WFont' is built from positional arguments in any order - a family (a
'GenericFamilyNum' or an installed family's name), a weight, a style, line
flags, a point size, a colour, and optionally a 'QFont' to start from:

    WFont(GenericFamilyNum.MONO, FontWeightNum.BOLD, 14)

Its typed fields ('familyName', 'weightNum', 'styleNum', 'fontSize', the
line flags) read from and write to the 'QFont' itself, so the two can never
disagree; only 'color' is extra state. Resolving the family needs the
installed fonts, so building a 'WFont' needs a running 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from string import ascii_letters
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QFontMetricsF, QPen
from worktoy.desc import Field
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

from ..mixin import MixinBase
from ._color import Color
from .font_nums import FontFamily, GenericFamilyNum, FontWeightNum
from .font_nums import FontStyleNum, FontLineFlags
from .geom import Size
from .qee_num import ColorNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, TypeAlias, Union

  FamilyLike: TypeAlias = Union[GenericFamilyNum, str]
  WeightLike: TypeAlias = Union[FontWeightNum, QFont.Weight, str]
  StyleLike: TypeAlias = Union[FontStyleNum, QFont.Style, str]
  ColorLike: TypeAlias = Union[Color, QColor, ColorNum]
  Aspects: TypeAlias = dict[str, Any]


class WFont(QFont, MixinBase):
  """
  WFont is the font worQt paints text with: a 'QFont' that also carries
  the text colour. See the module docstring for how to build one.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_family__: str = 'SANS'  # a 'GenericFamilyNum' member name
  __fallback_size__: int = 20
  __fallback_color__: tuple[int, int, int, int] = (0, 0, 0, 255)

  #  Private Variables
  __text_color__: Optional[Color] = None

  #  Public Variables
  familyName: Field[str] = Field()
  weightNum: Field[FontWeightNum] = Field()
  styleNum: Field[FontStyleNum] = Field()
  underlineFlag: Field[bool] = Field()
  strikeoutFlag: Field[bool] = Field()
  overlineFlag: Field[bool] = Field()
  fontSize: Field[int] = Field()
  color: Field[Color] = Field()

  #  Virtual Variables
  pen: Field[QPen] = Field()
  metrics: Field[QFontMetrics] = Field()
  metricsF: Field[QFontMetricsF] = Field()
  charSize: Field[Size] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @familyName.GET
  def _getFamilyName(self, ) -> str:
    return QFont.family(self)

  @weightNum.GET
  def _getWeightNum(self, ) -> FontWeightNum:
    return FontWeightNum(QFont.weight(self))

  @styleNum.GET
  def _getStyleNum(self, ) -> FontStyleNum:
    return FontStyleNum(QFont.style(self))

  @underlineFlag.GET
  def _getUnderlineFlag(self, ) -> bool:
    return True if QFont.underline(self) else False

  @strikeoutFlag.GET
  def _getStrikeoutFlag(self, ) -> bool:
    return True if QFont.strikeOut(self) else False

  @overlineFlag.GET
  def _getOverlineFlag(self, ) -> bool:
    return True if QFont.overline(self) else False

  @fontSize.GET
  def _getFontSize(self, ) -> int:
    return QFont.pointSize(self)

  def _createColor(self, ) -> None:
    self.__text_color__ = Color(*self.__fallback_color__)

  @color.GET
  def _getColor(self, **kwargs) -> Color:
    if self.__text_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createColor()
      return self._getColor(_recursion=True)
    if isinstance(self.__text_color__, Color):
      return self.__text_color__
    raise TypeException('__text_color__', self.__text_color__, Color)

  @pen.GET
  def _getPen(self, ) -> QPen:
    """
    The 'pen' getter returns the solid, one pixel wide pen in the text
    colour that 'WPainter.setFont' paints this font's text with.
    """
    pen = QPen()
    QPen.setColor(pen, self.color.Q)
    QPen.setStyle(pen, Qt.PenStyle.SolidLine)
    QPen.setWidth(pen, 1)
    return pen

  @metrics.GET
  def _getMetrics(self, ) -> QFontMetrics:
    return QFontMetrics(self)

  @metricsF.GET
  def _getMetricsF(self, ) -> QFontMetricsF:
    return QFontMetricsF(self)

  @charSize.GET
  def _getCharSize(self, ) -> Size:
    """
    The 'charSize' getter returns the size of an average letter: the mean
    advance of the ASCII letters by the line height.
    """
    metricsF = self.metricsF
    widthSum = sum(metricsF.horizontalAdvance(c) for c in ascii_letters)
    width = int(round(widthSum / len(ascii_letters)))
    return Size(width, int(round(metricsF.height())))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @familyName.SET
  def _setFamilyName(self, value: FamilyLike) -> None:
    """
    The 'familyName' setter takes a 'GenericFamilyNum', which always finds
    an installed family, or a family name, which must be installed.
    """
    if isinstance(value, GenericFamilyNum):
      return QFont.setFamily(self, value.family)
    if isinstance(value, str):
      return QFont.setFamily(self, FontFamily.resolve(value))
    raise TypeException('familyName', value, GenericFamilyNum, str)

  @weightNum.SET
  def _setWeightNum(self, value: WeightLike) -> None:
    QFont.setWeight(self, FontWeightNum(value).value)

  @styleNum.SET
  def _setStyleNum(self, value: StyleLike) -> None:
    QFont.setStyle(self, FontStyleNum(value).value)

  @underlineFlag.SET
  def _setUnderlineFlag(self, value: bool) -> None:
    QFont.setUnderline(self, True if value else False)

  @strikeoutFlag.SET
  def _setStrikeoutFlag(self, value: bool) -> None:
    QFont.setStrikeOut(self, True if value else False)

  @overlineFlag.SET
  def _setOverlineFlag(self, value: bool) -> None:
    QFont.setOverline(self, True if value else False)

  @fontSize.SET
  def _setFontSize(self, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
      raise TypeException('fontSize', value, int)
    if value <= 0:
      infoSpec = """A font size must be positive, but received: %d!"""
      raise ValueError(textFmt(infoSpec % value))
    QFont.setPointSize(self, value)

  @color.SET
  def _setColor(self, value: ColorLike) -> None:
    """
    The 'color' setter takes a 'Color', a 'QColor' or a 'ColorNum' member,
    and keeps a copy of its own.
    """
    self.__text_color__ = Color(value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _aspectOf(arg: Any) -> str:
    """
    The '_aspectOf' method names the aspect a constructor argument sets,
    judged by its type alone. 'QFont.Weight' is an 'int', so it is checked
    before the point size.
    """
    if isinstance(arg, QFont):
      return 'base'
    if isinstance(arg, (GenericFamilyNum, str)):
      return 'familyName'
    if isinstance(arg, (FontWeightNum, QFont.Weight)):
      return 'weightNum'
    if isinstance(arg, (FontStyleNum, QFont.Style)):
      return 'styleNum'
    if isinstance(arg, FontLineFlags):
      return 'lineFlags'
    if isinstance(arg, (Color, QColor, ColorNum)):
      return 'color'
    if isinstance(arg, int) and not isinstance(arg, bool):
      return 'fontSize'
    raise TypeException('arg', arg, QFont, GenericFamilyNum, str,
                        FontWeightNum, FontStyleNum, FontLineFlags, Color,
                        int)

  @classmethod
  def _sortAspects(cls, *args: Any) -> Aspects:
    """
    The '_sortAspects' method maps each constructor argument to the aspect
    it sets. Two arguments for the same aspect are refused rather than
    letting one silently win.
    """
    aspects = dict()
    for arg in args:
      aspect = cls._aspectOf(arg)
      if aspect in aspects:
        infoSpec = """'%s' received two arguments for '%s': '%s' and
        '%s'!"""
        info = infoSpec % (cls.__name__, aspect, aspects[aspect], arg)
        raise ValueError(textFmt(info))
      aspects[aspect] = arg
    return aspects

  def _fallbackAspects(self, ) -> Aspects:
    """
    The '_fallbackAspects' method returns what a font built from nothing
    starts as: the fallback generic family and point size. A font built
    from a 'QFont' starts as that font instead.
    """
    family = GenericFamilyNum(self.__fallback_family__)
    return {'familyName': family, 'fontSize': self.__fallback_size__}

  def __init__(self, *args: Any) -> None:
    aspects = self._sortAspects(*args)
    base = aspects.pop('base', None)
    if base is None:
      QFont.__init__(self, )
      aspects = {**self._fallbackAspects(), **aspects}
    else:
      QFont.__init__(self, base)
    for aspect, value in aspects.items():
      if aspect == 'lineFlags':
        value.apply(self)
        continue
      setattr(self, aspect, value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def boundingWidth(self, text: str, ) -> Size:
    """
    The 'boundingWidth' method returns the size 'text' takes up on one line
    in this font: its advance by the line height.
    """
    metrics = self.metrics
    return Size(metrics.horizontalAdvance(text), metrics.height())
