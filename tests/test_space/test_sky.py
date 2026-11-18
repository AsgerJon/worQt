"""
TestSky covers the flown sky (user, 2026-11-18: real gravity among the
heavy bodies, "PHYSICS MUST BE REAL"; '_ephemeris'): flown a year, the
whole sky's energy and its spin (angular momentum) about its middle
hold; Luna goes round in the Moon's month, between the Moon's nearest
and farthest; Terra swings round the Terra-Luna barycentre, some 4700
km off it, while the barycentre's path is a smooth ellipse round Sol;
Mani stays Terra's for five years; a saved sky flown on again is the
same to the bit; it flies its rows ahead as time goes, a step or two at
a time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.space._conic import Conic
from worQt.gaming.space._ephemeris import AHEAD, SPAN

from . import SpaceTest

G = 6.6743e-11
DAY = 86400.0
YEAR = 365.25 * DAY


def _absolute(row: numpy.ndarray, parents: tuple) -> numpy.ndarray:
  """Returns each body's place (or velocity) from Sol, 'row' each's from
  its parent."""
  out = numpy.zeros_like(row)
  for k, parent in enumerate(parents):
    if parent >= 0:
      out[k] = row[k] + out[parent]
  return out


def _wholeOf(system: object, row: numpy.ndarray) -> tuple:
  """Returns the sky's energy (J) and angular momentum (kg m²/s, a
  triple) about its barycentre, at the states 'row'."""
  parents = system.ephemeris.parents
  masses = numpy.asarray(system.ephemeris.mus) / G
  places = _absolute(row[:, 0], parents)
  speeds = _absolute(row[:, 1], parents)
  whole = masses.sum()
  places = places - (masses[:, None] * places).sum(0) / whole
  speeds = speeds - (masses[:, None] * speeds).sum(0) / whole
  energy = 0.5 * (masses * (speeds * speeds).sum(1)).sum()
  for i in range(len(masses)):
    for j in range(i + 1, len(masses)):
      energy -= G * masses[i] * masses[j] / numpy.linalg.norm(
        places[i] - places[j])
  spin = (masses[:, None] * numpy.cross(places, speeds)).sum(0)
  return energy, spin


class TestSky(SpaceTest):
  """Tests for the flown sky."""

  #  A year of the sky on the CPU: some ten seconds; five years, a
  #  minute.
  __time_out__ = 600.0

  def test_whole(self) -> None:
    """Flown a year, the sky's energy holds to a millionth, its spin to
    a ten-millionth."""
    system = self.systemOf()
    ephemeris = system.ephemeris
    energy, spin = _wholeOf(system, ephemeris.rows[0])
    system.coveredTo(YEAR)
    later, turned = _wholeOf(system, ephemeris.rows[-1])
    self.assertLess(abs(later - energy), 1e-6 * abs(energy))
    self.assertLess(numpy.linalg.norm(turned - spin),
                    1e-7 * numpy.linalg.norm(spin))

  def test_month(self) -> None:
    """Luna goes round Terra in the Moon's sidereal month (27.32 days, on
    the average over a year), between the Moon's nearest and farthest
    (some 356 000 and 406 700 km)."""
    system = self.systemOf()
    luna = system.named('Luna')
    crossings, before = [], None
    for k in range(int(400 * DAY / 3600.0)):
      place = system.stateOf(luna, k * 3600.0)[0]
      angle = math.atan2(place[1], place[0])
      if before is not None and before < 0.0 <= angle:
        crossings.append(k * 3600.0 / DAY)
      before = angle
      apart = math.dist(place, (0.0, 0.0, 0.0))
      self.assertGreater(apart, 354e6)
      self.assertLess(apart, 408e6)
      if k % 2000 == 0:
        system.ephemeris.trimmed(k * 3600.0)
    months = (crossings[-1] - crossings[0]) / (len(crossings) - 1)
    self.assertGreaterEqual(len(crossings), 14)
    self.assertLess(abs(months - 27.32), 0.06)

  def test_barycentre(self) -> None:
    """Terra swings round the barycentre of it and its moons, some 4700
    km off it; the barycentre's path round Sol is a month on where its
    path then (Sol alone pulling it) has it, within a twentieth of
    that."""
    system = self.systemOf()
    terra = system.named('Terra')
    moons = system.children(terra)
    masses = [system.bodies[k].mu for k in (terra,) + moons]
    whole = sum(masses)

    def barycentre(t: float) -> tuple:
      place, speed = system.stateOf(terra, t)
      shift = [0.0, 0.0, 0.0]
      drift = [0.0, 0.0, 0.0]
      for k, mu in zip(moons, masses[1:]):
        there, moving = system.stateOf(k, t)
        shift = [s + mu * x / whole for s, x in zip(shift, there)]
        drift = [s + mu * x / whole for s, x in zip(drift, moving)]
      return (tuple(p + s for p, s in zip(place, shift)),
              tuple(v + s for v, s in zip(speed, drift)), shift)

    offs = [math.dist(barycentre(d * DAY)[2], (0.0, 0.0, 0.0))
            for d in range(28)]
    self.assertGreater(sum(offs) / len(offs), 4400e3)
    self.assertLess(sum(offs) / len(offs), 5000e3)
    place, speed, _ = barycentre(0.0)
    path = Conic.fromState(system.bodies[0].mu + whole, place, speed)
    later = barycentre(28.0 * DAY)[0]
    self.assertLess(math.dist(path.stateAt(28.0 * DAY)[0], later),
                    0.05 * 4700e3 * 28.0)

  def test_mani(self) -> None:
    """Mani stays Terra's, flown five years: within Terra's reach, never
    nearer Luna than her own reach and Mani's."""
    system = self.systemOf()
    terra, luna, mani = (system.named(name) for name in
                         ('Terra', 'Luna', 'Mani'))
    reach = system.bodies[terra].reach
    near = system.bodies[luna].reach + system.bodies[mani].reach
    ephemeris = system.ephemeris
    for year in range(1, 6):
      system.coveredTo(year * YEAR)
      rows = ephemeris.rows
      far = numpy.linalg.norm(rows[:, mani, 0], axis=1).max()
      apart = numpy.linalg.norm(rows[:, mani, 0] - rows[:, luna, 0],
                                axis=1).min()
      self.assertLess(far, reach)
      self.assertGreater(apart, near)
      ephemeris.trimmed(year * YEAR)

  def test_kept(self) -> None:
    """A sky kept (at its last leap) and flown on anew from there is the
    same to the bit, a day on."""
    system = self.systemOf()
    system.fold(5.0 * SPAN + 123.0)
    kept = system.ephemeris.kept()
    system.coveredTo(DAY)
    before = [system.stateOf(k, DAY) for k in range(len(system.bodies))]
    other = self.systemOf()
    other.restored(kept)
    for k in range(len(system.bodies)):
      self.assertEqual(other.stateOf(k, DAY), before[k])

  def test_ahead(self) -> None:
    """It keeps 'AHEAD' s flown past what is asked, a step or two at a
    time as time goes on; asked of a time before its rows, it raises."""
    system = self.systemOf()
    ephemeris = system.ephemeris
    system.coveredTo(0.0)
    self.assertGreaterEqual(ephemeris.end, AHEAD)
    rows = len(ephemeris.rows)
    system.coveredTo(1.5 * SPAN)
    self.assertLessEqual(len(ephemeris.rows) - rows, 2)
    system.fold(10.0 * SPAN)
    with self.assertRaises(ValueError):
      ephemeris.stateOf(1, -100.0 * SPAN)
