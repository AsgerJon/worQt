"""
Hexapod is a test rig, a Gough-Stewart platform: a moving platform
carried by six actuators from the ground, its legs' lengths worked out
from the motion it is to make (LegStroke), so it moves as told in all
six degrees of freedom; HeldPose and SwayingPose are such motions.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._assembly import Actuator
from ._body import Body, State
from ._vectors import ORIGIN, UNTURNED, Quaternion, Vector
from ._vectors import cross, dot, matrixOf, applied, minus, norm, plus
from ._vectors import product, scaled, turnAbout


class PoseAt(NamedTuple):
  """
  PoseAt is how a body is to be at a moment: 'place' of its centre, m;
  'turn' of its own frame; 'velocity', m/s, and 'spin', rad/s; and how
  fast they grow, 'acceleration', m/s², and 'turning', rad/s²; all in
  the world.
  """

  place: Vector
  turn: Quaternion
  velocity: Vector
  spin: Vector
  acceleration: Vector
  turning: Vector

  def state(self, ) -> State:
    """The 'state' method returns the body's state so."""
    return State(self.place, self.turn, self.velocity, self.spin)


class HeldPose(NamedTuple):
  """
  HeldPose holds a body still, its centre at 'place', its frame turned
  'turn'.
  """

  place: Vector
  turn: Quaternion = UNTURNED

  def at(self, time: float) -> PoseAt:
    """The 'at' method returns the pose at 'time': as held, still."""
    return PoseAt(self.place, self.turn, ORIGIN, ORIGIN, ORIGIN, ORIGIN)


class SwayingPose(NamedTuple):
  """
  SwayingPose sways a body about a pose, 'frequency' times a second:
  its centre about 'place' along 'shift' (m, as far either way as long
  as it is), its frame about 'turn' about the fixed axis 'tilt' (rad,
  as far either way as long as it is), both by the sine of the time,
  so from the pose, moving, at time nought. One of the shift's axes
  alone is surge, sway or heave; one of the tilt's, roll, pitch or yaw.
  """

  place: Vector
  turn: Quaternion
  shift: Vector
  tilt: Vector
  frequency: float

  def at(self, time: float) -> PoseAt:
    """The 'at' method returns the pose at 'time'."""
    rate = 2.0 * math.pi * self.frequency
    swing, swinging = math.sin(rate * time), math.cos(rate * time)
    place = plus(self.place, scaled(self.shift, swing))
    angle = norm(self.tilt)
    turn = self.turn
    if angle > 0.0:
      turn = product(turnAbout(self.tilt, angle * swing), self.turn)
    return PoseAt(place, turn, scaled(self.shift, rate * swinging),
                  scaled(self.tilt, rate * swinging),
                  scaled(self.shift, -rate * rate * swing),
                  scaled(self.tilt, -rate * rate * swing))


class LegStroke(NamedTuple):
  """
  LegStroke is the stroke of a leg from 'base', a point in the world,
  to a point at 'arm' from the centre of a body (in its own frame)
  moving as 'motion' says: as long as from one to the other.
  """

  base: Vector
  arm: Vector
  motion: object

  def at(self, time: float) -> tuple[float, float, float]:
    """The 'at' method returns the leg's length at 'time', how fast it
    grows, and how fast that grows."""
    pose = self.motion.at(time)
    reach = applied(matrixOf(pose.turn), self.arm)
    apart = minus(plus(pose.place, reach), self.base)
    moving = plus(pose.velocity, cross(pose.spin, reach))
    speeding = plus(plus(pose.acceleration, cross(pose.turning, reach)),
                    cross(pose.spin, cross(pose.spin, reach)))
    length = norm(apart)
    rate = dot(apart, moving) / length
    growing = (dot(moving, moving) + dot(apart, speeding)
               - rate * rate) / length
    return length, rate, growing


class Hexapod(NamedTuple):
  """
  Hexapod is the rig's geometry, m and degrees: six legs from
  the ground to the moving platform, in three pairs. Their feet stand on
  the ground ('baseLevel' high) on a circle of 'baseRadius', each pair
  'baseSpread' apart about every third of a turn from the x axis; their
  heads hold the platform at 'topLevel' in its own frame on a circle of
  'topRadius', each pair 'topSpread' apart about every third of a turn
  from the sixth; each foot's leg goes to the nearest head of the
  next pair over, so the legs zigzag.
  """

  baseRadius: float = 1.0
  topRadius: float = 0.6
  baseSpread: float = 20.0
  topSpread: float = 20.0
  baseLevel: float = 0.0
  topLevel: float = 0.0

  def feet(self, ) -> tuple[Vector, ...]:
    """The 'feet' method returns where the legs stand on the ground, in
    the world, in leg order."""
    out = []
    for third in range(3):
      for side in (-1.0, 1.0):
        angle = math.radians(120.0 * third + 0.5 * side * self.baseSpread)
        out.append((self.baseRadius * math.cos(angle),
                    self.baseRadius * math.sin(angle), self.baseLevel))
    return tuple(out)

  def heads(self, ) -> tuple[Vector, ...]:
    """The 'heads' method returns where the legs hold the platform, in
    its own frame, in leg order."""
    out = []
    for third in range(3):
      for side in (-1.0, 1.0):
        angle = math.radians(120.0 * third + side * 60.0
                             - 0.5 * side * self.topSpread)
        out.append((self.topRadius * math.cos(angle),
                    self.topRadius * math.sin(angle), self.topLevel))
    return tuple(out)

  def legs(self, platform: Body, index: int, motion: object,
           middle: tuple = (0.0, 0.0)) -> tuple[Actuator, ...]:
    """The 'legs' method returns the six legs, actuators from the
    ground to 'platform' (its place in the assembly 'index'), their
    strokes making it move as 'motion' says, their feet round 'middle'
    (its x and y on the ground; the world's origin unless given)."""
    shift = (middle[0], middle[1], 0.0)
    return tuple(Actuator(None, plus(foot, shift), index, head,
                          LegStroke(plus(foot, shift),
                                    minus(head, platform.centre), motion))
                 for foot, head in zip(self.feet(), self.heads()))
