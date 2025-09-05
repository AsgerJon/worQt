"""
PartClick encapsulates a part of a click event. A double click would
contain two 'PartClick' objects one for each click.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QMouseEvent
from worktoy.desc import Field
from worktoy.mcls import BaseObject

from ..geometry import Point2D
from . import MouseButtonNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union


class PartClick(BaseObject):
  """
  PartClick encapsulates a part of a click event. A double click would
  contain two 'PartClick' objects one for each click.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __press_button__ = None
  __press_modifiers__ = None
  __press_position__ = None
  __press_time_stamp__ = None
  __release_button__ = None
  __release_modifiers__ = None
  __release_position__ = None
  __release_time_stamp__ = None

  #  Public Variables
  pressButton = Field()
  pressModifiers = Field()
  pressPosition = Field()
  pressMoment = Field()
  releaseButton = Field()
  releaseModifiers = Field()
  releasePosition = Field()
  releaseMoment = Field()

  #  Virtual Variables
  drift = Field()
  pressMove = Field()
  releaseMove = Field()

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, event_: QMouseEvent) -> None:
    """Initializes the moment mouse button is pressed. """
    self.__mouse_button__ = MouseButtonNum.fromValue(event_.button())
    self.__key_modifiers__ = KeyMod.fromValue(event_.modifiers())
    self.__press_position__ = Point2D(event_.position())
    self.__press_time_stamp__ = event_.timestamp()

  def release(self, event_: QMouseEvent) -> None:
    """Updates the moment the mouse button releases. """
    self.__release_position__ = Point2D(event_.position())
    self.__release_time_stamp__ = event_.timestamp()
