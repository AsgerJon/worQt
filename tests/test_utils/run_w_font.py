"""
RunWFont subclasses 'UtilsAppTest' and tests 'worQt.utils.WFont': building
it from positional arguments in any order, its typed fields reading from
and writing to the underlying 'QFont' (which stays the one source of
truth), the text colour and its pen, and the font metrics. Building a
'WFont' resolves its family against the installed fonts, which needs a
running 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontMetrics, QFontMetricsF, QPen
from worktoy.waitaminute import TypeException

from worQt.utils import WFont, Color
from worQt.utils.geom import Size
from worQt.utils.font_nums import FontFamily, GenericFamilyNum
from worQt.utils.font_nums import FontWeightNum, FontStyleNum, FontLineFlags
from worQt.utils.qee_num import ColorNum

from . import UtilsAppTest


class RunWFont(UtilsAppTest):
  """Tests for the 'WFont' value type."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  BUILDING   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_defaults(self) -> None:
    """A font built from nothing is sans, 20 points, normal, unlined and
    black."""
    font = WFont()
    self.assertEqual(font.familyName, GenericFamilyNum.SANS.family)
    self.assertEqual(font.fontSize, 20)
    self.assertIs(font.weightNum, FontWeightNum.NORMAL)
    self.assertIs(font.styleNum, FontStyleNum.NORMAL)
    self.assertFalse(font.underlineFlag)
    self.assertFalse(font.strikeoutFlag)
    self.assertFalse(font.overlineFlag)
    self.assertEqual((*font.color,), (0, 0, 0, 255))

  def run_any_order(self) -> None:
    """Every aspect is picked out by its type, whatever its position."""
    font = WFont(14, FontStyleNum.ITALIC, GenericFamilyNum.MONO,
                 Color(255, 0, 0), FontWeightNum.BOLD)
    self.assertEqual(font.fontSize, 14)
    self.assertIs(font.styleNum, FontStyleNum.ITALIC)
    self.assertEqual(font.familyName, GenericFamilyNum.MONO.family)
    self.assertEqual((*font.color,), (255, 0, 0, 255))
    self.assertIs(font.weightNum, FontWeightNum.BOLD)

  def run_written_through_to_qfont(self) -> None:
    """What the fields say is what the 'QFont' itself holds."""
    font = WFont(FontWeightNum.BOLD, FontStyleNum.OBLIQUE, 14)
    self.assertEqual(QFont.weight(font), QFont.Weight.Bold)
    self.assertEqual(QFont.style(font), QFont.Style.StyleOblique)
    self.assertEqual(QFont.pointSize(font), 14)

  def run_raw_qt_values(self) -> None:
    """Plain 'QFont.Weight' and 'QFont.Style' values are accepted too;
    a weight is an 'int' in PySide6 but is never taken for a size."""
    font = WFont(QFont.Weight.Black, QFont.Style.StyleItalic, 12)
    self.assertIs(font.weightNum, FontWeightNum.BLACK)
    self.assertIs(font.styleNum, FontStyleNum.ITALIC)
    self.assertEqual(font.fontSize, 12)

  def run_combined_line_flags(self) -> None:
    """A combination of line flags sets each line in it."""
    font = WFont(FontLineFlags.UNDERLINE | FontLineFlags.STRIKEOUT)
    self.assertTrue(font.underlineFlag)
    self.assertTrue(font.strikeoutFlag)
    self.assertFalse(font.overlineFlag)

  def run_family_by_name(self) -> None:
    """A family named by string is looked up however it is spelled."""
    family = FontFamily.installed()[0]
    font = WFont(str.replace(str.lower(family), ' ', '-'))
    self.assertEqual(FontFamily.normalize(font.familyName),
                     FontFamily.normalize(family))

  def run_unknown_family_refused(self) -> None:
    """A family that is not installed is refused, not substituted."""
    with self.assertRaises(LookupError):
      WFont('definitely not a real font zzz')

  def run_from_qfont_keeps_it(self) -> None:
    """Built from a 'QFont', a font starts as that font, not as the
    defaults, and further arguments still apply."""
    base = QFont()
    base.setPointSize(9)
    base.setUnderline(True)
    font = WFont(base, FontWeightNum.BOLD)
    self.assertEqual(font.fontSize, 9)
    self.assertTrue(font.underlineFlag)
    self.assertIs(font.weightNum, FontWeightNum.BOLD)

  def run_copy_of_wfont(self) -> None:
    """A 'WFont' built from another keeps its face, but its colour starts
    as the default unless given."""
    original = WFont(GenericFamilyNum.SERIF, 11, Color(0, 0, 255))
    copy = WFont(original, Color(0, 255, 0))
    self.assertEqual(copy.familyName, original.familyName)
    self.assertEqual(copy.fontSize, 11)
    self.assertEqual((*copy.color,), (0, 255, 0, 255))

  def run_two_of_a_kind_refused(self) -> None:
    """Two arguments for the same aspect are refused, not one silently
    winning."""
    with self.assertRaises(ValueError):
      WFont(12, 14)
    with self.assertRaises(ValueError):
      WFont(FontWeightNum.BOLD, QFont.Weight.Thin)

  def run_unknown_argument_refused(self) -> None:
    """An argument of no known kind is refused."""
    with self.assertRaises(TypeException):
      WFont(12.5)
    with self.assertRaises(TypeException):
      WFont(True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  FIELDS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_setters_write_through(self) -> None:
    """Setting a field changes the 'QFont'."""
    font = WFont()
    font.weightNum = FontWeightNum.LIGHT
    self.assertEqual(QFont.weight(font), QFont.Weight.Light)
    font.styleNum = 'italic'
    self.assertEqual(QFont.style(font), QFont.Style.StyleItalic)
    font.underlineFlag = True
    self.assertTrue(QFont.underline(font))
    font.strikeoutFlag = True
    self.assertTrue(QFont.strikeOut(font))
    font.overlineFlag = True
    self.assertTrue(QFont.overline(font))
    font.fontSize = 8
    self.assertEqual(QFont.pointSize(font), 8)

  def run_qfont_is_the_source_of_truth(self) -> None:
    """A change made through 'QFont' directly shows in the fields."""
    font = WFont()
    QFont.setWeight(font, QFont.Weight.Thin)
    QFont.setStyle(font, QFont.Style.StyleOblique)
    QFont.setPointSize(font, 33)
    QFont.setOverline(font, True)
    self.assertIs(font.weightNum, FontWeightNum.THIN)
    self.assertIs(font.styleNum, FontStyleNum.OBLIQUE)
    self.assertEqual(font.fontSize, 33)
    self.assertTrue(font.overlineFlag)

  def run_family_setter(self) -> None:
    """'familyName' takes a generic family or a name, nothing else."""
    font = WFont()
    font.familyName = GenericFamilyNum.MONO
    self.assertEqual(font.familyName, GenericFamilyNum.MONO.family)
    with self.assertRaises(TypeException):
      font.familyName = 42

  def run_font_size_must_be_a_positive_int(self) -> None:
    """A point size must be a positive 'int'."""
    font = WFont()
    with self.assertRaises(ValueError):
      font.fontSize = 0
    with self.assertRaises(TypeException):
      font.fontSize = 12.5
    with self.assertRaises(TypeException):
      font.fontSize = True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  COLOUR AND METRICS   # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_pen_follows_color(self) -> None:
    """The pen is solid, one pixel wide, and always in the text colour."""
    font = WFont()
    font.color = ColorNum.RED
    pen = font.pen
    self.assertIsInstance(pen, QPen)
    self.assertEqual(pen.width(), 1)
    self.assertEqual(pen.color().name(), '#ff0000')
    font.color = QColor(0, 0, 255)
    self.assertEqual(font.pen.color().name(), '#0000ff')

  def run_color_is_a_copy(self) -> None:
    """The font keeps its own copy of the colour it is given."""
    given = Color(1, 2, 3)
    font = WFont(given)
    self.assertEqual((*font.color,), (1, 2, 3, 255))
    self.assertIsNot(font.color, given)

  def run_color_guards(self) -> None:
    """A corrupt colour slot is reported, and the lazy default refuses to
    recurse on a failed build."""
    font = WFont()
    font.__text_color__ = None
    with self.assertRaises(RecursionError):
      font._getColor(_recursion=True)
    font.__text_color__ = 'red'
    with self.assertRaises(TypeException):
      _ = font.color

  def run_metrics(self) -> None:
    """The metric fields return the matching Qt metric objects."""
    font = WFont()
    self.assertIsInstance(font.metrics, QFontMetrics)
    self.assertIsInstance(font.metricsF, QFontMetricsF)

  def run_char_and_bounding_size(self) -> None:
    """The character and bounding sizes are positive 'Size's, and longer
    text is wider."""
    font = WFont()
    self.assertIsInstance(font.charSize, Size)
    self.assertGreater(font.charSize.height, 0)
    short, long = font.boundingWidth('wo'), font.boundingWidth('worQt!')
    self.assertIsInstance(short, Size)
    self.assertGreater(long.width, short.width)
    self.assertGreater(long.height, 0)
