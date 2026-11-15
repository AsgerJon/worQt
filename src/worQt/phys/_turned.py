"""
Turned is a solid turned on a lathe: its cross-section, its 'profile',
spun about its own z axis. Its mass and moments are integrated from the
profile exactly; a ball meets it in the cut through the ball's middle
and the axis, where every line and arc of the profile is a contact of
its own. 'outerRing' turns a bearing's outer ring with a gothic arch
groove, 'innerRing' its inner ring, 'onShaft' an inner ring pressed on
a hollow shaft.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._shape import Shape
from ._vectors import Matrix, Vector

#  Gauss and Legendre's five points on -1 to 1, with their weights:
#  exact for polynomials to the ninth power.
_GAUSS = ((-0.9061798459386640, 0.2369268850561891),
          (-0.5384693101056831, 0.4786286704993665),
          (0.0, 0.5688888888888889),
          (0.5384693101056831, 0.4786286704993665),
          (0.9061798459386640, 0.2369268850561891))
#  How many parts an arc is integrated in, and drawn with.
_ARC_PARTS = 32
_ARC_DRAWN = 4
TWO_PI = 2.0 * math.pi


class Turned(NamedTuple):
  """
  Turned is a solid turned on a lathe: 'profile' spun about its own z
  axis, drawn with 'sides' faces round. The profile lies in the half
  plane of the distance from the axis (rho) and the height along it
  (w): a closed loop of pieces, the solid on its left as it is walked,
  each a line, ('line', (rho, w), (rho, w)), or an arc, ('arc', (rho, w)
  its centre, its radius, from angle, to angle) (angles from the rho
  axis toward w, walked either way).
  """

  profile: tuple
  sides: int = 96

  def moments(self, ) -> tuple[float, Vector, Matrix]:
    """The 'moments' method returns the solid's volume, its first moment
    and its second about its frame's origin, integrated over the profile
    (Green's theorem along it, each piece by Gauss and Legendre:
    exact for the lines, to the digit for the arcs)."""
    return _momentsOf(self.profile)

  def volume(self, ) -> float:
    """The 'volume' method returns the solid's volume, m³."""
    return self.moments()[0]

  def centre(self, ) -> Vector:
    """The 'centre' method returns the solid's centre (of one stuff)."""
    volume, first, _ = self.moments()
    return first[0] / volume, first[1] / volume, first[2] / volume

  def isClosed(self, ) -> bool:
    """The 'isClosed' method tells that a turned solid is closed: its
    profile is a closed loop."""
    return True

  def mesh(self, ) -> Shape:
    """The 'mesh' method returns the solid drawn as a closed surface of
    triangles, 'sides' round (its sides flat)."""
    return _meshOf(self)

  def quads(self, ) -> tuple[tuple[int, int, int, int], ...]:
    """The 'quads' method returns the mesh's faces as quadrilaterals,
    each four indices into its points, anticlockwise seen from
    outside."""
    return _quadsOf(self)

  def normals(self, ) -> tuple:
    """The 'normals' method returns, for each of the mesh's 'quads', the
    true surface's outward normal at its four corners (unit, in its own
    frame), as the profile has it: a line's across it, an arc's along
    its radius (outward from a bulge, inward to a hollow), turned to the
    corner's side. Shading by them draws the solid round where it is
    round, its edges sharp where its profile turns a corner."""
    return _normalsOf(self)

  def corners(self, ) -> tuple[Vector, ...]:
    """The 'corners' method returns where the ground may meet the
    solid: the ends of its profile's lines, turned round, 'sides' of
    each."""
    return _cornersOf(self)

  def bounds(self, ) -> tuple[float, float, float, float]:
    """The 'bounds' method returns the least and most distance from the
    axis and the least and most height of the profile."""
    return _boundsOf(self.profile)

  def presses(self, rho: float, w: float,
              radius: float) -> list[tuple[int, float, float, float]]:
    """The 'presses' method returns how a ball of 'radius' whose middle
    is 'rho' from the axis and 'w' up it presses the solid: for each
    piece of the profile it presses, the piece's place in the profile,
    the normal pushing the ball out (along rho and w), and how deep. A
    piece is pressed where the ball's middle lies in front of it (on the
    side away from the solid) nearer than the radius, at the piece's
    nearest point."""
    return pressesOf(self.profile, rho, w, radius)


def outerRing(pitch: float, ball: float, angle: float, hug: float,
              width: float, thickness: float, sides: int) -> Turned:
  """The 'outerRing' function returns a bearing's outer ring for balls
  of diameter 'ball' running on a circle of diameter 'pitch' about its
  axis: 'width' along the axis, 'thickness' out from its bore, the bore
  a little outside the balls' middles (0.45 of their radius), and in it
  a gothic arch groove: two arcs of radius 'hug' times the ball's
  diameter, each touching a ball on the pitch circle at the contact
  angle 90 - 'angle' / 2 degrees from straight across the axis ('angle'
  the V the arch replaces), their centres moved off the ball's middle
  along the contact lines, meeting in a point outside the ball."""
  r, rho = 0.5 * ball, 0.5 * pitch
  alpha = math.radians(90.0 - 0.5 * angle)
  arc = hug * ball
  off = arc - r
  bore, rim, half = rho + 0.45 * r, rho + 0.45 * r + thickness, 0.5 * width
  upper = (rho - off * math.cos(alpha), -off * math.sin(alpha))
  lower = (rho - off * math.cos(alpha), off * math.sin(alpha))
  edge = upper[1] + math.sqrt(arc * arc - (bore - upper[0]) ** 2)
  if edge >= half:
    raise ValueError('the ring is too narrow for its groove')
  apex = upper[0] + math.sqrt(arc * arc - upper[1] * upper[1])
  profile = (
    ('line', (bore, -half), (rim, -half)),
    ('line', (rim, -half), (rim, half)),
    ('line', (rim, half), (bore, half)),
    ('line', (bore, half), (bore, edge)),
    ('arc', upper, arc, math.atan2(edge - upper[1], bore - upper[0]),
     math.atan2(-upper[1], apex - upper[0])),
    ('arc', lower, arc, math.atan2(-lower[1], apex - lower[0]),
     math.atan2(-edge - lower[1], bore - lower[0])),
    ('line', (bore, -edge), (bore, -half)),
  )
  return Turned(profile, sides)


def innerRing(pitch: float, ball: float, angle: float, hug: float,
              width: float, thickness: float, sides: int) -> Turned:
  """The 'innerRing' function returns the inner ring to 'outerRing'
  with the same arguments: its outside a little inside the balls'
  middles (0.45 of their radius), its bore 'thickness' in from there,
  and in its outside the same gothic arch groove facing out: two arcs
  of radius 'hug' times the ball's diameter, each touching a ball on
  the pitch circle at the contact angle either side of straight across
  the axis, their centres moved off the ball's middle along the contact
  lines, meeting in a point inside the ball."""
  r, rho = 0.5 * ball, 0.5 * pitch
  alpha = math.radians(90.0 - 0.5 * angle)
  arc = hug * ball
  off = arc - r
  face, bore, half = rho - 0.45 * r, rho - 0.45 * r - thickness, 0.5 * width
  if bore <= 0.0:
    raise ValueError('the ring is too thick for its pitch')
  upper = (rho + off * math.cos(alpha), -off * math.sin(alpha))
  lower = (rho + off * math.cos(alpha), off * math.sin(alpha))
  edge = upper[1] + math.sqrt(arc * arc - (face - upper[0]) ** 2)
  if edge >= half:
    raise ValueError('the ring is too narrow for its groove')
  apex = upper[0] - math.sqrt(arc * arc - upper[1] * upper[1])
  profile = (
    ('line', (bore, -half), (face, -half)),
    ('line', (face, -half), (face, -edge)),
    ('arc', lower, arc, math.atan2(-edge - lower[1], face - lower[0]),
     math.atan2(-lower[1], apex - lower[0])),
    ('arc', upper, arc, math.atan2(-upper[1], apex - upper[0]),
     math.atan2(edge - upper[1], face - upper[0])),
    ('line', (face, edge), (face, half)),
    ('line', (face, half), (bore, half)),
    ('line', (bore, half), (bore, -half)),
  )
  return Turned(profile, sides)


def onShaft(ring: Turned, inside: float, front: float, back: float,
            places: tuple = (0.0,)) -> Turned:
  """The 'onShaft' function returns 'ring' (an 'innerRing', its bore the
  last piece of its profile) pressed on a hollow shaft as one solid, a
  ring with its middle at each of 'places' (m along the axis, rising):
  the shaft as thick as the bore round a hole of 'inside' radius, from
  'back' behind nought to 'front' before it (both beyond the rings'
  faces; the rings apart). ('onShaftOf' with the ring at every place.)
  """
  places = tuple(places)
  return onShaftOf(tuple(ring for _ in places), inside, front, back,
                   places)


def onShaftOf(rings: tuple, inside: float, front: float, back: float,
              places: tuple) -> Turned:
  """The 'onShaftOf' function returns 'rings' (each an inner ring, its
  bore the last piece of its profile, the bores alike) pressed on a
  hollow shaft as one solid, each with its middle at its place in
  'places' (m along the axis, rising), as 'onShaft' has one ring."""
  places, rings = tuple(places), tuple(rings)
  if len(rings) != len(places) or not rings:
    raise ValueError('a ring for every place')
  spans, bore = [], None
  for ring in rings:
    last = ring.profile[-1]
    (own, high), (_, low) = last[1], last[2]
    if last[0] != 'line' or last[1][0] != last[2][0] or high <= low:
      raise ValueError('the ring\'s bore is not the last of its profile')
    if bore is not None and abs(own - bore) > 1e-12:
      raise ValueError('the rings\' bores differ')
    bore = own
    spans.append((low, high))
  if not inside < bore or not front > places[-1] + spans[-1][1] \
      or not -back < places[0] + spans[0][0]:
    raise ValueError('the shaft does not reach through the rings')
  if any(one + span[1] >= two + nextSpan[0]
         for one, two, span, nextSpan in zip(places, places[1:], spans,
                                             spans[1:])):
    raise ValueError('the rings overlap')
  pieces = [('line', (inside, -back), (bore, -back))]
  start = -back
  for ring, at, (low, high) in zip(rings, places, spans):
    pieces.append(('line', (bore, start), (bore, at + low)))
    pieces.extend(_shifted(piece, at) for piece in ring.profile[:-1])
    start = at + high
  pieces += [('line', (bore, start), (bore, front)),
             ('line', (bore, front), (inside, front)),
             ('line', (inside, front), (inside, -back))]
  return Turned(tuple(pieces), max(ring.sides for ring in rings))


def rollerShape(diameter: float, length: float, sides: int) -> Turned:
  """The 'rollerShape' function returns a cylindrical roller: a solid
  cylinder 'diameter' across and 'length' long along its own z, its
  middle at the origin, drawn 'sides' round (a rectangle turned)."""
  r, half = 0.5 * diameter, 0.5 * length
  return Turned((('line', (0.0, -half), (r, -half)),
                 ('line', (r, -half), (r, half)),
                 ('line', (r, half), (0.0, half)),
                 ('line', (0.0, half), (0.0, -half))), sides)


def rollerOf(shape: object) -> tuple[float, float] | None:
  """The 'rollerOf' function returns the radius and half the length of
  a roller ('rollerShape': a rectangle from the axis turned, its middle
  at the origin), or None for any other shape."""
  if not isinstance(shape, Turned) or len(shape.profile) != 4:
    return None
  if any(piece[0] != 'line' for piece in shape.profile):
    return None
  corners = {piece[1] for piece in shape.profile}
  rhos = sorted({corner[0] for corner in corners})
  ws = sorted({corner[1] for corner in corners})
  if len(corners) != 4 or len(rhos) != 2 or len(ws) != 2:
    return None
  if rhos[0] != 0.0 or abs(ws[0] + ws[1]) > 1e-12 or ws[1] <= 0.0:
    return None
  return rhos[1], ws[1]


def nuOuterRing(pitch: float, roller: float, play: float, width: float,
                rim: float, rib: float, ribWidth: float,
                sides: int) -> Turned:
  """The 'nuOuterRing' function returns the outer ring of a cylindrical
  roller bearing of type NU, for rollers 'roller' across on a circle
  'pitch' across: its raceway a cylinder 'play' m outside the rollers,
  between two ribs (flanges) at its faces, each 'ribWidth' along the
  axis and reaching 'rib' in from the raceway, guiding the rollers'
  ends; its outside 'rim' from the axis, 'width' along it."""
  race = 0.5 * pitch + 0.5 * roller + play
  inner, half = race - rib, 0.5 * width
  if not 0.5 * pitch < inner < race < rim or not 0.0 < ribWidth < half:
    raise ValueError('the ring cannot hold its rollers so')
  return Turned((('line', (inner, -half), (rim, -half)),
                 ('line', (rim, -half), (rim, half)),
                 ('line', (rim, half), (inner, half)),
                 ('line', (inner, half), (inner, half - ribWidth)),
                 ('line', (inner, half - ribWidth), (race, half - ribWidth)),
                 ('line', (race, half - ribWidth), (race, ribWidth - half)),
                 ('line', (race, ribWidth - half), (inner, ribWidth - half)),
                 ('line', (inner, ribWidth - half), (inner, -half))), sides)


def nuInnerRing(pitch: float, roller: float, play: float, width: float,
                bore: float, sides: int) -> Turned:
  """The 'nuInnerRing' function returns the inner ring to 'nuOuterRing':
  a plain cylinder, no ribs, its outside 'play' m inside the rollers on
  the circle 'pitch' across, its bore 'bore' from the axis (the last
  piece of its profile, for 'onShaftOf'), 'width' along the axis: the
  rollers run on it wherever it lies along them, so the shaft it is on
  slides through the bearing (a floating bearing)."""
  race, half = 0.5 * pitch - 0.5 * roller - play, 0.5 * width
  if not 0.0 < bore < race:
    raise ValueError('the ring is too thick for its pitch')
  return Turned((('line', (bore, -half), (race, -half)),
                 ('line', (race, -half), (race, half)),
                 ('line', (race, half), (bore, half)),
                 ('line', (bore, half), (bore, -half))), sides)


def _shifted(piece: tuple, along: float) -> tuple:
  """Returns a piece of a profile moved 'along' m along the axis."""
  if piece[0] == 'line':
    (r0, w0), (r1, w1) = piece[1], piece[2]
    return 'line', (r0, w0 + along), (r1, w1 + along)
  _, (r, w), radius, start, end = piece
  return 'arc', (r, w + along), radius, start, end


def pressesOf(profile: tuple, rho: float, w: float,
              radius: float) -> list[tuple[int, float, float, float]]:
  """The 'pressesOf' function returns 'Turned.presses' for 'profile'."""
  low, high, bottom, top = _boundsOf(profile)
  if (rho < low - radius or rho > high + radius or w < bottom - radius
      or w > top + radius):
    return []
  out = []
  for at, piece in enumerate(profile):
    q, outward = nearestOnPiece(piece, rho, w)
    dr, dw = rho - q[0], w - q[1]
    if dr * outward[0] + dw * outward[1] < 0.0:
      continue
    far = dr * dr + dw * dw
    if far >= radius * radius:
      continue
    apart = math.sqrt(far)
    if apart == 0.0:
      out.append((at, outward[0], outward[1], radius))
    else:
      out.append((at, dr / apart, dw / apart, radius - apart))
  return out


def nearestOnPiece(piece: tuple, rho: float,
                   w: float) -> tuple[tuple[float, float], tuple]:
  """The 'nearestOnPiece' function returns the point of a profile's
  piece nearest ('rho', 'w'), and the piece's outward normal there (to
  the right as it is walked: away from the solid)."""
  if piece[0] == 'line':
    (r0, w0), (r1, w1) = piece[1], piece[2]
    dr, dw = r1 - r0, w1 - w0
    length2 = dr * dr + dw * dw
    share = ((rho - r0) * dr + (w - w0) * dw) / length2
    share = min(1.0, max(0.0, share))
    length = math.sqrt(length2)
    return (r0 + share * dr, w0 + share * dw), (dw / length, -dr / length)
  (cr, cw), radius, a0, a1 = piece[1], piece[2], piece[3], piece[4]
  low, high = min(a0, a1), max(a0, a1)
  angle = math.atan2(w - cw, rho - cr)
  while angle < low:
    angle += TWO_PI
  while angle >= low + TWO_PI:
    angle -= TWO_PI
  if angle > high:
    first = (cr + radius * math.cos(a0), cw + radius * math.sin(a0))
    last = (cr + radius * math.cos(a1), cw + radius * math.sin(a1))
    if ((first[0] - rho) ** 2 + (first[1] - w) ** 2
        <= (last[0] - rho) ** 2 + (last[1] - w) ** 2):
      angle = a0
    else:
      angle = a1
  c, s = math.cos(angle), math.sin(angle)
  way = 1.0 if a1 > a0 else -1.0
  return (cr + radius * c, cw + radius * s), (way * c, way * s)


@functools.lru_cache(maxsize=64)
def _boundsOf(profile: tuple) -> tuple[float, float, float, float]:
  """Returns the least and most rho and w of 'profile' (arcs sampled
  finely, and their ends)."""
  points = _outline(profile, 256)
  return (min(p[0] for p in points), max(p[0] for p in points),
          min(p[1] for p in points), max(p[1] for p in points))


def _outline(profile: tuple, perArc: int) -> list[tuple[float, float]]:
  """Returns the profile as points round it: each line's start, each
  arc's start and 'perArc' - 1 points along it (each piece's end is the
  next one's start)."""
  out = []
  for piece in profile:
    if piece[0] == 'line':
      out.append(piece[1])
      continue
    (cr, cw), radius, a0, a1 = piece[1], piece[2], piece[3], piece[4]
    for k in range(perArc):
      a = a0 + (a1 - a0) * k / perArc
      out.append((cr + radius * math.cos(a), cw + radius * math.sin(a)))
  return out


@functools.lru_cache(maxsize=64)
def _momentsOf(profile: tuple) -> tuple[float, Vector, Matrix]:
  """Returns 'Turned.moments' for 'profile': with Green's theorem, over
  the profile's area, the integrals of rho, rho w, rho³ and rho w² are
  those along its loop of rho²/2, rho² w / 2, rho^4 / 4 and rho² w² / 2
  times dw; then the volume is 2 pi of the first, the first moment along
  the axis 2 pi of the second, the second moment across pi of the third
  and along 2 pi of the fourth."""
  sums = [0.0, 0.0, 0.0, 0.0]
  for piece in profile:
    if piece[0] == 'line':
      (r0, w0), (r1, w1) = piece[1], piece[2]
      parts = ((0.0, 1.0),)

      def at(t: float) -> tuple[float, float, float]:
        """Returns rho, w and dw/dt along the line."""
        return r0 + t * (r1 - r0), w0 + t * (w1 - w0), w1 - w0
    else:
      (cr, cw), radius, a0, a1 = piece[1], piece[2], piece[3], piece[4]
      step = (a1 - a0) / _ARC_PARTS
      parts = tuple((a0 + k * step, a0 + (k + 1) * step)
                    for k in range(_ARC_PARTS))

      def at(a: float) -> tuple[float, float, float]:
        """Returns rho, w and dw/da along the arc."""
        return (cr + radius * math.cos(a), cw + radius * math.sin(a),
                radius * math.cos(a))
    for start, end in parts:
      middle, half = 0.5 * (start + end), 0.5 * (end - start)
      for node, weight in _GAUSS:
        rho, w, dw = at(middle + half * node)
        dw *= weight * half
        rho2 = rho * rho
        sums[0] += 0.5 * rho2 * dw
        sums[1] += 0.5 * rho2 * w * dw
        sums[2] += 0.25 * rho2 * rho2 * dw
        sums[3] += 0.5 * rho2 * w * w * dw
  across, along = math.pi * sums[2], TWO_PI * sums[3]
  return (TWO_PI * sums[0], (0.0, 0.0, TWO_PI * sums[1]),
          ((across, 0.0, 0.0), (0.0, across, 0.0), (0.0, 0.0, along)))


@functools.lru_cache(maxsize=16)
def _meshOf(turned: Turned) -> Shape:
  """Returns 'Turned.mesh' for 'turned'."""
  outline = _outline(turned.profile, _ARC_DRAWN)
  points = []
  for i in range(turned.sides):
    a = TWO_PI * i / turned.sides
    c, s = math.cos(a), math.sin(a)
    points.extend((rho * c, rho * s, w) for rho, w in outline)
  faces = []
  for a, b, d, c in _quadsOf(turned):
    faces.append((a, b, c))
    faces.append((b, d, c))
  return Shape(tuple(points), tuple(faces))


@functools.lru_cache(maxsize=16)
def _quadsOf(turned: Turned) -> tuple:
  """Returns 'Turned.quads' for 'turned': round the sides and along
  the outline, each quad (this side, that side, that side on, this side
  on)."""
  count = len(_outline(turned.profile, _ARC_DRAWN))
  sides = turned.sides
  quads = []
  for i in range(sides):
    j = (i + 1) % sides
    for k in range(count):
      m = (k + 1) % count
      quads.append((i * count + k, j * count + k, j * count + m,
                    i * count + m))
  return tuple(quads)


@functools.lru_cache(maxsize=16)
def _normalsOf(turned: Turned) -> tuple:
  """Returns 'Turned.normals' for 'turned'."""
  ends = []
  for piece in turned.profile:
    if piece[0] == 'line':
      (r0, w0), (r1, w1) = piece[1], piece[2]
      size = math.hypot(r1 - r0, w1 - w0)
      normal = ((w1 - w0) / size, -(r1 - r0) / size)
      ends.append((normal, normal))
      continue
    a0, a1 = piece[3], piece[4]
    way = 1.0 if a1 > a0 else -1.0
    for k in range(_ARC_DRAWN):
      start = a0 + (a1 - a0) * k / _ARC_DRAWN
      end = a0 + (a1 - a0) * (k + 1) / _ARC_DRAWN
      ends.append(((way * math.cos(start), way * math.sin(start)),
                   (way * math.cos(end), way * math.sin(end))))
  sides = turned.sides
  out = []
  for i in range(sides):
    turns = []
    for side in (i, (i + 1) % sides):
      a = TWO_PI * side / sides
      turns.append((math.cos(a), math.sin(a)))
    for (rs, ws), (re, we) in ends:
      out.append(((rs * turns[0][0], rs * turns[0][1], ws),
                  (rs * turns[1][0], rs * turns[1][1], ws),
                  (re * turns[1][0], re * turns[1][1], we),
                  (re * turns[0][0], re * turns[0][1], we)))
  return tuple(out)


@functools.lru_cache(maxsize=16)
def _cornersOf(turned: Turned) -> tuple:
  """Returns 'Turned.corners' for 'turned'."""
  ends = [piece[1] for piece in turned.profile if piece[0] == 'line']
  out = []
  for i in range(turned.sides):
    a = TWO_PI * i / turned.sides
    c, s = math.cos(a), math.sin(a)
    out.extend((rho * c, rho * s, w) for rho, w in ends)
  return tuple(out)
