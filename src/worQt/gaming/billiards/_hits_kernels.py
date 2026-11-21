"""
The Warp kernel 'Hits' steps the balls through their hits with: the
balls touching a cushion or each other, pushed by the cushions' springs
and each other's, with friction, on the slate, step by step, as
'Hits.run' does in plain Python, compiled: one thread, many steps a
launch. Balls touching nothing are left to Python, which moves them
exactly ('Cloth'); the kernel hands back as soon as one is free. Its
pieces are functions, the pushes of one ball or pair a step, shared
with keglebillard's kernel ('_kegle_kernels.kegleRun').

Units are mm, s and g; float64 throughout, every number named, as Warp
keeps float64 and float32 apart. A ball's turn is a quaternion, scalar
first, as 'Ball.turn' has it.
"""
from __future__ import annotations

import warp as wp

wp.config.log_level = wp.LOG_WARNING
wp.set_module_options({'enable_backward': False})

ZERO = wp.constant(wp.float64(0.0))
ONE = wp.constant(wp.float64(1.0))
HALF = wp.constant(wp.float64(0.5))
TWO = wp.constant(wp.float64(2.0))
TOUCH = wp.constant(wp.float64(1e-6))  # mm: nearer than this touches
ROLL = wp.constant(wp.float64(3.5))  # 1 + R²/I, a share
PAIR = wp.constant(wp.float64(7.0))  # both balls' 3.5
TINY = wp.constant(wp.float64(1e-15))


@wp.struct
class HitRules:
  """What the steps through hits use, as 'Motion._Fixed' has it."""
  radius: wp.float64
  drop: wp.float64
  inertia: wp.float64
  stiffness: wp.float64
  damping: wp.float64
  stiffening: wp.float64
  grip: wp.float64
  across: wp.float64
  down: wp.float64
  storing: wp.float64
  storingShare: wp.float64
  squaring: wp.float64
  squaringFrom: wp.float64
  squaringOnset: wp.float64
  squaringBelow: wp.float64
  squaringWidth: wp.float64
  squaringNorm: wp.float64
  swingSquared: wp.float64
  swingDamping: wp.float64
  fastFriction: wp.float64
  frictionSpread: wp.float64
  slipScale: wp.float64
  sliding: wp.float64
  gravity: wp.float64
  spinDecay: wp.float64
  cushionStep: wp.float64
  caromStep: wp.float64
  settleSpeed: wp.float64
  width: wp.float64
  length: wp.float64


@wp.func
def _away(rules: HitRules, x: wp.float64, y: wp.float64,
          side: int) -> wp.vec3d:
  """How far a ball's middle at 'x', 'y' is from cushion 'side' (left,
  right, foot, head), and the way into the table."""
  if side == 0:
    return wp.vec3d(x, ONE, ZERO)
  if side == 1:
    return wp.vec3d(rules.width - x, -ONE, ZERO)
  if side == 2:
    return wp.vec3d(y, ZERO, ONE)
  return wp.vec3d(rules.length - y, ZERO, -ONE)


@wp.func
def turned(turn: wp.vec4d, ax: wp.float64, ay: wp.float64,
            az: wp.float64) -> wp.vec4d:
  """'turn', scalar first, turned on by the angle 'ax', 'ay', 'az'."""
  angle = wp.sqrt(ax * ax + ay * ay + az * az)
  if angle < TINY:
    return turn
  half = HALF * angle
  share = wp.sin(half) / angle
  qw = wp.cos(half)
  qx = ax * share
  qy = ay * share
  qz = az * share
  w = turn[0]
  x = turn[1]
  y = turn[2]
  z = turn[3]
  nw = qw * w - qx * x - qy * y - qz * z
  nx = qw * x + qx * w + qy * z - qz * y
  ny = qw * y - qx * z + qy * w + qz * x
  nz = qw * z + qx * y - qy * x + qz * w
  size = wp.sqrt(nw * nw + nx * nx + ny * ny + nz * nz)
  return wp.vec4d(nw / size, nx / size, ny / size, nz / size)


@wp.func
def contactsOf(rules: HitRules, place: wp.array(dtype=wp.vec2d),
               speed: wp.array(dtype=wp.vec2d), k: int) -> int:
  """Ball 'k's contacts now, as '_touchesAmong' finds them: its four
  cushions as bits, then a bit, 4 on, each ball it meets."""
  count = place.shape[0]
  x = place[k][0]
  y = place[k][1]
  vx = speed[k][0]
  vy = speed[k][1]
  bits = int(0)
  for side in range(4):
    sided = _away(rules, x, y, side)
    away = sided[0]
    if away >= rules.radius + TOUCH:
      continue
    given = rules.radius - wp.sqrt(away * away + rules.drop * rules.drop)
    if given > ZERO or (given > -TOUCH and
                        sided[1] * vx + sided[2] * vy < ZERO):
      bits = bits | (1 << side)
  for j in range(count):
    if j == k:
      continue
    dx = place[j][0] - x
    dy = place[j][1] - y
    pressed = TWO * rules.radius - wp.sqrt(dx * dx + dy * dy)
    if pressed <= -TOUCH:
      continue
    if pressed > ZERO or dx * (speed[j][0] - vx) + \
        dy * (speed[j][1] - vy) < ZERO:
      bits = bits | (1 << (4 + j))
  return bits


@wp.func
def loggedOf(events: wp.array(dtype=wp.vec4i), logged: int, steps: int,
             k: int, fresh: int, count: int) -> int:
  """Writes ball 'k's contacts beginning, 'fresh', to 'events', (step,
  kind, first, second), kind 0 a cushion, 1 a pair, each pair once;
  returns how many events there are now."""
  room = events.shape[0]
  out = logged
  for bit in range(4 + count):
    if (fresh >> bit) & 1 == 1 and out < room:
      if bit < 4:
        events[out] = wp.vec4i(steps, 0, k, bit)
        out += 1
      elif bit - 4 > k:
        events[out] = wp.vec4i(steps, 1, k, bit - 4)
        out += 1
  return out


@wp.func
def softplus(x: wp.float64) -> wp.float64:
  """ln(1 + e^x), as '_cushion.softplus' has it."""
  if x > ZERO:
    return x + wp.log(ONE + wp.exp(-x))
  return wp.log(ONE + wp.exp(x))


@wp.func
def sidePushed(rules: HitRules, speed: wp.array(dtype=wp.vec2d),
               spin: wp.array(dtype=wp.vec3d), k: int, away: wp.float64,
               ix: wp.float64, iy: wp.float64, step: wp.float64,
               lift: wp.float64) -> wp.float64:
  """Pushes ball 'k' off a cushion's nose 'away' from its middle across
  the cloth, 'ix', 'iy' the way from the nose to the ball, for 'step',
  as Mathavan et al. (2010) have a cushion push, the user's squaring
  past where they hold, as '_motion._nosePushed' does, sum for sum;
  returns 'lift' with the nose's push up on it added."""
  if away >= rules.radius:
    return lift
  apart = wp.sqrt(away * away + rules.drop * rules.drop)
  given = rules.radius - apart
  if given <= ZERO:
    return lift
  vx = speed[k][0]
  vy = speed[k][1]
  wx = spin[k][0]
  wy = spin[k][1]
  wz = spin[k][2]
  up = lift
  ex = ix * rules.across
  ey = iy * rules.across
  ez = rules.down
  giving = -away * (ix * vx + iy * vy) / apart
  spring = rules.stiffness * wp.pow(given, rules.stiffening)
  push = wp.max(spring + rules.damping * giving, ZERO)
  vx = vx + push * ex * step
  vy = vy + push * ey * step
  up = up + push * ez
  if push > ZERO:
    rx = -rules.radius * ex
    ry = -rules.radius * ey
    rz = -rules.radius * ez
    cx = vx + wy * rz - wz * ry
    cy = vy + wz * rx - wx * rz
    cz = wx * ry - wy * rx
    normal = cx * ex + cy * ey + cz * ez
    sx = cx - normal * ex
    sy = cy - normal * ey
    sz = cz - normal * ez
    slip = wp.sqrt(sx * sx + sy * sy + sz * sz)
    if slip > ZERO:
      size = wp.min(rules.grip * push * step, slip / ROLL)
      jx = -sx / slip * size
      jy = -sy / slip * size
      jz = -sz / slip * size
      vx = vx + jx
      vy = vy + jy
      up = up + jz / step
      wx = wx + (ry * jz - rz * jy) / rules.inertia
      wy = wy + (rz * jx - rx * jz) / rules.inertia
      wz = wz + (rx * jy - ry * jx) / rules.inertia
    if rules.squaring > ZERO:
      ax = -iy
      ay = ix
      along = vx * ax + vy * ay
      stored = rules.storingShare * wp.pow(given, rules.storing)
      comes = wp.sqrt(giving * giving + TWO * stored) / rules.across
      over = comes - rules.squaringFrom
      if over > ZERO and along != ZERO:
        hard = over * over / (over + rules.squaringOnset)
        angle = wp.atan2(wp.abs(along), comes)
        near = softplus((rules.squaringBelow - angle) / rules.squaringWidth)
        share = rules.squaring * hard * near / rules.squaringNorm
        size = wp.min(share * push * step, wp.abs(along))
        held = -size
        if along < ZERO:
          held = size
        vx = vx + held * ax
        vy = vy + held * ay
  speed[k] = wp.vec2d(vx, vy)
  spin[k] = wp.vec3d(wx, wy, wz)
  return up


@wp.func
def cushionsPushed(rules: HitRules, place: wp.array(dtype=wp.vec2d),
                   speed: wp.array(dtype=wp.vec2d),
                   spin: wp.array(dtype=wp.vec3d), k: int,
                   step: wp.float64) -> wp.float64:
  """Pushes ball 'k' off each cushion it presses for 'step', as
  '_cushionPush' does; returns the cushions' push up on it."""
  lift = ZERO
  for side in range(4):
    sided = _away(rules, place[k][0], place[k][1], side)
    lift = sidePushed(rules, speed, spin, k, sided[0], sided[1], sided[2],
                      step, lift)
  return lift


@wp.func
def pairPushed(rules: HitRules, place: wp.array(dtype=wp.vec2d),
               speed: wp.array(dtype=wp.vec2d),
               spin: wp.array(dtype=wp.vec3d),
               lifts: wp.array(dtype=wp.float64), offset: int, k: int,
               m: int, step: wp.float64):
  """Pushes balls 'k' and 'm' apart for 'step', with friction where
  they touch, as '_ballPush' does; adds their pushes up to 'lifts',
  'offset' on."""
  dx = place[m][0] - place[k][0]
  dy = place[m][1] - place[k][1]
  apart = wp.sqrt(dx * dx + dy * dy)
  if apart <= ZERO:
    return
  nx = dx / apart
  ny = dy / apart
  given = TWO * rules.radius - apart
  giving = -((speed[m][0] - speed[k][0]) * nx +
             (speed[m][1] - speed[k][1]) * ny)
  push = ZERO
  if given > ZERO:
    both = rules.swingSquared * given + rules.swingDamping * giving
    push = wp.max(HALF * both, ZERO)
  speed[k] = speed[k] - wp.vec2d(push * nx * step, push * ny * step)
  speed[m] = speed[m] + wp.vec2d(push * nx * step, push * ny * step)
  if push <= ZERO:
    return
  rx = rules.radius * nx
  ry = rules.radius * ny
  one = spin[k]
  other = spin[m]
  c1x = speed[k][0] - one[2] * ry
  c1y = speed[k][1] + one[2] * rx
  c1z = one[0] * ry - one[1] * rx
  c2x = speed[m][0] + other[2] * ry
  c2y = speed[m][1] - other[2] * rx
  c2z = -other[0] * ry + other[1] * rx
  sx = c1x - c2x
  sy = c1y - c2y
  sz = c1z - c2z
  normal = sx * nx + sy * ny
  sx = sx - normal * nx
  sy = sy - normal * ny
  slip = wp.sqrt(sx * sx + sy * sy + sz * sz)
  if slip <= ZERO:
    return
  fall = wp.exp(-wp.abs(slip) / rules.slipScale)
  friction = rules.fastFriction + rules.frictionSpread * fall
  size = wp.min(friction * push * step, slip / PAIR)
  jx = -sx / slip * size
  jy = -sy / slip * size
  jz = -sz / slip * size
  speed[k] = speed[k] + wp.vec2d(jx, jy)
  speed[m] = speed[m] - wp.vec2d(jx, jy)
  turnOne = wp.vec3d(ry * jz / rules.inertia, -rx * jz / rules.inertia,
                     (rx * jy - ry * jx) / rules.inertia)
  spin[k] = spin[k] + turnOne
  spin[m] = spin[m] + turnOne
  lifts[offset + k] = lifts[offset + k] + jz / step
  lifts[offset + m] = lifts[offset + m] - jz / step


@wp.func
def slated(rules: HitRules, place: wp.array(dtype=wp.vec2d),
           turn: wp.array(dtype=wp.vec4d), speed: wp.array(dtype=wp.vec2d),
           spin: wp.array(dtype=wp.vec3d),
           settling: wp.array(dtype=wp.int32), k: int, lift: wp.float64,
           step: wp.float64):
  """Moves ball 'k', touching a cushion or ball, on for 'step' on the
  slate, bearing its weight less 'lift', as '_slate' does: hit again,
  set going faster than the felt's push back, it will be pushed back
  as its next roll ends."""
  bearing = wp.max(rules.gravity - lift, ZERO)
  vx = speed[k][0]
  vy = speed[k][1]
  wx = spin[k][0]
  wy = spin[k][1]
  wz = spin[k][2]
  sx = vx - rules.radius * wy
  sy = vy + rules.radius * wx
  slip = wp.sqrt(sx * sx + sy * sy)
  if slip > ZERO:
    size = wp.min(rules.sliding * bearing * step, slip / ROLL) / slip
    jx = -sx * size
    jy = -sy * size
    vx = vx + jx
    vy = vy + jy
    wx = wx + rules.radius * jy / rules.inertia
    wy = wy - rules.radius * jx / rules.inertia
  decay = rules.spinDecay * bearing / rules.gravity * step
  left = wp.max(wp.abs(wz) - decay, ZERO)
  if wz < ZERO:
    left = -left
  wz = left
  speed[k] = wp.vec2d(vx, vy)
  spin[k] = wp.vec3d(wx, wy, wz)
  place[k] = place[k] + wp.vec2d(vx * step, vy * step)
  turn[k] = turned(turn[k], wx * step, wy * step, wz * step)
  if wp.sqrt(vx * vx + vy * vy) > rules.settleSpeed:
    settling[k] = int(0)


@wp.kernel
def hitsRun(rules: HitRules, place: wp.array(dtype=wp.vec2d),
            turn: wp.array(dtype=wp.vec4d),
            speed: wp.array(dtype=wp.vec2d),
            spin: wp.array(dtype=wp.vec3d),
            settling: wp.array(dtype=wp.int32),
            going: wp.array(dtype=wp.int32),
            begun: wp.float64, start: wp.float64, seconds: wp.float64,
            whole: wp.int32, wake: wp.float64, most: wp.int32,
            events: wp.array(dtype=wp.vec4i),
            out: wp.array(dtype=wp.float64)):
  """Steps the balls, all touching something, through their hits for
  'seconds' at most, cut short at the end unless 'whole'; hands back
  once all are clear ('out' [2] one), once one is free of contacts, or
  once 'wake' has passed, a ball asleep in Python due. 'going' holds
  the contacts now, a ball's four cushions as bits and its pairs after;
  each contact beginning is written to 'events': (step, kind, first,
  second), kind 0 a cushion, 1 a pair. Time is kept as 'Hits' keeps
  it, from 'start', the run begun at 'begun', each step added on, so a
  run cut anywhere goes on the same. 'out': the time now, the steps,
  whether all are clear, how many events, then each ball's lift."""
  count = place.shape[0]
  used = start
  steps = int(0)
  clear = int(0)
  logged = int(0)
  while used - begun < seconds and steps < most:
    #  The contacts now, as '_touchesAmong' finds them.
    anyContact = int(0)
    free = int(0)
    pairs = int(0)
    for k in range(count):
      mine = contactsOf(rules, place, speed, k)
      if mine == 0:
        free = int(1)
      else:
        anyContact = int(1)
      if mine >= 16:
        pairs = int(1)
      logged = loggedOf(events, logged, steps, k, mine & (~going[k]),
                        count)
      going[k] = mine
    if anyContact == 0:
      clear = int(1)
      break
    if free != 0:
      break
    fine = rules.cushionStep
    if pairs != 0:
      fine = rules.caromStep
    step = fine
    if whole == 0:
      step = wp.min(fine, seconds - (used - begun))
    #  The pushes, as '_cushionPush', '_ballPush' and '_slate' give them.
    for k in range(count):
      lift = ZERO
      if going[k] & 15 != 0:
        lift = cushionsPushed(rules, place, speed, spin, k, step)
      out[4 + k] = lift
    for k in range(count):
      for m in range(count):
        if m > k and (going[k] >> (4 + m)) & 1 == 1:
          pairPushed(rules, place, speed, spin, out, 4, k, m, step)
    #  On the slate, moved, turned.
    for k in range(count):
      if going[k] != 0:
        slated(rules, place, turn, speed, spin, settling, k, out[4 + k],
               step)
    used = used + step
    steps = steps + 1
    if used >= wake:
      break
  out[0] = used
  out[1] = wp.float64(steps)
  out[2] = wp.float64(clear)
  out[3] = wp.float64(logged)
