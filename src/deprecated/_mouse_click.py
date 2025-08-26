"""
MouseClick encapsulates an accepted mouse click as implemented in the
'MouseButtonState' class.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

from ...geometry import Point2D

if TYPE_CHECKING:  # pragma: no cover
  from . import MouseButtonState
  from . import MouseButtonState as State
  from ...nums import MouseInputNum, MouseButtonNum
  from ...nums import MouseInputNum as MINum


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
  __button_state__ = None
  __button_num__ = None
  __input_num__ = None
  __cursor_position__ = None
  __time_stamp__ = None

  #  Public Variables
  buttonState = Field()
  buttonNum = Field()
  inputNum = Field()
  position = Field()  # from the releasing event
  timeStamp = Field()  # from the releasing event

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @buttonState.GET
  def _getButtonState(self, **kwargs) -> MouseButtonState:
    return self.__button_state__

  @buttonNum.GET
  def _getButtonNum(self, **kwargs) -> MouseButtonNum:
    return self.__button_state__.buttonNum

  @inputNum.GET
  def _getInputNum(self, **kwargs) -> MouseInputNum:
    return MouseInputNum.CLICK

  @position.GET
  def _getPosition(self, **kwargs) -> Point2D:
    return maybe(self.__cursor_position__, Point2D(-1, -1))

  @timeStamp.GET
  def _getTimeStamp(self, **kwargs) -> int:
    return maybe(self.__time_stamp__, -1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, state: State, inNum: MINum) -> None:
    self.__button_state__ = state
    self.__input_num__ = inNum

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
