"""
FontMeta subclasses 'KeeMeta' and implements '_resolveMember' to allow
derived classes to manually provide a resolution method for members. This
is done by implementing a classmethod called 'resolve'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeMeta
from worktoy.waitaminute.keenum import KeeValueError

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

  @classmethod
  def _resolveMember(cls, identifier: Any) -> Any:
    try:
      classResolve = getattr(cls, '__class_resolve__')
    except AttributeError:
      pass
    else:
      try:
        return classResolve(identifier)
      except KeeValueError:
        pass
    return super()._resolveMember(identifier)
