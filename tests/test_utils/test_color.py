"""
TestColor subclasses 'UtilsTest' and tests the 'worQt.utils.Color' value
type: its overloaded constructors, channel access by key/index, iteration,
the hex string form, and the 'Q' conversion.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QPen

from worQt.utils import Color
from worQt.utils.qee_num import ColorNum
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import WriteOnceError

from . import UtilsTest


class TestColor(UtilsTest):
  """Tests for the 'Color' value type."""

  def test_rgba_constructor(self) -> None:
    """Four integers fix red, green, blue and alpha."""
    color = Color(10, 20, 30, 40)
    self.assertEqual((*color,), (10, 20, 30, 40))

  def test_rgb_constructor(self) -> None:
    """Three integers fix the channels and leave alpha opaque."""
    color = Color(10, 20, 30)
    self.assertEqual((*color,), (10, 20, 30, 255))

  def test_gray_constructor(self) -> None:
    """A single integer sets all three channels to that gray level."""
    color = Color(128)
    self.assertEqual((*color,), (128, 128, 128, 255))

  def test_qcolor_constructor(self) -> None:
    """A 'QColor' copies all four channels."""
    color = Color(QColor(10, 20, 30, 40))
    self.assertEqual((*color,), (10, 20, 30, 40))

  def test_keenum_constructor(self) -> None:
    """A 'ColorNum' member builds the 'Color' it carries."""
    color = Color(ColorNum.RED)
    self.assertEqual((*color,), (255, 0, 0, 255))

  def test_copy_constructor(self) -> None:
    """A 'Color' rebuilds an independent copy via 'THIS'."""
    original = Color(10, 20, 30, 40)
    copy = Color(original)
    self.assertEqual((*copy,), (10, 20, 30, 40))

  def test_default_is_opaque_white(self) -> None:
    """The default channels are opaque white."""
    color = Color()
    self.assertEqual((*color,), (255, 255, 255, 255))

  def test_getitem_by_key(self) -> None:
    """Channels resolve by their named and short keys."""
    color = Color(10, 20, 30, 40)
    self.assertEqual(color['red'], 10)
    self.assertEqual(color['g'], 20)
    self.assertEqual(color['blue'], 30)
    self.assertEqual(color['a'], 40)

  def test_getitem_by_index(self) -> None:
    """Channels resolve by integer index in r, g, b, a order."""
    color = Color(10, 20, 30, 40)
    self.assertEqual(color[0], 10)
    self.assertEqual(color[-1], 40)

  def test_len(self) -> None:
    """A 'Color' has four channels."""
    self.assertEqual(len(Color(10, 20, 30, 40)), 4)

  def test_str_opaque(self) -> None:
    """An opaque color renders as a six-digit hex string."""
    self.assertEqual(str(Color(255, 0, 0)), '#FF0000')

  def test_str_with_alpha(self) -> None:
    """A translucent color includes the alpha byte in the hex string."""
    self.assertEqual(str(Color(255, 0, 0, 128)), '#FF000080')

  def test_q_conversion(self) -> None:
    """The 'Q' field yields a matching 'QColor'."""
    qColor = Color(10, 20, 30, 40).Q
    self.assertIsInstance(qColor, QColor)
    self.assertEqual(qColor.red(), 10)
    self.assertEqual(qColor.alpha(), 40)

  def test_fill_brush(self) -> None:
    """'fillBrush' is a solid 'QBrush' carrying the colour."""
    brush = Color(255, 0, 0).fillBrush
    self.assertIsInstance(brush, QBrush)
    self.assertEqual(brush.style(), Qt.BrushStyle.SolidPattern)
    self.assertEqual(brush.color().red(), 255)

  def test_pens(self) -> None:
    """Each pen field is a 'QPen' of the colour with its own line style."""
    color = Color(255, 0, 0)
    self.assertEqual(color.solidPen.style(), Qt.PenStyle.SolidLine)
    self.assertEqual(color.dashedPen.style(), Qt.PenStyle.DashLine)
    self.assertEqual(color.dottedPen.style(), Qt.PenStyle.DotLine)
    self.assertEqual(color.dashDotPen.style(), Qt.PenStyle.DashDotLine)
    self.assertIsInstance(color.solidPen, QPen)
    self.assertEqual(color.solidPen.color().red(), 255)

  def test_getitem_slice(self) -> None:
    """A slice returns the matching tuple of channel values."""
    self.assertEqual(Color(10, 20, 30, 40)[0:2], (10, 20))

  def test_getitem_bad_key_raises(self) -> None:
    """An unknown channel key raises 'KeyError'."""
    with self.assertRaises(KeyError):
      _ = Color(10, 20, 30)['purple']

  def test_getitem_bad_type_raises(self) -> None:
    """An identifier that is neither key, index nor slice is refused."""
    with self.assertRaises(TypeException):
      _ = Color(10, 20, 30)[1.5]

  def test_getitem_index_out_of_range(self) -> None:
    """An out-of-range channel index raises 'IndexError'."""
    with self.assertRaises(IndexError):
      _ = Color(10, 20, 30)[99]

  def test_repr(self) -> None:
    """The repr reports the constructor form with all four channels."""
    self.assertEqual(repr(Color(10, 20, 30, 40)), 'Color(10, 20, 30, 40)')

  def test_kwargs_constructor(self) -> None:
    """The keyword form fixes channels by name."""
    color = Color(red=1, green=2, blue=3, alpha=4)
    self.assertEqual((*color,), (1, 2, 3, 4))

  def test_kwargs_set_unset_channel(self) -> None:
    """A keyword for a channel not set positionally is applied."""
    self.assertEqual((*Color(10, 20, 30, alpha=128),), (10, 20, 30, 128))

  def test_kwargs_override_rgba_refused(self) -> None:
    """Overriding an already-set channel is refused (write-once)."""
    with self.assertRaises(WriteOnceError):
      Color(10, 20, 30, 40, alpha=128)

  def test_kwargs_override_gray_refused(self) -> None:
    """A gray level sets all channels, so a keyword override is refused."""
    with self.assertRaises(WriteOnceError):
      Color(128, green=200)

  def test_kwargs_override_qcolor_refused(self) -> None:
    """A 'QColor' sets all channels, so a keyword override is refused."""
    with self.assertRaises(WriteOnceError):
      Color(QColor(1, 2, 3, 4), alpha=9)

  def test_kwargs_override_copy_refused(self) -> None:
    """A copy sets all channels, so a keyword override is refused."""
    with self.assertRaises(WriteOnceError):
      Color(Color(1, 2, 3, 4), alpha=9)

  def test_kwargs_bad_type(self) -> None:
    """A non-integer channel keyword is refused."""
    with self.assertRaises(TypeException):
      Color(red='nope')
