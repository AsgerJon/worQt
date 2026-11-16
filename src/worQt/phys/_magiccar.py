"""
The real car a level of detail up (user, 2026-11-15: "Create a copy of
the car where you replace our physical parts with the equivalences at
higher abstraction levels"; "keep the disc brakes. python side, same
bodywork, selectable defaulting to the new cheaper one"; "automatic
transmission bro... fake in other words. audible only"). The car of
parts ('_realcar.realCar') is the reference: each stand-in is taken from
it as built or measured on it, and checked against it
('test_magiccar'); its looks are the same.

Its bodies: the walker (0); the chassis (1: the car of parts' chassis
with its rack, every part of its drivetrain, its shocks' and struts'
rods and the sprung half of each wishbone, shock tube and half shaft,
lumped as built: their mass, middle and moments, 'lumped'); each
corner's carrier and its wheel ('CARRIERS', 'WHEELS': the knuckle or
upright with the unsprung halves, shapeless; the wheel as built); the
steering column as built ('COLUMN').

Each carrier slides on a line on the chassis ('Slide', its wheel's rise
and fall, turning about it): in front straight up through the wheel's
middle (the car of parts' wishbones gained no camber and held their roll
centre at the ground), behind leaning out at its top as far as moves the
tyre's patch out as the strut did ('REAR_LEAN': its roll centre ~180 mm
up). Along that line its coil, damper and stops at the wheel: the shock's
or strut's rates times its motion ratio squared ('FRONT_MOTION',
'REAR_MOTION', measured), its travel to each stop over it, its coil
holding at the wheel as much as the car of parts' holds there standing
(it rides as built). Its turning about the line held by a servo (a
'TurnPoint' toward a fourth wall point of its own, as the hands turn the
column; '_servosteering.ServoSteering' sets each one's angle each
frame): the front ones following the steering wheel as the rack
turned the knuckles, each wheel by its toe, the rear's toe in as the car
of parts stands; each wheel's camber as its tune-up sets it (its axle
tilted on its carrier). The wheels on their carriers on two ties (the
bearing), their disc brakes (their calipers on the carriers) and tyres
as the car of parts'. The rear ones driven by a fake automatic
('_automatic.AutomaticDrive'), each wheel twisted on its carrier
('Motor': the small steps have no driveshafts; the slide hands the
twist's take-back to the chassis as the half shaft and differential
did). Drawn as the car of parts: its bodywork,
its knuckles and uprights on the carriers, the coils between their
seats, its wishbones, tie rods, radius rods, toe links, struts' rods and
half shafts as rods between where their ends are ('LINKS': drawing only,
'magicLinks').

Left out, stated (what a level up does not need to see): the
wishbones' and the struts' camber gain and bump steer, the links' and
bushes' give (compliance steer), the tyres' aligning twist back to the
hands, the engine's and the gearbox's turning inertia, the clutch.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._assembly import Assembly, BrakeLine, Contact, Damper, DiscBrake
from ._assembly import FourthWall, Hinge, Motor, Slide, Spring
from ._assembly import Tie, TurnPoint
from ._automatic import AutomaticDrive
from ._axle import HANDS
from ._body import Body, State
from ._drivetrain import DrivetrainControls
from ._realcar import CORNER_BODIES, CORNERS, FLYWHEEL_MASS, HALVES
from ._realcar import FRONT_SHOCK, REAR_SHOCK
from ._realcar import SEAT, _WALKER_ON_STEEL, Antilock
from ._realcar import RealCarControls, chassisShape, realCar
from ._realcar import COLUMN as PARTS_COLUMN
from ._realcar import WHEELS as PARTS_WHEELS
from ._rig import HUB_HEIGHT, WHEEL_Y, TuneUp, WheelSetup
from ._servosteering import ServoSteering
from ._shock import BUMP_DAMPING, TOP_OUT
from ._soapbox import _sided
from ._tyred import _WALKER_ON_RUBBER, tyreOf
from ._vectors import Vector, dot, matrixOf, matrixProduct, minus, plus
from ._vectors import product, rotated, scaled, transposed, turnAbout

#  Its bodies: the chassis, each corner's carrier and wheel ('CORNERS'
#  order), the steering column.
CHASSIS = 1
CARRIERS, WHEELS = (2, 4, 6, 8), (3, 5, 7, 9)
COLUMN = 10
#  The car of parts' motion ratios (its coil's, then its damper's, change
#  of length over its wheel's rise from 0.6 g to 1.4 g on the yard, either
#  side alike to 0.001; scratch magic/reference.py, 2026-11-15): front,
#  rear.
FRONT_MOTION, REAR_MOTION = (0.679, 0.684), (0.549, 0.551)
#  How far the rear slides lean out at their tops, rad (the car of parts'
#  tyre's patch moved out 0.22 m a metre its wheel rose behind, none in
#  front).
REAR_LEAN = math.atan(0.22)
#  Each corner's rate at the wheel over its coil's times its motion
#  ratio squared, front, rear: what the car of parts' links add (its
#  wheels, loaded from 0.6 g to 1.4 g, rose 51.5 mm in front and 31.9
#  behind, as on stiffer coils than theirs alone: the stand-in on theirs
#  alone rose 53.4 and 43.6 and leant 1.18 deg at half a g to its 0.86;
#  at 1.0 and 1.5, 53.4, 31.2 and 0.97 deg; scratch magic/rates.py,
#  2026-11-15).
RATE_SHARE = (1.04, 1.47)
#  What of each of the car of parts' bodies rides on its corner's wheel
#  (its carrier's), by what it is; the rest is the chassis' (every body
#  not named: the chassis, rack, drivetrain).
UNSPRUNG = {'knuckle': 1.0, 'lower': 0.5, 'upper': 0.5, 'tube': 0.5,
            'rod': 0.0, 'half shaft': 0.5}
#  The coil's line: from the wheel's middle up its slide to its end on
#  the chassis, m.
SPAN = 0.3
#  The servos ('TurnPoint's): the front ones' (the steering: stiff as
#  the car of parts' rack and tie rods turned the knuckles), the rear
#  ones' (the toe links: stiffer), each N m a radian, N m s, N m.
STEER_SERVO = (3e4, 600.0, 3000.0)
TOE_SERVO = (1e5, 1000.0, 1e4)


@functools.lru_cache(maxsize=1)
def reference() -> tuple:
  """The 'reference' function returns the car of parts as built at the
  world's middle, along x (its assembly and states: the car's frame the
  world's), its tune-up as built."""
  controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0), TuneUp(
    (WheelSetup(),) * len(CORNERS)), DrivetrainControls(), Antilock())
  return realCar(controls)


@functools.lru_cache(maxsize=1)
def _shares() -> dict:
  """Returns, of each of the car of parts' bodies the stand-in lumps,
  its corner (None: no corner's) and the share of it that rides on
  that corner's wheel ('UNSPRUNG'): {index: (corner, share)}."""
  parts, _ = reference()
  roles = {}
  for c, corner in enumerate(CORNER_BODIES):
    for part, index in corner.items():
      roles[index] = (c, part)
  for k, half in enumerate(HALVES):
    roles[half] = (2 + k, 'half shaft')
  kept = {0, PARTS_COLUMN} | set(PARTS_WHEELS)
  out = {}
  for index in range(len(parts.bodies)):
    if index in kept:
      continue
    corner, part = roles.get(index, (None, None))
    out[index] = (corner, UNSPRUNG.get(part, 0.0) if corner is not None
                  else 0.0)
  return out


def lumped(parts: tuple, shape: object) -> Body:
  """The 'lumped' function returns one body of the car of parts' bodies
  'parts' ((index, share) each: that share of its stuff), as built: their
  mass, their middle, their moments about it (each turned into the car's
  frame and moved there by the parallel axes), its own frame the car's;
  its shape 'shape' (None: none)."""
  assembly, states = reference()
  bodies = assembly.bodies
  mass = sum(share * bodies[k].mass for k, share in parts)
  centre = tuple(sum(share * bodies[k].mass * states[k].place[i]
                     for k, share in parts) / mass for i in range(3))
  moment = [[0.0] * 3 for _ in range(3)]
  for k, share in parts:
    body, state = bodies[k], states[k]
    turn = matrixOf(state.turn)
    own = matrixProduct(matrixProduct(turn, body.inertia), transposed(turn))
    off = minus(state.place, centre)
    far = dot(off, off)
    for i in range(3):
      for j in range(3):
        moment[i][j] += share * (own[i][j] + body.mass * (
          (far if i == j else 0.0) - off[i] * off[j]))
  return Body(mass, centre, tuple(tuple(row) for row in moment), shape)


@functools.lru_cache(maxsize=1)
def chassisBody() -> Body:
  """The 'chassisBody' function returns the stand-in's chassis: all the
  car of parts' bodies lump but the walker, wheels, column and what rides
  on the wheels ('_shares'), its shape the chassis' ('chassisShape': how
  it meets the ground and the walker)."""
  parts = tuple((index, 1.0 - share)
                for index, (_, share) in _shares().items() if share < 1.0)
  return lumped(parts, chassisShape())


@functools.lru_cache(maxsize=4)
def carrierBody(corner: int) -> Body:
  """The 'carrierBody' function returns corner 'corner''s carrier: what
  of the car of parts rides on its wheel ('_shares'), shapeless."""
  parts = tuple((index, share) for index, (c, share) in _shares().items()
                if c == corner and share > 0.0)
  return lumped(parts, None)


def slideOf(corner: int) -> tuple[Vector, Vector]:
  """The 'slideOf' function returns corner 'corner''s slide in the car's
  frame: its point (the wheel's middle) and its way up (in front
  straight up; behind leaning out 'REAR_LEAN' at its top)."""
  at, side = CORNERS[corner]
  middle = _sided((0.0, WHEEL_Y, HUB_HEIGHT), side, at)
  lean = 0.0 if at == 0.0 else REAR_LEAN
  return middle, (0.0, side * math.sin(lean), math.cos(lean))


@functools.lru_cache(maxsize=4)
def _travelOf(corner: int) -> tuple[float, float, float, float]:
  """Returns corner 'corner''s coil at the wheel as the car of parts'
  holds it standing as built: its rate, N/m (the coil's times its motion
  ratio squared, times 'RATE_SHARE'), what it holds there, N (the
  coil's push times its motion ratio), and its wheel's travel up to the
  bump stop and down to the top-out, m (its damper's to each over its
  motion ratio)."""
  parts, states = reference()
  shock = FRONT_SHOCK if CORNERS[corner][0] == 0.0 else REAR_SHOCK
  coil, damper = FRONT_MOTION if CORNERS[corner][0] == 0.0 else (
    REAR_MOTION)
  body = CORNER_BODIES[corner]
  moving = {body['knuckle'], body.get('tube', -1), body.get('lower', -1)}

  def length(connection: object) -> float:
    """Returns how long 'connection' is between its points as built."""
    ends = []
    for index, point in ((connection.first, connection.firstPoint),
                         (connection.second, connection.secondPoint)):
      ends.append(parts.bodies[index].placeOf(states[index], point))
    return math.dist(*ends)

  springs = [x for x in parts.connections if isinstance(x, Spring)
             and x.stiffness == shock.spring and x.rest == shock.free
             and (x.first in moving or x.second in moving)]
  dampers = [x for x in parts.connections if isinstance(x, Damper)
             and (x.first in moving or x.second in moving)]
  if len(springs) != 1 or len(dampers) != 1:
    raise ValueError('corner %d: found %d coils and %d dampers, wanted one'
                     ' each' % (corner, len(springs), len(dampers)))
  held = shock.spring * (shock.free - length(springs[0])) * coil
  eye = length(dampers[0])
  share = RATE_SHARE[0 if CORNERS[corner][0] == 0.0 else 1]
  return (shock.spring * coil ** 2 * share, held,
          (eye - shock.shortest) / damper, (shock.longest - eye) / damper)


def _cornerAdded(corner: int, setup: WheelSetup, line: BrakeLine,
                 world: object, carTurn: tuple, bodies: list,
                 states: list, connections: list) -> FourthWall:
  """Adds corner 'corner''s carrier and wheel to 'bodies', 'states' and
  'connections' (set up as 'setup' says: its tyre's pressure, its axle
  tilted for its camber), its brake on 'line'; returns the fourth wall
  point its servo turns it toward (set each frame: 'ServoSteering')."""
  parts, built = reference()
  at, side = CORNERS[corner]
  carrier, wheel = CARRIERS[corner], WHEELS[corner]
  front = at == 0.0
  hub, way = slideOf(corner)
  tilt = turnAbout((1.0, 0.0, 0.0), -side * setup.camber)

  def tilted(point: Vector) -> Vector:
    """Returns 'point' of the car's frame tilted about the hub for the
    camber."""
    return plus(hub, rotated(tilt, minus(point, hub)))

  body = carrierBody(corner)
  bodies.append(body)
  states.append(State(world(body.centre), carTurn))
  turning = PARTS_WHEELS[corner]
  rim = built[turning]
  bodies.append(parts.bodies[turning])
  states.append(State(world(tilted(rim.place)), product(
    carTurn, product(tilt, rim.turn))))
  rate, held, bump, droop = _travelOf(corner)
  motion = FRONT_MOTION if front else REAR_MOTION
  shock = FRONT_SHOCK if front else REAR_SHOCK
  top = plus(hub, scaled(way, SPAN))
  servo = FourthWall(0.0)
  connections += [
    Slide(CHASSIS, hub, way, carrier, hub, way),
    TurnPoint(carrier, CHASSIS, way, servo,
              *(STEER_SERVO if front else TOE_SERVO)),
    Spring(CHASSIS, top, carrier, hub, rate, SPAN + held / rate, 0.0,
           False, True),
    Damper(carrier, hub, CHASSIS, top, shock.bump * motion[1] ** 2,
           shock.rebound * motion[1] ** 2),
    Spring(carrier, hub, CHASSIS, top, shock.stop * motion[1] ** 2,
           SPAN - bump, BUMP_DAMPING * motion[1] ** 2, False, True),
    Spring(carrier, hub, CHASSIS, top, TOP_OUT * motion[1] ** 2,
           SPAN + droop, 0.0, True, False)]
  for w in (0.02, 0.07):
    connections.append(Tie(carrier, tilted(plus(hub, (0.0, side * w,
                                                      0.0))),
                           wheel, (0.0, 0.0, w)))
  brakes = [x for x in parts.connections if isinstance(x, DiscBrake)
            and x.disc == turning]
  if len(brakes) != 1:
    raise ValueError('corner %d: found %d disc brakes, wanted one' % (
      corner, len(brakes)))
  disc = brakes[0]
  connections.append(DiscBrake(wheel, carrier, disc.middle, disc.axle,
                               tilted(disc.pad), disc.inner, disc.outer,
                               line, disc.piston, disc.friction))
  connections.append(tyreOf(wheel, setup.pressure))
  return servo


def magicCar(controls: RealCarControls,
             start: tuple = None) -> tuple[Assembly, tuple[State, ...]]:
  """The 'magicCar' function returns the stand-in car worked by
  'controls' (its drive an 'AutomaticDrive', its brakes an 'Antilock' of
  its 'WHEELS'): the walker (body 0) sat in it, the chassis ('CHASSIS'),
  each corner's carrier and wheel ('CARRIERS', 'WHEELS'), the column
  ('COLUMN'); as built, still, in drive, idling; its frame where 'start'
  puts it (its place and turn; None: on the ground at the world's
  middle, along x)."""
  from ._scenes import WALKER
  drive = controls.drive
  if not isinstance(drive, AutomaticDrive):
    raise TypeError('the stand-in car drives through an AutomaticDrive, '
                    'not %s' % type(drive).__name__)
  if tuple(controls.brakes.wheels) != WHEELS:
    raise ValueError('the stand-in car\'s anti-lock must read its own '
                     'wheels %s, not %s' % (WHEELS, controls.brakes.wheels))
  carAt, carTurn = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)) if (
    start is None) else start

  def world(point: Vector) -> Vector:
    """Returns 'point' of the car's frame in the world."""
    return plus(carAt, rotated(carTurn, point))

  setups = (WheelSetup(),) * len(CORNERS) if controls.tune is None else (
    tuple(controls.tune.wheels))
  chassis = chassisBody()
  bodies = [WALKER.body(), chassis]
  states = [State(world(SEAT)), State(world(chassis.centre), carTurn)]
  connections = []
  servos = [_cornerAdded(c, setups[c], controls.brakes.lines[c], world,
                         carTurn, bodies, states, connections)
            for c in range(len(CORNERS))]
  parts, built = reference()
  wheel = built[PARTS_COLUMN]
  bodies.append(parts.bodies[PARTS_COLUMN])
  states.append(State(world(wheel.place), product(carTurn, wheel.turn)))
  top = parts.bodies[PARTS_COLUMN].placeOf(wheel, (0.0, 0.0, 0.0))
  up = (0.0, 0.0, 1.0)
  connections += [Hinge(CHASSIS, top, rotated(wheel.turn, up), COLUMN,
                        (0.0, 0.0, 0.0), up),
                  TurnPoint(COLUMN, CHASSIS, up, controls.steer, *HANDS)]
  for k in range(2):
    connections.append(Motor(CARRIERS[2 + k], WHEELS[2 + k], up,
                             drive.shafts[k]))
  connections.append(Contact(0, CHASSIS, *_WALKER_ON_STEEL))
  connections += [Contact(0, w, *_WALKER_ON_RUBBER) for w in WHEELS]
  drive.wheels, drive.rolling = WHEELS[2:], WHEELS[:2]
  drive.flywheel = FLYWHEEL_MASS if controls.tune is None or (
    controls.tune.flywheel is None) else controls.tune.flywheel
  drive.steering = ServoSteering(servos, controls.steer,
                                 tuple(setup.toe for setup in setups),
                                 tuple(0.0 if at == 0.0 else REAR_LEAN
                                       for at, _ in CORNERS))
  drive.steering.worked(0.0)
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)


def magicCarFinishes(assembly: Assembly) -> dict:
  """The 'magicCarFinishes' function returns how the stand-in car's
  bodies are drawn, by index, as the car of parts': the chassis by its
  parts under its bodywork ('chassisFinish'), each front carrier as the
  knuckle drawn round, each rear one as the upright with its strut's
  tube ('_cornerlooks'), each wheel as the brake bench's (rim, tyre,
  disc); the steering wheel and column: the view's own."""
  from ._brakes import discRuns
  from ._carcass import rimRuns
  from ._cornerlooks import knuckleFinish, uprightFinish
  from ._realcar import chassisFinish
  from ._tyred import tyreRuns
  out = {CHASSIS: chassisFinish()}
  for corner, (at, side) in enumerate(CORNERS):
    out[CARRIERS[corner]] = (knuckleFinish(side, at) if at == 0.0
                             else uprightFinish(side, at))
    out[WHEELS[corner]] = rimRuns() + tyreRuns() + discRuns()
  return out


def _shockLine(side: float, at: float) -> tuple[Vector, Vector, Vector]:
  """Returns the front shock's eyes on the corner 'at' on 'side' as
  built (its foot, on the lower wishbone, drawn on the carrier; its top
  on the chassis) and its unit way up from the foot."""
  from ._rig import SHOCK_FOOT, SHOCK_TOP
  foot, top = _sided(SHOCK_FOOT, side, at), _sided(SHOCK_TOP, side, at)
  way = minus(top, foot)
  return foot, top, scaled(way, 1.0 / math.dist(foot, top))


def magicCarCoils(assembly: Assembly) -> tuple:
  """The 'magicCarCoils' function returns how the stand-in car's coils
  are drawn ('CoilDress'), as the car of parts' shocks' and struts': in
  front from the shock's lower seat (on the carrier) to its upper (on
  the chassis), behind from the strut's tube's seat (on the carrier) to
  its rod's (on the chassis)."""
  from ._shock import COIL_RADIUS, COIL_TURNS, LOWER_SEAT, UPPER_SEAT
  from ._shock import WIRE_RADIUS
  from ._strut import COIL_ROUND, LOWER_AT, STRUT_FOOT, STRUT_TOP
  from ._strut import TURNS, UPPER_AT, WIRE_ROUND, strutWay
  out = []
  for corner, (at, side) in enumerate(CORNERS):
    carrier = CARRIERS[corner]
    if at == 0.0:
      foot, top, way = _shockLine(side, at)
      out.append((carrier, plus(foot, scaled(way, LOWER_SEAT)), CHASSIS,
                  plus(top, scaled(way, -UPPER_SEAT)), COIL_RADIUS,
                  WIRE_RADIUS, COIL_TURNS))
    else:
      way = strutWay()
      out.append((carrier, _sided(plus(STRUT_FOOT, scaled(way, LOWER_AT)),
                                  side, at), CHASSIS,
                  _sided(plus(STRUT_TOP, scaled(way, -UPPER_AT)), side,
                         at), COIL_ROUND, WIRE_ROUND, TURNS))
  return tuple(out)


@functools.lru_cache(maxsize=1)
def magicLinks() -> tuple:
  """The 'magicLinks' function returns the stand-in car's links drawn as
  rods between where their ends are now, drawing only ('LinksDress':
  each its first body and point, its second and point, its radius, its
  key, and how far it reaches from the first's point toward the
  second's, None: all the way): in front the wishbones' legs from their
  pivots on the chassis to their ball joints on the carrier ('arm'), the
  tie rod from the rack's end to the steering arm ('legs'), the shock's
  tube up from its foot ('damper') and its rod down from its top
  ('chrome'); behind the radius rod and the toe link from the chassis to
  the carrier ('legs'), the strut's rod down from its top ('chrome'),
  the half shaft from the differential to the wheel ('shaft')."""
  from ._cornerlooks import ARM_TUBE
  from ._realcar import INNER_JOINT, OUTER_JOINT, SHAFT, WHEELBASE
  from ._rig import LOWER_BALL, LOWER_PIVOT_Y, LOWER_SPREAD, TIE_INNER
  from ._rig import TIE_OUTER, UPPER_BALL, UPPER_PIVOT_Y, UPPER_SPREAD
  from ._shock import ROD_DOWN, ROD_RADIUS, TUBE_RADIUS, TUBE_UP
  from ._strut import RADIUS_BACK, RADIUS_FRONT, ROD_LONG, ROD_ROUND
  from ._strut import STRUT_FOOT, STRUT_TOP, TOE_INNER
  legs = 0.006
  out = []
  for corner, (at, side) in enumerate(CORNERS):
    carrier = CARRIERS[corner]

    def sided(point: Vector) -> Vector:
      """Returns the left corner's 'point' at this corner."""
      return _sided(point, side, at)

    if at == 0.0:
      for ball, y, x0, spread in ((LOWER_BALL, LOWER_PIVOT_Y, 0.0,
                                   LOWER_SPREAD),
                                  (UPPER_BALL, UPPER_PIVOT_Y, UPPER_BALL[0],
                                   UPPER_SPREAD)):
        for way in (-1.0, 1.0):
          out.append((CHASSIS, sided((x0 + way * spread, y, ball[2])),
                      carrier, sided(ball), ARM_TUBE, 'arm', None))
      out.append((CHASSIS, sided(TIE_INNER), carrier, sided(TIE_OUTER),
                  legs, 'legs', None))
      foot, top, _ = _shockLine(side, at)
      out.append((carrier, foot, CHASSIS, top, TUBE_RADIUS, 'damper',
                  TUBE_UP))
      out.append((CHASSIS, top, carrier, foot, ROD_RADIUS, 'chrome',
                  ROD_DOWN))
    else:
      out.append((CHASSIS, sided(RADIUS_FRONT), carrier, sided(RADIUS_BACK),
                  legs, 'legs', None))
      out.append((CHASSIS, sided(TOE_INNER), carrier, sided(TIE_OUTER),
                  legs, 'legs', None))
      out.append((CHASSIS, sided(STRUT_TOP), carrier, sided(STRUT_FOOT),
                  ROD_ROUND, 'chrome', ROD_LONG))
      out.append((CHASSIS, (-WHEELBASE, side * INNER_JOINT, HUB_HEIGHT),
                  WHEELS[corner], (0.0, 0.0, OUTER_JOINT), SHAFT, 'shaft',
                  None))
  return tuple(out)
