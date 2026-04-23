"""
MixinSpace provides the namespace class used to create the mixin classes
used throughout the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseSpace

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MixinSpace(BaseSpace):
  """
  MixinSpace provides the namespace class used to create the mixin classes
  used throughout the worQt framework.
  """
