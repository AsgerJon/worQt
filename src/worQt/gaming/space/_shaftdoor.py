"""
ShaftDoor is one of the top floor's four doors (user, 2026-11-19: "the
top floor has four doors in each direction ... We then pick either of
the four of our doors to enter a particular elevator on terra prime"):
a leaf of 'LEAF_MASS' kg in the head's wall ('_levels.TOP_DOORS': door
'k' out along '_levels.DOOR_WAYS[k]'), sliding round the rocket's axis
into the wall (a pocket door, 'POCKET'), on its motor ('_hoist.hoisted',
as the main door's, '_door'), pulled along its way as the cabin pulls
there, pushed by what is in its way (Asger: '_cabinworld.CabinWorld.
struck'); closing, pushed back harder than its motor, it opens again.
It opens only docked (its doorway then leads over the gap into the
station's shaft; undocked, to space): docked, its leaf is a solid in the
cabin's world ('boxOf') and the doorway is always there behind it.
Qt-free, the rocket's own axes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._hoist import hoisted
from ._levels import DOOR_ANGLES, DOOR_HALF_HIGH, DOOR_HALF_SPAN
from ._levels import DOORS_HIGH, HEAD, WALL
from ._turns import aboutAxis, product, quaternionOf

#  The leaf: its mass, kg; as thick as the wall less a hair, m; half its
#  span round the wall, rad; its middle's distance from the rocket's
#  axis (the wall's middle), m; how far round it slides opening (its
#  span and a degree), rad; how far its middle goes, m.
LEAF_MASS = 60.0
LEAF_THICK = WALL - 0.01
HALF_SPAN = math.radians(DOOR_HALF_SPAN)
MIDDLE_FAR = HEAD - 0.5 * WALL
POCKET = 2.0 * HALF_SPAN + math.radians(1.0)
TRAVEL = POCKET * MIDDLE_FAR
#  Its motor (as the main door's): its most push along its way, N; how
#  fast it speeds up and slows, m/s²; the fastest it goes, m/s.
MOTOR_MOST = 150.0
ACCEL = 2.0
FAST = 1.0
#  The leaf's half sizes (across the wall, round it, up it), m.
HALVES = (0.5 * LEAF_THICK, MIDDLE_FAR * math.sin(HALF_SPAN),
          DOOR_HALF_HIGH)


class ShaftDoor:
  """
  ShaftDoor holds top floor door 'k''s leaf: how far it has gone round
  from shut ('arc', m, nought to 'TRAVEL'), how fast it goes (m/s, the
  opening way), the stop its motor drives it to ('target': None, its
  latch holds it where it is). 'opened' and 'closed' work it, each
  returning why not ('' done); 'moved' moves it on; 'boxOf' is its leaf
  as a solid; 'share' how far open it is (the scene slides the leaf by
  it: 'leafTurnOf').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('arc', 'speed', 'target')

  #  Public Variables
  k: int
  arc: float
  speed: float
  target: float | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, k: int) -> None:
    if k not in range(len(DOOR_ANGLES)):
      raise ValueError('no top floor door %r' % (k,))
    self.k, self.arc, self.speed, self.target = int(k), 0.0, 0.0, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def share(self, ) -> float:
    """The 'share' property is how far open it is (nought shut, one
    open)."""
    return self.arc / TRAVEL

  @property
  def wanted(self, ) -> bool:
    """The 'wanted' property says whether it is opening or held open."""
    if self.target is None:
      return self.arc > 0.5 * TRAVEL
    return self.target > 0.5 * TRAVEL

  @property
  def shut(self, ) -> bool:
    """The 'shut' property says whether it is closed and held so."""
    return self.target is None and self.arc <= 1e-6

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def opened(self, docked: bool) -> str:
    """The 'opened' method sends it open, 'docked' (else it would open
    to space); returns why not ('' it opens)."""
    if not docked:
      return 'not docked: it would open to space'
    if self.wanted:
      return 'the door is open'
    self.target = TRAVEL
    return ''

  def closed(self, ) -> str:
    """The 'closed' method sends it shut (what is in its way stops it);
    returns why not ('' it closes)."""
    if not self.wanted:
      return 'the door is closed'
    self.target = 0.0
    return ''

  def moved(self, seconds: float, along: float, push: float) -> float:
    """The 'moved' method moves it 'seconds' s on: pushed 'push' N s along
    its way (opening) by what was in its way over the last frame, its
    motor driving it to its stop, pulled 'along' m/s² along its way; the
    wall's pocket and its frame stop it at either end; latched at a stop
    it does not move. Returns how fast it sped up along its way (m/s²,
    on the average: the rocket feels its leaf's moving)."""
    if seconds <= 0.0:
      return 0.0
    began = self.speed
    if self.target is not None:
      self.speed += push / LEAF_MASS
      if self.target < self.arc and push > MOTOR_MOST * seconds:
        self.target = TRAVEL
    self.arc, self.speed, self.target, _ = hoisted(
      self.arc, self.speed, self.target, seconds, along, LEAF_MASS,
      MOTOR_MOST, ACCEL, FAST)
    if self.arc < 0.0 or self.arc > TRAVEL:
      self.arc = min(TRAVEL, max(0.0, self.arc))
      self.speed = 0.0
    return (self.speed - began) / seconds

  def boxOf(self, ) -> tuple:
    """The 'boxOf' method returns its leaf as a solid: its middle, half
    sizes (across the wall, round it, up it), turn (w x y z) and
    velocity."""
    way, middle = self.wayAt()
    return middle, HALVES, self.turn(), tuple(self.speed * w for w in way)

  def turn(self, ) -> tuple:
    """The 'turn' method returns its leaf's turn: its own axes (across
    the wall outward, round the axis the way it opens, up the wall) to
    the rocket's, slid round the axis as far as it has gone."""
    return product(leafTurnOf(self.share), _shutTurn(self.k))

  def wayAt(self, ) -> tuple:
    """The 'wayAt' method returns the way its middle goes opening (a unit
    vector, the rocket's own axes) and its middle."""
    a = math.radians(DOOR_ANGLES[self.k]) + self.arc / MIDDLE_FAR
    middle = (MIDDLE_FAR * math.cos(a), MIDDLE_FAR * math.sin(a),
              DOORS_HIGH)
    return (-math.sin(a), math.cos(a), 0.0), middle


def leafTurnOf(share: float) -> tuple:
  """Returns a top floor door's leaf's turn 'share' of the way open: slid
  round the rocket's axis into the wall."""
  return aboutAxis((0.0, 0.0, 1.0), share * POCKET)


def shaftLeafRows(k: int) -> tuple:
  """Returns top floor door 'k''s leaf shut, in the wall's cut (the
  rocket's own axes; it slides about the axis, 'leafTurnOf'): its outer
  face, its inner face and its edges, in steps round: rows (place,
  normal) and triangles."""
  middle = math.radians(DOOR_ANGLES[k])
  steps = 8
  angles = [middle - HALF_SPAN + 2.0 * HALF_SPAN * j / steps
            for j in range(steps + 1)]
  low = DOORS_HIGH - DOOR_HALF_HIGH + 0.004
  high = DOORS_HIGH + DOOR_HALF_HIGH - 0.004
  outer, inner = HEAD - 0.003, HEAD - WALL + 0.003
  rows, faces = [], []

  def quad(corners: list, normal: tuple) -> None:
    first = len(rows)
    for corner in corners:
      rows.append(tuple(corner) + tuple(normal))
    a, b, c = (numpy.array(corners[j]) for j in range(3))
    if float(numpy.dot(numpy.cross(b - a, c - a), normal)) >= 0.0:
      faces.extend((first, first + 1, first + 2, first, first + 2,
                    first + 3))
    else:
      faces.extend((first, first + 2, first + 1, first, first + 3,
                    first + 2))

  def at(angle: float, z: float, far: float) -> tuple:
    return far * math.cos(angle), far * math.sin(angle), z

  for b0, b1 in zip(angles[:-1], angles[1:]):
    c = math.cos(0.5 * (b0 + b1))
    s = math.sin(0.5 * (b0 + b1))
    quad([at(b0, low, outer), at(b1, low, outer), at(b1, high, outer),
          at(b0, high, outer)], (c, s, 0.0))
    quad([at(b0, low, inner), at(b1, low, inner), at(b1, high, inner),
          at(b0, high, inner)], (-c, -s, 0.0))
    for z, up in ((low, -1.0), (high, 1.0)):
      quad([at(b0, z, inner), at(b1, z, inner), at(b1, z, outer),
            at(b0, z, outer)], (0.0, 0.0, up))
  for b, sign in ((angles[0], -1.0), (angles[-1], 1.0)):
    normal = (-sign * math.sin(b), sign * math.cos(b), 0.0)
    quad([at(b, low, inner), at(b, low, outer), at(b, high, outer),
          at(b, high, inner)], normal)
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _shutTurn(k: int) -> tuple:
  """Returns door 'k''s leaf's turn shut: across the wall (outward),
  round the axis the way it opens, up the wall."""
  a = math.radians(DOOR_ANGLES[k])
  c, s = math.cos(a), math.sin(a)
  return quaternionOf(((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0)))

