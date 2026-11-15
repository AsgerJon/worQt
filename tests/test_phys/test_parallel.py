"""
TestParallel covers the world stepped side by side ('runParallel', user,
2026-11-13: "everything should run on gpu always!"): run by one thread
on the CPU ('cpu-parallel') it steps a tower of blocks and the bearing
(both its bearings, its motor on) as the serial run does, to a
picometre; on a GPU ('cuda', 256 threads in one block), where there is
one, to a micrometre over 0.02 s (the pushes added in another order:
alike but for the last bits, which contacts grow).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.phys import HeldPose, World, groundAt, minus, norm, runMotor
from worQt.phys import towerOnHexapod, walkingBearing
from worQt.phys._compiled import gpuDevice
from worQt.phys._scenes import BEARING_FIDELITY, MOTOR_FREE, MOTOR_STALL

from . import PhysTest

SHRUNK = 0.032 / 1.75


def tower(device: str) -> tuple:
  """The 'tower' function returns three layers of blocks on the held
  hexapod after 0.05 s stepped on 'device'."""
  assembly, states = towerOnHexapod(HeldPose((0.0, 0.0, 0.12)), 3, 0.01)
  world = World((0.0, 0.0, -9.81), 1e-3, None, None, True, None, device)
  return world.advancedAll(assembly, states, 0.05)


def bearing(device: str) -> tuple:
  """The 'bearing' function returns the bearing, its motor on, after
  0.02 s stepped on 'device' as the walk window steps it."""
  world = World((0.0, 0.0, -9.81), 1e-3, groundAt(SHRUNK), None, True,
                None, device, BEARING_FIDELITY)
  assembly, states = walkingBearing(SHRUNK)
  runMotor(assembly.motors[0].drive, MOTOR_STALL, MOTOR_FREE, True)
  for k in range(10):
    states = world.advancedAll(assembly, states, 0.002, 0.002 * k)
  return states


def farthest(one: tuple, two: tuple) -> float:
  """The 'farthest' function returns how far apart the most apart of
  two runs' bodies end, m."""
  return max(norm(minus(a.place, b.place)) for a, b in zip(one, two))


class TestParallel(PhysTest):
  """Tests for the world stepped side by side."""

  def test_tower(self) -> None:
    """Side by side on the CPU, a tower of blocks steps as serially, to
    a picometre."""
    self.assertLess(farthest(tower('cpu'), tower('cpu-parallel')), 1e-12)

  def test_bearing(self) -> None:
    """Side by side on the CPU, the bearing steps as serially, to a
    picometre."""
    self.assertLess(farthest(bearing('cpu'), bearing('cpu-parallel')),
                    1e-12)

  def test_gpu(self) -> None:
    """On a GPU, where there is one, the bearing steps as on the CPU, to
    a micrometre."""
    device = gpuDevice()
    if device is None:
      self.skipTest('no GPU here')
    self.assertLess(farthest(bearing('cpu'), bearing(device)), 1e-6)
