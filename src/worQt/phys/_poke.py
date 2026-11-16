"""
Poking a body: 'hitOf' finds the nearest body a ray meets, where, and
the surface's outward normal there; 'poked' gives a body an impulse at
a point. Together they push what a click lands on. 'driven' turns a
body about an axis toward a speed, as a motor does, no harder than its
torque; 'motorTorque' is how hard a motor twists at a speed,
'runMotor' sets a 'Motor''s drive to twist so at every step, and
'rotorSpinOf' how fast a 'Motor's rotor turns on its housing. 'reachOf'
is how far a body's shape reaches from its centre of mass.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import TYPE_CHECKING

import numpy

from ._body import Body, State
from ._shape import Sphere
from ._turned import Turned
from ._vectors import Vector, conjugate, cross, dot, minus, norm, plus
from ._vectors import rotated, scaled, solved

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Assembly


def hitOf(assembly: Assembly, states: tuple[State, ...], eye: Vector,
          direction: Vector, passed: tuple[int, ...]) -> tuple | None:
  """The 'hitOf' function returns the nearest body of 'assembly' (in
  'states') the ray from 'eye' along 'direction' meets: its index, the
  point met, and the surface's outward normal there; passing over the
  bodies 'passed' and the faces turned away from the ray. None where it
  meets none."""
  length = norm(direction)
  if length == 0.0:
    return None
  way = scaled(direction, 1.0 / length)
  best = None
  for index, (body, state) in enumerate(zip(assembly.bodies, states)):
    if index in passed or body.shape is None:
      continue
    if isinstance(body.shape, Sphere):
      found = _onBall(body.placeOf(state, body.centre), body.shape.radius,
                      eye, way)
    else:
      found = _onShape(body, state, eye, way)
    if found is not None and (best is None or found[0] < best[0]):
      best = (found[0], index, found[1])
  if best is None:
    return None
  far, index, normal = best
  return index, plus(eye, scaled(way, far)), normal


def poked(body: Body, state: State, point: Vector,
          impulse: Vector) -> State:
  """The 'poked' function returns 'state' after 'impulse', N s, given
  'body' at 'point', both in the world: its velocity changes by the
  impulse over its mass, its spin by its inertia's inverse times the
  twist about its centre; and it wakes."""
  centre = body.placeOf(state, body.centre)
  velocity = plus(state.velocity, scaled(impulse, 1.0 / body.mass))
  inertia = body.inertiaIn(state)
  momentum = plus(_times(inertia, state.spin),
                  cross(minus(point, centre), impulse))
  spin = tuple(solved([list(row) for row in inertia], list(momentum)))
  return State(state.place, state.turn, velocity, spin, state.bristles,
               state.holds, 0.0)


def driven(body: Body, state: State, axis: Vector, wanted: float,
           torque: float, seconds: float) -> State:
  """The 'driven' function returns 'state' as a motor leaves 'body'
  after turning it for 'seconds' about the unit 'axis' (in the world,
  through its centre) toward 'wanted' rad/s, with at most 'torque' N m:
  its angular momentum about the axis changed toward that of turning so
  fast by no more than torque x seconds, as a twist (its centre's
  velocity as it was); woken. What holds the motor takes the twist
  back."""
  inertia = body.inertiaIn(state)
  about = dot(axis, _times(inertia, axis))
  gap = about * (wanted - dot(axis, state.spin))
  most = torque * seconds
  gap = max(-most, min(most, gap))
  change = solved([list(row) for row in inertia], list(scaled(axis, gap)))
  return State(state.place, state.turn, state.velocity,
               plus(state.spin, tuple(change)), state.bristles,
               state.holds, 0.0)


def motorTorque(stall: float, free: float, spin: float) -> float:
  """The 'motorTorque' function returns how hard an electric motor
  twists its rotor turning 'spin' rad/s on its housing, N m: 'stall'
  standing, less straight with the speed to nought at 'free' rad/s (a
  motor on a steady voltage: the faster it turns the more its windings
  push back), braking past it, harder than 'stall' turned backwards;
  no harder either way than twice 'stall' (its current is cut there)."""
  torque = stall * (1.0 - spin / free)
  return max(-2.0 * stall, min(2.0 * stall, torque))


def runMotor(drive: object, stall: float, free: float, on: bool) -> None:
  """The 'runMotor' function sets 'drive' (a 'Motor''s 'Drive') to run
  as an electric motor ('motorTorque': 'stall' N m standing, nought at
  'free' rad/s, braking past it, cut at twice 'stall'), worked out at
  every half step (worked out once a frame, a light pinion free in its
  teeth's play overran its free speed within the frame, the motor
  braked hard the next, and it rattled), or, 'on' False, to turn
  freely."""
  drive.stiffness, drive.target = 0.0, 0.0
  drive.torque = stall if on else 0.0
  drive.damping = stall / free if on else 0.0
  drive.most = 2.0 * stall if on else 0.0

def rotorSpinOf(motor: object, states: tuple[State, ...]) -> float:
  """The 'rotorSpinOf' function returns how fast the rotor of 'motor'
  (a 'Motor': its second body) turns on its housing (its first, or the
  world) about the motor's axis, rad/s, in 'states'."""
  rotor = states[motor.second]
  axis = rotated(rotor.turn, motor.axis)
  spin = rotor.spin if motor.first is None else minus(
    rotor.spin, states[motor.first].spin)
  return dot(spin, axis)


def reachOf(body: Body) -> float:
  """The 'reachOf' function returns how far the shape of 'body' reaches
  from its centre of mass, m: the ball about the centre holding it
  whole; nought for a body with no shape."""
  return _reachOf(body.shape, body.centre)


@functools.lru_cache(maxsize=4096)
def _reachOf(shape: object, centre: Vector) -> float:
  """Returns how far 'shape' reaches from 'centre'."""
  if shape is None:
    return 0.0
  if isinstance(shape, Sphere):
    return shape.radius + norm(centre)
  if isinstance(shape, Turned):
    _, out, low, high = shape.bounds()
    return math.hypot(out, max(-low, high)) + norm(centre)
  return max(norm(minus(point, centre)) for point in shape.points)


def _times(matrix: tuple, vector: Vector) -> Vector:
  """Returns 'matrix' times 'vector'."""
  return tuple(dot(row, vector) for row in matrix)


def _onBall(centre: Vector, radius: float, eye: Vector,
            way: Vector) -> tuple | None:
  """Returns how far along the unit 'way' from 'eye' the ray first
  meets the ball at 'centre', and the outward normal there; None where
  it misses it or it is behind."""
  off = minus(eye, centre)
  b = dot(off, way)
  c = dot(off, off) - radius * radius
  under = b * b - c
  if under < 0.0:
    return None
  far = -b - math.sqrt(under)
  if far <= 0.0:
    return None
  point = plus(eye, scaled(way, far))
  return far, scaled(minus(point, centre), 1.0 / radius)


def _onShape(body: Body, state: State, eye: Vector,
             way: Vector) -> tuple | None:
  """Returns how far along the unit 'way' from 'eye' the ray first
  meets a face of the body's shape turned toward it, and that face's
  outward normal; None where it meets none (or the ball holding the
  shape whole, which is looked at first)."""
  off = minus(body.placeOf(state, body.centre), eye)
  along, reach = dot(off, way), reachOf(body)
  if along < -reach or dot(off, off) - along * along > reach * reach:
    return None
  if isinstance(body.shape, Turned):
    return _onTurned(body, state, eye, way)
  back = conjugate(state.turn)
  start = plus(rotated(back, minus(eye, state.place)), body.centre)
  found = _onCorners(_cornersOf(body.shape), start, rotated(back, way))
  if found is None:
    return None
  return found[0], rotated(state.turn, found[1])


@functools.lru_cache(maxsize=4096)
def _cornersOf(shape: object) -> numpy.ndarray:
  """Returns the faces of 'shape' as an array of their corners (n, 3,
  3: in its own frame), made once a shape."""
  points = numpy.array(shape.points, numpy.float64)
  return points[numpy.array(shape.faces, numpy.int64)]


def _onCorners(corners: numpy.ndarray, eye: Vector,
               way: Vector) -> tuple | None:
  """Returns how far along 'way' from 'eye' the ray first meets one of
  the faces whose 'corners' (n, 3, 3) are given, turned toward it, and
  its outward normal; None for none ('_onFaces' for every face at once)."""
  eye, way = numpy.array(eye, numpy.float64), numpy.array(way, numpy.float64)
  a, b, c = corners[:, 0], corners[:, 1], corners[:, 2]
  facing = numpy.cross(b - a, c - a)
  size = numpy.linalg.norm(facing, axis=1)
  toward = facing @ way
  turned = (size > 0.0) & (toward < 0.0)
  if not turned.any():
    return None
  a, b, c = a[turned], b[turned], c[turned]
  facing, size, toward = facing[turned], size[turned], toward[turned]
  far = numpy.einsum('ij,ij->i', facing, a - eye) / toward
  point = eye + far[:, None] * way
  inside = far > 0.0
  for p, q in ((a, b), (b, c), (c, a)):
    inside &= numpy.einsum('ij,ij->i', numpy.cross(q - p, point - p),
                           facing) >= -1e-12 * size
  if not inside.any():
    return None
  k = numpy.flatnonzero(inside)[numpy.argmin(far[inside])]
  return float(far[k]), tuple(float(x) for x in facing[k] / size[k])


def _onTurned(body: Body, state: State, eye: Vector,
              way: Vector) -> tuple | None:
  """Returns '_onShape' for a turned solid: the ray taken into its own
  frame, only the faces of the sides whose boxes it passes through
  looked at (a few of its sides, not all of them round), the normal
  turned back out."""
  shape, back = body.shape, conjugate(state.turn)
  start = plus(rotated(back, minus(eye, state.place)), body.centre)
  along = rotated(back, way)
  mesh, boxes = shape.mesh(), _sideBoxesOf(shape)
  count = len(mesh.points) // shape.sides
  faces = []
  for side, (low, high) in enumerate(boxes):
    if _meetsBox(start, along, low, high):
      first = 2 * side * count
      faces.extend(mesh.faces[first:first + 2 * count])
  found = _onFaces(mesh.points, faces, start, along)
  if found is None:
    return None
  return found[0], rotated(state.turn, found[1])


def _onFaces(places: list, faces: tuple, eye: Vector,
             way: Vector) -> tuple | None:
  """Returns how far along 'way' from 'eye' the ray first meets one of
  'faces' (corners in 'places') turned toward it, and its outward
  normal; None for none."""
  best = None
  for i, j, k in faces:
    a, b, c = places[i], places[j], places[k]
    facing = cross(minus(b, a), minus(c, a))
    size = norm(facing)
    toward = dot(facing, way)
    if size == 0.0 or toward >= 0.0:
      continue
    far = dot(facing, minus(a, eye)) / toward
    if far <= 0.0 or (best is not None and far >= best[0]):
      continue
    point = plus(eye, scaled(way, far))
    if all(dot(cross(minus(q, p), minus(point, p)), facing) >= -1e-12 * size
           for p, q in ((a, b), (b, c), (c, a))):
      best = (far, scaled(facing, 1.0 / size))
  return best


def _meetsBox(start: Vector, way: Vector, low: Vector,
              high: Vector) -> bool:
  """Tells whether the ray from 'start' along 'way' meets the box from
  'low' to 'high' (slabs)."""
  near, far = 0.0, math.inf
  for s, w, lo, hi in zip(start, way, low, high):
    if w == 0.0:
      if s < lo or s > hi:
        return False
      continue
    a, b = (lo - s) / w, (hi - s) / w
    if a > b:
      a, b = b, a
    near, far = max(near, a), min(far, b)
    if near > far:
      return False
  return True


@functools.lru_cache(maxsize=16)
def _sideBoxesOf(shape: Turned) -> tuple:
  """Returns the box about each side of a turned solid's mesh (its
  outline there and at the next side), in its own frame, a hair
  larger."""
  points = shape.mesh().points
  count = len(points) // shape.sides
  out = []
  for side in range(shape.sides):
    after = (side + 1) % shape.sides
    near = points[side * count:(side + 1) * count]
    near = near + points[after * count:(after + 1) * count]
    out.append((tuple(min(p[k] for p in near) - 1e-9 for k in range(3)),
                tuple(max(p[k] for p in near) + 1e-9 for k in range(3))))
  return tuple(out)
