"""
QuestsTest and QuestsWidgetTest are the base classes for the tests of
'worQt.engineering.quests': 'QuestsTest' subclasses 'BaseTest' for the
model, which needs no Qt; 'QuestsWidgetTest' subclasses 'WidgetTest'
for the window.

'play' runs a circuit frame by frame, as the window does, a goal
watching it, switches worked at the times given; 'switched' returns a
circuit with a switch set.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.engineering.circuits import Circuit, Run, Switch
from worQt.engineering.quests import Goal
from worQt.qtest import WidgetTest


def switched(circuit: Circuit, index: int, closed: bool) -> Circuit:
  """The 'switched' function returns 'circuit' with the switch of
  'index' closed or open."""
  part = circuit.parts[index]
  return circuit.withPart(index, Switch(part.first, part.second, closed))


def play(circuit: Circuit, goal: Goal, frame: float, seconds: float,
         *actions: tuple[float, int, bool]) -> Run:
  """The 'play' function runs 'circuit' for 'seconds' in frames of
  'frame' s, 'goal' watching it from the start and after each frame;
  each of 'actions', a time, a switch and whether it is closed, worked
  at the frame of its time; a test bench setting its inputs before each
  frame. It returns the run, stopping once the goal is reached."""
  run = Run(circuit)
  goal.update(run)
  steps = int(round(seconds / frame))
  for step in range(steps):
    changed = goal.drive(run)
    if changed is not None:
      run = Run(changed, run)
    for at, index, closed in actions:
      if abs(at - step * frame) < frame / 2:
        run = Run(switched(run.circuit, index, closed), run)
    run.advance(frame)
    goal.update(run)
    if goal.reached:
      break
  return run


class QuestsTest(BaseTest):
  """Base class for the tests of the quests' model."""


class QuestsWidgetTest(WidgetTest):
  """Base class for the tests of the quests' window."""
