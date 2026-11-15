"""
Gears as they are cut (user, 2026-11-13: "in one end put teeth outside
of the shaft and put a motor with a tooth wheel to drive"): a spur
gear's teeth, involute, on the standard basic rack (pressure angle
'PRESSURE', addendum 'ADDENDUM' and dedendum 'DEDENDUM' modules). Each
tooth is a solid of its own, a prism along the gear's axis (its own z)
whose outline runs straight out from where it starts ('inside', on what
carries it) to the base circle, then along the involute in 'facets'
flat facets to the tip, across the tip: convex, as a contact takes a
piece of a shape. Two gears so cut, 'centreOf' apart, mesh: their teeth
meet on their involutes and the one turns the other at the ratio of
their teeth, as true as the facets (a facet stands off the involute by
a few hundredths of a millimetre at a module of 1.5). Gears that mesh
are given teeth with no common factor (user: "tooth wheel connections
must have their numbers of teeth be co prime"): each tooth then meets
every tooth of the other in turn, so they wear in alike.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._shape import Shape

PRESSURE = math.radians(20.0)
ADDENDUM, DEDENDUM = 1.0, 1.25


def involuteOf(angle: float) -> float:
  """The 'involuteOf' function returns the involute function of
  'angle': its tangent less itself, the angle an involute's point has
  turned on from where it leaves its base circle, rad."""
  return math.tan(angle) - angle


def pitchOf(module: float, teeth: int) -> float:
  """The 'pitchOf' function returns the radius of the pitch circle of a
  gear of 'teeth' at 'module', m."""
  return 0.5 * module * teeth


def tipOf(module: float, teeth: int) -> float:
  """The 'tipOf' function returns the radius of the tip circle, m."""
  return pitchOf(module, teeth) + ADDENDUM * module


def rootOf(module: float, teeth: int) -> float:
  """The 'rootOf' function returns the radius of the root circle, m."""
  return pitchOf(module, teeth) - DEDENDUM * module


def centreOf(module: float, teeth: int, others: int,
             backlash: float) -> float:
  """The 'centreOf' function returns how far apart the axles of two
  gears of 'teeth' and 'others' at 'module' stand to mesh, m: the sum of
  their pitch radii and 'backlash' more (so their teeth have play)."""
  return pitchOf(module, teeth) + pitchOf(module, others) + backlash


def halfThicknessAt(module: float, teeth: int, radius: float) -> float:
  """The 'halfThicknessAt' function returns half the angle a tooth
  spans at 'radius' (no less than the base circle's), rad: at the pitch
  circle a quarter of the angle a tooth and its gap take, and the
  involute's angle at the pitch circle less its angle there."""
  base = pitchOf(module, teeth) * math.cos(PRESSURE)
  pressure = math.acos(min(1.0, base / max(radius, base)))
  return (0.5 * math.pi / teeth + involuteOf(PRESSURE)
          - involuteOf(pressure))


def toothOutline(module: float, teeth: int, inside: float,
                 facets: int) -> tuple[tuple[float, float], ...]:
  """The 'toothOutline' function returns the outline of one tooth of a
  gear of 'teeth' at 'module', pointing along x, anticlockwise: from
  'inside' (m from the axle; inside the base circle, straight out to
  it) along its lower involute in 'facets' facets to the tip, across it
  and back down the upper side. A tooth pointed at its tip, or not
  convex, is refused."""
  base = pitchOf(module, teeth) * math.cos(PRESSURE)
  tip = tipOf(module, teeth)
  radii = [base + (tip - base) * k / facets for k in range(facets + 1)]
  if inside < base:
    radii.insert(0, inside)
  if halfThicknessAt(module, teeth, tip) <= 0.0:
    raise ValueError('the teeth come to a point')
  lower = [(r * math.cos(halfThicknessAt(module, teeth, r)),
            -r * math.sin(halfThicknessAt(module, teeth, r)))
           for r in radii]
  outline = tuple(lower + [(x, -y) for x, y in reversed(lower)])
  for k in range(len(outline)):
    a, b, c = outline[k - 1], outline[k], outline[(k + 1) % len(outline)]
    turn = ((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]))
    if turn <= 0.0:
      raise ValueError('the tooth is not convex')
  return outline


def prismOf(outline: tuple, low: float, high: float) -> Shape:
  """The 'prismOf' function returns the prism standing on 'outline' (a
  convex polygon in x and y, anticlockwise) from 'low' to 'high' along
  z."""
  count = len(outline)
  points = tuple((x, y, low) for x, y in outline)
  points += tuple((x, y, high) for x, y in outline)
  faces = []
  for k in range(count):
    after = (k + 1) % count
    faces.append((k, after, count + after))
    faces.append((k, count + after, count + k))
  for k in range(1, count - 1):
    faces.append((count, count + k, count + k + 1))
    faces.append((0, k + 1, k))
  return Shape(points, tuple(faces))


def spurGear(module: float, teeth: int, width: float, inside: float,
             hub: float, facets: int, sides: int) -> Shape:
  """The 'spurGear' function returns a spur gear of 'teeth' at 'module',
  'width' along its axle (its own z, its middle at nought): its teeth,
  each a solid of its own ('toothOutline', from 'inside' m from the
  axle), the first pointing along x, and, with 'hub' above nought, a
  hub of that radius they stand on, a regular polygon of 'sides' (its
  teeth reach into it). With no hub the teeth stand on what carries
  them (a shaft they are cut on)."""
  outline = toothOutline(module, teeth, inside, facets)
  half = 0.5 * width
  shape = None
  for k in range(teeth):
    angle = 2.0 * math.pi * k / teeth
    c, s = math.cos(angle), math.sin(angle)
    turned = tuple((c * x - s * y, s * x + c * y) for x, y in outline)
    tooth = prismOf(turned, -half, half)
    shape = tooth if shape is None else shape.joined(tooth)
  if hub > 0.0:
    shape = shape.joined(prismOf(roundOutline(hub, sides), -half, half))
  return shape


def roundOutline(radius: float,
                 sides: int) -> tuple[tuple[float, float], ...]:
  """The 'roundOutline' function returns a circle of 'radius' as a
  regular polygon of 'sides' corners on it, anticlockwise from x."""
  return tuple((radius * math.cos(2.0 * math.pi * k / sides),
                radius * math.sin(2.0 * math.pi * k / sides))
               for k in range(sides))

