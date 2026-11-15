"""
SpringForces pushes and pulls bodies by the springs between them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._vectors import Vector, cross, plus, scaled

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Spring


class SpringForces:
  """
  SpringForces is 'springs' on the bodies 'movers' (the world's
  stepping's '_Moving', in the order of the assembly's bodies): each
  pulls its first body at its point and its second as hard the other
  way, as the bodies are now; a damped one ('Spring.damping') pushes
  back by how fast it lengthens as they now move, one spring after the
  other (each seeing the pushes of those before it), the heat booked as
  a damper's.
  """

  def __init__(self, springs: tuple[Spring, ...], movers: list) -> None:
    self.springs = springs
    self.ends = []
    for spring in springs:
      ends = []
      for index, point in ((spring.first, spring.firstPoint),
                           (spring.second, spring.secondPoint)):
        if index is None:
          ends.append((None, point))
        else:
          mover = movers[index]
          ends.append((mover, mover.inward(point)))
      self.ends.append(tuple(ends))

  def endsNow(self, ) -> list[tuple]:
    """The 'endsNow' method returns each spring's ends as the bodies are
    now: each end where it is in the world and its arm from its body's
    centre (None at the world)."""
    out = []
    for ends in self.ends:
      now = []
      for mover, arm in ends:
        if mover is None:
          now.append((arm, None))
          continue
        reach = mover.outward(arm)
        now.append((plus(mover.place, reach), reach))
      out.append(tuple(now))
    return out

  def kick(self, h: float) -> None:
    """The 'kick' method gives the bodies the springs' pulls for 'h'
    s, and the damped ones' pushes."""
    for spring, ends, now in zip(self.springs, self.ends, self.endsNow()):
      (first, firstArm), (second, secondArm) = now
      pull = spring.pullOf(first, second)
      damped = None
      if spring.damping:
        damped = spring.dampedOf(first, second,
                                 _movingOf(ends[0][0], firstArm),
                                 _movingOf(ends[1][0], secondArm))
      if ends[0][0] is not None:
        ends[0][0].pushed(scaled(pull, h), firstArm, None)
        if damped is not None:
          ends[0][0].pushed(scaled(damped, h), firstArm, 'damper')
      if ends[1][0] is not None:
        ends[1][0].pushed(scaled(pull, -h), secondArm, None)
        if damped is not None:
          ends[1][0].pushed(scaled(damped, -h), secondArm, 'damper')

  def forces(self, ) -> dict:
    """The 'forces' method returns the springs' force and torque about
    its centre on each body they pull, keyed by the body's 'id'."""
    out: dict[int, tuple[Vector, Vector]] = {}
    for spring, ends, now in zip(self.springs, self.ends, self.endsNow()):
      (first, firstArm), (second, secondArm) = now
      pull = spring.pullOf(first, second)
      if spring.damping:
        pull = plus(pull, spring.dampedOf(
          first, second, _movingOf(ends[0][0], firstArm),
          _movingOf(ends[1][0], secondArm)))
      for (mover, _), arm, force in ((ends[0], firstArm, pull),
                                     (ends[1], secondArm,
                                      scaled(pull, -1.0))):
        if mover is None:
          continue
        had = out.get(id(mover), ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        out[id(mover)] = (plus(had[0], force),
                          plus(had[1], cross(arm, force)))
    return out


def _movingOf(mover: object, arm: Vector | None) -> Vector:
  """Returns how fast the point at 'arm' (in the world) from the centre
  of 'mover' moves now, or nought for the world's ('mover' None)."""
  if mover is None:
    return 0.0, 0.0, 0.0
  return plus(mover.velocity, cross(mover.spin(), arm))
