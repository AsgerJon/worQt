"""
TowerLift is the launch tower's lift (user, 2026-11-17: "An EXIT sign
should point us to a stair case and to an elevator that can take us to
the ground"): a car in its shaft ('_launchtower.SHAFT') between the
ground and the hall, its floor and roof plates and its two walls (the
west and the south: its doorways are the east, to the hall, and the
north, to the yard), a window in each (user, 2026-11-18: "Give the
staircase and elevator and elevatorshaft windows"), solids the cabin's
world meets (moving with it); its doors open only where it stands. It
speeds up and slows down at 'ACCEL' to at most 'FAST'. Qt-free, the
rocket's own axes on the pad.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._cockpit import FLOOR
from ._launchtower import CAR_HIGH, GROUND, PLATE, SHAFT

#  Its stops (its floor's height): the ground, the hall's floor, m.
FOOT, TOP = GROUND, FLOOR
#  How hard it speeds up and slows down (m/s²), how fast it goes (m/s),
#  how near a stop it has arrived (m).
ACCEL = 1.5
FAST = 4.0
ARRIVED = 0.005
#  Its walls: half their thickness, how far in from the shaft's walls
#  (as its plates are), m; its windows' sill and head over its floor,
#  and how far in from the walls' ends, m.
CAR_WALL = 0.02
CAR_IN = 0.02
CAR_SILL, CAR_HEAD = 0.9, 2.0
CAR_WINDOW_IN = 0.3


def carMiddle() -> tuple:
  """Returns the middles of the car's floor plate, roof plate, west
  wall and south wall, its floor at nought (the rocket's own axes)."""
  (x0, y0, _), (x1, y1, _) = SHAFT
  x, y = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
  wall = CAR_IN + CAR_WALL
  return ((x, y, -PLATE), (x, y, CAR_HIGH + PLATE),
          (x0 + wall, y, 0.5 * CAR_HIGH), (x, y0 + wall, 0.5 * CAR_HIGH))


def carHalves() -> tuple:
  """Returns the half sizes of the car's floor plate, roof plate, west
  wall and south wall, m."""
  (x0, y0, _), (x1, y1, _) = SHAFT
  across, along = 0.5 * (x1 - x0) - CAR_IN, 0.5 * (y1 - y0) - CAR_IN
  return ((across, along, PLATE), (across, along, PLATE),
          (CAR_WALL, along, 0.5 * CAR_HIGH),
          (across, CAR_WALL, 0.5 * CAR_HIGH))


def carWindow(wall: int) -> tuple:
  """Returns the window in the car's wall 'wall' (nought the west,
  one the south), about the wall's middle: its span along the wall (its
  long side), its sill and head, m."""
  half = carHalves()[2 + wall]
  long = half[1] if wall == 0 else half[0]
  low = CAR_SILL - 0.5 * CAR_HIGH
  return ((-long + CAR_WINDOW_IN, long - CAR_WINDOW_IN),
          (low, low + CAR_HEAD - CAR_SILL))


class TowerLift:
  """
  TowerLift holds the lift's car: its floor's height ('floor'), how fast
  it goes up ('speed', m/s), the stop it goes to ('target', None:
  standing). 'sent' sends it to a stop, 'holds' says whether a point is
  in the car, 'moved' moves it on, 'boxesOf' its floor and roof plates
  (each its middle, half sizes, turn and velocity).
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
    self.floor, self.speed, self.target = TOP, 0.0, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def atTop(self, ) -> bool:
    """The 'atTop' property is whether it stands at the hall."""
    return self.target is None and abs(self.floor - TOP) < ARRIVED

  @property
  def atFoot(self, ) -> bool:
    """The 'atFoot' property is whether it stands at the ground."""
    return self.target is None and abs(self.floor - FOOT) < ARRIVED

  @property
  def doors(self, ) -> int:
    """The 'doors' property is which of its doors are open (as the
    cabin's world takes them: four, the hall's; eight, the ground's)."""
    return (4 if self.atTop else 0) | (8 if self.atFoot else 0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sent(self, stop: float) -> None:
    """The 'sent' method sends it to 'stop' (its floor's height)."""
    if abs(self.floor - stop) >= ARRIVED:
      self.target = float(stop)

  def holds(self, point: tuple) -> bool:
    """The 'holds' method says whether 'point' is in the car."""
    (x0, y0, _), (x1, y1, _) = SHAFT
    x, y, z = point
    return (x0 < x < x1 and y0 < y < y1
            and self.floor < z < self.floor + CAR_HIGH)

  def moved(self, seconds: float) -> None:
    """The 'moved' method moves it 'seconds' s on toward its target,
    speeding up and slowing down to stop on it."""
    if self.target is None:
      self.speed = 0.0
      return
    left = self.target - self.floor
    way = 1.0 if left > 0.0 else -1.0
    braking = (2.0 * ACCEL * abs(left)) ** 0.5
    wanted = way * min(FAST, braking)
    step = ACCEL * seconds
    self.speed += max(-step, min(step, wanted - self.speed))
    self.floor += self.speed * seconds
    if abs(self.target - self.floor) < ARRIVED or (
        way * (self.target - self.floor) < 0.0):
      self.floor, self.speed, self.target = self.target, 0.0, None

  def boxesOf(self, ) -> tuple:
    """The 'boxesOf' method returns its floor's and roof's plates and
    its west and south walls (each its middle, half sizes, turn (w x y
    z) and velocity)."""
    velocity = (0.0, 0.0, self.speed)
    still = (1.0, 0.0, 0.0, 0.0)
    out = []
    for (x, y, z), half in zip(carMiddle(), carHalves()):
      out.append(((x, y, z + self.floor), half, still, velocity))
    return tuple(out)
