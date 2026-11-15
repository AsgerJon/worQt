"""
CarDress draws the car's moving parts as they are now, Qt-free: what
hangs between its bodies (the wishbones' rods, the tie rods and toe
links, the coilovers, the halfshafts, the drag link and the rack's
guides), made anew each frame from where the bodies are, bigger and
brighter than life where it helps them be seen (user: "Most
importantly: suspension. Make that more visible even if more
cartoonish"), but each where it acts and as long as it is: a coilover's
spring is a helix from its perch to its top, closing as the coilover
closes, its damper a body and a shaft sliding in it, its buffer a
rubber stop on the shaft that meets the damper's body just as the
buffer starts to push; its foot forked about the halfshaft.

Each part is quads (four corners and their normals, in the world, a
triangle as a quad with its last corner twice), keyed by how it looks
('arm', 'chrome', 'rubber', 'spring', 'damper', 'shaft'); 'detail'
says how finely ('FINE' for the GPU, 'COARSE' for the painter).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

import numpy

from .._car import TRAVEL, CarBuild
from .._vectors import rotated


class Detail(NamedTuple):
  """
  Detail is how finely the parts are drawn: a rod's 'sides', a ball's
  'rings' and 'round', a spring's 'perTurn' points and its wire's
  'wire' sides, whether rods' ends are capped ('caps') and the least
  ball drawn ('least', m).
  """

  sides: int
  rings: int
  round: int
  perTurn: int
  wire: int
  caps: bool
  least: float


FINE = Detail(12, 5, 10, 20, 6, True, 0.0)
COARSE = Detail(5, 2, 4, 6, 3, False, 0.02)

#  The wishbones' rods and the brace between each pair, their bushings
#  (radius, length) and ball joints; the tie rods and toe links and their
#  balls; the rack's guides, m.
_ARM, _BRACE, _BUSH, _JOINT = 0.016, 0.011, (0.026, 0.07), 0.028
_LINK, _LINK_BALL, _GUIDE = 0.011, 0.018, 0.006
#  The coilover: the spring's radius (to its wire's middle), its wire's
#  radius, its turns; the fork's half width, its prongs' radius and how
#  high it reaches; the damper's body and shaft; the perches (radius,
#  thickness); the buffer's rubber stop (radius, length); the eyes.
_COIL, _WIRE, _TURNS = 0.052, 0.011, 6
_FORK, _PRONG, _FORK_HIGH = 0.068, 0.009, 0.17
_BODY, _SHAFT, _PERCH, _STOP, _EYE = (0.028, 0.011, (0.066, 0.012),
                                      (0.024, 0.05), 0.024)
#  The halfshafts and their joints' boots (radius at the joint, at the
#  shaft, length).
_HALFSHAFT, _BOOT = 0.017, (0.045, 0.02, 0.09)


class CarDress:
  """
  CarDress draws 'car''s moving parts ('quads'), as finely as 'detail'
  says; a skin for 'PhysView' too (its quads by key; 'outlines').
  """

  #  How far from the chassis the parts reach at most, m (a view draws
  #  them within that of it).
  around = 3.0

  def __init__(self, car: CarBuild, detail: Detail) -> None:
    self.car, self.detail = car, detail
    connections = car.assembly.connections
    self.longs = tuple(connections[index + 1].rest - TRAVEL
                       for index in car.links.coilovers)

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the parts as they are in 'states', by
    how they look: each an array of quads (n, 4, 6: a corner's place and
    its normal)."""
    parts = _Parts(self.detail)
    links = self.car.links
    for corner in range(4):
      for pair in (links.uppers[corner], links.lowers[corner]):
        self._wishbone(parts, states, pair)
      self._link(parts, states, links.steers[corner])
      self._coilover(parts, states, corner)
    for index in range(len(links.halfshafts)):
      self._halfshaft(parts, states, index)
    self._link(parts, states, links.drag)
    for index in links.guides:
      a, b = self._ends(states, index)
      parts.tube('chrome', a, b, _GUIDE, _GUIDE, False)
    return parts.quads()

  def outlines(self, states: tuple) -> list:
    """The 'outlines' method returns no shadows (as a skin's: the parts
    cast none in the painter's view)."""
    return []

  def _ends(self, states: tuple, index: int) -> tuple:
    """Returns the ends of connection 'index' (a spring) in the world
    now."""
    spring = self.car.assembly.connections[index]
    bodies = self.car.assembly.bodies
    return tuple(numpy.array(bodies[body].placeOf(states[body], point))
                 for body, point in ((spring.first, spring.firstPoint),
                                     (spring.second, spring.secondPoint)))

  def _wishbone(self, parts: _Parts, states: tuple, pair: tuple) -> None:
    """Adds a wishbone: its two rods, a brace across them, a bushing at
    each inner end along the line of its pivots, the ball joint where
    they meet."""
    caps = self.detail.caps
    (a0, b0), (a1, b1) = (self._ends(states, index) for index in pair)
    for a, b in ((a0, b0), (a1, b1)):
      parts.tube('arm', a, b, _ARM, _ARM, caps)
    parts.tube('arm', a0 + 0.45 * (b0 - a0), a1 + 0.45 * (b1 - a1),
               _BRACE, _BRACE, False)
    way = _unit(a1 - a0)
    for a in (a0, a1):
      parts.tube('rubber', a - 0.5 * _BUSH[1] * way,
                 a + 0.5 * _BUSH[1] * way, _BUSH[0], _BUSH[0], True)
    parts.ball('chrome', 0.5 * (b0 + b1), _JOINT)

  def _link(self, parts: _Parts, states: tuple, index: int) -> None:
    """Adds a rod with a ball at each end (a tie rod, a toe link, the
    drag link)."""
    a, b = self._ends(states, index)
    parts.tube('chrome', a, b, _LINK, _LINK, self.detail.caps)
    for end in (a, b):
      parts.ball('chrome', end, _LINK_BALL)

  def _coilover(self, parts: _Parts, states: tuple, corner: int) -> None:
    """Adds the coilover at 'corner': its fork about the halfshaft, the
    damper's body, the perches, the spring between them, the shaft, the
    buffer's stop and the eyes at its ends."""
    caps = self.detail.caps
    car = self.car
    top, foot = self._ends(states, car.links.coilovers[corner])
    long = self.longs[corner]
    up = _unit(top - foot)
    knuckle = car.knuckles[corner]
    across = numpy.array(rotated(states[knuckle].turn, (1.0, 0.0, 0.0)))
    across = _unit(across - numpy.dot(across, up) * up)
    reach = long - TRAVEL - (_STOP[1] + _PERCH[1]) - _FORK_HIGH
    yoke = foot + _FORK_HIGH * up
    side = _FORK * across
    for a, b, radius in ((foot - side, foot + side, _PRONG),
                         (foot - side, yoke - side, _PRONG),
                         (foot + side, yoke + side, _PRONG),
                         (yoke - side, yoke + side, 1.3 * _PRONG)):
      parts.tube('damper', a, b, radius, radius, caps)
    parts.tube('damper', yoke, yoke + reach * up, _BODY, _BODY, True)
    low = yoke + 0.025 * up
    high = top - _PERCH[1] * up
    for a in (low, high):
      parts.tube('chrome', a, a + _PERCH[1] * up, _PERCH[0], _PERCH[0],
                 True)
    parts.helix('spring', low + _PERCH[1] * up, high)
    shaft = long + TRAVEL - _FORK_HIGH - reach + 0.03
    parts.tube('chrome', top, top - shaft * up, _SHAFT, _SHAFT, caps)
    parts.tube('rubber', high, high - _STOP[1] * up, _STOP[0], _STOP[0],
               True)
    for end in (top, foot):
      parts.ball('chrome', end, _EYE)

  def _halfshaft(self, parts: _Parts, states: tuple, index: int) -> None:
    """Adds the 'index'th halfshaft (of the driven wheels): the shaft, a
    boot over each joint."""
    assembly = self.car.assembly
    shaft = assembly.connections[self.car.links.halfshafts[index]]
    inner, outer = (numpy.array(assembly.bodies[body].placeOf(
      states[body], point)) for body, point in (
      (shaft.first, shaft.firstPoint), (shaft.second, shaft.secondPoint)))
    way = _unit(outer - inner)
    wide, narrow, long = _BOOT
    parts.tube('shaft', inner + long * way, outer - long * way,
               _HALFSHAFT, _HALFSHAFT, False)
    parts.tube('rubber', inner, inner + long * way, wide, narrow, True)
    parts.tube('rubber', outer, outer - long * way, wide, narrow, True)


class _Parts:
  """
  _Parts gathers the rods, balls and springs to draw, by how they look,
  and makes them into quads all at once ('quads').
  """

  def __init__(self, detail: Detail) -> None:
    self.detail = detail
    self.tubes, self.balls, self.helices = {}, {}, {}

  def tube(self, key: str, a: numpy.ndarray, b: numpy.ndarray, ra: float,
           rb: float, caps: bool) -> None:
    """Adds a round rod, a cone from 'ra' at 'a' to 'rb' at 'b', its ends
    closed with 'caps' (when the detail closes any)."""
    caps = caps and self.detail.caps
    self.tubes.setdefault((key, caps), []).append((a, b, ra, rb))

  def ball(self, key: str, middle: numpy.ndarray, radius: float) -> None:
    """Adds a ball (none smaller than the detail's 'least')."""
    if radius >= self.detail.least:
      self.balls.setdefault(key, []).append((middle, radius))

  def helix(self, key: str, a: numpy.ndarray, b: numpy.ndarray) -> None:
    """Adds a coilover's spring from 'a' to 'b'."""
    self.helices.setdefault(key, []).append((a, b))

  def quads(self, ) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns all that was added as quads by how they
    look, as finely as the detail says."""
    detail = self.detail
    out: dict[str, list] = {}
    for (key, caps), tubes in self.tubes.items():
      out.setdefault(key, []).append(_tubes(tubes, detail.sides, caps))
    for key, balls in self.balls.items():
      template = _ballOf(detail.rings, detail.round)
      middles = numpy.array([middle for middle, _ in balls])
      radii = numpy.array([radius for _, radius in balls])
      quads = numpy.empty((len(balls),) + template.shape)
      quads[..., :3] = (middles[:, None, None, :]
                        + radii[:, None, None, None]
                        * template[None, ..., :3])
      quads[..., 3:] = template[None, ..., 3:]
      out.setdefault(key, []).append(quads.reshape(-1, 4, 6))
    for key, helices in self.helices.items():
      for a, b in helices:
        out.setdefault(key, []).append(_helix(a, b, _COIL, _WIRE, _TURNS,
                                              detail.perTurn, detail.wire))
    return {key: numpy.concatenate(parts) for key, parts in out.items()}


def _unit(vector: numpy.ndarray) -> numpy.ndarray:
  """Returns 'vector' made a unit."""
  return vector / numpy.linalg.norm(vector)


def _square(ways: numpy.ndarray) -> tuple:
  """Returns, for each of the units 'ways' (n, 3), two units square to
  it and to each other, right handed with it."""
  other = numpy.where((numpy.abs(ways[:, 0]) < 0.9)[:, None],
                      numpy.array((1.0, 0.0, 0.0)),
                      numpy.array((0.0, 1.0, 0.0)))
  first = numpy.cross(ways, other)
  first /= numpy.linalg.norm(first, axis=1)[:, None]
  return first, numpy.cross(ways, first)


def _tubes(tubes: list, sides: int, caps: bool) -> numpy.ndarray:
  """Returns round rods (each a cone: 'a', 'b', 'ra', 'rb') as quads,
  'sides' round, smooth; with 'caps' their ends closed (fans, flat)."""
  a = numpy.array([tube[0] for tube in tubes])
  b = numpy.array([tube[1] for tube in tubes])
  ra = numpy.array([tube[2] for tube in tubes])[:, None, None]
  rb = numpy.array([tube[3] for tube in tubes])[:, None, None]
  along = b - a
  length = numpy.linalg.norm(along, axis=1)
  way = along / length[:, None]
  first, second = _square(way)
  angles = 2.0 * math.pi * numpy.arange(sides + 1) / sides
  out = (numpy.cos(angles)[None, :, None] * first[:, None, :]
         + numpy.sin(angles)[None, :, None] * second[:, None, :])
  slope = ((ra - rb)[:, 0, 0] / length)[:, None, None]
  normals = out + slope * way[:, None, :]
  normals /= numpy.linalg.norm(normals, axis=2)[:, :, None]
  ringA, ringB = a[:, None, :] + ra * out, b[:, None, :] + rb * out
  quads = numpy.empty((len(tubes), sides, 4, 6))
  quads[:, :, 0, :3], quads[:, :, 1, :3] = ringA[:, :-1], ringA[:, 1:]
  quads[:, :, 2, :3], quads[:, :, 3, :3] = ringB[:, 1:], ringB[:, :-1]
  quads[:, :, 0, 3:], quads[:, :, 1, 3:] = normals[:, :-1], normals[:, 1:]
  quads[:, :, 2, 3:], quads[:, :, 3, 3:] = normals[:, 1:], normals[:, :-1]
  if not caps:
    return quads.reshape(-1, 4, 6)
  fans = numpy.empty((len(tubes), 2, sides, 4, 6))
  fans[:, 0, :, 0, :3] = a[:, None, :]
  fans[:, 0, :, 1, :3], fans[:, 0, :, 2, :3] = ringA[:, 1:], ringA[:, :-1]
  fans[:, 0, :, :, 3:] = -way[:, None, None, :]
  fans[:, 1, :, 0, :3] = b[:, None, :]
  fans[:, 1, :, 1, :3], fans[:, 1, :, 2, :3] = ringB[:, :-1], ringB[:, 1:]
  fans[:, 1, :, :, 3:] = way[:, None, None, :]
  fans[:, :, :, 3, :3] = fans[:, :, :, 2, :3]
  return numpy.concatenate((quads.reshape(-1, 4, 6),
                            fans.reshape(-1, 4, 6)))


_BALLS: dict = {}


def _ballOf(rings: int, round_: int) -> numpy.ndarray:
  """Returns a ball of radius one about nought as quads, 'rings' from
  pole to pole, 'round_' about, smooth (its poles' quads triangles);
  made once for each fineness."""
  if (rings, round_) in _BALLS:
    return _BALLS[rings, round_]
  down = math.pi * numpy.arange(rings + 1) / rings
  about = 2.0 * math.pi * numpy.arange(round_ + 1) / round_
  ways = numpy.stack((numpy.sin(down)[:, None] * numpy.cos(about),
                      numpy.sin(down)[:, None] * numpy.sin(about),
                      numpy.cos(down)[:, None] * numpy.ones_like(about)),
                     axis=2)
  corners = numpy.stack((ways[:-1, :-1], ways[1:, :-1], ways[1:, 1:],
                         ways[:-1, 1:]), axis=2).reshape(-1, 4, 3)
  quads = numpy.empty((len(corners), 4, 6))
  quads[:, :, :3] = corners
  quads[:, :, 3:] = corners
  quads[:round_] = quads[:round_][:, (0, 1, 2, 2)]
  quads[-round_:] = quads[-round_:][:, (0, 1, 3, 3)]
  _BALLS[rings, round_] = quads
  return quads


def _helices(a: numpy.ndarray, b: numpy.ndarray, coil: numpy.ndarray,
             wire: numpy.ndarray, turns: int, perTurn: int,
             sides: int) -> numpy.ndarray:
  """Returns coil springs' wires as quads, as '_helix' makes each, one
  coil after another, all in one go ('a', 'b' (c, 3) their ends, 'coil',
  'wire' (c,) their radii, alike in 'turns', 'perTurn' and 'sides'):
  the same sums on every coil at once (four coils made one by one were
  half the walk window's frame: numpy's every call's own cost)."""
  along = b - a
  first, second = _square(along / numpy.linalg.norm(along, axis=1)[:, None])
  count = turns * perTurn + 1
  t = numpy.arange(count) / (count - 1)
  turn = 2.0 * math.pi * turns * t
  radial = (numpy.cos(turn)[None, :, None] * first[:, None, :]
            + numpy.sin(turn)[None, :, None] * second[:, None, :])
  middles = (a[:, None, :] + t[None, :, None] * along[:, None, :]
             + coil[:, None, None] * radial)
  ahead = numpy.gradient(middles, axis=1)
  ahead /= numpy.linalg.norm(ahead, axis=2)[:, :, None]
  binormal = numpy.cross(ahead, radial)
  binormal /= numpy.linalg.norm(binormal, axis=2)[:, :, None]
  normal = numpy.cross(binormal, ahead)
  angles = 2.0 * math.pi * numpy.arange(sides + 1) / sides
  ways = (numpy.cos(angles)[None, None, :, None] * normal[:, :, None, :]
          + numpy.sin(angles)[None, None, :, None] * binormal[:, :, None, :])
  rings = middles[:, :, None, :] + wire[:, None, None, None] * ways
  quads = numpy.empty((len(a), count - 1, sides, 4, 6))
  quads[:, :, :, 0, :3] = rings[:, :-1, :-1]
  quads[:, :, :, 0, 3:] = ways[:, :-1, :-1]
  quads[:, :, :, 1, :3] = rings[:, :-1, 1:]
  quads[:, :, :, 1, 3:] = ways[:, :-1, 1:]
  quads[:, :, :, 2, :3] = rings[:, 1:, 1:]
  quads[:, :, :, 2, 3:] = ways[:, 1:, 1:]
  quads[:, :, :, 3, :3] = rings[:, 1:, :-1]
  quads[:, :, :, 3, 3:] = ways[:, 1:, :-1]
  return quads.reshape(-1, 4, 6)


def _helix(a: numpy.ndarray, b: numpy.ndarray, coil: float, wire: float,
           turns: int, perTurn: int, sides: int) -> numpy.ndarray:
  """Returns a coil spring's wire from 'a' to 'b' as quads: a helix
  'coil' round its axis, 'turns' turns, its wire 'wire' thick, 'perTurn'
  points a turn and 'sides' round, smooth."""
  along = b - a
  first, second = (way[0] for way in _square(_unit(along)[None, :]))
  count = turns * perTurn + 1
  t = numpy.arange(count) / (count - 1)
  turn = 2.0 * math.pi * turns * t
  radial = (numpy.cos(turn)[:, None] * first
            + numpy.sin(turn)[:, None] * second)
  middles = a + t[:, None] * along + coil * radial
  ahead = numpy.gradient(middles, axis=0)
  ahead /= numpy.linalg.norm(ahead, axis=1)[:, None]
  binormal = numpy.cross(ahead, radial)
  binormal /= numpy.linalg.norm(binormal, axis=1)[:, None]
  normal = numpy.cross(binormal, ahead)
  angles = 2.0 * math.pi * numpy.arange(sides + 1) / sides
  ways = (numpy.cos(angles)[None, :, None] * normal[:, None, :]
          + numpy.sin(angles)[None, :, None] * binormal[:, None, :])
  rings = middles[:, None, :] + wire * ways
  quads = numpy.empty((count - 1, sides, 4, 6))
  quads[:, :, 0, :3], quads[:, :, 0, 3:] = rings[:-1, :-1], ways[:-1, :-1]
  quads[:, :, 1, :3], quads[:, :, 1, 3:] = rings[:-1, 1:], ways[:-1, 1:]
  quads[:, :, 2, :3], quads[:, :, 2, 3:] = rings[1:, 1:], ways[1:, 1:]
  quads[:, :, 3, :3], quads[:, :, 3, 3:] = rings[1:, :-1], ways[1:, :-1]
  return quads.reshape(-1, 4, 6)
