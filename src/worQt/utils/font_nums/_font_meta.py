"""
FontMeta subclasses 'KeeMeta' and implements '_resolveMember' to allow
derived classes to manually provide a resolution method for members. This
is done by implementing a classmethod called 'resolve'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeMeta
from worktoy.waitaminute.keenum import KeeResolveError

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class FontMeta(KeeMeta):
  """
  FontMeta subclasses 'KeeMeta' and implements '_resolveMember' to allow
  derived classes to manually provide a resolution method for members. This
  is done by implementing a classmethod called 'resolve'.
  """

  def __instancecheck__(cls, instance) -> bool:
    for member in cls:
      if instance is member:
        return True
    for member in cls:
      if instance == member.value:
        return True
    return False

  def _resolveMember(cls, identifier: Any, **kwargs) -> Any:
    classResolve = getattr(cls, '__class_resolve__', None)
    if classResolve is not None:
      try:
        return classResolve(identifier)
      except KeeResolveError:
        pass
    return super()._resolveMember(identifier, **kwargs)
