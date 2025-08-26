"""
ButtonFlags enumerates button states as combinations of the
following flags:
- ENABLED: The button is enabled.
- HOVERED: The button is hovered.
- PRESSED: The button is pressed.
- CHECKED: The button is checked.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeFlags, Kee

if TYPE_CHECKING:  # pragma: no cover
  pass


class ButtonFlags(KeeFlags):
  """
  ButtonFlags enumerates button states as combinations of the
  following flags:
  - ENABLED: The button is enabled.
  - HOVERED: The button is hovered.
  - PRESSED: The button is pressed.
  - CHECKED: The button is checked.
  """

  #  Flags
  ENABLED = Kee[int](2 ** 0)
  HOVERED = Kee[int](2 ** 1)
  PRESSED = Kee[int](2 ** 2)
  CHECKED = Kee[int](2 ** 3)
