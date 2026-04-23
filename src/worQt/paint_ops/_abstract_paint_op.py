"""
AbstractPaintOp provides an abstract baseclass for the paint_ops operation
classes. It implements the descriptor protocol, meaning that it should
*not* be kept in a 'BaseBox' class, but should instead be class variables.

The widget currently painted on is returned by the 'QPainter.device'
method which returns a 'QPaintDevice' (a superclass of 'QWidget'). This
allows the paint_ops operation to access properties of the widget to allow
dynamically adjusting the paint_ops operation based on widget properties. For
example, a widget could be painted darker when under the mouse cursor.

Subclasses should implement the 'paint_ops' method to specify the paint_ops
operation. Additionally, subclasses may implement the 'update' method.
This method receives both the widget being painted on and the
'QPaintEvent' object. The widget should *not* be changed by the 'update'
method, but allow the paint_ops operation to adjust its internal state to
align with the widget state prior to painting. This is safer than the
general descriptor implementation in 'worktoy', which attempts to allow
descriptor instances to retain reference to the instance when '__get__' is
running. This behaviour will likely be removed in future versions of
'worktoy' except if a much stronger implementation is found.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPainter, QPaintEvent, QPaintDevice, QBrush, QPen
from worktoy.mcls import BaseObject
from worktoy.desc import Field
from worktoy.waitaminute import MissingVariable, TypeException

from ..utils import EmptyPen, EmptyBrush
from ..utils.geom import Rect

# from ..widgets import WPainter, PaintedWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, TypeAlias, Union, Optional
  from ..widgets import PaintedWidget
  from ..utils import WPainter

  Widget: TypeAlias = Optional[PaintedWidget]
  WidgetType: TypeAlias = Type[PaintedWidget]
  WidgetTypeField: TypeAlias = Union[WidgetType, Field]
  StrField: TypeAlias = Union[str, Field]
  WidgetField: TypeAlias = Union[Widget, Field]
  Painter: TypeAlias = Union[QPainter, WPainter]
  PainterField: TypeAlias = Union[Painter, Field]
  BoolField: TypeAlias = Union[bool, Field]

  MaybeDevice: TypeAlias = Optional[QPaintDevice]
  DeviceField: TypeAlias = Union[MaybeDevice, Field]
  MaybeDeviceType: TypeAlias = Optional[type]
  DeviceTypeField: TypeAlias = Union[MaybeDeviceType, Field]

  Pen: TypeAlias = Union[QPen, EmptyPen]
  Brush: TypeAlias = Union[QBrush, EmptyBrush]

  from abc import abstractmethod, ABC
else:
  abstractmethod, ABC = lambda func: func, object


class AbstractPaintOp(BaseObject, ABC):
  """
  AbstractPaintOp provides an abstract baseclass for the paint_ops operation
  classes. Subclasses that require particular values from their owning
  widget class should imp
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __widget_instance__ = None
  __widget_type__ = None
  __op_name__ = None
  __is_root__ = None
  __paint_device__: MaybeDevice = None
  __device_type__: MaybeDeviceType = None

  #  Public Variables
  widget: WidgetField = Field()
  widgetType: WidgetTypeField = Field()
  opName: StrField = Field()
  isRoot: BoolField = Field()
  device: DeviceField = Field()
  deviceType: DeviceTypeField = Field()

  #  Virtual Variables
  emptyPen: Pen = EmptyPen()
  emptyBrush: Brush = EmptyBrush()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @widget.GET
  def _getWidget(self, ) -> QPaintDevice:
    return self.__widget_instance__

  @widgetType.GET
  def _getWidgetType(self, ) -> WidgetType:
    return self.__widget_type__

  @opName.GET
  def _getOpName(self, ) -> str:
    return self.__op_name__

  @isRoot.GET
  def _getIsRoot(self, ) -> bool:
    return True if self.__is_root__ else False

  @device.GET
  def _getDevice(self, ) -> QPaintDevice:
    if self.__paint_device__ is None:
      raise MissingVariable(self, '__paint_device__', QPaintDevice)
    if isinstance(self.__paint_device__, QPaintDevice):
      return self.__paint_device__
    name, value = '__paint_device__', self.__paint_device__
    raise TypeException(name, value, QPaintDevice)

  @deviceType.GET
  def _getDeviceType(self, ) -> type:
    if self.__device_type__ is None:
      raise MissingVariable(self, '__device_type__', type)
    if isinstance(self.__device_type__, type):
      return self.__device_type__
    name, value = '__device_type__', self.__device_type__
    raise TypeException(name, value, type)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def prepare(self, painter: Painter, ) -> Painter:
    """
    The same widget may own an arbitrary number of paint_ops operations. Each
    operation will use the same painter. Subclasses may implement this
    method to initialize the painter for the paint_ops operation. As an
    example consider a text painting operation. This operation would likely
    set a cosmetic 'QPen' with solid line style and the 'QColor' of the
    intended text color.

    This method is not strictly necessary, as the paint_ops method could
    easily setup the painter as part of the paint_ops operation. It does
    however help provide modularity. As a continuation of the text
    painting example, suppose a situation requires a more advanced test
    painting operation. This could conceivably be implemented as a
    subclass of the text painting operation. It would obviously need to
    implement the more advanced operation in the 'paint_ops' method,
    but might
    very well be able to reuse the painter initialization provided by this
    method.

    Parameters
    ----------
    painter : QPainter
      The painter currently painting the owning widget. This method should
      'setFont', 'setPen' and such. Do *not* call 'painter.begin()' or
      'painter.end()' in this method!
    Returns
    -------
    return: QPainter
      The painter after preparation.
    """
    self.__paint_device__ = painter.device()
    return painter

  def reset(self, painter: Painter) -> Painter:
    """
    Resets the paint_ops operation.
    Parameters
    ----------
    painter : QPainter
      The painter currently painting the owning widget. This method should
      reset any changes made to the painter in 'preparePainter'. Do *not*
      call 'painter.begin()' or 'painter.end()' in this method!
    Returns
    -------
    return: QPainter
      The painter after resetting.
    """
    self.__paint_device__ = None
    return painter

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @abstractmethod
  def paint(self, painter: Painter, rect: Rect, event: QPaintEvent) -> Rect:
    """
    Subclasses should implement this method to specify the paint_ops
    operation.

    Parameters
    ----------
    painter : QPainter | WPainter
      The painter to use for the paint_ops operation. *DO NOT* call
      'painter.begin()' or 'painter.end()' in this method. Use the painter
      to apply the painting operations.
    rect: Rect
      The rectangle to paint_ops within. This is the content area of the
      widget,
      meaning that it is the area left after painting margins, borders, and
      paddings. Subclasses should apply their painting within this rectangle.
      In future, clipping may be applied.
    event: QPaintEvent
      While 'painter' and 'rect' are likely sufficient, the 'event' should
      be passed to subclasses of 'EventException' raised during painting.
    Returns
    -------
    return: Rect
      The rectangle available for painting by the next paint_ops operation.
      Only paint_ops operations, such as box model implementations, should
      need to modify the rectangle. Most paint_ops operations should simply
      return the provided rectangle.
    """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, widgetType: WidgetType, name: str) -> None:
    BaseObject.__set_name__(self, widgetType, name)
    self.__widget_type__ = widgetType
    widgetType.registerPaintOp(self, )
    self.__op_name__ = name

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
