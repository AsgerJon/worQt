"""
TestVectors covers the vectors and turns 'worQt.phys' reckons with: a
quarter turn about z takes x to y; turns compose as the quaternions
multiply, the conjugate undoing one; a turn's matrix has the axes
turned as its columns, and the matrix gives the turn back.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import AXES, IDENTITY, UNTURNED
from worQt.phys import conjugate, cross, matrixOf, matrixProduct
from worQt.phys import normalised, product, rotated, transposed
from worQt.phys import turnAbout, turnOf

from . import PhysTest

TURN = normalised((0.9, 0.2, -0.3, 0.4))
OTHER = normalised((-0.2, 0.7, 0.1, -0.5))


class TestVectors(PhysTest):
  """Tests for the vectors and turns."""

  def test_quarter_turn(self) -> None:
    """A quarter turn about z takes x to y and y to minus x."""
    quarter = turnAbout((0.0, 0.0, 2.0), 0.5 * math.pi)
    self.assertNear(rotated(quarter, (1.0, 0.0, 0.0)), (0.0, 1.0, 0.0),
                    1e-15)
    self.assertNear(rotated(quarter, (0.0, 1.0, 0.0)), (-1.0, 0.0, 0.0),
                    1e-15)
    self.assertNear(cross(AXES[0], AXES[1]), AXES[2], 0.0)

  def test_composed(self) -> None:
    """Turned by one turn, then another, is turned by their product;
    the conjugate turns back."""
    point = (0.3, -1.2, 2.5)
    twice = rotated(OTHER, rotated(TURN, point))
    self.assertNear(rotated(product(OTHER, TURN), point), twice, 1e-14)
    self.assertNear(rotated(conjugate(TURN), rotated(TURN, point)), point,
                    1e-14)
    self.assertNear(product(TURN, conjugate(TURN)), UNTURNED, 1e-15)

  def test_matrix(self) -> None:
    """A turn's matrix has the axes turned as columns, its transpose is
    its inverse, and 'turnOf' gives the turn back, scalar first not
    negative, even for half turns."""
    columns = transposed(matrixOf(TURN))
    for axis in range(3):
      self.assertNear(columns[axis], rotated(TURN, AXES[axis]), 1e-15)
    self.assertNear(matrixProduct(matrixOf(TURN),
                                  transposed(matrixOf(TURN))),
                    IDENTITY, 1e-15)
    for turn in (TURN, OTHER, UNTURNED):
      if turn[0] < 0.0:
        turn = tuple(-x for x in turn)
      self.assertNear(turnOf(matrixOf(turn)), turn, 1e-15)
    for axis in AXES:
      half = turnAbout(axis, math.pi)
      self.assertSameTurn(turnOf(matrixOf(half)), half, 1e-15)
