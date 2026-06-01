"""
MixinSpace is the namespace class used by MixinMeta. It is a straight
subclass of BaseSpace, reserved for MixinMeta-specific space hooks.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.mcls import BaseSpace


class MixinSpace(BaseSpace):
  """
  Namespace for classes constructed by MixinMeta. Inherits behaviour
  from BaseSpace without modification at this stage.
  """
