"""
Body is a rigid body, any shape, and State where it is and how it
moves: its six degrees of freedom.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

import numpy

from ._shape import Shape
from ._vectors import ORIGIN, UNTURNED, Matrix, Quaternion, Vector
from ._vectors import applied, cross, dot, matrixOf, matrixProduct, minus
from ._vectors import plus, rotated, scaled, transposed, turnOf


#  The bodies whose principal axes were found lately, and what was found.
_PRINCIPAL: list = []
_KEPT = 64


class State(NamedTuple):
  """
  State is where a body is and how it moves, in the world's frame:
  'place', where its centre of mass is, m; 'turn', how its own frame is
  turned (a unit quaternion, scalar first); 'velocity' of its centre,
  m/s; 'spin', its angular velocity, rad/s. Six degrees of freedom.
  And what holds it: 'bristles', each the index of a point of its shape
  touching the ground and where on the ground it is held to, x and y,
  least index first; 'holds', each the index of a point of its shape
  touching another body, that body's place in the assembly, and where
  on it the point is held to, x y z in its own frame, least first; and
  'rest', how long it has been still, s (a world that lets bodies sleep
  puts it to sleep once that is long enough: 'Sleep').
  """

  place: Vector = ORIGIN
  turn: Quaternion = UNTURNED
  velocity: Vector = ORIGIN
  spin: Vector = ORIGIN
  bristles: tuple[tuple[int, float, float], ...] = ()
  holds: tuple[tuple[int, int, float, float, float], ...] = ()
  rest: float = 0.0


class Body(NamedTuple):
  """
  Body is a rigid body: its 'mass', kg; its 'centre' of mass in its own
  frame, m; its 'inertia' about that centre along its own axes, kg m²
  (symmetric, three rows); and its 'shape' in its own frame, None for a
  body known only by its mass and inertia.
  """

  mass: float
  centre: Vector
  inertia: Matrix
  shape: Shape = None

  @classmethod
  def of(cls, shape: Shape, density: float) -> Body:
    """The 'of' method returns the body 'shape' makes, solid, of one
    stuff 'density' kg/m³. A shape not closed, or inside out, is
    refused."""
    if not shape.isClosed():
      raise ValueError('the shape is not closed')
    volume, first, second = shape.moments()
    if volume <= 0.0:
      raise ValueError('the shape is inside out')
    centre = scaled(first, 1.0 / volume)
    spread = [[second[i][j] - volume * centre[i] * centre[j]
               for j in range(3)] for i in range(3)]
    trace = spread[0][0] + spread[1][1] + spread[2][2]
    inertia = tuple(tuple(density * ((trace if i == j else 0.0)
                                     - spread[i][j]) for j in range(3))
                    for i in range(3))
    return cls(density * volume, centre, inertia, shape)

  def principal(self, ) -> tuple[Vector, Quaternion]:
    """The 'principal' method returns the body's principal moments of
    inertia, least first, and the turn from its principal axes to its
    own: its own frame's matrix of that turn has the principal axes as
    columns. A moment not above nought is refused."""
    for kept, found in _PRINCIPAL:
      if kept is self:
        return found
    found = self.principalAxes()
    _PRINCIPAL.insert(0, (self, found))
    del _PRINCIPAL[_KEPT:]
    return found

  def principalAxes(self, ) -> tuple[Vector, Quaternion]:
    """The 'principalAxes' method returns what 'principal' does, found
    anew."""
    values, vectors = numpy.linalg.eigh(numpy.array(self.inertia))
    if values[0] <= 0.0:
      raise ValueError('a principal moment of inertia is not above 0')
    if numpy.linalg.det(vectors) < 0.0:
      vectors[:, 2] = -vectors[:, 2]
    columns = tuple(tuple(float(v) for v in row) for row in vectors)
    moments = (float(values[0]), float(values[1]), float(values[2]))
    return moments, turnOf(columns)

  def placeOf(self, state: State, point: Vector) -> Vector:
    """The 'placeOf' method returns where 'point', given in the body's
    own frame, is in the world as the body is in 'state'."""
    return plus(state.place, rotated(state.turn, minus(point, self.centre)))

  def velocityOf(self, state: State, point: Vector) -> Vector:
    """The 'velocityOf' method returns how fast 'point', given in the
    body's own frame, moves in the world as the body is in 'state'."""
    arm = rotated(state.turn, minus(point, self.centre))
    return plus(state.velocity, cross(state.spin, arm))

  def inertiaIn(self, state: State) -> Matrix:
    """The 'inertiaIn' method returns the body's inertia about its
    centre along the world's axes as it is turned in 'state'."""
    turning = matrixOf(state.turn)
    return matrixProduct(matrixProduct(turning, self.inertia),
                         transposed(turning))

  def momentumOf(self, state: State) -> Vector:
    """The 'momentumOf' method returns the body's momentum in 'state',
    kg m/s."""
    return scaled(state.velocity, self.mass)

  def angularMomentumOf(self, state: State) -> Vector:
    """The 'angularMomentumOf' method returns the body's angular
    momentum about its centre in 'state', kg m²/s, in the world's
    frame."""
    return applied(self.inertiaIn(state), state.spin)

  def kineticOf(self, state: State) -> float:
    """The 'kineticOf' method returns the body's kinetic energy in
    'state', moving and turning, J."""
    moving = 0.5 * self.mass * dot(state.velocity, state.velocity)
    return moving + 0.5 * dot(state.spin, self.angularMomentumOf(state))
