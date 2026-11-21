"""
TestCollision covers the rocket meeting the space station (a bad
approach passed straight through it: user, 2026-11-17, the station and
"Get the docking!"): the station's solids and the hull's balls (the
kernel's distances checked against the reference); drifting into the
drum's side, the ring (its rim running at 94 m/s), a thin antenna and,
its head in the drum's hole, the hole's wall the rocket bounces off,
never deep in, never through; centred in the hole it meets nothing;
the bump said; far off, the flight is as it was to the bit.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._station import SPIN, Station
from worQt.gaming.space._stationinterior import PLANE
from worQt.gaming.space._stationsolids import CAPSULE, HOLLOW, TORUS
from worQt.gaming.space._stationsolids import hullBalls, hullReach
from worQt.gaming.space._stationsolids import solidDistance
from worQt.gaming.space._stationsolids import stationSolids, sweptDistance
from worQt.gaming.space._turns import norm, quaternionOf
from worQt.gaming.space._turns import rotated
from worQt.gaming.space._vessel import RADIUS, Vessel

from . import FRAME, SpaceTest

#  The deepest a ball may be pressed into a solid, m.
DEEPEST = 0.4


class TestCollision(SpaceTest):
  """Tests for the rocket meeting the space station."""

  __time_out__ = 900.0

  def _drifting(self, own: tuple, axes: tuple, moving: tuple) -> tuple:
    """Returns a system, its station and a vessel at 'own' (the
    station's own axes, m from its middle, at time nought), its own axes
    'axes' (columns: the station's own axes), drifting 'moving' (m/s,
    the station's own axes) from the station's middle, not turning."""
    system = self.systemOf()
    station = Station(system)
    rows = station.turnAt(0.0)
    middle, velocity = station.stateAt(0.0)

    def world(x: tuple) -> tuple:
      return tuple(sum(rows[i][j] * x[j] for j in range(3))
                   for i in range(3))

    columns = tuple(world(c) for c in axes)
    turn = quaternionOf(tuple(tuple(columns[k][i] for k in range(3))
                              for i in range(3)))
    vessel = Vessel()
    vessel.placed(station.parent, tuple(m + x for m, x in zip(
      middle, world(own))), tuple(v + x for v, x in zip(
      velocity, world(moving))), turn, (0.0, 0.0, 0.0))
    return system, station, vessel

  def _ownOf(self, station: Station, vessel: Vessel, t: float,
             x: tuple) -> tuple:
    """Returns where 'x' (the vessel's own axes) is in the station's own
    axes at time 't'."""
    rows = station.turnAt(t)
    middle = station.stateAt(t)[0]
    world = tuple(p + r - m for p, r, m in zip(
      vessel.place, rotated(vessel.turn, x), middle))
    return tuple(sum(rows[i][j] * world[i] for i in range(3))
                 for j in range(3))

  def _flown(self, station: Station, system: object, vessel: Vessel,
             solid: tuple, seconds: float) -> tuple:
    """Flies 'seconds' s a frame at a time meeting the station; returns
    the deepest any ball went into 'solid' (m, nought: never in), the
    hardest bump said and how fast the vessel moves from the station's
    middle at the end, out from its axis and along it (m/s: whatever
    way the station has turned)."""
    flight, t, deepest, bump = self.flightOf(), 0.0, 0.0, 0.0
    balls = hullBalls()
    while t < seconds:
      flight.flown((vessel,), system, t, FRAME, math.inf, station)
      t += FRAME
      bump = max(bump, vessel.bumped)
      for x, y, z, r in balls:
        gap = solidDistance(solid, self._ownOf(station, vessel, t,
                                               (x, y, z))) - r
        deepest = max(deepest, -gap)
    rows = station.turnAt(t)
    middle, velocity = station.stateAt(t)
    at = tuple(sum(rows[i][j] * (p - m) for i, (p, m) in enumerate(zip(
      vessel.place, middle))) for j in range(3))
    moving = tuple(sum(rows[i][j] * (v - s) for i, (v, s) in enumerate(
      zip(vessel.velocity, velocity))) for j in range(3))
    out = (at[0] * moving[0] + at[1] * moving[1]) / math.hypot(at[0],
                                                               at[1])
    return deepest, bump, (out, moving[2])

  def test_shapes(self) -> None:
    """The station: the ring a torus round its axis, the drum a hollow
    cylinder on it, the rest capsules and balls; the hull's balls
    within the rocket's radius, each two along it overlapping (their
    waist some half the smaller one at the nose's blunt cone, where
    they shrink fast, more elsewhere: a thin antenna finds no gap),
    reaching near its nose's tip, not past it; a solid's
    swept distance never more than its distance."""
    solids = stationSolids()
    self.assertLessEqual(len(solids), 32)
    self.assertEqual([s[0] for s in solids[:2]], [TORUS, HOLLOW])
    self.assertTrue(all(s[0] == CAPSULE for s in solids[2:]))
    balls = hullBalls()
    self.assertTrue(all(r <= RADIUS + 1e-9 for _, _, _, r in balls))
    self.assertAlmostEqual(hullReach(), 36.0, 0)
    axial = sorted((z, r) for x, y, z, r in balls if x == y == 0.0)
    for (z0, r0), (z1, r1) in zip(axial, axial[1:]):
      gap = z1 - z0
      along = (gap * gap + r0 * r0 - r1 * r1) / (2.0 * gap)
      waist = math.sqrt(r0 * r0 - along * along)
      self.assertGreater(waist, 0.4 * min(r0, r1), (z0, z1))
    self.assertLessEqual(axial[-1][0] + axial[-1][1], 36.0 + 1e-9)
    self.assertGreater(axial[-1][0] + axial[-1][1], 35.0)
    for solid in solids:
      for point in ((900.0, 30.0, 20.0), (50.0, -40.0, 70.0),
                    (-600.0, 640.0, 5.0), (0.0, 3.0, -300.0)):
        self.assertLessEqual(sweptDistance(solid, point),
                             solidDistance(solid, point) + 1e-9)

  def test_drum(self) -> None:
    """Nose first down onto the drum's face beside its hole at 1 m/s (its
    sides are hidden between the spokes: the rocket is wider than their
    gaps there) it bounces off, never 'DEEPEST' in; the bump said."""
    from worQt.gaming.space._dockingport import NOSE_PORT
    from worQt.gaming.space._stationmeshes import DRUM_HALF
    solid = stationSolids()[1]
    axes = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
    system, station, vessel = self._drifting(
      (8.5, 0.0, DRUM_HALF + 2.0 + NOSE_PORT[2]), axes, (0.0, 0.0, -1.0))
    deepest, bump, moving = self._flown(station, system, vessel, solid,
                                        12.0)
    self.assertGreater(deepest, 0.0)
    self.assertLess(deepest, DEEPEST)
    self.assertGreater(moving[1], 0.2)
    self.assertGreater(bump, 0.5)
    self.assertLess(bump, 1.5)

  def test_socket(self) -> None:
    """Its head in the drum's hole, nose first down the axis as it docks
    (user, 2026-11-19: "the head our rocket insert itself here"):
    centred it meets nothing; drifting across at 0.3 m/s it meets the
    hole's wall and bounces off it, never 'DEEPEST' in; the bump
    said."""
    solid = stationSolids()[1]
    axes = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
    for drift in (0.0, 0.3):
      system, station, vessel = self._drifting(
        (0.0, 0.0, PLANE), axes, (drift, 0.0, 0.0))
      deepest, bump, _ = self._flown(station, system, vessel, solid, 8.0)
      if drift == 0.0:
        self.assertEqual((deepest, bump), (0.0, 0.0))
      else:
        self.assertGreater(deepest, 0.0)
        self.assertLess(deepest, DEEPEST)
        self.assertGreater(bump, 0.1)

  def test_ring(self) -> None:
    """Dropping onto the ring's tube from above at 2 m/s (its rim
    running at 94 m/s under it) it bounces up, never 'DEEPEST' in; the
    rim's rub sets it turning."""
    solid = stationSolids()[0]
    system, station, vessel = self._drifting(
      (solid[1][0], 0.0, 80.0), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                                 (0.0, 0.0, 1.0)), (0.0, 0.0, -2.0))
    deepest, _, moving = self._flown(station, system, vessel, solid, 25.0)
    self.assertGreater(deepest, 0.0)
    self.assertLess(deepest, DEEPEST)
    self.assertGreater(moving[1], 0.3)
    self.assertGreater(norm(vessel.spin), 0.01)

  def test_antenna(self) -> None:
    """Broadside down onto a thin antenna out of the ring at 3 m/s,
    between two of the hull's balls, carried round with it (its speed
    round the axis there matched; the one along the axis is gone: user,
    2026-11-18, the second port), it bounces off, never through."""
    solid = stationSolids()[8]
    _, a, b, radius = solid
    mid = tuple(0.5 * (p + q) for p, q in zip(a, b))
    far = math.hypot(mid[0], mid[1])
    out = (mid[0] / far, mid[1] / far, 0.0)
    across = (-out[1], out[0], 0.0)
    own = tuple(m + (radius + RADIUS + 1.0) * z + 1.0 * c for m, z, c in
                zip(mid, (0.0, 0.0, 1.0), across))
    moving = (-SPIN * own[1], SPIN * own[0], -3.0)
    system, station, vessel = self._drifting(
      own, (out, (0.0, 0.0, -1.0), across), moving)
    deepest, _, moving = self._flown(station, system, vessel, solid, 3.0)
    self.assertGreater(deepest, 0.0)
    self.assertLess(deepest, 1.0)
    self.assertGreater(moving[1], 0.5)

  def test_far(self) -> None:
    """Far from the station the flight is as it was without it, to the
    bit."""
    system, station, one = self._drifting(
      (0.0, 0.0, 5000.0), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                           (0.0, 0.0, 1.0)), (0.0, 0.0, -1.0))
    _, _, two = self._drifting(
      (0.0, 0.0, 5000.0), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                           (0.0, 0.0, 1.0)), (0.0, 0.0, -1.0))
    flight = self.flightOf()
    flight.flown((one,), system, 0.0, 1.0, math.inf, station)
    flight.flown((two,), system, 0.0, 1.0)
    self.assertEqual(one.place, two.place)
    self.assertEqual(one.velocity, two.velocity)
    self.assertEqual(one.bumped, 0.0)
