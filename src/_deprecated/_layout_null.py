"""
LayoutNULL subclasses 'LayoutCell' and represents a cell within the bounds
a 'LayoutManager' object, but not occupied by any 'LayoutEntry' object.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.layouts import LayoutCell

if TYPE_CHECKING:  # pragma: no cover
  pass


class LayoutNULL(LayoutCell):
  """
  LayoutNULL subclasses 'LayoutCell' and represents a cell within the bounds
  a 'LayoutManager' object, but not occupied by any 'LayoutEntry' object.
  """

  def __bool__(self, ) -> bool:
    return False
