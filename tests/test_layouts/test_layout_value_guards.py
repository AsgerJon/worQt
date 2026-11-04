"""
TestLayoutValueGuards covers the guard and edge branches of the
'LayoutCell' and 'LayoutIndex' value types: the write-once setters, the
key/index resolution and its type guards, equality with non-cells,
'_resolveOther', and the 'LayoutIndex' containment, span setters and
empty/single rendering.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import WriteOnceError

from worQt.layouts import LayoutCell, LayoutIndex

from . import LayoutTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestLayoutValueGuards(LayoutTest):
  """Guard and edge branches of the layout value types."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LAYOUT CELL  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_cell_write_once(self) -> None:
    """A cell's row/col are write-once."""
    cell = LayoutCell(1, 2)
    with self.assertRaises(WriteOnceError):
      cell.row = 9
    with self.assertRaises(WriteOnceError):
      cell.col = 9

  def test_cell_getitem(self) -> None:
    """Index and key resolution, and their type guards."""
    cell = LayoutCell(1, 2)
    self.assertEqual(cell[0], 1)
    self.assertEqual(cell[1], 2)
    self.assertEqual(cell['row'], 1)
    self.assertEqual(cell['COL'], 2)  # case-insensitive
    with self.assertRaises(KeyError):
      _ = cell['nope']
    with self.assertRaises(TypeException):
      _ = cell[2.5]
    with self.assertRaises(TypeException):
      cell._resolveKey(123)
    with self.assertRaises(TypeException):
      cell._resolveIndex('x')

  def test_cell_equality(self) -> None:
    """A cell equals a coercible pair and rejects junk."""
    cell = LayoutCell(1, 2)
    self.assertFalse(cell == 'nope')
    self.assertIs(LayoutCell._resolveOther('nope'), NotImplemented)
    self.assertNotEqual(cell, LayoutCell(3, 4))

  def test_cell_lazy_defaults(self) -> None:
    """Reading row/col on a default cell populates the fallbacks."""
    cell = LayoutCell()
    self.assertEqual((cell.row, cell.col), (0, 0))

  def test_cell_kwargs_type_guard(self) -> None:
    """The keyword constructor rejects a wrong-typed value."""
    with self.assertRaises(TypeException):
      LayoutCell(row='x')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LAYOUT INDEX  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_index_lazy_defaults(self) -> None:
    """A default index reads its fallback row/col/spans."""
    index = LayoutIndex()
    self.assertEqual((index.row, index.col), (0, 0))
    self.assertEqual((index.rowSpan, index.colSpan), (1, 1))

  def test_index_span_setters_guard(self) -> None:
    """The span setters are write-once and type-checked."""
    with self.assertRaises(TypeException):
      LayoutIndex().rowSpan = 'x'
    with self.assertRaises(TypeException):
      LayoutIndex().colSpan = 'x'
    index = LayoutIndex()
    index.rowSpan = 2
    with self.assertRaises(WriteOnceError):
      index.rowSpan = 3

  def test_index_contains(self) -> None:
    """Containment accepts cells and sub-indices, rejects junk."""
    block = LayoutIndex(1, 2, 3, 4)
    self.assertIn(LayoutCell(1, 2), block)
    self.assertIn(LayoutIndex(1, 2), block)
    self.assertNotIn(LayoutCell(99, 99), block)
    self.assertNotIn('nope', block)

  def test_index_resolve_other(self) -> None:
    """'_resolveOther' yields 'NotImplemented' for junk."""
    self.assertIs(LayoutIndex._resolveOther('nope'), NotImplemented)

  def test_index_rendering(self) -> None:
    """Zero-span, single-cell and block indices render distinctly."""
    empty = LayoutIndex(0, 0, 0, 0)  # zero span -> falsy / 'Empty'
    self.assertFalse(empty)
    self.assertIn('Empty', str(empty))
    self.assertEqual(repr(empty), 'LayoutIndex()')
    self.assertIn('(1, 2)', str(LayoutIndex(1, 2)))
    self.assertEqual(repr(LayoutIndex(1, 2)), 'LayoutIndex(1, 2)')
    self.assertIn('rows', str(LayoutIndex(1, 2, 3, 4)))
    self.assertEqual(repr(LayoutIndex(1, 2, 3, 4)), 'LayoutIndex(1, 2, 3, 4)')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LAZY / RECURSION / TYPE GUARDS  # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_cell_getter_lazy_fallback(self) -> None:
    """Reading row/col with a cleared backing slot repopulates the
    fallback."""
    cell = LayoutCell(1, 2)
    cell.__row_value__ = None
    self.assertEqual(cell.row, 0)
    cell2 = LayoutCell(1, 2)
    cell2.__col_value__ = None
    self.assertEqual(cell2.col, 0)

  def test_cell_setter_type_guard(self) -> None:
    """The row/col setters reject a non-int once the slot is open."""
    cell = LayoutCell(1, 2)
    cell.__row_value__ = None
    with self.assertRaises(TypeException):
      cell.row = 'x'
    cell2 = LayoutCell(1, 2)
    cell2.__col_value__ = None
    with self.assertRaises(TypeException):
      cell2.col = 'x'

  def test_index_recursion_guards(self) -> None:
    """Each lazy index getter guards against a failed build."""
    for name in ('_getRow', '_getCol', '_getRowSpan', '_getColSpan'):
      with self.assertRaises(RecursionError):
        getattr(LayoutIndex(), name)(_recursion=True)

  def test_index_getter_type_guards(self) -> None:
    """Each index getter rejects a corrupt backing slot."""
    specs = (('__col_value__', 'col'),
             ('__rowSpan_value__', 'rowSpan'),
             ('__colSpan_value__', 'colSpan'))
    for slot, attr in specs:
      index = LayoutIndex()
      setattr(index, slot, 'bad')
      with self.assertRaises(TypeException):
        getattr(index, attr)

  def test_index_col_setter_type_guard(self) -> None:
    """The col setter rejects a non-int."""
    with self.assertRaises(TypeException):
      LayoutIndex().col = 'x'

  def test_index_resolve_other_coerces(self) -> None:
    """'_resolveOther' returns an index unchanged and coerces a cell."""
    index = LayoutIndex(1, 2)
    self.assertIs(LayoutIndex._resolveOther(index), index)
    self.assertIsInstance(LayoutIndex._resolveOther(LayoutCell(1, 2)),
                          LayoutIndex)
