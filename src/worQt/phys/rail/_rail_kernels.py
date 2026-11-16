"""
The Warp kernel 'railRun' steps wheelsets on a track as 'RailWorld'
does in plain Python ('_stepped', the reference, line for line): each
wheelset found on the track by Newton from where it was, its four rail
points' Hertz pushes and relaxed creep taken to Polach's saturation,
its axleboxes' springs, dampers, Palmgren and brake torques and
traction motors (their pushes on
their frames summed for the trade, box by box), its motion by
semi-implicit Euler, its spin by Euler's equations in its own frame.
One thread a wheelset (user, 2026-11-16: "warp that shit"), a call's
steps in one launch; trading with the small steps on the device
('railTraded'), each thread first reads its own boxes off their frames
there (one launch a trade the fewer: "warp the shit out of it so the
performance doesn't troll us").

float32 (user: "no! fuck64! float32!"), as the spec has it: nothing is
a world coordinate. Each wheelset is stepped in the track's frame where
it stood at the call's start ('RailRun' takes it there and back in
float64): its place from the track's centre line there, its velocity,
spin and turn turned into that frame, gravity too, and the track itself
as a table of its steps within 'WINDOW' m either way, each from its
start there (the first started at the window's edge), so every place
is under a metre or so: float32 holds it to ~0.03 um, against contacts
~15 um deep. A step's frame turns by the exact rotation's series (to
theta 0.25 rad: closed forms of 1 - cos lose float32's digits).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import warp as wp

from . import _wheelset
from ._axlebox import BEARING_EASE, BRAKE_EASE, JOURNAL_AT, MOTOR_LEAST
from ._railworld import A0, B0, C11, C22, CONTACT_DAMPING, EPS_MOST
from ._railworld import LOST, N0, OFF_ACROSS, OFF_UP, Q0, SHEAR

wp.config.quiet = True
wp.set_module_options({'enable_backward': False})


def _single(x: float) -> object:
  """Returns 'x' as a float32 constant of Warp's."""
  return wp.constant(wp.float32(x))


ZERO = _single(0.0)
ONE = _single(1.0)
TWO = _single(2.0)
HALF = _single(0.5)
SERIES_TURN = _single(0.25)
SETTLED = _single(1e-7)
QUIET = _single(1e-9)
STEEP = _single(-1e9)
#  How far either way of a wheelset the track's table reaches, m (a
#  wheelset moves 0.12 m a 4 ms trade at 30 m/s).
WINDOW = 0.5
#  The wheel's profile ('_wheelset.profileAt').
RADIUS = _single(_wheelset.RADIUS)
NOMINAL = _single(_wheelset.NOMINAL)
CONE = _single(_wheelset.CONE)
ROOT = _single(_wheelset.ROOT)
ON_TREAD = _single(_wheelset._ON_TREAD)
ON_FLANGE = _single(_wheelset._ON_FLANGE)
ON_FLANGE_R = _single(_wheelset._ON_FLANGE_R)
CENTRE_E = _single(_wheelset._CENTRE[0])
CENTRE_R = _single(_wheelset._CENTRE[1])
FLANGE_SLOPE = _single(math.tan(_wheelset.FLANGE_ANGLE))
TIP = _single(_wheelset._TIP)
TOP_ACROSS = _single(_wheelset.RAIL_TOP[0])
TOP_UP = _single(_wheelset.RAIL_TOP[1])
CORNER_ACROSS = _single(_wheelset.GAUGE_CORNER[0])
CORNER_UP = _single(_wheelset.GAUGE_CORNER[1])
#  The contact ('_railworld').
REF_LOAD = _single(N0)
REF_A = _single(A0)
REF_B = _single(B0)
REF_DEPTH = _single(Q0)
KALKER_11 = _single(C11)
KALKER_22 = _single(C22)
SHEAR_MODULUS = _single(SHEAR)
DAMPING = _single(CONTACT_DAMPING)
MOST = _single(EPS_MOST)
LOST_DEPTH = _single(LOST)
SHOE_EASE = _single(BRAKE_EASE)
MOTOR_TURNING = _single(MOTOR_LEAST)
OFF_SIDE = _single(OFF_ACROSS)
OFF_HIGH = _single(OFF_UP)
OFF_RAILS = _single(-2.0)
PI = _single(math.pi)
#  The axlebox ('_axlebox').
JOURNAL = _single(JOURNAL_AT)
EASE = _single(BEARING_EASE)
RPM = _single(60.0 / (2.0 * math.pi))
FAST = _single(2000.0)
SLOW_M0 = _single(160e-7)
FAST_M0 = _single(1e-7)
TWO_THIRDS = _single(2.0 / 3.0)
THIRD = _single(1.0 / 3.0)
THREE_HALVES = _single(1.5)
MILLI = _single(1e-3)
#  A wheelset's row in 'wheels' (in the track's frame where it stood):
#  place 0-2, turn 3-6 (w x y z), velocity 7-9, spin 10-12, how far
#  along it has gone 13, its four contacts' slips 14-21 (two each),
#  their loads 22-25, how it went wrong 26 (nought: fine; above nought
#  how deep into a rail past 'LOST'; below: off its table's ends),
#  gravity 27-29, how far back and ahead it may go along 30, 31 (the
#  track's ends or its table's) and where it is off its table 32, 33
#  (its table's ends, or past reach where the track ends first). A row
#  of the track's 'table': its step's start along 0, place 1-3, frame
#  4-12 (row by row), turn rates 13-15. An axlebox's row in 'seen' (its
#  wheelset's frame): its box's place 0-2 and velocity 3-5, its arm 6-8
#  and the arm's swing 9-11, its frame's axes 12-20 (a matrix row by
#  row, its columns the axes), the frame's spin 21-23; in 'fixed': its
#  side 0, stiffness 1-3, damping 4-6, bearing 7-10; in 'results': its
#  push on its frame over the launch (impulse 0-2, twist about the
#  frame's centre 3-5; let go once pushed) and its mean load over each
#  launch, summed over the launches 6. 'held': a wheelset's first box,
#  how many, its first table row, how many.
WHEEL_ROW = 34
TABLE_ROW = 16
SEEN_ROW = 24
FIXED_ROW = 11
RESULT_ROW = 7


@wp.func
def matrixOf(q: wp.vec4):
  """Returns the unit quaternion 'q' (w, x, y, z) as a matrix (its
  columns the axes turned), as '_vectors.matrixOf'."""
  w, x, y, z = q[0], q[1], q[2], q[3]
  return wp.mat33(
    ONE - TWO * (y * y + z * z), TWO * (x * y - w * z),
    TWO * (x * z + w * y),
    TWO * (x * y + w * z), ONE - TWO * (x * x + z * z),
    TWO * (y * z - w * x),
    TWO * (x * z - w * y), TWO * (y * z + w * x),
    ONE - TWO * (x * x + y * y))


@wp.func
def profileAt(e: wp.float32):
  """Returns the wheel's radius 'e' m out from its nominal rolling
  circle and its slope, as '_wheelset.profileAt'."""
  if e >= ON_TREAD:
    return RADIUS - CONE * e, -CONE
  if e >= ON_FLANGE:
    de = e - CENTRE_E
    dr = -wp.sqrt(wp.max(ROOT * ROOT - de * de, ZERO))
    slope = STEEP
    if dr < ZERO:
      slope = -de / dr
    return CENTRE_R + dr, slope
  r = ON_FLANGE_R + FLANGE_SLOPE * (ON_FLANGE - e)
  if r >= TIP:
    return TIP, ZERO
  return r, -FLANGE_SLOPE


@wp.func
def segmentAt(table: wp.array2d(dtype=wp.float32), first: int, count: int,
              s: wp.float32):
  """Returns the last of the table's rows from 'first' ('count' of
  them) starting at or before 's' (its first at least), as
  'bisect_right' less one."""
  low = int(0)
  high = count
  while low < high:
    middle = (low + high) // 2
    if table[first + middle, 0] <= s:
      low = middle + 1
    else:
      high = middle
  return first + wp.max(low - 1, 0)


@wp.func
def segmentFrom(table: wp.array2d(dtype=wp.float32), first: int,
                count: int, s: wp.float32, guess: int):
  """Returns the row 'segmentAt' returns, walked to from row 'guess' (a
  wheelset moves a few millimetres a step: the row it was on, or the
  next; a search's dozen loads from memory each time cost the kernel
  most of its time)."""
  i = wp.min(wp.max(guess, first), first + count - 1)
  last = first + count - 1
  while i < last and table[i + 1, 0] <= s:
    i = i + 1
  while i > first and table[i, 0] > s:
    i = i - 1
  return i


@wp.func
def frameAt(table: wp.array2d(dtype=wp.float32), first: int, count: int,
            s: wp.float32):
  """Returns the track at 's' along: its centre line's place, its frame
  and its turn rates there, as 'RailWorld.frameAt' (its series taken to
  'SERIES_TURN')."""
  return frameOfRow(table, segmentAt(table, first, count, s), s)


@wp.func
def frameOfRow(table: wp.array2d(dtype=wp.float32), i: int,
               s: wp.float32):
  """Returns the track at 's' along from its row 'i', as 'frameAt'."""
  h = s - table[i, 0]
  k = wp.vec3(table[i, 13], table[i, 14], table[i, 15])
  kx, ky, kz = k[0], k[1], k[2]
  w2 = kx * kx + ky * ky + kz * kz
  w = wp.sqrt(w2)
  theta = w * h
  s1 = ZERO
  s2 = ZERO
  s3 = ZERO
  if theta < SERIES_TURN:
    t2 = theta * theta
    s1 = h * (ONE - t2 / wp.float32(6.0) * (ONE - t2 / wp.float32(20.0) * (
      ONE - t2 / wp.float32(42.0))))
    s2 = h * h * (HALF - t2 / wp.float32(24.0) * (ONE - t2 / (
      wp.float32(30.0)) * (ONE - t2 / wp.float32(56.0))))
    s3 = h * h * h * (ONE / wp.float32(6.0) - t2 / wp.float32(120.0) * (
      ONE - t2 / wp.float32(42.0) * (ONE - t2 / wp.float32(72.0))))
  else:
    sine = wp.sin(theta)
    cosine = wp.cos(theta)
    s1 = sine / w
    s2 = (ONE - cosine) / w2
    s3 = (theta - sine) / (w2 * w)
  step = wp.vec3(h + s3 * (kx * kx - w2), s2 * kz + s3 * kx * ky,
                 -s2 * ky + s3 * kx * kz)
  turn = wp.mat33(
    ONE + s2 * (kx * kx - w2), -s1 * kz + s2 * kx * ky,
    s1 * ky + s2 * kx * kz,
    s1 * kz + s2 * kx * ky, ONE + s2 * (ky * ky - w2),
    -s1 * kx + s2 * ky * kz,
    -s1 * ky + s2 * kx * kz, s1 * kx + s2 * ky * kz,
    ONE + s2 * (kz * kz - w2))
  f = wp.mat33(table[i, 4], table[i, 5], table[i, 6], table[i, 7],
               table[i, 8], table[i, 9], table[i, 10], table[i, 11],
               table[i, 12])
  at = wp.vec3(table[i, 1], table[i, 2], table[i, 3])
  return at + f * step, f * turn, k


@wp.func
def alongAt(table: wp.array2d(dtype=wp.float32), first: int, count: int,
            low: wp.float32, high: wp.float32, place: wp.vec3,
            s: wp.float32, guess: int):
  """Returns where along the track 'place' lies, by Newton from 's',
  kept within 'low' and 'high', as 'RailWorld.along', and the table's
  row there (each looked for from the last, 'guess' first)."""
  row = guess
  for _ in range(4):
    row = segmentFrom(table, first, count, s, row)
    at, f, k = frameOfRow(table, row, s)
    d = place - at
    ahead = f[0, 0] * d[0] + f[1, 0] * d[1] + f[2, 0] * d[2]
    left = f[0, 1] * d[0] + f[1, 1] * d[1] + f[2, 1] * d[2]
    up = f[0, 2] * d[0] + f[1, 2] * d[1] + f[2, 2] * d[2]
    slope = -ONE + k[2] * left - k[1] * up
    move = -ahead / slope
    s = wp.min(wp.max(s + move, low), high)
    if wp.abs(move) < SETTLED:
      break
  return s, segmentFrom(table, first, count, s, row)


@wp.func
def contactOf(point: wp.vec3, p: wp.vec3, m: wp.mat33, v: wp.vec3,
              omega: wp.vec3, tangent: wp.vec3, speed: wp.float32,
              slip: wp.vec2, h: wp.float32, friction: wp.float32):
  """Returns the push one rail point puts on the wheelset, its relaxed
  slip after the step, its load and how deep it went (a load of nought:
  not touching, its slip let go), as 'RailWorld._contact'."""
  nothing = wp.vec3(ZERO, ZERO, ZERO)
  free = wp.vec2(ZERO, ZERO)
  d = point - p
  b = wp.transpose(m) * d
  rho = wp.sqrt(b[0] * b[0] + b[1] * b[1])
  r, slope = profileAt(wp.abs(b[2]) - NOMINAL)
  if r - rho <= ZERO or rho <= ZERO:
    return nothing, free, ZERO, ZERO
  size = wp.sqrt(ONE + slope * slope)
  depth = (r - rho) / size
  if depth > LOST_DEPTH:
    return nothing, free, ZERO, depth
  sign = ONE
  if b[2] < ZERO:
    sign = -ONE
  normal = m * wp.vec3(b[0] / rho / size, b[1] / rho / size,
                        -slope * sign / size)
  moving = v + wp.cross(omega, d)
  sinking = wp.dot(moving, normal)
  load = REF_LOAD * wp.pow(depth / REF_DEPTH, THREE_HALVES) + (
    DAMPING * sinking)
  if load <= ZERO:
    return nothing, free, ZERO, depth
  if friction <= ZERO:
    return -load * normal, free, load, depth
  inward = -normal
  along = tangent - wp.dot(tangent, inward) * inward
  t1 = along / wp.length(along)
  t2 = wp.cross(inward, t1)
  w1 = wp.dot(moving, t1)
  w2 = wp.dot(moving, t2)
  grown = wp.pow(load / REF_LOAD, THIRD)
  a = REF_A * grown
  bb = REF_B * grown
  u1 = slip[0]
  u2 = slip[1]
  rate = speed / a
  if rate * h > QUIET:
    fade = wp.exp(-rate * h)
    u1 = w1 / rate + (u1 - w1 / rate) * fade
    u2 = w2 / rate + (u2 - w2 / rate) * fade
  else:
    u1 = u1 + w1 * h
    u2 = u2 + w2 * h
  g1 = KALKER_11 * u1 / a
  g2 = KALKER_22 * u2 / a
  pull = wp.sqrt(g1 * g1 + g2 * g2)
  f1 = ZERO
  f2 = ZERO
  if pull > ZERO:
    epsilon = SHEAR_MODULUS * PI * a * bb * pull / (
      wp.float32(4.0) * load * friction)
    if epsilon > MOST:
      u1 = u1 * MOST / epsilon
      u2 = u2 * MOST / epsilon
      epsilon = MOST
    creep = TWO * load * friction / PI * (
      epsilon / (ONE + epsilon * epsilon) + wp.atan(epsilon))
    f1 = -creep * g1 / pull
    f2 = -creep * g2 / pull
  return -load * normal + f1 * t1 + f2 * t2, wp.vec2(u1, u2), load, depth


@wp.func
def palmgren(spin: wp.float32, load: wp.float32, bearing: wp.vec4):
  """Returns a bearing's friction torque, N m, as '_axlebox.palmgrenOf'
  ('bearing': f0, f1, viscosity mm²/s, mean diameter mm)."""
  rpm = wp.abs(spin) * RPM
  middle = bearing[3]
  m0 = SLOW_M0 * bearing[0] * middle * middle * middle
  if bearing[2] * rpm >= FAST:
    m0 = FAST_M0 * bearing[0] * wp.pow(bearing[2] * rpm, TWO_THIRDS) * (
      middle * middle * middle)
  m1 = bearing[1] * wp.abs(load) * middle
  return MILLI * (m0 + m1) * wp.tanh(spin / EASE)


@wp.func
def motorTorque(spin: wp.float32, drive: wp.float32, power: wp.float32):
  """Returns a traction motor's torque, N m, as '_axlebox.motorOf'."""
  if drive == ZERO:
    return ZERO
  turning = wp.max(wp.abs(spin), MOTOR_TURNING)
  if power > ZERO and wp.abs(drive) * turning > power:
    if drive > ZERO:
      return power / turning
    return -power / turning
  return drive


@wp.func
def vec3At(rows: wp.array2d(dtype=wp.float32), i: int, at: int):
  """Returns three numbers of row 'i' from 'at' as a vector."""
  return wp.vec3(rows[i, at], rows[i, at + 1], rows[i, at + 2])


@wp.func
def rolledOn(i: int, count: int, h: wp.float32, friction: wp.float32,
             mass: wp.float32, moments: wp.vec3,
             table: wp.array2d(dtype=wp.float32),
             wheels: wp.array2d(dtype=wp.float32),
             held: wp.array2d(dtype=int),
             seen: wp.array2d(dtype=wp.float32),
             fixed: wp.array2d(dtype=wp.float32),
             results: wp.array2d(dtype=wp.float32),
             brakes: wp.array(dtype=wp.float32),
             drives: wp.array2d(dtype=wp.float32)):
  """Steps wheelset 'i' (its row of 'wheels', in the track's frame
  where it stood) 'count' steps of 'h' s in place, held in its boxes
  (each one's shoes braking it 'brakes', N m, as the bearing's torque,
  its motor driving it 'drives': its most torque, N m, and power, W),
  their pushes on their frames summed in 'results' box by box; gone
  into a rail past 'LOST' (its depth), off its table (-1) or off the
  rails ('OFF_ACROSS' across, 'OFF_UP' up: 'OFF_RAILS'), it says so in
  its row's lost and stops (and in the call's later trades does not
  start: it is derailed)."""
  if wheels[i, 26] != ZERO:
    return
  p = vec3At(wheels, i, 0)
  q = wp.vec4(wheels[i, 3], wheels[i, 4], wheels[i, 5], wheels[i, 6])
  v = vec3At(wheels, i, 7)
  omega = vec3At(wheels, i, 10)
  s = wheels[i, 13]
  gravity = vec3At(wheels, i, 27)
  low = wheels[i, 30]
  high = wheels[i, 31]
  first = held[i, 2]
  rows = held[i, 3]
  ix = moments[0]
  iy = moments[1]
  iz = moments[2]
  row = segmentAt(table, first, rows, s)
  for step in range(count):
    s, row = alongAt(table, first, rows, low, high, p, s, row)
    if s <= wheels[i, 32] or s >= wheels[i, 33]:
      wheels[i, 26] = -ONE
      return
    at, f, k = frameOfRow(table, row, s)
    off = p - at
    if wp.abs(off[0] * f[0, 1] + off[1] * f[1, 1] + off[2] * f[2, 1]) > (
        OFF_SIDE) or (off[0] * f[0, 2] + off[1] * f[1, 2]
                      + off[2] * f[2, 2] - RADIUS > OFF_HIGH):
      wheels[i, 26] = OFF_RAILS
      return
    m = matrixOf(q)
    axle = wp.vec3(m[0, 2], m[1, 2], m[2, 2])
    leftward = axle[0] * f[0, 1] + axle[1] * f[1, 1] + axle[2] * f[2, 1]
    sign = ONE
    if leftward < ZERO:
      sign = -ONE
    tangent = wp.vec3(f[0, 0], f[1, 0], f[2, 0])
    speed = wp.abs(wp.dot(v, tangent))
    force = mass * gravity
    torque = wp.vec3(ZERO, ZERO, ZERO)
    for half in range(2):
      side = ONE
      if half == 1:
        side = -ONE
      reach = side * sign * NOMINAL
      wheel = p + axle * reach
      ahead = wp.dot(tangent, wheel - at)
      for kind in range(2):
        across = TOP_ACROSS
        up = TOP_UP
        if kind == 1:
          across = CORNER_ACROSS
          up = CORNER_UP
        y = side * across
        point = at + tangent * ahead + (
          wp.vec3(f[0, 1], f[1, 1], f[2, 1]) * y) + (
          wp.vec3(f[0, 2], f[1, 2], f[2, 2]) * up)
        key = half * 2 + kind
        slip = wp.vec2(wheels[i, 14 + 2 * key], wheels[i, 15 + 2 * key])
        pushed, slip, load, depth = contactOf(point, p, m, v, omega,
                                              tangent, speed, slip, h,
                                              friction)
        if depth > LOST_DEPTH:
          wheels[i, 26] = depth
          return
        wheels[i, 14 + 2 * key] = slip[0]
        wheels[i, 15 + 2 * key] = slip[1]
        wheels[i, 22 + key] = load
        force = force + pushed
        torque = torque + wp.cross(point - p, pushed)
    since = wp.float32(step) * h
    for j in range(held[i, 0], held[i, 0] + held[i, 1]):
      reach = fixed[j, 0] * JOURNAL
      a = axle * reach
      moving = vec3At(seen, j, 3)
      out = p + a - vec3At(seen, j, 0) - moving * since
      rate = v + wp.cross(omega, a) - moving
      push = wp.vec3(ZERO, ZERO, ZERO)
      for e in range(3):
        axis = wp.vec3(seen[j, 12 + e], seen[j, 15 + e], seen[j, 18 + e])
        size = -(fixed[j, 1 + e] * wp.dot(axis, out)
                 + fixed[j, 4 + e] * wp.dot(axis, rate))
        push = push + size * axis
      relative = wp.dot(omega - vec3At(seen, j, 21), axle)
      boxed = wp.length(push)
      bearing = wp.vec4(fixed[j, 7], fixed[j, 8], fixed[j, 9], fixed[j, 10])
      lean = ONE
      if (axle[0] * seen[j, 13] + axle[1] * seen[j, 16]
          + axle[2] * seen[j, 19]) < ZERO:
        lean = -ONE
      drag = palmgren(relative, boxed, bearing) + brakes[j] * wp.tanh(
        relative / SHOE_EASE) - lean * motorTorque(
        lean * relative, drives[j, 0], drives[j, 1])
      force = force + push
      torque = torque + wp.cross(a, push) - drag * axle
      lever = vec3At(seen, j, 6) + vec3At(seen, j, 9) * since
      twist = -wp.cross(lever, push) + drag * axle
      for c in range(3):
        results[j, c] = results[j, c] - push[c] * h
        results[j, 3 + c] = results[j, 3 + c] + twist[c] * h
      results[j, 6] = results[j, 6] + boxed / wp.float32(count)
    v = v + force / mass * h
    body = wp.transpose(m) * omega
    pulled = wp.transpose(m) * torque
    wx = body[0]
    wy = body[1]
    wz = body[2]
    wx = wx + (pulled[0] - (iz - iy) * wy * wz) / ix * h
    wy = wy + (pulled[1] - (ix - iz) * wz * wx) / iy * h
    wz = wz + (pulled[2] - (iy - ix) * wx * wy) / iz * h
    omega = m * wp.vec3(wx, wy, wz)
    p = p + v * h
    halved = HALF * h
    dw = -halved * (q[1] * wx + q[2] * wy + q[3] * wz)
    dx = halved * (q[0] * wx + q[2] * wz - q[3] * wy)
    dy = halved * (q[0] * wy + q[3] * wx - q[1] * wz)
    dz = halved * (q[0] * wz + q[1] * wy - q[2] * wx)
    q = wp.vec4(q[0] + dw, q[1] + dx, q[2] + dy, q[3] + dz)
    q = q / wp.length(q)
  for c in range(3):
    wheels[i, c] = p[c]
    wheels[i, 7 + c] = v[c]
    wheels[i, 10 + c] = omega[c]
  for c in range(4):
    wheels[i, 3 + c] = q[c]
  wheels[i, 13] = s


@wp.func
def boxSeen(j: int, w: int, place: wp.array(dtype=wp.vec3),
            shift: wp.array(dtype=wp.vec3),
            turn: wp.array(dtype=wp.quat),
            velocity: wp.array(dtype=wp.vec3),
            spin: wp.array(dtype=wp.vec3),
            boxBody: wp.array(dtype=int),
            boxArm: wp.array(dtype=wp.vec3),
            boxAxes: wp.array(dtype=wp.mat33),
            originHigh: wp.array(dtype=wp.vec3),
            originLow: wp.array(dtype=wp.vec3),
            localAxes: wp.array(dtype=wp.mat33),
            seen: wp.array2d(dtype=wp.float32)):
  """Writes box 'j''s row of 'seen' from its frame as the small steps
  have it on the device (body 'boxBody': its centre a place and a shift
  from their origin, its turn from its principal axes), in its
  wheelset 'w''s frame (that frame's origin from the small steps'
  origin as two float32s, high and low, and its axes): its box's place
  and velocity, its arm ('boxArm', in the frame's principal axes) and
  the arm's swing, the frame's own axes ('boxAxes', in its principal
  axes), the frame's spin."""
  b = boxBody[j]
  r = wp.quat_to_matrix(turn[b])
  back = wp.transpose(localAxes[w])
  centre = (place[b] - originHigh[w]) + (shift[b] - originLow[w])
  arm = r * boxArm[j]
  swing = wp.cross(spin[b], arm)
  at = back * (centre + arm)
  moving = back * (velocity[b] + swing)
  armed = back * arm
  swung = back * swing
  axes = back * (r * boxAxes[j])
  spun = back * spin[b]
  for c in range(3):
    seen[j, c] = at[c]
    seen[j, 3 + c] = moving[c]
    seen[j, 6 + c] = armed[c]
    seen[j, 9 + c] = swung[c]
    seen[j, 21 + c] = spun[c]
    for e in range(3):
      seen[j, 12 + 3 * c + e] = axes[c, e]


@wp.kernel
def railRun(count: int, h: wp.float32, friction: wp.float32,
            mass: wp.float32, moments: wp.vec3,
            table: wp.array2d(dtype=wp.float32),
            wheels: wp.array2d(dtype=wp.float32),
            held: wp.array2d(dtype=int),
            seen: wp.array2d(dtype=wp.float32),
            fixed: wp.array2d(dtype=wp.float32),
            results: wp.array2d(dtype=wp.float32),
            brakes: wp.array(dtype=wp.float32),
            drives: wp.array2d(dtype=wp.float32)):
  """Steps wheelset 'tid' as 'rolledOn' does, its boxes as 'seen' holds
  them (written by the host)."""
  rolledOn(wp.tid(), count, h, friction, mass, moments, table, wheels,
           held, seen, fixed, results, brakes, drives)


@wp.kernel
def railTraded(count: int, h: wp.float32, friction: wp.float32,
               mass: wp.float32, moments: wp.vec3,
               table: wp.array2d(dtype=wp.float32),
               wheels: wp.array2d(dtype=wp.float32),
               held: wp.array2d(dtype=int),
               seen: wp.array2d(dtype=wp.float32),
               fixed: wp.array2d(dtype=wp.float32),
               results: wp.array2d(dtype=wp.float32),
               brakes: wp.array(dtype=wp.float32),
               drives: wp.array2d(dtype=wp.float32),
               place: wp.array(dtype=wp.vec3),
               shift: wp.array(dtype=wp.vec3),
               turn: wp.array(dtype=wp.quat),
               velocity: wp.array(dtype=wp.vec3),
               spin: wp.array(dtype=wp.vec3),
               boxBody: wp.array(dtype=int),
               boxArm: wp.array(dtype=wp.vec3),
               boxAxes: wp.array(dtype=wp.mat33),
               originHigh: wp.array(dtype=wp.vec3),
               originLow: wp.array(dtype=wp.vec3),
               localAxes: wp.array(dtype=wp.mat33)):
  """Steps wheelset 'tid' as 'rolledOn' does (one trade), each of its
  boxes first read off its frame as the small steps have it on the
  device ('boxSeen')."""
  i = wp.tid()
  if wheels[i, 26] != ZERO:
    return
  for j in range(held[i, 0], held[i, 0] + held[i, 1]):
    boxSeen(j, i, place, shift, turn, velocity, spin, boxBody, boxArm,
            boxAxes, originHigh, originLow, localAxes, seen)
  rolledOn(i, count, h, friction, mass, moments, table, wheels, held,
           seen, fixed, results, brakes, drives)


@wp.kernel
def framesPushed(frameBody: wp.array(dtype=int),
                 frameFirst: wp.array(dtype=int),
                 frameCount: wp.array(dtype=int),
                 frameBoxes: wp.array(dtype=int),
                 boxWheel: wp.array(dtype=int),
                 localAxes: wp.array(dtype=wp.mat33),
                 results: wp.array2d(dtype=wp.float32),
                 turn: wp.array(dtype=wp.quat),
                 velocity: wp.array(dtype=wp.vec3),
                 spin: wp.array(dtype=wp.vec3),
                 give: wp.array(dtype=float),
                 turnGive: wp.array(dtype=wp.vec3)):
  """Pushes frame 'tid' (body 'frameBody' of the small steps) by what
  its boxes pushed it with in the trade (each in its wheelset's frame,
  turned into the world's), at once: its velocity by the impulse over
  its mass, its spin by its inertia's inverse times the twist; the
  boxes' pushes then let go (their loads kept)."""
  f = wp.tid()
  b = frameBody[f]
  impulse = wp.vec3(ZERO, ZERO, ZERO)
  twist = wp.vec3(ZERO, ZERO, ZERO)
  for k in range(frameFirst[f], frameFirst[f] + frameCount[f]):
    j = frameBoxes[k]
    a = localAxes[boxWheel[j]]
    impulse = impulse + a * vec3At(results, j, 0)
    twist = twist + a * vec3At(results, j, 3)
    for c in range(6):
      results[j, c] = ZERO
  velocity[b] = velocity[b] + give[b] * impulse
  r = wp.quat_to_matrix(turn[b])
  inside = wp.transpose(r) * twist
  g = turnGive[b]
  spin[b] = spin[b] + r * wp.vec3(inside[0] * g[0], inside[1] * g[1],
                                  inside[2] * g[2])
