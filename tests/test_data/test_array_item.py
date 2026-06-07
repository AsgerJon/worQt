"""
TestArrayItem subclasses 'DataTest' and covers the 'AbstractItem' /
'NotifyBox' machinery: the metaclass enforcement (only 'NotifyBox' state on
an item), the no-default-items guard on 'ArrayField', the in-place change
notification chain (item -> field), and the array save/load round-trip.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox

from worQt.data import AbstractItem, NotifyBox, ArrayField, AbstractDocument
from . import DataTest
from .examples import SampleFile

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Point(AbstractItem):
  """A 2D point item whose coordinates notify on every write."""

  x = NotifyBox[float](0.0)
  y = NotifyBox[float](0.0)


class SpyArrayField(ArrayField):
  """An 'ArrayField' that records each 'notifyChange', so a test can see the
  item -> field change chain fire."""

  calls = []  # documents notified; class-level, cleared per test

  def notifyChange(self, doc: Any) -> None:
    type(self).calls.append(doc)


class SpyDoc(AbstractDocument):
  """Document whose array field records change notifications."""

  points = SpyArrayField[Point]()


class PointDoc(AbstractDocument):
  """Document persisting an array of points, for the save/load round-trip."""

  mainFile = AttriBox[SampleFile]('points.tmp')
  points = ArrayField[Point]()

  @points.setEncoder
  def _encodePoint(self, point: Point) -> dict:
    return {'x': point.x, 'y': point.y}

  @points.setDecoder
  def _decodePoint(self, raw: dict) -> Point:
    point = Point()
    point.x = float(raw['x'])
    point.y = float(raw['y'])
    return point


class TestArrayItem(DataTest):
  """Covers item enforcement, the notify chain and array persistence."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ENFORCEMENT (metaclass)   # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_attribox_field_rejected(self) -> None:
    """A plain 'AttriBox' on an item raises at class creation."""
    with self.assertRaises(TypeError):
      class BadItem(AbstractItem):
        x = AttriBox[float](0.0)

  def test_notifybox_field_allowed(self) -> None:
    """A 'NotifyBox' on an item is accepted."""

    class GoodItem(AbstractItem):
      x = NotifyBox[float](0.0)

    self.assertIsInstance(GoodItem(), AbstractItem)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NO DEFAULT ITEMS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_array_field_rejects_default_items(self) -> None:
    """'ArrayField[T](item)' raises: arrays start empty."""
    with self.assertRaises(TypeError):
      _ = ArrayField[Point](Point())

  def test_array_field_empty_call_ok(self) -> None:
    """'ArrayField[T]()' declares the field with no default items."""
    self.assertIsInstance(ArrayField[Point](), ArrayField)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFY CHAIN   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_in_place_edit_notifies_owning_field(self) -> None:
    """Editing an item already held by an array fires the field's hook."""
    SpyArrayField.calls.clear()
    document = SpyDoc()
    point = Point()
    document.points.append(point)  # adopts the point
    SpyArrayField.calls.clear()  # drop the append's own notification
    point.x = 9.0  # the in-place edit under test
    self.assertTrue(SpyArrayField.calls)
    self.assertIs(SpyArrayField.calls[-1], document)

  def test_unowned_item_edit_is_silent(self) -> None:
    """Editing an item not yet in any array is a no-op, never a crash."""
    SpyArrayField.calls.clear()
    point = Point()  # never added to an array: no owner
    point.x = 5.0
    self.assertEqual(SpyArrayField.calls, [])
    self.assertEqual(point.x, 5.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SAVE / LOAD   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_array_round_trips_through_save_load(self) -> None:
    """An array of items survives a save/load round-trip via the per-item
    encoder/decoder."""
    document = PointDoc()
    first, second = Point(), Point()
    first.x, first.y = 1.0, 2.0
    second.x, second.y = 3.0, 4.0
    document.points.append(first)
    document.points.append(second)
    document.save()

    other = PointDoc()
    other.load()
    coords = [(point.x, point.y) for point in other.points]
    self.assertEqual(coords, [(1.0, 2.0), (3.0, 4.0)])
