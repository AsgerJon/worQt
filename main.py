"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from worQt.app import App
from worQt.ezword.gui import EZWordApp
from worQt.engineering.gui import DiskApp
from worQt.engineering.meso.gui import MesoApp
from worQt.engineering.lab.gui import LabApp
from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover, no mutate
  pass


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, App]
  for item in stuff:
    print(item)
  return 0


def ezWord(*args, ) -> int:
  """Opens EZWord and returns its exit code once its window closes."""
  with EZWordApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def diskApp(*args, ) -> int:
  """Opens the disk app and returns its exit code once its window
  closes."""
  with DiskApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def mesoApp(*args, ) -> int:
  """Opens the concrete testing app and returns its exit code once its
  window closes."""
  with MesoApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def labApp(*args, ) -> int:
  """Opens the beam lab and returns its exit code once its window
  closes."""
  with LabApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def pusherApp(*args, ) -> int:
  """Opens the coin pusher and returns its exit code once its window
  closes."""
  from worQt.gaming.pusher.gui import PusherApp
  with PusherApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def billiardsApp(*args, ) -> int:
  """Opens the billiard room, walking, both tables in it, and returns
  its exit code once its window closes."""
  from worQt.gaming.billiards.gui import BilliardsApp
  with BilliardsApp(*sys.argv) as app:
    app.window.show()
    app.window.startWalking()
  return app.returnCode


def kegleApp(*args, ) -> int:
  """Opens the billiard room, walking from its entrance, cue in hand,
  both tables in it (the user: not straight to kegler's lag), and
  returns its exit code once its window closes."""
  from worQt.gaming.billiards.gui import BilliardsApp
  with BilliardsApp(*sys.argv) as app:
    app.window.show()
    app.window.startWalking()
  return app.returnCode


#  The billiards' test modules, those of the shot streaming and the views
#  first.
BILLIARDS_TESTS = (
    'tests.test_gaming.test_billiards.test_recorder',
    'tests.test_gaming.test_billiards.test_shot_worker',
    'tests.test_gaming.test_billiards.test_literature',
    'tests.test_gaming.test_billiards.test_referee',
    'tests.test_gaming.test_billiards.run_billiards_window',
    'tests.test_gaming.test_billiards.test_carom_table',
    'tests.test_gaming.test_billiards.test_cloth',
    'tests.test_gaming.test_billiards.test_cushion',
    'tests.test_gaming.test_billiards.test_carom',
    'tests.test_gaming.test_billiards.test_cue',
    'tests.test_gaming.test_billiards.test_unfolded',
    'tests.test_gaming.test_billiards.test_trenches',
  'tests.test_gaming.test_billiards.test_room',
    'tests.test_gaming.test_billiards.test_sounds',
    'tests.test_gaming.test_billiards.test_hand_picture',
    'tests.test_gaming.test_billiards.test_match',
    'tests.test_gaming.test_billiards.test_room_light',
    'tests.test_gaming.test_billiards.test_table_shapes',
)


def billiardsTests(*args, ) -> int:
  """Runs the billiards' tests, each class in its own child process, and
  returns 0 when all passed, 1 otherwise; 'latest.log' has the record."""
  return runTests(*BILLIARDS_TESTS)


#  The tests of the cue as a cushion and of the unfolded map.
CUE_AND_MAP_TESTS = (
    'tests.test_gaming.test_billiards.test_cue',
    'tests.test_gaming.test_billiards.test_unfolded',
    'tests.test_gaming.test_billiards.test_sounds',
    'tests.test_gaming.test_billiards.test_referee',
    'tests.test_gaming.test_billiards.test_literature',
    'tests.test_gaming.test_billiards.run_billiards_window',
)


def cueAndMapTests(*args, ) -> int:
  """Runs the tests of the cue as a cushion and of the unfolded map, and
  returns 0 when all passed, 1 otherwise; 'latest.log' has the record."""
  return runTests(*CUE_AND_MAP_TESTS)


#  The tests of a ball spinning in place ending its phase and its shot.
SPIN_TESTS = (
    'tests.test_gaming.test_billiards.test_cloth',
    'tests.test_gaming.test_billiards.test_recorder',
)


def spinTests(*args, ) -> int:
  """Runs the tests of a ball spinning in place ending its phase and its
  shot, and returns 0 when all passed, 1 otherwise; 'latest.log' has the
  record."""
  return runTests(*SPIN_TESTS)


#  The tests of keglebillard, the second billiards game: its table, its
#  pins, the balls and pins moved together, its referee and its match,
#  as DDBU's rules have them.
KEGLE_TESTS = (
    'tests.test_gaming.test_billiards.test_kegle_table',
    'tests.test_gaming.test_billiards.test_kegle_pin',
    'tests.test_gaming.test_billiards.test_kegle_pins',
    'tests.test_gaming.test_billiards.test_kegle_motion',
    'tests.test_gaming.test_billiards.test_kegle_game',
    'tests.test_gaming.test_billiards.test_kegle_referee',
    'tests.test_gaming.test_billiards.test_kegle_match',
)


def kegleTests(*args, ) -> int:
  """Runs the tests of keglebillard's rules, and returns 0 when all
  passed, 1 otherwise; 'latest.log' has the record."""
  return runTests(*KEGLE_TESTS)


#  The engine's tests that today's changes touched: the faster hits, the
#  cushion's grip, the estimate's refit, the sounds, the pin's mesh.
ENGINE_TESTS = (
    'tests.test_gaming.test_billiards.test_carom',
    'tests.test_gaming.test_billiards.test_cushion',
    'tests.test_gaming.test_billiards.test_literature',
    'tests.test_gaming.test_billiards.test_referee',
    'tests.test_gaming.test_billiards.test_unfolded',
    'tests.test_gaming.test_billiards.test_table_shapes',
    'tests.test_gaming.test_billiards.test_sounds',
    'tests.test_gaming.test_billiards.test_shot_worker',
)


def quickTests(*args, ) -> int:
  """Runs keglebillard's tests, the spin tests and the engine's tests in
  one go, so 'latest.log', rewritten by every run, keeps them all; the
  window's slow run ('billiardsTests') apart. Returns 0 when all
  passed, 1 otherwise."""
  return runTests(*KEGLE_TESTS, *SPIN_TESTS, *ENGINE_TESTS)


def unfoldedShots(*args, ) -> int:
  """Paints the unfolded map offscreen to 'previews/unfolded-*.png', as
  'previews/shoot_unfolded.py' does, in a process of its own so its
  offscreen platform stays there, and returns its exit code."""
  import subprocess
  env = dict(os.environ, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE='1')
  path = os.path.join(here, 'previews', 'shoot_unfolded.py')
  return subprocess.run([sys.executable, path], env=env).returncode


def billiardsShots(*args, ) -> int:
  """Saves the 3D table from a few views to 'previews/billiards-*.png',
  as 'previews/shoot_billiards.py' does, and returns its exit code."""
  import importlib.util
  path = os.path.join(here, 'previews', 'shoot_billiards.py')
  spec = importlib.util.spec_from_file_location('shoot_billiards', path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module.main()


if __name__ == '__main__':
  yolo(quickTests, kegleApp, )
