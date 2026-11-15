"""
SmallSteps steps bodies on in small steps, their touches kept as rules
(user, 2026-11-13: "we don't need a 'good' solution, we need one that
my RTX 5060 is 'good at solving'!"): no springs, no matrix, every touch
on its own thread at once, in float32 ('_small_steps_kernels'). So far
balls, convex shapes (a shape's pieces), turned solids (met by balls,
and by rollers: 'rollerShape', on a ring's straight raceways and
ribs, and on each other),
bodies made part of the world ('Fixed'), the flat ground, contacts'
grip, ties, actuators holding their length ('HeldStroke'), motors
(their drives' torque, damping and most), cord lines ('CordLine', each
held whole at once), air sealed in ('Air'), crowds of balls ('Crowd',
which may touch found near each call), disc brakes ('DiscBrake': pads
holding a disc by their friction), hinges ('Hinge', rigid or bushed),
sliding joints ('Slide'), springs ('Spring', pulling, pushing or both)
and dampers ('Damper', its rebound its own), rams ('Ram') and tyres
('Tyre') on the ground and on turntables (a turned solid's wide flat
face, with the 'Humps' bolted to it); no drags,
welds or moving strokes yet, and a turned solid does not meet the
ground.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from types import SimpleNamespace
from typing import TYPE_CHECKING, NamedTuple

import numpy

from ._assembly import ATMOSPHERE, HUMP_ROOM, HeldStroke, Hinge
from ._body import State
from ._ground import Ground
from ._poke import reachOf
from ._rounds import piecesOf
from ._shape import Sphere
from ._turned import Turned, nearestOnPiece, rollerOf
from ._vectors import Vector, applied, conjugate, matrixOf, minus, norm
from ._vectors import dot, plus, product, rotated, transposed

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Assembly

#  How near a skin point must start to a turned solid's straight piece
#  facing it to be let meet it, m ('_landTouches').
LAND_REACH = 5e-4
#  How much nearer than they could close in a call two balls of a crowd
#  are let touch anyway, m ('_Packed.crowded'); the crowds' hash grid's
#  cells, at least this wide, m, and four of the widest ball across.
CROWD_MARGIN = 5e-3
CROWD_CELL = 0.05
#  How many threads step a world on a GPU, in one block (the user's RTX
#  5060, the bearing, one pass: 256 0.755 s of computing a simulated
#  second, 512 0.694, 1024 refused: too many registers for one block;
#  2026-11-14, the real car's kernel grown, 512 refused too, CUDA error
#  701: a block of 256 always launches, each thread up to 255 registers,
#  and it is Warp's own block, so one build serves the spread path too).
THREADS = 256
#  How many steps one CUDA graph replays, spread over the GPU.
GRAPH_STEPS = 16
#  The grids over bodies of many pieces (a track of planks: a touch
#  looks only at the pieces near it, not every one): from how many
#  pieces a body gets one, its cells' width, m (wider where there would
#  be more than 'GRID_MOST' of them), and how much further than its
#  pieces' boxes a cell lists them, m, past the widest ball's or tyre's
#  radius (the soapbox's chassis, 200 skin points each looking at all
#  179 planks, took 38 % of its step).
GRID_FROM, GRID_CELL, GRID_MOST, GRID_MARGIN = 32, 1.0, 20000, 0.1
_kernels = None


def _kernelsOf():
  """Returns the kernels' module, imported (and Warp started) at its
  first use."""
  global _kernels
  if _kernels is None:
    import warp as wp
    wp.init()
    from . import _small_steps_kernels
    _kernels = _small_steps_kernels
  return _kernels


def preloaded(device: str) -> None:
  """The 'preloaded' function has the small steps' kernels ready on
  'device' (compiled, or loaded from Warp's cache) at every block size a
  world launches them at, each built apart: on a GPU one block of
  'THREADS' (a call's steps in one launch) and Warp's own (the spread
  path's parts, the crowds'); on the CPU one thread. (Loaded at Warp's
  own alone, the walk window's first frame built the whole kernel again
  for its block: a minute's hang on the GPU.)"""
  import warp as wp
  kernels = _kernelsOf()
  if device == 'cpu':
    wp.load_module(kernels, device, False, 1)
    return
  wp.load_module(kernels, device, False, THREADS)
  wp.load_module(kernels, device, False, None)


class SmallSteps(NamedTuple):
  """
  SmallSteps is a world stepped as GPUs step games' (extended position
  based dynamics in small steps, '_small_steps_kernels'): 'gravity',
  m/s²; the ground (only its 'grip' counts: it is rigid; level, or its
  'terrain''s heights, bilinear, as the springs' world has them: the
  oval's banking, user, 2026-11-15; its 'wall' not yet), or None for
  none; steps no longer than 'step' s; 'passes' over the touches a
  step; 'grease', m, how far each skin point is shaken at random as it
  is looked for in another body, and each ball's middle in a turned
  solid (its depth alone: 'found'), each pass, nought for none (user,
  2026-11-13: "what about a some stochastic noise grease? some
  yoloD-40?"; tried on five blocks stacked true, edge on edge, which
  sank each into the one under it: shaken by a micrometre they sank
  alike; the cure was the face a point went in through ('faceFor'),
  and then a micrometre's shaking threw that tower down, so none by
  default; a micrometre breaks the fight of the rear hub's balls, each
  at nought on both raceways: 'HUB_GREASE'); on 'device', Warp's 'cpu'
  (one thread) or 'cuda' (a GPU, 'threads' side by side in one block,
  'THREADS' by default: the bearing's 3125 touches on one of the GPU's
  multiprocessors, 0.69 s of computing a simulated second against one
  CPU thread's 1.02); on a GPU
  'spread' (by default) over the whole of it instead: each part of a
  step a kernel of its own, a thread for each body, touch, link or
  motor, a step's launches captured once as a CUDA graph and replayed
  each step (user: "speed first, let's go!"); the road's texture as the
  tyres feel it (user, 2026-11-14: "the tyre effect is one that is
  decidedly chaotic ... not greasy noise exactly"): their grip varying
  along the road by 'roughness' (its spread, a share; nought: smooth),
  smooth over 'grain' m, seeded 'texture' (the same seed, the same
  road; a turntable's texture turning with it); and, 'profiled', each
  call's steps timed part by part in one block ('profileOf': cycles a
  part, a GPU's own count; the spread path is not). Touches are rigid: a
  contact's stiffness and damping do not count, its grip does (holding
  where it can, sliding
  where it cannot: Coulomb), and nothing bounces. A stack holds its
  weight sunk a little, as much as its steps' length squared (each
  touch fixing its own depth, its bodies' masses split among the rules
  pressing them; a body pressed on what holds still giving not at all
  to a push back into it: the twisted tower's top block, five oak
  blocks up, 54 um at 0.25 ms; settled, not creeping); over-relaxing
  let a rolling ball slip and jump off its ramp.
  """

  gravity: Vector = (0.0, 0.0, -9.81)
  ground: Ground = None
  step: float = 2.5e-4
  passes: int = 1
  grease: float = 0.0
  device: str = 'cpu'
  threads: int = THREADS
  spread: bool = True
  roughness: float = 0.0
  grain: float = 0.05
  texture: int = 0
  profiled: bool = False

  def advancedAll(self, assembly: Assembly, states: tuple[State, ...],
                  seconds: float, start: float = 0.0) -> tuple[State, ...]:
    """The 'advancedAll' method returns the bodies of 'assembly'
    'seconds' on from 'states' (at time 'start', which nothing here
    hangs on yet), in steps alike, none longer than 'step'."""
    if seconds <= 0.0:
      return tuple(states)
    count = max(1, math.ceil(seconds / self.step - 1e-9))
    packed = _packedOf(self, assembly, states)
    packed.load(states)
    packed.drive(assembly, seconds)
    kernels = _kernelsOf()
    run = packed.run
    run.count, run.h = count, seconds / count
    run.seed = round(start / run.h) % 2147483647
    run.profiling = 1 if self.profiled else 0
    packed.crowded(seconds)
    if self.device != 'cpu' and self.spread:
      packed.replayed(count, run.h, run.seed)
      return packed.states()
    threads = 1 if self.device == 'cpu' else self.threads
    run.threads = threads
    import warp as wp
    wp.launch(kernels.stepsRun, threads, [run, packed.bodies,
                                          packed.shapes, packed.touches,
                                          packed.links, packed.motors,
                                          packed.chains, packed.airs,
                                          packed.brakes, packed.hinges,
                                          packed.lines, packed.turns,
                                          packed.gears, packed.train],
              [], [], [], self.device, None, False, True, False, 0,
              threads)
    return packed.states()

  def profileOf(self, assembly: Assembly) -> dict[str, int]:
    """The 'profileOf' method returns how long each part of a step took
    in the calls since it was last asked ('profiled' calls in one block:
    cycles of the device's clock, by 'PROFILE_PARTS'; after a barrier,
    the slowest thread's), and starts counting anew (nothing before it
    has been stepped)."""
    for kept, packed in _PACKED:
      if kept[0] is assembly and kept[1] == self:
        counted = packed.run.profile.numpy().copy()
        packed.run.profile.zero_()
        return {name: int(cycles) for name, cycles in zip(
          _kernelsOf().PROFILE_PARTS, counted)}
    return {}

  def pressuresOf(self, assembly: Assembly) -> tuple[float, ...]:
    """The 'pressuresOf' method returns the pressure of each air of
    'assembly' over the outside's, Pa, as last stepped in this world
    (none before it has been)."""
    for kept, packed in _PACKED:
      if kept[0] is assembly and kept[1] == self:
        return packed.pressures()
    return ()


  def tyreForcesOf(self, assembly: Assembly) -> tuple[Vector, ...]:
    """The 'tyreForcesOf' method returns the force on each tyre's wheel
    of 'assembly' from what it rolls on (the ground, a turntable), N, in
    the world, as the last call in this world had it on average: its
    load and its grip's pull (none before it has been stepped)."""
    for kept, packed in _PACKED:
      if kept[0] is assembly and kept[1] == self:
        return packed.tyreForces()
    return ()

  def turnsOf(self, assembly: Assembly) -> tuple[float, ...]:
    """The 'turnsOf' method returns how far each fourth wall point that
    turns of 'assembly' has turned its body on its holder since built,
    rad, as last stepped in this world (none before it has been)."""
    for kept, packed in _PACKED:
      if kept[0] is assembly and kept[1] == self:
        return packed.turned()
    return ()


#  The last few assemblies packed, each with the world it was packed
#  for.
_PACKED: list = []


def _packedOf(world: SmallSteps, assembly: Assembly,
              states: tuple[State, ...]) -> _Packed:
  """Returns 'assembly' packed for 'world', packed anew only when it
  was not lately (its origin where its bodies first were)."""
  for kept, packed in _PACKED:
    if kept[0] is assembly and kept[1] == world:
      return packed
  packed = _Packed(world, assembly, states)
  _PACKED.insert(0, ((assembly, world), packed))
  del _PACKED[4:]
  return packed


class _Packed:
  """An assembly's bodies, shapes, touches, links and motors as the
  kernel takes them, on the world's device: places from 'origin' (the
  middle of where its bodies first were), turns from their principal
  axes."""

  def __init__(self, world: SmallSteps, assembly: Assembly,
               states: tuple[State, ...]) -> None:
    import warp as wp
    kernels = _kernelsOf()
    self.wp, self.device = wp, world.device
    _refused(assembly)
    bodies = assembly.bodies
    count = len(bodies)
    self.origin = tuple(sum(state.place[i] for state in states) / count
                        for i in range(3))
    self.axes, self.centres = [], []
    fixed = assembly.fixed
    give, turnGive, radius = [], [], []
    pieceFirst, pieceCount, reach, rollers = [], [], [], []
    turns, centres, profileFirst, profileCount, bounds = [], [], [], [], []
    shapes = _ShapeData()
    movers = []
    for index, body in enumerate(bodies):
      moments, axes = body.principal()
      self.axes.append(axes)
      self.centres.append(body.centre)
      mover = SimpleNamespace(body=body, axes=axes)
      movers.append(mover)
      still = index in fixed
      give.append(0.0 if still else 1.0 / body.mass)
      turnGive.append((0.0, 0.0, 0.0) if still else tuple(
        1.0 / moment for moment in moments))
      ball = isinstance(body.shape, Sphere)
      radius.append(body.shape.radius if ball else 0.0)
      turned = isinstance(body.shape, Turned)
      first = shapes.pieceCount()
      if body.shape is not None and not ball and not turned:
        shapes.addPieces(piecesOf(mover)[0])
      pieceFirst.append(first)
      pieceCount.append(shapes.pieceCount() - first)
      reach.append(reachOf(body))
      rollers.append(rollerOf(body.shape) or (0.0, 0.0))
      w, x, y, z = axes
      turns.append((x, y, z, w))
      centres.append(body.centre)
      profileFirst.append(len(shapes.profileKind))
      if turned:
        shapes.addProfile(body.shape.profile)
        bounds.append(body.shape.bounds())
      else:
        bounds.append((0.0, 0.0, 0.0, 0.0))
      profileCount.append(len(shapes.profileKind) - profileFirst[-1])
    margin = GRID_MARGIN + max(
      [body.shape.radius for body in bodies
       if isinstance(body.shape, Sphere)]
      + [tyre.radius for tyre in assembly.tyres] + [0.0])
    grids = [shapes.addGrid(first, count, margin)
             if count >= GRID_FROM else (-1, (0.0, 0.0, 0.0), (1, 1, 1),
                                         1.0)
             for first, count in zip(pieceFirst, pieceCount)]
    touches = _touchesOf(world, assembly, movers, shapes, states,
                         profileFirst)
    rooms = []
    for crowd in assembly.crowds:
      rooms.append((len(touches), crowd.room))
      touches.extend([(int(kernels.NO_TOUCH), 0, -1, -1, crowd.grip)]
                     * crowd.room)
    self.count = count
    b = kernels.Bodies()
    b.place = wp.zeros(count, wp.vec3, self.device)
    b.shift = wp.zeros(count, wp.vec3, self.device)
    b.turn = wp.zeros(count, wp.quat, self.device)
    b.velocity = wp.zeros(count, wp.vec3, self.device)
    b.spin = wp.zeros(count, wp.vec3, self.device)
    b.shiftBefore = wp.zeros(count, wp.vec3, self.device)
    b.turnBefore = wp.zeros(count, wp.quat, self.device)
    b.give = self.array(give, wp.float32, 0.0)
    b.turnGive = self.array(turnGive, wp.vec3, (0.0, 0.0, 0.0))
    b.radius = self.array(radius, wp.float32, 0.0)
    b.pieceFirst = self.array(pieceFirst, wp.int32, 0)
    b.pieceCount = self.array(pieceCount, wp.int32, 0)
    b.gridFirst = self.array([grid[0] for grid in grids], wp.int32, -1)
    b.gridLow = self.array([grid[1] for grid in grids], wp.vec3,
                           (0.0, 0.0, 0.0))
    b.gridDims = self.array([grid[2] for grid in grids], wp.vec3i,
                            (1, 1, 1))
    b.gridCell = self.array([grid[3] for grid in grids], wp.float32, 1.0)
    b.reach = self.array(reach, wp.float32, 0.0)
    b.roller = self.array(rollers, wp.vec2, (0.0, 0.0))
    b.axes = self.array(turns, wp.quat, (0.0, 0.0, 0.0, 1.0))
    b.centre = self.array(centres, wp.vec3, (0.0, 0.0, 0.0))
    b.profileFirst = self.array(profileFirst, wp.int32, 0)
    b.profileCount = self.array(profileCount, wp.int32, 0)
    b.bounds = self.array(bounds, wp.vec4, (0.0, 0.0, 0.0, 0.0))
    rotorOf, held = [-1] * count, [0] * count
    for index, motor in enumerate(assembly.motors):
      rotorOf[motor.second] = index
    for link in list(assembly.ties) + list(assembly.actuators):
      for end in (link.first, link.second):
        if end is not None and end not in fixed:
          held[end] += 1
    for hinge in assembly.hinges:
      rules = 3 if hinge.bush is None or hinge.bush.twist <= 0.0 else 4
      for end in (hinge.first, hinge.second):
        if end is not None and end not in fixed:
          held[end] += rules
    for link, rules in ([(slide, 2) for slide in assembly.slides]
                        + [(line, 1) for line in assembly.springs]
                        + [(line, 1) for line in assembly.dampers]):
      for end in (link.first, link.second):
        if end is not None and end not in fixed:
          held[end] += rules
    for ends in ([(point.body, point.holder)
                  for point in assembly.turnPoints]
                 + [(gear.pinion, gear.rack, gear.housing)
                    for gear in assembly.racks]):
      for end in ends:
        if end is not None and end not in fixed:
          held[end] += 1
    b.rotorOf = self.array(rotorOf, wp.int32, -1)
    b.linkCount = self.array(held, wp.int32, 0)
    b.dampCount = self.array(_dampsOf(assembly, count), wp.int32, 0)
    b.settled = wp.zeros(count, wp.int32, self.device)
    b.twist = wp.zeros(count, wp.vec3, self.device)
    for name in ('backing', 'backed'):
      setattr(b, name, wp.zeros(count, wp.vec3, self.device))
    for name in ('backs', 'backsLast'):
      setattr(b, name, wp.zeros(count, wp.int32, self.device))
    for name in ('carried', 'carriedLast'):
      setattr(b, name, wp.zeros(count, wp.float32, self.device))
    b.moved = wp.zeros(count, wp.vec3, self.device)
    b.turned = wp.zeros(count, wp.vec3, self.device)
    b.asked = wp.zeros(count, wp.int32, self.device)
    self.bodies = b
    self.shapes = shapes.packed(self, kernels.Shapes())
    t = kernels.Touches()
    size = len(touches)
    t.kind = self.array([touch[0] for touch in touches], wp.int32, 0)
    t.first = self.array([touch[1] for touch in touches], wp.int32, 0)
    t.second = self.array([touch[2] for touch in touches], wp.int32, 0)
    t.point = self.array([touch[3] for touch in touches], wp.int32, 0)
    t.piece = self.array([touch[5] if len(touch) > 5 else -1
                          for touch in touches], wp.int32, -1)
    t.grip = self.array([touch[4] for touch in touches], wp.float32, 0.0)
    for name in ('normal', 'firstArm', 'secondArm'):
      setattr(t, name, wp.zeros(max(1, size), wp.vec3, self.device))
    t.depth = wp.zeros(max(1, size), wp.float32, self.device)
    t.pushed = wp.zeros(max(1, size), wp.float32, self.device)
    t.gripped = wp.zeros(max(1, size), wp.float32, self.device)
    t.face = self.array([-1] * size, wp.int32, -1)

    def extra(at: int, blank: object) -> list:
      """Returns each touch's field 'at' (a tyre's), 'blank' where it
      has none."""
      return [touch[at] if len(touch) > at else blank for touch in touches]

    zero = (0.0, 0.0, 0.0)
    t.reach = self.array(extra(6, 0.0), wp.float32, 0.0)
    t.hub = self.array(extra(7, zero), wp.vec3, zero)
    t.axle = self.array(extra(8, zero), wp.vec3, zero)
    t.soft = self.array(extra(9, 0.0), wp.float32, 0.0)
    t.lag = self.array(extra(10, 0.0), wp.float32, 0.0)
    t.roll = self.array(extra(11, (0.0, 0.0)), wp.vec2, (0.0, 0.0))
    t.impulse = wp.zeros(max(1, size), wp.vec3, self.device)
    t.stretch = wp.zeros(max(1, size), wp.vec3, self.device)
    t.twist = wp.zeros(max(1, size), wp.float32, self.device)
    t.near = self.array([1] * size, wp.int32, 1)
    t.nearList = self.array(list(range(size)), wp.int32, 0)
    t.nearCount = self.array([size], wp.int32, 0)
    self.touches = t
    rolling = (int(kernels.WHEEL_GROUND), int(kernels.WHEEL_TURNED),
               int(kernels.WHEEL_PIECES))
    self.tyreTouches = tuple(
      [i for i, touch in enumerate(touches)
       if touch[0] in rolling and touch[1] == tyre.body]
      for tyre in assembly.tyres)
    self.seconds = 0.0
    links = _linksOf(assembly, movers, self.origin)
    linked = kernels.Links()
    zero = (0.0, 0.0, 0.0)
    linked.kind = self.array([link[0] for link in links], wp.int32, 0)
    linked.first = self.array([link[1] for link in links], wp.int32, 0)
    linked.second = self.array([link[2] for link in links], wp.int32, 0)
    linked.firstArm = self.array([link[3] for link in links], wp.vec3, zero)
    linked.secondArm = self.array([link[4] for link in links], wp.vec3, zero)
    linked.length = self.array([link[5] for link in links], wp.float32, 0.0)
    self.links = linked
    motors = assembly.motors
    m = kernels.Motors()
    m.rotor = self.array([motor.second for motor in motors], wp.int32, 0)
    m.housing = self.array([-1 if motor.first is None else motor.first
                            for motor in motors], wp.int32, -1)
    m.along = self.array([applied(transposed(matrixOf(
      movers[motor.second].axes)), motor.axis) for motor in motors],
      wp.vec3, zero)
    for name in ('torque', 'damping', 'most'):
      setattr(m, name, wp.zeros(max(1, len(motors)), wp.float32,
                                self.device))
    self.motors = m
    self.crowd, self.grid = _crowdsOf(self, assembly, rooms), None
    self.crowdBalls = sum(len(group) for crowd in assembly.crowds
                          for group in crowd.groups)
    self.crowdSlots = sum(room for _, room in rooms)
    self.crowdCount = len(rooms)
    if self.crowd is not None:
      widest = max(bodies[k].shape.radius for crowd in assembly.crowds
                   for group in crowd.groups for k in group)
      self.crowdCell = max(CROWD_CELL, 4.0 * widest)
      self.grid = wp.HashGrid(64, 64, 64, self.device)
    self.axesArray = numpy.array(self.axes, numpy.float64)
    self.backArray = self.axesArray * numpy.array((1.0, -1.0, -1.0, -1.0))
    self.lastStates, self.mirrors = None, None
    self.chains, colors = _chainsOf(self, assembly, movers)
    self.airs, faces = _airsOf(self, assembly, movers)
    self.brakes = _brakesOf(self, assembly, movers)
    self.hinges = _hingesOf(self, assembly, movers, states)
    self.lines = _linesOf(self, assembly, movers)
    self.rams = len(assembly.rams)
    self.turns = _turnsOf(self, assembly, movers)
    self.asked = None
    self.gears = _gearsOf(self, assembly, movers, states)
    self.train, pairs = _trainOf(self, assembly)
    run = kernels.Run()
    run.passes = world.passes
    run.gravity = wp.vec3(*world.gravity)
    run.floor = -self.origin[2]
    run.grease = world.grease
    run.rough, run.grain = world.roughness, world.grain
    run.texture = world.texture
    run.bodies = count
    run.touches = size
    run.links = len(links)
    run.motors = len(motors)
    run.colors = len(colors)
    run.airs = len(assembly.airs)
    run.faces = faces
    run.brakes = len(assembly.brakes)
    run.hinges = len(assembly.hinges) + len(assembly.slides)
    run.lines = (len(assembly.springs) + len(assembly.dampers)
                 + len(assembly.rams))
    run.turns = len(assembly.turnPoints)
    run.gears = len(assembly.racks) + len(assembly.meshes)
    run.racks = len(assembly.racks)
    run.pairs = pairs
    run.profiling = 0
    run.profile = wp.zeros(len(kernels.PROFILE_PARTS), wp.int64,
                           self.device)
    self.terrained(world.ground, run)
    self.walled(world.ground, run)
    self.colors = colors
    run.motorsMerged = 1 if all(
      motor.first is None or motor.first in fixed
      for motor in motors) else 0
    self.run = run
    self.clock = wp.zeros(1, wp.float32, self.device)
    self.ticks = wp.zeros(1, wp.int32, self.device)
    self.graph, self.chunk = None, None
    self.hosts = {}

  def terrained(self, ground: Ground | None, run: object) -> None:
    """Puts the terrain of 'ground' (if it has one) in 'run' as the
    kernel takes it ('groundAt'): its grid's first corner from the
    origin, its cell, its points' count along x and y, their heights
    from the origin in float32 (a row along y for each x), how much its
    slope changes about each cell ('_bendsOf') and at most; none, level,
    without one."""
    wp = self.wp
    terrain = None if ground is None else ground.terrain
    if terrain is None:
      run.terrain, run.terrainCell = 0, 1.0
      run.terrainAt = wp.vec2(0.0, 0.0)
      run.terrainNx, run.terrainNy, run.terrainBend = 0, 0, 0.0
      run.heights = wp.zeros(1, float, self.device)
      run.bends = wp.zeros(1, float, self.device)
      return
    from ._terrain import _gridOf
    grid = _gridOf(terrain)
    run.terrain, run.terrainCell = 1, float(terrain.cell)
    run.terrainAt = wp.vec2(terrain.origin[0] - self.origin[0],
                            terrain.origin[1] - self.origin[1])
    run.terrainNx, run.terrainNy = int(grid.shape[0]), int(grid.shape[1])
    bends = _bendsOf(grid, float(terrain.cell))
    run.terrainBend = float(bends.max())
    run.bends = wp.array(bends.astype(numpy.float32).ravel(), float, None,
                         None, None, None, self.device)
    run.heights = wp.array((grid - self.origin[2]).astype(
      numpy.float32).ravel(), float, None, None, None, None, self.device)

  def walled(self, ground: Ground | None, run: object) -> None:
    """Puts the oval's safety barrier of 'ground' (if it has one) in
    'run' as the kernel takes it ('wallBeyond'): the oval's middle from
    the origin, its straights' half length, its turns' radius, how far
    out the barrier's face stands, how tall it is."""
    wall = None if ground is None else ground.wall
    run.wall = 0 if wall is None else 1
    run.wallAt = self.wp.vec2(-self.origin[0], -self.origin[1])
    run.wallHalf, run.wallRadius, run.wallOut, run.wallHeight = (
      (0.0, 0.0, 0.0, 0.0) if wall is None else (
        float(wall.half), float(wall.radius), float(wall.out),
        float(wall.height)))

  def hostOf(self, array: object) -> object:
    """Returns the host memory kept for 'array' (on a GPU), pinned, as
    large and of the same kind, made the first time."""
    kept = self.hosts.get(id(array))
    if kept is None or kept[0] is not array:
      kept = (array, self.wp.empty_like(array, 'cpu', False, True))
      self.hosts[id(array)] = kept
    return kept[1]

  def hostCopies(self, arrays: tuple) -> tuple:
    """Returns 'arrays' (on the device) as numpy arrays of their own: on
    the CPU copied from where they lie; on a GPU each copied into the
    host memory kept for it ('hostOf'), all queued, then waited for once
    (each Warp array's 'numpy' made host memory, copied and waited, and
    every call into the GPU's driver lets Python's lock go: see
    '_walk.SWITCH_INTERVAL')."""
    if self.device == 'cpu':
      return tuple(array.numpy().copy() for array in arrays)
    wp = self.wp
    hosts = tuple(self.hostOf(array) for array in arrays)
    for host, array in zip(hosts, arrays):
      wp.copy(host, array)
    wp.synchronize_device(self.device)
    return tuple(host.numpy().copy() for host in hosts)

  def sent(self, array: object, values: numpy.ndarray) -> None:
    """Puts 'values' (float32, one a slot) in the first slots of
    'array' on the device: on a GPU through the host memory kept for it
    ('hostOf'), queued, not waited for (the step launched next comes
    after it; the host memory is written again only after the call's
    states were waited for)."""
    if self.device == 'cpu':
      array.assign(values)
      return
    host = self.hostOf(array)
    host.numpy()[:len(values)] = values
    self.wp.copy(array, host, 0, 0, len(values))

  def array(self, values: list, dtype, blank) -> object:
    """Returns 'values' as a Warp array of 'dtype' on the device (a
    single 'blank' when there are none: Warp takes no empty arrays)."""
    return self.wp.array(values if values else [blank], dtype, None, None,
                         None, None, self.device)

  def load(self, states: tuple[State, ...]) -> None:
    """Puts 'states' on the device: places from the origin (in float32,
    and what that rounds off as the shift), turns from the principal
    axes (as Warp's x y z w), velocities and spins. Only the states not
    as last handed back ('states': the same objects) are worked out
    anew (a walker's world changes its walker and what it holds; its
    hundreds of other bodies are on the device as they are)."""
    last, mirrors = self.lastStates, self.mirrors
    which = range(len(states))
    if last is not None and len(last) == len(states):
      which = [k for k in which if states[k] is not last[k]]
      if not which:
        return
    else:
      mirrors = tuple(numpy.empty((len(states), size), numpy.float32)
                      for size in (3, 3, 4, 3, 3))
    place, shift, turn, velocity, spin = mirrors
    which = numpy.fromiter(which, numpy.int64)
    given = [states[k] for k in which]
    exact = numpy.array([state.place for state in given],
                        numpy.float64) - numpy.array(self.origin)
    rounded = exact.astype(numpy.float32)
    place[which] = rounded
    shift[which] = (exact - rounded.astype(numpy.float64)).astype(
      numpy.float32)
    turned = _products(numpy.array([state.turn for state in given],
                                   numpy.float64), self.axesArray[which])
    turn[which] = turned[:, (1, 2, 3, 0)]
    velocity[which] = [state.velocity for state in given]
    spin[which] = [state.spin for state in given]
    b = self.bodies
    for array, values in zip((b.place, b.shift, b.turn, b.velocity,
                              b.spin), mirrors):
      array.assign(values)
    self.mirrors, self.lastStates = mirrors, None

  def crowded(self, seconds: float) -> None:
    """Fills each crowd's room, on the device, with the touches of its
    balls that could meet in the next 'seconds' (any two of different
    groups whose gap is no more than they could close going as fast as
    they go, and 'CROWD_MARGIN'; as many as there is room for), the rest
    of its room touching nothing: its balls gathered where they are
    ('crowdGather'), a hash grid built over them, each ball's near ones
    looked up in it ('crowdPairs'). Nothing comes back to the host (a
    k-d tree a group on the host took 10 ms a call for two tyres)."""
    if self.crowd is None:
      return
    wp, kernels, device = self.wp, _kernelsOf(), self.device
    wp.launch(kernels.crowdReset, max(self.crowdSlots, self.crowdCount),
              [self.crowd, self.touches, self.crowdSlots,
               self.crowdCount], [], [], [], device)
    wp.launch(kernels.crowdGather, self.crowdBalls,
              [self.bodies, self.crowd], [], [], [], device)
    self.grid.build(self.crowd.points, self.crowdCell)
    wp.launch(kernels.crowdPairs, self.crowdBalls,
              [self.crowd, self.touches, self.grid.id, seconds,
               CROWD_MARGIN], [], [], [], device)

  def pressures(self, ) -> tuple[float, ...]:
    """Returns each air's pressure over the outside's, Pa, by its volume
    as last summed."""
    if self.run.airs == 0:
      return ()
    gas, volume = self.hostCopies((self.airs.gas, self.airs.volume))
    return tuple(float(g) / float(v) - ATMOSPHERE if v > 0.0 else 0.0
                 for g, v in zip(gas[:self.run.airs], volume))

  def tyreForces(self, ) -> tuple[Vector, ...]:
    """Returns the mean force on each tyre's wheel from what it rolls
    on over the last call, N, from its touches' sums ('impulse')."""
    if not self.tyreTouches or self.seconds <= 0.0:
      return ()
    impulse = self.hostCopies((self.touches.impulse,))[0].astype(
      numpy.float64)
    return tuple(tuple(float(x) / self.seconds
                       for x in impulse[indices].sum(axis=0))
                 if indices else (0.0, 0.0, 0.0)
                 for indices in self.tyreTouches)

  def turned(self, ) -> tuple[float, ...]:
    """Returns how far each fourth wall point that turns has turned its
    body on its holder, rad, as counted on the device."""
    if self.run.turns == 0:
      return ()
    angles = self.hostCopies((self.turns.angle,))[0]
    return tuple(float(angle) for angle in angles[:self.run.turns])

  def replayed(self, count: int, h: float, seed: int) -> None:
    """Steps the bodies on the device 'count' steps of 'h' s, the
    first numbered 'seed', spread over the whole GPU: 'GRAPH_STEPS'
    steps' launches captured as one CUDA graph the first time (and one
    step's, for what is left over), replayed (a frame's 133 steps one
    graph each, every replay asked for from Python)."""
    wp = self.wp
    self.clock.assign(numpy.array([h], numpy.float32))
    self.ticks.assign(numpy.array([seed], numpy.int32))
    if self.graph is None:
      for steps in (1, GRAPH_STEPS):
        wp.capture_begin(self.device)
        try:
          for step in range(steps):
            self.launchStep(steps if step == 0 else 0)
        finally:
          graph = wp.capture_end(self.device)
        if steps == 1:
          self.graph = graph
        else:
          self.chunk = graph
    for _ in range(count // GRAPH_STEPS):
      wp.capture_launch(self.chunk)
    for _ in range(count % GRAPH_STEPS):
      wp.capture_launch(self.graph)

  def launchStep(self, near: int) -> None:
    """Launches one step's parts in order, each over as many threads as
    it has bodies, touches, links, motors, faces of air or cord lines
    of a colour; first, if 'near' (a number of steps), which touches on
    the ground could reach it in that many ('nearPart')."""
    wp, kernels, device = self.wp, _kernelsOf(), self.device
    run, b, s, t = self.run, self.bodies, self.shapes, self.touches
    links, m = self.links, self.motors

    def go(kernel: object, dim: int, inputs: list) -> None:
      """Launches 'kernel' over 'dim' threads, if any."""
      if dim > 0:
        wp.launch(kernel, dim, inputs, [], [], [], device)

    if near > 0:
      go(kernels.nearResetPart, 1, [t])
      go(kernels.nearPart, run.touches, [run, b, s, t, self.clock, near])
    if run.airs > 0:
      go(kernels.airZeroPart, run.airs, [self.airs])
      go(kernels.airVolumePart, run.faces, [b, self.airs])
      go(kernels.airPushPart, run.faces, [b, self.airs, self.clock])
    if not run.motorsMerged:
      go(kernels.motorsPart, run.motors, [b, m, self.clock])
    if self.rams:
      go(kernels.linePushPart, run.lines, [b, self.lines, self.clock])
    go(kernels.movePart, max(run.bodies, run.touches),
       [run, b, t, m, self.clock])
    for p in range(run.passes):
      go(kernels.countPart, run.touches, [run, b, s, t, self.ticks, p])
      go(kernels.pushPart, run.touches, [b, t, self.clock])
      go(kernels.takeTouchMovesPart, run.bodies, [b])
      if (run.links > 0 or run.hinges > 0 or run.lines > 0
          or run.turns > 0 or run.gears > 0):
        go(kernels.holdPart, run.links, [b, links])
        go(kernels.hingePart, run.hinges, [run, b, self.hinges, self.ticks,
                                           self.clock, p])
        go(kernels.linePart, run.lines, [run, b, self.lines, self.ticks,
                                         self.clock, p])
        go(kernels.turnPart, run.turns, [b, self.turns, self.clock])
        go(kernels.gearPart, run.gears, [run, b, self.gears, self.ticks,
                                         self.clock, p])
        go(kernels.takeMovesPart, run.bodies, [b])
      for start, size in self.colors:
        go(kernels.chainPart, size, [b, self.chains, start, self.clock])
        go(kernels.takeMovesPart, run.bodies, [b])
      rules = run.gears - run.racks + run.brakes
      if rules > 0:
        tr = self.train
        go(kernels.trainRulePart, rules * rules,
           [run, b, self.gears, self.brakes, tr, self.ticks, self.clock, p])
        go(kernels.trainPairPart, run.pairs, [run, tr])
        go(kernels.trainSolvePart, int(kernels.TRAIN_LANES),
           [run, self.brakes, tr])
        go(kernels.trainMovesPart, rules, [tr])
        go(kernels.trainTurnedPart, run.bodies, [b, tr])
    go(kernels.velocitiesPart, run.bodies, [b, self.clock])
    go(kernels.settlePart, run.touches, [run, b, t, self.clock])
    go(kernels.takeKicksPart, run.bodies, [b, self.ticks])
    if (run.brakes > 0 or run.hinges > 0 or run.lines > 0
        or run.turns > 0 or run.gears > 0):
      go(kernels.brakeSettlePart, run.brakes, [b, self.brakes,
                                               self.clock])
      rounds = int(kernels.DAMP_ROUNDS)
      go(kernels.hingeSettlePart, run.hinges, [b, self.hinges,
                                               self.clock, rounds])
      go(kernels.lineSettlePart, run.lines, [b, self.lines, self.clock,
                                             rounds])
      go(kernels.turnSettlePart, max(run.turns, run.gears),
         [b, self.turns, self.gears, run.turns, run.gears, self.clock])
      go(kernels.brakeKicksPart, run.bodies, [b])
      if run.hinges > 0 or run.lines > 0:
        for _ in range(rounds - 1):
          go(kernels.hingeSettlePart, run.hinges, [b, self.hinges,
                                                   self.clock, rounds])
          go(kernels.lineSettlePart, run.lines, [b, self.lines,
                                                 self.clock, rounds])
          go(kernels.brakeKicksPart, run.bodies, [b])

  def drive(self, assembly: Assembly, seconds: float) -> None:
    """Puts the motors' drives, the brakes' lines, the rams' pushes,
    the humps bolted on and the fourth wall points' asks on the device
    as they are set now, for a call of 'seconds' (an ask's rate: how far
    it moved since the last call, over that; a servo's stiffness
    refused); the tyres' sums of what pushed them forgotten."""
    self.seconds = seconds
    if assembly.tyres:
      self.touches.impulse.zero_()
    if assembly.rams:
      self.sent(self.lines.push, numpy.array(
        [0.0] * (len(assembly.springs) + len(assembly.dampers))
        + [ram.wall.value for ram in assembly.rams], numpy.float32))
    if assembly.humps:
      humps, spans = _humpsOf(assembly)
      self.shapes.hump.assign(humps)
      self.shapes.humpSpan.assign(spans)
    if assembly.brakes:
      self.sent(self.brakes.force, numpy.array(
        [brake.force() for brake in assembly.brakes], numpy.float32))
    if assembly.turnPoints:
      asked = numpy.array([point.wall.value
                           for point in assembly.turnPoints], numpy.float64)
      last = asked if self.asked is None else self.asked
      self.sent(self.turns.target, asked.astype(numpy.float32))
      self.sent(self.turns.rate, ((asked - last) / seconds).astype(
        numpy.float32))
      self.asked = asked
    motors = assembly.motors
    if not motors:
      return
    for motor in motors:
      if motor.drive.stiffness != 0.0:
        raise ValueError('servos are not in the small steps yet')
    m = self.motors
    self.sent(m.torque, numpy.array([motor.drive.torque
                                     for motor in motors], numpy.float32))
    self.sent(m.damping, numpy.array([motor.drive.damping
                                      for motor in motors], numpy.float32))
    self.sent(m.most, numpy.array([motor.drive.most for motor in motors],
                                  numpy.float32))

  def states(self, ) -> tuple[State, ...]:
    """Returns the bodies as the device has them now (worked out all at
    once, as the one at a time did to the bit), noting them as handed
    back ('load')."""
    b = self.bodies
    mirrors = self.hostCopies((b.place, b.shift, b.turn, b.velocity,
                               b.spin))
    place, shift, turn, velocity, spin = mirrors
    places = numpy.array(self.origin) + (place.astype(numpy.float64)
                                         + shift.astype(numpy.float64))
    turns = _products(turn[:, (3, 0, 1, 2)].astype(numpy.float64),
                      self.backArray)
    out = tuple(State(tuple(at), tuple(turned), tuple(moving),
                      tuple(spun)) for at, turned, moving, spun in zip(
      places.tolist(), turns.tolist(),
      velocity.astype(numpy.float64).tolist(),
      spin.astype(numpy.float64).tolist()))
    self.mirrors, self.lastStates = mirrors, out
    return out


class _ShapeData:
  """The shapes' skin points and pieces gathered as the kernel takes
  them."""

  def __init__(self, ) -> None:
    self.arms, self.skins = [], {}
    self.planeFirst, self.planeCount = [], []
    self.triangleFirst, self.triangleCount = [], []
    self.low, self.high, self.box = [], [], []
    self.facing, self.offset, self.corners = [], [], []
    self.planePiece = []
    self.profileKind, self.profileA, self.profileB = [], [], []
    self.cellFirst, self.cellCount, self.cellPieces = [], [], []

  def pieceCount(self, ) -> int:
    """Returns how many pieces there are so far."""
    return len(self.planeFirst)

  def addPieces(self, pieces: tuple) -> None:
    """Adds a body's pieces ('piecesOf'): planes, the box about each,
    whether it is that box, triangles."""
    for planes, low, high, box, triangles in pieces:
      self.planeFirst.append(len(self.facing))
      self.planeCount.append(len(planes))
      for facing, offset in planes:
        self.facing.append(facing)
        self.offset.append(offset)
        self.planePiece.append(len(self.planeFirst) - 1)
      self.triangleFirst.append(len(self.corners) // 3)
      self.triangleCount.append(len(triangles))
      for triangle in triangles:
        self.corners.extend(triangle)
      self.low.append(low)
      self.high.append(high)
      self.box.append(1 if box else 0)

  def addGrid(self, first: int, count: int, margin: float) -> tuple:
    """Adds a grid over pieces 'first' on, 'count' of them (a body's,
    along its principal axes): cells 'GRID_CELL' m across (larger where
    there would be more than 'GRID_MOST'), each listing the pieces whose
    box, widened 'margin' m, reaches into it (what a point there could
    touch); returns where its cells begin, its low corner, how many
    cells along each axis and how wide a cell is."""
    lows, highs = self.low[first:first + count], self.high[first:
                                                           first + count]
    low = tuple(min(p[i] for p in lows) - margin for i in range(3))
    high = tuple(max(p[i] for p in highs) + margin for i in range(3))
    span = tuple(max(b - a, 1e-6) for a, b in zip(low, high))
    cell = max(GRID_CELL, (span[0] * span[1] * span[2] / GRID_MOST)
               ** (1.0 / 3.0))
    dims = tuple(max(1, math.ceil(x / cell)) for x in span)
    cells = [[] for _ in range(dims[0] * dims[1] * dims[2])]
    for c in range(first, first + count):
      ranges = [range(max(0, int((self.low[c][i] - margin - low[i])
                                 // cell)),
                      min(dims[i] - 1, int((self.high[c][i] + margin
                                            - low[i]) // cell)) + 1)
                for i in range(3)]
      for i in ranges[0]:
        for j in ranges[1]:
          for k in ranges[2]:
            cells[(i * dims[1] + j) * dims[2] + k].append(c)
    start = len(self.cellFirst)
    for members in cells:
      self.cellFirst.append(len(self.cellPieces))
      self.cellCount.append(len(members))
      self.cellPieces.extend(members)
    return start, low, dims, cell

  def addProfile(self, profile: tuple) -> None:
    """Adds a turned solid's profile: each line its ends (rho, w, rho,
    w), each arc its centre, radius and angles."""
    for piece in profile:
      if piece[0] == 'line':
        (r0, w0), (r1, w1) = piece[1], piece[2]
        self.profileKind.append(0)
        self.profileA.append((r0, w0, r1, w1))
        self.profileB.append((0.0, 0.0, 0.0, 0.0))
      else:
        _, (cr, cw), radius, start, end = piece
        self.profileKind.append(1)
        self.profileA.append((cr, cw, radius, 0.0))
        self.profileB.append((start, end, 0.0, 0.0))

  def skinOf(self, mover: object, points: tuple) -> list[int]:
    """Returns the indices of a body's skin 'points' (in its own frame,
    'mover' its body and axes), each along its principal axes from its
    centre, added the first time asked."""
    key = (id(mover), points)
    if key not in self.skins:
      back = transposed(matrixOf(mover.axes))
      first = len(self.arms)
      for point in points:
        self.arms.append(applied(back, minus(point, mover.body.centre)))
      self.skins[key] = list(range(first, len(self.arms)))
    return self.skins[key]

  def packed(self, owner: _Packed, shapes: object) -> object:
    """Returns 'shapes' (the kernel's) filled on 'owner's device."""
    wp, zero = owner.wp, (0.0, 0.0, 0.0)
    shapes.arm = owner.array(self.arms, wp.vec3, zero)
    shapes.planeFirst = owner.array(self.planeFirst, wp.int32, 0)
    shapes.planeCount = owner.array(self.planeCount, wp.int32, 0)
    shapes.triangleFirst = owner.array(self.triangleFirst, wp.int32, 0)
    shapes.triangleCount = owner.array(self.triangleCount, wp.int32, 0)
    shapes.low = owner.array(self.low, wp.vec3, zero)
    shapes.high = owner.array(self.high, wp.vec3, zero)
    shapes.box = owner.array(self.box, wp.int32, 0)
    shapes.facing = owner.array(self.facing, wp.vec3, zero)
    shapes.offset = owner.array(self.offset, wp.float32, 0.0)
    shapes.planePiece = owner.array(self.planePiece, wp.int32, 0)
    shapes.corner = owner.array(self.corners, wp.vec3, zero)
    shapes.profileKind = owner.array(self.profileKind, wp.int32, 0)
    shapes.profileA = owner.array(self.profileA, wp.vec4,
                                  (0.0, 0.0, 0.0, 0.0))
    shapes.profileB = owner.array(self.profileB, wp.vec4,
                                  (0.0, 0.0, 0.0, 0.0))
    shapes.hump = owner.array([(-1.0, 0.0, 0.0, 0.0)] * HUMP_ROOM,
                              wp.vec4, (-1.0, 0.0, 0.0, 0.0))
    shapes.humpSpan = owner.array([(0.0, 0.0)] * HUMP_ROOM, wp.vec2,
                                  (0.0, 0.0))
    shapes.cellFirst = owner.array(self.cellFirst, wp.int32, 0)
    shapes.cellCount = owner.array(self.cellCount, wp.int32, 0)
    shapes.cellPieces = owner.array(self.cellPieces, wp.int32, 0)
    return shapes


def _bendsOf(grid: numpy.ndarray, cell: float) -> numpy.ndarray:
  """Returns how much a terrain's slope (its heights 'grid', 'cell' m
  apart, bilinear between) changes at most within each of its cells and
  into the cells about it (a cell's value for each cell): within a cell
  its slope along x runs between those of its two edges along x (and so
  across); from one cell into the next along x it jumps from one row of
  edges' to the next (and so across); each cell then takes the most of
  the nine about it (in the near look's time a point crosses into the
  next cell at most)."""
  along = numpy.diff(grid, 1, 0) / cell
  across = numpy.diff(grid, 1, 1) / cell
  bend = numpy.maximum(numpy.abs(along[:, 1:] - along[:, :-1]),
                       numpy.abs(across[1:, :] - across[:-1, :]))
  jumps = numpy.abs(numpy.diff(along, 1, 0))
  jumps = numpy.maximum(jumps[:, 1:], jumps[:, :-1])
  bend[1:] = numpy.maximum(bend[1:], jumps)
  bend[:-1] = numpy.maximum(bend[:-1], jumps)
  jumps = numpy.abs(numpy.diff(across, 1, 1))
  jumps = numpy.maximum(jumps[1:], jumps[:-1])
  bend[:, 1:] = numpy.maximum(bend[:, 1:], jumps)
  bend[:, :-1] = numpy.maximum(bend[:, :-1], jumps)
  padded = numpy.pad(bend, 1, 'edge')
  rows, columns = bend.shape
  return numpy.max([padded[a:a + rows, c:c + columns]
                    for a in range(3) for c in range(3)], 0)


def _touchesOf(world: SmallSteps, assembly: Assembly, movers: list,
               shapes: _ShapeData, states: tuple[State, ...],
               profileFirst: list[int]) -> list[tuple]:
  """Returns the touches the kernel looks at, each (kind, first,
  second, skin point or profile piece, grip): every contact's (a ball
  against a ball or a convex shape, one; against a turned solid, one
  for each piece of its profile it could press ('_profileNear'); two
  convex shapes', every skin point of each, 'spacing' apart, against
  the other's pieces), and on the ground every free body's (a ball's,
  one; another's, its corners; a turned solid's none yet: it falls
  through the ground, which none here reaches, a shaft hanging in its
  bearings). Two turned solids meet only as a roller and a ring
  ('_turnedTouches'), or a tyred wheel and another: its tyre's springs
  on the other's wide flat faces square to its axis ('_isTable': a
  turntable's top, as on the ground), its probes on the rest; a tyred
  wheel and a convex shape (a track of planks) by its tyre's springs on
  the shape's faces ('WHEEL_PIECES'; its sidewalls' probes not yet: a
  wheel lying on a plank sinks through it); a convex shape meets a
  turned solid at its skin points near the solid's straight pieces
  ('_landTouches'); two convex shapes, the first's skin points alone if
  the contact says not 'both' (a car's chassis on a track of planks,
  the track's edges too many to count).
  """
  kernels = _kernelsOf()
  fixed = assembly.fixed
  tyres = {tyre.body: tyre for tyre in assembly.tyres}
  out = []
  for contact in assembly.contacts:
    a, b = contact.first, contact.second
    if a in fixed and b in fixed:
      continue
    roundA = isinstance(movers[a].body.shape, Sphere)
    roundB = isinstance(movers[b].body.shape, Sphere)
    turnedA = isinstance(movers[a].body.shape, Turned)
    turnedB = isinstance(movers[b].body.shape, Turned)
    grip = contact.grip
    if turnedA and turnedB and (a in tyres or b in tyres):
      for mine, theirs in ((a, b), (b, a)):
        if mine not in tyres:
          continue
        tyre = tyres[mine]
        probes = shapes.skinOf(movers[mine], tyre.probes)
        profile = movers[theirs].body.shape.profile
        for piece, part in enumerate(profile):
          at = profileFirst[theirs] + piece
          if _isTable(part, tyre):
            for tread in _treadsOf(tyre, movers[mine], True):
              out.append((int(kernels.WHEEL_TURNED), mine, theirs, -1,
                          grip, at, tyre.radius) + tread)
            continue
          for probe in probes:
            out.append((int(kernels.PROBE_TURNED), mine, theirs, probe,
                        grip, at, tyre.probe))
      continue
    if (turnedA and a in tyres and not (roundB or turnedB)) or (
        turnedB and b in tyres and not (roundA or turnedA)):
      wheel, track = (a, b) if turnedA else (b, a)
      tyre = tyres[wheel]
      for tread in _treadsOf(tyre, movers[wheel]):
        out.append((int(kernels.WHEEL_PIECES), wheel, track, -1, grip,
                    -1, tyre.radius) + tread)
      continue
    if turnedA and turnedB:
      out.extend(_turnedTouches(kernels, movers, states, profileFirst, a,
                                b, grip))
      continue
    if (turnedA and not roundB) or (turnedB and not roundA):
      shape, ring = (b, a) if turnedA else (a, b)
      out.extend(_landTouches(kernels, movers, states, shapes,
                              profileFirst, shape, ring, contact))
      continue
    if roundA and roundB:
      out.append((int(kernels.BALL_BALL), a, b, -1, grip))
    elif turnedA or turnedB:
      ball, other = (a, b) if roundA else (b, a)
      for piece in _profileNear(movers[ball].body, states[ball],
                                movers[other].body, states[other]):
        out.append((int(kernels.BALL_TURNED), ball, other,
                    profileFirst[other] + piece, grip))
    elif roundA or roundB:
      ball, other = (a, b) if roundA else (b, a)
      out.append((int(kernels.BALL_PIECES), ball, other, -1, grip))
    else:
      for mine, theirs in ((a, b), (b, a)) if contact.both else (
          (a, b),):
        mover = movers[mine]
        skin = tuple(point for point, _ in mover.body.shape.skin(
          contact.spacing))
        for point in shapes.skinOf(mover, skin):
          out.append((int(kernels.POINT_PIECES), mine, theirs, point,
                      grip))
  if world.ground is not None:
    for tyre in assembly.tyres:
      mover = movers[tyre.body]
      axle = applied(transposed(matrixOf(mover.axes)), tyre.axle)
      roll = (tyre.rolling * tyre.radius, tyre.scrub)
      for tread in _treadsOf(tyre, mover):
        out.append((int(kernels.WHEEL_GROUND), tyre.body, -1, -1,
                    world.ground.grip, -1, tyre.radius) + tread)
      for probe in shapes.skinOf(mover, tyre.sides):
        out.append((int(kernels.PROBE_GROUND), tyre.body, -1, probe,
                    world.ground.grip, -1, tyre.sideProbe, (0.0, 0.0, 0.0),
                    axle, 0.0, 0.0, roll))
    housed = assembly.housed
    for index, mover in enumerate(movers):
      shape = mover.body.shape
      if index in fixed or index in housed or shape is None:
        continue
      if isinstance(shape, Sphere):
        out.append((int(kernels.BALL_GROUND), index, -1, -1,
                    world.ground.grip))
        continue
      if isinstance(shape, Turned):
        continue
      for point in shapes.skinOf(mover, tuple(shape.points)):
        out.append((int(kernels.POINT_GROUND), index, -1, point,
                    world.ground.grip))
    if world.ground.wall is not None:
      out += _wallTouches(kernels, world.ground.wall, assembly, movers,
                          shapes)
  return out


def _wallTouches(kernels: object, wall: object, assembly: Assembly,
                 movers: list, shapes: '_ShapeData') -> list[tuple]:
  """Returns the touches of the bodies of 'assembly' with an oval's
  safety barrier ('wall', gripping at its 'grip'): each tyre's sidewalls'
  probes ('PROBE_WALL', as they meet the ground), each ball
  ('BALL_WALL'), each skin point of every other shape ('POINT_WALL'); not
  the bodies of the world nor those housed."""
  out = []
  for tyre in assembly.tyres:
    mover = movers[tyre.body]
    for probe in shapes.skinOf(mover, tyre.sides):
      out.append((int(kernels.PROBE_WALL), tyre.body, -1, probe, wall.grip,
                  -1, tyre.sideProbe))
  fixed, housed = assembly.fixed, assembly.housed
  for index, mover in enumerate(movers):
    shape = mover.body.shape
    if index in fixed or index in housed or shape is None:
      continue
    if isinstance(shape, Sphere):
      out.append((int(kernels.BALL_WALL), index, -1, -1, wall.grip))
      continue
    if isinstance(shape, Turned):
      continue
    for point in shapes.skinOf(mover, tuple(shape.points)):
      out.append((int(kernels.POINT_WALL), index, -1, point, wall.grip))
  return out


def _treadsOf(tyre: object, mover: object,
              middle: bool = False) -> list[tuple]:
  """Returns the springs a tyre stands on (one at its tread's middle,
  or one at either edge, each half as stiff and damped; at its middle
  alone if 'middle': on a turntable, where the deck under the edges,
  nearer and farther from its axis, runs at speeds 3 % apart, and the
  two held each to its own by its grip leaned the rig's wheel over 5.4
  degrees) as its touches take them: each the middle of its tread's
  circle and the axle (along the wheel's principal axes, the circle's
  from its centre), its softness (m/N), damping (N s/m) and what it
  loses rolling and pivoting (its arms, m)."""
  back = transposed(matrixOf(mover.axes))
  edges = ((0.0, 1.0),) if tyre.tread <= 0.0 or middle else (
    (-tyre.tread, 0.5), (tyre.tread, 0.5))
  axle = applied(back, tyre.axle)
  roll = (tyre.rolling * tyre.radius, tyre.scrub)
  out = []
  for off, share in edges:
    hub = plus(tyre.hub, tuple(off * a for a in tyre.axle))
    out.append((applied(back, minus(hub, mover.body.centre)), axle,
                1.0 / (share * tyre.stiffness), share * tyre.damping,
                roll))
  return out


def _isTable(part: tuple, tyre: object) -> bool:
  """Returns whether piece 'part' of a turned solid's profile is a
  face a tyre rolls on as on the ground: flat, square to the axis, at
  least as wide as the tyre's radius (a turntable's top; a rim's narrow
  flanges are met by its probes)."""
  if part[0] != 'line':
    return False
  (r0, w0), (r1, w1) = part[1], part[2]
  return w0 == w1 and abs(r1 - r0) >= tyre.radius


def _landTouches(kernels: object, movers: list, states: tuple,
                 shapes: _ShapeData, profileFirst: list[int], shape: int,
                 ring: int, contact: object) -> list[tuple]:
  """Returns the touches of a convex shape (body 'shape': a cage) with
  a turned solid ('ring'): each skin point of the shape ('spacing'
  apart) against each straight piece of the ring's profile, along the
  axis or across it, that faces it within 'LAND_REACH' as they start
  (a turned solid the same all round, a point keeps its distance from
  its axis and along it as the shape turns: the cage's inner face
  meets the spindle's land, its outer the hub's; the rest of its skin,
  far from either, none), each (kind, shape, ring, skin point, grip,
  piece)."""
  mover, other = movers[shape], movers[ring]
  where, at = states[ring], states[shape]
  points = tuple(point for point, _ in mover.body.shape.skin(
    contact.spacing))
  indices = shapes.skinOf(mover, points)
  profile = other.body.shape.profile
  out = []
  for point, index in zip(points, indices):
    world = mover.body.placeOf(at, point)
    own = plus(rotated(conjugate(where.turn), minus(world, where.place)),
               other.body.centre)
    rho, w = math.hypot(own[0], own[1]), own[2]
    for piece, part in enumerate(profile):
      if part[0] != 'line':
        continue
      (r0, w0), (r1, w1) = part[1], part[2]
      if abs(r1 - r0) > 1e-12 and abs(w1 - w0) > 1e-12:
        continue
      near, outward = nearestOnPiece(part, rho, w)
      ahead = (rho - near[0]) * outward[0] + (w - near[1]) * outward[1]
      if 0.0 <= ahead <= LAND_REACH and math.hypot(
          rho - near[0], w - near[1]) <= LAND_REACH:
        out.append((int(kernels.POINT_TURNED), shape, ring, index,
                    contact.grip, profileFirst[ring] + piece))
  return out


def _turnedTouches(kernels: object, movers: list, states: tuple,
                   profileFirst: list[int], a: int, b: int,
                   grip: float) -> list[tuple]:
  """Returns the touches of two turned solids, 'a' and 'b': two
  rollers', two points along them; a roller's and a ring's, two points
  for each straight piece of the ring's profile, along the axis or
  across it, that the roller could reach ('_rollerPiecesNear'). Two
  rings are refused."""
  rollerA, rollerB = rollerOf(movers[a].body.shape), rollerOf(
    movers[b].body.shape)
  if rollerA and rollerB:
    return [(int(kernels.ROLLER_ROLLER), a, b, end, grip)
            for end in (0, 1)]
  if not (rollerA or rollerB):
    raise ValueError('two turned solids meet only as a roller and a '
                     'ring so far')
  roller, ring = (a, b) if rollerA else (b, a)
  out = []
  for piece in _rollerPiecesNear(movers[roller].body, states[roller],
                                 movers[ring].body, states[ring]):
    for end in (0, 1):
      out.append((int(kernels.ROLLER_TURNED), roller, ring,
                  2 * (profileFirst[ring] + piece) + end, grip))
  return out


def _rollerPiecesNear(roller: object, at: State, ring: object,
                      where: State) -> list[int]:
  """Returns the pieces of the ring's profile (the turned solid 'ring',
  in 'where') a roller (in 'at') is let meet: its straight pieces along
  the axis or across it (raceways, ribs' faces; a roller meets nothing
  else yet) that face its middle (it in front of them: a face turned
  away, its housing's outside, would have it 14.5 mm deep) within its
  reach and a radius more as it starts (a roller in its bearing stays
  there)."""
  r, half = rollerOf(roller.shape)
  own = plus(rotated(conjugate(where.turn), minus(at.place, where.place)),
             ring.centre)
  rho, w = math.hypot(own[0], own[1]), own[2]
  reach = math.hypot(r, half) + r
  out = []
  for index, piece in enumerate(ring.shape.profile):
    if piece[0] != 'line':
      continue
    (r0, w0), (r1, w1) = piece[1], piece[2]
    if abs(r1 - r0) > 1e-12 and abs(w1 - w0) > 1e-12:
      continue
    near, outward = nearestOnPiece(piece, rho, w)
    if (rho - near[0]) * outward[0] + (w - near[1]) * outward[1] <= 0.0:
      continue
    if math.hypot(rho - near[0], w - near[1]) <= reach:
      out.append(index)
  return out


def _profileNear(ball: object, at: State, turned: object,
                 where: State) -> list[int]:
  """Returns the pieces of the turned solid 'turned' (in 'where') a
  ball (in 'at') is let press: those within two of its radii of its
  middle when it starts within that of the solid (a ball in a bearing's
  groove stays by its groove: the rest are never met), else every
  piece (a ball coming from afar, the walker, may meet any)."""
  r = ball.shape.radius
  own = plus(rotated(conjugate(where.turn), minus(at.place, where.place)),
             turned.centre)
  rho, w = math.hypot(own[0], own[1]), own[2]
  low, high, bottom, top = turned.shape.bounds()
  profile = turned.shape.profile
  if (rho < low - 2.0 * r or rho > high + 2.0 * r or w < bottom - 2.0 * r
      or w > top + 2.0 * r):
    return list(range(len(profile)))
  out = []
  for index, piece in enumerate(profile):
    near, _ = nearestOnPiece(piece, rho, w)
    if math.hypot(rho - near[0], w - near[1]) <= 2.0 * r:
      out.append(index)
  return out


def _products(p: numpy.ndarray, q: numpy.ndarray) -> numpy.ndarray:
  """Returns the quaternions 'p' times 'q', row by row ('product', the
  same sums in the same order)."""
  w1, x1, y1, z1 = p[:, 0], p[:, 1], p[:, 2], p[:, 3]
  w2, x2, y2, z2 = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
  return numpy.stack((w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                      w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                      w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                      w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2), axis=1)


def _crowdsOf(owner: _Packed, assembly: Assembly,
              rooms: list) -> object | None:
  """Returns the crowds as the kernels take them ('Crowds'), their
  rooms at 'rooms' (first touch, how many: one after another), or None
  where there are none; refuses a crowd that is not of balls."""
  if not rooms:
    return None
  wp, kernels = owner.wp, _kernelsOf()
  bodies = assembly.bodies
  ball, group, radius, crowdOf, widest = [], [], [], [], []
  for c, crowd in enumerate(assembly.crowds):
    wide = 0.0
    for g, members in enumerate(crowd.groups):
      for index in members:
        shape = bodies[index].shape
        if not isinstance(shape, Sphere):
          raise ValueError('a crowd is of balls only')
        ball.append(index)
        group.append(g)
        radius.append(shape.radius)
        crowdOf.append(c)
        wide = max(wide, shape.radius)
    widest.append(wide)
  cr = kernels.Crowds()
  cr.ball = owner.array(ball, wp.int32, 0)
  cr.group = owner.array(group, wp.int32, 0)
  cr.radius = owner.array(radius, wp.float32, 0.0)
  cr.crowdOf = owner.array(crowdOf, wp.int32, 0)
  cr.points = wp.zeros(max(1, len(ball)), wp.vec3, owner.device)
  cr.speed = wp.zeros(max(1, len(ball)), wp.float32, owner.device)
  cr.start = owner.array([start for start, _ in rooms], wp.int32, 0)
  cr.room = owner.array([room for _, room in rooms], wp.int32, 0)
  cr.taken = wp.zeros(len(rooms), wp.int32, owner.device)
  cr.fastest = wp.zeros(len(rooms), wp.float32, owner.device)
  cr.widest = owner.array(widest, wp.float32, 0.0)
  return cr


def _armOf(mover: object, point: Vector) -> Vector:
  """Returns a point of a body (in its own frame) along its principal
  axes from its centre."""
  return applied(transposed(matrixOf(mover.axes)),
                 minus(point, mover.body.centre))


def _chainsOf(owner: _Packed, assembly: Assembly,
              movers: list) -> tuple[object, list[tuple[int, int]]]:
  """Returns the cord lines as the kernel takes them ('Chains') and its
  colours, each (its first place in the order, how many lines): a line
  takes the first colour none of whose lines shares a body with it but
  at both their ends (lines sharing only ends are held side by side,
  the body's mass split among its slots there; a tyre's meridians, all
  ending on its rim, one colour; its rings another; its cords from node
  to node a third); bodies of the world share freely."""
  wp, kernels = owner.wp, _kernelsOf()
  fixed = assembly.fixed
  lines = assembly.cordLines
  first, count, closed = [], [], []
  body, arm, rest, soft = [], [], [], []
  colorOf, colors = [], []
  for line in lines:
    n = len(line.points)
    pieces = n if line.closed else n - 1
    if n < (3 if line.closed else 2) or len(line.stiffness) != pieces \
        or len(line.rests) != pieces:
      raise ValueError('a cord line takes two points or more (a ring '
                       'three), a stiffness and a rest for each piece')
    first.append(len(body))
    count.append(n)
    closed.append(1 if line.closed else 0)
    for j, (index, point) in enumerate(line.points):
      body.append(index)
      arm.append(_armOf(movers[index], point))
      rest.append(line.rests[j] if j < pieces else 0.0)
      stiff = line.stiffness[j] if j < pieces else math.inf
      soft.append(0.0 if math.isinf(stiff) else 1.0 / stiff)
    held = [index for index, _ in line.points if index not in fixed]
    if line.closed or n < 3:
      ends, inner = (set(), set(held)) if line.closed else (set(held),
                                                            set())
    else:
      inner = {index for index, _ in line.points[1:-1]
               if index not in fixed}
      ends = {index for index in (line.points[0][0], line.points[-1][0])
              if index not in fixed} - inner
    chosen = len(colors)
    for colour, (theirEnds, theirInner) in enumerate(colors):
      if inner & (theirEnds | theirInner) or ends & theirInner:
        continue
      chosen = colour
      break
    if chosen == len(colors):
      colors.append((set(), set()))
    colors[chosen][0].update(ends)
    colors[chosen][1].update(inner)
    colorOf.append(chosen)
  shared = {}
  for c, line in enumerate(lines):
    for index, _ in line.points:
      shared[colorOf[c], index] = shared.get((colorOf[c], index), 0) + 1
  split = []
  for c, line in enumerate(lines):
    for index, _ in line.points:
      split.append(1.0 if index in fixed else float(
        shared[colorOf[c], index]))
  order = sorted(range(len(lines)), key=lambda c: colorOf[c])
  spans, at = [], 0
  for colour in range(len(colors)):
    size = sum(1 for c in colorOf if c == colour)
    spans.append((at, size))
    at += size
  ch = kernels.Chains()
  zero = (0.0, 0.0, 0.0)
  ch.first = owner.array(first, wp.int32, 0)
  ch.count = owner.array(count, wp.int32, 0)
  ch.closed = owner.array(closed, wp.int32, 0)
  ch.order = owner.array(order, wp.int32, 0)
  ch.colorFirst = owner.array([span[0] for span in spans], wp.int32, 0)
  ch.colorCount = owner.array([span[1] for span in spans], wp.int32, 0)
  ch.body = owner.array(body, wp.int32, 0)
  ch.arm = owner.array(arm, wp.vec3, zero)
  ch.split = owner.array(split, wp.float32, 1.0)
  ch.rest = owner.array(rest, wp.float32, 0.0)
  ch.soft = owner.array(soft, wp.float32, 0.0)
  size = max(1, len(body))
  ch.way = wp.zeros(size, wp.vec3, owner.device)
  ch.start = wp.zeros(size, wp.vec3, owner.device)
  ch.active = wp.zeros(size, wp.int32, owner.device)
  for name in ('miss', 'lo', 'mid', 'hi', 'rhs', 'cp', 'dp', 'pull',
               'aux'):
    setattr(ch, name, wp.zeros(size, wp.float32, owner.device))
  return ch, spans


def _hingesOf(owner: _Packed, assembly: Assembly, movers: list,
              states: tuple) -> object:
  """Returns the hinges as the kernel takes them ('Hinges'): each end's
  pin's point and line along its body's principal axes (the world's
  from the origin, its line as is; a pin is a line, not a way: the
  second's turned about if it lay against the first in 'states', which
  read two lines half a turn apart, balanced on their tilt's knife
  edge, and lost the pin), a line square to the pin on each
  that lay alike in 'states' (its twist's nought: as the assembly was
  first packed), how easily its rubber gives (none: rigid; a twist with
  no stiffness free), its lag."""
  wp, kernels = owner.wp, _kernelsOf()
  hinges = tuple(assembly.hinges) + tuple(
    Hinge(slide.first, slide.firstPoint, slide.firstAxis, slide.second,
          slide.secondPoint, slide.secondAxis, _SLIDING)
    for slide in assembly.slides)

  def ends(index: int | None, point: Vector, line: Vector) -> tuple:
    """Returns an end's point and line as the kernel takes them, and
    the turn from its frame to the world's."""
    if index is None:
      return minus(point, owner.origin), line, (1.0, 0.0, 0.0, 0.0)
    mover = movers[index]
    back = transposed(matrixOf(mover.axes))
    return (applied(back, minus(point, mover.body.centre)),
            applied(back, line), states[index].turn)

  out = {name: [] for name in ('firstArm', 'secondArm', 'firstAxis',
                               'secondAxis', 'firstRef', 'secondRef',
                               'give', 'lag')}
  for hinge in hinges:
    size = norm(hinge.firstAxis)
    axis = tuple(x / size for x in hinge.firstAxis)
    square = (1.0, 0.0, 0.0) if abs(axis[0]) < 0.9 else (0.0, 1.0, 0.0)
    square = minus(square, tuple(dot(square, axis) * x for x in axis))
    size = norm(square)
    square = tuple(x / size for x in square)
    armK, lineK, turnK = ends(hinge.first, hinge.firstPoint,
                              hinge.firstAxis)
    armO, lineO, turnO = ends(hinge.second, hinge.secondPoint,
                              hinge.secondAxis)
    if dot(rotated(turnK, hinge.firstAxis), rotated(
        turnO, hinge.secondAxis)) < 0.0:
      lineO = tuple(-x for x in lineO)
    world = rotated(turnK, square)
    out['firstArm'].append(armK)
    out['secondArm'].append(armO)
    out['firstAxis'].append(_unit(lineK))
    out['secondAxis'].append(_unit(lineO))
    for name, index, own in (('firstRef', hinge.first, square),
                             ('secondRef', hinge.second, rotated(
                               conjugate(turnO), world))):
      if index is None:
        out[name].append(world)
        continue
      out[name].append(applied(transposed(matrixOf(movers[index].axes)),
                               own))
    bush = hinge.bush
    if bush is _SLIDING:
      out['give'].append((0.0, -1.0, 0.0, -1.0))
      out['lag'].append(0.0)
      continue
    if bush is None:
      out['give'].append((0.0, 0.0, 0.0, -1.0))
      out['lag'].append(0.0)
      continue
    out['give'].append(tuple(1.0 / k for k in (bush.radial, bush.axial,
                                               bush.tilt)) + (
      1.0 / bush.twist if bush.twist > 0.0 else -1.0,))
    out['lag'].append(bush.lag)
  zero = (0.0, 0.0, 0.0)
  hg = kernels.Hinges()
  hg.first = owner.array([-1 if h.first is None else h.first
                          for h in hinges], wp.int32, -1)
  hg.second = owner.array([-1 if h.second is None else h.second
                           for h in hinges], wp.int32, -1)
  for name in ('firstArm', 'secondArm', 'firstAxis', 'secondAxis',
               'firstRef', 'secondRef'):
    setattr(hg, name, owner.array(out[name], wp.vec3, zero))
  hg.give = owner.array(out['give'], wp.vec4, (0.0, 0.0, 0.0, -1.0))
  hg.lag = owner.array(out['lag'], wp.float32, 0.0)
  return hg


def _linesOf(owner: _Packed, assembly: Assembly, movers: list) -> object:
  """Returns the springs, dampers and rams as the kernel takes them
  ('Lines'): each end's point along its body's principal axes (the
  world's from the origin), a spring's stiffness, rest, whether it
  pulls and pushes and its rubber's damping both ways; a damper's
  damping shortening and lengthening (its 'rebound', else as
  shortening); a ram's nothing but its push, set each call
  ('_Packed.drive')."""
  wp, kernels = owner.wp, _kernelsOf()

  def armOf(index: int | None, point: Vector) -> tuple[int, Vector]:
    """Returns a line's end as the kernel takes it."""
    if index is None:
      return -1, minus(point, owner.origin)
    mover = movers[index]
    return index, applied(transposed(matrixOf(mover.axes)),
                          minus(point, mover.body.centre))

  rows = []
  for spring in assembly.springs:
    rows.append((armOf(spring.first, spring.firstPoint),
                 armOf(spring.second, spring.secondPoint),
                 spring.stiffness, spring.rest, int(spring.pulls),
                 int(spring.pushes), spring.damping, spring.damping))
  for damper in assembly.dampers:
    rebound = damper.damping if damper.rebound is None else (
      damper.rebound)
    rows.append((armOf(damper.first, damper.firstPoint),
                 armOf(damper.second, damper.secondPoint), 0.0, 0.0, 1, 1,
                 damper.damping, rebound))
  for ram in assembly.rams:
    rows.append((armOf(ram.first, ram.firstPoint),
                 armOf(ram.second, ram.secondPoint), 0.0, 0.0, 1, 1, 0.0,
                 0.0))
  zero = (0.0, 0.0, 0.0)
  ln = kernels.Lines()
  ln.first = owner.array([row[0][0] for row in rows], wp.int32, -1)
  ln.second = owner.array([row[1][0] for row in rows], wp.int32, -1)
  ln.firstArm = owner.array([row[0][1] for row in rows], wp.vec3, zero)
  ln.secondArm = owner.array([row[1][1] for row in rows], wp.vec3, zero)
  for at, name, dtype, blank in ((2, 'stiffness', wp.float32, 0.0),
                                 (3, 'rest', wp.float32, 0.0),
                                 (4, 'pulls', wp.int32, 1),
                                 (5, 'pushes', wp.int32, 1),
                                 (6, 'bump', wp.float32, 0.0),
                                 (7, 'rebound', wp.float32, 0.0)):
    setattr(ln, name, owner.array([row[at] for row in rows], dtype, blank))
  ln.push = wp.zeros(max(1, len(rows)), wp.float32, owner.device)
  return ln


def _turnsOf(owner: _Packed, assembly: Assembly, movers: list) -> object:
  """Returns the fourth wall points that turn as the kernel takes them
  ('Turns'): each its body, holder, axis along the body's principal
  axes, the hands' give, damping and most; their targets set each call
  ('_Packed.drive'), their angles counted from nought."""
  wp, kernels = owner.wp, _kernelsOf()
  points = assembly.turnPoints
  tn = kernels.Turns()
  tn.body = owner.array([point.body for point in points], wp.int32, 0)
  tn.holder = owner.array([-1 if point.holder is None else point.holder
                           for point in points], wp.int32, -1)
  tn.axis = owner.array([_unit(applied(transposed(matrixOf(
    movers[point.body].axes)), point.axis)) for point in points], wp.vec3,
    (0.0, 0.0, 1.0))
  tn.give = owner.array([1.0 / point.stiffness for point in points],
                        wp.float32, 0.0)
  tn.damping = owner.array([point.damping for point in points],
                           wp.float32, 0.0)
  tn.most = owner.array([point.most for point in points], wp.float32, 0.0)
  tn.target = wp.zeros(max(1, len(points)), wp.float32, owner.device)
  tn.rate = wp.zeros(max(1, len(points)), wp.float32, owner.device)
  tn.angle = wp.zeros(max(1, len(points)), wp.float32, owner.device)
  return tn


def _gearsOf(owner: _Packed, assembly: Assembly, movers: list,
             states: tuple) -> object:
  """Returns the racks and pinions and the gears meshing as the kernel
  takes them ('Gears', the racks first): a pinion's axis along its
  principal axes, its rack's line along the housing's (the world's), the
  rack's place along it as 'states' have it (its start) and the
  pinion's angle counted from nought; a mesh's two gears' axes along
  their principal axes, their pitch radii (the second's below nought
  where it turns the same way), their slip counted from nought."""
  wp, kernels = owner.wp, _kernelsOf()
  racks, meshes = assembly.racks, assembly.meshes
  axes, lines, starts = [], [], []
  for gear in racks:
    axes.append(_unit(applied(transposed(matrixOf(
      movers[gear.pinion].axes)), gear.pinionAxis)))
    world = rotated(states[gear.rack].turn, gear.rackAxis)
    if gear.housing is None:
      line = _unit(world)
      starts.append(dot(minus(states[gear.rack].place, owner.origin), line))
    else:
      housed = states[gear.housing]
      inside = rotated(conjugate(housed.turn), world)
      line = _unit(applied(transposed(matrixOf(
        movers[gear.housing].axes)), inside))
      apart = rotated(conjugate(housed.turn), minus(
        states[gear.rack].place, housed.place))
      starts.append(dot(applied(transposed(matrixOf(
        movers[gear.housing].axes)), apart), line))
    lines.append(line)
  radii, seconds = [gear.radius for gear in racks], [0.0] * len(racks)
  for mesh in meshes:
    axes.append(_unit(applied(transposed(matrixOf(
      movers[mesh.first].axes)), mesh.firstAxis)))
    lines.append(_unit(applied(transposed(matrixOf(
      movers[mesh.second].axes)), mesh.secondAxis)))
    starts.append(0.0)
    first, second = mesh.radii()
    radii.append(first)
    seconds.append(-second if mesh.same else second)
  both = list(racks) + list(meshes)
  gr = kernels.Gears()
  gr.kind = owner.array([int(kernels.RACK)] * len(racks)
                        + [int(kernels.MESH)] * len(meshes), wp.int32, 0)
  gr.pinion = owner.array([gear.pinion for gear in racks]
                          + [mesh.first for mesh in meshes], wp.int32, 0)
  gr.rack = owner.array([gear.rack for gear in racks]
                        + [mesh.second for mesh in meshes], wp.int32, 0)
  gr.housing = owner.array([-1 if gear.housing is None else gear.housing
                            for gear in both], wp.int32, -1)
  gr.pinionAxis = owner.array(axes, wp.vec3, (0.0, 0.0, 1.0))
  gr.rackAxis = owner.array(lines, wp.vec3, (1.0, 0.0, 0.0))
  gr.radius = owner.array(radii, wp.float32, 0.0)
  gr.secondRadius = owner.array(seconds, wp.float32, 0.0)
  gr.start = owner.array(starts, wp.float32, 0.0)
  gr.angle = wp.zeros(max(1, len(both)), wp.float32, owner.device)
  return gr


def _trainOf(owner: _Packed, assembly: Assembly) -> tuple[object, int]:
  """Returns the drivetrain's rules as the kernel solves them together
  ('Train': the gears meshing, then the disc brakes; a mesh's gears and
  housing, a brake's disc and caliper) and how many pairs of them share
  a body (every two, each way round and each with itself; a body of the
  world turns for none)."""
  wp, kernels = owner.wp, _kernelsOf()
  rules = [(mesh.first, mesh.second, -1 if mesh.housing is None
            else mesh.housing) for mesh in assembly.meshes]
  rules += [(brake.disc, -1 if brake.caliper is None else brake.caliper,
             -1) for brake in assembly.brakes]
  fixed = assembly.fixed
  pairs = [(j, a, k, c) for j, first in enumerate(rules)
           for a, body in enumerate(first)
           if body >= 0 and body not in fixed
           for k, second in enumerate(rules)
           for c, other in enumerate(second) if other == body]
  count, device = len(rules), owner.device
  tr = kernels.Train()
  tr.body = wp.zeros(max(1, count), wp.vec3i, device)
  tr.jacobian = wp.zeros(max(1, 3 * count), wp.vec3, device)
  tr.given = wp.zeros(max(1, 3 * count), wp.vec3, device)
  for name in ('miss', 'most', 'scale', 'found', 'work', 'down', 'pull'):
    setattr(tr, name, wp.zeros(max(1, count), wp.float32, device))
  tr.holds = wp.zeros(max(1, count), wp.int32, device)
  tr.order = wp.zeros(max(1, count), wp.int32, device)
  tr.kept = wp.zeros(max(1, count), wp.int32, device)
  tr.count = wp.zeros(5, wp.int32, device)
  tr.pairs = owner.array(pairs, wp.vec4i, (0, 0, 0, 0))
  tr.matrix = wp.zeros(max(1, count * count), wp.float32, device)
  tr.factor = wp.zeros(max(1, count * count), wp.float32, device)
  tr.inverse = wp.zeros(max(1, count * count), wp.float32, device)
  tr.turn = wp.zeros(len(assembly.bodies), wp.vec3, device)
  return tr, len(pairs)


#  The bush a slide is packed with among the hinges ('_hingesOf'): along
#  its line and about it, free.
_SLIDING = object()


def _unit(line: Vector) -> Vector:
  """Returns 'line' made a unit long."""
  size = norm(line)
  return tuple(x / size for x in line)


def _brakesOf(owner: _Packed, assembly: Assembly,
              movers: list) -> object:
  """Returns the disc brakes as the kernel takes them ('Brakes'): the
  disc's middle and axle and the pads' middle along their bodies'
  principal axes (the world's pads from the origin), each body's share
  the brakes on it; their forces set each call ('_Packed.drive')."""
  wp, kernels = owner.wp, _kernelsOf()
  brakes = assembly.brakes
  on = {}
  for brake in brakes:
    for body in (brake.disc, brake.caliper):
      if body is not None:
        on[body] = on.get(body, 0) + 1

  def own(index: int, point: Vector) -> Vector:
    """Returns 'point' in body 'index''s own frame along its principal
    axes from its centre."""
    mover = movers[index]
    return applied(transposed(matrixOf(mover.axes)),
                   minus(point, mover.body.centre))

  middles, axles, pads, rings = [], [], [], []
  for brake in brakes:
    back = transposed(matrixOf(movers[brake.disc].axes))
    middles.append(own(brake.disc, brake.middle))
    axles.append(applied(back, brake.axle))
    pads.append(minus(brake.pad, owner.origin) if brake.caliper is None
                else own(brake.caliper, brake.pad))
    rings.append((brake.inner, brake.outer))
  zero = (0.0, 0.0, 0.0)
  br = kernels.Brakes()
  br.disc = owner.array([brake.disc for brake in brakes], wp.int32, 0)
  br.caliper = owner.array([-1 if brake.caliper is None else brake.caliper
                            for brake in brakes], wp.int32, -1)
  br.middle = owner.array(middles, wp.vec3, zero)
  br.axle = owner.array(axles, wp.vec3, zero)
  br.pad = owner.array(pads, wp.vec3, zero)
  br.ring = owner.array(rings, wp.vec2, (0.0, 0.0))
  br.force = wp.zeros(max(1, len(brakes)), wp.float32, owner.device)
  br.discShare = owner.array([float(on[brake.disc]) for brake in brakes],
                             wp.float32, 1.0)
  br.caliperShare = owner.array(
    [1.0 if brake.caliper is None else float(on[brake.caliper])
     for brake in brakes], wp.float32, 1.0)
  br.held = wp.zeros(max(1, len(brakes)), wp.float32, owner.device)
  br.gripping = wp.zeros(max(1, len(brakes)), wp.int32, owner.device)
  return br


def _airsOf(owner: _Packed, assembly: Assembly,
            movers: list) -> tuple[object, int]:
  """Returns the airs as the kernel takes them ('Airs') and how many
  faces they have; each air's corners reckoned from its first face's
  first corner's body."""
  wp, kernels = owner.wp, _kernelsOf()
  gas, base, faceAir, body, arm = [], [], [], [], []
  for a, air in enumerate(assembly.airs):
    gas.append(air.gas)
    base.append(air.faces[0][0][0])
    for face in air.faces:
      if len(face) != 3:
        raise ValueError('an air\'s faces are triangles')
      faceAir.append(a)
      for index, point in face:
        body.append(index)
        arm.append(_armOf(movers[index], point))
  airs = kernels.Airs()
  airs.gas = owner.array(gas, wp.float32, 0.0)
  airs.volume = wp.zeros(max(1, len(gas)), wp.float32, owner.device)
  airs.base = owner.array(base, wp.int32, 0)
  airs.faceAir = owner.array(faceAir, wp.int32, 0)
  airs.body = owner.array(body, wp.int32, 0)
  airs.arm = owner.array(arm, wp.vec3, (0.0, 0.0, 0.0))
  return airs, len(faceAir)


def _linksOf(assembly: Assembly, movers: list,
             origin: Vector) -> list[tuple]:
  """Returns the ties and the actuators holding their length, each
  (kind, first, second, first's point, second's point, length): a
  body's point along its principal axes from its centre, the world's
  from 'origin'."""
  kernels = _kernelsOf()

  def armOf(index: int | None, point: Vector) -> tuple[int, Vector]:
    """Returns a link's end as the kernel takes it."""
    if index is None:
      return -1, minus(point, origin)
    mover = movers[index]
    return index, applied(transposed(matrixOf(mover.axes)),
                          minus(point, mover.body.centre))

  out = []
  for tie in assembly.ties:
    first, firstArm = armOf(tie.first, tie.firstPoint)
    second, secondArm = armOf(tie.second, tie.secondPoint)
    out.append((int(kernels.TIE), first, second, firstArm, secondArm,
                0.0))
  for rod in assembly.actuators:
    first, firstArm = armOf(rod.first, rod.firstPoint)
    second, secondArm = armOf(rod.second, rod.secondPoint)
    out.append((int(kernels.ROD), first, second, firstArm, secondArm,
                rod.stroke.length))
  return out


def _dampsOf(assembly: Assembly, count: int) -> list[int]:
  """Returns how many rules damp each of the 'count' bodies after the
  touches settle (the kernel's 'dampGive' splits a body among them): a
  spring's rubber and a damper, one an end; a bushed hinge's rubber, one
  for each way it gives (across, along, tilting, twisting if it holds
  it); the hands on a fourth wall point, one on its body and holder.
  The world and bodies made part of it none."""
  fixed = assembly.fixed
  out = [0] * count

  def add(ends: tuple, rules: int) -> None:
    """Counts 'rules' more on each of 'ends' that moves."""
    for end in ends:
      if end is not None and end not in fixed:
        out[end] += rules

  for spring in assembly.springs:
    if spring.damping > 0.0:
      add((spring.first, spring.second), 1)
  for damper in assembly.dampers:
    add((damper.first, damper.second), 1)
  for hinge in assembly.hinges:
    bush = hinge.bush
    if bush is not None and bush.lag > 0.0:
      ways = sum(1 for k in (bush.radial, bush.axial, bush.tilt) if k > 0.0)
      add((hinge.first, hinge.second), ways + (1 if bush.twist > 0.0
                                               else 0))
  for point in assembly.turnPoints:
    if point.damping > 0.0:
      add((point.body, point.holder), 1)
  return out


def _humpsOf(assembly: Assembly) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Returns the humps bolted on now as the kernel takes them, room for
  'HUMP_ROOM' (the rest none: body below nought): each its body, angle,
  length and height, and its span from the axis; more refused."""
  humps = numpy.zeros((HUMP_ROOM, 4), numpy.float32)
  spans = numpy.zeros((HUMP_ROOM, 2), numpy.float32)
  humps[:, 0] = -1.0
  rows = [(bolted.body, hump) for bolted in assembly.humps
          for hump in bolted.humps]
  if len(rows) > HUMP_ROOM:
    raise ValueError('at most %d humps can be bolted on' % HUMP_ROOM)
  for at, (body, hump) in enumerate(rows):
    humps[at] = (body, hump.angle, hump.length, hump.height)
    spans[at] = (hump.inner, hump.outer)
  return humps, spans


def _refused(assembly: Assembly) -> None:
  """Refuses what the small steps cannot step yet: drags, welds, an
  actuator's moving stroke, a driveshaft's motor."""
  for name, found in (('drags', assembly.drags),
                      ('welds', assembly.welds)):
    if found:
      raise ValueError('%s are not in the small steps yet' % name)
  for rod in assembly.actuators:
    if not isinstance(rod.stroke, HeldStroke):
      raise ValueError('only held strokes are in the small steps yet')
  for motor in assembly.motors:
    if motor.bearer is not None:
      raise ValueError('driveshafts are not in the small steps yet')
