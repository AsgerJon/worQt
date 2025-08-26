"""
ButtonStates enumerates button states for button widgets.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import KeeNum, Kee


class ButtonStates(KeeNum):
  """
  ButtonStates enumerates button states for button widgets.
  """

  #  Enumerations
  ENABLED = Kee[str]('enabled')
  HOVERED = Kee[str]('hovered')
  PRESSED = Kee[str]('pressed')
  CHECKED = Kee[str]('checked')
