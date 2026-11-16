"""
TestTurnout covers the points ('Turnout', user, 2026-11-16: "do all the
things", the points among them) and the way they send a wheelset
('wayOf'): the way's pieces behind and ahead as the points are set, a
branch's way back onto its track behind the points, the tracks' ends;
a turnout joining a track to itself, or a branch not beginning at its
points, refused; a lone wheelset rolling at 3 m/s through the points
stays on the line or takes the branch as they are set, its wheels on
that track's rails, in plain Python and in the kernel alike; one
rolling back out of the branch trails through onto the line behind the
points however they are set.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly
from worQt.phys._small_steps import preloaded
from worQt.phys.rail import RailWorld, Ribbon, Turnout, bend, straight
from worQt.phys.rail import wayOf, wheelsetBody, wheelsetOn
from worQt.phys.rail._wheelset import RADIUS

from . import PhysTest

#  A frame, s; where the points stand on the line, m; the branch's
#  reverse curve (radius, m; how far aside it takes it, m).
FRAME = 1.0 / 60.0
TOE = 10.0
CURVE, ASIDE = 40.0, 4.5


class _Still:
  """A world that moves nothing (the inner world of a lone wheelset)."""

  def advancedAll(self, assembly: object, states: tuple, seconds: float,
                  start: float = 0.0) -> tuple:
    """Returns 'states' as they are."""
    return states


def _tracks() -> tuple:
  """Returns the line (40 m straight) and the branch leaving it at
  'TOE' (a reverse curve 'ASIDE' m to the left, then 10 m straight)."""
  line = Ribbon((straight(40.0),))
  turn = math.acos(1.0 - ASIDE / (2.0 * CURVE))
  place, frame = line.frameAt(TOE)
  branch = Ribbon((bend(turn, CURVE, (0.0, 0.0, 1.0)),
                   bend(turn, CURVE, (0.0, 0.0, -1.0)), straight(10.0)),
                  tuple(float(x) for x in place), frame)
  return line, branch


class TestTurnout(PhysTest):
  """Tests for the points (a minute or so)."""

  __time_out__ = 300.0

  def test_ways(self) -> None:
    """The way's pieces as the points send a wheelset."""
    lengths = (40.0, 30.0)
    points = Turnout(0, TOE, 1)
    self.assertEqual(wayOf(lengths, (points,), 0, 8.0, 5.0, 5.0),
                     ([(3.0, 8.0, 0, 0.0), (8.0, 13.0, 0, 0.0)], False,
                      False))
    points.thrown = True
    self.assertEqual(wayOf(lengths, (points,), 0, 8.0, 5.0, 5.0),
                     ([(3.0, 8.0, 0, 0.0), (8.0, 10.0, 0, 0.0),
                       (10.0, 13.0, 1, -10.0)], False, False))
    self.assertEqual(wayOf(lengths, (points,), 0, 12.0, 5.0, 5.0),
                     ([(7.0, 12.0, 0, 0.0), (12.0, 17.0, 0, 0.0)], False,
                      False))
    for thrown in (False, True):
      points.thrown = thrown
      with self.subTest(thrown=thrown):
        self.assertEqual(wayOf(lengths, (points,), 1, 2.0, 5.0, 5.0),
                         ([(-3.0, 0.0, 0, 10.0), (0.0, 2.0, 1, 0.0),
                           (2.0, 7.0, 1, 0.0)], False, False))
    self.assertEqual(wayOf(lengths, (points,), 0, 1.0, 5.0, 5.0)[1:],
                     (True, False))
    self.assertEqual(wayOf(lengths, (points,), 1, 28.0, 5.0, 5.0),
                     ([(23.0, 28.0, 1, 0.0), (28.0, 30.0, 1, 0.0)], False,
                      True))

  def test_refused(self) -> None:
    """A track branching off itself, points off their track, or a
    branch not beginning at its points, are refused."""
    with self.assertRaises(ValueError):
      Turnout(0, TOE, 0)
    with self.assertRaises(ValueError):
      Turnout(0, -1.0, 1)
    line, branch = _tracks()
    for points in (Turnout(0, TOE + 1.0, 1), Turnout(0, 50.0, 1),
                   Turnout(0, TOE, 2)):
      with self.subTest(at=points.at, branch=points.branch):
        with self.assertRaises(ValueError):
          RailWorld(_Still(), line, wheelsetBody(), 1e-4, 0.3, 2e-3,
                    None, (branch,), (points,))

  def rolled(self, start: tuple, speed: float, thrown: bool,
             device: str) -> tuple:
    """Returns a lone wheelset rolled 3 s from 'start' (track, s) at
    'speed' m/s, the points 'thrown' or not, stepped on 'device' (None:
    plain Python): its state and where the world finds it (track, s)."""
    line, branch = _tracks()
    points = Turnout(0, TOE, 1)
    points.thrown = thrown
    body = wheelsetBody()
    world = RailWorld(_Still(), line, body, 1e-4, 0.3, 2e-3, device,
                      (branch,), (points,))
    track, s = start
    states = (wheelsetOn(world.tracks[track], s, speed),)
    assembly = Assembly((body,), ())
    for k in range(round(3.0 / FRAME)):
      states = world.advancedAll(assembly, states, FRAME, k * FRAME)
    memory = world.rolling[0]
    return states[0], (memory['track'], memory['s']), world

  def onRails(self, world: RailWorld, state: object, track: int,
              s: float) -> None:
    """Asserts the wheelset's centre lies on track 'track' at 's', a
    wheel's radius over its rails (within 1 cm)."""
    place, frame, _ = world.frameOn(track, s)
    over = tuple(place[i] + RADIUS * frame[3 * i + 2] for i in range(3))
    self.assertLess(math.dist(state.place, over), 0.01)

  def test_rolls_through(self) -> None:
    """Rolling at 3 m/s from 5 m before the points it stays on the line
    or takes the branch as they are set, in plain Python and in the
    kernel (CPU) alike: within 1 mm across the track and up, 1 cm along
    it (the float32 kernel gains ~1.5 mm/s a second rolling at 3 m/s,
    with or without points: 7 mm in the 3 s)."""
    preloaded('cpu')
    for thrown in (False, True):
      runs = []
      for device in (None, 'cpu'):
        with self.subTest(thrown=thrown, device=device):
          state, (track, s), world = self.rolled((0, 5.0), 3.0, thrown,
                                                 device)
          self.assertEqual(track, 1 if thrown else 0)
          self.assertGreater(s, (13.5 - TOE) if thrown else 13.5)
          self.onRails(world, state, track, s)
          self.assertFalse(world.derailed)
          runs.append((state, track, s))
      (python, track, s), (kernel, _, _) = runs
      _, frame, _ = world.frameOn(track, s)
      apart = [kernel.place[i] - python.place[i] for i in range(3)]
      along, across, up = (sum(apart[i] * frame[3 * i + c]
                               for i in range(3)) for c in range(3))
      self.assertLess(abs(along), 0.01)
      self.assertLess(abs(across), 1e-3)
      self.assertLess(abs(up), 1e-3)

  def test_trails_back(self) -> None:
    """Rolling back at 3 m/s out of the branch it goes on along the line
    behind the points, however they are set."""
    preloaded('cpu')
    for thrown in (False, True):
      for device in (None, 'cpu'):
        with self.subTest(thrown=thrown, device=device):
          state, (track, s), world = self.rolled((1, 4.0), -3.0, thrown,
                                                 device)
          self.assertEqual(track, 0)
          self.assertLess(s, TOE - 4.5)
          self.onRails(world, state, track, s)
          self.assertFalse(world.derailed)
