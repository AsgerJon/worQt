"""
A FEM-skeleton example for the 'worQt.document' tests. It exercises every
field kind:

- 'Node'       - value attributes ('x', 'y').
- 'Element'    - a multi-reference ('ReferenceList[Node]') connecting nodes.
- 'Constraint' - a single reference ('Reference[Node]') pinning one node.
- 'FemSkeleton'- the document owning the three array fields.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.document import (Document,
                            Member,
                            ValueField,
                            ArrayField,
                            Reference,
                            ReferenceList)

if TYPE_CHECKING:  # pragma: no cover
  from typing import Tuple


class Node(Member):
  """A mesh node positioned in the plane."""

  x = ValueField[float](0.0)
  y = ValueField[float](0.0)


class Element(Member):
  """An element connecting a set of nodes (the connectivity)."""

  nodes = ReferenceList[Node]()


class Constraint(Member):
  """A boundary constraint pinning a single node."""

  node = Reference[Node]()


class FemSkeleton(Document):
  """A FEM skeleton: nodes, elements connecting them, and constraints
  pinning individual nodes."""

  nodes = ArrayField[Node]()
  elements = ArrayField[Element]()
  constraints = ArrayField[Constraint]()


def sample() -> tuple:
  """Build a small skeleton - two nodes, one element spanning both, one
  constraint pinning the first node - and return
  '(skeleton, a, b, element, constraint)'."""
  skeleton = FemSkeleton()
  a = Node()
  a.x, a.y = 1.0, 2.0
  b = Node()
  b.x, b.y = 3.0, 4.0
  skeleton.nodes.append(a)
  skeleton.nodes.append(b)
  element = Element()
  skeleton.elements.append(element)
  element.nodes.append(a)
  element.nodes.append(b)
  constraint = Constraint()
  skeleton.constraints.append(constraint)
  constraint.node = a
  return skeleton, a, b, element, constraint
