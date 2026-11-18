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
from . import _crewman as crew
from . import _stationinterior as rooms
from . import _launchtower as tower
from . import _walkway as walkway

wp.config.log_level = wp.LOG_WARNING
#  No loop unrolled (Asger's box looks round 74 points in loops called
#  from loops: unrolled, the module took over a quarter of an hour to
#  compile for the GPU).
wp.set_module_options({'enable_backward': False, 'max_unroll': 1})


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
FAR_LOW = _single(rooms.FAR_LOW)
FAR_HIGH = _single(rooms.FAR_HIGH)
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
#  connected to a retractable walk way"; '_walkway'; "We *must* have the
#  ability to walk around in the dark before getting in"; '_launchtower'):
#  the hull's skin at the floor (its radius; it narrows as the wall
#  does), the walkway's tunnel, the doorway through the wall; the launch
#  tower's hall, stairwell, lift shaft, the doorways between them and
#  the ground (each a box: its low and high corners); the yard (a box,
#  outside the rocket's body (a round column, 'BODY' radius) and the
#  stair tower's walls (a box)).
HULL_LOW = _single(capsuleRadius(FLOOR))


def _box(box: tuple) -> tuple:
  """Returns 'box' (its low and high corners) as two Warp constants."""
  return wp.constant(wp.vec3(*box[0])), wp.constant(wp.vec3(*box[1]))


TUNNEL_LOW, TUNNEL_HIGH = _box(walkway.TUNNEL)
DOORWAY_LOW, DOORWAY_HIGH = _box(walkway.DOORWAY)
HALL_LOW, HALL_HIGH = _box(tower.HALL)
STAIRS_LOW, STAIRS_HIGH = _box(tower.STAIRWELL)
SHAFT_LOW, SHAFT_HIGH = _box(tower.SHAFT)
STAIR_TOP_LOW, STAIR_TOP_HIGH = _box(tower.STAIR_TOP)
STAIR_FOOT_LOW, STAIR_FOOT_HIGH = _box(tower.STAIR_FOOT)
LIFT_TOP_LOW, LIFT_TOP_HIGH = _box(tower.LIFT_TOP)
LIFT_FOOT_LOW, LIFT_FOOT_HIGH = _box(tower.LIFT_FOOT)
YARD_LOW, YARD_HIGH = _box(tower.YARD)
TOWER_LOW = wp.constant(wp.vec3(tower.TOWER[0][0], tower.TOWER[0][1],
                                tower.GROUND - 1.0))
TOWER_HIGH = wp.constant(wp.vec3(tower.TOWER[1][0], tower.TOWER[1][1],
                                 tower.TOWER_TOP))
BODY = _single(tower.BODY)
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
#  Air in the rooms drags what moves through it (user, 2026-11-18:
#  "PHYSICS MUST BE REAL"; it was a share of the speed a second): half
#  its density times the drag's coefficient and area times the speed
#  squared, against it. The air's density (sea level's: the cabin, the
#  station and the pad all at one atmosphere), kg/m³; a box's drag
#  coefficient (a cube's), its area its mean outline's (a quarter of its
#  surface); Asger's drag coefficient times his outline, m² (a man broad
#  on: 1.0 x 0.8 m²); over his mass: his drag a metre, 1/m. A loose
#  thing's spin the air does not slow (a turning box's drag is some
#  thousandths of its own).
AIR_RHO = 1.2
AIR_DENSITY = _single(AIR_RHO)
BOX_DRAG = _single(1.05)
ASGER_DRAG = _single(0.5 * AIR_RHO * 0.8 / 80.0)
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
def boxOutside(point: wp.vec3, low: wp.vec3, high: wp.vec3) -> wp.vec4:
  """Returns how far 'point' is outside the box from 'low' to 'high'
  (along the axis it is furthest out by) and the way out of it."""
  room = wp.vec4(-1.0, 0.0, 0.0, low[0] - point[0])
  room = deeper(room, point[0] - high[0], wp.vec3(1.0, 0.0, 0.0))
  room = deeper(room, low[1] - point[1], wp.vec3(0.0, -1.0, 0.0))
  room = deeper(room, point[1] - high[1], wp.vec3(0.0, 1.0, 0.0))
  room = deeper(room, low[2] - point[2], wp.vec3(0.0, 0.0, -1.0))
  return deeper(room, point[2] - high[2], wp.vec3(0.0, 0.0, 1.0))


@wp.func
def towerRooms(point: wp.vec3, best: wp.vec4, outside: int) -> wp.vec4:
  """Returns 'best' or the launch tower's rooms if deeper: its hall,
  stairwell and lift shaft, the stairwell's doorways, the lift's open
  ones ('outside' four: the hall's, eight: the ground's), the yard round
  it (outside the rocket's body and the stair tower)."""
  room = boxRoom(point, HALL_LOW, HALL_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  room = boxRoom(point, STAIRS_LOW, STAIRS_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  room = boxRoom(point, SHAFT_LOW, SHAFT_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  room = boxRoom(point, STAIR_TOP_LOW, STAIR_TOP_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  room = boxRoom(point, STAIR_FOOT_LOW, STAIR_FOOT_HIGH)
  best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  if outside % 8 >= 4:
    room = boxRoom(point, LIFT_TOP_LOW, LIFT_TOP_HIGH)
    best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  if outside >= 8:
    room = boxRoom(point, LIFT_FOOT_LOW, LIFT_FOOT_HIGH)
    best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  yard = boxRoom(point, YARD_LOW, YARD_HIGH)
  across = wp.sqrt(point[0] * point[0] + point[1] * point[1])
  outward = wp.vec3(1.0, 0.0, 0.0)
  if across > 1.0e-6:
    outward = wp.vec3(point[0] / across, point[1] / across, 0.0)
  yard = shallower(yard, across - BODY, outward)
  walls = boxOutside(point, TOWER_LOW, TOWER_HIGH)
  yard = shallower(yard, walls[3], wp.vec3(walls[0], walls[1], walls[2]))
  return deeper(best, yard[3], wp.vec3(yard[0], yard[1], yard[2]))


@wp.func
def outsideRooms(point: wp.vec3, best: wp.vec4, outside: int) -> wp.vec4:
  """Returns 'best' or the rooms outside the rocket on the pad if
  deeper: 'outside' one, the walkway's tunnel (outside the hull's skin)
  and the launch tower's rooms ('towerRooms'); two, the doorway."""
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
    best = towerRooms(point, best, outside)
  if outside % 4 >= 2:
    room = boxRoom(point, DOORWAY_LOW, DOORWAY_HIGH)
    best = deeper(best, room[3], wp.vec3(room[0], room[1], room[2]))
  return best


@wp.func
def roomGap(point: wp.vec3, docked: int, outside: int,
            ways: wp.array(dtype=wp.vec3)) -> wp.vec4:
  """Returns how far 'point' is inside the rooms (the cabin; docked
  also the hatch, the ports, the hub, the shafts out along 'ways', the
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
  room = roundRoom(point, PORT_INSIDE, FAR_LOW, FAR_HIGH)
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


#  The most solids near a loose body a frame ('bodiesNear': its points
#  look at those alone; each point reading all four hundred solids each
#  1/1200 s step, most of them the station's empty slots, took 0.15 ms a
#  step: 10-20 ms a frame. More near than this, it reads them all.) And
#  how much further than its own reach and its speed may take it in the
#  frame it looks, m, and as if pulled how hard besides what it feels,
#  m/s² (the frame's turning and pushes).
BODY_NEAR_MOST = 48
BODY_SLACK = _single(1.0)
BODY_PULL = _single(20.0)


@wp.kernel
def bodiesNear(places: wp.array(dtype=wp.vec3),
               velocities: wp.array(dtype=wp.vec3),
               reaches: wp.array(dtype=wp.float32),
               solidMiddles: wp.array(dtype=wp.vec3),
               solidHalves: wp.array(dtype=wp.vec3),
               solidVelocities: wp.array(dtype=wp.vec3),
               near: wp.array2d(dtype=wp.int32),
               nearCount: wp.array(dtype=wp.int32), felt: float,
               seconds: float):
  """Lists the solids each loose body (a thread a body and a solid) may
  meet this frame: within its reach ('reaches': its points' farthest
  from its middle and their round), how far it may go in 'seconds' (its
  speed, and pulled 'felt' and 'BODY_PULL' m/s²) and 'BODY_SLACK', and
  the solid's as far as it moves; at most 'BODY_NEAR_MOST' in its row
  of 'near', how many in 'nearCount' (emptied before)."""
  body, k = wp.tid()
  if body == 0:
    return
  going = (wp.length(velocities[body]) * seconds
           + 0.5 * (felt + BODY_PULL) * seconds * seconds)
  reach = (reaches[body] + going + BODY_SLACK + wp.length(solidHalves[k])
           + wp.length(solidVelocities[k]) * seconds)
  if wp.length(solidMiddles[k] - places[body]) < reach:
    slot = wp.atomic_add(nearCount, body, 1)
    if slot < BODY_NEAR_MOST:
      near[body, slot] = k


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
            bodyNear: wp.array2d(dtype=wp.int32),
            bodyNearCount: wp.array(dtype=wp.int32),
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
  rubbing), the fastest he met anything ('landing') and the thuds. A
  loose body's points look at the solids listed near it this frame
  ('bodiesNear'), all of them if more than it lists."""
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
  listed = int(1)
  total = bodyNearCount[body]
  if body == 0 or total > BODY_NEAR_MOST:
    listed = 0
    total = solidMiddles.shape[0]
  for m in range(total):
    j = m
    if listed == 1:
      j = bodyNear[body, m]
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
          halves: wp.array(dtype=wp.vec3),
          pushes: wp.array(dtype=wp.vec3),
          twists: wp.array(dtype=wp.vec3),
          asger: wp.array(dtype=wp.vec3),
          reaction: wp.array(dtype=wp.vec3),
          felt: wp.vec3, turning: wp.vec3, speeding: wp.vec3,
          gunBody: int, gun: wp.vec3, step: float):
  """Moves each loose body (a thread a body) a 'step' on: pushed, and
  feeling the vessel's push 'felt' (its own axes: what it feels, thrust,
  drag and the ground; gravity it does not), its turning ('turning',
  rad/s) and its turning faster ('speeding', rad/s²); body 'gunBody'
  also by the Grav-Gun ('gun': its force on it over its mass, m/s²,
  '_gravgun'). Body nought is no body (Asger's box is moved by
  'walked'). Its pushes are spent (made nought for the next step).
  What really pushed it (the meetings, the gun, the air; not what the
  vessel's own moving makes it feel) pushes the vessel back as hard
  ('reaction' 2: the push, N s; 3: its twist about the vessel's middle,
  N m s; the vessel's own axes: the walls and the air are the
  vessel's, a push between two loose bodies cancels)."""
  b = wp.tid()
  push = pushes[b]
  twist = twists[b]
  pushes[b] = wp.vec3(0.0, 0.0, 0.0)
  twists[b] = wp.vec3(0.0, 0.0, 0.0)
  if b == 0:
    asger[0] = wp.vec3(0.0, 0.0, 0.0)
    asger[1] = wp.vec3(0.0, 0.0, 0.0)
    return
  heft = masses[b]
  place = places[b]
  velocity = velocities[b]
  feel = (push / heft - felt - wp.cross(turning, wp.cross(turning, place))
          - 2.0 * wp.cross(turning, velocity) - wp.cross(speeding, place))
  half = halves[b]
  outline = 2.0 * (half[0] * half[1] + half[1] * half[2]
                   + half[0] * half[2])
  drag = (0.5 * AIR_DENSITY * BOX_DRAG) * outline * wp.length(velocity)
  real = push - drag * velocity
  if b == gunBody:
    feel = feel + gun
    real = real + gun * heft
  velocity = velocity + (feel - (drag / heft) * velocity) * step
  places[b] = place + velocity * step
  velocities[b] = velocity
  turn = turns[b]
  inertia = inertias[b]
  spin = wp.quat_rotate_inv(turn, spins[b])
  torque = wp.quat_rotate_inv(turn, twist)
  held = wp.cw_mul(inertia, spin)
  spin = spin + wp.cw_div(torque - wp.cross(spin, held), inertia) * step
  spin = wp.quat_rotate(turn, spin)
  spin = spin + (-speeding - wp.cross(turning, spin)) * step
  spins[b] = spin
  wp.atomic_add(reaction, 2, -real * step)
  wp.atomic_add(reaction, 3, -(wp.cross(place, real) + twist) * step)
  turned = turn + wp.quat(spin[0], spin[1], spin[2], 0.0) * turn * (
    0.5 * step)
  turns[b] = wp.normalize(turned)


#  Asger's box (user, 2026-11-17: "Could we just give Asger the minecraft
#  implementation of some blocks or whatever rather than just a few
#  balls?"; "those movements were janky af"; "and make me able to
#  crouch!"; '_crewman'): half its width, its height standing and
#  crouched, its middle over its soles, the most it steps up onto, how
#  far off what it rests on it keeps, m; the most a part of a frame moves
#  it, m; how many times a move is pushed out of what it is in; how many
#  levels up its sides it looks for walls (and three a side round each);
#  a meeting's normal up its 'up' past 'FLOORED' stands on it.
BOX_HALF = _single(crew.WIDE * 0.5)
#  His mass, kg (what his meetings push the vessel back by: 'walked').
ASGER_HEFT = _single(crew.HEFT)
BOX_TALL = _single(crew.TALL)
BOX_LOW = _single(crew.LOW)
BOX_MIDDLE = _single(crew.MIDDLE)
STEP_UP = _single(crew.STEP)
GAP = _single(0.001)
MOVE_MOST = _single(0.08)
ITERATIONS = 5
LEVELS = 9
FLOORED = _single(0.6)
#  How far up is no way out ('upOnto').
BLOCKED = _single(1.0e9)
#  Shoved out of what he met, he moves on as fast as it moved him, no
#  faster than the fastest solid near him by this, m/s ('shovedBy': a
#  solid put where he stood throws him no faster).
SHOVE_MORE = _single(1.0)
#  The most solids near him a frame ('nearby': his box looks at those
#  alone; a GPU thread reading all four hundred each time it looked took
#  18 ms a frame walking).
NEAR_MOST = 64
#  A face's axis is taken over an edge's when the edge's is not shallower
#  by this much, m (an edge's axis grazing a box's side would push him
#  up or aside where its face should).
EDGE_BIAS = _single(0.003)


@wp.func
def boxAxes(up: wp.vec3) -> wp.mat33:
  """Returns his box's axes as columns: across (from a fixed way: the
  vessel's z, or its x when his up is near it), across that, up."""
  ref = wp.vec3(0.0, 0.0, 1.0)
  if wp.abs(up[2]) > 0.9:
    ref = wp.vec3(1.0, 0.0, 0.0)
  a = wp.normalize(ref - wp.dot(ref, up) * up)
  b = wp.cross(up, a)
  return wp.mat33(a[0], b[0], up[0], a[1], b[1], up[1], a[2], b[2], up[2])


@wp.func
def spanOf(axis: wp.vec3, e0: wp.vec3, e1: wp.vec3, e2: wp.vec3,
           half: wp.vec3) -> float:
  """Returns how far a box (its axes 'e0' 'e1' 'e2', 'half' its size)
  reaches either way along 'axis' from its middle."""
  return (half[0] * wp.abs(wp.dot(e0, axis)) + half[1] * wp.abs(wp.dot(
    e1, axis)) + half[2] * wp.abs(wp.dot(e2, axis)))


@wp.func
def axisTried(best: wp.vec4, axis: wp.vec3, apart: wp.vec3, a0: wp.vec3,
              a1: wp.vec3, a2: wp.vec3, ha: wp.vec3, b0: wp.vec3,
              b1: wp.vec3, b2: wp.vec3, hb: wp.vec3,
              bias: float) -> wp.vec4:
  """Returns 'best' or the two boxes' overlap along 'axis' if shallower
  ('bias' added in the weighing): the way out (from box b toward box a)
  and how deep (below nought: apart)."""
  along = wp.dot(apart, axis)
  overlap = (spanOf(axis, a0, a1, a2, ha) + spanOf(axis, b0, b1, b2, hb)
             - wp.abs(along))
  if overlap + bias < best[3]:
    side = float(1.0)
    if along < 0.0:
      side = -1.0
    return wp.vec4(side * axis[0], side * axis[1], side * axis[2], overlap)
  return best


@wp.func
def edgeTried(best: wp.vec4, one: wp.vec3, two: wp.vec3, apart: wp.vec3,
              a0: wp.vec3, a1: wp.vec3, a2: wp.vec3, ha: wp.vec3,
              b0: wp.vec3, b1: wp.vec3, b2: wp.vec3,
              hb: wp.vec3) -> wp.vec4:
  """Returns 'best' or the overlap across edges 'one' and 'two' (their
  cross) if shallower by more than 'EDGE_BIAS'."""
  axis = wp.cross(one, two)
  size = wp.length(axis)
  if size < 1.0e-4:
    return best
  return axisTried(best, axis / size, apart, a0, a1, a2, ha, b0, b1, b2, hb,
                   EDGE_BIAS)


@wp.func
def boxApart(ca: wp.vec3, axes: wp.mat33, ha: wp.vec3, cb: wp.vec3,
             turn: wp.quat, hb: wp.vec3) -> wp.vec4:
  """Returns how deep box a ('ca', its 'axes' as columns, 'ha') is in box
  b ('cb', 'turn', 'hb') and the way out of it (separating axes: the
  shallowest overlap of the fifteen; below nought: apart at least so
  far)."""
  a0 = wp.vec3(axes[0, 0], axes[1, 0], axes[2, 0])
  a1 = wp.vec3(axes[0, 1], axes[1, 1], axes[2, 1])
  a2 = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  b0 = wp.quat_rotate(turn, wp.vec3(1.0, 0.0, 0.0))
  b1 = wp.quat_rotate(turn, wp.vec3(0.0, 1.0, 0.0))
  b2 = wp.quat_rotate(turn, wp.vec3(0.0, 0.0, 1.0))
  apart = ca - cb
  best = wp.vec4(0.0, 0.0, 1.0, 1.0e9)
  best = axisTried(best, a0, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, a1, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, a2, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = axisTried(best, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, 0.0)
  best = edgeTried(best, a0, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a0, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a0, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a1, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a1, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a1, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a2, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a2, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  best = edgeTried(best, a2, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb)
  return best


@wp.func
def liftTried(least: float, axis: wp.vec3, apart: wp.vec3, a0: wp.vec3,
              a1: wp.vec3, a2: wp.vec3, ha: wp.vec3, b0: wp.vec3,
              b1: wp.vec3, b2: wp.vec3, hb: wp.vec3,
              up: wp.vec3) -> float:
  """Returns 'least' or how far box a must go along 'up' to come apart
  from box b along 'axis' if less (nought: apart along it already)."""
  along = wp.dot(apart, axis)
  overlap = (spanOf(axis, a0, a1, a2, ha) + spanOf(axis, b0, b1, b2, hb)
             - wp.abs(along))
  if overlap <= 0.0:
    return 0.0
  side = float(1.0)
  if along < 0.0:
    side = -1.0
  going = side * wp.dot(up, axis)
  if going > 1.0e-4:
    return wp.min(least, overlap / going)
  return least


@wp.func
def liftEdge(least: float, one: wp.vec3, two: wp.vec3, apart: wp.vec3,
             a0: wp.vec3, a1: wp.vec3, a2: wp.vec3, ha: wp.vec3,
             b0: wp.vec3, b1: wp.vec3, b2: wp.vec3, hb: wp.vec3,
             up: wp.vec3) -> float:
  """Returns 'least' or the lift across edges 'one' and 'two'."""
  axis = wp.cross(one, two)
  size = wp.length(axis)
  if size < 1.0e-4:
    return least
  return liftTried(least, axis / size, apart, a0, a1, a2, ha, b0, b1, b2,
                   hb, up)


@wp.func
def liftApart(ca: wp.vec3, axes: wp.mat33, ha: wp.vec3, cb: wp.vec3,
              turn: wp.quat, hb: wp.vec3) -> float:
  """Returns how far box a ('ca', its 'axes' as columns, its up the
  third; 'ha') must go up to be clear of box b ('cb', 'turn', 'hb'):
  the least along any of the separating axes ('BLOCKED': going up never
  parts them)."""
  a0 = wp.vec3(axes[0, 0], axes[1, 0], axes[2, 0])
  a1 = wp.vec3(axes[0, 1], axes[1, 1], axes[2, 1])
  a2 = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  b0 = wp.quat_rotate(turn, wp.vec3(1.0, 0.0, 0.0))
  b1 = wp.quat_rotate(turn, wp.vec3(0.0, 1.0, 0.0))
  b2 = wp.quat_rotate(turn, wp.vec3(0.0, 0.0, 1.0))
  apart = ca - cb
  least = BLOCKED
  least = liftTried(least, a0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, a1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, a2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftTried(least, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a0, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a0, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a0, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a1, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a1, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a1, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a2, b0, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a2, b1, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  least = liftEdge(least, a2, b2, apart, a0, a1, a2, ha, b0, b1, b2, hb, a2)
  return least


@wp.func
def samplePoint(soles: wp.vec3, axes: wp.mat33, high: float, level: int,
                i: int, j: int) -> wp.vec3:
  """Returns where one of the points looked at round his box is: on
  'level' up it (of 'LEVELS'), 'i' and 'j' across (each of -1, 0, 1)."""
  a = wp.vec3(axes[0, 0], axes[1, 0], axes[2, 0])
  b = wp.vec3(axes[0, 1], axes[1, 1], axes[2, 1])
  up = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  h = high * float(level) / float(LEVELS - 1)
  return (soles + h * up + BOX_HALF * float(i) * a
          + BOX_HALF * float(j) * b)


@wp.func
def sampled(level: int, i: int, j: int) -> int:
  """Returns whether that point is looked at: round the sides on every
  level, the middles of the foot and the top too."""
  if i == 0 and j == 0 and level > 0 and level < LEVELS - 1:
    return 0
  return 1


@wp.func
def deepestIn(soles: wp.vec3, axes: wp.mat33, high: float, t: float,
              own: int, docked: int, outside: int,
              ways: wp.array(dtype=wp.vec3),
              solidMiddles: wp.array(dtype=wp.vec3),
              solidTurns: wp.array(dtype=wp.quat),
              solidHalves: wp.array(dtype=wp.vec3),
              solidVelocities: wp.array(dtype=wp.vec3),
              near: wp.array(dtype=wp.int32), count: int) -> wp.vec4:
  """Returns how deep his box (its soles at 'soles', 'high') is in what
  it meets at 't' s into the frame (the rooms' walls at its points, the
  solids, but his own, 'own') at the deepest, and the way out of it
  (depth below nought: in nothing)."""
  best = wp.vec4(0.0, 0.0, 1.0, -1.0e9)
  for level in range(LEVELS):
    for i in range(-1, 2):
      for j in range(-1, 2):
        if sampled(level, i, j) == 1:
          room = roomGap(samplePoint(soles, axes, high, level, i, j), docked,
                         outside, ways)
          if -room[3] > best[3]:
            best = wp.vec4(room[0], room[1], room[2], -room[3])
  up = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  middle = soles + 0.5 * high * up
  half = wp.vec3(BOX_HALF, BOX_HALF, 0.5 * high)
  for m in range(count):
    k = near[m]
    there = solidMiddles[k] + solidVelocities[k] * t
    reach = wp.length(solidHalves[k]) + wp.length(half)
    if wp.length(middle - there) < reach:
      met = boxApart(middle, axes, half, there, solidTurns[k],
                     solidHalves[k])
      if met[3] > best[3]:
        best = met
  return best


@wp.func
def pushedOut(soles: wp.vec3, axes: wp.mat33, high: float, t: float,
              own: int, docked: int, outside: int,
              ways: wp.array(dtype=wp.vec3),
              solidMiddles: wp.array(dtype=wp.vec3),
              solidTurns: wp.array(dtype=wp.quat),
              solidHalves: wp.array(dtype=wp.vec3),
              solidVelocities: wp.array(dtype=wp.vec3),
              near: wp.array(dtype=wp.int32), count: int) -> wp.vec3:
  """Returns his box's soles pushed out of what it is in, the deepest
  first, 'ITERATIONS' times at most, each a 'GAP' clear of it."""
  out = soles
  free = int(0)
  for _ in range(ITERATIONS):
    if free == 0:
      met = deepestIn(out, axes, high, t, own, docked, outside, ways,
                      solidMiddles, solidTurns, solidHalves,
                      solidVelocities, near, count)
      if met[3] > 0.0:
        out = out + wp.vec3(met[0], met[1], met[2]) * (met[3] + GAP)
      else:
        free = int(1)
  return out


@wp.func
def shovedBy(v: wp.vec3, shove: wp.vec3, dt: float,
             fastest: float) -> wp.vec3:
  """Returns his velocity 'v' after what he met shoved his box 'shove'
  (m) out of it in a part of 'dt' s (how hard they met is had from his
  velocity before the part's meetings, 'walked'): along the shove he
  moves as much faster as it moved him (a still wall stops him going
  into it; a moving one, an elevator's cage, carries him at its speed:
  the user's let's play, 2026-11-18, the cage moved him and kept its
  speed, its roof and floor met him at 25 m/s), at most 'fastest' and
  'SHOVE_MORE' that way."""
  size = wp.length(shove)
  if size < 1.0e-6 or dt <= 0.0:
    return v
  way = shove / size
  along = wp.dot(v, way)
  after = wp.min(along + size / dt, wp.max(along, fastest + SHOVE_MORE))
  return v + (after - along) * way


@wp.func
def upOnto(soles: wp.vec3, axes: wp.mat33, high: float, t: float, own: int,
           docked: int, outside: int, ways: wp.array(dtype=wp.vec3),
           solidMiddles: wp.array(dtype=wp.vec3),
           solidTurns: wp.array(dtype=wp.quat),
           solidHalves: wp.array(dtype=wp.vec3),
           solidVelocities: wp.array(dtype=wp.vec3),
           near: wp.array(dtype=wp.int32), count: int) -> float:
  """Returns how far up his box (its soles at 'soles') must go to stand
  clear on what it is in (nought: in nothing); 'BLOCKED' when that is
  no way out: a wall, or what is higher than 'STEP_UP' over its soles
  (lowered onto a step, it is set on the step's top, never pushed off
  its edge)."""
  up = wp.vec3(axes[0, 2], axes[1, 2], axes[2, 2])
  need = float(0.0)
  for level in range(LEVELS):
    for i in range(-1, 2):
      for j in range(-1, 2):
        if sampled(level, i, j) == 1:
          room = roomGap(samplePoint(soles, axes, high, level, i, j), docked,
                         outside, ways)
          if room[3] < 0.0:
            lean = wp.dot(wp.vec3(room[0], room[1], room[2]), up)
            if lean > 0.3:
              need = wp.max(need, -room[3] / lean)
            else:
              need = BLOCKED
  middle = soles + 0.5 * high * up
  half = wp.vec3(BOX_HALF, BOX_HALF, 0.5 * high)
  for m in range(count):
    k = near[m]
    there = solidMiddles[k] + solidVelocities[k] * t
    reach = wp.length(solidHalves[k]) + wp.length(half)
    if wp.length(middle - there) < reach:
      lift = liftApart(middle, axes, half, there, solidTurns[k],
                       solidHalves[k])
      if lift > STEP_UP + 0.01:
        need = BLOCKED
      else:
        need = wp.max(need, lift)
  return need


@wp.kernel
def nearby(solidMiddles: wp.array(dtype=wp.vec3),
           solidHalves: wp.array(dtype=wp.vec3),
           solidVelocities: wp.array(dtype=wp.vec3),
           place: wp.array(dtype=wp.vec3),
           near: wp.array(dtype=wp.int32),
           nearCount: wp.array(dtype=wp.int32), up: wp.vec3,
           margin: float, own: int, seconds: float):
  """Lists the solids (a thread a solid) his box may meet this frame
  ('place': his soles; 'margin': how far he may go in it, m; the solid
  as far as it moves in 'seconds'): at most 'NEAR_MOST', in 'near', how
  many in 'nearCount' ('walked' looks at those alone, and empties it)."""
  k = wp.tid()
  if k == own:
    return
  middle = place[0] + 0.5 * BOX_TALL * wp.normalize(up)
  reach = (wp.length(solidHalves[k]) + 0.5 * BOX_TALL + 2.0 * BOX_HALF
           + margin + wp.length(solidVelocities[k]) * seconds)
  if wp.length(solidMiddles[k] - middle) < reach:
    slot = wp.atomic_add(nearCount, 0, 1)
    if slot < NEAR_MOST:
      near[slot] = k


@wp.kernel
def walked(place: wp.array(dtype=wp.vec3),
           velocity: wp.array(dtype=wp.vec3),
           ground: wp.array(dtype=wp.vec3),
           contact: wp.array(dtype=wp.vec3),
           met: wp.array(dtype=wp.vec3),
           thuds: wp.array(dtype=wp.float32),
           solidMiddles: wp.array(dtype=wp.vec3),
           solidTurns: wp.array(dtype=wp.quat),
           solidHalves: wp.array(dtype=wp.vec3),
           solidVelocities: wp.array(dtype=wp.vec3),
           ways: wp.array(dtype=wp.vec3),
           near: wp.array(dtype=wp.int32),
           nearCount: wp.array(dtype=wp.int32),
           reaction: wp.array(dtype=wp.vec3),
           felt: wp.vec3, turning: wp.vec3, speeding: wp.vec3,
           wanted: wp.vec3, leap: wp.vec3, up: wp.vec3, walking: int,
           wanting: int, gun: wp.vec3, jet: wp.vec3, crouch: int,
           docked: int, outside: int, own: int, seconds: float):
  """Moves Asger's box a frame ('seconds' s) on, one thread: what is
  felt there moves it (as a loose thing: 'felt', 'turning', 'speeding'),
  his legs while he touches something ('wanted', 'walking', 'wanting',
  a 'leap' once: as against what he stands on, 'ground' its velocity,
  kept from frame to frame: the user's let's play, 2026-11-18, standing
  on the side of an elevator's cage running 30 m/s out his legs held him
  still to the station, the cage's roof and floor beat him to death),
  the Grav-Gun's field or pulse ('gun': its force on him
  over his mass, m/s², '_gravgun'), his jetpack ('jet': likewise,
  '_jetpack'); in parts of the frame no longer than
  'MOVE_MOST',
  first along his up, then across, each pushed out of what it meets
  ('pushedOut'): what it meets stops it and it slides along (Minecraft's
  way, his box upright along 'up'); walking, it steps up onto what is
  no higher than 'STEP_UP' and keeps to the ground going down (a ledge
  deeper than that: he falls; crouched ('crouch'), he stops at it). It
  stands up again only with room overhead. Its place, velocity, what it
  touches ('contact': touching, standing on something, crouched; 'met'
  0: how many meetings, how far it stepped up, the fastest it met
  anything; 1: their normals summed; 2: those it stands on's) back for
  the host ('place': his soles, not his middle: his up turning, he turns
  about his feet); the thuds; its
  box into the solids' slot 'own' (moving as it does through the frame)
  for the loose things. Whatever really changed his speed (his legs on
  what he stands on, the leap, what he met, the gun, the jetpack's and
  the air's pushes: all but what the vessel's own moving makes him
  feel) pushes the vessel back as hard ('reaction' 0: the push, N s; 1:
  its twist about the vessel's middle, N m s, his mass at his middle;
  the vessel's own axes): the walls, the bolts and the air are the
  vessel's."""
  v = velocity[0]
  under = ground[0]
  up = wp.normalize(up)
  axes = boxAxes(up)
  soles = place[0]
  known = wp.min(nearCount[0], NEAR_MOST)
  nearCount[0] = 0
  touching = int(0)
  pressing = int(0)
  grounded = int(0)
  crouched = int(0)
  if contact[0][0] > 0.5:
    touching = int(1)
  if contact[0][0] > 1.5:
    pressing = int(1)
  if contact[0][1] > 0.5:
    grounded = int(1)
  if contact[0][2] > 0.5:
    crouched = int(1)
  if crouch == 1:
    crouched = int(1)
  elif crouched == 1:
    standing = deepestIn(soles, axes, BOX_TALL, 0.0, own, docked, outside,
                         ways, solidMiddles, solidTurns, solidHalves,
                         solidVelocities, near, known)
    if standing[3] <= 0.0:
      crouched = int(0)
  high = BOX_TALL
  if crouched == 1:
    high = BOX_LOW
  start = soles + 0.5 * high * up
  half = wp.vec3(BOX_HALF, BOX_HALF, 0.5 * high)
  solidMiddles[own] = start
  solidTurns[own] = wp.quat_from_matrix(axes)
  solidHalves[own] = half
  fastest = float(0.0)
  for m in range(known):
    if near[m] != own:
      fastest = wp.max(fastest, wp.length(solidVelocities[near[m]]))
  count = int(wp.ceil(seconds * (wp.length(v) + 2.0) / MOVE_MOST))
  count = wp.clamp(count, 1, 24)
  dt = seconds / float(count)
  rose = float(0.0)
  landing = float(0.0)
  hardest = float(0.0)
  normals = wp.vec3(0.0, 0.0, 0.0)
  floors = wp.vec3(0.0, 0.0, 0.0)
  meetings = int(0)
  pushedBack = wp.vec3(0.0, 0.0, 0.0)
  twistedBack = wp.vec3(0.0, 0.0, 0.0)
  for k in range(count):
    t = float(k + 1) * dt
    body = soles + BOX_MIDDLE * up
    feel = (-felt - wp.cross(turning, wp.cross(turning, body))
            - 2.0 * wp.cross(turning, v) - wp.cross(speeding, body))
    framed = feel
    began = v
    if k == 0 and touching == 1:
      v = v + leap
    feel = feel + gun + jet
    if touching == 1:
      rel = v - under
      legs = (wanted - rel) / LEGS_TIME
      if walking == 1:
        along = rel - wp.dot(rel, up) * up
        legs = (wanted - along) / LEGS_TIME
      size = wp.length(legs)
      if size > LEGS_MOST:
        legs = legs * (LEGS_MOST / size)
      if walking == 1 or wanting == 1:
        feel = feel + legs
    v = v + (feel - ASGER_DRAG * wp.length(v) * v) * dt
    meeting = v
    move = v * dt
    rise = wp.dot(move, up) * up
    across = move - rise
    p = soles + rise
    settled = int(0)
    if wp.dot(rise, up) < 0.0:
      onto = upOnto(p, axes, high, t, own, docked, outside, ways,
                    solidMiddles, solidTurns, solidHalves, solidVelocities,
                    near, known)
      if onto < BLOCKED:
        settled = int(1)
        if onto > 0.0:
          p = p + (onto + GAP) * up
          v = shovedBy(v, (onto + GAP) * up, dt, fastest)
    if settled == 0:
      aimed = p
      p = pushedOut(p, axes, high, t, own, docked, outside, ways,
                    solidMiddles, solidTurns, solidHalves, solidVelocities,
                    near, known)
      v = shovedBy(v, p - aimed, dt, fastest)
    before = p
    p = pushedOut(before + across, axes, high, t, own, docked, outside,
                  ways, solidMiddles, solidTurns, solidHalves,
                  solidVelocities, near, known)
    shoved = p - (before + across)
    climbedNow = int(0)
    wide = wp.length(across)
    onFoot = int(0)
    if grounded == 1 and walking == 1 and wp.dot(v, up) < 0.5:
      onFoot = int(1)
    if onFoot == 1 and wide > 1.0e-6:
      way = across / wide
      gone = wp.dot(p - before, way)
      if gone < 0.95 * wide - 1.0e-4:
        raised = pushedOut(before + STEP_UP * up, axes, high, t, own,
                           docked, outside, ways, solidMiddles, solidTurns,
                           solidHalves, solidVelocities, near, known)
        lift = wp.dot(raised - before, up)
        ahead = pushedOut(raised + across, axes, high, t, own, docked,
                          outside, ways, solidMiddles, solidTurns,
                          solidHalves, solidVelocities, near, known)
        lowered = ahead - (lift + 0.002) * up
        onto = upOnto(lowered, axes, high, t, own, docked, outside, ways,
                      solidMiddles, solidTurns, solidHalves,
                      solidVelocities, near, known)
        if onto < BLOCKED:
          down = lowered + (onto + GAP) * up
          climbed = wp.dot(down - before, up)
          if wp.dot(down - before, way) > gone + 0.002 and climbed > 0.002:
            p = down
            rose = rose + climbed
            climbedNow = int(1)
    if climbedNow == 0:
      v = shovedBy(v, shoved, dt, fastest)
    if onFoot == 1:
      dropped = p - STEP_UP * up
      onto = upOnto(dropped, axes, high, t, own, docked, outside, ways,
                    solidMiddles, solidTurns, solidHalves, solidVelocities,
                    near, known)
      if onto < BLOCKED and onto > 0.003:
        p = dropped + (onto + GAP) * up
      elif onto <= 0.003 and crouched == 1:
        p = before
        v = wp.dot(v, up) * up
    soles = p
    was = pressing
    touching = int(0)
    pressing = int(0)
    grounded = int(0)
    closing = float(0.0)
    floorMost = float(-2.0)
    beneath = wp.vec3(0.0, 0.0, 0.0)
    for level in range(LEVELS):
      for i in range(-1, 2):
        for j in range(-1, 2):
          if sampled(level, i, j) == 1:
            room = roomGap(samplePoint(soles, axes, high, level, i, j),
                           docked, outside, ways)
            if room[3] < NEAR:
              normal = wp.vec3(room[0], room[1], room[2])
              touching = int(1)
              meetings = meetings + 1
              normals = normals + normal
              if wp.dot(normal, up) > floorMost:
                floorMost = wp.dot(normal, up)
                beneath = wp.vec3(0.0, 0.0, 0.0)
              if wp.dot(normal, up) > FLOORED:
                grounded = int(1)
                floors = floors + normal
              into = wp.dot(v, normal)
              if room[3] < 0.004:
                pressing = int(1)
                closing = wp.max(closing, -wp.dot(meeting, normal))
                if into < 0.0:
                  v = v - into * normal
    middle = soles + 0.5 * high * up
    for m in range(known):
      n = near[m]
      if n != own:
        there = solidMiddles[n] + solidVelocities[n] * t
        reach = wp.length(solidHalves[n]) + wp.length(half) + NEAR
        if wp.length(middle - there) < reach:
          box = boxApart(middle, axes, half, there, solidTurns[n],
                         solidHalves[n])
          if box[3] > -NEAR:
            normal = wp.vec3(box[0], box[1], box[2])
            touching = int(1)
            meetings = meetings + 1
            normals = normals + normal
            if wp.dot(normal, up) > floorMost:
              floorMost = wp.dot(normal, up)
              beneath = solidVelocities[n]
            if wp.dot(normal, up) > FLOORED:
              grounded = int(1)
              floors = floors + normal
            into = wp.dot(v - solidVelocities[n], normal)
            turn = solidTurns[n]
            hb = solidHalves[n]
            top = wp.dot(there - soles, up) + spanOf(up, wp.quat_rotate(
              turn, wp.vec3(1.0, 0.0, 0.0)), wp.quat_rotate(turn, wp.vec3(
                0.0, 1.0, 0.0)), wp.quat_rotate(turn, wp.vec3(0.0, 0.0,
                                                              1.0)), hb)
            foot = top - 2.0 * spanOf(up, wp.quat_rotate(turn, wp.vec3(
              1.0, 0.0, 0.0)), wp.quat_rotate(turn, wp.vec3(0.0, 1.0, 0.0)),
                                      wp.quat_rotate(turn, wp.vec3(
                                        0.0, 0.0, 1.0)), hb)
            step = int(0)
            if (onFoot == 1 and wp.abs(wp.dot(normal, up)) < 0.3
                and top > 0.005 and top <= STEP_UP + 0.01
                and foot < 0.005):
              step = int(1)
            if box[3] > -0.004 and step == 0:
              pressing = int(1)
              closing = wp.max(closing, -wp.dot(
                meeting - solidVelocities[n], normal))
              if into < 0.0:
                v = v - into * normal
    if touching == 1:
      under = beneath
    if was == 0:
      hardest = wp.max(hardest, closing)
      landing = wp.max(landing, closing)
    really = ASGER_HEFT * ((v - began) - framed * dt)
    pushedBack = pushedBack - really
    twistedBack = twistedBack - wp.cross(body, really)
  wp.atomic_add(reaction, 0, pushedBack)
  wp.atomic_add(reaction, 1, twistedBack)
  if hardest > THUD:
    wp.atomic_add(thuds, 0, 1.0)
    wp.atomic_max(thuds, 1, hardest)
  place[0] = soles
  velocity[0] = v
  ground[0] = under
  solidVelocities[own] = (soles + 0.5 * high * up - start) / seconds
  stood = float(0.0)
  if grounded == 1:
    stood = 1.0
  touched = float(0.0)
  if pressing == 1:
    touched = 2.0
  elif touching == 1:
    touched = 1.0
  low = float(0.0)
  if crouched == 1:
    low = 1.0
  contact[0] = wp.vec3(touched, stood, low)
  met[0] = wp.vec3(float(meetings), rose, landing)
  met[1] = normals
  met[2] = floors
