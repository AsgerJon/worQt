"""
RunWFont subclasses 'UtilsAppTest' and tests 'worQt.utils.WFont': its
flexible positional constructor (picking out family/weight/style/lines/size
from any order), the property descriptors and their write-through to the
underlying 'QFont', the lazily built pen, and the font-metric fields. A
running 'QApplication' is required because 'QFontMetrics' queries the font
database.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont, QFontMetrics, QFontMetricsF, QPen

from worktoy.waitaminute import TypeException

from worQt.utils import WFont, Color
from worQt.utils.geom import Size
from worQt.utils.font_nums import FontWeightNum, FontStyleNum, FontLineFlags

from . import UtilsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunWFont(UtilsAppTest):
  """Tests for the 'WFont' value type."""

  def run_defaults(self) -> None:
    """A default font is normal weight/style, size 20, no line flags."""
    font = WFont()
    self.assertEqual(font.fontSize, 20)
    self.assertIs(font.weightNum, FontWeightNum.NORMAL)
    self.assertIs(font.styleNum, FontStyleNum.NORMAL)
    self.assertFalse(font.underlineFlag)
    self.assertFalse(font.strikeoutFlag)
    self.assertFalse(font.overlineFlag)
    self.assertEqual((*font.color,), (0, 0, 0, 255))

  def run_weight_and_size_constructor(self) -> None:
    """A weight and a size are picked out regardless of position."""
    font = WFont(FontWeightNum.BOLD, 14)
    self.assertIs(font.weightNum, FontWeightNum.BOLD)
    self.assertEqual(font.fontSize, 14)
    self.assertEqual(font.pointSize(), 14)
    self.assertEqual(font.weight(), FontWeightNum.BOLD.value)

  def run_style_constructor(self) -> None:
    """A style argument sets the style and writes through to 'QFont'."""
    font = WFont(FontStyleNum.ITALIC)
    self.assertIs(font.styleNum, FontStyleNum.ITALIC)
    self.assertEqual(font.style(), FontStyleNum.ITALIC.value)

  def run_line_flags_constructor(self) -> None:
    """A line flag sets exactly the corresponding 'QFont' line property."""
    font = WFont(FontLineFlags.UNDERLINE)
    self.assertTrue(font.underlineFlag)
    self.assertTrue(QFont.underline(font))
    self.assertFalse(font.strikeoutFlag)

  def run_copy_from_qfont(self) -> None:
    """A 'QFont' argument seeds the underlying font."""
    font = WFont(QFont())
    self.assertIsInstance(font, QFont)

  def run_set_font_size(self) -> None:
    """Setting 'fontSize' writes through to the point size."""
    font = WFont()
    font.fontSize = 12
    self.assertEqual(font.pointSize(), 12)

  def run_font_size_rejects_non_positive(self) -> None:
    """A non-positive font size is refused."""
    font = WFont()
    with self.assertRaises(ValueError):
      font.fontSize = 0

  def run_set_weight_style_flags(self) -> None:
    """Setting the enum/flag descriptors writes through to 'QFont'."""
    font = WFont()
    font.weightNum = FontWeightNum.BOLD
    self.assertEqual(font.weight(), FontWeightNum.BOLD.value)
    font.styleNum = FontStyleNum.OBLIQUE
    self.assertEqual(font.style(), FontStyleNum.OBLIQUE.value)
    font.underlineFlag = True
    self.assertTrue(QFont.underline(font))
    font.strikeoutFlag = True
    self.assertTrue(QFont.strikeOut(font))
    font.overlineFlag = True
    self.assertTrue(QFont.overline(font))

  def run_pen_built_from_color(self) -> None:
    """The pen is a solid, width-1 'QPen' carrying the font colour."""
    font = WFont()
    font.color = Color(255, 0, 0)
    pen = font.pen
    self.assertIsInstance(pen, QPen)
    self.assertEqual(pen.width(), 1)
    self.assertEqual(pen.color().red(), 255)

  def run_metrics(self) -> None:
    """The metric fields return the matching Qt metric objects."""
    font = WFont()
    self.assertIsInstance(font.metrics, QFontMetrics)
    self.assertIsInstance(font.metricsF, QFontMetricsF)

  def run_preset_skips_same_value(self) -> None:
    """Re-setting a property to its current value is skipped, not re-applied."""
    font = WFont()
    font.weightNum = FontWeightNum.BOLD
    font.weightNum = FontWeightNum.BOLD  # second set hits the skip branch
    self.assertIs(font.weightNum, FontWeightNum.BOLD)
    font.styleNum = FontStyleNum.ITALIC
    font.styleNum = FontStyleNum.ITALIC
    self.assertIs(font.styleNum, FontStyleNum.ITALIC)
    font.underlineFlag = True
    font.underlineFlag = True
    self.assertTrue(font.underlineFlag)
    font.fontSize = 12
    font.fontSize = 12
    self.assertEqual(font.fontSize, 12)

  def run_reimplementations_resync(self) -> None:
    """The 'QFont' accessors re-sync when the underlying value drifts."""
    font = WFont()
    QFont.setWeight(font, QFont.Weight.Thin)
    self.assertEqual(font.weight(), font.weightNum.value)
    QFont.setStyle(font, QFont.Style.StyleItalic)
    self.assertEqual(font.style(), font.styleNum.value)
    QFont.setPointSize(font, 99)
    self.assertEqual(font.pointSize(), font.fontSize)
    QFont.setFamily(font, 'NoSuchFamily')
    self.assertEqual(font.family(), font.familyNum.value)

  def run_reimplementations_recursion_guard(self) -> None:
    """When the underlying value still disagrees, the re-syncing accessors
    give up rather than recurse forever."""
    font = WFont()
    QFont.setFamily(font, 'ZzzNoSuchFamily')
    with self.assertRaises(RecursionError):
      font.family(_recursion=True)
    other = (QFont.Weight.Thin if font.weightNum.value != QFont.Weight.Thin
             else QFont.Weight.Black)
    QFont.setWeight(font, other)
    with self.assertRaises(RecursionError):
      font.weight(_recursion=True)
    otherStyle = (QFont.Style.StyleItalic
                  if font.styleNum.value != QFont.Style.StyleItalic
                  else QFont.Style.StyleOblique)
    QFont.setStyle(font, otherStyle)
    with self.assertRaises(RecursionError):
      font.style(_recursion=True)
    QFont.setPointSize(font, 999)
    with self.assertRaises(RecursionError):
      font.pointSize(_recursion=True)

  def run_pen_recursion_guard(self) -> None:
    """A direct recursive pen read with an empty cache raises."""
    font = WFont()
    font.__cached_pen__ = None
    with self.assertRaises(RecursionError):
      font._getPen(_recursion=True)

  def run_family_num_skips_same_value(self) -> None:
    """Re-setting 'familyNum' to its current value is skipped."""
    font = WFont()
    current = font.familyNum
    font.familyNum = current  # hits the SkipSet branch
    self.assertIs(font.familyNum, current)

  def run_getter_type_errors(self) -> None:
    """A corrupt cached pen or size slot is reported on read."""
    font = WFont()
    font.__cached_pen__ = 'bad'
    with self.assertRaises(TypeException):
      _ = font.pen
    font.__font_size__ = 'bad'
    with self.assertRaises(TypeException):
      _ = font.fontSize

  def run_fontsize_must_be_int(self) -> None:
    """A non-integer font size is refused by the setter."""
    font = WFont()
    with self.assertRaises(TypeException):
      font.fontSize = 12.5

  def run_char_and_bounding_size(self) -> None:
    """The character and bounding sizes are positive-height 'Size's."""
    font = WFont()
    self.assertIsInstance(font.charSize, Size)
    self.assertGreater(font.charSize.height, 0)
    bounds = font.boundingWidth('worQt')
    self.assertIsInstance(bounds, Size)
    self.assertGreater(bounds.height, 0)
