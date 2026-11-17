"""
TestInstruments covers the cabin kept to the flight (user, 2026-11-16:
"dials, switches and indicators illuminated. *Every* fourtpeep input
... must visibly deform when activated"; "all of the inputs and outputs
should have appropriate clicky sounds"): each switch stands as its mode
is, the warp knob at the warp, the slide at the throttle, the play key
latched while the tape plays, each counted for its sound; the lamps
lit as the flight is; the needles easing to their values; the tape
starting itself out of the air; what the sound is told.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space import _cabinmixer as mixer
from worQt.gaming.space._ascentguidance import AscentGuidance
from worQt.gaming.space._cockpit import LAMPS, Cockpit
from worQt.gaming.space._dashboard import LEGENDS, dialShare
from worQt.gaming.space._instruments import Instruments, NEEDLE
from worQt.gaming.space._timekeeper import Timekeeper

from . import SpaceTest


class TestInstruments(SpaceTest):
  """Tests for 'Instruments'."""

  def _ready(self, ) -> tuple:
    """Returns the system, a vessel on the pad (its legs down), a
    timekeeper, the guidance and the instruments."""
    system = self.systemOf()
    vessel = self.padded(system)
    vessel.touching = 4
    cockpit = Cockpit()
    return (system, vessel, Timekeeper(system), AscentGuidance(),
            Instruments(cockpit))

  def test_switches(self) -> None:
    """A mode engaged, its switch is thrown (a snap); the warp knob
    stands at the warp's notch (a tick a notch); the slide goes to the
    throttle; the legend over a thrown switch is lit."""
    system, vessel, keeper, guidance, kit = self._ready()
    kit.acted(0.0, vessel, system, keeper, guidance, False, True, 'go')
    self.assertEqual((kit.snaps, kit.ticks), (1, 0))
    vessel.autopilot.engaged('hold', vessel.turn)
    keeper.factor = 100
    vessel.engine.throttled(0.5)
    kit.acted(1.0, vessel, system, keeper, guidance, True, True, 'go')
    cockpit = kit.cockpit
    self.assertEqual(cockpit.controlOf('hold').peep.value, 1.0)
    self.assertEqual(cockpit.controlOf('map').peep.value, 1.0)
    self.assertEqual(cockpit.controlOf('view').peep.value, 1.0)
    self.assertEqual(cockpit.controlOf('prograde').peep.value, 0.0)
    self.assertEqual(cockpit.controlOf('warp').peep.notch, 4)
    self.assertEqual(kit.ticks, 4)
    self.assertEqual(kit.snaps, 3)
    self.assertAlmostEqual(cockpit.controlOf('throttle').peep.value, 0.5)
    lit = dict(zip(LEGENDS, kit.legends))
    self.assertTrue(lit['HOLD'] and lit['MAP'] and lit['VIEW'])
    self.assertFalse(lit['PRO'] or lit['ASCENT'])
    kit.acted(1.0, vessel, system, keeper, guidance, True, True, 'go')
    self.assertEqual((kit.snaps, kit.ticks), (3, 4))

  def test_keys(self) -> None:
    """A key pressed sinks and clicks; switches, knobs and the slide
    are not pressed (they follow what they work); the play key stays in
    while the tape plays."""
    system, vessel, keeper, guidance, kit = self._ready()
    kit.pressed('toAp')
    self.assertEqual(kit.clicks, 1)
    self.assertEqual(kit.cockpit.controlOf('toAp').peep.target, 1.0)
    kit.pressed('hold')
    kit.pressed('warp')
    self.assertEqual(kit.clicks, 1)
    kit.deck.play()
    kit.acted(0.5, vessel, system, keeper, guidance, False, True, 'go')
    play = kit.cockpit.controlOf('play').peep
    self.assertTrue(play.latched)
    self.assertEqual(play.value, 1.0)
    self.assertEqual(kit.clicks, 2)
    kit.deck.halt()
    kit.acted(0.5, vessel, system, keeper, guidance, False, True, 'go')
    self.assertFalse(play.latched)
    self.assertEqual(play.value, 0.0)

  def test_lamps(self) -> None:
    """On the pad the air and ground lamps are lit, the rest dark; in
    orbit the orbit's lamp alone, each change a relay's click."""
    system, vessel, keeper, guidance, kit = self._ready()
    kit.acted(0.1, vessel, system, keeper, guidance, False, True, 'go')
    lit = {name: on for (name, _), on in zip(LAMPS, kit.lamps)}
    self.assertEqual(lit, {'ENGINE': False, 'AIR': True, 'GROUND': True,
                           'WARP': False, 'GUIDE': False, 'ORBIT': False,
                           'DOCK': False})
    self.assertEqual(kit.relays, 2)
    vessel = self.orbiting(system, 300e3, 300e3)
    kit.acted(0.1, vessel, system, keeper, guidance, False, True, 'go')
    lit = {name: on for (name, _), on in zip(LAMPS, kit.lamps)}
    self.assertEqual([name for name, on in lit.items() if on], ['ORBIT'])
    self.assertEqual(kit.relays, 5)

  def test_needles(self) -> None:
    """The needles ease to their values, most of the way in 'NEEDLE' s;
    in orbit the height's stands at the height's share; on the pad the
    speed's at nought (the speed over the ground, in the air)."""
    system, vessel, keeper, guidance, kit = self._ready()
    vessel = self.orbiting(system, 300e3, 300e3)
    kit.acted(NEEDLE, vessel, system, keeper, guidance, False, True, 'go')
    want = dialShare('HEIGHT', vessel.heightOver(system))
    self.assertAlmostEqual(kit.needles[0], want * (1.0 - math.exp(-1.0)),
                           6)
    for _ in range(40):
      kit.acted(0.1, vessel, system, keeper, guidance, False, True, 'go')
    self.assertAlmostEqual(kit.needles[0], want, 6)
    self.assertGreater(kit.needles[1], 0.5)
    vessel = self.padded(system)
    for _ in range(40):
      kit.acted(0.1, vessel, system, keeper, guidance, False, True, 'go')
    self.assertLess(kit.needles[1], 0.01)

  def test_announced(self) -> None:
    """Climbing to leave the air within 'LEAD_IN' s the deck is
    announced (its clicks), once; further below, or falling, not; the
    sound is told how often."""
    from worQt.gaming.space._tapedeck import LEAD_IN
    system, vessel, keeper, guidance, kit = self._ready()
    terra = system.named('Terra')
    body = system.bodies[terra]
    up = tuple(row[0] for row in body.tilt)
    for below, climb, want in ((500.0, 1000.0, True), (5000.0, 1000.0,
                                                       False),
                               (500.0, -1000.0, False)):
      kit = Instruments(Cockpit())
      vessel.placed(terra, tuple((body.radius + body.air.top - below) * x
                                 for x in up), tuple(climb * x for x in up),
                    vessel.turn, (0.0, 0.0, 0.0))
      kit.acted(0.1, vessel, system, keeper, guidance, False, True, 'go')
      self.assertEqual(kit.deck.announced, want, (below, climb))
      self.assertEqual(kit.told(vessel, system, True)[mixer.ANNOUNCED],
                       1 if want else 0)
      self.assertFalse(kit.deck.playing)
    self.assertLess(500.0, 1000.0 * LEAD_IN)

  def test_cheered(self) -> None:
    """Leaving the air the tape plays, from its beginning, once."""
    system, vessel, keeper, guidance, kit = self._ready()
    kit.acted(0.1, vessel, system, keeper, guidance, False, True, 'go')
    self.assertFalse(kit.deck.playing)
    vessel = self.orbiting(system, 300e3, 300e3)
    kit.acted(0.1, vessel, system, keeper, guidance, False, True, 'go')
    self.assertTrue(kit.deck.playing)
    self.assertEqual(kit.deck.rewinds, 1)

  def test_told(self) -> None:
    """The sound is told every number: the engine, inside or out, the
    air (whole on the pad, none in orbit), the counts."""
    system, vessel, keeper, guidance, kit = self._ready()
    vessel.engine.throttled(1.0)
    told = kit.told(vessel, system, True)
    self.assertEqual(len(told), mixer.TOLD)
    self.assertEqual(told[mixer.ENGINE], 1.0)
    self.assertEqual(told[mixer.INSIDE], 1.0)
    self.assertAlmostEqual(told[mixer.AIR], 1.0, 2)
    self.assertEqual(kit.told(vessel, system, False)[mixer.INSIDE], 0.0)
    vessel = self.orbiting(system, 300e3, 300e3)
    self.assertEqual(kit.told(vessel, system, True)[mixer.AIR], 0.0)
