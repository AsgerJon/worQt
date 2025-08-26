"""
AbstractEvent provides the abstract base class for the custom events in
the custom event system.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import VariableNotNone

from ..nums import KeyMod

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class AbstractEvent(BaseObject):
  """
  AbstractEvent provides the abstract base class for the custom events in
  the custom event system.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __time_stamp__ = None
  __event_type__ = None
  __keyboard_modifiers__: KeyMod = None

  #  Public Variables
  timeStamp = Field()
  eventType = Field()
  keyboardModifiers = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @timeStamp.GET
  def _getTimeStamp(self, ) -> int:
    """
    Returns the time stamp of when this event was created in the
    'BaseWidget' implementation. This is available when this event is
    created on the basis of a 'QInputEvent' object as this class
    implements a timestamp. This time stamp comes from the window system
    and can be assumed to be in milliseconds since some arbitrary fixed
    point in time. Please note that this is *not* since epoch
    (1970-01-01), but is typically since the system booted.
    """
    return self.__time_stamp__

  @eventType.GET
  def _getEventType(self, ) -> QEvent.Type:
    """
    Returns the event type of this event. This is available when this
    event is created on the basis of a 'QEvent' object as this class
    implements an event type. This is typically used to identify the type
    of event that this class represents.
    """
    return self.__event_type__

  @keyboardModifiers.GET
  def _getKeyboardModifiers(self, ) -> KeyMod:
    """
    Returns the keyboard modifiers of this event. This is available when
    this event is created on the basis of a 'QInputEvent' object as this
    class implements keyboard modifiers. This is typically used to
    identify the state of the keyboard when this event was created.
    """
    if self.__keyboard_modifiers__ is None:
      return KeyMod.NULL
    if TYPE_CHECKING:  # pragma: no cover
      assert isinstance(self.__keyboard_modifiers__, KeyMod)
    return self.__keyboard_modifiers__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @timeStamp.SET
  def _setTimeStamp(self, value: int) -> None:
    """Write-once setter for the time stamp."""
    if self.__time_stamp__ is not None:
      raise VariableNotNone('__time_stamp__', self.__time_stamp__)
    self.__time_stamp__ = value

  @eventType.SET
  def _setEventType(self, value: QEvent.Type) -> None:
    """Write-once setter for the event type."""
    if self.__event_type__ is not None:
      raise VariableNotNone('__event_type__', self.__event_type__)
    self.__event_type__ = value

  @keyboardModifiers.SET
  def _setKeyboardModifiers(self, value: KeyMod) -> None:
    """Write-once setter for the keyboard modifiers."""
    if self.__keyboard_modifiers__ is not None:
      name, value = '__keyboard_modifiers__', self.__keyboard_modifiers__
      raise VariableNotNone(name, value)
    if TYPE_CHECKING:  # pragma: no cover
      assert isinstance(value, KeyMod)
    self.__keyboard_modifiers__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  @abstractmethod  # noqa whatevs
  def fromQEvent(cls, event_: QEvent) -> Self:
    """
    Subclasses must implement this method to specify how to instantiate
    based on a QEvent object. Please note that the C++ garbage collection
    system, does *not* rely on reference counting. Thus, it is possible to
    have a python object referencing a garbage-collected C++ object. In
    this case, the application will exit with a segmentation fault. Thus,
    the subclass implementation must collect all necessary information
    when running this method.
    """
