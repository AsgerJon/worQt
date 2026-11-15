"""
WalkWindow walks a person round one of the 'PLACES' (a car's wheel on
its stand, its tyre built from what it is made of, on the road or
lifted to be spun, the walker shrunk to its height, 'walkingWheel';
the car's ball bearing on its hollow shaft, a motor turning it by its
gears, the walker shrunk to 32 mm to walk through it, 'walkingBearing';
the giant hjulleje's outer ring alone with balls, 'walkingRing'; the
yard, 'walkingYard') seen through their eyes, or flies them as a
game's creative mode does, a grabber in their hands: it pulls in what
it points at, holds it floating before them, punts it away, and gives
them a new ball on asking. WalkView is the view, drawn by the GPU (Qt
Quick 3D, as the car's: user, 2026-11-13, "always on graphics card!"):
the mouse turns the head once clicked into, keys walk and fly. WalkApp
opens the window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import json
import math
import os
import sys
import threading
import time
from typing import NamedTuple

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import QComboBox, QMainWindow
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from ...app import App
from ...engineering.gui import QuantitySlider
from .._assembly import BrakeLine, FourthWall
from .._axle import steeringBench
from .._books import Sleep
from .._brakes import benchFinishes, benchOf
from .._hinges import HINGE_GREASE, hingeBench
from .._shock import benchFinishes as shockFinishes
from .._shock import shockBench, shockCoils
from .._hinges import benchFinishes as hingeFinishes
from .._compiled import fastestDevice, gpuDevice
from .._ground import Ground
from .._body import State
from .._poke import hitOf, poked, reachOf, runMotor
from .._scenes import APRON, BEARING_FIDELITY, MOTOR_FREE, MOTOR_STALL
from .._scenes import SMALL_BEARING
from .._scenes import RING_GRABBER
from .._scenes import WALKER, YARD_GROUND
from .._scenes import carBallGiven, giantBallGiven, groundAt
from .._scenes import oakBallGiven, walkingBearing, walkingRing
from .._scenes import ROAD, WHEEL_DROP, WHEEL_LIFT, walkingWheel
from .._scenes import voidBearing, walkingYard, wheelBallGiven, wheelSkin
from .._hub import HUB_GREASE, hubFinishes, rearHub
from .._assembly import Drive, Humps
from .._rig import LOAD, LOAD_MOST, TABLE_TOP, RigControls, rigCoils
from .._rig import TuneUp, WheelSetup, rigFinishes, rigHumps, tyreRig
from .._soapbox import CHASSIS, COLUMN, CORNERS, FIRST_CORNER, HOLD, SEAT
from .._soapbox import LineKeeper, SoapboxControls, soapbox, soapboxCoils
from .._soapbox import soapboxFinishes
from .._drivetrain import CASE as GEARBOX_CASE, DrivetrainControls
from .._drivetrain import benchFinishes as drivetrainFinishes
from .._drivetrain import drivetrainBench, drivetrainWorked, readingOf
from .. import _realcar
from .._realcar import FLYWHEEL_MASS, FOOT, Antilock, RealCarControls
from .._realcar import realCar
from .._realcar import realCarCoils
from .._realcar import realCarFinishes
from .._carcass import TYRE_YARD, rimFinishes, tyreYard, wheelGiven
from .._laps import LapTimer, lapText
from .._city import CITY_TRACK, cityCourse, cityGround, cityTrack
from .._city import realCarInCity, squareFinishes
from .._crg import ATTRIBUTION
from .._realdriver import CityDriver, RealCarRacer
from .._realoval import ovalGround, parkedFinishes, realCarOnOval
from .._carcass import wheelsOf
from .._tyred import tyredFinishes, tyredGiven, wheelYard
from .._small_steps import THREADS, SmallSteps
from .._small_steps import preloaded
from .._vectors import conjugate, minus, norm, plus, rotated, scaled
from .._walking import Grabber, Walker, flyingOf, wantedOf
from .._world import FULL, Fidelity, World
from ._gpu import GpuView
from ._readings import readingsOf
from ._recorder import Recorder
from ._engine_sound import ENGINE_SIM, EngineSound
from ._toggle import Toggle
from ._tune import TunePanel
from ._steeringwheel import axleFinishes, columnFinish
from ._walkdress import CoilDress, HumpDress, LegsDress, RamDress
from ._walkdress import ParkedDress, SkinDress, TyreDress

#  A frame steps the world on as long as it took since the last, but no
#  less than half of 'FRAME' (s) nor more than two (slow frames slow it
#  down, not the world).
FRAME = 1.0 / 60.0
GRAVITY = (0.0, 0.0, -9.81)
#  How long a thread keeps Python's lock while another waits for it, s
#  (Python's own is 5 ms): the physics' thread lets the lock go at every
#  call into the GPU's driver (a copy, a launch: a dozen or more a
#  step), and got it back only once the window's tick, running Python
#  meanwhile, let it go: up to 5 ms each time, while the GPU stood
#  idle. Headless the car ran at 171 % of real time on the GPU, in the
#  window at 89 % (2026-11-14). The CPU's arrays are read in place, so
#  there it never showed.
SWITCH_INTERVAL = 0.0002


class Place(NamedTuple):
  """
  Place is somewhere to walk: its 'name', how it is 'built' (a function
  returning its assembly and how it starts, the walker first), its
  'ground', the 'grabber' in the walker's hands there, which way they
  look at first, 'yaw' (the view's), the ground's checker, 'tile' m,
  whether bodies there may sleep ('sleeping', a 'Sleep' or None), how
  a ball is 'given' (a function of the assembly, the states and the
  new ball's state, returning them with it last), the 'motor' there may
  be to run (its place among the assembly's motors, its free speed,
  rad/s, and its stall torque, N m, as 'motorTorque' takes them; None
  for none), and
  how far the walker is shrunk there, 'scale' (one: not at all), and
  how it is 'dressed' (None, or a function of nothing returning the
  bodies not drawn, nor their shadows, and the skins drawn over them,
  each with its parts' tones, for the view's 'skins'), how
  faithfully its world is stepped ('fidelity'), and whether the legs
  and rods of the rigs holding its bodies are drawn ('rigs'; not where
  solid supports show what holds them), and the turned bodies painted
  with spiral stripes, so they are seen to turn ('stripes': each its
  index, the paint's colour, how many stripes and how far one climbs a
  turn, m), and the step its world may be stepped in as GPUs step games'
  ('small', s: 'SmallSteps', its touches kept as rules, on the GPU
  where there is one; nought: never, the springs' world 'World' only;
  the 'Small steps' toggle chooses), and whether the springs' world
  can step it at all ('springs'; not the roller bearing's rollers:
  then small steps only, the toggle held on), and how low the walker
  may fall before they are set back where they started, still
  ('respawn', m; None: never; a place with no ground draws none), and
  the bodies drawn as tinted glass, so what turns inside them is seen
  ('glass': their indices; they stay steel as they are stepped), and
  the bodies drawn in finishes of their own ('finishes': None, or a
  function of the assembly returning them as the view's 'finishes'
  takes them, index: a key or runs), each key's look in 'looks' (as the
  view's 'palette' has it: colour, metalness, roughness, casts shadows,
  picture), what the menu gives ('gift', its name: 'Give ball'), and
  how many passes the small steps make a step ('passes': a cord tyre's
  grip on the ground chatters in one) and their grease ('grease', m:
  the rear hub's balls, 'HUB_GREASE'), and the line of the brake the
  window works ('brake', a 'BrakeLine'; None: none), and its coil
  springs drawn ('coils': a function of the assembly returning them as
  'CoilDress' takes them; None: none), and the steering wheel's fourth
  wall point the window works ('steer': the arrow keys turn it, up
  centres it; sat in the car, A and D, let go it comes back straight;
  None: none), and the tyre rig's controls the window works
  ('rig', a 'RigControls': the turntable's speed, the ram's load, the
  humps; None: none), and the soapbox's ('soapbox', a 'SoapboxControls':
  the walker starts sat in its tub, riding it, held on the ramp by its
  brakes; None: none), and the drivetrain's ('drivetrain', a
  'DrivetrainControls': W the throttle (Up standing), the keypad's 0
  the clutch, its 4 5 6 and 1 2 3 the stick (the gate's own rows: R 2 4
  over 1 3 5), N neutral, I the starter; None: none), and the car the
  walker starts sat in ('ride', a 'Ride': the camera riding it, F out of
  it, S its brakes, Space its handbrake, its tune-up; None: none), and
  the robot that drives that car round a course ('racing': a function
  of the assembly and the real car's controls returning it, while 'Robot
  hands' is on, its laps timed: 'RealCarRacer' on the oval, 'CityDriver'
  in town; None: none), and the dresses drawn beside the bodies
  ('extras': None, or a function of the assembly returning them: the old
  car parked on the oval), how the ground's terrain is drawn ('drawn':
  'oval', the oval's surfaces; 'crg', the city lap's road along its rows;
  None, the terrain's grid), and a credit its data asks to be shown
  ('credit', in the readings: the city's heights). A place's ground may
  be a function returning it (the city's, seconds to lay out: made when
  the place is first chosen). Cord
  tyres
  ('wheelsOf') are drawn over their nodes ('TyreDress'), their wheels
  grabbed and punted whole.
  Shrunk, the walker and
  its grabber
  are as 'Walker.scaled' makes them, and the view's near cut and the
  ground drawn shrink alike; time is never slowed (user, 2026-11-13:
  "NEVER SLOW DOWN TIME AGAIN! Let it fall fucking fast!": watched at
  its true pace, a small world's falls are quick, as gravity makes
  them).
  """

  name: str
  built: object
  ground: Ground
  grabber: Grabber
  yaw: float
  tile: float
  sleeping: Sleep
  given: object
  motor: tuple
  scale: float
  dressed: object = None
  fidelity: Fidelity = FULL
  rigs: bool = True
  stripes: tuple = ()
  small: float = 0.0
  springs: bool = True
  respawn: float = None
  glass: tuple = ()
  finishes: object = None
  looks: object = None
  gift: str = 'ball'
  passes: int = 1
  grease: float = 0.0
  brake: BrakeLine = None
  coils: object = None
  steer: FourthWall = None
  rig: RigControls = None
  soapbox: SoapboxControls = None
  drivetrain: DrivetrainControls = None
  ride: object = None
  racing: object = None
  extras: object = None
  drawn: str = None
  credit: str = None


class Ride(NamedTuple):
  """
  Ride is a car the walker starts sat in, riding it (the soapbox, the
  real car): its chassis' body, the walker's ball's middle in its seat
  (in the chassis' own frame), its wheels' tune-up (a 'TuneUp'), its
  steered knuckles' bodies and its anti-lock brakes and handbrake
  (an 'Antilock'; None: its brakes straight off the foot's line, no
  handbrake).
  """

  chassis: int
  seat: tuple
  tune: object
  knuckles: tuple
  brakes: object = None


#  The walker as a game's player moves (user, 2026-11-13: "just make
#  the movement speed not be dogshit", then "Just fucking walking!"):
#  walking 6 m/s, running 12 (Shift), flying 20 (40 with Ctrl), rising
#  10, getting up to speed, walking or flying, at 60 m/s² (a tenth of a
#  second; a person walks 1.6, runs 4); as big, as heavy, jumping as
#  high. Shrunk, as 'Walker.scaled' has it.
PLAYER = Walker(WALKER.radius, WALKER.mass, WALKER.eye, 6.0, 12.0,
                WALKER.legs, WALKER.jump, 20.0, 10.0, 60.0)
#  The bearing's shaft and inner ring painted as a cement truck's drum
#  (user, 2026-11-13: "put some texture or whatevs on the shaft so it's
#  rotation is clearly visible. Like cement trucks."): two orange spiral
#  stripes on the steel, climbing 200 mm a turn (first 50: "make it's
#  travel faster and less blocky": as the shaft turns they travel along
#  it as fast as they climb).
_SHAFT_PAINT = QColor(235, 120, 30)
#  How far the walker is shrunk to walk round the car's bearing (user,
#  2026-11-13: first "player height is a bit larger than inner diameter
#  of the bearing", then "a hollow shaft that is tall enough for the
#  player to walk through"): they stand 32 mm tall (1.75 m at full
#  size), 4 mm under the shaft's 36.3 mm hole, their eyes 30 mm up; the
#  64 mm pitch circle looks to them as a 3.5 m one would at full size.
#  Their grabber there is stronger than the yard's (it is a tool, not a
#  person), holding a steel ball of the bearing (8.4 g: to them as 1.4
#  t) up twice over.
SHRUNK = 0.032 / 1.75
#  The tinted glass the parts round the bearings are drawn in (user,
#  2026-11-13: "i know that glass panels showing the hardware in our
#  sweet 2015 gamer PC's aren't really practical in motor vehicles.
#  BUT... this is a video game. So please implement some tinted glass to
#  replace the steel around the bearings. Think managlass"): pale sky
#  blue, two thirds seen through, glossy.
MANA_GLASS = QColor(150, 215, 255, 85)
#  How far under the void's platform the walker falls before they are
#  set back on it (user, 2026-11-13: "if we fall down we just spawn back
#  on the platform"): 0.3 m, to them as 16 m.
VOID_FALL = -0.3
#  How the rear hub's parts look (user, 2026-11-13: "make the gearhub in
#  the void have more realistically colored textures, and just leave a
#  small bit of transparent glass where the balls are visible"), by
#  their finishes' keys ('hubFinishes'): colour, metalness, roughness,
#  casts shadows, picture ('cast' blotched, 'turned' ringed: the colour
#  times its grey). The disc grey cast iron, its braking faces bare and
#  lighter, its hat painted near black, its rim rusting brown; the hub's
#  flange forged, dark; its wheel's face, the journal and the bearing's
#  rings bright from the lathe and the grinder; the nut zinc plated; the
#  balls polished; the cages glass filled polyamide, black; the axle's
#  plate painted black; the platform aluminium; the hub's raceway ring
#  glass. (Metalness stays low: with nothing round it to mirror, metal
#  draws black.)
HUB_LOOKS = {
  'glass': (MANA_GLASS, 0.0, 0.04, False, None),
  'braking': (QColor(142, 140, 138), 0.3, 0.42, True, 'cast'),
  'hat': (QColor(46, 47, 50), 0.1, 0.55, True, 'cast'),
  'edge': (QColor(112, 92, 76), 0.15, 0.75, True, 'cast'),
  'forged': (QColor(84, 86, 92), 0.25, 0.6, True, 'cast'),
  'machined': (QColor(178, 182, 190), 0.3, 0.3, True, 'turned'),
  'race': (QColor(206, 210, 217), 0.3, 0.18, True, 'turned'),
  'nut': (QColor(196, 198, 202), 0.3, 0.38, True, 'turned'),
  'thread': (QColor(96, 98, 104), 0.25, 0.5, True, 'cast'),
  'ball': (QColor(222, 225, 232), 0.35, 0.12, True, None),
  'cage': (QColor(38, 36, 34), 0.0, 0.55, True, None),
  'axle': (QColor(30, 31, 33), 0.0, 0.45, True, None),
  'platform': (QColor(168, 172, 178), 0.3, 0.45, True, None)}
#  How the wheels of the tyre yard look ('rimRuns', 'TyreDress'): the
#  rim's barrel and flanges gunmetal, the outboard lip polished, its hub
#  and spokes machined bright aluminium; the tyre's rubber near black,
#  its tread a little rougher (metalness low: with nothing round it to
#  mirror, metal draws black).
TYRE_LOOKS = {
  'alloy': (QColor(72, 76, 84), 0.3, 0.32, True, 'turned'),
  'lip': (QColor(222, 226, 232), 0.35, 0.16, True, 'turned'),
  'hub': (QColor(206, 210, 216), 0.3, 0.22, True, 'turned'),
  'spoke': (QColor(214, 218, 224), 0.3, 0.22, True, None),
  'tyre': (QColor(28, 28, 30), 0.0, 0.72, True),
  'sidewall': (QColor(255, 255, 255), 0.0, 0.72, True, 'souffle'),
  'tread': (QColor(22, 22, 24), 0.0, 0.88, True)}
#  How many passes the cord tyre yard's small steps make (one let a
#  fallen wheel's sidewall chatter on the ground and buzz off across
#  it); the tyre yard's steps, s (its wheels on springs: 0.5 ms keeps a
#  tyre's 20 Hz bounce to a tenth of a radian a step).
TYRE_PASSES = 2
TYRED_STEP = 5e-4
#  The brake bench's line (the window's pedal works it: its pressure while
#  the brake is on or B held, else none), the line's pressure the
#  slider starts at (bar: a firm stop's; 2 bar slows the wheel from 20
#  rad/s in half a second), and its looks: the tyre yard's wheel, its
#  disc machined bright, smooth (user, 2026-11-14: "the disks should have
#  that shine. The calibers bright red": no reflections in the scene, so
#  the shine is the suns' highlights on a smooth, light face, its turning
#  rings on it; more metal draws black), the stand's steel, the caliper
#  glossy bright red.
BENCH_LINE = BrakeLine(0.0)
BENCH_BAR = 10.0
BENCH_LOOKS = dict(TYRE_LOOKS)
BENCH_LOOKS.update({
  'disc': (QColor(208, 210, 214), 0.45, 0.16, True, 'turned'),
  'stand': (QColor(96, 100, 108), 0.3, 0.4, True, 'cast'),
  'caliper': (QColor(238, 16, 20), 0.0, 0.22, True)})
#  The hinge bench's steps, s, and its looks: the gantry steel, its
#  brackets zinc, the wishbones blue, their sleeves steel or rubber, the
#  door oak.
HINGE_STEP = 2.5e-4
HINGE_LOOKS = {
  'frame': (QColor(96, 100, 108), 0.3, 0.4, True, 'cast'),
  'bracket': (QColor(196, 178, 96), 0.3, 0.35, True),
  'arm': (QColor(40, 92, 196), 0.1, 0.35, True),
  'sleeve': (QColor(200, 204, 210), 0.3, 0.25, True),
  'rubber': (QColor(22, 22, 24), 0.0, 0.85, True),
  'door': (QColor(150, 104, 58), 0.0, 0.6, True)}
#  The shock bench's looks: the hinge bench's, the damper's tube yellow,
#  its rod chrome (smooth, its turning rings on it), the coil glossy red
#  (user, 2026-11-14: "very visibly"), the weight dark steel.
SHOCK_LOOKS = dict(HINGE_LOOKS)
SHOCK_LOOKS.update({
  'damper': (QColor(240, 196, 40), 0.1, 0.3, True),
  'chrome': (QColor(220, 222, 226), 0.45, 0.12, True, 'turned'),
  'coil': (QColor(226, 18, 24), 0.15, 0.25, True),
  'weight': (QColor(70, 72, 78), 0.3, 0.45, True, 'cast')})
#  The steering bench's fourth wall points (the hands on the steering
#  wheel, the brake's line), how fast the arrow keys turn the wheel
#  (rad/s), how far either way (a hair past the rack's lock), and its
#  looks: the hinge and brake benches', the rim's leather perforated
#  with an orange mark, alloy spokes, a dark hub on a chrome quick
#  release, the badge, the column dark, the rack and pinion steel, the
#  knuckles cast.
AXLE_WALL, AXLE_LINE = FourthWall(0.0), BrakeLine(0.0)
STEER_RATE, STEER_MOST = 2.0 * math.pi, 3.0 * math.pi + 0.3
AXLE_LOOKS = dict(HINGE_LOOKS)
AXLE_LOOKS.update(BENCH_LOOKS)
AXLE_LOOKS.update({
  'grip': (QColor(34, 34, 36), 0.0, 0.8, True, 'leather'),
  'marker': (QColor(255, 118, 18), 0.0, 0.3, True),
  'spoke': (QColor(200, 204, 210), 0.45, 0.22, True),
  'hub': (QColor(40, 40, 44), 0.2, 0.5, True),
  'quick': (QColor(220, 222, 226), 0.45, 0.12, True, 'turned'),
  'badge': (QColor(255, 255, 255), 0.1, 0.3, True, 'badge'),
  'column': (QColor(60, 60, 64), 0.3, 0.4, True),
  'pinion': (QColor(180, 182, 188), 0.4, 0.3, True, 'turned'),
  'rack': (QColor(170, 172, 178), 0.4, 0.3, True, 'turned'),
  'knuckle': (QColor(110, 112, 118), 0.3, 0.45, True, 'cast')})


#  The tyre rig's controls (user, 2026-11-14: "this setup can then put
#  force on the wheel and different speeds. We can then observe breaking
#  at different weights"), its steps, s (the wheel spinning 65 rad/s at
#  20 m/s: at 0.25 ms its knuckle shimmied, the spin's wobble about its
#  axle stepped forward one step at a time and growing; at 0.125 ms
#  steady), its deck's fastest, m/s (user: "the same setup just
#  slower"; steered at 20 the wheel shimmied, its side force swinging 6
#  kN either way: the rigid tyre's; with the tyre's slip law steady at
#  20, side force 0.22 kN), how many humps the
#  toggle bolts on, how its bodies are drawn
#  ('rigFinishes', and the steering wheel on its column as the steering
#  bench's), and its looks: the brake and hinge benches', the boom machine
#  blue, its weights dark, the deck steel grey with its painted stripes
#  and lane, the motor's housing green, the ram's barrel red on a chrome
#  rod, the humps yellow.
RIG = RigControls(Drive(), FourthWall(LOAD), Humps(2), BrakeLine(0.0),
                  FourthWall(0.0), TuneUp())
RIG_STEP, RIG_FASTEST, RIG_HUMPS = 1.25e-4, 20.0, 4
#  How far either way the menu's 'Steer' holds the rig's steering wheel,
#  degrees (a turn: the rack's lock; user, 2026-11-14: "make it so that
#  in the menu i can set the steering wheel angle to hold a particular
#  value").
RIG_LOCK = 360.0
RIG_LOOKS = dict(AXLE_LOOKS)
RIG_LOOKS.update(SHOCK_LOOKS)
RIG_LOOKS.update({
  'boom': (QColor(30, 70, 150), 0.1, 0.4, True),
  'weight': (QColor(70, 72, 78), 0.3, 0.45, True, 'cast'),
  'deck': (QColor(120, 124, 130), 0.3, 0.5, True, 'cast'),
  'stripe': (QColor(236, 236, 236), 0.0, 0.6, True),
  'lane': (QColor(58, 60, 64), 0.0, 0.85, True),
  'housing': (QColor(40, 110, 70), 0.1, 0.4, True),
  'ram': (QColor(200, 30, 30), 0.1, 0.3, True),
  'ramrod': (QColor(220, 222, 226), 0.45, 0.12, True),
  'hump': (QColor(240, 196, 40), 0.1, 0.45, True),
  'yoke': (QColor(96, 100, 108), 0.3, 0.4, True, 'cast')})


#  The soapbox (user, 2026-11-14: "Here's our first car: rolling down hill
#  picking up speed until it can complete a loop de loop... steering on
#  front wheel only. breaks on all four wheels. no drive train"): its
#  controls (the brakes' line, the hands on the steering wheel, its four
#  wheels' tune-up), its looks (the rig's corners; the planks two woods
#  in turn, the posts grey steel, the chassis machine blue, its plywood
#  birch), where the driver's eyes are over their ball's middle in the
#  tub, m (sat, up the car's own up), and the four corners' names.
SOAPBOX = SoapboxControls(BrakeLine(0.0), FourthWall(0.0),
                          TuneUp((WheelSetup(),) * len(CORNERS)))
SOAPBOX_LOOKS = dict(AXLE_LOOKS)
SOAPBOX_LOOKS.update(SHOCK_LOOKS)
SOAPBOX_LOOKS.update({
  'plank': (QColor(176, 128, 78), 0.0, 0.7, True, 'cast'),
  'board': (QColor(150, 104, 60), 0.0, 0.7, True, 'cast'),
  'post': (QColor(110, 114, 120), 0.3, 0.5, True, 'cast'),
  'frame': (QColor(30, 70, 150), 0.1, 0.4, True),
  'wood': (QColor(214, 190, 150), 0.0, 0.65, True)})
SOAPBOX_EYES = 0.55
CORNER_NAMES = ('Front left', 'Front right', 'Rear left', 'Rear right')


#  The drivetrain bench (user, 2026-11-14: "the differential and the
#  stick shift gearbox and clutch ... dog-leg ... R-2-4 / 1-3-5"): its
#  controls, its looks (the steering bench's wheels; the engine's block
#  dark, the stands grey, the flywheel and the clutch's cover steel, the
#  lining brown, the shafts and gears bright steel, the crown wheel and
#  pinion brass coloured, the carrier cast), the keys that pick the gear
#  the hand moves the stick to.
DRIVETRAIN = DrivetrainControls()
DRIVETRAIN_LOOKS = dict(AXLE_LOOKS)
DRIVETRAIN_LOOKS.update({
  'block': (QColor(46, 48, 52), 0.3, 0.5, True, 'cast'),
  'stand': (QColor(110, 114, 120), 0.3, 0.5, True, 'cast'),
  'flywheel': (QColor(120, 122, 128), 0.6, 0.35, True, 'cast'),
  'cover': (QColor(150, 152, 158), 0.6, 0.3, True),
  'lining': (QColor(110, 76, 50), 0.0, 0.8, True),
  'shaft': (QColor(200, 202, 208), 0.7, 0.2, True),
  'gear': (QColor(214, 216, 222), 0.8, 0.18, True),
  'pinion': (QColor(198, 160, 80), 0.8, 0.2, True),
  'crown': (QColor(198, 160, 80), 0.8, 0.2, True),
  'carrier': (QColor(96, 100, 108), 0.3, 0.4, True, 'cast')})
#  How loud the drivetrain bench's engine is played (of the sound's
#  full scale).
SOUND_VOLUME = 0.8
#  The keys the stick is moved by (user, 2026-11-14): the keypad's, as
#  the dog-leg gate lies, R 2 4 over 1 3 5 (4 5 6 over 1 2 3); N to
#  neutral. The clutch is the keypad's 0 ('padKey' tells the keypad's
#  keys from the row's).
GEAR_KEYS = {'pad4': 'R', 'pad5': '2', 'pad6': '4', 'pad1': '1',
             'pad2': '3', 'pad3': '5', Qt.Key.Key_N: 'N'}
CLUTCH_KEY = 'pad0'
#  What the keypad's keys send with Num Lock off, the digits they are.
_PAD_OFF = {Qt.Key.Key_Insert: 0, Qt.Key.Key_End: 1, Qt.Key.Key_Down: 2,
            Qt.Key.Key_PageDown: 3, Qt.Key.Key_Left: 4, Qt.Key.Key_Clear: 5,
            Qt.Key.Key_Right: 6, Qt.Key.Key_Home: 7, Qt.Key.Key_Up: 8,
            Qt.Key.Key_PageUp: 9}


def padKey(event: object) -> object:
  """The 'padKey' function returns the key 'event' is of as the walk
  view keeps it held: a keypad's digit as 'pad0' to 'pad9' (with Num
  Lock off too), any other key as Qt has it."""
  key = event.key()
  if not event.modifiers() & Qt.KeyboardModifier.KeypadModifier:
    return key
  if int(Qt.Key.Key_0) <= int(key) <= int(Qt.Key.Key_9):
    return 'pad%d' % (int(key) - int(Qt.Key.Key_0))
  if key in _PAD_OFF:
    return 'pad%d' % _PAD_OFF[key]
  return key


def _drivetrainBuilt() -> tuple:
  """Returns the drivetrain bench anew, its engine idling in neutral."""
  DRIVETRAIN.reset()
  return drivetrainBench(DRIVETRAIN)


#  The real car (user, 2026-11-14: "continue to assemble the real car"):
#  its controls (the brakes' line, the hands, the tune-up of four, the
#  drivetrain), its looks (the soapbox's corners, the bench's
#  drivetrain, the engine's block dark, the case glass: seen into, the
#  gears turning; made opaque a while to spare the GPU, then back, the
#  user, 2026-11-15: "bring back transparency"); its bodywork
#  ('_bodyshell': user, 2026-11-15, "let's do something about our
#  minecraft ass blocky car") a period's dark green, its intake's grille
#  dark, its screen glass.
REALCAR = RealCarControls(BrakeLine(0.0), FourthWall(0.0),
                          TuneUp((WheelSetup(),) * len(CORNERS),
                                 FLYWHEEL_MASS),
                          DrivetrainControls(), Antilock())
REALCAR_LOOKS = dict(SOAPBOX_LOOKS)
REALCAR_LOOKS.update(DRIVETRAIN_LOOKS)
REALCAR_LOOKS.update({
  'case': (QColor(150, 215, 255, 85), 0.0, 0.1, False),
  'paint': (QColor(20, 66, 44), 0.2, 0.3),
  'cockpit': (QColor(34, 32, 30), 0.0, 0.8),
  'coil': (QColor(26, 26, 28), 0.3, 0.4, True),
  'damper': (QColor(150, 152, 156), 0.5, 0.3, True),
  'tank': (QColor(176, 178, 182), 0.5, 0.35),
  'grille': (QColor(22, 22, 24), 0.4, 0.6),
  'screen': (QColor(205, 228, 238, 60), 0.0, 0.05, False)})
#  The oval's looks: the real car's, and the old car's parked by it (its
#  own window's palette, each key 'old ' and its own; its rims gold, its
#  tyres rubber).
OVAL_LOOKS = dict(REALCAR_LOOKS)
OVAL_LOOKS.update({
  'old rim': (QColor(206, 164, 62), 0.3, 0.35),
  'old rubber': (QColor(36, 36, 40), 0.0, 0.9)})
#  The city's looks: the real car's, and the palace square's (its
#  palaces' warm grey plaster, their dark roofs, the statue's pale stone
#  pedestal and green bronze).
CITY_LOOKS = dict(REALCAR_LOOKS)
CITY_LOOKS.update({
  'palace': (QColor(222, 208, 178), 0.0, 0.85),
  'roof': (QColor(64, 68, 72), 0.3, 0.6),
  'pedestal': (QColor(196, 194, 188), 0.0, 0.7),
  'bronze': (QColor(74, 122, 104), 0.6, 0.45)})


def _realCarBuilt() -> tuple:
  """Returns the real car anew, its engine idling in neutral, its
  brakes off."""
  REALCAR.drive.reset()
  REALCAR.brakes.reset()
  return realCar(REALCAR)


def _realCarFinishes(assembly: object) -> dict:
  """Returns how the real car's bodies are drawn: 'realCarFinishes',
  its steering wheel and short column as the steering bench's."""
  finishes = dict(realCarFinishes(assembly))
  finishes[_realcar.COLUMN] = columnFinish(_realcar.COLUMN_LENGTH)
  return finishes


def _ovalBuilt() -> tuple:
  """Returns the real car anew on the oval's start, its engine idling in
  neutral, its brakes off, the old car parked in the infield
  ('realCarOnOval')."""
  REALCAR.drive.reset()
  REALCAR.brakes.reset()
  return realCarOnOval(REALCAR)


def _ovalFinishes(assembly: object) -> dict:
  """Returns how the real car and the old car parked by it are drawn
  ('_realCarFinishes', 'parkedFinishes')."""
  finishes = _realCarFinishes(assembly)
  finishes.update(parkedFinishes())
  return finishes


def _ovalRacer(assembly: object, controls: RealCarControls) -> object:
  """Returns the oval's racing driver at the real car's wheel."""
  return RealCarRacer(assembly, controls)


def _cityBuilt() -> tuple:
  """Returns the real car anew at the city lap's start, its engine
  idling in neutral, its brakes off, the palace square by it
  ('realCarInCity')."""
  REALCAR.drive.reset()
  REALCAR.brakes.reset()
  return realCarInCity(REALCAR)


def _cityFinishes(assembly: object) -> dict:
  """Returns how the real car and the palace square are drawn
  ('_realCarFinishes', 'squareFinishes')."""
  finishes = _realCarFinishes(assembly)
  finishes.update(squareFinishes())
  return finishes


def _cityRacer(assembly: object, controls: RealCarControls) -> object:
  """Returns the city driver at the real car's wheel round the lap."""
  return CityDriver(assembly, controls, cityCourse())


def _ovalExtras(assembly: object) -> tuple:
  """Returns the old car's dress as it stands parked ('ParkedDress')."""
  return ParkedDress(),


def _soapboxBuilt() -> tuple:
  """Returns the soapbox on its ramp, as its controls set it up now."""
  return soapbox(SOAPBOX)


def _soapboxFinishes(assembly: object) -> dict:
  """Returns how the soapbox's bodies are drawn: 'soapboxFinishes', its
  steering wheel and column as the steering bench's."""
  finishes = dict(soapboxFinishes(assembly))
  finishes[COLUMN] = columnFinish()
  return finishes


def _rigFinishes(assembly: object) -> dict:
  """Returns how the tyre rig's bodies are drawn: 'rigFinishes', its
  steering wheel and column (body 12) as the steering bench's."""
  finishes = dict(rigFinishes(assembly))
  finishes[12] = columnFinish()
  return finishes


def _hubFinishes(assembly: object) -> dict:
  """Returns how the rear hub's bodies are drawn ('hubFinishes'; the
  same whatever is given)."""
  return hubFinishes()


BEARING_GRABBER = Grabber(10.0, 2e4, 6.0, 1.0, 3e4, 0.1, 1e4,
                          4.0).scaled(SHRUNK)
#  How far the walker is shrunk to walk round the car's wheel (user,
#  2026-11-12: "maybe the wheel should be the size of the player"): the
#  632 mm tyre stands as tall as they do (1.75 m at full size), their
#  eyes 0.6 m up; their grabber the yard's, shrunk.
WHEEL_SHRUNK = 0.632 / 1.75
WHEEL_GRABBER = Grabber().scaled(WHEEL_SHRUNK)
#  The tyre's rubber: its tread and its sidewalls.
_TREAD_TONE = QColor(74, 74, 78)
_SIDEWALL_TONE = QColor(60, 60, 64)


def _wheelDressed() -> tuple:
  """Returns how the wheel is dressed: its tyre's lumps not drawn, nor
  their shadows; its skin drawn over them."""
  skin = wheelSkin()
  lumps = set(range(skin.first, skin.first + skin.tyre.nodes))
  return lumps, [(skin, {'tread': _TREAD_TONE, 'side': _SIDEWALL_TONE})]


#  The wheel on its stand on the road, the walker shrunk before it,
#  nothing driving it, and the same lifted 3 cm clear of it, to be spun
#  by hand (grab the tyre: its lump there pulls the wheel round); the
#  car's bearing, the walker shrunk before the ramp into its shaft, its
#  motor to run (the ring up to 1.9 rad/s in a third of a second); the
#  outer ring alone with three giant balls in
#  its groove and one on the apron; none sleeping; the yard, the walker
#  facing the crates, its many bodies let sleep.
PLACES = (Place('The tyre yard', wheelYard, TYRE_YARD, Grabber(),
                -0.5 * math.pi, 1.0, None, tyredGiven, None, 1.0, None,
                FULL, True, (), TYRED_STEP, False, None, (),
                tyredFinishes, TYRE_LOOKS, 'wheel'),
          Place('The brake bench', functools.partial(benchOf, BENCH_LINE),
                TYRE_YARD, Grabber(), -0.5 * math.pi, 1.0, None,
                oakBallGiven, None, 1.0, None, FULL, True, (), TYRED_STEP,
                False, None, (), benchFinishes, BENCH_LOOKS, 'ball', 1,
                0.0, BENCH_LINE),
          Place('The hinge bench', hingeBench, TYRE_YARD, Grabber(),
                -0.5 * math.pi, 1.0, None, oakBallGiven, None, 1.0, None,
                FULL, True, (), HINGE_STEP, False, None, (), hingeFinishes,
                HINGE_LOOKS, 'ball', 1, HINGE_GREASE),
          Place('The shock bench', shockBench, TYRE_YARD, Grabber(),
                -0.5 * math.pi, 1.0, None, oakBallGiven, None, 1.0, None,
                FULL, True, (), HINGE_STEP, False, None, (), shockFinishes,
                SHOCK_LOOKS, 'ball', 1, HINGE_GREASE, None, shockCoils),
          Place('The steering bench', functools.partial(
                  steeringBench, AXLE_WALL, AXLE_LINE), TYRE_YARD,
                Grabber(), math.pi, 1.0, None, oakBallGiven, None, 1.0,
                None, FULL, True, (), HINGE_STEP, False, None, (),
                axleFinishes, AXLE_LOOKS, 'ball', 1, HINGE_GREASE,
                AXLE_LINE, None, AXLE_WALL),
          Place('The tyre rig', functools.partial(tyreRig, RIG), TYRE_YARD,
                Grabber(), -0.5 * math.pi, 1.0, None, oakBallGiven, None,
                1.0, None, FULL, True, (), RIG_STEP, False, None, (),
                _rigFinishes, RIG_LOOKS, 'ball', 1, HINGE_GREASE, RIG.line,
                rigCoils, RIG.steer, RIG),
          Place('The soapbox', _soapboxBuilt, TYRE_YARD, Grabber(),
                math.pi, 1.0, None, oakBallGiven, None, 1.0, None, FULL,
                True, (), RIG_STEP, False, None, (), _soapboxFinishes,
                SOAPBOX_LOOKS, 'ball', 1, HINGE_GREASE, SOAPBOX.line,
                soapboxCoils, SOAPBOX.steer, None, SOAPBOX, None,
                Ride(CHASSIS, SEAT, SOAPBOX.tune, (FIRST_CORNER + 2,
                                                   FIRST_CORNER + 8))),
          Place('The drivetrain bench', _drivetrainBuilt, TYRE_YARD,
                Grabber(), -0.5 * math.pi, 1.0, None, oakBallGiven, None,
                1.0, None, FULL, True, (), RIG_STEP, False, None,
                (GEARBOX_CASE,), drivetrainFinishes, DRIVETRAIN_LOOKS,
                'ball', 1, HINGE_GREASE, DRIVETRAIN.line, None, None, None,
                None, DRIVETRAIN),
          Place('The real car', _realCarBuilt, TYRE_YARD, Grabber(),
                math.pi, 1.0, None, oakBallGiven, None, 1.0, None, FULL,
                True, (), RIG_STEP, False, None, (), _realCarFinishes,
                REALCAR_LOOKS, 'ball', 1, HINGE_GREASE, REALCAR.line,
                realCarCoils, REALCAR.steer, None, None, REALCAR.drive,
                Ride(_realcar.CHASSIS, _realcar.SEAT, REALCAR.tune,
                     _realcar.KNUCKLES[:2], REALCAR.brakes)),
          Place('The oval', _ovalBuilt, ovalGround(), Grabber(), math.pi,
                1.0, None, oakBallGiven, None, 1.0, None, FULL, True, (),
                RIG_STEP, False, None, (), _ovalFinishes, OVAL_LOOKS,
                'ball', 1, HINGE_GREASE, REALCAR.line, realCarCoils,
                REALCAR.steer, None, None, REALCAR.drive,
                Ride(_realcar.CHASSIS, _realcar.SEAT, REALCAR.tune,
                     _realcar.KNUCKLES[:2], REALCAR.brakes),
                _ovalRacer, _ovalExtras, 'oval'),
          Place('The cord tyre yard', tyreYard, TYRE_YARD, Grabber(),
                -0.5 * math.pi, 1.0, None, wheelGiven, None, 1.0, None,
                FULL, True, (), 2.5e-4, False, None, (), rimFinishes,
                TYRE_LOOKS, 'wheel', TYRE_PASSES),
          Place('The wheel', functools.partial(walkingWheel, WHEEL_SHRUNK,
                                              WHEEL_DROP),
                ROAD, WHEEL_GRABBER, -0.5 * math.pi, 1.0, None,
                functools.partial(wheelBallGiven, WHEEL_SHRUNK), None,
                WHEEL_SHRUNK, _wheelDressed),
          Place('The wheel on a lift',
                functools.partial(walkingWheel, WHEEL_SHRUNK, WHEEL_LIFT),
                ROAD, WHEEL_GRABBER, -0.5 * math.pi, 1.0, None,
                functools.partial(wheelBallGiven, WHEEL_SHRUNK), None,
                WHEEL_SHRUNK, _wheelDressed),
          Place('The bearing', functools.partial(walkingBearing, SHRUNK,
                                                 True),
                groundAt(SHRUNK), BEARING_GRABBER, -0.5 * math.pi, 1.0,
                None, functools.partial(carBallGiven, SHRUNK),
                (0, MOTOR_FREE, MOTOR_STALL), SHRUNK, None,
                BEARING_FIDELITY, False, ((2, _SHAFT_PAINT, 2, 0.2),),
                SMALL_BEARING, False, None, (1, 8)),
          Place('The bearing in the void',
                functools.partial(voidBearing, SHRUNK), None,
                BEARING_GRABBER, -0.5 * math.pi, 1.0, None,
                functools.partial(carBallGiven, SHRUNK),
                (0, MOTOR_FREE, MOTOR_STALL), SHRUNK, None,
                BEARING_FIDELITY, False, ((2, _SHAFT_PAINT, 2, 0.2),),
                SMALL_BEARING, False, VOID_FALL, (1, 8)),
          Place('The rear hub in the void',
                functools.partial(rearHub, SHRUNK), None, BEARING_GRABBER,
                -0.5 * math.pi, 1.0, None,
                functools.partial(carBallGiven, SHRUNK), None, SHRUNK,
                None, BEARING_FIDELITY, False, (), SMALL_BEARING, False,
                VOID_FALL, (), _hubFinishes, HUB_LOOKS, 'ball', 1,
                HUB_GREASE),
          Place('The ring', functools.partial(walkingRing, 3, 1), APRON,
                RING_GRABBER, -0.5 * math.pi, 2.0, None, giantBallGiven,
                None, 1.0),
          Place('The yard', walkingYard, YARD_GROUND, Grabber(), math.pi,
                1.0, Sleep(), oakBallGiven, None, 1.0)) + ((
  Place('Copenhagen', _cityBuilt, cityGround, Grabber(), math.pi, 1.0,
        None, oakBallGiven, None, 1.0, None, FULL, True, (), RIG_STEP,
        False, None, (), _cityFinishes, CITY_LOOKS, 'ball', 1,
        HINGE_GREASE, REALCAR.line, realCarCoils, REALCAR.steer, None,
        None, REALCAR.drive,
        Ride(_realcar.CHASSIS, _realcar.SEAT, REALCAR.tune,
             _realcar.KNUCKLES[:2], REALCAR.brakes),
        _cityRacer, None, 'crg', ATTRIBUTION),) if os.path.isfile(
  os.path.normpath(CITY_TRACK)) else ())



#  A punt hits no harder than sends this much off at the 'Punt' speed,
#  kg, at full size (a 'scale' cubed of it shrunk): a body heavier is
#  punted as though it weighed so (a bearing's ring is nudged, not
#  slammed into its balls).
_PUNT_MASS = 100.0
#  The view's near cut at full size, m.
_NEAR_CUT = 0.02
#  How fast a punt sends what it punts off at first, m/s.
PUNT = 12.0
#  Two presses of Space within this, s, start or stop flying.
_DOUBLE = 0.3
#  A recording: how long, s, at how many frames a second, into which
#  folder (made if missing; 'previews' is the repo's own, gitignored).
RECORDED = 10.0
_RECORD_FPS = 60
_RECORDINGS = 'previews'

#  The hold is put no lower than this (rad down) before the eyes, so a
#  body held is not pressed into the walker's own feet; and is let go
#  once it is this far (m, past its own reach) from where it is held.
_LOWEST_HOLD = 0.75
_LOST = 2.0
#  Radians the head turns for a pixel the mouse moves; how far up or
#  down it looks at most.
_TURN = 0.0025
_TILT = 1.48
_HELD_TONE = QColor(120, 205, 230)
_AIMED_TONE = QColor(235, 215, 150)
#  Bodies this dense (kg/m³) or more are steel, drawn so; between the
#  next two, plastics (PA66 1140), drawn ivory.
_STEEL = 5000.0
_STEEL_TONE = QColor(160, 168, 180)
_PLASTIC = (900.0, 1500.0)
_PLASTIC_TONE = QColor(232, 226, 208)
#  How steel and plastic look on the GPU (metalness, roughness: more
#  metal than this draws black, having no surroundings to mirror), and
#  rubber; the legs, bars this thick at full size, m, their tone and
#  look.
_STEEL_LOOK, _PLASTIC_LOOK, _RUBBER_LOOK = (0.3, 0.35), (0.0, 0.55), (
  0.0, 0.85)
_LEG_THICK, _LEG_TONE, _LEG_LOOK = 0.012, QColor(200, 200, 210), (0.3, 0.4)
_HINT = ('Click to look round.  E: the menu (its buttons).  WASD walk, '
         'Shift runs, Space jumps; Space twice flies (Space up, Shift '
         'down, Ctrl faster; landing '
         'walks).  Right button: grab or drop.  Left: punt.  Wheel: hold '
         'nearer or further.  In a car, V: the chase view (the mouse looks '
         'round the car, the wheel nearer or further).  F9 records ten '
         'seconds.  Esc lets the mouse go.')
#  The chase view (user, 2026-11-15: "more camera views like chase where
#  the mouse can look around, like in GTA V"): sat in a car, V swaps the
#  driver's eyes for a camera behind and over the car, level, swinging
#  round after it as it turns ('GpuView.follow'); the mouse looks round
#  it, and once it has been left 'CHASE_BACK' s with the car going over
#  'CHASE_MOVING' m/s the look eases back behind at 'CHASE_RETURN' rad/s;
#  how far back it starts, m (the wheel nearer or further, between
#  'CHASE_NEAREST' and 'CHASE_FARTHEST'), how high over the chassis'
#  middle it looks, m, and how far down, rad (the mouse within
#  'CHASE_LOWEST' and 'CHASE_HIGHEST').
CHASE_DISTANCE, CHASE_LIFT, CHASE_PITCH = 6.5, 1.0, 0.22
CHASE_NEAREST, CHASE_FARTHEST = 3.0, 25.0
CHASE_LOWEST, CHASE_HIGHEST = -0.35, 1.2
CHASE_BACK, CHASE_MOVING, CHASE_RETURN = 1.5, 2.0, 2.5


class WalkView(GpuView):
  """WalkView is a 'GpuView' seen through the walker's eyes ('target',
  'distance' nought), the world drawn at their size ('magnify'), a
  cross in the middle where the grabber points and, while the mouse is
  let go, the keys along the bottom; every actuator drawn as a bar
  ('LegsDress': nothing holds anything unseen), but those to the bodies
  in 'hiddenLegs', and the skins in 'skins' (each with its parts'
  tones) drawn over the bodies they hide ('SkinDress'), the cord tyres
  of 'tyres' over their nodes ('TyreDress'), the coil springs of
  'coils' wound between their seats ('CoilDress'), the looks of its
  'finishes'' keys in 'finishLooks' (put in its 'palette'). Clicked into
  it
  hides the pointer and the mouse turns the head ('yaw', 'pitch'); the
  pointer is put back in the middle as it strays, where the system lets
  it be moved. Each move is read from the nearer of where the pointer
  last was and where it was put ('lookFrames', the one last moved
  last): the move putting it back, even one that has moved on a little
  since it landed, and moves still coming from before it, all turn the
  head only as far as the hand moved. Keys held are in 'keys'; Space
  emits 'jumped', the left button 'punted', the right 'grabbing' (True
  pressed, False let go), the wheel 'reached' (m further), F9
  'recordAsked', E 'menuAsked'. Esc, or leaving the window, lets the
  mouse go. It only asks: the window walks, grabs and punts."""

  punted = Signal()
  grabbing = Signal(bool)
  jumped = Signal()
  reached = Signal(float)
  recordAsked = Signal()
  menuAsked = Signal()

  def __init__(self, ) -> None:
    GpuView.__init__(self)
    self.distance, self.pitch = 0.0, 0.1
    self.chasing, self.chaseFar, self.chaseTilt = False, CHASE_DISTANCE, (
      CHASE_PITCH)
    self.lookedAt, self.seatLook = 0.0, (0.0, 0.1)
    self.looking, self.lookFrames = False, []
    self.skins, self.hiddenLegs, self.finishLooks = [], set(), {}
    self.tyres, self.coils, self.extras = (), (), ()
    self.crosshair, self.hint, self.dressedFor = True, _HINT, None

  def show_(self, assembly: object, states: tuple, settle: float) -> None:
    """Shows 'assembly' in 'states', dressed: its legs as bars, its
    skins over what they hide, faces over a tinted lump tinted."""
    if assembly is not self.dressedFor:
      self.dressedFor = assembly
      self.dresses = [LegsDress(assembly, self.hiddenLegs,
                                _LEG_THICK / self.magnify)]
      self.palette = dict(self.finishLooks)
      self.palette['legs'] = (_LEG_TONE,) + _LEG_LOOK
      tints = {'aimed': _AIMED_TONE, 'held': _HELD_TONE}
      for key, tone in tints.items():
        self.palette[key] = (tone,) + _RUBBER_LOOK
      for skin, tones in self.skins:
        self.dresses.append(SkinDress(skin, tints))
        for part, tone in tones.items():
          self.palette[part] = (tone,) + _RUBBER_LOOK
      if self.tyres:
        self.dresses.append(TyreDress(assembly, self.tyres, tints))
      if self.coils:
        self.dresses.append(CoilDress(assembly, self.coils))
      self.dresses.extend(self.extras)
    for dress in self.dresses[1:]:
      dress.tones = self.tones
    GpuView.show_(self, assembly, states, settle)

  def setLooking(self, looking: bool) -> None:
    """The 'setLooking' method has the mouse turn the head, its pointer
    hidden and put in the middle, or lets it go."""
    self.looking = True if looking else False
    self.lookFrames = []
    if self.looking:
      self.quick.setCursor(Qt.CursorShape.BlankCursor)
      self.quick.setMouseGrabEnabled(True)
      self.box.setFocus()
      self._recentre()
      self.hint = ''
    else:
      self.quick.setMouseGrabEnabled(False)
      self.quick.unsetCursor()
      self.hint = _HINT

  def eventFilter(self, watched: object, event: object) -> bool:
    """Reads the keys and the mouse from the scene's window (it, not the
    view, has them): a click takes the mouse, then the left button
    punts and the right grabs (letting it go drops); moves turn the
    head; the wheel holds nearer or further; keys held into 'keys',
    Space jumps, F9 asks for a recording, Esc lets the mouse go;
    leaving the window forgets where the pointer was, losing the focus
    lets every key and the mouse go."""
    if watched is not self.quick:
      return False
    kind, types = event.type(), QEvent.Type
    if kind == types.MouseButtonPress:
      if not self.looking:
        self.setLooking(True)
      elif event.button() == Qt.MouseButton.LeftButton:
        self.punted.emit()
      elif event.button() == Qt.MouseButton.RightButton:
        self.grabbing.emit(True)
      return True
    if kind == types.MouseButtonRelease:
      if self.looking and event.button() == Qt.MouseButton.RightButton:
        self.grabbing.emit(False)
      return True
    if kind == types.MouseMove:
      if self.looking:
        self._looked(event)
      return True
    if kind == types.Wheel:
      nearer = event.angleDelta().y() > 0
      if self.chasing:
        self.chaseFar = min(CHASE_FARTHEST, max(CHASE_NEAREST, (
          self.chaseFar * (0.9 if nearer else 1.1))))
        return True
      self.reached.emit(0.25 if nearer else -0.25)
      return True
    if kind == types.KeyPress:
      self._pressed(event)
      return True
    if kind == types.KeyRelease:
      if not event.isAutoRepeat():
        self.keys.discard(padKey(event))
      return True
    if kind == types.Leave:
      self.lookFrames = []
    elif kind == types.FocusOut:
      self.keys.clear()
      if self.looking:
        self.setLooking(False)
    return False

  def focusLost(self, ) -> None:
    """The 'focusLost' method lets every key held go, and the mouse
    ('setLooking')."""
    self.keys.clear()
    if self.looking:
      self.setLooking(False)

  def _pressed(self, event: object) -> None:
    """Keeps a key held; Space jumps, F9 asks for a recording, Esc lets
    the mouse go."""
    if event.key() == Qt.Key.Key_Escape:
      self.setLooking(False)
      return
    if event.isAutoRepeat():
      return
    if event.key() == Qt.Key.Key_F9:
      self.recordAsked.emit()
      return
    if event.key() == Qt.Key.Key_E:
      self.menuAsked.emit()
      return
    if event.key() == Qt.Key.Key_V:
      self.chased(not self.chasing)
      return
    if event.key() == Qt.Key.Key_Space:
      self.jumped.emit()
    self.keys.add(padKey(event))

  def chased(self, on: bool) -> None:
    """The 'chased' method takes the chase view ('on') or gives it back
    for the driver's eyes, each as it was left: the head's turn in the
    seat kept for its coming back; the chase behind the car anew."""
    if on == self.chasing:
      return
    if on:
      self.seatLook = (self.yaw, self.pitch)
      self.heading, self.around, self.chaseTilt = None, 0.0, CHASE_PITCH
      self.chasing = True
      return
    self.chasing = False
    self.yaw, self.pitch = self.seatLook
    self.distance, self.crosshair = 0.0, True

  def _looked(self, event: object) -> None:
    """Turns the head by a move of the mouse (in the chase view, the
    look round the car: 'around', 'chaseTilt'), read from the nearer of
    the pointer's frames ('lookFrames'): where it last was and, once put
    back, where it was put; puts it back as it strays."""
    at = event.globalPosition()
    frames = self.lookFrames
    if not frames:
      frames.append(at)
    nearest = min(range(len(frames)), key=lambda k: abs(
      at.x() - frames[k].x()) + abs(at.y() - frames[k].y()))
    last = frames.pop(nearest)
    frames.append(at)
    if self.chasing:
      self.around -= _TURN * (at.x() - last.x())
      self.chaseTilt = min(CHASE_HIGHEST, max(CHASE_LOWEST, self.chaseTilt
                                              + _TURN * (at.y() - last.y())))
      self.lookedAt = time.perf_counter()
    else:
      self.yaw -= _TURN * (at.x() - last.x())
      self.pitch = min(_TILT, max(-_TILT, self.pitch
                                  + _TURN * (at.y() - last.y())))
    local, width, height = event.position(), self.quick.width(), (
      self.quick.height())
    if abs(local.x() - 0.5 * width) > 0.25 * width \
        or abs(local.y() - 0.5 * height) > 0.25 * height:
      self._recentre()

  def _recentre(self, ) -> None:
    """Puts the hidden pointer back in the middle, where the system lets
    it be moved, keeping two frames to read moves from: where it last
    was (moves from before it was put back may still come) and where it
    is put (the pointer's place read back at once may still be the old
    one, so it is not asked)."""
    target = self.quick.mapToGlobal(QPoint(self.quick.width() // 2,
                                           self.quick.height() // 2))
    self.lookFrames = self.lookFrames[-1:] + [QPointF(target)]
    QCursor.setPos(target)


class ControlsMenu(QWidget):
  """ControlsMenu is the walk window's buttons in a little menu over the
  view (user, 2026-11-13: "make the E button open a little menu where
  the buttons are again. From minecraft muscle memory."), a popup: E
  closes it, back to looking round, Esc or a click outside just
  closes it; 'closed' tells which (True: by E)."""

  closed = Signal(bool)

  def __init__(self, parent: QWidget, widgets: tuple) -> None:
    QWidget.__init__(self, parent, Qt.WindowType.Popup)
    layout = QVBoxLayout()
    for widget in widgets:
      layout.addWidget(widget)
    self.setLayout(layout)
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.byKey = False

  def keyPressEvent(self, event: object) -> None:
    """E closes the menu, back to looking round; Esc closes it."""
    if event.key() in (Qt.Key.Key_E, Qt.Key.Key_Escape):
      self.byKey = event.key() == Qt.Key.Key_E
      self.close()
      return
    QWidget.keyPressEvent(self, event)

  def hideEvent(self, event: object) -> None:
    """Tells that the menu closed, and how."""
    self.closed.emit(self.byKey)
    self.byKey = False
    QWidget.hideEvent(self, event)


class WalkWindow(QMainWindow):
  """WalkWindow walks the places live."""

  def __init__(self, ) -> None:
    QMainWindow.__init__(self)
    self.setWindowTitle('Walk and grab')
    self.view = WalkView()
    self.view.hidden = {0}
    self.view.punted.connect(self.askPunt)
    self.view.grabbing.connect(self.askGrab)
    self.view.jumped.connect(self.askJump)
    self.view.reached.connect(self.reach)
    self.view.recordAsked.connect(self.record)
    self.status = readingsOf(self)
    self.playButton = QPushButton('Pause')
    self.playButton.clicked.connect(self.togglePlay)
    self.placeBox = QComboBox()
    self.placeBox.addItems([place.name for place in PLACES])
    self.placeBox.setToolTip('Where to walk')
    self.placeBox.activated.connect(self.reset)
    backButton = QPushButton('Set it up anew')
    backButton.clicked.connect(self.reset)
    self.giveButton = QPushButton('Give ball')
    self.giveButton.setToolTip('A new one, held before you')
    self.giveButton.clicked.connect(self.giveBall)
    self.driveButton = Toggle('Motor', 'The motor turning the shaft by '
                              'its pinion and gear', False)
    self.smallButton = Toggle('Small steps', 'The world stepped as GPUs '
                              'step games\' (every touch a rule, all at '
                              'once, on the GPU); off: by springs', True)
    self.spreadButton = Toggle('Whole GPU', 'The small steps spread over '
                               'the whole GPU, each part of a step its '
                               'own launch (16 steps a graph); off: one '
                               'block of it runs a frame\'s steps in one '
                               'launch (a small world: fewer launches). '
                               'The status says how near real time it '
                               'runs', False)
    self.brakeButton = Toggle('Brake', 'The brake pedal held down: the '
                              'line\'s pressure on the caliper (or hold '
                              'B)', False)
    self.lineSlider = QuantitySlider()
    self.lineSlider.text = 'Line'
    self.lineSlider.setLogScale(1.0, 100.0, 'bar', 1)
    self.lineSlider.quantity = BENCH_BAR
    self.lineSlider.setToolTip('How hard the pedal presses the brake '
                               'fluid, bar')
    self.speedSlider = QuantitySlider()
    self.speedSlider.text = 'Deck'
    self.speedSlider.setScale(0.0, RIG_FASTEST, 'm/s', 1)
    self.speedSlider.quantity = 0.0
    self.speedSlider.setToolTip('How fast the tyre rig\'s turntable runs '
                                'under the wheel')
    self.loadSlider = QuantitySlider()
    self.loadSlider.text = 'Ram'
    self.loadSlider.setScale(0.0, LOAD_MOST / 1000.0, 'kN', 2)
    self.loadSlider.quantity = LOAD / 1000.0
    self.loadSlider.setToolTip('How hard the ram presses the boom down '
                               '(load on the wheel besides the boom\'s)')
    self.humpButton = Toggle('Humps', 'Humps bolted across the turntable '
                             '(%d, 3 cm high)' % RIG_HUMPS, False)
    self.steerSlider = QuantitySlider()
    self.steerSlider.text = 'Steer'
    self.steerSlider.setScale(-RIG_LOCK, RIG_LOCK, '°', 0)
    self.steerSlider.quantity = 0.0
    self.steerSlider.setToolTip('The angle the hands turn the tyre rig\'s '
                                'steering wheel to and hold it at (left '
                                'positive: the wheel rolls in across the '
                                'deck; a turn is a lock)')
    self.tuneButton = QPushButton('Tune-up')
    self.tuneButton.setToolTip('The wheels\' tyre pressure, camber and '
                               'toe (the car or rig is set up anew with '
                               'them)')
    self.soundButton = Toggle('Sound (M)', 'The drivetrain bench\'s engine '
                              'heard: a V12, as AngeTheGreat\'s Engine '
                              'Simulator hears one (its gas stepped in a '
                              'process of its own; the first time it '
                              'compiles a few seconds)', False)
    self.soundButton.clicked.connect(self._chooseSound)
    self.engineSound = EngineSound()
    self.handsButton = Toggle('Robot hands', 'The soapbox\'s line kept '
                              'for you round the loop (hands off it '
                              'drifts off the planks three quarters '
                              'round); on the oval, the racing driver '
                              'drives the real car (wheel, pedals, '
                              'clutch and stick); off: you drive',
                              False)
    self.tuneButton.clicked.connect(self.openTune)
    self.tunePanel = None
    self.recordButton = QPushButton('Record 10 s')
    self.recordButton.setToolTip('Records the next ten seconds of the '
                                 'view into a video in previews (F9)')
    self.recordButton.clicked.connect(self.record)
    self.puntSlider = QuantitySlider()
    self.puntSlider.text = 'Punt'
    self.puntSlider.setLogScale(1.0, 40.0, 'm/s', 1)
    self.puntSlider.quantity = PUNT
    self.puntSlider.setToolTip('How fast a punt sends what it punts off')
    widgets = (self.playButton, self.placeBox, backButton, self.giveButton,
               self.driveButton, self.brakeButton, self.lineSlider,
               self.speedSlider, self.loadSlider, self.humpButton,
               self.steerSlider, self.tuneButton, self.handsButton,
               self.soundButton,
               self.smallButton, self.spreadButton, self.recordButton,
               self.puntSlider)
    for widget in widgets:
      widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.menu = ControlsMenu(self, widgets)
    self.menu.closed.connect(self._menuClosed)
    self.view.menuAsked.connect(self.openMenu)
    column = QVBoxLayout()
    column.addWidget(self.view, 1)
    holder = QWidget()
    holder.setLayout(column)
    self.setCentralWidget(holder)
    self.playing, self.seconds = True, FRAME
    self.recording, self.recorded = None, ''
    self.lastTick = self.chasedAt = time.perf_counter()
    self.lock, self.alive, self.driving = threading.RLock(), True, False
    self.physicsTook, self.speedNow, self.failed = 0.0, 1.0, None
    self.compiling, self.loaded, self.solver = None, set(), ''
    self.driveButton.toggled.connect(self._setDriving)
    self.braking, self.linePressure = False, 1e5 * BENCH_BAR
    self.brakeButton.toggled.connect(self._setBraking)
    self.lineSlider.quantityChanged.connect(self._setLine)
    self.rigSpeed, self.rigLoad, self.rigHumped = 0.0, LOAD, False
    self.tyreForces = ()
    self.speedSlider.quantityChanged.connect(self._setRigSpeed)
    self.loadSlider.quantityChanged.connect(self._setRigLoad)
    self.humpButton.toggled.connect(self._setHumps)
    self.rigSteer = 0.0
    self.steerSlider.quantityChanged.connect(self._setRigSteer)
    self.seated, self.robotHands, self.keeper = False, False, None
    self.handsButton.toggled.connect(self._setHands)
    self.smallButton.toggled.connect(self._setSmall)
    self.spreadButton.toggled.connect(self._setSmall)
    self.reset()
    self.timer = QTimer()
    self.timer.setInterval(15)
    self.timer.timeout.connect(self.tick)
    self.timer.start()
    sys.setswitchinterval(SWITCH_INTERVAL)
    self.physics = threading.Thread(target=self._run, daemon=True)
    self.physics.start()

  def closeEvent(self, event: object) -> None:
    """Closing stops the physics' thread and the engine's sound."""
    self.engineSound.close()
    self.alive = False
    self.physics.join(1.0)
    QMainWindow.closeEvent(self, event)

  def openMenu(self, ) -> None:
    """Opens the menu of the window's buttons over the middle of the
    view, the mouse let go to click them."""
    self.view.setLooking(False)
    self.menu.adjustSize()
    middle = self.view.mapToGlobal(self.view.rect().center())
    self.menu.move(middle.x() - self.menu.width() // 2,
                   middle.y() - self.menu.height() // 2)
    self.menu.show()
    self.menu.activateWindow()
    self.menu.setFocus()

  def _menuClosed(self, back: bool) -> None:
    """The menu closed: by E, back to looking round; else the mouse
    stays let go."""
    if back:
      self.view.setLooking(True)

  def reset(self, ) -> None:
    """Sets the place chosen up anew, the walker (shrunk as the place
    says) looking at what is there; bodies on legs are held (the grabber
    does not grab them; their legs are drawn, as all is: nothing holds
    anything unseen), steel is drawn steel; the physics' thread waits."""
    with self.lock:
      self._setUp(PLACES[max(0, self.placeBox.currentIndex())])
    self._showNow()

  def _setUp(self, place: Place) -> None:
    """Sets 'place' up anew (as 'reset'): its ground made first, should
    it be a function ('ground': the city's, made once)."""
    self.place = place
    self.ground = place.ground() if callable(place.ground) else (
      place.ground)
    self.smallButton.setEnabled(place.small > 0.0 and place.springs)
    if not place.springs:
      self.smallButton.setChecked(True)
    self.world = self._worldFor(place)
    self.grabber = place.grabber
    self.walker = PLAYER.scaled(place.scale)
    self.view.near = _NEAR_CUT * place.scale
    self.view.magnify = 1.0 / place.scale
    self.view.tiles = {'ground': place.tile * place.scale}
    ground = self.ground
    self.view.void = ground is None
    terrain = None if ground is None else ground.terrain
    self.view.terrain = terrain
    self.view.wall = None if ground is None else ground.wall
    self.view.oval = terrain is not None and place.drawn == 'oval'
    self.view.crg = cityTrack() if place.drawn == 'crg' else None
    self.view.glass = {index: MANA_GLASS for index in place.glass}
    self.view.finishLooks = {} if place.looks is None else place.looks
    self.giveButton.setText('Give %s' % place.gift)
    self.view.regrounded()
    self.driveButton.setEnabled(place.motor is not None)
    self.driveButton.setChecked(False)
    self.brakeButton.setEnabled(place.brake is not None)
    self.lineSlider.setEnabled(place.brake is not None)
    self.brakeButton.setChecked(False)
    for widget in (self.speedSlider, self.loadSlider, self.humpButton,
                   self.steerSlider):
      widget.setEnabled(place.rig is not None)
    self.tuneButton.setEnabled(place.rig is not None
                               or place.ride is not None)
    self.handsButton.setEnabled(place.soapbox is not None
                                or place.racing is not None)
    if place.racing is not None:
      self.handsButton.setChecked(True)
    self.soundButton.setEnabled(place.drivetrain is not None)
    if place.drivetrain is None and self.soundButton.isChecked():
      self.soundButton.setChecked(False)
      self._chooseSound()
    self.seated = place.ride is not None
    self.keeper = None if place.soapbox is None else LineKeeper(
      place.soapbox.steer)
    if place.soapbox is not None:
      self.lineSlider.quantity = HOLD / 1e5
    if place.rig is not None:
      self._rigged(place.rig)
    if place.steer is not None:
      place.steer.value = 0.0
    self.assembly, self.states = place.built()
    self.spawn = self.states[0]
    self.racer = None if place.racing is None else place.racing(
      self.assembly, REALCAR)
    self.lapTimer = LapTimer(0.0, None if self.racer is None else (
      self.racer.course))
    self.rescueAsked = False
    self.rigged = {leg.second for leg in self.assembly.actuators}
    self.view.hiddenLegs = set() if place.rigs else set(
      range(len(self.assembly.bodies)))
    self.view.stripes = {index: (paint, count, pitch)
                         for index, paint, count, pitch in place.stripes}
    self._dressed()
    self.clock, self.further = 0.0, 0.0
    self.held, self.pulling, self.flying = None, False, False
    self.puntAsked, self.jumpAsked, self.lastSpace = False, False, -1.0
    self.view.yaw, self.view.pitch = place.yaw, 0.1
    self.lastYaw = self.view.yaw
    self.view.riding = None
    if place.soapbox is not None:
      self.brakeButton.setChecked(True)

  def _dressed(self, ) -> None:
    """Dresses the assembly as the place says: the walker hidden, skins
    over what they hide, every cord tyre over its hidden nodes (its
    wheel carried whole: 'carried', its rim's nodes; 'carriers', each
    node's rim), finishes; steel and plastic found."""
    place = self.place
    hidden, skins = (set(), []) if place.dressed is None else (
      place.dressed())
    wheels = wheelsOf(self.assembly)
    self.carried = {rim: tuple(node for row in rows for node in row)
                    for rim, rows in wheels}
    self.carriers = {node: rim for rim, nodes in self.carried.items()
                     for node in nodes}
    self.tyreHits = TyreDress(self.assembly, wheels, {})
    self.pressures, self.wheelTurned = (), ()
    self.view.tyres = wheels
    self.view.hidden = {0} | hidden | set(self.carriers)
    self.view.skins = skins
    self.view.coils = () if place.coils is None else place.coils(
      self.assembly)
    rig = place.rig
    extras = () if rig is None else (
      RamDress(self.assembly), HumpDress(self.assembly, rig.table,
                                         rig.humps, TABLE_TOP))
    if place.extras is not None:
      extras += tuple(place.extras(self.assembly))
    self.view.extras = extras
    self.tyreForces = ()
    self.passed = frozenset(self.view.hidden)
    self.view.finishes = {} if place.finishes is None else (
      place.finishes(self.assembly))
    self._findSteel()

  def _worldFor(self, place: Place) -> object:
    """Returns the world 'place' is stepped in: in small steps on the
    GPU (or the CPU, where there is none) if it may be and the toggle
    says so (its kernels loaded first, '_readied'), else the springs'
    world; 'solver' says which, for the status."""
    if place.small > 0.0 and self.smallButton.isChecked():
      device = gpuDevice() or 'cpu'
      self._readied(device)
      spread = self.spreadButton.isChecked() and device != 'cpu'
      self.solver = 'small steps, %s%s' % (device, (
        ', whole GPU' if spread else ', one block') if device != 'cpu'
                                            else '')
      return SmallSteps(GRAVITY, self.ground, place.small, place.passes,
                        place.grease, device, THREADS, spread)
    self.solver = 'springs, %s' % fastestDevice()
    return World(GRAVITY, 1e-3, self.ground, None, True, place.sleeping,
                 fastestDevice(), place.fidelity)

  def _readied(self, device: str) -> None:
    """Loads the small steps' kernels for 'device' in a thread of its
    own (compiling them, the first time after a change, takes seconds),
    the physics waiting meanwhile ('compiling'), the status saying so,
    the window never waiting."""
    if device in self.loaded or self.compiling is not None:
      return
    self.compiling = device

    def load() -> None:
      """Loads (or compiles) the kernels at every block size the world
      launches them at ('preloaded'), then lets the physics go."""
      try:
        preloaded(device)
        self.loaded.add(device)
      except Exception as error:
        self.failed = 'the small steps would not load: %s: %s' % (
          type(error).__name__, error)
      finally:
        self.compiling = None

    threading.Thread(target=load, daemon=True).start()

  def _setSmall(self, on: bool) -> None:
    """Steps the place on in small steps, or by springs, from where it
    is now."""
    with self.lock:
      self.world = self._worldFor(self.place)

  def askPunt(self, ) -> None:
    """Punts at the next frame."""
    self.puntAsked = True

  def askGrab(self, pressed: bool) -> None:
    """Pressed, drops what is held, or starts pulling; let go, stops
    pulling."""
    with self.lock:
      if pressed and self.held is not None:
        self.held = None
        return
      self.pulling = pressed

  def askJump(self, ) -> None:
    """Jumps at the next frame, if standing; pressed twice quickly,
    starts or stops flying; sat in a car, nothing (Space is its
    handbrake)."""
    if self.seated:
      return
    now = time.perf_counter()
    if now - self.lastSpace <= _DOUBLE:
      self.flying = not self.flying
      self.jumpAsked, self.lastSpace = False, -1.0
      return
    self.jumpAsked, self.lastSpace = True, now

  def giveBall(self, ) -> None:
    """Gives the walker a new ball, held before them, moving with
    them."""
    with self.lock:
      self._givenBall()
    self._showNow()

  def _givenBall(self, ) -> None:
    """Gives the walker a new ball, or whatever the place gives (as
    'giveBall'): its bodies moved so its heaviest is in the hold, or
    over it clear of every other body (anything held let go first: a
    wheel given into the one held came inside it, and the small steps
    pushed it out at hundreds of metres a second, kilometres off, its
    shadow striping the ground: user, 2026-11-13), all moving with the
    walker, that one held."""
    walker = self.states[0]
    eye, _ = self._eyes(walker)
    self.held = None
    before = len(self.states)
    assembly, states = self.place.given(self.assembly, self.states,
                                        State(eye))
    added = range(before, len(states))
    held = before
    for k in added:
      if assembly.bodies[k].mass > assembly.bodies[held].mass:
        held = k
    reach = reachOf(assembly.bodies[held])
    target = plus(eye, scaled(self._aim(), self.grabber.holdOf(
      assembly.bodies[held]) + self.further))
    for _ in range(100):
      if all(norm(minus(target, states[k].place)) > reach + reachOf(
          assembly.bodies[k]) for k in range(1, before)):
        break
      target = plus(target, (0.0, 0.0, 0.25 * reach))
    moved = minus(target, states[held].place)
    moving = (walker.velocity[0], walker.velocity[1], 0.0)
    self.assembly = assembly
    self.states = states[:before] + tuple(
      State(plus(states[k].place, moved), states[k].turn, moving)
      for k in added)
    self.held, self.pulling = held, False
    self._dressed()

  def record(self, ) -> None:
    """Records the next ten seconds of the view into a video in
    '_RECORDINGS', named for the time, and what each frame was painted
    from into a log beside it (none while one is under way)."""
    if self.recording is not None or self.view.recorder is not None:
      return
    os.makedirs(_RECORDINGS, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    path = os.path.abspath(os.path.join(_RECORDINGS,
                                        'phys-walk-%s.mp4' % stamp))
    meta = {'place': self.place.name, 'bodies': len(self.assembly.bodies),
            'fps': _RECORD_FPS, 'video': path}
    self.recording = Recorder(path, _RECORD_FPS, RECORDED, meta)
    self.view.recorder = self.recording
    self.recordButton.setEnabled(False)

  def reach(self, further: float) -> None:
    """Holds what is held 'further' m further (nearer if less than
    nought), within reason."""
    self.further = min(3.0, max(-0.5, self.further + further))

  def togglePlay(self, ) -> None:
    """Plays or pauses."""
    self.playing = not self.playing
    self.playButton.setText('Pause' if self.playing else 'Play')

  def tick(self, ) -> None:
    """Shows the world as the physics' thread last left it, and how it
    goes: the frames a second drawn, how long the physics' last step
    took, and, when it cannot keep up, how much of its true speed the
    world runs at."""
    began = time.perf_counter()
    passed, self.lastTick = began - self.lastTick, began
    self._heard()
    if self.rescueAsked:
      self.reset()
    if self.failed is not None:
      self.status.setText('  the physics stopped: %s' % self.failed)
      return
    if self.compiling is not None:
      self.status.setText('  compiling the small steps for %s (the first '
                          'run after a change: a few seconds)'
                          % self.compiling)
      return
    if not self.playing:
      self.status.setText('  paused%s' % self._recordingNow())
      return
    took = self.physicsTook
    aimed = self._showNow()
    walker = self.states[0]
    speed = math.hypot(walker.velocity[0], walker.velocity[1])
    held = ('holding %s' % self._massOf(self.held)
            if self.held is not None else
            'pointing at %s' % self._massOf(aimed)
            if aimed is not None else 'nothing in reach')
    behind = ('    the world at %.0f %% of real time (the physics '
              'cannot keep up)' % (100.0 * self.speedNow)
              if self.speedNow < 0.98 else '')
    held += self._tyreNow(aimed) + self._brakeNow() + self._steerNow()
    held += self._rigNow() + self._soapboxNow() + self._drivetrainNow()
    held += self._racerNow()
    held += self._soundNow()
    self.status.setText('  %.3f s    %.0f frames a second, physics (%s) '
                        '%.1f ms    %s %.2f m/s    %s%s%s'
                        % (self.clock, 1.0 / max(passed, 1e-3),
                           self.solver, 1000.0 * took,
                           'flying' if self.flying else 'riding'
                           if self.seated else 'walking',
                           speed, held, behind, self._recordingNow()))

  def _massOf(self, index: int) -> str:
    """Returns the mass of body 'index' and all it carries (a wheel's
    tyre), to read."""
    return _massOf(self.assembly.bodies[index].mass + sum(
      self.assembly.bodies[node].mass
      for node in self.carried.get(index, ())))

  def _steerNow(self, ) -> str:
    """Returns the steering wheel's angle asked and as it is, and the
    road wheels' (the knuckles', bodies 4 and 5; the tyre rig's, its
    one: left of straight ahead positive), degrees, where the place
    steers."""
    wall = self.place.steer
    if wall is None:
      return ''
    turned = self.wheelTurned[0] if self.wheelTurned else 0.0
    rig = self.place.rig
    road = []
    ride = self.place.ride
    knuckles = (4, 5) if ride is None else ride.knuckles
    for knuckle in knuckles if rig is None else (rig.knuckle,):
      ahead = rotated(self.states[knuckle].turn, (1.0, 0.0, 0.0))
      if ride is not None:
        ahead = rotated(conjugate(self.states[ride.chassis].turn), ahead)
      road.append('%+.1f°' % math.degrees(math.atan2(ahead[1], ahead[0])))
    how = ('set in the menu, E' if rig is not None else
           'A D steer, let go it centres' if self.seated else
           'arrows steer' if self.place.drivetrain is not None else
           'arrows steer, up centres')
    return ('    wheel %+.0f° (asked %+.0f°), road %s  (%s)' % (
      math.degrees(turned), math.degrees(wall.value), ' '.join(road), how))

  def _brakeNow(self, ) -> str:
    """Returns the brake's line's pressure, to read, where the place has
    a brake (and its first disc's wheel's speed)."""
    line = self.place.brake
    if line is None:
      return ''
    brakes = self.assembly.brakes
    turning = norm(self.states[brakes[0].disc].spin) if brakes else 0.0
    said = 'off' if line.pressure <= 0.0 else '%.0f bar' % (
      line.pressure / 1e5)
    return '    brake %s, wheel %.1f rad/s' % (said, turning)

  def _tyreNow(self, aimed: int | None) -> str:
    """Returns the pressure of the tyre held, or pointed at, or else the
    first, for the status ('' where there are none): a spring tyre's
    ('Tyre') as set, and its stiffness; a cord tyre's as the physics'
    thread last read them ('pressures': only that thread touches the
    GPU; read from here, the device was asked while that thread was
    capturing a new wheel's steps as a CUDA graph, and the capture
    broke: "Warp error: unknown stream", user, 2026-11-13)."""
    tyres = {tyre.body: tyre for tyre in self.assembly.tyres}
    if tyres:
      tyre = tyres.get(self.held, tyres.get(aimed, next(iter(
        tyres.values()))))
      return '    tyre %.2f bar, %.0f kN/m' % (tyre.pressure / 1e5,
                                               tyre.stiffness / 1e3)
    pressures, rims = self.pressures, list(self.carried)
    if not pressures or len(pressures) != len(rims):
      return ''
    which = self.held if self.held in self.carried else (
      aimed if aimed in self.carried else rims[0])
    return '    tyre %.2f bar' % (pressures[rims.index(which)] / 1e5)

  def _recordingNow(self, ) -> str:
    """Ends the recording once its time is up, and returns how it goes
    for the status: the time left, the frames still to write, where it
    was saved, or what went wrong."""
    recording = self.recording
    if recording is None:
      return self.recorded
    if self.view.recorder is not None:
      left = recording.left(time.perf_counter())
      if left > 0.0:
        return '    recording, %.1f s left' % left
      self.view.recorder = None
      recording.finish()
    if recording.writing:
      return '    writing the video, %d frames to go' % recording.pending
    self.recording = None
    self.recordButton.setEnabled(True)
    if recording.error is not None:
      self.recorded = '    recording failed: %s' % recording.error
    else:
      self.recorded = '    saved %s (and .json)' % recording.path
    return self.recorded

  def _run(self, ) -> None:
    """Steps the world on in a thread of its own (the window never
    waits for it: the GPU draws what it last left), each step as long as
    passed since the last, in the world's own time, never slowed (no
    less than half a frame: it waits), but no longer than the physics
    works out in two frames ('cost', the computing a simulated second
    takes, as lately found): the world then runs slower than real time,
    'speedNow' how much of it, and the picture still moves on every
    step. The walker walks, grabs and punts as asked. An error stops it,
    said in the status ('failed')."""
    last, cost = time.perf_counter(), 0.0
    while self.alive:
      now = time.perf_counter()
      passed = now - last
      if self.compiling is not None:
        last = now
        time.sleep(0.05)
        continue
      if not self.playing:
        last = now
        time.sleep(0.01)
        continue
      if passed < 0.5 * FRAME:
        time.sleep(0.5 * FRAME - passed)
        continue
      last, real = now, min(passed, 2.0 * FRAME)
      real = min(real, 2.0 * FRAME / cost) if cost > 0.0 else min(real,
                                                                  1e-3)
      try:
        with self.lock:
          self._step(real)
      except Exception as error:
        self.failed = '%s: %s' % (type(error).__name__, error)
        return
      self.physicsTook = time.perf_counter() - now
      found = self.physicsTook / real
      cost = found if cost == 0.0 else cost + 0.2 * (found - cost)
      self.speedNow += 0.2 * (real / passed - self.speedNow)

  def _step(self, real: float) -> None:
    """Walks, drives, grabs, punts and steps the world on for 'real' s
    of the world's own time."""
    self.seconds = real
    states = list(self.states)
    if self.seated and Qt.Key.Key_F in self.view.keys:
      self._getOut(states)
    if not self.seated:
      standing = self.walker.standingOn(self.assembly, self.states, 0,
                                        self.ground)
      self._walk(states, standing)
    self._drive(states)
    eye, forward = self._eyes(states[0])
    self._grab(states, eye, forward)
    self._punt(states, eye, forward)
    self.puntAsked, self.jumpAsked = False, False
    self.lastYaw = self.view.yaw
    stepped = tuple(self.world.advancedAll(
      self.assembly, tuple(states), self.seconds, self.clock))
    if not _finite(stepped):
      raise ValueError('the physics blew up (NaN) at %.3f s; what it '
                       'stepped from is in %s' % (self.clock, self._dumped(
                         tuple(states))))
    self.states = stepped
    if self.carried and isinstance(self.world, SmallSteps):
      self.pressures = self.world.pressuresOf(self.assembly)
    if self.place.steer is not None and isinstance(self.world, SmallSteps):
      self.wheelTurned = self.world.turnsOf(self.assembly)
    if (self.place.rig is not None or self.place.ride is not None) and (
        isinstance(self.world, SmallSteps)):
      self.tyreForces = self.world.tyreForcesOf(self.assembly)
    self.clock += self.seconds
    if self.racer is not None:
      chassis = self.states[_realcar.CHASSIS]
      self.lapTimer.seen(chassis.place[0], chassis.place[1], self.clock)
    respawn = self.place.respawn
    if respawn is not None and self.states[0].place[2] < respawn:
      self.states = (self.spawn,) + self.states[1:]
      self.flying = False

  def _dumped(self, states: tuple) -> str:
    """Writes what the world was stepped from when it blew up (the
    place, the time, the step asked, what was held, every body's place,
    turn, velocity and spin) to a JSON file in '_RECORDINGS', and
    returns its path: the step can be stepped again from it."""
    os.makedirs(_RECORDINGS, exist_ok=True)
    path = os.path.abspath(os.path.join(
      _RECORDINGS, 'phys-nan-%s.json' % time.strftime('%Y%m%d-%H%M%S')))
    with open(path, 'w') as file:
      json.dump({'place': self.place.name, 'clock': self.clock,
                 'seconds': self.seconds, 'held': self.held,
                 'flying': self.flying, 'solver': self.solver,
                 'bodies': len(self.assembly.bodies),
                 'states': [[state.place, state.turn, state.velocity,
                             state.spin] for state in states]}, file)
    return path

  def _setDriving(self, on: bool) -> None:
    """Notes whether the motor is to run (read by the physics' thread,
    which must not ask the button)."""
    self.driving = True if on else False

  def _setBraking(self, on: bool) -> None:
    """Notes whether the brake pedal is held down by the button (read by
    the physics' thread, which must not ask the button)."""
    self.braking = True if on else False

  def _setLine(self, bar: float) -> None:
    """Notes the line's pressure the pedal gives, Pa (from 'bar')."""
    self.linePressure = 1e5 * bar

  def _setRigSpeed(self, speed: float) -> None:
    """Notes how fast the tyre rig's deck is to run, m/s (read by the
    physics' thread, which must not ask the slider)."""
    self.rigSpeed = speed

  def _setRigLoad(self, kilonewtons: float) -> None:
    """Notes how hard the tyre rig's ram is to press, N (from kN)."""
    self.rigLoad = 1000.0 * kilonewtons

  def openTune(self, ) -> None:
    """Opens the tune-up menu ('TunePanel') beside the window, its
    sliders as the rig is set up now; a change sets the rig up anew
    with it ('_tuned')."""
    rig = self.place.rig if self.place.ride is None else self.place.ride
    if rig is None or rig.tune is None:
      return
    names = ('Front left',) if self.place.ride is None else (
      CORNER_NAMES)
    built = None if rig.tune.flywheel is None else FLYWHEEL_MASS
    if self.tunePanel is not None and (self.tunePanel.names != names or
                                       self.tunePanel.built != built):
      self.tunePanel.close()
      self.tunePanel = None
    if self.tunePanel is None:
      self.tunePanel = TunePanel(names, self, built)
      self.tunePanel.changed.connect(self._tuned)
    self.tunePanel.setSetups(rig.tune.wheels)
    self.tunePanel.setFlywheel(rig.tune.flywheel)
    self.tunePanel.show()
    self.tunePanel.raise_()

  def _tuned(self, setups: tuple) -> None:
    """Sets the rig up anew with the wheels' tune-up 'setups', as a
    mechanic sets a car up stopped."""
    rig = self.place.rig if self.place.ride is None else self.place.ride
    if rig is None or rig.tune is None:
      return
    rig.tune.wheels = tuple(setups)
    if rig.tune.flywheel is not None and self.tunePanel is not None:
      rig.tune.flywheel = self.tunePanel.flywheel
    self.reset()

  def _setRigSteer(self, degrees: float) -> None:
    """Notes the angle the tyre rig's steering wheel is to be held at,
    rad (from degrees; read by the physics' thread)."""
    self.rigSteer = math.radians(degrees)

  def _chooseSound(self, ) -> None:
    """Starts the engine's sound, or ends it, as 'Sound' says."""
    if self.soundButton.isChecked():
      self.engineSound.start(ENGINE_SIM)
    else:
      self.engineSound.close()

  def _heard(self, ) -> None:
    """Tells the engine's sound what the drivetrain bench's engine does
    (M turns it on or off): its revolutions and the throttle it opens
    (the idle governor's too); nothing heard elsewhere or off."""
    keys = self.view.keys
    if Qt.Key.Key_M in keys and self.soundButton.isEnabled():
      keys.discard(Qt.Key.Key_M)
      self.soundButton.toggle()
      self._chooseSound()
    controls = self.place.drivetrain
    if controls is None or not self.soundButton.isChecked():
      return
    read = readingOf(controls, self.states)
    on = self.playing and controls.running
    self.engineSound.heard(max(read.rpm, 0.0), controls.effective,
                           SOUND_VOLUME if on else 0.0)

  def _soundNow(self, ) -> str:
    """Returns what goes on with the sound, for the status (nothing
    while it plays, or is off)."""
    sound = self.engineSound
    if not self.soundButton.isChecked():
      return ''
    if sound.trouble:
      return '    no sound: %s' % sound.trouble[:60]
    if not sound.running:
      return '    no sound: its process ended'
    return '' if sound.ready else '    sound starting'

  def _setHands(self, on: bool) -> None:
    """Notes whether the soapbox's robot hands keep its line (read by
    the physics' thread)."""
    self.robotHands = True if on else False

  def _getOut(self, states: list) -> None:
    """Has the walker climb out of the car they ride (F): set a
    metre over it, as fast as it goes, flying (Shift lands), the view
    the world's again, looking the car's way."""
    chassis = states[self.place.ride.chassis]
    ahead = rotated(chassis.turn, (1.0, 0.0, 0.0))
    states[0] = State(plus(states[0].place, (0.0, 0.0, 1.0)),
                      (1.0, 0.0, 0.0, 0.0), chassis.velocity)
    self.seated, self.flying, self.jumpAsked = False, True, False
    self.view.yaw = math.atan2(-ahead[1], -ahead[0])

  def _drivetrained(self, controls: DrivetrainControls,
                    states: list) -> None:
    """Works the drivetrain as the keys ask: W the throttle open (Up,
    standing at the bench: W walks), the keypad's 0 the clutch down, I
    the starter, the keypad's 4 5 6 and 1 2 3 (R 2 4 over 1 3 5) and N
    the gear the hand moves the stick to ('GEAR_KEYS',
    'drivetrainWorked')."""
    keys = self.view.keys
    throttle = Qt.Key.Key_W if self.seated else Qt.Key.Key_Up
    controls.throttle = 1.0 if throttle in keys else 0.0
    controls.pedal = 1.0 if CLUTCH_KEY in keys else 0.0
    if Qt.Key.Key_I in keys:
      controls.starting = True
    for key, name in GEAR_KEYS.items():
      if key in keys:
        controls.asked = name
    drivetrainWorked(controls, states, self.seconds)

  def _drivetrainNow(self, ) -> str:
    """Returns the drivetrain bench's readings, where the place is it:
    the engine's revolutions and twist (or stalled), the gear and the
    stick in its dog-leg gate (held at a synchro), the clutch's slip and
    the wheels' speeds."""
    controls = self.place.drivetrain
    if controls is None:
      return ''
    read = readingOf(controls, self.states)
    engine = ('%.0f rpm, %+.0f N m' % (read.rpm, read.twist)
              if controls.running else 'stalled (hold I to start)')
    stick = controls.shifter
    held = '' if stick.blocked is None else (
      ', held at %s\'s synchro' % stick.blocked)
    return ('    engine %s    gear %s (stick %+.1f across, %+.1f along%s)'
            '    clutch %s, slipping %.0f rad/s    wheels %.1f %.1f km/h%s'
            '    (%s, keypad 0 clutch, keypad 456/123 R24/135, N neutral, I '
            'start, %s)' % (
              engine, read.gear, read.across, read.throw, held,
              'down' if controls.pressed > 0.5 else 'up', read.slip,
              3.6 * read.left, 3.6 * read.right, self._antilockNow(),
              'W throttle' if self.seated else 'Up throttle',
              'S brakes, Space handbrake, F get out' if self.seated
              else 'B brake'))

  def _antilockNow(self, ) -> str:
    """Returns what the car's anti-lock brakes do, where it has them:
    the wheels they let go of (front left, front right, rear left, rear
    right), the handbrake pulled."""
    ride = self.place.ride
    if ride is None or ride.brakes is None:
      return ''
    brakes = ride.brakes
    eased = [name for name, share in zip(('FL', 'FR', 'RL', 'RR'),
                                         brakes.shares) if share < 1.0]
    return '%s%s' % (', ABS easing %s' % ' '.join(eased) if eased else '',
                     ', handbrake' if brakes.pulled else '')

  def _soapboxNow(self, ) -> str:
    """Returns the soapbox's readings, where the place is it: its speed,
    how hard its tyres press (all four, in its weight: g), whether the
    driver is sat in it and who steers."""
    if self.place.soapbox is None:
      return ''
    chassis = self.states[CHASSIS]
    weight = 9.81 * sum(body.mass for k, body in enumerate(
      self.assembly.bodies) if k != 1)
    pressed = sum(norm(force) for force in self.tyreForces) / weight
    return ('    soapbox %.1f m/s (%.0f km/h), tyres %.1f g, %s, %s' % (
      norm(chassis.velocity), 3.6 * norm(chassis.velocity), pressed,
      'sat in it (F: get out, S brakes)' if self.seated else 'out of it',
      'robot hands' if self.robotHands else 'A D steer'))

  def _setHumps(self, on: bool) -> None:
    """Notes whether the tyre rig's humps are to be bolted on."""
    self.rigHumped = True if on else False

  def _rigged(self, rig: RigControls) -> None:
    """Works the tyre rig's controls as the window's are set: the deck's
    motor asked for the speed, the ram's load, the humps on or off, the
    hands turning the steering wheel toward the angle the menu holds it
    at ('STEER_RATE' at most: a hand's, not a jump)."""
    rig.setSpeed(self.rigSpeed)
    rig.load.value = self.rigLoad
    step = STEER_RATE * self.seconds
    rig.steer.value += max(-step, min(step, self.rigSteer - rig.steer.value))
    rig.humps.humps = rigHumps(RIG_HUMPS) if self.rigHumped else ()

  def _rigNow(self, ) -> str:
    """Returns the tyre rig's readings, where the place is it: the
    deck's speed under the wheel, how far out from its middle the wheel
    runs (steered: the boom swings it across, as a record player's arm),
    and the wheel's rim's speed (its slip: the rim
    slower than the deck is braking), and what the deck does to the tyre
    as the last call had it: its load, its pull along the deck's way
    (braking: the deck dragging the tyre back) and the share that is of
    the load, its side force (toward the deck's middle positive)."""
    rig = self.place.rig
    if rig is None or not self.tyreForces:
      return ''
    wheel, table = self.states[rig.wheel], self.states[rig.table]
    axle = rotated(wheel.turn, (0.0, 0.0, 1.0))
    radius = wheel.place[2] - TABLE_TOP
    rim = abs(sum(a * b for a, b in zip(wheel.spin, axle))) * radius
    out = (wheel.place[0] - table.place[0], wheel.place[1] - table.place[1])
    reach = math.hypot(out[0], out[1])
    deck = abs(table.spin[2]) * reach
    force = self.tyreForces[0]
    way = (-out[1] / reach, out[0] / reach) if table.spin[2] > 0.0 else (
      out[1] / reach, -out[0] / reach)
    pull = force[0] * way[0] + force[1] * way[1]
    side = -(force[0] * out[0] + force[1] * out[1]) / reach
    load = force[2]
    slip = (rim - deck) / deck if deck > 0.5 else 0.0
    camber = math.degrees(math.asin(max(-1.0, min(1.0, -axle[2]))))
    tune = '' if rig.tune is None else '    tune %.2f bar, camber %+.1f°, ' \
      'toe %+.2f° in' % (rig.tune.wheels[0].pressure / 1e5,
                         math.degrees(rig.tune.wheels[0].camber),
                         math.degrees(rig.tune.wheels[0].toe))
    return ('    deck %.1f m/s %.2f m out, rim %.1f (slip %+.1f %%), load '
            '%.2f kN, pull %.2f kN (%.2f of it), side %+.2f kN, camber '
            '%+.1f°%s' % (
              deck, reach, rim, 100.0 * slip, load / 1000.0,
              pull / 1000.0, pull / load if load > 1.0 else 0.0,
              side / 1000.0, camber, tune))

  def _steer(self, wall: FourthWall) -> None:
    """Turns the steering wheel's fourth wall point as the keys ask (the
    player's hands): sat in the car, A and D turn it 'STEER_RATE' rad/s
    left and right, and with neither (or both) held it comes back to
    straight as fast (user, 2026-11-14); standing, the arrow keys, up
    bringing it back where there is no drivetrain (Up is its throttle);
    never past 'STEER_MOST' either way."""
    keys, step = self.view.keys, STEER_RATE * self.seconds
    if self.seated:
      way = (Qt.Key.Key_A in keys) - (Qt.Key.Key_D in keys)
      if way == 0:
        way = -1 if wall.value > 0.0 else 1 if wall.value < 0.0 else 0
        step = min(step, abs(wall.value))
      wall.value = max(-STEER_MOST, min(STEER_MOST,
                                        wall.value + way * step))
      return
    way = (Qt.Key.Key_Left in keys) - (Qt.Key.Key_Right in keys)
    if way == 0 and Qt.Key.Key_Up in keys and self.place.drivetrain is None:
      way = -1 if wall.value > 0.0 else 1 if wall.value < 0.0 else 0
      step = min(step, abs(wall.value))
    wall.value = max(-STEER_MOST, min(STEER_MOST, wall.value + way * step))

  def _drive(self, states: list) -> None:
    """Sets the place's brake's line, its pressure while the brake is on
    or B held (sat in a car, S), else none; a car with anti-lock brakes
    pressed hard ('FOOT') by S, each wheel's caliper as its anti-lock
    lets it, the handbrake pulled while Space is held ('Antilock'); and
    its motor running, as an electric motor does, worked out at every
    step ('runMotor'), while the drive is on; turning freely while off;
    its housing takes the twist back."""
    keys, ride = self.view.keys, self.place.ride
    if self.racer is not None and self.robotHands:
      self._raced(states)
      return
    if self.place.brake is not None:
      foot = self.seated and Qt.Key.Key_S in keys
      down = self.braking or foot or (
        not self.seated and Qt.Key.Key_B in keys)
      hard = foot and ride is not None and ride.brakes is not None
      self.place.brake.pressure = (FOOT if hard else self.linePressure
                                   if down else 0.0)
    if ride is not None and ride.brakes is not None:
      ride.brakes.pulled = self.seated and Qt.Key.Key_Space in keys
      pressed = 0.0 if self.place.brake is None else (
        self.place.brake.pressure)
      ride.brakes.worked(pressed, self.assembly, states, self.seconds)
    if self.place.drivetrain is not None:
      self._drivetrained(self.place.drivetrain, states)
    if self.keeper is not None and self.robotHands:
      self.keeper.steer(states[CHASSIS], self.assembly.bodies[CHASSIS],
                        self.seconds)
    elif self.place.steer is not None and self.place.rig is None:
      self._steer(self.place.steer)
    if self.place.rig is not None:
      self._rigged(self.place.rig)
    if self.place.motor is None:
      return
    index, free, stall = self.place.motor
    runMotor(self.assembly.motors[index].drive, stall, free, self.driving)

  def _raced(self, states: list) -> None:
    """Has the racing driver drive the real car round the oval
    ('RealCarRacer': its steering wheel, pedals and stick as it asks),
    its anti-lock brakes and drivetrain worked as the controls say; a
    driver stranded (no way made for long: rolled over, stuck) has the
    car set on the start line again ('rescueAsked', by the window's
    tick)."""
    racer, place = self.racer, self.place
    racer.take(states, self.seconds)
    place.ride.brakes.worked(place.brake.pressure, self.assembly, states,
                             self.seconds)
    drivetrainWorked(place.drivetrain, states, self.seconds)
    if racer.stranded:
      self.rescueAsked = True

  def _racerNow(self, ) -> str:
    """Returns the racing driver's readings, where it drives: who drives,
    what its left foot and hand do, the lap it runs, the last and the
    best."""
    if self.racer is None:
      return ''
    timer = self.lapTimer
    who = ('robot driving (%s, gear %s)' % (self.racer.shifting,
                                             self.racer.gear)
           if self.robotHands else 'you drive (Robot hands: off)')
    credit = '' if self.place.credit is None else (
      '    ' + self.place.credit)
    return '    %s    lap %d %s    last %s    best %s%s' % (
      who, len(timer.laps) + 1, lapText(timer.now(self.clock)),
      lapText(timer.last), lapText(timer.best), credit)

  def _walk(self, states: list, standing: tuple | None) -> None:
    """Walks the walker in 'states' as the keys ask, at once, as a
    game's player ('Walker.strode'), and jumps it if asked, standing
    (what it stood on pushed down as hard); or flies it, landing
    (walking again) once it is let down onto something."""
    keys, body = self.view.keys, self.assembly.bodies[0]
    ahead = (Qt.Key.Key_W in keys) - (Qt.Key.Key_S in keys)
    aside = (Qt.Key.Key_D in keys) - (Qt.Key.Key_A in keys)
    down = Qt.Key.Key_Shift in keys
    if self.flying and standing is not None and down:
      self.flying = False
    if self.flying:
      upward = (Qt.Key.Key_Space in keys) - down
      wanted = flyingOf(self.walker, self.view.yaw, ahead, aside, upward,
                        Qt.Key.Key_Control in keys)
      states[0] = self.walker.flown(states[0], wanted, GRAVITY,
                                    self.seconds)
      return
    wanted = wantedOf(self.walker, self.view.yaw, ahead, aside, down)
    if standing is None:
      state = states[0]
      states[0] = poked(body, state, state.place, (0.0, 0.0, 0.0))
      return
    states[0] = self.walker.strode(states[0], wanted, self.seconds)
    if not self.jumpAsked:
      return
    states[0], impulse = self.walker.jumped(body, states[0])
    under, point = standing
    if under is not None:
      self._pushBack(states, under, point, impulse)

  def _grab(self, states: list, eye: tuple, forward: tuple) -> None:
    """Holds what is held where the hold is, letting it go once it is
    lost; or pulls in what the grabber points at, holding it once it
    is near the hold. Nothing is pushed back."""
    if self.held is None and not self.pulling:
      return
    aim = self._aim()
    walker, grabber = states[0], self.grabber
    moving = (walker.velocity[0], walker.velocity[1], 0.0)
    index = self.held
    if index is None:
      hit = self._aimed(states, eye, forward, grabber.reach)
      if hit is None or hit[0] in self.rigged:
        return
      index = hit[0]
    body, state = self.assembly.bodies[index], states[index]
    hold = grabber.holdOf(body)
    target = plus(eye, scaled(aim, hold + self.further))
    if self.held is None:
      if grabber.catches(body, state, target):
        self.held, self.pulling = index, False
      else:
        states[index], _ = grabber.pulled(body, state, target, moving,
                                          GRAVITY, self.seconds)
        self._carry(states, index, state)
        return
    if norm(minus(state.place, target)) > _LOST + hold:
      self.held = None
      return
    turning = (0.0, 0.0, (self.view.yaw - self.lastYaw) / self.seconds)
    states[index], _ = grabber.held(body, state, target, moving, turning,
                                    GRAVITY, self.seconds)
    self._carry(states, index, state)

  def _carry(self, states: list, index: int, was: State) -> None:
    """Moves what body 'index' carries (a wheel's tyre: 'carried') as
    much faster as it was just made to go than 'was' (the grabber holds
    a wheel whole: held by its rim alone, its tyre hung off it)."""
    nodes = self.carried.get(index, ())
    if not nodes:
      return
    change = minus(states[index].velocity, was.velocity)
    for node in nodes:
      at = states[node]
      states[node] = State(at.place, at.turn, plus(at.velocity, change),
                           at.spin, at.bristles, at.holds, at.rest)

  def _punt(self, states: list, eye: tuple, forward: tuple) -> None:
    """Punts what is held along the look, letting it go, or what the
    grabber points at within its punt's reach (not a body on legs),
    where it points: as hard as sends it off at the 'Punt' slider's
    speed (shrunk by the root of the place's 'scale', as speeds are), up
    to '_PUNT_MASS' (times its cube; heavier, a bearing's ring say, it is
    punted as that much: not slammed into its balls). A body on springs
    weighs all it is sprung to (a tyre's lump, the tyre and its wheel:
    a punt spins the wheel, not a lump alone). Nothing is pushed
    back."""
    if not self.puntAsked:
      return
    if self.held is not None:
      index = self.held
      point = states[index].place
      self.held = None
    else:
      hit = self._aimed(states, eye, forward, self.grabber.punt)
      if hit is None or hit[0] in self.rigged:
        return
      index, point = hit[0], hit[1]
    body = self.assembly.bodies[index]
    scale = self.place.scale
    speed = self.puntSlider.quantity * math.sqrt(scale)
    if index in self.carried:
      whole = body.mass + sum(self.assembly.bodies[node].mass
                              for node in self.carried[index])
      was = states[index]
      share = min(1.0, _PUNT_MASS * scale ** 3 / whole)
      states[index], _ = self.grabber.punted(body, was, point, forward,
                                             body.mass * speed * share)
      self._carry(states, index, was)
      return
    mass = min(_sprungMassOf(self.assembly, index),
               _PUNT_MASS * scale ** 3)
    states[index], _ = self.grabber.punted(body, states[index], point,
                                           forward, mass * speed)

  def _pushBack(self, states: list, index: int, point: tuple,
                impulse: tuple) -> None:
    """Gives body 'index' in 'states' 'impulse' the other way at
    'point'."""
    body = self.assembly.bodies[index]
    states[index] = poked(body, states[index], point, scaled(impulse, -1.0))

  def _aim(self, ) -> tuple:
    """Returns the way from the eyes to the hold: the look, no lower
    than '_LOWEST_HOLD' down."""
    yaw, pitch = self.view.yaw, min(self.view.pitch, _LOWEST_HOLD)
    return (-math.cos(pitch) * math.cos(yaw),
            -math.cos(pitch) * math.sin(yaw), -math.sin(pitch))

  def _findSteel(self, ) -> None:
    """Notes the bodies of steel, drawn steel, and of plastic, drawn
    ivory (by how dense they are), each looking so; hidden ones are not
    drawn (a tyre's lumps, whose tone its skin would take)."""
    self.steel, looks = {}, {}
    for index, body in enumerate(self.assembly.bodies):
      if body.shape is None or index in self.view.hidden:
        continue
      dense = body.mass / body.shape.volume()
      if dense >= _STEEL:
        self.steel[index], looks[index] = _STEEL_TONE, _STEEL_LOOK
      elif _PLASTIC[0] <= dense < _PLASTIC[1]:
        self.steel[index], looks[index] = _PLASTIC_TONE, _PLASTIC_LOOK
    self.view.looks = looks

  def _aimed(self, states: list, eye: tuple, forward: tuple,
             reach: float) -> tuple | None:
    """Returns what the grabber points at within 'reach' m of the eyes,
    as 'hitOf' gives it; None for nothing (the walker and hidden bodies
    passed over). A skin the view draws is met too, nearer first: at a
    tyre, the lump under the rubber there; a cord tyre's rubber, its
    wheel's rim."""
    states = tuple(states)
    hit = hitOf(self.assembly, states, eye, forward, self.passed)
    met = self.tyreHits.hitOf(states, eye, forward)
    if met is not None and (hit is None or norm(minus(met[1], eye))
                            < norm(minus(hit[1], eye))):
      hit = met
    for skin, _ in self.view.skins:
      met = skin.hitOf(states, eye, forward)
      if met is not None and (hit is None or norm(minus(met[1], eye))
                              < norm(minus(hit[1], eye))):
        hit = met
    if hit is None or norm(minus(hit[1], eye)) > reach:
      return None
    return hit

  def _eyes(self, walker: object) -> tuple:
    """Returns where the walker's eyes are and the way they look: sat
    in the soapbox, its chassis' own over the seat ('SOAPBOX_EYES' up
    the car's up from their ball's middle), the view riding with it (but
    in the chase view: '_chased' places the camera)."""
    yaw, pitch = self.view.yaw, self.view.pitch
    forward = (-math.cos(pitch) * math.cos(yaw),
               -math.cos(pitch) * math.sin(yaw), -math.sin(pitch))
    if not self.seated:
      self.view.riding = None
      return self.walker.eyeOf(walker), forward
    ride = self.place.ride
    chassis = self.states[ride.chassis]
    self.view.riding = None if self.view.chasing else chassis.turn
    eye = self.assembly.bodies[ride.chassis].placeOf(
      chassis, plus(ride.seat, (0.0, 0.0, SOAPBOX_EYES)))
    return eye, rotated(chassis.turn, forward)

  def _showNow(self, ) -> int | None:
    """Shows the place from the walker's eyes (to 10 µm) and its bodies
    where they are (to the micrometre, their turns to 1e-9; both times
    the place's 'scale'): standing on a springy ground the walker bobs by
    nanometres and balls held in stiff contacts quiver so, which flipped
    pixels on edges and cuts to and fro; tints what is held and what the
    grabber points at within its reach (asleep or not, bodies keep their
    own tones; sat in a car, nothing: its ray was a tenth of a frame's
    work); returns what it points at. Sat in a car with the chase view
    on, from behind it ('_chased')."""
    eyeStep, step = 1e-5 * self.place.scale, 1e-6 * self.place.scale
    hit = None
    if self.seated and self.view.chasing:
      self._chased()
    else:
      eye, forward = self._eyes(self.states[0])
      self.view.distance, self.view.crosshair = 0.0, True
      self.view.target = tuple(round(x / eyeStep) * eyeStep for x in eye)
      if not self.seated:
        hit = self._aimed(list(self.states), eye, forward,
                          self.grabber.reach)
    aimed = None if hit is None else hit[0]
    tones = dict(self.steel)
    if aimed is not None and aimed not in self.rigged:
      tones[aimed] = _AIMED_TONE
    if self.held is not None:
      tones[self.held] = _HELD_TONE
    self.view.tones = tones
    self.view.show_(self.assembly, tuple(
      State(tuple(round(x / step) * step for x in state.place),
            tuple(round(x, 9) for x in state.turn), state.velocity,
            state.spin, (), (), state.rest)
      for state in self.states), math.inf)
    return aimed


  def _chased(self, ) -> None:
    """Puts the camera behind the car ridden ('CHASE_' constants):
    'chaseFar' m back, looking 'CHASE_LIFT' m over its chassis' middle
    and 'chaseTilt' down, swung round after its heading
    ('GpuView.follow') and the mouse's look; the look eased back behind
    once left alone a while with the car going."""
    view, ride = self.view, self.place.ride
    chassis = self.states[ride.chassis]
    ahead = rotated(chassis.turn, (1.0, 0.0, 0.0))
    now = time.perf_counter()
    seconds = min(0.1, max(0.0, now - self.chasedAt))
    self.chasedAt = now
    if now - view.lookedAt > CHASE_BACK and norm(chassis.velocity) > (
        CHASE_MOVING):
      back = CHASE_RETURN * seconds
      around = (view.around + math.pi) % (2.0 * math.pi) - math.pi
      view.around = around - max(-back, min(back, around))
      view.chaseTilt += max(-back, min(back, CHASE_PITCH - view.chaseTilt))
    view.riding, view.crosshair = None, False
    view.distance, view.pitch = view.chaseFar, view.chaseTilt
    view.follow(chassis.place, math.atan2(ahead[1], ahead[0]), seconds)
    place = chassis.place
    view.target = (place[0], place[1], place[2] + CHASE_LIFT)


def _finite(states: tuple) -> bool:
  """Returns whether every body of 'states' is somewhere, moving
  somehow (no NaN, no infinity in its place or velocity)."""
  return math.isfinite(sum(x for state in states
                           for x in state.place + state.velocity))


def _sprungMassOf(assembly: object, index: int) -> float:
  """Returns the mass of body 'index' of 'assembly' and of every body
  springs join it to, through one another, kg."""
  near = {}
  for spring in assembly.springs:
    if spring.first is not None and spring.second is not None:
      near.setdefault(spring.first, set()).add(spring.second)
      near.setdefault(spring.second, set()).add(spring.first)
  seen, waiting = {index}, [index]
  while waiting:
    for other in near.get(waiting.pop(), ()):
      if other not in seen:
        seen.add(other)
        waiting.append(other)
  return sum(assembly.bodies[one].mass for one in seen)


def _massOf(mass: float) -> str:
  """Returns 'mass' (kg) to read: kg, or g under one."""
  if mass < 1.0:
    return '%.3g g' % (1000.0 * mass)
  return '%.0f kg' % mass


class WalkApp(App):
  """WalkApp opens a 'WalkWindow'. On a Wayland desktop it runs through
  XWayland ('xcb'), unless a platform is asked for: Wayland lets no
  program move the pointer, so the hidden pointer could not be put back
  in the middle and left the window as the head turned (user,
  2026-11-13: "make it keep the mouse cursor in the window")."""

  __window_class__ = WalkWindow

  def __init__(self, *args) -> None:
    if os.environ.get('WAYLAND_DISPLAY') and os.environ.get('DISPLAY'):
      os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')
    App.__init__(self, *args)
