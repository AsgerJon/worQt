"""
TestGears covers spur gears as cut ('spurGear'): a tooth is half the
circular pitch thick at its pitch circle; its flanks lie on the
involute of its base circle (each corner where the involute unwound
from the base circle puts it), straight out from inside it; its outline
turns the same way at every corner (convex, anticlockwise). A gear is
closed, each tooth a piece of its own (a hub one more), its volume its
outlines' areas times its width. Two gears 'centreOf' apart with play
mesh: the one's tooth sits in the other's gap, no corner of either
inside the other, and turned on by more than the play they would
overlap. The bearing's gear and pinion have numbers of teeth with no
common factor (user: "tooth wheel connections must have their numbers
of teeth be co prime").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import centreOf, spurGear
from worQt.phys._gears import PRESSURE, halfThicknessAt, pitchOf
from worQt.phys._gears import rootOf, toothOutline
from worQt.phys._scenes import GEAR_TEETH, PINION_TEETH

from . import PhysTest

MODULE, WIDTH = 1.5e-3, 0.006
PLAY = 1e-4


def areaOf(outline: tuple) -> float:
  """The 'areaOf' function returns the area of the polygon 'outline'
  (anticlockwise: above nought), m²."""
  return 0.5 * sum(a[0] * b[1] - b[0] * a[1]
                   for a, b in zip(outline, outline[1:] + outline[:1]))


def turnedOutline(outline: tuple, angle: float, shift: float) -> tuple:
  """The 'turnedOutline' function returns 'outline' turned 'angle' rad
  about the origin, then moved 'shift' m along x."""
  c, s = math.cos(angle), math.sin(angle)
  return tuple((c * x - s * y + shift, s * x + c * y) for x, y in outline)


def inside(point: tuple, outline: tuple) -> bool:
  """The 'inside' function tells whether 'point' lies inside the convex
  anticlockwise polygon 'outline', more than a nanometre in."""
  for a, b in zip(outline, outline[1:] + outline[:1]):
    across = ((b[0] - a[0]) * (point[1] - a[1])
              - (b[1] - a[1]) * (point[0] - a[0]))
    if across / math.hypot(b[0] - a[0], b[1] - a[1]) <= 1e-9:
      return False
  return True


def overlapping(gearTurn: float, pinionTurn: float) -> bool:
  """The 'overlapping' function tells whether any corner of a tooth of
  the gear ('GEAR_TEETH', its axle at the origin, turned 'gearTurn')
  lies inside a tooth of the pinion ('PINION_TEETH', its axle
  'centreOf' with play along x, turned 'pinionTurn'), or the other way
  round."""
  centre = centreOf(MODULE, GEAR_TEETH, PINION_TEETH, PLAY)
  gear = toothOutline(MODULE, GEAR_TEETH, rootOf(MODULE, GEAR_TEETH), 3)
  pinion = toothOutline(MODULE, PINION_TEETH,
                        rootOf(MODULE, PINION_TEETH), 3)
  gears = [turnedOutline(gear, gearTurn + 2.0 * math.pi * k / GEAR_TEETH,
                         0.0) for k in range(GEAR_TEETH)]
  pinions = [turnedOutline(pinion, pinionTurn + 2.0 * math.pi * k
                           / PINION_TEETH, centre)
             for k in range(PINION_TEETH)]
  for ones, others in ((gears, pinions), (pinions, gears)):
    for one in ones:
      for other in others:
        if any(inside(point, other) for point in one):
          return True
  return False


class TestGears(PhysTest):
  """Tests for spur gears."""

  def test_thickness(self) -> None:
    """At its pitch circle a tooth is half the circular pitch thick (to
    1e-12 of it)."""
    for teeth in (PINION_TEETH, GEAR_TEETH):
      pitch = pitchOf(MODULE, teeth)
      thick = 2.0 * halfThicknessAt(MODULE, teeth, pitch) * pitch
      self.assertAlmostEqual(thick / (0.5 * math.pi * MODULE), 1.0, 12)

  def test_involute(self) -> None:
    """The lower flank's corners from the base circle out lie where the
    involute unwound from the base circle at the flank's foot puts them
    (to a nanometre); inside the base circle the flank runs straight out
    along a radius."""
    for teeth in (PINION_TEETH, GEAR_TEETH):
      base = pitchOf(MODULE, teeth) * math.cos(PRESSURE)
      outline = toothOutline(MODULE, teeth, rootOf(MODULE, teeth), 3)
      foot = -halfThicknessAt(MODULE, teeth, base)
      lower = outline[:len(outline) // 2]
      self.assertNear(math.atan2(lower[0][1], lower[0][0]), foot, 1e-12)
      for x, y in lower[1:]:
        t = math.sqrt(max(0.0, (x * x + y * y) / (base * base) - 1.0))
        unwound = (base * (math.cos(foot + t) + t * math.sin(foot + t)),
                   base * (math.sin(foot + t) - t * math.cos(foot + t)))
        self.assertNear((x, y), unwound, 1e-9)

  def test_convex(self) -> None:
    """Every corner of a tooth's outline turns left (anticlockwise,
    convex)."""
    for teeth in (PINION_TEETH, GEAR_TEETH):
      outline = toothOutline(MODULE, teeth, 0.95 * rootOf(MODULE, teeth),
                             3)
      for k in range(len(outline)):
        a, b = outline[k - 1], outline[k]
        c = outline[(k + 1) % len(outline)]
        self.assertGreater((b[0] - a[0]) * (c[1] - b[1])
                           - (b[1] - a[1]) * (c[0] - b[0]), 0.0)

  def test_gear(self) -> None:
    """A gear is closed, a piece to each tooth and one to its hub, its
    volume the teeth's and the hub's outlines' areas times its width."""
    root = rootOf(MODULE, PINION_TEETH)
    gear = spurGear(MODULE, PINION_TEETH, WIDTH, root, root, 3, 32)
    self.assertTrue(gear.isClosed())
    self.assertEqual(len(gear.pieces()), PINION_TEETH + 1)
    tooth = areaOf(toothOutline(MODULE, PINION_TEETH, root, 3))
    hub = 0.5 * 32 * root * root * math.sin(2.0 * math.pi / 32)
    self.assertAlmostEqual(gear.moments()[0] / (
        (PINION_TEETH * tooth + hub) * WIDTH), 1.0, 12)

  def test_mesh(self) -> None:
    """The bearing's gear and pinion, 'centreOf' apart with 0.1 mm of
    play, the gear's first tooth toward the pinion, the pinion turned
    half a tooth so a gap faces it (as the bearing has them): none of
    their corners inside the other's teeth, nor with the pinion turned
    0.1 degrees either way (within its play); turned 1.5 degrees (0.3 mm
    at its pitch circle) they would overlap."""
    gap = math.pi / PINION_TEETH
    for off, overlaps in ((0.0, False), (0.1, False), (-0.1, False),
                          (1.5, True), (-1.5, True)):
      self.assertEqual(overlapping(0.0, gap + math.radians(off)),
                       overlaps)

  def test_co_prime(self) -> None:
    """The bearing's gear and pinion have numbers of teeth with no
    common factor."""
    self.assertEqual(math.gcd(GEAR_TEETH, PINION_TEETH), 1)
