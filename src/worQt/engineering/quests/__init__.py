"""
The 'worQt.engineering.quests' package is a game of electric circuits:
a line of quests, each a circuit begun, its parts fixed, and a goal to
reach by adding parts already unlocked; reaching it unlocks more. It
needs no Qt; 'worQt.engineering.quests.gui' plays it.

- Goal, Glow, Toggles, Measures, Afterglow, OneWay, Touch, All: what a
  quest asks, each watching a circuit run; glowOf: how brightly a lamp
  or a light emitting diode glows.
- Tester, table, depthOf, levelOf: a test bench setting a circuit's
  logic inputs itself, step by step, and checking its probes; a truth
  table's steps; how many chips an output reads through; what a probe
  reads.
- Bench, bench, SuperQuest, SUPERS: the super quests' test benches and
  makings.
- Clocked, readOf, setOf: a goal ticking a computer's clock itself and
  noting what a probe reads; what a probe or a bus probe reads; an input
  or a bus input set.
- busBench, programmerBench, ComputerQuest, COMPUTERS, outputs,
  FIBONACCI, JUMPS, TIMES: the computer quests' benches of buses, their
  makings, what a program shows, and their programs.
- MICROS, COUNTDOWN, DIGIT: the microprocessor quests' makings, after
  Intel's 4004, and their programs.
- Quest, QUESTS, MAIN, SUPER, COMPUTER, MICRO, STARTING: the quests in
  their order, the first eight, the super quests, the computer quests
  and the microprocessor quests, and the parts a player has from the
  start.
- Progress: the quests done, the parts unlocked, kept in a file.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._goals import glowOf, Goal, Glow, Toggles, Measures, Afterglow
from ._goals import OneWay, Touch, All, Tester, table, depthOf, levelOf
from ._goals import Clocked, readOf, setOf
from ._super import Bench, bench, SuperQuest, SUPERS
from ._computer import busBench, programmerBench, ComputerQuest
from ._computer import COMPUTERS, outputs, FIBONACCI, JUMPS, TIMES
from ._micro import MICROS, COUNTDOWN, DIGIT
from ._quests import Quest, QUESTS, MAIN, SUPER, COMPUTER, MICRO
from ._quests import STARTING
from ._progress import Progress

__all__ = (
  'glowOf',
  'Goal',
  'Glow',
  'Toggles',
  'Measures',
  'Afterglow',
  'OneWay',
  'Touch',
  'All',
  'Tester',
  'table',
  'depthOf',
  'levelOf',
  'Clocked',
  'readOf',
  'setOf',
  'busBench',
  'programmerBench',
  'ComputerQuest',
  'COMPUTERS',
  'outputs',
  'FIBONACCI',
  'JUMPS',
  'TIMES',
  'MICROS',
  'COUNTDOWN',
  'DIGIT',
  'Bench',
  'bench',
  'SuperQuest',
  'SUPERS',
  'Quest',
  'QUESTS',
  'MAIN',
  'SUPER',
  'COMPUTER',
  'MICRO',
  'STARTING',
  'Progress',
)
