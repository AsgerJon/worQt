"""
TestWalkThrough covers walking through the steam train (user,
2026-11-16: "make the train, however realistic or not, such that we can
walk from the locomotive and back through each car. Then put some memes
on the inside walls"): the tender's corridor rises from a coach's floor
at its back to the cab's at its front; down the middle from the cab to
the last coach's back door there is floor under foot all the way (no
gap wider than a gangway's few centimetres), at the cab's, the
corridor's slope and the coaches' heights; an avatar in the cab runs
back through the tender and every coach, and from the last coach
forward to the cab; every coach has its posters, a cell of the memes'
picture each, the picture there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys._body import State
from worQt.phys._poke import hitOf

from worQt.gaming.sandbox import PERSON, Avatar
from worQt.gaming.trains._coach import FLOOR, WINDOWS
from worQt.gaming.trains._layout import OVAL_UP
from worQt.gaming.trains._locomotive import CORRIDOR_FLOOR, ENGINE_PIECES
from worQt.gaming.trains._locomotive import TENDER_AT, TENDER_ENDS
from worQt.gaming.trains._memes import GRID, MEME_LOOK, MEMES, MEMES_FILE
from worQt.gaming.trains._memes import memeCell

from . import TrainsTest

#  The cab's floor's top, m over the rails (the engine's piece under it).
CAB_FLOOR = ENGINE_PIECES[5][4]


class TestWalkThrough(TrainsTest):
  """Tests for walking through the train (a few minutes on the CPU)."""

  __time_out__ = 600.0

  def floorAt(self, x: float) -> float:
    """Returns the floor wanted 'x' m along the engine (its own frame)
    down the middle: the cab's, the tender corridor's slope, the
    coaches'."""
    back, front = (TENDER_AT + end for end in TENDER_ENDS)
    if x >= front:
      return CAB_FLOOR
    if x >= back:
      low, high = CORRIDOR_FLOOR
      return low + (high - low) * (x - back) / (front - back)
    return FLOOR[1]

  def test_joins(self) -> None:
    """The corridor meets the cab's floor at the tender's front and a
    coach's at its back."""
    self.assertEqual(CORRIDOR_FLOOR, (FLOOR[1], CAB_FLOOR))

  def test_floor(self) -> None:
    """Down the middle from the cab to the last coach's back door, a ray
    down from 0.6 m over the floor wanted meets the train within 3 cm
    of it, but for gaps no wider than 6 cm."""
    world = self.ovalWorld()
    engine, last = world.vehicles[0], world.vehicles[3]
    bodies, states = world.assembly.bodies, world.states
    frame = states[engine.frame]
    train = {i for vehicle in world.vehicles[:4] for i in vehicle.bodies}
    end = bodies[last.frame].placeOf(states[last.frame], (-9.5, 0.0, 0.0))
    origin = bodies[engine.frame].placeOf(frame, (0.0, 0.0, 0.0))
    tail = float(end[0] - origin[0])
    passed = tuple(i for i in range(len(states)) if i not in train)
    missed, worst = 0.0, 0.0
    for x in numpy.arange(-4.0, tail + 0.3, -0.02):
      wanted = self.floorAt(float(x))
      eye = bodies[engine.frame].placeOf(frame, (float(x), 0.0,
                                                 wanted + 0.6))
      hit = hitOf(world.assembly, states, eye, (0.0, 0.0, -1.0), passed)
      if hit is None or abs(eye[2] - 0.6 - hit[1][2]) > 0.03:
        missed += 0.02
        worst = max(worst, missed)
      else:
        missed = 0.0
    self.assertLess(worst, 0.065)

  def test_runs(self) -> None:
    """An avatar in the cab running back (Shift and W, facing back)
    comes through the tender and two coaches into the last in 4.6 s;
    from the back of the last coach running ahead it comes up the
    tender's corridor into the cab in 6 s; on the train's floors all
    the way."""
    for start, yaw, seconds, wanted in ((-4.6, math.pi, 4.6, -56.0),
                                        (-70.0, 0.0, 6.0, -5.4)):
      with self.subTest(start=start):
        world = self.ovalWorld()
        avatar = Avatar(PERSON)
        avatar.enter(world)
        self.ran(world, 0.2)
        engine = world.vehicles[0]
        bodies, states = world.assembly.bodies, list(world.states)
        frame = states[engine.frame]
        states[avatar.index] = State(bodies[engine.frame].placeOf(
          frame, (start, 0.0, self.floorAt(start) + 0.31)))
        world.states = tuple(states)
        avatar.yaw, avatar.held = yaw, frozenset(('w', 'shift'))
        self.ran(world, seconds)
        place = numpy.array(world.states[avatar.index].place)
        origin = bodies[engine.frame].placeOf(frame, (0.0, 0.0, 0.0))
        along = float(place[0] - origin[0])
        if yaw == 0.0:
          self.assertGreater(along, wanted)
        else:
          self.assertLess(along, wanted)
        self.assertGreater(place[2], OVAL_UP + FLOOR[1])

  def test_posters(self) -> None:
    """Every coach has its posters (one above each window either side,
    two on each end wall: four corners of eight numbers each), drawn on
    the memes' picture (there), each within a cell of it."""
    self.assertTrue(MEMES_FILE.is_file())
    self.assertEqual(MEME_LOOK[3], str(MEMES_FILE))
    self.assertLessEqual(len(MEMES), GRID[0] * GRID[1])
    world = self.ovalWorld()
    for coach in world.vehicles[1:]:
      parts = {look: rows for rows, _, look in world.dressed[coach.frame]}
      rows = parts['memes']
      with self.subTest(coach=coach.number):
        self.assertEqual(rows.shape, (4 * (2 * WINDOWS + 4), 8))
        self.assertTrue(((rows[:, 6:] >= 0.0) & (rows[:, 6:] <= 1.0))
                        .all())
    for k in range(len(MEMES)):
      u0, v0, u1, v1 = memeCell(k)
      self.assertAlmostEqual(u1 - u0, 1.0 / GRID[0], 12)
      self.assertAlmostEqual(v1 - v0, 1.0 / GRID[1], 12)
