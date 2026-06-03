"""
The 'fea' subpackage is a pure (Qt-free) 2D finite-element model for
pin-jointed trusses: 'Material', 'Section', 'Node' and 'Bar' elements, the
'Truss' that assembles and solves them, and the 'TrussSolution' results. It
has no worktoy-external dependencies beyond worktoy itself, so it builds and
solves without a running 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._linalg import matVec, solveLinear
from ._elements import Material, Section, Node, Bar
from ._truss import Truss, TrussSolution

__all__ = (
  'matVec',
  'solveLinear',
  'Material',
  'Section',
  'Node',
  'Bar',
  'Truss',
  'TrussSolution',
)
