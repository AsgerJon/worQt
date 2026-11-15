"""
LabTest and LabWidgetTest are the base classes for the tests of
'worQt.engineering.lab': 'LabTest' subclasses 'BaseTest' for the model,
which needs no Qt, each class given a 'Worker' of its own, closed when
it is done; 'LabWidgetTest' subclasses 'WidgetTest' for the widgets.

The standard beam is the lab's own: 3300 mm long, 300 high and 200
wide, of concrete of fcm 38 MPa (C30), with 3 Ø16 along the bottom and
2 Ø10 along the top, both with 30 mm of cover, of B500 bars yielding at
550 MPa. By hand, its bottom bars, As = 603 mm², d = 262 mm, carry
Mu = As fy (d - 0.4 x) = 79.7 kNm, x = As fy / (0.8 b fcm) = 54.6 mm;
it cracks at Mcr = fctm b h² / 6 = 8.7 kNm, fctm = 2.90 MPa.

The small beam, quick to reckon as a solid, is 1600 x 200 x 120, of the
same concrete, 2 Ø12 along its bottom and 2 Ø8 along its top, both
with 25 mm of cover, Ø6 stirrups every 100 mm, on 'smallRig'. By hand,
d = 169 mm: its bars carry Mu = 19.3 kNm, 77 kN in all over its shear
spans of 500 mm; without stirrups, EN 1992-1-1's VRd,c with mean values,
0.18 k (100 rho fck)^(1/3) b d = 23.5 kN a span, 47 kN in all, so it
fails in shear first; its stirrups, Asw / s z fy cot 21.8°, carry 118
kN a span, so with them it bends to failure.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worksees import Worker

from worQt.engineering.lab import Actuator, BarLayer, Control, RCBeam
from worQt.engineering.lab import Rig, Stirrups, Support
from worQt.qtest import WidgetTest


def standardBeam() -> RCBeam:
  """The 'standardBeam' function returns the standard beam."""
  return RCBeam()


def smallBeam(stirrups: Stirrups = None) -> RCBeam:
  """The 'smallBeam' function returns the small beam, of 'stirrups',
  Ø6 every 100 mm unless given others."""
  if stirrups is None:
    stirrups = Stirrups(6.0, 100.0, ())
  return RCBeam(1600.0, 200.0, 120.0, 38.0, 550.0, 2e5,
                BarLayer(2, 12.0, 25.0), BarLayer(2, 8.0, 25.0), stirrups)


def smallRig() -> Rig:
  """The 'smallRig' function returns the small beam's rig: four point
  bending over 1400 mm, the loads 500 mm in from the supports, the
  control ramping midspan down 0.1 mm a second, steps of 0.2 mm."""
  return Rig((Support(100.0, 'pin'), Support(1500.0, 'roller')),
             (Actuator(600.0, -1, 1.0), Actuator(1000.0, 0, 1.0)),
             (600.0, 1000.0, 800.0),
             Control(2, 0, -0.1, -50.0, 0.004, 0.5, 0.05, 0.0, 1.0))


class LabTest(BaseTest):
  """Base class for the tests of the lab's model, each class given a
  'worker' of its own."""

  worker: Worker

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.worker = Worker()

  @classmethod
  def tearDownClass(cls) -> None:
    try:
      cls.worker.close()
    finally:
      super().tearDownClass()


class LabWidgetTest(WidgetTest):
  """Base class for the tests of the lab's widgets."""
