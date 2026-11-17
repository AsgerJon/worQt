"""
Quest is Asger's way from the pad to Terra Prime's deck (user,
2026-11-17: "Here the quest begins: 1 Get into rocket by interacting
with controls in the walkway tunnel by the door. 2 Lock door from
inside 3 Dismiss the walkway 4 Eat food, chill out by sitting in sofa.
5 Read warning manual by going to warning panel ... 6 Get ready. Asger
sits in chair 7 (OPTIONAL) Set controls to rendezvouz with Terra Prime
(the big ass space station) 8 Launch! 9 Asger should stay seated to
avoid damage If Asger happens to approach Terra Prime, do either of:
11a activate auto docking 11b manual docking 12 use bolts to enter
Terra Prime docking 13 take the elevator"; the quest list on the screen
agreed): its steps (each its name, what it says, whether it may be
left out), which are done; a step is done whenever what it asks
happens ('ticked': the window watches). Numbered on from one (the list
skipped 10; the two ways to dock are one step). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  The steps: name, what it says, whether it may be left out.
STEPS = (
  ('aboard', 'Get into the rocket: the door\'s panel in the walkway',
   False),
  ('locked', 'Lock the door from inside', False),
  ('dismissed', 'Dismiss the walkway', False),
  ('rested', 'Eat a ration, chill out on the sofa', False),
  ('read', 'Read the warning manual by the door', False),
  ('seated', 'Get ready: sit in your chair', False),
  ('armed', 'Set the autopilot to ORBIT (J) and engage it (C)', True),
  ('launched', 'Launch! (Space: the red LAUNCH key)', False),
  ('orbit', 'Stay seated to avoid damage, into orbit', False),
  ('docked', 'At Terra Prime: the autopilot\'s RNDZ (H), then DOCK (N);'
   ' or dock by hand', False),
  ('hub', 'Use the bolts to get into Terra Prime', False),
  ('deck', 'Take the elevator down to the deck', False))
#  The parts of a step done once all of them are: eating and the sofa.
PARTS = {'ate': 'rested', 'lounged': 'rested'}
#  The LAUNCH key's checklist on the dashboard: the first eight steps as
#  a checklist says them (user, 2026-11-17: "the relevant items from teh
#  quests take diegetic shape in the form of a check list next it that
#  includes the first 8 items (the eat and chill being reworded to be
#  more formal on the checklist, whilst retaining the original relaxed
#  wording on the quest)"): each step's name and its line.
CHECKLIST = (('aboard', 'CREW ABOARD'), ('locked', 'HATCH LOCKED'),
             ('dismissed', 'WALKWAY RETRACTED'),
             ('rested', 'CREW FED AND RESTED'),
             ('read', 'SAFETY BRIEFING READ'),
             ('seated', 'PILOT SEATED, HARNESS ON'),
             ('armed', 'AUTOPILOT SET (OPTIONAL)'),
             ('launched', 'LAUNCH'))


class Quest:
  """
  Quest holds which steps are done ('done', their names) and which parts
  of steps ('parts'). 'ticked' marks one done; 'current' is the first
  step not done that may not be left out; 'rows' is the list as the
  screen shows it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('done', 'parts')

  #  Public Variables
  done: set
  parts: set

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.done, self.parts = set(), set()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def current(self, ) -> str | None:
    """The 'current' property is the first step not done that may not be
    left out (None: the quest is done)."""
    for name, _, optional in STEPS:
      if name not in self.done and not optional:
        return name
    return None

  @property
  def finished(self, ) -> bool:
    """The 'finished' property says whether every step is done that may
    not be left out."""
    return self.current is None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def ticked(self, name: str) -> bool:
    """The 'ticked' method marks step 'name' (or a part of one, 'PARTS')
    done; returns whether that finished a step not done before."""
    if name in PARTS:
      self.parts.add(name)
      step = PARTS[name]
      if any(PARTS[part] == step and part not in self.parts
             for part in PARTS):
        return False
      name = step
    if name not in {step for step, _, _ in STEPS}:
      raise KeyError('no quest step %r' % (name,))
    if name in self.done:
      return False
    self.done.add(name)
    return True

  def textOf(self, name: str) -> str:
    """The 'textOf' method returns what step 'name' says, numbered."""
    for k, (step, text, _) in enumerate(STEPS):
      if step == name:
        return '%d. %s' % (k + 1, text)
    raise KeyError('no quest step %r' % (name,))

  def rows(self, ) -> list:
    """The 'rows' method returns the list as the screen shows it: each
    step's text (numbered), whether it is done, whether it is the
    current one, whether it may be left out."""
    current = self.current
    return [{'text': self.textOf(name) + (' (optional)' if optional
                                          else ''),
             'done': name in self.done, 'current': name == current,
             'optional': optional} for name, _, optional in STEPS]
