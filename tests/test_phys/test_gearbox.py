"""
TestGearbox covers the car's engine and gearbox ('Gearbox'): the
engine's full-load torque is the spec sheet's (205 N m at 4000 rpm,
135 kW at 7000), drawn straight between its points and held at its
ends; standing at full throttle it launches in first, the clutch
slipping at 'LAUNCH', passing that torque through first gear and the
final drive less the driveline's loss, times its boost; idling it gives
nothing; it shifts up at 'SHIFT_UP' on the throttle (not off it) and
down under 'SHIFT_DOWN', giving nothing for 'SHIFT_TIME' while it does;
at 'REDLINE' it cuts; backing, a standing car is put in first and
driven back at 'REVERSE' of the engine's torque.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.phys._gearbox import DRIVELINE, FINAL, GEARS, IDLE, LAUNCH
from worQt.phys._gearbox import REDLINE, REVERSE, RPM, SHIFT_DOWN
from worQt.phys._gearbox import SHIFT_TIME, SHIFT_UP, Gearbox
from worQt.phys._gearbox import engineTorque

from . import PhysTest

STEP = 0.01


def spinAt(rpm: float, gear: int) -> float:
  """The 'spinAt' function returns how fast the driven wheels turn,
  rad/s, turning the engine at 'rpm' in 'gear'."""
  return rpm / (GEARS[gear - 1] * FINAL * RPM)


class TestGearbox(PhysTest):
  """Tests for the engine and gearbox."""

  def test_torque(self) -> None:
    """205 N m at 4000 rpm, 135 kW at 7000 (to 50 W), straight between
    the curve's points, its ends' beyond."""
    self.assertNear(engineTorque(4000.0), 205.0, 1e-9)
    self.assertNear(engineTorque(7000.0) * 7000.0 / RPM, 135e3, 50.0)
    self.assertNear(engineTorque(3000.0), 0.5 * (188.0 + 202.0), 1e-9)
    self.assertEqual(engineTorque(100.0), engineTorque(800.0))
    self.assertEqual(engineTorque(9000.0), engineTorque(7500.0))

  def test_launch(self) -> None:
    """Standing at full throttle: first gear, the clutch slipping at
    'LAUNCH', its torque through first and the final drive, times the
    boost; idling, nothing."""
    box = Gearbox(2.0)
    whole = box.driven(0.0, 0.0, 1.0, STEP)
    self.assertEqual((box.gear, box.rpm, box.load), (1, LAUNCH, 1.0))
    self.assertNear(whole, 2.0 * engineTorque(LAUNCH) * GEARS[0] * FINAL
                    * DRIVELINE, 1e-9)
    self.assertEqual(box.driven(0.0, 0.0, 0.0, STEP), 0.0)
    self.assertEqual(box.rpm, IDLE)

  def test_shifts_up(self) -> None:
    """Past 'SHIFT_UP' on the throttle it shifts up, nothing driven for
    'SHIFT_TIME' (to a step), then drives in second at the revolutions
    second gives; off the throttle it stays in first."""
    box, spin = Gearbox(1.0), spinAt(SHIFT_UP + 10.0, 1)
    passed = 0.0
    self.assertEqual(box.driven(spin, 20.0, 1.0, STEP), 0.0)
    self.assertNear(box.shifting, SHIFT_TIME, 1e-12)
    while box.shifting:
      self.assertEqual(box.driven(spin, 20.0, 1.0, STEP), 0.0)
      passed += STEP
    self.assertNear(passed, SHIFT_TIME, 1.1 * STEP)
    self.assertEqual(box.gear, 2)
    self.assertGreater(box.driven(spin, 20.0, 1.0, STEP), 0.0)
    self.assertNear(box.rpm, (SHIFT_UP + 10.0) * GEARS[1] / GEARS[0],
                    1e-6)
    coasting = Gearbox(1.0)
    self.assertEqual(coasting.driven(spin, 20.0, 0.0, STEP), 0.0)
    self.assertEqual((coasting.gear, coasting.shifting), (1, 0.0))

  def test_shifts_down(self) -> None:
    """Under 'SHIFT_DOWN' it shifts down a gear."""
    box = Gearbox(1.0)
    box.gear = 3
    spin = spinAt(SHIFT_DOWN - 10.0, 3)
    self.assertEqual(box.driven(spin, 15.0, 0.5, STEP), 0.0)
    while box.shifting:
      box.driven(spin, 15.0, 0.5, STEP)
    self.assertEqual(box.gear, 2)

  def test_redline(self) -> None:
    """Past 'REDLINE' in top gear the limiter cuts the engine."""
    box = Gearbox(1.0)
    box.gear = len(GEARS)
    spin = spinAt(REDLINE + 10.0, len(GEARS))
    self.assertEqual(box.driven(spin, 70.0, 1.0, STEP), 0.0)
    self.assertEqual(box.load, 0.0)

  def test_reverse(self) -> None:
    """Standing in third and backing: put in first, driven back at
    'REVERSE' of the torque at the launch revolutions."""
    box = Gearbox(1.0)
    box.gear = 3
    whole = box.driven(0.0, 0.0, -1.0, STEP)
    self.assertEqual(box.gear, 1)
    self.assertNear(whole, -REVERSE * engineTorque(LAUNCH) * GEARS[0]
                    * FINAL * DRIVELINE, 1e-9)
