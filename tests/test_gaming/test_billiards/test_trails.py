"""
TestTrails covers 'Trails', 'ribbonMesh' and the parts of 'Recording'
they read: the places over a run of samples are the balls' middles at
them; the balls struck are those moving at the first sample; followed a
frame at a time, the trails keep what they keep followed all at once;
each way starts where its ball set off and ends where it is, its places
kept 'spacing' apart, a ball standing still keeping one; a moment not
past those taken in adds nothing. A ribbon is as wide as asked, mitred
at a bend and cut square where the way turns back, lifted, facing up;
a way of one place has none.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from worQt.gaming.billiards import Motion, Recorder, Recording, Trails
from worQt.gaming.billiards import ribbonMesh

from . import BilliardsTest, firstBreak


@functools.cache
def firstRecording() -> Recording:
  """The user's first break, recorded at a thousand samples a second."""
  return Recorder(Motion()).recorded(firstBreak())


def framed(recording: Recording, frame: float) -> Trails:
  """Returns the trails of 'recording' followed a 'frame' at a time to
  its end."""
  trails, seconds = Trails(), 0.0
  while seconds < recording.known() + frame:
    trails = trails.followed(recording, seconds)
    seconds += frame
  return trails


class TestTrails(BilliardsTest):
  """Tests for 'Trails' and 'ribbonMesh'."""

  def test_places(self) -> None:
    """The places over a run of samples are the balls' middles at them,
    across the stretches they came in; none past the end."""
    recording = firstRecording()
    rate = recording.rate
    places = recording.placesOf(40, 260)
    self.assertEqual(places.shape, (220, 3, 2))
    for k in (0, 9, 10, 11, 219):
      balls = recording.ballsAt((40 + k) / rate)
      for ball, (x, y) in zip(balls, places[k]):
        self.assertAlmostEqual(ball.x, x, 6)
        self.assertAlmostEqual(ball.y, y, 6)
    count = recording.count()
    self.assertEqual(len(recording.placesOf(count - 5, count + 50)), 5)
    self.assertEqual(len(recording.placesOf(count, count + 5)), 0)

  def test_struck(self) -> None:
    """The ball struck is the cue ball, as it was struck."""
    recording = firstRecording()
    self.assertEqual(recording.struck(), (firstBreak()[0],))

  def test_framed(self) -> None:
    """Followed a frame at a time, the trails are those followed all at
    once."""
    recording = firstRecording()
    whole = Trails().followed(recording, recording.known())
    self.assertEqual(framed(recording, 0.016), whole)
    self.assertEqual(framed(recording, 0.05), whole)

  def test_ways(self) -> None:
    """Each way starts where its ball set off and ends where it rests;
    its places are 'spacing' apart; a ball standing still has one."""
    recording = firstRecording()
    end = recording.known()
    trails = Trails(5.0).followed(recording, end)
    paths = trails.paths(recording, end)
    for path, start, ball in zip(paths, firstBreak(), recording.last()):
      self.assertEqual(tuple(path[0]), (start.x, start.y))
      self.assertEqual(tuple(path[-1]), (ball.x, ball.y))
      steps = numpy.hypot(*numpy.diff(path[:-1], axis=0).T)
      if len(steps):
        self.assertGreaterEqual(steps.min(), 5.0)
    still = [len(path) for path in paths if len(path) == 1]
    moved = [len(path) for path in paths if len(path) > 100]
    self.assertEqual(len(still) + len(moved), 3)
    self.assertGreaterEqual(len(moved), 2)

  def test_so_far(self) -> None:
    """Half way through the shot, each way ends where its ball is then;
    an earlier moment adds nothing."""
    recording = firstRecording()
    trails = Trails().followed(recording, 0.75)
    self.assertEqual(trails.taken, 751)
    for path, ball in zip(trails.paths(recording, 0.7505),
                          recording.ballsAt(0.7505)):
      self.assertEqual(tuple(path[-1]), (ball.x, ball.y))
    self.assertIs(trails.followed(recording, 0.5), trails)
    self.assertEqual(Trails().followed(Recording(), 1.0), Trails())

  def test_ribbon_straight(self) -> None:
    """Along a straight way the ribbon is two triangles a piece, the
    half width either side, lifted, facing up."""
    mesh = ribbonMesh(numpy.array([[0.0, 0.0], [100.0, 0.0],
                                   [250.0, 0.0]]), 5.0, 0.5)
    self.assertEqual(mesh.shape, (12, 6))
    self.assertTrue(numpy.all(mesh[:, 1] == 0.5))
    self.assertTrue(numpy.all(mesh[:, 3:] == [0.0, 1.0, 0.0]))
    self.assertEqual(sorted(set(numpy.abs(mesh[:, 2]).tolist())), [5.0])
    self.assertEqual(mesh[:, 0].min(), 0.0)
    self.assertEqual(mesh[:, 0].max(), 250.0)

  def test_ribbon_bends(self) -> None:
    """At a square bend the mitre reaches the half width times root two;
    where the way turns straight back it is cut square, no wider; a way
    of one place, or of one place again and again, has no ribbon."""
    bend = ribbonMesh(numpy.array([[0.0, 0.0], [100.0, 0.0],
                                   [100.0, 100.0]]), 5.0, 0.0)
    corner = numpy.hypot(bend[:, 0] - 100.0, bend[:, 2])
    self.assertAlmostEqual(corner[corner < 20.0].max(),
                           5.0 * math.sqrt(2.0), 9)
    back = ribbonMesh(numpy.array([[0.0, 0.0], [100.0, 0.0],
                                   [0.0, 0.0]]), 5.0, 0.0)
    self.assertAlmostEqual(numpy.abs(back[:, 2]).max(), 5.0, 9)
    self.assertEqual(ribbonMesh(numpy.zeros((1, 2)), 5.0, 0.0).shape,
                     (0, 6))
    self.assertEqual(ribbonMesh(numpy.zeros((4, 2)), 5.0, 0.0).shape,
                     (0, 6))
