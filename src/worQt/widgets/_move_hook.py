"""
MoveHook subclasses 'BaseObject' and provides a hook that triggers one
callback if the cursor moves from where it was when the hook triggered,
OR another callback after some time without movement.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException, MissingVariable

from ..utils.geom import Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Callable, Union, Optional, Type

  from . import MoveHook
  from . import AbstractWidget as Widget

  Shiboken: TypeAlias = Type[Widget]
  Callback: TypeAlias = Callable[[Any, ...], None]
  MaybeCallback: TypeAlias = Optional[Callback]
  MaybeInt: TypeAlias = Optional[int]
  IntField: TypeAlias = Union[int, Field]
  MaybeStr: TypeAlias = Optional[str]
  StrField: TypeAlias = Union[str, Field]
  KeySetter: TypeAlias = Callable[[MoveHook, str], None]


class MoveHook(BaseObject):
  """
  MoveHook subclasses 'BaseObject' and provides a hook that triggers one
  callback if the cursor moves from where it was when the hook triggered,
  OR another callback after some time without movement.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_time__: int = 1000  # Milliseconds

  #  Private Variables
  __time_limit__: MaybeInt = None  # Milliseconds
  __moving_callback__: MaybeCallback = None
  __timeout_callback__: MaybeCallback = None
  __moving_key__: MaybeStr = None
  __timeout_key__: MaybeStr = None

  #  Public Variables
  timeLimit: IntField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @timeLimit.GET
  def _getTimeLimit(self, **kwargs) -> int:
    if self.__time_limit__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      return self._getTimeLimit(_recursion=True)
    if isinstance(self.__time_limit__, int):
      return self.__time_limit__
    raise TypeException('__time_limit__', self.__time_limit__, int)

  def _getMovingCallbackKey(self, ) -> str:
    if self.__moving_key__ is None:
      raise MissingVariable(self, '__moving_key__', str)
    if isinstance(self.__moving_key__, str):
      return self.__moving_key__
    raise TypeException('__moving_key__', self.__moving_key__, str)

  def _getTimeoutCallbackKey(self, ) -> str:
    if self.__timeout_key__ is None:
      raise MissingVariable(self, '__timeout_key__', str)
    if isinstance(self.__timeout_key__, str):
      return self.__timeout_key__
    raise TypeException('__timeout_key__', self.__timeout_key__, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @timeLimit.SET
  def _setTimeLimit(self, time: int, **kwargs) -> None:
    if not isinstance(time, int):
      raise TypeException('time', time, int)
    self.__time_limit__ = time

  def _setMovingCallbackKey(self, key: str) -> None:
    if not isinstance(key, str):
      raise TypeException('key', key, str)
    self.__moving_key__ = key

  def _setTimeoutCallbackKey(self, key: str) -> None:
    if not isinstance(key, str):
      raise TypeException('key', key, str)
    self.__timeout_key__ = key

  #  Decorators
  onMoving: KeySetter = _setMovingCallbackKey
  onTimeout: KeySetter = _setTimeoutCallbackKey

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(
      self,
      widget: Widget,
      widgetType: Shiboken,
      **kwargs,
      ) -> Any:
    if not self.hovered:
      raise NotImplementedError
    originPoint: Point2D = widget.contentRectPosition
