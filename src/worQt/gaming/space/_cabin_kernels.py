"""
The Warp kernels that step the cabin's loose bodies (user, 2026-11-17:
Asger getting up and floating round in micro-gravity, "FAFO rules"; the
loose things too): in the vessel's own axes, which move and turn, so
each body feels what is felt there (the vessel's push, its turning)
and the gravity enchantment's pull toward the floor.

Two launches a small step: 'pressed' (a thread a point) finds where
each body's points meet the cabin (its floor, its cone of a wall, its
ceiling), the solids fixed in it and the other bodies' boxes, and pushes
(a spring and a damper along the meeting's normal, as stiff as its
body's share of 'OMEGA', rubbing along it no harder than 'GRIP' of the
push), the push's other half onto the other body; 'moved' (a thread a
body) moves each body a step on by what pushed it and what is felt
there (semi-implicit Euler; a body's spin by Euler's equations in its
own axes).

Body 0 is Asger: never turned (his up the host's), five balls along it
from his feet to his head, moved by his legs as the host asks while he
touches something (walking: along the ground, as fast as asked; else
pushing off along the way asked), a leap once; left out while he sits.
The loose things are boxes: their eight corners meet the rest (a ball
of 'SKIN' each, inside the box), their boxes are met by the others'
points. float32 throughout ('feedback: GPU always'): a few metres in
the cabin.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import warp as wp

from ._cockpit import FLOOR, NOSE, WALL, capsuleRadius

wp.config.log_level = wp.LOG_WARNING
wp.set_module_options({'enable_backward': False})


def _single(x: float) -> object:
  """Returns 'x' as a float32 constant of Warp's."""
  return wp.constant(wp.float32(x))


#  The cabin: its floor's and ceiling's heights; its wall's inner radius
#  at the floor and how fast it narrows going up (m a m), and the cosine
#  of the wall's lean (a distance across it is the radial one times it).
CABIN_FLOOR = _single(FLOOR)
CABIN_TOP = _single(NOSE)
_LOW = capsuleRadius(FLOOR) - WALL
_SLOPE = (capsuleRadius(NOSE) - capsuleRadius(FLOOR)) / (NOSE - FLOOR)
CABIN_LOW = _single(_LOW)
CABIN_SLOPE = _single(_SLOPE)
CABIN_LEAN = _single(1.0 / (1.0 + _SLOPE * _SLOPE) ** 0.5)
#  A meeting's spring: four of them carry a body at 'OMEGA' rad/s (its
#  mass by them sinks g / OMEGA² under g: 0.16 mm at one g, 0.8 mm at
#  five), damped 'DAMPING' of critical; rubbing at most 'GRIP' of the
#  push, slipping slower than that stuck by a damper as stiff.
OMEGA = _single(250.0)
DAMPING = _single(0.4)
GRIP = _single(0.5)
#  A loose box's corners are balls this big, inside its corners.
SKIN_SIZE = 0.004
SKIN = _single(SKIN_SIZE)
#  A meeting closing faster than this, m/s, thuds; Asger touches what is
#  within 'NEAR' of him, m (floating a hair off the floor, he can still
#  push off it).
THUD = _single(0.6)
NEAR = _single(0.03)
#  Air in the cabin slows what moves through it, a share a second: a
#  loose thing, its spin, Asger (heavy for his size: he drifts on).
AIR = _single(0.03)
AIR_SPIN = _single(0.05)
AIR_ASGER = _single(0.01)
#  Asger's legs: how fast they bring him to the speed asked (most of the
#  way in), s, and at most how hard, m/s².
LEGS_TIME = _single(0.1)
LEGS_MOST = _single(40.0)


@wp.func
def meetingPush(depth: float, normal: wp.vec3, moving: wp.vec3,
                heft: float, grip: float) -> wp.vec3:
  """Returns the push on a point 'depth' m into something along
  'normal' (out of it), moving 'moving' against it, its body's share of
  mass 'heft' kg: a spring and a damper along the normal (never
  pulling), rubbing across it at most 'grip' of the push."""
  stiff = heft * OMEGA * OMEGA * 0.25
  damp = heft * OMEGA * DAMPING * 0.5
  closing = wp.dot(moving, normal)
  push = wp.max(stiff * depth - damp * closing, 0.0)
  sliding = moving - closing * normal
  speed = wp.length(sliding)
  out = push * normal
  if speed > 1.0e-6:
    rub = wp.min(grip * push, heft * OMEGA * 0.25 * speed)
    out = out - sliding * (rub / speed)
  return out


@wp.func
def boxDepth(point: wp.vec3, radius: float, middle: wp.vec3,
             turn: wp.quat, half: wp.vec3) -> wp.vec4:
  """Returns how far a ball ('point', 'radius') is into a box ('middle',
  'turn', 'half') and the way out of it: the normal's x, y, z and the
  depth (below nought: not in)."""
  local = wp.quat_rotate_inv(turn, point - middle)
  near = wp.vec3(wp.clamp(local[0], -half[0], half[0]),
                 wp.clamp(local[1], -half[1], half[1]),
                 wp.clamp(local[2], -half[2], half[2]))
  off = local - near
  apart = wp.length(off)
  depth = float(-1.0)
  normal = wp.vec3(0.0, 0.0, 1.0)
  if apart > 1.0e-9:
    if apart < radius:
      depth = radius - apart
      normal = off / apart
  else:
    ex = half[0] - wp.abs(local[0])
    ey = half[1] - wp.abs(local[1])
    ez = half[2] - wp.abs(local[2])
    side = float(1.0)
    if ex <= ey and ex <= ez:
      if local[0] < 0.0:
        side = -1.0
      depth = radius + ex
      normal = wp.vec3(side, 0.0, 0.0)
    elif ey <= ez:
      if local[1] < 0.0:
        side = -1.0
      depth = radius + ey
      normal = wp.vec3(0.0, side, 0.0)
    else:
      if local[2] < 0.0:
        side = -1.0
      depth = radius + ez
      normal = wp.vec3(0.0, 0.0, side)
  way = wp.quat_rotate(turn, normal)
  return wp.vec4(way[0], way[1], way[2], depth)


@wp.func
def thudOf(depth: float, closing: float, before: int, heft: float,
           thuds: wp.array(dtype=wp.float32)) -> int:
  """Counts a thud on a meeting begun closing fast ('before': the point
  touched nothing the step before), its loudness by its speed and heft;
  returns one (it touches)."""
  if before == 0 and -closing > THUD:
    wp.atomic_add(thuds, 0, 1.0)
    wp.atomic_max(thuds, 1, -closing * wp.min(1.0, wp.sqrt(heft / 20.0)))
  return 1


@wp.kernel
def pressed(places: wp.array(dtype=wp.vec3),
            turns: wp.array(dtype=wp.quat),
            velocities: wp.array(dtype=wp.vec3),
            spins: wp.array(dtype=wp.vec3),
            masses: wp.array(dtype=wp.float32),
            halves: wp.array(dtype=wp.vec3),
            owners: wp.array(dtype=wp.int32),
            locals: wp.array(dtype=wp.vec3),
            radii: wp.array(dtype=wp.float32),
            solidMiddles: wp.array(dtype=wp.vec3),
            solidTurns: wp.array(dtype=wp.quat),
            solidHalves: wp.array(dtype=wp.vec3),
            touched: wp.array(dtype=wp.int32),
            pushes: wp.array(dtype=wp.vec3),
            twists: wp.array(dtype=wp.vec3),
            asger: wp.array(dtype=wp.vec3),
            thuds: wp.array(dtype=wp.float32),
            up: wp.vec3, present: int, legs: int):
  """Pushes each point (a thread a point) out of what it is in: the
  floor, the ceiling, the wall, the solids, the other bodies' boxes
  (their share pushed back); counts Asger's meetings ('asger' 0: their
  count in x, 1: their normals summed: he touches what is within 'NEAR'
  of him; his legs at work ('legs'), they hold him, not the rubbing)
  and the thuds."""
  i = wp.tid()
  body = owners[i]
  middle = places[body]
  arm = wp.vec3(0.0, 0.0, 0.0)
  moving = velocities[body]
  margin = float(0.0)
  grip = GRIP
  if body == 0:
    if present == 0:
      touched[i] = 0
      return
    arm = up * locals[i][2]
    margin = NEAR
    if legs == 1:
      grip = 0.0
  else:
    arm = wp.quat_rotate(turns[body], locals[i])
    moving = moving + wp.cross(spins[body], arm)
  point = middle + arm
  radius = radii[i] + margin
  heft = masses[body]
  before = touched[i]
  touching = int(0)
  push = wp.vec3(0.0, 0.0, 0.0)
  normals = wp.vec3(0.0, 0.0, 0.0)
  depth = radius - (point[2] - CABIN_FLOOR)
  if depth > 0.0:
    normal = wp.vec3(0.0, 0.0, 1.0)
    touching = thudOf(depth, wp.dot(moving, normal), before, heft, thuds)
    normals = normals + normal
    if depth > margin:
      push = push + meetingPush(depth - margin, normal, moving, heft, grip)
  depth = radius - (CABIN_TOP - point[2])
  if depth > 0.0:
    normal = wp.vec3(0.0, 0.0, -1.0)
    touching = thudOf(depth, wp.dot(moving, normal), before, heft, thuds)
    normals = normals + normal
    if depth > margin:
      push = push + meetingPush(depth - margin, normal, moving, heft, grip)
  across = wp.sqrt(point[0] * point[0] + point[1] * point[1])
  inner = CABIN_LOW + CABIN_SLOPE * wp.clamp(point[2] - CABIN_FLOOR, 0.0,
                                             CABIN_TOP - CABIN_FLOOR)
  depth = radius - (inner - across) * CABIN_LEAN
  if depth > 0.0 and across > 1.0e-6:
    normal = wp.vec3(-point[0] / across * CABIN_LEAN,
                     -point[1] / across * CABIN_LEAN,
                     CABIN_SLOPE * CABIN_LEAN)
    touching = thudOf(depth, wp.dot(moving, normal), before, heft, thuds)
    normals = normals + normal
    if depth > margin:
      push = push + meetingPush(depth - margin, normal, moving, heft, grip)
  for j in range(solidMiddles.shape[0]):
    half = solidHalves[j]
    if wp.length(point - solidMiddles[j]) < wp.length(half) + radius:
      met = boxDepth(point, radius, solidMiddles[j], solidTurns[j], half)
      if met[3] > 0.0:
        normal = wp.vec3(met[0], met[1], met[2])
        touching = thudOf(met[3], wp.dot(moving, normal), before, heft,
                          thuds)
        normals = normals + normal
        if met[3] > margin:
          push = push + meetingPush(met[3] - margin, normal, moving, heft,
                                    grip)
  for other in range(1, places.shape[0]):
    if other != body:
      half = halves[other]
      there = places[other]
      if wp.length(point - there) < wp.length(half) + radius:
        met = boxDepth(point, radius, there, turns[other], half)
        if met[3] > 0.0:
          normal = wp.vec3(met[0], met[1], met[2])
          meeting = point - radius * normal
          theirs = velocities[other] + wp.cross(spins[other],
                                                meeting - there)
          shared = heft * masses[other] / (heft + masses[other])
          touching = thudOf(met[3], wp.dot(moving - theirs, normal),
                            before, shared, thuds)
          normals = normals + normal
          if met[3] > margin:
            metPush = meetingPush(met[3] - margin, normal, moving - theirs,
                                  shared, GRIP)
            push = push + metPush
            wp.atomic_add(pushes, other, -metPush)
            wp.atomic_add(twists, other, wp.cross(meeting - there,
                                                  -metPush))
  touched[i] = touching
  if touching == 0:
    return
  wp.atomic_add(pushes, body, push)
  if body == 0:
    wp.atomic_add(asger, 0, wp.vec3(1.0, 0.0, 0.0))
    wp.atomic_add(asger, 1, normals)
  else:
    wp.atomic_add(twists, body, wp.cross(arm, push))


@wp.kernel
def moved(places: wp.array(dtype=wp.vec3),
          turns: wp.array(dtype=wp.quat),
          velocities: wp.array(dtype=wp.vec3),
          spins: wp.array(dtype=wp.vec3),
          masses: wp.array(dtype=wp.float32),
          inertias: wp.array(dtype=wp.vec3),
          pushes: wp.array(dtype=wp.vec3),
          twists: wp.array(dtype=wp.vec3),
          asger: wp.array(dtype=wp.vec3),
          met: wp.array(dtype=wp.vec3),
          felt: wp.vec3, turning: wp.vec3, speeding: wp.vec3,
          enchanted: wp.vec3, wanted: wp.vec3, leap: wp.vec3,
          up: wp.vec3, walking: int, wanting: int, present: int,
          step: float):
  """Moves each body (a thread a body) a 'step' on: pushed, and feeling
  the vessel's push 'felt' (its own axes: what it feels, thrust, drag
  and the ground; gravity it does not), its turning ('turning', rad/s)
  and its turning faster ('speeding', rad/s²) and the enchantment's
  pull ('enchanted'); Asger also by his legs ('wanted', 'walking',
  'wanting', a 'leap' once) while he touches something (his meetings
  kept in 'met' for the host). Its pushes are spent (made nought for
  the next step)."""
  b = wp.tid()
  push = pushes[b]
  twist = twists[b]
  pushes[b] = wp.vec3(0.0, 0.0, 0.0)
  twists[b] = wp.vec3(0.0, 0.0, 0.0)
  if b == 0 and present == 0:
    asger[0] = wp.vec3(0.0, 0.0, 0.0)
    asger[1] = wp.vec3(0.0, 0.0, 0.0)
    return
  heft = masses[b]
  place = places[b]
  velocity = velocities[b]
  feel = (push / heft - felt - wp.cross(turning, wp.cross(turning, place))
          - 2.0 * wp.cross(turning, velocity) - wp.cross(speeding, place)
          + enchanted)
  if b == 0:
    touching = asger[0][0] > 0.0
    met[0] = asger[0]
    met[1] = asger[1]
    asger[0] = wp.vec3(0.0, 0.0, 0.0)
    asger[1] = wp.vec3(0.0, 0.0, 0.0)
    if touching:
      velocity = velocity + leap
      legs = (wanted - velocity) / LEGS_TIME
      if walking == 1:
        along = velocity - wp.dot(velocity, up) * up
        legs = (wanted - along) / LEGS_TIME
      size = wp.length(legs)
      if size > LEGS_MOST:
        legs = legs * (LEGS_MOST / size)
      if walking == 1 or wanting == 1:
        feel = feel + legs
    velocity = velocity + (feel - AIR_ASGER * velocity) * step
    places[b] = place + velocity * step
    velocities[b] = velocity
    return
  velocity = velocity + (feel - AIR * velocity) * step
  places[b] = place + velocity * step
  velocities[b] = velocity
  turn = turns[b]
  inertia = inertias[b]
  spin = wp.quat_rotate_inv(turn, spins[b])
  torque = wp.quat_rotate_inv(turn, twist)
  held = wp.cw_mul(inertia, spin)
  spin = spin + wp.cw_div(torque - wp.cross(spin, held), inertia) * step
  spin = wp.quat_rotate(turn, spin)
  spin = spin + (-speeding - wp.cross(turning, spin)
                 - AIR_SPIN * spin) * step
  spins[b] = spin
  turned = turn + wp.quat(spin[0], spin[1], spin[2], 0.0) * turn * (
    0.5 * step)
  turns[b] = wp.normalize(turned)
