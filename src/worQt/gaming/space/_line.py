"""
Line hands Qt Quick 3D a line through points made in Python: an orbit's
path on the map.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry

_SEMANTIC = QQuick3DGeometry.Attribute.Semantic
_FLOAT = QQuick3DGeometry.Attribute.ComponentType.F32Type
_STRIP = QQuick3DGeometry.PrimitiveType.LineStrip


class Line(QQuick3DGeometry):
  """
  Line is a line strip for Qt Quick 3D through 'points' (rows of three
  numbers, in order; a closed path repeats its first at its end),
  'pointed' anew as it moves. Made with no parent: whoever made it keeps
  it alive.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, points: object) -> None:
    QQuick3DGeometry.__init__(self, )
    self.setStride(12)
    self.setPrimitiveType(_STRIP)
    self.addAttribute(_SEMANTIC.PositionSemantic, 0, _FLOAT)
    self.pointed(points)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def pointed(self, points: object) -> None:
    """The 'pointed' method runs the line through 'points' instead."""
    rows = numpy.ascontiguousarray(points, numpy.float32).reshape(-1, 3)
    self.setVertexData(QByteArray(rows.tobytes()))
    if len(rows):
      low, high = rows.min(0), rows.max(0)
    else:
      low = high = numpy.zeros(3, numpy.float32)
    self.setBounds(QVector3D(*(float(x) for x in low)),
                   QVector3D(*(float(x) for x in high)))
    self.update()
