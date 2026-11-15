"""
TestCompiled holds the compiled stepping ('World.compiled', Warp) to
the plain Python, the reference: on a body tumbling in the air, tossed
on the ground, two rods swinging on ties, a shaker's actuator, spring
and damper, a greased block, the hexapod's legs and a box landing on a
slab, the two agree to a hair, states, holds and books alike; on a
GPU, where there is one, as on the processor; a stroke the kernel does
not know runs in plain Python; ties holding nothing are refused
compiled too.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from worQt.phys import ORIGIN, UNTURNED, Actuator, Assembly, Body, Books
from worQt.phys import Contact, Damper, Grease, Ground, Hexapod
from worQt.phys import SineStroke, Spring, State, SwayingPose, Tie, World
from worQt.phys import boxShape, minus, normalised, rotated, turnAbout

from . import PhysTest

BOX = Body.of(boxShape(0.4, 0.3, 0.2), 1000.0)
BLOCK = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
ROD = Body.of(boxShape(1.0, 0.02, 0.02), 1000.0)
GRAVITY = (0.0, 0.0, -9.81)
TOP = (0.0, 0.0, 0.1)


class Ramp(NamedTuple):
  """Ramp is a stroke the kernel does not know: its length 'start' m,
  growing 'rate' m/s."""

  start: float
  rate: float

  def at(self, time: float) -> tuple[float, float, float]:
    """The 'at' method returns the length at 'time', its rate, and
    nought."""
    return self.start + self.rate * time, self.rate, 0.0


def hung(swing: float, hook: tuple) -> State:
  """The 'hung' function returns the rod hung by its end from 'hook',
  swung 'swing' from straight down."""
  turn = turnAbout((0.0, 1.0, 0.0), swing - 0.5 * math.pi)
  return State(minus(hook, rotated(turn, (0.5, 0.0, 0.0))), turn)


class TestCompiled(PhysTest):
  """Tests for the compiled stepping."""

  def agree(self, world: World, assembly: Assembly, states: tuple,
            seconds: float, start: float) -> None:
    """Asserts the compiled run of 'assembly' from 'states' agrees with
    the plain Python's: states (bristles and holds too) and books."""
    fast = World(world.gravity, world.step, world.ground, world.grease,
                 True)
    slow = World(world.gravity, world.step, world.ground, world.grease,
                 False)
    quick, quickBooks = fast.booked(assembly, states, seconds, start,
                                    Books())
    plain, plainBooks = slow.booked(assembly, states, seconds, start,
                                    Books())
    for one, other in zip(quick, plain):
      self.assertNear(one[:4], other[:4], 1e-12)
      self.assertEqual(len(one.bristles), len(other.bristles))
      self.assertEqual(len(one.holds), len(other.holds))
      self.assertNear(one.bristles, other.bristles, 1e-12)
      self.assertNear(one.holds, other.holds, 1e-12)
    self.assertNear(quickBooks, plainBooks, 1e-10)

  def test_free(self) -> None:
    """A box tumbling in the air."""
    toss = State((0.0, 0.0, 2.0), normalised((0.9, 0.2, -0.3, 0.4)),
                 (1.0, 0.0, 4.0), (3.0, -6.0, 2.0))
    self.agree(World(GRAVITY), Assembly((BOX,)), (toss,), 0.5, 0.0)

  def test_ground(self) -> None:
    """A box tossed on the ground, bristles holding."""
    toss = State((0.0, 0.0, 0.3), normalised((0.9, 0.2, -0.3, 0.4)),
                 (1.0, 0.5, 0.0), (3.0, -6.0, 2.0))
    self.agree(World(GRAVITY, 1e-3, Ground()), Assembly((BOX,)), (toss,),
               0.5, 0.0)

  def test_ties(self) -> None:
    """Two rods swinging end to end on ties."""
    upper = hung(math.radians(60.0), ORIGIN)
    joint = ROD.placeOf(upper, (-0.5, 0.0, 0.0))
    pair = Assembly((ROD, ROD), (Tie(0, (0.5, 0.0, 0.0), None, ORIGIN),
                                 Tie(1, (0.5, 0.0, 0.0), 0,
                                     (-0.5, 0.0, 0.0))))
    self.agree(World(), pair, (upper, hung(math.radians(-30.0), joint)),
               0.5, 0.0)

  def test_shaker(self) -> None:
    """A shaker's actuator under a block on a spring and a damper,
    begun at a later time."""
    base = Body.of(boxShape(0.1, 0.1, 0.1), 1000.0)
    shaker = Assembly((base, BLOCK), (
      Actuator(None, ORIGIN, 0, ORIGIN, SineStroke(0.5, 0.01, 1.6)),
      Spring(0, ORIGIN, 1, ORIGIN, 800.0, 0.5),
      Damper(0, ORIGIN, 1, ORIGIN, 16.0)))
    states = (State((0.0, 0.0, -0.5)), State((0.0, 0.0, -1.098)))
    self.agree(World(), shaker, states, 0.5, 0.3)

  def test_grease(self) -> None:
    """A greased block on a spring and a damper: the same draws."""
    hang = Assembly((BLOCK,), (Spring(None, ORIGIN, 0, TOP, 800.0, 1.0),
                               Damper(None, ORIGIN, 0, TOP, 16.0)))
    greased = World(GRAVITY, 1e-3, None, Grease(0.05, 0.05, 1))
    self.agree(greased, hang, (State((0.0, 0.0, -1.1)),), 0.5, 0.0)

  def test_hexapod(self) -> None:
    """The hexapod's legs rolling and surging the platform."""
    plate = Body.of(boxShape(1.4, 1.4, 0.05), 2700.0)
    rig = Hexapod(1.0, 0.6, 20.0, 20.0, 0.0, -0.025)
    motion = SwayingPose((0.0, 0.0, 1.0), UNTURNED, (0.03, 0.0, 0.0),
                         (math.radians(5.0), 0.0, 0.0), 0.7)
    self.agree(World(), Assembly((plate,), rig.legs(plate, 0, motion)),
               (motion.at(0.0).state(),), 0.3, 0.0)

  def test_contact(self) -> None:
    """A box landing tilted on a slab on the ground, holds and all."""
    slab = Body.of(boxShape(0.6, 0.6, 0.2), 1000.0)
    cube = Body.of(boxShape(0.3, 0.3, 0.2), 1000.0)
    stack = Assembly((slab, cube), (Contact(0, 1),))
    states = (State((0.0, 0.0, 0.0978)),
              State((0.02, 0.01, 0.2985), normalised((1.0, 0.01, 0.02,
                                                      0.0)),
                    (0.1, 0.0, -0.1)))
    ground = World(GRAVITY, 1e-3, Ground(), None, False)
    states = ground.advancedAll(stack, states, 0.05)
    self.agree(ground, stack, states, 0.05, 0.05)

  def test_gpu(self) -> None:
    """Where there is a GPU (CUDA), the compiled stepping runs on it as
    on the processor: a box landing tilted on a slab, holds and all."""
    import warp
    warp.init()
    if not warp.is_cuda_available():
      self.skipTest('no CUDA device here')
    slab = Body.of(boxShape(0.6, 0.6, 0.2), 1000.0)
    cube = Body.of(boxShape(0.3, 0.3, 0.2), 1000.0)
    stack = Assembly((slab, cube), (Contact(0, 1),))
    states = (State((0.0, 0.0, 0.0978)),
              State((0.02, 0.01, 0.2985), normalised((1.0, 0.01, 0.02,
                                                      0.0)),
                    (0.1, 0.0, -0.1)))
    processor = World(GRAVITY, 1e-3, Ground(), None, True, None, 'cpu')
    graphics = World(GRAVITY, 1e-3, Ground(), None, True, None, 'cuda')
    here = processor.advancedAll(stack, states, 0.1)
    there = graphics.advancedAll(stack, states, 0.1)
    self.assertNear(there, here, 1e-9)

  def test_unknown_stroke(self) -> None:
    """An actuator ramping, a stroke the kernel does not know, runs in
    plain Python, as it would uncompiled."""
    ramped = Assembly((BLOCK,), (Actuator(None, ORIGIN, 0, ORIGIN,
                                          Ramp(1.0, 0.1)),))
    states = (State((0.0, 0.0, -1.0)),)
    fast = World(GRAVITY, 1e-3, None, None, True)
    slow = World(GRAVITY, 1e-3, None, None, False)
    self.assertEqual(fast.advancedAll(ramped, states, 0.2),
                     slow.advancedAll(ramped, states, 0.2))

  def test_refused(self) -> None:
    """A tie holding nothing that moves is refused compiled too."""
    nothing = Assembly((ROD,), (Tie(None, ORIGIN, None, ORIGIN),))
    with self.assertRaises(ValueError):
      World().advancedAll(nothing, (hung(0.0, ORIGIN),), 0.01)
