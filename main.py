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
#  The test windows main.py runs open without taking the focus (user,
#  2026-11-15: "do something so the window doesn't grab focus pls"):
#  shown unactivated, never focused; the children inherit it. Set it to
#  '0' to have them raised and activated.
os.environ.setdefault('QTEST_NO_FOCUS', '1')

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover, no mutate
  pass


def tester00(*args, ) -> int:
  """Hello World!"""
  from worQt.app import App
  stuff = ['hello world!', os, sys, frozenset, runTests, App]
  for item in stuff:
    print(item)
  return 0


def ezWord(*args, ) -> int:
  """Opens EZWord and returns its exit code once its window closes."""
  from worQt.ezword.gui import EZWordApp
  with EZWordApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def diskApp(*args, ) -> int:
  """Opens the disk app and returns its exit code once its window
  closes."""
  from worQt.engineering.gui import DiskApp
  with DiskApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def mesoApp(*args, ) -> int:
  """Opens the concrete testing app and returns its exit code once its
  window closes."""
  from worQt.engineering.meso.gui import MesoApp
  with MesoApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def labApp(*args, ) -> int:
  """Opens the beam lab and returns its exit code once its window
  closes."""
  from worQt.engineering.lab.gui import LabApp
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


PHYS_TESTS = (
    'tests.test_phys.test_vectors',
    'tests.test_phys.test_shape',
    'tests.test_phys.test_body',
    'tests.test_phys.test_world',
    'tests.test_phys.test_ground',
    'tests.test_phys.test_tie',
    'tests.test_phys.test_weld',
    'tests.test_phys.test_spring',
    'tests.test_phys.test_damper',
    'tests.test_phys.test_actuator',
    'tests.test_phys.test_books',
    'tests.test_phys.test_hexapod',
    'tests.test_phys.test_contact',
    'tests.test_phys.test_compiled',
    'tests.test_phys.test_tower',
    'tests.test_phys.test_sleep',
    'tests.test_phys.test_ball',
    'tests.test_phys.test_round_contact',
    'tests.test_phys.test_poke',
    'tests.test_phys.test_turned',
    'tests.test_phys.test_gears',
    'tests.test_phys.test_fixed',
    'tests.test_phys.test_parallel',
    'tests.test_phys.test_small_steps',
    'tests.test_phys.test_walking',
    'tests.test_phys.test_bearing',
    'tests.test_phys.test_tyre',
    'tests.test_phys.test_car',
    'tests.test_phys.test_terrain',
    'tests.test_phys.test_steering',
    'tests.test_phys.test_robot',
    'tests.test_phys.test_bench',
    'tests.test_phys.test_laps',
    'tests.test_phys.test_wall',
    'tests.test_phys.test_gearbox',
    'tests.test_phys.test_voice',
    'tests.test_phys.run_recorder',
    'tests.test_phys.run_view',
)


def physTests(*args, ) -> int:
  """Runs the tests of 'worQt.phys', the lab's own physics. Returns 0
  when all passed, 1 otherwise."""
  return runTests(*PHYS_TESTS)


#  The tests of the small steps and the softened bearing (2026-11-13).
NEW_PHYS_TESTS = (
    'tests.test_phys.test_small_steps',
    'tests.test_phys.test_bearing',
    'tests.test_phys.test_parallel',
    'tests.test_phys.test_turned',
    'tests.test_phys.test_walking',
    'tests.test_phys.test_carcass',
    'tests.test_phys.test_tyred',
    'tests.test_phys.test_brakes',
    'tests.test_phys.test_hinges',
    'tests.test_phys.test_shocks',
    'tests.test_phys.test_axle',
    'tests.test_phys.test_rig',
    'tests.test_phys.test_soapbox',
)

#  What today's solver changes touch (2026-11-14: the tyre rig, its
#  record-player steering; rams, humps, tyres on turntables, the
#  velocity pass's damping split among the rules that damp and run in
#  rounds, the shock's damper and stops eye to eye): the rig's own, the
#  benches the damping and shocks reach, the tyres', the small steps'.
RIG_TESTS = (
    'tests.test_phys.test_rig',
    'tests.test_phys.test_shocks',
    'tests.test_phys.test_hinges',
    'tests.test_phys.test_axle',
    'tests.test_phys.test_brakes',
    'tests.test_phys.test_tyred',
    'tests.test_phys.test_small_steps',
)


def rigTests(*args, ) -> int:
  """Runs the tests today's solver changes touch ('RIG_TESTS'; several
  minutes on the CPU, the rig's the longest). Returns 0 when all
  passed, 1 otherwise."""
  return runTests(*RIG_TESTS)


#  The tyre's slip law (2026-11-14, written before the law: tolerant, the
#  road textured) and the rig it is measured on.
TYRE_TESTS = (
    'tests.test_phys.test_tyre_slip',
    'tests.test_phys.test_rig',
)


def tyreTests(*args, ) -> int:
  """Runs the tyre's slip law's tests and the tyre rig's ('TYRE_TESTS';
  several minutes on the CPU). Returns 0 when all passed, 1 otherwise."""
  return runTests(*TYRE_TESTS)


#  The soapbox (2026-11-14: the first new car, a gravity racer down a
#  ramp and round a loop) and what its new touch reaches: tyres on a
#  track's planks ('WHEEL_PIECES'), a chassis' one-way contact; the
#  tyres', the rig's and the small steps' besides.
SOAPBOX_TESTS = (
    'tests.test_phys.test_soapbox',
    'tests.test_phys.test_tyred',
    'tests.test_phys.test_rig',
    'tests.test_phys.test_small_steps',
)


def soapboxTests(*args, ) -> int:
  """Runs the soapbox's tests and those its touch reaches
  ('SOAPBOX_TESTS'; several minutes on the CPU, the soapbox's loop the
  longest). Returns 0 when all passed, 1 otherwise."""
  return runTests(*SOAPBOX_TESTS)


#  The drivetrain (2026-11-14 night: the differential, the dog-leg stick
#  shift gearbox and the clutch, on a bench) and what its solver change
#  reaches: gears meshing and every disc brake now held one after
#  another in the drivetrain's sweep, the brakes' grip remembered (every
#  brake's: the soapbox's, the rig's, the benches').
DRIVETRAIN_TESTS = (
    'tests.test_phys.test_drivetrain',
    'tests.test_phys.test_brakes',
    'tests.test_phys.test_soapbox',
    'tests.test_phys.test_rig',
    'tests.test_phys.test_axle',
    'tests.test_phys.test_tyred',
    'tests.test_phys.test_tyre_slip',
    'tests.test_phys.test_shocks',
    'tests.test_phys.test_hinges',
    'tests.test_phys.test_small_steps',
)

#  The real car (2026-11-14 night) and what building it changed: the
#  drivetrain split into 'addDrivetrain' (its crown wheel moved to the
#  other side of its pinion: first gear drove backward), the soapbox's
#  corners into 'addCorners'/'addSteering', 'Housed' bodies, the
#  drivetrain's sweep stopping early, a column's length.
REALCAR_TESTS = (
    'tests.test_phys.test_realcar',
    'tests.test_phys.test_drivetrain',
    'tests.test_phys.test_soapbox',
    'tests.test_phys.test_axle',
    'tests.test_phys.test_rig',
    'tests.test_phys.test_small_steps',
)

#  Warp time (2026-11-14 evening): the drivetrain solved exactly on a
#  warp's lanes (every disc brake with it), each mesh's slip counted
#  itself (float32 lost its two gears' angles), ground touches too high
#  to reach not looked for: every test on the small steps.
WARP_TESTS = (
    'tests.test_phys.test_realcar',
    'tests.test_phys.test_drivetrain',
    'tests.test_phys.test_brakes',
    'tests.test_phys.test_soapbox',
    'tests.test_phys.test_rig',
    'tests.test_phys.test_axle',
    'tests.test_phys.test_tyred',
    'tests.test_phys.test_tyre_slip',
    'tests.test_phys.test_carcass',
    'tests.test_phys.test_shocks',
    'tests.test_phys.test_hinges',
    'tests.test_phys.test_small_steps',
)


def warpTests(*args, ) -> int:
  """Runs every test on the small steps ('WARP_TESTS'; five minutes or
  so on the CPU, the user's run of 2026-11-14 evening). Returns 0 when
  all passed, 1 otherwise."""
  return runTests(*WARP_TESTS)


#  Before the show (user, 2026-11-14: "we do tests, lots of tests,
#  before we start the show", then "make sure main.py does not run shit
#  we don't need"): what the show stands on, nothing else: the small
#  steps' tests, the walk window's keys in the real car (on the GPU where
#  there is one) and the readings' dock window. The rest of the phys
#  suite: 'physTests'.
SHOW_TESTS = WARP_TESTS + ('tests.test_phys.test_realoval',
                           'tests.test_phys.test_city',
                           'tests.test_phys.test_car_geometry',
                           'tests.test_phys.run_walk_keys',
                           'tests.test_phys.run_readings',
                           'tests.test_phys.run_oval',
                           'tests.test_phys.run_city')


def showTests(*args, ) -> int:
  """Runs 'SHOW_TESTS' (five minutes or so). Returns 0 when all passed,
  1 otherwise."""
  return runTests(*SHOW_TESTS)


#  The GPU being made ready for the show, beside the tests
#  ('preloadGpu'): the thread doing it.
_PRELOAD = []


def preloadGpu(*args, ) -> int:
  """Starts making the GPU ready for the show in a thread of its own,
  beside whatever runs next (user, 2026-11-14: "make a preload function
  that prepares the GPU ahead of time. So the show doesn't hang for a
  minute at the beginning building gpu stuff"): the small steps'
  kernels compiled for the GPU (or loaded from Warp's cache) at every
  block size the walk window launches them at, then the V12's voice's
  on the CPU; each printed with its time once done ('[preload]'). The
  show waits for it ('_preloadWaited'). Returns 0."""
  import threading
  import time

  def ready() -> None:
    """Compiles or loads the kernels, saying what and how long."""
    began = time.perf_counter()
    try:
      from worQt.phys._compiled import gpuDevice
      from worQt.phys._enginesim import preloaded as voiceReady
      from worQt.phys._small_steps import preloaded
      device = gpuDevice() or 'cpu'
      print('[preload] the small steps\' kernels for %s: a minute or two '
            'after a change, seconds from Warp\'s cache' % device,
            flush=True)
      preloaded(device)
      print('[preload] the small steps\' kernels ready on %s (%.0f s)' % (
          device, time.perf_counter() - began), flush=True)
      voiceReady()
      print('[preload] the V12\'s voice ready (%.0f s)' % (
          time.perf_counter() - began), flush=True)
      from worQt.phys._realoval import ovalGround, parkedCar
      ovalGround()
      parkedCar()
      print('[preload] the oval and the old car parked on it ready (%.0f '
            's)' % (time.perf_counter() - began), flush=True)
      import os
      from worQt.phys._city import CITY_TRACK, cityCourse, cityGround
      if os.path.isfile(os.path.normpath(CITY_TRACK)):
        cityGround()
        cityCourse()
        print('[preload] the city lap ready (%.0f s)' % (
            time.perf_counter() - began), flush=True)
    except Exception as error:
      print('[preload] failed: %s: %s' % (type(error).__name__, error),
            flush=True)

  thread = threading.Thread(target=ready, daemon=True)
  thread.start()
  _PRELOAD.append(thread)
  return 0


def gpuDiagnosis(*args, ) -> int:
  """Finds where the walk window's time goes on the GPU (2026-11-15: the
  window 71 % of real time on the RTX 5060, the CPU 100 %): the step part
  by part ('gpuProfile'), then the walk window at the real car (driven
  off in first, its screen shown) timed call by call for eight seconds:
  the kernel (its launch to its states read back), the Python round it,
  the window's tick, the frames the view drew, the kernel's time a step;
  at the window's 0.2 ms lock switch ('SWITCH_INTERVAL'), drawn as it
  is now (phys.qml's 'aaSamples' 2 and 'shadows' 2; its 'glass' as the
  view decides: none while nothing drawn is see-through), at the real
  car, then in town (the city driver driving), then in town with the
  3D view hidden. The drawing shares the GPU with the physics, taking
  turns (2026-11-15, the real car's kernel: 116 us a step drawn at 4 2
  3, 98 at 2 1 2 or 1 0 1, 86 hidden, 67 headless; in town 129, 125,
  108-119, 91 hidden, 71-75 headless; the ground casting no shadows
  made no odds). A few minutes; prints as
  it goes, into previews/gpu-diagnosis.log as well (for me to read).
  Returns 0."""
  terminal = sys.stdout
  log = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'previews', 'gpu-diagnosis.log'), 'w')

  class Both:
    """Writes to the terminal and the log alike."""

    def write(self, text: str) -> int:
      """Writes 'text' to both, at once."""
      terminal.write(text)
      log.write(text)
      log.flush()
      return len(text)

    def flush(self, ) -> None:
      """Flushes both."""
      terminal.flush()
      log.flush()

  sys.stdout = Both()
  try:
    return _gpuDiagnosed()
  finally:
    sys.stdout = terminal
    log.close()


def _gpuDiagnosed() -> int:
  """Runs 'gpuDiagnosis' (its output as it finds it). Returns 0."""
  import threading
  import time
  from collections import defaultdict
  gpuProfile()
  _preloadWaited()
  from PySide6.QtCore import QEvent, Qt, QTimer
  from PySide6.QtGui import QKeyEvent
  from worQt.phys import _small_steps as ss
  from worQt.phys import norm
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui import _walk
  from worQt.phys.gui._walk import PLACES, WalkWindow
  spent, calls, lock = defaultdict(float), defaultdict(int), threading.Lock()

  def timed(owner: object, name: str, label: str) -> None:
    """Wraps 'owner.name' to add its time under 'label'."""
    inner = getattr(owner, name)

    def wrapper(*inputs):
      began = time.perf_counter()
      try:
        return inner(*inputs)
      finally:
        with lock:
          spent[label] += time.perf_counter() - began
          calls[label] += 1

    setattr(owner, name, wrapper)

  timed(WalkWindow, 'tick', 'gui tick')
  timed(WalkWindow, '_step', 'physics call')
  timed(ss.SmallSteps, 'advancedAll', '  advancedAll')
  timed(ss._Packed, 'states', '    states (waits for the GPU)')
  timed(ss._Packed, 'drive', '    drive (copies in)')
  timed(ss._Packed, 'load', '    load')
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The real car'))
    window.reset()
    window.resize(1600, 900)
    window.show()
    state = {'phase': 0, 'began': time.perf_counter(), 'mark': None,
             'frames': 0}
    settings = ('aaSamples', 'shadows')
    passes = (('The real car', 'drawn as it is', (2, 2)),
              ('Copenhagen', 'drawn as it is', (2, 2)),
              ('Copenhagen', 'the view hidden', None))

    def drawn() -> None:
      """Counts a frame the view drew."""
      state['frames'] += 1

    window.view.quick.frameSwapped.connect(drawn)
    plan = [(0.0, Qt.Key.Key_0, True, True),
            (1.0, Qt.Key.Key_1, True, True),
            (2.0, Qt.Key.Key_1, False, True),
            (2.1, Qt.Key.Key_W, True, False),
            (2.5, Qt.Key.Key_0, False, True)]

    def key(code: object, held: bool, pad: bool) -> None:
      """Sends a key to the view as the system does."""
      kind = QEvent.Type.KeyPress if held else QEvent.Type.KeyRelease
      mods = Qt.KeyboardModifier.KeypadModifier if pad else (
          Qt.KeyboardModifier.NoModifier)
      app.sendEvent(window.view.quick, QKeyEvent(kind, code, mods))

    def poll() -> None:
      """Drives, then times each run of eight seconds and reports."""
      now = time.perf_counter()
      if window.failed is not None:
        print('FAILED', window.failed, flush=True)
        app.quit()
        return
      if window.clock < 1.0:
        state['began'] = now
        return
      passed = now - state['began']
      while plan and state['phase'] == 0 and passed >= plan[0][0]:
        key(*plan.pop(0)[1:])
      if state['mark'] is None and passed > 4.0:
        sys.setswitchinterval(_walk.SWITCH_INTERVAL)
        root, levels = window.view.quick.rootObject(), passes[
          state['phase']][2]
        if levels is None:
          window.view.box.hide()
        else:
          for name, level in zip(settings, levels):
            root.setProperty(name, level)
        with lock:
          spent.clear()
          calls.clear()
        state['mark'] = (now, window.clock)
        state['frames'] = 0
      if state['mark'] is not None and now - state['mark'][0] > 8.0:
        wall = now - state['mark'][0]
        sim = window.clock - state['mark'][1]
        waited = spent['    states (waits for the GPU)']
        print('%s, %s (glass %s): %.0f %% of real time, %.1f m/s, '
              '%.0f frames drawn a second, the kernel %.0f us a step' % (
                passes[state['phase']][0], passes[state['phase']][1],
                window.view.quick.rootObject().property('glass'),
                100.0 * sim / wall, norm(window.states[
                  _walk._realcar.CHASSIS].velocity), state['frames'] / wall,
                1e6 * waited * window.place.small / max(sim, 1e-9)),
              flush=True)
        with lock:
          for label in sorted(spent):
            print('  %-30s %6d calls %7.2f ms a call %5.1f %% of wall' % (
                label, calls[label], 1000.0 * spent[label] / calls[label],
                100.0 * spent[label] / wall), flush=True)
        state['phase'] += 1
        state['mark'] = None
        state['began'] = now - 4.0
        if state['phase'] == len(passes):
          window.close()
          app.quit()
        elif passes[state['phase']][0] != window.place.name:
          key(Qt.Key.Key_W, False, False)
          names = [place.name for place in PLACES]
          window.placeBox.setCurrentIndex(names.index(
            passes[state['phase']][0]))
          window.reset()

    timer = QTimer()
    timer.timeout.connect(poll)
    timer.start(50)
  return 0


def gpuProfile(*args, ) -> int:
  """Times the real car's steps on the GPU (the CPU if there is none)
  as the walk window steps them, in one block, part by part, by the
  device's own clock ('SmallSteps.profileOf'; user, 2026-11-14: "the
  physics are still tooo slow"): on the yard, its engine idling a
  second, then driven off in first, two seconds of its own time timed;
  and in town (the square, the CRG road's terrain), the city driver
  driving it, three seconds, then two timed. ('Whole GPU', the steps
  spread over the GPU, took twice as long a step each time: 122-125 us
  against 67-69, so it is not timed now.) A minute or two (after
  'preloadGpu' is done). Returns 0."""
  import time
  _preloadWaited()
  from worQt.phys import BrakeLine, FourthWall, SmallSteps
  from worQt.phys._compiled import gpuDevice
  from worQt.phys._drivetrain import DrivetrainControls, drivetrainWorked
  from worQt.phys._realcar import Antilock, CORNERS, RealCarControls
  from worQt.phys._realcar import realCar
  from worQt.phys._realdriver import CityDriver
  from worQt.phys._rig import TuneUp, WheelSetup
  from worQt.phys._small_steps import THREADS, preloaded
  from worQt.phys._hinges import HINGE_GREASE
  from worQt.phys.gui._walk import RIG_STEP
  from worQt.phys._carcass import TYRE_YARD
  from worQt.phys._city import CITY_TRACK, cityCourse, cityGround
  from worQt.phys._city import realCarInCity
  device = gpuDevice() or 'cpu'
  print('the real car on %s: loading its kernels' % device, flush=True)
  preloaded(device)
  frame = 1.0 / 60.0
  scenes = ('the yard', 'town') if os.path.isfile(os.path.normpath(
    CITY_TRACK)) else ('the yard',)
  for scene in scenes:
    controls = RealCarControls(BrakeLine(0.0), FourthWall(0.0), TuneUp(
        (WheelSetup(),) * len(CORNERS)), DrivetrainControls(), Antilock())
    if scene == 'town':
      assembly, states = realCarInCity(controls)
      ground = cityGround()
      driver = CityDriver(assembly, controls, cityCourse())
    else:
      assembly, states = realCar(controls)
      ground, driver = TYRE_YARD, None
    world = SmallSteps((0.0, 0.0, -9.81), ground, RIG_STEP, 1,
                       HINGE_GREASE, device, THREADS, False, 0.0, 0.05, 0,
                       True)
    clock = 0.0

    def ran(seconds: float) -> float:
      """Steps the car 'seconds' of its own time (the city driver
      driving, in town); returns the wall clock's seconds it took."""
      nonlocal states, clock
      began = time.perf_counter()
      for _ in range(round(seconds / frame)):
        if driver is not None:
          driver.take(states, frame)
        drivetrainWorked(controls.drive, states, frame)
        controls.brakes.worked(controls.line.pressure, assembly, states,
                               frame)
        states = world.advancedAll(assembly, states, frame, clock)
        clock += frame
      return time.perf_counter() - began

    print('  %s: warming up' % scene, flush=True)
    if driver is None:
      ran(1.0)
      drive = controls.drive
      drive.pedal, drive.asked = 1.0, '1'
      ran(0.6)
      drive.throttle = 0.5
      ran(0.4)
      drive.pedal = 0.0
    else:
      ran(3.0)
    world.profileOf(assembly)
    print('  %s: driving two seconds' % scene, flush=True)
    took = ran(2.0)
    steps = 2.0 / RIG_STEP
    print('  %s, one block: %.0f us a step, %.0f %% of real time' % (
        scene, 1e6 * took / steps, 100.0 * 2.0 / took), flush=True)
    parts = world.profileOf(assembly)
    total = max(1, sum(parts.values()))
    for name, cycles in parts.items():
      if cycles > 0:
        print('    %-18s %5.1f %%  %6.1f us a step' % (
            name,
            100.0 * cycles / total,
            1e6 * took / steps * cycles / total))
  return 0


def _preloadWaited() -> None:
  """Waits for 'preloadGpu' to be done, if it was started, saying how
  long it has waited every ten seconds."""
  import time
  began = time.perf_counter()
  for thread in _PRELOAD:
    while thread.is_alive():
      thread.join(10.0)
      if thread.is_alive():
        print('[preload] the show waits for the GPU (%.0f s)' % (
            time.perf_counter() - began), flush=True)


def realCarTests(*args, ) -> int:
  """Runs the real car's tests and those its building touched
  ('REALCAR_TESTS'; several minutes on the CPU). Returns 0 when all
  passed, 1 otherwise."""
  return runTests(*REALCAR_TESTS)


def drivetrainTests(*args, ) -> int:
  """Runs the drivetrain's tests and those its solver change reaches
  ('DRIVETRAIN_TESTS'; ten minutes or so on the CPU). Returns 0 when all
  passed, 1 otherwise."""
  return runTests(*DRIVETRAIN_TESTS)


def newPhysTests(*args, ) -> int:
  """Runs the small steps', the bearing's, the side by side steps' and
  the tyres' tests ('NEW_PHYS_TESTS'; the cord tyre's about a minute on
  the CPU). Returns 0 when all passed, 1 otherwise."""
  return runTests(*NEW_PHYS_TESTS)


#  The qtest harness's own test modules: what worktoy 1.2.0's 'TestMeta'
#  (doCleanups and debug kept for the library) changed in worQt.qtest.
QTEST_TESTS = (
    'tests.test_qtest.test_meta_test',
    'tests.test_qtest.test_space_test',
    'tests.test_qtest.test_app_test',
    'tests.test_qtest.test_app_test_suite',
    'tests.test_qtest.test_app_test_run',
    'tests.test_qtest.run_app_test_internals',
)


def qtestTests(*args, ) -> int:
  """Runs the tests of 'worQt.qtest', the harness itself. Returns 0 when
  all passed, 1 otherwise."""
  return runTests(*QTEST_TESTS)


def physAndQtestTests(*args, ) -> int:
  """Runs the tests of 'worQt.phys' and of 'worQt.qtest' together (the
  work of 2026-11-12: the walk, the bearing, worktoy 1.2.0). Returns 0
  when all passed, 1 otherwise."""
  return runTests(*PHYS_TESTS, *QTEST_TESTS)


def towerShow(*args, ) -> int:
  """Opens the tower on the hexapod, live: hold, heave, surge or roll
  the platform. Returns the exit code once its window closes."""
  from worQt.phys.gui import PhysApp
  with PhysApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def ballsShow(*args, ) -> int:
  """Opens steel balls on the ground with an oak prism launched across
  them: click a ball or the prism to push it. Returns the exit code
  once its window closes."""
  from worQt.phys.gui import BallsApp
  with BallsApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def ringShow(*args, ) -> int:
  """Opens the giant hjulleje's outer ring standing upright with balls
  in its groove: click a ball to push it along. Returns the exit code
  once its window closes."""
  from worQt.phys.gui import RingApp
  with RingApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def gpuBench(*args, ) -> int:
  """Times the bearing's world (its motor on, 0.1 s) stepped on the CPU
  (one thread, the reference) and on the GPU (256 threads side by side,
  where Warp finds one), and says how far apart they end; shows what it
  is doing as it goes: each phase with its expected time, a heartbeat
  every 5 s while a kernel compiles (the first run after a change: the
  CPU's ~15-30 s, the GPU's ~1-2 min), the simulated time as it runs.
  Everything it and Warp print, what Warp finds (devices, CUDA, its
  driver), any error with its traceback, and a hard crash's (Python's
  'faulthandler') go into 'previews/gpu-bench.log' too (written anew
  each run, flushed line by line). Returns 0, or 1 on an error."""
  import faulthandler
  import math
  import platform
  import threading
  import time
  import traceback
  os.makedirs('previews', exist_ok=True)
  log = open(os.path.join('previews', 'gpu-bench.log'), 'w', buffering=1)
  faulthandler.enable(log)
  began = time.perf_counter()

  class Tee:
    """Writes to the terminal and to the log alike."""

    def __init__(self, stream: object) -> None:
      self.stream = stream

    def write(self, text: str) -> int:
      self.stream.write(text)
      log.write(text)
      return len(text)

    def flush(self, ) -> None:
      self.stream.flush()
      log.flush()

  terminal, errors = sys.stdout, sys.stderr
  sys.stdout, sys.stderr = Tee(terminal), Tee(errors)

  def said(text: str) -> None:
    """Prints 'text' with the time since the start."""
    print('[%6.1f s] %s' % (time.perf_counter() - began, text), flush=True)

  try:
    said('gpuBench %s, Python %s on %s' % (
        time.strftime('%Y-%m-%d %H:%M:%S'), platform.python_version(),
        platform.platform()))
    said('importing warp and the physics')
    import warp as wp
    from worQt.phys import World, groundAt, minus, norm, runMotor
    from worQt.phys import walkingBearing
    from worQt.phys._compiled import _kernelsOf, gpuDevice
    from worQt.phys._scenes import BEARING_FIDELITY, MOTOR_FREE
    from worQt.phys._scenes import MOTOR_STALL
    said('warp %s initialising' % wp.__version__)
    _kernelsOf()
    said('cuda available: %s; cuda devices: %s; devices: %s' % (
        wp.is_cuda_available(), wp.get_cuda_device_count(),
        [str(device) for device in wp.get_devices()]))
    for device in wp.get_cuda_devices():
      said('  %s: %s, sm_%s' % (device, device.name, device.arch))
    shrunk, step, steps = 0.032 / 1.75, 0.002, 50

    def compiled(device: str, expected: str) -> None:
      """Compiles (or loads, if cached) the world's kernel for 'device',
      saying so every 5 s meanwhile."""
      said('compiling the world kernel for %s (cached: a moment; after '
           'a change: %s)' % (device, expected))
      done = threading.Event()

      def beat() -> None:
        """Says the compile still runs, every 5 s."""
        while not done.wait(5.0):
          said('  still compiling for %s ...' % device)

      threading.Thread(target=beat, daemon=True).start()
      start = time.perf_counter()
      try:
        wp.load_module(_kernelsOf(), 'cpu' if device.startswith('cpu')
        else device)
      finally:
        done.set()
      said('  compiled for %s in %.1f s' % (device,
                                            time.perf_counter() - start))

    def timed(device: str) -> tuple:
      """Returns the bearing after 0.1 s on 'device', and the computing
      a simulated second took, s, saying how far it has got."""
      world = World((0.0, 0.0, -9.81), 1e-3, groundAt(shrunk), None,
                    True, None, device, BEARING_FIDELITY)
      assembly, states = walkingBearing(shrunk)
      runMotor(assembly.motors[0].drive, MOTOR_STALL, MOTOR_FREE, True)
      said('%s: packing the bearing and a first step' % device)
      states = world.advancedAll(assembly, states, step, 0.0)
      said('%s: running 0.1 s of the bearing (the cpu ~1-2 s)' % device)
      start = time.perf_counter()
      for k in range(steps):
        states = world.advancedAll(assembly, states, step,
                                   step * (k + 1))
        if (k + 1) % 10 == 0:
          said('  %s: %.3f s of 0.100 s simulated' % (device,
                                                      step * (k + 1)))
      return states, (time.perf_counter() - start) / (steps * step)

    def parted(device: str) -> None:
      """Times a step of the bearing on the CPU and on 'device', all of
      it and with parts left out (the rules: ties and rods; the
      contacts; both), at the whole bearing's step, so where the
      GPU's time goes shows."""
      from worQt.phys._assembly import Actuator, Assembly, Contact, Tie
      from worQt.phys._world import _CONTACT_SHARE, _contactBoundOf
      assembly, states = walkingBearing(shrunk)
      runMotor(assembly.motors[0].drive, MOTOR_STALL, MOTOR_FREE, True)
      world = World((0.0, 0.0, -9.81), 1e-3, groundAt(shrunk), None,
                    True, None, 'cpu', BEARING_FIDELITY)
      quick = _contactBoundOf(world, assembly, states)
      h = 1e-3 / math.ceil(1e-3 * quick / (_CONTACT_SHARE * 2.0))
      said('where a step goes (each step %.2f us; 10 calls of 2 ms):'
           % (1e6 * h))
      kept = assembly.connections
      for name, connections in (
            ('all', kept),
            ('no rules', tuple(c for c in kept
                               if not isinstance(c, (Actuator, Tie)))),
            ('no contacts', tuple(c for c in kept
                                  if not isinstance(c, Contact))),
            ('neither', tuple(c for c in kept
                              if not isinstance(c, (Actuator, Tie,
                                                    Contact))))):
        part = Assembly(assembly.bodies, connections)
        costs = []
        for where in ('cpu', device):
          fixed = World((0.0, 0.0, -9.81), h, groundAt(shrunk), None,
                        True, None, where, BEARING_FIDELITY)
          moved = fixed.advancedAll(part, states, step, 0.0)
          start = time.perf_counter()
          for k in range(10):
            moved = fixed.advancedAll(part, moved, step, step * (k + 1))
          costs.append(1e6 * (time.perf_counter() - start)
                       / (10 * step / h))
        said('  %-12s cpu %8.1f us a step   %s %8.1f us a step'
             % (name, costs[0], device, costs[1]))

    def drifting(device: str) -> None:
      """Says how far apart the CPU's and the GPU's bearings drift as
      they run: from the last bits (a hair, growing as stiff contacts
      grow it) or at once (a fault)."""
      said('how far apart, as they run:')
      worlds = [World((0.0, 0.0, -9.81), 1e-3, groundAt(shrunk), None,
                      True, None, where, BEARING_FIDELITY)
                for where in ('cpu', device)]
      runs = []
      for world in worlds:
        assembly, states = walkingBearing(shrunk)
        runMotor(assembly.motors[0].drive, MOTOR_STALL, MOTOR_FREE,
                 True)
        runs.append([world, assembly, states])
      for k in range(25):
        for run in runs:
          run[2] = run[0].advancedAll(run[1], run[2], step, step * k)
        if k in (0, 1, 2, 4, 9, 24):
          apart = max(norm(minus(one.place, two.place))
                      for one, two in zip(runs[0][2], runs[1][2]))
          worst = max(range(len(runs[0][2])), key=lambda i: norm(minus(
              runs[0][2][i].place, runs[1][2][i].place)))
          said('  after %.3f s: %.3e m (body %d)'
               % (step * (k + 1), apart, worst))

    device = gpuDevice() or 'cpu'
    said('gpu here: %s' % device)
    compiled('cpu', '~15-30 s')
    cpu, cpuCost = timed('cpu')
    said('cpu: %.2f s of computing a simulated second' % cpuCost)
    if device != 'cpu':
      compiled(device, '~1-2 min')
      gpu, gpuCost = timed(device)
      apart = max(norm(minus(one.place, two.place))
                  for one, two in zip(cpu, gpu))
      said('%s: %.2f s of computing a simulated second (%.1f x the cpu)'
           % (device, gpuCost, cpuCost / gpuCost))
      said('farthest apart after 0.1 s: %.3e m' % apart)
      parted(device)
      drifting(device)
    said('done')
    return 0
  except BaseException:
    said('FAILED:\n%s' % traceback.format_exc())
    return 1
  finally:
    sys.stdout, sys.stderr = terminal, errors
    faulthandler.disable()
    log.close()


def smallStepsBench(*args, ) -> int:
  """Times the small steps ('SmallSteps': touches kept as rules, all at
  once, float32) against today's springs ('World', compiled, on the
  CPU) on the three proofs: the steel ball in its groove (1 s), rolling
  down its ramp (0.5 s), the tower of five twisted oak blocks (2 s);
  the small steps on the CPU (one thread) and on the GPU (256 threads
  in one block), where Warp finds one. For each: the computing a
  simulated second takes, and how right it came out (the ball's creep,
  the ramp's way against rolling's 5/7 g sin a, the tower's sink and
  turn). Shows each phase as it goes, its expected time, a heartbeat
  every 5 s while a kernel compiles (the first run after a change: the
  springs' CPU kernel ~15-30 s, the small steps' a few seconds on the
  CPU, up to a minute or two on the GPU), the simulated time as it
  runs; everything goes into 'previews/small-steps-bench.log' too.
  Returns 0, or 1 on an error."""
  import faulthandler
  import math
  import platform
  import threading
  import time
  import traceback
  os.makedirs('previews', 0o777, True)
  log = open(os.path.join('previews', 'small-steps-bench.log'), 'w', 1)
  faulthandler.enable(log)
  began = time.perf_counter()

  class Tee:
    """Writes to the terminal and to the log alike."""

    def __init__(self, stream: object) -> None:
      self.stream = stream

    def write(self, text: str) -> int:
      self.stream.write(text)
      log.write(text)
      return len(text)

    def flush(self, ) -> None:
      self.stream.flush()
      log.flush()

  terminal, errors = sys.stdout, sys.stderr
  sys.stdout, sys.stderr = Tee(terminal), Tee(errors)

  def said(text: str) -> None:
    """Prints 'text' with the time since the start."""
    print('[%6.1f s] %s' % (time.perf_counter() - began, text), flush=True)

  try:
    said('smallStepsBench %s, Python %s on %s' % (
        time.strftime('%Y-%m-%d %H:%M:%S'), platform.python_version(),
        platform.platform()))
    said('importing warp and the physics')
    import warp as wp
    from worQt.phys import SmallSteps, World, ballInGroove, ballOnRamp
    from worQt.phys import cross, dot, minus, norm, product, conjugate
    from worQt.phys import twistedTower
    from worQt.phys import _small_steps
    from worQt.phys._compiled import _kernelsOf, gpuDevice
    from worQt.phys._scenes import PROOF_BALL, RAMP_ANGLE, RAMP_START
    from worQt.phys._scenes import YARD_GROUND
    _kernelsOf()
    said('warp %s; cuda devices: %s' % (
        wp.__version__, [str(device) for device in wp.get_cuda_devices()]))
    device = gpuDevice()
    said('gpu here: %s' % device)
    frame, gravity = 1.0 / 60.0, (0.0, 0.0, -9.81)

    def compiled(module: object, where: str, expected: str) -> None:
      """Compiles (or loads, if cached) 'module' for 'where', saying so
      every 5 s meanwhile."""
      said('compiling %s for %s (cached: a moment; after a change: %s)'
           % (module.__name__.split('.')[-1], where, expected))
      done = threading.Event()

      def beat() -> None:
        """Says the compile still runs, every 5 s."""
        while not done.wait(5.0):
          said('  still compiling for %s ...' % where)

      threading.Thread(target=beat, daemon=True).start()
      try:
        wp.load_module(module, where)
      finally:
        done.set()
      said('  compiled for %s' % where)

    def grooveOf(first: tuple, last: tuple) -> str:
      """Says how the ball in its groove ended."""
      return 'the ball crept %.2f um, still to %.1e m/s' % (
          1e6 * norm(minus(last[0].place, first[0].place)),
          norm(last[0].velocity))

    def rampOf(first: tuple, last: tuple) -> str:
      """Says how the ball on its ramp ended."""
      a = RAMP_ANGLE
      along = (0.0, math.cos(a), math.sin(a))
      out = (0.0, -math.sin(a), math.cos(a))
      want = 0.5 * 5.0 / 7.0 * 9.81 * math.sin(a) * 0.25
      went = RAMP_START - dot(last[0].place, along)
      r = PROOF_BALL.shape.radius
      slip = norm(minus(last[0].velocity, cross(last[0].spin, tuple(
          r * x for x in out))))
      return 'rolled %+.3f %% of rolling\'s way, slipping %.1e m/s' % (
          100.0 * (went / want - 1.0), slip)

    def towerOf(first: tuple, last: tuple) -> str:
      """Says how the tower ended."""
      sunk = max(norm(minus(end.place, one.place))
                 for one, end in zip(first, last))
      turned = max(2.0 * math.acos(min(1.0, abs(product(
          end.turn, conjugate(one.turn))[0])))
                   for one, end in zip(first, last))
      return 'most moved %.1f um, most turned %.1e rad' % (1e6 * sunk,
                                                           turned)

    scenes = (('groove', ballInGroove, 1.0, None, grooveOf),
              ('ramp', ballOnRamp, 0.5, None, rampOf),
              ('tower', lambda: twistedTower(5), 2.0, YARD_GROUND,
               towerOf))
    results = []

    def timed(name: str, way: str, world: object, scene: object,
              seconds: float, says: object) -> None:
      """Steps 'scene' 'seconds' in 'world' a frame a call (after one
      frame to warm up), says how fast and how right."""
      assembly, states = scene()
      first = states
      states = world.advancedAll(assembly, states, frame, 0.0)
      frames = round(seconds / frame)
      start = time.perf_counter()
      for k in range(1, frames):
        states = world.advancedAll(assembly, states, frame, k * frame)
        if k % 30 == 0:
          said('  %s, %s: %.2f of %.2f s simulated' % (name, way,
                                                       k * frame, seconds))
      cost = (time.perf_counter() - start) / ((frames - 1) * frame)
      said('%s, %s: %.3f s of computing a simulated second (%.0f x real '
           'time); %s' % (name, way, cost, 1.0 / cost,
                          says(first, states)))
      results.append((name, way, cost))

    said('phase 1: today\'s springs on the CPU (each scene its seconds '
         'at about 0.1-1 s of computing a simulated second)')
    compiled(_kernelsOf(), 'cpu', '~15-30 s')
    for name, scene, seconds, ground, says in scenes:
      world = World(gravity, 1e-3, ground, None, True, None, 'cpu')
      timed(name, 'springs cpu', world, scene, seconds, says)
    said('phase 2: the small steps on the CPU (one thread)')
    compiled(_small_steps._kernelsOf(), 'cpu', 'a few seconds')
    for name, scene, seconds, ground, says in scenes:
      world = SmallSteps(gravity, ground, 2.5e-4, 1, 0.0, 'cpu')
      timed(name, 'small steps cpu', world, scene, seconds, says)
    if device is not None:
      said('phase 3: the small steps on the GPU (256 threads, one block)')
      compiled(_small_steps._kernelsOf(), device, 'up to a minute or two')
      for name, scene, seconds, ground, says in scenes:
        world = SmallSteps(gravity, ground, 2.5e-4, 1, 0.0, device)
        timed(name, 'small steps gpu', world, scene, seconds, says)
    else:
      said('no GPU found: phase 3 skipped')
    said('summary, s of computing a simulated second (below 1: faster '
         'than real time):')
    for name, way, cost in results:
      said('  %-7s %-16s %8.3f' % (name, way, cost))
    said('done')
    return 0
  except BaseException:
    said('FAILED:\n%s' % traceback.format_exc())
    return 1
  finally:
    sys.stdout, sys.stderr = terminal, errors
    faulthandler.disable()
    log.close()


def bearingStepsBench(*args, ) -> int:
  """Times the bearing ('walkingBearing', its motor on, 1 s) in the
  small steps ('SmallSteps'), one pass a step and four, on the CPU (one
  thread) and the GPU, where Warp finds one (spread over all of it, a
  step captured as a CUDA graph; and one block of 512 threads):
  for each, the computing a simulated second takes, the shaft's speed
  every 0.1 s (today's springs reach 2.00 rad/s by 0.4 s and hold it),
  how far it sank on its balls, and the gears' ratio over the last half.
  Shows each phase as it goes, its expected time, a heartbeat every 5 s
  while a kernel compiles (after a change: a few seconds on the CPU, a
  minute or two on the GPU), the simulated time as it runs; everything
  goes into 'previews/bearing-steps-bench.log' too. Returns 0, or 1 on
  an error."""
  import faulthandler
  import platform
  import threading
  import time
  import traceback
  os.makedirs('previews', 0o777, True)
  log = open(os.path.join('previews', 'bearing-steps-bench.log'), 'w', 1)
  faulthandler.enable(log)
  began = time.perf_counter()

  class Tee:
    """Writes to the terminal and to the log alike."""

    def __init__(self, stream: object) -> None:
      self.stream = stream

    def write(self, text: str) -> int:
      self.stream.write(text)
      log.write(text)
      return len(text)

    def flush(self, ) -> None:
      self.stream.flush()
      log.flush()

  terminal, errors = sys.stdout, sys.stderr
  sys.stdout, sys.stderr = Tee(terminal), Tee(errors)

  def said(text: str) -> None:
    """Prints 'text' with the time since the start."""
    print('[%6.1f s] %s' % (time.perf_counter() - began, text), flush=True)

  try:
    said('bearingStepsBench %s, Python %s on %s' % (
        time.strftime('%Y-%m-%d %H:%M:%S'), platform.python_version(),
        platform.platform()))
    said('importing warp and the physics')
    import warp as wp
    from worQt.phys import SmallSteps, dot, groundAt, rotated, runMotor
    from worQt.phys import rotorSpinOf, walkingBearing
    from worQt.phys import _small_steps
    from worQt.phys._compiled import gpuDevice
    from worQt.phys._scenes import GEAR_TEETH, MOTOR_FREE, MOTOR_STALL
    from worQt.phys._scenes import PINION_TEETH, RING_UPRIGHT
    device = gpuDevice()
    said('gpu here: %s' % device)
    shrunk, frame, window = 0.032 / 1.75, 0.002, 1.0 / 60.0
    axle = rotated(RING_UPRIGHT, (0.0, 0.0, 1.0))

    def compiled(where: str, expected: str) -> None:
      """Compiles (or loads) the small steps' kernel for 'where',
      saying so every 5 s meanwhile."""
      said('compiling the small steps for %s (cached: a moment; after a '
           'change: %s)' % (where, expected))
      done = threading.Event()

      def beat() -> None:
        """Says the compile still runs, every 5 s."""
        while not done.wait(5.0):
          said('  still compiling for %s ...' % where)

      threading.Thread(target=beat, daemon=True).start()
      try:
        wp.load_module(_small_steps._kernelsOf(), where)
      finally:
        done.set()
      said('  compiled for %s' % where)

    results = []

    def timed(where: str, passes: int, threads: int = 512,
              spread: bool = False) -> None:
      """Runs the bearing 1 s on 'where', 'passes' a step (on a GPU,
      'spread' over all of it as a CUDA graph, else one block of
      'threads') in frames of 1/60 s as the walk window does, then again
      in one call (the stepping alone, nothing handed to Python between
      steps), and says how it went."""
      world = SmallSteps((0.0, 0.0, -9.81), groundAt(shrunk), 2.5e-4,
                         passes, 0.0, where, threads, spread)
      if where != 'cpu':
        where = '%s %s' % (where, 'graph' if spread else 'x%d' % threads)
      assembly, states = walkingBearing(shrunk)
      motor = assembly.motors[0]
      runMotor(motor.drive, MOTOR_STALL, MOTOR_FREE, True)
      first = states
      states = world.advancedAll(assembly, states, frame, 0.0)
      speeds, ring, pinion, clock = [], 0.0, 0.0, frame
      start = time.perf_counter()
      for k in range(1, 61):
        states = world.advancedAll(assembly, states, window, clock)
        clock += window
        if k % 6 == 0:
          speeds.append(-dot(states[2].spin, axle))
          said('  %s, %d passes: %.1f s simulated, shaft %.3f rad/s'
               % (where, passes, clock, speeds[-1]))
        if k > 30:
          ring += dot(states[2].spin, axle) * window
          pinion += rotorSpinOf(motor, states) * window
      cost = (time.perf_counter() - start) / (clock - frame)
      sank = first[2].place[2] - states[2].place[2]
      ratio = -pinion / ring / (GEAR_TEETH / PINION_TEETH)
      fresh, again = walkingBearing(shrunk)
      runMotor(fresh.motors[0].drive, MOTOR_STALL, MOTOR_FREE, True)
      again = world.advancedAll(fresh, again, frame, 0.0)
      start = time.perf_counter()
      world.advancedAll(fresh, again, 1.0, frame)
      alone = time.perf_counter() - start
      said('%s, %d passes: in 1/60 s frames %.3f s of computing a '
           'simulated second (%.1f x real time); stepping alone %.3f '
           '(%.1f x, %.0f us a step); shaft every 0.1 s: %s; sank %.1f '
           'um; gears %.5f of 31/16' % (
               where, passes, cost, 1.0 / cost, alone, 1.0 / alone,
               1e6 * alone / 4000.0, ' '.join('%.3f' % speed
                                              for speed in speeds),
               1e6 * sank, ratio))
      results.append((where, passes, cost, alone, min(speeds[4:]), sank))

    said('phase 1: the CPU (one thread; ~0.8 s of computing a '
         'simulated second at one pass, ~3 at four; each run twice)')
    compiled('cpu', 'a few seconds')
    timed('cpu', 1)
    timed('cpu', 4)
    if device is not None:
      said('phase 2: the GPU, spread over all of it (each part of a step '
           'a kernel, a step captured as a CUDA graph, replayed), and one '
           'block of 512 threads to compare')
      compiled(device, 'a minute or two')
      for spread, passes in ((True, 1), (True, 2), (True, 4),
                             (False, 1)):
        if True:
          try:
            timed(device, passes, 512, spread)
          except Exception as error:
            said('%s refused: %s: %s' % (device, type(error).__name__,
                                         error))
    else:
      said('no GPU found: phase 2 skipped')
    said('summary: where, passes, s of computing a simulated second in '
         '1/60 s frames and stepping alone, slowest shaft after 0.5 s '
         '(rad/s), sank (um):')
    for where, passes, cost, alone, slowest, sank in results:
      said('  %-12s %d  %7.3f  %7.3f  %.3f  %6.1f' % (
          where, passes, cost, alone, slowest, 1e6 * sank))
    said('done')
    return 0
  except BaseException:
    said('FAILED:\n%s' % traceback.format_exc())
    return 1
  finally:
    sys.stdout, sys.stderr = terminal, errors
    faulthandler.disable()
    log.close()


def demo(*args, ) -> int:
  """Opens the walk in the yard for showing off: crates, dominoes,
  planks and balls to walk among (WASD, the mouse to look), grab with
  the gravity gun and punt away; E opens the menu, where the place box
  goes to the bearing, the ring or the wheel. Returns the exit code once
  its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The yard'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def hubShow(*args, ) -> int:
  """Opens the walk at the rear wheel hub in the void (a front wheel
  driven car's: the still spindle, the hub with its flange and brake
  disc turning on two rows of balls in their cages), standing on the
  platform under the disc: punt or grab the disc to spin it, fly
  (Space twice) to look in; E opens the menu. Returns the exit code once
  its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The rear hub in the void'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def tyreShow(*args, ) -> int:
  """Opens the walk in the tyre yard: an alloy wheel standing on its
  tyre, the tyre a spring in the wheel's plane as stiff as its 2.3 bar
  makes it (260 kN/m). Grab it (right button) or punt it (left), E
  opens the menu, whose 'Give wheel' gives another, held before you;
  'The cord tyre yard' there is the tyre of cords and air. The first run
  compiles the small steps (said in the status). Returns the exit code
  once its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The tyre yard'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def steerShow(*args, ) -> int:
  """Opens the walk at the steering bench: a front axle on a rig, the
  walker in the driver's place behind a Soufflé racing wheel. Left and
  right arrows turn the wheel (the player's hands, a fourth wall point),
  up centres it; the column's pinion slides the rack, the tie rods
  steer the knuckles and the wheels on the ground (Ackermann). B (or
  'Brake' in the menu, E) brakes them. Returns the exit code once its
  window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The steering bench'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def rigShow(*args, ) -> int:
  """Opens the walk at the tyre rig: a front corner on the end of a
  boom, pressed by a ram onto a turntable. In the menu (E): 'Steer'
  holds the steering wheel on the boom at an angle: the wheel steers and
  rolls across the deck, the boom swinging after it on its yoke, as a
  record player's arm; 'Tune-up' opens the wheel's tyre pressure,
  camber and toe (the rig set up anew with them); 'Deck' sets the
  turntable's
  speed under the wheel (0-20 m/s), 'Ram' the load, 'Humps' bolts four
  humps across it, 'Brake' and 'Line' (or hold B) brake the wheel; the
  status reads the deck's speed and how far out the wheel runs, the
  rim's speed, the load, the brake's pull and the side force. Returns
  the exit code once its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The tyre rig'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def soapboxShow(*args, ) -> int:
  """Opens the walk at the soapbox: sat in it on its ramp, its brakes
  holding it ('Brake: on'); turn 'Brake' off in the menu (E) to let it
  go (B brakes again). It rolls down, round the bend and into the loop:
  the arrows steer (hold a little left through the top: hands off it
  drifts off the planks' inner edge three quarters round), or 'Robot
  hands' keeps the line. 'Tune-up' sets each wheel's tyre pressure,
  camber and toe; the mouse looks round the car; Space climbs out
  (flying: Shift lands); 'Set it up anew' puts it back on the ramp. The
  status reads its speed and how hard its tyres press (g). Returns the
  exit code once its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The soapbox'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def realCarShow(*args, ) -> int:
  """Opens the walk at the real car: a mid-engined two seater of our
  own parts (the tyre rig's corners, the drivetrain bench's engine,
  clutch, dog-leg transaxle and differential, half shafts through
  constant velocity joints to the rear wheels), the walker sat in it.
  A and D steer (let go: it centres), W the throttle, S the brakes
  (anti-lock), Space the handbrake (the rears locked at once), keypad 0
  holds the clutch down, keypad 4 5 6 / 1 2 3 move the stick to R 2 4 /
  1 3 5 (the gate's own rows; through it, held at the synchro: clutch
  down to shift), N neutral, I the starter, M the V12's sound, F out of
  it; 'Tune-up' in the menu (E) sets each wheel. To pull away: clutch
  down, keypad 1, some throttle, let the clutch up. Returns the exit
  code once its window closes. Waits first for 'preloadGpu', if it
  runs."""
  _preloadWaited()
  from PySide6.QtCore import Qt
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The real car'))
    window.reset()
    window.resize(1920, 1080)
    #  Shown without taking the focus (it opens after the tests, maybe
    #  while the user works elsewhere): a click on it gives it the keys.
    window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
    window.show()
  return app.returnCode


def realOvalShow(*args, ) -> int:
  """Opens the walk at the oval (user, 2026-11-15: "park the old car by
  inside the grass on the Dover track, put this car there instead, have
  an AI driver take the wheel"): the real car on the start line, the
  walker sat in it, the racing driver at its wheel ('Robot hands' on:
  steering wheel, pedals, clutch and stick; its laps timed in the
  readings), the old car parked in the infield's grass by the front
  straight. 'Robot hands' off, you drive it ('realCarShow''s keys); F
  gets you out (Space twice flies). Shown without taking the focus.
  Returns the exit code once its window closes. Waits first for
  'preloadGpu', if it runs."""
  _preloadWaited()
  from PySide6.QtCore import Qt
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The oval'))
    window.reset()
    window.resize(1920, 1080)
    window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
    window.show()
  return app.returnCode


def cityShow(*args, ) -> int:
  """Opens the walk in town (user, 2026-11-15: uncannyball's lap of
  central Copenhagen, previews/royal_race.crg): the real car at the
  lap's start by Amalienborg Slotsplads (its palaces and Frederik V on
  horseback stand there), the walker sat in it, the city driver at its
  wheel at the 50 km/h limit ('Robot hands' on; off, you drive it as in
  'realCarShow'). The height data's credit is in the readings. Shown
  without taking the focus. Returns the exit code once its window
  closes. Waits first for 'preloadGpu', if it runs."""
  _preloadWaited()
  from PySide6.QtCore import Qt
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'Copenhagen'))
    window.reset()
    window.resize(1920, 1080)
    window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
    window.show()
  return app.returnCode


def drivetrainShow(*args, ) -> int:
  """Opens the walk at the drivetrain bench: an engine, the clutch, a
  five-speed transaxle with a dog-leg gate (R 2 4 forward, 1 3 5 back)
  and synchromesh, the differential, two wheels, the gearbox's case in
  glass. Up opens the throttle, C holds the clutch down, 1 to 5, R and
  N move the stick (through the gate: held at the synchro until the
  gear is at speed: with the clutch in it will not go), I the starter
  (it stalls), B the wheels' brakes ('Line' in the menu, E), M the
  engine's sound (a naturally aspirated V12 as AngeTheGreat's Engine
  Simulator hears one; the first time it compiles a few seconds). The
  status
  reads the engine, the gear and the stick, the clutch's slip and the
  wheels' speeds. Returns the exit code once its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The drivetrain bench'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def shockShow(*args, ) -> int:
  """Opens the walk at the shock bench: a quarter car's corner on a
  rig, a wishbone in rubber bushings with a 100 kg weight at its end,
  held up by a coilover (yellow damper, chrome rod, red coil). Grab the
  weight (right button) and yank it, or punt it (left). Returns the exit
  code once its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The shock bench'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def hingeShow(*args, ) -> int:
  """Opens the walk at the hinge bench: two wishbones hanging from a
  gantry on two hinges each, the left rigid, the right in rubber
  bushings (black), and an oak door on two hinges. Punt them (left
  button), grab them (right). Returns the exit code once its window
  closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The hinge bench'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def brakeShow(*args, ) -> int:
  """Opens the walk at the brake bench: the Soufflé wheel with its cast
  iron disc on a stand, its caliper red. Punt the tyre (left button) to
  spin it; hold B (or 'Brake' in the menu, E) to brake it at the
  'Line' slider's pressure (10 bar first). Returns the exit code once
  its window closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The brake bench'))
    window.reset()
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def bearingShow(*args, ) -> int:
  """Opens the walk at the car's bearing on its hollow shaft (drawn by
  the GPU): walk up the ramp and through the shaft; 'Motor: off' turns
  it on, turning the shaft by its gears. Returns the exit code once its
  window
  closes."""
  from worQt.phys.gui import WalkApp
  from worQt.phys.gui._walk import PLACES
  with WalkApp(*sys.argv) as app:
    window = app.window
    window.placeBox.setCurrentIndex([place.name for place in PLACES].index(
        'The bearing'))
    window.reset()
    window.resize(1280, 800)
    window.show()
  return app.returnCode


def walkShow(*args, ) -> int:
  """Opens the walk (first place: the car's wheel on its stand, the
  walker shrunk to its height) seen through a walker's eyes, a grabber
  in their hands: click in to look round, WASD to walk, right button to
  grab, left to punt. Returns the exit code once its window closes."""
  from worQt.phys.gui import WalkApp
  with WalkApp(*sys.argv) as app:
    app.window.resize(1280, 800)
    app.window.show()
  return app.returnCode


def carShow(*args, ) -> int:
  """Opens the car, four wheels on suspensions of their own, steered
  through a column, driven from behind it: W/S drive and brake, A/D
  steer. Returns the exit code once its window closes."""
  from worQt.phys.gui import CarApp
  with CarApp(*sys.argv) as app:
    app.window.resize(1280, 800)
    app.window.show()
  return app.returnCode


def ovalShow(*args, ) -> int:
  """Opens the car on the oval: a mile of concrete, banked 9 degrees on
  its straights and 24 in its turns, set down on its start line (W
  drives, the turns go left). Returns the exit code once its window
  closes."""
  from worQt.phys.gui import CarApp
  with CarApp(*sys.argv) as app:
    window = app.window
    window.groundBox.setCurrentIndex(window.groundBox.findText('Oval'))
    window.resize(1920, 1080)
    window.show()
  return app.returnCode


def robotOval(*args, ) -> int:
  """The robot drives the car a lap of the oval at 'FULL' fidelity
  (the reference), recording the car 200 times a second: its
  progress printed each simulated second; the recording written to
  previews/robot-oval-<when>.csv with a .json beside it (each channel's
  unit and meaning, the lap time, the run). Returns 0."""
  import time
  from worQt.phys import FULL
  from worQt.phys._robot import robotLaps
  from worQt.phys._terrain import OVAL_LENGTH
  speed, rate, laps = 30.0, 200.0, 1.0

  def report(clock: float, robot: object, took: float) -> None:
    """Prints how far the robot has got."""
    print('  %5.1f s simulated, lap %.2f, %+.2f m off its line, '
          '%.0f s of compute (%.1f x real time)'
          % (clock, robot.along / OVAL_LENGTH, robot.off, took,
             took / clock),
          flush=True)

  print('the robot drives %g lap(s) at %.0f m/s, recorded %.0f times a '
        'second (FULL: ~4.3 s of compute a simulated second, ~4 '
        'min a lap)'
        % (laps, speed, rate), flush=True)
  began = time.time()
  recorder, times, _ = robotLaps(laps, speed, 0.0, rate, FULL, report)
  path = os.path.join('previews', 'robot-oval-%s.csv'
                      % time.strftime('%Y%m%d-%H%M%S'))
  written = recorder.saved(path, {
      'speed'         : speed, 'laps': laps, 'lapTimes': list(times),
      'rate'          : rate, 'fidelity': 'FULL', 'line': 'the middle line',
      'computeSeconds': time.time() - began})
  print('lap times %s; saved %s and %s' % (times, *written))
  return 0


def benchCar(*args, ) -> int:
  """Puts the car on the suspension bench at 'FULL' fidelity and
  prints what it found: the scales, the bounce test (heave, pitch,
  roll: measured beside designed), the sideways pull (roll a g, each
  corner's travel, side force, steer, camber). ~1-2 min. Returns 0."""
  from worQt.phys import FULL, carBuilt
  from worQt.phys._bench import benchOf, reportOf
  print('the bench: building the car, then tapping and pulling it '
        '(~1-2 min)', flush=True)
  print(reportOf(benchOf(carBuilt(0.5, FULL), FULL)))
  return 0


def trainRacer(*args, ) -> int:
  """Trains the learning racer on the oval, headless, at 'LIVE'
  fidelity (as the window runs): 20 laps from the start line, its brain
  kept after each in previews/racer-brain.json (the window's robot, B,
  carries on from it); each lap's time, its seconds on the apron, the
  pace and lane it has learnt printed. ~1 min of compute a lap.
  Returns 0."""
  import time
  from worQt.phys import LIVE
  from worQt.phys._laps import lapText
  from worQt.phys._robot import BRAIN, trainRacer as trained
  began = time.time()

  def report(lap: int, took: float, apron: float, racer: object) -> None:
    """Prints a lap's time (or that the racer was stranded and set on
    the start line again) and what the racer has learnt so far."""
    pace = 100.0 * (racer.paceLearnt - 1.0)
    lane = sum(racer.lane) / len(racer.lane)
    print('  %s  apron %.2f s  pace %+.1f %%  lane %.2f m  '
          '(%d passes learnt, %.0f s of compute)'
          % ('lap %2d  %s' % (lap, lapText(took)) if took is not None
             else 'stranded: set on the start line again', apron, pace,
             lane, racer.learnt, time.time() - began), flush=True)

  print('training the learning racer, 20 laps (~1 min each)', flush=True)
  trained(20, BRAIN, LIVE, report)
  return 0


if __name__ == '__main__':
  # yolo(preloadGpu, showTests, cityShow, )
  yolo(cityShow, )
