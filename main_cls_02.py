"""
LOL
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.ezdata import EZData

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator


class LOL(EZData, frozen=True):
  row = 0
  col = 0
  rowSpan = 1
  colSpan = 1

  cells = Field()

  @cells.GET
  def _getCells(self, ) -> Iterator[int]:
    for item in self:
      yield item
