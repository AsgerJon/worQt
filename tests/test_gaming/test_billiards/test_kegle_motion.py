"""
TestKegleMotion covers 'KegleMotion', keglebillard's balls and pins
moved together, and 'KegleRecorder', a shot of them sampled: a shot
nowhere near the pins plays as three-cushion plays it, exactly; on the
cloth a ball stops exactly on the edge of a pin's zone, to be stepped
with the pins from there; a fallen pin stays on the cloth, slowing a
ball that meets it and shoved by it (the user: pins must be allowed to
remain on the table slowing the balls); a pin hit square on and hard
flies over the rail, off the table, onto the floor (the user: it is
yeeted off the table), knocked over, out of play; a ball rolled into a
middle or a corner pocket goes in, kept far off the table, while one
rolled into the cushion beside it, or onto a jaw, comes back; recorded, a shot through the
pins comes out the same at any rate, to the last digit, and as played
at once over its whole length; the samples hold the pins, standing on
their spots as the shot begins, and the pins it leaves fallen.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.billiards import STILL, Ball, Cloth, Cue, KegleMotion
from worQt.gaming.billiards import KegleRecorder, KegleTable, Motion
from worQt.gaming.billiards import Trails
from worQt.gaming.billiards._kegle_table import HOLE_NAMES

from . import BilliardsTest
from .test_kegle_pins import tipped

TABLE = KegleTable()
MOTION = KegleMotion()
RADIUS = TABLE.table.radius


def rolling(name: str, x: float, y: float, vx: float, vy: float) -> Ball:
  """A ball at 'x', 'y' rolling at 'vx', 'vy' mm/s."""
  return Ball(name, x, y, STILL, vx, vy, -vy / RADIUS, vx / RADIUS, 0.0)


def throughThePins() -> tuple[Ball, ...]:
  """The balls as they lie, red struck from near the foot at the cross,
  3.5 m/s, a little follow and right side: it fells all five."""
  white = Ball('white', *TABLE.spots()[0])
  yellow = Ball('yellow', *TABLE.spots()[1])
  red = Ball('red', TABLE.middle()[0] + 100.0, 600.0)
  x, y = TABLE.pinSpots()[0]
  dx, dy = x - red.x + 15.0, y - red.y
  size = math.hypot(dx, dy)
  struck = Cue().sent(red, dx / size, dy / size, 3500.0, 0.2, 0.1, RADIUS)
  return white, yellow, struck


class TestKegleMotion(BilliardsTest):
  """Tests for 'KegleMotion' and 'KegleRecorder'."""

  @classmethod
  def setUpClass(cls) -> None:
    """Records the shot through the pins at two rates, once."""
    super().setUpClass()
    shot = throughThePins()
    cls.recordings = {rate: KegleRecorder(MOTION, rate).recorded(shot)
                      for rate in (250.0, 1000.0)}

  def test_far_from_pins(self) -> None:
    """A shot nowhere near the pins, white into the foot cushion and
    back, plays as three-cushion plays it, exactly, the pins left
    standing."""
    balls = (rolling('white', 300.0, 400.0, 0.0, -400.0),
             Ball('yellow', 1100.0, 300.0), Ball('red', 700.0, 2600.0))
    field = MOTION.fieldOf()
    after, touches = MOTION.played(balls, field, 8.0)
    self.assertEqual((after, touches), Motion().played(balls, 8.0))
    self.assertEqual(field.fallen(), ())
    self.assertFalse(field.awake())

  def test_zone(self) -> None:
    """On the cloth a ball rolled at the cross stops on the edge of the
    near pin's zone, and from there is stepped with the pins."""
    x, y = TABLE.pinSpots()[3]
    ball = rolling('white', x, 600.0, 0.0, 1500.0)
    field = MOTION.fieldOf()
    glide = MOTION.glided((ball,), field, 5.0)
    cx, cy, size = MOTION.zonesOf(field)[3]
    after = glide.after[0]
    self.assertAlmostEqual(math.hypot(after.x - cx, after.y - cy), size, 6)
    self.assertTrue(MOTION.busy(glide.after, field))
    self.assertFalse(MOTION.busy((ball,), field))

  def test_lying_pins_slow(self) -> None:
    """A pin lying fallen on the cloth stays there, slowing a ball that
    meets it, and is shoved along by it (the user)."""
    field = tipped(12.0)
    MOTION.played((), field, 1.0)
    pin = field.pins[0]
    self.assertGreater(math.degrees(field.tilt(pin)), 80.0)
    lying = list(pin.p)
    ball = rolling('white', lying[0], lying[1] - 300.0, 0.0, 1000.0)
    after, touches = MOTION.played((ball,), field, 0.6)
    alone = Cloth().advanced(ball, 0.6, RADIUS)
    self.assertLess(math.hypot(after[0].vx, after[0].vy),
                    0.9 * math.hypot(alone.vx, alone.vy))
    self.assertGreater(math.dist(pin.p[:2], lying[:2]), 50.0)
    self.assertIn(('pin', 'white', '1'), touches)

  def test_yeeted(self) -> None:
    """A pin hit square on at 6 m/s flies over the rail, off the table,
    and lies on the floor, out of play, knocked over (the user: it is
    yeeted off the table)."""
    x, y = TABLE.pinSpots()[3]
    field = MOTION.fieldOf((3,))
    ball = rolling('white', x, y - 300.0, 0.0, 6000.0)
    MOTION.played((ball,), field, 3.0)
    pin = field.pins[0]
    carom = TABLE.table
    self.assertTrue(pin.off)
    self.assertFalse(pin.awake)
    self.assertLess(pin.p[2], -0.5 * carom.bed)
    out = carom.cushion + carom.rail
    beyond = (-pin.p[0], pin.p[0] - carom.width, -pin.p[1],
              pin.p[1] - carom.length)
    self.assertGreater(max(beyond), out)
    self.assertEqual(field.fallen(), ((3, 'white'),))
    self.assertEqual(MOTION.zonesOf(field), ())

  def test_pockets(self) -> None:
    """A ball rolled into the left middle pocket, or the foot left
    corner's, goes in, kept far off the table ('pocketOf'), its touch
    logged; one rolled into the cushion beside the middle pocket, or onto
    its jaw, comes back off the cushion."""
    for ball, hole in ((rolling('white', 300.0, 1420.0, -1500.0, 0.0), 4),
                       (rolling('white', 400.0, 400.0, -1000.0, -1000.0),
                        0)):
      after, touches = MOTION.played((ball,), MOTION.fieldOf(()), 3.0)
      self.assertEqual(TABLE.pocketOf(after[0]), hole)
      self.assertEqual(after[0][1:3], TABLE.parkedAt(hole))
      self.assertIn(('pocket', 'white', HOLE_NAMES[hole]), touches)
    for y in (1700.0, 1470.0):
      ball = rolling('white', 300.0, y, -1500.0, 0.0)
      after, touches = MOTION.played((ball,), MOTION.fieldOf(()), 3.0)
      self.assertEqual(TABLE.pocketOf(after[0]), -1)
      self.assertIn(('cushion', 'white', 'left'), touches)

  def test_pocket_recorded(self) -> None:
    """A shot into a pocket, recorded, comes out the same at any rate
    and as played; between the samples either side of its going in the
    ball shows where it was, not flying off, and its trail stops at the
    pocket."""
    shot = (rolling('white', 300.0, 1420.0, -1500.0, 0.0),
            Ball('yellow', 700.0, 700.0), Ball('red', 1000.0, 2400.0))
    slow = KegleRecorder(MOTION, 250.0).recorded(shot)
    fast = KegleRecorder(MOTION, 1000.0).recorded(shot)
    self.assertEqual(slow.last(), fast.last())
    self.assertEqual(slow.touchesOf(), fast.touchesOf())
    after, touches = MOTION.played(shot, MOTION.fieldOf(), fast.known())
    self.assertEqual((after, touches), (fast.last(), fast.touchesOf()))
    went = next(time for time, touch in fast.touches
                if touch.kind == 'pocket')
    for k in range(-3, 4):
      white = fast.ballsAt(went + 0.0004 * k)[0]
      if TABLE.pocketOf(white) < 0:
        self.assertGreater(white.x, -100.0)
    path = Trails().followed(fast, fast.known()).paths(fast,
                                                       fast.known())[0]
    self.assertGreater(float(path[:, 1].min()), 0.0)

  def test_rates(self) -> None:
    """Recorded at 250 and at 1000 samples a second, the shot through
    the pins ends the same to the last digit: the balls, the pins and
    the contacts."""
    slow, fast = self.recordings[250.0], self.recordings[1000.0]
    self.assertEqual(slow.last(), fast.last())
    self.assertTrue(numpy.array_equal(slow.lastPins(), fast.lastPins()))
    self.assertEqual(slow.touchesOf(), fast.touchesOf())

  def test_as_played(self) -> None:
    """Recorded, the shot through the pins ends as played at once over
    its whole length, its contacts the same, the same pins fallen."""
    recording = self.recordings[1000.0]
    field = MOTION.fieldOf()
    after, touches = MOTION.played(throughThePins(), field,
                                   recording.known())
    self.assertEqual(after, recording.last())
    self.assertEqual(touches, recording.touchesOf())
    self.assertEqual(field.fallen(),
                     KegleRecorder(MOTION).fallenOf(recording))

  def test_pins_recorded(self) -> None:
    """The samples hold the pins: standing on their spots as the shot
    begins, all five felled as it ends, some by the balls, their
    touches logged, red's on the near pin first, the rest by the pins
    falling; at rest as the shot ends."""
    recording = self.recordings[1000.0]
    start = recording.pinsAt(0.0)
    spots = TABLE.pinSpots()
    for row in start:
      self.assertEqual(tuple(row[1:3]), spots[int(row[0])])
      self.assertEqual(tuple(row[4:8]), (1.0, 0.0, 0.0, 0.0))
    fallen = KegleRecorder(MOTION).fallenOf(recording)
    self.assertEqual(sorted(number for number, _ in fallen),
                     [0, 1, 2, 3, 4])
    self.assertEqual(recording.touchesOf()[0], ('pin', 'red', '3'))
    met = {touch.second for touch in recording.touchesOf()
           if touch.kind == 'pin'}
    self.assertLess(met, {'0', '1', '2', '3', '4'})
    self.assertIn('3', met)
    self.assertTrue(recording.over)
    self.assertEqual(recording.lastPins()[:, 8].tolist(), [0.0] * 5)
