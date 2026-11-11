"""
Trench is the way a ball goes on the cloth as a shot sends it, a ball
wide, to where it first meets a cushion or a ball or comes to rest;
'Trenches' finds ball 1's along the aim and, when it meets a ball, that
ball's, ball 2's, and ball 1's on from the hit.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from functools import lru_cache
from typing import NamedTuple

import numpy

from ._carom_table import STILL, Ball, CaromTable, isParked
from ._cloth import Cloth
from ._cue import Cue
from ._trails import ribbonMesh

#  Phases a ball goes through on the cloth before it rests, at most.
_PHASES = 4
#  Places a slide is followed by: a slide curves, a roll runs straight.
_SLIDE_PLACES = 48
#  The least speed, mm/s, and spin, rad/s, a ball leaves a hit with to
#  have a way after it.
_LEAST_SPEED = 1.0
_LEAST_SPIN = 0.05


class Trench(NamedTuple):
  """
  Trench is the way ball 'name' goes, 'points', where its middle passes,
  (x, y) on the table, from where it sets off to where it 'end's: at a
  'cushion', touching it; at a 'ball', 'met', touching it; or at a
  'stop', at rest before it meets anything.
  """

  name: str
  points: tuple[tuple[float, float], ...]
  end: str
  met: str = ''

  def startPlace(self, ) -> tuple[float, float]:
    """The 'startPlace' method returns where the ball sets off."""
    return self.points[0]

  def endPlace(self, ) -> tuple[float, float]:
    """The 'endPlace' method returns where the ball's middle is as the
    trench ends."""
    return self.points[-1]

  def distance(self, ) -> float:
    """The 'distance' method returns how far the ball's middle goes
    along the trench."""
    places = numpy.asarray(self.points, float)
    steps = numpy.diff(places, axis=0)
    return float(numpy.hypot(steps[:, 0], steps[:, 1]).sum())


class Trenches(NamedTuple):
  """
  Trenches finds the ways balls go on 'table' as a shot struck with
  'cue' sends them over 'cloth' (the user: the shadow both eyes see, a
  trench, telling whereabouts ball 1 stops, and ball 2's too, and both
  after the hit). Ball 1, sent along the aim at a speed and a point
  struck as 'Cue.sent' sends it, goes straight on to the first cushion
  it would touch, the first ball it would meet, or where it comes to
  rest on the cloth, as 'Cloth' moves it exactly, sliding then rolling
  ('trenchesOf'). Meeting a ball, the two part as frictionless equal
  balls: the ball met sets off along the line of their middles with
  ball 1's speed along it, sliding without spin; ball 1 keeps its speed
  across that line and all its spin, so follow and draw bend its way
  till it rolls; each on to the first cushion, ball or rest. A guide:
  the cushions, the balls' throw and the spin passed on in the hit are
  not in it.
  """

  table: CaromTable = CaromTable()
  cloth: Cloth = Cloth()
  cue: Cue = Cue()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def trenchesOf(self, balls: tuple[Ball, ...], cue: str, aimX: float,
                 aimY: float, speed: float, top: float,
                 side: float) -> tuple[Trench, ...]:
    """The 'trenchesOf' method returns the trenches of a shot, 'cue' of
    'balls' sent along 'aimX', 'aimY' at 'speed' mm/s, struck at 'top'
    and 'side' as shares of the radius: ball 1's to the first thing it
    meets or its rest; if that is a ball, that ball's on from the hit
    and, if it goes on at all, ball 1's on from it. None if there is no
    such ball or no aim."""
    named = {ball.name: ball for ball in balls}
    first = named.get(cue)
    size = math.hypot(aimX, aimY)
    if first is None or size <= 0.0 or isParked(first.x, first.y):
      return ()
    dx, dy = aimX / size, aimY / size
    radius = self.table.radius
    phases = _phasesOf(self.cloth, self.cue, speed, top, side, radius)
    reach = _reachOf(phases)
    way = ((first.x, first.y),
           (first.x + dx * reach, first.y + dy * reach))
    others = [ball for ball in balls if ball.name != cue]
    trench = self._trenchOf(cue, way, others)
    if trench.end != 'ball':
      return (trench,)
    met = named[trench.met]
    gx, gy = trench.endPlace()
    nx, ny = met.x - gx, met.y - gy
    apart = math.hypot(nx, ny)
    if apart <= 0.0:
      return (trench,)
    nx, ny = nx / apart, ny / apart
    x, y, vx, vy, wx, wy, wz = _stateAt(self.cloth, phases,
                                        trench.distance(), radius)
    vx, vy = vx * dx - vy * dy, vx * dy + vy * dx
    wx, wy = wx * dx - wy * dy, wx * dy + wy * dx
    passed = vx * nx + vy * ny
    if passed <= 0.0:
      return (trench,)
    rest = [ball for ball in others if ball.name != met.name]
    hit = Ball(met.name, met.x, met.y, STILL, passed * nx, passed * ny)
    out = [trench, self._trenchOf(met.name, self._wayOf(hit), rest)]
    on = Ball(cue, gx, gy, STILL, vx - passed * nx, vy - passed * ny, wx,
              wy, wz)
    moving = math.hypot(on.vx, on.vy) > _LEAST_SPEED
    spinning = math.hypot(on.wx, on.wy) > _LEAST_SPIN
    if moving or spinning:
      after = self._trenchOf(cue, self._wayOf(on), rest)
      if after.distance() > 0.0:
        out.append(after)
    return tuple(out)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _wayOf(self, ball: Ball) -> tuple[tuple[float, float], ...]:
    """Returns where the middle of 'ball' passes on the cloth until it
    rests, cushions and balls left out: each slide followed by
    '_SLIDE_PLACES' places, each roll, straight, by its ends."""
    radius = self.table.radius
    cloth = self.cloth
    points = [(ball.x, ball.y)]
    for _ in range(_PHASES):
      phase = cloth.phaseOf(ball, radius)
      if phase not in ('sliding', 'rolling'):
        break
      span = cloth.phaseTime(ball, phase, radius)
      count = _SLIDE_PLACES if phase == 'sliding' else 1
      for k in range(1, count + 1):
        moment = cloth.motionAt(ball, phase, span * k / count, radius)
        points.append((moment[0], moment[1]))
      ball = _phaseEnded(cloth, ball, phase, span, radius)
    return tuple(points)

  def _trenchOf(self, name: str, way: tuple,
                others: list[Ball]) -> Trench:
    """Returns the trench of ball 'name' going along 'way': cut where it
    first touches a cushion or meets one of 'others', else to its end,
    where it rests."""
    table = self.table
    radius = table.radius
    rise = table.nose - radius
    inside = math.sqrt(max(radius * radius - rise * rise, 0.0))
    walls = ((0, inside, -1.0), (0, table.width - inside, 1.0),
             (1, inside, -1.0), (1, table.length - inside, 1.0))
    circles = [(ball.x, ball.y, ball.name) for ball in others
               if not isParked(ball.x, ball.y)]
    reach = 2.0 * radius
    points = [way[0]]
    for (px, py), (qx, qy) in zip(way[:-1], way[1:]):
      first, end, met = math.inf, 'stop', ''
      for axis, line, out in walls:
        start, stop = (px, qx) if axis == 0 else (py, qy)
        going = (stop - start) * out
        if going <= 0.0:
          continue
        beyond = (start - line) * out
        if beyond >= 0.0:
          share = 0.0
        else:
          share = -beyond / going
        if share <= 1.0 and share < first:
          first, end, met = share, 'cushion', ''
      ex, ey = qx - px, qy - py
      square = ex * ex + ey * ey
      for cx, cy, other in circles:
        fx, fy = px - cx, py - cy
        near = fx * ex + fy * ey
        gap = fx * fx + fy * fy - reach * reach
        if gap <= 0.0:
          share = 0.0 if near < 0.0 else math.inf
        elif square <= 0.0 or near >= 0.0:
          continue
        else:
          room = near * near - square * gap
          if room < 0.0:
            continue
          share = (-near - math.sqrt(room)) / square
        if share <= 1.0 and share < first:
          first, end, met = share, 'ball', other
      if first <= 1.0:
        points.append((px + ex * first, py + ey * first))
        return Trench(name, tuple(points), end, met)
      points.append((qx, qy))
    return Trench(name, tuple(points), 'stop')


def _phaseEnded(cloth: Cloth, ball: Ball, phase: str, span: float,
                radius: float) -> Ball:
  """Returns 'ball' as 'phase', 'span' long, ends and the next begins."""
  x, y, vx, vy, wx, wy = cloth.motionAt(ball, phase, span, radius)
  wz = cloth.spinAt(ball, span, radius)
  ended = Ball(ball.name, x, y, STILL, vx, vy, wx, wy, wz)
  return cloth.settled(ended, phase, radius)


@lru_cache(maxsize=64)
def _phasesOf(cloth: Cloth, cue: Cue, speed: float, top: float,
              side: float, radius: float) -> tuple:
  """Returns how ball 1, sent along +x from the origin at 'speed' mm/s
  struck at 'top' and 'side', goes over 'cloth' until it rests: each
  phase it moves in, sliding or rolling, as (ball, phase, span, along,
  forward, ahead), the ball as the phase begins, how long it lasts, how
  far along it has come, its speed along and how fast that changes, the
  same all through it. The same along any aim, so worked out once."""
  ball = cue.sent(Ball('cue', 0.0, 0.0), 1.0, 0.0, speed, top, side,
                  radius)
  phases = []
  for _ in range(_PHASES):
    phase = cloth.phaseOf(ball, radius)
    if phase not in ('sliding', 'rolling'):
      break
    span = cloth.phaseTime(ball, phase, radius)
    ahead = cloth.accelerationOf(ball, phase, radius)[0]
    phases.append((ball, phase, span, ball.x, ball.vx, ahead))
    ball = _phaseEnded(cloth, ball, phase, span, radius)
  return tuple(phases)


def _reachOf(phases: tuple) -> float:
  """Returns how far along the ball 'phases' move gets at most."""
  most = 0.0
  for _, _, span, along, forward, ahead in phases:
    most = max(most, along)
    turns = -forward / ahead if ahead != 0.0 else -1.0
    for time in (span, turns):
      if 0.0 <= time <= span:
        most = max(most, along + forward * time + 0.5 * ahead * time * time)
  return most


def _stateAt(cloth: Cloth, phases: tuple, distance: float,
             radius: float) -> tuple:
  """Returns how the ball 'phases' move is as it first comes 'distance'
  along: (x, y, vx, vy, wx, wy, wz) along +x; still where it never
  gets."""
  for ball, phase, span, along, forward, ahead in phases:
    end = along + forward * span + 0.5 * ahead * span * span
    if distance > end:
      continue
    need = max(distance - along, 0.0)
    #  The first time 'ahead' t² / 2 + 'forward' t comes to 'need'.
    root = math.sqrt(max(forward * forward + 2.0 * ahead * need, 0.0))
    time = 2.0 * need / (forward + root) if forward + root > 0.0 else 0.0
    time = min(max(time, 0.0), span)
    moment = cloth.motionAt(ball, phase, time, radius)
    return (*moment, cloth.spinAt(ball, time, radius))
  return distance, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0


def trenchMesh(points: tuple, half: float, lift: float,
               pieces: int = 24) -> numpy.ndarray:
  """The 'trenchMesh' function returns the triangles of a trench seen on
  the cloth, 'points' its middle's way, each its 'x' and 'z', in the
  plane 'lift' above nought, as 'ribbonMesh' returns them: a band
  'half' either side of the way, ending round in half a disc of radius
  'half' about its last place, the ball's own outline where it stops or
  touches; 'pieces' triangles round that half."""
  places = numpy.asarray(points, float).reshape(-1, 2)
  band = ribbonMesh(places, half, lift)
  x1, z1 = places[-1]
  dx, dz = 1.0, 0.0
  for x0, z0 in places[-2::-1]:
    size = math.hypot(x1 - x0, z1 - z0)
    if size > 1e-9:
      dx, dz = (x1 - x0) / size, (z1 - z0) / size
      break
  sx, sz = -dz * half, dx * half
  ax, az = dx * half, dz * half
  corners = []
  for k in range(pieces):
    for angle in (math.pi * k / pieces, math.pi * (k + 1) / pieces):
      c, s = math.cos(angle), math.sin(angle)
      corners.append((x1 + c * sx + s * ax, z1 + c * sz + s * az))
    corners.append((x1, z1))
  cap = numpy.zeros((len(corners), 6))
  cap[:, 0] = [corner[0] for corner in corners]
  cap[:, 1] = lift
  cap[:, 2] = [corner[1] for corner in corners]
  cap[:, 4] = 1.0
  return numpy.vstack((band, cap))
