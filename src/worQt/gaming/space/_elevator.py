"""
Elevator is a spoke's elevator in the space station (user, 2026-11-17:
"fine, just put elevaotr in the shafts then"; "all aboard Asger's
kolonihave i rummet!"): a cage riding its shaft from the hub, its roof
flush with the hub's wall and open there, to the ring's deck, its floor
flush with the deck and its two sides along the ring open there; closed
on the way. It speeds up and slows down at 'ACCEL' to at most 'FAST':
everything in it feels it, and the station's turn too (riding out at
30 m/s the shaft's wall pushes sideways with 0.6 g: honest, not added).
Its boxes ('boxesOf') are solids the cabin's world meets, moving.
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._stationinterior import DECK, HUB_INSIDE, PLANE
from ._turns import cross, quaternionOf

#  The cage inside (half its width across the shaft, both ways; its
#  height along it) and its plates' half thickness, m.
CAR_HALF = 2.0
CAR_HIGH = 3.0
PLATE = 0.08
#  Its stops (its floor's distance from the axis): by the hub (its roof
#  in the hub's wall), at the deck (its floor in the deck), m.
HUB_STOP = HUB_INSIDE + CAR_HIGH
DECK_STOP = DECK
#  How hard it speeds up and slows down (m/s²), how fast it goes (m/s),
#  how near a stop it has arrived (m).
ACCEL = 2.0
FAST = 30.0
ARRIVED = 0.005
#  Where a box that is not there is kept (far from everything), m.
AWAY = (0.0, 0.0, -1e4)
#  The plates' half sizes (along the ring, along the axis, out): floor,
#  roof, the two sides along the ring, the two across it.
_WIDE = CAR_HALF + 2.0 * PLATE
PLATE_HALVES = ((_WIDE, _WIDE, PLATE), (_WIDE, _WIDE, PLATE),
                (PLATE, _WIDE, 0.5 * CAR_HIGH),
                (PLATE, _WIDE, 0.5 * CAR_HIGH),
                (CAR_HALF, PLATE, 0.5 * CAR_HIGH),
                (CAR_HALF, PLATE, 0.5 * CAR_HIGH))


class Elevator:
  """
  Elevator holds one spoke's cage: where its floor is ('floor', m from
  the axis), how fast it goes out ('speed', m/s), the stop it goes to
  ('target', None: standing). 'called' sends it to the other stop,
  'sent' to a stop, 'holds' says whether a point is in its cage,
  'moved' moves it on, 'boxesOf' says its six plates (floor, roof, two
  sides along the ring, two across it) in the docked rocket's own axes
  along its shaft's way out, each moving with it, the open ones away.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('floor', 'speed', 'target')

  #  Public Variables
  floor: float
  speed: float
  target: float | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.floor, self.speed, self.target = HUB_STOP, 0.0, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def atHub(self, ) -> bool:
    """The 'atHub' property is whether it stands at the hub's stop."""
    return self.target is None and abs(self.floor - HUB_STOP) < ARRIVED

  @property
  def atDeck(self, ) -> bool:
    """The 'atDeck' property is whether it stands at the deck's stop."""
    return self.target is None and abs(self.floor - DECK_STOP) < ARRIVED

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def called(self, ) -> None:
    """The 'called' method sends it to the other stop (the nearer one's
    other, going: back the way it came)."""
    if self.target is not None:
      self.target = HUB_STOP if self.target == DECK_STOP else DECK_STOP
      return
    self.target = DECK_STOP if self.atHub else HUB_STOP

  def sent(self, stop: float) -> None:
    """The 'sent' method sends it to 'stop' (one of its two), unless it
    stands there."""
    if self.target is None and abs(self.floor - stop) < ARRIVED:
      return
    self.target = stop

  def holds(self, way: tuple, point: tuple) -> bool:
    """The 'holds' method returns whether 'point' (the docked rocket's
    own axes) is inside its cage, its shaft out along 'way'."""
    side = cross((0.0, 0.0, 1.0), way)
    out = point[0] * way[0] + point[1] * way[1]
    along = point[0] * side[0] + point[1] * side[1]
    return (self.floor - CAR_HIGH <= out <= self.floor
            and abs(along) <= CAR_HALF and abs(point[2] - PLANE) <= CAR_HALF)

  def moved(self, seconds: float) -> None:
    """The 'moved' method moves it 'seconds' s on toward its stop:
    speeding up, at most 'FAST', slowing down to stop on it."""
    if self.target is None or seconds <= 0.0:
      self.speed = 0.0
      return
    left = self.target - self.floor
    way = 1.0 if left > 0.0 else -1.0
    braking = self.speed * self.speed / (2.0 * ACCEL)
    toward = self.speed * way
    if toward > 0.0 and braking >= abs(left):
      self.speed -= way * ACCEL * seconds
    else:
      self.speed += way * ACCEL * seconds
    self.speed = max(-FAST, min(FAST, self.speed))
    step = self.speed * seconds
    if abs(step) >= abs(left) or (abs(left) < ARRIVED):
      self.floor, self.speed, self.target = self.target, 0.0, None
      return
    self.floor += step

  def boxesOf(self, way: tuple) -> tuple:
    """The 'boxesOf' method returns its six plates (floor, roof, the two
    sides along the ring, the two across it) along a shaft out 'way'
    (the docked rocket's own axes): each its middle, half sizes, turn
    (w x y z: its axes along the ring, along the axis, out) and
    velocity; those open (the roof at the hub, the sides at the deck)
    kept away."""
    up = (0.0, 0.0, 1.0)
    side = cross(up, way)
    turn = quaternionOf(tuple((side[k], up[k], way[k]) for k in range(3)))
    moving = tuple(self.speed * w for w in way)
    still = (0.0, 0.0, 0.0)
    mid = self.floor - 0.5 * CAR_HIGH

    def at(out: float, along: float, axial: float) -> tuple:
      return tuple(out * w + along * s + axial * u for w, s, u in zip(
        way, side, up))

    def placed(middle: tuple) -> tuple:
      return middle[0], middle[1], middle[2] + PLANE

    middles = (at(self.floor + PLATE, 0.0, 0.0),
               at(self.floor - CAR_HIGH - PLATE, 0.0, 0.0),
               at(mid, CAR_HALF + PLATE, 0.0),
               at(mid, -CAR_HALF - PLATE, 0.0),
               at(mid, 0.0, CAR_HALF + PLATE),
               at(mid, 0.0, -CAR_HALF - PLATE))
    boxes = [(placed(m), h) for m, h in zip(middles, PLATE_HALVES)]
    open_ = {1} if self.atHub else {2, 3} if self.atDeck else set()
    return tuple((AWAY, half, turn, still) if k in open_ else (
      middle, half, turn, moving) for k, (middle, half) in enumerate(boxes))
