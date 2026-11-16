"""
TestCrankPin covers wheels of any size and the crank pin (user,
2026-11-16: a steam locomotive): a wheelset's profile shifts with its
radius; one of each size is one body, its radius known by it; a
locomotive's driving wheelset (2.086 m wheels) let go on a 3 degree
grade gains speed as rolling says (g sin a / (1 + k), its own k), in
plain Python and in the kernel alike; a rod hung on a crank pin of a
wheelset spun in its boxes on a frame held still has its eye follow the
pin round (within 5 mm), the wheel turning on, in plain Python and in
the kernel alike.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys import Assembly, Body, State
from worQt.phys._assembly import Fixed
from worQt.phys._shape import boxShape
from worQt.phys._small_steps import THREADS, SmallSteps, preloaded
from worQt.phys._vectors import rotated
from worQt.phys.rail import JOURNAL_AT, Axlebox, RailWorld, Ribbon
from worQt.phys.rail import profileAt, straight, wheelsetBody, wheelsetOn
from worQt.phys.rail._crankpin import CrankPin
from worQt.phys.rail._wheelset import RADIUS, radiusOf

from . import PhysTest

#  A frame, s; the driving wheels' radius, m; the grade, rad; the crank's
#  throw, m, and how far out along the axle its pin is, m; the boxes'
#  and the pin's stiffness, N/m, and damping, N s/m (the pin's light:
#  traded with the rod every 2 ms, explicitly, 2e4 on a rod swinging as
#  ~63 kg at its eye grew without bound; 1e3-5e3 hold it to 0.2 mm).
FRAME = 1.0 / 60.0
DRIVER = 1.043
GRADE = math.radians(3.0)
THROW, OUT = 0.33, 1.25
STIFF, DAMPED, PIN_DAMPED = 2e7, 2e4, 2e3
#  How far the spun wheelset is lifted off its rails, m (clear of them,
#  short of 'OFF_UP', where the rail world takes it as flown off).
LIFT = 0.2


class _Still:
  """A world that moves nothing (the inner world of a lone wheelset)."""

  def advancedAll(self, assembly: object, states: tuple, seconds: float,
                  start: float = 0.0) -> tuple:
    """Returns 'states' as they are."""
    return states


class TestCrankPin(PhysTest):
  """Tests for wheels of any size and the crank pin (a minute or so)."""

  __time_out__ = 240.0

  def test_sizes(self) -> None:
    """The profile shifts with the radius; each size one body, its radius
    known by it; any other body has none."""
    for e in (0.02, 0.0, -0.03, -0.05):
      with self.subTest(e=e):
        small, big = profileAt(e), profileAt(e, DRIVER)
        self.assertAlmostEqual(big[0] - small[0], DRIVER - RADIUS, 12)
        self.assertEqual(big[1], small[1])
    self.assertIs(wheelsetBody(), wheelsetBody(RADIUS))
    self.assertIs(wheelsetBody(DRIVER), wheelsetBody(DRIVER))
    self.assertEqual(radiusOf(wheelsetBody(DRIVER)), DRIVER)
    self.assertIsNone(radiusOf(Body.of(boxShape(1.0, 1.0, 1.0), 1.0)))
    self.assertGreater(wheelsetBody(DRIVER).mass,
                       2.0 * wheelsetBody().mass)

  def test_rolls_down(self) -> None:
    """A driving wheelset let go on a 3 degree grade gains in 2 s what
    rolling says (within 0.5 %), in plain Python and in the kernel."""
    pitched = numpy.array(((math.cos(GRADE), 0.0, math.sin(GRADE)),
                           (0.0, 1.0, 0.0),
                           (-math.sin(GRADE), 0.0, math.cos(GRADE))))
    track = Ribbon((straight(40.0),), (0.0, 0.0, 10.0), pitched)
    body = wheelsetBody(DRIVER)
    k = body.inertia[2][2] / (body.mass * DRIVER ** 2)
    wanted = 9.81 * math.sin(GRADE) / (1.0 + k) * 2.0
    preloaded('cpu')
    for device in (None, 'cpu'):
      with self.subTest(device=device):
        world = RailWorld(_Still(), track, (body,), 1e-4, 0.3, 2e-3,
                          device)
        states = (wheelsetOn(track, 5.0, 0.0, DRIVER),)
        for frame in range(round(2.0 / FRAME)):
          states = world.advancedAll(Assembly((body,), ()), states, FRAME,
                                     frame * FRAME)
        speed = math.sqrt(sum(v * v for v in states[0].velocity))
        self.assertAlmostEqual(speed, wanted, None, None, 0.005 * wanted)
        self.assertFalse(world.derailed)

  def test_follows_the_pin(self) -> None:
    """A rod hung by its eye on a crank pin of a driving wheelset spun
    at 3 rad/s in its boxes (lifted 'LIFT' off the rails, its frame held
    still)
    follows the pin round: after a second the eye within 5 mm of the
    pin, the wheel still turning; in plain Python and in the kernel."""
    track = Ribbon((straight(20.0),))
    wheels = wheelsetBody(DRIVER)
    lifted = wheelsetOn(track, 10.0, 0.0, DRIVER)
    lifted = State((lifted.place[0], lifted.place[1],
                    lifted.place[2] + LIFT), lifted.turn, (0.0, 0.0, 0.0),
                   (0.0, 3.0, 0.0))
    frame = Body.of(boxShape(3.0, 2.0, 0.3), 7850.0)
    held = State((10.0, 0.0, DRIVER + LIFT + 0.8))
    rod = Body.of(boxShape(0.2, 0.1, 1.2), 7850.0)
    pin = (THROW, 0.0, OUT)
    where = numpy.array(lifted.place) + numpy.array(rotated(lifted.turn,
                                                            pin))
    hung = State(tuple(where - numpy.array((0.0, 0.0, 0.6))))
    preloaded('cpu')
    for device in (None, 'cpu'):
      with self.subTest(device=device):
        boxes = tuple(Axlebox(1, side, 0, (0.0, side * JOURNAL_AT,
                                           -0.8), (STIFF,) * 3,
                              (DAMPED,) * 3)
                      for side in (1.0, -1.0))
        eye = CrankPin(1, pin, 2, (0.0, 0.0, 0.6), (STIFF,) * 3,
                       (PIN_DAMPED,) * 3)
        inner = SmallSteps((0.0, 0.0, -9.81), None, 2.5e-4, 1, 0.0, 'cpu',
                           THREADS, False)
        world = RailWorld(inner, track, (wheels,), 1e-4, 0.3, 2e-3,
                          device)
        assembly = Assembly((frame, wheels, rod),
                            (Fixed(0),) + boxes + (eye,))
        states = (held, lifted, hung)
        for k in range(round(1.0 / FRAME)):
          states = world.advancedAll(assembly, states, FRAME, k * FRAME)
        pinned = numpy.array(states[1].place) + numpy.array(rotated(
          states[1].turn, pin))
        eyed = numpy.array(rod.placeOf(states[2], (0.0, 0.0, 0.6)))
        self.assertLess(float(numpy.linalg.norm(pinned - eyed)), 5e-3)
        self.assertGreater(abs(states[1].spin[1]), 1.0)
