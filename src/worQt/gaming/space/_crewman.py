"""
Crewman is Asger out of his chair (user, 2026-11-17: "when can Asger
get up and float around in micro-gravity?"; getting up and the loose
things: "FAFO rules"): where his body is in the cabin, the way it is up
and ahead, whether he touches anything, how he wants to move (walking
where he is pulled to the floor hard enough, as fast as the pull lets
him; else pushing off what he touches, the way he looks), his stride,
and his figure standing, walking or floating. The cabin's kernel moves
his body ('CabinWorld'); Qt-free, the vessel's own axes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.sandbox._gait import Gait

from ._aerospike import G0
from ._cockpit import CUSHION, FLOOR, HIPS, LIMBS, NECK_YAW, SCALE
from ._cockpit import UP_PITCH_MOST, seated
from ._turns import aboutAxis, cross, dot, norm, product, quaternionOf
from ._turns import rotated, unit

#  His body (user, 2026-11-17: "Could we just give Asger the minecraft
#  implementation of some blocks or whatever rather than just a few
#  balls?"; "those movements were janky af"; '_cabin_kernels.walked'):
#  an upright box along his up, 'WIDE' across both ways (slimmer than
#  Minecraft's 0.6: "we need to be more forgiving about how much space
#  Asger needs"), 'TALL' from his soles to his crown, crouched 'LOW'
#  ("and make me able to crouch!": Minecraft's sneak), its 'MIDDLE' this
#  far over his soles (his place, m); walking it steps up onto what is no
#  higher than 'STEP' (the stairs' steps are 0.21), m. His eyes this far
#  up and ahead of his soles, m; his mass, kg.
MIDDLE = 0.9
WIDE = 0.4
TALL = 32.0 * SCALE
LOW = 1.55
STEP = 0.35
EYES_UP = 28.0 * SCALE
EYES_AHEAD = 4.0 * SCALE + 0.02
HEFT = 80.0
#  Getting up he stands behind his chair (his rig's middle, his soles a
#  hair over the floor), facing ahead; he sits again within 'SIT' m of
#  his seat's middle.
STAND = seated(-0.88, 0.0, 0.002)
SIT = 1.0
#  Pulled to the floor harder than 'WALK' g he walks, at 'STRIDE' m/s
#  ('CROUCHED' of it crouched), slower the harder he is pulled past one g
#  (as its square); crouched his body leans 'LEAN' rad forward from his
#  hips (his eyes and head lower with it); stepping up, his eyes follow
#  most of the way in 'EASE_STEP' s (not at once: a jump); he jumps
#  'JUMP' m high. Pulled less, he pushes off what he touches at 'PUSH'
#  m/s. Pulled harder than 'UPRIGHT' g, standing, his feet turn him to
#  stand against the pull (on a floor within 'SQUARE' (a cosine) of
#  that, square on the floor; 'RIGHTING' is left of the old easing's
#  time for the gait).
WALK = 0.3
STRIDE = 3.0
CROUCHED = 0.3
LEAN = 0.6
EASE_STEP = 0.08
JUMP = 0.5
PUSH = 2.0
UPRIGHT = 0.15
RIGHTING = 0.5
SQUARE = 0.7
#  His limbs: how far his legs and arms swing either way at a full
#  stride, rad; floating, how they hang (legs a little ahead, arms out
#  before him).
SWING = 0.6
FLOAT_LEGS, FLOAT_ARMS = -0.35, -0.7
#  His body turning (user, 2026-11-18: "PHYSICS MUST BE REAL"; "AsgerJon
#  can turn, because of his 'jetpack'"): his moments of inertia, kg m²,
#  about his own axes (ahead, left, up: a standing man's, across him and
#  along him); his neck's reach either way ('_cockpit.NECK_YAW'); what
#  turns his body toward where his head looks
#  (and, standing, up against the pull): his feet on the floor, as hard
#  as his weight on half his stance ('STANCE' m) holds, his hands on what
#  he touches weightless ('ARMS' N m), his jetpack's fans across their
#  lever ('FAN_ARM' m times their push), each a turning spring of
#  'TURNING' rad/s critically damped, no harder than that; its steps, s.
#  Knocked down (user, 2026-11-18: "You Spin me Round (Like a Record)":
#  what he meets pushes him where it meets him, '_cabin_kernels.walked'),
#  lying on what he touches, his arms and legs push him up, as hard as
#  his weight on 'GET_UP' m (a little more than his middle is over his
#  soles: he can rise from flat), a spring of 'RISING' rad/s, till he
#  stands within 'RISEN' (a cosine) of up against the pull; leant past
#  'FALLEN' (a cosine) he is down. Nothing else turns him: weightless and
#  touching nothing he keeps spinning as he spins.
MOMENTS = (13.0, 13.0, 1.5)
NECK = NECK_YAW
STANCE = 0.15
GET_UP = 1.0
RISING = 12.0
RISEN = 0.985
FALLEN = 0.7
ARMS = 30.0
FAN_ARM = 0.3
TURNING = 6.0
TURN_STEP = 1.0 / 240.0
#  The keys' wishes: ahead, back, left, right.
#  Off the sofa he stands this far before its seat's middle, m.
LEAVE = 0.6
MOVES = {'ahead': (1.0, 0.0), 'back': (-1.0, 0.0), 'left': (0.0, 1.0),
         'right': (0.0, -1.0)}


class Crewman:
  """
  Crewman is Asger's body: 'buckled' in his chair (then nothing of it
  moves) or out of it, its 'middle' and 'velocity' (the kernel's), its
  'up' and 'ahead' (unit, across each other: his head turns from them)
  and its 'spin' (rad/s, the vessel's own axes),
  whether it 'touches' anything and the way out of what it touches
  ('ground', summed normals' unit, None: nothing), his 'gait', and on
  the sofa ('lounge': the seat's
  top middle and the way it faces; None: not on it; user, 2026-11-17:
  "chill out by sitting in sofa"), sitting as in his chair, still; on
  the handles ('climbing', '_ladder': user, 2026-11-19, "When Asger is
  in ladder mode, no more physics. Asger just moves through the ladder
  system"), his body moved by them alone, out of the cabin's world.
  'unbuckled' gets him up, 'satDown' sits him if near enough; 'righted'
  turns his body as his feet, hands or jetpack turn it toward where his
  head looks (standing, up against the pull) and as it spins; 'wantOf'
  is how his legs want to move for the keys held; 'eyeOf' and
  'figureOf' where his eyes and limbs are.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('buckled', 'lounge', 'climbing', 'crouching', 'up', 'ahead',
           'spin', 'middle', 'velocity', 'touches', 'ground', 'crouched',
           'rising', 'floor', 'fallen')

  #  Public Variables
  buckled: bool
  middle: tuple
  velocity: tuple
  up: tuple
  ahead: tuple
  spin: tuple
  touches: bool
  ground: tuple | None
  gait: Gait
  lounge: tuple | None
  climbing: bool
  crouched: bool
  crouching: bool
  rising: float
  floor: tuple | None
  fallen: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.buckled, self.lounge, self.climbing = True, None, False
    self.crouching = False
    self._stood()
    self.gait = Gait()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def unbuckled(self, ) -> None:
    """The 'unbuckled' method gets him up: standing behind his chair,
    still, upright, facing ahead."""
    self.buckled = False
    self._stood()

  def satDown(self, ) -> bool:
    """The 'satDown' method sits him in his chair if he is within 'SIT'
    of it; returns whether he could."""
    if self.seatFar() > SIT:
      return False
    self.buckled = True
    self._stood()
    return True

  @property
  def sitting(self, ) -> bool:
    """The 'sitting' property says whether he sits (in his chair or on
    the sofa): his body is not moved then."""
    return self.buckled or self.lounge is not None

  def lounged(self, seat: tuple, facing: tuple,
              up: tuple = (0.0, 0.0, 1.0),
              velocity: tuple = (0.0, 0.0, 0.0)) -> None:
    """The 'lounged' method sits him on a seat ('seat': its top's middle;
    'facing': the way it faces; 'up' its up: the sofa's the cabin's, an
    elevator's toward the station's axis), moving with it ('velocity'),
    his head ahead."""
    self.buckled, self.lounge = False, (tuple(seat), tuple(facing))
    self.up, self.ahead = tuple(up), tuple(facing)
    self.middle = tuple(s + 0.3 * u for s, u in zip(seat, self.up))
    self.velocity, self.touches = tuple(velocity), True

  def offSofa(self, ) -> None:
    """The 'offSofa' method stands him up off the sofa, before it,
    facing the way it does."""
    seat, facing = self.lounge
    self.lounge = None
    soles = (seat[0] + LEAVE * facing[0], seat[1] + LEAVE * facing[1],
             FLOOR + 0.002)
    self.middle = tuple(s + MIDDLE * u for s, u in zip(soles, self.up))
    self.velocity, self.ground = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)

  def strappedIn(self, ) -> None:
    """The 'strappedIn' method puts him in his chair wherever he is."""
    self.buckled = True
    self._stood()

  def seatFar(self, ) -> float:
    """The 'seatFar' method returns how far his middle is from his
    seat's, m."""
    return math.dist(self.middle, CUSHION[0])

  def soles(self, ) -> tuple:
    """The 'soles' method returns where his soles are."""
    return tuple(m - MIDDLE * u for m, u in zip(self.middle, self.up))

  def facing(self, yaw: float) -> tuple:
    """The 'facing' method returns the way he faces, his head turned
    'yaw' (rad, toward his left) from 'ahead'."""
    return rotated(aboutAxis(self.up, yaw), self.ahead)

  def eyeOf(self, yaw: float) -> tuple:
    """The 'eyeOf' method returns his eyes' place, his head turned
    'yaw', swayed by his stride (on the sofa, sitting)."""
    facing = self.facing(yaw)
    if self.lounge is not None:
      origin = self._seatedFrom()
      return tuple(o + 28.0 * SCALE * u + EYES_AHEAD * f for o, u, f in zip(
        origin, self.up, facing))
    left = cross(self.up, facing)
    sway, rise = self.gait.offset()
    up, ahead = self._eyesUp()
    rise -= self.rising
    return tuple(s + up * u + ahead * f - sway * l + rise * u
                 for s, u, f, l in zip(self.soles(), self.up, facing,
                                       left))

  def _eyesUp(self, ) -> tuple:
    """Returns how far up and ahead of his soles his eyes are: crouched,
    his head leant forward with his body from his hips."""
    if not self.crouched:
      return EYES_UP, EYES_AHEAD
    hips = 12.0 * SCALE
    over = EYES_UP - hips
    return (hips + over * math.cos(LEAN) - EYES_AHEAD * math.sin(LEAN),
            EYES_AHEAD * math.cos(LEAN) + over * math.sin(LEAN))

  def placed(self, middle: tuple, velocity: tuple, met: int,
             normals: tuple, crouched: bool = False, rose: float = 0.0,
             floors: tuple = (0.0, 0.0, 0.0), spin: tuple = None) -> None:
    """The 'placed' method takes his body from the kernel: its 'middle'
    and 'velocity', how many meetings it touches and their normals
    summed, whether it is crouched, how far it stepped up (his eyes
    follow it eased: 'rising'), the normals of what it stands on summed
    ('floor': their unit, None: nothing; on his feet only: it is under
    his soles), its spin ('spin', as what he met twisted it; None: as it
    was)."""
    self.middle, self.velocity = tuple(middle), tuple(velocity)
    if spin is not None:
      self.spin = tuple(spin)
    size = norm(normals)
    self.touches = met > 0
    self.ground = tuple(n / size for n in normals) if (
      self.touches and size > 1e-9) else None
    size = norm(floors)
    self.floor = tuple(f / size for f in floors) if size > 1e-9 else None
    self.crouched = bool(crouched)
    self.rising += float(rose)

  def righted(self, pull: tuple, seconds: float, yaw: float = 0.0,
              pitch: float = 0.0, fans: float = 0.0,
              limp: bool = False) -> tuple:
    """The 'righted' method turns his body 'seconds' s on, his head
    turned 'yaw' and 'pitch' from it, pulled 'pull' (m/s²), his jetpack's
    fans pushing 'fans' N (nought: off): pulled harder than 'UPRIGHT' g,
    standing on his feet, they turn him up against the pull (square on
    the floor within 'SQUARE') and round to where his head looks;
    knocked down ('fallen': leant past 'FALLEN', till he stands within
    'RISEN' again), his arms and legs push him up so; weightless,
    touching something, his hands turn him to it whole (his up his
    head's), or not touching, his jetpack's fans; else (or 'limp':
    dead) he spins on (as a free body: his moments differ). Each no harder
    than it can ('STANCE', 'GET_UP', 'ARMS', 'FAN_ARM'). His head keeps
    looking where it looked (within his neck's reach: 'NECK'). Moves his
    stride on.
    Returns his head's yaw and pitch from his body then and the twist
    what turned him took back (N m s, the vessel's own axes: his feet's,
    arms' and hands' on what he touches, the fans' on the air)."""
    self._squared()
    look, head = self.lookOf(yaw, pitch), self.headUpOf(yaw, pitch)
    weight = norm(pull)
    most, aim, rate = 0.0, None, TURNING
    if limp:
      pass
    elif self.touches and weight > UPRIGHT * G0:
      up = tuple(-p / weight for p in pull)
      lean = dot(self.up, up)
      if lean < FALLEN:
        self.fallen = True
      elif self.fallen and lean > RISEN and self.floor is not None:
        self.fallen = False
      if (self.floor is not None and dot(self.floor, up) > SQUARE
              and not self.fallen):
        up = self.floor
      facing = self.facing(yaw)
      along = dot(facing, up)
      ahead = tuple(f - along * u for f, u in zip(facing, up))
      if norm(ahead) < 1e-6:
        along = dot(self.up, up)
        ahead = tuple(b - along * u for b, u in zip(self.up, up))
      if norm(ahead) > 1e-6:
        aim = unit(ahead), up
        most = HEFT * weight * (GET_UP if self.fallen else STANCE)
        rate = RISING if self.fallen else TURNING
    elif self.touches:
      aim, most = (look, head), ARMS
    elif fans > 0.0:
      aim, most = (look, head), fans * FAN_ARM
    back = [0.0, 0.0, 0.0]
    steps = max(1, math.ceil(seconds / TURN_STEP))
    dt = seconds / steps
    for _ in range(steps):
      torque = (0.0, 0.0, 0.0)
      if aim is not None:
        torque = self._turningTo(aim, most, rate)
      self._spun(torque, dt)
      back = [b - q * dt for b, q in zip(back, torque)]
    left = cross(self.up, self.ahead)
    yaw = math.atan2(dot(look, left), dot(look, self.ahead))
    yaw = max(-NECK, min(NECK, yaw))
    pitch = math.asin(max(-1.0, min(1.0, dot(look, self.up))))
    pitch = max(-UP_PITCH_MOST, min(UP_PITCH_MOST, pitch))
    along = tuple(v - dot(self.velocity, self.up) * u for v, u in zip(
      self.velocity, self.up))
    walking = self.touches and weight > WALK * G0
    self.gait.stepped(norm(along), walking, seconds)
    self.rising *= math.exp(-seconds / EASE_STEP)
    return yaw, pitch, tuple(back)

  def headUpOf(self, yaw: float, pitch: float) -> tuple:
    """The 'headUpOf' method returns his head's up, his head turned 'yaw'
    and 'pitch' from his body."""
    facing = self.facing(yaw)
    c, s = math.cos(pitch), math.sin(pitch)
    return tuple(-s * f + c * u for f, u in zip(facing, self.up))

  def wantOf(self, held: set, yaw: float, pitch: float,
             pull: tuple) -> tuple:
    """The 'wantOf' method returns how his legs want to move for the
    keys 'held' ('MOVES' names), his head turned 'yaw' and 'pitch',
    pulled 'pull': the velocity wanted, whether he walks (one: along
    the ground) and whether he wants anything at all (one)."""
    ahead = sum(MOVES[name][0] for name in held if name in MOVES)
    aside = sum(MOVES[name][1] for name in held if name in MOVES)
    weight = norm(pull) / G0
    if weight > WALK:
      facing = self.facing(yaw)
      left = cross(self.up, facing)
      way = tuple(ahead * f + aside * l for f, l in zip(facing, left))
      size = norm(way)
      speed = STRIDE / max(1.0, weight) ** 2
      if self.crouched or self.crouching:
        speed *= CROUCHED
      if size < 1e-9:
        return (0.0, 0.0, 0.0), 1, 1
      return tuple(speed * w / size for w in way), 1, 1
    if not (ahead or aside):
      return (0.0, 0.0, 0.0), 0, 0
    look = self.lookOf(yaw, pitch)
    left = cross(self.up, self.facing(yaw))
    way = unit(tuple(ahead * k + aside * l for k, l in zip(look, left)))
    return tuple(PUSH * w for w in way), 0, 1

  def wayOf(self, held: set, yaw: float, pitch: float) -> tuple:
    """The 'wayOf' method returns the way the keys 'held' ('MOVES'
    names) ask of him in space, his head turned 'yaw' and 'pitch' (a
    unit vector: ahead where he looks, aside across it; nought: none,
    or ahead and back held at once): his jetpack's ('_jetpack')."""
    ahead = sum(MOVES[name][0] for name in held if name in MOVES)
    aside = sum(MOVES[name][1] for name in held if name in MOVES)
    if not (ahead or aside):
      return 0.0, 0.0, 0.0
    look = self.lookOf(yaw, pitch)
    left = cross(self.up, self.facing(yaw))
    return unit(tuple(ahead * k + aside * l for k, l in zip(look, left)))

  def leapOf(self, pull: tuple) -> tuple:
    """The 'leapOf' method returns the velocity a jump adds: walking (on
    his feet), up as high as 'JUMP' against the pull; floating, a push
    off what he touches ('PUSH' along its normal); touching nothing, or
    knocked down, none."""
    if not self.touches:
      return 0.0, 0.0, 0.0
    weight = norm(pull)
    if weight > WALK * G0:
      if self.floor is None:
        return 0.0, 0.0, 0.0
      speed = math.sqrt(2.0 * weight * JUMP)
      return tuple(speed * u for u in self.up)
    way = self.ground or self.up
    return tuple(PUSH * w for w in way)

  def lookOf(self, yaw: float, pitch: float) -> tuple:
    """The 'lookOf' method returns the way his eyes look, his head
    turned 'yaw' round and 'pitch' up."""
    facing = self.facing(yaw)
    return tuple(math.cos(pitch) * f + math.sin(pitch) * u
                 for f, u in zip(facing, self.up))

  def figureOf(self, yaw: float, parts: tuple) -> tuple:
    """The 'figureOf' method returns how his figure stands for the
    skin's 'parts': each part's index, its pivot's place and its turn
    (his body facing 'yaw' from 'ahead'): walking, his legs and arms
    swinging with his stride; floating, hanging loose."""
    if self.lounge is not None:
      return self._seatedFigure(parts)
    facing = self.facing(yaw)
    left = cross(self.up, facing)
    body = quaternionOf(tuple((facing[k], left[k], self.up[k])
                              for k in range(3)))
    soles = self.soles()
    swing = SWING * self.gait.swing * math.sin(self.gait.phase)
    floating = not self.touches and self.gait.swing < 0.05
    angles = {'right leg': swing, 'left leg': -swing,
              'right arm': -0.8 * swing, 'left arm': 0.8 * swing}
    if floating:
      angles = {'right leg': FLOAT_LEGS, 'left leg': FLOAT_LEGS,
                'right arm': FLOAT_ARMS, 'left arm': FLOAT_ARMS}
    hips = (0.0, 0.0, 12.0 * SCALE)
    lean = aboutAxis((0.0, 1.0, 0.0), LEAN if self.crouched else 0.0)
    out = []
    for index, part in enumerate(parts):
      local = tuple(SCALE * p for p in part[2])
      turn = body
      if not part[0].endswith('leg'):
        local = tuple(h + x for h, x in zip(hips, rotated(lean, tuple(
          p - h for p, h in zip(local, hips)))))
        turn = product(body, lean)
      place = tuple(s + x for s, x in zip(soles, rotated(body, local)))
      limb = aboutAxis((0.0, 1.0, 0.0), angles.get(part[0], 0.0))
      out.append((index, place, product(turn, limb)))
    return tuple(out)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _seatedFrom(self, ) -> tuple:
    """Returns where his figure is laid from sitting on the sofa (as in
    his chair: his hips on the seat, his soles' line below them)."""
    seat, facing = self.lounge
    return tuple(s - 0.05 * f + (HIPS - 12.0 * SCALE) * u for s, f, u in zip(
      seat, facing, self.up))

  def _seatedFigure(self, parts: tuple) -> tuple:
    """Returns his figure sitting on the sofa (his chair's pose, turned
    the way the sofa faces)."""
    facing = self.lounge[1]
    left = cross(self.up, facing)
    body = quaternionOf(tuple((facing[k], left[k], self.up[k])
                              for k in range(3)))
    origin = self._seatedFrom()
    out = []
    for index, part in enumerate(parts):
      local = tuple(SCALE * p for p in part[2])
      place = tuple(o + x for o, x in zip(origin, rotated(body, local)))
      limb = aboutAxis((0.0, 1.0, 0.0), LIMBS.get(part[0], 0.0))
      out.append((index, place, product(body, limb)))
    return tuple(out)

  def _turningTo(self, aim: tuple, most: float, rate: float) -> tuple:
    """Returns the twist turning his body to 'aim' (its ahead and up), a
    turning spring of 'rate' rad/s critically damped, no harder than
    'most' N m (the vessel's own axes)."""
    ahead, up = aim
    left = cross(up, ahead)
    body = self._rows()
    wanted = tuple((ahead[i], left[i], up[i]) for i in range(3))
    turn = product(quaternionOf(wanted), _inverse(quaternionOf(body)))
    error = _rotationOf(turn)
    own = _back(body, error)
    spun = _back(body, self.spin)
    torque = _forth(body, tuple(m * (rate * rate * e - 2.0 * rate * w)
                                for m, e, w in zip(MOMENTS, own, spun)))
    size = norm(torque)
    if size > most:
      torque = tuple(q * most / size for q in torque)
    return torque

  def _spun(self, torque: tuple, dt: float) -> None:
    """Turns his body 'dt' s on, twisted 'torque' (N m, the vessel's own
    axes): Euler's equations in its own axes, then turned by its spin."""
    body = self._rows()
    own = _back(body, self.spin)
    pushed = _back(body, torque)
    held = tuple(m * w for m, w in zip(MOMENTS, own))
    gyro = cross(own, held)
    own = tuple(w + (q - g) / m * dt for w, q, g, m in zip(
      own, pushed, gyro, MOMENTS))
    self.spin = _forth(body, own)
    rate = norm(self.spin)
    if rate * dt > 0.0:
      turn = aboutAxis(tuple(s / rate for s in self.spin), rate * dt)
      up = unit(rotated(turn, self.up))
      ahead = rotated(turn, self.ahead)
      ahead = unit(tuple(a - dot(ahead, up) * u for a, u in zip(ahead, up)))
      self.up, self.ahead = up, ahead

  def _squared(self, ) -> None:
    """Makes his ahead square to his up (set from outside, it may lean on
    it: any way across it, his old ahead's if it can)."""
    self.up = unit(self.up)
    along = dot(self.ahead, self.up)
    ahead = tuple(a - along * u for a, u in zip(self.ahead, self.up))
    if norm(ahead) < 1e-6:
      other = (1.0, 0.0, 0.0) if abs(self.up[0]) < 0.9 else (0.0, 1.0, 0.0)
      ahead = cross(self.up, cross(other, self.up))
    self.ahead = unit(ahead)

  def _rows(self, ) -> tuple:
    """Returns his body's axes as rows' columns: ahead, left, up."""
    left = cross(self.up, self.ahead)
    return tuple((self.ahead[i], left[i], self.up[i]) for i in range(3))

  def _stood(self, ) -> None:
    """Stands him behind his chair, still, upright, facing ahead,
    touching the floor."""
    self.up, self.ahead, self.lounge = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), None
    self.spin = (0.0, 0.0, 0.0)
    self.middle = tuple(s + MIDDLE * u for s, u in zip(STAND, self.up))
    self.velocity, self.touches = (0.0, 0.0, 0.0), True
    self.ground = (0.0, 0.0, 1.0)
    self.crouched, self.rising, self.floor = False, 0.0, (0.0, 0.0, 1.0)
    self.fallen = False


def _back(rows: tuple, x: tuple) -> tuple:
  """Returns 'x' in the axes whose columns are 'rows'."""
  return tuple(sum(rows[i][j] * x[i] for i in range(3)) for j in range(3))


def _forth(rows: tuple, x: tuple) -> tuple:
  """Returns 'x' (in the axes whose columns are 'rows') in the vessel's
  own."""
  return tuple(sum(rows[i][j] * x[j] for j in range(3)) for i in range(3))


def _inverse(turn: tuple) -> tuple:
  """Returns the turn 'turn' undoes (w x y z)."""
  w, x, y, z = turn
  return w, -x, -y, -z


def _rotationOf(turn: tuple) -> tuple:
  """Returns 'turn' as a rotation vector (axis times angle, rad), the
  short way round."""
  w, x, y, z = turn
  if w < 0.0:
    w, x, y, z = -w, -x, -y, -z
  size = math.sqrt(x * x + y * y + z * z)
  if size < 1e-12:
    return 2.0 * x, 2.0 * y, 2.0 * z
  angle = 2.0 * math.atan2(size, w)
  return x * angle / size, y * angle / size, z * angle / size
