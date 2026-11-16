"""
TestGauge covers the real car's speedometer on its dash ('_gauge';
user, 2026-11-15: "let's add a speedometer. both a virtual one on the
GUI and a diegetic one next to the steering wheel"): its needle points
at 0 km/h 135 degrees left of upright, at the dial's middle speed
upright, at its top 135 degrees right, held there past it, either way
the car goes; the dial faces the driver's eyes, its ways square; it
stands clear of the steering wheel's rim, behind the dash hoop's bar,
inside the cockpit's opening; its face's picture spans it once; and
the needle drawn on the stand-in car turns with its speed
('gui._walkdress.GaugeDress').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys import BrakeLine, FourthWall, State
from worQt.phys import _gauge, _magiccar
from worQt.phys._automatic import AutomaticDrive
from worQt.phys._realcar import COLUMN_TOP, CORNERS, Antilock
from worQt.phys._realcar import RealCarControls, TUB_FRONT
from worQt.phys._rig import TuneUp, WheelSetup
from worQt.phys._vectors import dot, minus, norm, plus, scaled

from . import PhysTest

#  The steering wheel's rim's radius (its grip's middle), m.
RIM = 0.165


class TestGauge(PhysTest):
  """Tests for the dash's speedometer (a few seconds)."""

  def test_angles(self) -> None:
    """The needle sweeps 270 degrees from 0 km/h to the top, upright at
    half the top, held at its ends; backing reads as going."""
    top = _gauge.TOP_SPEED
    self.assertNear(math.degrees(_gauge.angleOf(0.0)), -135.0, 1e-9)
    self.assertNear(math.degrees(_gauge.angleOf(0.5 * top)), 0.0, 1e-9)
    self.assertNear(math.degrees(_gauge.angleOf(top)), 135.0, 1e-9)
    self.assertNear(_gauge.angleOf(2.0 * top), _gauge.angleOf(top), 1e-12)
    self.assertNear(_gauge.angleOf(-50.0), _gauge.angleOf(50.0), 1e-12)

  def test_frame(self) -> None:
    """The dial faces the driver's eyes; its ways are units, square to
    each other, its right the car's right."""
    middle, out, up, right = _gauge.frameOf()
    toward = minus(_gauge.EYES, middle)
    self.assertNear(dot(out, scaled(toward, 1.0 / norm(toward))), 1.0,
                    1e-12)
    for way in (out, up, right):
      self.assertNear(norm(way), 1.0, 1e-12)
    for one, two in ((out, up), (out, right), (up, right)):
      self.assertNear(dot(one, two), 0.0, 1e-12)
    self.assertLess(right[1], -0.5)
    self.assertGreater(up[2], 0.5)

  def test_placed(self) -> None:
    """Every point of the dial's bezel stands 3 cm or more clear of the
    steering wheel's rim (as far from its middle as its rim, or more),
    behind the dash hoop's bar, inside the cockpit's opening."""
    from worQt.phys._bodyshell import COCKPIT_FRONT
    rows = _gauge.bezelRows()
    points = rows[:, :3]
    far = numpy.linalg.norm(points - numpy.array(COLUMN_TOP), axis=1)
    self.assertGreater(far.min(), RIM + 0.03)
    bezel = points[numpy.linalg.norm(
      points - numpy.array(_gauge.MIDDLE), axis=1) < 0.06]
    self.assertLess(bezel[:, 0].max(), TUB_FRONT)
    self.assertLess(bezel[:, 0].max(), COCKPIT_FRONT)

  def test_face(self) -> None:
    """The face's picture spans it once (its coordinates 0 to 1), every
    corner facing the driver."""
    rows = _gauge.faceRows()
    _, out, _, _ = _gauge.frameOf()
    self.assertNear(rows[:, 6].min(), 0.0, 1e-9)
    self.assertNear(rows[:, 6].max(), 1.0, 1e-9)
    self.assertNear(rows[:, 7].min(), 0.0, 1e-9)
    self.assertNear(rows[:, 7].max(), 1.0, 1e-9)
    self.assertLess(numpy.abs(rows[:, 3:6] - numpy.array(out)).max(), 1e-12)

  def test_dressed(self) -> None:
    """On the stand-in car going 120 km/h (half the dial), its needle's
    tip stands straight up the dial from its hub; standing, 135 degrees
    left."""
    from worQt.phys.gui._walkdress import GaugeDress
    controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0),
                               TuneUp((WheelSetup(),) * len(CORNERS)),
                               AutomaticDrive(), Antilock(_magiccar.WHEELS))
    assembly, states = _magiccar.magicCar(controls)
    middle, out, up, right = _gauge.frameOf()
    for kmh, angle in ((120.0, 0.0), (0.0, -135.0)):
      chassis = states[_magiccar.CHASSIS]
      moving = list(states)
      moving[_magiccar.CHASSIS] = State(chassis.place, chassis.turn,
                                        (kmh / 3.6, 0.0, 0.0))
      quads = GaugeDress(assembly, _magiccar.CHASSIS).quads(
        tuple(moving))['needle']
      corners = quads[:, :, :3].reshape(-1, 3)
      tip = corners[numpy.argmax(corners @ numpy.array(plus(
        scaled(up, math.cos(math.radians(angle))),
        scaled(right, math.sin(math.radians(angle))))))]
      way = minus(tuple(tip), middle)
      seen = math.degrees(math.atan2(dot(way, right), dot(way, up)))
      with self.subTest(kmh=kmh):
        self.assertNear(seen, angle, 3.0)
