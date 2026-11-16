"""
Locomotive is a steam locomotive and its tender (user, 2026-11-16: "let
us go and make a steam locomotive and a bunch of cars being pulled by
it. At first we will have the cylinders moved by the steam just be
actuators"), a 4-6-2 after the 1DesignTool model it is drawn by
(previews/locomotive.glb: its wheels, rods and crossheads where the
model has them): a frame on three coupled driving wheelsets, a leading
bogie on a pivot and a trailing wheelset, each in axleboxes; on either
side a coupling rod on the drivers' crank pins (in two, knuckled at the
main driver's pin: one rod on three pins would hold the axles' springs
together as a beam), a connecting rod from
the main driver's crank pin to a crosshead sliding on its bars; steam
pushing each crosshead from its cylinder ('Ram': a force, set each
step as the valves would admit it); a tender on three wheelsets behind
on a drawbar, a corridor down its middle from the cab to the train
(user, 2026-11-16: walk from the engine back through every car); in the
cab the regulator, the reverser and the brake; buffers at the engine's
front and the tender's back.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import TYPE_CHECKING

import numpy

from worQt.phys._assembly import FourthWall, Hinge, Ram, Slide, Tie
from worQt.phys._body import Body, State
from worQt.phys._shape import boxShape
from worQt.phys._vectors import UNTURNED, rotated, turnAbout, turnOf
from worQt.phys.rail import JOURNAL_AT, Axlebox, wheelsetBody, wheelsetOn
from worQt.phys.rail._crankpin import CrankPin

from worQt.gaming.sandbox._fourthpeep import FourthPeep
from worQt.gaming.sandbox._vehicle import Vehicle

from ._coupling import CarEnd, carApart
from ._dress import boxQuads, partsOf
from ._model import MODEL, carvedOut, modelParts
from ._offrails import putBack, tookOff

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import World

#  The wheels' radii at their nominal circles, m (the model's: drivers
#  2.086 m across, the bogie's 1.016, the trailing wheel's 1.176, the
#  tender's 1.336).
DRIVER, BOGIE_WHEEL = 1.043, 0.508
TRAILING_WHEEL, TENDER_WHEEL = 0.588, 0.668
#  Where the wheelsets stand, m along the frame from the main driver's
#  axle (its own frame's origin, on the rails' top under it; x ahead):
#  the three drivers (leading, main, trailing; 4.5 m coupled, as a
#  Castle's), the bogie's pivot and its wheelsets either side of it,
#  the trailing wheelset.
DRIVERS = (2.25, 0.0, -2.25)
BOGIE_AT, BOGIE_HALF = 5.95, 1.05
TRAILING_AT = -4.5
#  The motion: the cranks' throw (half the piston's 0.66 m stroke), m;
#  the coupling rods' and the connecting rods' planes either side of the
#  middle, m; the connecting rod's length, eye to eye, m; where each
#  cylinder's piston is pushed from (its front cover, on the slide's
#  line at the axles' height), m along; the cranks' angle round from
#  ahead toward up, on the right (y below nought) and the left, rad
#  (quartered, the left leading, as the model has them).
THROW = 0.33
COUPLING_SIDE, CONNECTING_SIDE = 0.9, 1.04
ROD_LONG = 4.4
CYLINDER_AT = 6.0
CRANKS = {-1.0: 0.0, 1.0: 0.5 * math.pi}
#  Steam: the boiler's pressure, Pa (225 psi, a Castle's), on a piston of
#  'BORE' m (16 in), so the force at full regulator; the cut-off in full
#  gear (steam admitted for so much of each stroke, then shut).
PRESSURE, BORE = 1.55e6, 0.406
FORCE = PRESSURE * math.pi * 0.25 * BORE * BORE
CUTOFF = 0.75
#  Masses, kg: the engine's frame with its boiler and cab (the sprung
#  part, 77.4 t: the drivers carrying 20 t an axle, the trailing
#  wheelset 14 t, the bogie 18 t), its centre of mass this far ahead of
#  the main axle, m (where those loads balance); the bogie's frame;
#  the tender loaded, less its wheelsets.
ENGINE_MASS, ENGINE_MIDDLE = 77.4e3, 0.2456
BOGIE_MASS = 3.0e3
TENDER_MASS = 44.0e3
STEEL = 7850.0
#  The axleboxes: stiffness, N/m (along, across, up: horn guides of steel
#  ahead and across, laminated springs up), damping, N s/m; how far each
#  box's spring is pressed under its share, m (its box set that much
#  low, so the frame stands at its height loaded).
DRIVER_BOX = ((5e7, 1e7, 1.5e6), (2e4, 2e4, 3e4))
#  The main driver's and the tender's middle axle's boxes have sideplay
#  (across, soft: on a 150 m curve a middle axle stands 1.7 / 2.5 cm out
#  of line with its neighbours).
MIDDLE_BOX = ((5e7, 1e6, 1.5e6), (2e4, 1e4, 3e4))
TENDER_MIDDLE_BOX = ((3e7, 2e5, 2.0e6), (1e4, 5e3, 3e4))
TRAILING_BOX = ((5e7, 1e6, 1.2e6), (2e4, 1e4, 2e4))
BOGIE_BOX = ((3e7, 1e7, 1.0e6), (1e4, 1e4, 1e4))
TENDER_BOX = ((3e7, 1e7, 2.0e6), (1e4, 1e4, 3e4))
#  The crank pins: stiffness, N/m, and damping, N s/m, alike each way
#  (a rod's own axes turn with it, and it may roll about its length:
#  softer along the pin it rolled soft upward and blew up); light
#  damping (traded with the rods every 2 ms, explicitly; 2e7 holds a
#  full piston's 200 kN to a centimetre). The two rods of a side, each
#  between two ball joints, yaw to take the axles' sideplay.
PIN = ((2e7,) * 3, (2e3,) * 3)
#  The engine's pieces (x from, x to, y half width, z from, z to, m, in
#  its own frame; where the model has them): frames between the wheels,
#  the boiler with its firebox, the firebox's lower part between the
#  frames, the smokebox, the running plate, the cab (open behind: floor,
#  sides, roof, its front the firebox's back), the buffer beam.
ENGINE_PIECES = ((-5.7, 8.4, 0.55, 0.6, 1.7),
                 (-3.5, 5.6, 1.0, 2.1, 3.85),
                 (-3.5, -1.5, 0.9, 1.2, 2.1),
                 (5.6, 8.15, 1.1, 1.4, 3.9),
                 (-3.5, 8.4, 1.4, 2.12, 2.17),
                 (-5.58, -3.5, 1.44, 1.95, 2.05),
                 (-5.58, -3.5, 1.44, 3.99, 4.09),
                 (8.4, 8.64, 1.4, 0.8, 1.3))
CAB_SIDES = ((-5.58, -3.5, 1.34, 1.44, 2.05, 3.99),)
#  Where a rider's ball is held: on the cab's floor, left, m; the levers
#  on the cab's floor before the firebox's back (regulator, reverser,
#  brake: pivots, m), long, m, thrown back from leaning ahead, rad.
SEAT = (-4.6, 0.6, 2.35)
REGULATOR, REVERSER, BRAKE = ((-3.75, 0.35, 2.05), (-3.85, 0.8, 2.05),
                              (-3.85, -0.6, 2.05))
LEVER_LONG, LEVER_NEAR, LEVER_FAR = 0.7, 0.4, -0.5
#  The brake (a train brake: the engine's handle works every vehicle's
#  shoes): at full pull each box's shoes hold, N m, on the drivers, the
#  tender's wheels and a coach's (each about 0.15 of what its wheel
#  presses on its rail, times its radius: ~1 m/s² for the whole train;
#  the engine's and the tender's alone made 0.25).
BRAKE_MOST, TENDER_BRAKE, COACH_BRAKE = 10e3, 6e3, 2.7e3
#  The tender: its middle wheelset this far behind the main axle, m; its
#  wheelsets either side of that, m; its back and front, m (its own
#  frame); its pieces as the engine's (its frame under the corridor, its
#  tank over it, its tank either side of it); the drawbar's joints on
#  the engine's back and the tender's front (x, z), m.
TENDER_AT, TENDER_HALF = -9.65, 2.75
TENDER_ENDS = (-3.86, 4.2)
TENDER_PIECES = ((-3.86, 4.2, 0.9, 0.8, 1.1),
                 (-3.86, 4.2, 0.45, 3.0, 3.66))
TENDER_SIDES = ((-3.86, 4.2, 0.45, 1.44, 1.1, 3.66),)
ENGINE_TAIL, TENDER_NOSE = (-5.2, 1.5), (3.9, 1.5)
#  The tender's corridor (user, 2026-11-16: "make the train, however
#  realistic or not, such that we can walk from the locomotive and back
#  through each car"; the LNER's non-stop tenders had one, down a side;
#  this one runs down the middle, as the coaches' doors do): half its
#  width, m; its floor's top at the tender's back (a coach's floor) and
#  front (the cab's), m over the rails' top, its floor 'CORRIDOR_DEEP'
#  thick; its roof this high over its floor (drawn: the eyes 1.65 m up
#  pass under it; the tank's solid over it from 'TENDER_PIECES' up).
CORRIDOR_HALF = 0.45
CORRIDOR_FLOOR, CORRIDOR_DEEP = (1.15, 2.05), 0.05
CORRIDOR_HIGH = 1.95
#  The buffers' heads, m along their bodies' own x (where the model has
#  them): the engine's front, the tender's back.
ENGINE_HEAD, TENDER_HEAD = 8.64, -4.49
#  How the corridor is drawn (a look each: its floor, its lining).
CORRIDOR_LOOKS = {'floor': ((118, 82, 52), 0.0, 0.7),
                  'lining': ((222, 208, 176), 0.0, 0.8)}
#  Bars (the coupling and connecting rods, the drawbar), m thick and
#  deep; the crosshead (with its piston and rod), m.
ROD_THICK, ROD_DEEP = 0.08, 0.16
CROSSHEAD = (0.5, 0.25, 0.35)
#  How the train touches what is spawned (stiffness, damping, grip,
#  bristle, its damping, its edges met every so many m).
TRAIN_LAW = (1e6, 1.0, 0.5, 1e6, 2e3, 0.2)
#  A wheelset's own axes in the engine's as it stands ('wheelsetOn': x
#  ahead, y down, z to the left), as columns.
WHEEL_AXES = ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
#  Which of the model's parts each body wears: the engine's (the frame,
#  the boiler and the rest that do not move on it, the valve gear drawn
#  where it stands), the bogie's, the tender's.
ENGINE_PARTS = ('frame', 'cylinders', 'boiler', 'smokebox', 'chimney',
                'domes', 'cab', 'brakes', 'drawbar', 'combination_lever_l',
                'combination_lever_r', 'valve_rod_l', 'valve_rod_r',
                'radius_rod_l', 'radius_rod_r', 'expansion_link_l',
                'expansion_link_r', 'eccentric_rod_l', 'eccentric_rod_r')
TENDER_PARTS = ('tender_frame', 'tender_body', 'tender_coal')
WHEEL_PARTS = ('driver_1', 'driver_2', 'driver_3', 'trailing_wheel',
               'bogie_wheel_1', 'bogie_wheel_2', 'tender_wheel_1',
               'tender_wheel_2', 'tender_wheel_3')
#  The model's sides: its '_l' parts on the engine's right (y below
#  nought), its '_r' on the left.
MODEL_SIDES = {-1.0: '_l', 1.0: '_r'}


def _blocks(pieces: tuple) -> object:
  """Returns 'pieces' (x from, x to, y half width, z from, z to) as one
  shape of boxes."""
  shape = None
  for x0, x1, half, z0, z1 in pieces:
    box = boxShape(x1 - x0, 2.0 * half, z1 - z0).moved(
      (0.5 * (x0 + x1), 0.0, 0.5 * (z0 + z1)), UNTURNED)
    shape = box if shape is None else shape.joined(box)
  return shape


def _sides(pieces: tuple, shape: object) -> object:
  """Returns 'shape' with 'pieces' (x from, x to, y from, y to, z from,
  z to: a side's) added on both sides."""
  for x0, x1, y0, y1, z0, z1 in pieces:
    for way in (1.0, -1.0):
      shape = shape.joined(boxShape(x1 - x0, y1 - y0, z1 - z0).moved(
        (0.5 * (x0 + x1), way * 0.5 * (y0 + y1), 0.5 * (z0 + z1)),
        UNTURNED))
  return shape


def _weighted(shape: object, mass: float, middle: float) -> Body:
  """Returns 'shape' as a body of 'mass' kg whose centre of mass lies
  'middle' m along x: its shape of one stuff, a ballast block in the
  frames (inside its shape, at its far end the way the centre must
  move) taking up what the shape's own centre misses."""
  plain = Body.of(shape, 1.0)
  volume = plain.mass
  lacking = middle - plain.centre[0]
  if abs(lacking) < 1e-6:
    return Body.of(shape, mass / volume)
  at = 7.5 if lacking > 0.0 else -4.5
  ballast = mass * lacking / (at - plain.centre[0])
  body = Body.of(shape, (mass - ballast) / volume)
  block = Body.of(boxShape(0.5, 0.9, 0.9), 1.0)
  block = Body(ballast, (at, 0.0, 1.1), tuple(
    tuple(ballast / block.mass * x for x in row) for row in block.inertia),
               None)
  return _joined(body, block)


def _joined(one: Body, two: Body) -> Body:
  """Returns two bodies made one (their masses, their centre of mass,
  their inertias about it by the parallel axes), 'one''s shape."""
  mass = one.mass + two.mass
  centre = tuple((one.mass * a + two.mass * b) / mass
                 for a, b in zip(one.centre, two.centre))
  inertia = [[0.0] * 3 for _ in range(3)]
  for body in (one, two):
    d = tuple(c - m for c, m in zip(body.centre, centre))
    square = sum(x * x for x in d)
    for i in range(3):
      for j in range(3):
        inertia[i][j] += body.inertia[i][j] + body.mass * (
          (square if i == j else 0.0) - d[i] * d[j])
  return Body(mass, centre, tuple(tuple(row) for row in inertia),
              one.shape)


@functools.lru_cache(None)
def engineBody() -> Body:
  """Returns the engine's frame, boiler and cab as one body
  ('ENGINE_PIECES', the cab's sides), 'ENGINE_MASS' kg, its centre of
  mass 'ENGINE_MIDDLE' ahead of the main axle."""
  shape = _sides(CAB_SIDES, _blocks(ENGINE_PIECES))
  return _weighted(shape, ENGINE_MASS, ENGINE_MIDDLE)


def corridorFrame() -> tuple:
  """The 'corridorFrame' function returns the tender's corridor's frame
  (its own frame's origin on the middle of its floor's top, its x up the
  slope to the front): (that place, the turn there as a matrix, as a
  turn, the floor's length along the slope)."""
  back, front = TENDER_ENDS
  low, high = CORRIDOR_FLOOR
  rise, run = high - low, front - back
  angle = math.atan2(rise, run)
  matrix = numpy.array(((math.cos(angle), 0.0, -math.sin(angle)),
                        (0.0, 1.0, 0.0),
                        (math.sin(angle), 0.0, math.cos(angle))))
  return ((0.5 * (back + front), 0.0, 0.5 * (low + high)), matrix,
          turnAbout((0.0, 1.0, 0.0), -angle), math.hypot(rise, run))


@functools.lru_cache(None)
def tenderBody() -> Body:
  """Returns the tender, loaded, as one body ('TENDER_PIECES', its tank
  either side of the corridor 'TENDER_SIDES', the corridor's sloping
  floor), 'TENDER_MASS' kg."""
  middle, _, turn, long = corridorFrame()
  floor = boxShape(long, 2.0 * CORRIDOR_HALF, CORRIDOR_DEEP).moved(
    (0.0, 0.0, -0.5 * CORRIDOR_DEEP), UNTURNED).moved(middle, turn)
  shape = _sides(TENDER_SIDES, _blocks(TENDER_PIECES)).joined(floor)
  return Body.of(shape, TENDER_MASS / Body.of(shape, 1.0).mass)


def corridorParts(centre: tuple) -> tuple:
  """The 'corridorParts' function returns the tender's corridor drawn
  (its floor, its walls and its roof, lined), about the tender's body's
  'centre'."""
  middle, matrix, _, long = corridorFrame()
  wall = 0.02

  def tilted(low: tuple, high: tuple) -> list:
    return list(boxQuads(low, high, matrix, middle))
  floor = tilted((-0.5 * long, -CORRIDOR_HALF, 0.0),
                 (0.5 * long, CORRIDOR_HALF, 0.005))
  lining = tilted((-0.5 * long, -CORRIDOR_HALF - wall, CORRIDOR_HIGH),
                  (0.5 * long, CORRIDOR_HALF + wall,
                   CORRIDOR_HIGH + wall))
  for side in (1.0, -1.0):
    low, high = sorted((side * CORRIDOR_HALF,
                        side * (CORRIDOR_HALF + wall)))
    lining += tilted((-0.5 * long, low, 0.0),
                     (0.5 * long, high, CORRIDOR_HIGH))
  return partsOf({'floor': floor, 'lining': lining}, centre)


@functools.lru_cache(None)
def bogieBody() -> Body:
  """Returns the bogie's frame (two side frames over the axleboxes and a
  bolster across, 'BOGIE_MASS' kg), its pivot at its own origin's top."""
  shape = _blocks(((-1.6, 1.6, 1.15, 0.45, 0.75),))
  return Body.of(shape, BOGIE_MASS / Body.of(shape, 1.0).mass)


@functools.lru_cache(None)
def barBody(long: float) -> Body:
  """Returns a steel bar 'long' m along its own x ('ROD_THICK' across,
  'ROD_DEEP' up), its middle at its own origin."""
  return Body.of(boxShape(long, ROD_THICK, ROD_DEEP), STEEL)


@functools.lru_cache(None)
def crossheadBody() -> Body:
  """Returns a crosshead with its piston and piston rod, steel."""
  return Body.of(boxShape(*CROSSHEAD), STEEL)


def pinOf(angle: float, side: float) -> tuple:
  """Returns a crank pin at 'angle' (round from ahead toward up, rad)
  'side' m out along the axle, in the wheelset's own frame (x ahead, y
  down, z to the left, as 'wheelsetOn' stands it)."""
  return (THROW * math.cos(angle), -THROW * math.sin(angle), side)


def crossheadAt(angle: float) -> float:
  """Returns where the crosshead stands, m ahead of the main axle, with
  the crank at 'angle'."""
  up = THROW * math.sin(angle)
  return THROW * math.cos(angle) + math.sqrt(ROD_LONG ** 2 - up * up)


class Locomotive(Vehicle):
  """
  Locomotive is a steam locomotive and its tender on its world's track
  'line' with its main driving axle at 'along' m (standing still where
  it is put; its world has 'tracks', ribbons, and steps its wheelsets
  in a rail world): the engine ('engineBody', its frame: 'bodies''s
  first), its 'wheelsets' (drivers, bogie, trailing, tender), the
  bogie's frame on a pivot ('Hinge'), the 'rods' (coupling and
  connecting, either side), the 'crossheads' on their slide bars
  ('Slide'), each pushed by its cylinder's 'steam' ('Ram', a
  'FourthWall' set each step), the 'tender' on a drawbar (a corridor
  down its middle: 'tenderBody'); buffers at its 'front' and 'back'
  ('CarEnd's), its engine and tender meeting every car not coupled to
  it ('world.cars'). In the cab
  the 'regulator' (how much steam: 'FORCE' at full), the 'reverser'
  (thrown back: running backward) and the 'brake' (each driver's and
  tender wheel's shoes at full, 'BRAKE_MOST' and 'TENDER_BRAKE', and
  every coach's in its 'train' 'COACH_BRAKE': a train brake). Each step
  it acts as its valves would: each cylinder gets steam pushing its
  piston the way the gear runs it, for the first 'CUTOFF' of each
  stroke. A wheelset the rail world finds off its rails it takes off
  ('_offrails.tookOff': a free body held by springs where its boxes and
  pins held it, the engine, the bogie and the tender then meeting the
  ground: 'off'); put back, it is as it was made ('restored').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  seat = SEAT
  name = 'Locomotive'

  #  Public Variables
  along: float
  line: int
  wheelsets: tuple
  boxes: tuple
  rods: tuple
  crossheads: dict
  steam: dict
  tender: int
  train: tuple
  off: dict
  regulator: FourthPeep
  reverser: FourthPeep
  brake: FourthPeep

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, along: float, line: int) -> None:
    Vehicle.__init__(self, )
    self.along, self.line = along, line
    self.wheelsets, self.boxes, self.rods = (), (), ()
    self.crossheads, self.steam, self.tender = {}, {}, None
    self._locals = {}
    self.train, self.off = (), {}
    self.regulator = self.reverser = self.brake = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def placed(self, world: World) -> None:
    """The 'placed' method puts the engine, its wheelsets, bogie, motion
    and tender in 'world', still, each journal in its axlebox, each rod
    on its crank pins, and its levers in the cab. Nothing of it touches
    another part of it or the world's own bodies (held over its rails by
    its wheels it cannot reach them); what is spawned later meets it."""
    track = world.tracks[self.line]
    place, frame = track.frameAt(self.along)
    self.world = world
    self._rows = tuple(tuple(float(x) for x in row) for row in frame)
    self._place = tuple(float(x) for x in place)
    engine = self._spawned(engineBody(), (0.0, 0.0, 0.0), None, 'engine',
                           carApart(world, self, None))
    world.cars.append((engine, self))
    bodies, boxes, wheelsets = [engine], [], []
    for x in DRIVERS:
      wheelsets.append(self._wheelset(track, x, DRIVER))
    trailing = self._wheelset(track, TRAILING_AT, TRAILING_WHEEL)
    bogie = self._spawned(bogieBody(), (BOGIE_AT, 0.0, 0.0), None, 'black')
    world.connected(Hinge(engine, (BOGIE_AT, 0.0, 0.75), (0.0, 0.0, 1.0),
                          bogie, (0.0, 0.0, 0.75), (0.0, 0.0, 1.0)))
    leading = [self._wheelset(track, BOGIE_AT + x, BOGIE_WHEEL)
               for x in (BOGIE_HALF, -BOGIE_HALF)]
    for wheelset, x in zip(wheelsets, DRIVERS):
      boxes += self._boxed(wheelset, engine, x, DRIVER, MIDDLE_BOX
                           if x == 0.0 else DRIVER_BOX, 8.65e3)
    boxes += self._boxed(trailing, engine, TRAILING_AT, TRAILING_WHEEL,
                         TRAILING_BOX, 6.35e3)
    for wheelset, x in zip(leading, (BOGIE_HALF, -BOGIE_HALF)):
      boxes += self._boxed(wheelset, bogie, x, BOGIE_WHEEL, BOGIE_BOX,
                           3.95e3)
    rods, pins = self._motion(engine, wheelsets)
    tender, tenderSets = self._tendered(track, engine)
    for wheelset, x in zip(tenderSets, (TENDER_HALF, 0.0, -TENDER_HALF)):
      boxes += self._boxed(wheelset, tender, x, TENDER_WHEEL,
                           TENDER_MIDDLE_BOX if x == 0.0 else TENDER_BOX,
                           (TENDER_MASS / 6.0))
    self.wheelsets = tuple(wheelsets) + (trailing,) + tuple(leading) + (
      tuple(tenderSets))
    self._bogie = bogie
    self.boxes, self.rods, self.tender = tuple(boxes), rods, tender
    self._pins = pins
    self.bodies = (engine,) + self.wheelsets + (bogie,) + rods + tuple(
      self.crossheads.values()) + (tender, self._drawbar)
    self.regulator = self._levered('regulator', REGULATOR, (
      'Open the regulator', 'Close the regulator'))
    self.reverser = self._levered('reverser', REVERSER, (
      'Reverse', 'Run ahead'))
    self.brake = self._levered('brake', BRAKE, None)
    world.addActor(self)
    if MODEL.is_file():
      self._dressed()

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method sets the brake as its lever stands and lets
    steam into each cylinder as the valves would: pushing the piston the
    way the gear runs the engine (the crank's way round: ahead, or back
    with the reverser thrown), for the first 'CUTOFF' of each stroke, as
    hard as the regulator lets it."""
    derailed = getattr(self.world.solver, 'derailed', ())
    for index in self.wheelsets:
      if index in derailed and index not in self.off:
        frames = () if self.off else (self.frame, self._bogie, self.tender)
        self.off[index] = tookOff(self.world, index, states, TRAIN_LAW,
                                  frames)
    pulled = self.brake.value
    for box in self.boxes:
      if box.wheelset in self.wheelsets[:3]:
        box.brake = BRAKE_MOST * pulled
      elif box.wheelset in self.wheelsets[6:]:
        box.brake = TENDER_BRAKE * pulled
    for coach in self.train:
      for box in coach.boxes:
        box.brake = COACH_BRAKE * pulled
    gear = -1.0 if self.reverser.value > 0.5 else 1.0
    opened = self.regulator.value
    for side, wall in self.steam.items():
      angle = self.crankOf(states, side)
      wall.value = -self.admitted(angle, gear) * FORCE * opened

  def restored(self, ) -> None:
    """The 'restored' method puts every wheelset taken off back on its
    rails as it was made."""
    for index, record in self.off.items():
      putBack(self.world, index, record)
    self.off = {}

  def readout(self, states: tuple) -> str:
    """The 'readout' method returns what the engine says of itself: its
    speed, its regulator, which way it runs, its brake."""
    return '%s    regulator %.0f %% %s    brake %.0f %%' % (
      Vehicle.readout(self, states), 100.0 * self.regulator.value,
      'reversed' if self.reverser.value > 0.5 else 'ahead',
      100.0 * self.brake.value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def front(self, ) -> CarEnd:
    """The 'front' property is the engine's front end: its buffers'
    heads at 'ENGINE_HEAD'."""
    return CarEnd(self.frame, ENGINE_HEAD, 1.0, self)

  @property
  def back(self, ) -> CarEnd:
    """The 'back' property is the tender's back end, where the train's
    first car couples: its buffers' heads at 'TENDER_HEAD'."""
    return CarEnd(self.tender, TENDER_HEAD, -1.0, self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def crankOf(self, states: tuple, side: float) -> float:
    """The 'crankOf' method returns the angle of the main driver's crank
    on 'side' (-1 right, 1 left) in 'states', round from the engine's
    ahead toward its up, rad."""
    main, frame = states[self.wheelsets[1]], states[self.frame]
    pin = rotated(main.turn, pinOf(CRANKS[side], side * CONNECTING_SIDE))
    ahead = rotated(frame.turn, (1.0, 0.0, 0.0))
    up = rotated(frame.turn, (0.0, 0.0, 1.0))
    return math.atan2(sum(p * u for p, u in zip(pin, up)),
                      sum(p * a for p, a in zip(pin, ahead)))

  def admitted(self, angle: float, gear: float) -> float:
    """The 'admitted' method returns which way steam pushes a piston, its
    crank at 'angle' and the engine in 'gear' (1 ahead, -1 back): 1
    ahead, -1 back, 0 shut (past the cut-off of its stroke, or at a
    dead centre)."""
    sine = math.sin(angle)
    way = (1.0 if sine > 0.0 else -1.0 if sine < 0.0 else 0.0) * gear
    if way == 0.0:
      return 0.0
    at = crossheadAt(angle)
    back, ahead = ROD_LONG - THROW, ROD_LONG + THROW
    done = (at - back if way > 0.0 else ahead - at) / (2.0 * THROW)
    return way if done < CUTOFF else 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _stateAt(self, body: Body, local: tuple, axes: tuple = None) -> State:
    """Returns 'body' standing still at 'local' (a point in the engine's
    own frame where its own frame's origin goes), turned by 'axes' (its
    own axes in the engine's, as columns; None: the engine's)."""
    rows, place = self._rows, self._place
    turned = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)) if (
      axes is None) else axes
    centre = tuple(local[i] + sum(turned[i][j] * body.centre[j]
                                  for j in range(3)) for i in range(3))
    world = tuple(place[i] + sum(rows[i][j] * centre[j] for j in range(3))
                  for i in range(3))
    matrix = tuple(tuple(sum(rows[i][k] * turned[k][j] for k in range(3))
                         for j in range(3)) for i in range(3))
    return State(world, turnOf(matrix))

  def _spawned(self, body: Body, local: tuple, axes: tuple, look: str,
               apart: frozenset = None) -> int:
    """Puts 'body' in the world at 'local' ('_stateAt'), apart from
    'apart' (None: every body already there), drawn as 'look'; returns
    its index."""
    world = self.world
    if apart is None:
      apart = frozenset(range(len(world.states)))
    index = world.spawned(body, self._stateAt(body, local, axes),
                          TRAIN_LAW, look, apart)
    self._locals[index] = (local, axes)
    return index

  def _wheelset(self, track: object, x: float, radius: float) -> int:
    """Puts a wheelset of wheels 'radius' m on the track 'x' m along the
    engine from its main axle, still; returns its index."""
    world = self.world
    index = world.spawned(wheelsetBody(radius), wheelsetOn(
      track, self.along + x, 0.0, radius), TRAIN_LAW, 'wheel',
                          frozenset(range(len(world.states))))
    self._locals[index] = ((x, 0.0, radius), WHEEL_AXES)
    return index

  def _boxed(self, wheelset: int, frame: int, x: float, radius: float,
             spring: tuple, share: float) -> list:
    """Holds 'wheelset''s two journals in boxes of 'spring' (stiffness,
    damping) on body 'frame' at 'x' m along it (its own frame's), each
    set low by how far it is pressed under 'share' kg; returns them."""
    stiffness, damping = spring
    pressed = share * 9.81 / stiffness[2]
    boxes = []
    for side in (1.0, -1.0):
      box = Axlebox(wheelset, side, frame, (x, side * JOURNAL_AT,
                                            radius - pressed),
                    stiffness, damping)
      self.world.connected(box)
      boxes.append(box)
    return boxes

  def _motion(self, engine: int, drivers: list) -> tuple:
    """Puts the motion in the world, either side: the coupling rod on
    the three drivers' crank pins (two rods, the leading and main
    drivers' and the main and trailing's: knuckled at the main pin), the
    connecting rod from the main
    driver's crank pin to the crosshead, the crosshead on its slide
    bars, its cylinder's steam pushing it. Returns the rods and the
    pins."""
    world, rods, pins = self.world, [], []
    for side, angle in CRANKS.items():
      up = DRIVER + THROW * math.sin(angle)
      ahead = THROW * math.cos(angle)
      couplings = []
      for first in (0, 1):
        x0, x1 = DRIVERS[first], DRIVERS[first + 1]
        middle = 0.5 * (x0 + x1)
        coupling = self._spawned(barBody(x0 - x1 + 0.3), (
          ahead + middle, side * COUPLING_SIDE, up), None, 'rod')
        for wheelset, x in ((drivers[first], x0), (drivers[first + 1], x1)):
          pin = CrankPin(wheelset, pinOf(angle, side * COUPLING_SIDE),
                         coupling, (x - middle, 0.0, 0.0), *PIN)
          world.connected(pin)
          pins.append(pin)
        couplings.append(coupling)
      at = crossheadAt(angle)
      big = (ahead, side * CONNECTING_SIDE, up)
      small = (at, side * CONNECTING_SIDE, DRIVER)
      along = tuple((s - b) / ROD_LONG for s, b in zip(small, big))
      axes = ((along[0], 0.0, -along[2]), (0.0, 1.0, 0.0),
              (along[2], 0.0, along[0]))
      middle = tuple(0.5 * (s + b) for s, b in zip(small, big))
      connecting = self._spawned(barBody(ROD_LONG + 0.3), middle, axes,
                                 'rod')
      pin = CrankPin(drivers[1], pinOf(angle, side * CONNECTING_SIDE),
                     connecting, (-0.5 * ROD_LONG, 0.0, 0.0), *PIN)
      world.connected(pin)
      pins.append(pin)
      crosshead = self._spawned(crossheadBody(), small, None, 'rod')
      world.connected(Slide(engine, small, (1.0, 0.0, 0.0), crosshead,
                            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
      world.connected(Tie(connecting, (0.5 * ROD_LONG, 0.0, 0.0),
                          crosshead, (0.0, 0.0, 0.0)))
      wall = FourthWall(0.0)
      world.connected(Ram(engine, (CYLINDER_AT, side * CONNECTING_SIDE,
                                   DRIVER), crosshead, (0.0, 0.0, 0.0),
                          wall))
      self.crossheads[side], self.steam[side] = crosshead, wall
      rods += couplings + [connecting]
    return tuple(rods), tuple(pins)

  def _tendered(self, track: object, engine: int) -> tuple:
    """Puts the tender behind the engine on its three wheelsets, a
    drawbar between them; returns the tender and its wheelsets."""
    world = self.world
    tender = self._spawned(tenderBody(), (TENDER_AT, 0.0, 0.0), None,
                           'tender', carApart(world, self, None))
    world.cars.append((tender, self))
    wheelsets = [self._wheelset(track, TENDER_AT + x, TENDER_WHEEL)
                 for x in (TENDER_HALF, 0.0, -TENDER_HALF)]
    back = (ENGINE_TAIL[0], 0.0, ENGINE_TAIL[1])
    front = (TENDER_AT + TENDER_NOSE[0], 0.0, TENDER_NOSE[1])
    long = back[0] - front[0]
    bar = self._spawned(barBody(long), (0.5 * (back[0] + front[0]), 0.0,
                                        back[2]), None, 'rod')
    world.connected(Tie(bar, (0.5 * long, 0.0, 0.0), engine, back))
    world.connected(Tie(bar, (-0.5 * long, 0.0, 0.0), tender,
                        (TENDER_NOSE[0], 0.0, TENDER_NOSE[1])))
    self._drawbar = bar
    return tender, wheelsets

  def _dressed(self, ) -> None:
    """Dresses its bodies in the model's parts ('_model.modelParts'),
    each body its own, in its own frame about its centre, each look one
    mesh: the engine its frame, boiler, cab and valve gear, the bogie
    its frame, each wheelset its wheels, each rod and crosshead its own
    (each side's coupling rod cut at the main driver's pin, the knuckle:
    a triangle goes with the rod its middle lies on), the tender its
    frame, tank and coal with its corridor cut through them
    ('tenderParts') and drawn."""
    parts, looks = modelParts(MODEL)
    wearing = {self.frame: [parts[name] for name in ENGINE_PARTS],
               self._bogie: [parts['bogie']],
               self.tender: list(tenderParts())}
    for index, name in zip(self.wheelsets, WHEEL_PARTS):
      wearing[index] = [parts[name]]
    for k, (side, end) in enumerate(MODEL_SIDES.items()):
      front, back, connecting = self.rods[3 * k:3 * k + 3]
      knuckle = THROW * math.cos(CRANKS[side])
      ahead, behind = [], []
      for places, normals, indices, look in parts['coupling_rod' + end]:
        middles = places[indices.reshape(-1, 3)].mean(1)[:, 0]
        triangles = indices.reshape(-1, 3)
        ahead.append((places, normals, triangles[middles > knuckle]
                      .ravel(), look))
        behind.append((places, normals, triangles[middles <= knuckle]
                       .ravel(), look))
      wearing[front], wearing[back] = [ahead], [behind]
      wearing[connecting] = [parts['connecting_rod' + end]]
      wearing[self.crossheads[side]] = [parts['crosshead' + end]]
    bodies = self.world.assembly.bodies
    for index, meshes in wearing.items():
      local, axes = self._locals[index]
      worn = _worn(meshes, local, axes, bodies[index].centre)
      if index == self.tender:
        worn += corridorParts(bodies[index].centre)
      self.world.dressedWith(index, worn, {**looks, **CORRIDOR_LOOKS})

  def _levered(self, name: str, pivot: tuple, prompts: tuple) -> FourthPeep:
    """Returns a lever working 'name' at 'pivot' on the engine (thrown
    back from leaning ahead), put among the world's levers."""
    lever = FourthPeep(name, self.frame if self.bodies else None, pivot,
                       (0.0, 1.0, 0.0), LEVER_LONG, LEVER_NEAR, LEVER_FAR,
                       prompts)
    self.world.addFourthPeep(lever)
    return lever


@functools.lru_cache(maxsize=1)
def tenderParts() -> tuple:
  """The 'tenderParts' function returns the model's tender ('TENDER_PARTS',
  in the engine's frame) with its corridor cut through it, made once."""
  parts, _ = modelParts(MODEL)
  back, front = TENDER_ENDS
  low, high = CORRIDOR_FLOOR
  past = 0.05 * (high - low) / (front - back)
  return tuple(carvedOut(parts[name], (TENDER_AT + back - 0.05,
                                       TENDER_AT + front + 0.05),
                         CORRIDOR_HALF, (low - past, high + past),
                         CORRIDOR_HIGH + 0.03) for name in TENDER_PARTS)


def _worn(meshes: list, local: tuple, axes: tuple, centre: tuple) -> tuple:
  """Returns the model's 'meshes' (lists of (places, normals, indices,
  look) in the engine's own frame) as a body standing at 'local' turned
  by 'axes' (its own axes in the engine's, as columns; None: the
  engine's) wears them: one mesh a look, its rows (place and normal)
  in the body's own frame about its 'centre'."""
  turned = numpy.eye(3) if axes is None else numpy.array(axes)
  grouped = {}
  for part in meshes:
    for places, normals, indices, look in part:
      if not len(indices):
        continue
      own = (places - numpy.array(local)) @ turned - numpy.array(centre)
      rows = numpy.hstack((own, normals @ turned))
      grouped.setdefault(look, []).append((rows, indices))
  out = []
  for look, pieces in grouped.items():
    rows, indices, at = [], [], 0
    for piece, index in pieces:
      rows.append(piece)
      indices.append(index.astype(numpy.uint32) + at)
      at += len(piece)
    out.append((numpy.vstack(rows).astype(numpy.float32),
                numpy.concatenate(indices), look))
  return tuple(out)
