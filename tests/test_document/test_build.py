"""
TestBuild subclasses 'DocumentTest' and covers in-memory construction of the
FEM skeleton: id assignment, attribute access, references by identity, type
checking and the read-only array guard.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import ReadOnlyError

from .examples import Node, FemSkeleton, sample
from . import DocumentTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestBuild(DocumentTest):
  """In-memory construction of the FEM skeleton."""

  def test_nodes_get_sequential_ids(self) -> None:
    """Adopting members assigns document-scoped ids 1, 2, 3..."""
    skeleton, a, b, element, constraint = sample()
    self.assertEqual(a.memberId, 1)
    self.assertEqual(b.memberId, 2)
    self.assertEqual(element.memberId, 3)
    self.assertEqual(constraint.memberId, 4)

  def test_node_attribute_defaults_and_set(self) -> None:
    """A fresh node reads its defaults; assignment sticks."""
    node = Node()
    self.assertEqual(node.x, 0.0)
    self.assertEqual(node.y, 0.0)
    node.x = 5.5
    self.assertEqual(node.x, 5.5)

  def test_element_references_nodes_by_identity(self) -> None:
    """An element's node list holds the very objects appended."""
    skeleton, a, b, element, constraint = sample()
    self.assertEqual(len(element.nodes), 2)
    self.assertIs(element.nodes[0], a)
    self.assertIs(element.nodes[1], b)

  def test_constraint_single_reference(self) -> None:
    """A constraint's single reference points at its node."""
    skeleton, a, b, element, constraint = sample()
    self.assertIs(constraint.node, a)

  def test_value_type_checking(self) -> None:
    """A non-float assigned to a float field raises 'TypeException'."""
    node = Node()
    with self.assertRaises(TypeException):
      node.x = 'not a number'

  def test_array_field_assignment_blocked(self) -> None:
    """Whole-array assignment is read-only; mutate the list instead."""
    skeleton = FemSkeleton()
    with self.assertRaises(ReadOnlyError):
      skeleton.nodes = [Node()]

  def test_member_lookup_by_id(self) -> None:
    """'document.member(id)' returns the adopted member."""
    skeleton, a, b, element, constraint = sample()
    self.assertIs(skeleton.member(a.memberId), a)
    self.assertIs(skeleton.member(b.memberId), b)

  def test_documents_are_independent(self) -> None:
    """Members adopted by one document do not appear in another."""
    first = sample()[0]
    second = FemSkeleton()
    self.assertEqual(len(first.nodes), 2)
    self.assertEqual(len(second.nodes), 0)
