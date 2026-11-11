"""
The 'worQt.engineering.meso' package simulates concrete from its
ingredients, at the scale of its stones, in mm, N and MPa: the stones,
placed as they are cast, held in mortar, and the bond between them, each
of its own stiffness, strength and toughness; tested as a laboratory
tests concrete. It needs no Qt; 'worQt.engineering.meso.gui' shows it.
It reckons with 'torch', and with 'scipy' for the cells and the exact
elastic solution.

- Grading: the grading curve of an aggregate, its 'kornkurve'.
- Stone: one stone of an aggregate, a convex polyhedron.
- Cylinder: a concrete cylinder as it is cast: its stones in the mould.
- WholeCylinder: a cylinder cast through and through, to see into.
- PhaseNum: what a spring of a lattice is made of.
- PhaseMaterial: how stiff, strong and tough a material is.
- LatticeBase: what a lattice of cells and springs is, plane or space.
- Lattice: the section through a cylinder's axis, as cells and springs.
- Lattice3D: the whole cylinder, as cells and springs in space.
- UniaxialTest: the lattice loaded between its platens, step by step.
- CompressionTest: the cylinder crushed.
- TensionTest: the cylinder pulled apart.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._grading import Grading, SIEVES
from ._stone import Stone
from ._cylinder import Cylinder, WholeCylinder
from ._phase_num import PhaseNum
from ._phase_material import PhaseMaterial
from ._lattice_base import LatticeBase
from ._lattice import Lattice
from ._lattice3d import Lattice3D
from ._uniaxial_test import UniaxialTest, CompressionTest, TensionTest

__all__ = (
  'Grading',
  'SIEVES',
  'Stone',
  'Cylinder',
  'WholeCylinder',
  'PhaseNum',
  'PhaseMaterial',
  'LatticeBase',
  'Lattice',
  'Lattice3D',
  'UniaxialTest',
  'CompressionTest',
  'TensionTest',
)
