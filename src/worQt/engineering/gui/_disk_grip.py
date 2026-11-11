"""
DiskGrip records what is selected, or taken hold of, on a 'DiskWidget'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from .. import EdgeNum
from . import GripNum


class DiskGrip(NamedTuple):
  """
  DiskGrip records what is selected, or taken hold of, on a
  'DiskWidget': its 'kind', the 'index' of the support or load it
  belongs to, -1 for none, and the 'edge' it is on, 'None' for the disk
  and its handles.
  """

  kind: GripNum
  index: int
  edge: EdgeNum | None
