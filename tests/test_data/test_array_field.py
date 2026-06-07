"""
TestArrayField subclasses 'DataTest' and provides tests for the
'worQt.data.ArrayField' / 'ArrayLike' system.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException, SubclassException

from worQt.data import AbstractDocument, AbstractItem, ArrayField, ArrayLike
from . import DataTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Item(AbstractItem):
  """A bare array element; instances are distinguished by identity."""


class ArrayDoc(AbstractDocument):
  """A document with a single 'ArrayField' of 'Item' elements."""

  items = ArrayField[Item]()


class TestArrayField(DataTest):
  """
  TestArrayField subclasses 'DataTest' and provides tests for the
  'worQt.data.ArrayField' / 'ArrayLike' system.
  """

  @classmethod
  def _field(cls) -> ArrayField:
    """The registered 'items' field descriptor."""
    return ArrayDoc.__array_fields__['items']

  def test_default_is_empty_arraylike(self) -> None:
    """An untouched field reads as an empty 'ArrayLike'."""
    document = ArrayDoc()
    self.assertIsInstance(document.items, ArrayLike)
    self.assertEqual(len(document.items), 0)

  def test_value_knows_its_field(self) -> None:
    """The 'ArrayLike' carries a reference back to its owning field."""
    document = ArrayDoc()
    self.assertIs(document.items.owningField, self._field())

  def test_field_append(self) -> None:
    """'field.append(doc, item)' stores the item on the document."""
    document = ArrayDoc()
    item = Item()
    self._field().append(document, item)
    self.assertEqual(len(document.items), 1)
    self.assertIs(document.items[0], item)

  def test_field_extend_preserves_order(self) -> None:
    """'field.extend(doc, items)' appends in order; 'append' follows."""
    document = ArrayDoc()
    first, second, third = Item(), Item(), Item()
    self._field().extend(document, [first, second])
    self._field().append(document, third)
    self.assertEqual(list(document.items), [first, second, third])

  def test_value_is_iterable_and_indexable(self) -> None:
    """The 'ArrayLike' behaves as a sequence of its items."""
    document = ArrayDoc()
    first, second = Item(), Item()
    self._field().extend(document, [first, second])
    self.assertIs(document.items[0], first)
    self.assertEqual([x for x in document.items], [first, second])

  def test_assignment_is_blocked(self) -> None:
    """The whole array cannot be replaced by assignment; mutate instead."""
    document = ArrayDoc()
    with self.assertRaises(TypeError):
      document.items = [Item()]

  def test_requires_abstract_item(self) -> None:
    """'ArrayField' of a non-'AbstractItem' type is rejected."""
    with self.assertRaises(SubclassException):
      _ = ArrayField[int]

  def test_extend_rejects_wrong_element_type(self) -> None:
    """An element of the wrong type raises 'TypeException'."""
    document = ArrayDoc()
    with self.assertRaises(TypeException):
      self._field().extend(document, ['not an item'])

  def test_per_document_independence(self) -> None:
    """Each document owns its own array."""
    first = ArrayDoc()
    second = ArrayDoc()
    self._field().append(first, Item())
    self.assertEqual(len(first.items), 1)
    self.assertEqual(len(second.items), 0)

  def test_ergonomic_append_writes_through(self) -> None:
    """'doc.items.append(x)' writes through to the document."""
    document = ArrayDoc()
    item = Item()
    document.items.append(item)
    self.assertEqual(len(document.items), 1)
    self.assertIs(document.items[0], item)

  def test_ergonomic_extend_writes_through(self) -> None:
    """'doc.items.extend(xs)' writes through to the document."""
    document = ArrayDoc()
    first, second = Item(), Item()
    document.items.extend([first, second])
    self.assertEqual(list(document.items), [first, second])
