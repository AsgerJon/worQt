"""
PaintedWidget subclasses 'AbstractWidget' and provides a base for painted
widgets. This means essentially all widgets except for container widgets.
The base implements the box model for margins, borders, paddings, and
content area, allowing customization of both sizes and colours. The base
applies this painting in the 'paintEvent' method, which should *not* be
overridden in subclasses. Instead, the base provides the 'paintMeLike'
method which it calls after painting the box model, but before calling
'QPainter.end'. The base passes both the 'QPaintEvent' and the 'QPainter'
objects to the 'paintMeLike' method. Subclasses should implement
'paintMeLike' to paint_ops using the provided 'QPainter'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import (QPaintEvent,
                           QPainter,
                           QPen,
                           QPaintDevice,
                           QBrush,
                           QTextOption)
from PySide6.QtWidgets import QSizePolicy
from worktoy.desc import Field, AttriBox
from worktoy.utilities import maybe
from worktoy.waitaminute import MissingVariable, TypeException
from worktoy.waitaminute.control_flow import SkipSet

from ..waitaminute.events import EventException
from ..utils import EmptyPen, EmptyBrush, WPainter
from ..utils.qee_num import (Alignum,
                             HAlignum,
                             VAlignum,
                             SizePolicy,
                             SizingMode)
from ..utils.geom import Size, Rect, Color
from ..utils.geom import InSets
from . import AbstractWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Iterator, Optional, Type

  from ..paint_ops import AbstractPaintOp

  MaybeRect: TypeAlias = Optional[Rect]
  RectField: TypeAlias = Union[Rect, Field]

  PaintOps: TypeAlias = Iterator[AbstractPaintOp]
  PaintOpsField: TypeAlias = Union[PaintOps, Field]

  MaybeAlign: TypeAlias = Optional[Alignum]
  AlignField: TypeAlias = Union[Alignum, Field]
  HAlignField: TypeAlias = Union[HAlignum, Field]
  VAlignField: TypeAlias = Union[VAlignum, Field]
  PolicyField: TypeAlias = Union[SizePolicy, Field]
  InSetsBox: TypeAlias = Union[InSets, AttriBox]
  ColorBox: TypeAlias = Union[Color, AttriBox]
  Colors: TypeAlias = tuple[Color, Color, Color]
  ColorFields: TypeAlias = Union[Field, Colors]
  Painter: TypeAlias = Union[QPainter, WPainter]
  PainterField: TypeAlias = Union[Painter, Field]
  SizeField: TypeAlias = Union[Size, Field]

  MaybeDevice: TypeAlias = Optional[QPaintDevice]
  DeviceType: TypeAlias = Type[QPaintDevice]
  MaybeDeviceType: TypeAlias = Optional[DeviceType]

  DeviceField: TypeAlias = Union[QPaintDevice, Field]
  DeviceTypeField: TypeAlias = Union[DeviceType, Field]

  MaybeInt: TypeAlias = Optional[int]
  IntField: TypeAlias = Union[int, Field]
  MaybeStr: TypeAlias = Optional[str]
  StrField: TypeAlias = Union[str, Field]
  MaybeColor: TypeAlias = Optional[Color]
  ColorField: TypeAlias = Union[Color, Field]
  InSetsField: TypeAlias = Union[InSets, Field]

  MaybeWrap: TypeAlias = Optional[QTextOption.WrapMode]
  WrapField: TypeAlias = Union[QTextOption.WrapMode, Field]
  MaybeAlignum: TypeAlias = Optional[Alignum]
  AlignumField: TypeAlias = Union[Alignum, Field]
  OptionField: TypeAlias = Union[QTextOption, Field]

  MaybeSizingMode: TypeAlias = Optional[SizingMode]
  SizingModeField: TypeAlias = Union[SizingMode, Field]
  MaybeSizePolicy: TypeAlias = Optional[SizePolicy]
  SizePolicyField: TypeAlias = Union[SizePolicy, Field]


class PaintedWidget(AbstractWidget):
  """
  PaintedWidget subclasses 'AbstractWidget' and provides a base for painted
  widgets. This means essentially all widgets except for container widgets.
  The base implements the box model for margins, borders, paddings, and
  content area, allowing customization of both sizes and colors. The base
  applies this painting in the 'paintEvent' method, which should *not* be
  overridden in subclasses. Instead, the base provides the 'paintMeLike'
  method which it calls after painting the box model, but before calling
  'QPainter.end'. The base passes both the 'QPaintEvent' and the 'QPainter'
  objects to the 'paintMeLike' method. Subclasses should implement
  'paintMeLike' to paint_ops using the provided 'QPainter'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __paint_ops__ = None

  #  Fallback Variables
  __fallback_alignum__ = Alignum.CENTER
  __fallback_policy__ = SizePolicy()
  __fallback_required_size__ = 32, 32
  # --- Box Model Variables
  __fallback_margins_dims__ = InSets(2, 2, 2, 2)
  __fallback_borders_dims__ = InSets(1, 1, 1, 1)
  __fallback_paddings_dims__ = InSets(2, 2, 2, 2)
  __fallback_margins_color__ = Color(255, 255, 255)
  __fallback_borders_color__ = Color(0, 0, 0)
  __fallback_paddings_color__ = Color(223, 223, 223)
  __fallback_wrap__ = QTextOption.WrapMode.NoWrap
  __fallback_horizontal_mode__ = SizingMode.INTRINSIC
  __fallback_vertical_mode__ = SizingMode.INTRINSIC
  __fallback_text_align__ = Alignum.CENTER

  #  Private Variables
  __alignment_flag__: MaybeAlign = None
  __size_policy__: MaybeSizePolicy = None
  __horizontal_mode__: MaybeSizingMode = None
  __vertical_mode__: MaybeSizingMode = None
  __paint_view__: MaybeRect = None
  __paint_device__: MaybeDevice = None
  __device_type__: MaybeDeviceType = None
  __wrap_mode__: MaybeWrap = None
  __text_align__: MaybeAlignum = None
  # --- Box Model Variables
  __margins_dims__: MaybeInt = None
  __borders_dims__: MaybeInt = None
  __paddings_dims__: MaybeInt = None
  __margins_color__: MaybeColor = None
  __borders_color__: MaybeColor = None
  __paddings_color__: MaybeColor = None

  #  Public Variables
  paintOps: Field[PaintOps] = Field()
  emptyPen: Union[QPen, EmptyPen] = EmptyPen()
  emptyBrush: Union[QBrush, EmptyBrush] = EmptyBrush()
  xr = AttriBox[int](0)  # horizontal corner radius for rounded rects
  yr = AttriBox[int](0)  # vertical corner radius for rounded rects
  wrapMode: WrapField = Field()
  textAlign: AlignumField = Field()
  paintView: RectField = Field()
  # --- Box Model Variables
  marginsDims: InSetsField = Field()
  bordersDims: InSetsField = Field()
  paddingsDims: InSetsField = Field()
  marginsColor: ColorField = Field()
  bordersColor: ColorField = Field()
  paddingsColor: ColorField = Field()
  # --- Alignment Flags
  align: AlignField = Field()
  hAlign: HAlignField = Field()
  vAlign: VAlignField = Field()
  hMode: SizingModeField = Field()
  vMode: SizingModeField = Field()
  reqSize: SizeField = Field()
  device: DeviceField = Field()
  deviceType: DeviceTypeField = Field()
  textOption: OptionField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # \__________________
  #  Paint Operations ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨
  @classmethod
  def _getClsPaintOps(cls, ) -> PaintOps:
    yield from maybe(cls.__paint_ops__, ())

  @classmethod
  def registerPaintOp(cls, paint_op: AbstractPaintOp) -> None:
    existing = cls._getClsPaintOps()
    cls.__paint_ops__ = (*existing, paint_op,)

  def _clearPaintOpObjects(self, ) -> None:
    self.__paint_ops__ = None

  def _instantiatePaintOpObjects(self, ) -> None:
    cls = type(self)
    OPS = maybe(cls.__paint_ops__, ())
    self.__paint_ops__ = [p.__get__(self, cls) for p in OPS]

  @paintOps.GET
  def _getPaintOps(self, ) -> PaintOps:
    """
    This getter collects the paint_ops operations registered on the class and
    passes 'self' and 'type(self)' to the '__get__' method on each
    operation.
    """
    cls = type(self)
    OPS = maybe(cls.__paint_ops__, ())
    self.__paint_ops__ = [p.__get__(self, cls) for p in OPS]

    for paintOp in self._getClsPaintOps():
      paintOp.__widget_instance__ = self
      paintOp.__widget_type__ = type(self)
      yield paintOp

  # \_________________________
  #  END OF Paint Operations
  #  =========================
  #  Alignment Flags /
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _createAlignment(self, ) -> None:
    self.align = self.__fallback_alignum__

  @align.GET
  def _getAlignment(self, **kwargs) -> Alignum:
    if self.__alignment_flag__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createAlignment()
      return self._getAlignment(_recursion=True)
    if isinstance(self.__alignment_flag__, Alignum):
      return self.__alignment_flag__
    name, value = '__alignment_flag__', self.__alignment_flag__
    raise TypeException(name, value, Alignum)

  @hAlign.GET
  def _getHorizontalAlignment(self, ) -> HAlignum:
    return self.align.horizontal

  @vAlign.GET
  def _getVerticalAlignment(self, ) -> Alignum:
    return self.align.vertical

  # \_________________________
  #  END OF Alignment Flags
  #  =========================
  #  Box Model Dimensions and Colours /
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _createMarginsDims(self, ) -> None:
    self.__margins_dims__ = InSets(self.__fallback_margins_dims__, )

  @marginsDims.GET
  def _getMarginsDims(self, **kwargs) -> InSets:
    if self.__margins_dims__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMarginsDims()
      return self._getMarginsDims(_recursion=True)
    if isinstance(self.__margins_dims__, InSets):
      return self.__margins_dims__
    raise TypeException('__margins_dims__', self.__margins_dims__, InSets)

  def _createBordersDims(self, ) -> None:
    self.__borders_dims__ = InSets(self.__fallback_borders_dims__)

  @bordersDims.GET
  def _getBordersDims(self, **kwargs) -> InSets:
    if self.__borders_dims__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBordersDims()
      return self._getBordersDims(_recursion=True)
    if isinstance(self.__borders_dims__, InSets):
      return self.__borders_dims__
    raise TypeException('__borders_dims__', self.__borders_dims__, InSets)

  def _createPaddingsDims(self, ) -> None:
    self.__paddings_dims__ = InSets(self.__fallback_paddings_dims__)

  @paddingsDims.GET
  def _getPaddingsDims(self, **kwargs) -> InSets:
    if self.__paddings_dims__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPaddingsDims()
      return self._getPaddingsDims(_recursion=True)
    if isinstance(self.__paddings_dims__, InSets):
      return self.__paddings_dims__
    raise TypeException('__paddings_dims__', self.__paddings_dims__, InSets)

  def _createMarginsColor(self, ) -> None:
    self.__margins_color__ = self.__fallback_margins_color__

  @marginsColor.GET
  def _getMarginsColor(self, **kwargs) -> Color:
    if self.__margins_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMarginsColor()
      return self._getMarginsColor(_recursion=True)
    if isinstance(self.__margins_color__, Color):
      return self.__margins_color__
    raise TypeException('__margins_color__', self.__margins_color__, Color)

  def _createBordersColor(self, ) -> None:
    self.__borders_color__ = self.__fallback_borders_color__

  @bordersColor.GET
  def _getBordersColor(self, **kwargs) -> Color:
    if self.__borders_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBordersColor()
      return self._getBordersColor(_recursion=True)
    if isinstance(self.__borders_color__, Color):
      return self.__borders_color__
    raise TypeException('__borders_color__', self.__borders_color__, Color)

  def _createPaddingsColor(self, ) -> None:
    self.__paddings_color__ = self.__fallback_paddings_color__

  @paddingsColor.GET
  def _getPaddingsColor(self, **kwargs) -> Color:
    if self.__paddings_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPaddingsColor()
      return self._getPaddingsColor(_recursion=True)
    if isinstance(self.__paddings_color__, Color):
      return self.__paddings_color__
    raise TypeException('__paddings_color__', self.__paddings_color__, Color)

  # \_______________________________________
  #  END OF Box Model Dimensions and Colours
  #  =======================================
  #  Miscellaneous /
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  @paintView.GET
  def _getPaintView(self, ) -> Rect:
    """
    The private variable is set at the beginning of each 'paintEvent' and
    is equal to the viewport of the 'QPainter' object cast to 'Rect'.
    """
    return self.__paint_view__

  @reqSize.GET
  def _getRequiredSize(self, ) -> Size:
    """
    Subclasses may implement this method to specify a required content
    size the box model system will use to apply the extrinsic size policy.
    By default, the 'intrinsic' policy grants as much content area as
    would fit in the viewport assigned to the widget during painting. In
    this case, this method is ignored. To support the 'extrinsic' policy,
    this method must provide content size. The box model system will then
    calculate the total outer size required.
    """
    return Size(*self.__fallback_required_size__, )

  def _createTextAlignum(self, ) -> None:
    self.__text_align__ = self.__fallback_text_align__

  @textAlign.GET
  def _getTextAlignum(self, **kwargs) -> Alignum:
    if self.__text_align__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createTextAlignum()
      return self._getTextAlignum(_recursion=True)
    if isinstance(self.__text_align__, Alignum):
      return self.__text_align__
    raise TypeException('__text_align__', self.__text_align__, Alignum)

  def _createWrapMode(self, ) -> None:
    self.__wrap_mode__ = self.__fallback_wrap__

  @wrapMode.GET
  def _getWrapMode(self, **kwargs) -> QTextOption.WrapMode:
    if self.__wrap_mode__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWrapMode()
      return self._getWrapMode(_recursion=True)
    if isinstance(self.__wrap_mode__, QTextOption.WrapMode):
      return self.__wrap_mode__
    name, value = '__wrap_mode__', self.__wrap_mode__
    raise TypeException(name, value, QTextOption.WrapMode)

  @textOption.GET
  def _getTextOption(self, ) -> QTextOption:
    """
    This method creates a 'QTextOption' object with the wrap mode and text
    alignment of the widget. Subclasses may override this method to provide
    a custom 'QTextOption' object, but by default it is created from the
    'wrapMode' and 'textAlign' properties of the widget.
    """
    option = QTextOption()
    option.setWrapMode(self.wrapMode)
    option.setAlignment(self.textAlign.Q)
    return option

  def _createHorizontalMode(self, ) -> None:
    self.hMode = self.__fallback_horizontal_mode__

  @hMode.GET
  def _getHorizontalMode(self, **kwargs) -> SizingMode:
    if self.__horizontal_mode__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createHorizontalMode()
      return self._getHorizontalMode(_recursion=True)
    if isinstance(self.__horizontal_mode__, SizingMode):
      return self.__horizontal_mode__
    name, value = '__horizontal_mode__', self.__horizontal_mode__
    raise TypeException(name, value, SizingMode)

  def _createVerticalMode(self, ) -> None:
    self.vMode = self.__fallback_vertical_mode__

  @vMode.GET
  def _getVerticalMode(self, **kwargs) -> SizingMode:
    if self.__vertical_mode__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createVerticalMode()
      return self._getVerticalMode(_recursion=True)
    if isinstance(self.__vertical_mode__, SizingMode):
      return self.__vertical_mode__
    name, value = '__vertical_mode__', self.__vertical_mode__
    raise TypeException(name, value, SizingMode)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @align.SET
  def _setAlignment(self, alignum: Alignum) -> None:
    if not isinstance(alignum, Alignum):
      raise TypeException('alignum', alignum, Alignum)
    self.__alignment_flag__ = alignum

  @hAlign.SET
  def _setHorizontalAlignment(self, hAlignum: HAlignum) -> None:
    raise NotImplementedError

  @vAlign.SET
  def _setVerticalAlignment(self, vAlignum: VAlignum) -> None:
    raise NotImplementedError

  @hMode.SET
  def _setHorizontalMode(self, mode: SizingMode) -> None:
    if not isinstance(mode, SizingMode):
      raise TypeException('mode', mode, SizingMode)
    self.__horizontal_mode__ = mode

  @vMode.SET
  def _setVerticalMode(self, mode: SizingMode) -> None:
    if not isinstance(mode, SizingMode):
      raise TypeException('mode', mode, SizingMode)
    self.__vertical_mode__ = mode

  @marginsColor.SET
  def _setMarginsColor(self, color: Color) -> None:
    if not isinstance(color, Color):
      raise TypeException('color', color, Color)
    self.__margins_color__ = color

  @bordersColor.SET
  def _setBordersColor(self, color: Color) -> None:
    if not isinstance(color, Color):
      raise TypeException('color', color, Color)
    self.__borders_color__ = color

  @paddingsColor.SET
  def _setPaddingsColor(self, color: Color) -> None:
    if not isinstance(color, Color):
      raise TypeException('color', color, Color)
    self.__paddings_color__ = color

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @align.preSet
  def _preSetAlignment(self, alignum: Alignum) -> None:
    try:
      oldAlignum = self._getAlignment(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldAlignum == alignum:
        raise SkipSet

  @align.onSet
  def _onSetAlignment(self, *args) -> None:
    """
    This notifier is called whenever the alignment is set. It should
    trigger a repaint of the widget to apply the new alignment.
    """
    self.update()

  @vMode.preSet
  def _preSetVerticalMode(self, mode: SizingMode) -> None:
    try:
      oldMode = self._getVerticalMode(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldMode == mode:
        raise SkipSet

  @hMode.preSet
  def _preSetHorizontalMode(self, mode: SizingMode) -> None:
    try:
      oldMode = self._getHorizontalMode(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldMode == mode:
        raise SkipSet

  @vMode.onSet
  @hMode.onSet
  def _onSetHorizontalMode(self, *args) -> None:
    """
    This notifier is called whenever the horizontal mode is set. It should
    trigger a repaint of the widget to apply the new mode.
    """
    sizePol = QSizePolicy()
    sizePol.setHorizontalPolicy(self.hMode.Q)
    sizePol.setVerticalPolicy(self.vMode.Q)
    self.setSizePolicy(sizePol)
    self.update()

  @marginsColor.preSet
  def _preSetMarginsColor(self, color: Color) -> None:
    try:
      oldColor = self._getMarginsColor(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldColor == color:
        raise SkipSet

  @bordersColor.preSet
  def _preSetBordersColor(self, color: Color) -> None:
    try:
      oldColor = self._getBordersColor(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldColor == color:
        raise SkipSet

  @paddingsColor.preSet
  def _preSetPaddingsColor(self, color: Color) -> None:
    try:
      oldColor = self._getPaddingsColor(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldColor == color:
        raise SkipSet

  @marginsColor.onSet
  @bordersColor.onSet
  @paddingsColor.onSet
  def _onSetMarginsColor(self, *args) -> None:
    """
    This notifier is called whenever the margins color is set. It should
    trigger a repaint of the widget to apply the new color.
    """
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintEvent(self, paintE: QPaintEvent) -> None:
    """
    paintEvent is called whenever the widget needs to be repainted. This
    implementation paints the box model (margins, borders, paddings, and
    content area) before calling the 'paintMeLike' method for custom
    painting.

    :param paintE: The QPaintEvent object.
    :return: None

    Subclasses should *not* override this method. Instead, they should
    implement the 'paintMeLike' method to perform their custom painting.
    """
    painter = WPainter()
    painter.begin(self, )
    try:
      self.__paint_view__ = Rect(painter.viewport())
      for paintOp in self.paintOps:
        painter.save()
        paintOp.prepare(painter)
        self.__paint_view__ = paintOp.paint(painter, self.paintView, paintE)
        if not isinstance(self.__paint_view__, Rect):
          raise TypeException('__paint_view__', self.__paint_view__, Rect)
        paintOp.reset(painter)
        painter.restore()
    except Exception as exception:
      raise EventException(paintE) from exception
    finally:
      painter.end()
