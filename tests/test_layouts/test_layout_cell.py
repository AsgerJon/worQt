"""
TestLayoutCell subclasses 'LayoutTest' and tests the
'worQt.layouts.LayoutCell' value type: its constructors, write-once
fields, index/key access, iteration, equality and hashing.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import WriteOnceError

from worQt.layouts import LayoutCell

from . import LayoutTest


class TestLayoutCell(LayoutTest):
  """Tests for the 'LayoutCell' value type."""

  def test_int_constructor(self) -> None:
    """Two integers fix the row and column."""
    cell = LayoutCell(7, 9)
    self.assertEqual(cell.row, 7)
    self.assertEqual(cell.col, 9)

  def test_empty_constructor(self) -> None:
    """The no-argument form defaults to the origin cell."""
    cell = LayoutCell()
    self.assertEqual(cell.row, 0)
    self.assertEqual(cell.col, 0)

  def test_write_once_row(self) -> None:
    """A second assignment to 'row' raises 'WriteOnceError'."""
    cell = LayoutCell(1, 2)
    with self.assertRaises(WriteOnceError):
      cell.row = 5

  def test_write_once_col(self) -> None:
    """A second assignment to 'col' raises 'WriteOnceError'."""
    cell = LayoutCell(1, 2)
    with self.assertRaises(WriteOnceError):
      cell.col = 5

  def test_getitem_by_index(self) -> None:
    """Even indices read the row, odd indices read the column."""
    cell = LayoutCell(7, 9)
    self.assertEqual(cell[0], 7)
    self.assertEqual(cell[1], 9)
    self.assertEqual(cell[2], 7)

  def test_getitem_by_key(self) -> None:
    """Row and column resolve by their several aliases."""
    cell = LayoutCell(7, 9)
    self.assertEqual(cell['row'], 7)
    self.assertEqual(cell['r'], 7)
    self.assertEqual(cell['y'], 7)
    self.assertEqual(cell['col'], 9)
    self.assertEqual(cell['c'], 9)
    self.assertEqual(cell['x'], 9)

  def test_iter(self) -> None:
    """Iteration yields the row then the column."""
    self.assertEqual((*LayoutCell(7, 9),), (7, 9))

  def test_len(self) -> None:
    """A cell has two coordinates."""
    self.assertEqual(len(LayoutCell(7, 9)), 2)

  def test_equality(self) -> None:
    """Two cells are equal when both coordinates match."""
    self.assertEqual(LayoutCell(1, 2), LayoutCell(1, 2))
    self.assertNotEqual(LayoutCell(1, 2), LayoutCell(3, 4))

  def test_hash(self) -> None:
    """A cell hashes by its coordinate pair, so it works as a dict key."""
    self.assertEqual(hash(LayoutCell(1, 2)), hash((1, 2)))
    store = {LayoutCell(1, 2): 'here'}
    self.assertEqual(store[LayoutCell(1, 2)], 'here')

  def test_repr(self) -> None:
    """The repr round-trips to the constructor form."""
    self.assertEqual(repr(LayoutCell(7, 9)), 'LayoutCell(7, 9)')

  def test_str(self) -> None:
    """The string form reports the row and column."""
    self.assertEqual(str(LayoutCell(7, 9)), '<LayoutCell: row=7, col=9>')

  def test_kwargs_constructor(self) -> None:
    """The keyword form fixes row and column by alias."""
    cell = LayoutCell(row=5, col=7)
    self.assertEqual(cell.row, 5)
    self.assertEqual(cell.col, 7)

  def test_kwargs_after_positional_write_once(self) -> None:
    """A keyword that re-sets an already-positional field is refused."""
    with self.assertRaises(WriteOnceError):
      LayoutCell(1, 2, c=9)

  def test_kwargs_bad_type(self) -> None:
    """A non-integer keyword value is refused."""
    with self.assertRaises(TypeException):
      LayoutCell(row='nope')

  def test_getitem_key_aliases(self) -> None:
    """Long and upper-case aliases resolve too."""
    cell = LayoutCell(7, 9)
    self.assertEqual(cell['vertical'], 7)
    self.assertEqual(cell['horizontal'], 9)
    self.assertEqual(cell['Y'], 7)
    self.assertEqual(cell['X'], 9)

  def test_getitem_unknown_key(self) -> None:
    """An unknown key raises 'KeyError'."""
    with self.assertRaises(KeyError):
      _ = LayoutCell(7, 9)['nope']

  def test_getitem_bad_type(self) -> None:
    """A non-int, non-str identifier is refused."""
    with self.assertRaises(TypeException):
      _ = LayoutCell(7, 9)[1.5]

  def test_eq_non_cell_is_false(self) -> None:
    """Comparison with a non-coercible value is not equal."""
    self.assertNotEqual(LayoutCell(1, 2), object())
