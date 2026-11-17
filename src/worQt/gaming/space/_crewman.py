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
from ._cockpit import CUSHION, FLOOR, HIPS, LIMBS, SCALE, seated
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
#  m/s. Pulled harder than 'UPRIGHT' g his up turns to stand against the
#  pull, most of the way in 'RIGHTING' s (standing on a floor within
#  'SQUARE' (a cosine) of that, square on the floor).
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
#  The keys' wishes: ahead, back, left, right.
#  Off the sofa he stands this far before its seat's middle, m.
LEAVE = 0.6
MOVES = {'ahead': (1.0, 0.0), 'back': (-1.0, 0.0), 'left': (0.0, 1.0),
         'right': (0.0, -1.0)}


class Crewman:
  """
  Crewman is Asger's body: 'buckled' in his chair (then nothing of it
  moves) or out of it, its 'middle' and 'velocity' (the kernel's), its
  'up' and 'ahead' (unit, across each other: his head turns from them),
  whether it 'touches' anything and the way out of what it touches
  ('ground', summed normals' unit, None: nothing), his 'gait', and on
  the sofa ('lounge': the seat's
  top middle and the way it faces; None: not on it; user, 2026-11-17:
  "chill out by sitting in sofa"), sitting as in his chair, still.
  'unbuckled' gets him up, 'satDown' sits him if near enough; 'righted'
  stands him against the pull; 'wantOf' is how his legs want to move for
  the keys held; 'eyeOf' and 'figureOf' where his eyes and limbs are.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  buckled: bool
  middle: tuple
  velocity: tuple
  up: tuple
  ahead: tuple
  touches: bool
  ground: tuple | None
  gait: Gait
  lounge: tuple | None
  crouched: bool
  crouching: bool
  rising: float
  floor: tuple | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.buckled, self.lounge = True, None
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

  def lounged(self, seat: tuple, facing: tuple) -> None:
    """The 'lounged' method sits him on the sofa ('seat': its top's
    middle; 'facing': the way it faces), still, his head ahead."""
    self.buckled, self.lounge = False, (tuple(seat), tuple(facing))
    self.up, self.ahead = (0.0, 0.0, 1.0), tuple(facing)
    self.middle = tuple(s + 0.3 * u for s, u in zip(seat, self.up))
    self.velocity, self.touches = (0.0, 0.0, 0.0), True

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
             floors: tuple = (0.0, 0.0, 0.0)) -> None:
    """The 'placed' method takes his body from the kernel: its 'middle'
    and 'velocity', how many meetings it touches and their normals
    summed, whether it is crouched, how far it stepped up (his eyes
    follow it eased: 'rising'), the normals of what it stands on summed
    ('floor': their unit, None: nothing)."""
    self.middle, self.velocity = tuple(middle), tuple(velocity)
    size = norm(normals)
    self.touches = met > 0
    self.ground = tuple(n / size for n in normals) if (
      self.touches and size > 1e-9) else None
    size = norm(floors)
    self.floor = tuple(f / size for f in floors) if size > 1e-9 else None
    self.crouched = bool(crouched)
    self.rising += float(rose)

  def righted(self, pull: tuple, seconds: float) -> None:
    """The 'righted' method turns his up a share of the way to stand
    against 'pull' (m/s²; pulled less than 'UPRIGHT' g his up stays as
    it is: floating, nothing is down), or standing on a floor, square on
    it (as Minecraft's player stands: the pull sideways in a moving
    elevator's cage does not tilt him) and moves his stride on."""
    weight = norm(pull)
    if weight > UPRIGHT * G0:
      want = tuple(-p / weight for p in pull)
      if self.floor is not None and dot(self.floor, want) > SQUARE:
        want = self.floor
      share = 1.0 - math.exp(-seconds / RIGHTING)
      up = unit(tuple(u + share * (w - u) for u, w in zip(self.up, want)))
      ahead = tuple(a - dot(self.ahead, up) * u for a, u in zip(
        self.ahead, up))
      if norm(ahead) < 1e-6:
        ahead = cross(up, cross(self.ahead, up))
      self.up, self.ahead = up, unit(ahead)
    along = tuple(v - dot(self.velocity, self.up) * u for v, u in zip(
      self.velocity, self.up))
    walking = self.touches and weight > WALK * G0
    self.gait.stepped(norm(along), walking, seconds)
    self.rising *= math.exp(-seconds / EASE_STEP)

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

  def leapOf(self, pull: tuple) -> tuple:
    """The 'leapOf' method returns the velocity a jump adds: walking,
    up as high as 'JUMP' against the pull; floating, a push off what he
    touches ('PUSH' along its normal); touching nothing, none."""
    if not self.touches:
      return 0.0, 0.0, 0.0
    weight = norm(pull)
    if weight > WALK * G0:
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

  def _stood(self, ) -> None:
    """Stands him behind his chair, still, upright, facing ahead,
    touching the floor."""
    self.up, self.ahead, self.lounge = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), None
    self.middle = tuple(s + MIDDLE * u for s, u in zip(STAND, self.up))
    self.velocity, self.touches = (0.0, 0.0, 0.0), True
    self.ground = (0.0, 0.0, 1.0)
    self.crouched, self.rising, self.floor = False, 0.0, (0.0, 0.0, 1.0)
