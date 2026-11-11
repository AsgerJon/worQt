"""
The 'worQt.engineering.diagrams' package draws section force diagrams,
'snitkraftkurver': a plane frame of straight members, a beam among
them, on its supports under its loads, in kN and m, y up, reckoned
exactly. It needs no Qt; 'worQt.engineering.diagrams.gui' shows it.

- Node, Member, Support: the joints, the members between them, hinged
  at an end or not, and what holds the frame at a node.
- PointLoad, LineLoad, PointMoment: the loads, each along a member.
- Frame: the parts together; how indeterminate it is.
- Analysis: the frame reckoned: its reactions, N, V and M along each
  member, where they peak, and how it bends.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._parts import Node, Member, Support
from ._parts import PointLoad, LineLoad, PointMoment
from ._frame import Frame
from ._analysis import Analysis

__all__ = (
  'Node',
  'Member',
  'Support',
  'PointLoad',
  'LineLoad',
  'PointMoment',
  'Frame',
  'Analysis',
)
