"""
The Warp kernels that step the cabin's loose bodies (user, 2026-11-17:
Asger getting up and floating round in micro-gravity, "FAFO rules"; the
loose things too): in the vessel's own axes, which move and turn, so
each body feels what is felt there (the vessel's push, its turning).

Two launches a small step: 'pressed' (a thread a point) finds where
each body's points meet the rooms' walls (the cabin's floor, cone of a
wall and ceiling; docked to the space station also the hatch through
the nose, the port, the hub, the four shafts and the ring's tube over
its deck: 'roomGap', each room how far inside it, the rooms joined as
deep as the deepest: '_stationinterior'), the solids in them (some
moving: the elevators' cages) and the other bodies' boxes, and pushes
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
from . import _stationinterior as rooms
from . import _walkway as walkway

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
#  Docked: the hatch, the port, the hub (radius, from, to up the axis),
#  the shafts (radius, from), the ring (its tube's middle from the axis,
#  its radius inside), the deck (from the axis), the station's plane up
#  the axis ('_stationinterior').
HATCH = _single(rooms.HATCH)
HATCH_LOW = _single(rooms.HATCH_LOW)
HATCH_HIGH = _single(rooms.HATCH_HIGH)
PORT_INSIDE = _single(rooms.PORT_INSIDE)
PORT_LOW = _single(rooms.PORT_LOW)
PORT_HIGH = _single(rooms.PORT_HIGH)
HUB_INSIDE = _single(rooms.HUB_INSIDE)
HUB_LOW = _single(rooms.HUB_LOW)
HUB_HIGH = _single(rooms.HUB_HIGH)
SHAFT_INSIDE = _single(rooms.SHAFT_INSIDE)
SHAFT_FROM = _single(rooms.SHAFT_FROM)
TUBE_MIDDLE = _single(rooms.TUBE_MIDDLE)
TUBE_INSIDE = _single(rooms.TUBE_INSIDE)
DECK = _single(rooms.DECK)
PLANE = _single(rooms.PLANE)
#  On the pad (user, 2026-11-17: "The door out of the rocket should be
#  connected to a retractable walk way"; '_walkway'): the hull's skin at
#  the floor (its radius; it narrows as the wall does), the walkway's
#  tunnel and the tower's platform (each a box: its low and high
#  corners), the doorway through the wall (a box).
HULL_LOW = _single(capsuleRadius(FLOOR))
TUNNEL_LOW = wp.constant(wp.vec3(*walkway.TUNNEL[0]))
TUNNEL_HIGH = wp.constant(wp.vec3(*walkway.TUNNEL[1]))
PLATFORM_LOW = wp.constant(wp.vec3(*walkway.PLATFORM[0]))
PLATFORM_HIGH = wp.constant(wp.vec3(*walkway.PLATFORM[1]))
DOORWAY_LOW = wp.constant(wp.vec3(*walkway.DOORWAY[0]))
DOORWAY_HIGH = wp.constant(wp.vec3(*walkway.DOORWAY[1]))
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
#  The gravity gun pulling him to a magic bolt (user, 2026-11-17: "The
#  gravity gun can pull Asger towards them"): no faster than 'TOW_SPEED'
#  m/s, slowing at 'TOW_BRAKE' m/s² to stop where it holds him, brought
#  to the speed it wants most of the way in 'TOW_TIME' s, at most
#  'TOW_MOST' m/s² (past four g: it holds him under the engine).
TOW_SPEED = _single(6.0)
TOW_BRAKE = _single(6.0)
TOW_TIME = _single(0.15)
TOW_MOST = _single(60.0)


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
def deeper(best: wp.vec4, inside: float, normal: wp.vec3) -> wp.vec4:
  """Returns 'best' or the room face 'inside' its 'normal' (into the
  room), whichever is deeper inside."""
  if inside > best[3]:
    return wp.vec4(normal[0], normal[1], normal[2], inside)
  return best


@wp.func
def shallower(best: wp.vec4, inside: float, normal: wp.vec3) -> wp.vec4:
  """Returns 'best' or the face 'inside' its 'normal', whichever is
  less inside (a room is inside as far as its nearest face)."""
  if inside < best[3]:
    return wp.vec4(normal[0], normal[1], normal[2], inside)
  return best


@wp.func
def roundRoom(point: wp.vec3, radius: float, low: float,
              high: float) -> wp.vec4:
  """Returns how far 'point' is inside a round room on the axis (its
  'radius', from 'low' to 'high' up it) and the way into it from its
  nearest face."""
  across = wp.sqrt(point[0] * point[0] + point[1] * point[1])
  inward = wp.vec3(0.0, 0.0, 1.0)
  if across > 1.0e-6:
    inward = wp.vec3(-point[0] / across, -point[1] / across, 0.0)
  room = wp.vec4(inward[0], inward[1], inward[2], radius - across)
  room = shallower(room, point[2] - low, wp.vec3(0.0, 0.0, 1.0))
  return shallower(room, high - point[2], wp.vec3(0.0, 0.0, -1.0))


@wp.func
def boxRoom(point: wp.vec3, low: wp.vec3, high: wp.vec3) -> wp.vec4:
  """Returns how far 'point' is inside the box room from 'low' to
  'high' (its nearest face) and the way into it from that face."""
  room = wp.vec4(1.0, 0.0, 0.0, point[0] - low[0])
  room = shallower(room, high[0] - point[0], wp.vec3(-1.0, 0.0, 0.0))
  room = shallower(room, point[1] - low[1], wp.vec3(0.0, 1.0, 0.0))
  room = shallower(room, high[1] - point[1], wp.vec3(0.0, -1.0, 0.0))
  room = shallower(room, point[2] - low[2], wp.vec3(0.0, 0.0, 1.0))
  return shallower(room, high[2] - point[2], wp.vec3(0.0, 0.0, -1.0))


@wp.func
def outsideRooms(point: wp.vec3, best: wp.vec4, outside: int) -> wp.vec4:
  """Returns 'best' or the rooms outside the rocket on the pad if
  deeper: 'outside' one, the walkway's tunnel (outside the hull's skin)
  and the tower's platform; two, the doorway."""
  if outside % 2 == 1:
    across = wp.sqrt(point[0] * point[0] + point[1] * point[1])
    outward = wp.vec3(1.0, 0.0, 0.0)
    if across > 1.0e-6:
      outward = wp.vec3(point[0] / across, point[1] / across, 0.0)
    skin = HULL_LOW + CABIN_SLOPE * wp.clamp(point[2] - CABIN_FLOOR, 0.0,
                                             CABIN_TOP - CABIN_FLOOR)
    tunnel = boxRoom(point, TUNNEL_LOW, TUNNEL_HIGH)
    tunnel = shallower(tunnel, (across - skin) * CABIN_LEAN, wp.vec3(
      outward[0] * CABIN_LEAN, outward[1] * CABIN_LEAN,
      -CABIN_SLOPE * CABIN_LEAN))
    best = deeper(best, tunnel[3], wp.vec3(tunnel[0], tunnel[1],
                                           tunnel[2]))
    room = boxRoom(point, PLATFORM_LOW, PLATFORM_HIGH)
    best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  if outside >= 2:
    room = boxRoom(point, DOORWAY_LOW, DOORWAY_HIGH)
    best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  return best


@wp.func
def roomGap(point: wp.vec3, docked: int, outside: int,
            ways: wp.array(dtype=wp.vec3)) -> wp.vec4:
  """Returns how far 'point' is inside the rooms (the cabin; docked
  also the hatch, the port, the hub, the shafts out along 'ways', the
  ring; on the pad the walkway's and the doorway as 'outside' says
  ('outsideRooms'): as deep as the room it is deepest in; less than
  nought: in a wall) and the way into them from the nearest face (x y
  z, then the depth)."""
  across = wp.sqrt(point[0] * point[0] + point[1] * point[1])
  outward = wp.vec3(1.0, 0.0, 0.0)
  if across > 1.0e-6:
    outward = wp.vec3(point[0] / across, point[1] / across, 0.0)
  inner = CABIN_LOW + CABIN_SLOPE * wp.clamp(point[2] - CABIN_FLOOR, 0.0,
                                             CABIN_TOP - CABIN_FLOOR)
  wall = wp.vec3(-outward[0] * CABIN_LEAN, -outward[1] * CABIN_LEAN,
                 CABIN_SLOPE * CABIN_LEAN)
  cabin = wp.vec4(wall[0], wall[1], wall[2], (inner - across) * CABIN_LEAN)
  cabin = shallower(cabin, point[2] - CABIN_FLOOR, wp.vec3(0.0, 0.0, 1.0))
  cabin = shallower(cabin, CABIN_TOP - point[2], wp.vec3(0.0, 0.0, -1.0))
  if outside != 0:
    cabin = outsideRooms(point, cabin, outside)
  if docked == 0:
    return cabin
  best = cabin
  room = roundRoom(point, HATCH, HATCH_LOW, HATCH_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  room = roundRoom(point, PORT_INSIDE, PORT_LOW, PORT_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  room = roundRoom(point, HUB_INSIDE, HUB_LOW, HUB_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  floor = -outward
  tube = wp.vec3(outward[0] * (across - TUBE_MIDDLE),
                 outward[1] * (across - TUBE_MIDDLE), point[2] - PLANE)
  size = wp.length(tube)
  inward = -outward
  if size > 1.0e-6:
    inward = -tube / size
  room = wp.vec4(inward[0], inward[1], inward[2], TUBE_INSIDE - size)
  room = shallower(room, DECK - across, floor)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  for k in range(ways.shape[0]):
    way = ways[k]
    out = wp.clamp(point[0] * way[0] + point[1] * way[1], SHAFT_FROM,
                   DECK)
    off = point - wp.vec3(out * way[0], out * way[1], PLANE)
    size = wp.length(off)
    inward = floor
    if size > 1.0e-6:
      inward = -off / size
    room = wp.vec4(inward[0], inward[1], inward[2], SHAFT_INSIDE - size)
    room = shallower(room, DECK - across, floor)
    best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  return best


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
           thuds: wp.array(dtype=wp.float32), body: int,
           landing: wp.array(dtype=wp.float32)) -> int:
  """Counts a thud on a meeting begun closing fast ('before': the point
  touched nothing the step before), its loudness by its speed and heft;
  Asger's (body nought) meetings begun keep the fastest in 'landing' (it
  hurts him); returns one (it touches)."""
  if before == 0 and -closing > THUD:
    wp.atomic_add(thuds, 0, 1.0)
    wp.atomic_max(thuds, 1, -closing * wp.min(1.0, wp.sqrt(heft / 20.0)))
  if before == 0 and body == 0:
    wp.atomic_max(landing, 0, -closing)
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
            solidVelocities: wp.array(dtype=wp.vec3),
            ways: wp.array(dtype=wp.vec3),
            touched: wp.array(dtype=wp.int32),
            pushes: wp.array(dtype=wp.vec3),
            twists: wp.array(dtype=wp.vec3),
            asger: wp.array(dtype=wp.vec3),
            thuds: wp.array(dtype=wp.float32),
            landing: wp.array(dtype=wp.float32),
            up: wp.vec3, present: int, legs: int, docked: int,
            outside: int, elapsed: float):
  """Pushes each point (a thread a point) out of what it is in: the
  rooms' walls ('roomGap'; 'docked': the station's rooms too, its shafts
  out along 'ways'; 'outside': the walkway's), the solids (where they
  were at the frame's start, moved on at their velocities 'elapsed' s
  since: an elevator's cage at 30 m/s left still a frame long had him
  0.4 m into its plates), the other bodies' boxes
  (their share pushed back); counts Asger's meetings ('asger' 0: their
  count in x, 1: their normals summed: he touches what is within 'NEAR'
  of him; his legs or the gun at work ('legs'), they hold him, not the
  rubbing), the fastest he met anything ('landing') and the thuds."""
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
  room = roomGap(point, docked, outside, ways)
  depth = radius - room[3]
  if depth > 0.0:
    normal = wp.vec3(room[0], room[1], room[2])
    touching = thudOf(depth, wp.dot(moving, normal), before, heft,
                       thuds, body, landing)
    normals = normals + normal
    if depth > margin:
      push = push + meetingPush(depth - margin, normal, moving, heft, grip)
  for j in range(solidMiddles.shape[0]):
    half = solidHalves[j]
    there = solidMiddles[j] + solidVelocities[j] * elapsed
    if wp.length(point - there) < wp.length(half) + radius:
      met = boxDepth(point, radius, there, solidTurns[j], half)
      if met[3] > 0.0:
        normal = wp.vec3(met[0], met[1], met[2])
        relative = moving - solidVelocities[j]
        touching = thudOf(met[3], wp.dot(relative, normal), before, heft,
                          thuds, body, landing)
        normals = normals + normal
        if met[3] > margin:
          push = push + meetingPush(met[3] - margin, normal, relative,
                                    heft, grip)
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
                            before, shared, thuds, body, landing)
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
          wanted: wp.vec3, leap: wp.vec3,
          up: wp.vec3, walking: int, wanting: int, present: int,
          towTo: wp.vec3, towing: int, sure: int, step: float):
  """Moves each body (a thread a body) a 'step' on: pushed, and feeling
  the vessel's push 'felt' (its own axes: what it feels, thrust, drag
  and the ground; gravity it does not), its turning ('turning', rad/s)
  and its turning faster ('speeding', rad/s²); Asger also by his
  legs ('wanted', 'walking', 'wanting', a 'leap' once) while he touches
  something ('sure': the leap whether or not: a push off a magic bolt),
  or by the gravity gun pulling him to 'towTo' ('towing') instead (his
  meetings kept in 'met' for the host). Its pushes are spent (made
  nought for the next step)."""
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
          - 2.0 * wp.cross(turning, velocity) - wp.cross(speeding, place))
  if b == 0:
    touching = asger[0][0] > 0.0
    met[0] = asger[0]
    met[1] = asger[1]
    asger[0] = wp.vec3(0.0, 0.0, 0.0)
    asger[1] = wp.vec3(0.0, 0.0, 0.0)
    if touching or sure == 1:
      velocity = velocity + leap
    if towing == 1:
      off = towTo - place
      far = wp.length(off)
      wish = wp.vec3(0.0, 0.0, 0.0)
      if far > 1.0e-4:
        wish = off * (wp.min(TOW_SPEED, wp.sqrt(2.0 * TOW_BRAKE * far))
                      / far)
      gun = (wish - velocity) / TOW_TIME
      size = wp.length(gun)
      if size > TOW_MOST:
        gun = gun * (TOW_MOST / size)
      feel = feel + gun
    elif touching:
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
