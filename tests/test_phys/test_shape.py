"""
TestShape covers 'Shape', the outside of a solid as a closed surface of
triangles: a box's volume, centre and second moments are as by hand,
its faces closed and facing out; moved, its centre moves along; a
cylinder's are its polygon prism's exactly; a wedge is closed, half its
box, its centre a third of the way up and a sixth of its length on
toward its high end; an open surface is not closed, one turned inside
out has a volume below nought.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import UNTURNED, Shape, boxShape, cross, cylinderShape
from worQt.phys import dot, minus, normalised, plus, scaled, wedgeShape

from . import PhysTest, lShape

BOX = boxShape(0.4, 0.3, 0.2)


class TestShape(PhysTest):
  """Tests for 'Shape'."""

  def test_box(self) -> None:
    """A box is closed; its volume and second moments are as by hand,
    its centre its middle."""
    self.assertTrue(BOX.isClosed())
    volume, first, second = BOX.moments()
    self.assertAlmostEqual(volume, 0.024, 15)
    self.assertNear(first, (0.0, 0.0, 0.0), 1e-17)
    by = (volume * 0.16 / 12.0, volume * 0.09 / 12.0,
          volume * 0.04 / 12.0)
    self.assertNear(second, ((by[0], 0.0, 0.0), (0.0, by[1], 0.0),
                             (0.0, 0.0, by[2])), 1e-17)

  def test_facing_out(self) -> None:
    """Every face of a box and of a cylinder, both round their origin,
    faces away from it."""
    for shape in (BOX, cylinderShape(0.3, 0.2, 12)):
      for i, j, k in shape.faces:
        a, b, c = shape.points[i], shape.points[j], shape.points[k]
        facing = cross(minus(b, a), minus(c, a))
        middle = scaled(plus(plus(a, b), c), 1.0 / 3.0)
        self.assertGreater(dot(facing, middle), 0.0)

  def test_moved(self) -> None:
    """Moved and turned, a solid keeps its volume, its centre going
    along."""
    turn = normalised((0.9, 0.2, -0.3, 0.4))
    moved = BOX.moved((1.0, 2.0, 3.0), turn)
    self.assertAlmostEqual(moved.volume(), 0.024, 14)
    self.assertNear(moved.centre(), (1.0, 2.0, 3.0), 1e-13)
    self.assertNear(lShape().centre(), (0.15, 0.0, 0.15), 1e-15)

  def test_cylinder(self) -> None:
    """A cylinder of n sides is closed, its volume its polygon prism's
    exactly, its centre its middle; with many sides it is round."""
    for sides in (3, 12, 256):
      shape = cylinderShape(0.3, 0.2, sides)
      self.assertTrue(shape.isClosed())
      prism = 0.5 * sides * 0.09 * math.sin(2.0 * math.pi / sides) * 0.2
      self.assertAlmostEqual(shape.volume(), prism, 14)
      self.assertNear(shape.centre(), (0.0, 0.0, 0.0), 1e-15)
    self.assertAlmostEqual(cylinderShape(0.3, 0.2, 256).volume()
                           / (math.pi * 0.09 * 0.2), 1.0, 3)

  def test_not_closed(self) -> None:
    """A box with a face left out is not closed; turned inside out its
    volume is below nought."""
    self.assertFalse(Shape(BOX.points, BOX.faces[1:]).isClosed())
    self.assertFalse(Shape(BOX.points, ()).isClosed())
    inside = Shape(BOX.points, tuple((i, k, j) for i, j, k in BOX.faces))
    self.assertTrue(inside.isClosed())
    self.assertAlmostEqual(inside.volume(), -0.024, 15)
    self.assertEqual(BOX.moved((0.0, 0.0, 0.0), UNTURNED), BOX)

  def test_wedge(self) -> None:
    """A wedge 0.6 long, 0.2 wide and 0.3 high is closed, every face
    facing away from its middle, its volume half its box's, its centre a
    sixth of its length on from its middle toward its high end and a
    third of its height up."""
    wedge = wedgeShape(0.6, 0.2, 0.3)
    self.assertTrue(wedge.isClosed())
    volume, first, _ = wedge.moments()
    self.assertAlmostEqual(volume, 0.018, 15)
    self.assertNear(scaled(first, 1.0 / volume), (0.0, 0.1, 0.1), 1e-15)
    middle = scaled(first, 1.0 / volume)
    for i, j, k in wedge.faces:
      a, b, c = wedge.points[i], wedge.points[j], wedge.points[k]
      facing = cross(minus(b, a), minus(c, a))
      self.assertGreater(dot(facing, minus(a, middle)), 0.0)
