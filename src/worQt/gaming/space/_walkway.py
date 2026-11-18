"""
Walkway is the way into the rocket on the pad (user, 2026-11-17: "let's
have an entrance ot the rocket perpendicular to the way Asger faces, but
behind him and behind where all those books were at"; "The door out of
the rocket should be connected to a retractable walk way"; "bro just fit
the door"): a door in the capsule's wall straight behind him, sliding
round into the wall; a covered walkway from it to the launch tower's
hall beside the rocket (on the pad, west of it; '_launchtower'). Its
rooms (in the rocket's own axes, the cabin's world's) join the cabin's
while it is at the door: the walkway and the tower's; and while the
door is open, the doorway through the wall. Its state: whether the
walkway is at the door ('attached'; dismissed, it slides back and
folds and swings away on its motors and is gone for good: real
sections, '_walkway.Walkway'), how far it has gone. The door is the
rocket's ('_door': a real leaf on its motor, user, 2026-11-18).
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._cockpit import FLOOR, NOSE, capsuleRadius
from ._hoist import hoisted
from ._pad import PAD_UP, fromPad, movingToPad, turnedToPad
from ._turns import aboutAxis, cross, rotated

#  The door: its span round the wall (deg from x toward y: straight behind
#  him, he faces x), from the floor up to 'DOOR_HIGH'; a pocket door: it
#  slides round the hull into the wall toward -y ('POCKET', rad: past its
#  width; about the rocket's axis, so it keeps to the cone; '_door'). The
#  cut through the walls is '_cabin''s ('DOOR').
DOOR_SPAN = (174.0, 186.0)
DOOR_HIGH = FLOOR + 2.0
DOOR = (DOOR_SPAN, (FLOOR, DOOR_HIGH))
#  The door's window (user, 2026-11-18: "Put a window in the main
#  door"): its span round the wall (deg, within the door's, on the
#  leaf's 2 deg strips) and how high it is over the floor, at his eyes.
DOOR_WINDOW = ((178.0, 182.0), (FLOOR + 1.25, FLOOR + 1.75))
POCKET = math.radians(DOOR_SPAN[1] - DOOR_SPAN[0] + 1.0)
#  The doorway's room (a box through the wall, inside the frame, out to
#  a hair past the hull's skin: beyond it the walkway's floor), m.
DOORWAY = ((-capsuleRadius(FLOOR) - 0.08, -0.42, FLOOR),
           (-4.0, 0.42, DOOR_HIGH - 0.05))
#  The walkway (user, 2026-11-18: "Implement some acutally moving physics for
#  the walkway to like harmonica away and turn to a different direction"):
#  from its pivot at the launch tower's hall's east wall ('TUNNEL_FROM'; its
#  floor the cabin's) out to the hull, inside 'TUNNEL_HALF' either side and
#  'TUNNEL_HIGH' high; its 'SECTIONS' sections, each 'SECTION_LONG' long and
#  'SECTION_MASS' kg, nested (each 'NEST' smaller all round than the one
#  after it, the last at the rocket the biggest, its floor the doorway's; its
#  plates 'PLATE' thick), spread evenly between the first's place and the
#  last's (a concertina: the last's far end 'long' from the pivot, the k-th's
#  near end k/(SECTIONS - 1) of the way to 'long' - 'SECTION_LONG'); out at
#  the door, its far end's seal against the hull ('HELD'), folded all in the
#  first ('SECTION_LONG'). Its motors (each on '_hoist.hoisted', held by its
#  brake at its stop): one draws its far end in or out, as hard as
#  'FOLD_MOST' N, speeding up 'FOLD_ACCEL' m/s², at most 'FOLD_FAST' m/s; one
#  swings it all about its pivot (toward y: north on the pad) as far as
#  'SWING_AWAY', as hard as 'SWING_MOST' N m, 'SWING_ACCEL' rad/s², at most
#  'SWING_FAST' rad/s. The hole through the hall's east wall into it, m. (The
#  hall and the rest of the tower: '_launchtower'.)
TUNNEL_FROM = -13.0
TUNNEL_HALF = 1.0
TUNNEL_HIGH = 2.4
SECTIONS = 5
SECTION_LONG = 2.0
SECTION_MASS = 300.0
NEST = 0.03
PLATE = 0.024
FOLD_MOST = 6000.0
FOLD_ACCEL = 0.5
FOLD_FAST = 1.0
SWING_AWAY = math.radians(85.0)
SWING_MOST = 4000.0
SWING_ACCEL = 0.2
SWING_FAST = 0.25
PIVOT = (TUNNEL_FROM, 0.0, FLOOR)
HOLE = ((TUNNEL_FROM - 1.0, -TUNNEL_HALF, FLOOR),
        (TUNNEL_FROM + 0.7, TUNNEL_HALF, FLOOR + TUNNEL_HIGH))
#  The hull's slope (the cone's radius falls this much a metre up) and
#  how much less a point's distance from its face is than across it.
SLOPE = (capsuleRadius(NOSE) - capsuleRadius(FLOOR)) / (NOSE - FLOOR)
LEAN = 1.0 / math.sqrt(1.0 + SLOPE * SLOPE)
#  Its far end's seal (user, 2026-11-18: "Use a soft inflatable thing
#  like for airliners"): an air bumper round the door 'SEAL' deep, as
#  stiff as 'SEAL_STIFF' N/m, damped 'SEAL_DAMP' N s/m, meeting the hull
#  'SEAL_HIGH' over the floor (where the cone is widest); driven out,
#  its motor stops once it presses 'SEAL_FIT' N ('HELD' out from the
#  pivot against the rocket where it stands), and drives no further
#  than 'OUT_MOST' (the far end a hair off the hull).
SEAL = 0.12
SEAL_STIFF = 20000.0
SEAL_DAMP = 3000.0
SEAL_FIT = 1200.0
SEAL_HIGH = 0.05
OUT_MOST = (-TUNNEL_FROM - capsuleRadius(FLOOR + SEAL_HIGH)
            - 0.02 / LEAN)
HELD = (-TUNNEL_FROM - capsuleRadius(FLOOR + SEAL_HIGH)
        - (SEAL - SEAL_FIT / SEAL_STIFF) / LEAN)


def boxInside(point: tuple, low: tuple, high: tuple) -> float:
  """Returns how far 'point' is inside the box from corner 'low' to
  'high' (its nearest face), m."""
  return min(min(p - a, b - p) for p, a, b in zip(point, low, high))


def hullOutside(point: tuple) -> float:
  """Returns how far 'point' is outside the capsule's skin, m."""
  x, y, z = point
  return (math.hypot(x, y) - capsuleRadius(z)) * LEAN


def walkwayInside(point: tuple) -> float:
  """Returns how far 'point' is inside the walkway out at the door (its
  sections' room inside, outside the hull), m."""
  low = (TUNNEL_FROM, -TUNNEL_HALF, FLOOR)
  high = (TUNNEL_FROM + HELD, TUNNEL_HALF, FLOOR + TUNNEL_HIGH)
  return min(boxInside(point, low, high), hullOutside(point))


def doorwayInside(point: tuple) -> float:
  """Returns how far 'point' is inside the doorway, m."""
  return boxInside(point, *DOORWAY)


def leafTurn(share: float) -> tuple:
  """Returns the door's leaf's turn 'share' of the way open: slid round
  the rocket's axis into the wall."""
  return aboutAxis((0.0, 0.0, 1.0), share * POCKET)


class Walkway:
  """
  Walkway holds the way in: whether it is at the door ('attached'), how
  far its far end is from its pivot ('long', m) and how fast it goes
  out ('outSpeed'), how far it is swung ('swing', rad) and how fast
  ('swingSpeed'), the stops its motors drive it to ('outTarget',
  'swingTarget': None, its brake holds it). 'dismissed' sends it away
  (returning why not, '' it goes: folded, then swung); 'moved' moves it
  on, pushed by what is on it ('loadsOf' from what Asger pushed its
  sections by); 'boxesOf' is its sections as solids, 'posesOf' where
  each is; 'outside' is which rooms join the cabin's (one: the pad's,
  at the door). The door is the rocket's ('_door').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('attached', 'long', 'outSpeed', 'outTarget', 'swing',
           'swingSpeed', 'swingTarget')

  #  Public Variables
  attached: bool
  long: float
  outSpeed: float
  outTarget: float | None
  swing: float
  swingSpeed: float
  swingTarget: float | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, attached: bool) -> None:
    self.attached = bool(attached)
    self.long = HELD if self.attached else SECTION_LONG
    self.swing = 0.0 if self.attached else SWING_AWAY
    self.outSpeed, self.swingSpeed = 0.0, 0.0
    self.outTarget, self.swingTarget = None, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def outside(self, ) -> int:
    """The 'outside' property is which rooms join the cabin's: one for
    the pad's (the launch tower's, the open air round it: at the
    door)."""
    return 1 if self.attached else 0

  @property
  def away(self, ) -> bool:
    """The 'away' property says whether the walkway has swung all the
    way away and stands there."""
    return (not self.attached and self.swingTarget is None
            and self.swing >= SWING_AWAY - 1e-6)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def dismissed(self, ) -> str:
    """The 'dismissed' method sends the walkway away (for good; the door
    locked first is the caller's to see to): it folds, then swings away;
    returns why not ('' it goes)."""
    if not self.attached:
      return 'the walkway is gone already'
    self.attached = False
    self.outTarget = SECTION_LONG
    return ''

  def moved(self, seconds: float, along: float, about: float,
            rocket: tuple = None) -> tuple:
    """The 'moved' method moves the walkway 'seconds' s on, its motors
    driving it to their stops, pushed 'along' N s out along it and
    'about' N m s round its pivot by what was on it over the last frame
    ('loadsOf'), as hard over this one (its drives weigh it), and by its
    seal on the rocket's hull ('sealOf': the rocket's pose 'rocket' in
    the pad's axes, '_pad'; None: no rocket near); driven out, its motor
    stops once the seal presses 'SEAL_FIT'; folded and held, it swings
    away. Returns the seal's push on the hull (N, the pad's axes) and
    where it meets it."""
    if seconds <= 0.0:
      return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    pressed, point = self.sealOf(rocket)
    way = (math.cos(self.swing), math.sin(self.swing), 0.0)
    along -= sum(p * w for p, w in zip(pressed, way)) * seconds
    squeezed = self.sealOf(rocket, True)[0]
    if (self.outTarget is not None and self.outTarget > self.long
            and math.sqrt(sum(p * p for p in squeezed)) >= SEAL_FIT):
      self.outTarget, self.outSpeed = None, 0.0
    mass, inertia = self._moments()
    self.long, self.outSpeed, self.outTarget, _ = hoisted(
      self.long, self.outSpeed, self.outTarget, seconds,
      along / (mass * seconds), mass, FOLD_MOST, FOLD_ACCEL, FOLD_FAST)
    if (not self.attached and self.outTarget is None
            and self.swing < SWING_AWAY - 1e-6
            and self.swingTarget is None):
      self.swingTarget = SWING_AWAY
    self.swing, self.swingSpeed, self.swingTarget, _ = hoisted(
      self.swing, self.swingSpeed, self.swingTarget, seconds,
      about / (inertia * seconds), inertia, SWING_MOST, SWING_ACCEL,
      SWING_FAST)
    return pressed, point

  def sealOf(self, rocket: tuple, still: bool = False) -> tuple:
    """The 'sealOf' method returns how hard its seal pushes the rocket's
    hull (N, the pad's axes: into the hull, as squeezed and closing;
    'still', as squeezed alone: what its motor's switch feels) and where
    (its far end's middle, 'SEAL_HIGH' over its floor), the rocket where
    'rocket' (its pose in the pad's axes) has it; None: nothing to
    push."""
    way = (math.cos(self.swing), math.sin(self.swing), 0.0)
    point = tuple(p + self.long * w for p, w in zip(PIVOT, way))
    point = (point[0], point[1], point[2] + SEAL_HIGH)
    if rocket is None:
      return (0.0, 0.0, 0.0), point
    q = fromPad(rocket, point)
    across = math.hypot(q[0], q[1])
    if across < 1e-6 or not FLOOR - 1.0 < q[2] < NOSE:
      return (0.0, 0.0, 0.0), point
    gap = (across - capsuleRadius(q[2])) * LEAN
    squeeze = SEAL - gap
    if squeeze <= 0.0:
      return (0.0, 0.0, 0.0), point
    out = turnedToPad(rocket, (q[0] / across * LEAN, q[1] / across * LEAN,
                               -SLOPE * LEAN))
    arm = tuple(p - c for p, c in zip(point, PIVOT))
    end = tuple(self.outSpeed * w + c for w, c in zip(way, cross(
      (0.0, 0.0, self.swingSpeed), arm)))
    hull = movingToPad(rocket, q, (0.0, 0.0, 0.0))
    closing = -sum((e - h) * o for e, h, o in zip(end, hull, out))
    if still:
      closing = 0.0
    push = max(0.0, SEAL_STIFF * squeeze + SEAL_DAMP * closing)
    return tuple(-push * o for o in out), point

  def posesOf(self, ) -> tuple:
    """The 'posesOf' method returns where each section is (its near end
    at its floor, the pad's axes: '_pad'), its turn (w x y z: its own x
    out along it, z up) and how fast its middle moves."""
    turn = aboutAxis((0.0, 0.0, 1.0), self.swing)
    way = (math.cos(self.swing), math.sin(self.swing), 0.0)
    out = []
    for k in range(SECTIONS):
      share = k / (SECTIONS - 1.0)
      near = share * (self.long - SECTION_LONG)
      place = tuple(p + near * w for p, w in zip(PIVOT, way))
      middle = tuple(p + (near + 0.5 * SECTION_LONG) * w
                     for p, w in zip(PIVOT, way))
      arm = tuple(m - p for m, p in zip(middle, PIVOT))
      moving = tuple(share * self.outSpeed * w + c for w, c in zip(
        way, (-self.swingSpeed * arm[1], self.swingSpeed * arm[0], 0.0)))
      out.append((place, turn, moving))
    return tuple(out)

  def boxesOf(self, ) -> tuple:
    """The 'boxesOf' method returns its sections as solids, four each
    (floor, the two walls, roof): each its middle, half sizes, turn (w x
    y z) and velocity, the pad's axes."""
    out = []
    for k, (place, turn, moving) in enumerate(self.posesOf()):
      for local, half in _plates(k):
        middle = tuple(p + r for p, r in zip(place, rotated(turn, local)))
        out.append((middle, half, turn, moving))
    return tuple(out)

  def loadsOf(self, struck: tuple) -> tuple:
    """The 'loadsOf' method returns what pushed it out along it (N s) and
    round its pivot (N m s) from what its sections were pushed by
    ('struck': each section's push and its twist about the pad's
    middle, the pad's axes)."""
    way = (math.cos(self.swing), math.sin(self.swing), 0.0)
    along, about = 0.0, 0.0
    for k, (push, twist) in enumerate(struck):
      share = k / (SECTIONS - 1.0)
      along += share * sum(p * w for p, w in zip(push, way))
      about += twist[2] - (PIVOT[0] * push[1] - PIVOT[1] * push[0])
    return along, about

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _moments(self, ) -> tuple:
    """Returns how heavy it is drawn out (its sections' masses, each as
    its share of the far end's way: kg) and swung (round its pivot: kg
    m², each a slab 'SECTION_LONG' long where it is)."""
    mass = sum(SECTION_MASS * (k / (SECTIONS - 1.0)) ** 2
               for k in range(SECTIONS))
    inertia = 0.0
    for k in range(SECTIONS):
      near = k / (SECTIONS - 1.0) * (self.long - SECTION_LONG)
      middle = near + 0.5 * SECTION_LONG
      inertia += SECTION_MASS * (middle * middle + SECTION_LONG ** 2
                                 / 12.0 + TUNNEL_HALF ** 2 / 3.0)
    return mass, inertia


def _plates(k: int) -> tuple:
  """Returns section 'k''s plates (floor, the two walls, roof) in its
  own axes (its near end at its floor, x out along it): each its middle
  and half sizes."""
  inset = (SECTIONS - 1 - k) * NEST
  wide = TUNNEL_HALF - inset
  low, high = inset, TUNNEL_HIGH - inset
  middle = 0.5 * SECTION_LONG
  out = [((middle, 0.0, low - 0.5 * PLATE),
          (middle, wide + PLATE, 0.5 * PLATE))]
  for side in (-1.0, 1.0):
    out.append(((middle, side * (wide + 0.5 * PLATE), 0.5 * (low + high)),
                (middle, 0.5 * PLATE, 0.5 * (high - low))))
  out.append(((middle, 0.0, high + 0.5 * PLATE),
              (middle, wide + PLATE, 0.5 * PLATE)))
  return tuple(out)
