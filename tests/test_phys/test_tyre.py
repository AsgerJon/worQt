"""
TestTyre covers the wheel's world: a spring of rubber ('Spring.damping')
dies away as by hand, its heat booked, the kernel agreeing; the springs'
step, as long as one spring's ever was, and for a tyre's many springs
far longer, yet short enough for the belt's quickest swing; the tyre
('TYRE', 'walkingWheel') carrying a quarter of a car on its stand,
settled and still, its belt held every way (no twisting screw left
free), and its skin ('TyreSkin') facing out and lying on the road in
the patch; a ball on the ground holds its energy where the books look.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, ROAD, TYRE, Actuator, Assembly, Body, Books
from worQt.phys import Ground, HeldStroke, Sphere, Spring, State, Tie
from worQt.phys import World, boxShape, conjugate, cross, dot, minus
from worQt.phys import norm, plus, rotated, scaled, walkingWheel
from worQt.phys import wheelSkin
from worQt.phys._scenes import RING_UPRIGHT, WHEEL_BODY, WHEEL_DROP
from worQt.phys._scenes import WHEEL_LIFT

from . import PhysTest

SHRUNK = 0.632 / 1.75
BLOCK = Body.of(boxShape(0.1, 0.1, 0.1), 1000.0)
#  A block of 1 kg on rubber: 20 rad/s, a tenth of critical.
RUBBER = Assembly((BLOCK,), (Spring(None, ORIGIN, 0, (0.0, 0.0, 0.05),
                                   400.0, 0.5, 4.0),))
HANG = 0.5 + 9.81 / 400.0
LET_GO = State((0.0, 0.0, -0.05 - HANG - 0.01))
ROADWORLD = World((0.0, 0.0, -9.81), 1e-3, ROAD)


def loadOf(states: tuple) -> float:
  """The 'loadOf' function returns how hard the road pushes the wheel's
  tyre up, N: each lump pressed in, its depth times the road's
  stiffness."""
  return sum(ROAD.stiffness * (TYRE.lump - state.place[2])
             for state in states[3:] if state.place[2] < TYRE.lump)


def ownOf(body: Body, state: State, point: tuple) -> tuple:
  """The 'ownOf' function returns the world's 'point' in the own frame
  of 'body' in 'state'."""
  return plus(rotated(conjugate(state.turn), minus(point, state.place)),
              body.centre)


def fastestOf(states: tuple) -> float:
  """The 'fastestOf' function returns the speed of the fastest body,
  m/s."""
  return max(norm(state.velocity) for state in states)


class TestTyre(PhysTest):
  """Tests for the tyre and the rubber it is made of."""

  def test_rubber_dies_away(self) -> None:
    """Let go a centimetre down, a block on rubber swings as by hand
    (to the first order the explicit damping is, 1e-4 m in a second),
    and what the spring and gravity held less is the heat booked (to
    the stepping's own wobble, a few uJ of 20 mJ)."""
    world = World((0.0, 0.0, -9.81), 1e-3, None, None, False)
    held = world.storedOf(RUBBER, (LET_GO,)).total()
    (state,), books = world.booked(RUBBER, (LET_GO,), 1.0, 0.0, Books())
    w, zeta = 20.0, 0.1
    turning = w * math.sqrt(1.0 - zeta * zeta)
    off = -0.01 * math.exp(-zeta * w) * (
      math.cos(turning) + zeta / math.sqrt(1.0 - zeta * zeta)
      * math.sin(turning))
    self.assertNear(state.place[2], -0.05 - HANG + off, 1e-4)
    self.assertGreater(books.dampers, 0.019)
    now = world.storedOf(RUBBER, (state,)).total()
    self.assertNear(held - now, books.dampers, 5e-6)

  def test_rubber_compiled(self) -> None:
    """The kernel steps rubber as the plain Python does."""
    plain = World((0.0, 0.0, -9.81), 1e-3, None, None, False)
    compiled = World((0.0, 0.0, -9.81), 1e-3, None, None, True)
    first = plain.advancedAll(RUBBER, (LET_GO,), 0.5)[0]
    second = compiled.advancedAll(RUBBER, (LET_GO,), 0.5)[0]
    self.assertNear((first.place, first.velocity),
                    (second.place, second.velocity), 1e-12)

  def test_one_spring_step(self) -> None:
    """One spring's step is what it always was: no swing past 0.05 rad,
    its stiffness over the mass and the arm's share of the least
    moment."""
    world = World((0.0, 0.0, -9.81), 1e-3)
    least = BLOCK.principal()[0][0]
    quickest = math.sqrt(400.0 * (1.0 / BLOCK.mass + 0.05 ** 2 / least))
    wanted = 1e-3 / math.ceil(1e-3 * quickest / 0.05)
    self.assertEqual(world.springStepFor(RUBBER), wanted)

  def test_many_springs_step(self) -> None:
    """A tyre's hundreds of springs, a few at each lump, are stepped
    three times longer than all of them summed (each times its two
    ends' give) would allow, yet no longer than keeps the belt's
    quickest swing (a lump between its neighbours and its sidewall
    springs, all pulling) within 0.05 rad a step."""
    assembly, _ = walkingWheel(SHRUNK, WHEEL_DROP)
    step = ROADWORLD.springStepFor(assembly)
    summed = 0.0
    for spring in assembly.springs:
      for index, point in ((spring.first, spring.firstPoint),
                           (spring.second, spring.secondPoint)):
        body = assembly.bodies[index]
        arm = norm(minus(point, body.centre))
        summed += spring.stiffness * (1.0 / body.mass + arm * arm
                                      / body.principal()[0][0])
    self.assertGreater(step, 3.0 * 0.05 / math.sqrt(summed))
    lump = TYRE.mass / TYRE.nodes
    belt = math.sqrt((4.0 * TYRE.belt + 4.0 * TYRE.sidewall) / lump)
    self.assertLessEqual(step * belt, 0.05)

  def test_carries_a_corner(self) -> None:
    """On its stand, the axle 18 mm low, the tyre carries a quarter of
    a 1400 kg car on three lumps, the wheel not turning, and stays
    still."""
    assembly, states = walkingWheel(SHRUNK, WHEEL_DROP)
    self.assertGreater(loadOf(states), 3200.0)
    self.assertLess(loadOf(states), 4000.0)
    down = [state for state in states[3:] if state.place[2] < TYRE.lump]
    self.assertGreaterEqual(len(down), 3)
    states = ROADWORLD.advancedAll(assembly, states, 0.25)
    self.assertLess(fastestOf(states), 2e-3)
    self.assertLess(norm(states[2].spin), 1e-3)

  def test_belt_held_every_way(self) -> None:
    """Off the road, its wheel on its bearing, a belt set screwing round
    and along the axle (the way two crossed sidewall springs left free)
    is held back: no lump goes a tenth of a millimetre on the wheel
    (which it turns, free on its bearing), where two crossed springs
    alone let it go 4."""
    turn = RING_UPRIGHT
    wheel = State(rotated(turn, WHEEL_BODY.centre), turn)
    bearing = (Tie(None, WHEEL_BODY.placeOf(wheel, ORIGIN), 0, ORIGIN),
               Actuator(None, plus(WHEEL_BODY.placeOf(
                 wheel, (0.0, 0.0, 0.05)), (0.05, 0.0, 0.0)), 0,
                 (0.0, 0.0, 0.05), HeldStroke(0.05)),
               Actuator(None, plus(WHEEL_BODY.placeOf(
                 wheel, (0.0, 0.0, 0.05)), (0.0, 0.0, 0.05)), 0,
                 (0.0, 0.0, 0.05), HeldStroke(0.05)))
    assembly = Assembly((WHEEL_BODY,) + (TYRE.node(),) * TYRE.nodes,
                        bearing + TYRE.springsOf(0, 1))
    axis = rotated(turn, (0.0, 0.0, 1.0))
    started = []
    for lump in TYRE.statesOn(WHEEL_BODY, wheel):
      along = cross(axis, lump.place)
      along = scaled(along, 1.0 / norm(along))
      screw = plus(scaled(along, 0.0465), scaled(axis, 0.018))
      started.append(State(lump.place, lump.turn, screw))
    space = World((0.0, 0.0, 0.0), 1e-3)
    states = space.advancedAll(assembly, (wheel,) + tuple(started), 0.5)
    for lump, start in zip(states[1:], started):
      now = ownOf(WHEEL_BODY, states[0], lump.place)
      then = ownOf(WHEEL_BODY, wheel, start.place)
      self.assertLess(norm(minus(now, then)), 1e-4)

  def test_skin(self) -> None:
    """The skin has a tread face and four sidewall faces between each
    two lumps, every face anticlockwise seen from outside (the tread's
    away from the axle, a sidewall's toward its side), and in the patch
    the tread lies on the road."""
    assembly, states = walkingWheel(SHRUNK, WHEEL_DROP)
    skin = wheelSkin()
    faces = skin.faces(states)
    self.assertEqual(len(faces), 5 * TYRE.nodes)
    wheel = states[2]
    middle = WHEEL_BODY.placeOf(wheel, ORIGIN)
    axis = minus(WHEEL_BODY.placeOf(wheel, (0.0, 0.0, 1.0)), middle)
    lowest = 1.0
    for part, corners, _ in faces:
      a, b, c = corners[0], corners[1], corners[2]
      facing = cross(minus(b, a), minus(c, a))
      centre = scaled(plus(plus(a, b), plus(c, corners[3])), 0.25)
      away = minus(centre, middle)
      if part == 'tread':
        out = minus(away, scaled(axis, dot(away, axis)))
        lowest = min(lowest, max(corner[2] for corner in corners))
      else:
        out = scaled(axis, dot(away, axis))
      self.assertGreater(dot(facing, out), 0.0)
    self.assertLess(abs(lowest), 2e-3)
    self.assertEqual(len(skin.outlines(states)), TYRE.nodes)

  def test_spun_by_its_tyre(self) -> None:
    """Lifted clear of the road, the wheel is spun by its tyre: a lump
    pushed along the tread drags the wheel round through the sidewalls,
    and a ray at the tread meets the skin at the lump under it."""
    assembly, states = walkingWheel(SHRUNK, WHEEL_LIFT)
    self.assertGreater(min(state.place[2] for state in states[3:]),
                       TYRE.lump + 0.02)
    wheel = states[2]
    middle = WHEEL_BODY.placeOf(wheel, ORIGIN)
    axis = minus(WHEEL_BODY.placeOf(wheel, (0.0, 0.0, 1.0)), middle)
    top = max(range(3, len(states)), key=lambda k: states[k].place[2])
    lump = states[top]
    along = cross(axis, minus(lump.place, middle))
    along = scaled(along, 1.0 / norm(along))
    pushed = list(states)
    pushed[top] = State(lump.place, lump.turn, scaled(along, 5.0))
    states = ROADWORLD.advancedAll(assembly, tuple(pushed), 0.2)
    self.assertGreater(abs(dot(states[2].spin, axis)), 0.2)
    states = walkingWheel(SHRUNK, WHEEL_LIFT)[1]
    out = minus(states[top].place, middle)
    eye = plus(states[top].place, scaled(out, 2.0 / norm(out)))
    hit = wheelSkin().hitOf(states, eye, minus(states[top].place, eye))
    self.assertIsNotNone(hit)
    self.assertEqual(hit[0], top)

  def test_ball_holds_on_the_ground(self) -> None:
    """A ball resting on the ground: the ground holds half its stiffness
    times how far it sinks, squared, where the books look."""
    ball = Body.of(Sphere(0.1), 1000.0)
    ground = Ground()
    world = World((0.0, 0.0, -9.81), 1e-3, ground)
    sunk = ball.mass * 9.81 / ground.stiffness
    resting = State((0.0, 0.0, 0.1 - sunk))
    stored = world.storedOf(Assembly((ball,), ()), (resting,))
    self.assertNear(stored.ground, 0.5 * ground.stiffness * sunk * sunk,
                    1e-12)
