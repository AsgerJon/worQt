"""
The 'worQt.phys.rail' package is the lab's railway physics (user,
2026-11-15: "phys dedicated to rails"), built from the spec "Trains:
the math first": the track as a ribbon (a centre line and a frame
turning along it, 'Ribbon', from 'Piece's), the loop's stage in the
void ('loopTrack', 'loopStage'), a wheelset ('wheelsetBody',
'profileAt'), its axleboxes ('Axlebox': bearings, brakes, traction
motors), points ('Turnout') and the rail world rolling it all
('RailWorld'). In m, kg, N
and s, z up; float64; no Qt.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._piece import LEVEL, Piece, bend, eased, easedLoop, loop, straight
from ._ribbon import GRAVITY, Ribbon, turnOf
from ._stage import loopRails, loopSpan, loopStage, loopTrack
from ._stage import stageFinishes
from ._railworld import EXCHANGE, RAIL_STEP, RailWorld, wheelsetOn
from ._axlebox import JOURNAL_AT, PALMGREN, Axlebox, motorOf, palmgrenOf
from ._turnout import Turnout, wayOf
from ._wheelset import profileAt, wheelsetBody

__all__ = (
  'Axlebox',
  'Turnout',
  'EXCHANGE',
  'JOURNAL_AT',
  'PALMGREN',
  'palmgrenOf',
  'GRAVITY',
  'LEVEL',
  'Piece',
  'RAIL_STEP',
  'RailWorld',
  'Ribbon',
  'bend',
  'eased',
  'easedLoop',
  'loop',
  'loopRails',
  'loopSpan',
  'loopStage',
  'loopTrack',
  'motorOf',
  'profileAt',
  'stageFinishes',
  'straight',
  'turnOf',
  'wayOf',
  'wheelsetBody',
  'wheelsetOn',
)
