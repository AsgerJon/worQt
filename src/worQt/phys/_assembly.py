"""
Assembly is bodies put together: the bodies, and how they are joined:
tied at a point (Tie), welded into one (Weld), sprung (Spring),
damped (Damper), driven (Actuator, its length a stroke: HeldStroke,
SineStroke), touching (Contact; many balls, a Crowd), corded
(CordLine), sealing in air (Air), on a tyre (Tyre).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._body import Body
from ._vectors import Vector, dot, minus, norm, scaled


class Tie(NamedTuple):
  """
  Tie is two bodies tied together at a point on each by a cord of no
  length (the user's: a cord bears no push, no shear and no twist, only
  pull, without end; its length taken to nought). Whichever way the two
  points would part they stretch it, so it holds them together every
  way, three degrees of freedom taken; it bears no twist, so the bodies
  turn freely about the point (a ball joint). 'first' and 'second' are
  the bodies' places in the assembly, None for the world itself;
  'firstPoint' and 'secondPoint' the points, each in its body's own
  frame (the world's, for the world).
  """

  first: int | None
  firstPoint: Vector
  second: int | None
  secondPoint: Vector


class Weld(NamedTuple):
  """
  Weld makes of any number of bodies, its 'parts' (their places in the
  assembly), one new rigid body: they keep as they lie to each other
  when welded, six degrees of freedom among them all. Welds sharing a
  body weld all their parts together. Parts welded moving apart are
  jerked together at once, their momentum and angular momentum kept.
  """

  parts: tuple[int, ...]


class Fixed(NamedTuple):
  """
  Fixed makes body 'body' (its place in the assembly) a part of the
  world: it never moves, gravity and the ground pass it by, and what
  pushes on it or is tied to it meets it as the world (infinitely
  heavy). For what is held still anyway (a stand, a housing on its
  pedestal: rigid legs held it as still) without the rules that held
  it, which cost every step (user, 2026-11-13: "everything should run on
  gpu always!": the bearing's still bodies took 30 of its 46 rules).
  """

  body: int


class Spring(NamedTuple):
  """
  Spring is a coil spring between a point on each of two bodies, 'first'
  and 'second' their places in the assembly (None for the world),
  'firstPoint' and 'secondPoint' the points in each body's own frame
  (the world's, for the world). It pushes or pulls along the line
  between them, 'stiffness' N/m times as far as that is from 'rest' m,
  and holds as much energy, half the stiffness times that squared. Of
  no rest length it pulls the points together whichever way they part.
  With 'damping' (N s/m, nought at first) it is rubber, not steel: it
  pushes back too, that times how fast it lengthens (of no rest length,
  how fast its points part, whichever way), worked from the bodies as
  they move at each kick (light damping, as a tyre's: a damping that
  must be solved with the rules is a 'Damper'). A spring that 'pulls'
  not (True at first) is a buffer: it only pushes, as a bump stop does,
  slack longer than its rest length; one that 'pushes' not is a strap:
  it only pulls, as a droop strap or a rope does, slack shorter (either
  way, slack, it holds nothing and damps nothing). One of no rest length
  does both.
  """

  first: int | None
  firstPoint: Vector
  second: int | None
  secondPoint: Vector
  stiffness: float
  rest: float
  damping: float = 0.0
  pulls: bool = True
  pushes: bool = True

  def slack(self, length: float) -> bool:
    """The 'slack' method tells whether the spring, 'length' m long,
    holds nothing: a buffer longer than its rest length, a strap
    shorter."""
    if self.rest == 0.0:
      return False
    if length > self.rest:
      return not self.pulls
    return not self.pushes

  def pullOf(self, first: Vector, second: Vector) -> Vector:
    """The 'pullOf' method returns the spring's pull on its first body,
    N, its ends at 'first' and 'second' in the world (its second is
    pulled as hard the other way)."""
    apart = minus(second, first)
    if self.rest == 0.0:
      return scaled(apart, self.stiffness)
    length = norm(apart)
    if length == 0.0 or self.slack(length):
      return 0.0, 0.0, 0.0
    return scaled(apart, self.stiffness * (length - self.rest) / length)

  def storedOf(self, first: Vector, second: Vector) -> float:
    """The 'storedOf' method returns the energy the spring holds, its
    ends at 'first' and 'second' in the world, J."""
    length = norm(minus(second, first))
    if self.slack(length):
      return 0.0
    stretch = length - self.rest
    return 0.5 * self.stiffness * stretch * stretch

  def dampedOf(self, first: Vector, second: Vector, firstMoving: Vector,
               secondMoving: Vector) -> Vector:
    """The 'dampedOf' method returns the spring's damping push on its
    first body, N, its ends at 'first' and 'second' moving at
    'firstMoving' and 'secondMoving' (its second is pushed as hard the
    other way): along the line by how fast it lengthens, or, of no rest
    length, by how fast its ends part."""
    parting = minus(secondMoving, firstMoving)
    if self.rest == 0.0:
      return scaled(parting, self.damping)
    apart = minus(second, first)
    length = norm(apart)
    if length == 0.0 or self.slack(length):
      return 0.0, 0.0, 0.0
    return scaled(apart, self.damping * dot(parting, apart)
                  / (length * length))


class Damper(NamedTuple):
  """
  Damper is a dashpot between a point on each of two bodies, 'first'
  and 'second' their places in the assembly (None for the world),
  'firstPoint' and 'secondPoint' the points in each body's own frame
  (the world's, for the world). It pushes or pulls along the line
  between them against how fast that lengthens or shortens, 'damping'
  N s/m times as fast; moving across the line, nothing. It holds no
  energy: what it takes is gone, as heat. With 'rebound' (N s/m; None:
  as 'damping') it holds back lengthening that hard and shortening by
  'damping' (a car's shock absorber: its rebound two to three times its
  bump; the small steps only).
  """

  first: int | None
  firstPoint: Vector
  second: int | None
  secondPoint: Vector
  damping: float
  rebound: float = None

  def lineOf(self, first: Vector, second: Vector) -> Vector:
    """The 'lineOf' method returns the unit line from the damper's end
    at 'first' to its end at 'second', in the world; nought when they
    are at one place."""
    apart = minus(second, first)
    length = norm(apart)
    if length == 0.0:
      return 0.0, 0.0, 0.0
    return scaled(apart, 1.0 / length)

  def pushOf(self, first: Vector, second: Vector, firstVelocity: Vector,
             secondVelocity: Vector) -> Vector:
    """The 'pushOf' method returns the damper's push on its first body,
    N, its ends at 'first' and 'second' moving at 'firstVelocity' and
    'secondVelocity' in the world (its second is pushed as hard the
    other way)."""
    line = self.lineOf(first, second)
    lengthening = dot(minus(secondVelocity, firstVelocity), line)
    return scaled(line, self.damping * lengthening)


class Actuator(NamedTuple):
  """
  Actuator is a rigid rod with ball ends between a point on each of two
  bodies, 'first' and 'second' their places in the assembly (None for
  the world), 'firstPoint' and 'secondPoint' the points in each body's
  own frame (the world's, for the world), its length what 'stroke' says
  at each moment (its 'at(time)' the length, m, how fast it grows, m/s,
  and how fast that grows, m/s²): it is that long, whatever force it
  takes (without end), pushing or pulling only along itself; a rule,
  one degree of freedom taken.
  """

  first: int | None
  firstPoint: Vector
  second: int | None
  secondPoint: Vector
  stroke: object


class HeldStroke(NamedTuple):
  """
  HeldStroke holds an actuator at 'length', m: a rigid rod with ball
  ends.
  """

  length: float

  def at(self, time: float) -> tuple[float, float, float]:
    """The 'at' method returns the length at 'time', how fast it grows,
    and how fast that grows: the length, nought, nought."""
    return self.length, 0.0, 0.0


class SineStroke(NamedTuple):
  """
  SineStroke swings an actuator's length about 'middle', m, as far as
  'amplitude' either way, 'frequency' times a second, from the middle
  growing at time nought: a shaker.
  """

  middle: float
  amplitude: float
  frequency: float

  def at(self, time: float) -> tuple[float, float, float]:
    """The 'at' method returns the length at 'time', how fast it grows,
    and how fast that grows."""
    rate = 2.0 * math.pi * self.frequency
    swing = math.sin(rate * time)
    return (self.middle + self.amplitude * swing,
            self.amplitude * rate * math.cos(rate * time),
            -self.amplitude * rate * rate * swing)


class Contact(NamedTuple):
  """
  Contact lets two bodies, 'first' and 'second' (their places in the
  assembly), touch: rest one on the other, lean, slide, knock, tip
  over an edge. Every real edge of each body's shape is a line of
  little springs, points 'spacing' m apart each with its share of the
  edge's length; wherever such a point is inside the other (each closed
  piece of a shape taken as convex: a box, a cylinder, the boxes of an
  L) the other pushes it out along the face it went in through as the
  ground does, per metre of edge: 'stiffness' N/m per m times as far,
  more the faster, by 'damping' s/m, never pulling; and holds it by a
  bristle, 'bristle' N/m per m and 'bristleDamping' N s/m per m, to
  where on the other it touched, slipping past 'grip' times the push.
  Each is pushed as hard the other way. One rule for every touch:
  corner on face, edge on face, edge across edge, face on face; a box
  resting flat sinks its weight over the stiffness times the length of
  its edges touching, however finely they are spaced. Unless 'both',
  only the first's edges press (a car's chassis on a track of a hundred
  planks: the track's edges too many to count; in small steps alone).
  """

  first: int
  second: int
  stiffness: float = 1e6
  damping: float = 1.0
  grip: float = 0.5
  bristle: float = 1e6
  bristleDamping: float = 1000.0
  spacing: float = 0.01
  both: bool = True

  def pushOf(self, share: float, depth: float, sinking: float) -> float:
    """The 'pushOf' method returns how hard a point holding 'share' m of
    edge, 'depth' into the other, sinking 'sinking' m/s deeper, is
    pushed out, N."""
    if depth <= 0.0:
      return 0.0
    return max(0.0, share * self.stiffness * depth
               * (1.0 + self.damping * sinking))


class Drive:
  """
  Drive is how hard a motor twists now, set from outside between runs
  (a driver's foot or hands), the one thing in an assembly that may
  change while it is kept: its 'torque', N m; or, with 'stiffness' (N m
  a radian) or 'damping' above nought, a servo's (with no stiffness and
  no torque, a brake's: it only ever opposes how the bodies turn on
  each other, no harder than 'most', and holds nothing still; with a
  torque and damping, an electric motor's: its torque standing, less as
  it turns, 'runMotor'): its torque, and a twist toward
  'target' rad, the
  second body turned on the first about the motor's axis from how it
  is turned on it in 'reference' (a turn, the second's own frame in the
  first's), 'stiffness' times how far off, less 'damping' (N m s) times
  how fast it turns on it, never harder than 'most' N m; worked out
  anew at every half step (a hand's muscles answer at once: worked out
  once a frame, a light steering column flew from lock to lock). A
  driveshaft's drive with a 'slip' above nought has traction control:
  its torque given in full while its wheel's rim (its spin on the
  shaft's first body, the chassis, times 'radius' m) outruns that
  body's speed along its own x by no more than that share of it (of 3
  m/s at least), none by twice that, worked out at every half step as
  a car's control unit reads its wheels a thousand times a second
  (read once a frame, the rear corners' 31 Hz hop at a launch showed as
  a steady slow rim and it never cut).
  """

  __slots__ = ('torque', 'target', 'stiffness', 'damping', 'most',
               'reference', 'slip', 'radius')

  def __init__(self, torque: float = 0.0) -> None:
    self.torque, self.target = torque, 0.0
    self.stiffness, self.damping, self.most = 0.0, 0.0, 0.0
    self.reference = (1.0, 0.0, 0.0, 0.0)
    self.slip, self.radius = 0.0, 0.0


class Motor(NamedTuple):
  """
  Motor is a motor between two bodies (the user, of the car: "we
  imagine that the bearings also contain engines"): it twists body
  'second' about 'axis' (a unit, in its own frame) as hard as its
  'drive' says now ('Drive.torque', N m), all through each step, and
  body 'first' (None for the world) as hard the other way, as a
  motor's housing takes its rotor's twist back. A twist acts on the
  whole body wherever it is put, so it has no point. Its work is
  booked with the actuators'.

  With a 'bearer' (a body's index) it is a driveshaft instead (the
  user, of the car: "four wheel drive"): the motor sits in body 'first'
  (a differential on the chassis) and turns a shaft from 'firstPoint'
  (in its own frame) out to 'secondPoint' on body 'second' (a wheel,
  in its own frame), jointed at both ends, the second turning in a
  bearing in 'bearer' (a knuckle). The shaft carries the drive's torque
  along its own line: the second is twisted about its axis by it, the
  first back along the bisector of the shaft's line and that axis, the
  bearer by what is between (a constant-velocity joint's moment lies
  along the bisector of the shafts it joins; the shaft's own end forces
  are left out). A driveshaft's
  drive is its torque, and, with 'damping', a brake on the shaft (an
  inboard brake: the damping times the rate the shaft's twists work at,
  no more than 'most'); no servo.
  """

  first: int | None
  second: int
  axis: Vector
  drive: Drive
  bearer: int | None = None
  firstPoint: Vector = None
  secondPoint: Vector = None


class Bush(NamedTuple):
  """
  Bush is a hinge's rubber bushing (a wishbone's in its bracket): how
  stiffly its rubber holds the pin across it, 'radial' N/m, along it,
  'axial' N/m, tilting it, 'tilt' N m/rad, and twisting about it,
  'twist' N m/rad (nought: it turns freely, as on a needle bearing;
  rubber twists, a car's 1 to 5 N m a degree), and how long its push
  lags its give, 'lag' s (its damping over its stiffness: rubber's loss
  of a sixth at 10 Hz is 2.4 ms). A car's wishbone bushing gives 2 to 10
  kN/mm across, a fifth of that along, 50 to 500 N m a degree tilted.
  """

  radial: float = 5e6
  axial: float = 1e6
  tilt: float = 1e4
  twist: float = 0.0
  lag: float = 2.4e-3


class Hinge(NamedTuple):
  """
  Hinge joins two bodies so that one turns on the other about one line
  only (user, 2026-11-14: "hinges, rigid and rubber-bushed or
  whatever"): a wishbone on its frame, a knuckle on its kingpin, a
  door. Its pin runs through 'firstPoint' along 'firstAxis' on body
  'first' and through 'secondPoint' along 'secondAxis' on 'second'
  (each in its body's own frame; None for the world, its points and
  lines the world's; a line either way along it), the two made one:
  the points kept together, the
  lines in line, the bodies turning freely about it. With no 'bush' it
  is rigid (five degrees of freedom taken); with one ('Bush') its
  rubber gives across the pin, along it and tilting it as stiffly as it
  says, damped, and, if it says so, holds the twist it was built with.
  """

  first: int | None
  firstPoint: Vector
  firstAxis: Vector
  second: int | None
  secondPoint: Vector
  secondAxis: Vector
  bush: Bush = None


class Slide(NamedTuple):
  """
  Slide is a sliding joint (a shock absorber's rod in its tube): the
  line through 'secondPoint' along 'secondAxis' on body 'second' kept
  on the line through 'firstPoint' along 'firstAxis' on body 'first'
  (each in its body's own frame; None for the world; a line either way
  along it): the bodies slide along it and turn about it freely, four
  degrees of freedom taken.
  """

  first: int | None
  firstPoint: Vector
  firstAxis: Vector
  second: int | None
  secondPoint: Vector
  secondAxis: Vector


class FourthWall:
  """
  FourthWall is a fourth wall point (user, 2026-11-14: "a concept for a
  new type of component: fourth wall points"): where the player's will
  comes into the world, 'value' (what they ask now: an angle, rad, for
  a 'TurnPoint'), set from outside between runs as a motor's 'Drive'
  is; what it moves is a part of the world, pushed as hard as the
  player can push, and pushing back. A brake's line ('BrakeLine') is
  one too: the player's foot at every caliper at once (a pedal, its
  master cylinder a fixed ratio to the line, would add nothing).
  """

  __slots__ = ('value',)

  def __init__(self, value: float = 0.0) -> None:
    self.value = value


class TurnPoint(NamedTuple):
  """
  TurnPoint is a fourth wall point that turns (the steering wheel: the
  player's hands on it): it turns body 'body' about 'axis' (a unit in
  its own frame) on body 'holder' (what the player sits in; None: the
  world) toward the angle 'wall' asks ('FourthWall.value', rad, from as
  built, a turn about 'axis' anticlockwise seen from its tip), as hands
  do: 'stiffness' N m a radian off, damped 'damping' N m s a radian a
  second, never harder than 'most' N m; the holder takes as much back.
  What resists (the tyres scrubbing, the rack's stops) is felt: past
  'most' the hands give.
  """

  body: int
  holder: int | None
  axis: Vector
  wall: FourthWall
  stiffness: float = 2000.0
  damping: float = 20.0
  most: float = 60.0


class RackAndPinion(NamedTuple):
  """
  RackAndPinion is a pinion on body 'pinion' (its axis 'pinionAxis', a
  unit in its own frame) meshing with a rack, body 'rack' (sliding along
  'rackAxis' in its own frame), both carried by body 'housing' (None:
  the world): as the pinion turns on the housing about its axis
  (anticlockwise seen from its tip), the rack slides on it along its
  axis 'radius' m (the pinion's pitch radius) a radian, and the other
  way round; each pushed as hard as the other is held back, the
  housing taking the rest. Its turning and sliding are from as built.
  """

  pinion: int
  pinionAxis: Vector
  rack: int
  rackAxis: Vector
  housing: int | None
  radius: float


class Housed(NamedTuple):
  """
  Housed says body 'body' turns inside another's case (a gear in its
  gearbox, a shaft in its housing): the ground never meets it, its case
  does (a gearbox's gears' teeth, every corner of them a point on the
  ground, gave the real car 12 000 touches that could never press).
  Small steps only.
  """

  body: int


class GearMesh(NamedTuple):
  """
  GearMesh is two gears meshing (user, 2026-11-14: "the differential and
  the stick shift gearbox and clutch"): a gear of 'firstTeeth' teeth on
  body 'first', turning about 'firstAxis' (a unit in its own frame), in
  mesh with one of 'secondTeeth' on body 'second' about 'secondAxis',
  both carried by body 'housing' (None: the world; a gearbox's case, a
  differential's carrier): as the first turns on the housing about its
  axis, the second turns on it about its own as many teeth, the other
  way (spur gears side by side, their axes alike) or, if 'same', the
  same way (bevel gears as their axes are given: a differential's
  spider with one side gear one way, with the other the other); each
  pushed as hard as the other is held back, at its pitch radius
  ('module' m a tooth, the radius half the module times the teeth), the
  housing taking the rest. Turns from as built; no backlash, no slip.
  Small steps only.
  """

  first: int
  firstAxis: Vector
  firstTeeth: int
  second: int
  secondAxis: Vector
  secondTeeth: int
  housing: int | None
  same: bool = False
  module: float = 0.003

  def radii(self, ) -> tuple[float, float]:
    """The 'radii' method returns the two gears' pitch radii, m."""
    return (0.5 * self.module * self.firstTeeth,
            0.5 * self.module * self.secondTeeth)


class Ram(NamedTuple):
  """
  Ram is a hydraulic ram (user, 2026-11-14, of the tyre rig: "An
  actuator then presses the arm such as to force the wheel into"
  the road) between a point on each of two bodies, 'first' and
  'second' (None: the world; points in their own frames, the world's
  for the world): it pushes them apart along the line between them as
  hard as 'wall' asks ('FourthWall.value', N: the oil's pressure on its
  piston, the operator's load; below nought it pulls), however long
  it is; it holds no length (a rule's none: a force, as gravity).
  Small steps only.
  """

  first: int | None
  firstPoint: Vector
  second: int | None
  secondPoint: Vector
  wall: FourthWall


class Hump(NamedTuple):
  """
  Hump is a bump bolted across a turntable (user, 2026-11-14: "the rod
  can also introduce 'bumps' in the road allowed us to observe how the
  suspension reacts"): a bar laid straight out from the table's axis at
  'angle' (rad, round it in its own frame, from its own x), from
  'inner' to 'outer' m from the axis, rounded across ('length' m, its
  rise and fall the square of a cosine) 'height' m high.
  """

  angle: float
  inner: float
  outer: float
  length: float = 0.4
  height: float = 0.03


class Humps:
  """
  Humps are the humps bolted across body 'body''s flat faces (a turned
  solid's, square to its axis: a turntable), 'humps' a tuple of 'Hump'
  as bolted on now (set from outside between runs, a fourth wall
  point: the operator's spanner): tyres on the face roll over them and
  balls are lifted by them. Small steps only, at most 'HUMP_ROOM'.
  """

  __slots__ = ('body', 'humps')

  def __init__(self, body: int, humps: tuple = ()) -> None:
    self.body, self.humps = body, tuple(humps)


#  How many humps an assembly may have bolted on at once.
HUMP_ROOM = 8


class BrakeLine:
  """
  BrakeLine is a brake's hydraulic line: how hard the driver's foot
  presses the fluid in it now, 'pressure', Pa over the outside's (a
  car's pedal hard down: 80 to 120 bar), set from outside between runs
  as a motor's 'Drive' is; every caliper on it squeezes by it. It is a
  fourth wall point ('FourthWall'): the player's foot.
  """

  __slots__ = ('pressure',)

  def __init__(self, pressure: float = 0.0) -> None:
    self.pressure = pressure


#  A car's caliper's piston, m² (one 54 mm), and its pads' friction on
#  cast iron (0.35 to 0.45).
PISTON = math.pi * 0.027 ** 2
PAD_FRICTION = 0.4


class DiscBrake(NamedTuple):
  """
  DiscBrake is a disc brake (user, 2026-11-14: "disc brakes (actual
  friction applies to discs connected to wheels)"): a disc, part of body
  'disc' (a wheel: its middle 'middle' and its axle 'axle', a unit,
  both in that body's own frame), turning between two pads in a
  caliper, part of body 'caliper' (a knuckle; None: the world), the
  pads' middle at 'pad' in its own frame (on the disc's middle plane).
  The line's pressure ('line', a 'BrakeLine') pushes the caliper's
  piston, 'piston' m², so each pad presses the disc as hard (a floating
  caliper: the piston pushes one pad, the caliper pulls the other); the
  pads rub where they are, while 'pad' lies between 'inner' and 'outer'
  m from the axle (the disc's swept ring), and each holds the disc by
  friction, 'friction' times its press: they slip while the disc turns
  under them, slowing it by no more than that, and grip and hold it
  once it stops (a parked car stays on its slope), the caliper taking
  as much back where it holds them.
  """

  disc: int
  caliper: int | None
  middle: Vector
  axle: Vector
  pad: Vector
  inner: float
  outer: float
  line: BrakeLine
  piston: float = PISTON
  friction: float = PAD_FRICTION

  def force(self, ) -> float:
    """The 'force' method returns how hard the pads can hold the disc
    now, N: both pads' friction at the line's pressure."""
    return 2.0 * self.friction * max(self.line.pressure, 0.0) * (
      self.piston)


class Drag(NamedTuple):
  """
  Drag is the air's drag on body 'body' (the user's oval: without it a
  car's engine sped it up lap after lap, as on no road): pushing its
  centre back along how it goes, half the air's 'density' (kg/m³) times
  its drag 'area' (its drag coefficient times its front, m²) times its
  speed squared; booked as a damper's heat (the air is still: no
  wind).
  """

  body: int
  area: float
  density: float = 1.2


class CordLine(NamedTuple):
  """
  CordLine is a cord threaded through a run of points (user,
  2026-11-13: a tyre is "elastic in tension only material with
  pressurized air inside"): 'points', each a body's place in the
  assembly and a point in its own frame; between each point and the
  next a piece of cord 'rests' m long unstretched, stretching as
  'stiffness' N/m says (each piece its own), pulling them together
  when longer, never pushing (slack when shorter: it folds); with
  'closed', the last point corded back to the first (a ring). A tyre's
  carcass is such cords from bead to bead, its belt rings of them.
  Small steps only ('SmallSteps': each line held whole at once).
  """

  points: tuple
  stiffness: tuple
  rests: tuple
  closed: bool = False


class Air(NamedTuple):
  """
  Air is air sealed in by a closed surface: 'faces', each three corners
  (a body's place in the assembly and a point in its own frame), wound
  anticlockwise seen from outside the air; 'gas', J, its pressure
  (absolute, Pa) times its volume (m³), kept as it is squeezed or let
  grow (as slowly as heat leaves it: isothermal), so its pressure is
  'gas' over the volume the faces enclose. It pushes every face out by
  its pressure over the air outside's ('ATMOSPHERE') times the face's
  area, a third at each corner. Small steps only.
  """

  faces: tuple
  gas: float


#  The air outside, Pa.
ATMOSPHERE = 101325.0


class Tyre(NamedTuple):
  """
  Tyre is a wheel's tyre as its air makes it (user, 2026-11-13: "model
  the wheel as a unidirectional spring working parallel to the plane of
  the wheel with whatever the fuck stiffness the current air pressure
  demands"): on the ground a spring pushing only, in the plane of the
  wheel 'body' (its axle 'axle', in its own frame; its tread's circle
  about 'hub', 'radius' m out), from the hub straight down that plane
  to the ground; as stiff as its air makes it: pressed in 'd', a
  toroidal tyre ('width' across its section) flattens to a patch of 2 pi
  d sqrt(radius width / 2) m², its air ('pressure' over the outside's,
  Pa) pushing on it all, so 2 pi pressure sqrt(radius width / 2) N/m
  ('stiffness': 2.3 bar on a 205/55 R16, 263 kN/m, as a real one's
  200-300), damped 'damping' N s/m. Its 'probes' (balls of 'probe' m
  about points of its own frame) meet other turned solids it touches
  (another wheel); lying over, its sidewalls' 'sides' (balls of
  'sideProbe' m, small: a wheel dropped upright squashes its spring
  2.5 cm, and 5 cm balls there bottomed out on the ground at 11.5 mm,
  killing its bounce) meet the ground. With a 'tread' (m, half its
  width) the spring is two, each half as stiff and damped, in planes
  parallel to the wheel's that far either side along the axle (its
  tread's edges): a wheel stands on its tread, as a real one does (one
  spring at its middle stood it on an edge, as a coin, and it fell
  over: user, 2026-11-13, "have the wheel start upright"). On the
  ground it loses what a tyre does: its push acts 'rolling' times its
  radius ahead of its patch (rolling resistance's coefficient), and its
  patch holds against pivoting about the upright with an arm of 'scrub'
  m (without either, a wheel rolled round on its edge for ever). Its
  grip on the road is its tread's (the small steps' 'tyreGrip', user,
  2026-11-14: its rigid grip walked the tyre rig's wheel sideways for
  ever): a brush whose stretch relaxes as it rolls (0.3 m), its force
  bending over to its grip at its peak (about 8 degrees of slip angle,
  15 to 20 % of slip) and falling as it slides on, its grip less a
  newton the more it carries, its patch's twist held to 'scrub' times its
  load, on a road textured as 'SmallSteps' says. Small steps only.
  """

  body: int
  hub: Vector
  axle: Vector
  radius: float
  width: float
  pressure: float
  damping: float
  probe: float
  probes: tuple
  sides: tuple
  sideProbe: float = 0.01
  tread: float = 0.0
  rolling: float = 0.0
  scrub: float = 0.0

  @property
  def stiffness(self, ) -> float:
    """The tyre's stiffness as its air makes it, N/m."""
    return 2.0 * math.pi * self.pressure * math.sqrt(
      self.radius * 0.5 * self.width)


class Crowd(NamedTuple):
  """
  Crowd lets many balls touch without a contact for every two of them
  (a tyre's hundreds of cord nodes against another's: hundreds of
  thousands of contacts, most never near): 'groups', each a run of
  balls (their places in the assembly), every ball of a group touching
  every ball of every other group, as a contact with grip 'grip' does;
  which may touch is found anew each call, those near enough to meet in
  it, at most 'room' at once (the nearest first). Small steps only.
  """

  groups: tuple
  grip: float = 0.5
  room: int = 8192


class Assembly(NamedTuple):
  """
  Assembly is 'bodies' put together by 'connections': ties, welds,
  springs, dampers, actuators, contacts, motors, drags, cord lines, air,
  crowds, tyres, disc brakes, hinges, slides, fourth wall points
  that turn, racks and pinions, rams, humps and bodies made part of the
  world
  ('Fixed'), in any order; a body held by nothing moves freely, six
  degrees of freedom its own.
  """

  bodies: tuple[Body, ...]
  connections: tuple = ()

  @property
  def ties(self, ) -> tuple[Tie, ...]:
    """The ties among the connections."""
    return _sortedOf(self)[Tie]

  @property
  def welds(self, ) -> tuple[Weld, ...]:
    """The welds among the connections."""
    return _sortedOf(self)[Weld]

  @property
  def springs(self, ) -> tuple[Spring, ...]:
    """The springs among the connections."""
    return _sortedOf(self)[Spring]

  @property
  def dampers(self, ) -> tuple[Damper, ...]:
    """The dampers among the connections."""
    return _sortedOf(self)[Damper]

  @property
  def actuators(self, ) -> tuple[Actuator, ...]:
    """The actuators among the connections."""
    return _sortedOf(self)[Actuator]

  @property
  def contacts(self, ) -> tuple[Contact, ...]:
    """The contacts among the connections."""
    return _sortedOf(self)[Contact]

  @property
  def motors(self, ) -> tuple[Motor, ...]:
    """The motors among the connections."""
    return _sortedOf(self)[Motor]

  @property
  def drags(self, ) -> tuple[Drag, ...]:
    """The air's drags among the connections."""
    return _sortedOf(self)[Drag]

  @property
  def cordLines(self, ) -> tuple[CordLine, ...]:
    """The cord lines among the connections."""
    return _sortedOf(self)[CordLine]

  @property
  def airs(self, ) -> tuple[Air, ...]:
    """The airs sealed in among the connections."""
    return _sortedOf(self)[Air]

  @property
  def tyres(self, ) -> tuple[Tyre, ...]:
    """The tyres among the connections."""
    return _sortedOf(self)[Tyre]

  @property
  def crowds(self, ) -> tuple[Crowd, ...]:
    """The crowds among the connections."""
    return _sortedOf(self)[Crowd]

  @property
  def turnPoints(self, ) -> tuple[TurnPoint, ...]:
    """The fourth wall points that turn among the connections."""
    return _sortedOf(self)[TurnPoint]

  @property
  def racks(self, ) -> tuple[RackAndPinion, ...]:
    """The racks and pinions among the connections."""
    return _sortedOf(self)[RackAndPinion]

  @property
  def housed(self, ) -> frozenset:
    """The bodies the ground never meets ('Housed')."""
    return frozenset(h.body for h in _sortedOf(self)[Housed])

  @property
  def meshes(self, ) -> tuple[GearMesh, ...]:
    """The gears meshing among the connections."""
    return _sortedOf(self)[GearMesh]

  @property
  def slides(self, ) -> tuple[Slide, ...]:
    """The sliding joints among the connections."""
    return _sortedOf(self)[Slide]

  @property
  def hinges(self, ) -> tuple[Hinge, ...]:
    """The hinges among the connections."""
    return _sortedOf(self)[Hinge]

  @property
  def brakes(self, ) -> tuple[DiscBrake, ...]:
    """The disc brakes among the connections."""
    return _sortedOf(self)[DiscBrake]

  @property
  def rams(self, ) -> tuple[Ram, ...]:
    """The hydraulic rams among the connections."""
    return _sortedOf(self)[Ram]

  @property
  def humps(self, ) -> tuple[Humps, ...]:
    """The humps bolted on among the connections."""
    return _sortedOf(self)[Humps]

  @property
  def fixed(self, ) -> frozenset[int]:
    """The bodies made part of the world ('Fixed')."""
    return frozenset(fixed.body for fixed in _sortedOf(self)[Fixed])


#  An assembly never changes, so its connections are sorted by kind once
#  for each of the last few assemblies and kept, each with its assembly.
_SORTED: list = []


def _sortedOf(assembly: Assembly) -> dict[type, tuple]:
  """Returns the connections of 'assembly' by kind, in their order,
  sorting them only when it was not lately."""
  for at, (kept, sorted_) in enumerate(_SORTED):
    if kept is assembly:
      if at:
        _SORTED.insert(0, _SORTED.pop(at))
      return sorted_
  sorted_ = {kind: tuple(c for c in assembly.connections
                         if isinstance(c, kind))
             for kind in (Tie, Weld, Spring, Damper, Actuator, Contact,
                          Motor, Drag, Fixed, CordLine, Air, Crowd,
                          Tyre, DiscBrake, Hinge, Slide, TurnPoint,
                          RackAndPinion, GearMesh, Housed, Ram,
                          Humps)}
  _SORTED.insert(0, (assembly, sorted_))
  del _SORTED[8:]
  return sorted_
