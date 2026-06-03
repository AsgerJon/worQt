"""
The pure structural elements of the FEA model (no Qt): 'Material' (a Young's
modulus), 'Section' (a cross-sectional area), 'Node' (a 2D point that may be
supported and loaded) and 'Bar' (a pin-jointed truss member carrying axial
force only). Units are millimetres, newtons and megapascals, so 'E' in MPa
times 'A' in mm^2 over 'L' in mm yields a force in N. Each is a 'worktoy'
'BaseObject', so the model builds and solves without a 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  pass


class Material(BaseObject):
  """A linear-elastic material, defined by Young's modulus 'E' (MPa)."""

  modulus = AttriBox[float](210000.0)  # steel, ~210 GPa as N/mm^2

  @overload(float)
  def __init__(self, modulus: float) -> None:
    self.modulus = modulus

  @overload()
  def __init__(self, ) -> None:
    pass

  def __str__(self, ) -> str:
    return 'Material(E=%g MPa)' % (self.modulus,)

  __repr__ = __str__


class Section(BaseObject):
  """A cross-section, defined by its area 'A' (mm^2)."""

  area = AttriBox[float](100.0)

  @overload(float)
  def __init__(self, area: float) -> None:
    self.area = area

  @overload()
  def __init__(self, ) -> None:
    pass

  def __str__(self, ) -> str:
    return 'Section(A=%g mm^2)' % (self.area,)

  __repr__ = __str__


class Node(BaseObject):
  """
  A 2D structural node at '(x, y)' mm. 'fixX'/'fixY' constrain its two
  translational degrees of freedom (a support); 'loadX'/'loadY' are the
  applied nodal force components in N.
  """

  x = AttriBox[float](0.0)
  y = AttriBox[float](0.0)
  fixX = AttriBox[bool](False)
  fixY = AttriBox[bool](False)
  loadX = AttriBox[float](0.0)
  loadY = AttriBox[float](0.0)

  @overload(float, float)
  def __init__(self, x: float, y: float) -> None:
    self.x = x
    self.y = y

  @overload()
  def __init__(self, ) -> None:
    pass

  def pin(self, ) -> Node:
    """Fully fix both translations (a pinned support); returns self."""
    self.fixX = True
    self.fixY = True
    return self

  def roller(self, horizontal: bool = True) -> Node:
    """
    Fix one translation. 'horizontal' True fixes the vertical DOF (the node
    rests on a horizontal surface, free to slide along it), else fixes the
    horizontal DOF. Returns self.
    """
    self.fixX = True if not horizontal else False
    self.fixY = True if horizontal else False
    return self

  def addLoad(self, fx: float, fy: float) -> Node:
    """Add a nodal force '(fx, fy)' in N; returns self."""
    self.loadX += fx
    self.loadY += fy
    return self

  def __str__(self, ) -> str:
    return 'Node(%g, %g)' % (self.x, self.y)

  __repr__ = __str__


class Bar(BaseObject):
  """
  A pin-jointed truss member between two nodes, carrying axial force only.
  Its axial stiffness is 'E * A / L'; tension is reported positive.
  """

  nodeA = AttriBox[Node]()
  nodeB = AttriBox[Node]()
  material = AttriBox[Material]()
  section = AttriBox[Section]()

  @overload(Node, Node, Material, Section)
  def __init__(self, a: Node, b: Node, material: Material,
               section: Section) -> None:
    self.nodeA = a
    self.nodeB = b
    self.material = material
    self.section = section

  @overload(Node, Node)
  def __init__(self, a: Node, b: Node) -> None:
    self.nodeA = a
    self.nodeB = b

  def length(self, ) -> float:
    """The member length 'L' (mm)."""
    return math.hypot(self.nodeB.x - self.nodeA.x,
                      self.nodeB.y - self.nodeA.y)

  def cosines(self, ) -> tuple:
    """The direction cosines '(c, s)' from node A to node B."""
    length = self.length()
    return ((self.nodeB.x - self.nodeA.x) / length,
            (self.nodeB.y - self.nodeA.y) / length)

  def axialStiffness(self, ) -> float:
    """The axial stiffness 'E * A / L' (N/mm)."""
    return self.material.modulus * self.section.area / self.length()

  def globalStiffness(self, ) -> list:
    """The 4x4 global stiffness matrix for DOFs '(uA, vA, uB, vB)'."""
    c, s = self.cosines()
    stiffness = self.axialStiffness()
    cc, ss, cs = c * c, s * s, c * s
    base = [
      [cc, cs, -cc, -cs],
      [cs, ss, -cs, -ss],
      [-cc, -cs, cc, cs],
      [-cs, -ss, cs, ss],
    ]
    return [[stiffness * value for value in row] for row in base]

  def axialForce(self, dispA: tuple, dispB: tuple) -> float:
    """
    The axial force (N, tension positive) from the end displacements
    'dispA' = (uA, vA) and 'dispB' = (uB, vB).
    """
    c, s = self.cosines()
    stiffness = self.axialStiffness()
    return stiffness * ((dispB[0] - dispA[0]) * c
                        + (dispB[1] - dispA[1]) * s)

  def __str__(self, ) -> str:
    return 'Bar(%s -> %s)' % (self.nodeA, self.nodeB)

  __repr__ = __str__
