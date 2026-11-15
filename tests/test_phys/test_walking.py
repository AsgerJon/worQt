"""
TestWalking covers the 'Walker' (a person as the world meets them, a
ball where their feet are, rolled by their legs) and the 'Grabber' (a
tool in their hands that pulls, holds and punts bodies). Asked to walk,
the walker rolls at the speed asked, without slipping; asked to stop,
it stops no quicker than the ground grips; on ice it goes nowhere. It
knows what it stands on and jumps as high as it should. Striding (a
game's player: 'strode') it is at the speed asked in the time its
thrust takes, its ball rolling with it, up and down left alone. Flying, it
hangs where it stops and climbs as fast as asked. Shrunk ('scaled', as a
world of its size must be to move alike), it jumps as high times the
scale, peaking as late times its root, and walks as fast times its root.
Held, a box
floats at the hold, the grabber carrying its weight; the steel block
is too heavy to lift. Pulled from afar, a giant steel ball of the
outer ring's is lifted before it is moved (the weight is carried
first) and is caught at the hold. A punt gives the punted body the
impulse and the walker the same back. A body asleep out of reach does
not shorten the world's steps; compiled (Warp) a walk into a box runs
as in plain Python; the yard and the ring stand still left alone; a
ball given is added last, touching every body.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Contact, Grabber, Ground, Sleep
from worQt.phys import Sphere, State, Walker, World, boxShape, wantedOf
from worQt.phys import flyingOf, giantBallGiven, groundAt, walkingRing
from worQt.phys import walkingYard
from worQt.phys._scenes import APRON, RING_GRABBER

from . import PhysTest

G = 9.81
FRAME = 1.0 / 60.0
GROUND = Ground(2e5, 2.0, 0.6, 2e5, 200.0)
ICE = Ground(2e5, 2.0, 0.0, 2e5, 200.0)
WALKER = Walker()
BALL = WALKER.body()
GRABBER = Grabber()
BOX = Body.of(boxShape(0.3, 0.3, 0.3), 185.0)
STEEL = Body.of(boxShape(0.35, 0.35, 0.35), 7850.0)
PLANK = Body.of(boxShape(2.4, 0.25, 0.05), 700.0)
GIANT = Body.of(Sphere(0.2), 7850.0)
#  Wood on wood, edges every 5 cm; and the walker's ball on wood.
ON_WOOD = (2e5, 2.0, 0.5, 2e5, 200.0, 0.05)
ROUND = (2e5, 2.0, 0.5, 2e5, 400.0)
GRAVITY = (0.0, 0.0, -G)


def standing(x: float, y: float) -> State:
  """The 'standing' function returns the walker standing still at 'x',
  'y', its ball sunk as its weight on the ground says."""
  return State((x, y, WALKER.radius - BALL.mass * G / GROUND.stiffness))


def walked(world: World, assembly: Assembly, states: tuple, seconds: float,
           wanted: tuple) -> list[tuple]:
  """The 'walked' function returns the states of 'assembly' (the walker
  first) frame by frame for 'seconds' from 'states', the walker asking
  its legs for 'wanted' each frame while it stands."""
  out, time = [], 0.0
  for _ in range(round(seconds / FRAME)):
    states = list(states)
    if WALKER.standingOn(assembly, tuple(states), 0) is not None:
      states[0] = WALKER.walked(BALL, states[0], wanted, FRAME)
    states = world.advancedAll(assembly, tuple(states), FRAME, time)
    time += FRAME
    out.append(states)
  return out


class TestWalking(PhysTest):
  """Tests for 'Walker' and 'Grabber'."""

  def test_wanted(self) -> None:
    """Looking along x (yaw pi), ahead is along x and right along -y,
    walking or running; ahead and aside at once goes no faster."""
    self.assertNear(wantedOf(WALKER, math.pi, 1.0, 0.0, False),
                    (WALKER.walk, 0.0, 0.0), 1e-12)
    self.assertNear(wantedOf(WALKER, math.pi, 0.0, 1.0, True),
                    (0.0, -WALKER.run, 0.0), 1e-12)
    x, y, _ = wantedOf(WALKER, math.pi, 1.0, 1.0, False)
    self.assertAlmostEqual(math.hypot(x, y), WALKER.walk, 12)
    self.assertNear(wantedOf(WALKER, 0.3, 0.0, 0.0, True),
                    (0.0, 0.0, 0.0), 0.0)

  def test_stands(self) -> None:
    """Asked for nothing it stands where it is."""
    world = World(GRAVITY, 1e-3, GROUND, None, True)
    states = walked(world, Assembly((BALL,)), (standing(0.0, 0.0),), 1.0,
                    (0.0, 0.0, 0.0))
    self.assertNear(states[-1][0].place[:2], (0.0, 0.0), 1e-6)
    self.assertNear(states[-1][0].velocity, (0.0, 0.0, 0.0), 1e-4)

  def test_walks(self) -> None:
    """Asked to walk along x it rolls at the speed asked within two
    seconds, spinning as a ball rolling without slipping."""
    world = World(GRAVITY, 1e-3, GROUND, None, True)
    states = walked(world, Assembly((BALL,)), (standing(0.0, 0.0),), 2.0,
                    (WALKER.walk, 0.0, 0.0))
    ball = states[-1][0]
    self.assertNear(ball.velocity, (WALKER.walk, 0.0, 0.0), 1e-3)
    self.assertNear(ball.spin, (0.0, WALKER.walk / WALKER.radius, 0.0),
                    1e-2)

  def test_stops_within_grip(self) -> None:
    """Running, then asked to stop, it stops within a second and a
    half, never slowing faster than the ground grips (its push bobbing
    a little over its weight)."""
    world = World(GRAVITY, 1e-3, GROUND, None, True)
    run = (WALKER.run, 0.0, 0.0)
    states = walked(world, Assembly((BALL,)), (standing(0.0, 0.0),), 2.0,
                    run)
    stopping = walked(world, Assembly((BALL,)), states[-1], 1.5,
                      (0.0, 0.0, 0.0))
    before = states[-1][0].velocity[0]
    for frame in stopping:
      now = frame[0].velocity[0]
      self.assertLessEqual(before - now, 1.05 * GROUND.grip * G * FRAME)
      before = now
    self.assertLess(abs(stopping[-1][0].velocity[0]), 0.01)

  def test_ice(self) -> None:
    """On ice its legs only spin the ball: it goes nowhere."""
    world = World(GRAVITY, 1e-3, ICE, None, True)
    states = walked(world, Assembly((BALL,)), (standing(0.0, 0.0),), 1.0,
                    (WALKER.walk, 0.0, 0.0))
    self.assertNear(states[-1][0].velocity[:2], (0.0, 0.0), 1e-9)
    self.assertGreater(states[-1][0].spin[1], 1.0)

  def test_standing_on(self) -> None:
    """On the ground it stands on the ground, on a box on the box, and
    half a metre up on nothing."""
    assembly = Assembly((BALL, BOX), (Contact(0, 1, *ROUND),))
    box = State((3.0, 0.0, 0.15))
    on = WALKER.standingOn(assembly, (standing(0.0, 0.0), box), 0)
    self.assertIsNone(on[0])
    up = State((3.0, 0.0, 0.3 + WALKER.radius + 0.01))
    on = WALKER.standingOn(assembly, (up, box), 0)
    self.assertEqual(on[0], 1)
    self.assertNear(on[1], (3.0, 0.0, 0.3), 1e-9)
    high = State((0.0, 0.0, WALKER.radius + 0.5))
    self.assertIsNone(WALKER.standingOn(assembly, (high, box), 0))

  def test_jumps(self) -> None:
    """Jumping from standing it rises 'jump' over where it stood, within
    a centimetre (the ground's give besides)."""
    world = World(GRAVITY, 1e-3, GROUND, None, True)
    start = standing(0.0, 0.0)
    state, impulse = WALKER.jumped(BALL, start)
    self.assertAlmostEqual(impulse[2] / BALL.mass,
                           math.sqrt(2.0 * G * WALKER.jump), 12)
    highest = start.place[2]
    for _ in range(60):
      state = world.advanced(BALL, state, FRAME)
      highest = max(highest, state.place[2])
    self.assertAlmostEqual(highest - start.place[2], WALKER.jump, 2)

  def test_holds(self) -> None:
    """A box held 1.2 m up floats there within a centimetre after a
    second (a little over it: it falls between frames), the grabber
    carrying its weight."""
    world = World(GRAVITY, 1e-3, GROUND, None, True)
    state, target = State((0.0, 0.0, 0.15)), (0.0, 0.0, 1.2)
    lifts = []
    for _ in range(90):
      state, impulse = GRABBER.held(BOX, state, target, (0.0, 0.0, 0.0),
                                    (0.0, 0.0, 0.0), GRAVITY, FRAME)
      state = world.advanced(BOX, state, FRAME)
      lifts.append(impulse[2])
    self.assertNear(state.place, target, 0.01)
    carried = sum(lifts[-30:]) / (30 * FRAME)
    self.assertAlmostEqual(carried / (BOX.mass * G), 1.0, 2)

  def test_too_heavy(self) -> None:
    """The steel block weighs more than the grabber lifts: held, it
    stays on the ground."""
    world = World(GRAVITY, 1e-3, GROUND, None, True)
    self.assertGreater(STEEL.mass * G, GRABBER.force)
    state = State((0.0, 0.0, 0.175))
    for _ in range(60):
      state, _ = GRABBER.held(STEEL, state, (0.0, 0.0, 1.2),
                              (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), GRAVITY,
                              FRAME)
      state = world.advanced(STEEL, state, FRAME)
    self.assertLess(state.place[2], 0.18)

  def test_punt(self) -> None:
    """A punt gives the box the impulse along its way, and the walker
    as much back: their momentum together stays nought."""
    box = State((1.0, 0.0, 1.0))
    punted, impulse = GRABBER.punted(BOX, box, box.place, (2.0, 0.0, 1.0),
                                     150.0)
    self.assertAlmostEqual(math.hypot(impulse[0], impulse[2]), 150.0, 12)
    walker = WALKER.body()
    back = State((0.0, 0.0, 0.3), (1.0, 0.0, 0.0, 0.0),
                 tuple(-x / walker.mass for x in impulse))
    total = tuple(BOX.mass * a + walker.mass * b
                  for a, b in zip(punted.velocity, back.velocity))
    self.assertNear(total, (0.0, 0.0, 0.0), 1e-12)
    self.assertNear(punted.spin, (0.0, 0.0, 0.0), 1e-12)

  def test_asleep_out_of_reach(self) -> None:
    """A plank asleep 8 m off needs far shorter steps than the walker,
    lying on the ground, but nothing can reach it in a frame to wake it:
    the walker walks exactly alike with it there or not."""
    world = World(GRAVITY, 1e-3, GROUND, None, True, Sleep())
    self.assertLess(world.stepFor(PLANK), 0.1 * world.stepFor(BALL))
    alone = walked(world, Assembly((BALL,)), (standing(0.0, 0.0),), 0.5,
                   (WALKER.walk, 0.0, 0.0))
    plank = State((8.0, 0.0, 0.025), (1.0, 0.0, 0.0, 0.0),
                  (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (), (), 1.0)
    both = walked(world, Assembly((BALL, PLANK)),
                  (standing(0.0, 0.0), plank), 0.5,
                  (WALKER.walk, 0.0, 0.0))
    self.assertEqual(both[-1][0].place, alone[-1][0].place)
    self.assertEqual(both[-1][1].place, plank.place)

  def test_compiled(self) -> None:
    """Walking into a box a metre ahead and shoving it: compiled as in
    plain Python."""
    assembly = Assembly((BALL, BOX), (Contact(0, 1, *ROUND),))
    states = (standing(0.0, 0.0), State((1.0, 0.0, 0.15)))
    wanted = (WALKER.walk, 0.0, 0.0)
    plain = walked(World(GRAVITY, 1e-3, GROUND, None, False), assembly,
                   states, 1.2, wanted)
    compiled = walked(World(GRAVITY, 1e-3, GROUND, None, True), assembly,
                      states, 1.2, wanted)
    self.assertGreater(plain[-1][1].place[0], 1.2)
    for one, other in zip(plain[-1], compiled[-1]):
      self.assertNear(other.place, one.place, 1e-9)
      self.assertNear(other.velocity, one.velocity, 1e-7)

  def test_yard(self) -> None:
    """The yard: the walker first, standing on the ground, every two
    bodies touching; left alone, nothing in it moves a centimetre in
    half a second."""
    assembly, states = walkingYard()
    count = len(assembly.bodies)
    self.assertEqual(len(assembly.contacts), count * (count - 1) // 2)
    self.assertIsNone(WALKER.standingOn(assembly, states, 0)[0])
    world = World(GRAVITY, 1e-3, GROUND, None, True, Sleep())
    later = world.advancedAll(assembly, states, 0.5)
    for before, after in zip(states, later):
      self.assertNear(after.place, before.place, 0.01)

  def test_pulls_up_first(self) -> None:
    """A giant ball (263 kg) on the apron, pulled toward a hold 4 m off
    and 1 m up: the ring's grabber carries its weight first, so it is
    off the apron within half a second, and caught within two."""
    world = World(GRAVITY, 1e-3, APRON, None, True)
    sunk = GIANT.mass * G / APRON.stiffness
    state, target = State((0.0, 0.0, 0.2 - sunk)), (0.0, -4.0, 1.2)
    caught = None
    for frame in range(120):
      state, _ = RING_GRABBER.pulled(GIANT, state, target,
                                     (0.0, 0.0, 0.0), GRAVITY, FRAME)
      state = world.advanced(GIANT, state, FRAME)
      if frame == 30:
        self.assertGreater(state.place[2], 0.25)
      if RING_GRABBER.catches(GIANT, state, target):
        caught = frame
        break
    self.assertIsNotNone(caught)

  def test_holds_a_giant_ball(self) -> None:
    """Caught, the giant ball is held at the hold within a centimetre,
    the ring's grabber carrying its 2580 N."""
    world = World(GRAVITY, 1e-3, APRON, None, True)
    state, target = State((0.0, -4.0, 1.0)), (0.0, -4.0, 1.2)
    lifts = []
    for _ in range(90):
      state, impulse = RING_GRABBER.held(GIANT, state, target,
                                         (0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                                         GRAVITY, FRAME)
      state = world.advanced(GIANT, state, FRAME)
      lifts.append(impulse[2])
    self.assertNear(state.place, target, 0.01)
    carried = sum(lifts[-30:]) / (30 * FRAME)
    self.assertAlmostEqual(carried / (GIANT.mass * G), 1.0, 2)

  def test_ring(self) -> None:
    """The ring: the walker first, standing on the apron, the ring
    second, held by six legs, giant balls in its groove and on the
    apron; left alone, nothing in it moves a centimetre in half a
    second."""
    assembly, states = walkingRing(3, 1)
    self.assertEqual(len(assembly.bodies), 2 + 3 + 1)
    self.assertEqual({leg.second for leg in assembly.actuators}, {1})
    self.assertEqual(len(assembly.actuators), 6)
    self.assertIsNone(WALKER.standingOn(assembly, states, 0)[0])
    world = World(GRAVITY, 1e-3, APRON, None, True, Sleep())
    later = world.advancedAll(assembly, states, 0.5)
    for before, after in zip(states, later):
      self.assertNear(after.place, before.place, 0.01)

  def test_flies(self) -> None:
    """Flying 3 m up, asked for nothing, it hangs there (its fall made
    up each frame) within a millimetre for a second; asked up, it climbs
    at 'rise' m/s once sped up; flying fast along, it goes twice
    'fly'."""
    world = World(GRAVITY, 1e-3, GROUND, None, True)
    state = State((0.0, 0.0, 3.0))
    for _ in range(60):
      state = WALKER.flown(state, (0.0, 0.0, 0.0), GRAVITY, FRAME)
      state = world.advanced(BALL, state, FRAME)
    self.assertNear(state.place, (0.0, 0.0, 3.0), 1e-3)
    up = flyingOf(WALKER, math.pi, 0.0, 0.0, 1.0, False)
    self.assertNear(up, (0.0, 0.0, WALKER.rise), 1e-12)
    heights = []
    for _ in range(60):
      state = WALKER.flown(state, up, GRAVITY, FRAME)
      state = world.advanced(BALL, state, FRAME)
      heights.append(state.place[2])
    self.assertAlmostEqual((heights[-1] - heights[-31]) / (30 * FRAME),
                           WALKER.rise, 6)
    self.assertNear(flyingOf(WALKER, math.pi, 1.0, 0.0, 0.0, True),
                    (2.0 * WALKER.fly, 0.0, 0.0), 1e-12)

  def test_ball_given(self) -> None:
    """A giant ball given in the ring is added last, in the state given,
    touching every body: the walker and the ring and the other balls."""
    assembly, states = walkingRing(3, 1)
    given = State((0.0, -4.0, 1.2))
    more, after = giantBallGiven(assembly, states, given)
    count = len(assembly.bodies)
    self.assertEqual(len(more.bodies), count + 1)
    self.assertEqual(after[-1], given)
    self.assertEqual(after[:-1], states)
    touching = {contact.first for contact in more.contacts
                if contact.second == count}
    self.assertEqual(touching, set(range(count)))
    self.assertEqual(len(more.actuators), len(assembly.actuators))

  def test_shrunk(self) -> None:
    """Shrunk to 1/78 on the apron shrunk alike ('groundAt'), it jumps
    the full-size jump times the scale, peaking at the full-size time
    (0.404 s) times its root, within a percent; it walks at the walk
    times the root; it flies and rises at the full-size speeds times
    the scale itself (as fast as they seem at the size it seems)."""
    self.assertAlmostEqual(WALKER.scaled(0.064 / 5.0).fly,
                           WALKER.fly * 0.064 / 5.0, 12)
    self.assertAlmostEqual(WALKER.scaled(0.064 / 5.0).rise,
                           WALKER.rise * 0.064 / 5.0, 12)
    scale = 0.064 / 5.0
    walker = WALKER.scaled(scale)
    body, ground = walker.body(), groundAt(scale)
    world = World(GRAVITY, 1e-3, ground, None, True)
    start = State((0.0, 0.0, walker.radius
                   - body.mass * G / ground.stiffness))
    state, _ = walker.jumped(body, start)
    highest, peak, time = start.place[2], 0.0, 0.0
    for _ in range(700):
      state = world.advanced(body, state, 1e-4)
      time += 1e-4
      if state.place[2] > highest:
        highest, peak = state.place[2], time
    rise = highest - start.place[2]
    self.assertAlmostEqual(rise / (WALKER.jump * scale), 1.0, 2)
    full = math.sqrt(2.0 * WALKER.jump / G)
    self.assertAlmostEqual(peak / (full * math.sqrt(scale)), 1.0, 2)
    state = start
    for _ in range(200):
      state = walker.walked(body, state, (walker.walk, 0.0, 0.0), 0.002)
      state = world.advanced(body, state, 0.002)
    self.assertAlmostEqual(state.velocity[0] / (WALKER.walk
                                                * math.sqrt(scale)), 1.0, 3)

  def test_strode(self) -> None:
    """Striding from a stand toward 6 m/s along x, falling at 1 m/s, the
    walker gains its thrust's worth of speed a frame (60 m/s², a tenth
    of a metre a second a sixtieth) till it is at 6 m/s, after a tenth of
    a second, never past it; its ball rolls with it (spin about y its
    speed over its radius), still falling at 1 m/s; asked to stop it
    stops as fast."""
    walker = Walker(0.3, 80.0, 1.65, 6.0, 12.0, 600.0, 0.8, 20.0, 10.0,
                    60.0)
    state = State((0.0, 0.0, 0.3), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    for k in range(1, 7):
      state = walker.strode(state, (6.0, 0.0, 0.0), 1.0 / 60.0)
      self.assertNear(state.velocity, (k * 1.0, 0.0, -1.0), 1e-12)
      self.assertNear(state.spin, (0.0, k * 1.0 / 0.3, 0.0), 1e-12)
    state = walker.strode(state, (6.0, 0.0, 0.0), 1.0 / 60.0)
    self.assertNear(state.velocity, (6.0, 0.0, -1.0), 1e-12)
    for _ in range(6):
      state = walker.strode(state, (0.0, 0.0, 0.0), 1.0 / 60.0)
    self.assertNear(state.velocity, (0.0, 0.0, -1.0), 1e-12)
