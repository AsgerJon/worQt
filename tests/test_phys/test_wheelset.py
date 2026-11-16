"""
TestWheelset covers the loop's first vehicle and the rail world rolling
it ('rail._wheelset', 'rail._railworld'; the spec "Trains: the math
first", the first benchmark): the wheelset weighed from its turned
steel, its axle along z, its profile smooth from tread to flange, the
flange meeting the gauge corner 9 mm over; set down on a level
straight it carries its weight and stays; rolling, it keeps its speed
and spins as it rolls; down the stage it reaches the loop's foot at
the closed form's speed (k from its own body), goes round and rolls
back; on a plain circle released from twice its radius, frictionless,
it leaves the rails where the sliding closed form says, and with real
friction it follows rigid rolling until friction can no longer turn
its spin down, then slips and leaves sooner; started off centre on a
straight it
sways at Klingel's wavelength; the rail world hands the rest to its
inner world, renumbered, the wheelset's connections dropped.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys import Assembly, Contact, Fixed, State
from worQt.phys.rail import RAIL_STEP, RailWorld, Ribbon, loop, loopSpan
from worQt.phys.rail import loopStage
from worQt.phys.rail import loopTrack, profileAt, straight, wheelsetBody
from worQt.phys.rail import wheelsetOn
from worQt.phys.rail import _stage, _wheelset

from . import PhysTest

#  A frame, s.
FRAME = 1.0 / 60.0


class _Still:
  """A world that moves nothing (the inner world of a lone wheelset)."""

  def advancedAll(self, assembly: object, states: tuple, seconds: float,
                  start: float = 0.0) -> tuple:
    """Returns 'states' as they are."""
    return states


def _rolled(track: Ribbon, start: State, seconds: float,
            watch: object = None) -> tuple:
    """Returns a lone wheelset rolled 'seconds' on 'track' from 'start',
    frame by frame (calling 'watch(world, state)' after each), and the
    world it rolled in."""
    body = wheelsetBody()
    world = RailWorld(_Still(), track, body)
    assembly = Assembly((body,), ())
    states = (start,)
    for k in range(round(seconds / FRAME)):
      states = world.advancedAll(assembly, states, FRAME, k * FRAME)
      if watch is not None:
        watch(world, states[0])
    return states[0], world


def _k() -> float:
  """Returns the wheelset's own k = Iz / (m r0^2)."""
  body = wheelsetBody()
  return body.inertia[2][2] / (body.mass * _wheelset.RADIUS ** 2)


class TestWheelset(PhysTest):
  """Tests for the wheelset rolling on rails (a minute or so)."""

  __time_out__ = 600.0

  def test_body(self) -> None:
    """Weighed from its turned steel: a tonne near enough, centred, its
    axle along z, its moments those of a body of revolution."""
    body = wheelsetBody()
    self.assertGreater(body.mass, 900.0)
    self.assertLess(body.mass, 1600.0)
    self.assertLess(max(abs(c) for c in body.centre), 1e-9)
    inertia = numpy.array(body.inertia)
    self.assertNear(float(inertia[0, 0]), float(inertia[1, 1]), 1e-6)
    self.assertLess(float(numpy.abs(inertia - numpy.diag(
      numpy.diag(inertia))).max()), 1e-6)
    self.assertLess(float(inertia[2, 2]), float(inertia[0, 0]))
    self.assertGreater(_k(), 0.3)
    self.assertLess(_k(), 0.5)

  def test_profile(self) -> None:
    """The running surface: the tread a 1:20 cone; the root's fillet
    meeting tread and flange without a step in radius or slope (either
    side of each join, 1e-9 m apart: to 1e-5); the flange's face at 70
    degrees; the gauge corner, 14 mm down, met at 9 mm of shift toward
    its rail."""
    self.assertNear(profileAt(0.0)[0], _wheelset.RADIUS, 1e-12)
    self.assertNear(profileAt(0.02)[1], -_wheelset.CONE, 1e-12)
    for join in (_wheelset._ON_TREAD, _wheelset._ON_FLANGE):
      below, above = profileAt(join - 1e-9), profileAt(join + 1e-9)
      self.assertNear(below[0], above[0], 1e-5)
      self.assertNear(below[1], above[1], 1e-5)
    self.assertNear(profileAt(-0.045)[1], -math.tan(math.radians(70.0)),
                    1e-12)
    gy, gz = _wheelset.GAUGE_CORNER
    reach = _wheelset.RADIUS - gz
    met = next(y for y in numpy.arange(0.0, 0.02, 1e-5)
               if profileAt(gy - _wheelset.NOMINAL - y)[0] >= reach)
    self.assertNear(float(met), 0.009, 0.0005)

  def test_standing(self) -> None:
    """Set down on a level straight, still: after a second it has not
    moved a micrometre, its loads carry its weight (the profile's tilt
    and the friction's grip between them, to 1 %), only the rails' tops
    touch."""
    track = Ribbon((straight(50.0),))
    start = wheelsetOn(track, 10.0, 0.0)
    state, world = _rolled(track, start, 1.0)
    moved = numpy.linalg.norm(numpy.array(state.place)
                              - numpy.array(start.place))
    self.assertLess(float(moved), 2e-5)
    loads = world.rolling[0]['loads']
    weight = wheelsetBody().mass * 9.81
    self.assertNear(loads[(1.0, 0)] + loads[(-1.0, 0)], weight,
                    0.01 * weight)
    self.assertEqual(loads[(1.0, 1)] + loads[(-1.0, 1)], 0.0)

  def test_rolling(self) -> None:
    """Rolling at 10 m/s on a level straight: a second on, the same
    speed and the spin it rolls at (v / r0), to 1e-4; still centred."""
    track = Ribbon((straight(100.0),))
    state, world = _rolled(track, wheelsetOn(track, 5.0, 10.0), 1.0)
    speed = math.sqrt(sum(c * c for c in state.velocity))
    spin = math.sqrt(sum(c * c for c in state.spin))
    self.assertNear(speed, 10.0, 1e-3)
    self.assertNear(spin * _wheelset.RADIUS, speed, 1e-4 * speed)
    self.assertLess(abs(state.place[1]), 1e-6)

  def test_stage(self) -> None:
    """Down the stage from where it starts: at the loop's foot its speed
    is the closed form's for its drop and its own k, to 0.2 %; it goes
    round the loop pressing all the way; it climbs short of the far
    platform and comes back toward the loop."""
    track = loopTrack()
    begins, ends = loopSpan()
    start = wheelsetOn(track, _stage.WHEELSET_AT, 0.0)
    seen = {'foot': None, 'least': math.inf, 'far': 0.0, 'back': False}

    def watch(world: RailWorld, state: State) -> None:
      s = world.rolling[0]['s']
      loads = sum(world.rolling[0]['loads'].values())
      speed = math.sqrt(sum(c * c for c in state.velocity))
      if seen['foot'] is None and s >= begins:
        seen['foot'] = (speed, state.place[2])
      if begins + 2.0 < s < ends - 2.0:
        seen['least'] = min(seen['least'], loads)
      if s > seen['far']:
        seen['far'] = s
      elif s < seen['far'] - 5.0:
        seen['back'] = True

    _rolled(track, start, 26.0, watch)
    speed, foot = seen['foot']
    drop = start.place[2] - foot
    self.assertNear(speed, math.sqrt(2.0 * 9.81 * drop / (1.0 + _k())),
                    0.002 * speed)
    self.assertGreater(seen['least'], 1000.0)
    self.assertLess(seen['far'], track.length - _stage.PLATFORM)
    self.assertTrue(seen['back'])

  def test_falls(self) -> None:
    """Frictionless, on a plain circle of 10 m (its centre's path 9.54
    m), started at the foot as fast as a slide from twice that path's
    radius: it slides (its spin kept, none of its speed turned into
    spin) and leaves the rails where the normal force reaches nought, at
    arccos(-2/3) from the bottom (131.8 degrees), to a degree."""
    angle = self._leaving(0.0, 0.0)[0]
    self.assertNear(angle, math.degrees(math.acos(-2.0 / 3.0)), 1.0)

  def test_slips_off(self) -> None:
    """With the rails' friction, released for rolling from twice its
    path's radius: its load follows rigid rolling's, m (v^2/rho + g cos
    theta), to 1 % while friction can turn its spin down with it (from
    15 degrees, past the ringing of the circle's sudden curvature, to
    90); then its load falls under what rolling needs (k m a over
    the friction), the wheel spins on faster than it rolls (by 5 % and
    more) and it leaves before rolling's arccos(-2/(3 + k)): an honest
    wheel on real friction, not the textbook's infinitely grippy one."""
    angle, slip, worst = self._leaving(None, _k())
    self.assertLess(worst, 0.01)
    self.assertGreater(slip, 1.05)
    rolling = math.degrees(math.acos(-2.0 / (3.0 + _k())))
    self.assertLess(angle, rolling - 1.0)
    self.assertGreater(angle, 110.0)

  def _leaving(self, friction: float | None, k: float) -> tuple:
    """Returns where a wheelset leaves a plain 10 m circle, degrees from
    the bottom, started at its foot as fast as from twice its centre's
    path's radius with 'k' (its rails' 'friction', None: as ever), how
    much faster it spins than it rolls then, and how far its load was
    from rigid rolling's from 15 to 90 degrees (a share)."""
    from worQt.phys.rail._railworld import FRICTION
    radius = 10.0
    track = Ribbon((straight(10.0), loop(radius, 0.0), straight(10.0)))
    path = radius - _wheelset.RADIUS
    speed = math.sqrt(2.0 * 9.81 * 2.0 * path / (1.0 + k))
    start = wheelsetOn(track, 9.0, speed)
    body = wheelsetBody()
    world = RailWorld(_Still(), track, body, RAIL_STEP,
                      FRICTION if friction is None else friction)
    assembly, states = Assembly((body,), ()), (start,)
    worst, step = 0.0, 1.0 / 600.0
    for n in range(round(3.0 / step)):
      states = world.advancedAll(assembly, states, step, n * step)
      state, memory = states[0], world.rolling[0]
      s = memory['s']
      if s <= radius:
        continue
      theta = (s - 10.0) / radius
      speedNow = math.sqrt(sum(c * c for c in state.velocity))
      load = sum(memory['loads'].values())
      if math.radians(15.0) < theta < 0.5 * math.pi:
        rolled = speed * speed - 2.0 * 9.81 * (
          state.place[2] - start.place[2]) / (1.0 + k)
        rigid = body.mass * (rolled / path + 9.81 * math.cos(theta))
        worst = max(worst, abs(load - rigid) / rigid)
      if load <= 0.0:
        spin = math.sqrt(sum(c * c for c in state.spin))
        return (math.degrees(theta), spin * _wheelset.RADIUS / speedNow,
                worst)
    self.fail('it never left the rails')

  def test_klingel(self) -> None:
    """Started 2 mm off centre at 3 m/s on a long straight, it sways at
    Klingel's wavelength 2 pi sqrt(r0 b0 / lambda) (16.5 m), to 5 %."""
    track = Ribbon((straight(200.0),))
    start = wheelsetOn(track, 5.0, 3.0)
    start = State((start.place[0], start.place[1] + 0.002,
                   start.place[2]), start.turn, start.velocity, start.spin)
    crossings = []
    last = {'y': start.place[1]}

    def watch(world: RailWorld, state: State) -> None:
      y = state.place[1]
      if last['y'] > 0.0 >= y or last['y'] < 0.0 <= y:
        crossings.append(state.place[0])
      last['y'] = y

    _rolled(track, start, 14.0, watch)
    self.assertGreater(len(crossings), 4)
    wavelength = 2.0 * float(numpy.mean(numpy.diff(crossings[:5])))
    expected = 2.0 * math.pi * math.sqrt(
      _wheelset.RADIUS * _wheelset.NOMINAL / _wheelset.CONE)
    self.assertNear(wavelength, expected, 0.05 * expected)

  def test_split(self) -> None:
    """The stage in the rail world: the inner world gets the walker and
    the island, renumbered, the wheelset kept back; a contact to the
    wheelset (a ball given) is dropped."""
    assembly, states = loopStage()
    seen = {}

    class Inner:
      def advancedAll(self, inner: Assembly, given: tuple,
                      seconds: float, start: float = 0.0) -> tuple:
        seen['inner'] = inner
        return given

    world = RailWorld(Inner(), loopTrack(), wheelsetBody())
    touching = Assembly(assembly.bodies, assembly.connections
                        + (Contact(1, 0),))
    world.advancedAll(touching, states, FRAME)
    inner = seen['inner']
    self.assertEqual(len(inner.bodies), 3)
    self.assertNotIn(wheelsetBody(), inner.bodies)
    kinds = sorted((type(c).__name__, getattr(c, 'body', None),
                    getattr(c, 'first', None), getattr(c, 'second', None))
                   for c in inner.connections)
    self.assertEqual(kinds, [('Contact', None, 0, 1),
                             ('Contact', None, 0, 2),
                             ('Fixed', 1, None, None),
                             ('Fixed', 2, None, None)])
    self.assertIsInstance(inner.connections[0], (Fixed, Contact))
