"""
CoinShape subclasses 'QQuick3DGeometry' and hands Qt Quick 3D a coin's
triangles, as 'coinMesh' makes them: its top, its bottom and its edge
as three parts, each drawn with its own material.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
from PySide6.QtGui import QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry

from .._coin import Coin
from .._coin_mesh import coinMesh

_SEMANTIC = QQuick3DGeometry.Attribute.Semantic
_FLOAT = QQuick3DGeometry.Attribute.ComponentType.F32Type
_TRIANGLES = QQuick3DGeometry.PrimitiveType.Triangles


def _vector(row: numpy.ndarray) -> QVector3D:
  """'row' as a 'QVector3D'."""
  return QVector3D(float(row[0]), float(row[1]), float(row[2]))


class CoinShape(QQuick3DGeometry):
  """
  CoinShape subclasses 'QQuick3DGeometry' and holds the triangles of a
  'coin' in its own frame, its axis z: each corner where it is, its
  normal and where on its picture, in three parts for a 'Model's three
  materials: the top, the bottom and the edge. It is made in Python,
  with no parent; whoever made it keeps it alive.
  """

  __fallback_segments__ = 252  # corners round the coin
  __fallback_sections__ = 7  # reeded stretches of its edge
  __fallback_share__ = 0.6  # of its stretch of the round each is reeded

  def __init__(self, coin: Coin) -> None:
    QQuick3DGeometry.__init__(self, )
    rows, parts = coinMesh(coin, self.__fallback_segments__,
                           self.__fallback_sections__,
                           self.__fallback_share__)
    self.setStride(32)
    self.setPrimitiveType(_TRIANGLES)
    self.addAttribute(_SEMANTIC.PositionSemantic, 0, _FLOAT)
    self.addAttribute(_SEMANTIC.NormalSemantic, 12, _FLOAT)
    self.addAttribute(_SEMANTIC.TexCoord0Semantic, 24, _FLOAT)
    self.setVertexData(numpy.ascontiguousarray(rows).tobytes())
    low, high = rows[:, :3].min(0), rows[:, :3].max(0)
    self.setBounds(_vector(low), _vector(high))
    for name, (start, count) in zip(('top', 'bottom', 'edge'), parts):
      corners = rows[start:start + count, :3]
      self.addSubset(start, count, _vector(corners.min(0)),
                     _vector(corners.max(0)), name)
    self.update()
