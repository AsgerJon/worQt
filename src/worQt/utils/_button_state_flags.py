"""
ButtonStateFlags subclasses 'KeeFlags' from the 'worktoy.keenum' package
enumerating the possible button states.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeFlags, KeeFlag

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Union, Optional


class ButtonStateFlags(KeeFlags):
  """
  ButtonStateFlags subclasses 'KeeFlags' from the 'worktoy.keenum' package
  enumerating the possible button states.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  HOVERED = KeeFlag()
  PRESSED = KeeFlag()
  DISABLED = KeeFlag()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __bool__(self, ) -> bool:
    return True if 1 << self.DISABLED.value & self.value else False
