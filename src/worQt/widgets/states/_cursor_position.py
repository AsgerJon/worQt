"""
CursorPosition encapsulates the position of the cursor on the owning
widget through the descriptor protocol. Owning widgets should have
'mouseTracking' enabled. Each pointer event the QEventPoint object to a
history of cursor positions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QEventPoint as EPoint, QMouseEvent, QPointerEvent
from worktoy.core import Object
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException

from moreworktoy.utilities import Ring
from ...geometry import Rect, Point2D

from ...settings import MouseClickSettings

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Any, Type, TypeAlias

  from .. import BaseWidget as Widget

  WidgetType: TypeAlias = Type[Widget]


class _Position(BaseObject):
  """
  CursorPosition encapsulates the position of the cursor on the owning
  widget through the descriptor protocol. Owning widgets should have
  'mouseTracking' enabled. Each pointer event the QEventPoint object to a
  history of cursor positions.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __max_points__ = 32
  clickSettings = MouseClickSettings()

  #  Fallback Variables

  #  Private Variables
  __point_history__ = None

  #  Public Variables
  maxPoints = Field()
  history = Field()

  #  Virtual Variables
  pressDrift = Field()
  releaseDrift = Field()
  holdDrift = Field()
  now = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @maxPoints.GET
  def _getMaxPoints(self) -> int:
    return self.__max_points__

  def _createHistory(self, ) -> None:
    self.__point_history__ = Ring(self.maxPoints, )

  @history.GET
  def _getHistory(self, **kwargs) -> Ring:
    if self.__point_history__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createHistory()
      return self._getHistory(_recursion=True)
    return self.__point_history__

  @now.GET
  def _getNow(self) -> int:
    if self.history:
      return self.history[-1].timestamp()
    return 0

  def _getRecent(self, timeLimit: int) -> list[EPoint]:
    """
    Returns a list of points that are within the time limit from the current
    time.
    """
    if not self:
      return []

    if not isinstance(timeLimit, int):
      raise TypeException('timeLimit', timeLimit, int, )

    if len(self) == 1:
      return [self.history[-1]]
    out = []
    for point in self:
      if timeLimit < self.now - point.timestamp():
        out.append(point)
    return out

  def _getDriftRect(self, timeLim: int) -> Rect:
    points = self._getRecent(timeLim)
    if len(points) < 2:
      return Rect()
    x0, x1, y0, y1 = None, None, None, None
    for point in points:
      point2D = Point2D(point)
      if x0 is None:
        x0, y0 = point2D
      elif x1 is None:
        x1, y1 = point2D
      else:
        X = (x0, x1, point2D.x,)
        Y = (y0, y1, point2D.y,)
        x0, x1 = min(X), max(X)
        y0, y1 = min(Y), max(Y)
    return Rect(x0, y0, x1, y1)

  @pressDrift.GET
  def _getPressDrift(self) -> float:
    rect = self._getDriftRect(self.clickSettings.pressTime)
    return rect.diagonal

  @releaseDrift.GET
  def _getReleaseDrift(self) -> float:
    rect = self._getDriftRect(self.clickSettings.releaseTime)
    return rect.diagonal

  @holdDrift.GET
  def _getHoldDrift(self) -> float:
    rect = self._getDriftRect(self.clickSettings.holdTime)
    return rect.diagonal

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def clear(self) -> None:
    self.history.clear()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __bool__(self, ) -> bool:
    for _ in self.history:
      return True
    return False

  def __len__(self, ) -> int:
    return len(self.history)

  def __iter__(self, ) -> Iterator[EPoint]:
    yield from self.history

  def __getitem__(self, index: int) -> EPoint:
    return self.history[index]

  def __str__(self, ) -> str:
    if not self:
      return '(Nan, Nan)'
    latestPoint = Point2D(self[-1])
    x, y = latestPoint.x, latestPoint.y
    infoSpec = """[%d, %d]"""
    return infoSpec % (int(x), int(y),)

  def __repr__(self, ) -> str:
    return repr(self[-1])


class CursorPosition(Object):
  """
  This class provides the actual descriptor
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  #  Public Variables

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: WidgetType, name: str) -> None:
    Object.__set_name__(self, owner, name)
    owner.registerMoveCallback(self._update)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, *args, **kwargs) -> _Position:
    pvtName = self.getPrivateName()
    if hasattr(self.instance, pvtName):
      return getattr(self.instance, pvtName)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, pvtName, _Position())
    return self.__instance_get__(*args, _recursion=True, **kwargs)

  def _update(self, widget: Widget, event_: QMouseEvent, **kwargs) -> None:
    """
    The '__set_name__' method registers this method as a callback for
    notifications of mouse move events. This method updates the cursor
    positions by extracting the QEventPoint from the QMouseEvent and
    appends it to the history of cursor positions.
    """
    pvtName = self.getPrivateName()
    try:
      cursorPosition = getattr(widget, pvtName)
    except AttributeError as attributeError:
      if kwargs.get('_recursion', False):
        raise RecursionError from attributeError
      setattr(widget, pvtName, _Position())
      return self._update(widget, event_, _recursion=True, **kwargs)
    else:
      eventPoint = QPointerEvent.points(event_)[0]
      cursorPosition.history.append(eventPoint)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
