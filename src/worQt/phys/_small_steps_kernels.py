"""
The Warp kernel 'stepsRun' steps an assembly on as 'SmallSteps' does:
in small steps, its touches kept as rules (extended position based
dynamics: Müller, Macklin, Chentanez, Jeschke and Kim, 2020, "Detailed
Rigid Body Simulation with Extended Position Based Dynamics"; small
steps: Macklin, Storey, Lu, Terdiman, Chentanez, Jeschke and Müller,
2019). Each step the motors twist their rotors (their damping solved
with the rotor's turning, so a light rotor stays steady) and every
body moves freely; then, as often as 'passes' says, every touch pushes
its two bodies just far enough apart, and holds the points that
touched together where its grip can (all at once, each touch on its
own thread: Jacobi's way, which a GPU is good at; each body's mass
split evenly among the rules pressing it in the pass, each rule solved
with its share, the body taking them all: mass splitting, Tonge, Gu
and Ma 2012; taking the average of their asks instead, an 8 g ball's
push on the 930 g shaft it carries was heard as a fortieth, and the
shaft sank a millimetre into its balls), and then every tie and rod
pulls its points together or to its length, and every hinge its pin's
points together and its lines in line (rigid, or as its rubber gives:
'holdHinge'), split among the links alone (split with the touches, the
shaft's 40 would leave the gear's key a fortieth of its own), and the
drivetrain, its gears meshing and its disc brakes, holds, solved
together and exactly ('trainSolved'); the bodies' velocities are read
off how far they moved; then every touch that
pushed takes away how fast its bodies close or part, and how fast they
slide along each other as far as its grip lets (no bounce); then the
brakes slow their discs and the bushings' rubber and the springs' and
dampers' damping damp, in 'DAMP_ROUNDS' rounds, each body split among
the rules that damp it ('dampGive'). Rams push before the bodies move
freely, as gravity does ('linePushed'); a tyre rolls on the ground or
on a turntable's face, over the humps bolted to it ('WHEEL_TURNED'),
or on a track's planks ('WHEEL_PIECES').

float32 throughout (a GeForce card works singles 64 times as fast as
doubles; user: "no float64!"), places from an origin near the bodies,
each as a place and a shift: how far the body has moved since its place
was last moved on. A step moves a body a few hundredths of a
millimetre, which a place 0.2 m out rounds to a few of float32's last
bits, the same way step after step (a ball rolling down a ramp lost
0.2 % of its way at 1 ms steps, 1.9 % at 0.06 ms); in the shift it is
exact, velocities are read off it, and once a step the place takes it
on, the shift keeping what that rounds off (Knuth's two-sum: together
they lose nothing). A body's spin likewise is read off how far it
turned in the step, kept as a turn of its own (the free turn and every
correction, in float32, exact), not off its turns before and after,
whose difference float32 rounds alike step after step (the bearing's
shaft, its motor cut, sped up 3 % coasting at 0.125 ms steps). Turns
are Warp's
quaternions (x, y, z, w), from a body's principal axes to the world's.
A call's steps are one launch, its threads in one block, waiting for
each other between the parts ('barrier'); on the CPU one thread runs
them all.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import warp as wp

wp.config.log_level = wp.LOG_WARNING
wp.set_module_options({'enable_backward': False})

#  What a touch is: a skin point against the ground, a ball against the
#  ground, a skin point against another body's pieces, a ball against
#  another body's pieces, a ball against a ball.
POINT_GROUND = wp.constant(0)
BALL_GROUND = wp.constant(1)
POINT_PIECES = wp.constant(2)
BALL_PIECES = wp.constant(3)
BALL_BALL = wp.constant(4)
#  A ball against one piece of a turned solid's profile; a roller (a
#  turned rectangle, 'rollerShape') against one (a raceway along its
#  line, a rib across its end), at one of two points; a roller against
#  a roller, at one of two points along them.
BALL_TURNED = wp.constant(5)
ROLLER_TURNED = wp.constant(6)
ROLLER_ROLLER = wp.constant(7)
#  A skin point of a convex shape against one straight piece of a
#  turned solid's profile (a cage on its ring's land).
POINT_TURNED = wp.constant(8)
#  A tyred wheel's tyre on the ground ('Tyre': a spring in the wheel's
#  plane, pushing only), a probe of a wheel (a ball of 'reach' at a skin
#  point) on a turned solid's profile piece, and on the ground.
WHEEL_GROUND = wp.constant(9)
PROBE_TURNED = wp.constant(10)
PROBE_GROUND = wp.constant(11)
#  A tyred wheel's tyre on a turned solid's flat face across its axis
#  (a turntable's top), as on the ground, over the humps bolted to it.
WHEEL_TURNED = wp.constant(12)
#  A tyred wheel's tyre on a convex shape's faces (a track of planks),
#  as on the ground: 'wheelOnPieces'.
WHEEL_PIECES = wp.constant(13)
#  A skin point, a probe (a ball of 'reach' at a skin point) and a ball
#  against an oval's safety barrier ('wallBeyond': its face, up to its
#  height over the ground).
POINT_WALL = wp.constant(14)
#  How far from any of a town's walls a place off their grid is held to
#  be, m ('_gridwall.WALL_REACH').
GRID_WALL_REACH = wp.constant(8.0)
PROBE_WALL = wp.constant(15)
BALL_WALL = wp.constant(16)
#  What a gear rule is: a rack and pinion, two gears meshing.
RACK = wp.constant(0)
MESH = wp.constant(1)
#  How much the drivetrain's equations are eased, each as a share of its
#  own ('trainFactored'): enough for float32 to solve a differential's
#  two spiders, each holding the side gears as the other does (of their
#  four meshes one says nothing new), and no more (what it leaves, the
#  solve's second round takes up).
TRAIN_EASE = wp.constant(1e-4)
#  How many threads solve the drivetrain's equations together: a GPU's
#  warp, waiting for each other as one ('laneBarrier': cheaper than the
#  whole block's 'barrier'; held to a factor of the 24 or so rules that
#  hold, its columns side by side).
TRAIN_LANES = wp.constant(32)
#  How many of a pass's drivetrain solves one inverse of its equations
#  serves ('trainSolved'; the same rules holding: a gear's axis and give
#  barely move in so few steps, and the solve's second round, on the
#  equations as they are, takes up what that leaves). A solve on the
#  user's GPU factored anew each step was 39 % of the real car's step.
TRAIN_REUSE = wp.constant(16)
#  How many steps apart the touches are looked over for which could press
#  ('nearTouch'), and how far past what their speeds and gravity carry
#  them in that time they still count, m.
NEAR_EVERY = wp.constant(16)
NEAR_MARGIN = wp.constant(0.05)
#  The parts of a step timed when profiled ('marked'), as numbered in
#  'stepsRun'.
PROFILE_PARTS = ('near', 'air', 'motors', 'move', 'touches found',
                 'touches push', 'moves taken', 'links and hinges', 'cords',
                 'train rules', 'train pairs', 'train solve', 'train turns',
                 'velocities', 'touches settle', 'kicks taken', 'damping')
#  A body's pieces looked at for a point: all of them (it has no grid),
#  none (the point is off its grid).
WHOLE = wp.constant(-2)
OFF_GRID = wp.constant(-1)
#  How far past a face's edge a tyre's touch on it still counts, m (planks
#  laid edge to edge: at the join it is on both, float32 rounding
#  whatever).
WHEEL_EDGE = wp.constant(1e-3)
#  How far from lying flat (the sine of its axle's tilt from upright) a
#  wheel's tyre still springs on the ground: flatter, its sidewalls'
#  probes meet it.
FLAT = wp.constant(0.1)
#  How fast a touch pushes its bodies out of each other at most, m/s
#  (PhysX's 'max depenetration velocity'): a fall's or a punt's
#  overlap, a step's travel, is undone at once; one deeper (a body put
#  into another) is undone at this pace, not in a step (a wheel given
#  inside another flew off at hundreds of metres a second).
UNSTICK = wp.constant(10.0)
#  How far out along a roller its two points meet a raceway or another
#  roller, a share of half its length.
ROLLER_REACH = wp.constant(0.8)
#  What a link is: a tie (its points together), a rod (its points its
#  length apart).
TIE = wp.constant(0)
ROD = wp.constant(1)
#  A profile's piece: a line, an arc.
LINE = wp.constant(0)
FAR = wp.constant(1e30)
TWO_PI = wp.constant(6.283185307179586)
#  m: a point this near a face's plane is on it (float32's rounding of
#  a place a metre out is ~0.1 um).
EDGE = wp.constant(1e-6)
#  A touch pushes a body into what holds it still when it pushes it
#  within 60 degrees of straight against that hold ('intoHold').
SHOCK = wp.constant(0.5)
#  A touch slot holding nothing (a crowd's room not taken this call).
NO_TOUCH = wp.constant(-1)
#  The air outside, Pa ('ATMOSPHERE').
OUTSIDE = wp.constant(101325.0)
#  How often a cord line is solved again, its cords found pushing let go
#  ('holdChain').
CHAIN_ROUNDS = wp.constant(4)
#  How many rounds the bushes' rubber and the springs' and dampers'
#  damping slow their bodies in, a step, each with its share of the step
#  (each round no more than stops what it slows, as its bodies' shares
#  give: once, a shock's damper on a light wishbone gave the tyre rig's
#  corner a sixth of critical for the third it was made with; rounds
#  close on what the damping asks, as Jacobi's do).
DAMP_ROUNDS = wp.constant(4)
#  The tyre's slip law (a brush's: the tread in its patch stretched as
#  its rim slips on the road, let go as it rolls through its relaxation
#  length; 'tyreGrip'; user, 2026-11-14, its rigid grip walking the rig's
#  wheel sideways for ever): its cornering stiffness at 'TYRE_LOAD' N on
#  it, N/rad (growing as its load to the 0.8), along the road that times
#  'TYRE_LONG', its relaxation length, m; its grip falling 'TYRE_LOAD_
#  SENSE' of itself for each 'TYRE_LOAD' more on it; past its peak, its
#  grip sliding down toward 'TYRE_SLIDE' of itself as the patch slides
#  faster than it first slid all through, by 'TYRE_SLIDE_SPEED' m/s
#  halfway; its tread's rubber damping its stretching while it holds,
#  N s/m; its patch's twist on the road, N m/rad at 'TYRE_LOAD' (as its
#  load), let go as it rolls as its stretch is (steering a parked car is
#  heavy, a rolling one light), damped N m s. Measured against
#  'test_tyre_slip'.
TYRE_LOAD = wp.constant(3000.0)
TYRE_CORNERING = wp.constant(7e4)
TYRE_LONG = wp.constant(1.5)
TYRE_RELAX = wp.constant(0.3)
TYRE_LOAD_SENSE = wp.constant(0.15)
TYRE_SLIDE = wp.constant(0.7)
TYRE_SLIDE_SPEED = wp.constant(1.0)
TYRE_TREAD_DAMPING = wp.constant(1000.0)
TYRE_TWIST = wp.constant(4000.0)
TYRE_TWIST_DAMPING = wp.constant(20.0)
#  The road's texture's field smoothed between its corners spreads 0.743
#  of theirs: this makes it one.
TEXTURE_SPREAD = wp.constant(1.3463)


@wp.struct
class Run:
  """What a call is: its steps, how long each is, s, how many passes
  each makes over the touches, gravity, m/s², how high the ground is
  (from the origin), how far a skin point is shaken at random as it is
  looked for in another body ('grease', m) and the draws' seed (the
  call's first step's number), whether the motors twist their rotors
  as the rotors move ('motorsMerged': every housing still), how many
  threads run it, and how many bodies, touches (and ways and groups of
  them looked for together: 'nearWay'), links and motors there are, how
  many colours of cord lines ('Chains'), airs and faces of
  them ('Airs'), how many disc brakes ('Brakes'), hinges and slides
  ('Hinges'), springs and dampers ('Lines'), fourth wall points that
  turn ('Turns') and racks and pinions and gears meshing ('Gears'), of
  them racks ('racks', the first; the meshes after), how many pairs of
  the drivetrain's rules share a body ('Train'); whether the call's
  steps are timed part by part ('profiling': 'marked', into 'profile',
  cycles a part: 'PROFILE_PARTS'); the road's texture as
  the tyres feel it: their grip's spread ('rough', a share), how far
  along it it is smooth ('grain', m), its seed ('texture'); and whether
  the ground is a terrain ('terrain': heights over a grid, the ground
  between them bilinear, the floor off it; user, 2026-11-15: the real
  car on the oval): its grid's first corner (from the origin, x y,
  'terrainAt'), its cells' size ('terrainCell', m), how many points
  along x and y ('terrainNx', 'terrainNy') and their heights from the
  origin ('heights', a row along y for each x, one after another), and
  how much its slope changes at most within a cell and into the cells
  about it ('bends', a cell's for each cell, as 'heights'; 'terrainBend'
  the most of all, for off the grid); and whether walls stand on it
  ('wall': 0 none, 1 an oval's safety barrier, 2 a town's on a grid):
  for an oval's barrier where the oval's middle is (from the origin,
  'wallAt'), its straights' half length and its turns' radius (its
  middle line's), how far out from that line the barrier's face stands
  and how tall it is over the ground ('wallHalf', 'wallRadius',
  'wallOut', 'wallHeight', m: '_terrain.OvalWall'); for walls on a grid
  its first corner (from the origin, 'wallGridAt'), its cells' size
  ('wallCell', m), how many points along x and y ('wallNx', 'wallNy'),
  how far each lies inside a wall ('wallInside', m, below nought out
  of them all) and how tall the wall stands over the ground there
  ('wallTops', m), each a row along y for each x
  ('_gridwall.GridWall')."""
  count: int
  h: float
  passes: int
  gravity: wp.vec3
  floor: float
  grease: float
  seed: int
  motorsMerged: int
  threads: int
  bodies: int
  touches: int
  ways: int
  groups: int
  links: int
  motors: int
  colors: int
  airs: int
  faces: int
  brakes: int
  hinges: int
  lines: int
  turns: int
  gears: int
  racks: int
  pairs: int
  rough: float
  grain: float
  texture: int
  profiling: int
  profile: wp.array(dtype=wp.int64)
  terrain: int
  terrainAt: wp.vec2
  terrainCell: float
  terrainNx: int
  terrainNy: int
  terrainBend: float
  heights: wp.array(dtype=float)
  bends: wp.array(dtype=float)
  wall: int
  wallAt: wp.vec2
  wallHalf: float
  wallRadius: float
  wallOut: float
  wallHeight: float
  wallGridAt: wp.vec2
  wallCell: float
  wallNx: int
  wallNy: int
  wallInside: wp.array(dtype=float)
  wallTops: wp.array(dtype=float)


@wp.struct
class Bodies:
  """The bodies: where each is (its centre, from the origin: its place
  and its shift), how it is turned (from its principal axes), how fast
  it moves and spins; its shift and turn at the step's start; how
  easily it gives (one over its mass, nought for a body of the world)
  and turns (one over each principal moment); a ball's radius (else
  nought); its pieces; how far its shape reaches from its centre; a
  turned solid's turn from its principal axes to its own frame, its
  centre there, its profile's pieces and their bounds (least and most
  from the axis, lowest and highest along it); a roller's radius and
  half its length (else noughts); the motor whose rotor it
  is (below nought: none); how many links hold it; how far it has
  turned in the step (a turn's axis times its angle, in the world);
  which way what holds it still pushes it, and by how many touches, in
  the pass and the last ('backing', 'backs'; 'backed', 'backsLast':
  the ground or a body of the world), and how
  much push it passed on to them, in the pass and the last ('carried',
  'carriedLast'); and, in a pass, how
  many rules press it (its mass split among them), how many touches
  have pushed it in the step, and what they move and turn it by, all
  told."""
  place: wp.array(dtype=wp.vec3)
  shift: wp.array(dtype=wp.vec3)
  turn: wp.array(dtype=wp.quat)
  velocity: wp.array(dtype=wp.vec3)
  spin: wp.array(dtype=wp.vec3)
  shiftBefore: wp.array(dtype=wp.vec3)
  turnBefore: wp.array(dtype=wp.quat)
  give: wp.array(dtype=float)
  turnGive: wp.array(dtype=wp.vec3)
  radius: wp.array(dtype=float)
  pieceFirst: wp.array(dtype=int)
  pieceCount: wp.array(dtype=int)
  gridFirst: wp.array(dtype=int)
  gridLow: wp.array(dtype=wp.vec3)
  gridDims: wp.array(dtype=wp.vec3i)
  gridCell: wp.array(dtype=float)
  reach: wp.array(dtype=float)
  boxLow: wp.array(dtype=wp.vec3)
  boxHigh: wp.array(dtype=wp.vec3)
  axes: wp.array(dtype=wp.quat)
  centre: wp.array(dtype=wp.vec3)
  profileFirst: wp.array(dtype=int)
  profileCount: wp.array(dtype=int)
  bounds: wp.array(dtype=wp.vec4)
  roller: wp.array(dtype=wp.vec2)
  rotorOf: wp.array(dtype=int)
  linkCount: wp.array(dtype=int)
  dampCount: wp.array(dtype=int)
  settled: wp.array(dtype=int)
  twist: wp.array(dtype=wp.vec3)
  backing: wp.array(dtype=wp.vec3)
  backed: wp.array(dtype=wp.vec3)
  backs: wp.array(dtype=int)
  backsLast: wp.array(dtype=int)
  carried: wp.array(dtype=float)
  carriedLast: wp.array(dtype=float)
  moved: wp.array(dtype=wp.vec3)
  turned: wp.array(dtype=wp.vec3)
  asked: wp.array(dtype=int)


@wp.struct
class Shapes:
  """The shapes, along their bodies' principal axes: the skin points
  touches press with; each convex piece's planes, triangles, the box
  about it and whether it is that box; each plane's outward normal, how
  far along it it lies and its piece; each triangle's corners, three in
  a row; each turned profile's piece: a line ('LINE': from rho, w to
  rho, w) or an arc (its centre's rho and w, its radius; from angle,
  to angle); the humps bolted across turned solids' faces, each its
  body (below nought: none), its middle's angle round the axis (rad, in
  the body's own frame), its length across (m) and height (m), and how
  far from the axis it runs (from, to, m); the grids' cells over bodies
  of many pieces (a track of planks: 'cellOf'), each its first place
  in 'cellPieces' and how many pieces it lists there."""
  arm: wp.array(dtype=wp.vec3)
  planeFirst: wp.array(dtype=int)
  planeCount: wp.array(dtype=int)
  triangleFirst: wp.array(dtype=int)
  triangleCount: wp.array(dtype=int)
  low: wp.array(dtype=wp.vec3)
  high: wp.array(dtype=wp.vec3)
  box: wp.array(dtype=int)
  facing: wp.array(dtype=wp.vec3)
  offset: wp.array(dtype=float)
  planePiece: wp.array(dtype=int)
  corner: wp.array(dtype=wp.vec3)
  profileKind: wp.array(dtype=int)
  profileA: wp.array(dtype=wp.vec4)
  profileB: wp.array(dtype=wp.vec4)
  hump: wp.array(dtype=wp.vec4)
  humpSpan: wp.array(dtype=wp.vec2)
  cellFirst: wp.array(dtype=int)
  cellCount: wp.array(dtype=int)
  cellPieces: wp.array(dtype=int)


@wp.struct
class Touches:
  """The touches: what each is ('POINT_GROUND' ...), the body pushed
  out ('first'), the one it presses ('second', below nought for the
  ground), its skin point (below nought for a ball), the turned solid's
  profile piece it meets (a skin point on a land; else below nought),
  its grip; as last
  found, the normal pushing the first out (in the world), the points
  that touch (each along its own body's principal axes from its centre;
  the ground's in the world), how deep; how hard it pushed in the step
  so far, N s, and how much of its grip it used in it so far ('gripped',
  holding and slowing alike: no more than its grip times its push, as
  Coulomb has it; found 2026-11-15: held back by its push's grip and then
  slowed by as much again, a box on the ground's four corners held still
  to twice its grip, 0.5 holding on 40 degrees); and the face it pushes a skin point out through, kept
  while the point stays in ('faceFor'; below nought: none yet); a
  wheel's tyre's ('WHEEL_GROUND') radius, the middle of its tread's
  circle and its axle (along the wheel's principal axes), or a probe's
  radius ('PROBE_TURNED'); and how soft the touch is (m/N: a spring;
  nought: rigid) and its damping (N s/m); a tyre's on the ground, how
  far ahead its push acts (rolling resistance's arm, m: its coefficient
  times its radius) and how hard its patch holds against pivoting (its
  arm, m), nought where none; and all it gave its first body since the
  call began ('impulse', N s, in the world: pushes and grip, for a
  tyre's load and pull to be read); a tyre's tread's stretch in its
  patch ('stretch', m, in the world: kept from step to step, call to
  call: 'tyreGrip') and its twist on the road ('twist', rad);
  whether it is looked for ('near': one whose bodies, or point and the
  ground, are too far apart to meet soon is not, 'nearTouch'); those
  looked for, gathered ('nearList', how many: 'nearCount'); the
  touches looked for together ('nearWay'): in groups, each group's
  first touch ('groupFirst'), how many side by side ('groupCount'),
  whether it was looked for last ('groupNear') and the ball about its
  skin points ('groupMiddle', along the first body's principal axes
  from its centre; 'groupReach'); the groups in ways (one body's skin
  points against another's pieces, else one touch), each way's first
  group ('wayFirst'), how many ('wayCount') and whether it was looked
  for last ('wayNear'); the groups to be looked through, listed
  ('groupList', how many: 'groupListCount')."""
  kind: wp.array(dtype=int)
  first: wp.array(dtype=int)
  second: wp.array(dtype=int)
  point: wp.array(dtype=int)
  piece: wp.array(dtype=int)
  grip: wp.array(dtype=float)
  normal: wp.array(dtype=wp.vec3)
  firstArm: wp.array(dtype=wp.vec3)
  secondArm: wp.array(dtype=wp.vec3)
  depth: wp.array(dtype=float)
  pushed: wp.array(dtype=float)
  gripped: wp.array(dtype=float)
  face: wp.array(dtype=int)
  reach: wp.array(dtype=float)
  hub: wp.array(dtype=wp.vec3)
  axle: wp.array(dtype=wp.vec3)
  soft: wp.array(dtype=float)
  lag: wp.array(dtype=float)
  roll: wp.array(dtype=wp.vec2)
  impulse: wp.array(dtype=wp.vec3)
  stretch: wp.array(dtype=wp.vec3)
  twist: wp.array(dtype=float)
  near: wp.array(dtype=int)
  nearList: wp.array(dtype=int)
  nearCount: wp.array(dtype=int)
  groupFirst: wp.array(dtype=int)
  groupCount: wp.array(dtype=int)
  groupNear: wp.array(dtype=int)
  groupMiddle: wp.array(dtype=wp.vec3)
  groupReach: wp.array(dtype=float)
  wayFirst: wp.array(dtype=int)
  wayCount: wp.array(dtype=int)
  wayNear: wp.array(dtype=int)
  groupList: wp.array(dtype=int)
  groupListCount: wp.array(dtype=int)


@wp.struct
class Links:
  """The ties and rods: what each is ('TIE', 'ROD'), its bodies (below
  nought: the world), its points (each along its body's principal axes
  from its centre; the world's from the origin), a rod's length."""
  kind: wp.array(dtype=int)
  first: wp.array(dtype=int)
  second: wp.array(dtype=int)
  firstArm: wp.array(dtype=wp.vec3)
  secondArm: wp.array(dtype=wp.vec3)
  length: wp.array(dtype=float)


@wp.struct
class Motors:
  """The motors: each its rotor, its housing (below nought: the world),
  its axis along the rotor's principal axes, and its drive as set for
  the call: how hard it twists standing, N m, how much less per rad/s
  of the rotor's turning on the housing, and the most either way."""
  rotor: wp.array(dtype=int)
  housing: wp.array(dtype=int)
  along: wp.array(dtype=wp.vec3)
  torque: wp.array(dtype=float)
  damping: wp.array(dtype=float)
  most: wp.array(dtype=float)


@wp.struct
class Chains:
  """The cord lines ('CordLine'), each held whole at once by a thread of
  its own ('holdChain'): for each line its first slot, how many points
  it has, whether it is a ring; the lines in order of their colour
  (lines of a colour share no point but at their ends: they are held
  side by side) and each colour's first place and count in that order;
  for each slot (a point of a line), its body and its point (along the
  body's principal axes from its centre), how many slots of its colour
  share that body (its mass split among them), and the piece of cord
  from it to the next point: how long unstretched, how soft (m/N); and
  each slot's working: the piece's way now and at the step's start, how
  far past its length it is, whether it pulls, its row of the line's
  equations (the pull of the piece before, its own, the piece after;
  what it must undo), the
  elimination's working, the pull found and a second solve's working
  (a ring's)."""
  first: wp.array(dtype=int)
  count: wp.array(dtype=int)
  closed: wp.array(dtype=int)
  order: wp.array(dtype=int)
  colorFirst: wp.array(dtype=int)
  colorCount: wp.array(dtype=int)
  body: wp.array(dtype=int)
  arm: wp.array(dtype=wp.vec3)
  split: wp.array(dtype=float)
  rest: wp.array(dtype=float)
  soft: wp.array(dtype=float)
  way: wp.array(dtype=wp.vec3)
  start: wp.array(dtype=wp.vec3)
  miss: wp.array(dtype=float)
  active: wp.array(dtype=int)
  lo: wp.array(dtype=float)
  mid: wp.array(dtype=float)
  hi: wp.array(dtype=float)
  rhs: wp.array(dtype=float)
  cp: wp.array(dtype=float)
  dp: wp.array(dtype=float)
  pull: wp.array(dtype=float)
  aux: wp.array(dtype=float)


@wp.struct
class Hinges:
  """The hinges ('Hinge'): each its bodies (below nought: the world),
  its pin's point and line on each (along the body's principal axes
  from its centre; the world's from the origin, its line as is), a
  line square to the pin on each, as they lay when built (its twist's
  nought), how easily its rubber gives across the pin, along it,
  tilting it and twisting about it ('give': m/N, m/N, rad/(N m),
  rad/(N m); nought: rigid; below nought, of the twist: free) and how
  long its rubber's push lags ('lag', s: its damping over its
  stiffness)."""
  first: wp.array(dtype=int)
  second: wp.array(dtype=int)
  firstArm: wp.array(dtype=wp.vec3)
  secondArm: wp.array(dtype=wp.vec3)
  firstAxis: wp.array(dtype=wp.vec3)
  secondAxis: wp.array(dtype=wp.vec3)
  firstRef: wp.array(dtype=wp.vec3)
  secondRef: wp.array(dtype=wp.vec3)
  give: wp.array(dtype=wp.vec4)
  lag: wp.array(dtype=float)


@wp.struct
class Lines:
  """The springs and dampers ('Spring', 'Damper'): each its bodies
  (below nought: the world), its points (along each body's principal
  axes from its centre; the world's from the origin), its stiffness
  (N/m; nought: a damper's, it holds no length), its rest length (m;
  nought: it pulls its points together), whether it pulls and pushes
  (a buffer only pushes, a strap only pulls), and its damping while it
  shortens ('bump') and lengthens ('rebound'), N s/m; a ram's push
  ('Ram': its points apart, N, set each call; nought for the rest)."""
  first: wp.array(dtype=int)
  second: wp.array(dtype=int)
  firstArm: wp.array(dtype=wp.vec3)
  secondArm: wp.array(dtype=wp.vec3)
  stiffness: wp.array(dtype=float)
  rest: wp.array(dtype=float)
  pulls: wp.array(dtype=int)
  pushes: wp.array(dtype=int)
  bump: wp.array(dtype=float)
  rebound: wp.array(dtype=float)
  push: wp.array(dtype=float)


@wp.struct
class Turns:
  """The fourth wall points that turn ('TurnPoint'): each its body and
  its holder (below nought: the world), its axis along the body's
  principal axes, how easily the hands give (rad/(N m)), their damping
  (N m s/rad) and their most (N m), the angle the player asks for the
  call ('target', rad) and how fast the asking moves ('rate', rad/s:
  what the hands damp is the body's turning less that), and how far
  the body has turned on its holder about the axis since built
  ('angle', rad, counted step by step: a steering wheel turns past half
  a turn)."""
  body: wp.array(dtype=int)
  holder: wp.array(dtype=int)
  axis: wp.array(dtype=wp.vec3)
  give: wp.array(dtype=float)
  damping: wp.array(dtype=float)
  most: wp.array(dtype=float)
  target: wp.array(dtype=float)
  rate: wp.array(dtype=float)
  angle: wp.array(dtype=float)


@wp.struct
class Gears:
  """The racks and pinions ('RackAndPinion') and the gears meshing
  ('GearMesh'): each what it is ('kind': 'RACK' or 'MESH'), its pinion
  (a mesh's first gear), rack (a mesh's second gear) and housing (below
  nought: the world), the pinion's axis along its principal axes, the
  rack's line along the housing's (the world's; a mesh's second gear's
  axis along its principal axes), the pinion's pitch radius (and the
  second gear's, below nought where it turns the same way), where the
  rack lay along its line as built ('start', m, from the housing's
  centre) and how far the pinion has turned on the housing since
  ('angle', rad, counted step by step); a mesh's 'angle' is how far its
  pitch circles have slipped apart since (m, counted step by step: the
  two gears' own turns, counted apart, grew past what float32 keeps,
  hundreds of radians on the bench in a minute, and their difference
  lost a micrometre a step, the carrier ringing 3 % in reverse)."""
  kind: wp.array(dtype=int)
  pinion: wp.array(dtype=int)
  rack: wp.array(dtype=int)
  housing: wp.array(dtype=int)
  pinionAxis: wp.array(dtype=wp.vec3)
  rackAxis: wp.array(dtype=wp.vec3)
  radius: wp.array(dtype=float)
  secondRadius: wp.array(dtype=float)
  start: wp.array(dtype=float)
  angle: wp.array(dtype=float)


@wp.struct
class Brakes:
  """The disc brakes ('DiscBrake'): each its disc's body and its
  caliper's (below nought: the world), the disc's middle and axle along
  its body's principal axes, the pads' middle along the caliper's (the
  world's: from the origin), the disc's swept ring (from, to, m from the
  axle), how hard the pads hold it as set for the call ('force', N:
  both pads' friction at the line's pressure), how many brakes act on
  each of its bodies (their masses split among them), how far the disc
  has turned on the caliper since the pads last gripped it ('held', rad:
  what they still hold it back by) and whether they gripped it in the
  step's last pass ('gripping')."""
  disc: wp.array(dtype=int)
  caliper: wp.array(dtype=int)
  middle: wp.array(dtype=wp.vec3)
  axle: wp.array(dtype=wp.vec3)
  pad: wp.array(dtype=wp.vec3)
  ring: wp.array(dtype=wp.vec2)
  force: wp.array(dtype=float)
  discShare: wp.array(dtype=float)
  caliperShare: wp.array(dtype=float)
  held: wp.array(dtype=float)
  gripping: wp.array(dtype=int)


@wp.struct
class Train:
  """The drivetrain's rules, the gears meshing and then the disc
  brakes, solved together each pass ('trainSolved'): each rule's bodies
  (up to three: a mesh's two gears and its housing, a brake's disc and
  caliper; below nought, none), how its miss grows as each of them
  turns ('jacobian', three a rule: m or rad a rad, in the world) and
  how each turns for its pull ('given': its inverse moment times that),
  its miss as the pass finds it, the most it can hold ('most': a
  brake's pads' friction over the step squared; below nought, a mesh,
  which holds whatever it takes) and whether it holds; every two rules
  sharing a body ('pairs': a rule, the body's place among its three,
  the other rule, its place); the equations, each rule's miss by every
  rule's pull ('matrix'); the rules that hold, gathered ('order'); how
  many, which brake lets go, how many the inverse is for, how many
  solves it has served and whether this one may reuse it ('count'); the
  rules it is for ('kept'), their equations' factor, inverse and scales,
  the pulls found and the working ('work', 'down'); each rule's pull;
  and each body's turn from them, rad, in the world."""
  body: wp.array(dtype=wp.vec3i)
  jacobian: wp.array(dtype=wp.vec3)
  given: wp.array(dtype=wp.vec3)
  miss: wp.array(dtype=float)
  most: wp.array(dtype=float)
  holds: wp.array(dtype=int)
  pairs: wp.array(dtype=wp.vec4i)
  matrix: wp.array(dtype=float)
  order: wp.array(dtype=int)
  count: wp.array(dtype=int)
  kept: wp.array(dtype=int)
  factor: wp.array(dtype=float)
  inverse: wp.array(dtype=float)
  scale: wp.array(dtype=float)
  found: wp.array(dtype=float)
  work: wp.array(dtype=float)
  down: wp.array(dtype=float)
  pull: wp.array(dtype=float)
  turn: wp.array(dtype=wp.vec3)


@wp.struct
class Airs:
  """The airs sealed in ('Air'): each its gas (absolute pressure times
  volume, J), its volume as last summed (m³) and the body its corners
  are reckoned from (for float32's sake: near them); each face its air,
  each corner (three a face) its body and its point (along the body's
  principal axes from its centre)."""
  gas: wp.array(dtype=float)
  volume: wp.array(dtype=float)
  base: wp.array(dtype=int)
  faceAir: wp.array(dtype=int)
  body: wp.array(dtype=int)
  arm: wp.array(dtype=wp.vec3)


@wp.struct
class Crowds:
  """The crowds' balls ('Crowd'), every crowd's in one run: each its
  body, its group, its radius, its crowd; where it is (from the origin)
  and how fast it goes, as found each call ('crowdGather'); for each
  crowd its room among the touches (first slot, how many), how many of
  them the call has taken, its fastest ball's speed and its widest
  ball's radius."""
  ball: wp.array(dtype=int)
  group: wp.array(dtype=int)
  radius: wp.array(dtype=float)
  crowdOf: wp.array(dtype=int)
  points: wp.array(dtype=wp.vec3)
  speed: wp.array(dtype=float)
  start: wp.array(dtype=int)
  room: wp.array(dtype=int)
  taken: wp.array(dtype=int)
  fastest: wp.array(dtype=float)
  widest: wp.array(dtype=float)


@wp.func_native("""
#if defined(__CUDA_ARCH__)
__syncthreads();
#endif
""")
def barrier():
  """Every thread of the block waits here for the rest (on a GPU; on
  the CPU, one thread running, nothing to wait for)."""
  ...


@wp.func_native("""
#if defined(__CUDA_ARCH__)
__syncwarp();
#endif
""")
def laneBarrier():
  """Every lane of the warp waits here for the rest, what each wrote
  seen by all (on a GPU; on the CPU, one thread running, nothing to
  wait for)."""
  ...


@wp.func_native("""
#if defined(__CUDA_ARCH__)
return clock64();
#else
return (long long)__builtin_readcyclecounter();
#endif
""")
def clockNow() -> wp.int64:
  """The clock's count now, cycles (a GPU's multiprocessor's; on the
  CPU, its own)."""
  ...


@wp.func
def marked(run: Run, tid: int, phase: int, last: wp.int64) -> wp.int64:
  """Counts the cycles since 'last' into 'phase' of the step's profile,
  if the call is profiled ('run.profiling'), on the first thread alone
  (after a barrier: the slowest thread's time); returns the clock now."""
  if run.profiling == 0 or tid != 0:
    return last
  now = clockNow()
  run.profile[phase] = run.profile[phase] + (now - last)
  return now


@wp.func
def apartOf(b: Bodies, k: int, o: int) -> wp.vec3:
  """How far body 'k's centre is from body 'o's: their places apart and
  their shifts apart, each nearly exact."""
  return (b.place[k] - b.place[o]) + (b.shift[k] - b.shift[o])


@wp.func
def folded(b: Bodies, k: int):
  """Moves body 'k's place on by its shift, the shift keeping what
  float32 rounds off (Knuth's two-sum, exact)."""
  a = b.place[k]
  d = b.shift[k]
  total = a + d
  back = total - a
  b.place[k] = total
  b.shift[k] = (a - (total - back)) + (d - back)


@wp.func
def giveAlong(b: Bodies, k: int, arm: wp.vec3, way: wp.vec3) -> float:
  """How easily body 'k' gives at 'arm' from its centre (in the world)
  pushed along 'way': one over its mass, and how far its turn moves
  the point; nought for the ground or a body of the world."""
  if k < 0:
    return 0.0
  u = wp.quat_rotate_inv(b.turn[k], wp.cross(arm, way))
  g = b.turnGive[k]
  return b.give[k] + u[0] * u[0] * g[0] + u[1] * u[1] * g[1] + (
    u[2] * u[2] * g[2])


@wp.func
def turnFor(b: Bodies, k: int, arm: wp.vec3, impulse: wp.vec3) -> wp.vec3:
  """How far (or fast) body 'k' turns, in the world, for 'impulse' at
  'arm' from its centre: its inertia's inverse times the twist."""
  u = wp.quat_rotate_inv(b.turn[k], wp.cross(arm, impulse))
  return wp.quat_rotate(b.turn[k], wp.cw_mul(u, b.turnGive[k]))


@wp.func
def note(b: Bodies, k: int):
  """Counts one more rule pressing body 'k' in the pass (the ground
  and a body of the world are not counted: they take nothing)."""
  if k < 0:
    return
  if b.give[k] == 0.0:
    return
  wp.atomic_add(b.asked, k, 1)


@wp.func
def shareGive(b: Bodies, k: int, arm: wp.vec3, way: wp.vec3,
              n: int) -> float:
  """How easily body 'k' gives at 'arm' along 'way' to one of 'n' rules
  pressing it: as its share of its mass and turning, split evenly among
  them ('giveAlong' times 'n')."""
  if k < 0:
    return 0.0
  return giveAlong(b, k, arm, way) * float(wp.max(n, 1))


@wp.func
def splitGive(b: Bodies, k: int, arm: wp.vec3, way: wp.vec3) -> float:
  """'shareGive' among the rules pressing body 'k' in the pass."""
  if k < 0:
    return 0.0
  return shareGive(b, k, arm, way, b.asked[k])


@wp.func
def linkGive(b: Bodies, k: int, arm: wp.vec3, way: wp.vec3) -> float:
  """'shareGive' among the links holding body 'k'."""
  if k < 0:
    return 0.0
  return shareGive(b, k, arm, way, b.linkCount[k])


@wp.func
def settleGive(b: Bodies, k: int, arm: wp.vec3, way: wp.vec3) -> float:
  """'shareGive' among the touches that pushed body 'k' in the step."""
  if k < 0:
    return 0.0
  return shareGive(b, k, arm, way, b.settled[k])


@wp.func
def noteSettled(b: Bodies, k: int):
  """Counts one more touch that pushed body 'k' in the step (not the
  ground's nor a body of the world's)."""
  if k < 0:
    return
  if b.give[k] == 0.0:
    return
  wp.atomic_add(b.settled, k, 1)


@wp.func
def ask(b: Bodies, k: int, arm: wp.vec3, impulse: wp.vec3):
  """Gives body 'k' 'impulse' at 'arm', added to what the pass's other
  rules give it (a body of the world, or the ground, takes nothing)."""
  if k < 0:
    return
  if b.give[k] == 0.0:
    return
  wp.atomic_add(b.moved, k, impulse * b.give[k])
  wp.atomic_add(b.turned, k, turnFor(b, k, arm, impulse))


@wp.func
def moveFreely(run: Run, b: Bodies, k: int, h: float):
  """Notes where body 'k' is and how it is turned, then moves it a step
  under gravity and what the airs gave it ('airPush': its velocity and
  spin changed by them, kept in 'moved' and 'turned' till now), turning
  as it spins (its spin changed by its own turning: Euler's
  equations)."""
  kick = b.moved[k]
  turning = b.turned[k]
  b.shiftBefore[k] = b.shift[k]
  b.turnBefore[k] = b.turn[k]
  b.moved[k] = wp.vec3(0.0, 0.0, 0.0)
  b.turned[k] = wp.vec3(0.0, 0.0, 0.0)
  b.asked[k] = 0
  b.settled[k] = 0
  b.twist[k] = wp.vec3(0.0, 0.0, 0.0)
  if b.give[k] == 0.0:
    return
  v = b.velocity[k] + run.gravity * h + kick
  b.velocity[k] = v
  b.shift[k] = b.shift[k] + v * h
  q = b.turn[k]
  g = b.turnGive[k]
  w = wp.quat_rotate_inv(q, b.spin[k] + turning)
  held = wp.vec3(w[0] / g[0], w[1] / g[1], w[2] / g[2])
  w = w - wp.cw_mul(g, wp.cross(w, held)) * h
  spin = wp.quat_rotate(q, w)
  b.spin[k] = spin
  b.twist[k] = spin * h
  rate = wp.quat(spin[0], spin[1], spin[2], 0.0) * q
  b.turn[k] = wp.normalize(q + rate * (0.5 * h))


@wp.func
def cellOf(b: Bodies, o: int, p: wp.vec3) -> int:
  """The cell of body 'o''s grid holding 'p' (along its principal axes
  from its centre): its pieces are those of 'o' near enough to touch
  anything there ('GRID_MARGIN' of the packer); 'WHOLE' where 'o' has
  no grid (all its pieces), 'OFF_GRID' off it (none near)."""
  g = b.gridFirst[o]
  if g < 0:
    return WHOLE
  rel = (p - b.gridLow[o]) / b.gridCell[o]
  dims = b.gridDims[o]
  i = int(wp.floor(rel[0]))
  j = int(wp.floor(rel[1]))
  k = int(wp.floor(rel[2]))
  if (i < 0 or j < 0 or k < 0 or i >= dims[0] or j >= dims[1]
      or k >= dims[2]):
    return OFF_GRID
  return g + (i * dims[1] + j) * dims[2] + k


@wp.func
def piecesFrom(b: Bodies, s: Shapes, o: int, cell: int) -> int:
  """Where the pieces to look at begin ('pieceOf' takes them): body
  'o''s first, or grid cell 'cell''s first place in its list."""
  if cell >= 0:
    return s.cellFirst[cell]
  return b.pieceFirst[o]


@wp.func
def piecesTo(b: Bodies, s: Shapes, o: int, cell: int) -> int:
  """Where the pieces to look at end (past the last)."""
  if cell >= 0:
    return s.cellFirst[cell] + s.cellCount[cell]
  if cell == OFF_GRID:
    return b.pieceFirst[o]
  return b.pieceFirst[o] + b.pieceCount[o]


@wp.func
def pieceOf(s: Shapes, cell: int, n: int) -> int:
  """The piece at 'n' of those looked at: the cell's list's, or 'n'
  itself (a body without a grid)."""
  if cell >= 0:
    return s.cellPieces[n]
  return n


@wp.func
def onTriangle(p: wp.vec3, a: wp.vec3, bb: wp.vec3, c: wp.vec3) -> wp.vec3:
  """The point of the triangle 'a' 'bb' 'c' nearest 'p' (as Ericson's
  'Real-Time Collision Detection' finds it)."""
  ab = bb - a
  ac = c - a
  ap = p - a
  d1 = wp.dot(ab, ap)
  d2 = wp.dot(ac, ap)
  if d1 <= 0.0 and d2 <= 0.0:
    return a
  bp = p - bb
  d3 = wp.dot(ab, bp)
  d4 = wp.dot(ac, bp)
  if d3 >= 0.0 and d4 <= d3:
    return bb
  vc = d1 * d4 - d3 * d2
  if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
    return a + ab * (d1 / (d1 - d3))
  cp = p - c
  d5 = wp.dot(ab, cp)
  d6 = wp.dot(ac, cp)
  if d6 >= 0.0 and d5 <= d6:
    return c
  vb = d5 * d2 - d1 * d6
  if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
    return a + ac * (d2 / (d2 - d6))
  va = d3 * d6 - d5 * d4
  if va <= 0.0 and d4 - d3 >= 0.0 and d5 - d6 >= 0.0:
    return bb + (c - bb) * ((d4 - d3) / ((d4 - d3) + (d5 - d6)))
  whole = 1.0 / (va + vb + vc)
  return a + ab * (vb * whole) + ac * (vc * whole)


@wp.func
def pastOf(s: Shapes, c: int, p: wp.vec3) -> float:
  """How far inside piece 'c' the point 'p' is from its nearest face
  (below nought: outside, past that far)."""
  under = float(FAR)
  start = s.planeFirst[c]
  for j in range(start, start + s.planeCount[c]):
    under = wp.min(under, s.offset[j] - wp.dot(s.facing[j], p))
  return under


@wp.func
def faceFor(b: Bodies, s: Shapes, o: int, p: wp.vec3, before: wp.vec3,
            toward: wp.vec3, kept: int) -> int:
  """The face (plane) of body 'o' a point at 'p' (along its principal
  axes from its centre) is pushed out through: 'kept', while the point
  is still in its piece (to within 'EDGE'); else, of the piece it is in
  (to within 'EDGE'), the face it went in through (where it was at the
  step's start, 'before': the one it was furthest out past, or least
  in behind), of faces alike to within 'EDGE' the one facing 'toward'
  most (the other body's centre: a block set on one alike, every edge
  point on a side face too, is pushed up, not aside); below nought
  where it is in none."""
  if kept >= 0:
    if pastOf(s, s.planePiece[kept], p) >= -EDGE:
      return kept
  chosen = int(-1)
  deepest = float(0.0)
  cell = cellOf(b, o, p)
  for listed in range(piecesFrom(b, s, o, cell), piecesTo(b, s, o, cell)):
    c = pieceOf(s, cell, listed)
    lo = s.low[c]
    hi = s.high[c]
    if (p[0] < lo[0] - EDGE or p[0] > hi[0] + EDGE or p[1] < lo[1] - EDGE
        or p[1] > hi[1] + EDGE or p[2] < lo[2] - EDGE
        or p[2] > hi[2] + EDGE):
      continue
    if pastOf(s, c, p) < -EDGE:
      continue
    start = s.planeFirst[c]
    least = float(FAR)
    for j in range(start, start + s.planeCount[c]):
      least = wp.min(least, s.offset[j] - wp.dot(s.facing[j], before))
    face = int(-1)
    facing = float(-FAR)
    for j in range(start, start + s.planeCount[c]):
      if s.offset[j] - wp.dot(s.facing[j], before) <= least + EDGE:
        score = wp.dot(s.facing[j], toward)
        if score > facing:
          facing = score
          face = j
    deep = s.offset[face] - wp.dot(s.facing[face], p)
    if chosen < 0 or deep > deepest:
      chosen = face
      deepest = deep
  return chosen


@wp.func
def ballOnPieces(b: Bodies, s: Shapes, o: int, p: wp.vec3,
                 r: float) -> wp.vec4:
  """How deep a ball of radius 'r' at 'p' (along body 'o's principal
  axes from its centre) presses the piece of 'o' it presses deepest,
  and the normal pushing it out (out of 'o'), as (depth, x, y, z): its
  middle inside a piece, out through the face it is least deep behind;
  outside, away from the piece's nearest point (a box's by clamping,
  else the nearest of its triangles' points)."""
  best = float(0.0)
  facing = wp.vec3(0.0, 0.0, 1.0)
  cell = cellOf(b, o, p)
  for listed in range(piecesFrom(b, s, o, cell), piecesTo(b, s, o, cell)):
    c = pieceOf(s, cell, listed)
    lo = s.low[c]
    hi = s.high[c]
    if (p[0] < lo[0] - r or p[0] > hi[0] + r or p[1] < lo[1] - r
        or p[1] > hi[1] + r or p[2] < lo[2] - r or p[2] > hi[2] + r):
      continue
    under = float(FAR)
    way = wp.vec3(0.0, 0.0, 1.0)
    start = s.planeFirst[c]
    for j in range(start, start + s.planeCount[c]):
      d = s.offset[j] - wp.dot(s.facing[j], p)
      if d < under:
        under = d
        way = s.facing[j]
    deep = float(0.0)
    normal = way
    if under >= 0.0:
      deep = r + under
    else:
      q = p
      if s.box[c] != 0:
        q = wp.vec3(wp.clamp(p[0], lo[0], hi[0]),
                    wp.clamp(p[1], lo[1], hi[1]),
                    wp.clamp(p[2], lo[2], hi[2]))
      else:
        nearest = float(FAR)
        t0 = s.triangleFirst[c]
        for t in range(t0, t0 + s.triangleCount[c]):
          on = onTriangle(p, s.corner[3 * t], s.corner[3 * t + 1],
                          s.corner[3 * t + 2])
          far = wp.length_sq(p - on)
          if far < nearest:
            nearest = far
            q = on
      off = p - q
      apart = wp.length(off)
      if apart < r and apart > 0.0:
        deep = r - apart
        normal = off / apart
    if deep > best:
      best = deep
      facing = normal
  return wp.vec4(best, facing[0], facing[1], facing[2])


@wp.func
def wheelOnPieces(b: Bodies, s: Shapes, o: int, hub: wp.vec3,
                  axle: wp.vec3, r: float) -> wp.vec4:
  """How deep a tyre's tread circle (its middle 'hub', its axle 'axle',
  its radius 'r', along body 'o''s principal axes from its centre)
  presses the piece of 'o' it presses deepest, and the way from its
  middle to where it touches (in its wheel's plane: its spring's), as
  (depth, x, y, z), as it would press the ground were that face's plane
  the ground ('WHEEL_GROUND': as deep as the circle reaches past the
  plane along the way toward it in its plane), of each piece the face it
  presses least (separating axes over the faces: a circle clear of any
  face's plane is clear of the piece; a plank's top, not its end, under
  a tyre rolling on it), where it touches on that face (not past its
  edges, to within 'WHEEL_EDGE': a plank's top, not its plane past its
  end; planks laid edge to edge, the touch at the join on both),
  its middle outside that face's plane (a plank's bottom, its middle
  behind it, never: where the top's touch fell just past the plank's end
  by float32's rounding and the bottom's just inside, the bottom pressed
  0.68 m deep and pulled the tyre through); faces square to the tyre's
  plane (within 'FLAT') press none (a plank's sides: its sidewall's)."""
  best = float(0.0)
  facing = wp.vec3(0.0, 0.0, -1.0)
  cell = cellOf(b, o, hub)
  for listed in range(piecesFrom(b, s, o, cell), piecesTo(b, s, o, cell)):
    c = pieceOf(s, cell, listed)
    lo = s.low[c]
    hi = s.high[c]
    if (hub[0] < lo[0] - r or hub[0] > hi[0] + r or hub[1] < lo[1] - r
        or hub[1] > hi[1] + r or hub[2] < lo[2] - r
        or hub[2] > hi[2] + r):
      continue
    start = s.planeFirst[c]
    count = s.planeCount[c]
    least = float(FAR)
    way = wp.vec3(0.0, 0.0, -1.0)
    clear = int(0)
    for j in range(start, start + count):
      n = s.facing[j]
      down = -n + axle * wp.dot(axle, n)
      size = wp.length(down)
      out = wp.dot(n, hub) - s.offset[j]
      if out >= r * size:
        clear = 1
      elif size > FLAT and out > 0.0:
        toward = down / size
        reach = out / size
        on = hub + toward * reach
        inside = int(1)
        for m in range(start, start + count):
          if m != j and (s.offset[m] - wp.dot(s.facing[m], on)
                         < -WHEEL_EDGE):
            inside = 0
        deep = r - reach
        if inside != 0 and deep < least:
          least = deep
          way = toward
    if clear == 0 and least < FAR and least > best:
      best = least
      facing = way
  return wp.vec4(best, facing[0], facing[1], facing[2])


@wp.func
def nearestOnProfile(s: Shapes, j: int, rho: float, w: float) -> wp.vec4:
  """The point of a turned profile's piece 'j' nearest ('rho', 'w'),
  and the piece's outward normal there (to the right as it is walked:
  away from the solid), as (rho, w, along rho, along w)."""
  a = s.profileA[j]
  if s.profileKind[j] == LINE:
    dr = a[2] - a[0]
    dw = a[3] - a[1]
    square = dr * dr + dw * dw
    share = wp.clamp(((rho - a[0]) * dr + (w - a[1]) * dw) / square, 0.0,
                     1.0)
    length = wp.sqrt(square)
    return wp.vec4(a[0] + share * dr, a[1] + share * dw, dw / length,
                   -dr / length)
  ends = s.profileB[j]
  a0 = ends[0]
  a1 = ends[1]
  low = wp.min(a0, a1)
  high = wp.max(a0, a1)
  angle = wp.atan2(w - a[1], rho - a[0])
  angle = angle - wp.floor((angle - low) / TWO_PI) * TWO_PI
  if angle > high:
    r0 = a[0] + a[2] * wp.cos(a0) - rho
    w0 = a[1] + a[2] * wp.sin(a0) - w
    r1 = a[0] + a[2] * wp.cos(a1) - rho
    w1 = a[1] + a[2] * wp.sin(a1) - w
    if r0 * r0 + w0 * w0 <= r1 * r1 + w1 * w1:
      angle = a0
    else:
      angle = a1
  c = wp.cos(angle)
  sn = wp.sin(angle)
  way = float(1.0)
  if a1 < a0:
    way = -1.0
  return wp.vec4(a[0] + a[2] * c, a[1] + a[2] * sn, way * c, way * sn)


@wp.func
def ballOnProfile(b: Bodies, s: Shapes, o: int, j: int, apart: wp.vec3,
                  r: float) -> wp.vec4:
  """How deep a ball of radius 'r', 'apart' from the turned solid 'o's
  centre (in the world), presses piece 'j' of its profile, and the
  normal pushing it out (in the world), as (depth, x, y, z): pressed
  where its middle lies in front of the piece (away from the solid)
  nearer than its radius, out from the piece's nearest point."""
  qo = b.turn[o]
  own = wp.quat_rotate(b.axes[o], wp.quat_rotate_inv(qo, apart)) + (
    b.centre[o])
  rho = wp.sqrt(own[0] * own[0] + own[1] * own[1])
  w = own[2]
  edges = b.bounds[o]
  none = wp.vec4(0.0, 0.0, 0.0, 1.0)
  if (rho < edges[0] - r or rho > edges[1] + r or w < edges[2] - r
      or w > edges[3] + r):
    return none
  ux = float(1.0)
  uy = float(0.0)
  if rho > 0.0:
    ux = own[0] / rho
    uy = own[1] / rho
  q = nearestOnProfile(s, j, rho, w)
  dr = rho - q[0]
  dw = w - q[1]
  if dr * q[2] + dw * q[3] < 0.0:
    return none
  far = dr * dr + dw * dw
  if far >= r * r:
    return none
  apartOwn = wp.sqrt(far)
  nr = q[2]
  nw = q[3]
  deep = r
  if apartOwn > 0.0:
    nr = dr / apartOwn
    nw = dw / apartOwn
    deep = r - apartOwn
  normal = wp.quat_rotate(qo, wp.quat_rotate_inv(
    b.axes[o], wp.vec3(nr * ux, nr * uy, nw)))
  return wp.vec4(deep, normal[0], normal[1], normal[2])


@wp.func
def toOwn(b: Bodies, o: int, v: wp.vec3) -> wp.vec3:
  """The world's 'v' along body 'o's own frame's axes."""
  return wp.quat_rotate(b.axes[o], wp.quat_rotate_inv(b.turn[o], v))


@wp.func
def fromOwn(b: Bodies, o: int, v: wp.vec3) -> wp.vec3:
  """'v', along body 'o's own frame's axes, in the world."""
  return wp.quat_rotate(b.turn[o], wp.quat_rotate_inv(b.axes[o], v))


@wp.func
def axisOf(b: Bodies, k: int) -> wp.vec3:
  """Body 'k's own z in the world (a roller's axis)."""
  return fromOwn(b, k, wp.vec3(0.0, 0.0, 1.0))


@wp.func
def rollerPoint(b: Bodies, s: Shapes, k: int, o: int, code: int,
                apart: wp.vec3) -> wp.vec4:
  """The point of roller 'k' ('apart' from the turned solid 'o's centre,
  in the world) that meets the line piece of 'o's profile 'code' // 2,
  along 'o's own axes from its axis, its fourth number one; nought
  where it meets none (its middle not in front of the piece: a face
  turned away from it); against a piece along the axis (a raceway), the
  roller's line nearest it at one of two points (code % 2) 'ROLLER_REACH'
  of the way out to either end; against a piece across the axis (a
  rib's face), the roller's end facing it, at one of two points over
  the middle of where they overlap, 'ROLLER_REACH' of the way out to
  either side across it (so the rib holds the roller from skewing:
  two points along the radius held it not)."""
  j = code // 2
  e = code - 2 * j
  own = toOwn(b, o, apart) + b.centre[o]
  u = toOwn(b, o, axisOf(b, k))
  size = b.roller[k]
  r = size[0]
  half = size[1]
  a = s.profileA[j]
  dr = a[2] - a[0]
  dw = a[3] - a[1]
  length = wp.sqrt(dr * dr + dw * dw)
  nr = dw / length
  nw = -dr / length
  rho = wp.sqrt(own[0] * own[0] + own[1] * own[1])
  none = wp.vec4(0.0, 0.0, 0.0, 0.0)
  if rho <= 0.0:
    return none
  if (rho - a[0]) * nr + (own[2] - a[1]) * nw <= 0.0:
    return none
  out = wp.vec3(own[0] / rho, own[1] / rho, 0.0)
  into = -(out * nr + wp.vec3(0.0, 0.0, nw))
  p = own
  if wp.abs(dw) >= wp.abs(dr):
    side = into - u * wp.dot(into, u)
    sideLength = wp.length(side)
    if sideLength <= 0.0:
      return none
    along = (2.0 * float(e) - 1.0) * ROLLER_REACH * half
    p = own + u * along + side * (r / sideLength)
  else:
    facing = wp.dot(into, u)
    if facing == 0.0:
      return none
    end = own + u * (wp.sign(facing) * half)
    radial = out - u * wp.dot(out, u)
    radialLength = wp.length(radial)
    if radialLength <= 0.0:
      return none
    radial = radial / radialLength
    low = wp.max(wp.min(a[0], a[2]) - rho, -r)
    high = wp.min(wp.max(a[0], a[2]) - rho, r)
    if low >= high:
      return none
    middle = 0.5 * (low + high)
    across = wp.cross(u, radial)
    chord = wp.sqrt(wp.max(r * r - middle * middle, 0.0))
    p = end + radial * middle + across * ((2.0 * float(e) - 1.0)
                                          * ROLLER_REACH * chord)
  return wp.vec4(p[0], p[1], p[2], 1.0)


@wp.func
def pointOnLine(s: Shapes, j: int, p: wp.vec3) -> wp.vec4:
  """How deep the point 'p' (along a turned solid's own axes from its
  axis) is behind the line piece 'j' of its profile, and the piece's
  outward normal there (along the same axes), as (depth, x, y, z);
  nought deep where it lies beside the piece."""
  a = s.profileA[j]
  dr = a[2] - a[0]
  dw = a[3] - a[1]
  square = dr * dr + dw * dw
  rho = wp.sqrt(p[0] * p[0] + p[1] * p[1])
  none = wp.vec4(0.0, 0.0, 0.0, 1.0)
  if rho <= 0.0 or square <= 0.0:
    return none
  share = ((rho - a[0]) * dr + (p[2] - a[1]) * dw) / square
  if share < 0.0 or share > 1.0:
    return none
  length = wp.sqrt(square)
  nr = dw / length
  nw = -dr / length
  depth = -((rho - a[0]) * nr + (p[2] - a[1]) * nw)
  return wp.vec4(depth, p[0] / rho * nr, p[1] / rho * nr, nw)


@wp.func
def humpAt(s: Shapes, o: int, own: wp.vec3) -> wp.vec2:
  """How high the humps bolted across body 'o''s face stand at 'own' (a
  point in its own frame), m, and how steeply they rise there going
  anticlockwise round its axis, m a m: each a bar laid straight out
  from the axis at its angle, over its span, as high as its height
  times the square of the cosine of how far across it the point is (a
  half turn over its length: smooth, nought at its edges)."""
  rho = wp.sqrt(own[0] * own[0] + own[1] * own[1])
  height = float(0.0)
  slope = float(0.0)
  if rho <= 0.0:
    return wp.vec2(0.0, 0.0)
  theta = wp.atan2(own[1], own[0])
  for j in range(s.hump.shape[0]):
    hump = s.hump[j]
    span = s.humpSpan[j]
    if int(hump[0]) == o and hump[3] != 0.0 and rho >= span[0] and (
        rho <= span[1]):
      off = theta - hump[1]
      off = off - wp.floor((off + 0.5 * TWO_PI) / TWO_PI) * TWO_PI
      across = rho * wp.sin(off)
      if wp.cos(off) > 0.0 and wp.abs(across) < 0.5 * hump[2]:
        phase = 0.5 * TWO_PI * across / hump[2]
        c = wp.cos(phase)
        height = height + hump[3] * c * c
        slope = slope - hump[3] * (0.5 * TWO_PI / hump[2]) * wp.sin(
          2.0 * phase) * wp.cos(off)
  return wp.vec2(height, slope)


@wp.func
def onFace(s: Shapes, o: int, j: int, own: wp.vec3) -> wp.vec4:
  """How far 'own' (a point in body 'o''s own frame) stands out of the
  flat face across the axis that is piece 'j' of its profile, over the
  humps bolted to it ('humpAt'), m, along the face's outward normal
  there (in its own frame: tilted where a hump rises), as (how far, x,
  y, z); 'FAR' off the face (nearer the axis or farther than its
  edges) or on a piece of another kind."""
  a = s.profileA[j]
  up = float(1.0)
  if a[2] > a[0]:
    up = -1.0
  rho = wp.sqrt(own[0] * own[0] + own[1] * own[1])
  if (s.profileKind[j] != LINE or a[1] != a[3] or rho <= 0.0
      or rho < wp.min(a[0], a[2]) or rho > wp.max(a[0], a[2])):
    return wp.vec4(FAR, 0.0, 0.0, up)
  bump = humpAt(s, o, own)
  tangent = wp.vec3(-own[1] / rho, own[0] / rho, 0.0)
  rise = wp.normalize(wp.vec3(0.0, 0.0, up) - tangent * bump[1])
  over = rise[2] * (own[2] - a[1] - up * bump[0])
  return wp.vec4(over, rise[0], rise[1], rise[2])


@wp.func
def groundAt(run: Run, x: float, y: float) -> wp.vec4:
  """How high the ground is under 'x', 'y' (from the origin, m) and
  its upward unit normal there, as (height, x, y, z): the floor, level,
  but on a terrain ('run.terrain') its grid's cell's bilinear surface
  (as '_terrain.Terrain.heightAt' and 'normalAt'; the floor, level, off
  the grid)."""
  if run.terrain == 0:
    return wp.vec4(run.floor, 0.0, 0.0, 1.0)
  cell = run.terrainCell
  a = (x - run.terrainAt[0]) / cell
  c = (y - run.terrainAt[1]) / cell
  i = int(wp.floor(a))
  j = int(wp.floor(c))
  if i < 0 or j < 0 or i >= run.terrainNx - 1 or j >= run.terrainNy - 1:
    return wp.vec4(run.floor, 0.0, 0.0, 1.0)
  u = a - float(i)
  v = c - float(j)
  n = run.terrainNy
  h00 = run.heights[i * n + j]
  h10 = run.heights[(i + 1) * n + j]
  h01 = run.heights[i * n + j + 1]
  h11 = run.heights[(i + 1) * n + j + 1]
  height = (h00 * (1.0 - u) + h10 * u) * (1.0 - v) + (
    h01 * (1.0 - u) + h11 * u) * v
  along = ((h10 - h00) * (1.0 - v) + (h11 - h01) * v) / cell
  across = ((h01 - h00) * (1.0 - u) + (h11 - h10) * u) / cell
  size = wp.sqrt(along * along + across * across + 1.0)
  return wp.vec4(height, -along / size, -across / size, 1.0 / size)


@wp.func
def bendAt(run: Run, x: float, y: float) -> float:
  """How much the ground's slope changes at most within the terrain's
  cell under 'x', 'y' and into the cells about it ('run.bends'; the most
  of all off the grid; nought without a terrain)."""
  if run.terrain == 0:
    return 0.0
  i = int(wp.floor((x - run.terrainAt[0]) / run.terrainCell))
  j = int(wp.floor((y - run.terrainAt[1]) / run.terrainCell))
  if i < 0 or j < 0 or i >= run.terrainNx - 1 or j >= run.terrainNy - 1:
    return run.terrainBend
  return run.bends[i * (run.terrainNy - 1) + j]


@wp.func
def gridBeyond(run: Run, x: float, y: float) -> wp.vec3:
  """How far 'x', 'y' (from the origin) is through a face of the walls
  on a grid, m (below nought: out of them all), and the face's outward
  normal there, level (x, y: the way deeper in), as '_gridwall.
  GridWall.beyond' (off the grid open, 'GRID_WALL_REACH' from any)."""
  fx = (x - run.wallGridAt[0]) / run.wallCell
  fy = (y - run.wallGridAt[1]) / run.wallCell
  i = int(wp.floor(fx))
  j = int(wp.floor(fy))
  if i < 0 or j < 0 or i >= run.wallNx - 1 or j >= run.wallNy - 1:
    return wp.vec3(-GRID_WALL_REACH, 1.0, 0.0)
  u = fx - float(i)
  v = fy - float(j)
  k = i * run.wallNy + j
  a = run.wallInside[k]
  b = run.wallInside[k + run.wallNy]
  c = run.wallInside[k + 1]
  d = run.wallInside[k + run.wallNy + 1]
  depth = (a * (1.0 - u) + b * u) * (1.0 - v) + (c * (1.0 - u) + d * u) * v
  gx = (b - a) * (1.0 - v) + (d - c) * v
  gy = (c - a) * (1.0 - u) + (d - b) * u
  size = wp.sqrt(gx * gx + gy * gy)
  if size < 1e-12:
    return wp.vec3(depth, 1.0, 0.0)
  return wp.vec3(depth, gx / size, gy / size)


@wp.func
def wallTop(run: Run, x: float, y: float) -> float:
  """How tall the wall at 'x', 'y' (from the origin) stands over the
  ground, m: the oval's barrier's height; on a grid its cell's tallest
  corner (off the grid nought)."""
  if run.wall != 2:
    return run.wallHeight
  i = int(wp.floor((x - run.wallGridAt[0]) / run.wallCell))
  j = int(wp.floor((y - run.wallGridAt[1]) / run.wallCell))
  if i < 0 or j < 0 or i >= run.wallNx - 1 or j >= run.wallNy - 1:
    return 0.0
  k = i * run.wallNy + j
  return wp.max(wp.max(run.wallTops[k], run.wallTops[k + 1]),
                wp.max(run.wallTops[k + run.wallNy],
                       run.wallTops[k + run.wallNy + 1]))


@wp.func
def wallBeyond(run: Run, x: float, y: float) -> wp.vec3:
  """How far 'x', 'y' (from the origin) is out through the wall's face,
  m (below nought: inside it, out in the open), and the face's outward
  normal there, level (x, y): a town's on a grid ('gridBeyond'), or
  the oval's barrier's, as '_terrain.OvalWall.beyond'."""
  if run.wall == 2:
    return gridBeyond(run, x, y)
  px = x - run.wallAt[0]
  py = y - run.wallAt[1]
  half = run.wallHalf
  radius = run.wallRadius
  if px > half or px < -half:
    middle = half
    if px < -half:
      middle = -half
    dx = px - middle
    dy = py - radius
    far = wp.sqrt(dx * dx + dy * dy)
    if far < 1e-9:
      return wp.vec3(-radius - run.wallOut, 1.0, 0.0)
    return wp.vec3(far - radius - run.wallOut, dx / far, dy / far)
  if py < radius:
    return wp.vec3(-py - run.wallOut, 0.0, -1.0)
  return wp.vec3(py - 2.0 * radius - run.wallOut, 0.0, 1.0)


@wp.func
def wallReach(b: Bodies, s: Shapes, t: Touches, i: int, k: int) -> float:
  """How far touch 'i' (a wall's: 'POINT_WALL', 'PROBE_WALL',
  'BALL_WALL') reaches out from its point on body 'k': nought, a probe's
  radius, the ball's."""
  kind = t.kind[i]
  if kind == PROBE_WALL:
    return t.reach[i]
  if kind == BALL_WALL:
    return b.radius[k]
  return 0.0


@wp.func
def found(run: Run, b: Bodies, s: Shapes, t: Touches, i: int,
          seed: int, draw: int) -> int:
  """Finds touch 'i' as the bodies are now: its normal, the points that
  touch (each from its own body's centre), how deep (the ground
  'run.floor' high, or a terrain's, 'groundAt': its normal the
  ground's under the point, the ball's middle, the probe, the hub, how
  deep along it as the plane there has it); a skin point looked for in another body shaken by
  up to 'run.grease' each way, at random ('seed' the step's number,
  'draw' its draws' place among the step's:
  a point on an edge of a face it lies on, as a block's on one alike
  under it, is in the other body as often as not, not never; a ball's
  middle looked for in a turned solid likewise, its depth alone taking
  the shake, where it touches as it is: shaken where it touched too,
  the grip took the shake for sliding and the hub's balls skidded);
  returns whether it presses."""
  kind = t.kind[i]
  k = t.first[i]
  o = t.second[i]
  qk = b.turn[k]
  up = wp.vec3(0.0, 0.0, 1.0)
  depth = float(0.0)
  normal = up
  arm = wp.vec3(0.0, 0.0, 0.0)
  apart = wp.vec3(0.0, 0.0, 0.0)
  if o >= 0:
    apart = apartOf(b, k, o)
  if kind == POINT_GROUND:
    arm = wp.quat_rotate(qk, s.arm[t.point[i]])
    if run.terrain == 0:
      depth = (run.floor - b.place[k][2]) - b.shift[k][2] - arm[2]
    else:
      at = b.place[k] + b.shift[k] + arm
      ground = groundAt(run, at[0], at[1])
      normal = wp.vec3(ground[1], ground[2], ground[3])
      depth = (ground[0] - at[2]) * ground[3]
  elif kind == BALL_GROUND:
    r = b.radius[k]
    if run.terrain == 0:
      arm = -up * r
      depth = r - ((b.place[k][2] - run.floor) + b.shift[k][2])
    else:
      at = b.place[k] + b.shift[k]
      ground = groundAt(run, at[0], at[1])
      normal = wp.vec3(ground[1], ground[2], ground[3])
      arm = -normal * r
      depth = r - (at[2] - ground[0]) * ground[3]
  elif kind == BALL_BALL:
    far = wp.length(apart)
    if far > 0.0:
      normal = apart / far
      depth = b.radius[k] + b.radius[o] - far
      arm = -normal * b.radius[k]
  elif kind == POINT_PIECES:
    arm = wp.quat_rotate(qk, s.arm[t.point[i]])
    qo = b.turn[o]
    inside = wp.quat_rotate_inv(qo, apart + arm)
    if wp.length(inside) > b.reach[o] + EDGE:
      t.face[i] = -1
      t.depth[i] = 0.0
      return 0
    if run.grease > 0.0:
      state = wp.rand_init(seed, draw)
      inside = inside + wp.vec3(wp.randf(state) - 0.5,
                                wp.randf(state) - 0.5,
                                wp.randf(state) - 0.5) * (2.0 * run.grease)
    went = (b.shift[k] - b.shiftBefore[k]) - (b.shift[o] - b.shiftBefore[o])
    before = wp.quat_rotate_inv(b.turnBefore[o], apart - went
                                + wp.quat_rotate(b.turnBefore[k],
                                                 s.arm[t.point[i]]))
    face = faceFor(b, s, o, inside, before, wp.quat_rotate_inv(qo, apart),
                   t.face[i])
    if face >= 0:
      depth = s.offset[face] - wp.dot(s.facing[face], inside)
      normal = wp.quat_rotate(qo, s.facing[face])
      if depth <= 0.0:
        face = -1
    t.face[i] = face
  elif kind == BALL_TURNED:
    r = b.radius[k]
    looked = apart
    if run.grease > 0.0:
      state = wp.rand_init(seed, draw)
      looked = apart + wp.vec3(wp.randf(state) - 0.5,
                               wp.randf(state) - 0.5,
                               wp.randf(state) - 0.5) * (2.0 * run.grease)
    pressed = ballOnProfile(b, s, o, t.point[i], looked, r)
    depth = pressed[0]
    normal = wp.vec3(pressed[1], pressed[2], pressed[3])
    if s.hump.shape[0] > 0 and int(s.hump[0][0]) >= 0:
      lies = onFace(s, o, t.point[i], toOwn(b, o, looked) + b.centre[o])
      if lies[0] > 0.0 and lies[0] < FAR:
        depth = r - lies[0]
        normal = fromOwn(b, o, wp.vec3(lies[1], lies[2], lies[3]))
    arm = -normal * r
  elif kind == WHEEL_TURNED:
    axle = wp.quat_rotate(qk, t.axle[i])
    hub = wp.quat_rotate(qk, t.hub[i])
    looked = apart + hub
    if run.grease > 0.0:
      state = wp.rand_init(seed, draw)
      looked = looked + wp.vec3(wp.randf(state) - 0.5,
                                wp.randf(state) - 0.5,
                                wp.randf(state) - 0.5) * (2.0 * run.grease)
    lies = onFace(s, o, t.piece[i], toOwn(b, o, looked) + b.centre[o])
    if lies[0] > 0.0 and lies[0] < FAR:
      rise = fromOwn(b, o, wp.vec3(lies[1], lies[2], lies[3]))
      down = -rise + axle * wp.dot(axle, rise)
      size = wp.length(down)
      if size > FLAT:
        way = down / size
        reach = lies[0] / size
        depth = t.reach[i] - reach
        normal = -way
        arm = hub + way * reach
  elif kind == WHEEL_PIECES:
    axle = wp.quat_rotate(qk, t.axle[i])
    hub = wp.quat_rotate(qk, t.hub[i])
    qo = b.turn[o]
    looked = apart + hub
    if run.grease > 0.0:
      state = wp.rand_init(seed, draw)
      looked = looked + wp.vec3(wp.randf(state) - 0.5,
                                wp.randf(state) - 0.5,
                                wp.randf(state) - 0.5) * (2.0 * run.grease)
    pressed = wheelOnPieces(b, s, o, wp.quat_rotate_inv(qo, looked),
                            wp.quat_rotate_inv(qo, axle), t.reach[i])
    if pressed[0] > 0.0:
      way = wp.quat_rotate(qo, wp.vec3(pressed[1], pressed[2],
                                       pressed[3]))
      depth = pressed[0]
      normal = -way
      arm = hub + way * (t.reach[i] - depth)
  elif kind == PROBE_TURNED:
    if wp.length(apart) < b.reach[k] + b.reach[o]:
      r = t.reach[i]
      probe = wp.quat_rotate(qk, s.arm[t.point[i]])
      pressed = ballOnProfile(b, s, o, t.piece[i], apart + probe, r)
      depth = pressed[0]
      normal = wp.vec3(pressed[1], pressed[2], pressed[3])
      arm = probe - normal * r
  elif kind == PROBE_GROUND:
    r = t.reach[i]
    probe = wp.quat_rotate(qk, s.arm[t.point[i]])
    if run.terrain == 0:
      arm = probe - up * r
      depth = r - ((b.place[k][2] - run.floor) + b.shift[k][2] + probe[2])
    else:
      at = b.place[k] + b.shift[k] + probe
      ground = groundAt(run, at[0], at[1])
      normal = wp.vec3(ground[1], ground[2], ground[3])
      arm = probe - normal * r
      depth = r - (at[2] - ground[0]) * ground[3]
  elif kind == WHEEL_GROUND:
    axle = wp.quat_rotate(qk, t.axle[i])
    hub = wp.quat_rotate(qk, t.hub[i])
    if run.terrain == 0:
      down = -up + axle * axle[2]
      size = wp.length(down)
      if size > FLAT:
        way = down / size
        reach = ((b.place[k][2] - run.floor) + b.shift[k][2] + hub[2]) / (
          size)
        depth = t.reach[i] - reach
        normal = -way
        arm = hub + way * reach
    else:
      at = b.place[k] + b.shift[k] + hub
      ground = groundAt(run, at[0], at[1])
      level = wp.vec3(ground[1], ground[2], ground[3])
      down = -level + axle * wp.dot(axle, level)
      size = wp.length(down)
      if size > FLAT:
        way = down / size
        reach = (at[2] - ground[0]) * ground[3] / size
        depth = t.reach[i] - reach
        normal = -way
        arm = hub + way * reach
  elif kind == POINT_WALL or kind == PROBE_WALL or kind == BALL_WALL:
    r = wallReach(b, s, t, i, k)
    if kind != BALL_WALL:
      arm = wp.quat_rotate(qk, s.arm[t.point[i]])
    at = b.place[k] + b.shift[k] + arm
    if at[2] - r < groundAt(run, at[0], at[1])[0] + wallTop(run, at[0],
                                                             at[1]):
      wall = wallBeyond(run, at[0], at[1])
      depth = wall[0] + r
      normal = wp.vec3(-wall[1], -wall[2], 0.0)
      arm = arm - normal * r
  elif kind == ROLLER_TURNED:
    near = rollerPoint(b, s, k, o, t.point[i], apart)
    if near[3] > 0.0:
      own = toOwn(b, o, apart) + b.centre[o]
      p = wp.vec3(near[0], near[1], near[2])
      pressed = pointOnLine(s, t.point[i] // 2, p)
      depth = pressed[0]
      normal = fromOwn(b, o, wp.vec3(pressed[1], pressed[2], pressed[3]))
      arm = fromOwn(b, o, p - own)
  elif kind == POINT_TURNED:
    arm = wp.quat_rotate(qk, s.arm[t.point[i]])
    own = toOwn(b, o, apart + arm) + b.centre[o]
    pressed = pointOnLine(s, t.piece[i], own)
    depth = pressed[0]
    normal = fromOwn(b, o, wp.vec3(pressed[1], pressed[2], pressed[3]))
  elif kind == ROLLER_ROLLER:
    uk = axisOf(b, k)
    uo = axisOf(b, o)
    lengthK = b.roller[k]
    lengthO = b.roller[o]
    along = (2.0 * float(t.point[i]) - 1.0) * ROLLER_REACH * lengthK[1]
    onK = apart + uk * along
    onO = uo * wp.clamp(wp.dot(onK, uo), -lengthO[1], lengthO[1])
    between = onK - onO
    far = wp.length(between)
    if far > 0.0:
      normal = between / far
      depth = lengthK[0] + lengthO[0] - far
      arm = uk * along - normal * lengthK[0]
  else:
    r = b.radius[k]
    pressed = ballOnPieces(b, s, o, wp.quat_rotate_inv(b.turn[o], apart),
                           r)
    depth = pressed[0]
    normal = wp.quat_rotate(b.turn[o], wp.vec3(pressed[1], pressed[2],
                                               pressed[3]))
    arm = -normal * r
  t.depth[i] = depth
  t.normal[i] = normal
  t.firstArm[i] = wp.quat_rotate_inv(qk, arm)
  if kind == WHEEL_TURNED or kind == WHEEL_PIECES:
    t.secondArm[i] = wp.quat_rotate_inv(b.turn[o], apart + arm)
  elif o >= 0:
    t.secondArm[i] = wp.quat_rotate_inv(b.turn[o],
                                        apart + arm + normal * depth)
  else:
    t.secondArm[i] = wp.vec3(0.0, 0.0, 0.0)
  if depth > 0.0:
    return 1
  return 0


@wp.func
def armOf(b: Bodies, k: int, arm: wp.vec3) -> wp.vec3:
  """Body 'k's point at 'arm' (along its principal axes) from its
  centre, in the world, as it is turned now (the ground's, as is)."""
  if k < 0:
    return arm
  return wp.quat_rotate(b.turn[k], arm)


@wp.func
def slidOf(b: Bodies, k: int, arm: wp.vec3) -> wp.vec3:
  """How far body 'k's point at 'arm' (along its principal axes) has
  moved since the step's start (the ground's, nowhere)."""
  if k < 0:
    return wp.vec3(0.0, 0.0, 0.0)
  return (b.shift[k] - b.shiftBefore[k]) + wp.quat_rotate(
    b.turn[k], arm) - wp.quat_rotate(b.turnBefore[k], arm)


@wp.func
def nearTouch(run: Run, b: Bodies, s: Shapes, t: Touches, i: int,
              seconds: float):
  """Notes whether touch 'i' could press within 'seconds' ('near'),
  as far as its bodies' speeds and turning carry them in that time,
  twice over, gravity's fall and 'NEAR_MARGIN' besides: a skin point's
  or a tyre's probe's on the ground, if it is no higher over it than
  that, by how fast it nears the ground (the point's own velocity
  toward it, its height's change along the ground's slope under it, the
  slope's change about it besides, twice 'bendAt' (all of it, 'run.
  terrainBend', should it go further than a cell); found 2026-11-15:
  by its whole speed, the real car at 41 m/s looked for every point of
  its underside within 21 cm of the ground, half its CPU's time; on
  the level its fall alone counts) (a car's arms and shafts, riding on its tyres, are not looked
  for, nor its tyres' sidewalls' probes over the patch: three quarters
  of the real car's touches, two thirds of its steps' time on a CPU);
  any other between two bodies, if the balls about them holding all
  either touches with (its shape; a tyre's tread or a probe as far
  again) are no further apart than that (the driver sat in the real car
  and its four wheels' profiles, 84 touches, a third of what was left).
  The rest are always looked for. Those looked for are gathered
  ('nearList': every touch's phases walk them alone, a thread or so each
  on a GPU; in order on the CPU's one thread)."""
  kind = t.kind[i]
  k = t.first[i]
  o = t.second[i]
  near = int(1)
  if kind == POINT_GROUND or kind == PROBE_GROUND:
    arm = wp.quat_rotate(b.turn[k], s.arm[t.point[i]])
    moving = b.velocity[k] + wp.cross(b.spin[k], arm)
    low = float(0.0)
    closing = float(0.0)
    if run.terrain == 0:
      low = (b.place[k][2] - run.floor) + b.shift[k][2] + arm[2]
      closing = wp.abs(moving[2])
    else:
      at = b.place[k] + b.shift[k] + arm
      ground = groundAt(run, at[0], at[1])
      low = (at[2] - ground[0]) * ground[3]
      level = wp.sqrt(moving[0] * moving[0] + moving[1] * moving[1])
      bend = bendAt(run, at[0], at[1])
      if 2.0 * level * seconds > run.terrainCell:
        bend = run.terrainBend
      closing = wp.abs(moving[2] + (ground[1] * moving[0]
                                    + ground[2] * moving[1]) / ground[3]) + (
        2.0 * bend * level)
    if kind == PROBE_GROUND:
      low = low - t.reach[i]
    if low > 2.0 * closing * seconds + wp.length(run.gravity) * (
        seconds * seconds) + NEAR_MARGIN:
      near = 0
  elif kind == POINT_WALL or kind == PROBE_WALL or kind == BALL_WALL:
    r = wallReach(b, s, t, i, k)
    arm = wp.vec3(0.0, 0.0, 0.0)
    if kind != BALL_WALL:
      arm = wp.quat_rotate(b.turn[k], s.arm[t.point[i]])
    at = b.place[k] + b.shift[k] + arm
    wall = wallBeyond(run, at[0], at[1])
    moving = b.velocity[k] + wp.cross(b.spin[k], arm)
    closing = wp.abs(moving[0] * wall[1] + moving[1] * wall[2]) + (
      wp.length(b.spin[k]) * r)
    if -(wall[0] + r) > 2.0 * closing * seconds + NEAR_MARGIN:
      near = 0
  elif o >= 0 and kind != NO_TOUCH:
    near = 1 - pairFar(b, t, i, seconds)
  t.near[i] = near
  if near == 0:
    forgotten(t, i)
  else:
    t.nearList[wp.atomic_add(t.nearCount, 0, 1)] = i


@wp.func
def pairFar(b: Bodies, t: Touches, i: int, seconds: float) -> int:
  """Returns whether touch 'i' between two bodies cannot press within
  'seconds' ('nearTouch'): the balls about them holding all either
  touches with (its shape; a tyre's tread or a probe as far again)
  further apart than their speeds and turning carry them in that time,
  twice over, and 'NEAR_MARGIN'."""
  k = t.first[i]
  o = t.second[i]
  reach = b.reach[k] + t.reach[i] + wp.length(t.hub[i])
  gap = wp.length(apartOf(b, k, o)) - reach - b.reach[o]
  speed = wp.length(b.velocity[k] - b.velocity[o]) + wp.length(
    b.spin[k]) * reach + wp.length(b.spin[o]) * b.reach[o]
  if gap > 2.0 * speed * seconds + NEAR_MARGIN:
    return 1
  return 0


@wp.func
def forgotten(t: Touches, i: int):
  """Touch 'i' not looked for ('nearTouch'): it presses nothing, its
  face forgotten."""
  t.near[i] = 0
  t.depth[i] = 0.0
  t.pushed[i] = 0.0
  t.gripped[i] = 0.0
  t.face[i] = -1


@wp.func
def outsideBox(b: Bodies, o: int, apart: wp.vec3) -> float:
  """Returns how far the point 'apart' from body 'o''s centre (in the
  world) lies outside the box about all its pieces ('boxLow', 'boxHigh':
  along its principal axes; a body with none, its reach ball's box),
  m; nought inside."""
  inside = wp.quat_rotate_inv(b.turn[o], apart)
  low = b.boxLow[o]
  high = b.boxHigh[o]
  out = wp.vec3(wp.max(wp.max(low[0] - inside[0], inside[0] - high[0]),
                       0.0),
                wp.max(wp.max(low[1] - inside[1], inside[1] - high[1]),
                       0.0),
                wp.max(wp.max(low[2] - inside[2], inside[2] - high[2]),
                       0.0))
  return wp.length(out)


@wp.func
def pointFar(b: Bodies, s: Shapes, t: Touches, i: int,
             seconds: float) -> int:
  """Returns whether skin point touch 'i' ('POINT_PIECES') cannot press
  within 'seconds': its point further outside the box about the other's
  pieces ('outsideBox': a point outside it is in none of them, 'found'
  passing it over) than their speeds and turning carry it in that time,
  twice over, and 'NEAR_MARGIN' (found 2026-11-16: by the other's ball,
  a derailed cart's 8 m body near the track kept 14 700 touches looked
  for, most far from its slender self)."""
  k = t.first[i]
  o = t.second[i]
  arm = wp.quat_rotate(b.turn[k], s.arm[t.point[i]])
  gap = outsideBox(b, o, apartOf(b, k, o) + arm)
  speed = wp.length(b.velocity[k] - b.velocity[o]) + wp.length(
    b.spin[k]) * wp.length(arm) + wp.length(b.spin[o]) * b.reach[o]
  if gap > 2.0 * speed * seconds + NEAR_MARGIN:
    return 1
  return 0


@wp.func
def groupFar(b: Bodies, t: Touches, g: int, k: int, o: int,
             seconds: float) -> int:
  """Returns whether the skin points of group 'g' (body 'k''s against
  body 'o''s pieces) cannot press within 'seconds': the ball about them
  ('groupMiddle', 'groupReach': along 'k''s principal axes from its
  centre) further outside the box about 'o''s pieces ('outsideBox')
  than their speeds and turning carry them in that time, twice over,
  and 'NEAR_MARGIN'."""
  middle = wp.quat_rotate(b.turn[k], t.groupMiddle[g])
  r = t.groupReach[g]
  gap = outsideBox(b, o, apartOf(b, k, o) + middle) - r
  speed = wp.length(b.velocity[k] - b.velocity[o]) + wp.length(
    b.spin[k]) * (wp.length(middle) + r) + wp.length(b.spin[o]) * (
    b.reach[o])
  if gap > 2.0 * speed * seconds + NEAR_MARGIN:
    return 1
  return 0


@wp.func
def groupForgotten(t: Touches, g: int):
  """The touches of group 'g' not looked for ('forgotten'), if they
  were."""
  if t.groupNear[g] == 0:
    return
  i = t.groupFirst[g]
  for j in range(t.groupCount[g]):
    if t.near[i + j] != 0:
      forgotten(t, i + j)
  t.groupNear[g] = 0


@wp.func
def nearWay(b: Bodies, t: Touches, w: int, seconds: float):
  """Notes whether the touches of way 'w' could press within 'seconds',
  as a whole: one body's skin points against another's pieces
  ('POINT_PIECES': 'wayCount' groups of at most 'GROUP_MOST' points
  side by side) by the two bodies' balls ('pairFar'), forgotten as
  they go out of reach; the groups of a way that could, and a way of
  one touch, listed to be looked through ('groupList', 'nearGroup'),
  in the order they come. Found 2026-11-16: a crate spawned by the
  loop's track looked for its 284 000 touches with the 214 still
  bodies there one by one every 'NEAR_EVERY' steps (three times the
  rest of the world's steps), and, near, for every point of the
  island's edges against it each step."""
  g0 = t.wayFirst[w]
  count = t.wayCount[w]
  if count > 1 or t.groupCount[g0] > 1:
    if pairFar(b, t, t.groupFirst[g0], seconds) != 0:
      if t.wayNear[w] != 0:
        for g in range(g0, g0 + count):
          groupForgotten(t, g)
        t.wayNear[w] = 0
      return
    t.wayNear[w] = 1
  start = wp.atomic_add(t.groupListCount, 0, count)
  for j in range(count):
    t.groupList[start + j] = g0 + j


@wp.func
def nearGroup(run: Run, b: Bodies, s: Shapes, t: Touches, g: int,
              seconds: float):
  """Notes whether the touches of group 'g' could press within
  'seconds' (its way's bodies near: 'nearWay'): a group of one as that
  touch ('nearTouch'); skin points by the ball about them ('groupFar'),
  then point by point ('pointFar')."""
  i = t.groupFirst[g]
  count = t.groupCount[g]
  if count == 1:
    nearTouch(run, b, s, t, i, seconds)
    return
  if groupFar(b, t, g, t.first[i], t.second[i], seconds) != 0:
    groupForgotten(t, g)
    return
  for j in range(count):
    e = i + j
    if pointFar(b, s, t, e, seconds) != 0:
      if t.near[e] != 0:
        forgotten(t, e)
    else:
      t.near[e] = 1
      t.nearList[wp.atomic_add(t.nearCount, 0, 1)] = e
  t.groupNear[g] = 1


@wp.func
def countTouch(run: Run, b: Bodies, s: Shapes, t: Touches, i: int,
               seed: int, draw: int):
  """Finds touch 'i' anew ('seed' and 'draw' its random draws' place),
  if it is looked for ('nearTouch'), and, if it presses, counts it on
  both its bodies, and as a hold on either pressed against what holds
  still ('noteHold')."""
  if t.near[i] == 0:
    return
  if found(run, b, s, t, i, seed, draw) == 0:
    return
  k = t.first[i]
  o = t.second[i]
  note(b, k)
  note(b, o)
  noteHold(b, k, o, t.normal[i])
  noteHold(b, o, k, -t.normal[i])


@wp.func
def heldStill(b: Bodies, k: int) -> int:
  """Whether body 'k' holds still against what pushes it: the ground or
  a body of the world (not one held so itself: a roller held by its
  ring made its neighbours holds too, and the load handed on gripped
  where they rub, slowing the shaft 3 %; a stack's blocks shuffled
  their loads and drifted)."""
  if k < 0:
    return 1
  if b.give[k] == 0.0:
    return 1
  return 0


@wp.func
def noteHold(b: Bodies, k: int, other: int, way: wp.vec3):
  """Notes that a touch pushes body 'k' along 'way' out of 'other', if
  'other' holds still ('heldStill'): a hold on 'k'."""
  if k < 0:
    return
  if b.give[k] == 0.0:
    return
  if heldStill(b, other) == 0:
    return
  wp.atomic_add(b.backing, k, way)
  wp.atomic_add(b.backs, k, 1)


@wp.func
def intoHold(hold: wp.vec3, way: wp.vec3) -> int:
  """Whether pushing along 'way' pushes a body held as 'hold' says (the
  sum of its holds' pushes) into what holds it."""
  size = wp.length(hold)
  if size <= 0.0:
    return 0
  if wp.dot(way, hold) < -SHOCK * size:
    return 1
  return 0


@wp.func
def handedOn(b: Bodies, k: int, other: int, held: int,
             carried: wp.array(dtype=float)) -> float:
  """The share of the push body 'k' handed on through its holds (held
  'held' times; 'carried' the push) that a touch of it with 'other'
  carries, if that touch is one of its holds, else nought."""
  if k < 0:
    return 0.0
  if b.give[k] == 0.0 or held <= 0:
    return 0.0
  if heldStill(b, other) == 0:
    return 0.0
  return carried[k] / float(held)


@wp.func
def pushApart(b: Bodies, t: Touches, i: int, h: float):
  """Touch 'i', if it presses, moves its bodies just far enough apart
  (each as easily as its share gives there: 'splitGive'), and, while
  its push times its grip is more than holding them takes, back where
  its points touched at the step's start along the faces. A body it
  pushes into what holds it still ('intoHold'), as a ball between the
  hub and the still spindle (held in this pass or the last: a ball
  pushed just clear of it by its own touch, held only every other pass,
  let the hub sink again between), gives not at all to the push: the
  other
  takes it all (shock propagation: the ball cannot give that way; let
  give, an 8 g ball under a 4.6 kg hub took nearly all of each push and
  the hub sank half a millimetre), the push handed on through its
  holds, counted in their grip ('handedOn'), as a ball under load
  grips its raceway; friction as ever, both bodies giving (a tyre's
  grip is its tread's, worked out as it settles: 'tyreGrip'). No deeper
  than 'UNSTICK' a step at once (a body put inside another comes out at
  that pace). A soft
  touch (a tyre: 'soft' m/N) pushes as a spring does, as far as its
  softness lets (extended position based dynamics: what it pushed so
  far in the step held against its depth), never pulling."""
  if t.depth[i] <= 0.0:
    return
  k = t.first[i]
  o = t.second[i]
  normal = t.normal[i]
  armK = armOf(b, k, t.firstArm[i])
  armO = wp.vec3(0.0, 0.0, 0.0)
  if o >= 0:
    armO = armOf(b, o, t.secondArm[i])
  stillK = intoHold(b.backing[k] + b.backed[k], normal)
  stillO = 0
  if o >= 0:
    stillO = intoHold(b.backing[o] + b.backed[o], -normal)
  if stillK != 0 and stillO != 0:
    stillK = 0
    stillO = 0
  giveK = float(0.0)
  if stillK == 0:
    giveK = splitGive(b, k, armK, normal)
  giveO = float(0.0)
  if stillO == 0:
    giveO = splitGive(b, o, armO, normal)
  total = giveK + giveO
  if total <= 0.0:
    return
  pushing = wp.min(t.depth[i], UNSTICK * h) / total
  if t.soft[i] > 0.0:
    give = t.soft[i] / (h * h)
    pushing = wp.max((t.depth[i] - give * t.pushed[i]) / (total + give),
                     -t.pushed[i])
    if pushing == 0.0:
      return
  if t.pushed[i] <= 0.0:
    noteSettled(b, k)
    noteSettled(b, o)
  t.pushed[i] = t.pushed[i] + pushing
  t.impulse[i] = t.impulse[i] + normal * (pushing / h)
  if stillK != 0:
    wp.atomic_add(b.carried, k, pushing)
  else:
    ask(b, k, armK, normal * pushing)
  if stillO != 0:
    wp.atomic_add(b.carried, o, pushing)
  else:
    ask(b, o, armO, -normal * pushing)
  load = t.pushed[i] + handedOn(b, k, o, b.backs[k], b.carriedLast) + (
    handedOn(b, o, k, b.backs[o], b.carriedLast))
  if (t.kind[i] == WHEEL_GROUND or t.kind[i] == WHEEL_TURNED
      or t.kind[i] == WHEEL_PIECES):
    return
  slid = slidOf(b, k, t.firstArm[i]) - slidOf(b, o, t.secondArm[i])
  along = slid - normal * wp.dot(slid, normal)
  far = wp.length(along)
  if far > 0.0:
    way = along / far
    holding = far / (splitGive(b, k, armK, way) + splitGive(b, o, armO,
                                                            way))
    if t.gripped[i] + holding < t.grip[i] * load:
      t.gripped[i] = t.gripped[i] + holding
      ask(b, k, armK, -way * holding)
      ask(b, o, armO, way * holding)
      t.impulse[i] = t.impulse[i] - way * (holding / h)


@wp.func
def holdLink(b: Bodies, links: Links, j: int):
  """Link 'j' brings its points together (a tie) or to its length
  apart (a rod), each body as easily as its share among its links
  gives there ('linkGive')."""
  k = links.first[j]
  o = links.second[j]
  armK = wp.vec3(0.0, 0.0, 0.0)
  armO = wp.vec3(0.0, 0.0, 0.0)
  apart = wp.vec3(0.0, 0.0, 0.0)
  if k >= 0:
    armK = wp.quat_rotate(b.turn[k], links.firstArm[j])
  if o >= 0:
    armO = wp.quat_rotate(b.turn[o], links.secondArm[j])
  if k >= 0 and o >= 0:
    apart = apartOf(b, k, o) + armK - armO
  elif k >= 0:
    apart = (b.place[k] - links.secondArm[j]) + b.shift[k] + armK
  elif o >= 0:
    apart = (links.firstArm[j] - b.place[o]) - b.shift[o] - armO
  far = wp.length(apart)
  if far <= 0.0:
    return
  way = apart / far
  miss = far
  if links.kind[j] == ROD:
    miss = far - links.length[j]
  total = linkGive(b, k, armK, way) + linkGive(b, o, armO, way)
  if total <= 0.0:
    return
  pull = way * (miss / total)
  ask(b, k, armK, -pull)
  ask(b, o, armO, pull)


@wp.func
def motorKick(b: Bodies, m: Motors, j: int, h: float):
  """Motor 'j' twists its rotor for the step (its housing back, if a
  body that moves) by its drive: its torque less its damping times how
  fast the rotor turns on the housing at the step's end, the turning
  solved with the twist (implicit: a light rotor neither lags nor
  rings), no more than its most either way."""
  r = m.rotor[j]
  hs = m.housing[j]
  q = b.turn[r]
  g = b.turnGive[r]
  along = m.along[j]
  axis = wp.quat_rotate(q, along)
  soft = along[0] * along[0] * g[0] + along[1] * along[1] * g[1] + (
    along[2] * along[2] * g[2])
  if soft <= 0.0:
    return
  spin = wp.dot(b.spin[r], axis)
  if hs >= 0:
    spin = spin - wp.dot(b.spin[hs], axis)
  after = (spin + h * soft * m.torque[j]) / (1.0 + h * soft * m.damping[j])
  torque = wp.clamp(m.torque[j] - m.damping[j] * after, -m.most[j],
                    m.most[j])
  twist = axis * (torque * h)
  b.spin[r] = b.spin[r] + wp.quat_rotate(q, wp.cw_mul(
    wp.quat_rotate_inv(q, twist), g))
  if hs >= 0:
    if b.give[hs] > 0.0:
      qh = b.turn[hs]
      b.spin[hs] = b.spin[hs] - wp.quat_rotate(qh, wp.cw_mul(
        wp.quat_rotate_inv(qh, twist), b.turnGive[hs]))


@wp.func
def giveBetween(b: Bodies, k: int, arm: wp.vec3, one: wp.vec3,
                two: wp.vec3) -> float:
  """How far body 'k's point at 'arm' (in the world) moves along 'two'
  for a unit push along 'one': one over its mass times their dot, and
  how its turning moves the point ('giveAlong' when they are one way);
  nought for the ground or a body of the world."""
  if k < 0:
    return 0.0
  q = b.turn[k]
  u = wp.quat_rotate_inv(q, wp.cross(arm, one))
  v = wp.quat_rotate_inv(q, wp.cross(arm, two))
  g = b.turnGive[k]
  return b.give[k] * wp.dot(one, two) + u[0] * v[0] * g[0] + (
    u[1] * v[1] * g[1]) + u[2] * v[2] * g[2]


@wp.func
def chainArm(b: Bodies, ch: Chains, a: int) -> wp.vec3:
  """Slot 'a's point from its body's centre, in the world, as the body
  is turned now."""
  return wp.quat_rotate(b.turn[ch.body[a]], ch.arm[a])


@wp.func
def chainArmBefore(b: Bodies, ch: Chains, a: int) -> wp.vec3:
  """Slot 'a's point from its body's centre, in the world, as the body
  was turned at the step's start (where a piece's pull acts: its turning
  as SHAKE's pulls, along the lines as they were)."""
  return wp.quat_rotate(b.turnBefore[ch.body[a]], ch.arm[a])


@wp.func
def chainStart(b: Bodies, ch: Chains, a: int, z: int) -> wp.vec3:
  """How far slot 'z's point was from slot 'a's at the step's start (as
  the bodies were before they moved freely: 'shiftBefore',
  'turnBefore')."""
  ka = ch.body[a]
  kz = ch.body[z]
  return (b.place[kz] - b.place[ka]) + (b.shiftBefore[kz]
                                        - b.shiftBefore[ka]) + (
    wp.quat_rotate(b.turnBefore[kz], ch.arm[z])
    - wp.quat_rotate(b.turnBefore[ka], ch.arm[a]))


@wp.func
def chainSolve(ch: Chains, first: int, m: int, bumpFirst: float,
               bumpLast: float, rhs: wp.array(dtype=float),
               out: wp.array(dtype=float)):
  """Solves a line's 'm' rows (from slot 'first': each 'lo' times the
  pull before, 'mid' (its first row's 'bumpFirst' more, its last's
  'bumpLast') its own, 'hi' the next) for 'rhs', into 'out' (which may
  be 'rhs'): Thomas's elimination, sound for the line's equations,
  which are nearly symmetric and positive."""
  for i in range(m):
    a = first + i
    diag = ch.mid[a]
    if i == 0:
      diag = diag + bumpFirst
    if i == m - 1:
      diag = diag + bumpLast
    below = float(0.0)
    carry = float(0.0)
    if i > 0:
      below = ch.lo[a]
      carry = ch.dp[a - 1]
      diag = diag - below * ch.cp[a - 1]
    ch.cp[a] = 0.0
    if i < m - 1:
      ch.cp[a] = ch.hi[a] / diag
    ch.dp[a] = (rhs[a] - below * carry) / diag
  out[first + m - 1] = ch.dp[first + m - 1]
  for r in range(m - 1):
    a = first + m - 2 - r
    out[a] = ch.dp[a] - ch.cp[a] * out[a + 1]


@wp.func
def holdChain(b: Bodies, ch: Chains, c: int, h: float):
  """Cord line 'c' pulls its points so that, as near as one Newton step
  of all its pieces at once says, no piece is longer than it may be
  (each as soft as it is: extended position based dynamics): its
  pieces' equations solved together (a piece's pull moves the point it
  shares with the next, and so that piece: a chain of rows, a ring's
  closing on itself, Sherman and Morrison's way), each body giving as
  its share among its colour's slots ('split'); a piece found pushing
  is let go and the rest solved again ('CHAIN_ROUNDS' at most: cords
  only pull). A whole line held at once carries a load from one end to
  the other in a step, which pieces each holding their own, a pass at
  a time, cannot (a tyre's air, held so, ballooned its cords by a
  quarter and lost three quarters of its pressure). Each piece pulls
  along its way at the step's start, not now (as SHAKE does): pulls
  along their ends' line as it was keep the bodies' angular momentum
  exactly, where pulls along the line as moved took a spinning tyre's
  spin away, the faster the harder its air pushed (each step's push
  out is pulled back: at 2.3 bar two thirds of it in 0.2 s); the line's
  equations so are not quite symmetric, which the elimination does not
  mind."""
  first = ch.first[c]
  n = ch.count[c]
  closed = ch.closed[c]
  m = n - 1
  if closed != 0:
    m = n
  for j in range(m):
    a = first + j
    z = first + (j + 1) % n
    ka = ch.body[a]
    kz = ch.body[z]
    apart = apartOf(b, kz, ka) + chainArm(b, ch, z) - chainArm(b, ch, a)
    far = wp.length(apart)
    ch.way[a] = wp.vec3(0.0, 0.0, 0.0)
    ch.start[a] = wp.vec3(0.0, 0.0, 0.0)
    ch.miss[a] = far - ch.rest[a]
    ch.active[a] = 0
    if far > 0.0 and far > ch.rest[a]:
      ch.way[a] = apart / far
      ch.start[a] = ch.way[a]
      then = chainStart(b, ch, a, z)
      was = wp.length(then)
      if was > 0.0:
        ch.start[a] = then / was
      ch.active[a] = 1
  done = int(0)
  for round_ in range(CHAIN_ROUNDS):
    if done == 0:
      for j in range(m):
        a = first + j
        z = first + (j + 1) % n
        ch.lo[a] = 0.0
        ch.hi[a] = 0.0
        ch.mid[a] = 1.0
        ch.rhs[a] = 0.0
        if ch.active[a] != 0:
          way = ch.way[a]
          pull = ch.start[a]
          armA = chainArmBefore(b, ch, a)
          armZ = chainArmBefore(b, ch, z)
          ch.mid[a] = giveBetween(b, ch.body[a], armA, pull, way) * (
            ch.split[a]) + giveBetween(b, ch.body[z], armZ, pull, way) * (
            ch.split[z]) + ch.soft[a] / (h * h)
          ch.rhs[a] = -ch.miss[a]
          if j > 0 or closed != 0:
            before = first + (j + m - 1) % m
            if ch.active[before] != 0:
              ch.lo[a] = -giveBetween(b, ch.body[a], armA,
                                      ch.start[before], way) * ch.split[a]
          if j < m - 1 or closed != 0:
            after = first + (j + 1) % m
            if ch.active[after] != 0:
              ch.hi[a] = -giveBetween(b, ch.body[z], armZ,
                                      ch.start[after], way) * ch.split[z]
      if closed == 0:
        chainSolve(ch, first, m, 0.0, 0.0, ch.rhs, ch.pull)
      else:
        last = first + m - 1
        corner = ch.hi[last]
        across = ch.lo[first]
        gamma = -ch.mid[first]
        chainSolve(ch, first, m, -gamma, -corner * across / gamma,
                   ch.rhs, ch.pull)
        for j in range(m):
          ch.aux[first + j] = 0.0
        ch.aux[first] = gamma
        ch.aux[last] = corner
        chainSolve(ch, first, m, -gamma, -corner * across / gamma,
                   ch.aux, ch.aux)
        fact = (ch.pull[first] + across * ch.pull[last] / gamma) / (
          1.0 + ch.aux[first] + across * ch.aux[last] / gamma)
        for j in range(m):
          ch.pull[first + j] = ch.pull[first + j] - fact * ch.aux[first + j]
      done = int(1)
      for j in range(m):
        a = first + j
        if ch.active[a] != 0 and ch.pull[a] > 0.0:
          ch.active[a] = 0
          done = 0
  for j in range(m):
    a = first + j
    if ch.active[a] != 0:
      z = first + (j + 1) % n
      impulse = ch.start[a] * ch.pull[a]
      ask(b, ch.body[z], chainArmBefore(b, ch, z), impulse)
      ask(b, ch.body[a], chainArmBefore(b, ch, a), -impulse)


@wp.func
def airCorner(b: Bodies, airs: Airs, corner: int, base: int) -> wp.vec3:
  """Corner 'corner' of a face, from the centre of body 'base'."""
  k = airs.body[corner]
  return apartOf(b, k, base) + wp.quat_rotate(b.turn[k], airs.arm[corner])


@wp.func
def airVolume(b: Bodies, airs: Airs, f: int):
  """Face 'f' adds its share to its air's volume (its corners' triple
  product over six: the divergence theorem, exact for a closed
  surface of flat faces)."""
  air = airs.faceAir[f]
  base = airs.base[air]
  p0 = airCorner(b, airs, 3 * f, base)
  p1 = airCorner(b, airs, 3 * f + 1, base)
  p2 = airCorner(b, airs, 3 * f + 2, base)
  wp.atomic_add(airs.volume, air, wp.dot(p0, wp.cross(p1, p2)) / 6.0)


@wp.func
def airPush(b: Bodies, airs: Airs, f: int, h: float):
  """Face 'f' is pushed out for the step by its air's pressure over the
  outside's times its area, a third at each corner (into each body's
  'moved' and 'turned', taken by 'moveFreely' as its velocity and spin
  changed)."""
  air = airs.faceAir[f]
  volume = airs.volume[air]
  if volume <= 0.0:
    return
  pressure = airs.gas[air] / volume - OUTSIDE
  base = airs.base[air]
  p0 = airCorner(b, airs, 3 * f, base)
  p1 = airCorner(b, airs, 3 * f + 1, base)
  p2 = airCorner(b, airs, 3 * f + 2, base)
  impulse = wp.cross(p1 - p0, p2 - p0) * (pressure * h / 6.0)
  for c in range(3):
    k = airs.body[3 * f + c]
    ask(b, k, wp.quat_rotate(b.turn[k], airs.arm[3 * f + c]), impulse)


@wp.func
def takeMoves(b: Bodies, k: int):
  """Moves and turns body 'k' by all its rules gave it this pass, and
  forgets them and their count (a body of the world takes nothing)."""
  if b.give[k] > 0.0:
    b.shift[k] = b.shift[k] + b.moved[k]
    tilt = b.turned[k]
    if wp.length_sq(tilt) > 0.0:
      b.twist[k] = b.twist[k] + tilt
      q = b.turn[k]
      b.turn[k] = wp.normalize(q + wp.quat(tilt[0], tilt[1], tilt[2],
                                           0.0) * q * 0.5)
  b.moved[k] = wp.vec3(0.0, 0.0, 0.0)
  b.turned[k] = wp.vec3(0.0, 0.0, 0.0)
  b.asked[k] = 0


@wp.func
def takeTouchMoves(b: Bodies, k: int):
  """'takeMoves' after the touches' part of a pass: and keeps body 'k's
  holds and the push it handed on as the last pass's, and forgets
  this pass's."""
  takeMoves(b, k)
  b.backed[k] = b.backing[k]
  b.backing[k] = wp.vec3(0.0, 0.0, 0.0)
  b.backsLast[k] = b.backs[k]
  b.backs[k] = 0
  b.carriedLast[k] = b.carried[k]
  b.carried[k] = 0.0


@wp.func
def velocitiesOf(b: Bodies, k: int, h: float):
  """Reads body 'k's velocity and spin off how far it moved and turned
  in the step (a body of the world stays still), and moves its place on
  by its shift ('folded')."""
  if b.give[k] == 0.0:
    return
  b.velocity[k] = (b.shift[k] - b.shiftBefore[k]) / h
  b.spin[k] = b.twist[k] / h
  folded(b, k)


@wp.func
def settle(run: Run, b: Bodies, t: Touches, i: int, h: float):
  """Touch 'i', if it pushed in the step, stops its bodies closing or
  parting at it (no bounce; a soft touch, a spring, only damps it: its
  damping times how fast, no more than stops it), a body it pushes into
  what held it still
  in the last pass giving not at all to that ('pushApart'); and slows
  their sliding along each other by as much as its grip times its push
  (and the push handed on through it) lets, both giving; each body as
  easily as its share among the touches that pushed it gives there
  ('settleGive'). A tyre's grip is its tread's ('tyreGrip': a slip law,
  its stretch relaxing as it rolls). A tyre's sidewall's probe on the
  ground ('roll') slows the
  tyre's spin about its axle as its push acting ahead of the patch does
  (rolling resistance) and about the upright as its patch scrubs
  (pivoting), each no more than stops it (a lone wheel rolled on, round
  and round on its edge, never losing a joule: user, 2026-11-14, "my
  tyre won't stop eulering"); on a turntable, its rolling on the
  table's, the table taking the twist back, and no pivoting (the wheel
  rolls round a circle on it: the patch ever pivots on the deck, and
  slowing that, the twist precessed the spinning wheel, 66 rad/s, till
  its spin's upright part was the table's: 5.8 degrees of camber, its
  whole grip pushing it out). All a
  touch gives its first body is summed ('impulse'). The slowing is an
  impulse, no more than
  the grip's
  (its push over the step, times the grip) nor than stops the sliding
  (how fast over how easily they give: the cap was once that speed over
  how easily they give, a speed taken for an impulse, which let a 20 g
  tyre node take a fiftieth of its grip: a tyre lying flat slid on as
  on ice)."""
  pushing = t.pushed[i]
  if pushing <= 0.0:
    return
  k = t.first[i]
  o = t.second[i]
  normal = t.normal[i]
  armK = armOf(b, k, t.firstArm[i])
  moving = b.velocity[k] + wp.cross(b.spin[k], armK)
  armO = wp.vec3(0.0, 0.0, 0.0)
  if o >= 0:
    armO = armOf(b, o, t.secondArm[i])
    moving = moving - (b.velocity[o] + wp.cross(b.spin[o], armO))
  closing = wp.dot(normal, moving)
  sliding = moving - normal * closing
  stillK = intoHold(b.backed[k], normal)
  stillO = 0
  if o >= 0:
    stillO = intoHold(b.backed[o], -normal)
  if stillK != 0 and stillO != 0:
    stillK = 0
    stillO = 0
  if closing != 0.0:
    giveK = float(0.0)
    if stillK == 0:
      giveK = settleGive(b, k, armK, normal)
    giveO = float(0.0)
    if stillO == 0:
      giveO = settleGive(b, o, armO, normal)
    if giveK + giveO > 0.0:
      stop = normal * (-closing / (giveK + giveO))
      if t.soft[i] > 0.0:
        stop = stop * wp.min(t.lag[i] * h * (giveK + giveO), 1.0)
      if stillK == 0:
        ask(b, k, armK, stop)
      if stillO == 0:
        ask(b, o, armO, -stop)
      t.impulse[i] = t.impulse[i] + stop
  if (t.kind[i] == WHEEL_GROUND or t.kind[i] == WHEEL_TURNED
      or t.kind[i] == WHEEL_PIECES):
    tyreGrip(run, b, t, i, h, armK, armO, moving, pushing)
    return
  fast = wp.length(sliding)
  if fast > 0.0:
    load = pushing + handedOn(b, k, o, b.backsLast[k], b.carriedLast) + (
      handedOn(b, o, k, b.backsLast[o], b.carriedLast))
    way = sliding / fast
    total = settleGive(b, k, armK, way) + settleGive(b, o, armO, way)
    room = wp.max(t.grip[i] * load - t.gripped[i], 0.0) / h
    if total > 0.0:
      slow = way * (-wp.min(room, fast / total))
      ask(b, k, armK, slow)
      ask(b, o, armO, -slow)
      t.impulse[i] = t.impulse[i] + slow
  arms = t.roll[i]
  if o < 0 and (arms[0] > 0.0 or arms[1] > 0.0):
    impulse = pushing / h
    axle = wp.normalize(wp.quat_rotate(b.turn[k], t.axle[i]))
    spinSlowed(b, k, axle, arms[0], impulse)
    spinSlowed(b, k, normal, arms[1], impulse)


@wp.func
def textureCorner(seed: int, u: int, v: int) -> float:
  """The road's texture at its grid's corner 'u', 'v' (seeded 'seed'):
  a draw spread one about nought (the grid repeats every 1024 corners
  either way)."""
  state = wp.rand_init(seed, (u & 1023) * 1024 + (v & 1023))
  return (wp.randf(state) - 0.5) * 3.4641016


@wp.func
def textureAt(run: Run, p: wp.vec3) -> float:
  """How much of its grip a tyre has at 'p' on the road (in the road's
  own frame: a turntable's turns with it): one, and the road's texture,
  'run.rough' its spread, smooth over 'run.grain' (its corners' draws
  between them as smoothsteps), never under a tenth."""
  if run.rough <= 0.0:
    return 1.0
  u = p[0] / run.grain
  v = p[1] / run.grain
  iu = int(wp.floor(u))
  iv = int(wp.floor(v))
  fu = u - float(iu)
  fv = v - float(iv)
  su = fu * fu * (3.0 - 2.0 * fu)
  sv = fv * fv * (3.0 - 2.0 * fv)
  value = (textureCorner(run.texture, iu, iv) * (1.0 - su) * (1.0 - sv)
           + textureCorner(run.texture, iu + 1, iv) * su * (1.0 - sv)
           + textureCorner(run.texture, iu, iv + 1) * (1.0 - su) * sv
           + textureCorner(run.texture, iu + 1, iv + 1) * su * sv)
  return wp.max(1.0 + run.rough * TEXTURE_SPREAD * value, 0.1)


@wp.func
def tyreGrip(run: Run, b: Bodies, t: Touches, i: int, h: float,
             armK: wp.vec3, armO: wp.vec3, moving: wp.vec3,
             pushing: float):
  """Tyre touch 'i' grips the road as its tread does (a brush; the
  'TYRE_' constants): the tread in its patch stretches as the rim
  slips on the road ('moving': how fast the wheel's patch moves on the
  road's) and lets go as it rolls ('TYRE_RELAX'), pushing back by its
  stretch along the road and across it, as stiff as its load makes it,
  that force's growth bent over as more of the patch slides (the brush:
  its share of its load's grip times 3 theta less 3 theta squared and
  theta cubed) to its grip times its load (falling as its load grows,
  textured by the road: 'textureAt'), held there sliding all through,
  its grip falling as it slides faster than it first did; its rubber
  damping its stretching while it holds (how fast its stretch changes:
  damping the slip itself, steady in a turn, added a kilonewton), never
  past its grip (holding again after sliding, the damping took the
  step's whole slip for a stretch: a textured road's grip flickering,
  its side force spread 10 % for 3 % of grip); the
  push given its wheel, its
  road taking it back, explicitly (stiff as it is, a wheel's rim swings
  on it a few hundredths of a radian a step). Then its rolling is
  slowed as its push acts ahead of its patch (rolling resistance) and
  its pivoting on the road (its heading turning on it, not its spin's
  upright part when it leans: slowing that precessed the spinning wheel
  over) by its patch twisting on the road, its twist let go as it
  rolls as its stretch is ('TYRE_TWIST', held no harder than its
  'scrub' arm times its load: as a turned bearing creeps, a stand held
  only as hard as stops the wheel alone crept 5 degrees a second under
  a twist the tyre should hold)."""
  k = t.first[i]
  o = t.second[i]
  normal = t.normal[i]
  load = pushing / (h * h)
  axle = wp.normalize(wp.quat_rotate(b.turn[k], t.axle[i]))
  road = wp.vec3(0.0, 0.0, 0.0)
  where = b.place[k] + b.shift[k] + armK
  if o >= 0:
    road = b.velocity[o] + wp.cross(b.spin[o], armO)
    where = t.secondArm[i]
  hub = b.velocity[k] - road
  hub = hub - normal * wp.dot(normal, hub)
  rolling = wp.length(hub)
  slip = moving - normal * wp.dot(normal, moving)
  before = t.stretch[i]
  before = before - normal * wp.dot(normal, before)
  stretch = (before + slip * h) / (1.0 + rolling * h / TYRE_RELAX)
  ahead = wp.normalize(wp.cross(axle, normal))
  aside = wp.cross(normal, ahead)
  share = load / TYRE_LOAD
  grip = t.grip[i] * textureAt(run, where) * wp.max(
    1.0 - TYRE_LOAD_SENSE * (share - 1.0), 0.3)
  cornering = TYRE_CORNERING * wp.pow(wp.max(share, 0.01), 0.8)
  across = cornering / TYRE_RELAX
  along = across * TYRE_LONG
  linear = -(ahead * (along * wp.dot(stretch, ahead))
             + aside * (across * wp.dot(stretch, aside)))
  full = 3.0 * grip * load
  size = wp.length(linear)
  force = linear
  if size > 0.0 and full > 0.0:
    theta = size / full
    if theta < 1.0:
      force = linear * (1.0 - theta + theta * theta / 3.0) - (
        stretch - before) * (TYRE_TREAD_DAMPING / h)
      most = grip * load
      if wp.length(force) > most:
        force = force * (most / wp.length(force))
    else:
      stretch = stretch / theta
      fast = wp.length(slip)
      stiff = cornering
      if fast > 0.0:
        lengthwise = wp.dot(slip, ahead) / fast
        stiff = cornering * (1.0 + (TYRE_LONG - 1.0) * lengthwise
                             * lengthwise)
      past = wp.max(fast - full * rolling / stiff, 0.0)
      slide = TYRE_SLIDE + (1.0 - TYRE_SLIDE) / (
        1.0 + past / TYRE_SLIDE_SPEED)
      force = linear * (slide / (3.0 * theta))
  t.stretch[i] = stretch
  push = force * h
  ask(b, k, armK, push)
  ask(b, o, armO, -push)
  t.impulse[i] = t.impulse[i] + push
  arms = t.roll[i]
  impulse = pushing / h
  if o < 0:
    spinSlowed(b, k, axle, arms[0], impulse)
  else:
    spinSlowedOn(b, k, o, axle, arms[0], impulse)
  turning = b.spin[k]
  if o >= 0:
    turning = turning - b.spin[o]
  turning = turning - axle * wp.dot(turning, axle)
  was = t.twist[i]
  twist = (was + wp.dot(turning, normal) * h) / (
    1.0 + rolling * h / TYRE_RELAX)
  stiff = TYRE_TWIST * share
  hold = arms[1] * load
  moment = -stiff * twist - (twist - was) * (TYRE_TWIST_DAMPING / h)
  if hold <= 0.0 or stiff <= 0.0:
    twist = 0.0
    moment = 0.0
  elif stiff * wp.abs(twist) > hold:
    twist = wp.sign(twist) * hold / stiff
    moment = -wp.sign(twist) * hold
  t.twist[i] = twist
  turnBy(b, k, normal, moment * h)
  turnBy(b, o, normal, -moment * h)


@wp.func
def spinGive(b: Bodies, k: int, way: wp.vec3) -> float:
  """How easily body 'k' turns about 'way' (unit, in the world): one
  over its moment about it."""
  u = wp.quat_rotate_inv(b.turn[k], way)
  g = b.turnGive[k]
  return u[0] * u[0] * g[0] + u[1] * u[1] * g[1] + u[2] * u[2] * g[2]


@wp.func
def spinSlowed(b: Bodies, k: int, way: wp.vec3, arm: float,
               impulse: float):
  """Slows body 'k''s spin about 'way' (unit, in the world) by a twist
  of 'arm' times 'impulse' (N m s), no more than stops it (its share
  among the touches that pushed it in the step)."""
  about = wp.dot(b.spin[k], way)
  give = spinGive(b, k, way) * float(wp.max(b.settled[k], 1))
  if about == 0.0 or give <= 0.0:
    return
  twist = wp.min(arm * impulse, wp.abs(about) / give)
  if about > 0.0:
    twist = -twist
  q = b.turn[k]
  wp.atomic_add(b.turned, k, wp.quat_rotate(q, wp.cw_mul(
    wp.quat_rotate_inv(q, way * twist), b.turnGive[k])))


@wp.func
def spinSlowedOn(b: Bodies, k: int, o: int, way: wp.vec3, arm: float,
                 impulse: float):
  """Slows body 'k''s spin about 'way' (unit, in the world) on body
  'o''s (a tyre's on the turntable it rolls on) by a twist of 'arm'
  times 'impulse' (N m s), no more than stops it, 'o' taking the twist
  back (each its share among the touches that pushed it in the step).
  """
  about = wp.dot(b.spin[k] - b.spin[o], way)
  give = spinGive(b, k, way) * float(wp.max(b.settled[k], 1)) + (
    spinGive(b, o, way) * float(wp.max(b.settled[o], 1)))
  if about == 0.0 or give <= 0.0:
    return
  twist = wp.min(arm * impulse, wp.abs(about) / give)
  if about > 0.0:
    twist = -twist
  q = b.turn[k]
  wp.atomic_add(b.turned, k, wp.quat_rotate(q, wp.cw_mul(
    wp.quat_rotate_inv(q, way * twist), b.turnGive[k])))
  if b.give[o] > 0.0:
    qo = b.turn[o]
    wp.atomic_add(b.turned, o, -wp.quat_rotate(qo, wp.cw_mul(
      wp.quat_rotate_inv(qo, way * twist), b.turnGive[o])))


@wp.func
def takeKicks(b: Bodies, k: int):
  """Speeds and spins body 'k' by all its touches gave it, and forgets
  them and their count (a body of the world takes nothing)."""
  if b.give[k] > 0.0:
    b.velocity[k] = b.velocity[k] + b.moved[k]
    b.spin[k] = b.spin[k] + b.turned[k]
  b.moved[k] = wp.vec3(0.0, 0.0, 0.0)
  b.turned[k] = wp.vec3(0.0, 0.0, 0.0)
  b.asked[k] = 0


@wp.func
def lineOf(b: Bodies, k: int, line: wp.vec3, before: int) -> wp.vec3:
  """Body 'k''s line 'line' (along its principal axes) in the world, as
  turned now or ('before') at the step's start; the world's as is."""
  if k < 0:
    return line
  if before != 0:
    return wp.quat_rotate(b.turnBefore[k], line)
  return wp.quat_rotate(b.turn[k], line)


@wp.func
def pinGap(b: Bodies, hg: Hinges, j: int, before: int) -> wp.vec3:
  """How far hinge 'j''s pin's point on its first body is from the one
  on its second, in the world, as they lie now or ('before') at the
  step's start (each place and shift apart, nearly exact)."""
  k = hg.first[j]
  o = hg.second[j]
  gap = lineOf(b, k, hg.firstArm[j], before) - lineOf(
    b, o, hg.secondArm[j], before)
  if k >= 0:
    gap = gap + b.place[k]
    if before != 0:
      gap = gap + b.shiftBefore[k]
    else:
      gap = gap + b.shift[k]
  if o >= 0:
    gap = gap - b.place[o]
    if before != 0:
      gap = gap - b.shiftBefore[o]
    else:
      gap = gap - b.shift[o]
  return gap


@wp.func
def turnBy(b: Bodies, k: int, way: wp.vec3, amount: float):
  """Turns body 'k' with the pass's other rules as a twist of 'amount'
  about 'way' (unit, in the world) does (nothing, for the world or a
  body of it)."""
  if k < 0:
    return
  if b.give[k] == 0.0:
    return
  q = b.turn[k]
  wp.atomic_add(b.turned, k, wp.quat_rotate(q, wp.cw_mul(
    wp.quat_rotate_inv(q, way * amount), b.turnGive[k])))


@wp.func
def linkTurnGive(b: Bodies, k: int, way: wp.vec3) -> float:
  """How easily body 'k' turns about 'way' as its share among the links
  holding it ('spinGive' times their count); nought for the world."""
  if k < 0:
    return 0.0
  return spinGive(b, k, way) * float(wp.max(b.linkCount[k], 1))


@wp.func
def dampGive(b: Bodies, k: int, arm: wp.vec3, way: wp.vec3) -> float:
  """'shareGive' among the rules that damp body 'k' after the touches
  settle ('dampCount': springs' and dampers' damping, bushes' rubber,
  the hands on a fourth wall point; split among all its links, a
  shock's damper on a 9 kg wishbone was held to a quarter of its
  rebound, the eleven links' share of what stops it)."""
  if k < 0:
    return 0.0
  return shareGive(b, k, arm, way, b.dampCount[k])


@wp.func
def dampTurnGive(b: Bodies, k: int, way: wp.vec3) -> float:
  """How easily body 'k' turns about 'way' as its share among the
  rules that damp it ('dampGive'); nought for the world."""
  if k < 0:
    return 0.0
  return spinGive(b, k, way) * float(wp.max(b.dampCount[k], 1))


@wp.func
def yielded(miss: float, give: float, total: float, h: float) -> float:
  """How far a hinge's rule moves its bodies apart along its way to
  undo 'miss', they giving 'total' along it: all of it, rigid ('give'
  nought), else as far as its rubber gives ('give' m/N or rad/(N m):
  extended position based dynamics' compliance, Macklin, Müller and
  Chentanez 2016), as an impulse's worth over the step, before the
  bodies' gives. Its damping is in the velocities ('settleHinge'):
  damped here, against how far it had moved in the step, a bush took
  each step's fall under gravity for motion, and a door's bush, its
  give and tilt sharing that fall, sagged 2.7 times its weight's give
  (0.5 ms steps; the more, the shorter)."""
  if give <= 0.0:
    return miss / total
  return miss / (total + give / (h * h))


@wp.func
def holdHinge(run: Run, b: Bodies, hg: Hinges, j: int, h: float,
              seed: int, draw: int):
  """Hinge 'j' brings its pin's points together, across the pin and
  along it, and its pin's lines into one, and, if its rubber holds it,
  its twist back to as built; each body as easily as its share among
  its links gives ('linkGive'); rigid, or as far as its rubber gives
  ('yielded'). Its points are looked for shaken by up to 'run.grease'
  each way, at random ('seed', 'draw'): two hinges on one line (a door's)
  or a hinge and a tie hold the same twice, and rules holding twice
  fight over every rounding, in step, unless shaken."""
  k = hg.first[j]
  o = hg.second[j]
  give = hg.give[j]
  axisK = lineOf(b, k, hg.firstAxis[j], 0)
  axisO = lineOf(b, o, hg.secondAxis[j], 0)
  pin = wp.normalize(axisK + axisO)
  gap = pinGap(b, hg, j, 0)
  if run.grease > 0.0:
    state = wp.rand_init(seed, draw)
    gap = gap + wp.vec3(wp.randf(state) - 0.5, wp.randf(state) - 0.5,
                        wp.randf(state) - 0.5) * (2.0 * run.grease)
  armK = wp.vec3(0.0, 0.0, 0.0)
  armO = wp.vec3(0.0, 0.0, 0.0)
  if k >= 0:
    armK = wp.quat_rotate(b.turn[k], hg.firstArm[j])
  if o >= 0:
    armO = wp.quat_rotate(b.turn[o], hg.secondArm[j])
  along = wp.dot(gap, pin)
  across = gap - pin * along
  far = wp.length(across)
  if far > 0.0:
    way = across / far
    total = linkGive(b, k, armK, way) + linkGive(b, o, armO, way)
    if total > 0.0:
      pull = way * yielded(far, give[0], total, h)
      ask(b, k, armK, -pull)
      ask(b, o, armO, pull)
  total = linkGive(b, k, armK, pin) + linkGive(b, o, armO, pin)
  if total > 0.0 and along != 0.0 and give[1] >= 0.0:
    pull = pin * yielded(along, give[1], total, h)
    ask(b, k, armK, -pull)
    ask(b, o, armO, pull)
  tilt = wp.cross(axisK, axisO)
  size = wp.length(tilt)
  if size > 0.0:
    way = tilt / size
    total = linkTurnGive(b, k, way) + linkTurnGive(b, o, way)
    if total > 0.0:
      amount = yielded(wp.asin(wp.min(size, 1.0)), give[2], total, h)
      turnBy(b, k, way, amount)
      turnBy(b, o, way, -amount)
  if give[3] < 0.0:
    return
  refK = lineOf(b, k, hg.firstRef[j], 0)
  refO = lineOf(b, o, hg.secondRef[j], 0)
  refK = refK - pin * wp.dot(refK, pin)
  refO = refO - pin * wp.dot(refO, pin)
  twist = wp.atan2(wp.dot(wp.cross(refK, refO), pin), wp.dot(refK, refO))
  total = linkTurnGive(b, k, pin) + linkTurnGive(b, o, pin)
  if total <= 0.0 or twist == 0.0:
    return
  amount = yielded(twist, give[3], total, h)
  turnBy(b, k, pin, amount)
  turnBy(b, o, pin, -amount)


@wp.func
def damped(fast: float, give: float, lag: float, total: float,
           h: float) -> float:
  """How hard (an impulse) a bush's rubber slows its bodies moving
  'fast' on each other along a way it holds them ('give' m/N or
  rad/(N m) there, 'lag' s: its damping, lag over give, N s/m), they
  giving 'total' along it, in a step: its damping times 'fast' times
  the step, no more than stops them; none, rigid or free."""
  if give <= 0.0 or lag <= 0.0 or total <= 0.0:
    return 0.0
  return wp.min(lag / give * fast * h, fast / total)


@wp.func
def settleHinge(b: Bodies, hg: Hinges, j: int, h: float):
  """Hinge 'j''s rubber, if bushed, slows its bodies' moving on each
  other at its pin, across, along, tilting and (if it holds the twist)
  twisting, by its damping ('damped'); each body as its share among the
  rules damping it gives ('dampGive')."""
  give = hg.give[j]
  lag = hg.lag[j]
  if lag <= 0.0:
    return
  k = hg.first[j]
  o = hg.second[j]
  pin = wp.normalize(lineOf(b, k, hg.firstAxis[j], 0) + lineOf(
    b, o, hg.secondAxis[j], 0))
  armK = wp.vec3(0.0, 0.0, 0.0)
  armO = wp.vec3(0.0, 0.0, 0.0)
  moving = wp.vec3(0.0, 0.0, 0.0)
  turning = wp.vec3(0.0, 0.0, 0.0)
  if k >= 0:
    armK = wp.quat_rotate(b.turn[k], hg.firstArm[j])
    moving = b.velocity[k] + wp.cross(b.spin[k], armK)
    turning = b.spin[k]
  if o >= 0:
    armO = wp.quat_rotate(b.turn[o], hg.secondArm[j])
    moving = moving - (b.velocity[o] + wp.cross(b.spin[o], armO))
    turning = turning - b.spin[o]
  along = wp.dot(moving, pin)
  across = moving - pin * along
  fast = wp.length(across)
  if fast > 0.0:
    way = across / fast
    total = dampGive(b, k, armK, way) + dampGive(b, o, armO, way)
    push = way * damped(fast, give[0], lag, total, h)
    ask(b, k, armK, -push)
    ask(b, o, armO, push)
  if along != 0.0:
    total = dampGive(b, k, armK, pin) + dampGive(b, o, armO, pin)
    push = pin * (damped(wp.abs(along), give[1], lag, total, h) * wp.sign(
      along))
    ask(b, k, armK, -push)
    ask(b, o, armO, push)
  spun = wp.dot(turning, pin)
  tilting = turning - pin * spun
  fast = wp.length(tilting)
  if fast > 0.0:
    way = tilting / fast
    total = dampTurnGive(b, k, way) + dampTurnGive(b, o, way)
    slow = damped(fast, give[2], lag, total, h)
    turnBy(b, k, way, -slow)
    turnBy(b, o, way, slow)
  if spun != 0.0:
    total = dampTurnGive(b, k, pin) + dampTurnGive(b, o, pin)
    slow = damped(wp.abs(spun), give[3], lag, total, h) * wp.sign(spun)
    turnBy(b, k, pin, -slow)
    turnBy(b, o, pin, slow)


@wp.func
def lineGap(b: Bodies, ln: Lines, j: int, armK: wp.vec3,
            armO: wp.vec3) -> wp.vec3:
  """How far line 'j''s point on its first body is from the one on its
  second, in the world ('armK', 'armO': its points from their bodies'
  centres in the world, as turned now)."""
  k = ln.first[j]
  o = ln.second[j]
  if k >= 0 and o >= 0:
    return apartOf(b, k, o) + armK - armO
  if k >= 0:
    return (b.place[k] - ln.secondArm[j]) + b.shift[k] + armK
  if o >= 0:
    return (ln.firstArm[j] - b.place[o]) - b.shift[o] - armO
  return ln.firstArm[j] - ln.secondArm[j]


@wp.func
def lineArm(b: Bodies, k: int, arm: wp.vec3) -> wp.vec3:
  """A line's point 'arm' on body 'k' from its centre, in the world as
  turned now (nought for the world: its points are places)."""
  if k < 0:
    return wp.vec3(0.0, 0.0, 0.0)
  return wp.quat_rotate(b.turn[k], arm)


@wp.func
def lineSlack(ln: Lines, j: int, far: float) -> int:
  """Whether line 'j', its points 'far' apart, holds nothing: a buffer
  longer than its rest, a strap shorter (one of no rest length never)."""
  rest = ln.rest[j]
  if rest <= 0.0:
    return 0
  if far > rest and ln.pulls[j] == 0:
    return 1
  if far < rest and ln.pushes[j] == 0:
    return 1
  return 0


@wp.func
def holdLine(run: Run, b: Bodies, ln: Lines, j: int, h: float,
             seed: int, draw: int):
  """Spring 'j' moves its points toward its rest length apart (of no
  rest, together) as far as its stiffness lets ('yielded': extended
  position based dynamics' compliance, one over it), unless slack;
  each body as its share among its links gives. Its points are looked
  for shaken by up to 'run.grease' each way ('seed', 'draw'). A damper
  holds no length."""
  stiffness = ln.stiffness[j]
  if stiffness <= 0.0:
    return
  k = ln.first[j]
  o = ln.second[j]
  armK = lineArm(b, k, ln.firstArm[j])
  armO = lineArm(b, o, ln.secondArm[j])
  gap = lineGap(b, ln, j, armK, armO)
  if run.grease > 0.0:
    state = wp.rand_init(seed, draw)
    gap = gap + wp.vec3(wp.randf(state) - 0.5, wp.randf(state) - 0.5,
                        wp.randf(state) - 0.5) * (2.0 * run.grease)
  far = wp.length(gap)
  if far <= 0.0 or lineSlack(ln, j, far) != 0:
    return
  miss = far
  if ln.rest[j] > 0.0:
    miss = far - ln.rest[j]
  way = gap / far
  total = linkGive(b, k, armK, way) + linkGive(b, o, armO, way)
  if total <= 0.0:
    return
  pull = way * yielded(miss, 1.0 / stiffness, total, h)
  ask(b, k, armK, -pull)
  ask(b, o, armO, pull)


@wp.func
def linePushed(b: Bodies, ln: Lines, j: int, h: float):
  """Ram 'j' pushes its points apart for the step, as hard as its
  push says ('Lines.push', N), along the line between them as they
  start it (before they move freely, as gravity does)."""
  push = ln.push[j]
  if push == 0.0:
    return
  k = ln.first[j]
  o = ln.second[j]
  armK = lineArm(b, k, ln.firstArm[j])
  armO = lineArm(b, o, ln.secondArm[j])
  gap = lineGap(b, ln, j, armK, armO)
  far = wp.length(gap)
  if far <= 0.0:
    return
  shove = gap * (push * h / far)
  ask(b, k, armK, shove)
  ask(b, o, armO, -shove)


@wp.func
def dampedOne(b: Bodies, hg: Hinges, ln: Lines, e: int, hinges: int,
              h: float):
  """Damps the hinge or line numbered 'e' among the hinges ('hinges' of
  them, first) and then the lines, over 'h' ('settleHinge',
  'settleLine'): each phase's rules side by side, a thread each (one
  after the other in a thread, a round lasted a hinge's and a line's
  damping), and only those that damp (a rigid hinge's, an undamped
  line's call cost what it did not do, on a CPU)."""
  if e < hinges:
    if hg.lag[e] > 0.0:
      settleHinge(b, hg, e, h)
  else:
    j = e - hinges
    if ln.bump[j] > 0.0 or ln.rebound[j] > 0.0:
      settleLine(b, ln, j, h)


@wp.func
def settleLine(b: Bodies, ln: Lines, j: int, h: float):
  """Line 'j''s damping slows its points' parting ('rebound') or
  closing ('bump'), along it, that times how fast, over the step, no
  more than stops it (each body as its share among the rules damping it
  gives: 'dampGive'); a slack spring damps nothing."""
  if ln.bump[j] <= 0.0 and ln.rebound[j] <= 0.0:
    return
  k = ln.first[j]
  o = ln.second[j]
  armK = lineArm(b, k, ln.firstArm[j])
  armO = lineArm(b, o, ln.secondArm[j])
  gap = lineGap(b, ln, j, armK, armO)
  far = wp.length(gap)
  if far <= 0.0:
    return
  if ln.stiffness[j] > 0.0 and lineSlack(ln, j, far) != 0:
    return
  way = gap / far
  moving = wp.vec3(0.0, 0.0, 0.0)
  if k >= 0:
    moving = b.velocity[k] + wp.cross(b.spin[k], armK)
  if o >= 0:
    moving = moving - (b.velocity[o] + wp.cross(b.spin[o], armO))
  rate = wp.dot(moving, way)
  if rate == 0.0:
    return
  damping = ln.bump[j]
  if rate > 0.0:
    damping = ln.rebound[j]
  total = dampGive(b, k, armK, way) + dampGive(b, o, armO, way)
  if total <= 0.0 or damping <= 0.0:
    return
  fast = wp.abs(rate)
  slow = way * (wp.min(damping * fast * h, fast / total) * wp.sign(rate))
  ask(b, k, armK, -slow)
  ask(b, o, armO, slow)


@wp.func
def turnedOn(b: Bodies, k: int, o: int, axis: wp.vec3) -> float:
  """How far body 'k' has turned on body 'o' (the world, below nought)
  about 'axis' (unit, in the world) in the step so far."""
  turned = wp.dot(b.twist[k], axis)
  if o >= 0:
    turned = turned - wp.dot(b.twist[o], axis)
  return turned


@wp.func
def holdTurn(b: Bodies, tn: Turns, j: int, h: float):
  """Fourth wall point 'j' (the player's hands) turns its body on its
  holder about its axis toward the angle asked, as stiff as the hands
  are ('yielded'), never harder than their most over the step; the
  holder as much back."""
  k = tn.body[j]
  o = tn.holder[j]
  axis = wp.quat_rotate(b.turn[k], tn.axis[j])
  miss = tn.angle[j] + turnedOn(b, k, o, axis) - tn.target[j]
  total = linkTurnGive(b, k, axis) + linkTurnGive(b, o, axis)
  if total <= 0.0 or miss == 0.0:
    return
  most = tn.most[j] * h * h
  amount = wp.clamp(yielded(miss, tn.give[j], total, h), -most, most)
  turnBy(b, k, axis, -amount)
  turnBy(b, o, axis, amount)


@wp.func
def settleTurn(b: Bodies, tn: Turns, j: int, h: float):
  """Fourth wall point 'j''s hands damp its body's turning on its holder
  as it lags or leads what the player asks ('rate': damping the turning
  itself held the wheel to its most over its damping, 3 rad/s), no
  harder than their most; and the step's turn is counted into its
  angle."""
  k = tn.body[j]
  o = tn.holder[j]
  axis = wp.quat_rotate(b.turn[k], tn.axis[j])
  tn.angle[j] = tn.angle[j] + turnedOn(b, k, o, axis)
  rate = wp.dot(b.spin[k], axis) - tn.rate[j]
  if o >= 0:
    rate = rate - wp.dot(b.spin[o], axis)
  total = dampTurnGive(b, k, axis) + dampTurnGive(b, o, axis)
  if total <= 0.0 or rate == 0.0:
    return
  fast = wp.abs(rate)
  slow = wp.min(wp.min(tn.damping[j] * fast * h, fast / total),
                tn.most[j] * h) * wp.sign(rate)
  turnBy(b, k, axis, -slow)
  turnBy(b, o, axis, slow)


@wp.func
def rackAt(b: Bodies, gr: Gears, j: int) -> float:
  """How far gear 'j''s rack lies along its line from its housing's
  centre, m, as they lie now."""
  r = gr.rack[j]
  hs = gr.housing[j]
  if hs >= 0:
    return wp.dot(wp.quat_rotate_inv(b.turn[hs], apartOf(b, r, hs)),
                  gr.rackAxis[j])
  return wp.dot(b.place[r] + b.shift[r], gr.rackAxis[j])


@wp.func
def trainGiven(b: Bodies, k: int, way: wp.vec3) -> wp.vec3:
  """How body 'k' turns, rad, in the world, for a twist's worth 'way'
  (in the world, kg m² rad): its inverse moment times it; nought for
  the world or a body of it."""
  if k < 0:
    return wp.vec3(0.0, 0.0, 0.0)
  if b.give[k] == 0.0:
    return wp.vec3(0.0, 0.0, 0.0)
  q = b.turn[k]
  return wp.quat_rotate(q, wp.cw_mul(wp.quat_rotate_inv(q, way),
                                     b.turnGive[k]))


@wp.func
def trainRule(run: Run, b: Bodies, gr: Gears, br: Brakes, tr: Train,
              r: int, h: float, seed: int, draw: int):
  """The drivetrain's rule 'r' as the pass finds it ('Train'). A mesh
  (the first 'run.gears' less 'run.racks'): the miss at the pitch
  circles, as far round as the first gear has turned on the housing at
  its radius and the second the other way at its (the same way, its
  radius below nought), from as built, looked for shaken by up to
  'run.grease' (m) at random ('seed', 'draw'); the two gears turn it
  about their axes at their radii, the housing about both. A disc
  brake, if its pads are on the disc and pressed: the disc's turn on
  the caliper since they last gripped it ('held': what it has crept
  since, held back too; held only as at the step's start, two brakes on
  one shaft, a gearbox's dogs and a held wheel's, split the slip
  between them every step for good: the shaft crept at half its gear's
  speed), the most it holds their friction at the pads' reach from the
  axle over the step squared (a push's worth: the pads' push on the
  disc and its bearing's on its hub are a twist about the axle, so it
  is solved; pushed as a force at the pads, the bearing solved apart,
  the brake held half again its torque, the wheel sliding on its
  bearing between); else it holds nothing."""
  meshes = run.gears - run.racks
  zero = wp.vec3(0.0, 0.0, 0.0)
  bodies = wp.vec3i(-1, -1, -1)
  one = zero
  two = zero
  three = zero
  miss = float(0.0)
  most = float(-1.0)
  holds = int(1)
  if r < meshes:
    j = run.racks + r
    p = gr.pinion[j]
    q = gr.rack[j]
    hs = gr.housing[j]
    first = wp.quat_rotate(b.turn[p], gr.pinionAxis[j])
    second = wp.quat_rotate(b.turn[q], gr.rackAxis[j])
    miss = gr.angle[j] + gr.radius[j] * turnedOn(b, p, hs, first) + (
      gr.secondRadius[j] * turnedOn(b, q, hs, second))
    if run.grease > 0.0:
      state = wp.rand_init(seed, draw + j)
      miss = miss + (wp.randf(state) - 0.5) * (2.0 * run.grease)
    bodies = wp.vec3i(p, q, hs)
    one = first * gr.radius[j]
    two = second * gr.secondRadius[j]
    three = -(one + two)
  else:
    j = r - meshes
    k = br.disc[j]
    o = br.caliper[j]
    bodies = wp.vec3i(k, o, -1)
    holds = 0
    at = onDisc(b, br, j)
    if at[3] > 0.0 and br.force[j] > 0.0:
      axle = wp.quat_rotate(b.turn[k], br.axle[j])
      out = wp.vec3(at[0], at[1], at[2]) - wp.quat_rotate(b.turn[k],
                                                          br.middle[j])
      most = br.force[j] * wp.length(out - axle * wp.dot(out, axle)) * (
        h * h)
      miss = br.held[j] + turnedOn(b, k, o, axle)
      one = axle
      two = -axle
      if most > 0.0:
        holds = 1
  tr.body[r] = bodies
  tr.jacobian[3 * r] = one
  tr.jacobian[3 * r + 1] = two
  tr.jacobian[3 * r + 2] = three
  tr.given[3 * r] = trainGiven(b, bodies[0], one)
  tr.given[3 * r + 1] = trainGiven(b, bodies[1], two)
  tr.given[3 * r + 2] = trainGiven(b, bodies[2], three)
  tr.miss[r] = miss
  tr.most[r] = most
  tr.holds[r] = holds


@wp.func
def trainPair(tr: Train, rules: int, e: int):
  """Adds pair 'e' (two rules sharing a body) to the equations: how much
  the first's miss changes by the second's pull, through that body."""
  pair = tr.pairs[e]
  wp.atomic_add(tr.matrix, pair[0] * rules + pair[2], wp.dot(
    tr.jacobian[3 * pair[0] + pair[1]], tr.given[3 * pair[2] + pair[3]]))


@wp.func
def trainFactored(tr: Train, rules: int, held: int, lane: int,
                  lanes: int):
  """Factors the equations of the 'held' rules that hold ('order'),
  each scaled to one ('scale') and eased by 'TRAIN_EASE' (Cholesky's,
  column by column, each column's rows and the rest's update side by
  side on 'lanes' lanes, this one 'lane'; the lower triangle in
  'factor')."""
  for a in range(lane, held, lanes):
    r = tr.order[a]
    tr.scale[a] = 1.0 / wp.sqrt(tr.matrix[r * rules + r])
  laneBarrier()
  for e in range(lane, held * held, lanes):
    a = e // held
    c = e - a * held
    if c <= a:
      v = tr.matrix[tr.order[a] * rules + tr.order[c]] * (
        tr.scale[a] * tr.scale[c])
      if a == c:
        v = v + TRAIN_EASE
      tr.factor[e] = v
  laneBarrier()
  for c in range(held):
    d = wp.sqrt(wp.max(tr.factor[c * held + c], TRAIN_EASE))
    for a in range(c + 1 + lane, held, lanes):
      tr.factor[a * held + c] = tr.factor[a * held + c] / d
    laneBarrier()
    rest = held - c - 1
    for e in range(lane, rest * rest, lanes):
      a = c + 1 + e // rest
      k = c + 1 + e - (e // rest) * rest
      if k <= a:
        tr.factor[a * held + k] = tr.factor[a * held + k] - (
          tr.factor[a * held + c] * tr.factor[k * held + c])
    if lane == 0:
      tr.factor[c * held + c] = d
    laneBarrier()


@wp.func
def trainInverted(tr: Train, held: int, lane: int, lanes: int):
  """The factored equations' inverse ('inverse', row by row), its columns
  side by side on 'lanes' lanes, each solved for its own unit down the
  factor and back up it, in place."""
  for c in range(lane, held, lanes):
    for a in range(held):
      tr.inverse[a * held + c] = 0.0
    tr.inverse[c * held + c] = 1.0
    for a in range(c, held):
      v = tr.inverse[a * held + c]
      for k in range(c, a):
        v = v - tr.factor[a * held + k] * tr.inverse[k * held + c]
      tr.inverse[a * held + c] = v / tr.factor[a * held + a]
    for back in range(held):
      a = held - 1 - back
      v = tr.inverse[a * held + c]
      for k in range(a + 1, held):
        v = v - tr.factor[k * held + a] * tr.inverse[k * held + c]
      tr.inverse[a * held + c] = v / tr.factor[a * held + a]
  laneBarrier()


@wp.func
def trainApplied(tr: Train, held: int, lane: int, lanes: int):
  """The pulls the inverse gives for what 'work' holds ('down'), and
  added to those found ('found', each scaled back), rows side by side."""
  for a in range(lane, held, lanes):
    v = float(0.0)
    for c in range(held):
      v = v + tr.inverse[a * held + c] * tr.work[c]
    tr.found[a] = tr.found[a] + tr.scale[a] * v
  laneBarrier()


@wp.func
def trainSolved(run: Run, br: Brakes, tr: Train, rules: int, lane: int,
                lanes: int):
  """The drivetrain's rules' pulls, all together, on 'lanes' lanes side
  by side (this one 'lane'): every rule that holds missing nothing once
  its bodies have turned for every pull (a light differential's spiders
  between its heavy half shafts: swept rule by rule, they took twelve
  sweeps to hold it to a percent, never fewer driving, and on a GPU's
  one thread those sweeps were the car's whole step), solved by the
  inverse of their equations (factored and inverted anew when other
  rules hold, or after 'TRAIN_REUSE' solves), then solved once more for
  what that left on the equations as they are; a brake that slipped in
  the last pass tried only if alone it could hold (its miss over its own
  give no more than its most: the sweep's own test; tried every pass, an
  anti-lock's four brakes at their grip let go one by one each step, the
  inverse made anew for each); one that would hold more than its most
  lets go (the one furthest past it, then solved anew without it: it
  slips, 'settleBrake'); each brake noted gripping or not
  ('gripping')."""
  meshes = run.gears - run.racks
  for r in range(lane, rules, lanes):
    tr.pull[r] = 0.0
    give = tr.matrix[r * rules + r]
    if give <= 0.0:
      tr.holds[r] = 0
    elif r >= meshes and tr.holds[r] != 0:
      if br.gripping[r - meshes] == 0 and wp.abs(tr.miss[r]) > (
          tr.most[r] * give):
        tr.holds[r] = 0
  if lane == 0:
    tr.count[3] = tr.count[3] + 1
  laneBarrier()
  held = int(0)
  for _ in range(run.brakes + 1):
    if lane == 0:
      count = int(0)
      same = int(1)
      for r in range(rules):
        if tr.holds[r] != 0:
          if count >= tr.count[2]:
            same = 0
          elif tr.kept[count] != r:
            same = 0
          tr.order[count] = r
          count = count + 1
      if count != tr.count[2] or tr.count[3] > TRAIN_REUSE:
        same = 0
      tr.count[0] = count
      tr.count[4] = same
    laneBarrier()
    held = tr.count[0]
    if tr.count[4] == 0:
      trainFactored(tr, rules, held, lane, lanes)
      trainInverted(tr, held, lane, lanes)
      if lane == 0:
        for a in range(held):
          tr.kept[a] = tr.order[a]
        tr.count[2] = held
        tr.count[3] = 1
    for a in range(lane, held, lanes):
      tr.found[a] = 0.0
      tr.work[a] = tr.scale[a] * tr.miss[tr.order[a]]
    laneBarrier()
    for again in range(2):
      trainApplied(tr, held, lane, lanes)
      if again == 0:
        for a in range(lane, held, lanes):
          row = tr.order[a] * rules
          left = tr.miss[tr.order[a]]
          for c in range(held):
            left = left - tr.matrix[row + tr.order[c]] * tr.found[c]
          tr.down[a] = tr.scale[a] * left
        laneBarrier()
        for a in range(lane, held, lanes):
          tr.work[a] = tr.down[a]
        laneBarrier()
    if lane == 0:
      worst = float(1.0)
      drop = int(-1)
      for a in range(held):
        r = tr.order[a]
        if r >= meshes:
          past = wp.abs(tr.found[a]) / tr.most[r]
          if past > worst:
            worst = past
            drop = r
      if drop >= 0:
        tr.holds[drop] = 0
      tr.count[1] = drop
    laneBarrier()
    if tr.count[1] < 0:
      break
  for a in range(lane, held, lanes):
    tr.pull[tr.order[a]] = tr.found[a]
  for j in range(lane, run.brakes, lanes):
    br.gripping[j] = tr.holds[meshes + j]


@wp.func
def trainMoves(tr: Train, r: int):
  """Rule 'r''s bodies turn for its pull, if it holds (added to each
  body's turn from the drivetrain, 'trainTurned')."""
  if tr.holds[r] == 0:
    return
  bodies = tr.body[r]
  for a in range(3):
    k = bodies[a]
    if k >= 0:
      wp.atomic_add(tr.turn, k, -tr.given[3 * r + a] * tr.pull[r])


@wp.func
def trainTurned(b: Bodies, tr: Train, k: int):
  """Body 'k' turns at once as the drivetrain's pulls turn it, its
  turn from them forgotten."""
  tilt = tr.turn[k]
  if tilt[0] == 0.0 and tilt[1] == 0.0 and tilt[2] == 0.0:
    return
  q = b.turn[k]
  b.twist[k] = b.twist[k] + tilt
  b.turn[k] = wp.normalize(q + wp.quat(tilt[0], tilt[1], tilt[2], 0.0)
                           * q * 0.5)
  tr.turn[k] = wp.vec3(0.0, 0.0, 0.0)


@wp.func
def holdGear(run: Run, b: Bodies, gr: Gears, j: int, h: float,
             seed: int, draw: int):
  """Rack and pinion 'j' holds its rack where its pinion's turning puts
  it (the pitch radius a radian, from as built): the rack pushed along
  its line, the pinion turned, each as easily as its share gives, the
  housing taking both back. Its miss is looked for shaken by up to
  'run.grease' (m) at random ('seed', 'draw')."""
  if gr.kind[j] == MESH:
    return
  p = gr.pinion[j]
  r = gr.rack[j]
  hs = gr.housing[j]
  radius = gr.radius[j]
  axis = wp.quat_rotate(b.turn[p], gr.pinionAxis[j])
  line = gr.rackAxis[j]
  if hs >= 0:
    line = wp.quat_rotate(b.turn[hs], line)
  miss = (rackAt(b, gr, j) - gr.start[j]) - radius * (
    gr.angle[j] + turnedOn(b, p, hs, axis))
  if run.grease > 0.0:
    state = wp.rand_init(seed, draw)
    miss = miss + (wp.randf(state) - 0.5) * (2.0 * run.grease)
  zero = wp.vec3(0.0, 0.0, 0.0)
  armH = zero
  if hs >= 0:
    armH = apartOf(b, r, hs)
  total = linkGive(b, r, zero, line) + radius * radius * linkTurnGive(
    b, p, axis) + linkGive(b, hs, armH, line) + radius * radius * (
    linkTurnGive(b, hs, axis))
  if total <= 0.0 or miss == 0.0:
    return
  pull = miss / total
  ask(b, r, zero, -line * pull)
  turnBy(b, p, axis, radius * pull)
  ask(b, hs, armH, line * pull)
  turnBy(b, hs, axis, -radius * pull)


@wp.func
def gearTurned(b: Bodies, gr: Gears, j: int):
  """Counts the step's turn of gear 'j''s pinion on its housing into
  its angle (a mesh's, both its gears' at their pitch circles: how far
  they slipped apart)."""
  p = gr.pinion[j]
  hs = gr.housing[j]
  axis = wp.quat_rotate(b.turn[p], gr.pinionAxis[j])
  if gr.kind[j] == MESH:
    q = gr.rack[j]
    other = wp.quat_rotate(b.turn[q], gr.rackAxis[j])
    gr.angle[j] = gr.angle[j] + gr.radius[j] * turnedOn(b, p, hs, axis) + (
      gr.secondRadius[j] * turnedOn(b, q, hs, other))
  else:
    gr.angle[j] = gr.angle[j] + turnedOn(b, p, hs, axis)


@wp.func
def onDisc(b: Bodies, br: Brakes, j: int) -> wp.vec4:
  """Where brake 'j''s pads are on its disc, as its bodies lie now: the
  pads' middle from the disc's body's centre, in the world (x, y, z),
  and, last, whether it lies on the disc's swept ring (1) or not (0)."""
  k = br.disc[j]
  o = br.caliper[j]
  onPads = wp.vec3(0.0, 0.0, 0.0)
  if o >= 0:
    onPads = apartOf(b, o, k) + wp.quat_rotate(b.turn[o], br.pad[j])
  else:
    onPads = (br.pad[j] - b.place[k]) - b.shift[k]
  axle = wp.quat_rotate(b.turn[k], br.axle[j])
  out = onPads - wp.quat_rotate(b.turn[k], br.middle[j])
  rho = wp.length(out - axle * wp.dot(out, axle))
  ring = br.ring[j]
  rubs = float(0.0)
  if rho >= ring[0] and rho <= ring[1]:
    rubs = 1.0
  return wp.vec4(onPads[0], onPads[1], onPads[2], rubs)


@wp.func
def brakeGive(b: Bodies, k: int, axle: wp.vec3, share: float) -> float:
  """How easily body 'k' turns about 'axle' (unit, in the world) for a
  brake: as its share among the brakes on it ('spinGive' times
  'share'); nought for the world or a body of it."""
  if k < 0:
    return 0.0
  return spinGive(b, k, axle) * share


@wp.func
def brakeTwist(b: Bodies, k: int, axle: wp.vec3, twist: float):
  """Turns body 'k' (or speeds its spin, at the velocities) as a twist
  of 'twist' about 'axle' does, with the pass's other rules (nothing,
  for the world)."""
  if k < 0:
    return
  if b.give[k] == 0.0:
    return
  q = b.turn[k]
  wp.atomic_add(b.turned, k, wp.quat_rotate(q, wp.cw_mul(
    wp.quat_rotate_inv(q, axle * twist), b.turnGive[k])))


@wp.func
def settleBrake(b: Bodies, br: Brakes, j: int, h: float):
  """Brake 'j''s pads, if gripping, count what the disc still turned on
  the caliper in the step into what they hold back ('held'; slipping,
  nothing); then, if on the disc, slow its turning on the caliper by as
  much as their friction gives in the step (its force at the pads'
  reach, times the step), no more than stops it; the caliper as much
  back."""
  k = br.disc[j]
  o = br.caliper[j]
  axle = wp.quat_rotate(b.turn[k], br.axle[j])
  if br.gripping[j] != 0:
    crept = wp.dot(b.twist[k], axle)
    if o >= 0:
      crept = crept - wp.dot(b.twist[o], axle)
    br.held[j] = br.held[j] + crept
  else:
    br.held[j] = 0.0
  at = onDisc(b, br, j)
  if at[3] <= 0.0:
    return
  out = wp.vec3(at[0], at[1], at[2]) - wp.quat_rotate(b.turn[k],
                                                      br.middle[j])
  reach = wp.length(out - axle * wp.dot(out, axle))
  turning = wp.dot(b.spin[k], axle)
  if o >= 0:
    turning = turning - wp.dot(b.spin[o], axle)
  total = brakeGive(b, k, axle, br.discShare[j]) + brakeGive(
    b, o, axle, br.caliperShare[j])
  if total <= 0.0 or turning == 0.0:
    return
  slow = wp.min(br.force[j] * reach * h, wp.abs(turning) / total)
  if turning > 0.0:
    slow = -slow
  brakeTwist(b, k, axle, slow)
  brakeTwist(b, o, axle, -slow)


@wp.kernel
def stepsRun(run: Run, b: Bodies, s: Shapes, t: Touches,
             links: Links, m: Motors, ch: Chains, airs: Airs,
             br: Brakes, hg: Hinges, ln: Lines, tn: Turns,
             gr: Gears, tr: Train):
  """The assembly stepped on 'run.count' steps of 'run.h', the
  launch's threads side by side in one block, each taking every n-th
  body, touch, link, cord line, face or motor, all waiting for the
  rest between the parts."""
  tid = wp.tid()
  n = run.threads
  h = run.h
  rules = run.gears - run.racks + run.brakes
  held = run.links + run.hinges + run.lines + run.turns + run.gears
  hingesTo = run.links + run.hinges
  linesTo = hingesTo + run.lines
  turnsTo = linesTo + run.turns
  dampedTo = run.brakes + run.hinges + run.lines
  settled = dampedTo + run.turns + run.gears
  last = clockNow()
  for step in range(run.count):
    if step % NEAR_EVERY == 0:
      if tid == 0:
        t.nearCount[0] = 0
        t.groupListCount[0] = 0
      barrier()
      for w in range(tid, run.ways, n):
        nearWay(b, t, w, h * float(NEAR_EVERY))
      barrier()
      listed = t.groupListCount[0]
      for e in range(tid, listed, n):
        nearGroup(run, b, s, t, t.groupList[e], h * float(NEAR_EVERY))
      barrier()
      last = marked(run, tid, 0, last)
    near = t.nearCount[0]
    if run.airs > 0:
      for a in range(tid, run.airs, n):
        airs.volume[a] = 0.0
      barrier()
      last = marked(run, tid, 1, last)
      for f in range(tid, run.faces, n):
        airVolume(b, airs, f)
      barrier()
      last = marked(run, tid, 1, last)
      for f in range(tid, run.faces, n):
        airPush(b, airs, f, h)
      barrier()
      last = marked(run, tid, 1, last)
    for e in range(tid, run.motors + run.lines, n):
      if e < run.motors:
        motorKick(b, m, e, h)
      else:
        linePushed(b, ln, e - run.motors, h)
    barrier()
    last = marked(run, tid, 2, last)
    for k in range(tid, run.bodies, n):
      moveFreely(run, b, k, h)
    for e in range(tid, near, n):
      t.pushed[t.nearList[e]] = 0.0
      t.gripped[t.nearList[e]] = 0.0
    barrier()
    last = marked(run, tid, 3, last)
    for p in range(run.passes):
      for e in range(tid, near, n):
        i = t.nearList[e]
        countTouch(run, b, s, t, i, run.seed + step, p * run.touches + i)
      barrier()
      last = marked(run, tid, 4, last)
      for e in range(tid, near, n):
        i = t.nearList[e]
        if t.depth[i] > 0.0:
          pushApart(b, t, i, h)
      barrier()
      last = marked(run, tid, 5, last)
      for k in range(tid, run.bodies, n):
        takeTouchMoves(b, k)
      barrier()
      last = marked(run, tid, 6, last)
      if (run.links > 0 or run.hinges > 0 or run.lines > 0
          or run.turns > 0 or run.gears > 0):
        for e in range(tid, held, n):
          if e < run.links:
            holdLink(b, links, e)
          elif e < hingesTo:
            holdHinge(run, b, hg, e - run.links, h, run.seed + step,
                      run.passes * run.touches + p * run.hinges
                      + e - run.links)
          elif e < linesTo:
            holdLine(run, b, ln, e - hingesTo, h, run.seed + step,
                     run.passes * (run.touches + run.hinges)
                     + p * run.lines + e - hingesTo)
          elif e < turnsTo:
            holdTurn(b, tn, e - linesTo, h)
          else:
            holdGear(run, b, gr, e - turnsTo, h, run.seed + step,
                     run.passes * (run.touches + run.hinges + run.lines)
                     + p * run.gears + e - turnsTo)
        barrier()
        last = marked(run, tid, 7, last)
        for k in range(tid, run.bodies, n):
          takeMoves(b, k)
        barrier()
        last = marked(run, tid, 6, last)
      for color in range(run.colors):
        start = ch.colorFirst[color]
        for c in range(tid, ch.colorCount[color], n):
          holdChain(b, ch, ch.order[start + c], h)
        barrier()
        last = marked(run, tid, 8, last)
        for k in range(tid, run.bodies, n):
          takeMoves(b, k)
        barrier()
        last = marked(run, tid, 8, last)
      if rules > 0:
        for e in range(tid, rules * rules, n):
          tr.matrix[e] = 0.0
        for r in range(tid, rules, n):
          trainRule(run, b, gr, br, tr, r, h, run.seed + step,
                    run.passes * (run.touches + run.hinges + run.lines
                                  + run.gears) + p * run.gears)
        barrier()
        last = marked(run, tid, 9, last)
        for e in range(tid, run.pairs, n):
          trainPair(tr, rules, e)
        barrier()
        last = marked(run, tid, 10, last)
        if tid < TRAIN_LANES:
          trainSolved(run, br, tr, rules, tid, wp.min(n, TRAIN_LANES))
        barrier()
        last = marked(run, tid, 11, last)
        for r in range(tid, rules, n):
          trainMoves(tr, r)
        barrier()
        last = marked(run, tid, 12, last)
        for k in range(tid, run.bodies, n):
          trainTurned(b, tr, k)
        barrier()
        last = marked(run, tid, 12, last)
    for k in range(tid, run.bodies, n):
      velocitiesOf(b, k, h)
    barrier()
    last = marked(run, tid, 13, last)
    for e in range(tid, near, n):
      i = t.nearList[e]
      if t.pushed[i] > 0.0:
        settle(run, b, t, i, h)
    barrier()
    last = marked(run, tid, 14, last)
    for k in range(tid, run.bodies, n):
      takeKicks(b, k)
    barrier()
    last = marked(run, tid, 15, last)
    if (run.brakes > 0 or run.hinges > 0 or run.lines > 0
        or run.turns > 0 or run.gears > 0):
      for e in range(tid, settled, n):
        if e < run.brakes:
          settleBrake(b, br, e, h)
        elif e < dampedTo:
          dampedOne(b, hg, ln, e - run.brakes, run.hinges,
                    h / float(DAMP_ROUNDS))
        elif e < dampedTo + run.turns:
          settleTurn(b, tn, e - dampedTo, h)
        else:
          gearTurned(b, gr, e - dampedTo - run.turns)
      barrier()
      last = marked(run, tid, 16, last)
      for k in range(tid, run.bodies, n):
        takeKicks(b, k)
      barrier()
      last = marked(run, tid, 15, last)
      if run.hinges > 0 or run.lines > 0:
        for _ in range(DAMP_ROUNDS - 1):
          for e in range(tid, run.hinges + run.lines, n):
            dampedOne(b, hg, ln, e, run.hinges, h / float(DAMP_ROUNDS))
          barrier()
          last = marked(run, tid, 16, last)
          for k in range(tid, run.bodies, n):
            takeKicks(b, k)
          barrier()
          last = marked(run, tid, 15, last)


#  The same steps spread over the whole GPU ('SmallSteps.spread'): each
#  part of a step a kernel of its own, a thread for each motor, body,
#  touch or link, as many blocks as that takes, one after the other
#  (a launch waits for the one before it: the parts' barriers); the
#  step's length and number read from the device ('clock', 'ticks'), so
#  a step's launches, captured once as a CUDA graph, replay unchanged.


@wp.kernel
def motorsPart(b: Bodies, m: Motors, clock: wp.array(dtype=float)):
  """The motors' twists ('motorKick')."""
  motorKick(b, m, wp.tid(), clock[0])


@wp.kernel
def linePushPart(b: Bodies, ln: Lines, clock: wp.array(dtype=float)):
  """Every ram pushes its points apart for the step ('linePushed')."""
  linePushed(b, ln, wp.tid(), clock[0])


@wp.kernel
def movePart(run: Run, b: Bodies, t: Touches, m: Motors,
             clock: wp.array(dtype=float)):
  """Every body moved freely ('moveFreely'), a motor's rotor first
  twisted by it ('motorKick', when every housing is still:
  'run.motorsMerged'); every touch's push in the step forgotten."""
  i = wp.tid()
  if i < run.bodies:
    if run.motorsMerged != 0:
      j = b.rotorOf[i]
      if j >= 0:
        motorKick(b, m, j, clock[0])
    moveFreely(run, b, i, clock[0])
  if i < run.touches:
    t.pushed[i] = 0.0
    t.gripped[i] = 0.0


@wp.kernel
def countPart(run: Run, b: Bodies, s: Shapes, t: Touches,
              ticks: wp.array(dtype=int), p: int):
  """Every touch found anew and counted ('countTouch'), in pass 'p'."""
  i = wp.tid()
  if t.near[i] != 0:
    countTouch(run, b, s, t, i, ticks[0], p * run.touches + i)


@wp.kernel
def pushPart(b: Bodies, t: Touches, clock: wp.array(dtype=float)):
  """Every touch pressing pushes its bodies apart ('pushApart')."""
  i = wp.tid()
  if t.depth[i] > 0.0:
    pushApart(b, t, i, clock[0])


@wp.kernel
def takeMovesPart(b: Bodies):
  """Every body takes what its rules gave it ('takeMoves')."""
  takeMoves(b, wp.tid())


@wp.kernel
def takeTouchMovesPart(b: Bodies):
  """Every body takes what the touches gave it ('takeTouchMoves')."""
  takeTouchMoves(b, wp.tid())


@wp.kernel
def holdPart(b: Bodies, links: Links):
  """Every link holds its points ('holdLink')."""
  holdLink(b, links, wp.tid())


@wp.kernel
def velocitiesPart(b: Bodies, clock: wp.array(dtype=float)):
  """Every body's velocity and spin read off its step ('velocitiesOf').
  """
  velocitiesOf(b, wp.tid(), clock[0])


@wp.kernel
def settlePart(run: Run, b: Bodies, t: Touches,
               clock: wp.array(dtype=float)):
  """Every touch that pushed settles its bodies ('settle')."""
  i = wp.tid()
  if t.pushed[i] > 0.0:
    settle(run, b, t, i, clock[0])


@wp.kernel
def takeKicksPart(b: Bodies, ticks: wp.array(dtype=int)):
  """Every body takes its touches' kicks ('takeKicks'); the step's
  number counted on."""
  k = wp.tid()
  takeKicks(b, k)
  if k == 0:
    ticks[0] = ticks[0] + 1


@wp.kernel
def hingePart(run: Run, b: Bodies, hg: Hinges,
              ticks: wp.array(dtype=int), clock: wp.array(dtype=float),
              p: int):
  """Every hinge holds its pin ('holdHinge'), in pass 'p', with the
  links (taking their moves after both)."""
  j = wp.tid()
  holdHinge(run, b, hg, j, clock[0], ticks[0],
            run.passes * run.touches + p * run.hinges + j)


@wp.kernel
def nearResetPart(t: Touches):
  """The touches looked for and the groups listed forgotten, to be
  gathered anew ('nearPart')."""
  t.nearCount[0] = 0
  t.groupListCount[0] = 0


@wp.kernel
def nearPart(run: Run, b: Bodies, s: Shapes, t: Touches,
             clock: wp.array(dtype=float), steps: int):
  """Every way of touches noted whether it could press in the next
  'steps' steps ('nearWay')."""
  nearWay(b, t, wp.tid(), clock[0] * float(steps))


@wp.kernel
def nearGroupPart(run: Run, b: Bodies, s: Shapes, t: Touches,
                  clock: wp.array(dtype=float), steps: int):
  """Every group of touches listed ('nearWay') noted whether it could
  press in the next 'steps' steps ('nearGroup')."""
  e = wp.tid()
  if e < t.groupListCount[0]:
    nearGroup(run, b, s, t, t.groupList[e], clock[0] * float(steps))


@wp.kernel
def trainRulePart(run: Run, b: Bodies, gr: Gears, br: Brakes, tr: Train,
                  ticks: wp.array(dtype=int), clock: wp.array(dtype=float),
                  p: int):
  """Every rule of the drivetrain as the pass finds it ('trainRule'),
  in pass 'p'; its equations cleared."""
  i = wp.tid()
  rules = run.gears - run.racks + run.brakes
  if i < rules * rules:
    tr.matrix[i] = 0.0
  if i < rules:
    trainRule(run, b, gr, br, tr, i, clock[0], ticks[0],
              run.passes * (run.touches + run.hinges + run.lines
                            + run.gears) + p * run.gears)


@wp.kernel
def trainPairPart(run: Run, tr: Train):
  """Every pair of the drivetrain's rules added to its equations
  ('trainPair')."""
  trainPair(tr, run.gears - run.racks + run.brakes, wp.tid())


@wp.kernel
def trainSolvePart(run: Run, br: Brakes, tr: Train):
  """The drivetrain's pulls, on a warp's lanes ('trainSolved')."""
  trainSolved(run, br, tr, run.gears - run.racks + run.brakes, wp.tid(),
              TRAIN_LANES)


@wp.kernel
def trainMovesPart(tr: Train):
  """Every rule of the drivetrain turns its bodies ('trainMoves')."""
  trainMoves(tr, wp.tid())


@wp.kernel
def trainTurnedPart(b: Bodies, tr: Train):
  """Every body turns as the drivetrain turned it ('trainTurned')."""
  trainTurned(b, tr, wp.tid())


@wp.kernel
def brakeSettlePart(b: Bodies, br: Brakes,
                    clock: wp.array(dtype=float)):
  """Every disc brake's pads slow their disc's sliding ('settleBrake').
  """
  settleBrake(b, br, wp.tid(), clock[0])


@wp.kernel
def hingeSettlePart(b: Bodies, hg: Hinges, clock: wp.array(dtype=float),
                    rounds: int):
  """Every bushed hinge's rubber damps its bodies' moving on each other
  ('settleHinge') for its share of the step, one of 'rounds'."""
  settleHinge(b, hg, wp.tid(), clock[0] / float(rounds))


@wp.kernel
def linePart(run: Run, b: Bodies, ln: Lines,
             ticks: wp.array(dtype=int), clock: wp.array(dtype=float),
             p: int):
  """Every spring holds its length ('holdLine'), in pass 'p', with the
  links."""
  j = wp.tid()
  holdLine(run, b, ln, j, clock[0], ticks[0],
           run.passes * (run.touches + run.hinges) + p * run.lines + j)


@wp.kernel
def lineSettlePart(b: Bodies, ln: Lines, clock: wp.array(dtype=float),
                   rounds: int):
  """Every spring's and damper's damping slows its points ('settleLine')
  for its share of the step, one of 'rounds'."""
  settleLine(b, ln, wp.tid(), clock[0] / float(rounds))


@wp.kernel
def turnPart(b: Bodies, tn: Turns, clock: wp.array(dtype=float)):
  """Every fourth wall point that turns turns its body ('holdTurn')."""
  holdTurn(b, tn, wp.tid(), clock[0])


@wp.kernel
def gearPart(run: Run, b: Bodies, gr: Gears, ticks: wp.array(dtype=int),
             clock: wp.array(dtype=float), p: int):
  """Every rack and pinion holds its rack to its pinion ('holdGear'), in
  pass 'p'."""
  j = wp.tid()
  holdGear(run, b, gr, j, clock[0], ticks[0],
           run.passes * (run.touches + run.hinges + run.lines)
           + p * run.gears + j)


@wp.kernel
def turnSettlePart(b: Bodies, tn: Turns, gr: Gears, turns: int,
                   gears: int, clock: wp.array(dtype=float)):
  """Every fourth wall point that turns damps and counts its turn
  ('settleTurn'); every pinion's turn is counted ('gearTurned')."""
  j = wp.tid()
  if j < turns:
    settleTurn(b, tn, j, clock[0])
  if j < gears:
    gearTurned(b, gr, j)


@wp.kernel
def brakeKicksPart(b: Bodies):
  """Every body takes its brakes' kicks ('takeKicks')."""
  takeKicks(b, wp.tid())


@wp.kernel
def chainPart(b: Bodies, ch: Chains, start: int,
              clock: wp.array(dtype=float)):
  """Every cord line of a colour (from 'start' in the order) held whole
  ('holdChain')."""
  holdChain(b, ch, ch.order[start + wp.tid()], clock[0])


@wp.kernel
def airZeroPart(airs: Airs):
  """Every air's volume forgotten, to be summed anew."""
  airs.volume[wp.tid()] = 0.0


@wp.kernel
def airVolumePart(b: Bodies, airs: Airs):
  """Every face adds its share to its air's volume ('airVolume')."""
  airVolume(b, airs, wp.tid())


@wp.kernel
def airPushPart(b: Bodies, airs: Airs, clock: wp.array(dtype=float)):
  """Every face is pushed out by its air ('airPush')."""
  airPush(b, airs, wp.tid(), clock[0])


#  A crowd's touches found anew each call, all on the device: its room
#  emptied, its balls gathered, a hash grid built over them (by the
#  host's call, between launches), and each ball's near ones of other
#  groups written into the room.


@wp.kernel
def crowdReset(cr: Crowds, t: Touches, slots: int, crowds: int):
  """Every slot of every crowd's room (the first 'slots' threads, from
  the first crowd's first slot on) touching nothing; every crowd's
  count and fastest speed forgotten."""
  i = wp.tid()
  if i < slots:
    s = cr.start[0] + i
    t.kind[s] = NO_TOUCH
    t.first[s] = 0
    t.second[s] = -1
  if i < crowds:
    cr.taken[i] = 0
    cr.fastest[i] = 0.0


@wp.kernel
def crowdGather(b: Bodies, cr: Crowds):
  """Every crowd ball's place (from the origin) and speed noted, its
  crowd's fastest kept."""
  i = wp.tid()
  k = cr.ball[i]
  cr.points[i] = b.place[k] + b.shift[k]
  fast = wp.length(b.velocity[k])
  cr.speed[i] = fast
  wp.atomic_max(cr.fastest, cr.crowdOf[i], fast)


@wp.kernel
def crowdPairs(cr: Crowds, t: Touches, grid: wp.uint64, seconds: float,
               margin: float):
  """Every crowd ball writes into its crowd's room a touch with each
  ball after it of another group of its crowd whose gap they could close
  within 'seconds' going as fast as they go now, and 'margin' more (as
  many as there is room for; the rest are not met this call)."""
  i = wp.tid()
  c = cr.crowdOf[i]
  p = cr.points[i]
  reach = cr.radius[i] + cr.widest[c] + (cr.speed[i] + cr.fastest[c]) * (
    seconds) + margin
  query = wp.hash_grid_query(grid, p, reach)
  j = int(0)
  while wp.hash_grid_query_next(query, j):
    if j > i and cr.crowdOf[j] == c and cr.group[j] != cr.group[i]:
      gap = wp.length(cr.points[j] - p) - cr.radius[i] - cr.radius[j]
      if gap <= (cr.speed[i] + cr.speed[j]) * seconds + margin:
        slot = wp.atomic_add(cr.taken, c, 1)
        if slot < cr.room[c]:
          s = cr.start[c] + slot
          t.kind[s] = BALL_BALL
          t.first[s] = cr.ball[i]
          t.second[s] = cr.ball[j]
