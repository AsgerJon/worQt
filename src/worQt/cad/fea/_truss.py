"""
The 'Truss' model assembles its nodes and bars into a global stiffness
system, applies the supports and nodal loads, and solves 'K u = F' for the
nodal displacements, the support reactions and the member axial forces.
'TrussSolution' carries the results, indexed to match the truss's node and
bar order. Everything is pure Python (no Qt, no numpy).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.mcls import BaseObject

from ._elements import Node, Bar
from ._linalg import solveLinear, matVec

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TrussSolution(BaseObject):
  """Results of a truss solve, indexed to the truss's nodes and bars."""

  displacements = AttriBox[list]()  # (dx, dy) per node, in mm
  reactions = AttriBox[list]()  # (rx, ry) per node, in N
  forces = AttriBox[list]()  # axial force per bar, in N (tension positive)

  def __str__(self, ) -> str:
    return 'TrussSolution(%d nodes, %d bars)' % (
        len(self.displacements), len(self.forces))

  __repr__ = __str__


class Truss(BaseObject):
  """An ordered collection of nodes and bars that can be solved."""

  nodes = AttriBox[list]()
  bars = AttriBox[list]()

  def addNode(self, node: Node) -> Node:
    """Append a node to the truss and return it."""
    self.nodes.append(node)
    return node

  def addBar(self, bar: Bar) -> Bar:
    """Append a bar to the truss and return it."""
    self.bars.append(bar)
    return bar

  def _index(self, ) -> dict:
    """Map each node's identity to its position, for DOF numbering."""
    return {id(node): i for i, node in enumerate(self.nodes)}

  def assemble(self, ) -> tuple:
    """The global stiffness matrix 'K' and load vector 'F' of the truss."""
    count = len(self.nodes)
    ndof = 2 * count
    stiffness = [[0.0] * ndof for _ in range(ndof)]
    index = self._index()
    for bar in self.bars:
      i = index[id(bar.nodeA)]
      j = index[id(bar.nodeB)]
      dofs = [2 * i, 2 * i + 1, 2 * j, 2 * j + 1]
      ke = bar.globalStiffness()
      for a in range(4):
        for b in range(4):
          stiffness[dofs[a]][dofs[b]] += ke[a][b]
    forces = [0.0] * ndof
    for i, node in enumerate(self.nodes):
      forces[2 * i] += node.loadX
      forces[2 * i + 1] += node.loadY
    return stiffness, forces

  def _fixedDofs(self, ) -> set:
    """The set of globally fixed degrees of freedom from the supports."""
    fixed = set()
    for i, node in enumerate(self.nodes):
      if node.fixX:
        fixed.add(2 * i)
      if node.fixY:
        fixed.add(2 * i + 1)
    return fixed

  def solve(self, ) -> TrussSolution:
    """
    Solve the truss and return a 'TrussSolution'. Raises 'ValueError' when
    the structure is insufficiently supported (a mechanism: a singular
    reduced system with no unique displacement solution).
    """
    count = len(self.nodes)
    ndof = 2 * count
    stiffness, loads = self.assemble()
    fixed = self._fixedDofs()
    free = [d for d in range(ndof) if d not in fixed]
    reduced = [[stiffness[a][b] for b in free] for a in free]
    reducedLoads = [loads[a] for a in free]
    freeDisp = solveLinear(reduced, reducedLoads)
    displacementVector = [0.0] * ndof
    for k, dof in enumerate(free):
      displacementVector[dof] = freeDisp[k]
    #  reactions: 'K u - F' is the support reaction at each fixed DOF.
    internal = matVec(stiffness, displacementVector)
    reactionVector = [internal[d] - loads[d] for d in range(ndof)]
    solution = TrussSolution()
    solution.displacements = [
        (displacementVector[2 * i], displacementVector[2 * i + 1])
        for i in range(count)]
    solution.reactions = [
        (reactionVector[2 * i] if 2 * i in fixed else 0.0,
         reactionVector[2 * i + 1] if 2 * i + 1 in fixed else 0.0)
        for i in range(count)]
    index = self._index()
    solution.forces = [
        bar.axialForce(solution.displacements[index[id(bar.nodeA)]],
                       solution.displacements[index[id(bar.nodeB)]])
        for bar in self.bars]
    return solution
