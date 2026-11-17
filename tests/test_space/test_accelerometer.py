"""
TestAccelerometer covers what the vessel feels (user, 2026-11-17: Asger
floating round, "FAFO rules"; then, after Asger suddenly had gravity
docked to Terra Prime: "There is NEVER gravity when in orbit EVER!!!",
"there better be a physically simulated such fucking thing every where
it needs to be calculated"): read from the simulated frame alone, the
forces but gravity a kilogram: on the pad the ground's one g up; in
orbit nought, coasting or docked to the station; thrusting, the thrust;
the latch's catch a jolt over its frame; nothing to read before a frame
has been simulated; the pull on what is loose in the cabin: the push the
other way, the turning's outward.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._dockingport import DockingPort, NOSE_PORT
from worQt.gaming.space._station import SPIN, Station
from worQt.gaming.space._turns import norm, rotated, unrotated
from worQt.gaming.space._vessel import MASS, Vessel

from . import FRAME, SpaceTest


class TestAccelerometer(SpaceTest):
  """Tests for the vessel's accelerometer."""

  __time_out__ = 300.0

  def _flown(self, vessel: Vessel, system: object, frames: int) -> None:
    """Flies 'vessel' 'frames' frames (the flight on the CPU)."""
    flight = self.flightOf()
    for k in range(frames):
      flight.flown((vessel,), system, k * FRAME, FRAME)

  def test_unread(self) -> None:
    """Before a frame has been simulated there is nothing to feel: it
    raises, it assumes nothing."""
    meter = Accelerometer()
    self.assertIsNone(meter.felt)
    with self.assertRaises(ValueError):
      meter.pullAt((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    with self.assertRaises(ValueError):
      meter.measured(Vessel(), FRAME)

  def test_pad(self) -> None:
    """Standing on the pad it feels the ground hold it up: about one g
    along its nose (less what the turning ground takes)."""
    system = self.systemOf()
    vessel = self.padded(system)
    self._flown(vessel, system, 120)
    meter = Accelerometer()
    meter.measured(vessel, FRAME)
    self.assertAlmostEqual(meter.felt[2], 9.79, 1)
    self.assertLess(abs(meter.felt[0]) + abs(meter.felt[1]), 0.05)

  def test_coasting(self) -> None:
    """Falling freely round Terra over the air it feels nothing at all,
    frame after frame."""
    system = self.systemOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    meter = Accelerometer()
    for _ in range(10):
      self._flown(vessel, system, 6)
      meter.measured(vessel, FRAME)
      self.assertLess(norm(meter.felt), 1e-5)
      self.assertLess(norm(meter.speeding), 1e-6)

  def test_thrust(self) -> None:
    """Thrusting in orbit it feels the thrust a kilogram, along its
    nose; the limiter holds it to its g."""
    system = self.systemOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    vessel.engine.throttled(1.0)
    vessel.engine.limited(1.0 * G0 * MASS)
    self._flown(vessel, system, 6)
    meter = Accelerometer()
    meter.measured(vessel, FRAME)
    self.assertAlmostEqual(meter.felt[2], G0, 3)
    self.assertLess(abs(meter.felt[0]) + abs(meter.felt[1]), 1e-3)

  def test_docked(self) -> None:
    """Docked to the station in orbit it feels the latch: nought but a
    hair (its middle on the station's axis: nothing to carry it round;
    the station falls as it does); the latch catching its drift is a
    jolt felt over that frame alone."""
    system = self.systemOf()
    station = Station(system)
    port = DockingPort(station)
    vessel = Vessel()
    middle, velocity = station.stateAt(0.0)
    rows = station.turnAt(0.0)
    axis = tuple(row[2] for row in rows)
    vessel.placed(station.parent, tuple(m + 120.0 * a for m, a in zip(
      middle, axis)), velocity, (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    port.aligned(vessel, 0.0)
    turn = port.turnAt(0.0)
    reading = port.readingOf(vessel, system, 0.0)
    place = tuple(p - n for p, n in zip(reading['port'], rotated(
      turn, NOSE_PORT)))
    drift = tuple(v - 0.5 * a for v, a in zip(reading['velocity'], axis))
    vessel.placed(station.parent, place, drift, turn, unrotated(
      turn, tuple(SPIN * a for a in axis)))
    port.latched(vessel, system, 0.0)
    meter = Accelerometer()
    meter.measured(vessel, FRAME)
    self.assertAlmostEqual(norm(meter.felt), 0.5 / FRAME, 3)
    for k in range(1, 30):
      port.heldOn(vessel, system, k * FRAME)
      meter.measured(vessel, FRAME)
      self.assertLess(norm(meter.felt), 1e-3)
      self.assertEqual(meter.speeding, (0.0, 0.0, 0.0))

  def test_pull(self) -> None:
    """The pull on what is loose: the push the other way; turning,
    outward from its axis."""
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 2.0 * G0), (0.0, 0.0, 0.0)
    meter.speeding = (0.0, 0.0, 0.0)
    self.assertClose(meter.pullAt((0.0, 1.0, 0.0), (0.0, 0.0, 0.0)),
                     (0.0, 0.0, -2.0 * G0), 1e-9)
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, 0.5)
    self.assertClose(meter.pullAt((0.0, 2.0, 0.0), (0.0, 0.0, 0.0)),
                     (0.0, 0.5, 0.0), 1e-9)
