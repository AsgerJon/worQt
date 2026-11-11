"""
TestRecorder covers 'Recorder' and 'Recording': a shot recorded ends as
'Motion.played' over its whole length ends it, its contacts the same,
whatever the rate; the first sample is the balls as struck, the last
the balls at rest, the samples a rate apart; between samples the balls
are blended; each contact is timed, the balls touching then; the
stretches follow on, only the last over; a stretch not following on is
not joined; a ball left spinning in place ends the shot as its spin
dies.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from worQt.gaming.billiards import STATE, STILL, Ball, CaromTable
from worQt.gaming.billiards import Motion, Recorder
from worQt.gaming.billiards import Recording

from . import BilliardsTest, firstBreak

TABLE = CaromTable()
MOTION = Motion()


@functools.cache
def firstRecording() -> Recording:
  """The user's first break, recorded at a thousand samples a second."""
  return Recorder(MOTION).recorded(firstBreak())


class TestRecorder(BilliardsTest):
  """Tests for 'Recorder' and 'Recording'."""

  def test_as_played(self) -> None:
    """Recorded, the shot ends as played at once over its whole length,
    every ball the same to the last digit, its contacts the same, at
    any rate."""
    after, touches = MOTION.played(firstBreak(), 60.0)
    recording = firstRecording()
    self.assertTrue(recording.over)
    self.assertEqual(recording.last(), after)
    self.assertEqual(recording.touchesOf(), touches)
    coarse = Recorder(MOTION, 240.0).recorded(firstBreak())
    self.assertEqual(coarse.last(), after)
    self.assertEqual(coarse.touchesOf(), touches)

  def test_samples(self) -> None:
    """The first sample is the balls as struck, the last the balls at
    rest; the samples are a rate apart; past the last the balls are as
    at it."""
    recording = firstRecording()
    self.assertEqual(recording.ballsAt(0.0), firstBreak())
    self.assertEqual(recording.count(),
                     round(recording.known() * recording.rate) + 1)
    radius = TABLE.radius
    for ball in recording.last():
      self.assertEqual(MOTION.cloth.phaseOf(ball, radius), 'still')
    self.assertEqual(recording.ballsAt(recording.known() + 5.0),
                     recording.last())
    self.assertGreater(recording.known(), 2.0)
    self.assertLess(recording.known(), 60.0)

  def test_between_samples(self) -> None:
    """Halfway between two samples a ball is halfway between, its turn
    of length one."""
    recording = firstRecording()
    every = 1.0 / recording.rate
    one = recording.ballsAt(1.0)
    other = recording.ballsAt(1.0 + every)
    half = recording.ballsAt(1.0 + 0.5 * every)
    for a, b, c in zip(one, other, half):
      self.assertAlmostEqual(c.x, 0.5 * (a.x + b.x), 9)
      self.assertAlmostEqual(c.y, 0.5 * (a.y + b.y), 9)
      self.assertAlmostEqual(math.hypot(*c.turn), 1.0, 12)

  def test_touch_times(self) -> None:
    """Each contact is timed, in order; at the first, white meeting the
    red at 4 m/s, the two touch to within the 4 mm white goes in a
    sample, the balls being blended through the hit, and were apart
    before."""
    recording = firstRecording()
    times = [time for time, _ in recording.touches]
    self.assertEqual(times, sorted(times))
    self.assertEqual(recording.timeOf(0), 0.0)
    self.assertEqual(recording.timeOf(len(times) + 1), math.inf)
    first = recording.touchesOf()[0]
    self.assertEqual((first.kind, {first.first, first.second}),
                     ('ball', {'white', 'red'}))
    white, _, red = recording.ballsAt(recording.timeOf(1))
    self.assertLess(abs(MOTION.pressedOf(white, red)), 4.0)
    white, _, red = recording.ballsAt(recording.timeOf(1) - 0.01)
    self.assertLess(MOTION.pressedOf(white, red), -10.0)

  def test_stretches(self) -> None:
    """The stretches follow on, each beginning where the last ended,
    none longer than a sample over its size, only the last over; joined,
    they are the recording."""
    recorder = Recorder(MOTION)
    stretches = list(recorder.stretches(firstBreak()))
    count = 0
    for stretch in stretches:
      self.assertEqual(stretch.first, count)
      self.assertLessEqual(len(stretch.states), recorder.size + 1)
      self.assertEqual(stretch.states.shape[1:], (3, STATE))
      count += len(stretch.states)
    self.assertEqual([stretch.over for stretch in stretches],
                     [False] * (len(stretches) - 1) + [True])
    self.assertEqual(count, firstRecording().count())
    self.assertGreater(len(stretches), 10)

  def test_joined(self) -> None:
    """A stretch not beginning where the recording ends is not joined,
    nor any once it is over."""
    stretches = list(Recorder(MOTION).stretches(firstBreak()))
    empty = Recording(('white', 'yellow', 'red'))
    self.assertIs(empty.joined(stretches[1]), empty)
    begun = empty.joined(stretches[0])
    self.assertEqual(begun.count(), len(stretches[0].states))
    self.assertFalse(begun.over)
    self.assertIs(firstRecording().joined(stretches[0]), firstRecording())

  def test_spin_ends(self) -> None:
    """A ball left spinning in place ends the shot as its spin dies, not
    at the longest a shot is followed."""
    recorder = Recorder(MOTION, 100.0)
    spun = (Ball('white', 710.0, 1420.0, STILL, 0.0, 0.0, 0.0, 0.0,
                 40.0),
            Ball('red', 300.0, 300.0))
    recording = recorder.recorded(spun)
    dies = MOTION.cloth.spinningTime(40.0, TABLE.radius)
    self.assertTrue(recording.over)
    self.assertLess(abs(recording.known() - dies), 1.5 / recorder.rate)
    self.assertEqual(recording.last()[0].wz, 0.0)
