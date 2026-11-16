"""
TestConic covers the paths round a puller (user, 2026-11-16: the "skrå
kast" "turns into something far more beautiful: an elliptic orbital
path"): a round orbit from its state, any ellipse's state and elements
taken back and forth, its apsides and the times to them, its time
carried on (the leap's fold), the hyperbola of a body leaving, the
points drawn along a path; a body falling straight has none.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._conic import TAU, Conic

from . import SpaceTest

MU = 3.986004418e14


class TestConic(SpaceTest):
  """Tests for 'Conic'."""

  def ellipse(self, ) -> Conic:
    """Returns a tilted, stretched ellipse round Terra."""
    return Conic(MU, 1.2e7, 0.3, 0.5, 1.0, 2.0, 0.7)

  def test_round(self) -> None:
    """A body at a round orbit's speed is on a circle: its a its
    distance, its e nought, its period 2 pi sqrt(r³/mu)."""
    r = 7.0e6
    conic = Conic.fromState(MU, (r, 0.0, 0.0), (0.0, math.sqrt(MU / r), 0.0))
    self.assertAlmostEqual(conic.a / r, 1.0, 12)
    self.assertLess(conic.e, 1e-12)
    self.assertAlmostEqual(conic.periapsis / r, 1.0, 12)
    self.assertAlmostEqual(conic.apoapsis / r, 1.0, 12)
    self.assertAlmostEqual(conic.period, TAU * math.sqrt(r ** 3 / MU), 6)

  def test_back_and_forth(self) -> None:
    """Any state on an ellipse gives the ellipse back: its elements, and
    the state again at time nought."""
    conic = self.ellipse()
    for t in (0.0, 1234.5, 7000.0, 20000.0):
      place, speed = conic.stateAt(t)
      again = Conic.fromState(MU, place, speed)
      for name in ('a', 'e', 'i', 'node', 'peri'):
        self.assertAlmostEqual(getattr(again, name), getattr(conic, name),
                               7, name)
      there, moving = again.stateAt(0.0)
      self.assertClose(there, place, 1e-6 * math.dist(place, (0, 0, 0)))
      self.assertClose(moving, speed, 1e-6 * math.dist(speed, (0, 0, 0)))

  def test_apsides(self) -> None:
    """An ellipse's nearest and furthest are a (1 -+ e); the body is
    there when it says it will be."""
    conic = self.ellipse()
    self.assertAlmostEqual(conic.periapsis, 1.2e7 * 0.7, 3)
    self.assertAlmostEqual(conic.apoapsis, 1.2e7 * 1.3, 3)
    for t in (0.0, 5000.0):
      far = t + conic.timeToApoapsis(t)
      near = t + conic.timeToPeriapsis(t)
      self.assertAlmostEqual(math.dist(conic.stateAt(far)[0], (0, 0, 0))
                             / conic.apoapsis, 1.0, 10)
      self.assertAlmostEqual(math.dist(conic.stateAt(near)[0], (0, 0, 0))
                             / conic.periapsis, 1.0, 10)
      self.assertLess(conic.timeToApoapsis(t), conic.period)

  def test_after(self) -> None:
    """Carried on 's', the path's time nought is the old time 's'; its
    anomaly within one turn."""
    conic = self.ellipse()
    for s in (100.0, 3.0 * conic.period + 17.0):
      later = conic.after(s)
      self.assertLess(later.anomaly, TAU)
      self.assertGreaterEqual(later.anomaly, 0.0)
      self.assertClose(later.stateAt(0.0)[0], conic.stateAt(s)[0], 1e-3)

  def test_hyperbola(self) -> None:
    """Past the escape speed a body leaves on a hyperbola: e over one,
    a under nought, no apoapsis; it is found again from its state."""
    r = 7.0e6
    speed = 1.2 * math.sqrt(2.0 * MU / r)
    conic = Conic.fromState(MU, (r, 0.0, 0.0), (0.0, speed, 0.0))
    self.assertGreater(conic.e, 1.0)
    self.assertLess(conic.a, 0.0)
    self.assertEqual(conic.apoapsis, math.inf)
    self.assertIsNone(conic.timeToApoapsis(0.0))
    self.assertAlmostEqual(conic.periapsis / r, 1.0, 10)
    place, moving = conic.stateAt(3600.0)
    again = Conic.fromState(MU, place, moving)
    self.assertAlmostEqual(again.e, conic.e, 9)
    self.assertClose(again.stateAt(0.0)[0], place, 1e-3)
    self.assertIsNone(again.timeToPeriapsis(0.0))

  def test_path(self) -> None:
    """The points drawn lie on the path: an ellipse's between its
    apsides, a hyperbola's out to the reach asked."""
    conic = self.ellipse()
    for point in conic.pathPoints(64, 0.0):
      r = math.dist(point, (0, 0, 0))
      self.assertGreaterEqual(r, conic.periapsis * (1.0 - 1e-12))
      self.assertLessEqual(r, conic.apoapsis * (1.0 + 1e-12))
    r = 7.0e6
    leaving = Conic.fromState(MU, (r, 0.0, 0.0),
                              (0.0, 1.2 * math.sqrt(2.0 * MU / r), 0.0))
    points = leaving.pathPoints(33, 1e8)
    self.assertAlmostEqual(math.dist(points[0], (0, 0, 0)) / 1e8, 1.0, 9)
    self.assertAlmostEqual(math.dist(points[16], (0, 0, 0)) / r, 1.0, 9)

  def test_straight(self) -> None:
    """A body still or moving straight at its puller has no conic: the
    vessel says None; one nearly so has a needle of an ellipse."""
    from worQt.gaming.space._vessel import Vessel
    with self.assertRaises(ValueError):
      Conic.fromState(MU, (7.0e6, 0.0, 0.0), (-100.0, 0.0, 0.0))
    system = self.systemOf()
    vessel = Vessel()
    vessel.placed(system.named('Luna'), (3.0e6, 0.0, 0.0), (0.0, 0.0, 0.0),
                  (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    self.assertIsNone(vessel.conicOf(system))
    needle = Conic.fromState(MU, (7.0e6, 0.0, 0.0), (-100.0, 1e-6, 0.0))
    self.assertTrue(needle.closed)
    self.assertLess(needle.periapsis, 1.0)
