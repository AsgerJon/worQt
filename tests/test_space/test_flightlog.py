"""
TestFlightLog covers what the teleprinter is told (the spec: a line
every 10 s, and one on each event): its header first, then each event
once as it happens (lift-off, out of the air, in orbit, the engine, the
guidance's phase), bells on the great ones, a line of how it goes every
'EVERY' s while the teleprinter is idle.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._flightlog import EVERY, FlightLog
from worQt.gaming.space._teleprinter import ICONS, WIDTH, Teleprinter

from . import SpaceTest


class TestFlightLog(SpaceTest):
  """Tests for 'FlightLog'."""

  def test_header(self) -> None:
    """The first look prints the header with a bell and a rule; nothing
    happening, nothing more till 'EVERY' s on."""
    system = self.systemOf()
    vessel = self.padded(system)
    log, printer = FlightLog(), Teleprinter()
    events = log.acted(0.0, vessel, system, 0.0, 'off', printer, 'hello')
    self.assertEqual(events, [])
    self.assertEqual(printer.queue, [('HELLO', True),
                                     ('-' * WIDTH, False)])
    printer.acted(100.0)
    self.assertEqual(log.acted(0.5 * EVERY, vessel, system, 0.0, 'off',
                               printer, 'hello'), [])
    self.assertEqual(printer.queue, [])
    log.acted(0.5 * EVERY, vessel, system, 0.0, 'off', printer, 'hello')
    self.assertTrue(printer.queue[0][0].startswith(ICONS['clock']))

  def test_events(self) -> None:
    """From the pad to an orbit 300 km up: lift-off, out of the air and
    in orbit, each once, bells rung; the engine lit and the guidance's
    phase each a line."""
    system = self.systemOf()
    log, printer = FlightLog(), Teleprinter()
    pad = self.padded(system)
    pad.touching = 4
    log.acted(0.0, pad, system, 0.0, 'off', printer, 'go')
    printer.acted(100.0)
    vessel = self.orbiting(system, 300e3, 300e3)
    events = log.acted(0.1, vessel, system, 600.0, 'off', printer, 'go')
    self.assertEqual(events, ['lift-off', 'out of the air', 'orbit'])
    self.assertEqual(sum(bell for _, bell in printer.queue), 3)
    self.assertTrue(any('IN ORBIT' in line for line, _ in printer.queue))
    printer.acted(100.0)
    vessel.engine.throttled(1.0)
    events = log.acted(0.1, vessel, system, 601.0, 'coast', printer, 'go')
    self.assertEqual(events, ['engine on', 'phase'])
    self.assertEqual(log.acted(0.1, vessel, system, 602.0, 'coast',
                               printer, 'go'), [])
