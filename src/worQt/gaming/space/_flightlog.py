"""
FlightLog tells the teleprinter what the flight does (the spec: a line
every 10 s, and one on each event: lift-off, the engine, out of the air,
the orbit reached, touching down, the ascent guidance's phases).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._orrery import lengthText, timeText
from ._teleprinter import ICONS, WIDTH
from ._turns import dot, norm, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._teleprinter import Teleprinter
  from ._vessel import Vessel

#  A line of how it goes every so many s of real time (none while the
#  teleprinter is still typing).
EVERY = 10.0
#  The ascent guidance's phases as the log names them.
PHASES = {'climb': 'ASCENT: CLIMBING', 'turn': 'ASCENT: TURNING',
          'coast': 'ASCENT: COASTING', 'round': 'ASCENT: ROUNDING THE ORBIT',
          'done': 'ASCENT: DONE'}


class FlightLog:
  """
  FlightLog watches the flight each frame ('acted') and tells a
  'Teleprinter': a header first, a line of how it goes every 'EVERY' s,
  and each event as it happens (bells on the great ones). It keeps what
  it saw last: whether the vessel has left the ground ('flown'),
  touches it, is in the air, burns its engine, is in orbit, and the
  guidance's phase. Returns the events it saw, by name.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('since', 'seen', 'flown')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.since, self.seen, self.flown = 0.0, None, False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def acted(self, real: float, vessel: Vessel, system: SolarSystem,
            elapsed: float, phase: str, printer: Teleprinter,
            header: str) -> list:
    """The 'acted' method looks at the flight a frame on ('real' s of
    real time; 'elapsed' s of the game's; the guidance's 'phase') and
    tells 'printer'; the first time, 'header' first. Returns the events
    seen this frame: 'lift-off', 'engine on', 'engine cut', 'out of the
    air', 'back in the air', 'orbit', 'touchdown', 'phase'."""
    now = self._stateOf(vessel, system, phase)
    events = []
    if self.seen is None:
      printer.said(header, True)
      printer.said('-' * WIDTH)
      self.seen = now
      return events
    was = self.seen
    if not now['touching'] and was['touching'] and not self.flown:
      self.flown = True
      events.append('lift-off')
      printer.said('%s LIFT-OFF  %s' % (ICONS['rocket'],
                                        timeText(elapsed)), True)
    if now['burning'] != was['burning']:
      events.append('engine on' if now['burning'] else 'engine cut')
      printer.said('%s ENGINE %s  %s' % (
        ICONS['flame' if now['burning'] else 'stop'],
        'ON' if now['burning'] else 'CUT', lengthText(now['height'])))
    if now['inAir'] != was['inAir']:
      events.append('back in the air' if now['inAir'] else
                    'out of the air')
      printer.said('%s BACK IN THE AIR' % ICONS['down'] if now['inAir']
                   else '%s OUT OF THE AIR  %s' % (
        ICONS['globe'], lengthText(now['height'])), not now['inAir'])
    if now['orbit'] and not was['orbit']:
      events.append('orbit')
      printer.said('%s IN ORBIT  AP %s  PE %s' % (
        ICONS['flag'], lengthText(now['apo']), lengthText(now['peri'])),
        True)
    if now['touching'] and not was['touching'] and self.flown:
      events.append('touchdown')
      printer.said('%s TOUCHDOWN  %.1f M/S' % (ICONS['down'],
                                               now['falling']), True)
    if now['phase'] != was['phase'] and now['phase'] in PHASES:
      events.append('phase')
      printer.said('%s %s' % (ICONS['cog'], PHASES[now['phase']]))
    self.seen = now
    self.since += real
    if self.since >= EVERY and not printer.busy:
      self.since = 0.0
      printer.said('%s %s %s %s/S AP %s' % (
        ICONS['clock'], timeText(elapsed), lengthText(now['height']),
        lengthText(now['speed']), lengthText(now['apo'])))
    return events

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _stateOf(self, vessel: Vessel, system: SolarSystem,
               phase: str) -> dict:
    """Returns what the log watches of the flight now."""
    body = system.bodies[vessel.anchor]
    height = vessel.heightOver(system)
    air = body.air
    inAir = air is not None and height < air.top
    conic = vessel.conicOf(system)
    apo = conic.apoapsis - body.radius if conic and conic.closed else 0.0
    peri = conic.periapsis - body.radius if conic else -body.radius
    top = air.top if air is not None else 0.0
    ground = vessel.groundVelocity(system)
    return {'touching': vessel.touching > 0, 'height': height,
            'inAir': inAir, 'burning': vessel.engine.throttle > 0.0,
            'orbit': conic is not None and conic.closed and peri > top,
            'apo': apo, 'peri': peri,
            'speed': norm(ground if inAir else vessel.velocity),
            'falling': max(0.0, -dot(ground, unit(vessel.place))),
            'phase': phase}
