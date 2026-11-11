"""
Room is the billiard room the game opens in, two tables in it, walked
first person (Qt's own 'WasdController' moves the walker; the room keeps
it on the floor, out of the walls and the tables, and says which table
it is near).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

#  How the tables stand in the room: each game's table, where its cloth's
#  middle is across the room ('x', mm); both along the room's length at
#  its middle, the head end away.
TABLES = (('carom', -2300.0), ('kegler', 2300.0))


class Room(NamedTuple):
  """
  Room is the billiard room, in mm, seen from above as the scene has it:
  'x' across, 'z' along, the head end away (negative), the floor
  'floor' below the cloths; 'halfWidth' and 'halfLength' to the walls,
  the tables where 'TABLES' puts them, each 'tableHalfWidth' by
  'tableHalfLength' to its rails' outer edges. A walker's eyes are 'eye'
  above the floor; it keeps 'keep' from walls and tables, and is near a
  table within 'near' of its rails. A walker comes in at 'door', facing
  the head wall.
  """

  halfWidth: float = 5200.0
  halfLength: float = 4600.0
  floor: float = 800.0
  tableHalfWidth: float = 890.0
  tableHalfLength: float = 1600.0
  keep: float = 280.0
  near: float = 650.0
  eye: float = 1650.0
  door: tuple[float, float] = (0.0, 3600.0)

  def tableAt(self, kind: str) -> tuple[float, float]:
    """The 'tableAt' method returns where the middle of 'kind's table's
    cloth is in the room, 'x' and 'z'."""
    return dict(TABLES)[kind], 0.0

  def kinds(self, ) -> tuple[str, ...]:
    """The 'kinds' method returns the games whose tables stand here."""
    return tuple(kind for kind, _ in TABLES)

  def gapTo(self, kind: str, x: float, z: float) -> float:
    """The 'gapTo' method returns how far 'x', 'z' is from the rails of
    'kind's table, seen from above; nought on it."""
    tx, tz = self.tableAt(kind)
    dx = max(abs(x - tx) - self.tableHalfWidth, 0.0)
    dz = max(abs(z - tz) - self.tableHalfLength, 0.0)
    return math.hypot(dx, dz)

  def kept(self, x: float, z: float) -> tuple[float, float]:
    """The 'kept' method returns 'x', 'z' moved the least way out of the
    walls and the tables, 'keep' clear of each, as the scene keeps the
    walker ('carom.qml' 'keptInRoom', the same sums)."""
    x = min(max(x, -self.halfWidth + self.keep), self.halfWidth - self.keep)
    z = min(max(z, -self.halfLength + self.keep),
            self.halfLength - self.keep)
    for kind in self.kinds():
      tx, tz = self.tableAt(kind)
      reachX = self.tableHalfWidth + self.keep
      reachZ = self.tableHalfLength + self.keep
      inX, inZ = reachX - abs(x - tx), reachZ - abs(z - tz)
      if inX <= 0.0 or inZ <= 0.0:
        continue
      if inX < inZ:
        x = tx + math.copysign(reachX, x - tx or 1.0)
      else:
        z = tz + math.copysign(reachZ, z - tz or 1.0)
    return x, z

  def nearOf(self, x: float, z: float) -> str:
    """The 'nearOf' method returns the game whose table 'x', 'z' is near
    enough to play, within 'near' of its rails; empty when none."""
    gap, kind = min((self.gapTo(kind, x, z), kind) for kind in self.kinds())
    return kind if gap <= self.near else ''

  def beside(self, kind: str) -> tuple[float, float, float, float]:
    """The 'beside' method returns where a player leaving 'kind's table
    stands, at its foot end a step back, facing it: 'x', 'z', and the
    turn of the head, about the vertical and up, in degrees, as the
    scene's camera takes them (nought facing the head wall)."""
    tx, tz = self.tableAt(kind)
    return tx, tz + self.tableHalfLength + self.keep + 300.0, 0.0, -20.0

  def layout(self, ) -> dict:
    """The 'layout' method returns the room as the scene takes it: its
    sizes, and where each table stands across it."""
    return {'halfWidth': self.halfWidth, 'halfLength': self.halfLength,
            'floor': self.floor, 'tableHalfWidth': self.tableHalfWidth,
            'tableHalfLength': self.tableHalfLength, 'keep': self.keep,
            'near': self.near, 'eye': self.eye, 'door': list(self.door),
            'tables': {kind: x for kind, x in TABLES}}
