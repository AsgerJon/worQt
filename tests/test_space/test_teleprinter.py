"""
TestTeleprinter covers the cabin's teleprinter (user, 2026-11-16:
"Instead of a terminal ... let's have a teleprinter"; "It should use a
modern font like nerd monospace to be cheeky"): capitals cut to its
width, ten characters a second, its bell before what matters, the
carriage returning between lines, the paper keeping its last lines.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._teleprinter import ICONS, KEPT, RATE, RETURN
from worQt.gaming.space._teleprinter import WIDTH, Teleprinter

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
    printer.said('one two three four five six seven eight', True)
    self.assertEqual(printer.queue, [('ONE TWO THREE FOUR FIVE', True),
                                     ('SIX SEVEN EIGHT', False)])

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
