"""
Walkway is the way into the rocket on the pad (user, 2026-11-17: "let's
have an entrance ot the rocket perpendicular to the way Asger faces, but
behind him and behind where all those books were at"; "The door out of
the rocket should be connected to a retractable walk way"; "bro just fit
the door"): a door in the capsule's wall straight behind him, sliding
round into the wall; a covered walkway from it to a platform on the launch
tower beside the rocket (on the pad, west of it). Its rooms (in the
rocket's own axes, the cabin's world's) join the cabin's while it is at
the door: the walkway and the platform; and while the door is open, the
doorway through the wall. Its state: whether the walkway is at the door
('attached'; dismissed, it swings away and is gone for good), how far
it has swung, the door (how far open, wanted open or not, locked).
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._cockpit import FLOOR, NOSE, capsuleRadius
from ._turns import aboutAxis
from ._vessel import CENTRE, SAG

#  The door: its span round the wall (deg from x toward y: straight behind
#  him, he faces x), from the floor up to 'DOOR_HIGH'; a pocket door: it
#  slides round the hull into the wall toward -y ('POCKET', rad: past its
#  width; about the rocket's axis, so it keeps to the cone), over 'SLIDE'
#  s; open past 'PASSABLE' of the way the doorway is a room. The cut
#  through the walls is '_cabin''s ('DOOR').
DOOR_SPAN = (174.0, 186.0)
DOOR_HIGH = FLOOR + 2.0
DOOR = (DOOR_SPAN, (FLOOR, DOOR_HIGH))
POCKET = math.radians(DOOR_SPAN[1] - DOOR_SPAN[0] + 1.0)
SLIDE = 1.5
PASSABLE = 0.97
#  The doorway's room (a box through the wall, inside the frame), m.
DOORWAY = ((-5.6, -0.42, FLOOR), (-4.0, 0.42, DOOR_HIGH - 0.05))
#  The walkway's tunnel (inside: from the platform's edge to the hull,
#  its room reaching a metre into the platform's: two rooms barely
#  meeting are each too shallow at their seam for his body to pass; half
#  its width across, its height over the floor), the platform at the
#  tower's top (inside its cage: from the far end to the tunnel; half its
#  width; open to the sky, the room as high as 'OPEN_SKY'), m.
TUNNEL_FROM = -13.0
TUNNEL_HALF = 1.0
TUNNEL_HIGH = 2.4
PLATFORM_FAR = -17.0
PLATFORM_HALF = 2.0
OPEN_SKY = 20.0
TUNNEL = ((TUNNEL_FROM - 1.0, -TUNNEL_HALF, FLOOR),
          (-3.0, TUNNEL_HALF, FLOOR + TUNNEL_HIGH))
PLATFORM = ((PLATFORM_FAR, -PLATFORM_HALF, FLOOR),
            (TUNNEL_FROM, PLATFORM_HALF, FLOOR + OPEN_SKY))
#  Dismissed, the walkway swings away about its tower's end (rad, toward
#  y: north on the pad) at 'SWING_SPEED' (rad/s).
SWING_AWAY = math.radians(85.0)
SWING_SPEED = math.radians(12.0)
#  The rocket's own axes on the pad: the pad's own (x east, y north, z up)
#  but this much higher (its middle over the ground), m.
PAD_UP = CENTRE - SAG
#  The hull's slope (the cone's radius falls this much a metre up) and
#  how much less a point's distance from its face is than across it.
SLOPE = (capsuleRadius(NOSE) - capsuleRadius(FLOOR)) / (NOSE - FLOOR)
LEAN = 1.0 / math.sqrt(1.0 + SLOPE * SLOPE)


def boxInside(point: tuple, low: tuple, high: tuple) -> float:
  """Returns how far 'point' is inside the box from corner 'low' to
  'high' (its nearest face), m."""
  return min(min(p - a, b - p) for p, a, b in zip(point, low, high))


def hullOutside(point: tuple) -> float:
  """Returns how far 'point' is outside the capsule's skin, m."""
  x, y, z = point
  return (math.hypot(x, y) - capsuleRadius(z)) * LEAN


def walkwayInside(point: tuple) -> float:
  """Returns how far 'point' is inside the walkway's tunnel (outside the
  hull) or on its platform, m."""
  tunnel = min(boxInside(point, *TUNNEL), hullOutside(point))
  return max(tunnel, boxInside(point, *PLATFORM))


def doorwayInside(point: tuple) -> float:
  """Returns how far 'point' is inside the doorway, m."""
  return boxInside(point, *DOORWAY)


def leafTurn(share: float) -> tuple:
  """Returns the door's leaf's turn 'share' of the way open: slid round
  the rocket's axis into the wall."""
  return aboutAxis((0.0, 0.0, 1.0), share * POCKET)


class Walkway:
  """
  Walkway holds the way in: whether the walkway is at the door
  ('attached'), how far it has swung away ('swing', rad), how far the
  door is open ('door', its share of the way) and whether it is wanted
  open ('wanted'),
  whether it is locked ('locked'). 'opened', 'closed', 'locking' and
  'dismissed' work it, each returning why not ('' done); 'moved' moves
  the door and the walkway on; 'outside' is which rooms join the
  cabin's (a bit each: the walkway's, the doorway's).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  attached: bool
  swing: float
  door: float
  wanted: bool
  locked: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, attached: bool) -> None:
    self.attached = bool(attached)
    self.swing = 0.0 if self.attached else SWING_AWAY
    self.door, self.wanted, self.locked = 0.0, False, not self.attached

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def shut(self, ) -> bool:
    """The 'shut' property says whether the door is closed (and not
    opening)."""
    return not self.wanted and self.door <= 1e-6

  @property
  def passable(self, ) -> bool:
    """The 'passable' property says whether the door is open enough to
    go through."""
    return self.wanted and self.door >= PASSABLE

  @property
  def outside(self, ) -> int:
    """The 'outside' property is which rooms join the cabin's: one for
    the walkway's (at the door), two for the doorway's (open)."""
    return (1 if self.attached else 0) | (2 if self.passable else 0)

  @property
  def away(self, ) -> bool:
    """The 'away' property says whether the walkway has swung all the
    way away."""
    return not self.attached and self.swing >= SWING_AWAY - 1e-9

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def opened(self, ) -> str:
    """The 'opened' method opens the door; returns why not ('' it
    opens)."""
    if self.locked:
      return 'the door is locked'
    if not self.attached:
      return 'the walkway is gone: it is a long way down'
    self.wanted = True
    return ''

  def closed(self, ) -> str:
    """The 'closed' method closes the door (whatever is in the doorway
    is the caller's to see to); returns why not ('' it closes)."""
    if self.shut:
      return 'the door is closed'
    self.wanted = False
    return ''

  def locking(self, ) -> str:
    """The 'locking' method locks the door, or unlocks it; returns why
    not ('' done)."""
    if not self.locked and not self.shut:
      return 'close the door first'
    if self.locked and not self.attached:
      return 'the walkway is gone: it is a long way down'
    self.locked = not self.locked
    return ''

  def dismissed(self, ) -> str:
    """The 'dismissed' method sends the walkway away (for good); returns
    why not ('' it goes)."""
    if not self.attached:
      return 'the walkway is gone already'
    if not self.locked:
      return 'lock the door first'
    self.attached = False
    return ''

  def moved(self, seconds: float) -> None:
    """The 'moved' method moves the door and the walkway 'seconds' s on
    toward where they are wanted."""
    step = seconds / SLIDE
    target = 1.0 if self.wanted else 0.0
    self.door += max(-step, min(step, target - self.door))
    if not self.attached:
      self.swing = min(SWING_AWAY, self.swing + SWING_SPEED * seconds)
