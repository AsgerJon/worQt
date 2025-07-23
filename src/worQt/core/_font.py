"""
'Font' implements text fonts.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QSize, QRect, QRectF, Qt, QSizeF
from PySide6.QtGui import QFont, QFontMetrics, QFontMetricsF
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

from ..nums import FontFamilyNum, Alignum
from ..nums import HorizontalAlignum as HAlign
from ..nums import VerticalAlignum as VAlign


class Font(BaseObject):
  """Font implements the font family and size."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_family__ = 'MONTSERRAT'
  __fallback_size__ = 12
  __fallback_weight__ = QFont.Weight.Normal
  __fallback_italic__ = False
  __fallback_align__ = Alignum.CENTER

  #  Private Variables
  __font_family__ = None
  __font_size__ = None
  __font_weight__ = None
  __italic_flag__ = None
  __text_align__ = None

  #  Public Variables
  family = Field()
  size = Field()
  weight = Field()
  italic = Field()
  alignment = Field()

  #  Virtual Variables
  Q = Field()
  metrics = Field()
  metricsF = Field()
  height = Field()
  heightF = Field()
  bound = Field()
  hAlign = Field()
  vAlign = Field()
  flags = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @family.GET
  def _getFamily(self, ) -> FontFamilyNum:
    fallback = FontFamilyNum[self.__fallback_family__]
    return maybe(self.__font_family__, fallback)

  @size.GET
  def _getSize(self) -> int:
    """Returns the font size."""
    return maybe(self.__font_size__, self.__fallback_size__)

  @weight.GET
  def _getWeight(self) -> int:
    """Returns the font weight."""
    return maybe(self.__font_weight__, self.__fallback_weight__)

  @italic.GET
  def _getItalic(self) -> bool:
    """Returns the italic flag."""
    return maybe(self.__italic_flag__, self.__fallback_italic__)

  @alignment.GET
  def _getAlignment(self) -> Alignum:
    """Returns the text alignment."""
    return maybe(self.__text_align__, self.__fallback_align__)

  @Q.GET
  def _getQ(self) -> QFont:
    """Returns the QFont object."""
    font = QFont()
    font.setFamily(self.family)
    font.setPointSize(self.size)
    font.setWeight(self.weight)
    font.setItalic(self.italic)
    return font

  @metrics.GET
  def _getMetrics(self) -> QFontMetrics:
    """Returns the font metrics."""
    return QFontMetrics(self.Q)

  @metricsF.GET
  def _getMetricsF(self) -> QFontMetricsF:
    """Returns the font metrics with floating point precision."""
    return QFontMetricsF(self.Q)

  @height.GET
  def _getHeight(self) -> int:
    """Returns the height of the font."""
    return self.metrics.height()

  @heightF.GET
  def _getHeightF(self) -> float:
    """Returns the height of the font with floating point precision."""
    return self.metricsF.height()

  @hAlign.GET
  def _getHAlign(self) -> HAlign:
    """Returns the horizontal alignment."""
    return self.alignment.horizontal

  @vAlign.GET
  def _getVAlign(self) -> VAlign:
    """Returns the vertical alignment."""
    return self.alignment.vertical

  @flags.GET
  def _getFlags(self) -> int:
    """Returns text option flags. """
    return Qt.TextFlag.TextWordWrap | self.hAlign.value | self.vAlign.value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def textWidth(self, text: str) -> int:
    return self.metrics.horizontalAdvance(text)

  def textWidthF(self, text: str) -> float:
    return self.metricsF.horizontalAdvance(text)

  def boundSize(self, *args, ) -> QSize:
    return self.boundRect(*args, ).size()

  def boundSizeF(self, *args, ) -> QSizeF:
    return self.boundRectF(*args, ).size()

  @overload(QRectF, str)
  def boundRectF(self, rect: QRectF, text: str) -> QRectF:
    return self.metricsF.boundingRect(rect, self.flags, text)

  @overload(QRect, str)
  def boundRectF(self, rect: QRect, text: str) -> QRectF:
    return self.metricsF.boundingRect(QRect.toRectF(rect), self.flags, text)

  @overload(str)
  def boundRectF(self, text: str) -> QRectF:
    """Returns the bounding rectangle of the text."""
    return self.metricsF.boundingRect(text, self.flags)

  @overload(QRectF, str)
  def boundRect(self, rect: QRectF, text: str) -> QRect:
    """Returns the bounding rectangle of the text in a QRect."""
    return self.metrics.boundingRect(QRectF.toRect(rect), self.flags, text)

  @overload(QRect, str)
  def boundRect(self, rect: QRect, text: str) -> QRect:
    """Returns the bounding rectangle of the text in a QRect."""
    return self.metrics.boundingRect(rect, self.flags, text)

  @overload(str)
  def boundRect(self, text: str) -> QRect:
    """Returns the bounding rectangle of the text in a QRect."""
    return self.metrics.boundingRect(text, self.flags)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QFont)
  def __init__(self, font: QFont) -> None:
    """Initializes the Font with a QFont object."""
    self.__font_family__ = font.family()
    self.__font_size__ = font.pointSize()
    self.__font_weight__ = font.weight()
    self.__italic_flag__ = font.italic()

  @overload(str, int, int, bool)
  def __init__(self, fam: str, s: int, w: int, k: bool) -> None:
    """Initializes the Font with family, size, weight and italic flag."""
    self.__font_family__ = fam
    self.__font_size__ = s
    self.__font_weight__ = w
    self.__italic_flag__ = k

  @overload(FontFamilyNum, int, int, bool)
  def __init__(self, fam: FontFamilyNum, s: int, w: int, k: bool) -> None:
    """Initializes the Font with family as FontFamilyNum."""
    self.__font_family__ = fam.name
    self.__font_size__ = s
    self.__font_weight__ = w
    self.__italic_flag__ = k

  @overload(str, int, int)
  def __init__(self, fam: str, s: int, w: int) -> None:
    """Initializes the Font with family, size and weight."""
    self.__font_family__ = fam
    self.__font_size__ = s
    self.__font_weight__ = w
    self.__italic_flag__ = self.__fallback_italic__

  @overload(FontFamilyNum, int, int)
  def __init__(self, fam: FontFamilyNum, s: int, w: int) -> None:
    """Initializes the Font with family as FontFamilyNum."""
    self.__font_family__ = fam.name
    self.__font_size__ = s
    self.__font_weight__ = w
    self.__italic_flag__ = self.__fallback_italic__

  @overload(str, int)
  def __init__(self, fam: str, s: int) -> None:
    """Initializes the Font with family and size."""
    self.__font_family__ = fam
    self.__font_size__ = s
    self.__font_weight__ = self.__fallback_weight__
    self.__italic_flag__ = self.__fallback_italic__

  @overload(FontFamilyNum, int)
  def __init__(self, fam: FontFamilyNum, s: int) -> None:
    """Initializes the Font with family as FontFamilyNum."""
    self.__font_family__ = fam.name
    self.__font_size__ = s
    self.__font_weight__ = self.__fallback_weight__
    self.__italic_flag__ = self.__fallback_italic__

  @overload(str)
  def __init__(self, fam: str) -> None:
    """Initializes the Font with family."""
    self.__font_family__ = fam
    self.__font_size__ = self.__fallback_size__
    self.__font_weight__ = self.__fallback_weight__
    self.__italic_flag__ = self.__fallback_italic__

  @overload(FontFamilyNum)
  def __init__(self, fam: FontFamilyNum) -> None:
    """Initializes the Font with family as FontFamilyNum."""
    self.__font_family__ = fam.name
    self.__font_size__ = self.__fallback_size__
    self.__font_weight__ = self.__fallback_weight__
    self.__italic_flag__ = self.__fallback_italic__

  @overload(int, int, bool)
  def __init__(self, s: int, w: int, k: bool) -> None:
    """Initializes the Font with size, weight and italic flag."""
    self.__font_family__ = self.__fallback_family__
    self.__font_size__ = s
    self.__font_weight__ = w
    self.__italic_flag__ = k

  @overload(int, int)
  def __init__(self, s: int, w: int) -> None:
    """Initializes the Font with size and weight."""
    self.__font_family__ = self.__fallback_family__
    self.__font_size__ = s
    self.__font_weight__ = w
    self.__italic_flag__ = self.__fallback_italic__

  @overload(int)
  def __init__(self, s: int) -> None:
    """Initializes the Font with size."""
    self.__font_family__ = self.__fallback_family__
    self.__font_size__ = s
    self.__font_weight__ = self.__fallback_weight__
    self.__italic_flag__ = self.__fallback_italic__

  @overload()
  def __init__(self) -> None:
    """Initializes the Font with default values."""
    self.__font_family__ = self.__fallback_family__
    self.__font_size__ = self.__fallback_size__
    self.__font_weight__ = self.__fallback_weight__
    self.__italic_flag__ = self.__fallback_italic__
