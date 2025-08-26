"""
MouseInputNum enumerates the mouse inputs.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import KeeNum, Kee


class MouseInputNum(KeeNum):
  """MouseInputNum enumerates the mouse inputs."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  CLICK = Kee[str]('click')
  HOLD = Kee[str]('hold')
