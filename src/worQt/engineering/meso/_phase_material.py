"""
PhaseMaterial is what the lattice needs to know of a material: how stiff
it is, how strong and how tough.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple


class PhaseMaterial(NamedTuple):
  """
  PhaseMaterial is what the lattice needs to know of a material, in mm,
  N and MPa: its 'stiffness', Young's modulus E; its 'tension', the
  tensile strength ft; its 'toughness', the fracture energy Gf, in N/mm,
  spent opening a crack in it; its 'cohesion' c and 'friction' mu, the
  shear it holds along a face being c + mu times the pressure across it;
  and its 'shearToughness', the energy, in N/mm, spent sliding the
  cohesion off.
  """

  stiffness: float
  tension: float
  toughness: float
  cohesion: float
  friction: float
  shearToughness: float
