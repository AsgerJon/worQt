"""
The car (user, 2026-11-12: "a 'car' with four wheels, two wheels being
turned an actual steering column. The propulsion could just be magic,
that is, we imagine that the bearings also contain engines. BUT, this
'car' should have actual independent suspensions").

Each wheel hangs on a knuckle of its own, and each knuckle on five rods
to the chassis (a five-link suspension: a double wishbone is its two
upper and two lower rods, each pair meeting at a ball joint on the
knuckle, the fifth a tie rod in front, a toe link behind): five rods
leave the knuckle one way to move, up and down along the arcs the
wishbones swing through, carried by a coilover (a spring and its
damper) from the knuckle to a tower on the chassis, 8 cm of travel
either way (a strap stops the droop, a rubber buffer the bump: without
them a car hard over let its inner front wheel hang until the
wishbones turned it 50 degrees and its steering locked over centre).
A rod is a stiff spring of its own length, its ends rubber bushings,
the rear's stiffer ('REAR_ROD': the rear wheels must not steer). Each is
drawn as the rod it is.

The front knuckles turn about their kingpins (the line through their
two ball joints) as the tie rods push their steering arms (angled for
Ackermann). The tie rods hang from the ends of a rack, a bar across the
car held by four rods so it only slides sideways, its ends beside the
wishbones' inner pivots, so a wheel's tie rod swings through much the
arc its wishbones do and the wheel hardly steers as it rises (a kart's
plate at the car's middle, its tie rods 0.6 m long, steered a wheel 7
degrees in 4 cm). A drag link from a plate at the foot of the steering
column pushes the rack: turning the column swings the plate's hole
sideways. The column turns in two bushings on the chassis; the
driver's hands, with the power steering's motor, twist it against the
chassis (a motor, a servo worked out at every step, set by 'steer').

The bearings are the wheel's world's stand-in (two stiff bushings on
the axle), each with a friction brake (a 'Motor' braking, its caliper
on the knuckle; tried inboard, braking through the halfshafts, the
twist along the leaning steering axes steered the wheels: the rears
toed out 0.8 degrees braked). The rear wheels are driven ('DRIVEN';
user: "remove drive from front wheels making giving it RWD"; it was
four wheel drive): the engine (the one magic left: a torque, no
pistons) drives a propshaft back to a differential on the rear axle,
which drives its two wheels by halfshafts jointed at both ends
('Motor' as a driveshaft: the drive goes into the wheel, the twist back
into the chassis along the shaft); the differential is open and its
gears' inertia left out, so each rear wheel gets half the engine's
torque whatever the other does ('drive' sets it each frame, no more
than the engine's power at its speed: the two wheels' mean). The
chassis is
an
open frame of solid bars (user: "don't put holes in the prismatic
constituent parts"; "Most importantly: suspension. Make that more
visible"), the coilovers through the upper wishbones, each forked at
its foot about the halfshaft. The tyres are the stand-in a car's world
takes for the tyre of the wheel's world: a rigid wheel and tyre turned
whole ('carWheel'), meeting the road at its tread's two edges' lowest
points, the rubber's give and grip in the road's law ('CAR_ROAD': each
edge as stiff as half the tyre, a bristle relaxing over the tyre's
relaxation length, so it pushes back as it slips). The coilovers' rest
lengths are set as it is built so it stands at its ride height without
its tyres' sideways grip ('_rideHeld').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._assembly import Assembly, Drag, Drive, Motor, Spring
from ._body import Body, State
from ._gearbox import Gearbox
from ._ground import Ground
from ._shape import Shape, boxShape, cylinderShape
from ._terrain import oval, ovalWall, track
from ._turned import Turned
from ._tyre import TYRE, Tyre, steelWheel
from ._vectors import UNTURNED, Quaternion, Vector, conjugate, dot
from ._vectors import minus, norm, plus, product, rotated, scaled
from ._vectors import turnAbout
from ._world import FULL, Fidelity, World

#  The road under a car's stand-in tyres: each tread edge 100 kN/m (the
#  tyre 200 kN/m, as the wheel's world's at its load), Hunt and
#  Crossley's damping 1 s/m, dry asphalt's grip, each edge's bristle 150
#  kN/m relaxing over 0.4 m (cornering and driving stiffness 60 kN a
#  unit of slip a edge, ~16 times the load, as a car's).
CAR_ROAD = Ground(1e5, 1.0, 1.0, 1.5e5, 300.0, 0.4)
GRAVITY = (0.0, 0.0, -9.81)
#  The wheelbase, between the axles, and the track, between the middles
#  of the two wheels on an axle, m; the corners, front left, front
#  right, rear left, rear right, each where along it is and its side
#  (left +1, y up the left).
WHEELBASE, TRACK = 2.5, 1.76
#  How much further out each wheel is than when the car was first
#  built (track 1.56; user, 2026-11-12: "Widen the car, that is longer
#  between wheels"), m: the wheel, its knuckle, ball joints and the
#  coilover's ends move out by it, the frame's pivots stay (the arms,
#  tie rods and halfshafts grow by it), the arches over the axles grow
#  to reach the coilovers' tops.
WIDER = 0.5 * TRACK - 0.78
CORNERS = ((0.5 * WHEELBASE, 1), (0.5 * WHEELBASE, -1),
           (-0.5 * WHEELBASE, 1), (-0.5 * WHEELBASE, -1))
#  The axle's height as built: the tyre sunk as its load will sink it.
AXLE_HEIGHT = 0.5 * TYRE.outside - 0.011
#  The masses: the chassis (all sprung but the column), each knuckle
#  (with its hub, brake and half its rods), the column, kg.
CHASSIS_MASS, KNUCKLE_MASS, COLUMN_MASS = 750.0, 15.0, 4.3
#  The front's share of the car's weight (user, 2026-11-12: "Cheaper
#  cars are front heavy, but let's keep this with mass centrally between
#  the wheels"; it was 45 to 55, the engine behind the seat): the engine
#  (the one magic part: no pistons, no gearbox) weighs what puts the
#  car's centre of mass so, the rest of the chassis one stuff
#  ('_balancedChassis').
FRONT_SHARE = 0.5
#  The rods' and bearings' bushings, N/m, and their damping, N s/m (a
#  rod's rubber ~0.25 of critical on a knuckle: at 200, 0.026, each ABS
#  pulse set the knuckles ringing and the front wheels' toe swung -1.6
#  to +3.2 degrees).
ROD, ROD_DAMPING = 1e6, 2000.0
#  The rear rods' bushings, N/m (user, 2026-11-12: "we should take
#  steering away from the rear wheels"): at 'ROD' the rear wheels
#  shifted and steered under side loads (0.25 degrees at half a g) and
#  above ~25 m/s the car swayed at 2.8 Hz, growing; rigid rods (rules)
#  took the sway away but, undamped, the driven rear wheels hopped
#  (power hop: launched, their rims 30 % slow, 8.6 m/s in 2 s).
REAR_ROD = 3e6
BEARING, BEARING_DAMPING = 4e6, 300.0
#  The coilovers: as stiff along their line as a 3 Hz ride asks of a
#  corner, damped 0.5 of critical ('retuned' sets others); each corner's
#  travel either way of its ride height, m (a strap beside the coilover
#  takes its droop, a rubber buffer its bump), and those stops'
#  stiffness, N/m, and damping, N s/m. (User, 2026-11-13: "this car...
#  it seems super wobbly. at around 163kph there is what feels like some
#  kind of resonance. Let's increase the stiffness of the shock
#  absorbers quite a lot"; "it also looks like it over cambers to the
#  right on the banking". At 1.5 Hz, 0.35 (LIVE, the column held, a
#  0.1 s nudge): the 3.3 Hz sway died at -0.86/s at 40 m/s, -0.39 at 45
#  and GREW at 50 (+0.26); through turns one and two at 41 m/s the body
#  rolled 2.2 deg out, the outside corners 56-71 mm up their 80, on the
#  stops at 85. At 3 Hz, 0.5: -2.07, -1.41, -0.98/s; rolled 0.65 deg,
#  14-20 mm. 1.5 Hz at 0.7: -0.56..-0.77; 3 Hz at 0.7: -0.88 at 45;
#  4 Hz, 0.5: rolled 0.40 deg, 7-11 mm.)
RIDE, RIDE_DAMPING = 3.0, 0.5
TRAVEL, STOP, STOP_DAMPING = 0.08, 3e5, 2000.0
#  The engine, as a spec sheet gives it (user, 2026-11-12: "give the
#  power and torque that the actual top Spec miata has"): a small
#  roadster's 2.0 litre, 205 N m (at 4000 rpm) and 135 kW (181 hp, at
#  7000 rpm) at its crank, through a five-speed gearbox ('Gearbox',
#  '_gearbox.py'; user, 2026-11-13: "a gearbox with 4 or 5 speeds, for
#  the sake of the sound": it was an ideal one, always in the gear that
#  gave the most, the wheels getting first gear's torque or the power at
#  their speed), its torque times this (user, 2026-11-13: "Lets double
#  power for the next run"; 1 is the spec sheet's). (It was 1800 N m
#  and 144 kW at the wheels, "stupid" rather than fast: at 1600, 1400
#  and 1500 the rear corners hopped at 31 Hz at a launch until the
#  traction control moved into the shafts.)
POWER_BOOST = 2.0
#  The air's drag on the car, its drag coefficient times its front, m²
#  (an open frame and its driver: ~0.9 x 1.1; flat out it tops out at
#  ~58 m/s, 210 km/h, where the drag takes the engine's power).
DRAG_AREA = 1.0
#  The differentials, where the halfshafts leave them (their middles,
#  each shaft's inner joint a 'DIFF_REACH' either side), and the
#  halfshafts' outer joints, along the wheel's axle from the tyre's
#  middle (inboard of the knuckle's boss), m.
REAR_DIFF = (-0.5 * WHEELBASE, 0.0, AXLE_HEIGHT)
#  The wheels the engine drives, by corner: the rear two (user,
#  2026-11-12: "remove drive from front wheels making giving it RWD";
#  it was four wheel drive, a centre differential, propshafts to a
#  differential on each axle).
DRIVEN = (2, 3)
DIFF_REACH, OUTER_JOINT = 0.12, -0.21
#  How far the column turns either way, rad, and the driver's hands
#  with the power steering's motor on the column (the kart's quick 1.3
#  to 1 asks ~300 N m of a standing car's scrubbing tyres): how hard
#  they twist it at most, N m, how stiffly they hold it, N m a radian,
#  and how they damp it, N m s.
#  The brakes' torque, front and rear (65 to 35: braking puts the load on
#  the front; braked alike, the rear let go and the car spun): a car's,
#  enough to lock a loaded tyre (user: "breaking needs a serious buff";
#  they stopped short of it before; the car's anti-lock keeps them
#  at the edge).
BRAKE_FRONT, BRAKE_REAR = 1600.0, 860.0
#  The brakes' grip on a wheel turning on its knuckle, N m s: past a
#  rad/s or so they hold as hard as they may.
BRAKE_GRIP = 500.0
#  The handbrake (user: "have space-bar lock the wheels instantly like
#  the handbrake"): on the rear wheels, as hard as this, N m, gripping
#  them this hard, N m s (a locked wheel creeps at its tyre's torque over
#  it; much harder and the light knuckle and wheel, kicked at each half
#  step, would ring).
HANDBRAKE, HANDBRAKE_GRIP = 2500.0, 2000.0
STEER_LOCK, HANDS, HANDS_STIFF, HANDS_DAMPING = 0.6, 400.0, 3000.0, 60.0


class CarLinks(NamedTuple):
  """
  CarLinks says which of a car's connections (their places in its
  assembly's) are what, for those who draw them: each corner's upper
  and lower wishbones (two rods each), its tie rod or toe link, its
  coilover (in the corners' order); the halfshafts (one a driven
  wheel, in 'DRIVEN''s order); the drag link and the rack's guides.
  """

  uppers: tuple
  lowers: tuple
  steers: tuple
  coilovers: tuple
  halfshafts: tuple
  drag: int
  guides: tuple


class CarBuild(NamedTuple):
  """
  CarBuild is the car as built: its 'assembly' and 'states' (settled on
  the road), the places in it of the 'chassis', the 'column', the
  'rack', the 'knuckles' and the 'wheels' (in the corners' order), the
  column's axis in the chassis' frame, 'columnAxis', its turn on the
  chassis steering straight ahead, 'straight', the drives of the brakes
  in the bearings, 'brakes' (the corners' order), of the halfshafts,
  'shafts' ('DRIVEN''s order), and of the driver's hands, 'hands';
  which of the
  assembly's connections are what, 'links' ('CarLinks'); the
  anti-lock's share of each brake now, 'antilock', and the engine and
  gearbox, 'gearbox' ('Gearbox': its gear, revolutions, load; the
  things of the car's own that change as it goes, beside its bodies).
  """

  assembly: Assembly
  states: tuple
  chassis: int
  column: int
  rack: int
  knuckles: tuple
  wheels: tuple
  columnAxis: Vector
  straight: Quaternion
  brakes: tuple
  shafts: tuple
  hands: Drive
  links: CarLinks
  antilock: list
  gearbox: Gearbox


def carWheel(tyre: Tyre, offset: float, reach: float,
             sides: int) -> Body:
  """The 'carWheel' function returns the wheel and its tyre as one
  rigid body, turned about its own z axis, the tyre's middle at z
  nought: the steel wheel ('steelWheel', its hub 'reach' m in) and the
  tyre, 'tyre.mass' and a share for its sidewalls in rubber, outlined
  as a turned solid: its tread flat across 160 mm, its shoulders 26 mm
  in and out to its width, down to the rim's flanges (the road meets
  the tread's edges)."""
  seat, half = 0.5 * tyre.bead, 0.5 * tyre.seat
  under, flange, edge = seat - 0.0032, seat + 0.015, half + 0.004
  hub, bore = 0.035, 0.0175
  inside, outside = offset - 0.006, offset
  top, wide, tread = 0.5 * tyre.outside, 0.5 * tyre.width, 0.08
  shoulder = top - 0.026
  whole = _turnedOf(((bore, outside), (bore, -reach), (hub, -reach),
                     (hub, inside), (under, inside), (under, -edge),
                     (flange, -edge), (shoulder, -wide), (top, -tread),
                     (top, tread), (shoulder, wide), (flange, edge),
                     (under, edge), (under, outside)), sides)
  rubber = _turnedOf(((seat, -half), (flange, -edge), (shoulder, -wide),
                      (top, -tread), (top, tread), (shoulder, wide),
                      (flange, edge), (seat, half)), sides)
  steel = steelWheel(tyre, offset, reach, sides)
  mass = tyre.mass * 8.5 / 7.0
  return _bodyOf(((steel, 7850.0), (rubber, mass / rubber.volume())),
                 whole)


def _turnedOf(points: tuple, sides: int) -> Turned:
  """Returns the turned solid of the closed profile through 'points',
  walked whichever way leaves it solid on the left."""
  profile = tuple(('line', points[k], points[(k + 1) % len(points)])
                  for k in range(len(points)))
  turned = Turned(profile, sides)
  if turned.volume() < 0.0:
    profile = tuple(('line', b, a) for _, a, b in reversed(profile))
    turned = Turned(profile, sides)
  return turned


def _bodyOf(parts: tuple, shape: object) -> Body:
  """Returns the body of 'parts' (each a solid and its density) with
  'shape' for its outline: their masses and moments added, as
  'Body.of' works them for one stuff."""
  mass, first = 0.0, (0.0, 0.0, 0.0)
  second = [[0.0] * 3 for _ in range(3)]
  for solid, density in parts:
    volume, moment, seconds = solid.moments()
    mass += density * volume
    first = plus(first, scaled(moment, density))
    for i in range(3):
      for j in range(3):
        second[i][j] += density * seconds[i][j]
  centre = scaled(first, 1.0 / mass)
  spread = [[second[i][j] - mass * centre[i] * centre[j]
             for j in range(3)] for i in range(3)]
  trace = spread[0][0] + spread[1][1] + spread[2][2]
  inertia = tuple(tuple((trace if i == j else 0.0) - spread[i][j]
                        for j in range(3)) for i in range(3))
  return Body(mass, centre, inertia, shape)


def _bar(centre: Vector, size: Vector, key: str,
         turn: Quaternion = UNTURNED) -> tuple:
  """Returns a solid bar (a box) 'size' (along x, y, z) about 'centre',
  turned by 'turn', with the key of how it looks."""
  return boxShape(*size).moved(centre, turn), key


def _roundBar(centre: Vector, radius: float, length: float, key: str,
              turn: Quaternion) -> tuple:
  """Returns a round rod 'radius' thick and 'length' long about
  'centre', along the y axis turned by 'turn', with the key of how it
  looks."""
  return cylinderShape(radius, length, 16).moved(centre, turn), key


def _joined(pieces: tuple) -> Shape:
  """Returns 'pieces' (each a solid and its look) joined as one solid."""
  shape = None
  for piece, _ in pieces:
    shape = piece if shape is None else shape.joined(piece)
  return shape


#  How thick the frame's bars are, m.
BAR = 0.06


@functools.lru_cache(maxsize=1)
def chassisPieces() -> tuple:
  """The 'chassisPieces' function returns the chassis as built, in the
  world, the car's middle at the origin, piece by piece, each a solid
  and the key of how it looks ('frame', 'bracket', 'chrome', 'rubber',
  'seat', 'engine', 'tank', 'diff', 'shaft'): an open frame of solid
  bars (two side rails, their underside 0.24 m up; a rail inboard over
  each side of each axle, on posts; over each axle an arch, the
  coilovers' tops under its bar; a hoop at the dash, the column's upper
  bushing in it, a beam across over the rack, its lower; a roll hoop;
  the rack's rubber stops); the wishbones'
  HINGES (user: "make more visible that 'here be a hinge!'"): at each
  inner pivot a bracket's two ears either side of the arm's bushing, a
  chrome pin through them along the hinge's line, a nut at each end
  (the lower ones hang under the side rails, the upper ones stand out
  from the inboard rails); a floor plate, a seat in the middle, the
  engine behind it, the fuel tank ahead, the gearbox before the
  engine, a propshaft back to the differential on the rear axle (how
  heavy each is: '_balancedChassis')."""
  pieces = [_bar((0.0, 0.0, 0.225), (0.5, 0.54, 0.03), 'frame')]
  for side in (1, -1):
    pieces.append(_bar((0.0, side * 0.30, 0.27), (3.0, BAR, BAR),
                       'frame'))
    pieces.append(_bar((0.21, side * 0.31, 0.58), (BAR, BAR, 0.56),
                       'frame'))
    pieces.append(_bar((-0.62, side * 0.31, 0.64), (BAR, BAR, 0.68),
                       'frame'))
    pieces.append(_bar((-0.25, side * 0.17, 0.26), (0.42, 0.04, 0.04),
                       'seat'))
    pieces.append(_bar((-0.92, side * 0.11, 0.66), (0.36, 0.12, 0.06),
                       'engine'))
    for x in (0.5 * WHEELBASE, -0.5 * WHEELBASE):
      pieces.append(_bar((x, side * 0.27, 0.48), (0.52, BAR, BAR),
                         'frame'))
      for along in (0.23, -0.23):
        pieces.append(_bar((x + along, side * 0.28, 0.38),
                           (BAR, BAR, 0.16), 'frame'))
      pieces.append(_bar((x, side * 0.27, 0.625), (BAR, BAR, 0.23),
                         'frame'))
      points = _corner(x, side)
      for pivot in points['uppers']:
        pieces.extend(_hingeOf(pivot, (0.08, 0.09),
                               (0.0, -side * 0.01, 0.0)))
      for pivot in points['lowers']:
        pieces.extend(_hingeOf(pivot, (0.08, 0.085), (0.0, 0.0, -0.0025)))
      if x < 0.0:
        pieces.append(_bar(points['inner'], (0.04, 0.04, 0.04),
                           'bracket'))
    end = plus(RACK, (0.0, side * RACK_END, 0.0))
    for away in _GUIDES:
      pieces.append(_bar(plus(end, away), (0.04, 0.04, 0.04), 'frame'))
    pieces.append(_bar(plus(_rackStopOf(side), (0.0, side * 0.012, 0.0)),
                       (0.05, 0.024, 0.05), 'rubber'))
  for x in (1.47, -1.47):
    pieces.append(_bar((x, 0.0, 0.27), (BAR, 0.66, BAR), 'frame'))
  for x in (0.5 * WHEELBASE, -0.5 * WHEELBASE):
    pieces.append(_bar((x, 0.0, 0.77), (BAR, 0.96 + 2.0 * WIDER, BAR),
                       'frame'))
  pieces.append(_bar((0.21, 0.0, 0.86), (BAR, 0.68, BAR), 'frame'))
  pieces.append(_bar((-0.62, 0.0, 0.98), (BAR, 0.68, BAR), 'frame'))
  pieces.append(_bar((COLUMN_FOOT[0] - 0.05, 0.0, 0.44), (BAR, 0.60, BAR),
                     'frame'))
  way, length, turn = _columnLine()
  for along in _COLUMN_HELD:
    pieces.append(_bar(plus(COLUMN_FOOT, scaled(way, along if along > 0.0
                                                else length + along)),
                       (0.08, 0.08, 0.06), 'frame', turn))
  pieces.append(_bar((-0.25, 0.0, 0.32), (0.42, 0.44, 0.08), 'seat'))
  pieces.append(_bar((-0.47, 0.0, 0.58), (0.07, 0.44, 0.48), 'seat',
                     turnAbout((0.0, 1.0, 0.0), -0.2)))
  pieces.append(_bar((-0.92, 0.0, 0.47), (0.40, 0.42, 0.32), 'engine'))
  pieces.append(_bar((0.70, 0.0, 0.38), (0.40, 0.50, 0.20), 'tank'))
  pieces.append(_bar((-0.62, 0.0, 0.29), (0.16, 0.18, 0.14), 'diff'))
  pieces.append(_bar(REAR_DIFF, (0.16, 0.20, 0.18), 'diff'))
  along = turnAbout((0.0, 0.0, 1.0), 0.5 * math.pi)
  back = REAR_DIFF[0] + 0.08
  pieces.append(_roundBar((0.5 * (back - 0.70), 0.0, 0.26), 0.015,
                          -0.70 - back, 'shaft', along))
  return tuple(pieces)


#  A hinge's pin along x: the turn laying a round bar (along y) so.
_ALONG_X = turnAbout((0.0, 0.0, 1.0), 0.5 * math.pi)


def _hingeOf(pivot: Vector, ears: tuple, shift: Vector) -> tuple:
  """Returns a wishbone's hinge on the frame at 'pivot' (its line along
  x): a bracket's two ears, 16 mm thick ('ears': how far across, y,
  and high, z; 'shift' from the pivot), either side of the arm's
  bushing (70 mm long), a chrome pin through them and a hex nut at each
  end."""
  out = [_roundBar(pivot, 0.01, 0.15, 'chrome', _ALONG_X)]
  for way in (1.0, -1.0):
    out.append(_bar(plus(pivot, plus(shift, (way * 0.043, 0.0, 0.0))),
                    (0.016, ears[0], ears[1]), 'bracket'))
    nut = cylinderShape(0.02, 0.014, 6).moved(
      plus(pivot, (way * 0.058, 0.0, 0.0)), _ALONG_X)
    out.append((nut, 'chrome'))
  return tuple(out)


def _balancedChassis(mass: float, moment: float) -> Body:
  """Returns the chassis: its pieces ('chassisPieces') all one stuff
  but the engine's, the two so dense that it weighs 'CHASSIS_MASS' and
  the car (the rest of it 'mass' kg, their first moment along the car
  'moment' kg m, as built) has its centre of mass where the front
  carries 'FRONT_SHARE' of its weight."""
  pieces = chassisPieces()
  engine = _joined(tuple(p for p in pieces if p[1] == 'engine'))
  rest = _joined(tuple(p for p in pieces if p[1] != 'engine'))
  volume, first, _ = rest.moments()
  engineVolume, engineFirst, _ = engine.moments()
  wanted = ((FRONT_SHARE - 0.5) * WHEELBASE * (CHASSIS_MASS + mass)
            - moment)
  across = volume * engineFirst[0] - engineVolume * first[0]
  dense = (CHASSIS_MASS * engineFirst[0] - engineVolume * wanted) / across
  engineDense = (volume * wanted - first[0] * CHASSIS_MASS) / across
  if dense <= 0.0 or engineDense <= 0.0:
    raise ValueError('no engine balances the car at %r' % FRONT_SHARE)
  return _bodyOf(((rest, dense), (engine, engineDense)), chassisShape())


def chassisShape() -> Shape:
  """The 'chassisShape' function returns the chassis as built, in the
  world, the car's middle at the origin: its pieces ('chassisPieces')
  as one solid."""
  return _joined(chassisPieces())


@functools.lru_cache(maxsize=2)
def knucklePieces(side: int) -> tuple:
  """The 'knucklePieces' function returns the knuckle on 'side' (left
  +1), about its middle, piece by piece as 'chassisPieces': an upright
  bar from below the lower ball joint to above the upper, leaning in
  as the steering axis does, the boss the wheel's bearings turn in
  (out into the wheel's dish), the brake's caliper behind it
  ('caliper', out where a disc's rim would pass it, giving the knuckle
  the moment a real one has), the steering arm (behind the axle: the
  toe link's, at the back), the coilover's lug inboard low
  ('knuckle')."""
  lean = turnAbout((1.0, 0.0, 0.0), side * math.atan2(
    _BALL_JOINTS[0][0] - _BALL_JOINTS[1][0],
    _BALL_JOINTS[1][1] - _BALL_JOINTS[0][1]))
  middle = KNUCKLE_MIDDLE
  joints = [(side * (y - middle[0]), z - middle[1])
            for y, z in _BALL_JOINTS]
  centre = (0.0, 0.5 * (joints[0][0] + joints[1][0]),
            0.5 * (joints[0][1] + joints[1][1]))
  boss = (0.5 * (_BOSS[0] + _BOSS[1]) - middle[0],
          _BOSS[1] - _BOSS[0])
  return (_bar(centre, (0.05, 0.05, 0.36), 'knuckle', lean),
          _roundBar((0.0, side * boss[0], AXLE_HEIGHT - middle[1]), 0.075,
                    boss[1], 'knuckle', UNTURNED),
          _bar((-0.115, 0.0, 0.085), (0.06, 0.07, 0.12), 'caliper'),
          _bar((-0.058, 0.0, 0.0), (0.12, 0.03, 0.03), 'knuckle'),
          _bar((0.0, -side * 0.07, -0.08), (0.04, 0.06, 0.05),
               'knuckle'))


@functools.lru_cache(maxsize=1)
def columnPieces() -> tuple:
  """The 'columnPieces' function returns the steering column as built,
  along its own z axis from the plate at its foot (110 mm across, 12 mm
  thick, nought at its underside), piece by piece as 'chassisPieces'
  ('steering', 'spoke', 'grip', 'horn'): up a 30 mm shaft to the
  steering wheel (user: "give the steering wheel more details than just
  'round'"): a hub, three spokes (to either side and down, as the
  wheel is held straight ahead), a rim 330 mm across of a 34 mm grip,
  a horn button in the middle."""
  length = _columnLine()[1]
  plane = length - 0.017
  rim = tuple((0.165 + 0.017 * math.cos(2.0 * math.pi * k / 12),
               plane + 0.017 * math.sin(2.0 * math.pi * k / 12))
              for k in range(12))
  pieces = [(_turnedOf(((0.005, 0.0), (0.11, 0.0), (0.11, 0.012),
                        (0.005, 0.012)), 32).mesh(), 'steering'),
            (_turnedOf(((0.005, 0.012), (0.015, 0.012),
                        (0.015, length - 0.045),
                        (0.005, length - 0.045)), 16).mesh(), 'steering'),
            (_turnedOf(((0.005, length - 0.05), (0.035, length - 0.05),
                        (0.035, length - 0.012),
                        (0.005, length - 0.012)), 16).mesh(), 'spoke'),
            (_turnedOf(((0.005, length - 0.012), (0.028, length - 0.012),
                        (0.028, length), (0.005, length)), 16).mesh(),
             'horn'),
            (_turnedOf(rim, 32).mesh(), 'grip')]
  for x, y in ((0.0, 1.0), (0.0, -1.0), (-1.0, 0.0)):
    size = (0.14 if x else 0.035, 0.14 if y else 0.035, 0.008)
    pieces.append(_bar((0.1 * x, 0.1 * y, length - 0.025), size, 'spoke'))
  return tuple(pieces)


def columnShape() -> Shape:
  """The 'columnShape' function returns the steering column as built:
  its pieces ('columnPieces') as one solid."""
  return _joined(columnPieces())


#  The steering column: its foot (the plate's underside) and the middle
#  of the steering wheel, as built; the plate's hole for the drag link,
#  behind its axis, in its frame. The rack: its middle as built, its
#  ends' reach either way (the tie rods' inner ends), its mass; the
#  drag link's end on it, along it from its middle.
COLUMN_FOOT = (0.5 * WHEELBASE - 0.067, 0.0, 0.37)
COLUMN_TOP = (0.12, 0.0, 0.88)
PLATE_HOLE = (-0.09, 0.0, 0.0)
RACK = (0.5 * WHEELBASE - 0.116, 0.0, 0.30)
RACK_END, RACK_MASS, DRAG_LINK = 0.29, 6.0, -0.15
#  The rack's four guide rods, N/m: they only keep it in line (stiff as
#  the others, they set the car's step, 17 us); where each is held on
#  the chassis from the rack's end it guides, m.
GUIDE = 2e5
_GUIDES = ((0.25, 0.0, 0.0), (0.0, 0.0, 0.2))
#  The rack's stops (user's screenshot: a front wheel folded past lock,
#  its steering arm over centre with its tie rod; in 4 of 6 runs of
#  rough driving one did, at a walk on full lock, the wheels pushing the
#  column past its lock against the hands): rubber buffers on the frame
#  that meet the rack's ends once it has slid 'RACK_TRAVEL' (full lock
#  slides it 48 mm), as stiff as 'RACK_STOP', N/m, damped
#  'RACK_STOP_DAMPING', N s/m, pushing the rack at its middle, along it
#  (at its ends the step's bound counted the rack turning, which a push
#  along it cannot do: at 4e5 N/m, all the step allowed, wheels shoved
#  it 28 mm through); where each sits off the rack's end face.
RACK_TRAVEL, RACK_STOP, RACK_STOP_DAMPING = 0.05, 3e6, 3000.0
_RACK_FACE, _RACK_GAP = RACK_END + 0.02, 0.004
#  Where the column's bushings hold it: from its foot up (over nought),
#  from its top down (under).
_COLUMN_HELD = (0.06, -0.1)


def _rackStopOf(side: int) -> Vector:
  """Returns where the rack's stop on 'side' meets its end, on the
  frame, as built: 'RACK_TRAVEL' and a hair ('_RACK_GAP') past the
  rack's end face."""
  return plus(RACK, (0.0, side * (_RACK_FACE + RACK_TRAVEL + _RACK_GAP),
                     0.0))


def _columnLine() -> tuple:
  """Returns the column's line as built: its way up (a unit), its
  length and its turn (its own z along it)."""
  way = minus(COLUMN_TOP, COLUMN_FOOT)
  length = norm(way)
  way = scaled(way, 1.0 / length)
  return way, length, turnAbout((0.0, 1.0, 0.0), math.atan2(way[0],
                                                             way[2]))


#  The ball joints, lower and upper, across (y, out from the middle) and
#  up (z), m: out in the wheel's dish (the tyre's middle is 0.78 out),
#  the steering axis through them leaning in 10 degrees, meeting the
#  ground 14 mm inside the tyre's middle (user's screenshot, a front
#  wheel folded: they were 0.67 and 0.645 out, the axis meeting the
#  ground 92 mm in, so braking and driving twisted the wheels 2.4 and
#  1.5 degrees about it and, braked on full lock, folded one past it).
_BALL_JOINTS = ((0.73 + WIDER, 0.20), (0.68 + WIDER, 0.48))
#  The knuckle's middle (across, up), m; its boss, across from and to
#  (inside the wheel's dish, the disc 0.82 out); the wheel's bearings
#  along its axle from the tyre's middle, 16 cm apart (10 cm let it
#  lean on them 1.4 degrees rolling).
KNUCKLE_MIDDLE = (0.70 + WIDER, 0.30)
#  How far fore and aft of the axle the lower wishbone's inner pivots
#  are, m (at 0.18, its rods 0.43 long met at 23 degrees: braked, the
#  lower ball joint went back 16 mm, the upper 5, and the knuckle toed
#  out 1.4 degrees).
_LOWER_SPREAD = 0.25
_BOSS = (0.59 + WIDER, 0.77 + WIDER)
_BEARINGS = (-0.02, -0.18)


def _corner(x: float, side: int) -> dict:
  """Returns the points of the corner at 'x' on 'side', as built, in the
  world: the knuckle's middle, its ball joints, steering arm (or toe
  link's end), the coilover's ends, the wishbone's and the toe link's
  inner ends (a tie rod's is on the plate), the wheel's middle, the
  halfshaft's inner joint. The upper wishbone's inner pivots are 0.4 m
  apart, so the coilover (its spring 0.13 m across) passes between its
  arms; the coilover's foot is on the knuckle's lug under the
  halfshaft (forked about it), its top under the arch."""
  caster = 0.02 if x > 0.0 else 0.0
  (lowY, lowZ), (upY, upZ) = _BALL_JOINTS
  axis = lowY + (upY - lowY) * (RACK[2] - lowZ) / (upZ - lowZ)
  arm = (x - 0.116, side * (axis - 0.026), RACK[2])
  inner = (x - 0.116, side * RACK_END, RACK[2])
  return {'knuckle': (x, side * KNUCKLE_MIDDLE[0], KNUCKLE_MIDDLE[1]),
          'upper': (x - caster, side * upY, upZ),
          'lower': (x, side * lowY, lowZ),
          'arm': arm, 'inner': inner,
          'uppers': ((x + 0.20, side * 0.33, 0.48),
                     (x - 0.20, side * 0.33, 0.48)),
          'lowers': ((x + _LOWER_SPREAD, side * 0.30, 0.20),
                     (x - _LOWER_SPREAD, side * 0.30, 0.20)),
          'top': (x, side * (0.42 + WIDER), 0.74),
          'bottom': (x, side * (0.62 + WIDER), 0.22),
          'wheel': (x, side * 0.5 * TRACK, AXLE_HEIGHT),
          'diff': (REAR_DIFF[0], side * DIFF_REACH, REAR_DIFF[2])
          if x < 0.0 else None}


def _rod(first: int, firstPoint: Vector, second: int,
         secondPoint: Vector, length: float) -> Spring:
  """Returns a rod of 'length' between the points: a stiff spring, its
  ends rubber bushings ('ROD', 'ROD_DAMPING')."""
  return Spring(first, firstPoint, second, secondPoint, ROD, length,
                ROD_DAMPING)


def _rearRod(first: int, firstPoint: Vector, second: int,
             secondPoint: Vector, length: float) -> Spring:
  """Returns a rear rod of 'length' between the points: its bushings
  'REAR_ROD' stiff, damped as the front's (user, 2026-11-12: "we should
  take steering away from the rear wheels")."""
  return Spring(first, firstPoint, second, secondPoint, REAR_ROD, length,
                ROD_DAMPING)


def retuned(car: CarBuild, rides: tuple, dampings: tuple) -> CarBuild:
  """The 'retuned' function returns 'car' with its coilovers retuned:
  their springs as stiff as a ride of 'rides' (front, rear, Hz) asks
  ('RIDE' as built), damped 'dampings' (front, rear) of critical
  ('RIDE_DAMPING' as built); each one's rest length moved so it pushes
  as hard at the length it has standing as built (the car stands as
  high; no settling). Bodies, states, drives and the rest as they are
  (user, 2026-11-13: "Let's increase the stiffness of the shock
  absorbers quite a lot ... adjustable with a settings window")."""
  connections = list(car.assembly.connections)
  for corner, index in enumerate(car.links.coilovers):
    link = connections[index]
    axle = 0 if CORNERS[corner][0] > 0.0 else 1
    ride, damping = rides[axle] / RIDE, dampings[axle] / RIDE_DAMPING
    stiffness = link.stiffness * ride ** 2
    bodies, states = car.assembly.bodies, car.states
    length = norm(minus(
      bodies[link.first].placeOf(states[link.first], link.firstPoint),
      bodies[link.second].placeOf(states[link.second], link.secondPoint)))
    push = link.stiffness * (link.rest - length)
    connections[index] = link._replace(
      stiffness=stiffness, rest=length + push / stiffness,
      damping=link.damping * damping * ride)
  return car._replace(assembly=car.assembly._replace(
    connections=tuple(connections)))


def _lengthened(link: Spring, by: float) -> Spring:
  """Returns the rod or coilover 'link' longer by 'by', m."""
  return link._replace(rest=link.rest + by)


def _wheelTurn(side: int) -> Quaternion:
  """Returns how a wheel on 'side' is turned: its own z axis (its axle,
  its disc's face) out to that side."""
  return turnAbout((1.0, 0.0, 0.0), -side * 0.5 * math.pi)


@functools.lru_cache(maxsize=2)
def carBuilt(settle: float, fidelity: Fidelity = FULL) -> CarBuild:
  """The 'carBuilt' function returns the car as built ('CarBuild'): the
  chassis first, the column second, the rack third, the four knuckles,
  the four wheels, in the corners' order ('CORNERS'), its rods (the
  rack's, the drag link, the wishbones, the tie rods and toe links),
  coilovers, bearings, the column's bushings and the motors (a brake in
  each bearing, a halfshaft to each driven wheel, the hands on the
  column);
  standing on 'CAR_ROAD' let settle 'settle' s, all but still, its
  ride height set and settled as faithfully as 'fidelity' says (the
  reference by default). Remembered."""
  knuckles = {}
  for side in (1, -1):
    solid = _joined(knucklePieces(side))
    knuckles[side] = Body.of(solid, KNUCKLE_MASS / solid.volume())
  wheel = carWheel(TYRE, 0.04, 0.16, 32)
  way, length, columnTurn = _columnLine()
  columnSolid = columnShape()
  column = Body.of(columnSolid, COLUMN_MASS / columnSolid.volume())
  rackShape = boxShape(0.05, 2.0 * RACK_END + 0.04, 0.04)
  rack = Body.of(rackShape, RACK_MASS / rackShape.volume())
  others = [(column.mass, COLUMN_FOOT[0]
             + rotated(columnTurn, column.centre)[0]),
            (rack.mass, RACK[0])]
  for x, side in CORNERS:
    points = _corner(x, side)
    others.append((knuckles[side].mass,
                   points['knuckle'][0] + knuckles[side].centre[0]))
    others.append((wheel.mass, points['wheel'][0] + rotated(
      _wheelTurn(side), wheel.centre)[0]))
  chassis = _balancedChassis(sum(m for m, _ in others),
                             sum(m * x for m, x in others))
  bodies = [chassis, column, rack]
  states = [State(chassis.centre), State(plus(
    COLUMN_FOOT, rotated(columnTurn, column.centre)), columnTurn),
    State(RACK)]
  hole = plus(COLUMN_FOOT, rotated(columnTurn, PLATE_HOLE))
  links = [_bushing(0, plus(COLUMN_FOOT, scaled(way, along)), 1,
                    (0.0, 0.0, along), 3e5)
           for along in (_COLUMN_HELD[0], length + _COLUMN_HELD[1])]
  drag = len(links)
  links.append(_rod(1, PLATE_HOLE, 2, (0.0, DRAG_LINK, 0.0),
                    norm(minus(plus(RACK, (0.0, DRAG_LINK, 0.0)), hole))))
  guides = []
  for side in (1, -1):
    end = plus(RACK, (0.0, side * RACK_END, 0.0))
    for away in _GUIDES:
      guides.append(len(links))
      links.append(Spring(0, plus(end, away), 2,
                          (0.0, side * RACK_END, 0.0), GUIDE, norm(away),
                          ROD_DAMPING))
    links.append(Spring(0, _rackStopOf(side), 2, (0.0, 0.0, 0.0),
                        RACK_STOP, _RACK_FACE + _RACK_GAP,
                        RACK_STOP_DAMPING, False, True))
  front = sum(1 for x, _ in CORNERS if x > 0.0)
  share = (chassis.centre[0] + 0.5 * WHEELBASE) / WHEELBASE
  uppers, lowers, steers, coilovers = [], [], [], []
  for index, (x, side) in enumerate(CORNERS):
    points = _corner(x, side)
    k = 3 + index
    knuckle = knuckles[side]
    bodies.append(knuckle)
    middle = points['knuckle']
    states.append(State(plus(middle, knuckle.centre)))

    def own(point: Vector) -> Vector:
      return minus(point, middle)

    rod = _rod if x > 0.0 else _rearRod
    for name, found in (('upper', uppers), ('lower', lowers)):
      found.append((len(links), len(links) + 1))
      for inner in points[name + 's']:
        links.append(rod(0, inner, k, own(points[name]),
                         norm(minus(points[name], inner))))
    steers.append(len(links))
    if x > 0.0:
      inner = plus(RACK, (0.0, side * RACK_END, 0.0))
      links.append(_rod(2, (0.0, side * RACK_END, 0.0), k,
                        own(points['arm']),
                        norm(minus(points['arm'], inner))))
    else:
      links.append(_rearRod(0, points['inner'], k, own(points['arm']),
                            norm(minus(points['arm'], points['inner']))))
    axle = share if x > 0.0 else 1.0 - share
    load = (CHASSIS_MASS + COLUMN_MASS) * 9.81 * axle / front
    line = minus(points['top'], points['bottom'])
    long = norm(line)
    upright = line[2] / long
    corner = load / 9.81
    stiff = corner * (2.0 * math.pi * RIDE) ** 2 / upright ** 2
    damp = (2.0 * RIDE_DAMPING * math.sqrt(stiff * upright ** 2 * corner)
            / upright ** 2)
    coilovers.append(len(links))
    links.append(Spring(0, points['top'], k, own(points['bottom']), stiff,
                        long + load / upright / stiff, damp))
    links.append(Spring(0, points['top'], k, own(points['bottom']),
                        STOP, long + TRAVEL, STOP_DAMPING, True, False))
    links.append(Spring(0, points['top'], k, own(points['bottom']),
                        STOP, long - TRAVEL, STOP_DAMPING, False, True))
  shafts, brakes, motors = [], [], []
  for index, (x, side) in enumerate(CORNERS):
    points = _corner(x, side)
    turn = _wheelTurn(side)
    centre = points['wheel']
    bodies.append(wheel)
    states.append(State(plus(centre, rotated(turn, wheel.centre)), turn))
    k, w = 3 + index, 7 + index
    for along in _BEARINGS:
      held = plus(centre, rotated(turn, (0.0, 0.0, along)))
      links.append(_bushing(k, minus(held, points['knuckle']), w,
                            (0.0, 0.0, along), BEARING))
    brakes.append(Drive())
    motors.append(Motor(k, w, (0.0, 0.0, 1.0), brakes[-1]))
  for corner in DRIVEN:
    shafts.append(Drive())
    shafts[-1].slip, shafts[-1].radius = TRACTION_SLIP, 0.5 * TYRE.outside
    motors.append(Motor(0, 7 + corner, (0.0, 0.0, 1.0), shafts[-1],
                        3 + corner, _corner(*CORNERS[corner])['diff'],
                        (0.0, 0.0, OUTER_JOINT)))
  hands = Drive()
  hands.stiffness, hands.damping = HANDS_STIFF, HANDS_DAMPING
  hands.most, hands.reference = HANDS, columnTurn
  steering = Motor(0, 1, (0.0, 0.0, 1.0), hands)
  motors.extend((steering, Drag(0, DRAG_AREA)))
  states = tuple(states)
  links = _rideHeld(tuple(bodies), tuple(links), states,
                    (tuple(coilovers), tuple(steers), tuple(uppers)),
                    steering, fidelity)
  halfshafts = tuple(len(links) + len(CORNERS) + index
                     for index in range(len(DRIVEN)))
  assembly = Assembly(tuple(bodies), links + tuple(motors))
  if settle > 0.0:
    states = carWorld(fidelity).advancedAll(assembly, states, settle)
  return CarBuild(assembly, states, 0, 1, 2, (3, 4, 5, 6), (7, 8, 9, 10),
                  way, columnTurn, tuple(brakes), tuple(shafts), hands,
                  CarLinks(tuple(uppers), tuple(lowers), tuple(steers),
                           tuple(coilovers), halfshafts, drag,
                           tuple(guides)), [1.0] * len(CORNERS),
                  Gearbox(POWER_BOOST))


def _rideHeld(bodies: tuple, links: tuple, states: tuple, tuned: tuple,
              hands: Motor, fidelity: Fidelity) -> tuple:
  """Returns 'links' set up as a car is aligned, standing on its wheels
  on a road without grip (so no tyre holds a wheel where it was built):
  each coilover's rest length so the car rests at the height it is built
  at (the rods carry some of a corner's load: from the load alone it
  sank 46 mm and splayed); each tie rod's and toe link's so its wheel
  points as aligned, the front ones toed out 'TOE_OUT', the rear ones
  toed in 'TOE_IN'; each upper
  wishbone's rods' so its wheel leans 'CAMBER' (built unloaded, under
  its weight the rubber gave: on the road its tyres held the wheels as
  built, rolling they let go over their relaxation length and the rear
  ones toed out 0.5 degrees and leaned in 2). 'tuned' are the corners'
  coilovers, tie rods or toe links and upper rods (pairs), by index
  among 'links'. The driver's 'hands' hold the column straight the while
  (as a shop locks the steering wheel: left free, the front wheels
  wandered together in steer between rounds, 1.5 degrees, then 3.9).
  Each round lets it settle and corrects each by how far it was off
  ('_RIDE_ROUNDS' rounds), stepped as faithfully as 'fidelity' says."""
  coilovers, steers, uppers = tuned
  slick = World(GRAVITY, 1e-3, CAR_ROAD._replace(grip=0.0), None, True,
                None, 'cpu', fidelity)
  for _ in range(_RIDE_ROUNDS):
    settled = slick.advancedAll(Assembly(bodies, links + (hands,)),
                                states, 0.8)
    links = list(links)
    for corner, (x, side) in enumerate(CORNERS):
      index = coilovers[corner]
      link = links[index]
      knuckle = link.second
      sank = (_riseOf(settled, knuckle) - _riseOf(states, knuckle))
      top = link.firstPoint
      bottom = bodies[knuckle].placeOf(states[knuckle], link.secondPoint)
      line = minus(top, bottom)
      links[index] = _lengthened(link, sank * line[2] / norm(line))
      axle = rotated(conjugate(settled[0].turn), rotated(
        settled[7 + corner].turn, (0.0, 0.0, 1.0)))
      toe = math.atan2(-side * axle[0], side * axle[1])
      wanted = side * TOE_OUT if x > 0.0 else -side * TOE_IN
      index = steers[corner]
      links[index] = _lengthened(links[index],
                                 side * (toe - wanted) * _STEER_ARM)
      camber = math.asin(max(-1.0, min(1.0, -axle[2])))
      for index in uppers[corner]:
        links[index] = _lengthened(links[index],
                                   (CAMBER - camber) * _CAMBER_LEVER)
    links = tuple(links)
  return links


#  The alignment: the camber every wheel is set to, the front wheels'
#  toe-out and the rear wheels' toe-in, each wheel, rad (user,
#  2026-11-12: "front .15 deg toe out, rear .15 deg toe in per wheel");
#  how far a tie rod or toe link lengthens to turn its
#  wheel a radian (its steering arm), and an upper wishbone's rods to
#  lean it a radian (the ball joints apart, as the rods lie), m.
CAMBER = math.radians(-0.5)
TOE_OUT, TOE_IN = math.radians(0.15), math.radians(0.15)
_STEER_ARM, _CAMBER_LEVER = 0.119, 0.25


def _riseOf(states: tuple, knuckle: int) -> float:
  """Returns how high 'knuckle' is over the chassis (body nought), in
  the chassis' own frame (as pitched or rolled)."""
  chassis = states[0]
  return rotated(conjugate(chassis.turn), minus(states[knuckle].place,
                                                chassis.place))[2]


#  How many rounds '_rideHeld' takes to set the coilovers.
_RIDE_ROUNDS = 4


def _bushing(first: int, firstPoint: Vector, second: int,
             secondPoint: Vector, stiffness: float) -> Spring:
  """Returns a bushing between the points: a spring of no length,
  'stiffness' N/m, damped as a bearing's."""
  return Spring(first, firstPoint, second, secondPoint, stiffness, 0.0,
                BEARING_DAMPING)


def wheelSpinOf(car: CarBuild, states: tuple, corner: int) -> float:
  """The 'wheelSpinOf' function returns how fast the wheel at 'corner'
  turns about its axle on the car (on the chassis: its knuckle, on stiff
  rubber, shakes; launching, at +-2.4 rad/s, read as wheelspin), rad/s,
  rolling forward counted up."""
  wheel = car.wheels[corner]
  axle = rotated(states[wheel].turn, (0.0, 0.0, 1.0))
  left = rotated(states[car.chassis].turn, (0.0, 1.0, 0.0))
  sign = 1.0 if dot(axle, left) > 0.0 else -1.0
  return sign * dot(minus(states[wheel].spin, states[car.chassis].spin),
                    axle)


def drive(car: CarBuild, states: tuple, throttle: float,
          seconds: float) -> None:
  """The 'drive' function sets the halfshafts and the brakes for the
  next 'seconds' as 'throttle' says (-1 to 1) and the car is in
  'states': forward, the engine drives through its gearbox ('car.
  gearbox', 'Gearbox.driven': its torque at its revolutions in the gear
  it is in, shifting as an automatic does) and its open differential,
  each driven wheel ('DRIVEN') an equal share (a wheel spinning, its
  shaft's traction control takes its drive back at every step,
  'TRACTION_SLIP'); back, while the car
  still rolls forward, each brake brakes its wheel, a friction brake
  ('BRAKE_GRIP', no harder than 'BRAKE_FRONT' or 'BRAKE_REAR' times how
  far back, enough to lock a wheel; worked out at every step, it only
  ever opposes the wheel's turning on its knuckle; the anti-lock lets a
  locking wheel's go, 'ANTILOCK_SLIP'; the engine runs on, free), and
  once the car has all but stopped the engine drives it backward (in
  first, 'REVERSE' of its torque); nought, they let go. 'handbrake'
  after it pulls the handbrake."""
  for brake in car.brakes:
    brake.torque, brake.damping, brake.most = 0.0, 0.0, 0.0
  for shaft in car.shafts:
    shaft.torque = 0.0
  speed = speedOf(car, states)
  share = 1.0 / len(DRIVEN)
  spin = share * sum(wheelSpinOf(car, states, corner)
                     for corner in DRIVEN)
  if throttle < 0.0 and speed > 0.5:
    car.gearbox.driven(spin, speed, 0.0, seconds)
    radius = 0.5 * TYRE.outside
    for corner, brake in enumerate(car.brakes):
      most = BRAKE_FRONT if CORNERS[corner][0] > 0.0 else BRAKE_REAR
      rim = radius * wheelSpinOf(car, states, corner)
      locked = (speed - rim) / max(speed, 3.0) > ANTILOCK_SLIP
      share = car.antilock[corner]
      step = (ANTILOCK_LET if locked else ANTILOCK_TAKE) * seconds
      goal = ANTILOCK_LEAST if locked else 1.0
      share += max(-step, min(step, goal - share))
      car.antilock[corner] = share
      brake.damping, brake.most = BRAKE_GRIP, most * -throttle * share
    return
  car.antilock[:] = [1.0] * len(CORNERS)
  whole = car.gearbox.driven(spin, speed, throttle, seconds)
  for corner, shaft in zip(DRIVEN, car.shafts):
    shaft.torque = _sideOf(car, states, corner) * share * whole


#  The traction control (the car's electronics, as a real car's: with
#  an open differential a wheel unloaded in a turn, or both launching,
#  spun up): past this share of the car's speed (3 m/s at least) a
#  driven wheel's rim outruns it, its shaft gives back its drive, all of
#  it by twice that (the other, gripping, keeps its own), worked out in
#  the shaft at every step ('Drive.slip'; once a frame, braking the
#  wheel, it never saw the rear corners hop at 31 Hz).
TRACTION_SLIP = 0.08
#  The anti-lock (the car's electronics too; "consequences": braked
#  hard, every wheel locked and left a skid): a wheel turning slower
#  than the car by this share of its speed (3 m/s at least) lets go of
#  its brake at 'ANTILOCK_LET' a second, to no less than
#  'ANTILOCK_LEAST' of it, and takes it back at 'ANTILOCK_TAKE' (our
#  tyres' grip does not fall as they slide, so a locked car brakes at
#  9.8 m/s²; so it brakes at ~9.3, steering kept).
ANTILOCK_SLIP, ANTILOCK_LEAST = 0.2, 0.1
ANTILOCK_LET, ANTILOCK_TAKE = 10.0, 10.0


def handbrake(car: CarBuild, pulled: bool) -> None:
  """The 'handbrake' function, 'pulled', locks the rear wheels for the
  next frame (after 'drive', which lets every brake go): each rear brake
  'HANDBRAKE' N m, gripping 'HANDBRAKE_GRIP'; let go, it leaves them as
  'drive' set them."""
  if not pulled:
    return
  for corner, brake in enumerate(car.brakes):
    if CORNERS[corner][0] < 0.0:
      brake.damping, brake.most = HANDBRAKE_GRIP, HANDBRAKE


def _sideOf(car: CarBuild, states: tuple, corner: int) -> float:
  """Returns one if the wheel at 'corner''s own axis points left on the
  chassis, else minus one (its motor twists it forward the other
  way)."""
  axle = rotated(states[car.wheels[corner]].turn, (0.0, 0.0, 1.0))
  left = rotated(states[car.chassis].turn, (0.0, 1.0, 0.0))
  return 1.0 if dot(axle, left) > 0.0 else -1.0


def steeringOf(car: CarBuild, states: tuple) -> float:
  """The 'steeringOf' function returns how far the column is turned on
  the chassis from straight ahead, rad (left counted up)."""
  chassis, column = states[car.chassis], states[car.column]
  relative = product(conjugate(chassis.turn), column.turn)
  twist = product(relative, conjugate(car.straight))
  along = dot(twist[1:], car.columnAxis)
  return 2.0 * math.atan2(along, twist[0])


def steer(car: CarBuild, wanted: float) -> None:
  """The 'steer' function sets the driver's hands (and the power
  steering) to twist the column on the chassis toward 'wanted' rad from
  straight (within 'STEER_LOCK'): a servo ('Drive'), 'HANDS_STIFF' a
  radian off it, damped by 'HANDS_DAMPING', never harder than
  'HANDS'."""
  car.hands.target = max(-STEER_LOCK, min(STEER_LOCK, wanted))


def _times(matrix: tuple, vector: Vector) -> Vector:
  """Returns 'matrix' times 'vector'."""
  return tuple(sum(matrix[i][j] * vector[j] for j in range(3))
               for i in range(3))


def toeOf(car: CarBuild, states: tuple, corner: int) -> float:
  """The 'toeOf' function returns how far the wheel at 'corner' is
  turned about the upright from straight ahead on the chassis, rad
  (left counted up)."""
  chassis = states[car.chassis]
  axle = rotated(states[car.wheels[corner]].turn, (0.0, 0.0, 1.0))
  axle = rotated(conjugate(chassis.turn), axle)
  side = 1.0 if axle[1] > 0.0 else -1.0
  return math.atan2(-side * axle[0], side * axle[1])


def camberOf(car: CarBuild, states: tuple, corner: int) -> float:
  """The 'camberOf' function returns how far the wheel at 'corner'
  leans from upright on the chassis, rad (its top out counted up: its
  axle, pointing out, then points down)."""
  chassis = states[car.chassis]
  axle = rotated(states[car.wheels[corner]].turn, (0.0, 0.0, 1.0))
  axle = rotated(conjugate(chassis.turn), axle)
  return math.asin(max(-1.0, min(1.0, -axle[2])))


def speedOf(car: CarBuild, states: tuple) -> float:
  """The 'speedOf' function returns how fast the car goes forward, m/s
  (the chassis' velocity along its own x)."""
  chassis = states[car.chassis]
  return dot(chassis.velocity, rotated(chassis.turn, (1.0, 0.0, 0.0)))


def carWorld(fidelity: Fidelity = FULL) -> World:
  """The 'carWorld' function returns the world the car drives in:
  gravity and 'CAR_ROAD', flat, compiled, as faithful as 'fidelity'
  says (the reference by default)."""
  return World(GRAVITY, 1e-3, CAR_ROAD, None, True, None, 'cpu', fidelity)


def ovalWorld(fidelity: Fidelity = FULL) -> World:
  """The 'ovalWorld' function returns the car's world with the oval
  ('oval': a mile round, banked 9 degrees on its straights and 24 in its
  turns, concrete) under 'CAR_ROAD', a safety barrier round its outside
  ('ovalWall'), compiled, as faithful as 'fidelity' says (the reference
  by default)."""
  return World(GRAVITY, 1e-3, CAR_ROAD._replace(terrain=oval(1.0),
                                                wall=ovalWall()),
               None, True, None, 'cpu', fidelity)


def carPlaced(states: tuple, at: Vector, up: Vector) -> tuple:
  """The 'carPlaced' function returns the car's 'states' (as built,
  standing on level ground at nought, heading along x) moved to stand
  at 'at' on ground leaning so its upward normal is 'up' (a banked
  straight: turned about the way it heads, so the car still heads along
  x), every body turned and moved alike, as it moves."""
  lean = turnAbout((1.0, 0.0, 0.0), math.atan2(-up[1], up[2]))
  return tuple(State(plus(at, rotated(lean, state.place)),
                     product(lean, state.turn),
                     rotated(lean, state.velocity),
                     rotated(lean, state.spin)) for state in states)


def trackWorld(fidelity: Fidelity = FULL) -> World:
  """The 'trackWorld' function returns the car's world with its track
  ('track': a hill, a dip, speed humps, washboard, rolling ground; flat
  about the start) under 'CAR_ROAD', compiled, as faithful as
  'fidelity' says (the reference by default)."""
  return World(GRAVITY, 1e-3, CAR_ROAD._replace(terrain=track(0.25)),
               None, True, None, 'cpu', fidelity)
