"""
Door is the rocket's main door (user, 2026-11-18: "And a real door."; it
slid at a set speed, whatever was in its way, and the doorway was a room
or not as it was open or not: "PHYSICS MUST BE REAL"): a leaf of
'LEAF_MASS' kg in the capsule's wall straight behind Asger ('_walkway.
DOOR_SPAN'), sliding round the rocket's axis into the wall (a pocket
door, 'POCKET'), on its motor ('_hoist.hoisted': toward its stop, never
harder than 'MOTOR_MOST' N along its way, slowing to stop on it; at a
stop its latch holds it), pulled along its way as the cabin pulls there,
pushed by what is in its way (Asger: the cabin's world says how hard,
'_cabinworld.CabinWorld.struck'). What holds harder than its motor
stops it; closing, pushed back harder than its motor, it opens again
(as a lift's door does). Its leaf is a solid in the cabin's world
('boxOf'), the doorway always open behind it: it is shut as long as
the leaf is in the way. Qt-free, the rocket's own axes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._cockpit import FLOOR, WALL, capsuleRadius
from ._hoist import hoisted
from ._turns import aboutAxis, product, quaternionOf, rotated
from ._walkway import DOOR_HIGH, DOOR_SPAN, POCKET, SLOPE

#  The leaf (an aluminium honeycomb door): its mass, kg; as thick as
#  the wall less a hair, m; the middle of its span round the wall and
#  half of it, rad; its middle's height and how far it is from the
#  rocket's axis (the wall's middle there), m.
LEAF_MASS = 60.0
LEAF_THICK = WALL - 0.01
MIDDLE_ANGLE = math.radians(0.5 * (DOOR_SPAN[0] + DOOR_SPAN[1]))
HALF_SPAN = math.radians(0.5 * (DOOR_SPAN[1] - DOOR_SPAN[0]))
MIDDLE_HIGH = 0.5 * (FLOOR + DOOR_HIGH)
MIDDLE_FAR = capsuleRadius(MIDDLE_HIGH) - 0.5 * WALL
#  How far its middle goes round from shut to open, m (along its way:
#  round the axis at 'MIDDLE_FAR').
TRAVEL = POCKET * MIDDLE_FAR
#  Its motor: the most it pushes along its way, N (a door's that a hand
#  stops); how fast it speeds up and slows, m/s²; the fastest it goes,
#  m/s (shut to open in some 1.6 s).
MOTOR_MOST = 150.0
ACCEL = 2.0
FAST = 1.0


class Door:
  """
  Door holds the leaf: how far it has gone round from shut ('arc', m,
  nought to 'TRAVEL'), how fast it goes (m/s, opening the way), the
  stop its motor drives it to ('target': None, its latch holds it where
  it is), whether it is locked ('locked'). 'opened', 'closed' and
  'locking' work it, each returning why not ('' done); 'moved' moves it
  on; 'boxOf' is its leaf as a solid; 'share' how far open it is (the
  scene turns the leaf by it).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('arc', 'speed', 'target', 'locked')

  #  Public Variables
  arc: float
  speed: float
  target: float | None
  locked: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, locked: bool) -> None:
    self.arc, self.speed, self.target = 0.0, 0.0, None
    self.locked = bool(locked)

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
    """The 'wanted' property says whether it is opening or held open (its
    motor's stop the open one, or none and open)."""
    if self.target is None:
      return self.arc > 0.5 * TRAVEL
    return self.target > 0.5 * TRAVEL

  @property
  def shut(self, ) -> bool:
    """The 'shut' property says whether it is closed and held so."""
    return self.target is None and self.arc <= 1e-6

  @property
  def passable(self, ) -> bool:
    """The 'passable' property says whether the leaf is clear of the
    doorway (what the Grav-Gun sees through)."""
    return self.share >= 0.97

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def opened(self, ) -> str:
    """The 'opened' method sends it open; returns why not ('' it
    opens)."""
    if self.locked:
      return 'the door is locked'
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

  def locking(self, ) -> str:
    """The 'locking' method locks it, or unlocks it; returns why not (''
    done)."""
    if not self.locked and not self.shut:
      return 'close the door first'
    self.locked = not self.locked
    return ''

  def moved(self, seconds: float, along: float, push: float) -> float:
    """The 'moved' method moves it 'seconds' s on: pushed 'push' N s along
    its way (opening) by what was in its way over the last frame, its
    motor driving it to its stop, pulled 'along' m/s² along its way;
    the wall's pocket and its frame stop it at either end; latched at a
    stop it does not move. Returns how fast it sped up along its way
    (m/s², on the average: the rocket feels its leaf's moving)."""
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
    sizes (across the wall, along it round the axis, up it), turn (w x y
    z) and velocity."""
    way, middle = self.wayAt()
    return middle, _HALVES, self.turn(), tuple(self.speed * w for w in way)

  def turn(self, ) -> tuple:
    """The 'turn' method returns its leaf's turn: its own axes (across
    the wall outward, round the axis the way it opens, up the wall) to
    the rocket's, slid round the axis as far as it has gone."""
    return product(aboutAxis((0.0, 0.0, 1.0), self.arc / MIDDLE_FAR),
                   _SHUT)

  def wayAt(self, ) -> tuple:
    """The 'wayAt' method returns the way its middle goes opening (a unit
    vector, the rocket's own axes) and its middle."""
    slid = aboutAxis((0.0, 0.0, 1.0), self.arc / MIDDLE_FAR)
    return rotated(self.turn(), (0.0, 1.0, 0.0)), rotated(slid, _MIDDLE)


def _shutTurn() -> tuple:
  """Returns the leaf's turn shut: across the wall (outward, leant as
  the cone leans), round the axis the way it opens, up the wall."""
  c, s = math.cos(MIDDLE_ANGLE), math.sin(MIDDLE_ANGLE)
  out = (c, s, 0.0)
  size = math.sqrt(1.0 + SLOPE * SLOPE)
  across = tuple((o - SLOPE * z) / size for o, z in zip(out, (0, 0, 1)))
  up = tuple((SLOPE * o + z) / size for o, z in zip(out, (0, 0, 1)))
  round_ = (-s, c, 0.0)
  return quaternionOf(tuple((across[k], round_[k], up[k])
                            for k in range(3)))


_SHUT = _shutTurn()
#  The leaf's middle shut and its half sizes.
_MIDDLE = (MIDDLE_FAR * math.cos(MIDDLE_ANGLE),
           MIDDLE_FAR * math.sin(MIDDLE_ANGLE), MIDDLE_HIGH)
_HALVES = (0.5 * LEAF_THICK, MIDDLE_FAR * math.sin(HALF_SPAN),
           0.5 * (DOOR_HIGH - FLOOR) * math.sqrt(1.0 + SLOPE * SLOPE))
