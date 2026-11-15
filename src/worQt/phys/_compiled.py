"""
compiledRun runs 'World.booked's steps in Warp ('worldRun'), the plain
Python's objects packed into arrays (so the kernel starts from exactly
what the plain Python would), launched once for all the steps of a
call, and read back into states and books.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING, NamedTuple

import numpy

from ._assembly import HeldStroke, SineStroke
from ._books import Books
from ._constraints import ConstraintSolver
from ._contacts import ContactForces
from ._hexapod import HeldPose, LegStroke, SwayingPose
from ._rounds import ROUND
from ._turned import Turned
from ._springs import SpringForces
from ._vectors import applied, matrixOf, minus, transposed

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._assembly import Assembly
  from ._body import State

_KINDS = {'tie': 4, 'actuator': 2, 'damper': 1}
#  How many threads step a world side by side on a GPU, in one block
#  ('runParallel').
THREADS = 256
_WIDE = 24
_kernels = None


def _kernelsOf():
  """Returns the kernels' module, imported (and Warp started) at its
  first use."""
  global _kernels
  if _kernels is None:
    import warp as wp
    wp.init()
    from . import _world_kernels
    _kernels = _world_kernels
  return _kernels


def strokeData(stroke: object) -> list[float] | None:
  """The 'strokeData' function returns an actuator's stroke as the
  kernel takes it, 24 numbers, or None for a stroke it cannot run."""
  out = [0.0] * _WIDE
  if isinstance(stroke, HeldStroke):
    out[0], out[1] = 0.0, stroke.length
    return out
  if isinstance(stroke, SineStroke):
    out[0:4] = [1.0, stroke.middle, stroke.amplitude, stroke.frequency]
    return out
  if not isinstance(stroke, LegStroke):
    return None
  motion = stroke.motion
  out[0] = 2.0
  out[1:4] = list(stroke.base)
  out[4:7] = list(stroke.arm)
  out[8:11] = list(motion.place)
  out[11:15] = list(motion.turn)
  if isinstance(motion, HeldPose):
    out[7] = 0.0
    return out
  if isinstance(motion, SwayingPose):
    out[7] = 1.0
    out[15:18] = list(motion.shift)
    out[18:21] = list(motion.tilt)
    out[21] = motion.frequency
    return out
  return None


def compiledRun(world, assembly: Assembly, states: tuple[State, ...],
                movers: list, count: int, h: float, start: float,
                books: Books) -> tuple | None:
  """The 'compiledRun' function runs 'assembly' from 'states' ('movers'
  the plain Python's bodies so) for 'count' steps of 'h' s from
  'start', compiled, and returns the states and 'books' booked on; or
  None where the kernel cannot run the assembly (a stroke it does not
  know). What does not change (the bodies, the links, the skins) is
  packed once for an assembly in a world and kept; each call fills in
  where the bodies are and how they move."""
  packed = _packedFor(world, assembly, movers)
  if packed is None:
    return None
  import warp as wp
  kernels = _kernelsOf()
  rules, bodies, links, touches, entries, out = packed
  rules.count, rules.h, rules.start = count, h, start
  rules.first = round(start / h)
  if rules.motors:
    drives = [motor.drive for motor in assembly.motors]
    links.motorDrive.assign(numpy.array(
      [value for drive in drives
       for value in (drive.torque, drive.target, drive.stiffness,
                     drive.damping, drive.most, drive.slip,
                     drive.radius)]))
    links.motorReference.assign(numpy.array([drive.reference
                                             for drive in drives]))
  _fillBodies(bodies, movers)
  bodies.groundPlane.assign(numpy.array(_planesOf(world.ground, movers,
                                                  count * h)))
  _fillHolds(touches, movers, entries)
  touches.fresh.assign(numpy.array([0, 1], numpy.int32))
  out.zero_()
  threads = rules.threads
  wp.launch(kernels.worldRun, threads, [rules, bodies, links, touches,
                                        out], [], [], [], deviceOf(world),
            None, False, True, False, 0, threads)
  got = out.numpy()
  if got[10] != 0.0:
    raise ValueError('no single solution: held twice, or nothing held')
  _readBack(movers, bodies, touches, entries)
  booked = Books(float(got[6] - got[8] - got[0]), float(-got[1]), 0.0,
                 float(got[2]), float(got[3]), float(got[4]),
                 float(got[7] - got[9] - got[5]))
  return tuple(mover.state() for mover in movers), books.plus(booked)


#  What was packed lately: the assembly and world it was packed for,
#  and the packing (None for one the kernel cannot run).
_PACKED: list = []
_KEPT = 8


def _packedFor(world, assembly: Assembly, movers: list) -> tuple | None:
  """Returns 'assembly' in 'world' packed for the kernel, packing it
  only when it was not lately; None where the kernel cannot run it (a
  stroke it does not know)."""
  for at, (kept, keptWorld, packing) in enumerate(_PACKED):
    if kept is assembly and keptWorld == world:
      if at:
        _PACKED.insert(0, _PACKED.pop(at))
      return packing
  data = {id(actuator): strokeData(actuator.stroke)
          for actuator in assembly.actuators}
  packing = None
  if not any(value is None for value in data.values()):
    packing = _packed(world, assembly, movers, data)
  _PACKED.insert(0, (assembly, world, packing))
  del _PACKED[_KEPT:]
  return packing


def _packed(world, assembly: Assembly, movers: list, data: dict) -> tuple:
  """Returns 'assembly' in 'world' packed for the kernel: the rules,
  the bodies, the links, the contacts, their skins' entries, and the
  kernel's out."""
  import warp as wp
  kernels = _kernelsOf()
  where = {id(mover): index for index, mover in enumerate(movers)}
  rules = kernels.Rules()
  _fillRules(rules, world, assembly, len(movers), wp)
  device = deviceOf(world)
  bodies = _bodiesOf(kernels, movers, wp, device)
  terrain = None if world.ground is None else world.ground.terrain
  heights = [0.0] if terrain is None else [
    height for row in terrain.heights for height in row]
  bodies.heights = _array(heights, wp.float64, wp, 0.0, device)
  links, rows = _linksOf(kernels, assembly, movers, where, data, wp,
                        device)
  rules.links = len(links[0])
  rules.rows = rows
  touching = ContactForces(assembly.contacts, movers)
  rules.contacts, rules.rounds = len(touching.contacts), len(touching.rounds)
  rules.slots = sum(rounding[5] for rounding in touching.roundings)
  touches, entries = _touchesOf(kernels, touching, assembly, movers, wp,
                                device)
  out = wp.zeros(16, wp.float64, device)
  return rules, bodies, links[1], touches, entries, out


def _fillBodies(bodies, movers: list) -> None:
  """Fills in where 'movers' are, how they move, how long each has
  been still, and their bristles (built on the processor and copied
  over, wherever the arrays live)."""
  bodies.place.assign(numpy.array([m.place for m in movers]))
  bodies.velocity.assign(numpy.array([m.velocity for m in movers]))
  bodies.turn.assign(numpy.array([m.turn for m in movers]))
  bodies.momentum.assign(numpy.array([m.momentum for m in movers]))
  bodies.rest.assign(numpy.array([m.rest for m in movers]))
  bristle = bodies.bristle.numpy().copy()
  on = bodies.bristleOn.numpy().copy()
  first = bodies.groundFirst.numpy()
  for k, mover in enumerate(movers):
    for at, (index, _, _) in enumerate(mover.arms):
      held = mover.bristles.get(index)
      on[first[k] + at] = 0 if held is None else 1
      if held is not None:
        bristle[first[k] + at] = held
  bodies.bristle.assign(bristle)
  bodies.bristleOn.assign(on)


class _Entries(NamedTuple):
  """
  _Entries are the contacts' ways round as packed: 'listed' each one's
  toucher, the other's place, where its holds begin and how many;
  'ways' the same by (toucher, other), each its place in 'listed' too;
  and for every hold's slot its toucher ('mine'), the other ('theirs')
  and its skin point ('index'). The round contacts' slots: 'rounds'
  each its ball, the other's place and the slot (the piece of a turned
  solid's profile, else nought), 'roundAt' the same to its place.
  """

  listed: list
  ways: dict
  mine: list
  theirs: list
  index: list
  rounds: list
  roundAt: dict


def _entriesOf(listed: list, rounds: list) -> _Entries:
  """Returns the ways round 'listed', and the round contacts 'rounds',
  as '_Entries'."""
  ways: dict[tuple[int, int], list] = {}
  mine, theirs, index = [], [], []
  for entry, (toucher, other, start, count) in enumerate(listed):
    ways.setdefault((toucher, other), []).append((entry, start, count))
    mine.extend([toucher] * count)
    theirs.extend([other] * count)
    index.extend(range(count))
  roundAt = {pair: at for at, pair in enumerate(rounds)}
  return _Entries(listed, ways, mine, theirs, index, rounds, roundAt)


def _fillHolds(touches, movers: list, entries: _Entries) -> None:
  """Fills in the contacts' holds from 'movers', and whether each way
  round holds any: only the holds there are, each found by its way
  round."""
  holdOn = numpy.zeros(touches.holdOn.shape[0], numpy.int32)
  hold = touches.hold.numpy().copy()
  entryOn = numpy.zeros(touches.entryOn.shape[0], numpy.int32)
  ways = entries.ways
  roundOn = numpy.zeros(touches.roundOn.shape[0], numpy.int32)
  stretch = numpy.zeros((touches.roundStretch.shape[0], 3))
  for mine, mover in enumerate(movers):
    for (index, theirs), held in mover.holds.items():
      if index <= ROUND:
        at = entries.roundAt.get((mine, theirs, ROUND - index))
        if at is not None:
          roundOn[at] = 1
          stretch[at] = held
        continue
      for entry, start, count in ways.get((mine, theirs), ()):
        if index < count:
          holdOn[start + index] = 1
          hold[start + index] = held
          entryOn[entry] = 1
  touches.roundOn.assign(roundOn)
  touches.roundStretch.assign(stretch)
  touches.holdOn.assign(holdOn)
  touches.hold.assign(hold)
  touches.entryOn.assign(entryOn)


def _planesOf(ground: object, movers: list, seconds: float) -> list:
  """Returns, for each body, the ground anywhere it could reach in the
  next 'seconds' (its farthest point about where it is, moved as fast
  again as it goes, and a metre to spare) as a plane and how far the
  ground rises over it ('Terrain.planeWithin'), eight numbers a body:
  the kernel looks no point higher over the plane than that up in the
  terrain (on the hill track a car's 600 points did, every half step:
  42 ms a frame; on the oval's 24 degree banks the ground's top beside
  the car stood metres over it, so a top alone let none be passed
  over). Level at nought on flat ground."""
  if ground is None or ground.terrain is None:
    return [0.0] * max(8, 8 * len(movers))
  out = []
  for mover in movers:
    x, y = mover.place[0], mover.place[1]
    far = (mover.reach + 1.0 + 2.0 * seconds
           * math.hypot(mover.velocity[0], mover.velocity[1]))
    out.extend(ground.terrain.planeWithin((x - far, y - far),
                                          (x + far, y + far)) + (0.0,))
  return out or [0.0] * 8


def _array(values: list, dtype, wp, blank, device: str) -> object:
  """Returns 'values' as a Warp array of 'dtype' on the processor (a
  single 'blank' when there are none: Warp takes no empty arrays)."""
  return wp.array(values if values else [blank], dtype, None, None, None,
                  None, device)


def fastestDevice() -> str:
  """The 'fastestDevice' function returns where a world is best stepped
  here: the CPU, for now. On the user's GPU (an RTX 5060, 2026-11-13)
  the side by side steps took 108 s of computing a simulated second of
  the bearing against the CPU's 13: the world is reckoned in doubles,
  which a GeForce card works at a 64th of its singles' pace, and in one
  block of its ~30 (user: "everything should run on gpu always!": not
  until the GPU is faster; see 'gpuDevice')."""
  return 'cpu'


def gpuDevice() -> str | None:
  """The 'gpuDevice' function returns the GPU Warp finds here ('cuda'),
  or None for none."""
  import warp as wp
  _kernelsOf()
  return 'cuda' if wp.is_cuda_available() else None


def deviceOf(world) -> str:
  """The 'deviceOf' function returns the Warp device 'world' is stepped
  on: its 'device', but 'cpu' for 'cpu-parallel' (the side by side steps
  run by one thread on the CPU: to hold them to the serial ones)."""
  return 'cpu' if world.device.startswith('cpu') else world.device


def _fillRules(rules, world, assembly, count: int, wp) -> None:
  """Fills 'rules' with the world's numbers ('compiledRun' the call's):
  stepped side by side ('parallel') on any device but the plain 'cpu',
  by 'THREADS' threads on a GPU, one on the CPU."""
  rules.gravity = wp.vec3d(*world.gravity)
  rules.parallel = 0 if world.device == 'cpu' else 1
  rules.threads = 1 if deviceOf(world) == 'cpu' else THREADS
  rules.bodies = count
  rules.springs = len(assembly.springs)
  rules.motors = len(assembly.motors)
  rules.drags = len(assembly.drags)
  rules.contacts = len(assembly.contacts)
  ground = world.ground
  rules.ground = 0 if ground is None else 1
  if ground is not None:
    rules.stiffness, rules.damping = ground.stiffness, ground.damping
    rules.grip, rules.bristle = ground.grip, ground.bristle
    rules.bristleDamping = ground.bristleDamping
    rules.relaxation = ground.relaxation
    terrain = ground.terrain
    rules.terrain = 0 if terrain is None else 1
    rules.terrainTop = ground.topOf()
    if terrain is not None:
      rules.terrainX, rules.terrainY = terrain.origin
      rules.terrainCell = terrain.cell
      rules.terrainNx = len(terrain.heights)
      rules.terrainNy = len(terrain.heights[0])
    wall = ground.wall
    rules.wall = 0 if wall is None else 1
    if wall is not None:
      rules.wallHalf, rules.wallRadius = wall.half, wall.radius
      rules.wallOut, rules.wallHeight = wall.out, wall.height
      rules.wallGrip = wall.grip
  grease = world.grease
  rules.grease = 0 if grease is None else 1
  if grease is not None:
    rules.shake, rules.spin = grease.shake, grease.spin
    rules.seed = wp.uint64(grease.seed & ((1 << 64) - 1))
  sleeping = world.sleeping
  rules.sleep = 0 if sleeping is None else 1
  if sleeping is not None:
    rules.sleepSpeed, rules.sleepSpin = sleeping.speed, sleeping.spin
    rules.settle = sleeping.settle


def _bodiesOf(kernels, movers: list, wp, device: str) -> object:
  """Returns the bodies as the kernel takes them."""
  bodies = kernels.Bodies()
  three, four = (0.0,) * 3, (0.0,) * 4
  bodies.mass = _array([m.mass for m in movers], wp.float64, wp, 0.0,
                       device)
  bodies.moments = _array([m.moments for m in movers], wp.vec3d, wp,
                          three, device)
  bodies.axes = _array([m.axes for m in movers], wp.vec4d, wp, four,
                       device)
  bodies.centre = _array([m.body.centre for m in movers], wp.vec3d, wp,
                         three, device)
  bodies.place = _array([m.place for m in movers], wp.vec3d, wp, three,
                        device)
  bodies.velocity = _array([m.velocity for m in movers], wp.vec3d, wp,
                           three, device)
  bodies.turn = _array([m.turn for m in movers], wp.vec4d, wp, four,
                       device)
  bodies.momentum = _array([m.momentum for m in movers], wp.vec3d, wp,
                           three, device)
  bodies.rest = _array([m.rest for m in movers], wp.float64, wp, 0.0,
                       device)
  bodies.free = _array([1 if m.free else 0 for m in movers], wp.int32, wp,
                       0, device)
  count = max(1, len(movers))
  bodies.round = _array([m.round for m in movers], wp.float64, wp, 0.0,
                       device)
  bodies.rollAxis = _array([(0.0,) * 3 if m.roll is None else m.roll
                            for m in movers], wp.vec3d, wp, (0.0,) * 3,
                           device)
  bodies.asleepNow = wp.zeros(count, wp.int32, device)
  bodies.stillNow = wp.zeros(count, wp.int32, device)
  bodies.woken = wp.zeros(count, wp.int32, device)
  firsts, counts, reaches, arms, rings = [], [], [], [], []
  bristles, on = [], []
  for mover in movers:
    firsts.append(len(arms))
    counts.append(len(mover.arms))
    reaches.append(mover.reach)
    for index, arm, ring in mover.arms:
      arms.append(arm)
      rings.append(ring)
      held = mover.bristles.get(index)
      bristles.append(held if held is not None else (0.0, 0.0))
      on.append(0 if held is None else 1)
  bodies.groundFirst = _array(firsts, wp.int32, wp, 0, device)
  bodies.groundCount = _array(counts, wp.int32, wp, 0, device)
  bodies.groundReach = _array(reaches, wp.float64, wp, 0.0, device)
  bodies.groundPlane = wp.zeros(max(1, 8 * len(movers)), wp.float64,
                                device)
  bodies.groundArm = _array(arms, wp.vec3d, wp, (0.0,) * 3, device)
  bodies.groundRing = _array(rings, wp.float64, wp, 0.0, device)
  bodies.bristle = _array(bristles, wp.vec2d, wp, (0.0, 0.0), device)
  bodies.bristleOn = _array(on, wp.int32, wp, 0, device)
  bodies.given = wp.zeros(max(1, 12 * len(movers)), wp.vec3d, device)
  bodies.drifting = wp.zeros(max(1, 2 * len(movers)), wp.vec3d, device)
  bodies.pushing = wp.zeros(max(1, 2 * len(movers)), wp.vec3d, device)
  return bodies


def _linksOf(kernels, assembly, movers: list, where: dict, data: dict,
             wp, device: str) -> tuple:
  """Returns the springs and the rules' links as the kernel takes them,
  and how many rules there are."""
  links = kernels.Links()
  springs = SpringForces(assembly.springs, movers)
  ends, arms, laws = [], [], []
  for spring, both in zip(assembly.springs, springs.ends):
    for mover, arm in both:
      ends.append(-1 if mover is None else where[id(mover)])
      arms.append(arm)
    laws.append((spring.stiffness, spring.rest, spring.damping,
                 0.0 if spring.pulls and spring.pushes
                 else 1.0 if spring.pushes else 2.0))
  links.springEnds = _array(ends, wp.int32, wp, 0, device)
  links.springArms = _array(arms, wp.vec3d, wp, (0.0,) * 3, device)
  links.springLaw = _array(laws, wp.vec4d, wp, (0.0,) * 4, device)
  turned = [0] * max(1, len(movers))
  for end, arm in zip(ends, arms):
    if end >= 0 and tuple(arm) != (0.0, 0.0, 0.0):
      turned[end] = 1
  links.springTurned = _array(turned, wp.int32, wp, 0, device)
  links.springTurning = wp.zeros(max(1, len(movers)), wp.mat33d, device)
  motorEnds, motorAxes = [], []
  for motor in assembly.motors:
    motorEnds.append(-1 if motor.first is None
                     else where[id(movers[motor.first])])
    second = movers[motor.second]
    motorEnds.append(where[id(second)])
    motorAxes.append(applied(transposed(matrixOf(second.axes)),
                             motor.axis))
  count = max(1, len(motorAxes))
  links.motorEnds = _array(motorEnds, wp.int32, wp, 0, device)
  links.motorAxis = _array(motorAxes, wp.vec3d, wp, (0.0,) * 3, device)
  links.motorOwnAxis = _array([motor.axis for motor in assembly.motors],
                              wp.vec3d, wp, (0.0,) * 3, device)
  bearers, motorArms, ownAxes = [], [], []
  for motor in assembly.motors:
    shaft = motor.bearer is not None
    bearers.append(where[id(movers[motor.bearer])] if shaft else -1)
    own = transposed(matrixOf(movers[motor.first].axes)) if (
      shaft and motor.first is not None) else None
    for way in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)):
      ownAxes.append((0.0, 0.0, 0.0) if own is None else applied(own,
                                                                 way))
    for index, point in ((motor.first, motor.firstPoint),
                         (motor.second, motor.secondPoint)):
      motorArms.append(movers[index].inward(point) if shaft
                       else (0.0, 0.0, 0.0))
  links.dragBody = _array([where[id(movers[drag.body])]
                          for drag in assembly.drags], wp.int32, wp, 0,
                         device)
  links.dragPull = _array([0.5 * drag.density * drag.area
                          for drag in assembly.drags], wp.float64, wp,
                         0.0, device)
  links.motorBearer = _array(bearers, wp.int32, wp, -1, device)
  links.motorArms = _array(motorArms, wp.vec3d, wp, (0.0,) * 3, device)
  links.motorForward = _array(ownAxes[0::2], wp.vec3d, wp, (0.0,) * 3,
                              device)
  links.motorLeft = _array(ownAxes[1::2], wp.vec3d, wp, (0.0,) * 3,
                           device)
  links.motorDrive = wp.zeros(7 * count, wp.float64, device)
  links.motorReference = wp.zeros(count, wp.vec4d, device)
  solver = ConstraintSolver(assembly.ties, assembly.actuators,
                            assembly.dampers, movers)
  kinds, linkEnds, linkArms, numbers = [], [], [], []
  for both, kind, link in solver.links:
    kinds.append(_KINDS[kind])
    for mover, arm, _ in both:
      linkEnds.append(-1 if mover is None else where[id(mover)])
      linkArms.append(arm)
    if kind == 'actuator':
      numbers.extend(data[id(link)])
    elif kind == 'damper':
      numbers.extend([link.damping] + [0.0] * (_WIDE - 1))
    else:
      numbers.extend([0.0] * _WIDE)
  rows = len(solver.rows)
  wide = max(1, rows)
  links.kind = _array(kinds, wp.int32, wp, 0, device)
  links.ends = _array(linkEnds, wp.int32, wp, 0, device)
  links.arms = _array(linkArms, wp.vec3d, wp, (0.0,) * 3, device)
  links.data = _array(numbers, wp.float64, wp, 0.0, device)
  links.rowLink = _array([link for link, _ in solver.rows], wp.int32, wp,
                         0, device)
  links.rowAxis = _array([-1 if axis is None else axis
                          for _, axis in solver.rows], wp.int32, wp, 0,
                         device)
  links.armsNow = wp.zeros(max(1, 2 * len(kinds)), wp.vec3d, device)
  links.ways = wp.zeros(wide, wp.vec3d, device)
  links.coupling = wp.zeros(wide * wide, wp.float64, device)
  links.matrix = wp.zeros(wide * (wide + 1), wp.float64, device)
  for name in ('impulses', 'better', 'speeds', 'before', 'misses'):
    setattr(links, name, wp.zeros(wide, wp.float64, device))
  count = max(1, len(movers))
  links.soft = wp.zeros(count, wp.mat33d, device)
  links.trialVelocity = wp.zeros(count, wp.vec3d, device)
  links.trialMomentum = wp.zeros(count, wp.vec3d, device)
  links.trialPlace = wp.zeros(count, wp.vec3d, device)
  links.trialTurn = wp.zeros(count, wp.vec4d, device)
  links.linkImpulse = wp.zeros(max(1, len(kinds)), wp.vec3d, device)
  held = [0] * len(movers)
  for end in linkEnds:
    if end >= 0:
      held[end] = 1
  links.held = _array(held, wp.int32, wp, 0, device)
  return (kinds, links), rows


def _touchesOf(kernels, touching: ContactForces, assembly, movers: list,
               wp, device: str) -> tuple:
  """Returns the contacts as the kernel takes them (each body's skin
  once, shared by its contacts; each way round's holds), and each way
  round's toucher, the other's place, where its holds begin and how
  many."""
  touches = kernels.Touches()
  where = {id(mover): index for index, mover in enumerate(movers)}
  pairs, laws = [], []
  skinBody, arms, shares, skins = [], [], [], {}
  entrySkin, entryCount, entryHold, on, holds = [], [], [], [], []
  entries, holdEntry = [], []
  for contact in touching.contacts:
    pairs.extend((contact.first, contact.second))
    laws.extend((contact.stiffness, contact.damping, contact.grip,
                 contact.bristle, contact.bristleDamping, 0.0))
    for mine, theirs in ((contact.first, contact.second),
                         (contact.second, contact.first)):
      toucher = movers[mine]
      key = (id(toucher), contact.spacing)
      skin = touching.skins[key]
      if key not in skins:
        skins[key] = len(arms)
        for arm, share in skin:
          skinBody.append(where[id(toucher)])
          arms.append(arm)
          shares.append(share)
      entrySkin.append(skins[key])
      entryCount.append(len(skin))
      entryHold.append(len(on))
      entries.append((mine, theirs, len(on), len(skin)))
      for index in range(len(skin)):
        held = toucher.holds.get((index, theirs))
        holdEntry.append(len(entryHold) - 1)
        on.append(0 if held is None else 1)
        holds.append(held if held is not None else (0.0,) * 3)
  pieceFirst, pieceCount, planeFirst, planeCount = [], [], [], []
  normals, offsets, reaches, lows, highs = [], [], [], [], []
  for mover in movers:
    shape = touching.shapes.get(id(mover), ((), (), 0.0))
    _, pieces, reach = shape
    pieceFirst.append(len(planeFirst))
    pieceCount.append(len(pieces))
    reaches.append(reach)
    for planes, (low, high) in zip(pieces, _boundsOf(mover)):
      planeFirst.append(len(normals))
      planeCount.append(len(planes))
      lows.append(low)
      highs.append(high)
      for facing, offset in planes:
        normals.append(facing)
        offsets.append(offset)
  edges = len(touching.contacts)
  for contact in touching.rounds:
    pairs.extend((contact.first, contact.second))
  touches.pair = _array(pairs, wp.int32, wp, 0, device)
  mine: list[list[int]] = [[] for _ in movers]
  for at, contact in enumerate(touching.contacts + touching.rounds):
    mine[contact.first].append(at)
    mine[contact.second].append(at)
  rounds = _roundsOf(touches, touching, movers, where, wp, device)
  firsts = [0]
  for listed in mine:
    firsts.append(firsts[-1] + len(listed))
  touches.bodyFirst = _array(firsts, wp.int32, wp, 0, device)
  touches.bodyContacts = _array([at for listed in mine for at in listed],
                                wp.int32, wp, 0, device)
  touches.queue = wp.zeros(max(1, len(movers)), wp.int32, device)
  touches.law = _array(laws, wp.float64, wp, 0.0, device)
  touches.entrySkin = _array(entrySkin, wp.int32, wp, 0, device)
  touches.entryCount = _array(entryCount, wp.int32, wp, 0, device)
  touches.entryHold = _array(entryHold, wp.int32, wp, 0, device)
  touches.entryOn = wp.zeros(max(1, len(entryHold)), wp.int32, device)
  touches.skinBody = _array(skinBody, wp.int32, wp, -1, device)
  touches.skinArm = _array(arms, wp.vec3d, wp, (0.0,) * 3, device)
  touches.skinShare = _array(shares, wp.float64, wp, 0.0, device)
  size = max(1, len(arms))
  touches.skinOut = wp.zeros(size, wp.vec3d, device)
  touches.skinPlace = wp.zeros(size, wp.vec3d, device)
  touches.fresh = wp.zeros(2, wp.int32, device)
  slots = max(1, len(on))
  touches.found = wp.zeros(slots, wp.int32, device)
  touches.depth = wp.zeros(slots, wp.float64, device)
  touches.normalOf = wp.zeros(slots, wp.vec3d, device)
  touches.entryFound = wp.zeros(max(1, len(entryHold)), wp.int32, device)
  touches.entryOpenNow = wp.zeros(max(1, len(entryHold)), wp.int32,
                                  device)
  touches.holdEntry = _array(holdEntry, wp.int32, wp, -1, device)
  count = max(1, len(movers))
  touches.turning = wp.zeros(count, wp.mat33d, device)
  touches.own = wp.zeros(count, wp.mat33d, device)
  touches.spin = wp.zeros(count, wp.vec3d, device)
  touches.boxLow = wp.zeros(count, wp.vec3d, device)
  touches.boxHigh = wp.zeros(count, wp.vec3d, device)
  touches.holdOn = _array(on, wp.int32, wp, 0, device)
  touches.hold = _array(holds, wp.vec3d, wp, (0.0,) * 3, device)
  touches.pieceFirst = _array(pieceFirst, wp.int32, wp, 0, device)
  touches.pieceCount = _array(pieceCount, wp.int32, wp, 0, device)
  touches.planeFirst = _array(planeFirst, wp.int32, wp, 0, device)
  touches.planeCount = _array(planeCount, wp.int32, wp, 0, device)
  touches.normal = _array(normals, wp.vec3d, wp, (0.0,) * 3, device)
  touches.offset = _array(offsets, wp.float64, wp, 0.0, device)
  touches.reach = _array(reaches, wp.float64, wp, 0.0, device)
  touches.low = _array(lows, wp.vec3d, wp, (0.0,) * 3, device)
  touches.high = _array(highs, wp.vec3d, wp, (0.0,) * 3, device)
  return touches, _entriesOf(entries, rounds)


def _roundsOf(touches, touching: ContactForces, movers: list, where: dict,
              wp, device: str) -> list:
  """Fills 'touches' with the round contacts (each its ball, the other,
  its law, its slots: one, or a turned solid's one a piece of its
  profile, each with its stretch and scratch), every body's shape as a
  ball meets it ('_rounds.piecesOf': pieces, planes, boxes, triangles),
  and every turned solid's profile; and returns each slot's ball, the
  other's place and the slot."""
  balls, others, laws, rounds = [], [], [], []
  slotFirst, slotCount, slotOf = [], [], []
  for at, (contact, ball, other, _, _, slots) in enumerate(
      touching.roundings):
    balls.append(where[id(ball)])
    others.append(where[id(other)])
    slotFirst.append(len(rounds))
    slotCount.append(slots)
    for slot in range(slots):
      rounds.append((where[id(ball)], where[id(other)], slot))
      slotOf.append(at)
    laws.extend((contact.stiffness, contact.damping, contact.grip,
                 contact.bristle, contact.bristleDamping))
  size = max(1, len(rounds))
  touches.roundSlotFirst = _array(slotFirst, wp.int32, wp, 0, device)
  touches.roundSlotCount = _array(slotCount, wp.int32, wp, 0, device)
  touches.roundSlotOf = _array(slotOf, wp.int32, wp, 0, device)
  _turnedOf(touches, movers, wp, device)
  touches.roundBall = _array(balls, wp.int32, wp, 0, device)
  touches.roundOther = _array(others, wp.int32, wp, 0, device)
  touches.roundLaw = _array(laws, wp.float64, wp, 0.0, device)
  touches.roundOn = wp.zeros(size, wp.int32, device)
  touches.roundStretch = wp.zeros(size, wp.vec3d, device)
  touches.roundArm = wp.zeros(2 * size, wp.vec3d, device)
  touches.roundNormal = wp.zeros(size, wp.vec3d, device)
  touches.roundNoted = wp.zeros(size, wp.int32, device)
  firsts, counts, reaches = [], [], []
  planeFirst, planeCount, lows, highs, boxes = [], [], [], [], []
  triFirst, triCount, normals, offsets, corners = [], [], [], [], []
  for mover in movers:
    pieces, reach = touching.pieces.get(id(mover), ((), 0.0))
    firsts.append(len(planeFirst))
    counts.append(len(pieces))
    reaches.append(reach)
    for planes, low, high, box, triangles in pieces:
      planeFirst.append(len(normals))
      planeCount.append(len(planes))
      lows.append(low)
      highs.append(high)
      boxes.append(1 if box else 0)
      triFirst.append(len(corners) // 3)
      triCount.append(len(triangles))
      for facing, offset in planes:
        normals.append(facing)
        offsets.append(offset)
      for triangle in triangles:
        corners.extend(triangle)
  three = (0.0, 0.0, 0.0)
  touches.rpBodyFirst = _array(firsts, wp.int32, wp, 0, device)
  touches.rpBodyCount = _array(counts, wp.int32, wp, 0, device)
  touches.rpReach = _array(reaches, wp.float64, wp, 0.0, device)
  touches.rpPlaneFirst = _array(planeFirst, wp.int32, wp, 0, device)
  touches.rpPlaneCount = _array(planeCount, wp.int32, wp, 0, device)
  touches.rpLow = _array(lows, wp.vec3d, wp, three, device)
  touches.rpHigh = _array(highs, wp.vec3d, wp, three, device)
  touches.rpBox = _array(boxes, wp.int32, wp, 0, device)
  touches.rpTriFirst = _array(triFirst, wp.int32, wp, 0, device)
  touches.rpTriCount = _array(triCount, wp.int32, wp, 0, device)
  touches.rpNormal = _array(normals, wp.vec3d, wp, three, device)
  touches.rpOffset = _array(offsets, wp.float64, wp, 0.0, device)
  touches.rpCorner = _array(corners, wp.vec3d, wp, three, device)
  return rounds


def _turnedOf(touches, movers: list, wp, device: str) -> None:
  """Fills 'touches' with every turned solid's profile: for each body
  where its pieces begin and how many (none but for a turned solid),
  the bounds of its profile, and each piece's kind (0 a line, 1 an arc)
  and six numbers (a line's two ends; an arc's centre, radius, and
  angles from and to)."""
  firsts, counts, bounds, kinds, data = [], [], [], [], []
  for mover in movers:
    shape = mover.body.shape
    firsts.append(len(kinds))
    if not isinstance(shape, Turned):
      counts.append(0)
      bounds.append((0.0, 0.0, 0.0, 0.0))
      continue
    counts.append(len(shape.profile))
    bounds.append(shape.bounds())
    for piece in shape.profile:
      if piece[0] == 'line':
        kinds.append(0)
        data.extend(piece[1] + piece[2] + (0.0, 0.0))
      else:
        kinds.append(1)
        data.extend(piece[1] + (piece[2], piece[3], piece[4], 0.0))
  touches.tdFirst = _array(firsts, wp.int32, wp, 0, device)
  touches.tdCount = _array(counts, wp.int32, wp, 0, device)
  touches.tdBound = _array(bounds, wp.vec4d, wp, (0.0,) * 4, device)
  touches.tdKind = _array(kinds, wp.int32, wp, 0, device)
  touches.tdData = _array(data, wp.float64, wp, 0.0, device)


def _boundsOf(mover) -> list[tuple]:
  """Returns the box about each piece of a body's shape along its
  principal axes, its corners' least and most, a hair wide (no point
  outside it is inside the piece)."""
  shape = mover.body.shape
  if shape is None or mover.round or isinstance(shape, Turned):
    return []
  back = transposed(matrixOf(mover.axes))
  pieces = []
  for corners in _piecePoints(shape):
    arms = [applied(back, minus(shape.points[index], mover.body.centre))
            for index in corners]
    pieces.append((tuple(min(arm[i] for arm in arms) - 1e-12
                         for i in range(3)),
                   tuple(max(arm[i] for arm in arms) + 1e-12
                         for i in range(3))))
  return pieces


def _piecePoints(shape) -> list[list[int]]:
  """Returns the points of each piece of 'shape', in the order of
  'Shape.pieces' (faces sharing corners)."""
  leader = list(range(len(shape.points)))

  def leaderOf(index: int) -> int:
    """Returns the least point joined to 'index' so far."""
    while leader[index] != index:
      index = leader[index]
    return index

  for face in shape.faces:
    least = min(leaderOf(index) for index in face)
    for index in face:
      leader[leaderOf(index)] = least
  groups: dict[int, set[int]] = {}
  for face in shape.faces:
    groups.setdefault(leaderOf(face[0]), set()).update(face)
  return [sorted(groups[key]) for key in sorted(groups)]


def _readBack(movers: list, bodies, touches, entries: _Entries) -> None:
  """Puts the kernel's bodies back into 'movers': where they are, how
  they move, their bristles and their holds (only the slots holding,
  in the order of the slots)."""
  place = bodies.place.numpy().tolist()
  velocity = bodies.velocity.numpy().tolist()
  turn = bodies.turn.numpy().tolist()
  momentum = bodies.momentum.numpy().tolist()
  bristle = bodies.bristle.numpy().tolist()
  on = bodies.bristleOn.numpy().tolist()
  first = bodies.groundFirst.numpy().tolist()
  rest = bodies.rest.numpy().tolist()
  for k, mover in enumerate(movers):
    mover.rest = rest[k]
    mover.place = tuple(place[k])
    mover.velocity = tuple(velocity[k])
    mover.turn = tuple(turn[k])
    mover.momentum = tuple(momentum[k])
    mover.bristles = {}
    for at, (index, _, _) in enumerate(mover.arms):
      if on[first[k] + at]:
        mover.bristles[index] = tuple(bristle[first[k] + at])
    mover.holds = {}
  slots = len(entries.index)
  holding = numpy.flatnonzero(touches.holdOn.numpy()[:slots]).tolist()
  hold = touches.hold.numpy()
  mine, theirs, index = entries.mine, entries.theirs, entries.index
  for slot in holding:
    movers[mine[slot]].holds[(index[slot], theirs[slot])] = tuple(
      hold[slot].tolist())
  if entries.rounds:
    roundOn = touches.roundOn.numpy().tolist()
    stretch = touches.roundStretch.numpy().tolist()
    for at, (ball, other, slot) in enumerate(entries.rounds):
      if roundOn[at]:
        movers[ball].holds[(ROUND - slot, other)] = tuple(stretch[at])
