"""
Instruments are the cabin's working parts alive (user, 2026-11-16:
"dials, switches and indicators illuminated. *Every* fourtpeep input
... must visibly deform when activated"; "all of the inputs and outputs
should have appropriate clicky sounds"): each input's FourthPeep kept to
what it works (a switch stands as its mode is, the warp knob at the
warp, the slide at the throttle; a key pressed sinks), the dials'
needles easing to their values, the lamps and legends lit, the
teleprinter typing the flight log, the tape deck, and what the
cabin's sound is told.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from worQt.gaming.sandbox import FourthPeep, Knob, Pushbutton, Slider
from worQt.gaming.sandbox._slider import SLIDE

from . import _cabinmixer as mixer
from ._ascentguidance import TARGET
from ._aerospike import G0
from ._tapedeck import LEAD_IN, TapeDeck
from ._cockpit import DIALS, GUARD_HOLD, KEYS, LAMPS, LIMITS, LIT_KEYS
from ._dashboard import LEGENDS, dialShare
from ._flightlog import FlightLog
from ._teleprinter import WIDTH, Teleprinter
from ._timekeeper import WARPS
from ._turns import dot, norm, unit
from ._vessel import MASS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._ascentguidance import AscentGuidance
  from ._cockpit import Cockpit
  from ._solarsystem import SolarSystem
  from ._timekeeper import Timekeeper
  from ._vessel import Vessel

#  How fast the needles ease to their values (most of the way in), s.
NEEDLE = 0.25
#  The sound's volume.
VOLUME = 0.8
#  The candles' flicker: how far it wanders a frame, how hard it is drawn
#  back to burning steady, its least and most.
FLICKER = (0.12, 0.25, 0.55, 1.15)
#  How fast a guard flips up and down (most of the way in), s.
GUARD_EASE = 0.07
#  How fast the tape deck's knob turns to play or stop (most of the way
#  in), s.
KNOB = 0.15
#  The switches' modes: the autopilot's (by the switch's action).
MODES = ('hold', 'prograde', 'retrograde', 'aim', 'match')

#  What the lit keys work (they stay in while it is on).
LIT_ACTIONS = tuple(key[2] for key in KEYS if key[0] in LIT_KEYS)


class Instruments:
  """
  Instruments hold the cabin's working parts for 'cockpit': its
  'printer' (a 'Teleprinter') told by its 'log' (a 'FlightLog'), its
  'deck' (a 'TapeDeck', cheering the vessel out of the air), the
  dials' 'needles' (each a share of its scale, eased), the 'lamps' and
  the 'legends' (lit or not); and the counts the sound
  plays one of as they grow: the keys' 'clicks', the switches' 'snaps',
  the knobs' 'ticks', the lamps' 'relays'; how fast the slide moves;
  'switched', what the window keeps that a switch or a latched key shows
  ('autodock': the automatic docking flies, 'camera': the monitor shows
  the nose's docking camera).
  'pressed' presses an input's key; 'acted' keeps everything to the
  flight a frame on; 'dash' and 'told' hand the view and the sound what
  they show and play.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, cockpit: Cockpit) -> None:
    self.cockpit = cockpit
    self.printer, self.log, self.deck = (Teleprinter(), FlightLog(),
                                         TapeDeck())
    self.needles = [0.0] * len(DIALS)
    self.lamps = [False] * len(LAMPS)
    self.legends = [False] * len(LEGENDS)
    self.clicks = self.snaps = self.ticks = self.relays = 0
    self.slide, self.knob, self.target = 0.0, 0.0, TARGET
    self.guards, self._held = {}, {}
    self.flicker, self._flame = 1.0, random.Random(1980)
    self.switched = {'autodock': False, 'camera': False}

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def pressed(self, action: str) -> None:
    """The 'pressed' method sinks the key working 'action' (and clicks):
    switches, knobs and the slide follow what they work instead."""
    control = self.cockpit.controlOf(action)
    if control is not None and isinstance(control.peep, Pushbutton):
      control.peep.used()
      self.clicks += 1

  def acted(self, real: float, vessel: Vessel, system: SolarSystem,
            keeper: Timekeeper, guidance: AscentGuidance, mapOpen: bool,
            inside: bool, header: str) -> None:
    """The 'acted' method keeps the cabin to the flight 'real' s of real
    time on: the log and the teleprinter, the deck (cheering the vessel
    out of the air), each input's FourthPeep (counting its snap or tick
    as it moves), the needles, lamps and legends."""
    self.target = guidance.target
    self._announced(vessel, system)
    events = self.log.acted(real, vessel, system, keeper.elapsed,
                            guidance.phase, self.printer, header)
    if 'out of the air' in events:
      self.deck.celebrated()
    self.printer.acted(real)
    self.deck.acted(real)
    states = {mode: vessel.autopilot.mode == mode for mode in MODES}
    states.update({'ascent': guidance.on, 'map': mapOpen,
                   'view': inside})
    states.update(self.switched)
    latched = {'play': self.deck.playing, 'camera': self.switched[
      'camera']}
    latched.update({action: bool(states.get(action))
                    for action in LIT_ACTIONS})
    slid = 0.0
    for control in self.cockpit.controls:
      peep = control.peep
      if type(peep) is FourthPeep:
        want = 1.0 if states.get(control.action) else 0.0
        if peep.target != want:
          peep.target = want
          self.snaps += 1
          self._held[control.action] = GUARD_HOLD
      elif isinstance(peep, Knob):
        notch = {'warp': WARPS.index(keeper.factor),
                 'limit': limitNotch(vessel.engine)}.get(control.action)
        if notch is None:
          notch = guidance.notch()
        if notch != peep.notch:
          self.ticks += abs(notch - peep.notch)
          peep.set(notch)
          self._held[control.action] = GUARD_HOLD
      elif isinstance(peep, Slider):
        before = peep.value
        peep.slid(vessel.engine.throttle)
        slid = before
      elif control.action in latched and (
          peep.latched != latched[control.action]):
        peep.held(latched[control.action])
        self.clicks += 1
    self.cockpit.acted(real)
    slider = self.cockpit.controlOf('throttle').peep
    self.slide = min(1.0, abs(slider.value - slid) / max(
      1e-6, real / SLIDE)) if real > 0.0 else 0.0
    self._needlesEased(real, vessel, system)
    self._lampsLit(vessel, system, keeper, guidance)
    actions = {control.name: control.action
               for control in self.cockpit.controls}
    self.legends = [bool(states.get(actions[name])) for name in LEGENDS]
    if real > 0.0:
      want = 1.0 if self.deck.playing else 0.0
      self.knob += (1.0 - math.exp(-real / KNOB)) * (want - self.knob)
      self._guardsMoved(real)
      wander, pull, least, most = FLICKER
      self.flicker = max(least, min(most, self.flicker + self._flame.uniform(
        -wander, wander) + pull * (1.0 - self.flicker)))

  def dash(self, ) -> dict:
    """The 'dash' method returns what the dashboard shows now, as
    'Scenery.cabinOf' takes it."""
    _, _, column = self.printer.paper()
    return {'needles': list(self.needles), 'lamps': list(self.lamps),
            'legends': list(self.legends), 'reels': self.deck.reels,
            'column': min(1.0, column / WIDTH), 'knob': self.knob,
            'bug': dialShare('HEIGHT', self.target),
            'guards': dict(self.guards), 'flicker': self.flicker}

  def told(self, vessel: Vessel, system: SolarSystem,
           inside: bool) -> tuple:
    """The 'told' method returns what the cabin's sound is told
    ('_cabinmixer.TOLD' numbers)."""
    body = system.bodies[vessel.anchor]
    air = body.air
    thick = 0.0 if air is None else math.sqrt(air.densityAt(
      vessel.heightOver(system)) / air.densities[0])
    out = [0.0] * mixer.TOLD
    out[mixer.VOLUME] = VOLUME
    out[mixer.ENGINE] = vessel.engine.push / vessel.engine.thrust
    out[mixer.INSIDE] = 1.0 if inside else 0.0
    out[mixer.AIR] = thick
    out[mixer.CLICKS], out[mixer.SNAPS] = self.clicks, self.snaps
    out[mixer.TICKS], out[mixer.SLIDE] = self.ticks, self.slide
    out[mixer.TYPED] = self.printer.typed
    out[mixer.BELLS] = self.printer.bells
    out[mixer.RETURNS] = self.printer.returns
    out[mixer.DECK] = 1.0 if self.deck.playing else 0.0
    out[mixer.REWINDS] = self.deck.rewinds
    out[mixer.RELAYS] = self.relays
    out[mixer.ANNOUNCED] = self.deck.announcements
    return tuple(out)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _announced(self, vessel: Vessel, system: SolarSystem) -> None:
    """Announces the deck (its clicks getting ready) once the vessel,
    climbing in the air, will be out of it within 'LEAD_IN' s (time does
    not warp in the air: the game's seconds are real ones), so the
    clicks end as the music starts (user, 2026-11-16: "The music should
    start only upon clearing the atmosphere")."""
    air = system.bodies[vessel.anchor].air
    if air is None or self.deck.announced or self.deck.cheered:
      return
    height = vessel.heightOver(system)
    climb = dot(vessel.velocity, unit(vessel.place))
    if height < air.top and climb > 0.0 and (
        air.top - height) <= climb * LEAD_IN:
      self.deck.announce()

  def _guardsMoved(self, real: float) -> None:
    """Flips each guard up while its input is worked and for
    'GUARD_HOLD' s after, then down, eased."""
    share = 1.0 - math.exp(-real / GUARD_EASE)
    for action in set(self._held) | set(self.guards):
      left = self._held.get(action, 0.0) - real
      self._held[action] = max(0.0, left)
      want = 1.0 if left > 0.0 else 0.0
      now = self.guards.get(action, 0.0)
      self.guards[action] = now + share * (want - now)

  def valuesOf(self, vessel: Vessel, system: SolarSystem) -> dict:
    """The 'valuesOf' method returns what each dial shows, by its
    name: the height, the speed (over the ground in the air, round the
    body above it), the apoapsis and the periapsis over the ground (none
    below it; 1e9: no closed orbit)."""
    body = system.bodies[vessel.anchor]
    conic = vessel.conicOf(system)
    height = vessel.heightOver(system)
    inAir = body.air is not None and height < body.air.top
    speed = norm(vessel.groundVelocity(system) if inAir
                 else vessel.velocity)
    apo = conic.apoapsis - body.radius if conic and conic.closed else (
      0.0 if conic is None else 1e9)
    peri = conic.periapsis - body.radius if conic else 0.0
    return {'HEIGHT': height, 'SPEED': speed, 'APOAPSIS': apo,
            'PERIAPSIS': peri}

  def _needlesEased(self, real: float, vessel: Vessel,
                    system: SolarSystem) -> None:
    """Eases each needle toward its value ('valuesOf')."""
    values = self.valuesOf(vessel, system)
    share = 1.0 - math.exp(-real / NEEDLE) if real > 0.0 else 0.0
    for k, (name, _) in enumerate(DIALS):
      want = dialShare(name, values[name])
      self.needles[k] += share * (want - self.needles[k])

  def _lampsLit(self, vessel: Vessel, system: SolarSystem,
                keeper: Timekeeper, guidance: AscentGuidance) -> None:
    """Lights the lamps (a relay's click each one changing): the engine
    burning, in the air, on the ground, warping, the guidance flying, in
    orbit."""
    body = system.bodies[vessel.anchor]
    air = body.air
    height = vessel.heightOver(system)
    inAir = air is not None and height < air.top
    conic = vessel.conicOf(system)
    top = air.top if air is not None else 0.0
    orbit = conic is not None and conic.closed and (
      conic.periapsis - body.radius) > top
    lit = {'ENGINE': vessel.engine.push > 0.0, 'AIR': inAir,
           'GROUND': vessel.touching > 0, 'WARP': keeper.factor > 1,
           'GUIDE': guidance.on, 'ORBIT': orbit, 'DOCK': vessel.docked}
    now = [lit[name] for name, _ in LAMPS]
    self.relays += sum(1 for a, b in zip(now, self.lamps) if a != b)
    self.lamps = now


def limitNotch(engine: object) -> int:
  """Returns the notch of the limiter's knob the engine's limit is on
  ('LIMITS', g: the nearest)."""
  gees = engine.most / (MASS * G0)
  return min(range(len(LIMITS)), key=lambda k: abs(LIMITS[k] - gees))
