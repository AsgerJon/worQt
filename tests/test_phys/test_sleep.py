"""
TestSleep covers 'Sleep', bodies at rest let sleep: a box dropped on
the ground, still long enough, falls asleep, stopped, and stays exactly
where it is; without sleeping it never does; a box dropped onto a
sleeping slab and box wakes them both; a block hung on a spring, on a
rule, never sleeps; a run with sleeping cut on its steps goes on as
whole; and the compiled stepping sleeps and wakes as the plain Python
does.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.phys import ORIGIN, Assembly, Body, Contact, Ground, Sleep
from worQt.phys import Spring, State, World, boxShape, norm

from . import PhysTest

SLEEPING = World((0.0, 0.0, -9.81), 1e-3, Ground(), None, True, Sleep())
AWAKE = World((0.0, 0.0, -9.81), 1e-3, Ground())
BOX = Body.of(boxShape(0.4, 0.3, 0.2), 1000.0)
SLAB = Body.of(boxShape(0.6, 0.6, 0.2), 1000.0)
CUBE = Body.of(boxShape(0.3, 0.3, 0.2), 1000.0)
STACK = Assembly((SLAB, CUBE), (Contact(0, 1),))


class TestSleep(PhysTest):
  """Tests for 'Sleep'."""

  def test_falls_asleep(self) -> None:
    """A box dropped on the ground comes to rest and, still long enough,
    falls asleep, stopped; asleep it stays exactly where it is."""
    alone = Assembly((BOX,))
    states = SLEEPING.advancedAll(alone, (State((0.0, 0.0, 0.3)),), 2.5)
    self.assertGreaterEqual(states[0].rest, Sleep().settle)
    self.assertEqual(states[0].velocity, ORIGIN)
    self.assertEqual(states[0].spin, ORIGIN)
    later = SLEEPING.advancedAll(alone, states, 1.0, 2.5)
    self.assertEqual(later[0].place, states[0].place)
    self.assertEqual(later[0].turn, states[0].turn)

  def test_off(self) -> None:
    """Without sleeping the box rests but never sleeps: its stillness
    is never counted."""
    states = AWAKE.advancedAll(Assembly((BOX,)), (State((0.0, 0.0, 0.3)),),
                               2.5)
    self.assertEqual(states[0].rest, 0.0)

  def test_wakes(self) -> None:
    """A slab and a box resting on it on the ground fall asleep; a box
    dropped onto them wakes them both, at once."""
    states = SLEEPING.advancedAll(STACK, (State((0.0, 0.0, 0.1)),
                                          State((0.05, 0.02, 0.35))), 3.0)
    for state in states:
      self.assertGreaterEqual(state.rest, Sleep().settle)
    small = Body.of(boxShape(0.2, 0.2, 0.1), 1000.0)
    three = Assembly((SLAB, CUBE, small), (Contact(0, 1), Contact(1, 2),
                                           Contact(0, 2)))
    dropped = states + (State((0.0, 0.0, 0.5)),)
    later = SLEEPING.advancedAll(three, dropped, 0.4, 3.0)
    for state in later:
      self.assertEqual(state.rest, 0.0)
    self.assertGreater(norm(later[1].velocity), 1e-3)

  def test_held(self) -> None:
    """A block hung still on a spring, on a rule, never sleeps."""
    block = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
    hung = Assembly((block,), (Spring(None, ORIGIN, 0, (0.0, 0.0, 0.1),
                                      800.0, 1.0),))
    sag = block.mass * 9.81 / 800.0
    world = World((0.0, 0.0, -9.81), 1e-3, None, None, True, Sleep())
    states = world.advancedAll(hung, (State((0.0, 0.0, -1.1 - sag)),), 1.0)
    self.assertEqual(states[0].rest, 0.0)

  def test_pieces(self) -> None:
    """With sleeping, a run cut on its steps goes on as whole, falling
    asleep at the same step."""
    start = (State((0.0, 0.0, 0.3)),)
    alone = Assembly((BOX,))
    whole = SLEEPING.advancedAll(alone, start, 2.5)
    pieces = SLEEPING.advancedAll(alone, SLEEPING.advancedAll(
      alone, start, 1.3), 1.2, 1.3)
    self.assertNear(pieces, whole, 1e-12)

  def test_compiled(self) -> None:
    """The compiled stepping sleeps as the plain Python does."""
    plain = World((0.0, 0.0, -9.81), 1e-3, Ground(), None, False, Sleep())
    start = (State((0.0, 0.0, 0.3)),)
    alone = Assembly((BOX,))
    quick = SLEEPING.advancedAll(alone, start, 2.5)
    slow = plain.advancedAll(alone, start, 2.5)
    self.assertNear(quick, slow, 1e-12)
