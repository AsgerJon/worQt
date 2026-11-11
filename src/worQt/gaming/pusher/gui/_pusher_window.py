"""
PusherWindow subclasses 'MainWindow' and is a coin pusher to play: the
machine in 3D, its buttons, and its books.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import faulthandler
import math
import sys
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from ....engineering.gui import TestStatus
from ....windows import MainWindow
from .._machine_worker import MachineWorker
from ._pusher_sounds import PusherSounds
from . import PusherPanel, PusherToolBar, PusherView

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QCloseEvent

  from .._machine_worker import Snapshot


class PusherWindow(MainWindow):
  """
  PusherWindow subclasses 'MainWindow' and is a coin pusher to play:
  the 'toolBar' above, the machine itself in 3D, 'view', and beside it
  the books, 'panel'. The machine runs in a process of its own, a
  'MachineWorker', in step with the clock; the window shows the newest
  frame every 16 ms. It opens on the machine empty, the pusher running;
  'Start game' has the house pour the coins in, in two great heaps;
  the machine runs while 4, 3, 2, 1 is counted down over it, then GO!,
  and the game is on: 'Left chute' and 'Right chute', or the arrow
  keys, drop a coin. 'Pause' and 'Play' stop and run the machine;
  'Start game' again starts over. The chute buttons are greyed while
  the game is not on. The coins are heard as they meet and land in the
  tray, the countdown beeps ('sounds'; 'Sound' in the toolbar).
  'snapshot' is the frame last shown.

  Nothing slow happens in the window's own thread, and everything slow
  is watched: 'status', the strip along the bottom, says live what is
  going on and for how long (the coin solver starting, compiled the
  first time on a computer; the 3D view loading, its shaders built the
  first time; the house pouring; the countdown; play, and how the
  machine keeps up with the clock), with a moving bar while it works.
  Each step's time is written to the terminal ('noted'), and a
  watchdog writes there, and says in the strip, whenever the window was
  held up, and while doing what. Waiting on the coin solver, the strip
  tells working from stuck: how busy its process is (a share of a core,
  or idle), that nothing has come from it for a while, a step running
  far past its usual time, or that the process has stopped.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Coin pusher'
  __start_size__ = 1400, 900
  __frame_ms__ = 16  # between two looks for a new frame

  #  Private Variables
  __window_worker__: MachineWorker | None = None
  __window_snapshot__: Snapshot | None = None
  __window_paused__: bool = False
  __window_keys__: list | None = None
  __window_sounds__: PusherSounds | None = None
  __go_time__: float | None = None
  __window_began__: float = 0.0
  __window_doing__: str = 'starting'
  __last_watch__: float | None = None
  __held_up__: tuple | None = None
  __pace_mark__: tuple | None = None
  __window_pace__: float | None = None
  __status_turn__: int = 0
  __cpu_mark__: tuple | None = None
  __worker_load__: float | None = None
  __last_come__: float | None = None
  __worker_dead__: bool = False
  __sounds_told__: set | None = None

  #  Public Variables
  toolBar = AttriBox[PusherToolBar](THIS)
  view = AttriBox[PusherView](THIS)
  panel = AttriBox[PusherPanel](THIS)
  status = AttriBox[TestStatus](THIS)
  frameTimer = AttriBox[QTimer](THIS)
  watchTimer = AttriBox[QTimer](THIS)

  #  Virtual Variables
  worker: Field[MachineWorker] = Field()
  sounds: Field[PusherSounds] = Field()
  snapshot: Field[Snapshot] = Field()
  paused: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @worker.GET
  def _getWorker(self, ) -> MachineWorker:
    """The 'worker' getter returns the process running the machine."""
    if self.__window_worker__ is None:
      self.__window_worker__ = MachineWorker()
    return self.__window_worker__

  @sounds.GET
  def _getSounds(self, ) -> PusherSounds:
    """The 'sounds' getter returns what plays the machine's sounds."""
    if self.__window_sounds__ is None:
      self.__window_sounds__ = PusherSounds()
      self.noted('starting the sounds in their own process')
    return self.__window_sounds__

  @snapshot.GET
  def _getSnapshot(self, ) -> Snapshot | None:
    """The 'snapshot' getter returns the frame last shown, or 'None'
    before the first."""
    return self.__window_snapshot__

  @paused.GET
  def _getPaused(self, ) -> bool:
    """The 'paused' getter tells whether the machine is stopped."""
    return self.__window_paused__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """The 'initUI' method lays the window out, sizes it and starts the
    machine, empty, the chutes shut until a game starts."""
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 2)
    layout.addWidget(self.view, 1, 0)
    layout.addWidget(self.panel, 1, 1)
    layout.addWidget(self.status, 2, 0, 1, 2)
    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 0)
    layout.setRowStretch(1, 1)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.toolBar.leftButton.setEnabled(False)
    self.toolBar.rightButton.setEnabled(False)
    self.__window_began__ = time.perf_counter()
    self.__sounds_told__ = set()
    self.noted('starting the coin solver in its own process')
    self.worker.start()
    self.sounds.enabled = self.toolBar.soundBox.checked
    self.frameTimer.start(self.__frame_ms__)
    self.watchTimer.start(100)
    self._showStatus()

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the buttons, the keys and the
    timer."""
    bar = self.toolBar
    bar.leftButton.clicked.connect(self.dropLeft)
    bar.rightButton.clicked.connect(self.dropRight)
    bar.playButton.clicked.connect(self.togglePlay)
    bar.newButton.clicked.connect(self.startGame)
    bar.soundBox.toggled.connect(self.setSound)
    self.frameTimer.timeout.connect(self.tick)
    self.watchTimer.timeout.connect(self.watch)
    self.view.sceneLoaded.connect(self._sceneLoaded)
    self.view.firstDrawn.connect(self._firstDrawn)
    self.mainMenuBar.fileMenu.exitAction.triggered.connect(self.close)
    keys = []
    for key, slot in ((Qt.Key.Key_Left, self.dropLeft),
                      (Qt.Key.Key_Right, self.dropRight),
                      (Qt.Key.Key_A, self.dropLeft),
                      (Qt.Key.Key_D, self.dropRight),
                      (Qt.Key.Key_Space, self.togglePlay)):
      shortcut = QShortcut(QKeySequence(key), self)
      shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
      shortcut.activated.connect(slot)
      keys.append(shortcut)
    self.__window_keys__ = keys

  def closeEvent(self, event: QCloseEvent) -> None:
    """Closing the window stops the machine and its process."""
    MainWindow.closeEvent(self, event)
    if event.isAccepted():
      self.frameTimer.stop()
      self.watchTimer.stop()
      faulthandler.cancel_dump_traceback_later()
      self.worker.close()
      self.sounds.close()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def dropLeft(self, ) -> None:
    """The 'dropLeft' method drops a coin down the left chute."""
    self.worker.drop(-1)

  def dropRight(self, ) -> None:
    """The 'dropRight' method drops a coin down the right chute."""
    self.worker.drop(1)

  def togglePlay(self, ) -> None:
    """The 'togglePlay' method stops the machine, or runs it on."""
    self.__window_paused__ = not self.__window_paused__
    self.worker.pause(self.__window_paused__)
    self.toolBar.playButton.text = 'Play' if self.paused else 'Pause'
    self.toolBar.playButton.update()

  def bannerOf(self, snapshot: Snapshot) -> str:
    """The 'bannerOf' method returns what is written big over the
    machine: the countdown's beats, 4 to 1, then 'GO!' for a second,
    else nothing."""
    if snapshot.countdown > 0.0:
      self.__go_time__ = None
      return '%d' % math.ceil(snapshot.countdown)
    if not snapshot.started:
      return ''
    if self.__go_time__ is None:
      self.__go_time__ = snapshot.time
    return 'GO!' if snapshot.time - self.__go_time__ < 1.0 else ''

  def watch(self, ) -> None:
    """The 'watch' method, called every 100 ms, notes when it was called
    late: the window held up, and while doing what. It also re-arms
    'faulthandler', whose watchdog runs outside Python: should the
    window not answer for 3 s, every thread's traceback is written to
    the terminal, again every 3 s while it does not, showing where it is
    stuck, even where this watch cannot run."""
    now = time.perf_counter()
    faulthandler.dump_traceback_later(3.0, True)
    self._loadMeasured(now)
    self._soundsMeasured()
    last, self.__last_watch__ = self.__last_watch__, now
    if last is None or now - last < 0.4:
      return
    held = now - last - 0.1
    self.__held_up__ = (now, held, self.__window_doing__)
    doing = self.__window_doing__
    self.noted('the window was held up %.1f s while %s' % (held, doing))

  def noted(self, words: str) -> None:
    """The 'noted' method writes 'words' to the terminal, with the time
    since the window opened."""
    stamp = time.perf_counter() - self.__window_began__
    sys.stderr.write('[coin pusher %6.1f s] %s\n' % (stamp, words))

  def startGame(self, ) -> None:
    """The 'startGame' method starts a game: an empty machine, the house
    pouring the coins in, a full purse; the coin solver started anew
    first if it has stopped."""
    if not self.worker.running:
      self.noted('starting the coin solver anew')
      self.__worker_dead__ = False
      self.__window_snapshot__ = None
      self.__last_come__ = None
      self.__cpu_mark__ = None
      self.__worker_load__ = None
      self.worker.start()
    self.noted('start game: the house pours')
    self.worker.begin()

  def setSound(self, sound: bool) -> None:
    """The 'setSound' method lets the machine be heard, or not."""
    self.sounds.enabled = True if sound else False

  def tick(self, ) -> None:
    """The 'tick' method shows the newest frame of the machine, if one
    came."""
    snapshot = self.worker.latest()
    self.__status_turn__ += 1
    if self.__status_turn__ % 6 == 0:
      self._showStatus()
    if snapshot is None:
      return
    self.__last_come__ = time.perf_counter()
    if self.__window_snapshot__ is None:
      self.noted('the coin solver ready after %.1f s' % self._elapsed())
      self.__window_doing__ = 'loading the 3D view'
    self._paced(snapshot)
    self.__window_snapshot__ = snapshot
    self.view.showSnapshot(snapshot)
    self.panel.snapshot = snapshot
    self.sounds.heard(snapshot)
    self.view.setBanner(self.bannerOf(snapshot))
    bar = self.toolBar
    for button in (bar.leftButton, bar.rightButton):
      if button.isEnabled() != snapshot.started:
        button.setEnabled(snapshot.started)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _elapsed(self, ) -> float:
    """How long since the window opened, in s."""
    return time.perf_counter() - self.__window_began__

  def _loadMeasured(self, now: float) -> None:
    """Once a second, how busy the coin solver's process has been since
    the last: a share of one core, or None where it cannot be read;
    and notes, once, if the process has died."""
    worker = self.worker
    if not self.__worker_dead__ and worker.exitCode is not None:
      self.__worker_dead__ = True
      self.noted('the coin solver stopped, exit code %s' % worker.exitCode)
    mark = self.__cpu_mark__
    if mark is not None and now - mark[0] < 1.0:
      return
    used = worker.cpuSeconds
    if used is not None and mark is not None and mark[1] is not None:
      self.__worker_load__ = (used - mark[1]) / (now - mark[0])
    self.__cpu_mark__ = (now, used)

  def _soundsMeasured(self, ) -> None:
    """Notes, once each, the sounds ready, in trouble, or their process
    stopped."""
    sounds = self.__window_sounds__
    if sounds is None:
      return
    player = sounds.player
    player.heard()
    told = self.__sounds_told__
    if player.ready and 'ready' not in told:
      told.add('ready')
      self.noted('the sounds ready after %.2f s' % player.readyAfter)
    if player.trouble and 'trouble' not in told:
      told.add('trouble')
      self.noted('the sounds: %s' % player.trouble)
    if player.exitCode is not None and 'stopped' not in told:
      told.add('stopped')
      self.noted('the sound process stopped, exit code %s' %
                 player.exitCode)

  def _soundState(self, ) -> str:
    """Words on the sounds, when they are not simply playing."""
    sounds = self.__window_sounds__
    if sounds is None or not self.toolBar.soundBox.checked:
      return ''
    player = sounds.player
    if player.exitCode is not None:
      return '; the sounds have STOPPED (exit code %s)' % player.exitCode
    if player.trouble:
      return '; the sounds: %s' % player.trouble
    if not player.ready:
      waited = self._elapsed()
      if waited > 10.0:
        return '; the sounds are not ready after %.0f s' % waited
      return '; the sounds loading'
    return ''

  def _liveness(self, ) -> str:
    """Words on whether the coin solver works: its share of a core, or
    that it has stopped."""
    if self.__worker_dead__:
      return 'its process has STOPPED (exit code %s)' % self.worker.exitCode
    load = self.__worker_load__
    if load is None:
      return 'its process is alive'
    if load < 0.05:
      return 'its process is IDLE (%d %% of a core): it may be stuck' % (
        round(100 * load))
    return 'working at %d %% of a core' % round(100 * load)

  def _sceneLoaded(self, ) -> None:
    """Notes the 3D view's scene loaded."""
    self.noted('the 3D scene loaded after %.1f s' % self._elapsed())
    self.__window_doing__ = 'drawing the first 3D frame'

  def _firstDrawn(self, ) -> None:
    """Notes the 3D view's first frame drawn."""
    self.noted('the first 3D frame drawn after %.1f s' % self._elapsed())
    self.__window_doing__ = 'running'

  def _paced(self, snapshot: Snapshot) -> None:
    """Measures every 2 s how fast the machine runs against the clock,
    noting when it falls behind."""
    now = time.perf_counter()
    mark = self.__pace_mark__
    if mark is None or self.paused or snapshot.time < mark[1]:
      self.__pace_mark__ = (now, snapshot.time)
      return
    if now - mark[0] < 2.0:
      return
    pace = (snapshot.time - mark[1]) / (now - mark[0])
    self.__pace_mark__ = (now, snapshot.time)
    if pace < 0.9 and (self.__window_pace__ or 1.0) >= 0.9:
      self.noted('the machine falls behind the clock: %.2fx' % pace)
    self.__window_pace__ = pace

  def _showStatus(self, ) -> None:
    """Says in the strip along the bottom what is going on, and for how
    long; and, for 5 s after, when the window was held up."""
    s, view, elapsed = self.snapshot, self.view, self._elapsed()
    come = self.__last_come__
    silent = 0.0 if come is None else time.perf_counter() - come
    if self.__worker_dead__:
      mode, text = 'finished', 'The coin solver has stopped'
      details = ('exit code %s: see the terminal; Start game starts it '
                 'anew' % self.worker.exitCode)
    elif s is None:
      mode, text = 'casting', 'Starting the machine'
      usual = ('usually about 6 s the first run on this computer, a '
               'second after')
      if elapsed > 30.0:
        usual = 'LONGER than the usual 6 s'
      details = 'starting the coin solver: %.0f s, %s; %s' % (
        elapsed, usual, self._liveness())
    elif silent > 3.0 and not self.paused:
      mode, text = 'casting', 'Waiting for the coin solver'
      details = 'nothing from it for %.0f s; %s' % (silent, self._liveness())
    elif not view.drawn:
      mode, text = 'casting', 'Loading the 3D view'
      details = ('%.1f s (the first run on this computer builds its '
                 'shaders)' % elapsed)
    elif s.filling and s.countdown <= 0.0:
      mode, text = 'casting', 'The house is pouring its coins in'
      details = '%d coins in' % s.onMachine
    elif s.countdown > 0.0:
      mode, text = 'running', 'Get ready'
      details = '%d' % math.ceil(s.countdown)
    elif not s.started:
      mode, text, details = 'idle', 'Empty', 'press Start game'
    elif self.paused:
      mode, text, details = 'paused', 'Paused', 'press Play'
    else:
      mode, text = 'running', 'Playing'
      details = '%d coins on the machine' % s.onMachine
    pace = self.__window_pace__
    if s is not None and pace is not None and not self.paused:
      details += ', the machine at %.2fx the clock' % pace
    details += self._soundState()
    held = self.__held_up__
    if held is not None and time.perf_counter() - held[0] < 5.0:
      details += ' | the window was held up %.1f s while %s' % held[1:]
    self.status.showState(mode, text, details)
