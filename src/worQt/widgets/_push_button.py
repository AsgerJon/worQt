"""
PushButton subclasses 'AbstractButton' and provides a hover aware push
button.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QPainter
from worktoy.desc import Field

from . import AbstractButton, ButtonFlags, ButtonStates

from typing import TYPE_CHECKING

from ..core import RGBA


class PushButton(AbstractButton):
  """
  PushButton is a subclass of AbstractButton that provides a hover aware
  push button.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getStateFlags(self, ) -> ButtonFlags:
    """
    This base class method reflects only 'hovered' and 'pressed' states.
    Subclasses requiring a more granular state management should
    reimplement this method.
    """
    if self.isEnabled():
      return AbstractButton.getStateFlags(self)
    state = ButtonFlags.NULL
    if self.hovered():
      state |= ButtonFlags.HOVERED
    if self.pressed():
      state |= ButtonFlags.PRESSED
    return state
