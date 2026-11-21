"""
Elevator is a spoke's elevator in the space station (user, 2026-11-17:
"fine, just put elevaotr in the shafts then"; "all aboard Asger's
kolonihave i rummet!"; 2026-11-19: "We then pick either of the four of
our doors to enter a particular elevator on terra prime"): a cage riding
its shaft from the drum's hole, its roof just out of the hole's wall and
open there (a docked rocket's top floor's door before it), down the
spoke's open girders (in vacuum: the cage is pressurised, its windows
looking out: user, 2026-11-19, "the spokes are not pressurized. Only the
elevators are") into the ring's terminal, its floor flush with the
landing over the deck and its side toward the platform and the stairs
open there ('_terminal'); closed on the way. A seat in it faces that
side ('seatOf': user, "put a seat in those elevators"). Its motor
drives it ('_hoist': user, 2026-11-18, "PHYSICS MUST BE REAL"),
speeding up and slowing down
at 'ACCEL' to at most 'FAST', no harder than 'MOTOR_MOST', against the
station's turning pulling it and its rider out: everything in it feels
it, and the station's turn too (riding out at 30 m/s the shaft's wall
pushes sideways with 0.6 g: honest, not added); what the motor and the
walls push it by pushes the station back.
Its boxes ('boxesOf') are solids the cabin's world meets, moving.
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._hoist import hoisted
from ._stationinterior import PLANE, SHAFT_FROM
from ._terminal import LANDING
from ._turns import aboutAxis, cross, product, quaternionOf, unit

#  The cage inside (half its width across the shaft, both ways: it fits
#  the shaft, '_stationmeshes.SHAFT'; its height along it) and its
#  plates' half thickness, m.
CAR_HALF = 1.6
CAR_HIGH = 3.0
PLATE = 0.08
#  Its stops (its floor's distance from the axis): by the drum's hole
#  (its roof 'HOLE_GAP' m out of the hole's wall: the top floor's door
#  just before it), at the ring's terminal (its floor flush with the
#  landing, '_terminal.LANDING'), m.
HOLE_GAP = 0.05
HUB_STOP = SHAFT_FROM + HOLE_GAP + CAR_HIGH
DECK_STOP = LANDING
#  Its seat: on its floor against its side away from the opening, facing
#  the opening (its top's middle this far off the floor, this far from
#  the cage's middle along the ring), m.
SEAT_HIGH = 0.45
SEAT_BACK = 1.1
#  Its handrail (the handles' run into it ends with his middle
#  'HANDLE_IN' in from its floor, before the seat: '_ladder'): along the
#  shaft from its roof to there, 'HANDLE_ASIDE' m along the axis from
#  the cage's middle, on brackets from the wall across, its radius, m.
HANDLE_IN = 1.15
HANDLE_ASIDE = 0.5
HANDLE = 0.02
#  Its button (user, 2026-11-19: "when Asger sits in the seat in the
#  elevator there is a single guarded button like in the pilot seat. when
#  this is triggered only then do we go down"): on a post at his right
#  hand as he sits (along the ring and along the axis from the cage's
#  middle; its top this high over the floor; the post's half width), the
#  cap's half sizes and how far it sinks pressed; its guard, a red flip
#  cover hinged at its far edge (half sizes over the post's top, its
#  walls' thickness), m; how far the guard opens, rad.
BUTTON_AT = (-SEAT_BACK + 0.35, 0.45)
BUTTON_HIGH = 0.62
BUTTON_POST = 0.05
BUTTON_CAP = (0.022, 0.022, 0.012)
BUTTON_SINK = 0.008
GUARD = (0.045, 0.045, 0.03)
GUARD_WALL = 0.004
GUARD_OPEN = math.radians(105.0)
#  How hard it speeds up and slows down (m/s²), how fast it goes (m/s),
#  how near a stop it has arrived (m).
ACCEL = 2.0
FAST = 30.0
ARRIVED = 0.005
#  The cage's mass (its frame and walls: the plates' thickness is a
#  wall's for the world's meetings, not its steel) and its motor's most
#  push along the shaft, kg and N.
CAGE_MASS = 2000.0
MOTOR_MOST = 40e3
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

  def moved(self, seconds: float, along: float = 0.0,
            load: float = 0.0) -> float:
    """The 'moved' method moves it 'seconds' s on toward its stop, its
    motor driving it ('_hoist.hoisted': at most 'FAST', speeding up and
    slowing down at 'ACCEL', no harder than 'MOTOR_MOST'), pulled
    'along' m/s² out along its shaft, pushed 'load' N s out along it by
    what is in it over the last frame (Asger standing in it: user,
    2026-11-18, "PHYSICS MUST BE REAL"; the cabin's world says how
    hard, '_cabinworld.CabinWorld.struck'), as hard over this one (its
    drive weighs it, as a lift's does; standing at a stop its brake
    takes it); returns how fast it sped up out along it (m/s², on the
    average)."""
    if seconds <= 0.0:
      return 0.0
    self.floor, self.speed, self.target, faster = hoisted(
      self.floor, self.speed, self.target, seconds,
      along + load / (CAGE_MASS * seconds), CAGE_MASS, MOTOR_MOST, ACCEL,
      FAST)
    return faster

  def seatOf(self, way: tuple, axial: tuple) -> tuple:
    """The 'seatOf' method returns its seat's top's middle, the way it
    faces (toward the opening at the terminal) and its up (toward the
    axis), the docked rocket's own axes ('way', 'axial' as 'boxesOf')."""
    side = unit(cross(axial, way))
    out = self.floor - SEAT_HIGH
    seat = tuple(out * w - SEAT_BACK * s for w, s in zip(way, side))
    return ((seat[0], seat[1], seat[2] + PLANE), side,
            tuple(-w for w in way))

  def buttonOf(self, way: tuple, axial: tuple, pressed: float) -> tuple:
    """The 'buttonOf' method returns its button's cap's place (the top of
    its post, sunk 'pressed' of 'BUTTON_SINK') and the cage's turn (the
    docked rocket's own axes; 'way', 'axial' as 'boxesOf')."""
    a, b = BUTTON_AT
    c = 0.5 * CAR_HIGH - BUTTON_HIGH + pressed * BUTTON_SINK
    return self._pointOf(way, axial, (a, b, c)), _frameOf(way, axial)[1]

  def guardOf(self, way: tuple, axial: tuple, share: float) -> tuple:
    """The 'guardOf' method returns its button's guard's hinge (the post's
    top's far edge along the ring) and its turn, opened 'share' of
    'GUARD_OPEN' (its free end up, toward the axis)."""
    a, b = BUTTON_AT
    hinge = (a + GUARD[0], b, 0.5 * CAR_HIGH - BUTTON_HIGH)
    turn = _frameOf(way, axial)[1]
    return self._pointOf(way, axial, hinge), product(turn, aboutAxis(
      (0.0, 1.0, 0.0), -GUARD_OPEN * share))

  def _pointOf(self, way: tuple, axial: tuple, local: tuple) -> tuple:
    """Returns 'local' (the cage's own axes: along the ring, along the
    axis, out; from its middle) in the docked rocket's own axes."""
    side = _frameOf(way, axial)[0]
    middle = self.middleOf(way)
    return tuple(m + local[0] * s + local[1] * x + local[2] * w
                 for m, s, x, w in zip(middle, side, axial, way))

  def middleOf(self, way: tuple) -> tuple:
    """The 'middleOf' method returns its cage's middle along a shaft out
    'way' (the docked rocket's own axes)."""
    out = self.floor - 0.5 * CAR_HIGH
    return out * way[0], out * way[1], out * way[2] + PLANE

  def boxesOf(self, way: tuple, axial: tuple) -> tuple:
    """The 'boxesOf' method returns its six plates (floor, roof, the two
    sides along the ring, the two across it) along a shaft out 'way'
    (the docked rocket's own axes; 'axial' the station's own z in them:
    the ring's turning way is 'axial' cross 'way', the terminal's
    platform that side): each its middle, half sizes, turn (w x y z: its
    axes along the ring, along the axis, out) and velocity; those open
    (the roof at the hub, the side toward the platform at the deck) kept
    away."""
    up = (0.0, 0.0, 1.0)
    side, turn = _frameOf(way, axial)
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
    open_ = {1} if self.atHub else {2} if self.atDeck else set()
    return tuple((AWAY, half, turn, still) if k in open_ else (
      middle, half, turn, moving) for k, (middle, half) in enumerate(boxes))


def _frameOf(way: tuple, axial: tuple) -> tuple:
  """Returns the ring's turning way along a shaft out 'way' ('axial' x
  'way': the terminal's platform's side) and the cage's turn (w x y z:
  its axes along the ring, along the station's axis, out; a turn, not a
  mirror)."""
  side = unit(cross(axial, way))
  return side, quaternionOf(tuple((side[k], axial[k], way[k])
                                  for k in range(3)))


#  The cage's windows (user, 2026-11-19: "Windows in the elevators, so
#  we can see the grandness of Terra Prime"): in each of its four sides,
#  from 'SILL' to 'HEAD' m over its floor, 'WINDOW_IN' m in from the
#  side's edges; the glass this thick, m.
SILL = 0.8
HEAD = 2.6
WINDOW_IN = 0.3
GLASS = 0.006


def windowOf(plate: int) -> tuple:
  """Returns side plate 'plate''s (two to five) window about its middle,
  in its own axes (along the ring, along the axis, out): its span along
  its long way in the side, its span out (from the head to the sill:
  out runs toward the floor), and which of its axes is the long way."""
  half = PLATE_HALVES[plate]
  long = 1 if plate in (2, 3) else 0
  reach = half[long] - WINDOW_IN
  middle = 0.5 * CAR_HIGH
  return (-reach, reach), (middle - HEAD, middle - SILL), long


def plateRows(plate: int) -> tuple:
  """Returns plate 'plate''s mesh about its middle in its own axes (the
  cage's: along the ring, along the axis, out): the floor and the roof
  whole, each side a frame round its window (the glass is its own,
  'glassRows')."""
  from ._shapes import UNTURNED, boxRows, joined
  half = PLATE_HALVES[plate]
  if plate < 2:
    return boxRows((0.0, 0.0, 0.0), half, UNTURNED)
  (a0, a1), (b0, b1), long = windowOf(plate)
  parts = []
  for low, high, sill in ((-half[long], a0, False), (a1, half[long], False),
                          (a0, a1, True)):
    if sill:
      spans = ((-half[2], b0), (b1, half[2]))
    else:
      spans = ((-half[2], half[2]),)
    for c0, c1 in spans:
      middle = [0.0, 0.0, 0.5 * (c0 + c1)]
      size = list(half)
      middle[long] = 0.5 * (low + high)
      size[long] = 0.5 * (high - low)
      size[2] = 0.5 * (c1 - c0)
      parts.append(boxRows(tuple(middle), tuple(size), UNTURNED))
  return joined(parts)


def glassRows(plate: int) -> tuple:
  """Returns side plate 'plate''s window's pane about the plate's
  middle, its own axes."""
  from ._shapes import UNTURNED, boxRows
  (a0, a1), (b0, b1), long = windowOf(plate)
  middle, size = [0.0, 0.0, 0.5 * (b0 + b1)], [GLASS, GLASS, 0.5 * (
    b1 - b0)]
  middle[long], size[long] = 0.5 * (a0 + a1), 0.5 * (a1 - a0)
  return boxRows(tuple(middle), tuple(size), UNTURNED)


def seatRows() -> tuple:
  """Returns the cage's seat about the cage's middle in its axes (along
  the ring, along the axis, out): its cushion with its top 'SEAT_HIGH'
  over the floor 'SEAT_BACK' back from the middle, its pedestal, its
  backrest behind; the button's post at his right hand ('BUTTON_AT');
  the handrail from the roof to before the seat on its two brackets."""
  from ._shapes import UNTURNED, boxRows, cylinderRows, joined
  floor = 0.5 * CAR_HIGH
  top = floor - SEAT_HIGH
  a, b = BUTTON_AT
  post = 0.5 * BUTTON_HIGH
  low, high = -floor + 0.1, floor - HANDLE_IN
  wall = CAR_HALF - HANDLE_ASIDE
  return joined([
    boxRows((-SEAT_BACK, 0.0, top + 0.05), (0.28, 0.32, 0.05), UNTURNED),
    boxRows((-SEAT_BACK, 0.0, 0.5 * (floor + top + 0.1)), (
      0.1, 0.1, 0.5 * (floor - top - 0.1)), UNTURNED),
    boxRows((-SEAT_BACK - 0.26, 0.0, top - 0.32), (0.04, 0.32, 0.34),
            UNTURNED),
    boxRows((a, b, floor - post), (BUTTON_POST, BUTTON_POST, post),
            UNTURNED),
    cylinderRows((0.0, HANDLE_ASIDE, low), (0.0, 0.0, 1.0), HANDLE,
                 high - low, 8)] + [
    boxRows((0.0, HANDLE_ASIDE + 0.5 * wall, c), (HANDLE, 0.5 * wall,
                                                  HANDLE), UNTURNED)
    for c in (low + 0.1, high - 0.1)])


def buttonRows() -> tuple:
  """Returns the button's cap about its place (the post's top's middle),
  the cage's axes: standing up out of the post's top (toward the
  axis)."""
  from ._shapes import UNTURNED, boxRows
  return boxRows((0.0, 0.0, -BUTTON_CAP[2]), BUTTON_CAP, UNTURNED)


def guardRows() -> tuple:
  """Returns the button's guard as it rests closed over it, about its
  hinge (the cage's axes): a lid, its two sides and a lip at its free
  end (open at the hinge and underneath)."""
  from ._shapes import UNTURNED, boxRows, joined
  hx, hy, hz = GUARD
  t = GUARD_WALL
  return joined([
    boxRows((-hx, 0.0, -2.0 * hz + 0.5 * t), (hx, hy, 0.5 * t), UNTURNED)]
    + [boxRows((-hx, side * (hy - 0.5 * t), -hz), (hx, 0.5 * t, hz),
               UNTURNED) for side in (-1.0, 1.0)]
    + [boxRows((-2.0 * hx + 0.5 * t, 0.0, -hz), (0.5 * t, hy, hz),
               UNTURNED)])
