"""
TestDrivetrain covers the drivetrain on its bench ('_drivetrain'; user,
2026-11-14: "you start work on the differential and the stick shift
gearbox and clutch ... dog-leg ... R-2-4 / 1-3-5"; "remember the
syncromesh"): every pair of gears in mesh shares no factor, the
gearbox's pairs as far apart; the stick goes through its dog-leg gate
(across only in the neutral row, 2 to 3 straight back, R and 1 on the
left), held at a synchro's blocker until its gear is at the shaft's
speed; each gear turns the wheels at its ratio times the final drive's
(to 2 %; forward, reverse backward); the differential: one wheel held,
the other turns twice the carrier, both free, their sum twice it (to 2
%); against held wheels the clutch let up stalls the engine at full
throttle (its 270 N m over the engine's 205), half let up with the
engine revved it slips (the engine running on); shifting with the clutch in the synchro cannot
bring the engine's side to the held shaft and the stick stays at the
blocker, the clutch down it goes in; the limiter holds it under 7700
rpm; the springs' world refuses gears. Tolerant: friction and gears
ring.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, GearMesh, SmallSteps, Sphere, State
from worQt.phys import World
from worQt.phys._drivetrain import BLOCKER, CARRIER, FINAL, FLYWHEEL
from worQt.phys._drivetrain import GATE, GEARS, HALVES, REVERSE, X, Z
from worQt.phys._drivetrain import DrivetrainControls, Shifter
from worQt.phys._drivetrain import drivetrainBench, drivetrainWorked
from worQt.phys._drivetrain import rpmOf, spinAbout

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 1.25e-4
GRAVITY = (0.0, 0.0, -9.81)
FORWARD = (0.0, 1.0, 0.0)


def ratioOf(name: str) -> float:
  """Returns gear 'name''s ratio, the engine's turns to the carrier's
  (reverse below nought)."""
  final = FINAL[1] / FINAL[0]
  if name == 'R':
    return -final * REVERSE[2] / REVERSE[0]
  low, high = GEARS[int(name) - 1]
  return final * high / low


class TestDrivetrain(PhysTest):
  """Tests for the drivetrain (about two minutes on the CPU)."""

  __time_out__ = 900.0

  def setUp(self) -> None:
    """A bench, its controls, its world (small steps, on the CPU)."""
    self.controls = DrivetrainControls()
    self.assembly, self.states = drivetrainBench(self.controls)
    self.world = SmallSteps(GRAVITY, None, STEP, 1, 1e-7, 'cpu')
    self.clock = 0.0

  def ran(self, seconds: float) -> None:
    """Works and steps the bench 'seconds' on, a frame at a time."""
    for _ in range(round(seconds / FRAME)):
      drivetrainWorked(self.controls, self.states, FRAME)
      self.states = self.world.advancedAll(self.assembly, self.states,
                                           FRAME, self.clock)
      self.clock += FRAME

  def shifted(self, name: str) -> None:
    """Shifts into 'name' as a driver does: the clutch down, the stick
    moved (waiting for the synchro, two seconds at most), the clutch
    let up."""
    c = self.controls
    c.throttle, c.pedal, c.asked = 0.0, 1.0, name
    wanted = None if name == 'N' else name
    for _ in range(10):
      self.ran(0.2)
      if c.shifter.engaged == wanted and abs(c.shifter.throw) in (
          0.0, 1.0):
        break
    self.assertEqual(c.shifter.engaged, wanted)
    c.pedal = 0.0
    self.ran(0.5)

  def test_teeth(self) -> None:
    """Every pair in mesh shares no factor; the gearbox's pairs all sum
    to the same teeth (as far apart)."""
    for mesh in self.assembly.meshes:
      self.assertEqual(math.gcd(mesh.firstTeeth, mesh.secondTeeth), 1)
    sums = {low + high for low, high in GEARS}
    self.assertEqual(len(sums), 1)

  def test_gate(self) -> None:
    """The stick crosses planes only in the neutral row: 1 to 2 through
    it, 2 to 3 straight back in the middle plane; R and 1 in the left
    plane; held at the blocker until synced, then in."""
    self.assertEqual(GATE['R'][0], GATE['1'][0])
    self.assertEqual(GATE['2'][0], GATE['3'][0])
    self.assertEqual(GATE['4'][0], GATE['5'][0])
    self.assertEqual({GATE[n][1] for n in 'R24'}, {1})
    self.assertEqual({GATE[n][1] for n in '135'}, {-1})
    stick, synced = Shifter(), {name: 0.0 for name in GATE}
    for name, path in (('1', []), ('2', []), ('3', [])):
      for _ in range(60):
        stick.moved(name, FRAME, synced)
        path.append((stick.across, stick.throw))
        if abs(stick.throw) > 0.05:
          self.assertAlmostEqual(stick.across, round(stick.across))
      self.assertEqual(stick.engaged, name)
      if name == '3':
        self.assertTrue(all(abs(at) < 1e-9 for at, _ in path))
    stick.moved('4', 1.0, {name: 30.0 for name in GATE})
    for _ in range(30):
      stick.moved('4', FRAME, {name: 30.0 for name in GATE})
    self.assertEqual(stick.engaged, None)
    self.assertEqual(stick.blocked, '4')
    self.assertAlmostEqual(stick.throw, BLOCKER)
    stick.moved('4', FRAME, synced)
    self.assertEqual(stick.engaged, '4')

  def test_ratios(self) -> None:
    """In each gear the engine turns the carrier at its ratio times the
    final drive's (to 2 %): forward forward, reverse backward."""
    c = self.controls
    for name in ('1', '2', '3', '4', '5', 'N', 'R'):
      self.shifted(name)
      if name == 'N':
        c.line.pressure = 60e5
        self.ran(1.0)
        c.line.pressure = 0.0
        continue
      c.throttle = 0.15
      self.ran(0.6)
      engine = spinAbout(self.states[FLYWHEEL], X)
      carrier = spinAbout(self.states[CARRIER], FORWARD)
      self.assertNear(engine / carrier, ratioOf(name),
                      0.02 * abs(ratioOf(name)))

  def test_differential(self) -> None:
    """In second, the left wheel held, the right turns twice the
    carrier; let go, the two together turn twice it (to 2 %)."""
    c = self.controls
    self.shifted('2')
    c.throttle = 0.3
    self.ran(0.5)
    c.held.pressure = 60e5
    self.ran(0.8)
    carrier = spinAbout(self.states[CARRIER], FORWARD)
    left = spinAbout(self.states[HALVES[0]], Z)
    right = -spinAbout(self.states[HALVES[1]], Z)
    self.assertLess(abs(left), 0.02 * abs(carrier))
    self.assertNear(right, 2.0 * carrier, 0.02 * abs(carrier))
    c.held.pressure = 0.0
    self.ran(0.5)
    carrier = spinAbout(self.states[CARRIER], FORWARD)
    left = spinAbout(self.states[HALVES[0]], Z)
    right = -spinAbout(self.states[HALVES[1]], Z)
    self.assertNear(left + right, 2.0 * carrier, 0.02 * abs(carrier))

  def test_clutch(self) -> None:
    """Against held wheels, in first: let up at idle the clutch stalls
    the engine; restarted and revved, the clutch half let up slips (the
    engine runs on at full throttle, its 205 N m over the half clamp's
    140); let up, it stalls it (its 277 N m)."""
    c = self.controls
    c.line.pressure = 80e5
    self.shifted('1')
    self.assertFalse(c.running)
    c.starting, c.pedal = True, 1.0
    self.ran(0.6)
    self.assertTrue(c.running)
    c.throttle = 1.0
    self.ran(0.6)
    c.pedal = 0.55
    self.ran(1.0)
    self.assertTrue(c.running)
    self.assertGreater(rpmOf(self.states), 1000.0)
    c.pedal = 0.0
    self.ran(2.0)
    self.assertFalse(c.running)
    self.assertLess(abs(rpmOf(self.states)), 150.0)

  def test_synchro(self) -> None:
    """The wheels held, the clutch in, the engine idling: asked for
    first, the stick stays at the blocker (the cone cannot bring the
    engine's side to the held shaft); the clutch down, it goes in."""
    c = self.controls
    c.line.pressure = 80e5
    c.asked = '1'
    self.ran(1.0)
    self.assertEqual(c.shifter.engaged, None)
    self.assertEqual(c.shifter.blocked, '1')
    self.assertTrue(c.running)
    c.pedal = 1.0
    self.ran(1.5)
    self.assertEqual(c.shifter.engaged, '1')

  def test_limiter(self) -> None:
    """In neutral at full throttle the limiter holds the engine between
    7000 and 7700 rpm."""
    self.controls.throttle = 1.0
    self.ran(2.0)
    self.assertGreater(rpmOf(self.states), 7000.0)
    self.assertLess(rpmOf(self.states), 7700.0)

  def test_springs_refuse(self) -> None:
    """The springs' world refuses gears in mesh."""
    ball = Body.of(Sphere(0.05), 7850.0)
    mesh = GearMesh(0, X, 13, 1, X, 21, None)
    start = (State((0.0, 0.0, 1.0)), State((0.0, 0.1, 1.0)))
    with self.assertRaises(ValueError):
      World(GRAVITY, 1e-3, None).advancedAll(Assembly((ball, ball),
                                                      (mesh,)), start, 0.01)
