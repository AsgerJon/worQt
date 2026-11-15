"""
A car's tyre, built from what it is made of, on its steel wheel. The
tread and its steel belt are a ring of lumps ('Tyre.nodes' of them),
each held to the rim by the sidewalls, four rubber springs from it to
the two beads, on each laced ahead and behind as a bicycle wheel's
spokes are (so the tyre bears the load, side pushes and the wheel's
twist, every way: two crossed springs alone left the belt free to
screw round and along the axle), and to its neighbours by the belt, a
stiff rubber spring along each chord. Every
lump meets the ground, the tread's rubber the ground's law. The air is
in the sidewalls' stiffness, set for one pressure, not a body apart.
A lump does not turn on its own: its turning is the belt's, which holds
it, so it is given a moment far beyond its own and, in the patch, it
grips instead of rolling as a free ball would.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._assembly import Spring
from ._body import Body, State
from ._shape import Sphere
from ._turned import Turned
from ._vectors import Vector, minus, norm, plus

#  A lump's moment, kg m²: far beyond a lump's own (~1e-4), so it does
#  not turn on its own (see the module's text).
_STEADY = 100.0


class Tyre(NamedTuple):
  """
  Tyre is a car's tyre as built: 'outside' its diameter and 'width' its
  section's width (m), on a rim of 'bead' diameter and 'seat' width
  between its flanges; 'nodes' lumps of tread and belt, each 'lump' (m)
  deep to the tread's face and of 'mass' (kg, all of them together:
  the tread, the belt and half the sidewalls); each of its four
  sidewall springs of 'sidewall' N/m damped 'sidewallDamping' N s/m,
  laced 'lacing' lumps ahead or behind; each belt spring of 'belt' N/m
  damped
  'beltDamping'. 'TYRE' is a 205/55 R16 at 2.3 bar on a 6.5 x 16 steel
  wheel.
  """

  outside: float
  width: float
  bead: float
  seat: float
  nodes: int
  lump: float
  mass: float
  sidewall: float
  sidewallDamping: float
  belt: float
  beltDamping: float
  lacing: int

  def node(self, ) -> Body:
    """The 'node' method returns one lump of tread and belt: a ball as
    deep as the lump, of its share of the mass, not turning on its
    own."""
    steady = ((_STEADY, 0.0, 0.0), (0.0, _STEADY, 0.0),
              (0.0, 0.0, _STEADY))
    return Body(self.mass / self.nodes, (0.0, 0.0, 0.0), steady,
                Sphere(self.lump))

  def angleOf(self, index: int) -> float:
    """The 'angleOf' method returns where round the wheel lump 'index'
    sits, rad from the wheel's own x axis."""
    return 2.0 * math.pi * index / self.nodes

  def nodeAt(self, index: int) -> Vector:
    """The 'nodeAt' method returns the middle of lump 'index' in the
    wheel's own frame (unloaded)."""
    reach, angle = 0.5 * self.outside - self.lump, self.angleOf(index)
    return reach * math.cos(angle), reach * math.sin(angle), 0.0

  def beadAt(self, index: int, side: int, lace: int) -> Vector:
    """The 'beadAt' method returns where a sidewall spring of lump
    'index' is held on the bead on 'side' (1 the wheel's own +z side,
    -1 the other), in the wheel's own frame: 'lacing' lumps ahead
    ('lace' 1) or behind (-1)."""
    angle = self.angleOf(index + lace * self.lacing)
    reach = 0.5 * self.bead
    return (reach * math.cos(angle), reach * math.sin(angle),
            side * 0.5 * self.seat)

  def springsOf(self, wheel: int, first: int) -> tuple[Spring, ...]:
    """The 'springsOf' method returns the tyre's springs, the wheel
    body 'wheel' and the lumps from 'first' on: each lump's four
    sidewall springs, then the belt round."""
    out = []
    for index in range(self.nodes):
      middle = self.nodeAt(index)
      for side in (1, -1):
        for lace in (1, -1):
          bead = self.beadAt(index, side, lace)
          out.append(Spring(wheel, bead, first + index, (0.0, 0.0, 0.0),
                            self.sidewall, norm(minus(middle, bead)),
                            self.sidewallDamping))
    chord = norm(minus(self.nodeAt(1), self.nodeAt(0)))
    for index in range(self.nodes):
      following = first + (index + 1) % self.nodes
      out.append(Spring(first + index, (0.0, 0.0, 0.0), following,
                        (0.0, 0.0, 0.0), self.belt, chord,
                        self.beltDamping))
    return tuple(out)

  def statesOn(self, wheel: Body, state: State) -> tuple[State, ...]:
    """The 'statesOn' method returns the lumps' states, unloaded, on
    'wheel' in 'state': each where it sits on it, moving with it."""
    out = []
    for index in range(self.nodes):
      place = wheel.placeOf(state, self.nodeAt(index))
      arm = minus(place, state.place)
      moving = plus(state.velocity, _crossed(state.spin, arm))
      out.append(State(place, state.turn, moving))
    return tuple(out)


def _crossed(a: Vector, b: Vector) -> Vector:
  """Returns 'a' x 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])


def steelWheel(tyre: Tyre, offset: float, reach: float,
               sides: int) -> Turned:
  """The 'steelWheel' function returns a pressed steel wheel for 'tyre'
  turned about its own z axis, the tyre's middle at z nought: the rim
  a 3.2 mm band under the beads, its flanges 4 mm thick and 15 mm high
  outside the seat, the disc 6 mm thick with its outer face 'offset' m
  toward +z (the wheel's offset, ET), and the hub, 70 mm across with a
  35 mm bore, from the disc 'reach' m in toward -z (where the bearing
  holds it)."""
  seat, half = 0.5 * tyre.bead, 0.5 * tyre.seat
  under, flange, edge = seat - 0.0032, seat + 0.015, half + 0.004
  hub, bore = 0.035, 0.0175
  inside, outside = offset - 0.006, offset
  points = ((bore, outside), (bore, -reach), (hub, -reach),
            (hub, inside), (under, inside), (under, -edge),
            (flange, -edge), (flange, -half), (seat, -half),
            (seat, half), (flange, half), (flange, edge), (under, edge),
            (under, outside))
  profile = tuple(('line', points[k], points[(k + 1) % len(points)])
                  for k in range(len(points)))
  turned = Turned(profile, sides)
  if turned.volume() < 0.0:
    profile = tuple(('line', b, a) for _, a, b in reversed(profile))
    turned = Turned(profile, sides)
  return turned


class TyreSkin(NamedTuple):
  """
  TyreSkin is how 'tyre' looks on 'wheel' (its place in the assembly
  'wheelIndex', its lumps from 'first' on): the tread, a band as wide
  as the rubber meets the road ('tread' m, across), over the lumps'
  faces, and each sidewall from on top of the rim's flange (a hair in
  from its face, so the two never lie in one plane) out to the tyre's
  full width halfway and in to the tread's edge, a face between each two
  lumps; drawn from where the lumps are, so it shows the tyre as it
  gives (the patch flat on the road, the sidewalls bulging).
  """

  tyre: Tyre
  wheel: Body
  wheelIndex: int
  first: int
  tread: float

  def faces(self, states: tuple) -> list[tuple[str, list, tuple]]:
    """The 'faces' method returns the skin as 'states' have the bodies:
    each face's part ('tread' or 'side'), its corners in the world,
    anticlockwise seen from outside, and the two lumps it lies between
    (their places in the assembly)."""
    out = []
    for group in self._groups(states):
      out.extend(group)
    return out

  def outlines(self, states: tuple) -> list[list[Vector]]:
    """The 'outlines' method returns the skin's points between each two
    lumps, a group each (their shadows outlined make the tyre's)."""
    return [[corner for _, corners, _ in group for corner in corners]
            for group in self._groups(states)]

  def hitOf(self, states: tuple, eye: Vector,
            direction: Vector) -> tuple | None:
    """The 'hitOf' method returns where the ray from 'eye' along
    'direction' first meets the skin, as 'hitOf' gives a body: the lump
    nearer the point (of the two the face lies between), the point and
    the face's outward normal; None if it misses. A grab or a punt at
    the tyre so takes the lump under the rubber there."""
    best, found = math.inf, None
    for _, corners, lumps in self.faces(states):
      a, b, c, d = corners
      for one, two in ((b, c), (c, d)):
        along = _rayMeets(eye, direction, a, one, two)
        if along is not None and along < best:
          normal = _crossed(minus(b, a), minus(c, a))
          size = norm(normal)
          best, found = along, (lumps, _scaledBy(normal, 1.0 / size))
    if found is None:
      return None
    point = plus(eye, _scaledBy(direction, best))
    lumps, normal = found
    nearer = min(lumps, key=lambda lump: norm(minus(
      states[lump].place, point)))
    return nearer, point, normal

  def _groups(self, states: tuple) -> list[list[tuple[str, list]]]:
    """Returns the skin's faces between each two lumps, a group each."""
    tyre, wheel = self.tyre, self.wheel
    state = states[self.wheelIndex]
    middle = wheel.placeOf(state, (0.0, 0.0, 0.0))
    axis = minus(wheel.placeOf(state, (0.0, 0.0, 1.0)), middle)
    flange = 0.5 * tyre.bead + 0.016
    edge, wide = 0.5 * tyre.seat + 0.002, 0.5 * tyre.width
    rows = []
    for index in range(tyre.nodes):
      at = states[self.first + index].place
      away = minus(at, middle)
      across = _dotted(away, axis)
      out = minus(away, _scaledBy(axis, across))
      size = norm(out)
      outward = _scaledBy(out, 1.0 / size) if size > 0.0 else axis
      face = plus(at, _scaledBy(outward, tyre.lump))
      angle = tyre.angleOf(index)
      row = {}
      for side in (1, -1):
        rim = wheel.placeOf(state, (flange * math.cos(angle),
                                    flange * math.sin(angle),
                                    side * edge))
        treadEdge = plus(face, _scaledBy(axis, side * 0.5 * self.tread))
        halfway = _scaledBy(plus(rim, treadEdge), 0.5)
        sideways = side * wide - _dotted(minus(halfway, middle), axis)
        row[side] = (rim, plus(halfway, _scaledBy(axis, sideways)),
                     treadEdge)
      rows.append((row, outward))
    groups = []
    for index in range(tyre.nodes):
      following = (index + 1) % tyre.nodes
      (one, outward), (two, _) = rows[index], rows[following]
      lumps = (self.first + index, self.first + following)
      group = [_facing('tread', [one[1][2], one[-1][2], two[-1][2],
                                 two[1][2]], outward, lumps)]
      for side in (1, -1):
        sideways = _scaledBy(axis, side)
        for low, high in ((0, 1), (1, 2)):
          group.append(_facing('side', [one[side][low], one[side][high],
                                        two[side][high], two[side][low]],
                               sideways, lumps))
      groups.append(group)
    return groups


def _dotted(a: Vector, b: Vector) -> float:
  """Returns 'a' dot 'b'."""
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _scaledBy(a: Vector, factor: float) -> Vector:
  """Returns 'a' times 'factor'."""
  return a[0] * factor, a[1] * factor, a[2] * factor


def _facing(part: str, corners: list, outward: Vector,
            lumps: tuple) -> tuple:
  """Returns 'part', 'corners' turned round, if need be, to go
  anticlockwise seen from 'outward' of them, and 'lumps'."""
  a, b, c = corners[0], corners[1], corners[2]
  facing = _crossed(minus(b, a), minus(c, a))
  if _dotted(facing, outward) < 0.0:
    corners = corners[::-1]
  return part, corners, lumps


def _rayMeets(eye: Vector, direction: Vector, a: Vector, b: Vector,
              c: Vector) -> float | None:
  """Returns how far along 'direction' (times its length) the ray from
  'eye' meets the triangle 'a', 'b', 'c' ahead of it, or None
  (Moller and Trumbore's)."""
  ab, ac = minus(b, a), minus(c, a)
  across = _crossed(direction, ac)
  det = _dotted(ab, across)
  if abs(det) < 1e-15:
    return None
  away = minus(eye, a)
  u = _dotted(away, across) / det
  if u < 0.0 or u > 1.0:
    return None
  turned = _crossed(away, ab)
  v = _dotted(direction, turned) / det
  if v < 0.0 or u + v > 1.0:
    return None
  along = _dotted(ac, turned) / det
  return along if along > 0.0 else None


#  The 205/55 R16 at 2.3 bar: 632 mm across, 205 wide, on a 16 in rim
#  6.5 in wide; 32 lumps of 20 mm, 7 kg of the tyre's 8.5 in them (the
#  rest in the rim's share of the sidewalls); four sidewall springs a
#  lump of 50 kN/m, damped 12.5 N s/m (~0.09 of critical), laced one
#  lump round; belt springs 100 kN/m, damped 20 (the belt sets the
#  step, 26 us: stiffer, it would be shorter). On the road, the axle 18
#  mm down, it carries ~3.6 kN (a quarter of a 1400 kg car).
TYRE = Tyre(0.632, 0.205, 0.4064, 0.165, 32, 0.02, 7.0, 5e4, 12.5, 1e5,
            20.0, 1)
