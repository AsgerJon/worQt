"""
TowerLift is the launch tower's lift (user, 2026-11-17: "An EXIT sign
should point us to a stair case and to an elevator that can take us to
the ground"): a car in its shaft ('_launchtower.SHAFT') between the
ground and the hall, its floor and roof plates solids the cabin's world
meets (moving with it); its doors open only where it stands. It speeds
up and slows down at 'ACCEL' to at most 'FAST'. Qt-free, the rocket's
own axes on the pad.
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
    """The 'boxesOf' method returns its floor's and roof's plates (each
    its middle, half sizes, turn (w x y z) and velocity)."""
    (x0, y0, _), (x1, y1, _) = SHAFT
    half = (0.5 * (x1 - x0) - 0.02, 0.5 * (y1 - y0) - 0.02, PLATE)
    middle = (0.5 * (x0 + x1), 0.5 * (y0 + y1))
    velocity = (0.0, 0.0, self.speed)
    still = (1.0, 0.0, 0.0, 0.0)
    return ((middle + (self.floor - PLATE,), half, still, velocity),
            (middle + (self.floor + CAR_HIGH + PLATE,), half, still,
             velocity))
