"""
TestSolarSystem covers the solar system (user, 2026-11-16: "just put in
the 9 planets around Terra, and yes, Pluto *is* a fucking planet!"):
its twelve bodies in their tree; every planet where JPL Horizons has
the real one on the day, Luna where the Moon is; places summed along
the tree; a vessel pulled by every body, its anchor's fall taken off;
the body a vessel is kept from; a leap folded into every body.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from . import SpaceTest

#  JPL Horizons, 2026-11-16 00:00 TDB, from the Sun's middle (the
#  Moon's from the Earth's), the ecliptic and equinox of J2000, km:
#  Terra the Earth and Moon's barycentre.
HORIZONS = {
  'Mercury': (-1.798890048075963E+07, 4.362066402307509E+07,
              5.214738317880146E+06),
  'Venus': (4.214016170904104E+07, 9.931713449066229E+07,
            -1.066585231760122E+06),
  'Terra': (8.850296188869809E+07, 1.185769791363914E+08,
            -7.875907861508429E+03),
  'Mars': (-7.239193920830978E+07, 2.295918065982436E+08,
           6.586441840638548E+06),
  'Jupiter': (-5.607957687224520E+08, 5.649675335840060E+08,
              1.020019355214059E+07),
  'Saturn': (1.375309524117914E+09, 3.018038005623050E+08,
             -6.000188038044496E+07),
  'Uranus': (1.311682269815298E+09, 2.594381194129184E+09,
             -7.372069564179659E+06),
  'Neptune': (4.462406511455085E+09, 2.281541684642297E+08,
              -1.075336346880741E+08),
  'Pluto': (3.005026297027666E+09, -4.386365507978231E+09,
            -3.997544828025942E+08),
  'Luna': (2.412956457567245E+05, -3.222653654968354E+05,
           -1.092296410081841E+04),
}
NAMES = ('Sol', 'Mercury', 'Venus', 'Terra', 'Mars', 'Jupiter', 'Saturn',
         'Uranus', 'Neptune', 'Pluto', 'Luna', 'Mani')


def _angle(one: tuple, two: tuple) -> float:
  """Returns the angle between 'one' and 'two', deg."""
  dot = sum(a * b for a, b in zip(one, two))
  size = math.dist(one, (0, 0, 0)) * math.dist(two, (0, 0, 0))
  return math.degrees(math.acos(max(-1.0, min(1.0, dot / size))))


class TestSolarSystem(SpaceTest):
  """Tests for 'SolarSystem' and the day's planets."""

  def test_bodies(self) -> None:
    """Sol, nine planets round it (Pluto among them), two moons round
    Terra."""
    system = self.systemOf()
    self.assertEqual(tuple(b.name for b in system.bodies), NAMES)
    terra = system.named('Terra')
    for name in NAMES[1:10]:
      self.assertEqual(system.parents[system.named(name)], 0, name)
    self.assertEqual(system.children(terra), (system.named('Luna'),
                                              system.named('Mani')))

  def test_today(self) -> None:
    """Every planet is within a tenth of a degree of the real one and
    its distance within a thousandth; Luna within two degrees (its mean
    path) and a hundredth."""
    system = self.systemOf()
    terra = system.named('Terra')
    for name, real in HORIZONS.items():
      to = terra if name == 'Luna' else 0
      place = system.relative(system.named(name), to, 0.0)[0]
      place = tuple(x / 1e3 for x in place)
      most, share = (2.0, 1e-2) if name == 'Luna' else (0.1, 1e-3)
      self.assertLess(_angle(place, real), most, name)
      self.assertAlmostEqual(math.dist(place, (0, 0, 0)) / math.dist(
        real, (0, 0, 0)), 1.0, delta=share, msg=name)

  def test_relative(self) -> None:
    """A body's place from another is the same summed along the tree as
    taken through Sol, and the reverse its opposite."""
    system = self.systemOf()
    luna, mars = system.named('Luna'), system.named('Mars')
    t = 5e4
    direct = system.relative(luna, mars, t)
    through = (system.relative(luna, 0, t), system.relative(mars, 0, t))
    for k in range(2):
      self.assertClose(direct[k], tuple(a - b for a, b in zip(
        through[0][k], through[1][k])), 1e-3)
    back = system.relative(mars, luna, t)
    self.assertClose(back[0], tuple(-x for x in direct[0]), 1e-3)

  def test_pull(self) -> None:
    """On Terra's ground the pull is 9.82 m/s² down, the rest (the
    tides: Luna's and Sol's pull there less theirs on Terra) a few
    millionths; the pull seen from Terra and Terra's own fall (every
    other body's pull on it) add up to every body's pull."""
    system = self.systemOf()
    terra = system.named('Terra')
    body = system.bodies[terra]
    place = (body.radius, 0.0, 0.0)
    pull = system.pullOn(terra, place, 0.0)
    self.assertClose(pull, (-9.82025, 0.0, 0.0), 1e-4)
    luna = system.relative(system.named('Luna'), terra, 0.0)[0]
    toward = tuple(1e8 * x / math.dist(luna, (0, 0, 0)) for x in luna)
    fall, every = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    for k, other in enumerate(system.bodies):
      there = system.relative(k, terra, 0.0)[0]
      d = tuple(a - b for a, b in zip(there, toward))
      r = math.dist(d, (0, 0, 0))
      for j in range(3):
        every[j] += other.mu * d[j] / r ** 3
      if k != terra:
        r = math.dist(there, (0, 0, 0))
        for j in range(3):
          fall[j] += other.mu * there[j] / r ** 3
    seen = system.pullOn(terra, toward, 0.0)
    self.assertClose(tuple(a + b for a, b in zip(seen, fall)), every, 1e-12)

  def test_anchor(self) -> None:
    """Within Luna's reach a vessel is kept from Luna; outside it, from
    Terra; past Terra's, from Sol; out of Luna's a little past its reach
    only."""
    system = self.systemOf()
    terra, luna = system.named('Terra'), system.named('Luna')
    there = system.relative(luna, terra, 0.0)[0]
    out = tuple(x / math.dist(there, (0, 0, 0)) for x in there)
    reach = system.bodies[luna].reach
    near = tuple(a - 0.9 * reach * b for a, b in zip(there, out))
    far = tuple(a - 1.1 * reach * b for a, b in zip(there, out))
    self.assertEqual(system.anchorFor(terra, near, 0.0), luna)
    self.assertEqual(system.anchorFor(terra, far, 0.0), terra)
    self.assertEqual(system.anchorFor(luna, (1.01 * reach, 0.0, 0.0), 0.0),
                     luna)
    self.assertEqual(system.anchorFor(luna, (1.05 * reach, 0.0, 0.0), 0.0),
                     terra)
    past = 1.1 * system.bodies[terra].reach
    self.assertEqual(system.anchorFor(terra, (past, 0.0, 0.0), 0.0), 0)

  def test_fold(self) -> None:
    """A leap folds into every body: at time nought each is where it was
    at the leap's time; the system's version counts it."""
    system = self.systemOf()
    s = 4.2e4
    before = [system.relative(k, 0, s)[0] for k in range(12)]
    system.fold(s)
    self.assertEqual(system.version, 1)
    for k in range(12):
      self.assertClose(system.relative(k, 0, 0.0)[0], before[k], 1e-3)
