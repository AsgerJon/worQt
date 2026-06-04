"""
CADScene is the document model for the drawing app: an ordered collection
of elements (node points, module lines and dimensions). It is a pure
'worktoy' model with no Qt dependency; the canvas renders whatever it holds.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Any


class CADScene(BaseObject):
  """An ordered collection of geometric items defined by coordinates."""

  items = AttriBox[list]()

  def addItem(self, item: Any) -> None:
    """Append a geometric item to the scene."""
    self.items.append(item)

  def clear(self, ) -> None:
    """Remove every item from the scene."""
    self.items.clear()

  def __iter__(self, ) -> Iterator:
    yield from self.items

  def __len__(self, ) -> int:
    return len(self.items)
