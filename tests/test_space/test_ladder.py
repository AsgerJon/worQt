"""
TestLadder covers the handles (user, 2026-11-19: "My intention was for
handles to stretch where Asger might wanna go when in microgravity. When
Asger is in ladder mode, no more physics. Asger just moves through the
ladder system"): the runs join (the ladder's foot to the cabin's runs,
its top to the four doors', each door's to its cage's) and run through
the rooms, his box clear of the walls all along; the handrails hang
overhead, out of a walking man's way; he takes hold only of a handle he
aims at, within reach; on them W carries him the way he looks (the
ladder up looking across it, and it stops at its top), S the other
way, at a joint on
along the run nearest that way; a shut door stops him short of its
leaf, an open one lets him over the gap, into the cage only while it is
at the drum; and on them nothing else moves him: the cabin's world
leaves him where they put him, even pulled at one g.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._crewman import TALL, WIDE
from worQt.gaming.space._elevator import CAR_HIGH, HANDLE_ASIDE, HUB_STOP
from worQt.gaming.space._ladder import CAGE_IN, DOOR_OUT, DOOR_STOP
from worQt.gaming.space._ladder import FOOT_SPOT, RAIL_UP, REACH, RUNS
from worQt.gaming.space._ladder import SPEED, TOP_SPOT, Ladder, lengthOf
from worQt.gaming.space._ladder import handleOf, railsOf, spotOf
from worQt.gaming.space._levels import DOOR_WAYS, FLOOR, HEAD, LEVELS
from worQt.gaming.space._levels import WALL
from worQt.gaming.space._stationinterior import roomsInside, shaftWays

from . import FRAME, SpaceTest

#  Asger's legs at rest.
STILL = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0))
#  The docked rocket's own axes in the station's (the debug warp's).
RELATIVE = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
#  Every door open, shut; every cage at the drum, none.
OPEN, SHUT = (True,) * 4, (False,) * 4
#  A cage's handrail's offset from its run (docked as 'RELATIVE': the
#  station's z is the rocket's -z).
ASIDE = (0.0, 0.0, -HANDLE_ASIDE)


class TestLadder(SpaceTest):
  """Tests for the handles."""

  #  The cabin's kernels on the CPU.
  __time_out__ = 900.0

  def _run(self, kind: str, k: int = -1) -> int:
    """Returns the index of the run of 'kind' (and door 'k')."""
    return next(on for on, run in enumerate(RUNS)
                if run[2] == kind and run[3] == k)

  def _went(self, ladder: Ladder, ask: int, look: tuple, seconds: float,
            docked: bool = True, opened: tuple = OPEN,
            home: tuple = OPEN) -> None:
    """Moves 'ladder' 'seconds' s on a frame at a time, 'ask' asked,
    looking 'look'."""
    for _ in range(int(round(seconds / FRAME))):
      ladder.moved(FRAME, ask, look, docked, opened, home)

  def test_joined(self) -> None:
    """The ladder runs from the cabin's foot to the top floor's middle;
    the cabin's runs start at its foot, the doors' at its top, each
    cage's at its door's end, along its way."""
    ladder = RUNS[self._run('ladder')]
    self.assertEqual(ladder[0], FOOT_SPOT)
    self.assertEqual(ladder[1], TOP_SPOT)
    for start, end, kind, k in RUNS:
      if kind == 'cabin':
        self.assertEqual(start, FOOT_SPOT)
      if kind == 'door':
        self.assertEqual(start, TOP_SPOT)
        self.assertAlmostEqual(math.hypot(*end[:2]), DOOR_OUT, 9)
      if kind == 'cage':
        self.assertEqual(start, RUNS[self._run('door', k)][1])
        self.assertAlmostEqual(math.hypot(*end[:2]), CAGE_IN, 9)
        self.assertGreater(CAGE_IN, HUB_STOP - CAR_HIGH + 0.5 * WIDE)

  def test_rooms(self) -> None:
    """Along every run (docked, the cages at the drum) his box is in the
    rooms: as deep as its half width at its middle, and its head and
    soles in them too."""
    ways = shaftWays(RELATIVE)
    cages = ((HUB_STOP - CAR_HIGH - 0.3, HUB_STOP + 0.3),) * 4
    for on in range(len(RUNS)):
      long = lengthOf(on)
      for k in range(21):
        middle = spotOf(on, long * k / 20.0)
        for lift in (0.0, 0.5 * TALL - 0.05, -0.5 * TALL + 0.05):
          point = (middle[0], middle[1], middle[2] + lift)
          depth = roomsInside(point, True, ways, cages)
          least = 0.5 * WIDE if lift == 0.0 else 0.0
          self.assertGreater(depth, least, (RUNS[on][2], k, lift))

  def test_rails(self) -> None:
    """The handrails hang overhead, over a standing man's head (he walks
    under them), under the ceilings."""
    for middle, half, axes in railsOf()[2:]:
      low = middle[2] - sum(abs(a[2]) * h for a, h in zip(axes, half))
      self.assertGreater(low, FLOOR + TALL - 0.05)
      if middle[2] > LEVELS[2][0]:
        self.assertGreater(low, LEVELS[2][0] + TALL - 0.05)
    self.assertGreater(min(RAIL_UP), 0.5 * TALL)

  def test_aimed(self) -> None:
    """He takes hold only of a handle he aims at within 'REACH' (user,
    2026-11-19: "Make it so you have to aim at the handles!"): the
    ladder looked at from before it, where his look meets it; looking
    past it or from too far, none; a handrail looked up at, its run; a
    cage's handrail only while the cage is there."""
    ladder = Ladder()
    eye = (FOOT_SPOT[0] - 0.6, 0.0, FOOT_SPOT[2] + 1.0)
    on, along = ladder.aimed(eye, (1.0, 0.0, 0.0), False, SHUT, SHUT,
                             ASIDE)
    self.assertEqual(RUNS[on][2], 'ladder')
    self.assertAlmostEqual(along, 1.0, 6)
    self.assertIsNone(ladder.aimed(eye, (0.0, 1.0, 0.0), False, SHUT,
                                   SHUT, ASIDE))
    far = (-REACH - 0.3, 0.0, eye[2])
    self.assertIsNone(ladder.aimed(far, (1.0, 0.0, 0.0), False, SHUT,
                                   SHUT, ASIDE))
    chair = self._run('cabin')
    start, end = handleOf(chair, ASIDE)[:2]
    under = tuple(0.5 * (p + q) for p, q in zip(start, end))
    eye = (under[0], under[1], under[2] - 1.0)
    on, _ = ladder.aimed(eye, (0.0, 0.0, 1.0), False, SHUT, SHUT, ASIDE)
    self.assertEqual(on, chair)
    self.assertIsNone(ladder.aimed(eye, (1.0, 0.0, 0.0), False, SHUT,
                                   SHUT, ASIDE))
    cage = self._run('cage', 0)
    start, end = handleOf(cage, ASIDE)[:2]
    rail = tuple(0.5 * (p + q) for p, q in zip(start, end))
    eye = (rail[0], rail[1] - 0.8, rail[2])
    self.assertIsNone(ladder.aimed(eye, (0.0, 1.0, 0.0), True, OPEN,
                                   SHUT, ASIDE))
    on, _ = ladder.aimed(eye, (0.0, 1.0, 0.0), True, OPEN, OPEN, ASIDE)
    self.assertEqual(on, cage)

  def test_up_and_down(self) -> None:
    """Looking across the ladder (at it), W climbs it at 'SPEED' to the
    top floor and stops there, held W or not; S back down to the cabin's
    floor, and stops there."""
    ladder = Ladder()
    ladder.taken(self._run('ladder'), 0.0)
    self._went(ladder, 1, (1.0, 0.0, 0.0), 1.0)
    self.assertAlmostEqual(ladder.spot[2], FOOT_SPOT[2] + SPEED, 6)
    self._went(ladder, 1, (1.0, 0.0, 0.0), 8.0)
    self.assertLess(math.dist(ladder.spot, TOP_SPOT), 1e-9)
    self._went(ladder, -1, (1.0, 0.0, 0.0), 8.0)
    self.assertLess(math.dist(ladder.spot, FOOT_SPOT), 1e-9)

  def test_doors(self) -> None:
    """From the ladder's top, W looking at door nought: shut, it stops him
    with his front short of its leaf; open, over the gap to the run's end
    (its cage away: no further); its cage there, into the cage; S looking
    the same way, back out of it, straight on through the top floor's
    middle, out of door two and into its cage."""
    ladder = Ladder()
    ladder.taken(self._run('ladder'), lengthOf(self._run('ladder')))
    way = DOOR_WAYS[0]
    self._went(ladder, 1, way, 5.0, True, SHUT, SHUT)
    out = ladder.spot[0]
    self.assertAlmostEqual(out, DOOR_STOP, 6)
    self.assertLess(out + 0.5 * WIDE, HEAD - WALL)
    self._went(ladder, 1, way, 5.0, True, OPEN, SHUT)
    self.assertAlmostEqual(ladder.spot[0], DOOR_OUT, 6)
    self._went(ladder, 1, way, 5.0, True, OPEN, OPEN)
    self.assertAlmostEqual(ladder.spot[0], CAGE_IN, 6)
    self.assertEqual(RUNS[ladder.on][2:], ('cage', 0))
    self._went(ladder, -1, way, 8.0, True, OPEN, OPEN)
    self.assertLess(math.dist(ladder.spot, (-CAGE_IN, 0.0, TOP_SPOT[2])),
                    1e-6)

  def test_turned(self) -> None:
    """At the ladder's top, W looking at door one goes to door one; from
    the cabin's foot, W looking at the daybed's end goes there."""
    ladder = Ladder()
    ladder.taken(self._run('ladder'), lengthOf(self._run('ladder')))
    self._went(ladder, 1, DOOR_WAYS[1], 1.0, True, SHUT, SHUT)
    self.assertEqual(RUNS[ladder.on][2:], ('door', 1))
    ladder.taken(self._run('ladder'), 0.0)
    for on, (start, end, kind, _) in enumerate(RUNS):
      if kind != 'cabin':
        continue
      ladder.taken(self._run('ladder'), 0.0)
      look = tuple(e - s for s, e in zip(start, end))
      size = math.hypot(*look)
      look = tuple(x / size for x in look)
      self._went(ladder, 1, look, 6.0, False, SHUT, SHUT)
      self.assertEqual(ladder.on, on)
      self.assertLess(math.dist(ladder.spot, end), 1e-9)

  def test_no_physics(self) -> None:
    """On the handles, pulled at one g, the cabin's world leaves him where
    they put him (no physics); let go, he falls."""
    world = CabinWorld('cpu')
    meter = self.stillMeter()
    meter.felt = (0.0, 0.0, G0)
    cockpit = Cockpit()
    cockpit.gotUp()
    crewman = cockpit.crewman
    ladder = Ladder()
    ladder.taken(self._run('ladder'), 1.5)
    crewman.climbing = True
    crewman.middle, crewman.velocity = ladder.spot, (0.0, 0.0, 0.0)
    crewman.up = (0.0, 0.0, 1.0)
    for _ in range(int(round(1.0 / FRAME))):
      world.stepped(FRAME, meter, crewman, STILL)
    self.assertEqual(crewman.middle, ladder.spot)
    crewman.climbing = False
    for _ in range(int(round(0.3 / FRAME))):
      crewman.righted(meter.pullAt(crewman.middle, crewman.velocity),
                      FRAME)
      world.stepped(FRAME, meter, crewman, STILL)
    self.assertLess(crewman.middle[2], ladder.spot[2] - 0.2)
