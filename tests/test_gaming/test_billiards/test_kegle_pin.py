"""
TestKeglePin covers 'KeglePin', a keglebillard pin as DDBU draws it: 120
mm tall on a 14 mm foot, 20 mm across the body at a ball's middle, 8
across the neck, 13 the head; ten and a half grams of wood, its centre
of mass 45 mm up, so it falls once tipped past 9 degrees; a ball passes
between two pins in the cross with a third of a mm to spare a side;
the spheres its surface is made of lie inside it, touching it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import CaromTable, KeglePin, KegleTable

from . import BilliardsTest

PIN = KeglePin()
RADIUS = CaromTable().radius


class TestKeglePin(BilliardsTest):
  """Tests for 'KeglePin'."""

  def test_measures(self) -> None:
    """120 mm tall, 14 across the foot, about 20 across the body at a
    ball's middle, 8 the neck, 13 the head, as DDBU writes them."""
    self.assertEqual((PIN.height(), PIN.foot()), (120.0, 7.0))
    body = max(PIN.radiusAt(z) for z in range(0, 50))
    self.assertAlmostEqual(2.0 * body, 20.0, 0)
    neck = min(PIN.radiusAt(z) for z in range(55, 85))
    self.assertAlmostEqual(2.0 * neck, 8.0, 0)
    head = max(PIN.radiusAt(z) for z in range(85, 115))
    self.assertAlmostEqual(2.0 * head, 13.0, 0)
    self.assertEqual(PIN.radiusAt(121.0), 0.0)

  def test_mass(self) -> None:
    """Its centre of mass 45 mm up, so on its 7 mm foot it falls once
    tipped past about 9 degrees; much harder to turn across than about
    its axis."""
    self.assertAlmostEqual(PIN.centre(), 45.1, 0)
    self.assertAlmostEqual(math.degrees(PIN.tipping()), 8.8, 0)
    along, across = PIN.inertia()
    self.assertGreater(across, 20.0 * along)

  def test_passes_between(self) -> None:
    """A ball passes between two pins standing in the cross, with a
    third of a mm to spare a side at its middle (the user: a ball may
    roll between two pins rightly set up)."""
    apart = KegleTable().pinApart
    spare = 0.5 * (apart - 2.0 * PIN.radiusAt(RADIUS) - 2.0 * RADIUS)
    self.assertGreater(spare, 0.2)
    self.assertLess(spare, 0.5)

  def test_spheres(self) -> None:
    """The spheres its surface is made of lie inside it and reach out
    to it, from near the foot to near the head's top."""
    spheres = PIN.spheres()
    self.assertGreater(len(spheres), 15)
    for z, size in spheres:
      for k in range(21):
        h = z - size + 2.0 * size * k / 20.0
        reach = math.sqrt(max(size * size - (h - z) ** 2, 0.0))
        self.assertLessEqual(reach, PIN.radiusAt(h) + 1e-6)
      if 10.0 <= z <= 110.0:
        self.assertGreater(size, 0.6 * PIN.radiusAt(z))
    heights = [z for z, _ in spheres]
    self.assertLess(min(heights), 5.0)
    self.assertGreater(max(heights), 115.0)
