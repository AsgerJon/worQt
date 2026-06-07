"""
TestMultiField subclasses 'DataTest' and provides tests for the
'worQt.data.MultiField' class and its observable 'MultiFieldList'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException
from worktoy.waitaminute import SubclassException

from worQt.data import MultiField, MultiFieldList
from test_data.examples import SampleDocument, SamplePoint
from test_data import DataTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestMultiField(DataTest):
  """
  TestMultiField subclasses 'DataTest' and provides tests for the
  'worQt.data.MultiField' class and its observable 'MultiFieldList'.
  """

  def test_default_is_empty_list(self) -> None:
    """A never-set 'MultiField' resolves to a fresh empty list."""
    document = SampleDocument()
    self.assertEqual([*document.pointsField], [])
    self.assertIsInstance(document.pointsField, MultiFieldList)

  def test_default_is_per_instance(self) -> None:
    """Each document gets its own list, not a shared mutable default."""
    first = SampleDocument()
    second = SampleDocument()
    first.pointsField.append(SamplePoint(1))
    self.assertEqual(len(first.pointsField), 1)
    self.assertEqual(len(second.pointsField), 0)

  def test_round_trip(self) -> None:
    """A list of items survives a save/load round-trip through disk."""
    document = SampleDocument()
    document.pointsField = [SamplePoint(1), SamplePoint(2), SamplePoint(3)]
    document.save()
    other = SampleDocument()
    self.assertEqual(len(other.pointsField), 0)
    other.load()
    self.assertEqual([p.value for p in other.pointsField], [1, 2, 3])

  def test_rejects_non_list(self) -> None:
    """Assigning a non-list value raises 'TypeException'."""
    document = SampleDocument()
    with self.assertRaises(TypeException):
      document.pointsField = SamplePoint(1)

  def test_rejects_wrong_element_type(self) -> None:
    """An element of the wrong type raises 'TypeException'."""
    document = SampleDocument()
    with self.assertRaises(TypeException):
      document.pointsField = [SamplePoint(1), 'nope']

  def test_append_rejects_wrong_element_type(self) -> None:
    """The list mutator type-checks too, not just assignment."""
    document = SampleDocument()
    with self.assertRaises(TypeException):
      document.pointsField.append('nope')

  def test_structural_change_signals(self) -> None:
    """Structural mutation fires the field's change hook."""
    document = SampleDocument()
    signals = []
    field = type(document).__single_fields__['pointsField']
    field._notifyChange = lambda instance, **k: signals.append(instance)
    document.pointsField.append(SamplePoint(1))
    document.pointsField.extend([SamplePoint(2)])
    self.assertEqual(len(signals), 2)

  def test_deep_change_signals(self) -> None:
    """Mutating a contained item's own state bubbles to the field."""
    document = SampleDocument()
    signals = []
    field = type(document).__single_fields__['pointsField']
    field._notifyChange = lambda instance, **k: signals.append(instance)
    point = SamplePoint(1)
    document.pointsField.append(point)
    signals.clear()
    point.value = 99
    self.assertEqual(len(signals), 1)

  def test_removed_item_is_disconnected(self) -> None:
    """A removed item no longer bubbles its changes."""
    document = SampleDocument()
    signals = []
    field = type(document).__single_fields__['pointsField']
    field._notifyChange = lambda instance, **k: signals.append(instance)
    point = SamplePoint(1)
    document.pointsField.append(point)
    document.pointsField.remove(point)
    signals.clear()
    point.value = 7
    self.assertEqual(len(signals), 0)

  def test_requires_abstract_item(self) -> None:
    """'MultiField' of a non-'AbstractItem' type is rejected."""
    with self.assertRaises(SubclassException):
      _ = MultiField[int]
