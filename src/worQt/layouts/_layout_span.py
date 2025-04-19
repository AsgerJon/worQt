"""LayoutSpan class for managing layout spans in a grid layout."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import Field

from . import LayoutIndex

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class LayoutSpan(LayoutIndex):
  """LayoutSpan class for managing layout spans in a grid layout."""

  nRows = Field()
  nCols = Field()
  colSpan = Field()
  rowSpan = Field()

  @rowSpan.GET
  @nRows.GET
  def _getNRows(self) -> int:
    """Get the number of rows in the span."""
    return self.row

  @colSpan.GET
  @nCols.GET
  def _getNCols(self) -> int:
    """Get the number of columns in the span."""
    return self.col

  def __len__(self) -> int:
    """Get the number of rows and columns in the span."""
    return self.nRows * self.nCols

  def __abs__(self) -> int:
    """Get the absolute value of the span."""
    return max(self.nRows ** 2, self.nCols ** 2) ** 0.5
