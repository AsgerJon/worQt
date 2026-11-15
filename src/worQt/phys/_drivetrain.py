"""
The drivetrain (user, 2026-11-14: "you start work on the differential
and the stick shift gearbox and clutch ... *one* note on the gear box
is dog-leg: For a 5 gear stick shift a dog-leg has the following
layout: R-2-4 / 1-3-5"; their picture: an open metal gate, the
Countach's and the 348's), built of its parts in the small steps, on a
bench: an engine (its flywheel turned by its crank's torque, the
roadster's curve times the throttle: the one stand-in, combustion);
the clutch (a lined disc on the gearbox's input shaft, clamped to the
flywheel by the pressure plate's spring, let go by the pedal: friction,
slipping or holding, as a disc brake's pads, 'DiscBrake' between two
turning bodies); a two-shaft gearbox as a transaxle's (an input shaft
with its five gears and reverse's cut on it, an output shaft below with
five gears turning free on it, each in constant mesh with its partner,
'GearMesh'; reverse through an idler), each free gear locked to the
output shaft by its dogs once its synchro's cone, pressed by the
driver's hand through the stick and the fork, has brought it to the
shaft's speed (the cone friction; the dogs a lock, both 'DiscBrake's
between the gear and the shaft); the stick in a dog-leg gate
('Shifter': R, 2, 4 forward, 1, 3, 5 back, the hand moving it as the
gate lets it, to the neutral row, across, then in, held at the synchro
until it is in); the output shaft's pinion turning the crown wheel on
the differential's carrier, two spider gears on the carrier between
the two side gears (bevel gears, 'GearMesh'), each side gear on a half
shaft to a wheel (the soapbox's), braked. The gearbox's case in glass.

The bench's frame: x forward (the engine ahead, the differential
behind), y left, z up from the floor; every shaft built in it as is
(its own frame the bench's), the half shafts in their wheels' (z out
along the axle).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._assembly import Assembly, BrakeLine, Contact, DiscBrake, Drive
from ._assembly import Fixed, GearMesh, Hinge, Housed, Motor
from ._axle import _summed
from ._body import Body, State
from ._brakes import DISC_AT, DISC_INNER, DISC_OUTER, PAD_RADIUS
from ._brakes import brakedWheel
from ._gearbox import engineTorque
from ._gears import rootOf, spurGear
from ._shape import Shape, cylinderShape
from ._turned import Turned
from ._tyred import _WALKER_ON_RUBBER, _loop
from ._vectors import Vector, plus, rotated, turnAbout

STEEL = 7850.0
X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
#  The gearbox: its gears' module, m; each forward gear's teeth on the
#  input shaft and on the output (every pair as far apart: 59 teeth
#  together, 88.5 mm between the shafts; each pair's counts sharing no
#  factor, every tooth meeting every other in turn), first to fifth
#  (ratios 3.21, 2.11, 1.46, 1.19, 0.90); reverse's: the input's, the
#  idler's, the output's (2.93... the idler turns it back: 41/13 = 3.15);
#  the gears' width along the shafts, m, and where along x each pair
#  is, first to fifth, then reverse.
MODULE = 0.003
GEARS = ((14, 45), (19, 40), (24, 35), (27, 32), (31, 28))
REVERSE = (13, 23, 41)
GEAR_WIDTH = 0.018
GEAR_AT = (-0.02, 0.04, 0.10, 0.16, 0.22, -0.08)
#  The final drive: the pinion's and the crown wheel's teeth, their
#  module, m; the differential's side gears' and spiders' teeth, module.
FINAL = (11, 41)
FINAL_MODULE = 0.004
SIDE, SPIDER = 17, 11
DIFF_MODULE = 0.003
#  Where things are on the bench, m: the input shaft's (and the
#  engine's) axis' height; the output shaft's under it; the flywheel's
#  and the clutch disc's places along x; the differential's apex (where
#  the pinion's and the crown wheel's axes meet) along x; the wheels'
#  middles out either side.
SHAFT_HEIGHT = 0.70
CENTRES = 0.5 * MODULE * (GEARS[0][0] + GEARS[0][1])
OUTPUT_HEIGHT = SHAFT_HEIGHT - CENTRES
FLYWHEEL_AT, CLUTCH_AT = 0.44, 0.41
APEX = -0.50
WHEEL_OUT = 0.75
#  The clutch: its lined disc's inner and outer radii, m; its lining's
#  friction; the pressure plate's spring's clamp, N (holding 2 x 0.3 x
#  5000 N at 9 cm: 270 N m, the engine's most 205); how far down the
#  pedal is when it starts to let go and when it has (shares of its
#  travel); how fast the foot pushes it down and lets it up, travels a
#  second.
CLUTCH_INNER, CLUTCH_OUTER, LINING = 0.07, 0.115, 0.3
CLAMP = 5000.0
BITE, FREE = 0.3, 0.8
PEDAL_DOWN, PEDAL_UP = 8.0, 1.0
#  The synchros: their cones' radius, m; the hand's push on the knob, N,
#  times the stick's and fork's leverage, the cone's friction over the
#  sine of its half angle: the cone's twist, N m (an 80 N push: 28 N m);
#  the dogs' hold, N m (all the teeth can take); how close the gear's
#  speed must come to the shaft's for the blocker ring to let the sleeve
#  through, rad/s.
CONE = 0.04
HAND, LEVER, CONE_GRIP = 80.0, 5.0, 0.1 / math.sin(math.radians(6.5))
SYNC = HAND * LEVER * CONE_GRIP * CONE
DOGS = 4e4
SYNCED = 2.0
#  The engine: its idle and its limiter, revolutions a minute; what it
#  loses turning (friction and pumping: N m, and N m a revolution a
#  minute more); its idle governor (how much throttle a revolution a
#  minute short of idle opens, and its most); when it stalls, rpm; its
#  starter's twist, N m, until it runs at 'CATCH' rpm; how fast the
#  foot opens and closes the throttle, a second.
IDLE, REDLINE = 850.0, 7500.0
DRAG, DRAG_RPM = 15.0, 0.0045
GOVERNOR, GOVERNOR_MOST = 1.0 / 400.0, 0.35
STALL, STARTER, CATCH = 250.0, 60.0, 600.0
THROTTLE_OPEN, THROTTLE_CLOSE = 5.0, 8.0
#  The dog-leg gate (user: "R-2-4 / 1-3-5"): each gear's place, (its
#  plane across, left to right, -1, 0, 1; its throw, forward 1, back
#  -1); neutral in the middle plane; how far the hand moves the stick a
#  second (a whole throw or a plane across); where along a throw the
#  synchro's blocker holds the sleeve; how near it counts as there.
GATE = {'R': (-1, 1), '1': (-1, -1), '2': (0, 1), '3': (0, -1),
        '4': (1, 1), '5': (1, -1)}
STICK_RATE = 7.0
BLOCKER = 0.55
#  The bodies: the walker, the frame (the engine's block, the stands),
#  the gearbox's case (glass), the flywheel, the input shaft, the output
#  shaft, the free gears first to fifth and reverse, the idler, the
#  differential's carrier, its two spiders, the half shafts with their
#  wheels (left, right).
FRAME, CASE, FLYWHEEL, INPUT, OUTPUT = 1, 2, 3, 4, 5
FIRST_GEAR = 6
REVERSE_GEAR, IDLER, CARRIER = 11, 12, 13
SPIDERS = (14, 15)
HALVES = (16, 17)
NAMES = ('1', '2', '3', '4', '5', 'R')
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)


class DrivetrainLayout(NamedTuple):
  """
  DrivetrainLayout is where a drivetrain's bodies are in its assembly:
  the flywheel, the input shaft, the output shaft, the first free gear
  (then second to fifth and reverse), the carrier, and the wheels the
  differential drives (left, right) with their axles (each in its own
  frame, out along the axle).
  """

  flywheel: int
  input: int
  output: int
  firstGear: int
  carrier: int
  left: int
  right: int
  leftAxle: Vector
  rightAxle: Vector


class DrivetrainControls:
  """
  DrivetrainControls are what the driver works and what works for them:
  the throttle the foot asks for ('throttle', 0 to 1) and opens
  ('open'; and as the engine has it, the idle governor's too, none past
  the limiter: 'effective', what its sound hears), the clutch pedal
  asked ('pedal', 0 up to 1 down) and where it is ('pressed'), the gear
  asked ('asked': 'N', 'R', '1' to '5';
  the hand moves the stick there), whether the starter is asked
  ('starting'); the engine's drive (its crank's torque, 'engine'), the
  clutch's line (its spring's clamp, N: 'clutch'), each free gear's
  coupling to its shaft (the synchro's cone, then the dogs: 'dogs', in
  'NAMES' order), the wheels' brakes' line ('line', the foot's) and the
  left wheel's own ('held', a test's), the stick ('shifter') and where
  its bodies are ('layout', set by 'addDrivetrain').
  """

  __slots__ = ('throttle', 'open', 'pedal', 'pressed', 'asked',
               'starting', 'running', 'effective', 'engine', 'clutch',
               'dogs', 'line', 'held', 'shifter', 'layout')

  def __init__(self, ) -> None:
    self.layout = None
    self.engine = Drive()
    self.engine.most = 1e4
    self.clutch = BrakeLine(CLAMP)
    self.dogs = tuple(BrakeLine(0.0) for _ in NAMES)
    self.line, self.held = BrakeLine(0.0), BrakeLine(0.0)
    self.shifter = Shifter()
    self.reset()

  def reset(self, ) -> None:
    """The 'reset' method sets everything back as at the start (the
    engine idling in neutral, the clutch in, the feet off, the brakes
    off), keeping its lines and drive (what an assembly holds)."""
    self.throttle, self.open, self.pedal, self.pressed = 0.0, 0.0, 0.0, 0.0
    self.asked, self.starting, self.running = 'N', False, True
    self.effective = 0.0
    self.engine.torque = 0.0
    self.clutch.pressure = CLAMP
    for line in self.dogs + (self.line, self.held):
      line.pressure = 0.0
    self.shifter.across, self.shifter.throw = 0.0, 0.0
    self.shifter.engaged, self.shifter.blocked = None, None


class Shifter:
  """
  Shifter is the gear stick in its dog-leg gate ('GATE'): where it is
  across ('across': the plane, -1 left, 0 middle, 1 right) and along
  its throw ('throw': 1 forward, -1 back, 0 the neutral row), the gear
  whose dogs are in ('engaged': a name in 'NAMES', or None) and whether
  the hand is held at a synchro ('blocked', the gear's name). The hand
  moves it toward the gear asked as the gate lets it: back to the
  neutral row, across to its plane, then along its throw; at
  'BLOCKER' the synchro's blocker ring holds the sleeve while the cone
  brings the gear to the shaft's speed, then the dogs go in.
  """

  __slots__ = ('across', 'throw', 'engaged', 'blocked')

  def __init__(self, ) -> None:
    self.across, self.throw = 0.0, 0.0
    self.engaged, self.blocked = None, None

  def gearAt(self, ) -> str | None:
    """The 'gearAt' method returns the gear the stick is toward (the one
    of its plane on its throw's side), None in the neutral row."""
    if abs(self.throw) < 0.05:
      return None
    plane = round(self.across)
    for name, (at, way) in GATE.items():
      if at == plane and way == (1 if self.throw > 0.0 else -1):
        return name
    return None

  def moved(self, asked: str, seconds: float, slips: dict) -> None:
    """The 'moved' method moves the stick toward 'asked' ('N' or a
    'GATE' name) for 'seconds', as the gate and the synchros let it
    ('slips': each gear's speed on the output shaft, rad/s): out of a
    gear to the neutral row, across, then in, held at 'BLOCKER' until
    its gear's slip is under 'SYNCED' (then its dogs are in)."""
    plane, way = GATE.get(asked, (0, 0))
    step = STICK_RATE * seconds
    self.blocked = None
    if abs(self.across - plane) > 1e-6 and asked != 'N' or (
        asked == 'N' and abs(self.throw) > 1e-6):
      if abs(self.throw) > 1e-6:
        self.throw = _toward(self.throw, 0.0, step)
      else:
        self.across = _toward(self.across, plane, step)
    elif asked == 'N':
      self.across = _toward(self.across, 0.0, step)
    else:
      self.throw = _toward(self.throw, float(way), step)
    gear = self.gearAt()
    if gear is None or abs(self.throw) < BLOCKER:
      self.engaged = None
      return
    if self.engaged == gear:
      return
    if abs(slips.get(gear, 0.0)) <= SYNCED:
      self.engaged = gear
      return
    self.blocked = gear
    self.throw = math.copysign(BLOCKER, self.throw)


def _toward(value: float, goal: float, step: float) -> float:
  """Returns 'value' moved toward 'goal' by no more than 'step'."""
  return value + max(-step, min(step, goal - value))


def engineTwist(rpm: float, open_: float, running: bool,
                starting: bool) -> float:
  """The 'engineTwist' function returns the twist the engine puts on its
  flywheel at 'rpm', its throttle 'open_' (0 to 1), N m: running, its
  full-load torque ('_gearbox.engineTorque') times the throttle (no
  less than its idle governor opens it; none past 'REDLINE': the
  limiter), less what it loses turning; stalled, only its losses (and
  the starter's twist while 'starting', under 'CATCH')."""
  losses = math.copysign(DRAG + DRAG_RPM * abs(rpm), rpm) if abs(
    rpm) > 1.0 else 0.0
  if not running:
    return (STARTER if starting and rpm < CATCH else 0.0) - losses
  governed = min(GOVERNOR_MOST, max(0.0, (IDLE - rpm) * GOVERNOR))
  opened = max(open_, governed)
  if rpm >= REDLINE:
    opened = 0.0
  return opened * engineTorque(rpm) - losses


def spinAbout(state: State, axis: Vector) -> float:
  """Returns how fast the body in 'state' spins about 'axis' (a unit in
  its own frame), rad/s."""
  way = rotated(state.turn, axis)
  return sum(a * b for a, b in zip(state.spin, way))


def drivetrainWorked(controls: DrivetrainControls, states: tuple,
                     seconds: float) -> None:
  """The 'drivetrainWorked' function works the drivetrain for the next
  'seconds' as the driver asks, the bodies as 'states' have them: the
  foot opens or closes the throttle and pushes or lets up the clutch
  (at their rates), the clutch's clamp follows the pedal, the engine
  twists its flywheel ('engineTwist'; stalling under 'STALL', caught by
  the starter at 'CATCH'), the hand moves the stick ('Shifter.moved'),
  each free gear's coupling then its synchro's cone (the gear the stick
  is held at), its dogs (the gear in) or nothing."""
  c = controls
  c.open = _toward(c.open, c.throttle, (
    THROTTLE_OPEN if c.throttle > c.open else THROTTLE_CLOSE) * seconds)
  c.pressed = _toward(c.pressed, c.pedal, (
    PEDAL_DOWN if c.pedal > c.pressed else PEDAL_UP) * seconds)
  c.clutch.pressure = CLAMP * min(1.0, max(0.0, (FREE - c.pressed) / (
    FREE - BITE)))
  bodies = c.layout
  rpm = spinAbout(states[bodies.flywheel], X) * 60.0 / (2.0 * math.pi)
  if c.running and rpm < STALL:
    c.running = False
  if not c.running and c.starting and rpm >= CATCH:
    c.running, c.starting = True, False
  c.engine.torque = engineTwist(rpm, c.open, c.running, c.starting)
  governed = min(GOVERNOR_MOST, max(0.0, (IDLE - rpm) * GOVERNOR))
  c.effective = 0.0 if not c.running or rpm >= REDLINE else max(
    c.open, governed)
  shaft = spinAbout(states[bodies.output], X)
  slips = {name: spinAbout(states[bodies.firstGear + k], X) - shaft
           for k, name in enumerate(NAMES)}
  c.shifter.moved(c.asked, seconds, slips)
  for name, line in zip(NAMES, c.dogs):
    line.pressure = (DOGS if c.shifter.engaged == name else SYNC
                     if c.shifter.blocked == name else 0.0) / CONE


def rpmOf(states: tuple, flywheel: int = FLYWHEEL) -> float:
  """The 'rpmOf' function returns the engine's revolutions a minute (its
  flywheel body 'flywheel')."""
  return spinAbout(states[flywheel], X) * 60.0 / (2.0 * math.pi)


def _onX(shape: Shape, at: float, height: float) -> Shape:
  """Returns 'shape' (turned about its own z) turned to turn about x,
  its middle at 'at' along x, 'height' up, on the bench's middle."""
  return shape.moved((at, 0.0, height), turnAbout(Y, 0.5 * math.pi))


def _cylinderX(radius: float, low: float, high: float,
               height: float) -> Shape:
  """Returns a cylinder about x from 'low' to 'high' along it, 'radius'
  m, 'height' up."""
  return cylinderShape(radius, high - low, 32).moved(
    (0.5 * (low + high), 0.0, height), turnAbout(Z, -0.5 * math.pi))


def gearShape(teeth: int, module: float = MODULE,
              width: float = GEAR_WIDTH) -> Shape:
  """The 'gearShape' function returns a spur gear of 'teeth' at
  'module', 'width' wide, about its own z, on its hub."""
  root = rootOf(module, teeth)
  return spurGear(module, teeth, width, root - 0.002, root, 3, 24)


def _box(low: Vector, high: Vector) -> Shape:
  """Returns a box from corner 'low' to corner 'high'."""
  from ._rig import _box as box
  return box(low, high)


def _joined(shapes: tuple) -> Shape:
  """Returns 'shapes' as one."""
  shape = shapes[0]
  for piece in shapes[1:]:
    shape = shape.joined(piece)
  return shape


def flywheelPieces(reach: float = 0.0) -> tuple[tuple[str, Shape], ...]:
  """The 'flywheelPieces' function returns the flywheel by its parts,
  'reach' m further ahead than on the bench (a car's engine ahead of its
  gearbox: 'addDrivetrain'): ('flywheel', its disc, 28 cm across, with
  the crank's snout), ('cover', the clutch's cover over the pressure
  plate, on it)."""
  at, clutch = FLYWHEEL_AT + reach, CLUTCH_AT + reach
  disc = _cylinderX(0.14, at - 0.015, at + 0.015, SHAFT_HEIGHT)
  snout = _cylinderX(0.03, at + 0.015, at + 0.06, SHAFT_HEIGHT)
  cover = _cylinderX(0.13, clutch - 0.025, clutch - 0.008, SHAFT_HEIGHT)
  return ('flywheel', _joined((disc, snout))), ('cover', cover)


def inputPieces(reach: float = 0.0) -> tuple[tuple[str, Shape], ...]:
  """The 'inputPieces' function returns the input shaft by its parts,
  reaching 'reach' m further ahead than on the bench to its clutch (a
  car's propshaft, the engine ahead of the gearbox): ('shaft', the shaft
  from the flywheel's pilot back through the box), ('lining', the
  clutch's disc), ('gear', its gears cut on it: first to fifth,
  reverse)."""
  clutch = CLUTCH_AT + reach
  shaft = _cylinderX(0.0125, -0.12, FLYWHEEL_AT + reach - 0.016,
                     SHAFT_HEIGHT)
  disc = _cylinderX(CLUTCH_OUTER, clutch - 0.004, clutch + 0.004,
                    SHAFT_HEIGHT)
  teeth = tuple(pair[0] for pair in GEARS) + (REVERSE[0],)
  gears = tuple(_onX(gearShape(count), at, SHAFT_HEIGHT)
                for count, at in zip(teeth, GEAR_AT))
  return ('shaft', shaft), ('lining', disc), ('gear', _joined(gears))


def outputPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'outputPieces' function returns the output shaft by its parts:
  ('shaft', the shaft, its synchros' hubs), ('pinion', the final
  drive's pinion at its back end)."""
  pinion = APEX + 0.5 * FINAL_MODULE * FINAL[1]
  shaft = _cylinderX(0.015, pinion + 0.02, 0.27, OUTPUT_HEIGHT)
  hubs = tuple(_cylinderX(CONE, at - 0.5 * GEAR_WIDTH - 0.012,
                          at - 0.5 * GEAR_WIDTH - 0.002, OUTPUT_HEIGHT)
               for at in GEAR_AT)
  gear = _onX(gearShape(FINAL[0], FINAL_MODULE, 0.03), pinion,
              OUTPUT_HEIGHT)
  return ('shaft', _joined((shaft,) + hubs)), ('pinion', gear)


def _freeGear(k: int) -> Shape:
  """Returns free gear 'k' (first to fifth, then reverse) on the output
  shaft."""
  teeth = GEARS[k][1] if k < 5 else REVERSE[2]
  return _onX(gearShape(teeth), GEAR_AT[k], OUTPUT_HEIGHT)


def idlerAt() -> Vector:
  """The 'idlerAt' function returns where reverse's idler's middle is:
  in mesh with the input's reverse gear and the output's, beside them
  (left)."""
  a = 0.5 * MODULE * (REVERSE[0] + REVERSE[1])
  b = 0.5 * MODULE * (REVERSE[1] + REVERSE[2])
  d = SHAFT_HEIGHT - OUTPUT_HEIGHT
  down = (a * a - b * b + d * d) / (2.0 * d)
  return (GEAR_AT[5], math.sqrt(a * a - down * down), SHAFT_HEIGHT - down)


def idlerShape() -> Shape:
  """The 'idlerShape' function returns reverse's idler."""
  at = idlerAt()
  return gearShape(REVERSE[1]).moved(at, turnAbout(Y, 0.5 * math.pi))


def carrierPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'carrierPieces' function returns the differential's carrier by
  its parts: ('carrier', its case about the axle, the spiders' pin),
  ('crown', the crown wheel bolted to it on the left of the apex: there
  first gear drives the wheels forward; on the right it drove them
  backward, the bench's sign as wrong as the gearbox, unseen till the
  real car backed away from its first launch)."""
  apex = (APEX, 0.0, OUTPUT_HEIGHT)
  case = cylinderShape(0.06, 0.09, 32).moved(apex, (1.0, 0.0, 0.0, 0.0))
  pin = _box((APEX - 0.008, -0.008, OUTPUT_HEIGHT - 0.045),
             (APEX + 0.008, 0.008, OUTPUT_HEIGHT + 0.045))
  crown = gearShape(FINAL[1], FINAL_MODULE, 0.02).moved(
    (APEX, 0.5 * FINAL_MODULE * FINAL[0] + 0.01, OUTPUT_HEIGHT),
    turnAbout(X, 0.5 * math.pi))
  return ('carrier', _joined((case, pin))), ('crown', crown)


def spiderShape(up: float) -> Shape:
  """The 'spiderShape' function returns a spider gear, above the apex
  ('up' 1) or under it (-1), turning about z."""
  return gearShape(SPIDER, DIFF_MODULE, 0.012).moved(
    (APEX, 0.0, OUTPUT_HEIGHT + up * 0.5 * DIFF_MODULE * SIDE),
    (1.0, 0.0, 0.0, 0.0))


def halfProfile() -> tuple:
  """The 'halfProfile' function returns a half shaft with its side gear
  as a turned profile in its wheel's frame (z out along the axle from
  the wheel's middle): the side gear at its inner end, the shaft out
  to the hub."""
  inner = -(WHEEL_OUT - 0.5 * DIFF_MODULE * SPIDER)
  gear = 0.5 * DIFF_MODULE * SIDE
  return _loop([(0.0, inner - 0.006), (gear, inner - 0.006),
                (gear, inner + 0.006), (0.016, inner + 0.006),
                (0.016, -0.06), (0.0, -0.06)])


@functools.lru_cache(maxsize=1)
def halfBody() -> Body:
  """The 'halfBody' function returns a half shaft with its side gear and
  its wheel (the soapbox's: rim, tyre, disc), in the wheel's frame; its
  shape the wheel's."""
  wheel = brakedWheel()
  shaft = Body.of(Turned(halfProfile(), 24), STEEL)
  return _summed((wheel, shaft), wheel.shape)


def framePieces() -> tuple[tuple[str, Shape], ...]:
  """The 'framePieces' function returns the bench's frame by its parts:
  ('block', the engine's block before the flywheel), ('stand', its
  stands and the floor plate)."""
  block = _box((FLYWHEEL_AT + 0.06, -0.22, SHAFT_HEIGHT - 0.25),
               (FLYWHEEL_AT + 0.66, 0.22, SHAFT_HEIGHT + 0.30))
  plate = _box((APEX - 0.4, -WHEEL_OUT - 0.2, 0.0),
               (FLYWHEEL_AT + 0.75, WHEEL_OUT + 0.2, 0.02))
  stands = [_box((FLYWHEEL_AT + 0.2, -0.15, 0.02),
                 (FLYWHEEL_AT + 0.5, 0.15, SHAFT_HEIGHT - 0.25))]
  for side in (-1.0, 1.0):
    y = side * (WHEEL_OUT - 0.25)
    stands.append(_box((APEX - 0.04, y - 0.04, 0.02),
                       (APEX + 0.04, y + 0.04, OUTPUT_HEIGHT - 0.02)))
  stands.append(_box((-0.05, -0.15, 0.02),
                     (0.05, 0.15, OUTPUT_HEIGHT - 0.10)))
  return ('block', block), ('stand', _joined((plate,) + tuple(stands)))


def casePieces(reach: float = 0.0) -> tuple[tuple[str, Shape], ...]:
  """The 'casePieces' function returns the gearbox's case and the bell
  housing (glass; the bell 'reach' m further ahead than on the bench,
  at the engine), and the differential's housing, by their parts
  ('case')."""
  bell = _box((CLUTCH_AT + reach - 0.04, -0.17, SHAFT_HEIGHT - 0.17),
              (FLYWHEEL_AT + reach + 0.05, 0.17, SHAFT_HEIGHT + 0.16))
  box = _box((-0.13, -0.10, OUTPUT_HEIGHT - 0.09),
             (0.28, 0.10, SHAFT_HEIGHT + 0.07))
  diff = _box((APEX - 0.11, -0.15, OUTPUT_HEIGHT - 0.11),
              (APEX + 0.13, 0.12, OUTPUT_HEIGHT + 0.11))
  return (('case', bell), ('case', box), ('case', diff))


def _bodyOf(pieces: tuple) -> Body:
  """Returns the steel body of 'pieces' ((key, shape), ...)."""
  return Body.of(_joined(tuple(shape for _, shape in pieces)), STEEL)


@functools.lru_cache(maxsize=1)
def benchBodies() -> tuple[Body, ...]:
  """The 'benchBodies' function returns the bench's bodies from the
  frame on ('FRAME' first), each in the bench's frame but the half
  shafts (in their wheels')."""
  from ._scenes import WALKER
  bodies = [WALKER.body(), _bodyOf(framePieces()), _bodyOf(casePieces()),
            _bodyOf(flywheelPieces()), _bodyOf(inputPieces()),
            _bodyOf(outputPieces())]
  bodies += [Body.of(_freeGear(k), STEEL) for k in range(6)]
  bodies += [Body.of(idlerShape(), STEEL), _bodyOf(carrierPieces()),
             Body.of(spiderShape(1.0), STEEL),
             Body.of(spiderShape(-1.0), STEEL), halfBody(), halfBody()]
  return tuple(bodies)


def wheelTurn(side: float) -> tuple:
  """The 'wheelTurn' function returns how a wheel (or half shaft) on
  'side' (left 1) lies: its own z out along the axle."""
  return turnAbout(X, -side * 0.5 * math.pi)


@functools.lru_cache(maxsize=4)
def drivetrainBodies(shift: Vector,
                     reach: float = 0.0) -> tuple[Body, ...]:
  """The 'drivetrainBodies' function returns the drivetrain's bodies
  moved 'shift' from the bench (the flywheel and the clutch 'reach' m
  further ahead, the input shaft reaching them): the flywheel, the input
  shaft, the output shaft, the free gears first to fifth and reverse,
  the idler, the carrier, its spiders (above, under)."""

  def moved(pieces: tuple) -> Body:
    """Returns the steel body of 'pieces', moved."""
    return Body.of(_joined(tuple(shape.moved(shift, (1.0, 0.0, 0.0, 0.0))
                                 for _, shape in pieces)), STEEL)

  return ((moved(flywheelPieces(reach)), moved(inputPieces(reach)),
           moved(outputPieces()))
          + tuple(moved((('gear', _freeGear(k)),)) for k in range(6))
          + (moved((('gear', idlerShape()),)), moved(carrierPieces()),
             moved((('gear', spiderShape(1.0)),)),
             moved((('gear', spiderShape(-1.0)),))))


def addDrivetrain(controls: DrivetrainControls, shift: Vector, frame: int,
                  case: int, first: int, sides: tuple, sideAxes: tuple,
                  world: object, turn: tuple, idle: float, bodies: list,
                  states: list, connections: list,
                  reach: float = 0.0) -> None:
  """The 'addDrivetrain' function adds the drivetrain, moved 'shift' from
  the bench (its frame's points; 'world' puts them in the world, turned
  'turn'), to 'bodies', 'states' and 'connections', worked by
  'controls' (its 'layout' set): its bodies from 'first' on
  ('drivetrainBodies'), the shafts and the carrier hinged in body
  'frame', the gears meshing in body 'case' (the bench's case; a car's
  chassis), the engine twisting the flywheel against 'frame', the
  clutch, each free gear's synchro and dogs (every one of them housed:
  the ground never meets them), the spiders meshing the
  side gears (bodies 'sides', left and right, their axes 'sideAxes' in
  their own frames, out from the differential's middle); the engine
  turning at 'idle' rpm in neutral, the clutch in; the flywheel and
  the clutch 'reach' m further ahead than on the bench, the input shaft
  reaching forward to them (a front engine's propshaft: user,
  2026-11-15, "Move the seat back, front engine")."""
  flywheel, inputShaft, output = first, first + 1, first + 2
  firstGear, idler, carrier = first + 3, first + 9, first + 10
  spiders = (first + 11, first + 12)
  controls.layout = DrivetrainLayout(flywheel, inputShaft, output,
                                     firstGear, carrier, sides[0],
                                     sides[1], sideAxes[0], sideAxes[1])
  made = drivetrainBodies(shift, reach)
  spin = idle * 2.0 * math.pi / 60.0
  inputs = tuple(pair[0] for pair in GEARS) + (REVERSE[0],)
  outputs = tuple(pair[1] for pair in GEARS) + (REVERSE[2],)
  turning = [spin, spin, 0.0]
  turning += [-spin * inputs[k] / outputs[k] for k in range(5)]
  turning += [spin * REVERSE[0] / REVERSE[2],
              -spin * REVERSE[0] / REVERSE[1], 0.0, 0.0, 0.0]
  connections += [Housed(first + k) for k in range(len(made))]
  for body, about in zip(made, turning):
    bodies.append(body)
    states.append(State(world(body.centre), turn, (0.0, 0.0, 0.0),
                        rotated(turn, (about, 0.0, 0.0))))

  def at(point: Vector) -> Vector:
    """Returns the bench's 'point' moved 'shift'."""
    return plus(point, shift)

  apex = at((APEX, 0.0, OUTPUT_HEIGHT))
  connections += [
    Hinge(frame, at((FLYWHEEL_AT + reach, 0.0, SHAFT_HEIGHT)), X,
          flywheel, at((FLYWHEEL_AT + reach, 0.0, SHAFT_HEIGHT)), X),
    Hinge(frame, at((0.0, 0.0, SHAFT_HEIGHT)), X, inputShaft,
          at((0.0, 0.0, SHAFT_HEIGHT)), X),
    Hinge(frame, at((0.0, 0.0, OUTPUT_HEIGHT)), X, output,
          at((0.0, 0.0, OUTPUT_HEIGHT)), X),
    Motor(frame, flywheel, X, controls.engine),
    DiscBrake(inputShaft, flywheel, at((CLUTCH_AT + reach, 0.0,
                                         SHAFT_HEIGHT)), X,
              at((CLUTCH_AT + reach, 0.0, SHAFT_HEIGHT + 0.5 * (
                CLUTCH_INNER + CLUTCH_OUTER))), CLUTCH_INNER, CLUTCH_OUTER,
              controls.clutch, 1.0, LINING)]
  for k in range(6):
    gear, middle = firstGear + k, at((GEAR_AT[k], 0.0, OUTPUT_HEIGHT))
    connections.append(Hinge(case, middle, X, gear, middle, X))
    connections.append(DiscBrake(gear, output, middle, X, at((
      GEAR_AT[k], 0.0, OUTPUT_HEIGHT + CONE)), 0.5 * CONE, 1.5 * CONE,
      controls.dogs[k], 1.0, 0.5))
    if k < 5:
      connections.append(GearMesh(inputShaft, X, inputs[k], gear, X,
                                  outputs[k], case))
  idled = at(idlerAt())
  connections += [
    Hinge(frame, idled, X, idler, idled, X),
    GearMesh(inputShaft, X, REVERSE[0], idler, X, REVERSE[1], case),
    GearMesh(idler, X, REVERSE[1], firstGear + 5, X, REVERSE[2], case),
    Hinge(frame, apex, Y, carrier, apex, Y),
    GearMesh(output, X, FINAL[0], carrier, (0.0, 1.0, 0.0), FINAL[1],
             case, False, FINAL_MODULE)]
  for spider, up in zip(spiders, (1.0, -1.0)):
    pin = plus(apex, (0.0, 0.0, up * 0.5 * DIFF_MODULE * SIDE))
    connections.append(Hinge(carrier, pin, Z, spider, pin, Z))
    for side, axis in zip(sides, sideAxes):
      connections.append(GearMesh(side, axis, SIDE, spider, (0.0, 0.0, up),
                                  SPIDER, carrier, False, DIFF_MODULE))


def drivetrainBench(controls: DrivetrainControls,
                    idle: float = IDLE) -> tuple[Assembly, tuple]:
  """The 'drivetrainBench' function returns the drivetrain on its bench
  worked by 'controls': the walker (body 0) beside it, the frame (1)
  and the case (2), both part of the world, the flywheel (3), the input
  shaft (4), the output shaft (5), the free gears first to fifth (6 to
  10) and reverse (11), the idler (12), the carrier (13), its spiders
  (14 above, 15 under), the half shafts with their wheels (16 left, 17
  right); the engine turning at 'idle' rpm in neutral, the clutch in
  (the input shaft and its gears turning with it), all else still."""
  made = benchBodies()
  bodies = list(made[:CASE + 1])
  states = [State((APEX + 0.3, -WHEEL_OUT - 0.6, 0.02 + 0.3)),
            State(made[FRAME].centre), State(made[CASE].centre)]
  connections = [Fixed(FRAME), Fixed(CASE)]
  addDrivetrain(controls, (0.0, 0.0, 0.0), FRAME, CASE, FLYWHEEL, HALVES,
                (Z, Z), lambda point: point, (1.0, 0.0, 0.0, 0.0), idle,
                bodies, states, connections)
  for side in (1.0, -1.0):
    turn = wheelTurn(side)
    middle = (APEX, side * WHEEL_OUT, OUTPUT_HEIGHT)
    bodies.append(halfBody())
    states.append(State(plus(middle, rotated(turn, halfBody().centre)),
                        turn))
  for half, side in zip(HALVES, (1.0, -1.0)):
    middle = (APEX, side * WHEEL_OUT, OUTPUT_HEIGHT)
    connections.append(Hinge(FRAME, middle, (0.0, side, 0.0), half,
                             (0.0, 0.0, 0.0), Z))
    pad = (APEX - PAD_RADIUS, side * (WHEEL_OUT + DISC_AT), OUTPUT_HEIGHT)
    lines = (controls.line, controls.held) if side > 0.0 else (
      controls.line,)
    for line in lines:
      connections.append(DiscBrake(half, None, (0.0, 0.0, DISC_AT), Z, pad,
                                   DISC_INNER, DISC_OUTER, line))
  connections += [Contact(0, k, *_WALKER_ON_STEEL) for k in (FRAME, CASE)]
  connections += [Contact(0, k, *_WALKER_ON_RUBBER) for k in HALVES]
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)


def benchFinishes(assembly: Assembly) -> dict:
  """The 'benchFinishes' function returns how the bench's bodies are
  drawn, by index: by their parts (the case as it is: glass); the half
  shafts as the wheel is (rim, tyre, disc) and their shafts turned
  ('shaft')."""
  from ._brakes import discRuns
  from ._carcass import rimRuns
  from ._tyred import tyreRuns
  half = rimRuns() + tyreRuns() + discRuns() + (('shaft', halfProfile()),)
  out = {FRAME: framePieces(), FLYWHEEL: flywheelPieces(),
         INPUT: inputPieces(), OUTPUT: outputPieces(),
         IDLER: (('gear', idlerShape()),),
         CARRIER: carrierPieces(), HALVES[0]: half, HALVES[1]: half}
  for k in range(6):
    out[FIRST_GEAR + k] = (('gear', _freeGear(k)),)
  for spider, up in zip(SPIDERS, (1.0, -1.0)):
    out[spider] = (('gear', spiderShape(up)),)
  return out


class Reading(NamedTuple):
  """
  Reading is what the bench reads out: the engine's revolutions a
  minute and its twist, N m; the clutch's slip (the flywheel's speed
  less the input shaft's, rad/s); the stick's gear and where it is; the
  wheels' speeds at the tyre's radius, m/s (left, right; forward
  positive: turning as they would rolling the car along x).
  """

  rpm: float
  twist: float
  slip: float
  gear: str
  across: float
  throw: float
  left: float
  right: float


def readingOf(controls: DrivetrainControls, states: tuple) -> Reading:
  """The 'readingOf' function returns the bench's reading as 'states'
  have it."""
  from ._tyred import tyreOf
  radius = tyreOf(1, 2.3e5).radius
  stick, bodies = controls.shifter, controls.layout
  return Reading(rpmOf(states, bodies.flywheel), controls.engine.torque,
                 spinAbout(states[bodies.flywheel], X)
                 - spinAbout(states[bodies.input], X),
                 stick.engaged or 'N', stick.across, stick.throw,
                 spinAbout(states[bodies.left], bodies.leftAxle) * radius,
                 -spinAbout(states[bodies.right], bodies.rightAxle) * radius)
