"""
TestLayoutIndex subclasses 'LayoutTest' and tests the
'worQt.layouts.LayoutIndex' value type: its constructors, the derived
edges and corners, the cell expansion, write-once fields, containment and
the truth value.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import WriteOnceError

from worQt.layouts import LayoutIndex, LayoutCell

from . import LayoutTest


class TestLayoutIndex(LayoutTest):
  """Tests for the 'LayoutIndex' value type."""

  def test_full_constructor(self) -> None:
    """Four integers fix the row, column and the two spans."""
    index = LayoutIndex(2, 3, 4, 5)
    self.assertEqual(index.row, 2)
    self.assertEqual(index.col, 3)
    self.assertEqual(index.rowSpan, 4)
    self.assertEqual(index.colSpan, 5)

  def test_row_col_constructor(self) -> None:
    """Two integers fix the position and leave the spans at one."""
    index = LayoutIndex(2, 3)
    self.assertEqual(index.row, 2)
    self.assertEqual(index.col, 3)
    self.assertEqual(index.rowSpan, 1)
    self.assertEqual(index.colSpan, 1)

  def test_empty_constructor(self) -> None:
    """The no-argument form is a single cell at the origin."""
    index = LayoutIndex()
    self.assertEqual(index.row, 0)
    self.assertEqual(index.col, 0)
    self.assertEqual(index.rowSpan, 1)
    self.assertEqual(index.colSpan, 1)

  def test_cell_constructor(self) -> None:
    """A single cell fixes the position with unit spans."""
    index = LayoutIndex(LayoutCell(3, 4))
    self.assertEqual(index.row, 3)
    self.assertEqual(index.col, 4)
    self.assertEqual(index.rowSpan, 1)
    self.assertEqual(index.colSpan, 1)

  def test_corner_cells_constructor(self) -> None:
    """Two corner cells fix the position and the inclusive spans."""
    index = LayoutIndex(LayoutCell(1, 1), LayoutCell(3, 4))
    self.assertEqual(index.row, 1)
    self.assertEqual(index.col, 1)
    self.assertEqual(index.rowSpan, 3)
    self.assertEqual(index.colSpan, 4)

  def test_edges(self) -> None:
    """The edges derive from the position and the spans."""
    index = LayoutIndex(2, 3, 4, 5)
    self.assertEqual(index.top, 2)
    self.assertEqual(index.left, 3)
    self.assertEqual(index.bottom, 5)
    self.assertEqual(index.right, 7)

  def test_spans(self) -> None:
    """'spans' pairs the row and column spans."""
    self.assertEqual(LayoutIndex(2, 3, 4, 5).spans, (4, 5))

  def test_corners(self) -> None:
    """The four corner cells read off the edges."""
    index = LayoutIndex(2, 3, 4, 5)
    self.assertEqual(index.topLeft, LayoutCell(2, 3))
    self.assertEqual(index.topRight, LayoutCell(2, 7))
    self.assertEqual(index.bottomRight, LayoutCell(5, 7))
    self.assertEqual(index.bottomLeft, LayoutCell(5, 3))

  def test_cells(self) -> None:
    """A 2x2 block expands to its four cells."""
    cells = [*LayoutIndex(0, 0, 2, 2).cells]
    self.assertEqual(len(cells), 4)
    self.assertIn(LayoutCell(0, 0), cells)
    self.assertIn(LayoutCell(1, 1), cells)

  def test_iter(self) -> None:
    """Iteration yields row, column, row span and column span."""
    self.assertEqual((*LayoutIndex(2, 3, 4, 5),), (2, 3, 4, 5))

  def test_abs_is_area(self) -> None:
    """'abs' is the number of cells the block spans."""
    self.assertEqual(abs(LayoutIndex(2, 3, 4, 5)), 20)

  def test_bool(self) -> None:
    """A spanning block is truthy; a zero-span block is falsy."""
    self.assertTrue(LayoutIndex(0, 0, 1, 1))
    self.assertFalse(LayoutIndex(0, 0, 1, 0))

  def test_contains_cell(self) -> None:
    """A cell inside the block is contained; one outside is not."""
    index = LayoutIndex(0, 0, 2, 2)
    self.assertIn(LayoutCell(1, 1), index)
    self.assertNotIn(LayoutCell(5, 5), index)

  def test_contains_index(self) -> None:
    """A sub-block whose cells all lie inside is contained."""
    outer = LayoutIndex(0, 0, 3, 3)
    inner = LayoutIndex(0, 0, 2, 2)
    self.assertIn(inner, outer)
    self.assertNotIn(outer, inner)

  def test_write_once(self) -> None:
    """A second assignment to any field raises 'WriteOnceError'."""
    index = LayoutIndex(2, 3, 4, 5)
    with self.assertRaises(WriteOnceError):
      index.rowSpan = 9
    with self.assertRaises(WriteOnceError):
      index.row = 9
    with self.assertRaises(WriteOnceError):
      index.col = 9
    with self.assertRaises(WriteOnceError):
      index.colSpan = 9

  def test_setter_type_check(self) -> None:
    """A non-integer field value is refused on a fresh index."""
    with self.assertRaises(TypeException):
      LayoutIndex().row = 'nope'
    with self.assertRaises(TypeException):
      LayoutIndex().colSpan = 'nope'

  def test_bad_slot_value_raises(self) -> None:
    """A corrupt field slot is reported on read."""
    index = LayoutIndex(2, 3)
    index.__row_value__ = 'bad'
    with self.assertRaises(TypeException):
      _ = index.row

  def test_str_repr_empty(self) -> None:
    """A zero-span index prints as empty."""
    index = LayoutIndex(0, 0, 1, 0)
    self.assertEqual(str(index), '<LayoutIndex: Empty>')
    self.assertEqual(repr(index), 'LayoutIndex()')

  def test_str_repr_single(self) -> None:
    """A unit index prints as a single cell."""
    index = LayoutIndex(2, 3)
    self.assertEqual(str(index), '<LayoutIndex: (2, 3)>')
    self.assertEqual(repr(index), 'LayoutIndex(2, 3)')

  def test_str_repr_block(self) -> None:
    """A spanning index prints its row and column ranges."""
    index = LayoutIndex(2, 3, 4, 5)
    self.assertEqual(str(index),
                     '<LayoutIndex: rows: (2, 5), columns: (3, 7)>')
    self.assertEqual(repr(index), 'LayoutIndex(2, 3, 4, 5)')
