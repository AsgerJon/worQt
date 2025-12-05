"""
BaseObject subclasses the 'Object' class from 'moreworktoy.core' using
the 'BaseMeta' metaclass from 'worktoy.mcls'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.mcls import BaseMeta

from ..core import Object


class BaseObject(Object, metaclass=BaseMeta):
  """
  BaseObject subclasses the 'Object' class from 'moreworktoy.core' using
  the 'BaseMeta' metaclass from 'worktoy.mcls'.
  """
