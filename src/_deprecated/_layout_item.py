"""
LayoutItem encapsulates content assigned to a group of cells, defined by
an instance of 'LayoutIndex', in a grid layout defined by an instance of
'LayoutManager'. Instances wraps either a nested layout or more commonly a
widget. It follows the 'AttriBox' pattern of lazy instantiation.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.mixin import BoxBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class LayoutItem(BoxBase):
  """
  LayoutItem encapsulates content assigned to a group of cells, defined by
  an instance of 'LayoutIndex', in a grid layout defined by an instance of
  'LayoutManager'. Instances wraps either a nested layout or more commonly a
  widget. It follows the 'AttriBox' pattern of lazy instantiation.
  """
  pass
