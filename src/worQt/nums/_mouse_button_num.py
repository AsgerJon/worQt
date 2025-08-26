"""
MouseButtonNum enumerates mouse buttons. Includes 'NULL' for no button
pressed and the following:
#  - LEFT: The left mouse button.
#  - RIGHT: The right mouse button.
#  - MIDDLE: The middle mouse button.
#  - BACK: The back mouse button.
#  - FORWARD: The forward mouse button.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.keenum import KeeNum, Kee


class MouseButtonNum(KeeNum):
  """MouseButtonNum enumerates mouse buttons."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations

  NULL = Kee[Qt.MouseButton](Qt.MouseButton.NoButton)
  LEFT = Kee[Qt.MouseButton](Qt.MouseButton.LeftButton)
  RIGHT = Kee[Qt.MouseButton](Qt.MouseButton.RightButton)
  MIDDLE = Kee[Qt.MouseButton](Qt.MouseButton.MiddleButton)
  BACK = Kee[Qt.MouseButton](Qt.MouseButton.BackButton)
  FORWARD = Kee[Qt.MouseButton](Qt.MouseButton.ForwardButton)

  def __bool__(self, ) -> bool:
    return False if self is type(self).NULL else True
