"""
TestTeleprinter covers the cabin's teleprinter (user, 2026-11-16:
"Instead of a terminal ... let's have a teleprinter"; "It should use a
modern font like nerd monospace to be cheeky"): capitals cut to its
width, ten characters a second, its bell before what matters, the
carriage returning between lines, the paper keeping its last lines;
77 to a line (user, 2026-11-17: "Smaller font on the teleprint. also
make it wider. It should fit 77 characters").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._cockpit import PAPER_AT, PAPER_HIGH, PAPER_WIDE
from worQt.gaming.space._cockpit import SECTIONS
from worQt.gaming.space._dashboard import paperLayout
from worQt.gaming.space._teleprinter import ICONS, KEPT, LINE, PITCH
from worQt.gaming.space._teleprinter import RATE, RETURN, WIDTH
from worQt.gaming.space._teleprinter import Teleprinter

from . import SpaceTest


class TestTeleprinter(SpaceTest):
  """Tests for 'Teleprinter'."""

  def test_types(self) -> None:
    """A line types at 'RATE' characters a second, in capitals; the
    paper shows the part typed and the carriage's column; done, the line
    is printed and the carriage returns."""
    printer = Teleprinter()
    self.assertFalse(printer.busy)
    printer.said('lift-off')
    self.assertTrue(printer.busy)
    printer.acted(4.0 / RATE)
    printed, part, column = printer.paper()
    self.assertEqual((printed, part, column), ([], 'LIFT', 4))
    self.assertEqual(printer.typed, 4)
    printer.acted(4.0 / RATE)
    self.assertEqual(printer.paper(), (['LIFT-OFF'], '', 0))
    self.assertEqual((printer.typed, printer.returns), (8, 1))
    self.assertFalse(printer.busy)

  def test_return(self) -> None:
    """Between lines the carriage takes 'RETURN' s; a bell rings as its
    line begins."""
    printer = Teleprinter()
    printer.said('ab')
    printer.said('cd', True)
    printer.acted(2.0 / RATE)
    self.assertEqual(printer.bells, 0)
    printer.acted(0.5 * RETURN)
    self.assertEqual(printer.paper()[1], '')
    printer.acted(0.5 * RETURN + 1.0 / RATE)
    self.assertEqual(printer.bells, 1)
    self.assertEqual(printer.paper(), (['AB'], 'C', 1))

  def test_wrap(self) -> None:
    """Past 'WIDTH' a line wraps at a space, its bell rung once, before
    its first part."""
    printer = Teleprinter()
    words = ['word%02d' % k for k in range(12)]
    printer.said(' '.join(words), True)
    self.assertEqual(printer.queue, [(' '.join(words[:11]).upper(), True),
                                     (words[11].upper(), False)])

  def test_paper(self) -> None:
    """A word longer than a line is cut to 'WIDTH'; the paper keeps the
    last 'KEPT' lines; the icons are single characters of the Nerd
    Font's own range."""
    printer = Teleprinter()
    printer.said('x' * (2 * WIDTH))
    for k in range(KEPT + 3):
      printer.said('line %d' % k)
    printer.acted(1000.0)
    printed = printer.paper()[0]
    self.assertEqual(len(printed), KEPT)
    self.assertEqual(printed[-1], 'LINE %d' % (KEPT + 2))
    self.assertEqual(printer.returns, KEPT + 4)
    self.assertEqual(printer.typed, WIDTH + sum(
      len('line %d' % k) for k in range(KEPT + 3)))
    for icon in ICONS.values():
      self.assertEqual(len(icon), 1)
      self.assertGreaterEqual(ord(icon), 0xe000)

  def test_fits(self) -> None:
    """A line of 'WIDTH' characters fits across the paper at a Teletype's
    pitch, margins either side, as its picture lays it out; the lines
    kept fill the paper above the line typed; the paper's window keeps
    clear of the panel's sections."""
    self.assertEqual(WIDTH, 77)
    self.assertLess(WIDTH * PITCH, PAPER_WIDE)
    at = paperLayout()
    self.assertAlmostEqual(at['height'] / at['width'],
                           PAPER_HIGH / PAPER_WIDE, 2)
    right = at['margin'] + WIDTH * 0.6 * at['font']
    self.assertGreater(at['margin'], 0.0)
    self.assertAlmostEqual(right + at['margin'], at['width'], 6)
    top = at['foot'] + KEPT * at['line'] + 0.75 * at['font']
    self.assertLess(top, at['height'])
    self.assertGreater(top + at['line'], at['height'])
    self.assertAlmostEqual(at['line'] / at['width'], LINE / PAPER_WIDE, 9)
    u, v = PAPER_AT
    edge = 0.5 * PAPER_WIDE + 0.012
    for title, left, bottom, right, top in SECTIONS:
      if bottom > v + 0.5 * PAPER_HIGH or top < v - 0.5 * PAPER_HIGH:
        continue
      self.assertTrue(right < u - edge or left > u + edge, title)
