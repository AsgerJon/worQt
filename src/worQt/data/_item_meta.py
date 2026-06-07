"""
ItemMeta subclasses 'BaseMeta' from 'worktoy.mcls' and provides the custom
metaclass for the 'AbstractItem' class.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseMeta

from . import ItemSpace as ISpace

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias

  Bases: TypeAlias = tuple[type, ...]


class ItemMeta(BaseMeta):
  """
  ItemMeta subclasses 'BaseMeta' from 'worktoy.mcls' and provides the
  custom metaclass for the 'AbstractItem' class.
  """

  @classmethod
  def __prepare__(mcls, name: str, bases: Bases, **kwargs) -> ISpace:
    return ISpace(mcls, name, bases, **kwargs)
