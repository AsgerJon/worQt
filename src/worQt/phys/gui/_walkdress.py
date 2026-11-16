"""
The dresses a walker's GPU view draws in the world each frame, as
'GpuView.dresses' takes them (each a 'quads(states)' of keys to quads,
corners in the world, m, with their normals): 'LegsDress', an
assembly's actuators (a rig's legs, the rods holding a gear or a
bearing) as square bars from end to end, nothing held unseen;
'SkinDress', a skin drawn over hidden bodies (a tyre's rubber over its
lumps), its faces as the bodies lie now, tinted where a lump under them
is; 'TyreDress', cord tyres' rubber over their hidden nodes;
'RamDress', hydraulic rams as barrel and rod; 'HumpDress', the humps
bolted across a turntable, turning with it; 'ParkedDress', the old car
parked on the oval, dressed as its own window dresses it; 'LinksDress',
rods drawn between bodies' points (the stand-in car's links, drawing
only); 'GaugeDress', the needle of the real car's speedometer, turned
for its speed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._dress import _helices, _tubes
from PySide6.QtGui import QColor

from .._carcass import BELT_FROM, rubberAt, tyreSection
from .._vectors import Vector, cross, matrixOf, minus, norm, plus, scaled

#  How many faces round a rod is drawn with ('rodQuads').
ROD_SIDES = 10


class LegsDress:
  """
  LegsDress draws the actuators of 'assembly' as round rods 'thick' m
  across ('rodQuads'), from the point on their first body (or the
  world) to the one on their second, as 'states' have them; but not
  those to the bodies in 'hidden'. Its quads are under the key 'legs'.
  """

  around = None

  def __init__(self, assembly: object, hidden: set, thick: float) -> None:
    self.assembly, self.hidden, self.thick = assembly, set(hidden), thick

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the rods as 'states' have the bodies:
    'ROD_SIDES' quads a rod, a corner a row of its place and normal."""
    bodies = self.assembly.bodies
    out = []
    for leg in self.assembly.actuators:
      if leg.second in self.hidden:
        continue
      head = bodies[leg.second].placeOf(states[leg.second],
                                        leg.secondPoint)
      foot = leg.firstPoint if leg.first is None else bodies[
        leg.first].placeOf(states[leg.first], leg.firstPoint)
      out.extend(rodQuads(foot, head, 0.5 * self.thick))
    if not out:
      return {}
    return {'legs': numpy.array(out, numpy.float64).reshape(-1, 4, 6)}


class GaugeDress:
  """
  GaugeDress draws the needle of the real car's speedometer on its dash
  ('_gauge': user, 2026-11-15, "a diegetic one next to the steering
  wheel"), turned for how fast body 'chassis' goes along its own
  forward as 'states' have it, a thin round rod ('rodQuads') under the
  key 'needle'.
  """

  around = None

  def __init__(self, assembly: object, chassis: int) -> None:
    self.assembly, self.chassis, self.tones = assembly, chassis, {}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the needle as 'states' have the car
    (its speed in km/h, 'needleOf'), in the world."""
    from .._gauge import HALF, needleOf
    from .._vectors import conjugate, rotated
    body, state = self.assembly.bodies[self.chassis], states[self.chassis]
    ahead = rotated(conjugate(state.turn), state.velocity)[0]
    tail, tip = needleOf(3.6 * ahead)
    quads = rodQuads(body.placeOf(state, tail), body.placeOf(state, tip),
                     HALF, 6)
    return {'needle': numpy.array(quads, numpy.float64).reshape(-1, 4, 6)}


class LinksDress:
  """
  LinksDress draws rods between two bodies' points as 'states' have the
  bodies, drawing only (the stand-in car's wishbones, links, struts'
  rods and half shafts: '_magiccar.magicLinks'): each link in 'links'
  its first body and point (in its own frame), its second and point,
  its radius, its key, and how far it reaches from the first's point
  toward the second's (None: all the way), round ('rodQuads'), under
  its key.
  """

  around = None

  def __init__(self, assembly: object, links: tuple) -> None:
    self.assembly, self.links, self.tones = assembly, tuple(links), {}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the rods as 'states' have the bodies,
    by key: 'ROD_SIDES' quads a rod, a corner a row of its place and
    normal."""
    bodies = self.assembly.bodies
    out = {}
    for first, there, second, here, radius, key, reach in self.links:
      start = bodies[first].placeOf(states[first], there)
      end = bodies[second].placeOf(states[second], here)
      if reach is not None:
        way = minus(end, start)
        length = norm(way)
        if length > 0.0:
          end = plus(start, scaled(way, min(1.0, reach / length)))
      out.setdefault(key, []).extend(rodQuads(start, end, radius))
    return {key: numpy.array(quads, numpy.float64).reshape(-1, 4, 6)
            for key, quads in out.items() if quads}


class CoilDress:
  """
  CoilDress draws coil springs as their wire wound round between their
  seats, as 'states' have the bodies (user, 2026-11-14: "make it look
  like a real spring. very visibly"): each coil in 'coils' its first
  body and seat (in its own frame), its second and seat, its radius (to
  the wire's middle), its wire's radius and its turns; the wire's
  turns close up as the seats close. Its quads are under the key
  'coil'.
  """

  around = None

  def __init__(self, assembly: object, coils: tuple) -> None:
    self.assembly, self.coils, self.tones = assembly, tuple(coils), {}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the coils as 'states' have their
    seats: the wire, 'COIL_POINTS' points a turn, 'COIL_SIDES' round;
    coils of as many turns one after another made together
    ('_helices'), in their order."""
    bodies = self.assembly.bodies
    out, run = [], []

    def made() -> None:
      """Makes the coils gathered in 'run' together."""
      if run:
        out.append(_helices(
          numpy.array([coil[0] for coil in run]),
          numpy.array([coil[1] for coil in run]),
          numpy.array([coil[2] for coil in run]),
          numpy.array([coil[3] for coil in run]), run[0][4], COIL_POINTS,
          COIL_SIDES))
        run.clear()

    for first, a, second, b, coil, wire, turns in self.coils:
      if run and run[0][4] != turns:
        made()
      run.append((bodies[first].placeOf(states[first], a),
                  bodies[second].placeOf(states[second], b), coil, wire,
                  turns))
    made()
    if not out:
      return {}
    return {'coil': numpy.concatenate(out)}


#  How finely a coil's wire is drawn: points a turn, sides round.
COIL_POINTS, COIL_SIDES = 18, 8


class RamDress:
  """
  RamDress draws the rams of 'assembly' ('Ram') as hydraulic cylinders,
  as 'states' have their ends: the barrel from the first end ('RAM_BARREL'
  of the way, its radius 'RAM_RADIUS'), the rod out of it to the second
  ('RAM_ROD' round). Its quads are under the keys 'ram' and 'ramrod'.
  """

  around = None

  def __init__(self, assembly: object) -> None:
    self.assembly, self.tones = assembly, {}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the rams' barrels and rods."""
    bodies = self.assembly.bodies
    barrels, rods = [], []
    for ram in self.assembly.rams:
      a = numpy.array(ram.firstPoint if ram.first is None else bodies[
        ram.first].placeOf(states[ram.first], ram.firstPoint))
      b = numpy.array(ram.secondPoint if ram.second is None else bodies[
        ram.second].placeOf(states[ram.second], ram.secondPoint))
      middle = a + RAM_BARREL * (b - a)
      barrels.append((a, middle, RAM_RADIUS, RAM_RADIUS))
      rods.append((middle, b, RAM_ROD, RAM_ROD))
    if not barrels:
      return {}
    return {'ram': _tubes(barrels, 16, True), 'ramrod': _tubes(rods, 12,
                                                              True)}


#  A ram's barrel's share of its length and its radius, its rod's, m.
RAM_BARREL, RAM_RADIUS, RAM_ROD = 0.55, 0.06, 0.025


class HumpDress:
  """
  HumpDress draws the humps bolted to body 'table' of 'assembly' (as its
  'humps', a 'Humps', has them now: 'Hump') on its face 'top' m up its
  axis, turning with it: each its rounded top across, 'HUMP_ACROSS'
  strips, and its ends. Its quads are under the key 'hump', a speck of
  nothing while none are bolted on (the view never makes a mesh anew).
  """

  around = None

  def __init__(self, assembly: object, table: int, humps: object,
               top: float) -> None:
    self.assembly, self.table, self.humps = assembly, table, humps
    self.top, self.tones = top, {}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the humps as the table lies now."""
    body = self.assembly.bodies[self.table]
    state = states[self.table]
    out = []
    for hump in self.humps.humps:
      out.extend(_humpQuads(body, state, hump, self.top))
    if not out:
      speck = body.placeOf(state, (0.0, 0.0, self.top))
      out = [[tuple(speck) + (0.0, 0.0, 1.0)] * 4]
    return {'hump': numpy.array(out, numpy.float64)}


#  How many strips across a hump is drawn in.
HUMP_ACROSS = 12


def _humpQuads(body: object, state: object, hump: object,
               top: float) -> list:
  """Returns 'hump' on 'body' (a turntable as 'state' has it, its face
  'top' up its axis) as quads, each corner its place and normal: its
  top across in strips, its two ends."""
  out_ = (math.cos(hump.angle), math.sin(hump.angle))
  side = (-out_[1], out_[0])

  def at(rho: float, u: float, lift: float) -> Vector:
    """Returns the point 'rho' out and 'u' across, 'lift' over the
    face, in the world."""
    return body.placeOf(state, (rho * out_[0] + u * side[0],
                                rho * out_[1] + u * side[1], top + lift))

  def heightAt(u: float) -> float:
    """Returns how high the hump stands 'u' across its middle."""
    return hump.height * math.cos(math.pi * u / hump.length) ** 2

  quads = []
  across = [hump.length * (k / HUMP_ACROSS - 0.5)
            for k in range(HUMP_ACROSS + 1)]
  for u0, u1 in zip(across, across[1:]):
    corners = (at(hump.inner, u0, heightAt(u0)),
               at(hump.outer, u0, heightAt(u0)),
               at(hump.outer, u1, heightAt(u1)),
               at(hump.inner, u1, heightAt(u1)))
    quads.append(_flatQuad(corners))
  for rho, flip in ((hump.inner, True), (hump.outer, False)):
    ring = [at(rho, u, heightAt(u)) for u in across]
    foot = [at(rho, u, 0.0) for u in across]
    for k in range(HUMP_ACROSS):
      corners = (foot[k], foot[k + 1], ring[k + 1], ring[k])
      if flip:
        corners = corners[::-1]
      quads.append(_flatQuad(corners))
  return quads


def _flatQuad(corners: tuple) -> list:
  """Returns a quad of 'corners' (anticlockwise from outside) with
  their face's normal."""
  normal = cross(minus(corners[1], corners[0]), minus(corners[3],
                                                      corners[0]))
  size = norm(normal)
  normal = (0.0, 0.0, 1.0) if size == 0.0 else scaled(normal, 1.0 / size)
  return [tuple(corner) + tuple(normal) for corner in corners]


class SkinDress:
  """
  SkinDress draws 'skin' (a 'TyreSkin': its 'faces(states)', each its
  part, its corners in the world anticlockwise from outside, and the
  two lumps it lies between) face by face, flat, under its part's key;
  a face over a lump whose tone in 'tones' (index: colour) is one of
  'tints' (key: colour; what the grabber points at, what it holds)
  under that tint's key instead. Every key is there from the first
  frame (a tint with no face a speck of nothing), so the view never
  makes a mesh anew while it walks.
  """

  around = None

  def __init__(self, skin: object, tints: dict) -> None:
    self.skin, self.tints, self.tones = skin, dict(tints), {}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the skin's faces as 'states' have the
    bodies, by key, every tint's key among them."""
    named = {QColor(tone).rgba(): key for key, tone in self.tints.items()}
    out: dict[str, list] = {key: [] for key in self.tints}
    speck = None
    for part, corners, lumps in self.skin.faces(states):
      key = part
      for lump in lumps:
        if lump in self.tones:
          key = named.get(QColor(self.tones[lump]).rgba(), key)
      a, b, c = corners[0], corners[1], corners[2]
      facing = cross(minus(b, a), minus(c, a))
      size = norm(facing)
      normal = scaled(facing, 1.0 / size) if size > 0.0 else (0.0, 0.0,
                                                               1.0)
      out.setdefault(key, []).append([tuple(corner) + normal
                                      for corner in corners[:4]])
      if speck is None:
        speck = [tuple(a) + normal] * 4
    for key in self.tints:
      if not out[key] and speck is not None:
        out[key].append(speck)
    return {key: numpy.array(faces, numpy.float64)
            for key, faces in out.items() if faces}


def rodQuads(a: Vector, b: Vector, half: float, sides: int = ROD_SIDES
             ) -> list:
  """The 'rodQuads' function returns a round rod from 'a' to 'b' of
  radius 'half' (user, 2026-11-15: "make it look proper, not these
  blocky things"), as its 'sides' faces round: quads, each corner its
  place and its own way out from the rod's line (smooth shaded),
  anticlockwise seen from outside; none for a rod of no length."""
  along = minus(b, a)
  length = norm(along)
  if length == 0.0:
    return []
  way = scaled(along, 1.0 / length)
  helper = (0.0, 0.0, 1.0) if abs(way[2]) < 0.9 else (1.0, 0.0, 0.0)
  u = cross(way, helper)
  u = scaled(u, 1.0 / norm(u))
  v = cross(way, u)
  rounds = [plus(scaled(u, math.cos(angle)), scaled(v, math.sin(angle)))
            for angle in (2.0 * math.pi * k / sides for k in range(sides))]
  out = []
  for k in range(sides):
    one, two = rounds[k], rounds[(k + 1) % sides]
    out.append([plus(a, scaled(one, half)) + one,
                plus(a, scaled(two, half)) + two,
                plus(b, scaled(two, half)) + two,
                plus(b, scaled(one, half)) + one])
  return out


class TyreDress:
  """
  TyreDress draws the cord tyres of 'wheels' (each its rim's index and
  its nodes', round by across: 'wheelsOf'): each tyre's rubber as its
  cords' surface ('tyreSurface') in smooth quads, under 'tread' where
  the belts are, else 'tyre'; a tyre whose rim's tone in 'tones' is one
  of 'tints' (key: colour) under that tint's key instead. Every key is
  there from the first frame (a speck of nothing where unused).
  """

  around = None

  def __init__(self, assembly: object, wheels: tuple, tints: dict) -> None:
    self.assembly, self.wheels = assembly, wheels
    self.tints, self.tones = dict(tints), {}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the tyres' rubber as 'states' have the
    bodies, by key, every key among them."""
    named = {QColor(tone).rgba(): key for key, tone in self.tints.items()}
    out: dict[str, list] = {key: [] for key in ('tread', 'tyre')}
    out.update({key: [] for key in self.tints})
    belt = numpy.array([rho >= BELT_FROM for rho, _ in tyreSection()])
    for rim, rows in self.wheels:
      at, normals = tyreSurface(self.assembly, states, rim, rows)
      tint = None
      if rim in self.tones:
        tint = named.get(QColor(self.tones[rim]).rgba())
      quads = _gridQuads(at, normals)
      tread = belt[:-1] & belt[1:]
      count = len(tread)
      kinds = numpy.tile(tread, len(quads) // count)
      if tint is not None:
        out[tint].append(quads)
        continue
      out['tread'].append(quads[kinds])
      out['tyre'].append(quads[~kinds])
    speck = numpy.zeros((1, 4, 6))
    speck[:, :, 5] = 1.0
    return {key: numpy.concatenate(parts) if parts and sum(
      len(part) for part in parts) else speck for key, parts in out.items()}

  def hitOf(self, states: tuple, eye: tuple,
            direction: tuple) -> tuple | None:
    """The 'hitOf' method returns where the ray from 'eye' along
    'direction' first meets a tyre's rubber: its wheel's rim, the point
    and the rubber's outward normal there; None where it meets none."""
    best = None
    origin, way = numpy.array(eye), numpy.array(direction)
    for rim, rows in self.wheels:
      at, normals = tyreSurface(self.assembly, states, rim, rows)
      middle = at.reshape(-1, 3).mean(axis=0)
      offset = middle - origin
      along = float(offset @ way)
      if numpy.linalg.norm(offset - along * way) > 0.4:
        continue
      quads = _gridQuads(at, normals)
      for a, b, c in ((0, 1, 2), (0, 2, 3)):
        p0, p1, p2 = (quads[:, k, :3] for k in (a, b, c))
        e1, e2 = p1 - p0, p2 - p0
        h = numpy.cross(way, e2)
        det = numpy.einsum('ij,ij->i', e1, h)
        good = numpy.abs(det) > 1e-12
        f = numpy.where(good, 1.0 / numpy.where(good, det, 1.0), 0.0)
        sv = origin - p0
        u = f * numpy.einsum('ij,ij->i', sv, h)
        q = numpy.cross(sv, e1)
        v = f * (q @ way)
        t = f * numpy.einsum('ij,ij->i', e2, q)
        hit = good & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0) & (t > 0.0)
        if not hit.any():
          continue
        k = int(numpy.argmin(numpy.where(hit, t, numpy.inf)))
        if best is None or t[k] < best[0]:
          normal = quads[k, 0, 3:]
          best = (float(t[k]), rim, tuple(origin + t[k] * way),
                  tuple(float(x) for x in normal))
    if best is None:
      return None
    return best[1], best[2], best[3]


def tyreSurface(assembly: object, states: tuple, rim: int,
                rows: tuple) -> tuple[numpy.ndarray, numpy.ndarray]:
  """The 'tyreSurface' function returns a cord tyre's rubber as 'states'
  have its rim (at 'rim') and nodes ('rows', round by across): its
  points round by across (the beads on the rim, then the nodes) moved
  out from the cords by the rubber's thickness there, and the surface's
  outward normals there (numpy, round by across by three)."""
  section = tyreSection()
  rimState = states[rim]
  centre = numpy.array(assembly.bodies[rim].centre)
  turn = numpy.array(matrixOf(rimState.turn))
  around = len(rows)
  beads = numpy.empty((around, 2, 3))
  for i in range(around):
    a = 2.0 * math.pi * i / around
    for side, (r, w) in enumerate((section[0], section[-1])):
      beads[i, side] = (r * math.cos(a), r * math.sin(a), w)
  beads = (beads - centre) @ turn.T + numpy.array(rimState.place)
  nodes = numpy.array([[states[k].place for k in row] for row in rows])
  at = numpy.concatenate((beads[:, :1], nodes, beads[:, 1:]), axis=1)
  radii = numpy.array([rubberAt(r) for r, _ in section])
  aroundWay = numpy.roll(at, -1, axis=0) - numpy.roll(at, 1, axis=0)
  acrossWay = numpy.empty_like(at)
  acrossWay[:, 1:-1] = at[:, 2:] - at[:, :-2]
  acrossWay[:, 0] = at[:, 1] - at[:, 0]
  acrossWay[:, -1] = at[:, -1] - at[:, -2]
  normals = numpy.cross(aroundWay, acrossWay)
  normals /= numpy.maximum(numpy.linalg.norm(normals, axis=2,
                                             keepdims=True), 1e-12)
  crown = at[0, at.shape[1] // 2] - numpy.array(rimState.place)
  if float(normals[0, at.shape[1] // 2] @ crown) < 0.0:
    normals = -normals
  return at + normals * radii[None, :, None], normals


def _gridQuads(at: numpy.ndarray, normals: numpy.ndarray) -> numpy.ndarray:
  """Returns a closed-round grid's quads (round by across), each corner
  its place and normal, wound anticlockwise seen along the normals."""
  after = numpy.roll(numpy.arange(len(at)), -1)
  corners = [(slice(None), slice(None, -1)), (after, slice(None, -1)),
             (after, slice(1, None)), (slice(None), slice(1, None))]
  quads = numpy.empty((len(at), at.shape[1] - 1, 4, 6))
  for k, (i, j) in enumerate(corners):
    quads[:, :, k, :3] = at[i][:, j]
    quads[:, :, k, 3:] = normals[i][:, j]
  quads = quads.reshape(-1, 4, 6)
  facing = numpy.cross(quads[:, 1, :3] - quads[:, 0, :3],
                       quads[:, 3, :3] - quads[:, 0, :3])
  if float(numpy.einsum('ij,ij->', facing, quads[:, 0, 3:])) < 0.0:
    quads = quads[:, ::-1]
  return quads


class ParkedDress:
  """
  ParkedDress draws the old car parked on the oval ('_realoval.
  parkedCar': the springs' world's car, every body still) dressed as its
  own window dresses it ('CarDress': wishbones, links, coilovers, half
  shafts), finely, once: it stands as parked. Its quads are under its
  keys with 'old ' before them (its own colours: '_walk.OVAL_LOOKS').
  """

  around = None

  def __init__(self, ) -> None:
    from .._realoval import parkedCar
    from ._dress import FINE, CarDress
    car, states = parkedCar()
    self.tones = {}
    self.drawn = {'old ' + key: quads for key, quads in CarDress(
      car, FINE).quads(states).items()}

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the parked car's dress, the same
    arrays each time (nothing of it moves)."""
    return self.drawn
