"""
MouseClick encapsulates an accepted mouse click as implemented in the
'MouseButtonState' class.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ...geometry import Point2D
from ...nums import MouseButtonNum

from . import MouseButtonState
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from .. import BaseWidget


class MouseClick(BaseObject):
  """
  MouseClick encapsulates an accepted mouse click as implemented in the
  'MouseButtonState' class.

  Attributes:
    - button (MouseButtonNum): The specific mouse button identified by the
    'MouseButtonNum' enumeration.
    - position (Point2D): The position of the mouse click, represented as a
    'Point2D' object.
    - timeStamp (int): The timestamp of the event completing the click. It
    is given as the number of milliseconds since the host system started.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __mouse_button__ = None
  __cursor_position__ = None
  __click_receiver__ = None
  __press_duration__ = None
  __release_duration__ = None
  __time_stamp__ = None

  #  Public Variables
  button = Field()
  position = Field()
  receiver = Field()
  pressDuration = Field()
  releaseDuration = Field()
  timeStamp = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @button.GET
  def _getButton(self) -> MouseButtonNum:
    return self.__mouse_button__

  @position.GET
  def _getPosition(self) -> Point2D:
    return self.__cursor_position__

  @pressDuration.GET
  def _getPressDuration(self) -> int:
    return self.__press_duration__

  @releaseDuration.GET
  def _getReleaseDuration(self) -> int:
    return self.__release_duration__

  @timeStamp.GET
  def _getTimeStamp(self) -> int:
    return self.__time_stamp__

  @receiver.GET
  def _getReceiver(self) -> BaseWidget:
    return self.__click_receiver__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(MouseButtonNum, Point2D, BaseWidget, int, int, int)
  def __init__(self, *args, ) -> None:
    btn, pos, rec, *times = args
    press, release, stamp = times
    self.__mouse_button__ = btn
    self.__cursor_position__ = pos
    self.__click_receiver__ = rec
    self.__press_duration__ = press
    self.__release_duration__ = release
    self.__time_stamp__ = stamp

  @overload(MouseButtonState, int, int, int)
  def __init__(self, *args, ) -> None:
    state, *times = args[0]
    btn = state.buttonNum
    rel = state.releasePosition
    rec = state.widget
    self.__init__(btn, rel, rec, *times)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
