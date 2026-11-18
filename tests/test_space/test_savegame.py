"""
TestSaveGame covers the save and the load (user, 2026-11-17: "Add a note
that we need a save/load system"; 2026-11-18: "Also implement the save
load system now"): values go through JSON as they were (tuples, lists,
sets, dicts, None, infinities); what is not a plain value raises; every
class a game keeps declares fields it has, and a fresh one takes them
back as they were; a save missing one raises; the sky put into another
day's solar system is the saved one's to the bit (Terra Prime's path and
axis too); a save is written whole or not at all and read back, another
version refused; a rocket loaded from a save into another session flies
on as the saved one did.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

from worQt.gaming.space._ascentguidance import AscentGuidance
from worQt.gaming.space._autoflight import Autoflight
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._dockingguidance import DockingGuidance
from worQt.gaming.space._dockingport import DockingPort
from worQt.gaming.space._elevator import Elevator
from worQt.gaming.space._gravgun import GravGun
from worQt.gaming.space._instruments import Instruments
from worQt.gaming.space._inventory import Inventory
from worQt.gaming.space._planets import solarSystemOn
from worQt.gaming.space._quest import Quest
from worQt.gaming.space._rendezvousguidance import RendezvousGuidance
from worQt.gaming.space._savegame import SAVE_VERSION, SaveGame, _back
from worQt.gaming.space._savegame import _plain, keptOf, keptTo, skyOf
from worQt.gaming.space._savegame import skyTo
from worQt.gaming.space._station import Station
from worQt.gaming.space._timekeeper import Timekeeper
from worQt.gaming.space._towerlift import TowerLift
from worQt.gaming.space._vessel import Vessel
from worQt.gaming.space._vitals import Vitals
from worQt.gaming.space._walkway import Walkway

from . import FRAME, SpaceTest
from ._space_test import TODAY


class TestSaveGame(SpaceTest):
  """Tests for the save and the load."""

  __time_out__ = 300.0

  def _kept(self, system: object) -> list:
    """Returns one of each class a game keeps, fresh."""
    station = Station(system)
    port = DockingPort(station)
    ascent, docking = AscentGuidance(), DockingGuidance()
    rendezvous = RendezvousGuidance(station)
    cockpit = Cockpit()
    return [Timekeeper(system), Vessel(), ascent, rendezvous, docking,
            port, Autoflight(ascent, rendezvous, docking, port), cockpit,
            Vitals(), Inventory(), Quest(), Walkway(True), TowerLift(),
            Elevator(), Instruments(cockpit), GravGun()]

  def test_values(self) -> None:
    """Tuples, lists, sets, dicts (of words), numbers, words, truths,
    None and infinities come back through JSON as they were."""
    value = ((1.0, 2, -0.0), [None, ['a', 3], (4.5,)], {'x', 'y'},
             {'k': (1.5, True), 'l': [{'z'}]}, math.inf, -math.inf, None,
             'w', ())
    back = _back(json.loads(json.dumps(_plain(value))))
    self.assertEqual(back, value)
    self.assertIs(type(back[1]), list)
    self.assertIs(type(back[1][1]), list)
    self.assertIs(type(back[1][2]), tuple)
    self.assertTrue(math.isnan(_back(json.loads(json.dumps(_plain(
      math.nan))))))

  def test_unsaveable(self) -> None:
    """What is not a plain value raises, as does a dict keyed by other
    than words."""
    with self.assertRaises(TypeError):
      _plain(object())
    with self.assertRaises(TypeError):
      _plain({1: 'one'})

  def test_declared(self) -> None:
    """Every class a game keeps declares fields it has; what it keeps
    goes through JSON and a fresh one takes it back as it was."""
    system = self.systemOf()
    things, fresh = self._kept(system), self._kept(system)
    vessel = things[1]
    vessel.engine.throttled(0.4)
    vessel.felt, vessel.docked = (0.0, 0.1, 9.8), True
    things[7].gotUp()
    things[9].chosen(4)
    things[10].done.add('door')
    things[14].printer.said('HELLO WORLD')
    for thing, other in zip(things, fresh):
      kept = json.loads(json.dumps(keptOf(thing)))
      keptTo(other, kept)
      self.assertEqual(keptOf(other), keptOf(thing), type(thing).__name__)
    self.assertEqual(fresh[1].engine.throttle, 0.4)
    self.assertFalse(fresh[7].crewman.buckled)
    self.assertEqual(fresh[10].done, {'door'})

  def test_missing(self) -> None:
    """A save missing a field (or a part) raises."""
    kept = keptOf(Vessel())
    kept.pop('turn')
    with self.assertRaises(KeyError):
      keptTo(Vessel(), kept)
    kept = keptOf(Vessel())
    kept.pop('engine')
    with self.assertRaises(KeyError):
      keptTo(Vessel(), kept)

  def test_sky(self) -> None:
    """The sky put into another day's solar system (another session,
    Terra Prime made there with another lead, then kept to the saved
    one) is the saved one's to the bit: every body's and Terra Prime's
    place, motion and turn; a sky of other bodies raises."""
    system = self.systemOf()
    station = Station(system)
    keeper = Timekeeper(system)
    keeper.leapt(12345.6)
    sky = json.loads(json.dumps(skyOf(system)))
    kept = json.loads(json.dumps(keptOf(station)))
    other = solarSystemOn(TODAY + 100.0, 'cpu')
    elsewhere = Station(other, -0.06)
    skyTo(other, sky)
    keptTo(elsewhere, kept)
    for t in (0.0, 600.0, 86400.0):
      for k in range(len(system.bodies)):
        self.assertEqual(other.stateOf(k, t), system.stateOf(k, t))
        self.assertEqual(other.bodies[k].turnAt(t),
                         system.bodies[k].turnAt(t))
      self.assertEqual(elsewhere.stateAt(t), station.stateAt(t))
      self.assertEqual(elsewhere.turnAt(t), station.turnAt(t))
    with self.assertRaises(ValueError):
      wrong = dict(sky, bodies=sky['bodies'][:-1])
      skyTo(self.systemOf(), wrong)

  def test_file(self) -> None:
    """A save is written whole (nothing left aside) and read back as it
    was; a save of another version is refused."""
    with tempfile.TemporaryDirectory() as folder:
      path = Path(folder) / 'quick.json'
      save = SaveGame({'a': [1, 2.5], 'b': None})
      save.written(path)
      self.assertEqual([p.name for p in Path(folder).iterdir()],
                       ['quick.json'])
      back = SaveGame.read(path)
      self.assertEqual(back.state, save.state)
      self.assertEqual(back.saved, save.saved)
      data = json.loads(path.read_text())
      data['version'] = SAVE_VERSION + 1
      path.write_text(json.dumps(data))
      with self.assertRaises(ValueError):
        SaveGame.read(path)

  def test_flown_on(self) -> None:
    """A rocket in orbit saved (through JSON), loaded into another
    session (another day's sky, a fresh rocket, a fresh flight) flies on
    as the saved one did, leaps and all: to the millimetre."""
    system = self.systemOf()
    keeper = Timekeeper(system)
    vessel = self.orbiting(system, 200e3, 260e3, 'ahead')
    flight = self.flightOf()
    keeper.factor = 1000
    self._flown(flight, vessel, system, keeper, 300)
    text = json.dumps({'sky': skyOf(system), 'keeper': keptOf(keeper),
                       'vessel': keptOf(vessel)})
    self._flown(flight, vessel, system, keeper, 300)
    other = solarSystemOn(TODAY + 30.0, 'cpu')
    loaded, again = Timekeeper(other), Vessel()
    state = json.loads(text)
    skyTo(other, state['sky'])
    keptTo(loaded, state['keeper'])
    keptTo(again, state['vessel'])
    loaded.factor = 1000
    self._flown(self.flightOf(), again, other, loaded, 300)
    self.assertEqual(loaded.leaps, keeper.leaps)
    self.assertClose(again.place, vessel.place, 1e-3)
    self.assertClose(again.velocity, vessel.velocity, 1e-6)

  def _flown(self, flight: object, vessel: Vessel, system: object,
             keeper: Timekeeper, frames: int) -> None:
    """Flies 'vessel' 'frames' frames on as the window does (time kept
    by 'keeper', leaps and all)."""
    for _ in range(frames):
      seconds = keeper.secondsOf(FRAME)
      flight.flown((vessel,), system, keeper.now, seconds)
      keeper.ticked(seconds)
