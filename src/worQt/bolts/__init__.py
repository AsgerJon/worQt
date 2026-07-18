"""
The 'worQt.bolts' package is a worked civil-engineering example built on the
worQt widget stack: an isolated, visual calculation of how a bolt group
distributes an eccentric in-plane load by the elastic (vector) method.

The Qt-free 'bolt_calc' functions hold the structural mathematics;
'PaintBoltGroup' draws a bolt group and its per-bolt resultant forces, and
'BoltGroupWidget' is a ready-to-show demonstration of both.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._bolt_calc import centroid, polarMoment, boltForces
from ._paint_bolt_group import PaintBoltGroup
from ._bolt_group_widget import BoltGroupWidget
from ._bolts_app import BoltsWindow, BoltsApp

__all__ = [
  'centroid',
  'polarMoment',
  'boltForces',
  'PaintBoltGroup',
  'BoltGroupWidget',
  'BoltsWindow',
  'BoltsApp',
  ]
