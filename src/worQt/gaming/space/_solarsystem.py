"""
SolarSystem is Sol and every heavenly body round it (user, 2026-11-16:
"the Sun the star, provides the origin of the coordinate system"; "just
put in the 9 planets around Terra, and yes, Pluto *is* a fucking
planet!"): where each is from any other, and how they pull a vessel.
Their paths are flown, each pulling every other (user, 2026-11-18:
real gravity, "PHYSICS MUST BE REAL": '_ephemeris').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._conic import Conic

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._ephemeris import Ephemeris
  from ._heavenlybody import HeavenlyBody

#  How far past a body's reach a vessel goes before it is kept from the
#  body's parent again, a share of the reach: going in at the reach and
#  out a little past it, a vessel on the edge is not passed back and
#  forth every frame.
OUTWARD = 1.02


class SolarSystem:
  """
  SolarSystem holds the heavenly bodies ('bodies', Sol first, each
  parent before its children; each body by its index) and their flown
  paths ('ephemeris': each pulling every other). Where one body is from
  another is summed along the tree from their nearest common forebear
  ('relative'): nothing is ever taken from Sol and back, so the numbers
  stay as small as the bodies are near. A vessel is pulled by every
  body ('pullOn'). Its 'satellites' are made things flown round a body
  (the space station: '_station'), listed for the views and folded with
  it. 'version' counts the leaps folded in ('fold'); at
  each the bodies' paths drawn (their 'conic', the ellipse each
  follows from then on as if nothing else pulled it: the map's lines,
  their reach) are taken anew from where they are.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  bodies: tuple
  parents: tuple
  version: int
  ephemeris: Ephemeris
  satellites: list

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, bodies: tuple, ephemeris: Ephemeris) -> None:
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
    if tuple(parents) != ephemeris.parents:
      raise ValueError('the ephemeris flies another tree')
    self.bodies, self.parents, self.version = bodies, tuple(parents), 0
    self.ephemeris, self.satellites = ephemeris, []
    self._osculated()

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

  def stateOf(self, index: int, t: float) -> tuple:
    """The 'stateOf' method returns where body 'index' is from its parent
    and how fast it moves at time 't' (s since the last leap; the sky
    flown on to it first, if it is not yet: '_ephemeris'): two triples,
    m and m/s; Sol's are nought."""
    if index == 0:
      return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    if t > self.ephemeris.end:
      self.ephemeris.coveredTo(t)
    return self.ephemeris.stateOf(index, t)

  def coveredTo(self, t: float) -> None:
    """The 'coveredTo' method has the bodies flown on to time 't' (and
    some way past: '_ephemeris.AHEAD')."""
    self.ephemeris.coveredTo(t)

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
    fall (every other body's pull on the anchor). The flight's kernel
    holds to this."""
    out = [0.0, 0.0, 0.0]
    for index, body in enumerate(self.bodies):
      there = self.relative(index, anchor, t)[0]
      _pulled(out, body.mu, there, place)
      if index != anchor:
        fall = [0.0, 0.0, 0.0]
        _pulled(fall, body.mu, there, (0.0, 0.0, 0.0))
        out = [a - b for a, b in zip(out, fall)]
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
    """The 'fold' method carries 'seconds' s into every body (a leap):
    what was at time 'seconds' is at time nought; the bodies' drawn
    paths taken anew from where they are then."""
    self.ephemeris.coveredTo(seconds)
    self.ephemeris.fold(seconds)
    for body in self.bodies:
      body.fold(seconds)
    for satellite in self.satellites:
      satellite.fold(seconds)
    self.ephemeris.trimmed(0.0)
    self._osculated()
    self.version += 1

  def restored(self, kept: dict) -> None:
    """The 'restored' method flies its paths anew from what a saved game
    kept of them ('Ephemeris.kept'), its drawn paths taken anew."""
    self.ephemeris.keptFrom(kept)
    self.ephemeris.coveredTo(0.0)
    self._osculated()
    self.version += 1

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _osculated(self, ) -> None:
    """Takes each body's drawn path anew from where it is at time
    nought: the ellipse (or hyperbola) it and its parent alone would
    follow, their G M summed."""
    for index, body in enumerate(self.bodies):
      if index == 0:
        continue
      place, speed = self.stateOf(index, 0.0)
      mu = self.bodies[self.parents[index]].mu + body.mu
      body.conic = Conic.fromState(mu, place, speed)

  def _added(self, place: list, speed: list, index: int, t: float,
             sign: float) -> None:
    """Adds body 'index''s place and velocity from its parent at 't',
    times 'sign', to 'place' and 'speed'."""
    there, moving = self.stateOf(index, t)
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
