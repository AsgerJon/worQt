"""
LatticeBase is what a lattice of cells and springs is, in the plane or
in space: the materials, the springs as rows, and their elastic forces.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
import torch
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import splu
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._phase_material import PhaseMaterial
from ._phase_num import PhaseNum

_STONE = PhaseNum.STONE.index
_MORTAR = PhaseNum.MORTAR.index


class LatticeBase(BaseObject):
  """
  LatticeBase is what a lattice of cells and springs is, in the plane or
  in space. Each cell is a rigid body, of 'bodyMoves' movements, three in
  the plane, six in space, and so is each platen, the bottom's after the
  cells and the top's last. Each spring joins two bodies across the face
  they share: 'first' and 'second', the nodes it joins; 'centres' and
  'faceAreas' of its face; 'distances' and 'normals', from the first
  node towards the second; 'phases', of 'PhaseNum', by index; and
  'stoneShares', how much of its reach is in stone, one for a spring on
  a platen from a cell in stone. 'normalRows' and 'shearRows' are how it
  stretches and slides, the latter one way in the plane and two in
  space, as the movements 'dofs' of its two bodies go.

  'moduliOf' are the springs' moduli of given stone and mortar: the
  stone's and the mortar's for their springs, the two in series along a
  bond's; 'moduli' are those of the lattice's own materials. Of
  Poisson's ratio nought, a spring's shear is as stiff as its stretch.
  'elasticForces' are the springs' forces at given movements, all
  elastic, and 'elasticModulus' the stress over the strain the lattice
  takes between its platens, worked out exactly.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __body_moves__ = 3  # movements of a body: three in the plane

  #  Fallback Variables
  #    E MPa, ft MPa, Gf N/mm, c MPa, mu, GII N/mm
  __fallback_stone_material__ = PhaseMaterial(
      70000.0, 10.0, 0.10, 20.0, 0.6, 1.0)
  __fallback_mortar_material__ = PhaseMaterial(
      25000.0, 4.0, 0.06, 8.0, 0.6, 0.6)
  __fallback_bond_material__ = PhaseMaterial(
      25000.0, 2.0, 0.025, 4.0, 0.6, 0.25)

  #  Private Variables
  __lattice_parts__: dict | None = None

  #  Virtual Variables
  stoneMaterial: Field[PhaseMaterial] = Field()
  mortarMaterial: Field[PhaseMaterial] = Field()
  bondMaterial: Field[PhaseMaterial] = Field()
  bodyMoves: Field[int] = Field()
  liftColumn: Field[int] = Field()
  platenLift: Field[int] = Field()
  loadedArea: Field[float] = Field()
  nodes: Field[torch.Tensor] = Field()
  nodeCount: Field[int] = Field()
  boundaryNodes: Field[torch.Tensor] = Field()
  first: Field[torch.Tensor] = Field()
  second: Field[torch.Tensor] = Field()
  centres: Field[torch.Tensor] = Field()
  faceAreas: Field[torch.Tensor] = Field()
  distances: Field[torch.Tensor] = Field()
  normals: Field[torch.Tensor] = Field()
  phases: Field[torch.Tensor] = Field()
  stoneShares: Field[torch.Tensor] = Field()
  moduli: Field[torch.Tensor] = Field()
  bottomMask: Field[torch.Tensor] = Field()
  topMask: Field[torch.Tensor] = Field()
  normalRows: Field[torch.Tensor] = Field()
  shearRows: Field[torch.Tensor] = Field()
  dofs: Field[torch.Tensor] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @stoneMaterial.GET
  def _getStoneMaterial(self, ) -> PhaseMaterial:
    """The 'stoneMaterial' getter returns the stones' material."""
    return self.__fallback_stone_material__

  @mortarMaterial.GET
  def _getMortarMaterial(self, ) -> PhaseMaterial:
    """The 'mortarMaterial' getter returns the mortar's material: cement
    paste with the sand and the stones too small to show."""
    return self.__fallback_mortar_material__

  @bondMaterial.GET
  def _getBondMaterial(self, ) -> PhaseMaterial:
    """The 'bondMaterial' getter returns the bond's material, where the
    mortar meets a stone; how stiff it is the stone and the mortar
    say."""
    return self.__fallback_bond_material__

  @bodyMoves.GET
  def _getBodyMoves(self, ) -> int:
    """The 'bodyMoves' getter returns how many ways a body moves."""
    return self.__body_moves__

  @liftColumn.GET
  def _getLiftColumn(self, ) -> int:
    """The 'liftColumn' getter returns which of a spring's movements is
    its second body moving up: a platen's, on a spring on it."""
    return self.bodyMoves + 1

  @platenLift.GET
  def _getPlatenLift(self, ) -> int:
    """The 'platenLift' getter returns which of all the movements is the
    top platen moving up."""
    return self.bodyMoves * (self.nodeCount + 1) + 1

  @loadedArea.GET
  def _getLoadedArea(self, ) -> float:
    """The 'loadedArea' getter returns the area the platens bear on, in
    mm²."""
    return self.faceAreas[self.bottomMask].sum().item()

  def _part(self, name: str) -> torch.Tensor:
    """One of the tensors the lattice is built of."""
    if self.__lattice_parts__ is None:
      raise MissingVariable(self, '__lattice_parts__', dict)
    return self.__lattice_parts__[name]

  @nodes.GET
  def _getNodes(self, ) -> torch.Tensor:
    """The 'nodes' getter returns the nodes, a row of coordinates
    each."""
    return self._part('nodes')

  @nodeCount.GET
  def _getNodeCount(self, ) -> int:
    """The 'nodeCount' getter returns how many nodes, and cells, there
    are."""
    return len(self.nodes)

  @boundaryNodes.GET
  def _getBoundaryNodes(self, ) -> torch.Tensor:
    """The 'boundaryNodes' getter tells which cells end on an edge."""
    return self._part('boundary')

  @first.GET
  def _getFirst(self, ) -> torch.Tensor:
    """The 'first' getter returns the first node of each spring."""
    return self._part('first')

  @second.GET
  def _getSecond(self, ) -> torch.Tensor:
    """The 'second' getter returns the second node of each spring, or
    the platen it bears on."""
    return self._part('second')

  @centres.GET
  def _getCentres(self, ) -> torch.Tensor:
    """The 'centres' getter returns the centre of each spring's face."""
    return self._part('centres')

  @faceAreas.GET
  def _getFaceAreas(self, ) -> torch.Tensor:
    """The 'faceAreas' getter returns the area of each spring's face, in
    mm²; in the plane, its length on a section a millimetre thick."""
    return self._part('faceAreas')

  @distances.GET
  def _getDistances(self, ) -> torch.Tensor:
    """The 'distances' getter returns how far each spring reaches: from
    node to node, or from the node to the platen."""
    return self._part('distances')

  @normals.GET
  def _getNormals(self, ) -> torch.Tensor:
    """The 'normals' getter returns the unit vector of each spring, from
    its first node towards its second."""
    return self._part('normals')

  @phases.GET
  def _getPhases(self, ) -> torch.Tensor:
    """The 'phases' getter returns what each spring is of, by the index
    of its 'PhaseNum'."""
    return self._part('phases')

  @stoneShares.GET
  def _getStoneShares(self, ) -> torch.Tensor:
    """The 'stoneShares' getter returns how much of each spring's reach is
    in stone."""
    return self._part('shares')

  @moduli.GET
  def _getModuli(self, ) -> torch.Tensor:
    """The 'moduli' getter returns how stiff the material of each spring
    is, of the lattice's own materials, Young's modulus in MPa."""
    return self.moduliOf(self.stoneMaterial, self.mortarMaterial)

  @bottomMask.GET
  def _getBottomMask(self, ) -> torch.Tensor:
    """The 'bottomMask' getter tells which springs bear on the bottom
    platen."""
    return self.second == self.nodeCount

  @topMask.GET
  def _getTopMask(self, ) -> torch.Tensor:
    """The 'topMask' getter tells which springs bear on the top
    platen."""
    return self.second == self.nodeCount + 1

  @normalRows.GET
  def _getNormalRows(self, ) -> torch.Tensor:
    """The 'normalRows' getter returns how much each spring stretches as
    each of its bodies' movements goes."""
    return self._part('normalRows')

  @shearRows.GET
  def _getShearRows(self, ) -> torch.Tensor:
    """The 'shearRows' getter returns how much each spring slides, each
    way it slides, as each of its bodies' movements goes."""
    return self._part('shearRows')

  @dofs.GET
  def _getDofs(self, ) -> torch.Tensor:
    """The 'dofs' getter returns the movements of each spring's two
    bodies, by their place among all the movements."""
    return self._part('dofs')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def moduliOf(self, stone: PhaseMaterial,
               mortar: PhaseMaterial, ) -> torch.Tensor:
    """The 'moduliOf' method returns each spring's modulus of 'stone' and
    'mortar': the stone's and the mortar's for their springs, the two in
    series, as much of each as the spring reaches through, for the
    rest."""
    shares = self.stoneShares
    series = 1.0 / (shares / stone.stiffness
                    + (1.0 - shares) / mortar.stiffness)
    phases = self.phases
    out = torch.where(phases == _MORTAR, mortar.stiffness, series)
    return torch.where(phases == _STONE, stone.stiffness, out)

  def elasticStiffness(self, ) -> torch.Tensor:
    """The 'elasticStiffness' method returns the stiffness of each
    spring, stretch and shear alike, in N/mm: the modulus over its face,
    over its reach."""
    return self.moduli * self.faceAreas / self.distances

  def elasticForces(self, moves: torch.Tensor) -> torch.Tensor:
    """The 'elasticForces' method returns the forces the springs, all
    elastic, need on each movement to hold the bodies at 'moves'."""
    stiffness = self.elasticStiffness()
    flat = self.dofs.reshape(-1)
    local = moves[flat].reshape(len(stiffness), -1)
    normal, shear = self.normalRows, self.shearRows
    stretch = (normal * local).sum(1)
    slides = (shear * local[:, None]).sum(2)
    each = (stretch[:, None] * normal
            + (slides[:, :, None] * shear).sum(1)) * stiffness[:, None]
    out = torch.zeros_like(moves)
    return out.index_add_(0, flat, each.reshape(-1))

  def elasticModulus(self, ) -> float:
    """The 'elasticModulus' method returns the stress over the strain the
    lattice takes, all elastic, shortened between its platens, the
    platens holding fast to the cells: the mean of the forces on the two
    platens over the area they bear on."""
    moves = self.bodyMoves
    count = moves * self.nodeCount
    matrix = self._stiffnessMatrix()
    held = numpy.zeros(2 * moves)
    held[moves + 1] = -1.0
    free = matrix[:count][:, :count].tocsc()
    pushed = matrix[:count][:, count:] @ held
    factor = splu(free, 'MMD_AT_PLUS_A', 0.0, None, None,
                  {'SymmetricMode': True})
    solution = numpy.concatenate([factor.solve(-pushed), held])
    forces = matrix @ solution
    top, bottom = forces[count + moves + 1], forces[count + 1]
    stress = (top - bottom) / 2 / self.loadedArea
    return stress / (-1.0 / self.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _stiffnessMatrix(self, ) -> csc_matrix:
    """The stiffness of the lattice, all elastic, over every movement."""
    stiffness = self.elasticStiffness()
    normal, shear = self.normalRows, self.shearRows
    each = normal[:, :, None] * normal[:, None]
    each = each + (shear[:, :, :, None] * shear[:, :, None]).sum(1)
    each = each * stiffness[:, None, None]
    dofs = self.dofs
    width = dofs.shape[1]
    rows = dofs[:, :, None].expand(-1, width, width).reshape(-1).numpy()
    cols = dofs[:, None, :].expand(-1, width, width).reshape(-1).numpy()
    size = self.bodyMoves * (self.nodeCount + 2)
    return csc_matrix((each.reshape(-1).numpy(), (rows, cols)), (size, size))
