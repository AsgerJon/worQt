"""Point subclasses Plane and provides a point in 2D space. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from moreworktoy.attr import Alias
from . import Plane

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class Point(Plane):
  """Point subclasses Plane and provides a point in 2D space."""

  x = Alias(Plane, 'r0')
  y = Alias(Plane, 'r1')
