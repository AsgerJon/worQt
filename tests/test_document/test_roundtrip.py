"""
TestRoundtrip subclasses 'DocumentTest' and covers atomic JSON save/load:
values survive, references resolve in the second pass, and a resolved
reference shares identity with the array entry it points at.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .examples import FemSkeleton, sample
from . import DocumentTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestRoundtrip(DocumentTest):
  """Save/load round-trips of the FEM skeleton."""

  def test_node_values_survive(self) -> None:
    """Node x/y round-trip through save/load."""
    skeleton, a, b, element, constraint = sample()
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertEqual(loaded.nodes[0].x, 1.0)
    self.assertEqual(loaded.nodes[0].y, 2.0)
    self.assertEqual(loaded.nodes[1].x, 3.0)
    self.assertEqual(loaded.nodes[1].y, 4.0)

  def test_element_connectivity_resolves(self) -> None:
    """An element's node references resolve after load."""
    skeleton = sample()[0]
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertEqual(len(loaded.elements[0].nodes), 2)
    self.assertEqual(loaded.elements[0].nodes[0].x, 1.0)
    self.assertEqual(loaded.elements[0].nodes[1].x, 3.0)

  def test_reference_identity_preserved(self) -> None:
    """A loaded reference is the same object as the array entry it names."""
    skeleton = sample()[0]
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertIs(loaded.elements[0].nodes[0], loaded.nodes[0])
    self.assertIs(loaded.elements[0].nodes[1], loaded.nodes[1])

  def test_constraint_single_reference_resolves(self) -> None:
    """A single reference resolves to the right loaded node."""
    skeleton = sample()[0]
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertIs(loaded.constraints[0].node, loaded.nodes[0])

  def test_ids_preserved(self) -> None:
    """Member ids survive the round-trip."""
    skeleton, a, b, element, constraint = sample()
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertEqual(loaded.nodes[0].memberId, a.memberId)
    self.assertEqual(loaded.nodes[1].memberId, b.memberId)

  def test_empty_document(self) -> None:
    """An empty skeleton round-trips to an empty skeleton."""
    FemSkeleton().save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertEqual(len(loaded.nodes), 0)
    self.assertEqual(len(loaded.elements), 0)
    self.assertEqual(len(loaded.constraints), 0)
