"""
SolarSystem is Sol and every heavenly body round it (user, 2026-11-16:
"the Sun the star, provides the origin of the coordinate system"; "just
put in the 9 planets around Terra, and yes, Pluto *is* a fucking
planet!"): where each is from any other, and how they pull a vessel.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._heavenlybody import HeavenlyBody

#  How far past a body's reach a vessel goes before it is kept from the
#  body's parent again, a share of the reach: going in at the reach and
#  out a little past it, a vessel on the edge is not passed back and
#  forth every frame.
OUTWARD = 1.02


class SolarSystem:
  """
  SolarSystem holds the heavenly bodies ('bodies', Sol first, each
  parent before its children; each body by its index). Gravity runs
  down its tree alone (user: "gravity affects only from planet pulled to
  sun, moons pulled to planet, vehicles/Asger pulled to any"): each body
  is pulled by its parent only, a vessel by every body. Where one body
  is from another is summed along the tree from their nearest common
  forebear ('relative'): nothing is ever taken from Sol and back, so the
  numbers stay as small as the bodies are near. 'version' counts the
  leaps folded in ('fold'). Its 'satellites' are made things on rails
  round a body (a space station: user, 2026-11-17, "We are going to
  have a space station in orbit"): each a 'HeavenlyBody' that pulls
  nothing and holds nothing near it, folded with the bodies.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  bodies: tuple
  parents: tuple
  version: int
  satellites: list

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, bodies: tuple) -> None:
    bodies = tuple(bodies)
    if not bodies or bodies[0].parent is not None:
      raise ValueError('a solar system starts with its star')
    parents = []
    for index, body in enumerate(bodies):
      if body.parent is None:
        if index:
          raise ValueError('%s goes round nothing' % body.name)
        parents.append(-1)
        continue
      if body.parent not in bodies[:index]:
        raise ValueError('%s comes before its parent' % body.name)
      parents.append(bodies.index(body.parent))
    self.bodies, self.parents, self.version = bodies, tuple(parents), 0
    self.satellites = []

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def named(self, name: str) -> int:
    """The 'named' method returns the index of the body called 'name'."""
    for index, body in enumerate(self.bodies):
      if body.name == name:
        return index
    raise KeyError('no heavenly body is called %r' % name)

  def children(self, index: int) -> tuple:
    """The 'children' method returns the indices of the bodies going
    round body 'index'."""
    return tuple(k for k, parent in enumerate(self.parents)
                 if parent == index)

  def relative(self, body: int, to: int, t: float) -> tuple:
    """The 'relative' method returns where body 'body' is and how fast it
    moves from body 'to' at time 't' (s): two triples, m and m/s, in the
    ecliptic's axes."""
    place, speed = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    bodies, parents = self.bodies, self.parents
    a, b = body, to
    while bodies[a].depth > bodies[b].depth:
      self._added(place, speed, a, t, 1.0)
      a = parents[a]
    while bodies[b].depth > bodies[a].depth:
      self._added(place, speed, b, t, -1.0)
      b = parents[b]
    while a != b:
      self._added(place, speed, a, t, 1.0)
      self._added(place, speed, b, t, -1.0)
      a, b = parents[a], parents[b]
    return tuple(place), tuple(speed)

  def pullOn(self, anchor: int, place: tuple, t: float) -> tuple:
    """The 'pullOn' method returns how a vessel at 'place' (m, from body
    'anchor', the ecliptic's axes) is pulled at time 't', m/s², as it is
    seen from its anchor: every body's pull on it, less the anchor's own
    fall (its parent's pull on it, and its parent's fall). The flight's
    kernel holds to this."""
    out = [0.0, 0.0, 0.0]
    for index, body in enumerate(self.bodies):
      there = self.relative(index, anchor, t)[0]
      _pulled(out, body.mu, there, place)
    child = anchor
    while self.parents[child] >= 0:
      parent = self.parents[child]
      there = self.relative(parent, child, t)[0]
      fall = [0.0, 0.0, 0.0]
      _pulled(fall, self.bodies[parent].mu, there, (0.0, 0.0, 0.0))
      out = [a - b for a, b in zip(out, fall)]
      child = parent
    return tuple(out)

  def anchorFor(self, anchor: int, place: tuple, t: float) -> int:
    """The 'anchorFor' method returns the body a vessel at 'place' (m,
    from body 'anchor') is kept from: a child of the anchor's when
    within its reach, the anchor's parent once past the anchor's reach
    (by 'OUTWARD'), else the anchor."""
    for child in self.children(anchor):
      there = self.relative(child, anchor, t)[0]
      if math.dist(there, place) < self.bodies[child].reach:
        return child
    reach = self.bodies[anchor].reach
    if self.parents[anchor] >= 0 and math.sqrt(sum(
        x * x for x in place)) > OUTWARD * reach:
      return self.parents[anchor]
    return anchor

  def fold(self, seconds: float) -> None:
    """The 'fold' method carries 'seconds' s into every body and
    satellite (a leap): what was at time 'seconds' is at time nought."""
    for body in self.bodies:
      body.fold(seconds)
    for satellite in self.satellites:
      satellite.fold(seconds)
    self.version += 1

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _added(self, place: list, speed: list, index: int, t: float,
             sign: float) -> None:
    """Adds body 'index''s place and velocity from its parent at 't',
    times 'sign', to 'place' and 'speed'."""
    there, moving = self.bodies[index].stateAt(t)
    for k in range(3):
      place[k] += sign * there[k]
      speed[k] += sign * moving[k]


def _pulled(out: list, mu: float, there: tuple, place: tuple) -> None:
  """Adds the pull at 'place' toward a body of G M 'mu' at 'there' to
  'out', m/s² (none at its very middle)."""
  d = tuple(a - b for a, b in zip(there, place))
  size2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
  if size2 == 0.0:
    return
  scale = mu / (size2 * math.sqrt(size2))
  for k in range(3):
    out[k] += scale * d[k]
