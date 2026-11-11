"""
DiagramsTest and DiagramsWidgetTest are the base classes for the tests
of 'worQt.engineering.diagrams': 'DiagramsTest' subclasses 'BaseTest'
for the model, which needs no Qt; 'DiagramsWidgetTest' subclasses
'WidgetTest' for the widgets.

'beam' makes a beam of members in a line along x, 6 m each, on the
supports given under the loads given: the hand's own cases, q 10 kN/m
and P 20 kN over L 6 m, give M = q L² / 8 = 45 kNm under a line load,
P L / 4 = 30 kNm under a point load at midspan, and so on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.engineering.diagrams import Frame, LineLoad, Member, Node
from worQt.engineering.diagrams import Support
from worQt.qtest import WidgetTest

SPAN = 6.0  # m
LOAD = 10.0  # kN/m
FORCE = 20.0  # kN


def beam(supports: tuple, loads: tuple, spans: int = 1) -> Frame:
  """The 'beam' function returns 'spans' members of 6 m in a line along
  x, on 'supports' under 'loads'."""
  nodes = (*[Node(SPAN * i, 0.0) for i in range(spans + 1)],)
  members = (*[Member(i, i + 1, 1e4, 1e6, False, False)
               for i in range(spans)],)
  return Frame(nodes, members, supports, loads)


def threeHinged() -> Frame:
  """The 'threeHinged' function returns a portal 6 m wide and 4 m high,
  pinned at its feet and hinged at the middle of its beam, under 10
  kN/m along its beam: by hand it thrusts q L² / 8 h = 11.25 kN at each
  foot, and its corners bend q L² / 8 = 45 kNm."""
  nodes = (Node(0.0, 0.0), Node(0.0, 4.0), Node(3.0, 4.0), Node(6.0, 4.0),
           Node(6.0, 0.0))
  members = (Member(0, 1, 1e4, 1e6, False, False),
             Member(1, 2, 1e4, 1e6, False, True),
             Member(2, 3, 1e4, 1e6, False, False),
             Member(3, 4, 1e4, 1e6, False, False))
  supports = (Support(0, 'pin'), Support(4, 'pin'))
  loads = (LineLoad(1, 0.0, 3.0, LOAD, LOAD, 'down'),
           LineLoad(2, 0.0, 3.0, LOAD, LOAD, 'down'))
  return Frame(nodes, members, supports, loads)


class DiagramsTest(BaseTest):
  """Base class for the tests of the diagrams' model."""


class DiagramsWidgetTest(WidgetTest):
  """Base class for the tests of the diagrams' widgets."""
