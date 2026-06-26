"""
LabelWidget subclasses 'PaintedWidget' and provides a widget for
displaying short labels. Please note that this widget is intended only for
very short labels, such as the name of a button or a checkbox. For text
rendering of longer text, 'TextWidget' provides a more suitable widget.
This widget on the other hand is suitable for further subclassing into
push buttons and similar.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFontMetrics, QTextOption
from PySide6.QtWidgets import QWidget
from icecream import ic
from worktoy.core.sentinels import THIS
from worktoy.desc import Field, AttriBox, Alias
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet

from . import PaintedWidget
from . import AbstractWidget as Widget
from ..paint_ops import PaintLabel, PaintBoxModel
from ..utils import Color, WFont
from ..utils.geom import Size
from ..utils.qee_num import SizePolicy, SizingMode

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union, Self

  MaybeStr: TypeAlias = Optional[str]
  MaybeInt: TypeAlias = Optional[int]
  StrField: TypeAlias = Union[str, Field]
  SizeField: TypeAlias = Union[Size, Field]
  IntField: TypeAlias = Union[int, Field]
  TextPaintBox: TypeAlias = Union[PaintLabel, AttriBox]
  BoxPaintBox: TypeAlias = Union[PaintBoxModel, AttriBox]
  IntAlias: TypeAlias = Union[Alias, int]
  ColorBox: TypeAlias = Union[AttriBox, Color]
  WFontBox: TypeAlias = Union[WFont, AttriBox]
  MaybeSizingMode: TypeAlias = Optional[SizingMode]
  SizingModeField: TypeAlias = Union[SizingMode, Field]
  MaybeSizePolicy: TypeAlias = Optional[SizePolicy]
  SizePolicyField: TypeAlias = Union[SizePolicy, Field]

  MaybeColor: TypeAlias = Optional[Color]
  ColorField: TypeAlias = Union[Color, Field]
  ColorAlias: TypeAlias = Union[Alias, Color, Field]


class LabelWidget(PaintedWidget):
  """
  LabelWidget subclasses 'PaintedWidget' and provides a widget for
  displaying short labels. Please note that this widget is intended only for
  very short labels, such as the name of a button or a checkbox. For text
  rendering of longer text, 'TextWidget' provides a more suitable widget.
  This widget on the other hand is suitable for further subclassing into
  push buttons and similar.

  Attributes
  ----------
  text: StrField
    'Field' descriptor exposing the text to be rendered by the widget.
    Subclasses should override the getter method of this field: '_getText'.
  labelOp: PaintLabel
    This paint operation prints the actual text.
  boxModelOp: PaintBoxModel
    This paint operation paints the box model of behind the text.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_text__: str = 'LABEL'
  __fallback_min_width__: int = 32
  __fallback_min_height__: int = 32
  __fallback_horizontal_mode__ = SizingMode.INTRINSIC
  __fallback_vertical_mode__ = SizingMode.INTRINSIC
  __fallback_radius__ = 0
  __fallback_background__ = Color(191, 191, 191, 255)

  #  Private Variables
  __current_text__: MaybeStr = None
  __min_width__: MaybeInt = None
  __min_height__: MaybeInt = None
  __horizontal_mode__: MaybeSizePolicy = None
  __vertical_mode__: MaybeSizePolicy = None
  __x_radius__: MaybeInt = None
  __y_radius__: MaybeInt = None
  __background_color__: MaybeColor = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  labelOp = PaintLabel()
  text: StrField = Field()
  minWidth: IntField = Field()
  minHeight: IntField = Field()
  cornerXRadius: IntField = Field()
  cornerYRadius: IntField = Field()
  xr: IntAlias = Alias('cornerXRadius')
  yr: IntAlias = Alias('cornerYRadius')
  font: WFontBox = AttriBox[WFont]()

  #  Virtual Variables
  minSize: SizeField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cornerXRadius.GET
  def _getCornerXRadius(self, **kwargs) -> int:
    if self.__x_radius__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__x_radius__ = self.__fallback_radius__
      return self._getCornerXRadius(_recursion=True)
    if isinstance(self.__x_radius__, int):
      return self.__x_radius__
    raise TypeException('__x_radius__', self.__x_radius__, int)

  @cornerYRadius.GET
  def _getCornerYRadius(self, **kwargs) -> int:
    if self.__y_radius__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__y_radius__ = self.__fallback_radius__
      return self._getCornerYRadius(_recursion=True)
    if isinstance(self.__y_radius__, int):
      return self.__y_radius__
    raise TypeException('__y_radius__', self.__y_radius__, int)

  def _createText(self, ) -> None:
    self.__current_text__ = self.__fallback_text__

  @labelOp.TEXT
  @text.GET
  def _getText(self, **kwargs) -> str:
    if self.__current_text__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createText()
      return self._getText(_recursion=True)
    if isinstance(self.__current_text__, str):
      return self.__current_text__
    raise TypeException('__current_text__', self.__current_text__, str)

  @minHeight.GET
  def _getMinHeight(self, **kwargs) -> int:
    if self.__min_height__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__min_height__ = self.__fallback_min_height__
      return self._getMinHeight(_recursion=True)
    if isinstance(self.__min_height__, int):
      return self.__min_height__
    raise TypeException('__min_height__', self.__min_height__, int)

  @minWidth.GET
  def _getMinWidth(self, **kwargs) -> int:
    if self.__min_width__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__min_width__ = self.__fallback_min_width__
      return self._getMinWidth(_recursion=True)
    if isinstance(self.__min_width__, int):
      return self.__min_width__
    raise TypeException('__min_width__', self.__min_width__, int)

  @minSize.GET
  def _getMinSize(self, **kwargs) -> Size:
    return Size(self.minWidth, self.minHeight)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cornerXRadius.SET
  def _setCornerXRadius(self, value: int, **kwargs) -> None:
    if not isinstance(value, int):
      raise TypeException('cornerXRadius', value, int)
    self.__x_radius__ = value

  @cornerYRadius.SET
  def _setCornerYRadius(self, value: int, **kwargs) -> None:
    if not isinstance(value, int):
      raise TypeException('cornerYRadius', value, int)
    self.__y_radius__ = value

  @text.SET
  def _setText(self, value: str, **kwargs) -> None:
    if not isinstance(value, str):
      raise TypeException('text', value, str)
    self.__current_text__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.preSet
  def _preSetText(self, value: str, **kwargs) -> None:
    try:
      oldText = self._getText(_recursion=True)
    except RecursionError:
      pass
    else:
      if value == oldText:
        raise SkipSet

  @text.onSet
  def _onSetBackgroundColor(self, value: Color, **kwargs) -> None:
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget, strict=True)
  def __init__(self, parent: QWidget, ) -> None:
    PaintedWidget.__init__(self, parent, )

  @overload(QWidget, str, strict=True)
  def __init__(self, parent: QWidget, text: str, ) -> None:
    PaintedWidget.__init__(self, parent, )
    self.text = text

  @overload(QWidget, str, int, int, strict=True)
  def __init__(self, parent: QWidget, text: str, xr: int, yr: int, ) -> None:
    PaintedWidget.__init__(self, parent, )
    self.text = text
    self.cornerXRadius = xr
    self.cornerYRadius = yr

  @overload(THIS, strict=True)
  def __init__(self, other: Self, ) -> None:
    parent = Widget.parent(other, )
    if parent is None:
      PaintedWidget.__init__(self, )
    else:
      PaintedWidget.__init__(self, parent, )
    self.text = other.text
    self.cornerXRadius = other.cornerXRadius
    self.cornerYRadius = other.cornerYRadius

  @overload.finalize
  def __init__(self, *args, **kwargs) -> None:
    QWidget.setMouseTracking(self, True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    This implementation includes the call the 'QWidget.setMouseTracking'
    method enabling continuous mouse tracking. This should be enabled only
    for widgets
    """
    super().initUI()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getRequiredSize(self, ) -> Size:
    """
    This method computest the size required to bound the label text.
    """
    metrics = QFontMetrics(self.font, self)
    textOption = QTextOption()
    textOption.setAlignment(Qt.AlignmentFlag.AlignCenter)
    textOption.setWrapMode(QTextOption.WrapMode.NoWrap)
    sampleText = """_%s_""" % self.text
    qRect = QFontMetrics.boundingRect(metrics, sampleText, textOption)
    width, height = QRect.width(qRect), QRect.height(qRect)
    newWidth = max(width, self.minWidth)
    newHeight = max(height, self.minHeight)
    return Size(newWidth, newHeight)
