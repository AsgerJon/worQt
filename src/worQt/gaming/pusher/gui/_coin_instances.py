"""
CoinInstances subclasses 'QQuick3DInstancing' and tells Qt Quick 3D
where each coin in play is and how it is turned, so one 'Model' draws
them all.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
from PySide6.QtCore import QByteArray
from PySide6.QtQuick3D import QQuick3DInstancing


def sceneTransforms(places: numpy.ndarray,
                    turns: numpy.ndarray) -> numpy.ndarray:
  """The 'sceneTransforms' function returns, for coins at 'places' (mm)
  turned by 'turns' (x y z w) in the machine's frame, the first three
  rows of each one's transform in the scene, a row of twelve each. The
  scene has y up and z toward the player: its x is the machine's -x
  (the machine's x runs to the player's left), its y the machine's z
  and its z the machine's y. That is a turn, not a mirror, so a coin
  keeps its handedness."""
  x, y, z, w = turns[:, 0], turns[:, 1], turns[:, 2], turns[:, 3]
  rows = numpy.empty((len(turns), 3, 3), numpy.float32)
  rows[:, 0, 0] = 1.0 - 2.0 * (y * y + z * z)
  rows[:, 0, 1] = 2.0 * (x * y - z * w)
  rows[:, 0, 2] = 2.0 * (x * z + y * w)
  rows[:, 1, 0] = 2.0 * (x * y + z * w)
  rows[:, 1, 1] = 1.0 - 2.0 * (x * x + z * z)
  rows[:, 1, 2] = 2.0 * (y * z - x * w)
  rows[:, 2, 0] = 2.0 * (x * z - y * w)
  rows[:, 2, 1] = 2.0 * (y * z + x * w)
  rows[:, 2, 2] = 1.0 - 2.0 * (x * x + y * y)
  scene = numpy.empty((len(turns), 3, 4), numpy.float32)
  scene[:, 0, :3] = -rows[:, 0]
  scene[:, 1, :3] = rows[:, 2]
  scene[:, 2, :3] = rows[:, 1]
  scene[:, 0, 3] = -places[:, 0]
  scene[:, 1, 3] = places[:, 2]
  scene[:, 2, 3] = places[:, 1]
  return scene.reshape(-1, 12)


class CoinInstances(QQuick3DInstancing):
  """
  CoinInstances subclasses 'QQuick3DInstancing' and holds, for each coin
  in play, its transform in the scene, white, no data of its own: what
  Qt Quick 3D asks for, 'getInstanceBuffer'. 'setCoins' gives it the
  coins anew and has them drawn so. It is made in Python, with no
  parent; whoever made it keeps it alive.
  """

  def __init__(self, ) -> None:
    QQuick3DInstancing.__init__(self, )
    self.__coin_table__ = QByteArray()
    self.__coin_count__ = 0

  def setCoins(self, places: numpy.ndarray, turns: numpy.ndarray) -> None:
    """The 'setCoins' method has the coins drawn at 'places', in mm in
    the machine's frame, turned by 'turns' (x y z w)."""
    count = len(places)
    table = numpy.zeros((count, 20), numpy.float32)
    table[:, :12] = sceneTransforms(places, turns)
    table[:, 12:16] = 1.0
    self.__coin_table__ = QByteArray(table.tobytes())
    self.__coin_count__ = count
    self.markDirty()

  def getInstanceBuffer(self, ) -> tuple[QByteArray, int]:
    """Qt Quick 3D asks for the coins' table and how many there are."""
    return self.__coin_table__, self.__coin_count__
