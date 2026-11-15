"""
TyreTracks are the marks a car's tyres leave on the dirt (user,
2026-11-12: "can you make the surface have a more dirt-like texture
that leaves tiretracks behind?"), Qt-free: each frame ('update'), for
each wheel touching the ground, where its tread meets it (the lowest
point of its rim toward the ground, its tread's width across), laid
down every 'SPACING' m it moves; the tracks drawn as strips of quads a
hair over the ground ('LIFT'), each part as dark as the tyre slid
there: rolling it leaves a print ('print'), scrubbing sideways a
darker mark ('scrub'), sliding hard (locked, spun, thrown sideways) a
skid ('skid'). The latest 'KEPT' parts of each kind are kept. They are
marks only: the ground is not changed by them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from .._car import TYRE, CarBuild
from .._vectors import cross, dot, minus, norm, plus, rotated, scaled

#  How far a wheel moves between the parts of its track, m; how far over
#  the ground they lie, m; how far off the ground a tread still marks
#  it, m; how wide a track is (the tread's flat), m.
SPACING, LIFT, NEAR, WIDE = 0.15, 0.008, 0.02, 0.16
#  How fast the tread slides over the ground, m/s, for a scrub and for a
#  skid; how many parts of each kind are kept.
SCRUB, SKID, KEPT = 1.0, 4.0, 6000
#  The kinds, lightest first.
KINDS = ('print', 'scrub', 'skid')


class TyreTracks:
  """
  TyreTracks are the tracks 'car''s tyres leave on 'ground' ('update'
  each frame; 'quads' to draw them, by kind).
  """

  def __init__(self, car: CarBuild, ground: object) -> None:
    self.car, self.ground = car, ground
    self.last = [None] * len(car.wheels)
    self.parts = {kind: numpy.zeros((KEPT, 4, 6)) for kind in KINDS}
    self.counts = {kind: 0 for kind in KINDS}
    self.changed = {kind: False for kind in KINDS}
    self.drawn = {}

  def update(self, states: tuple) -> None:
    """The 'update' method lays down the tracks' new parts for the
    wheels as they are in 'states'."""
    for corner, wheel in enumerate(self.car.wheels):
      touch = self._touchOf(states, wheel)
      if touch is None:
        self.last[corner] = None
        continue
      middle, left, right, kind = touch
      last = self.last[corner]
      if last is None or norm(minus(middle, last[0])) > 4.0 * SPACING:
        self.last[corner] = (middle, left, right)
        continue
      if norm(minus(middle, last[0])) < SPACING:
        continue
      self._lay(kind, (last[1], last[2], right, left))
      self.last[corner] = (middle, left, right)

  def quads(self, states: tuple) -> dict[str, numpy.ndarray]:
    """The 'quads' method returns the tracks as quads in the world by
    kind (n, 4, 6: each corner's place and normal), those of a kind the
    same array as long as none were laid since."""
    for kind in KINDS:
      if self.changed[kind]:
        self.drawn[kind] = self.parts[kind][:min(self.counts[kind], KEPT)]
        self.changed[kind] = False
    return dict(self.drawn)

  def _lay(self, kind: str, corners: tuple) -> None:
    """Lays a part of 'kind' with 'corners' (around, anticlockwise from
    above), its normal up."""
    at = self.counts[kind] % KEPT
    part = self.parts[kind][at]
    for index, corner in enumerate(corners):
      part[index, :3] = corner
    part[:, 3:] = (0.0, 0.0, 1.0)
    self.counts[kind] += 1
    self.changed[kind] = True

  def _touchOf(self, states: tuple, wheel: int) -> tuple | None:
    """Returns where the wheel's tread meets the ground now: its middle,
    its edges (left and right of the way it rolls) lifted over the
    ground, and the kind of mark it leaves; None off the ground."""
    body, state = self.car.assembly.bodies[wheel], states[wheel]
    centre = body.placeOf(state, (0.0, 0.0, 0.0))
    axle = rotated(state.turn, (0.0, 0.0, 1.0))
    up = self._upAt(centre)
    down = plus(scaled(up, -1.0), scaled(axle, dot(up, axle)))
    size = norm(down)
    if size < 1e-6:
      return None
    middle = plus(centre, scaled(down, 0.5 * TYRE.outside / size))
    if middle[2] - self._heightAt(middle) > NEAR:
      return None
    across = minus(axle, scaled(up, dot(axle, up)))
    across = scaled(across, 0.5 * WIDE / max(norm(across), 1e-9))
    edges = []
    for way in (1.0, -1.0):
      edge = plus(middle, scaled(across, way))
      edges.append((edge[0], edge[1], self._heightAt(edge) + LIFT))
    arm = minus(middle, body.placeOf(state, body.centre))
    moving = plus(state.velocity, cross(state.spin, arm))
    sliding = norm(minus(moving, scaled(up, dot(moving, up))))
    kind = 'skid' if sliding > SKID else 'scrub' if sliding > SCRUB else (
      'print')
    left, right = edges if dot(cross(axle, up), moving) >= 0.0 else (
      edges[1], edges[0])
    return middle, left, right, kind

  def _heightAt(self, point: tuple) -> float:
    """Returns how high the ground is under 'point'."""
    terrain = self.ground.terrain
    return 0.0 if terrain is None else terrain.heightAt(point[0], point[1])

  def _upAt(self, point: tuple) -> tuple:
    """Returns the ground's upward normal under 'point'."""
    terrain = self.ground.terrain
    return (0.0, 0.0, 1.0) if terrain is None else terrain.normalAt(
      point[0], point[1])
