"""
MouseButtonStateNum enumerates the possible states of any mouse button.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import KeeNum, Kee

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MouseButtonStateNum(KeeNum):
  """
  MouseButtonStateNum enumerates the possible states of any mouse button.
  """

  RELEASED = Kee[bool](False)
  PRESSED = Kee[bool](True)
