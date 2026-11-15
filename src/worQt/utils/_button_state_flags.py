"""
ButtonStateFlags subclasses 'KeeFlags' from the 'worktoy.keenum' package
enumerating the possible button states. A state combines flags - a
disabled button can still be hovered - and, like any 'KeeFlags', it is
falsy only when no flag is set.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeFlags, Kee

if TYPE_CHECKING:  # pragma: no cover, no mutate
  pass


class ButtonStateFlags(KeeFlags):
  """
  ButtonStateFlags subclasses 'KeeFlags' from the 'worktoy.keenum' package
  enumerating the possible button states.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  HOVERED = Kee[str]()
  PRESSED = Kee[str]()
  DISABLED = Kee[str]()
