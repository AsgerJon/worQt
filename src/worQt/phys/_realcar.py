"""
The real car (user, 2026-11-14: "continue to assemble the real car";
the differential "works and looks awesome!"): every part of it ours,
built whole in the small steps. A mid-engined, rear-driven two seater's
plan: the soapbox's four corners (the tyre rig's double wishbones,
mirrored; the front ones steered by the rack from a short column, the
rear ones held by tie rods, '_soapbox.addCorners', 'addSteering'), the
drivetrain bench's engine, clutch, dog-leg transaxle and differential
('_drivetrain.addDrivetrain') moved so the differential sits on the rear
axle at the wheels' height, the engine ahead of it behind the driver,
everything turning in the chassis; the differential's side gears turning
in its carrier, each driving a half shaft through a constant velocity
joint at either end (a ball joint, 'Tie', and the two shafts' turns
about their own axes held equal, 'GearMesh' one tooth to one, the same
way: swinging across the axis as the wheel rises adds nothing) to its
rear wheel. The engine's block and the gearbox's case are the chassis'
(their mass on it, the engine's twist taken back by it). The driver (the
walker) sits in the tub ahead of the engine. Its brakes have an anti-lock
system and a handbrake on the rear calipers ('Antilock').

The car's frame: x forward (the front axle at nought), y left, z up
from the road under its wheels.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._assembly import Assembly, BrakeLine, Contact, FourthWall, GearMesh
from ._assembly import Hinge, Housed, Tie
from ._body import Body, State
from ._drivetrain import APEX, DIFF_MODULE, OUTPUT_HEIGHT, SIDE, SPIDER
from ._drivetrain import DrivetrainControls, DrivetrainLayout
from ._drivetrain import addDrivetrain, carrierPieces
from ._drivetrain import casePieces, flywheelPieces, framePieces
from ._drivetrain import gearShape, idlerShape, inputPieces, outputPieces
from ._drivetrain import _freeGear, spiderShape
from ._rig import HUB_HEIGHT, STEEL, TIE_INNER, TuneUp, WheelSetup
from ._rig import _box, armPieces, knucklePieces
from ._shape import Shape, cylinderShape
from ._shock import Shock, coilOf
from ._soapbox import WOOD, _cornerBrackets, _joined, _sided, _summed
from ._soapbox import _sidedPieces, _sidedShape, addCorners, addSteering
from ._tyred import _WALKER_ON_RUBBER
from ._vectors import Vector, cross, dot, norm, plus, product, rotated
from ._vectors import scaled, turnAbout

#  The car: its wheelbase, m (the engine and the driver between the
#  axles); its corners, front left, front right, rear left, rear right.
WHEELBASE = 2.8
CORNERS = ((0.0, 1.0), (0.0, -1.0), (-WHEELBASE, 1.0),
           (-WHEELBASE, -1.0))
#  How far the drivetrain bench's parts are moved into the car's frame:
#  the differential's apex onto the rear axle, at the wheels' height.
SHIFT = (-WHEELBASE - APEX, 0.0, HUB_HEIGHT - OUTPUT_HEIGHT)
#  The chassis: its ends, its rails' place across (inner face), height
#  and top, how thick its side plates are, m; its hollow steel's share
#  of solid (rails, brackets: about a fifth); the engine's block's mass
#  (a V12's, its heads and sump, kg) and the gearbox's case's (kg);
#  the driver's tub (its back, front and either side's inner faces, its
#  floor's top) and the driver sat in it (their ball's middle).
NOSE, TAIL = 0.45, -WHEELBASE - 0.45
RAIL_IN, RAIL_LOW, RAIL_TOP, PLATE = 0.27, 0.15, 0.27, 0.004
HOLLOW = 0.2
BLOCK_MASS, CASE_MASS = 230.0, 60.0
TUB_BACK, TUB_FRONT, TUB_SIDE, TUB_FLOOR = -1.10, -0.48, 0.305, 0.165
SEAT = (-0.79, 0.0, TUB_FLOOR + 0.302)
#  The column: how long from its pinion to the steering wheel, m, and how
#  steeply it rises toward the driver.
COLUMN_LENGTH, COLUMN_RISE = 0.42, math.radians(30.0)
#  The shocks: the rig's coil and dampers, stiffer for the engine's
#  weight, their free lengths set so the car rides as built (front,
#  rear: the engine nearer the rear).
FRONT_SHOCK = Shock(1.2e5, 0.2069, 3400.0, 7600.0)
REAR_SHOCK = Shock(1.6e5, 0.2052, 3900.0, 8800.0)
#  The rear half shafts: where their inner joints are out from the
#  car's middle, m (past the differential's housing), where the outer
#  ones are in the wheels' own frames (in from the hub), their radius,
#  m; the joints' coupling's size (the gear rule's pitch, m).
INNER_JOINT, OUTER_JOINT, SHAFT = 0.13, -0.08, 0.014
JOINT_MODULE = 0.05
#  The bodies: the walker, the chassis, the corners (six each), the
#  rack, the column, the drivetrain (thirteen: flywheel to spiders),
#  the side gears (left, right), the half shafts (left, right).
CHASSIS, FIRST_CORNER = 1, 2
RACK, COLUMN = FIRST_CORNER + 24, FIRST_CORNER + 25
FIRST_DRIVE = COLUMN + 1
SIDES = (FIRST_DRIVE + 13, FIRST_DRIVE + 14)
HALVES = (FIRST_DRIVE + 15, FIRST_DRIVE + 16)
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)
#  The brakes' anti-lock system ('Antilock'): a wheel slower than the
#  road under it by 'ABS_SLIP' of its speed (its tyre past its grip,
#  locking) is let go at 'ABS_LET' of the foot's pressure a second, down
#  to 'ABS_LEAST' of it, and taken back at 'ABS_TAKE' a second once it
#  rolls again; under 'ABS_STILL' m/s the foot holds the car as it says
#  (stopped, nothing to lock). The foot pressed hard ('FOOT', Pa: 40 bar
#  already locks a wheel at the real car's grip) and the handbrake's
#  cable on the rear calipers ('HANDBRAKE', Pa: locking them at once at
#  any speed).
ABS_SLIP, ABS_LET, ABS_TAKE, ABS_LEAST, ABS_STILL = 0.15, 12.0, 6.0, 0.1, 1.0
FOOT, HANDBRAKE = 80e5, 150e5


class Antilock:
  """
  Antilock is the real car's anti-lock brakes and handbrake (user,
  2026-11-14: "Key_S: disc-brakes with ABS", "Key_Space: handbrake
  (instantly locks wheels)"): between the foot's line and each corner's
  caliper ('lines', as 'CORNERS': front left, front right, rear left,
  rear right), each wheel's share of the foot's pressure let through
  ('shares'), worked out call by call from how its wheel rolls
  ('worked'), and whether the handbrake is pulled ('pulled': the rear
  calipers squeezed at 'HANDBRAKE' at once, past the anti-lock).
  """

  __slots__ = ('lines', 'shares', 'pulled')

  def __init__(self, ) -> None:
    self.lines = tuple(BrakeLine(0.0) for _ in CORNERS)
    self.shares = [1.0] * len(CORNERS)
    self.pulled = False

  def reset(self, ) -> None:
    """The 'reset' method lets every caliper go, the handbrake down, and
    forgets how the wheels rolled."""
    for line in self.lines:
      line.pressure = 0.0
    self.shares = [1.0] * len(CORNERS)
    self.pulled = False

  def rolling(self, assembly: Assembly, states: tuple,
              corner: int) -> tuple[float, float]:
    """The 'rolling' method returns how fast corner 'corner''s wheel goes
    along its heading over the road, m/s, and how fast its tread goes
    round (its spin about its axle times its tyre's radius), m/s."""
    wheel = FIRST_CORNER + 6 * corner + 3
    state, side = states[wheel], CORNERS[corner][1]
    axle = rotated(state.turn, (0.0, 0.0, 1.0))
    heading = cross(scaled(axle, side), (0.0, 0.0, 1.0))
    size = norm(heading)
    if size <= 0.0:
      return 0.0, 0.0
    radius = next(tyre.radius for tyre in assembly.tyres
                  if tyre.body == wheel)
    return (dot(state.velocity, heading) / size,
            side * dot(state.spin, axle) * radius)

  def worked(self, pressure: float, assembly: Assembly, states: tuple,
             seconds: float) -> None:
    """The 'worked' method sets each caliper's line for the next
    'seconds' from the foot's 'pressure' (Pa), the wheels as 'states'
    have them: a wheel locking ('ABS_SLIP' slower than the road under
    it) let go of, one rolling taken back ('ABS_LET', 'ABS_TAKE',
    'ABS_LEAST'), every one as the foot says once the car is all but
    still ('ABS_STILL'); the rear ones at 'HANDBRAKE' while it is
    pulled."""
    for corner, line in enumerate(self.lines):
      going, rim = self.rolling(assembly, states, corner)
      share = self.shares[corner]
      if abs(going) < ABS_STILL or pressure <= 0.0:
        share = 1.0
      elif rim - going < -ABS_SLIP * abs(going):
        share = max(ABS_LEAST, share - ABS_LET * seconds)
      else:
        share = min(1.0, share + ABS_TAKE * seconds)
      self.shares[corner] = share
      line.pressure = pressure * share
      if self.pulled and CORNERS[corner][0] != 0.0:
        line.pressure = max(line.pressure, HANDBRAKE)


class RealCarControls(NamedTuple):
  """
  RealCarControls are what the driver works: the brakes' line ('line',
  the foot's), the steering wheel ('steer', the hands, rad, left
  positive), the wheels' tune-up ('tune', four), the drivetrain's
  ('drive': the throttle, the clutch, the stick, the starter) and the
  anti-lock system between the foot and the calipers, with the
  handbrake ('brakes': 'Antilock.worked' each call).
  """

  line: BrakeLine
  steer: FourthWall
  tune: TuneUp
  drive: DrivetrainControls
  brakes: Antilock


def _moved(pieces: tuple) -> tuple:
  """Returns the bench's 'pieces' moved into the car's frame."""
  return tuple((key, shape.moved(SHIFT, (1.0, 0.0, 0.0, 0.0)))
               for key, shape in pieces)


def _chassisParts() -> tuple:
  """Returns the chassis' parts by what they are made of, in the car's
  frame: its hollow steel (its rails, cross members, the corners'
  brackets, the rear tie rods', the dash hoop, the rack's housing), its
  plates (the corners' side plates), its plywood (the tub), the
  engine's block, the gearbox's case and the differential's housing."""
  steel = [_box((TAIL, side * RAIL_IN - (0.03 if side > 0.0 else 0.0),
                 RAIL_LOW), (NOSE, side * RAIL_IN + (0.0 if side > 0.0
                                                    else 0.03),
                             RAIL_TOP)) for side in (-1.0, 1.0)]
  steel += [_box((at - 0.04, -RAIL_IN, RAIL_LOW),
                 (at + 0.04, RAIL_IN, RAIL_LOW + 0.06))
            for at in (0.0, -WHEELBASE, TUB_BACK - 0.05)]
  hoop = TUB_FRONT + 0.06
  for side in (-1.0, 1.0):
    steel.append(_box((hoop - 0.02, side * RAIL_IN - 0.015, RAIL_TOP),
                      (hoop + 0.02, side * RAIL_IN + 0.015, 0.62)))
  steel.append(_box((hoop - 0.02, -RAIL_IN, 0.58), (hoop + 0.02, RAIL_IN,
                                                    0.62)))
  steel.append(_box((TIE_INNER[0] - 0.02, -0.24, TIE_INNER[2] - 0.02),
                    (TIE_INNER[0] + 0.02, 0.24, TIE_INNER[2] + 0.02)))
  inner = TIE_INNER
  bracket = _box((inner[0] - 0.02, 0.20, inner[2] - 0.02),
                 (inner[0] + 0.02, inner[1] + 0.01, inner[2] + 0.02))
  plates = []
  for at, side in CORNERS:
    shapes = _cornerBrackets() + ((bracket,) if at != 0.0 else ())
    plates.append(_sidedShape(shapes[0], side, at))
    steel += [_sidedShape(shape, side, at) for shape in shapes[1:]]
  back, front, side = TUB_BACK, TUB_FRONT, TUB_SIDE
  wood = (_box((back - 0.025, -side - 0.025, RAIL_LOW),
               (front + 0.025, side + 0.025, TUB_FLOOR)),
          _box((back - 0.025, -side - 0.025, TUB_FLOOR),
               (back, side + 0.025, 0.70)),
          _box((front, -side - 0.025, TUB_FLOOR),
               (front + 0.025, side + 0.025, 0.45)),
          _box((back, side, TUB_FLOOR), (front, side + 0.025, 0.52)),
          _box((back, -side - 0.025, TUB_FLOOR), (front, -side, 0.52)))
  block = _moved(framePieces())[0][1]
  case = tuple(shape for _, shape in _moved(casePieces()))
  return tuple(steel), tuple(plates), wood, block, case


def chassisPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'chassisPieces' function returns the chassis by its parts, in
  the car's frame: ('frame', its steel), ('wood', the tub), ('block',
  the engine's block), ('case', the gearbox's case and the
  differential's housing: glass, the gears seen turning)."""
  steel, plates, wood, block, case = _chassisParts()
  return (('frame', _joined(steel + plates)), ('wood', _joined(wood)),
          ('block', block), ('case', _joined(case)))


def chassisShape() -> Shape:
  """The 'chassisShape' function returns how the chassis meets the ground
  and the walker, in the car's frame: its rails before and behind the
  tub (a block each), the tub's floor and walls, the engine's block."""
  steel, plates, wood, block, case = _chassisParts()
  half = RAIL_IN + 0.03
  return _joined((_box((TUB_FRONT + 0.025, -half, RAIL_LOW),
                       (NOSE, half, RAIL_TOP)),
                  _box((TAIL, -half, RAIL_LOW),
                       (TUB_BACK - 0.025, half, RAIL_TOP)))
                 + wood + (block,))


@functools.lru_cache(maxsize=1)
def chassisBody() -> Body:
  """The 'chassisBody' function returns the chassis with the engine's
  block and the gearbox's case on it, in the car's frame: its side
  plates solid steel, its rails and brackets hollow ('HOLLOW'), its
  plywood, the block 'BLOCK_MASS' and the case 'CASE_MASS' kg spread
  through them; its shape 'chassisShape'."""
  steel, plates, wood, block, case = _chassisParts()
  joined = _joined(case)
  return _summed(((_joined(steel), STEEL * HOLLOW),
                  (_joined(plates), STEEL), (_joined(wood), WOOD),
                  (block, BLOCK_MASS / block.volume()),
                  (joined, CASE_MASS / joined.volume())), chassisShape())


def sideGearShape(side: float) -> Shape:
  """The 'sideGearShape' function returns a side gear and its stub out
  through the differential's housing to its half shaft's inner joint,
  on 'side' (left 1), in the car's frame."""
  apex = plus((APEX, 0.0, OUTPUT_HEIGHT), SHIFT)
  gear = gearShape(SIDE, DIFF_MODULE, 0.012).moved(
    plus(apex, (0.0, side * 0.5 * DIFF_MODULE * SPIDER, 0.0)),
    turnAbout((1.0, 0.0, 0.0), -side * 0.5 * math.pi))
  low, high = sorted((side * 0.5 * DIFF_MODULE * SPIDER,
                      side * INNER_JOINT))
  stub = cylinderShape(SHAFT + 0.004, high - low, 24).moved(
    (apex[0], 0.5 * (low + high), apex[2]), (1.0, 0.0, 0.0, 0.0))
  return gear.joined(stub)


def halfShaftShape(side: float) -> Shape:
  """The 'halfShaftShape' function returns a rear half shaft from its
  inner joint to its outer, on 'side', in the car's frame (along y at
  the rear axle, the wheels' height)."""
  from ._rig import WHEEL_Y
  outer = WHEEL_Y + OUTER_JOINT
  shaft = cylinderShape(SHAFT, outer - INNER_JOINT, 24).moved(
    (-WHEELBASE, side * 0.5 * (INNER_JOINT + outer), HUB_HEIGHT),
    (1.0, 0.0, 0.0, 0.0))
  joints = tuple(cylinderShape(0.035, 0.07, 24).moved(
    (-WHEELBASE, side * at, HUB_HEIGHT), (1.0, 0.0, 0.0, 0.0))
                 for at in (INNER_JOINT + 0.035, outer - 0.035))
  return _joined((shaft,) + joints)


@functools.lru_cache(maxsize=2)
def sideGearBody(side: float) -> Body:
  """The 'sideGearBody' function returns a side gear and its stub, steel,
  in the car's frame."""
  return Body.of(sideGearShape(side), STEEL)


@functools.lru_cache(maxsize=2)
def halfShaftBody(side: float) -> Body:
  """The 'halfShaftBody' function returns a rear half shaft with its
  joints' housings, steel, in the car's frame."""
  return Body.of(halfShaftShape(side), STEEL)


def realCar(controls: RealCarControls,
            start: tuple = None) -> tuple[Assembly, tuple[State, ...]]:
  """The 'realCar' function returns the real car worked by 'controls':
  the walker (body 0) sat in it, the chassis (1), the corners (2 on,
  six each: lower and upper wishbones, knuckle, wheel, shock's tube and
  rod), the rack ('RACK'), the column ('COLUMN'), the drivetrain
  ('FIRST_DRIVE' on: flywheel, input and output shafts, free gears,
  idler, carrier, spiders), the side gears ('SIDES') and the rear half
  shafts ('HALVES'); as built, still, its engine idling in neutral, its
  frame where 'start' puts it (its place and turn; None: on the ground
  at the world's middle, along x)."""
  from ._scenes import WALKER
  from ._rig import WHEEL_Y
  carAt, carTurn = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)) if (
    start is None) else start

  def world(point: Vector) -> Vector:
    """Returns 'point' of the car's frame in the world."""
    return plus(carAt, rotated(carTurn, point))

  def state(centre: Vector, turn: tuple = (1.0, 0.0, 0.0, 0.0)) -> State:
    """Returns the state of a body whose centre is at 'centre' in the
    car's frame, turned 'turn' from it."""
    return State(world(centre), product(carTurn, turn))

  setups = (WheelSetup(),) * len(CORNERS) if controls.tune is None else (
    tuple(controls.tune.wheels))
  chassis = chassisBody()
  bodies = [WALKER.body(), chassis]
  states = [State(world(SEAT)), state(chassis.centre)]
  connections = []
  addCorners(CORNERS, setups, (FRONT_SHOCK, REAR_SHOCK), CHASSIS,
             FIRST_CORNER, RACK, controls.brakes.lines, None, world, state,
             carTurn, bodies, states, connections)
  addSteering(CHASSIS, RACK, COLUMN, controls.steer, COLUMN_LENGTH,
              COLUMN_RISE, world, state, carTurn, bodies, states,
              connections)
  drive = controls.drive
  addDrivetrain(drive, SHIFT, CHASSIS, CHASSIS, FIRST_DRIVE, SIDES,
                ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0)), world, carTurn,
                850.0, bodies, states, connections)
  wheels = (FIRST_CORNER + 6 * 2 + 3, FIRST_CORNER + 6 * 3 + 3)
  drive.layout = DrivetrainLayout(*(tuple(drive.layout)[:5] + wheels + (
    (0.0, 0.0, 1.0), (0.0, 0.0, 1.0))))
  carrier = drive.layout.carrier
  apex = plus((APEX, 0.0, OUTPUT_HEIGHT), SHIFT)
  for k, side in enumerate((1.0, -1.0)):
    gear = sideGearBody(side)
    bodies.append(gear)
    states.append(state(gear.centre))
    connections.append(Housed(SIDES[k]))
  for side in (1.0, -1.0):
    shaft = halfShaftBody(side)
    bodies.append(shaft)
    states.append(state(shaft.centre))
  for k, side in enumerate((1.0, -1.0)):
    axle = (0.0, side, 0.0)
    middle = plus(apex, (0.0, side * 0.5 * DIFF_MODULE * SPIDER, 0.0))
    inner = (-WHEELBASE, side * INNER_JOINT, HUB_HEIGHT)
    outer = (-WHEELBASE, side * (WHEEL_Y + OUTER_JOINT), HUB_HEIGHT)
    connections += [
      Hinge(carrier, middle, axle, SIDES[k], middle, axle),
      Tie(SIDES[k], inner, HALVES[k], inner),
      GearMesh(SIDES[k], axle, 1, HALVES[k], axle, 1, CHASSIS, True,
               JOINT_MODULE),
      Tie(HALVES[k], outer, wheels[k], (0.0, 0.0, OUTER_JOINT)),
      GearMesh(HALVES[k], axle, 1, wheels[k], (0.0, 0.0, 1.0), 1, CHASSIS,
               True, JOINT_MODULE)]
  connections += [Contact(0, CHASSIS, *_WALKER_ON_STEEL)]
  connections += [Contact(0, FIRST_CORNER + 6 * c + 3, *_WALKER_ON_RUBBER)
                  for c in range(len(CORNERS))]
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)


def realCarCoils(assembly: Assembly) -> tuple:
  """The 'realCarCoils' function returns how the real car's coils are
  drawn ('coilOf': each corner's shock's tube)."""
  return tuple(coilOf(FIRST_CORNER + 6 * c + 4) for c in range(len(CORNERS)))


def realCarFinishes(assembly: Assembly) -> dict:
  """The 'realCarFinishes' function returns how the real car's bodies are
  drawn, by index: the chassis by its parts (its case glass), each
  corner's wishbones and knuckle by theirs (mirrored on the right), its
  wheel as the brake bench's (rim, tyre, disc), its shock's tube and rod
  by their profiles, the rack whole, the drivetrain as on its bench
  (moved), the side gears and half shafts whole ('gear', 'shaft'); the
  steering wheel and column: the view's own."""
  from ._brakes import discRuns
  from ._carcass import rimRuns
  from ._shock import shockRuns
  from ._tyred import tyreRuns
  runs = shockRuns()
  out = {CHASSIS: chassisPieces(), RACK: 'rack'}
  for c, (at, side) in enumerate(CORNERS):
    first = FIRST_CORNER + 6 * c
    out[first] = _sidedPieces(armPieces(True), side, at)
    out[first + 1] = _sidedPieces(armPieces(False), side, at)
    out[first + 2] = _sidedPieces(knucklePieces(), side, at)
    out[first + 3] = rimRuns() + tyreRuns() + discRuns()
    out[first + 4] = runs['tube']
    out[first + 5] = runs['rod']
  parts = ([flywheelPieces(), inputPieces(), outputPieces()]
           + [(('gear', _freeGear(k)),) for k in range(6)]
           + [(('gear', idlerShape()),), carrierPieces(),
              (('gear', spiderShape(1.0)),), (('gear', spiderShape(-1.0)),)])
  for k, pieces in enumerate(parts):
    out[FIRST_DRIVE + k] = _moved(pieces)
  for k, side in enumerate((1.0, -1.0)):
    out[SIDES[k]] = (('gear', sideGearShape(side)),)
    out[HALVES[k]] = (('shaft', halfShaftShape(side)),)
  return out
