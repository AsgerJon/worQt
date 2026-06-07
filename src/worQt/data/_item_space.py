"""
ItemSpace subclasses 'BaseSpace' from 'worktoy.mcls' and provides the
custom namespace class for the 'ItemMeta' metaclass.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseSpace

from . import ItemSpaceHook

if TYPE_CHECKING:  # pragma: no cover
  pass


class ItemSpace(BaseSpace):
  """
  ItemSpace subclasses 'BaseSpace' from 'worktoy.mcls' and provides the
  custom namespace class for the 'ItemMeta' metaclass.
  """

  itemSpaceHook: ItemSpaceHook = ItemSpaceHook()
