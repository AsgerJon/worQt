"""
Ground is the ground a body falls onto and comes to rest on: flat, or
shaped by a terrain ('Terrain').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._vectors import Vector

#  Under this sliding speed along a wall, m/s, its friction eases off in
#  proportion (Coulomb, eased: no bristle holds a point to it).
WALL_SLIDE = 0.5
#  A bristle: the index of the point it holds and where it holds it to on
#  the ground, x and y.
Bristle = tuple[int, float, float]


class Ground(NamedTuple):
  """
  Ground is flat at height nought, z up, met by a body at the points of
  its shape. A point pressed 'depth' into it is pushed up 'stiffness'
  N/m times as far, more the faster it is pressed, by 'damping' s/m
  (Hunt and Crossley: k d (1 + damping d'), so the push grows from
  nought as it touches and dies to nought as it leaves, never pulling).
  Along the ground each point touching is held by a bristle to where it
  touched down, 'bristle' N/m and 'bristleDamping' N s/m: it holds
  still as long as that is no more than 'grip' times the push, and
  slips where it would hold harder (Coulomb): the bristle dragged along
  so it never pulls harder than that, the whole held to it. Standing
  still on a slope a body does not creep. Slipping never stretches a
  bristle further, so it never makes energy. A turned solid (a wheel)
  meets it at the lowest points of its circles, each bristle rolling
  along with it; with a 'relaxation' length (m, nought at first: none)
  each such bristle also lets go of what it held as the solid rolls
  that far, as a tyre's patch takes in fresh rubber (so it pushes back
  in proportion to how it slips, not as hard as it can grip whatever
  the slip: its slip stiffness is the bristle's times the length). With
  a 'terrain' ('Terrain', None at first: flat) it is shaped: a point is
  as deep as it is under it, along its normal there, and pushed out
  along that normal; its bristles still hold it along the level (a
  car stands on a slope as steep as its grip, as on the level). With a
  'wall' ('OvalWall', None at first) a point through its face, below
  its top, is pushed back out level, by the ground's own stiffness and
  damping as deep as it is through, and dragged along it by the wall's
  grip times that push against the way it slides (Coulomb, eased under
  'WALL_SLIDE' m/s; no bristle: it holds nothing still).
  """

  stiffness: float = 1e5
  damping: float = 1.0
  grip: float = 0.5
  bristle: float = 1e5
  bristleDamping: float = 100.0
  relaxation: float = 0.0
  terrain: object = None
  wall: object = None

  def contactOf(self, place: Vector) -> tuple[float, Vector]:
    """The 'contactOf' method returns how deep 'place' is in the
    ground, m (along the ground's normal under it), and that normal."""
    if self.terrain is None:
      return -place[2], (0.0, 0.0, 1.0)
    normal = self.terrain.normalAt(place[0], place[1])
    height = self.terrain.heightAt(place[0], place[1])
    return (height - place[2]) * normal[2], normal

  def topOf(self, ) -> float:
    """The 'topOf' method returns the highest the ground gets, its wall
    on it, m."""
    top = 0.0 if self.terrain is None else self.terrain.top()
    return top if self.wall is None else top + self.wall.height

  def wallOf(self, place: Vector) -> tuple[float, Vector]:
    """The 'wallOf' method returns how deep 'place' is through the
    wall's face, m (nought or less: not in it, or over its top), and
    the face's outward normal there."""
    if self.wall is None:
      return 0.0, (0.0, 0.0, 0.0)
    depth, nx, ny = self.wall.beyond(place[0], place[1])
    if depth <= 0.0:
      return 0.0, (0.0, 0.0, 0.0)
    base = 0.0 if self.terrain is None else self.terrain.heightAt(
      place[0], place[1])
    if place[2] > base + self.wall.height:
      return 0.0, (0.0, 0.0, 0.0)
    return depth, (nx, ny, 0.0)

  def wallPush(self, place: Vector, velocity: Vector) -> Vector:
    """The 'wallPush' method returns the wall's push on a point at
    'place' moving at 'velocity', N."""
    depth, (nx, ny, _) = self.wallOf(place)
    if depth <= 0.0:
      return 0.0, 0.0, 0.0
    sinking = velocity[0] * nx + velocity[1] * ny
    push = max(0.0, self.stiffness * depth * (1.0 + self.damping * sinking))
    tx, ty, tz = (velocity[0] - sinking * nx, velocity[1] - sinking * ny,
                  velocity[2])
    slide = max(math.sqrt(tx * tx + ty * ty + tz * tz), WALL_SLIDE)
    share = self.wall.grip * push / slide
    return -nx * push - share * tx, -ny * push - share * ty, -share * tz

  def pushOf(self, depth: float, sinking: float) -> float:
    """The 'pushOf' method returns how hard the ground pushes a point
    'depth' into it, sinking 'sinking' m/s deeper, N."""
    if depth <= 0.0:
      return 0.0
    return max(0.0, self.stiffness * depth * (1.0 + self.damping * sinking))

  def pushed(self, places: list[tuple[int, Vector]],
             velocities: list[Vector], bristles: dict) -> list[Vector]:
    """The 'pushed' method returns the ground's push on each of
    'places' (a point's index and where it is), moving at
    'velocities', and holds 'bristles' (index to where its bristle
    holds it, x and y) to them: a point leaving lets go, one touching
    down is held where it is, one slipping drags its bristle."""
    forces = []
    for (index, place), velocity in zip(places, velocities):
      wall = (0.0, 0.0, 0.0) if self.wall is None else self.wallPush(
        place, velocity)
      depth, normal = -place[2], None
      if self.terrain is not None:
        depth, normal = self.contactOf(place)
      if depth <= 0.0:
        bristles.pop(index, None)
        forces.append(wall)
        continue
      if normal is None:
        push = self.pushOf(depth, -velocity[2])
      else:
        push = self.pushOf(depth, -(velocity[0] * normal[0]
                                    + velocity[1] * normal[1]
                                    + velocity[2] * normal[2]))
      most = self.grip * push
      x, y = bristles.get(index, (place[0], place[1]))
      sx, sy = -self.bristle * (place[0] - x), -self.bristle * (place[1] - y)
      held = math.hypot(sx, sy)
      if held > most:
        share = most / held
        sx, sy = sx * share, sy * share
        x, y = place[0] + sx / self.bristle, place[1] + sy / self.bristle
      fx = sx - self.bristleDamping * velocity[0]
      fy = sy - self.bristleDamping * velocity[1]
      along = math.hypot(fx, fy)
      if along > most:
        fx, fy = fx * most / along, fy * most / along
      bristles[index] = (x, y)
      if normal is None:
        forces.append((fx + wall[0], fy + wall[1], push + wall[2]))
      else:
        forces.append((fx + normal[0] * push + wall[0],
                       fy + normal[1] * push + wall[1],
                       normal[2] * push + wall[2]))
    return forces

  def storedIn(self, places: list[tuple[int, Vector]],
               bristles: dict) -> float:
    """The 'storedIn' method returns the energy the ground and the
    bristles hold, pressed and stretched by 'places', J."""
    stored = 0.0
    for index, place in places:
      through = self.wallOf(place)[0]
      stored += 0.5 * self.stiffness * through * through
      depth = self.contactOf(place)[0]
      if depth <= 0.0:
        continue
      stored += 0.5 * self.stiffness * depth * depth
      x, y = bristles.get(index, (place[0], place[1]))
      stretch = (place[0] - x) ** 2 + (place[1] - y) ** 2
      stored += 0.5 * self.bristle * stretch
    return stored

  def quickest(self, mass: float, least: float,
               arms: list[float]) -> float:
    """The 'quickest' method returns a bound on how fast, rad/s, a body
    of 'mass' and least principal moment 'least' may swing on the
    ground, its points 'arms' m from its centre, all touching: no
    swing faster than the sum, over the points, of each one's
    stiffness, down and both ways along, over the least mass it could
    have there."""
    stiff = self.stiffness + 2.0 * self.bristle
    total = sum(stiff * (1.0 / mass + arm * arm / least) for arm in arms)
    return math.sqrt(total)
