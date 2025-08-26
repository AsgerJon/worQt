"""
TimerBox provides QTimer objects to owning instances.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from worktoy.core import Object
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.dispatch import overload
from worktoy.utilities import maybe
from worktoy.waitaminute import VariableNotNone

from worQt.desQt import Etc


class TimerBox(BaseObject):
  """
  TimerBox provides QTimer objects to owning instances.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()

  #  Fallback Variables
  __fallback_type__ = Qt.TimerType.PreciseTimer
  __fallback_interval__ = 1000

  #  Private Variables
  __timer_type__ = None
  __timeout_interval__ = None

  #  Public Variables
  timerType = Field()
  timeoutInterval = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @timerType.GET
  def _getTimerType(self) -> Qt.TimerType:
    """Get the timer type."""
    return maybe(self.__timer_type__, self.__fallback_type__)

  @timeoutInterval.GET
  def _getTimeoutInterval(self) -> int:
    """Get the timeout interval."""
    return maybe(self.__timeout_interval__, self.__fallback_interval__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @timerType.SET
  def _setTimerType(self, type_: Qt.TimerType) -> None:
    if self.__timer_type__ is not None:
      raise VariableNotNone('__timer_type__', self.__timer_type__)
    self.__timer_type__ = type_

  @timeoutInterval.SET
  def _setTimeoutInterval(self, interval: int) -> None:
    if self.__timeout_interval__ is not None:
      name, value = '__timeout_interval__', self.__timeout_interval__
      raise VariableNotNone(name, value)
    self.__timeout_interval__ = interval

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, Qt.TimerType)
  def __init__(self, interval: int, type_: Qt.TimerType) -> None:
    self.__timer_type__ = type_
    self.__timeout_interval__ = interval

  @overload(Qt.TimerType, int)
  def __init__(self, type_: Qt.TimerType, interval: int) -> None:
    self.__timer_type__ = type_
    self.__timeout_interval__ = interval

  @overload(int)
  def __init__(self, interval: int) -> None:
    self.__timeout_interval__ = interval

  @overload()
  def __init__(self, ) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, *args, **kwargs) -> QTimer:
    pvtName = self.getPrivateName()
    if hasattr(self.instance, pvtName):
      return getattr(self.instance, pvtName)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, pvtName, self._createTimer())
    return self.__instance_get__(_recursion=True)

  def _createTimer(self) -> QTimer:
    timer = QTimer(self.instance)
    timer.setTimerType(self.timerType)
    timer.setInterval(self.timeoutInterval)
    timer.setSingleShot(True)
    return timer
  
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
