"""
TestSize subclasses 'UtilsTest' and tests the 'worQt.utils.geom.Size'
value type: its overloaded constructors, the 'area' field, and the
'Q'/'QF' conversions.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QSize, QSizeF, QRect, QRectF

from worQt.utils.geom import Size

from . import UtilsTest


class TestSize(UtilsTest):
  """Tests for the 'Size' value type."""

  def test_int_constructor(self) -> None:
    """Two integers fix width and height directly."""
    size = Size(20, 10)
    self.assertEqual(size.width, 20)
    self.assertEqual(size.height, 10)

  def test_empty_constructor(self) -> None:
    """The no-argument form is the zero size."""
    size = Size()
    self.assertEqual(size.width, 0)
    self.assertEqual(size.height, 0)

  def test_float_constructor(self) -> None:
    """Two floats are rounded to integer dimensions."""
    size = Size(20.4, 10.6)
    self.assertEqual(size.width, 20)
    self.assertEqual(size.height, 11)

  def test_qsize_constructor(self) -> None:
    """A 'QSize' is accepted strictly."""
    size = Size(QSize(20, 10))
    self.assertEqual(size.width, 20)
    self.assertEqual(size.height, 10)

  def test_qsizef_constructor(self) -> None:
    """A 'QSizeF' is accepted strictly and rounded."""
    size = Size(QSizeF(20.6, 10.2))
    self.assertEqual(size.width, 21)
    self.assertEqual(size.height, 10)

  def test_qrect_constructor(self) -> None:
    """A 'QRect' contributes its size."""
    size = Size(QRect(5, 5, 20, 10))
    self.assertEqual(size.width, 20)
    self.assertEqual(size.height, 10)

  def test_qrectf_constructor(self) -> None:
    """A 'QRectF' contributes its size, rounded."""
    size = Size(QRectF(5.0, 5.0, 20.0, 10.0))
    self.assertEqual(size.width, 20)
    self.assertEqual(size.height, 10)

  def test_qf_conversion(self) -> None:
    """The 'QF' field yields a matching 'QSizeF'."""
    qSizeF = Size(20, 10).QF
    self.assertIsInstance(qSizeF, QSizeF)
    self.assertAlmostEqual(qSizeF.width(), 20.0)

  def test_copy_constructor(self) -> None:
    """A 'Size' rebuilds an independent copy via 'THIS'."""
    original = Size(20, 10)
    copy = Size(original)
    self.assertEqual(copy.width, 20)
    self.assertEqual(copy.height, 10)
    copy.width = 99
    self.assertEqual(original.width, 20)

  def test_area(self) -> None:
    """'area' is the product of width and height."""
    self.assertEqual(Size(20, 10).area, 200)

  def test_q_conversion(self) -> None:
    """The 'Q' field yields a matching 'QSize'."""
    qSize = Size(20, 10).Q
    self.assertIsInstance(qSize, QSize)
    self.assertEqual(qSize.width(), 20)
    self.assertEqual(qSize.height(), 10)

  def test_str(self) -> None:
    """The string form reports both dimensions."""
    self.assertEqual(str(Size(20, 10)), 'Size(20, 10)')
