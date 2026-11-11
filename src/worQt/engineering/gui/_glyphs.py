"""
The private '_glyphs' module holds the sizes, in pixels, of what a
'DiskWidget' draws around its disk, shared by the painting and by the
widget finding what the mouse is over.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from PySide6.QtCore import QPointF

PLATE = 5.0  # how thick a bearing plate is drawn
TRIANGLE = 18.0  # how deep a support's triangle is
HALF_BASE = 10.0  # half the base of a support's triangle
ROLLER = 3.0  # the radius of a roller
HATCH = 5.0  # how long the strokes of hatched ground are
HANDLE = 8.0  # the side of a resizing handle


def unit(vector: QPointF) -> QPointF:
  """The unit vector along 'vector', or along x for a zero vector."""
  length = math.hypot(vector.x(), vector.y())
  if length:
    return QPointF(vector.x() / length, vector.y() / length)
  return QPointF(1.0, 0.0)


def dot(a: QPointF, b: QPointF) -> float:
  """The dot product of 'a' and 'b'."""
  return a.x() * b.x() + a.y() * b.y()
