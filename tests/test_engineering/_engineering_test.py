"""
EngineeringTest and EngineeringWidgetTest are the base classes for the
tests of 'worQt.engineering'. 'EngineeringTest' subclasses 'BaseTest'
for the structural model, which needs no Qt; 'EngineeringWidgetTest'
subclasses 'WidgetTest' for the widgets.

Both share one example: the wall over the entrance of KIT's
'AC20-Institute-Var-2', a deep beam spanning 6 m between two bearings,
2.7 m high and 0.3 m thick, carrying 1200 kN spread along its top, of
the default materials. 'DEEP_BEAM' is its text and 'deepBeam' builds
it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.engineering import Disk
from worQt.qtest import WidgetTest

DEEP_BEAM = """disk 6 x 2.7 x 0.3 fc 30 fy 800 E 200000
support bottom 0 0.3 y
support bottom 5.7 6 x y
load top 0 6 F 0 -1200"""


def deepBeam() -> Disk:
  """The 'deepBeam' function returns the example disk, read from
  'DEEP_BEAM'."""
  return Disk(DEEP_BEAM)


class EngineeringTest(BaseTest):
  """Base class for the tests of the structural model."""


class EngineeringWidgetTest(WidgetTest):
  """Base class for the tests of the engineering widgets."""
