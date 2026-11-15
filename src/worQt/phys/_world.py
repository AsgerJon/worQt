"""
World is where bodies move: gravity, the ground, and time stepped on,
bodies alone or put together.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

import numpy

from ._assembly import Assembly, Drag
from ._books import Books, Grease, Sleep, Stored
from ._draws import normalDraws
from ._body import Body, State
from ._shape import Sphere
from ._turned import Turned
from ._ground import Ground
from ._poke import reachOf
from ._springs import SpringForces
from ._dampers import DamperForces
from ._contacts import ContactForces
from ._compiled import compiledRun
from ._constraints import ConstraintSolver
from ._vectors import Matrix, Quaternion, Vector
from ._welding import Welding
from ._vectors import applied, conjugate, cross, dot, matrixOf
from ._vectors import matrixProduct, minus, norm, normalised, plus
from ._vectors import product, rotated, scaled, transposed

#  The free turn split about the principal axes, each part exact: about
#  the first for half the step, the second for half, the third for all
#  of it, then back the same way (Dullweber, Leimkuhler and McLachlan,
#  1997), so the angular momentum is kept exactly, the energy within
#  the step squared, and stepping back undoes a step.
_SPLIT = ((0, 0.5), (1, 0.5), (2, 1.0), (1, 0.5), (0, 0.5))

#  The ground's steps: none longer than this share of a radian of the
#  quickest swing a body may have on it; the springs', of the quickest
#  they may swing it at (finer: their swings are what is looked at).
_SWING_SHARE = 0.25
_SPRING_SHARE = 0.05
#  The contacts' steps: two radians of their bound, which sums over the
#  modes, takes each body at its point that gives most, and every edge
#  as if pressing: tried, a tower of blocks steps stably to 13 radians
#  of it, a box on the hexapod past 16 (stepping fails past 2 of the
#  true quickest swing), so this keeps the true one at about half a
#  radian a step.
_CONTACT_SHARE = 2.0
#  How far, m, a body's lowest point must stay above the ground over a
#  run for the ground not to set its step ('stepAt').
_CLEAR = 1e-3


class Fidelity(NamedTuple):
  """
  Fidelity is how faithfully a world is stepped, traded for speed (the
  user, 2026-11-12: "the physics we implement here should be able to
  trade off fidelity for performance, so that we can get the fidelity
  back when we [are] in a more optimized setup than Qt"): 'swing', how
  many times the reference's shares of a radian ('_SWING_SHARE',
  '_SPRING_SHARE') the quickest swings of the ground and the springs may
  go in a step (1, the reference; 2, half the steps: the stiff links'
  own ringing, kHz, is followed coarser, the motions looked at, a car's
  1.5 Hz ride, hardly change; the contacts' share is not scaled: it is
  set near where they stop being steady); 'hull', whether a shape meets
  the ground only at its points on its convex hull (none inside it can
  meet flat ground first: there it is exact; on a terrain a bump
  narrower than the underside may reach a point inside unmet), else at
  every point. 'FULL' is the reference (tests, recordings, a port);
  'LIVE' what a Qt window can afford: swing 8 (user, 2026-11-13: "12
  fps.... bro...": at 2 the car on the oval took 27 ms a frame, 50 at
  its worst tenth, and slow frames stepped the world further, slower
  still; at 3, 4, 6: 20, 17, 14 ms; then, the terrain's planes fitted
  straight, not by polyfit, 6, 8, 10: 10.3, 8.7, 7.9 ms (17.7, 14.2,
  12.5 worst), the robot's laps alike to the hundredth (41.95, 37.15).
  Against the reference: a 3 s launch 15.392 m/s, at 2 15.394, at 8
  15.401; braked 1.5 s from 25 m/s 10.411, 10.496, 10.459; a 2 s turn
  at 30 m/s 31.07, 31.08, 31.13 deg). 'contacts', how many times the
  reference's share ('_CONTACT_SHARE') of the contacts' bound a step may
  go: a bound that sums over all a body's contacts is pessimistic for
  some (the car's bearing, the walker shrunk: user, 2026-11-13, "make
  the fucking ballbearing ... in a way that works at a useful
  framerate"): there 2 ran the motor's 0.3 s alike to the reference
  (ring 1.930 rad/s, gears 1.9399 to 1.9400, the balls' orbit 1.0012
  of rolling) in 10.3 s a simulated second against 18; 4 lost it (the
  ring stalled at 0.12 rad/s, a ball flung at 0.76 m/s); the balls as
  stiff as steel (a hundredth as stiff, 2.6 s against 4.0, the ground's
  swing doubled too: '_scenes.BEARING_FIDELITY').
  """

  swing: float = 1.0
  hull: bool = False
  contacts: float = 1.0


FULL = Fidelity()
LIVE = Fidelity(8.0, True)


class World(NamedTuple):
  """
  World is where bodies move, in m, kg, s, z up: 'gravity', m/s²,
  pulling every body's centre; the 'ground', flat at height nought, or
  None for none; time stepped on no longer than 'step' s at a time,
  and on the ground in whole parts of it, short enough for the ground's
  quickest swing; 'grease' shaking the bodies at random, or None for
  none. 'compiled' steps them in Warp ('_world_kernels'), held to the
  plain Python, which it otherwise uses (the reference), on 'device':
  'cpu', one thread, step by step, the kernel's reference; 'cuda' (a
  GPU, where there is one), side by side, 256 threads in one block
  ('runParallel'); 'cpu-parallel', the side by side steps by one thread
  on the CPU (to hold them to the serial ones). 'sleeping' lets bodies
  at rest sleep ('Sleep'), or None for none (the default: exact).
  'fidelity' trades faithfulness for speed ('Fidelity'; 'FULL', the
  reference, by default).
  """

  gravity: Vector = (0.0, 0.0, -9.81)
  step: float = 1e-3
  ground: Ground = None
  grease: Grease = None
  compiled: bool = True
  sleeping: Sleep = None
  device: str = 'cpu'
  fidelity: Fidelity = FULL

  def stepFor(self, body: Body) -> float:
    """The 'stepFor' method returns the longest step 'body' is moved
    in: 'step', or on the ground a whole part of it, short enough for
    the quickest swing it could have there."""
    if self.ground is None or body.shape is None:
      return self.step
    moments, axes = body.principal()
    if isinstance(body.shape, Sphere):
      arms = [body.shape.radius]
    else:
      arms = [norm(arm) + ring for _, arm, ring in _armsOf(
        body, axes, self.fidelity.hull)[0]]
    quickest = self.ground.quickest(body.mass, moments[0], arms)
    return self.step / math.ceil(self.step * quickest / (
      _SWING_SHARE * self.fidelity.swing))

  def stepAt(self, body: Body, state: State, seconds: float) -> float:
    """The 'stepAt' method returns the longest step 'body', as 'state'
    has it, is moved in over 'seconds': 'stepFor', or the world's
    'step' where it cannot reach the ground in that time (its lowest
    point now stays above it, however fast it now closes on the ground
    (its velocity toward it, square to the ground's plane about it,
    'Terrain.planeWithin', and its points' turning) and gravity could
    add; a prism riding on balls needs no step short enough for landing
    on the ground; nor a car running along a banked straight, which
    counted at its whole speed set a chassis's step at 40 m/s). The ball
    holding the body whole ('reachOf') is asked first: high enough, its
    points are not placed (a 21 m ring's thousand corners were, every
    frame)."""
    if self.ground is None or body.shape is None:
      return self.step
    whole = reachOf(body)
    speed = norm(state.velocity) + norm(state.spin) * whole
    fall = speed * seconds + 0.5 * norm(self.gravity) * seconds * seconds
    if state.place[2] - self.ground.topOf() - whole > fall + _CLEAR:
      return self.step
    terrain = self.ground.terrain
    reach = (body.shape.radius if isinstance(body.shape, Sphere)
             else _armsOf(body, body.principal()[1], self.fidelity.hull)[1])
    x0 = y0 = level = gx = gy = over = 0.0
    if terrain is not None:
      far = reach + math.hypot(state.velocity[0], state.velocity[1]) * (
        seconds) + 1.0
      x, y = state.place[0], state.place[1]
      x0, y0, level, gx, gy, over, _ = terrain.planeWithin(
        (x - far, y - far), (x + far, y + far))
    size = math.sqrt(gx * gx + gy * gy + 1.0)
    if terrain is None and isinstance(body.shape, Sphere):
      lowest = state.place[2] - reach
    else:
      lowest = (min(place[2] - level - gx * (place[0] - x0)
                    - gy * (place[1] - y0)
                    for _, place in _groundPlaces(body, state, self.ground,
                                                  self.fidelity.hull))
                - over) / size
    up = (-gx / size, -gy / size, 1.0 / size)
    speed = max(0.0, -dot(state.velocity, up)) + norm(state.spin) * reach
    fall = speed * seconds + 0.5 * norm(self.gravity) * seconds * seconds
    if lowest > fall + _CLEAR:
      return self.step
    return self.stepFor(body)

  def advanced(self, body: Body, state: State, seconds: float) -> State:
    """The 'advanced' method returns 'body' 'seconds' on from 'state',
    alone in the world (see 'advancedAll')."""
    return self.advancedAll(Assembly((body,)), (state,), seconds)[0]

  def advancedAll(self, assembly: Assembly, states: tuple[State, ...],
                  seconds: float, start: float = 0.0) -> tuple[State, ...]:
    """The 'advancedAll' method returns the bodies of 'assembly'
    'seconds' on from 'states' at time 'start' (see 'booked')."""
    return self.booked(assembly, states, seconds, start, Books())[0]

  def booked(self, assembly: Assembly, states: tuple[State, ...],
             seconds: float, start: float,
             books: Books) -> tuple[tuple[State, ...], Books]:
    """The 'booked' method returns the bodies of 'assembly' 'seconds' on
    from 'states' at time 'start', and 'books' with the run's energy
    booked on. The run goes in steps alike, none longer than any body's
    'stepFor', the springs' 'springStepFor' or what the contacts allow:
    each a kick for half the step from gravity, the ground, the springs,
    the contacts and the grease as the bodies are then; the ties' and
    actuators' pulls, just enough that their rules are kept after the
    bodies are moved and turned freely for the whole step (tied points
    together, actuators at their strokes' lengths), with the dampers'
    pushes; another half kick; and
    the pulls again, just enough that the rules keep moving as they
    must, with the dampers' pushes again (velocity Verlet with RATTLE: a
    fall under gravity alone is exact, a body at rest stays so, rules
    never drift; each damper pushing on the average of how fast it
    lengthens before and after each half, solved with the pulls, so it
    knows how the actuators will move its ends: the trapezoidal rule,
    right to the step squared and steady however stiff). Welded bodies
    are moved as the one body they make ('Welding'), parts welded moving
    apart losing what their snap together takes."""
    if seconds <= 0.0:
      return tuple(states), books
    if (assembly.cordLines or assembly.airs or assembly.crowds
        or assembly.tyres or assembly.brakes or assembly.hinges
        or assembly.slides or assembly.turnPoints or assembly.racks
        or assembly.rams or assembly.humps or assembly.meshes
        or assembly.housed
        or any(damper.rebound is not None
               for damper in assembly.dampers)):
      raise ValueError('cord lines, air, crowds, tyres, disc brakes, '
                       'hinges, slides, turn points, racks, gears, housed '
                       'bodies, rams, humps and dampers with a rebound of '
                       'their own are in the small steps only')
    if assembly.welds:
      welding = Welding(assembly, states)
      books = books.plus(Books(0.0, 0.0, welding.lost))
      moved, books = self.booked(welding.joined, welding.states, seconds,
                                 start, books)
      return welding.split(moved), books
    longest = min((self.stepAt(assembly.bodies[index], states[index],
                               seconds)
                   for index in _movingOf(self, assembly, states, seconds)
                   if index not in assembly.fixed),
                  default=self.step)
    longest = min(longest, self.springStepFor(assembly))
    if assembly.contacts:
      quickest = _contactBoundOf(self, assembly, states)
      longest = min(longest, self.step / math.ceil(
        self.step * quickest / (_CONTACT_SHARE
                                * self.fidelity.contacts)))
    count = max(1, math.ceil(seconds / longest - 1e-9))
    h = seconds / count
    movers = [_Moving(self, body, state, h)
              for body, state in zip(assembly.bodies, states)]
    for index in _freeOf(assembly):
      movers[index].free = True
    for index in assembly.fixed:
      movers[index].fix()
    if self.compiled:
      done = compiledRun(self, assembly, states, movers, count, h, start,
                         books)
      if done is not None:
        return done
    held = assembly.ties or assembly.actuators or assembly.dampers
    held = ConstraintSolver(assembly.ties, assembly.actuators,
                            assembly.dampers, movers) if held else None
    springs = assembly.springs
    springs = SpringForces(springs, movers) if springs else None
    touching = assembly.contacts
    touching = ContactForces(touching, movers) if touching else None
    motors = assembly.motors + assembly.drags
    first = round(start / h)
    pressed = sum(mover.groundStored() for mover in movers)
    leaning = touching.stored() if touching is not None else 0.0
    work = {'ground': 0.0, 'damper': 0.0, 'actuator': 0.0, 'grease': 0.0,
            'tie': 0.0, 'contact': 0.0}
    for step in range(count):
      now = start + (step + 1) * h
      if self.sleeping is not None:
        _woken(movers)
      self._kicked(movers, springs, touching, held, h, (first + step, 0),
                   motors)
      if held is not None:
        held.pulled(h, now)
      for mover in movers:
        mover.drift(h)
      if touching is not None:
        touching.rolled(h)
      self._kicked(movers, springs, touching, held, h, (first + step, 1),
                   motors)
      if held is not None:
        held.steadied(h, now)
      for mover in movers:
        for kind, worked in mover.worked().items():
          work[kind] += worked
      if self.sleeping is not None:
        _slept(movers, self.sleeping, h)
    pressed -= sum(mover.groundStored() for mover in movers)
    if touching is not None:
      leaning -= touching.stored()
    books = books.plus(Books(pressed - work['ground'], -work['damper'],
                             0.0, work['actuator'], work['grease'],
                             work['tie'], leaning - work['contact']))
    return tuple(mover.state() for mover in movers), books

  def _kicked(self, movers: list, springs: SpringForces | None,
              touching: ContactForces | None,
              held: ConstraintSolver | None, h: float,
              when: tuple[int, int], motors: tuple) -> None:
    """The '_kicked' method kicks 'movers' for half of 'h': gravity, the
    ground, the springs, the motors (and the air's drags among them), the
    contacts and the grease, 'held'
    noting first how its rules moved before. 'when' is the step's place
    in time and which half it is, for the grease."""
    if held is not None:
      held.remember()
    for mover in movers:
      mover.kick()
    if springs is not None:
      springs.kick(0.5 * h)
    for motor in motors:
      if isinstance(motor, Drag):
        _dragKick(motor, movers, 0.5 * h)
      else:
        _motorKick(motor, movers, 0.5 * h)
    if touching is not None:
      touching.kick(0.5 * h)
    if self.grease is not None:
      for index, mover in enumerate(movers):
        draws = normalDraws(self.grease.seed, when[0], when[1], index)
        mover.greased(self.grease, draws)

  def springStepFor(self, assembly: Assembly) -> float:
    """The 'springStepFor' method returns the longest step the springs
    of 'assembly' let it be moved in: 'step', or a whole part of it,
    short enough for the quickest they could swing it at. Each end of a
    spring gives as much as the least mass it could have, its 'give'
    (one over the mass, and its arm squared over the least moment); no
    swing is faster than the lesser of two bounds: the sum over the
    springs of each one's stiffness times both its ends' give (the
    trace: exact for one spring), and Collatz and Wielandt's on how
    hard the springs couple the bodies, each end giving as much as it
    truly can (its arm's turning by the moments about the axes it
    turns about: a steering column's tie rods hang at its plate, near
    its axis, far from its middle; '_perronBoundOf': a tyre's hundreds
    of springs, a few at each lump, swing no faster than a few do).
    Kept per assembly ('_SPRING_BOUNDS')."""
    for kept, bound in _SPRING_BOUNDS:
      if kept is assembly:
        quickest = bound
        break
    else:
      quickest = _springBoundOf(assembly)
      _SPRING_BOUNDS.insert(0, (assembly, quickest))
      del _SPRING_BOUNDS[8:]
    if quickest == 0.0:
      return self.step
    return self.step / math.ceil(self.step * quickest / (
      _SPRING_SHARE * self.fidelity.swing))

  def pullsOf(self, assembly: Assembly, states: tuple[State, ...],
              time: float = 0.0) -> tuple[Vector, ...]:
    """The 'pullsOf' method returns how hard each tie of 'assembly'
    pulls its first body at its point as the bodies are in 'states' at
    'time', N, in the world's frame (the second is pulled as hard the
    other way): just what keeps the tied points together, everything
    else pushing as it does."""
    return self.heldBy(assembly, states, time)[0]

  def pushesOf(self, assembly: Assembly, states: tuple[State, ...],
               time: float = 0.0) -> tuple[float, ...]:
    """The 'pushesOf' method returns how hard each actuator of
    'assembly' pushes its ends apart as the bodies are in 'states' at
    'time', N (pulling them together below nought): just what keeps it
    at its stroke, everything else pushing as it does."""
    return self.heldBy(assembly, states, time)[1]

  def heldBy(self, assembly: Assembly, states: tuple[State, ...],
             time: float) -> tuple[tuple, tuple]:
    """The 'heldBy' method returns the ties' pulls and the actuators'
    pushes as 'pullsOf' and 'pushesOf' have them."""
    if assembly.welds:
      welding = Welding(assembly, states)
      return self.heldBy(welding.joined, welding.states, time)
    movers = [_Moving(self, body, state, 0.0)
              for body, state in zip(assembly.bodies, states)]
    besides = SpringForces(assembly.springs, movers).forces()
    for more in (DamperForces(assembly.dampers, movers).forces(),
                 ContactForces(assembly.contacts, movers).forces()):
      for key, (force, torque) in more.items():
        had = besides.get(key, ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        besides[key] = (plus(had[0], force), plus(had[1], torque))
    solver = ConstraintSolver(assembly.ties, assembly.actuators, (),
                              movers)
    return solver.pullsAndPushes(besides, time)

  def groundPushOf(self, body: Body, state: State) -> Vector:
    """The 'groundPushOf' method returns the ground's push on 'body' in
    'state', N, in the world's frame, its bristles as they are: what a
    scale under it reads (and, along the ground, what holds it)."""
    if self.ground is None:
      return 0.0, 0.0, 0.0
    moving = _Moving(self, body, state, 0.0)
    if not moving.arms or moving._clear():
      return 0.0, 0.0, 0.0
    return moving.groundPush(dict(moving.bristles))[0]

  def energyOf(self, body: Body, state: State) -> float:
    """The 'energyOf' method returns the body's energy in 'state':
    moving, turning, its height in 'gravity' (nought at the origin),
    and what the ground and its bristles hold, J."""
    energy = body.kineticOf(state) - body.mass * dot(self.gravity,
                                                     state.place)
    if self.ground is None or body.shape is None:
      return energy
    bristles = {index: (x, y) for index, x, y in state.bristles}
    return energy + self.ground.storedIn(_groundPlaces(
      body, state, self.ground, self.fidelity.hull), bristles)

  def storedOf(self, assembly: Assembly,
               states: tuple[State, ...]) -> Stored:
    """The 'storedOf' method returns the energy the bodies of 'assembly'
    hold in 'states', line by line."""
    kinetic = gravity = ground = springs = 0.0
    for body, state in zip(assembly.bodies, states):
      kinetic += body.kineticOf(state)
      gravity -= body.mass * dot(self.gravity, state.place)
      if self.ground is not None and body.shape is not None:
        bristles = {index: (x, y) for index, x, y in state.bristles}
        ground += self.ground.storedIn(_groundPlaces(
          body, state, self.ground, self.fidelity.hull), bristles)
    for spring in assembly.springs:
      ends = []
      for index, point in ((spring.first, spring.firstPoint),
                           (spring.second, spring.secondPoint)):
        if index is None:
          ends.append(point)
        else:
          ends.append(assembly.bodies[index].placeOf(states[index], point))
      springs += spring.storedOf(ends[0], ends[1])
    contacts = 0.0
    if assembly.contacts:
      movers = [_Moving(self, body, state, 0.0)
                for body, state in zip(assembly.bodies, states)]
      contacts = ContactForces(assembly.contacts, movers).stored()
    return Stored(kinetic, gravity, springs, ground, contacts)

  def energyOfAll(self, assembly: Assembly,
                  states: tuple[State, ...]) -> float:
    """The 'energyOfAll' method returns the energy of all the bodies of
    'assembly' in 'states', and what its springs and contacts hold
    (ties, welds, dampers and actuators hold none), J."""
    return self.storedOf(assembly, states).total()

class _Moving:
  """
  _Moving is a body as the stepping holds it, kicked 'h' s at a time:
  where it is, its velocity, its principal axes' 'turn' and its angular
  'momentum' along them; its points that may touch the ground ('arms',
  each its index and arm from the centre along the principal axes, none
  lower than 'reach' below the centre) and their bristles. A ball
  ('round' its radius, else nought) touches the ground at its lowest
  point, straight under its centre whichever way it has turned, one
  bristle holding it there whose anchor rolls along with the ball, so
  rolling stretches it not at all and only slipping does.
  """

  def __init__(self, world: World, body: Body, state: State,
               h: float) -> None:
    self.world, self.body, self.mass = world, body, body.mass
    self.moments, self.axes = body.principal()
    self.turn = product(state.turn, self.axes)
    held = applied(transposed(matrixOf(self.turn)), state.spin)
    self.momentum = (self.moments[0] * held[0], self.moments[1] * held[1],
                     self.moments[2] * held[2])
    self.place, self.velocity = state.place, state.velocity
    arms = _armsOf(body, self.axes, world.fidelity.hull) if (
      world.ground) else ((), 0.0)
    self.arms, self.reach = arms
    shape = body.shape
    self.round = shape.radius if isinstance(shape, Sphere) else 0.0
    self.roll = None
    if isinstance(shape, Turned):
      self.roll = applied(transposed(matrixOf(self.axes)),
                          (0.0, 0.0, 1.0))
    self.bristles = {index: (x, y) for index, x, y in state.bristles}
    self.holds = {(index, other): (x, y, z)
                  for index, other, x, y, z in state.holds}
    self.rest, self.free = state.rest, False
    self.h = 0.5 * h
    self.fall = scaled(world.gravity, 0.5 * h)
    self.given: dict[str, tuple[Vector, Vector]] = {}
    self.drifting = (self.velocity, (0.0, 0.0, 0.0))

  def fix(self, ) -> None:
    """The 'fix' method makes the body part of the world ('Fixed'):
    infinitely heavy, still, never free to sleep."""
    self.mass = math.inf
    self.moments = (math.inf, math.inf, math.inf)
    self.momentum, self.velocity = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    self.drifting, self.free = (self.velocity, (0.0, 0.0, 0.0)), False

  def fixed(self, ) -> bool:
    """The 'fixed' method tells whether the body is part of the
    world."""
    return math.isinf(self.mass)

  def state(self, ) -> State:
    """The 'state' method returns the body's state as it is now."""
    spin = applied(matrixOf(self.turn), self.spinHeld(self.momentum))
    kept = tuple((index, x, y)
                 for index, (x, y) in sorted(self.bristles.items()))
    holds = tuple((index, other, x, y, z)
                  for (index, other), (x, y, z)
                  in sorted(self.holds.items()))
    return State(self.place, product(self.turn, conjugate(self.axes)),
                 self.velocity, spin, kept, holds, self.rest)

  def asleep(self, ) -> bool:
    """The 'asleep' method tells whether the body sleeps: its world
    lets bodies sleep, it may ('free': held by nothing but contacts and
    the ground), and it has been still long enough."""
    sleeping = self.world.sleeping
    if sleeping is None or not self.free:
      return False
    return self.rest >= sleeping.settle

  def still(self, ) -> bool:
    """The 'still' method tells whether the body moves and turns slower
    than its world's sleeping says is still."""
    sleeping = self.world.sleeping
    return (norm(self.velocity) < sleeping.speed
            and norm(self.spin()) < sleeping.spin)

  def spinHeld(self, momentum: Vector) -> Vector:
    """The 'spinHeld' method returns the spin along the principal axes
    of the angular 'momentum' along them."""
    return (momentum[0] / self.moments[0], momentum[1] / self.moments[1],
            momentum[2] / self.moments[2])

  def spin(self, ) -> Vector:
    """The 'spin' method returns the body's spin in the world now."""
    return applied(matrixOf(self.turn), self.spinHeld(self.momentum))

  def inward(self, point: Vector) -> Vector:
    """The 'inward' method returns 'point', in the body's own frame, as
    an arm from its centre along its principal axes."""
    return applied(transposed(matrixOf(self.axes)),
                   minus(point, self.body.centre))

  def reaching(self, turning: Matrix, arm: Vector,
               ring: float) -> Vector:
    """The 'reaching' method returns the arm, in the world, from the
    centre to where the point 'arm' (along the principal axes) may touch
    the ground, the body turned by 'turning': for a ball its lowest
    point, straight down, whichever way it has turned; for a turned
    solid's circle of radius 'ring' about its axis, its middle at
    'arm', the circle's lowest point."""
    terrain = self.world.ground.terrain
    if self.round:
      if terrain is None:
        return 0.0, 0.0, -self.round
      return scaled(terrain.normalAt(self.place[0], self.place[1]),
                    -self.round)
    if ring:
      axis = applied(turning, self.roll)
      way = _lowestWay(axis)
      if terrain is not None:
        middle = plus(self.place, applied(turning, arm))
        way = _deepestWay(axis, terrain.normalAt(middle[0], middle[1]))
      return plus(applied(turning, arm), scaled(way, ring))
    return applied(turning, arm)

  def outward(self, arm: Vector) -> Vector:
    """The 'outward' method returns 'arm', along the principal axes, in
    the world as the body is turned now."""
    return applied(matrixOf(self.turn), arm)

  def softness(self, ) -> Matrix:
    """The 'softness' method returns the inverse of the body's inertia
    about its centre, in the world as it is turned now."""
    turning = matrixOf(self.turn)
    inverse = ((1.0 / self.moments[0], 0.0, 0.0),
               (0.0, 1.0 / self.moments[1], 0.0),
               (0.0, 0.0, 1.0 / self.moments[2]))
    return _turnedMatrix(turning, inverse)

  def pushed(self, impulse: Vector, arm: Vector, kind: str | None) -> None:
    """The 'pushed' method gives the body 'impulse', N s, at 'arm' from
    its centre, in the world, booking it under 'kind' (None for what is
    held as energy, not booked: gravity, springs); a body asleep takes
    none."""
    if self.asleep():
      return
    self.velocity = plus(self.velocity, scaled(impulse, 1.0 / self.mass))
    twist = applied(transposed(matrixOf(self.turn)), cross(arm, impulse))
    self.momentum = plus(self.momentum, twist)
    if kind is not None:
      self.book(kind, impulse, cross(arm, impulse))

  def book(self, kind: str, impulse: Vector, twist: Vector) -> None:
    """The 'book' method notes 'impulse', N s, and angular 'twist', N m
    s about the centre, in the world, given the body this step under
    'kind'."""
    had = self.given.get(kind, ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
    self.given[kind] = (plus(had[0], impulse), plus(had[1], twist))

  def worked(self, ) -> dict[str, float]:
    """The 'worked' method returns the work each kind of push did on the
    body this step, J, and forgets them: what each gave, over both
    halves, times how fast the body moved and turned while it drifted
    (force times how far its point went: so a tie whose points move
    together does none, and the books balance but for a hair that comes
    and goes)."""
    moving, turning = self.drifting
    out = {kind: dot(impulse, moving) + dot(twist, turning)
           for kind, (impulse, twist) in self.given.items()}
    self.given = {}
    return out

  def drifted(self, velocity: Vector, momentum: Vector,
              h: float) -> tuple[Vector, Quaternion, Vector]:
    """The 'drifted' method returns where the body would be, its turn
    and its angular momentum along its principal axes, moved and turned
    freely for 'h' s from where it is now, at 'velocity' with angular
    'momentum' along its principal axes."""
    place = plus(self.place, scaled(velocity, h))
    turn, momentum = _turnedFreely(self.turn, momentum, self.moments, h)
    return place, turn, momentum

  def drift(self, h: float) -> None:
    """The 'drift' method moves and turns the body freely for 'h' s,
    noting how fast it moved and turned meanwhile: its velocity, and its
    spin on average (it may change as the body turns freely); a body
    asleep, or part of the world, stays where it is."""
    if self.asleep() or self.fixed():
      self.drifting = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
      return
    setting = self.spin()
    if self.round and 0 in self.bristles:
      x, y = self.bristles[0]
      self.bristles[0] = (x + self.round * setting[1] * h,
                          y - self.round * setting[0] * h)
    if self.roll is not None and self.bristles:
      self._rolled(setting, h)
    moved = self.drifted(self.velocity, self.momentum, h)
    self.place, self.turn, self.momentum = moved
    self.drifting = (self.velocity, scaled(plus(setting, self.spin()), 0.5))

  def _rolled(self, setting: Vector, h: float) -> None:
    """Rolls the bristles of a turned solid's circles along with it for
    'h' s at spin 'setting': each anchor moved as the circle's lowest
    point rolls on, so rolling stretches it not at all and only slipping
    does; with the ground's 'relaxation', let go of as much of its
    stretch as the share of that length rolled (first, where the point
    is now: so rolling alone leaves it unstretched)."""
    turning = matrixOf(self.turn)
    relaxation = self.world.ground.relaxation
    for index, arm, ring in self.arms:
      if index not in self.bristles:
        continue
      out = self.reaching(turning, arm, ring)
      rolling = minus(out, applied(turning, arm))
      dx = -(setting[1] * rolling[2] - setting[2] * rolling[1]) * h
      dy = -(setting[2] * rolling[0] - setting[0] * rolling[2]) * h
      x, y = self.bristles[index]
      if relaxation > 0.0:
        share = min(1.0, math.sqrt(dx * dx + dy * dy) / relaxation)
        x = x + (self.place[0] + out[0] - x) * share
        y = y + (self.place[1] + out[1] - y) * share
      self.bristles[index] = (x + dx, y + dy)

  def twisted(self, twist: Vector, kind: str) -> None:
    """The 'twisted' method gives the body the angular impulse 'twist',
    N m s about its centre, in the world, booked under 'kind'; a body
    asleep takes none."""
    if self.asleep():
      return
    self.momentum = plus(self.momentum,
                         applied(transposed(matrixOf(self.turn)), twist))
    self.book(kind, (0.0, 0.0, 0.0), twist)

  def kinetic(self, ) -> float:
    """The 'kinetic' method returns the body's kinetic energy now, J
    (none, part of the world)."""
    if self.fixed():
      return 0.0
    m = self.momentum
    return (0.5 * self.mass * dot(self.velocity, self.velocity)
            + 0.5 * (m[0] * m[0] / self.moments[0]
                     + m[1] * m[1] / self.moments[1]
                     + m[2] * m[2] / self.moments[2]))

  def kick(self, ) -> None:
    """The 'kick' method kicks the body for half the step: gravity, and
    the ground where its points may touch it (booked); not asleep, nor
    part of the world."""
    if self.asleep() or self.fixed():
      return
    self.velocity = plus(self.velocity, self.fall)
    if not self.arms or self._clear():
      self.bristles.clear()
      return
    force, torque = self.groundPush(self.bristles)
    self.velocity = plus(self.velocity, scaled(force, self.h / self.mass))
    twist = applied(transposed(matrixOf(self.turn)), torque)
    h = self.h
    self.momentum = (self.momentum[0] + h * twist[0],
                     self.momentum[1] + h * twist[1],
                     self.momentum[2] + h * twist[2])
    self.book('ground', scaled(force, h), scaled(torque, h))

  def _clear(self, ) -> bool:
    """Tells whether the body is too high to touch the ground: its
    centre higher over the ground's top than it reaches."""
    return self.place[2] - self.world.ground.topOf() >= self.reach

  def groundStored(self, ) -> float:
    """The 'groundStored' method returns the energy the ground and the
    body's bristles hold as it is now, J."""
    if not self.arms or self._clear():
      return 0.0
    turning = matrixOf(self.turn)
    places = [(index, plus(self.place, self.reaching(turning, arm, ring)))
              for index, arm, ring in self.arms]
    return self.world.ground.storedIn(places, self.bristles)

  def greased(self, grease: Grease, draws: tuple[float, ...]) -> None:
    """The 'greased' method shakes the body for half the step, at
    random by 'draws' (six normal draws), as 'grease' says (the velocity
    and the spin along its principal axes each changed by a normal draw
    of their shaking times the square root of the half step: white
    noise, so how far it wanders does not hang on the step), booked; not
    asleep, nor part of the world."""
    if self.asleep() or self.fixed():
      return
    root = math.sqrt(self.h)
    shaken = (grease.shake * root * draws[0],
              grease.shake * root * draws[1],
              grease.shake * root * draws[2])
    self.velocity = plus(self.velocity, shaken)
    spun = (grease.spin * root * draws[3], grease.spin * root * draws[4],
            grease.spin * root * draws[5])
    given = (self.moments[0] * spun[0], self.moments[1] * spun[1],
             self.moments[2] * spun[2])
    self.momentum = plus(self.momentum, given)
    self.book('grease', scaled(shaken, self.mass),
              applied(matrixOf(self.turn), given))

  def groundPush(self, bristles: dict) -> tuple[Vector, Vector]:
    """The 'groundPush' method returns the ground's push on the body as
    it is now, the force and the torque about its centre, holding
    'bristles' to it."""
    turning, spin = matrixOf(self.turn), self.spin()
    places, velocities, outs = [], [], []
    for index, arm, ring in self.arms:
      out = self.reaching(turning, arm, ring)
      places.append((index, plus(self.place, out)))
      velocities.append(plus(self.velocity, cross(spin, out)))
      outs.append(out)
    forces = self.world.ground.pushed(places, velocities, bristles)
    force, torque = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    for out, push in zip(outs, forces):
      force = plus(force, push)
      torque = plus(torque, cross(out, push))
    return force, torque

  def forces(self, ) -> tuple[Vector, Vector]:
    """The 'forces' method returns the force and the torque about its
    centre on the body as it is now, but for the ties: gravity, and the
    ground (its bristles left as they are)."""
    weight = scaled(self.world.gravity, self.mass)
    if not self.arms or self._clear():
      return weight, (0.0, 0.0, 0.0)
    force, torque = self.groundPush(dict(self.bristles))
    return plus(weight, force), torque


#  The contacts' bound on how fast they could swing the bodies hangs
#  on the assembly alone (its bodies' shapes and masses, its contacts),
#  so it is worked out once for each of the last few assemblies and
#  kept, each with its assembly.
_BOUNDS: list = []
#  The springs' step bounds of the last few assemblies, by identity.
_SPRING_BOUNDS: list = []


def _springBoundOf(assembly: Assembly) -> float:
  """Returns how fast, rad/s, the springs of 'assembly' could at most
  swing it: the lesser of the trace bound and Collatz and Wielandt's
  (see 'World.springStepFor'); nought with no springs."""
  gives, total, among = {}, 0.0, {}

  def giveOf(index: int | None, point: tuple) -> tuple[float, float]:
    """Returns how much the point gives, as the trace bound takes it
    (its arm squared over the least moment) and as it truly does at
    most (the greatest eigenvalue of [r]x' I^-1 [r]x, r the arm along
    the principal axes), each with one over the mass."""
    if index is None:
      return 0.0, 0.0
    if (index, point) not in gives:
      body = assembly.bodies[index]
      moments, axes = body.principal()
      arm = minus(point, body.centre)
      r = applied(transposed(matrixOf(axes)), arm)
      crossing = numpy.array(((0.0, -r[2], r[1]), (r[2], 0.0, -r[0]),
                              (-r[1], r[0], 0.0)))
      soft = numpy.diag([1.0 / moments[0], 1.0 / moments[1],
                         1.0 / moments[2]])
      most = float(numpy.linalg.eigvalsh(crossing.T @ soft
                                         @ crossing)[-1])
      reach = norm(arm)
      gives[index, point] = (1.0 / body.mass + reach * reach / moments[0],
                             1.0 / body.mass + max(0.0, most))
    return gives[index, point]

  for spring in assembly.springs:
    first, firstMost = giveOf(spring.first, spring.firstPoint)
    second, secondMost = giveOf(spring.second, spring.secondPoint)
    total += spring.stiffness * (first + second)
    across = spring.stiffness * math.sqrt(firstMost * secondMost)
    for index, other, own in ((spring.first, spring.second, firstMost),
                              (spring.second, spring.first, secondMost)):
      if index is None:
        continue
      row = among.setdefault(index, {})
      row[index] = row.get(index, 0.0) + spring.stiffness * own
      if other is not None:
        row[other] = row.get(other, 0.0) + across
  if total == 0.0:
    return 0.0
  return math.sqrt(min(total, _perronBoundOf(among)))


def _perronBoundOf(among: dict) -> float:
  """Returns a bound on how large the eigenvalues of the matrix 'among'
  (rows by body, each its columns by body: how hard each spring couples
  them, as one over their give) can be: the matrix of how its blocks
  couple bounds them by its own largest eigenvalue, and for any weights
  all above nought that is at most the largest of its rows' weighted
  sums over their own weight (Collatz and Wielandt); the weights are
  bettered by multiplying by the matrix, the least bound kept. With
  every weight one this is Gershgorin's, row by row."""
  weights = {index: 1.0 for index in among}
  best = math.inf
  for _ in range(_PERRON_ROUNDS):
    weighted = {index: sum(value * weights[other]
                           for other, value in row.items())
                for index, row in among.items()}
    best = min(best, max(weighted[index] / weights[index]
                         for index in among))
    most = max(weighted.values())
    weights = {index: max(value / most, 1e-12)
               for index, value in weighted.items()}
  return best


#  How many times the weights of '_perronBoundOf' are bettered.
_PERRON_ROUNDS = 40


def _contactBoundOf(world: World, assembly: Assembly,
                    states: tuple[State, ...]) -> float:
  """Returns 'ContactForces.quickest' for 'assembly', worked out only
  when it was not lately."""
  for at, (kept, quickest) in enumerate(_BOUNDS):
    if kept is assembly:
      if at:
        _BOUNDS.insert(0, _BOUNDS.pop(at))
      return quickest
  movers = [_Moving(world, body, state, 0.0)
            for body, state in zip(assembly.bodies, states)]
  quickest = ContactForces(assembly.contacts, movers).quickest()
  _BOUNDS.insert(0, (assembly, quickest))
  del _BOUNDS[8:]
  return quickest


def _movingOf(world: World, assembly: Assembly, states: tuple,
              seconds: float) -> list[int]:
  """The '_movingOf' function returns the bodies of 'assembly' that may
  move in a run of 'seconds' from 'states', so their steps count: all,
  unless the world lets bodies sleep; then every body awake, and every
  one asleep that may be woken in the run: one whose ball (about its
  centre, holding its shape whole) meets an awake body's as far as that
  may go in the time, or a woken one's as far as it may then go (twice
  as fast as the fastest awake body, gravity besides). One asleep and
  out of reach stays where it is, whatever step it would need. With no
  ground every body's step is the world's: all are taken, unlooked."""
  sleep, count = world.sleeping, len(states)
  if sleep is None or world.ground is None:
    return list(range(count))
  free = _freeOf(assembly)
  asleep = [index for index in free if states[index].rest >= sleep.settle]
  if not asleep:
    return list(range(count))
  sleeping = set(asleep)
  reaches = [reachOf(body) for body in assembly.bodies]
  fall = 0.5 * norm(world.gravity) * seconds * seconds
  out, reaching, fastest = [], [], 0.0
  for index in range(count):
    if index in sleeping:
      continue
    out.append(index)
    state, reach = states[index], reaches[index]
    speed = norm(state.velocity) + norm(state.spin) * reach
    fastest = max(fastest, speed)
    reaching.append((state.place, reach + speed * seconds + fall))
  margin = 2.0 * fastest * seconds + fall
  while reaching and asleep:
    place, far = reaching.pop()
    waiting = []
    for index in asleep:
      reach = reaches[index]
      if norm(minus(states[index].place, place)) <= far + reach + margin:
        out.append(index)
        reaching.append((states[index].place, reach + margin))
      else:
        waiting.append(index)
    asleep = waiting
  return out


def _freeOf(assembly: Assembly) -> set[int]:
  """The '_freeOf' function returns the bodies of 'assembly' that may
  sleep: those with a shape, held by nothing but contacts and the
  ground (on no tie, actuator, spring, damper or motor)."""
  held = set()
  for link in (assembly.ties + assembly.actuators + assembly.springs
               + assembly.dampers):
    held.update(index for index in (link.first, link.second)
                if index is not None)
  for motor in assembly.motors:
    held.update(index for index in (motor.first, motor.second,
                                    motor.bearer) if index is not None)
  return {index for index, body in enumerate(assembly.bodies)
          if body.shape is not None and index not in held
          and index not in assembly.fixed}


def _motorKick(motor: object, movers: list, hh: float) -> None:
  """Gives the motor's twist for 'hh' s: its second body twisted about
  its axis by its drive's torque (a servo's worked out now,
  '_servoTorque'), its first (if a body) back."""
  second = movers[motor.second]
  along = applied(transposed(matrixOf(second.axes)), motor.axis)
  axis = applied(matrixOf(second.turn), along)
  drive = motor.drive
  if motor.bearer is not None:
    _shaftKick(motor, movers, axis, hh)
    return
  torque = drive.torque
  if drive.stiffness > 0.0 or drive.damping > 0.0:
    first = None if motor.first is None else movers[motor.first]
    torque = _servoTorque(drive, first, second, motor.axis, axis)
  twist = scaled(axis, torque * hh)
  second.twisted(twist, 'actuator')
  if motor.first is not None:
    movers[motor.first].twisted(scaled(twist, -1.0), 'actuator')


def _dragKick(drag: object, movers: list, hh: float) -> None:
  """Gives the air's drag on its body for 'hh' s ('Drag'), booked as a
  damper's heat."""
  mover = movers[drag.body]
  velocity = mover.velocity
  pull = -0.5 * drag.density * drag.area * norm(velocity) * hh
  mover.pushed(scaled(velocity, pull), (0.0, 0.0, 0.0), 'damper')


def _shaftKick(motor: object, movers: list, axis: Vector,
               hh: float) -> None:
  """Gives a driveshaft's twist for 'hh' s ('Motor' with a bearer): its
  second body about its 'axis' (in the world), its first back along the
  bisector of the shaft's line (from its point on the first to its point
  on the second, taken the way 'axis' points) and the axis, its bearer
  the difference (a constant-velocity joint's moment lies along the
  bisector of the shafts it joins: so the bearer, the knuckle, takes
  half the shaft's angle's cross twist; taking all of it, a rear wheel
  braked on 41 mm of droop toed out 1.5 degrees); its
  drive's torque, less, with damping, a brake's on the shaft (an
  inboard brake: the damping times how fast the shaft turns, the rate
  its twists work at, no more than 'most')."""
  first, second = movers[motor.first], movers[motor.second]
  inner = plus(first.place, first.outward(first.inward(motor.firstPoint)))
  outer = plus(second.place,
               second.outward(second.inward(motor.secondPoint)))
  line = minus(outer, inner)
  line = scaled(line, (1.0 if dot(line, axis) >= 0.0 else -1.0)
                / norm(line))
  drive = motor.drive
  torque = drive.torque
  if drive.slip > 0.0 and torque != 0.0:
    torque *= _tractionShare(drive, first, second, axis, torque)
  middle = scaled(plus(line, axis), 0.5)
  if drive.damping > 0.0:
    bearer = movers[motor.bearer]
    rate = (dot(axis, minus(second.spin(), bearer.spin()))
            + dot(middle, minus(bearer.spin(), first.spin())))
    torque -= max(-drive.most, min(drive.most, drive.damping * rate))
  torque *= hh
  second.twisted(scaled(axis, torque), 'actuator')
  movers[motor.bearer].twisted(scaled(minus(middle, axis), torque),
                               'actuator')
  first.twisted(scaled(middle, -torque), 'actuator')


def _tractionShare(drive: object, first: object, second: object,
                   axis: Vector, torque: float) -> float:
  """Returns the share of its torque a driveshaft with traction control
  ('Drive.slip') gives now: all of it while its wheel's rim outruns the
  first body's speed along its own x (the way the torque drives it) by
  no more than 'slip' of that speed (3 m/s at least), none by twice."""
  own = transposed(matrixOf(first.axes))
  forward = first.outward(applied(own, (1.0, 0.0, 0.0)))
  left = first.outward(applied(own, (0.0, 1.0, 0.0)))
  speed = dot(first.velocity, forward)
  rim = drive.radius * dot(minus(second.spin(), first.spin()), left)
  ahead = 1.0 if torque * dot(axis, left) >= 0.0 else -1.0
  slip = ahead * (rim - speed) / max(abs(speed), 3.0)
  return max(0.0, min(1.0, 2.0 - slip / drive.slip))


def _servoTorque(drive: object, first: object, second: object,
                 own: Vector, axis: Vector) -> float:
  """Returns a servo's torque now ('Drive'): its torque, and the second
  body's turn on the first, taken from the drive's reference, about the
  motor's axis ('own' in the second's own frame, 'axis' in the
  world)."""
  firstTurn = (1.0, 0.0, 0.0, 0.0) if first is None else product(
    first.turn, conjugate(first.axes))
  secondTurn = product(second.turn, conjugate(second.axes))
  twist = product(product(conjugate(firstTurn), secondTurn),
                  conjugate(drive.reference))
  about = rotated(drive.reference, own)
  angle = 2.0 * math.atan2(dot(twist[1:], about), twist[0])
  spin = second.spin() if first is None else minus(second.spin(),
                                                   first.spin())
  torque = (drive.torque + drive.stiffness * (drive.target - angle)
            - drive.damping * dot(spin, axis))
  return max(-drive.most, min(drive.most, torque))


def _touchingOf(movers: list) -> set[tuple[int, int]]:
  """The '_touchingOf' function returns the pairs of bodies touching
  now (one holding a point to the other), least first."""
  pairs = set()
  for mine, mover in enumerate(movers):
    for _, other in mover.holds:
      pairs.add((min(mine, other), max(mine, other)))
  return pairs


def _woken(movers: list) -> None:
  """The '_woken' function wakes every body asleep touching one awake
  and moving, and every body asleep touching one so woken, at once."""
  asleep = [mover.asleep() for mover in movers]
  pairs = sorted(_touchingOf(movers))
  woken = set()
  for a, b in pairs:
    for sleeper, waker in ((a, b), (b, a)):
      if asleep[sleeper] and not asleep[waker] and (
          not movers[waker].still()):
        woken.add(sleeper)
  grown = bool(woken)
  while grown:
    grown = False
    for a, b in pairs:
      for sleeper, waker in ((a, b), (b, a)):
        if asleep[sleeper] and sleeper not in woken and waker in woken:
          woken.add(sleeper)
          grown = True
  for index in woken:
    movers[index].rest = 0.0


def _slept(movers: list, sleeping: Sleep, h: float) -> None:
  """The '_slept' function counts how long each body that may sleep
  has been still, and puts to sleep, stopped, those still long enough
  whose every touching body is asleep or still; one that may not yet
  waits half the settling again."""
  asleep = [mover.asleep() for mover in movers]
  still = [not asleep[index] and mover.still()
           for index, mover in enumerate(movers)]
  for index, mover in enumerate(movers):
    if mover.free and not asleep[index]:
      mover.rest = mover.rest + h if still[index] else 0.0
  partners: dict[int, list[int]] = {}
  for a, b in sorted(_touchingOf(movers)):
    partners.setdefault(a, []).append(b)
    partners.setdefault(b, []).append(a)
  for index, mover in enumerate(movers):
    if not mover.free or asleep[index] or mover.rest < sleeping.settle:
      continue
    if all(asleep[other] or still[other]
           for other in partners.get(index, [])):
      mover.velocity = (0.0, 0.0, 0.0)
      mover.momentum = (0.0, 0.0, 0.0)
    else:
      mover.rest = 0.5 * sleeping.settle


def _turnedMatrix(turning: Matrix, matrix: Matrix) -> Matrix:
  """The '_turnedMatrix' function returns 'matrix' turned by 'turning':
  R M R'."""
  return matrixProduct(matrixProduct(turning, matrix), transposed(turning))


@functools.lru_cache(maxsize=64)
def _armsOf(body: Body, axes: Quaternion,
            hull: bool) -> tuple[tuple, float]:
  """The '_armsOf' function returns where 'body' may touch the ground,
  each its index, its arm from the centre along the principal axes
  ('axes' the turn from them to the body's own) and its ring (nought
  for a corner of a shape, or a ball's lowest point; a turned solid's
  circles on its hull, each its middle's arm and its radius: it meets
  the ground at their lowest points, exactly, as it rolls), and the
  farthest it reaches: no point is lower than the centre less that.
  Remembered for the last 64 (they hang on the body alone: a ring's
  thousand corners were worked out every frame)."""
  if body.shape is None:
    return (), 0.0
  if isinstance(body.shape, Sphere):
    return ((0, (0.0, 0.0, -body.shape.radius), 0.0),), body.shape.radius
  back: Matrix = transposed(matrixOf(axes))
  if isinstance(body.shape, Turned):
    arms = tuple((index, applied(back, minus((0.0, 0.0, w),
                                             body.centre)), rho)
                 for index, (rho, w) in enumerate(_ringsOf(body.shape)))
  else:
    points = body.shape.points
    arms = tuple((index, applied(back, minus(points[index], body.centre)),
                  0.0) for index in _pointsMet(body.shape, hull))
  return arms, max(norm(arm) + ring for _, arm, ring in arms)


def _pointsMet(shape: object, hull: bool) -> tuple[int, ...] | range:
  """Returns which of 'shape''s points the ground meets: those on its
  hull ('_hullOf'), with 'hull' ('Fidelity.hull'), else all."""
  return _hullOf(shape) if hull else range(len(shape.points))


@functools.lru_cache(maxsize=64)
def _hullOf(shape: object) -> tuple[int, ...]:
  """Returns which of 'shape''s points lie on its convex hull (its
  corners and any on its faces), in order: only they can meet flat
  ground first (a point inside the hull is above some on it), so only
  they are met (a car's frame of 200 bars has 1700 corners, ~60 on its
  hull; met at all of them, its physics took 130 ms a frame). On a
  terrain a bump narrower than the hull's underside could reach a point
  inside it unmet. All of them, should the hull not be found (a flat
  shape)."""
  from scipy.spatial import ConvexHull, QhullError
  points = numpy.array(shape.points, numpy.float64)
  try:
    hull = ConvexHull(points)
  except QhullError:
    return tuple(range(len(points)))
  normals, offsets = hull.equations[:, :3], hull.equations[:, 3]
  size = max(1.0, float(numpy.abs(points).max()))
  out = (points @ normals.T + offsets).max(axis=1) > -1e-9 * size
  return tuple(numpy.flatnonzero(out).tolist())


@functools.lru_cache(maxsize=64)
def _ringsOf(shape: Turned) -> tuple[tuple[float, float], ...]:
  """Returns the circles of the turned solid 'shape' on its hull, each
  its radius and height along the axis (rho, w): the ends of its
  profile's pieces that lie on the hull of them and their mirror across
  the axis (the solid's own hull is that hull turned round, so only
  they can be its lowest point on flat ground)."""
  points = set()
  for piece in shape.profile:
    if piece[0] == 'line':
      points.update((piece[1], piece[2]))
    else:
      _, (rho, w), radius, start, end = piece
      for angle in (start, end):
        points.add((rho + radius * math.cos(angle),
                    w + radius * math.sin(angle)))
  mirrored = sorted(points | {(-rho, w) for rho, w in points})
  hull = _hullOf2(mirrored)
  return tuple(sorted({(rho, w) for rho, w in hull if rho > 0.0}))


def _hullOf2(points: list) -> list:
  """Returns the corners of the convex hull of 'points' (sorted), in the
  plane (Andrew's monotone chain), none on a straight edge's middle."""
  def turn(o: tuple, a: tuple, b: tuple) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

  lower, upper = [], []
  for point in points:
    while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= 0.0:
      lower.pop()
    lower.append(point)
  for point in reversed(points):
    while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= 0.0:
      upper.pop()
    upper.append(point)
  return lower[:-1] + upper[:-1]


def _lowestWay(axis: Vector) -> Vector:
  """Returns the way, in the world, from the middle of a circle about
  'axis' (a unit, in the world) to its lowest point: straight down,
  less its share along the axis; for a circle lying flat, any way
  along it (all its points are as low)."""
  way = (axis[0] * axis[2], axis[1] * axis[2], axis[2] * axis[2] - 1.0)
  size = norm(way)
  if size < 1e-12:
    return 1.0, 0.0, 0.0
  return scaled(way, 1.0 / size)


def _deepestWay(axis: Vector, normal: Vector) -> Vector:
  """Returns the way, in the world, from the middle of a circle about
  'axis' (a unit) to its point deepest along the ground's 'normal' (a
  unit): against the normal, less its share along the axis; for a
  circle lying flat on the ground, any way along it."""
  share = -dot(normal, axis)
  way = (-normal[0] - share * axis[0], -normal[1] - share * axis[1],
         -normal[2] - share * axis[2])
  size = norm(way)
  if size < 1e-12:
    return 1.0, 0.0, 0.0
  return scaled(way, 1.0 / size)


def _groundPlaces(body: Body, state: State, ground: Ground,
                  hull: bool) -> list[tuple[int, Vector]]:
  """Returns where the points of 'body' the 'ground' meets are in
  'state' (a shape's on its hull alone with 'hull'), each with its index
  as the bristles have it: a ball's lowest
  point, a turned solid's circles' lowest points (deepest along the
  ground's normal, on a terrain), else its shape's corners."""
  terrain = ground.terrain
  if isinstance(body.shape, Sphere):
    place, radius = state.place, body.shape.radius
    if terrain is None:
      return [(0, (place[0], place[1], place[2] - radius))]
    return [(0, plus(place, scaled(terrain.normalAt(place[0], place[1]),
                                   -radius)))]
  if isinstance(body.shape, Turned):
    axis = rotated(state.turn, (0.0, 0.0, 1.0))
    out = []
    for index, (rho, w) in enumerate(_ringsOf(body.shape)):
      middle = body.placeOf(state, (0.0, 0.0, w))
      way = (_lowestWay(axis) if terrain is None else
             _deepestWay(axis, terrain.normalAt(middle[0], middle[1])))
      out.append((index, plus(middle, scaled(way, rho))))
    return out
  points = body.shape.points
  return [(index, body.placeOf(state, points[index]))
          for index in _pointsMet(body.shape, hull)]


def _turnedFreely(turn: Quaternion, momentum: Vector, moments: Vector,
                  h: float) -> tuple[Quaternion, Vector]:
  """The '_turnedFreely' function returns a body turned freely for 'h'
  s: 'turn' its principal axes' turn, 'momentum' its angular momentum
  along them, 'moments' its principal moments. Each part of '_SPLIT'
  turns it about one principal axis as the momentum along that axis
  alone would, and turns the momentum back as much, so in the world it
  stays the same."""
  m = list(momentum)
  for axis, share in _SPLIT:
    angle = share * h * m[axis] / moments[axis]
    c, s = math.cos(angle), math.sin(angle)
    half = [0.0, 0.0, 0.0]
    half[axis] = math.sin(0.5 * angle)
    turn = product(turn, (math.cos(0.5 * angle), half[0], half[1],
                          half[2]))
    j, k = (axis + 1) % 3, (axis + 2) % 3
    m[j], m[k] = c * m[j] + s * m[k], c * m[k] - s * m[j]
  return normalised(turn), (m[0], m[1], m[2])
