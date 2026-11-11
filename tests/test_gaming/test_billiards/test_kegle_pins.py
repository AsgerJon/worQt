"""
TestKeglePins covers 'PinField', keglebillard's pins as rigid bodies on
the cloth, moved with the balls by 'KegleMotion': a pin left standing
stays, upright inside its ring, and falls asleep; tipped less than its
tipping angle it rocks back, past it it falls and lies; a ball rolled
into a pin knocks it over, keeping most of its speed, the pin credited
to it, its touches logged; a ball rolled midway between two pins
passes, both left standing (the user); a pin knocked into the next
knocks it over too, credited to the ball that started it; the compiled
kernel fells the same pins as the plain Python it is checked against;
the pins as a sample holds them come back as they were.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import STILL, Ball, Cloth, KegleMotion
from worQt.gaming.billiards import KegleTable, PinField
from worQt.gaming.billiards._kegle_pins import _turned

from . import BilliardsTest

TABLE = KegleTable()
CLOTH = Cloth()
MOTION = KegleMotion()
RADIUS = TABLE.table.radius


def rolling(name: str, x: float, y: float, speed: float) -> Ball:
  """A ball at 'x', 'y' rolling along the table at 'speed' mm/s."""
  return Ball(name, x, y, STILL, 0.0, speed, -speed / RADIUS, 0.0, 0.0)


def tipped(degrees: float) -> PinField:
  """A field of the left pin alone, tipped 'degrees' over on its foot's
  edge, its foot still on its spot, let go."""
  field = PinField(TABLE, (1,))
  pin = field.pins[0]
  pin.q = _turned([1.0, 0.0, 0.0, 0.0], [math.radians(degrees), 0.0, 0.0],
                  1.0)
  foot = field.footAt(pin)
  x, y = TABLE.pinSpots()[1]
  lift = field.shape.foot() * math.sin(math.radians(degrees))
  pin.p = [pin.p[0] + x - foot[0], pin.p[1] + y - foot[1],
           pin.p[2] - foot[2] + lift]
  pin.awake = True
  return field


class TestKeglePins(BilliardsTest):
  """Tests for 'PinField'."""

  def test_stands(self) -> None:
    """A pin left standing stays upright inside its ring, and falls
    asleep."""
    field = PinField(TABLE, (0,))
    field.pins[0].awake = True
    MOTION.played((), field, 0.5)
    pin = field.pins[0]
    self.assertTrue(field.stands(pin))
    self.assertFalse(pin.awake)
    self.assertEqual(field.fallen(), ())

  def test_tipping(self) -> None:
    """Tipped 6 degrees, less than its 8.8, a pin rocks back and stands;
    tipped 12, it falls and lies."""
    back = tipped(6.0)
    MOTION.played((), back, 3.0)
    self.assertTrue(back.stands(back.pins[0]))
    over = tipped(12.0)
    MOTION.played((), over, 1.0)
    self.assertGreater(math.degrees(over.tilt(over.pins[0])), 80.0)
    self.assertFalse(over.stands(over.pins[0]))

  def test_knocked(self) -> None:
    """A ball rolled into a pin knocks it over, keeping most of its
    speed, the pin credited to it, the ball's touches on it logged, the
    first as it meets it (it may catch the falling pin again)."""
    x, y = TABLE.pinSpots()[3]
    field = PinField(TABLE, (3,))
    ball = rolling('white', x, y - 200.0, 1500.0)
    after, touches = MOTION.played((ball,), field, 0.4)
    self.assertEqual(field.fallen(), ((3, 'white'),))
    alone = CLOTH.advanced(ball, 0.4, RADIUS)
    self.assertGreater(math.hypot(after[0].vx, after[0].vy),
                       0.75 * math.hypot(alone.vx, alone.vy))
    self.assertEqual(touches[0], ('pin', 'white', '3'))
    self.assertEqual(set(touches), {('pin', 'white', '3')})

  def test_passes_between(self) -> None:
    """A ball rolled midway between two pins passes them, both left
    standing (the user: it must be possible), touching neither."""
    spots = TABLE.pinSpots()
    x = 0.5 * (spots[0][0] + spots[1][0])
    field = PinField(TABLE, (0, 1))
    after, touches = MOTION.played((rolling('white', x, spots[0][1] - 200.0,
                                            1000.0),), field, 0.5)
    self.assertEqual(field.fallen(), ())
    self.assertGreater(after[0].y, spots[0][1] + 100.0)
    self.assertEqual(touches, ())

  def test_chain(self) -> None:
    """A ball knocking a pin into the next knocks both over, both
    credited to the ball."""
    x, y = TABLE.pinSpots()[3]
    field = PinField(TABLE, (0, 3))
    MOTION.played((rolling('yellow', x, y - 250.0, 1500.0),), field, 0.6)
    self.assertEqual(sorted(field.fallen()), [(0, 'yellow'),
                                              (3, 'yellow')])

  def test_kernel_agrees(self) -> None:
    """The compiled kernel ('KegleMotion') fells the same pins, credited
    to the same ball, as the plain Python ('playedSlowly'), the ball
    meeting no cushion meanwhile."""
    x, y = TABLE.pinSpots()[3]
    ball = rolling('white', x, y - 250.0, 3000.0)
    fast, slow = PinField(TABLE), PinField(TABLE)
    MOTION.played((ball,), fast, 0.4)
    slow.playedSlowly((ball,), 0.4, CLOTH)
    self.assertEqual(sorted(fast.fallen()), sorted(slow.fallen()))
    self.assertTrue(fast.fallen())

  def test_rows(self) -> None:
    """The pins as a sample holds them come back as they were: where
    they are, how they are turned, the ball each is credited to."""
    x, y = TABLE.pinSpots()[3]
    field = PinField(TABLE)
    MOTION.played((rolling('red', x, y - 250.0, 3000.0),), field, 0.3)
    names = ('white', 'yellow', 'red')
    again = PinField(TABLE)
    again.setRows(field.rows(names), names)
    self.assertEqual(again.fallen(), field.fallen())
    for one, other in zip(field.pins, again.pins):
      self.assertEqual((one.number, one.p, one.q, one.credit),
                       (other.number, other.p, other.q, other.credit))
