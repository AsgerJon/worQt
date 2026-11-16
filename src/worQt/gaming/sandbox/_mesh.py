"""
Mesh hands Qt Quick 3D a mesh made in Python ('_bodymesh').
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
_INDEX = QQuick3DGeometry.Attribute.ComponentType.U32Type
_TRIANGLES = QQuick3DGeometry.PrimitiveType.Triangles


class Mesh(QQuick3DGeometry):
  """
  Mesh is triangles for Qt Quick 3D: 'rows' of six numbers a corner (its
  place and its normal), or eight (and where it lies on a picture, from
  the picture's bottom left: a skin's), and 'indices', three rows a
  triangle. Made with no parent: whoever made it keeps it alive.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, rows: numpy.ndarray, indices: numpy.ndarray) -> None:
    QQuick3DGeometry.__init__(self, )
    rows = numpy.ascontiguousarray(rows, numpy.float32)
    if rows.ndim != 2 or rows.shape[1] not in (6, 8):
      raise ValueError('a mesh wants six or eight numbers a corner, not '
                       '%r' % (rows.shape,))
    self.setStride(4 * rows.shape[1])
    self.setPrimitiveType(_TRIANGLES)
    self.addAttribute(_SEMANTIC.PositionSemantic, 0, _FLOAT)
    self.addAttribute(_SEMANTIC.NormalSemantic, 12, _FLOAT)
    if rows.shape[1] == 8:
      self.addAttribute(_SEMANTIC.TexCoord0Semantic, 24, _FLOAT)
    self.addAttribute(_SEMANTIC.IndexSemantic, 0, _INDEX)
    self.setVertexData(QByteArray(rows.tobytes()))
    self.setIndexData(QByteArray(numpy.ascontiguousarray(
      indices, numpy.uint32).tobytes()))
    if len(rows):
      low, high = rows[:, :3].min(0), rows[:, :3].max(0)
    else:
      low = high = numpy.zeros(3, numpy.float32)
    self.setBounds(QVector3D(*(float(x) for x in low)),
                   QVector3D(*(float(x) for x in high)))
    self.update()
