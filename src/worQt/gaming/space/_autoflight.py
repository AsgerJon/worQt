"""
Autoflight is the autopilot's three modes and whether it has the
controls (user, 2026-11-17: "Right now we have three modes of operation
that should be distinct: Orbit, Rendezvous and Docking. We don't need
the autopilot to do all three at once. Instead we should have the three
modes. Next we should have an indicator of the auto pilot being allowed
to have control, basically active/inactive"): ORBIT flies up to a round
orbit ('_ascentguidance'), RNDZ to Terra Prime ('_rendezvousguidance'),
DOCK into its port ('_dockingguidance'); each flies its leg and lets go,
the next chosen and engaged by hand. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._dockingguidance import REACH
from ._orrery import lengthText

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._ascentguidance import AscentGuidance
  from ._dockingguidance import DockingGuidance
  from ._dockingport import DockingPort
  from ._rendezvousguidance import RendezvousGuidance
  from ._solarsystem import SolarSystem
  from ._timekeeper import Timekeeper
  from ._vessel import Vessel

#  The modes, as their keys say them.
MODES = ('orbit', 'rendezvous', 'dock')
SAID = {'orbit': 'ORBIT', 'rendezvous': 'RNDZ', 'dock': 'DOCK'}


class Autoflight:
  """
  Autoflight holds the autopilot's 'mode' (one of 'MODES', ORBIT at
  first) and whether it has the controls ('engaged'), and each mode's
  guidance: 'ascent', 'rendezvous', 'docking' (the port's 'port').
  'chosen' picks a mode (engaged, the new one flies at once if it may,
  else it lets go); 'toggled' engages the mode or lets go; 'letGo' lets
  go (the controls taken); 'acted' flies the mode a frame on and lets go
  once it is done. Each returns what it says ('' nothing).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  mode: str
  engaged: bool
  ascent: AscentGuidance
  rendezvous: RendezvousGuidance
  docking: DockingGuidance
  port: DockingPort

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ascent: AscentGuidance,
               rendezvous: RendezvousGuidance, docking: DockingGuidance,
               port: DockingPort) -> None:
    self.ascent, self.rendezvous, self.docking = ascent, rendezvous, docking
    self.port, self.mode, self.engaged = port, 'orbit', False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def flying(self, ) -> object:
    """The 'flying' property is the chosen mode's guidance."""
    return {'orbit': self.ascent, 'rendezvous': self.rendezvous,
            'dock': self.docking}[self.mode]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def chosen(self, mode: str, vessel: Vessel, system: SolarSystem,
             keeper: Timekeeper) -> str:
    """The 'chosen' method picks 'mode'; engaged, the mode flying lets go
    and the new one flies if it may (else the autopilot lets go too)."""
    if mode not in MODES:
      raise KeyError('no autopilot mode %r' % mode)
    if mode == self.mode:
      return 'Autopilot mode %s (%s)' % (SAID[mode], 'engaged'
                                          if self.engaged else 'not engaged')
    if not self.engaged:
      self.mode = mode
      return 'Autopilot mode %s: C engages it' % SAID[mode]
    self._stopped(vessel)
    self.mode = mode
    why = self._begun(vessel, system, keeper)
    if why:
      self.engaged = False
      return 'Autopilot off: %s %s' % (SAID[mode], why)
    return 'Autopilot engaged: %s' % SAID[mode]

  def toggled(self, vessel: Vessel, system: SolarSystem,
              keeper: Timekeeper) -> str:
    """The 'toggled' method engages the chosen mode (if it may fly now)
    or lets go."""
    if self.engaged:
      self.letGo(vessel)
      return 'Autopilot off'
    why = self._begun(vessel, system, keeper)
    if why:
      return 'Autopilot not engaged: %s %s' % (SAID[self.mode], why)
    self.engaged = True
    return 'Autopilot engaged: %s' % SAID[self.mode]

  def letGo(self, vessel: Vessel) -> None:
    """The 'letGo' method lets go of the controls: the mode's guidance
    stops."""
    if self.engaged:
      self._stopped(vessel)
    self.engaged = False

  def acted(self, vessel: Vessel, system: SolarSystem, keeper: Timekeeper,
            reading: dict, seated: bool) -> str:
    """The 'acted' method flies the engaged mode a frame on ('reading':
    the nose to the port, 'DockingPort.readingOf', for DOCK; 'seated':
    Asger in his chair, ORBIT tops up only then); once it is done (or its
    guidance has stopped by itself) the autopilot lets go, said."""
    if not self.engaged:
      return ''
    if self.mode == 'orbit':
      self.ascent.acted(vessel, system, keeper, seated)
    elif self.mode == 'rendezvous':
      self.rendezvous.acted(vessel, system, keeper)
    elif not vessel.docked:
      self.docking.acted(vessel, self.port, reading, keeper.now)
    if self.mode == 'dock' and vessel.docked:
      self.docking.stopped(vessel)
    if self.flying.on:
      return ''
    self.engaged = False
    if self.mode == 'orbit' and self.ascent.phase == 'done':
      conic = vessel.conicOf(system)
      radius = system.bodies[vessel.anchor].radius
      return 'ORBIT done: %s x %s. Next: RNDZ (H), C engages' % (
        lengthText(conic.apoapsis - radius), lengthText(
          conic.periapsis - radius))
    if self.mode == 'rendezvous' and self.rendezvous.phase == 'done':
      self.rendezvous.phase = 'off'
      return 'RNDZ done: Terra Prime %s off. Next: DOCK (N), C engages' % (
        lengthText(reading['distance']))
    if self.mode == 'dock' and vessel.docked:
      return 'DOCK done: docked to Terra Prime'
    return 'Autopilot off: %s stopped' % SAID[self.mode]

  def inOrbit(self, vessel: Vessel, system: SolarSystem) -> bool:
    """The 'inOrbit' method says whether the vessel is in orbit round
    Terra Prime's planet: its path closed, its periapsis over the air."""
    if vessel.anchor != self.port.station.parent or vessel.touching:
      return False
    conic = vessel.conicOf(system)
    body = system.bodies[vessel.anchor]
    top = body.air.top if body.air is not None else 0.0
    return conic is not None and conic.closed and (
      conic.periapsis - body.radius > top)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _begun(self, vessel: Vessel, system: SolarSystem,
             keeper: Timekeeper) -> str:
    """Starts the chosen mode's guidance; returns why it cannot ('' it
    flies)."""
    if vessel.docked:
      return 'docked to Terra Prime (undock first)' if (
        self.mode != 'dock') else 'docked already'
    reading = self.port.readingOf(vessel, system, keeper.now)
    if self.mode == 'orbit':
      if self.inOrbit(vessel, system):
        return 'in orbit already'
      self.ascent.started(vessel, system)
      return ''
    if self.mode == 'rendezvous':
      if not self.inOrbit(vessel, system):
        return 'needs an orbit (ORBIT first)'
      if reading['distance'] <= REACH:
        return 'Terra Prime is %s off: DOCK (N)' % lengthText(
          reading['distance'])
      return self.rendezvous.started(vessel, system, keeper)
    return self.docking.started(vessel, self.port, reading, keeper.now)

  def _stopped(self, vessel: Vessel) -> None:
    """Stops the chosen mode's guidance."""
    if self.mode == 'orbit':
      self.ascent.stopped(vessel)
    elif self.mode == 'rendezvous':
      self.rendezvous.stopped(vessel)
    else:
      self.docking.stopped(vessel)
