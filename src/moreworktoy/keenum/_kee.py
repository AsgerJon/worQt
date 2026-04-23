"""
Kee now type hints in '__get__' to the owning class.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import Kee as __old_kee__

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, TypeVar

  T = TypeVar('T')


class Kee(__old_kee__):
  """
  Kee now type hints in '__get__' to the owning class.
  """

  def __get__(self, instance: Any, owner: Type[T], **kwargs) -> T:
    return super().__get__(instance, owner, **kwargs)
