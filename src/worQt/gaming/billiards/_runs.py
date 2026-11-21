"""
The billiards' runs for the user's 'yolo' (user, 2026-11-16: "when you
want me to run something they must be functions. Just give me a tuple
of the functions and i will put them in yolo myself"): each takes
nothing and returns an exit code, nought when all went well.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

#  The tests the billiards stand on, the window's last (it opens one).
BILLIARDS_TESTS = ('tests.test_gaming.test_billiards.test_carom_table',
                   'tests.test_gaming.test_billiards.test_cloth',
                   'tests.test_gaming.test_billiards.test_cushion',
                   'tests.test_gaming.test_billiards.test_carom',
                   'tests.test_gaming.test_billiards.test_cue',
                   'tests.test_gaming.test_billiards.test_recorder',
                   'tests.test_gaming.test_billiards.test_literature',
                   'tests.test_gaming.test_billiards.test_referee',
                   'tests.test_gaming.test_billiards.test_match',
                   'tests.test_gaming.test_billiards.test_shot_worker',
                   'tests.test_gaming.test_billiards.test_trails',
                   'tests.test_gaming.test_billiards.test_trenches',
                   'tests.test_gaming.test_billiards.test_unfolded',
                   'tests.test_gaming.test_billiards.test_table_shapes',
                   'tests.test_gaming.test_billiards.test_room',
                   'tests.test_gaming.test_billiards.test_room_light',
                   'tests.test_gaming.test_billiards.test_hand_picture',
                   'tests.test_gaming.test_billiards.test_sounds',
                   'tests.test_gaming.test_billiards.test_kegle_table',
                   'tests.test_gaming.test_billiards.test_kegle_pin',
                   'tests.test_gaming.test_billiards.test_kegle_pins',
                   'tests.test_gaming.test_billiards.test_kegle_motion',
                   'tests.test_gaming.test_billiards.test_kegle_referee',
                   'tests.test_gaming.test_billiards.test_kegle_match',
                   'tests.test_gaming.test_billiards.test_kegle_game',
                   'tests.test_gaming.test_billiards.test_phrasebook',
                   'tests.test_gaming.test_billiards.run_billiards_window')


def billiardsTests() -> int:
  """The 'billiardsTests' function runs the billiards' tests, each class
  in its own child process ('latest.log' has the record), the window's
  last, a window opening for it; nought when all passed."""
  from worQt.qtest import AppTestSuite
  return AppTestSuite().runNames(*BILLIARDS_TESTS)


def billiardsShow() -> int:
  """The 'billiardsShow' function opens the billiard room, walked first
  person (W A S D, the mouse looking), both tables in it: near one, E
  opens its menu, a game or the sandbox; at the table a right-button
  drag back strikes; in the language last chosen ('Language' in the
  menu bar). Returns the window's exit code once it closes."""
  from worQt.gaming.billiards.gui import BilliardsApp, savedLanguage
  with BilliardsApp(*sys.argv) as app:
    app.window.show()
    app.window.setLanguage(savedLanguage())
    app.window.enterRoom()
  return app.returnCode


def mainBilliards() -> int:
  """The 'mainBilliards' function opens the billiard room, no tests
  first ('billiardsTests' runs them), as 'mainSpace' does the space.
  Returns the window's exit code."""
  return billiardsShow()
