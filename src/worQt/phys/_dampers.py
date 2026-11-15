"""
DamperForces reads how hard the dampers between bodies push them as
they move now (the stepping finds the dampers' pushes with the ties'
and actuators' pulls: 'ConstraintSolver').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._vectors import Vector, cross, plus, scaled

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Damper


class DamperForces:
  """
  DamperForces is 'dampers' on the bodies 'movers' (the world's
  stepping's '_Moving', in the order of the assembly's bodies): each
  pushes its first body at its point and its second as hard the other
  way, as the bodies are and move now.
  """

  def __init__(self, dampers: tuple[Damper, ...], movers: list) -> None:
    self.dampers = dampers
    self.ends = []
    for damper in dampers:
      ends = []
      for index, point in ((damper.first, damper.firstPoint),
                           (damper.second, damper.secondPoint)):
        if index is None:
          ends.append((None, point))
        else:
          mover = movers[index]
          ends.append((mover, mover.inward(point)))
      self.ends.append(tuple(ends))

  def endsNow(self, ) -> list[tuple]:
    """The 'endsNow' method returns each damper's ends as the bodies are
    now: each end where it is in the world, its arm from its body's
    centre (None at the world) and how fast it moves."""
    out = []
    for ends in self.ends:
      now = []
      for mover, arm in ends:
        if mover is None:
          now.append((arm, None, (0.0, 0.0, 0.0)))
          continue
        reach = mover.outward(arm)
        moving = plus(mover.velocity, cross(mover.spin(), reach))
        now.append((plus(mover.place, reach), reach, moving))
      out.append(tuple(now))
    return out

  def forces(self, ) -> dict:
    """The 'forces' method returns the dampers' force and torque about
    its centre on each body they push, keyed by the body's 'id'."""
    out: dict[int, tuple[Vector, Vector]] = {}
    for damper, ends, now in zip(self.dampers, self.ends, self.endsNow()):
      (first, firstArm, firstMoving), (second, secondArm, secondMoving) = now
      push = damper.pushOf(first, second, firstMoving, secondMoving)
      for (mover, _), arm, force in ((ends[0], firstArm, push),
                                     (ends[1], secondArm,
                                      scaled(push, -1.0))):
        if mover is None:
          continue
        had = out.get(id(mover), ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        out[id(mover)] = (plus(had[0], force),
                          plus(had[1], cross(arm, force)))
    return out
