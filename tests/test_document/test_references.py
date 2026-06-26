"""
TestReferences subclasses 'DocumentTest' and covers the relational layer:
growing a reference list, removal unregistering a member, dangling
references (list entry dropped, single reference -> None) on reload, and the
guard against referencing a member that was never adopted.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .examples import Node, FemSkeleton, sample
from . import DocumentTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestReferences(DocumentTest):
  """The reference / relational layer."""

  def test_reference_list_grows(self) -> None:
    """Appending to a reference list extends the connectivity."""
    skeleton, a, b, element, constraint = sample()
    c = Node()
    skeleton.nodes.append(c)
    element.nodes.append(c)
    self.assertEqual(len(element.nodes), 3)
    self.assertIs(element.nodes[2], c)

  def test_remove_unregisters_member(self) -> None:
    """A removed member is gone from the document index."""
    skeleton, a, b, element, constraint = sample()
    removedId = b.memberId
    skeleton.nodes.remove(b)
    self.assertIsNone(skeleton.member(removedId))

  def test_dangling_list_reference_dropped_on_reload(self) -> None:
    """A node removed from the document drops out of an element's list on
    the next load."""
    skeleton, a, b, element, constraint = sample()
    skeleton.nodes.remove(b)
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    ids = [n.memberId for n in loaded.elements[0].nodes]
    self.assertEqual(ids, [a.memberId])

  def test_dangling_single_reference_becomes_none(self) -> None:
    """A single reference to a removed node resolves to None on reload."""
    skeleton, a, b, element, constraint = sample()
    skeleton.nodes.remove(a)
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertIsNone(loaded.constraints[0].node)

  def test_unadopted_reference_target_raises_on_save(self) -> None:
    """Referencing a member never added to the document raises on save."""
    skeleton, a, b, element, constraint = sample()
    orphan = Node()  # never appended to 'skeleton.nodes'
    element.nodes.append(orphan)
    with self.assertRaises(ValueError):
      skeleton.save(self.path())
