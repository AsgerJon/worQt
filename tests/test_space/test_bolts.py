"""
TestBolts covers the magic bolts and the gravity gun aiming at them
(user, 2026-11-17: "Let the space station and the rocket have a few
clearly marked 'magic' bolts in the walls floors and ceilings. The
gravity gun can pull Asger towards them"): each on the cabin's floor,
ceiling or wall facing into the room, where it holds him inside the
cabin clear of every solid; the gun points at one he looks at, never
from his chair, never one facing away.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._bolts import holdOf, rocketBolts
from worQt.gaming.space._cabinsolids import solids
from worQt.gaming.space._cockpit import FLOOR, NOSE, WALL, Cockpit
from worQt.gaming.space._cockpit import capsuleRadius

from . import SpaceTest


class TestBolts(SpaceTest):
  """Tests for the magic bolts and aiming the gravity gun."""

  def test_placed(self) -> None:
    """Each bolt is on the floor, the ceiling or the wall, facing into
    the room; on the floor, the ceiling and the wall alike."""
    kinds = set()
    for place, way in rocketBolts():
      self.assertAlmostEqual(math.hypot(*way), 1.0, 9)
      if way[2] > 0.99:
        self.assertAlmostEqual(place[2], FLOOR, 9)
        kinds.add('floor')
      elif way[2] < -0.99:
        self.assertAlmostEqual(place[2], NOSE, 9)
        kinds.add('ceiling')
      else:
        across = math.hypot(place[0], place[1])
        self.assertAlmostEqual(across, capsuleRadius(place[2]) - WALL, 9)
        self.assertLess(way[0] * place[0] + way[1] * place[1], 0.0)
        kinds.add('wall')
    self.assertEqual(kinds, {'floor', 'ceiling', 'wall'})

  def test_held(self) -> None:
    """Where the gun holds him is inside the cabin, half a metre and
    more from its wall, floor and ceiling, outside every solid's
    round."""
    for bolt in rocketBolts():
      hold = holdOf(bolt)
      self.assertLess(math.hypot(hold[0], hold[1]),
                      capsuleRadius(hold[2]) - WALL - 0.5)
      self.assertGreater(hold[2], FLOOR + 0.5)
      self.assertLess(hold[2], NOSE - 0.5)
      for middle, half, _ in solids():
        far = math.dist(hold, middle) - math.sqrt(sum(
          h * h for h in half))
        self.assertGreater(far, 0.0, (bolt, middle))

  def test_aimed(self) -> None:
    """Up, looking at a bolt the gun points at it; sitting, at none."""
    cockpit = Cockpit()
    bolts = rocketBolts()
    self.assertIsNone(cockpit.boltAimed(bolts))
    cockpit.gotUp()
    crewman = cockpit.crewman
    soles = crewman.soles()
    for k, (place, way) in enumerate(bolts):
      flat = math.hypot(place[0] - soles[0], place[1] - soles[1])
      if flat < 0.5:
        continue
      crewman.ahead = ((place[0] - soles[0]) / flat,
                       (place[1] - soles[1]) / flat, 0.0)
      off = tuple(p - e for p, e in zip(place, cockpit.eye()))
      far = math.sqrt(sum(x * x for x in off))
      cockpit.yaw, cockpit.pitch = 0.0, math.asin(off[2] / far)
      self.assertEqual(cockpit.boltAimed(bolts), k, (place, far))
