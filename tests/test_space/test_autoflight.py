"""
TestAutoflight covers the autopilot's three modes (user, 2026-11-17:
"Right now we have three modes of operation that should be distinct:
Orbit, Rendezvous and Docking. We don't need the autopilot to do all
three at once. Instead we should have the three modes. Next we should
have an indicator of the auto pilot being allowed to have control"):
ORBIT chosen at first, nothing engaged; a mode chosen while not engaged
only chosen; engaged, it flies its guidance, refused (said why) where
it cannot fly; another chosen while engaged flies at once or lets go;
done, it lets go by itself; the engine dark on the pad until LAUNCH.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._ascentguidance import AscentGuidance
from worQt.gaming.space._autoflight import Autoflight
from worQt.gaming.space._dockingguidance import DockingGuidance
from worQt.gaming.space._dockingport import DockingPort
from worQt.gaming.space._rendezvousguidance import RendezvousGuidance
from worQt.gaming.space._station import Station
from worQt.gaming.space._timekeeper import Timekeeper
from worQt.gaming.space._transfers import Transfers

from . import FRAME, SpaceTest


class TestAutoflight(SpaceTest):
  """Tests for 'Autoflight'."""

  __time_out__ = 300.0

  def _ready(self, ) -> tuple:
    """Returns a system, its timekeeper and an autopilot with its three
    guidances (the rendezvous's transfers on the CPU)."""
    system = self.systemOf()
    station = Station(system)
    rendezvous = RendezvousGuidance(station)
    rendezvous.transfers = Transfers('cpu')
    flying = Autoflight(AscentGuidance(), rendezvous, DockingGuidance(),
                        DockingPort(station))
    return system, Timekeeper(system), flying

  def test_chosen(self) -> None:
    """ORBIT is chosen at first, not engaged; choosing another mode
    while not engaged only chooses it; an unknown mode raises."""
    system, keeper, flying = self._ready()
    vessel = self.padded(system)
    self.assertEqual((flying.mode, flying.engaged), ('orbit', False))
    said = flying.chosen('dock', vessel, system, keeper)
    self.assertEqual((flying.mode, flying.engaged), ('dock', False))
    self.assertIn('DOCK', said)
    with self.assertRaises(KeyError):
      flying.chosen('warp', vessel, system, keeper)

  def test_pad(self) -> None:
    """On the pad ORBIT engages (the ascent flies) and lets go again;
    RNDZ and DOCK are refused, said why, not engaged."""
    system, keeper, flying = self._ready()
    vessel = self.padded(system)
    self.assertIn('engaged', flying.toggled(vessel, system, keeper))
    self.assertTrue(flying.engaged and flying.ascent.on)
    self.assertEqual(flying.toggled(vessel, system, keeper),
                     'Autopilot off')
    self.assertFalse(flying.engaged or flying.ascent.on)
    flying.chosen('rendezvous', vessel, system, keeper)
    self.assertIn('needs an orbit', flying.toggled(vessel, system,
                                                   keeper))
    self.assertFalse(flying.engaged)
    flying.chosen('dock', vessel, system, keeper)
    self.assertIn('km off', flying.toggled(vessel, system, keeper))
    self.assertFalse(flying.engaged)

  def test_switched(self) -> None:
    """Engaged in ORBIT on the pad, choosing RNDZ lets go (it cannot
    fly there), the ascent stopped; in orbit ORBIT is refused and RNDZ
    flies."""
    system, keeper, flying = self._ready()
    vessel = self.padded(system)
    flying.toggled(vessel, system, keeper)
    said = flying.chosen('rendezvous', vessel, system, keeper)
    self.assertIn('Autopilot off', said)
    self.assertFalse(flying.engaged or flying.ascent.on)
    vessel = self.orbiting(system, 200e3, 200e3, 'ahead')
    flying.chosen('orbit', vessel, system, keeper)
    self.assertIn('in orbit already', flying.toggled(vessel, system,
                                                     keeper))
    flying.chosen('rendezvous', vessel, system, keeper)
    self.assertIn('engaged', flying.toggled(vessel, system, keeper))
    self.assertTrue(flying.engaged and flying.rendezvous.on)
    flying.letGo(vessel)
    self.assertFalse(flying.engaged or flying.rendezvous.on)

  def test_done(self) -> None:
    """Once its guidance is done the autopilot lets go by itself, said;
    the next mode is named."""
    system, keeper, flying = self._ready()
    vessel = self.padded(system)
    flying.toggled(vessel, system, keeper)
    reading = flying.port.readingOf(vessel, system, keeper.now)
    self.assertEqual(flying.acted(vessel, system, keeper, reading, True),
                     '')
    self.assertTrue(flying.engaged)
    vessel = self.orbiting(system, 200e3, 200e3, 'ahead')
    flying.ascent.phase = 'done'
    said = flying.acted(vessel, system, keeper, reading, True)
    self.assertTrue(said.startswith('ORBIT done'))
    self.assertIn('RNDZ', said)
    self.assertFalse(flying.engaged)

  def test_dark(self) -> None:
    """Unlit, the throttle stays shut though the ascent opens it (user,
    2026-11-19: "The launch switch allows the throttle. It doesn't just
    hold down the rocket, whilst the autopilot keeps burning the
    rocket"): nothing pushes, the rocket stays on the pad; lit, the
    ascent opens it and it lifts off."""
    system, keeper, flying = self._ready()
    flight = self.flightOf()
    vessel = self.padded(system)
    vessel.engine.lit = False
    standing = vessel.heightOver(system)
    flying.toggled(vessel, system, keeper)
    for _ in range(60):
      reading = flying.port.readingOf(vessel, system, keeper.now)
      flying.acted(vessel, system, keeper, reading, True)
      flight.flown((vessel,), system, keeper.now, FRAME)
      keeper.ticked(FRAME)
    self.assertEqual(vessel.engine.throttle, 0.0)
    self.assertEqual(vessel.engine.push, 0.0)
    self.assertLess(abs(vessel.heightOver(system) - standing), 0.05)
    vessel.engine.lit = True
    for _ in range(120):
      reading = flying.port.readingOf(vessel, system, keeper.now)
      flying.acted(vessel, system, keeper, reading, True)
      flight.flown((vessel,), system, keeper.now, FRAME)
      keeper.ticked(FRAME)
    self.assertGreater(vessel.heightOver(system), standing + 10.0)
