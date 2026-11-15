"""
TestBody covers 'Body', a rigid body of any shape, and 'State', its six
degrees of freedom: a solid's mass, centre and inertia from its shape
are as by hand (a box; a round cylinder; an L of two boxes, by the
parallel axes); turned, its inertia turns along; its principal axes and
moments diagonalise it; open or inside out shapes are refused; a point
on it moves as its centre plus its spin about it, and its energy is
its moving and turning.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.phys import ORIGIN, UNTURNED, Body, Shape, State, applied
from worQt.phys import boxShape, cross, cylinderShape, dot, matrixOf
from worQt.phys import matrixProduct, minus, normalised, plus, rotated
from worQt.phys import scaled, transposed

from . import PhysTest, lShape

BOX = boxShape(0.4, 0.3, 0.2)
TURN = normalised((0.9, 0.2, -0.3, 0.4))


def boxInertia(mass: float, length: float, width: float,
               height: float) -> tuple:
  """The 'boxInertia' function returns a box's inertia about its middle
  along its sides, by hand."""
  return ((mass * (width ** 2 + height ** 2) / 12.0, 0.0, 0.0),
          (0.0, mass * (length ** 2 + height ** 2) / 12.0, 0.0),
          (0.0, 0.0, mass * (length ** 2 + width ** 2) / 12.0))


def steinered(inertia: tuple, mass: float, away: tuple) -> tuple:
  """The 'steinered' function returns 'inertia', about a piece's own
  centre, about a point 'away' from it: the parallel axes."""
  far = dot(away, away)
  return tuple(tuple(inertia[i][j] + mass * ((far if i == j else 0.0)
                                             - away[i] * away[j])
                     for j in range(3)) for i in range(3))


class TestBody(PhysTest):
  """Tests for 'Body' and 'State'."""

  def test_box(self) -> None:
    """A box of 1000 kg/m³ weighs as much as its volume says, its
    centre its middle, its inertia as by hand."""
    body = Body.of(BOX, 1000.0)
    self.assertAlmostEqual(body.mass, 24.0, 12)
    self.assertNear(body.centre, ORIGIN, 1e-15)
    self.assertNear(body.inertia, boxInertia(24.0, 0.4, 0.3, 0.2), 1e-14)

  def test_cylinder(self) -> None:
    """A cylinder of many sides is round: m r²/2 about its axle (y),
    m (3 r² + w²)/12 across."""
    body = Body.of(cylinderShape(0.3, 0.2, 256), 1000.0)
    mass = body.mass
    self.assertAlmostEqual(body.inertia[1][1] / (0.5 * mass * 0.09), 1.0, 3)
    across = mass * (3.0 * 0.09 + 0.04) / 12.0
    self.assertAlmostEqual(body.inertia[0][0] / across, 1.0, 3)
    self.assertAlmostEqual(body.inertia[2][2] / across, 1.0, 3)
    self.assertNear((body.inertia[0][1], body.inertia[0][2],
                     body.inertia[1][2]), ORIGIN, 1e-14)

  def test_joined(self) -> None:
    """An L of two boxes weighs as both, its centre between theirs by
    their masses, its inertia theirs about it by the parallel axes:
    turning about x and z it leans."""
    body = Body.of(lShape(), 1000.0)
    self.assertAlmostEqual(body.mass, 64.0, 12)
    self.assertNear(body.centre, (0.15, 0.0, 0.15), 1e-15)
    lying = steinered(boxInertia(40.0, 1.0, 0.2, 0.2), 40.0,
                      (-0.15, 0.0, -0.15))
    standing = steinered(boxInertia(24.0, 0.2, 0.2, 0.6), 24.0,
                         (0.25, 0.0, 0.25))
    both = tuple(tuple(a + b for a, b in zip(rowA, rowB))
                 for rowA, rowB in zip(lying, standing))
    self.assertNear(body.inertia, both, 1e-13)
    self.assertLess(body.inertia[0][2], -1.0)

  def test_turned(self) -> None:
    """A solid turned and moved in its frame has its centre moved along
    and its inertia turned: R I R'."""
    body = Body.of(lShape(), 1000.0)
    moved = Body.of(lShape().moved((1.0, 2.0, 3.0), TURN), 1000.0)
    self.assertAlmostEqual(moved.mass, body.mass, 11)
    self.assertNear(moved.centre, plus(rotated(TURN, body.centre),
                                       (1.0, 2.0, 3.0)), 1e-13)
    turning = matrixOf(TURN)
    turned = matrixProduct(matrixProduct(turning, body.inertia),
                           transposed(turning))
    self.assertNear(moved.inertia, turned, 1e-11)

  def test_principal(self) -> None:
    """The principal moments come least first, each with its axis: the
    inertia takes each axis to its moment times the axis."""
    body = Body.of(lShape(), 1000.0)
    moments, axes = body.principal()
    self.assertLess(moments[0], moments[1])
    self.assertLess(moments[1], moments[2])
    columns = transposed(matrixOf(axes))
    for moment, axis in zip(moments, columns):
      self.assertNear(applied(body.inertia, axis), scaled(axis, moment),
                      1e-12)
    trace = sum(body.inertia[i][i] for i in range(3))
    self.assertAlmostEqual(sum(moments), trace, 12)

  def test_refused(self) -> None:
    """An open shape and one inside out make no body; a body with a
    principal moment of nought has no principal axes."""
    with self.assertRaises(ValueError):
      Body.of(Shape(BOX.points, BOX.faces[2:]), 1000.0)
    with self.assertRaises(ValueError):
      Body.of(Shape(BOX.points, tuple((i, k, j)
                                      for i, j, k in BOX.faces)), 1000.0)
    flat = Body(1.0, ORIGIN, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                              (0.0, 0.0, 0.0)))
    with self.assertRaises(ValueError):
      flat.principal()

  def test_moving(self) -> None:
    """A corner of a turned, moving, spinning box is where its centre
    and its turned arm put it, moving as its centre plus the spin
    across the arm; its energy is half its mass times its speed
    squared plus half its spin through its inertia, turned."""
    body = Body.of(BOX.moved((0.5, 0.0, 0.0), UNTURNED), 1000.0)
    state = State((1.0, 2.0, 3.0), TURN, (0.5, -1.0, 2.0), (3.0, 1.0, -2.0))
    corner = body.shape.points[7]
    arm = rotated(TURN, minus(corner, body.centre))
    self.assertNear(body.placeOf(state, corner), plus(state.place, arm),
                    1e-15)
    self.assertNear(body.velocityOf(state, corner),
                    plus(state.velocity, cross(state.spin, arm)), 1e-15)
    held = applied(transposed(matrixOf(TURN)), state.spin)
    turning = 0.5 * dot(held, applied(body.inertia, held))
    moving = 0.5 * body.mass * dot(state.velocity, state.velocity)
    self.assertAlmostEqual(body.kineticOf(state), moving + turning, 11)
    self.assertNear(body.momentumOf(state),
                    scaled(state.velocity, body.mass), 1e-13)
