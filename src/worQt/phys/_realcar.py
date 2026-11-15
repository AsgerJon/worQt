"""
The real car (user, 2026-11-14: "continue to assemble the real car";
the differential "works and looks awesome!"): every part of it ours,
built whole in the small steps. A front-engined, rear-driven single
seater's plan, as the late fifties' (user, 2026-11-15: "Move the seat
back, front engine. Maybe something like the Lotus 12 from 1958? as
copyright allows of course?": its layout only, no name or mark of
anyone's): the soapbox's four corners (the tyre rig's double wishbones,
mirrored; the front ones steered by the rack from a long column passing
the engine on its left, the rear ones held by tie rods,
'_soapbox.addCorners', 'addSteering'), the drivetrain bench's engine,
clutch, dog-leg transaxle and differential ('_drivetrain.addDrivetrain')
moved so the differential sits on the rear axle at the wheels' height,
the gearbox just ahead of it, the engine with its flywheel and clutch
'REACH' further ahead behind the front axle, the input shaft reaching
forward to them as the propshaft, under the driver in a tunnel;
everything turning in the chassis; the differential's side gears turning
in its carrier, each driving a half shaft through a constant velocity
joint at either end (a ball joint, 'Tie', and the two shafts' turns
about their own axes held equal, 'GearMesh' one tooth to one, the same
way: swinging across the axis as the wheel rises adds nothing) to its
rear wheel. The engine's block and the gearbox's case are the chassis'
(their mass on it, the engine's twist taken back by it). The driver (the
walker) sits in the tub between the engine and the gearbox. Its brakes
have an anti-lock system and a handbrake on the rear calipers
('Antilock').

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
from ._assembly import DiscBrake, Hinge, Housed, Tie
from ._body import Body, State
from ._drivetrain import APEX, DIFF_MODULE, OUTPUT_HEIGHT, SHAFT_HEIGHT
from ._drivetrain import SIDE, SPIDER
from ._drivetrain import CLUTCH_AT, FLYWHEEL_AT
from ._drivetrain import DrivetrainControls, DrivetrainLayout
from ._drivetrain import addDrivetrain, carrierPieces
from ._drivetrain import casePieces, flywheelPieces
from ._drivetrain import gearShape, idlerShape, inputPieces, outputPieces
from ._drivetrain import _freeGear, spiderShape
from ._rig import HUB_HEIGHT, LOWER_PIVOT_Y, LOWER_SPREAD, SHOCK_TOP
from ._rig import STEEL, TIE_INNER, UPPER_BALL, UPPER_PIVOT_Y
from ._rig import UPPER_SPREAD, TuneUp, WheelSetup
from ._rig import _bar, _box
from ._shape import Shape, cylinderShape
from ._shock import Shock, coilOf
from ._soapbox import _joined, _sided, _summed
from ._soapbox import _sidedShape, addCorners, addSteering
from ._strut import addStrutCorners
from ._tyred import _WALKER_ON_RUBBER
from ._vectors import Vector, cross, dot, norm, plus, product, rotated
from ._vectors import scaled, turnAbout

#  The car: its wheelbase, m (the engine and the driver between the
#  axles); its corners, front left, front right, rear left, rear right.
WHEELBASE = 2.8
CORNERS = ((0.0, 1.0), (0.0, -1.0), (-WHEELBASE, 1.0),
           (-WHEELBASE, -1.0))
#  How far the drivetrain bench's parts are moved into the car's frame:
#  the differential's apex onto the rear axle, at the wheels' height;
#  how much further ahead the engine's flywheel and clutch sit, m (the
#  engine well behind the front axle, its block clear of the tub by 0.28
#  m: at 1.0 the car, its driver in it, stood 56 % on its front wheels;
#  the input shaft the propshaft); the crank's height in the car, m.
SHIFT = (-WHEELBASE - APEX, 0.0, HUB_HEIGHT - OUTPUT_HEIGHT)
REACH = 0.7
CRANK = SHAFT_HEIGHT + HUB_HEIGHT - OUTPUT_HEIGHT
#  The chassis: its ends, its rails' place across (inner face), height
#  and top, how thick its side plates are, m; its hollow steel's share
#  of solid (a spaceframe's thin tubes: rails, brackets), its side
#  plates' (lightened), its tub's stuff (aluminium sheet over the
#  boards' room, kg/m³); the engine's block's mass (a two litre twin cam
#  four's, its head, sump and ancillaries: the 2.5 litre's 132 kg less
#  its difference, kg) and the gearbox's case's (light alloy, kg) (user,
#  2026-11-15: "the lotus 12 had a curb weight of only 320 kg. Also,
#  it's engine was naturally aspirated inline 4 with DOHC and 1965cc":
#  the block was a V12's 230 kg, the case 60, the frame 79, the car 655
#  kg); the driver's tub (its back, front and either side's inner faces,
#  its floor's top: just ahead of the gearbox's case; its back's top,
#  under the bodywork: user, 2026-11-15, "why is there a soap box lol?",
#  the plywood tub's back stood out of the cockpit), the driver sat in
#  it (their ball's middle), the propshaft's tunnel's half width and
#  top, m.
NOSE, TAIL = 0.45, -WHEELBASE - 0.45
RAIL_IN, RAIL_LOW, RAIL_TOP, PLATE = 0.27, 0.15, 0.27, 0.004
HOLLOW, PLATED, TUB_SKIN = 0.09, 0.4, 250.0
BLOCK_MASS, CASE_MASS = 115.0, 25.0
#  How much lighter than solid steel (or than as they are elsewhere, the
#  soapbox's and the rigs') the car's moving parts are built, a share of
#  each one's mass (and moments: the same shape in lighter stuff): its
#  wishbones and column tubes, its front knuckles cast alloy, its wheels
#  magnesium on the period's narrow tyres, its half shafts hollow, its
#  flywheel a racing one, its gearbox's and differential's gears and
#  shafts lightened (webbed, bored: a light single seater's transaxle,
#  the dog-leg kept: user, 2026-11-15, "the lotus *did* have sequential
#  transmission, but just stick with the dog-leg from before, scaled
#  appropriately"; its shape and ratios as they were); its springs and
#  dampers and its brakes' pistons as much softer and smaller as the car
#  is lighter (its ride and its pedal as they were). Its rack as it was.
LIGHTER = {'lower': 0.3, 'upper': 0.3, 'knuckle': 0.36, 'wheel': 0.5,
           'column': 0.5, 'half shaft': 0.5, 'gear': 0.5}
#  The flywheel's mass as built, kg (a racing one; the tune-up sets it,
#  'TuneUp.flywheel': user, 2026-11-15, "the flywheel weight must be
#  adjustable. If it's too heavy. the engine speed falls too slowly").
FLYWHEEL_MASS = 13.5
#  The tank in the tail behind the differential (its fuel and oil): its
#  box, m, and its mass, kg: as heavy as brings the car's middle of mass,
#  its driver in it, to the wheelbase's middle (user, 2026-11-15:
#  "assume the driver weight brings center of gravity back to even
#  between from and rear": the engine 0.3 m further back did most of it,
#  'REACH'; 'test_realcar.test_balanced').
TANK_LOW, TANK_HIGH = (-3.20, -0.15, 0.22), (-2.95, 0.15, 0.40)
TANK_MASS = 12.7
SOFTER = 0.5
TUB_BACK, TUB_FRONT, TUB_SIDE, TUB_FLOOR = -2.00, -1.38, 0.305, 0.165
TUB_TOP = 0.60
SEAT = (TUB_BACK + 0.31, 0.0, TUB_FLOOR + 0.302)
TUNNEL, TUNNEL_TOP = 0.05, CRANK + 0.055
#  The engine: a four, its crankcase and sump from behind the rack back
#  to the flywheel, its head and cam cover narrower over it, its
#  bores right of the middle (the column passes it on the left), m: the
#  block's front and back, its sides (left, right), the head's, the
#  crankcase's top and the head's; its cams' covers' radius (two along
#  the head: twin cam); the bell housing's radius about the crank
#  (round: the column passes close by).
BLOCK_FRONT, BLOCK_BACK = -0.50, -1.10
BLOCK_LEFT, BLOCK_RIGHT, HEAD_LEFT, HEAD_RIGHT = 0.08, -0.15, 0.05, -0.12
BLOCK_TOP, HEAD_TOP = CRANK + 0.08, CRANK + 0.24
CAM, BELL = 0.03, 0.155
#  How far a face sits off another's plane where the two would
#  otherwise overlap facing alike, m (drawn, such faces fight: the depth
#  buffer cannot tell them apart).
SHY = 0.002
#  The column: its pinion's middle on the rack (left of the car's
#  middle, past the engine's side), the steering wheel's middle before
#  the driver, how far apart, m.
COLUMN_FOOT = (TIE_INNER[0] - 0.025, 0.21, TIE_INNER[2])
COLUMN_TOP = (-1.42, 0.10, 0.68)
COLUMN_LENGTH = math.sqrt(sum((a - b) ** 2 for a, b in zip(COLUMN_TOP,
                                                          COLUMN_FOOT)))
#  The shocks: the rig's coil and dampers, stiffer for the engine's
#  weight, their free lengths set so the car rides as built, each wheel
#  within half a millimetre settled on the yard (front, rear: the engine
#  in front now, the car with its driver balanced ('TANK_MASS'); mid-
#  engined, the rear's were the stiffer; the rear ones
#  the struts', a strut rising with its wheel near one to one where the
#  wishbone's shock did 0.71: the coil softer, the dampers so; all of
#  them halved again for the car's lightness, 'SOFTER').
FRONT_SHOCK = Shock(8e4, 0.2051, 1950.0, 4400.0)
REAR_SHOCK = Shock(1.12e5, 0.3948, 3100.0, 6850.0, 0.53, 0.42)
#  The rear half shafts: where their inner joints are out from the
#  car's middle, m (past the differential's housing), where the outer
#  ones are in the wheels' own frames (in from the hub: its housing clear
#  of the upright, 'test_car_geometry'), their radius, m; the joints'
#  coupling's size (the gear rule's pitch, m).
INNER_JOINT, OUTER_JOINT, SHAFT = 0.13, -0.10, 0.014
JOINT_MODULE = 0.05
#  The bodies: the walker, the chassis, the corners (six each), the
#  rack, the column, the drivetrain (thirteen: flywheel to spiders),
#  the side gears (left, right), the half shafts (left, right).
CHASSIS, FIRST_CORNER = 1, 2
#  Each corner's bodies by what they are, corner after corner from
#  'FIRST_CORNER': the front ones' double wishbones, knuckle, wheel and
#  shock's tube and rod; the rear ones on Chapman struts ('_strut': user,
#  2026-11-15, "chapman, that's it!"), the upright with its strut's tube,
#  the wheel and the strut's rod.
FRONT_PARTS = ('lower', 'upper', 'knuckle', 'wheel', 'tube', 'rod')
REAR_PARTS = ('knuckle', 'wheel', 'rod')


def _cornerBodies() -> tuple:
  """Returns each corner's bodies by what they are (index by part), and
  the first body after them."""
  out, at = [], FIRST_CORNER
  for x, _ in CORNERS:
    parts = FRONT_PARTS if x == 0.0 else REAR_PARTS
    out.append({part: at + k for k, part in enumerate(parts)})
    at += len(parts)
  return tuple(out), at


CORNER_BODIES, _AFTER_CORNERS = _cornerBodies()
WHEELS = tuple(corner['wheel'] for corner in CORNER_BODIES)
KNUCKLES = tuple(corner['knuckle'] for corner in CORNER_BODIES)
#  Where the car's parts would otherwise cut into each other (the
#  car-tests, 'test_car_geometry'; user, 2026-11-15: "a sanity check of
#  the geometries that they don't overlap or anything stupid like
#  that"): over the front axle, how far either way the rails are notched
#  and how high their bottom is there, m (the lower wishbones' pivots
#  under them).
NOTCH, NOTCH_LOW = 0.22, 0.19
#  The rails run straight from just behind the rear axle ('RAIL_BACK') to
#  the front notch's end, then as round tubes in to the nose's cross tube
#  and the tail's ('FRAME_NOSE', 'FRAME_TAIL': each tube's end on the
#  left, m), inside the bodywork (their square ends stood out of its
#  narrowing nose and tail: user, 2026-11-15, "at the lower rear of the
#  car are still weird out of place prisms").
RAIL_BACK = -2.85
FRAME_NOSE, FRAME_TAIL = (0.42, 0.10, 0.27), (-3.24, 0.17, 0.27)
RACK, COLUMN = _AFTER_CORNERS, _AFTER_CORNERS + 1
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
    wheel = WHEELS[corner]
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


class ChassisParts(NamedTuple):
  """
  ChassisParts are the chassis' parts by what they are made of, in the
  car's frame: its hollow steel as boxes ('steel': its rails, cross
  members, the corners' brackets, the rear tie rods', the dash hoop, the
  rack's housing) and as round tubes ('rods': each its two ends and its
  radius, m: the brackets out in the open, drawn round, in the physics
  square bars as thick, 'barsOf'), its plates (the front corners' side
  plates), its tub ('wood': aluminium now, 'TUB_SKIN'), the engine's
  block, the gearbox's case and the differential's housing ('case'),
  the tank in the tail ('tank'); all of them inside the bodywork
  ('_bodyshell.insideShell': 'test_car_geometry.test_inside') but the
  front corners' brackets out in the open, to the upper wishbones and
  the shocks' tops, as boxes ('open') and round tubes ('openRods').
  """

  steel: tuple
  rods: tuple
  plates: tuple
  wood: tuple
  block: Shape
  case: tuple
  tank: Shape
  open: tuple
  openRods: tuple

  def barsOf(self, ) -> tuple[Shape, ...]:
    """The 'barsOf' method returns the round tubes (inside and in the
    open) as the physics has them: square bars as thick."""
    return tuple(_bar(start, end, 2.0 * radius)
                 for start, end, radius in self.rods + self.openRods)


def _frontBrackets() -> tuple:
  """Returns the chassis' brackets at the left front corner (in its
  frame): as boxes inside the bodywork (the side plate, first; the lower
  wishbone's ears, as the soapbox's, '_cornerBrackets'), as boxes in the
  open (the upper wishbone's ears) and as round tubes in the open (their
  ends and radius: the upper wishbone's two arms out to its ears, the
  shock's top's frame, a V out to over its eye and a stem down to
  it)."""
  upper = UPPER_BALL[2]
  boxes = [_box((-0.30, 0.20 - PLATE, RAIL_LOW), (0.20, 0.20, 0.57))]
  for x in (-LOWER_SPREAD, LOWER_SPREAD):
    for way in (-1.0, 1.0):
      ear = x + way * 0.04
      boxes.append(_box((ear - 0.006, 0.20, 0.13),
                        (ear + 0.006, LOWER_PIVOT_Y + 0.02, 0.19)))
  arms = (UPPER_BALL[0] - UPPER_SPREAD, UPPER_BALL[0] + UPPER_SPREAD)
  open_ = []
  for x in arms:
    for way in (-1.0, 1.0):
      ear = x + way * 0.04
      open_.append(_box((ear - 0.006, UPPER_PIVOT_Y - 0.04, upper - 0.03),
                        (ear + 0.006, UPPER_PIVOT_Y + 0.02, upper + 0.03)))
  rods = tuple(((x, 0.20, upper), (x, UPPER_PIVOT_Y - 0.03, upper), 0.022)
               for x in arms)
  over = (SHOCK_TOP[0], SHOCK_TOP[1], SHOCK_TOP[2] + 0.045)
  rods += tuple(((SHOCK_TOP[0] + x, 0.20, SHOCK_TOP[2] + 0.045), over,
                 0.015) for x in (-0.07, 0.07))
  rods += ((over, (SHOCK_TOP[0], SHOCK_TOP[1], SHOCK_TOP[2] + 0.012),
            0.015),)
  return tuple(boxes), tuple(open_), rods


def _sidedRod(rod: tuple, side: float, at: float) -> tuple:
  """Returns a round tube of the left corner (its ends, its radius) at
  the corner 'at' on 'side'."""
  start, end, radius = rod
  return _sided(start, side, at), _sided(end, side, at), radius


def _chassisParts() -> ChassisParts:
  """Returns the chassis' parts by what they are made of
  ('ChassisParts').
  No two of its faces lie in one plane facing alike where they overlap
  (drawn, they fought, flickering: user, 2026-11-15, "a thing in the
  engine"): the cross members end at the rails' inner faces, the dash
  hoop's bar at its posts', the tub's floor 'SHY' over the rails'
  bottoms. The tub's front and back walls leave the propshaft a gap
  (closed over it at the back), its tunnel (steel) over it between them;
  a cross member under the bell housing."""
  ends = (RAIL_BACK, -NOTCH, NOTCH)
  steel = [_box((ends[k], side * RAIL_IN - (0.03 if side > 0.0 else 0.0),
                 RAIL_LOW if k % 2 == 0 else NOTCH_LOW),
                (ends[k + 1], side * RAIL_IN + (0.0 if side > 0.0
                                                else 0.03), RAIL_TOP))
           for side in (-1.0, 1.0) for k in range(len(ends) - 1)]
  inside = RAIL_IN - 0.03
  flywheel = SHIFT[0] + FLYWHEEL_AT + REACH
  steel += [_box((at - 0.04, -inside, RAIL_LOW),
                 (at + 0.04, inside, RAIL_LOW + 0.06))
            for at in (0.0, -WHEELBASE, TUB_BACK - 0.05, flywheel)]
  hoop = TUB_FRONT + 0.02
  for side in (-1.0, 1.0):
    steel.append(_box((hoop - 0.02, side * RAIL_IN - 0.015, RAIL_TOP),
                      (hoop + 0.02, side * RAIL_IN + 0.015, 0.60)))
  steel.append(_box((hoop - 0.02, 0.015 - RAIL_IN, 0.56),
                    (hoop + 0.02, RAIL_IN - 0.015, 0.60)))
  steel.append(_box((TUB_BACK, -TUNNEL, TUNNEL_TOP - 0.012),
                    (TUB_FRONT, TUNNEL, TUNNEL_TOP)))
  for side in (-1.0, 1.0):
    low, high = sorted((side * TUNNEL, side * (TUNNEL - 0.004)))
    steel.append(_box((TUB_BACK, low, TUB_FLOOR),
                      (TUB_FRONT, high, TUNNEL_TOP - 0.012)))
  steel.append(_box((TIE_INNER[0] - 0.02, -0.24, TIE_INNER[2] - 0.02),
                    (TIE_INNER[0] + 0.02, 0.24, TIE_INNER[2] + 0.02)))
  from ._strut import TOE_INNER
  inner = TOE_INNER
  bracket = _box((inner[0] - 0.02, inner[1] - 0.02, inner[2] - 0.035),
                 (inner[0] + 0.02, inner[1] + 0.015, inner[2] + 0.02))
  plates, rods, open_, openRods = [], [], [], []
  middle = 0.5 * (RAIL_LOW + RAIL_TOP)
  for x, end in ((NOTCH, FRAME_NOSE), (RAIL_BACK, FRAME_TAIL)):
    rods += [((x, side * (RAIL_IN - 0.015), middle),
              (end[0], side * end[1], end[2]), 0.015)
             for side in (-1.0, 1.0)]
    rods.append(((end[0], -end[1], end[2]), end, 0.015))
  for at, side in CORNERS:
    if at == 0.0:
      boxes, outside, round_ = _frontBrackets()
      plates.append(_sidedShape(boxes[0], side, at))
      steel += [_sidedShape(shape, side, at) for shape in boxes[1:]]
      open_ += [_sidedShape(shape, side, at) for shape in outside]
      openRods += [_sidedRod(rod, side, at) for rod in round_]
    else:
      boxes, round_ = _strutMounts()
      steel += [_sidedShape(shape, side, at) for shape in
                (bracket,) + boxes]
      rods += [_sidedRod(rod, side, at) for rod in round_]
  back, front, side = TUB_BACK, TUB_FRONT, TUB_SIDE
  wood = [_box((back - 0.025, -side - 0.025, RAIL_LOW + SHY),
               (front + 0.025, side + 0.025, TUB_FLOOR)),
          _box((back - 0.025, -TUNNEL, TUNNEL_TOP),
               (back, TUNNEL, TUB_TOP)),
          _box((back, side, TUB_FLOOR), (front, side + 0.025, 0.52)),
          _box((back, -side - 0.025, TUB_FLOOR), (front, -side, 0.52))]
  for low, high in ((-side - 0.025, -TUNNEL), (TUNNEL, side + 0.025)):
    wood += [_box((back - 0.025, low, TUB_FLOOR), (back, high, TUB_TOP)),
             _box((front, low, TUB_FLOOR), (front + 0.025, high, 0.45))]
  block = _joined((_box((BLOCK_BACK, BLOCK_RIGHT, RAIL_LOW),
                        (BLOCK_FRONT, BLOCK_LEFT, BLOCK_TOP)),
                   _box((BLOCK_BACK + 0.03, HEAD_RIGHT, BLOCK_TOP),
                        (BLOCK_FRONT - 0.03, HEAD_LEFT, HEAD_TOP))))
  pieces = _moved(casePieces(REACH))
  housing = cylinderShape(BELL, FLYWHEEL_AT - CLUTCH_AT + 0.09, 32).moved(
    (SHIFT[0] + REACH + 0.5 * (CLUTCH_AT + FLYWHEEL_AT + 0.01), 0.0,
     CRANK), turnAbout((0.0, 0.0, 1.0), 0.5 * math.pi))
  case = (housing,) + tuple(shape for _, shape in pieces[1:])
  return ChassisParts(tuple(steel), tuple(rods), tuple(plates),
                      tuple(wood), block, case, _box(TANK_LOW, TANK_HIGH),
                      tuple(open_), tuple(openRods))


def _strutMounts() -> tuple:
  """Returns the chassis' mounts at the left rear corner (in its frame)
  as boxes (the mount's cup over the rod's ball, the radius rod's
  bracket on the rail's outside) and as round tubes (their ends and
  radius: the strut's tower, two legs up from the rail to the cup, both
  ahead of the axle: the half shaft passes behind them)."""
  from ._strut import RADIUS_FRONT, STRUT_TOP
  top = STRUT_TOP
  legs = tuple(((top[0] + x, RAIL_IN - 0.015, RAIL_TOP - 0.01),
                (top[0], top[1] - 0.05, top[2] + 0.025), 0.015)
               for x in (-0.06, 0.12))
  cup = _box((top[0] - 0.03, top[1] - 0.06, top[2] + 0.005),
             (top[0] + 0.03, top[1] + 0.02, top[2] + 0.035))
  front = RADIUS_FRONT
  bracket = _box((front[0] - 0.025, RAIL_IN, front[2] - 0.025),
                 (front[0] + 0.025, front[1] + 0.02, front[2] + 0.025))
  return (cup, bracket), legs


def chassisPieces() -> tuple:
  """The 'chassisPieces' function returns the chassis by its parts, in
  the car's frame, as drawn: ('frame', its steel: its boxes, its round
  tubes round, '_tubes'), ('cockpit', the tub: the cockpit's floor and
  sides, dark), ('block', the engine's block), ('cover', its twin cams'
  covers along its head: user, 2026-11-15, "naturally aspirated inline
  4 with DOHC"), ('case', the gearbox's case and the differential's
  housing: glass, the gears seen turning), ('tank', in the tail)."""
  from ._tubes import joinedRows, tubeRows
  parts = _chassisParts()
  rods = joinedRows(*(tubeRows(start, end, radius)
                      for start, end, radius in parts.rods +
                      parts.openRods))
  middle, height = 0.5 * (HEAD_LEFT + HEAD_RIGHT), HEAD_TOP - 0.005
  cams = joinedRows(*(tubeRows((BLOCK_BACK + 0.05, y, height),
                               (BLOCK_FRONT - 0.05, y, height), CAM)
                      for y in (middle - 0.04, middle + 0.04)))
  return (('frame', _joined(parts.steel + parts.open + parts.plates)),
          ('frame', ('rows', rods)), ('cockpit', _joined(parts.wood)),
          ('block', parts.block), ('cover', ('rows', cams)),
          ('tank', parts.tank), ('case', _joined(parts.case)))


def chassisShape() -> Shape:
  """The 'chassisShape' function returns how the chassis meets the ground
  and the walker, in the car's frame: its rails before and behind the
  tub (a block each), the tub's floor and walls, the engine's block."""
  parts = _chassisParts()
  half = RAIL_IN + 0.03
  return _joined((_box((TUB_FRONT + 0.025, -half, RAIL_LOW),
                       (NOSE, half, RAIL_TOP)),
                  _box((TAIL, -half, RAIL_LOW),
                       (TUB_BACK - 0.025, half, RAIL_TOP)))
                 + parts.wood + (parts.block,))


def realCarSolids() -> dict:
  """The 'realCarSolids' function returns the solids the real car's
  bodies are designed as where their shapes say otherwise, by index (for
  '_overlaps.overlapsOf'): the chassis' steel, plates, tub and engine's
  block as built ('chassisShape' is a block over the rails, for the
  ground and the walker; the gearbox's case is glass, hollow)."""
  parts = _chassisParts()
  return {CHASSIS: _joined(parts.steel + parts.open + parts.barsOf()
                           + parts.plates + parts.wood + (parts.block,
                                                          parts.tank))}


@functools.lru_cache(maxsize=1)
def chassisBody() -> Body:
  """The 'chassisBody' function returns the chassis with the engine's
  block and the gearbox's case on it, in the car's frame: its side
  plates lightened steel ('PLATED'), its rails and brackets hollow
  ('HOLLOW'), its tub aluminium ('TUB_SKIN'), the block 'BLOCK_MASS', the
  case 'CASE_MASS' and the tank 'TANK_MASS' kg spread through them; its
  shape 'chassisShape'."""
  parts = _chassisParts()
  case, block = _joined(parts.case), parts.block
  return _summed(((_joined(parts.steel + parts.open + parts.barsOf()),
                   STEEL * HOLLOW),
                  (_joined(parts.plates), STEEL * PLATED),
                  (_joined(parts.wood), TUB_SKIN),
                  (block, BLOCK_MASS / block.volume()),
                  (case, CASE_MASS / case.volume()),
                  (parts.tank, TANK_MASS / parts.tank.volume())),
                 chassisShape())


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
  lines = controls.brakes.lines
  addCorners(CORNERS[:2], setups[:2], (FRONT_SHOCK, FRONT_SHOCK), CHASSIS,
             FIRST_CORNER, RACK, lines[:2], None, world, state, carTurn,
             bodies, states, connections)
  addStrutCorners(CORNERS[2:], setups[2:], REAR_SHOCK, CHASSIS,
                  CORNER_BODIES[2]['knuckle'], lines[2:], world, state,
                  carTurn, bodies, states, connections)
  addSteering(CHASSIS, RACK, COLUMN, controls.steer, COLUMN_FOOT,
              COLUMN_TOP, world, state, carTurn, bodies, states,
              connections)
  drive = controls.drive
  addDrivetrain(drive, SHIFT, CHASSIS, CHASSIS, FIRST_DRIVE, SIDES,
                ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0)), world, carTurn,
                850.0, bodies, states, connections, REACH)
  wheels = WHEELS[2:]
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
  connections += [Contact(0, wheel, *_WALKER_ON_RUBBER)
                  for wheel in WHEELS]
  flywheel = FLYWHEEL_MASS if controls.tune is None or (
    controls.tune.flywheel is None) else controls.tune.flywheel
  _lightened(bodies, connections, drive.layout.flywheel, flywheel)
  return Assembly(tuple(bodies), tuple(connections)), tuple(states)


def _lighter(body: Body, share: float) -> Body:
  """Returns 'body' built in stuff 'share' as heavy: its shape, its
  centre, its mass and moments that share."""
  return Body(body.mass * share, body.centre, tuple(
    tuple(share * value for value in row) for row in body.inertia),
              body.shape)


def _lightened(bodies: list, connections: list, flywheel: int,
               heavy: float) -> None:
  """Builds the real car's moving parts lighter ('LIGHTER': each corner's
  by what it is, the column, the half shafts, the gearbox's and the
  differential's gears and shafts; the flywheel 'heavy' kg) and its
  wheels' brakes' pistons smaller ('SOFTER'), in place."""
  shares = {}
  for corner in CORNER_BODIES:
    for part, index in corner.items():
      if part in LIGHTER and not (part == 'knuckle' and 'tube' not in
                                  corner):
        shares[index] = LIGHTER[part]
  for gear in range(FIRST_DRIVE, SIDES[1] + 1):
    shares[gear] = LIGHTER['gear']
  shares[COLUMN] = LIGHTER['column']
  shares[flywheel] = heavy / bodies[flywheel].mass
  for half in HALVES:
    shares[half] = LIGHTER['half shaft']
  for index, share in shares.items():
    bodies[index] = _lighter(bodies[index], share)
  for k, connection in enumerate(connections):
    if isinstance(connection, DiscBrake) and connection.disc in WHEELS:
      connections[k] = connection._replace(
        piston=connection.piston * SOFTER)


def realCarCoils(assembly: Assembly) -> tuple:
  """The 'realCarCoils' function returns how the real car's coils are
  drawn ('coilOf': each corner's shock's tube)."""
  from ._strut import strutCoilOf
  return tuple(coilOf(corner['tube']) if 'tube' in corner else
               strutCoilOf(corner['knuckle'], corner['rod'], side, at)
               for corner, (at, side) in zip(CORNER_BODIES, CORNERS))


@functools.lru_cache(maxsize=1)
def chassisFinish() -> tuple:
  """The 'chassisFinish' function returns how the chassis is drawn: by
  its parts ('chassisPieces'), and its bodywork over them
  ('_bodyshell': the shell and its headrest's fairing 'paint', the
  intake's 'grille', the 'screen'), made once."""
  from ._bodyshell import grilleRows, screenRows, shellRows
  return chassisPieces() + (('paint', ('rows', shellRows())),
                            ('grille', ('rows', grilleRows())),
                            ('screen', ('rows', screenRows())))


def realCarFinishes(assembly: Assembly) -> dict:
  """The 'realCarFinishes' function returns how the real car's bodies are
  drawn, by index: the chassis by its parts (its case glass) under its
  bodywork ('chassisFinish'), each
  front corner's wishbones and knuckle drawn round, each rear's
  upright with its strut's tube ('_cornerlooks': user, 2026-11-15,
  "make it look proper, not these blocky things"),
  each wheel as the brake bench's (rim, tyre, disc), each shock's or
  strut's tube and rod by their profiles, the rack whole, the
  drivetrain as on its bench (moved), the side gears and half shafts
  whole ('gear', 'shaft'); the steering wheel and column: the view's
  own."""
  from ._brakes import discRuns
  from ._carcass import rimRuns
  from ._cornerlooks import armFinish, knuckleFinish, uprightFinish
  from ._strut import strutRodProfile
  from ._shock import shockRuns
  from ._tyred import tyreRuns
  runs = shockRuns()
  out = {CHASSIS: chassisFinish(), RACK: 'rack'}
  for corner, (at, side) in zip(CORNER_BODIES, CORNERS):
    if 'tube' in corner:
      out[corner['lower']] = armFinish(True, side, at)
      out[corner['upper']] = armFinish(False, side, at)
      out[corner['knuckle']] = knuckleFinish(side, at)
      out[corner['tube']] = runs['tube']
    else:
      out[corner['knuckle']] = uprightFinish(side, at)
    out[corner['wheel']] = rimRuns() + tyreRuns() + discRuns()
    out[corner['rod']] = runs['rod'] if 'tube' in corner else (
      ('chrome', strutRodProfile()),)
  parts = ([flywheelPieces(REACH), inputPieces(REACH), outputPieces()]
           + [(('gear', _freeGear(k)),) for k in range(6)]
           + [(('gear', idlerShape()),), carrierPieces(),
              (('gear', spiderShape(1.0)),), (('gear', spiderShape(-1.0)),)])
  for k, pieces in enumerate(parts):
    out[FIRST_DRIVE + k] = _moved(pieces)
  for k, side in enumerate((1.0, -1.0)):
    out[SIDES[k]] = (('gear', sideGearShape(side)),)
    out[HALVES[k]] = (('shaft', halfShaftShape(side)),)
  return out
