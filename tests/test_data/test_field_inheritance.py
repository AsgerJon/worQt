"""
TestFieldInheritance subclasses 'DataTest' and covers 'AbstractField's
clone-on-subclass behaviour: a field declared on a base document is cloned
and re-registered the first time it is accessed through a subclass, so the
subclass gets its own field descriptor rather than sharing the base's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.data import AbstractDocument, SingleField
from . import DataTest

if TYPE_CHECKING:  # pragma: no cover
  pass


class BaseDoc(AbstractDocument):
  """A base document carrying one single field."""

  title = SingleField[str]('base title')


class SubDoc(BaseDoc):
  """A subclass that inherits the field without redeclaring it."""


class TestFieldInheritance(DataTest):
  """Covers the field clone-on-subclass path in 'AbstractField.__get__'."""

  def test_field_clones_for_subclass(self) -> None:
    """Reading the inherited field on a subclass clones and re-registers it,
    yielding a field descriptor distinct from the base's while preserving
    the value."""
    self.assertEqual(BaseDoc().title, 'base title')
    self.assertEqual(SubDoc().title, 'base title')  # triggers the clone
    self.assertIsNot(
        SubDoc.__single_fields__['title'],
        BaseDoc.__single_fields__['title'])
