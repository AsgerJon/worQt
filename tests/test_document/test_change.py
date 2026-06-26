"""
TestChange subclasses 'DocumentTest' and covers the change channel: dirty
tracking, the revision counter, subscriber notifications, and the
pristine-on-load / pristine-on-new baseline.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .examples import FemSkeleton, sample
from . import DocumentTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestChange(DocumentTest):
  """The document change channel."""

  def test_fresh_document_clean(self) -> None:
    """A brand-new document is clean at revision 0."""
    skeleton = FemSkeleton()
    self.assertFalse(skeleton.isDirty())
    self.assertEqual(skeleton.revision(), 0)

  def test_editing_node_dirties(self) -> None:
    """Editing an adopted node's attribute dirties the document."""
    skeleton, a, b, element, constraint = sample()
    skeleton.clean()
    self.assertFalse(skeleton.isDirty())
    a.x = 99.0
    self.assertTrue(skeleton.isDirty())

  def test_save_clears_dirty(self) -> None:
    """Saving clears the dirty flag."""
    skeleton = sample()[0]
    self.assertTrue(skeleton.isDirty())
    skeleton.save(self.path())
    self.assertFalse(skeleton.isDirty())

  def test_load_is_pristine(self) -> None:
    """A loaded document reads like a fresh one: clean, revision 0."""
    skeleton = sample()[0]
    skeleton.save(self.path())
    loaded = FemSkeleton.load(self.path())
    self.assertFalse(loaded.isDirty())
    self.assertEqual(loaded.revision(), 0)

  def test_subscribe_receives_changes(self) -> None:
    """A subscriber is notified once per change, with the field name."""
    skeleton, a, b, element, constraint = sample()
    seen = []
    skeleton.subscribe(lambda change: seen.append(change))
    a.x = 7.0
    self.assertEqual(len(seen), 1)
    self.assertEqual(seen[0].name, 'x')

  def test_markPristine_resets_revision(self) -> None:
    """'markPristine' clears dirty and zeroes the revision counter."""
    skeleton = sample()[0]
    self.assertGreater(skeleton.revision(), 0)
    skeleton.markPristine()
    self.assertFalse(skeleton.isDirty())
    self.assertEqual(skeleton.revision(), 0)
