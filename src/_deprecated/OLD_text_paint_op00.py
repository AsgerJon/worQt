"""
Font encapsulates fonts with 'QFont' version available at name 'Q'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPainter, QPen
from PySide6.QtGui import QFont, QFontMetrics, QFontMetricsF
from worktoy.desc import Field
from worktoy.waitaminute import TypeException

from worQt.utils.font_nums import FontFamilyNum, FontStyleNum
from worQt.utils.font_nums import FontWeightNum, FontLineFlags

from worQt.utils.qee_num import ColorNum

from worQt.utils.geom import InSets, Color, Rect

from worQt.paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union
  from abc import ABC
  from worQt.widgets import WPainter

  Painter: TypeAlias = Union[QPainter, WPainter]
  InSetsField: TypeAlias = Union[InSets, Field]
  ColorField: TypeAlias = Union[Color, Field]
  Keys: TypeAlias = tuple[str, str, str, str, str]
  Rects: TypeAlias = tuple[Rect, Rect, Rect, Rect]
  FamilyField: TypeAlias = Union[FontFamilyNum, Field]
  WeightField: TypeAlias = Union[FontWeightNum, Field]
  StyleField: TypeAlias = Union[FontStyleNum, Field]
  LinesField: TypeAlias = Union[FontLineFlags, Field]
  PenField: TypeAlias = Union[QPen, Field]
  MetricsField: TypeAlias = Union[QFontMetrics, QFontMetricsF, Field]
  FontField: TypeAlias = Union[QFont, Field]
  TupleField: TypeAlias = Union[tuple[str, ...], Field]
else:
  abstractmethod, ABC = lambda func: func, object


class TextPaintOp(AbstractPaintOp, ABC):
  """
  Font encapsulates fonts with 'QFont' version available at name 'Q'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_family__ = FontFamilyNum.MONTSERRAT
  __fallback_weight__ = FontWeightNum.NORMAL
  __fallback_style__ = FontStyleNum.NORMAL
  __fallback_lines__ = FontLineFlags.NULL
  __fallback_color__ = ColorNum.BLACK

  #  Private Variables
  __font_family__ = None
  __font_weight__ = None
  __font_style__ = None
  __font_lines__ = None
  __font_color__ = None

  #  Public Variables
  family: FamilyField = Field()
  weight: WeightField = Field()
  style: StyleField = Field()
  lines: LinesField = Field()
  color: ColorField = Field()
  Q: FontField = Field()
  textPen: PenField = Field()
  QFMetrics: MetricsField = Field()
  QFMetricsF: MetricsField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @family.GET
  def _getFamily(self, **kwargs) -> FontFamilyNum:
    if self.__font_family__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__font_family__ = self.__fallback_family__
      return self._getFamily(_recursion=True)
    if isinstance(self.__font_family__, FontFamilyNum):
      return self.__font_family__
    name, value = '__font_family__', self.__font_family__
    raise TypeException(name, value, FontFamilyNum)

  @weight.GET
  def _getWeight(self, **kwargs) -> FontWeightNum:
    if self.__font_weight__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__font_weight__ = self.__fallback_weight__
      return self._getWeight(_recursion=True)
    if isinstance(self.__font_weight__, FontWeightNum):
      return self.__font_weight__
    name, value = '__font_weight__', self.__font_weight__
    raise TypeException(name, value, FontWeightNum)

  @style.GET
  def _getStyle(self, **kwargs) -> FontStyleNum:
    if self.__font_style__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__font_style__ = self.__fallback_style__
      return self._getStyle(_recursion=True)
    if isinstance(self.__font_style__, FontStyleNum):
      return self.__font_style__
    name, value = '__font_style__', self.__font_style__
    raise TypeException(name, value, FontStyleNum)

  @lines.GET
  def _getLines(self, **kwargs) -> FontLineFlags:
    if self.__font_lines__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__font_lines__ = self.__fallback_lines__
      return self._getLines(_recursion=True)
    if isinstance(self.__font_lines__, FontLineFlags):
      return self.__font_lines__
    name, value = '__font_lines__', self.__font_lines__
    raise TypeException(name, value, FontLineFlags)

  @color.GET
  def _getColor(self, **kwargs) -> Color:
    if self.__font_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__font_color__ = self.__fallback_color__
      return self._getColor(_recursion=True)
    if isinstance(self.__font_color__, Color):
      return self.__font_color__
    name, value = '__font_color__', self.__font_color__
    raise TypeException(name, value, Color)

  @Q.GET
  def _getQ(self, ) -> QFont:
    family = self.family.value
    weight = self.weight.value
    style = self.style.value
    lines = self.lines.value
    qFont = QFont(family, weight, style)
    qFont = lines.apply(qFont)
    return qFont

  @textPen.GET
  def _getPen(self, ) -> QPen:
    raise NotImplementedError

  @QFMetrics.GET  # QFontMetrics
  def _getQM(self, ) -> QFontMetrics:
    return QFontMetrics(self.Q)

  @QFMetricsF.GET  # QFontMetricsF
  def _getQMF(self, ) -> QFontMetricsF:
    return QFontMetricsF(self.Q)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def prepare(self, painter: Painter, ) -> Painter:
    return painter

  def reset(self, painter: Painter) -> Painter:
    return painter

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
