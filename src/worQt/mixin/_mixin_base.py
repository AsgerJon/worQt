"""
MixinBase subclasses 'BaseObject' from 'worktoy.mcls' but derives from
'MixinMeta' rather than from 'BaseMeta'. Thus, it brings the functionality
from 'BaseObject' to Qt-derived classes, leveraging 'MixinMeta' to
overcome the metaclass related conflict trolling.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject
from . import MixinMeta

if TYPE_CHECKING:  # pragma: no cover
  pass


class MixinBase(BaseObject, metaclass=MixinMeta):
  """
  MixinBase subclasses 'BaseObject' from 'worktoy.mcls' but derives from
  'MixinMeta' rather than from 'BaseMeta'. Thus, it brings the functionality
  from 'BaseObject' to Qt-derived classes, leveraging 'MixinMeta' to
  overcome the metaclass related conflict trolling.
  """
