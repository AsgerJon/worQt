"""
Prism subclasses 'QQuick3DGeometry' and hands Qt Quick 3D triangles, as
'prismMesh' makes them: a piece of the table, or a ball's trail.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
from PySide6.QtGui import QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry

_SEMANTIC = QQuick3DGeometry.Attribute.Semantic
_FLOAT = QQuick3DGeometry.Attribute.ComponentType.F32Type
_TRIANGLES = QQuick3DGeometry.PrimitiveType.Triangles


class Prism(QQuick3DGeometry):
  """
  Prism subclasses 'QQuick3DGeometry' and holds 'mesh', triangles a row
  a corner, its place then its normal, as 'prismMesh' returns them, for
  a 'Model' in the scene to draw; 'setMesh' gives it others, the model
  drawing them at once, none drawing nothing. It is made in Python, with
  no parent; whoever made it keeps it alive.
  """

  def __init__(self, mesh: numpy.ndarray) -> None:
    QQuick3DGeometry.__init__(self, )
    self.setStride(24)
    self.setPrimitiveType(_TRIANGLES)
    self.addAttribute(_SEMANTIC.PositionSemantic, 0, _FLOAT)
    self.addAttribute(_SEMANTIC.NormalSemantic, 12, _FLOAT)
    self.setMesh(mesh)

  def setMesh(self, mesh: numpy.ndarray) -> None:
    """The 'setMesh' method has the model draw the triangles 'mesh'
    instead."""
    rows = numpy.ascontiguousarray(mesh, numpy.float32).reshape(-1, 6)
    self.setVertexData(rows.tobytes())
    if len(rows):
      low, high = rows[:, :3].min(0), rows[:, :3].max(0)
    else:
      low = high = numpy.zeros(3, numpy.float32)
    self.setBounds(QVector3D(float(low[0]), float(low[1]), float(low[2])),
                   QVector3D(float(high[0]), float(high[1]),
                             float(high[2])))
    self.update()
