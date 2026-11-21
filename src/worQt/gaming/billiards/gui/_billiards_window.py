"""
BilliardsWindow subclasses 'MainWindow' and is three-cushion in 3D: a
game kept and refereed by the FFB's rules, or a sandbox to try shots in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import random
import time
from typing import TYPE_CHECKING

import numpy
from PySide6.QtCore import QDir, QPoint, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMenu
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ....windows import MainWindow
from .. import Ball, Cue, Match, Motion, Recorder, Recording, Referee
from .. import KegleCall, KegleGame, KegleMatch, KegleMotion
from .. import KegleRecorder, KegleReferee
from .. import KegleShot, KegleTable, PinField, Rules, Shot, ShotWorker
from .._kegle_motion import flingOf
from .. import Room, Streak, Trails, Trenches, Unfolded
from .._carom_table import isParked
from . import BilliardsSounds, BilliardsToolBar, ShotPanel, TableView
from . import FOLLOW_SECONDS, STROKE_MOST, UnfoldedMap, cueBackAt

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Callable

  from PySide6.QtGui import QCloseEvent


#  How near, in mm, a ball's middle stays to where it comes to rest for it
#  to lie still, if spinning in place.
_STILL_WITHIN = 0.01


class BilliardsWindow(MainWindow):
  """
  BilliardsWindow subclasses 'MainWindow' and is three-cushion in 3D:
  the table, 'view'; the 'toolBar' above; the 'panel' beside, where shots
  are set up and the game kept.

  In a 'game' the players lag for the break, both shooting at once,
  white's shot set first; the winner chooses who breaks, from spot 4 or
  5; each shot is called by the 'referee', the FFB's Code sportif
  carambole, and kept by the 'match': a point plays on, a miss or a foul
  passes the turn, a ball off the table is respotted, the equalizing
  inning and the next set start from the starting position. While the
  balls lie as a game opens, 'Left spot' and 'Right spot' lay the cue
  ball on spot 4 or 5, left or right of the head spot as the player
  breaking sees it; the side chosen is kept for the openings to come,
  and in the sandbox 'Reset' lays the opening for the cue ball chosen.
  In the
  'sandbox' any ball may be struck from anywhere, each shot still
  called; 'Mulligan' takes the last shot back, the balls as they were
  before it and its mark as it was; 'Move balls' lets a drag on the
  cloth put them anywhere. When the cue
  ball rests frozen to another, 'Respot' puts the two back on their
  spots (2.2.07-E).

  The game played is three-cushion or keglebillard ('setKind', the
  toolbar's 'Three-cushion' and 'Kegler'), each with a game loop of its
  own. Keglebillard's ('kegleGame', 'KegleGame') lags as three-cushion
  does; the winner lays out or lets the other ('Lay out'); red is the
  cue ball, in hand at the layout and after it went into a pocket, put
  down by a drag within a quarter of either short cushion ('Place
  red'); the pins are set up on their spots again as soon as a shot's
  balls rest (the user: they respawn before each shot); each shot is
  called by keglebillard's referee, the series going on while it
  scores, to the distance chosen before the lag ('To 400': 200 to 800).
  A debug, the menu 'Debug', 'Fling pins', or F8 (the user: to see a pin
  go over a cushion at will): on, a click on a pin sends it flying over
  the nearest cushion, where it evaporates ('flingPin'), the game
  untouched.

  The stroke (the user) is a spring: pressing the right button on the
  view and pulling the mouse back towards the player draws the cue back,
  the further the harder, the speedometer over the ball showing how
  hard; letting the button go strikes the cue ball at once that hard
  ('pullPressed', 'pullMoved', 'pullReleased', 'springSpeed',
  'strikeAt'); pushed back to where it was pressed first, nothing is
  struck; a left click or Escape meanwhile calls it off ('cancelStroke').
  It is the only way a shot is made (the user); pressed while no shot
  may be struck, a barrier shows over the ball ('TableView.
  flashBarrier'). The panel's point struck and power may be set there
  only while the full map shows (the user: in the regular view they show
  what is set, by the keys and the pull, output only).
  Each shot starts from the middle of the ball, the point struck
  centred again as the last one's balls rest.

  The next shot may be set up before all rest (the user): once the
  ball it is played with lies where it stays, still or only spinning in
  place, and the balls are to be played as they will lie, the game is
  kept, the view comes back from watching the shot to turn round that
  ball, and the aim, the point struck, the power and the stroke's pull
  may be set while the others roll on ('settingUp'); a stroke begun
  before every ball rests is refused, a barrier shown over the ball.

  While the balls rest, the camera turns round the ball looked from,
  the cue ball unless another is chosen or tapped, and a faint line
  shows the aim; the stroke strikes the cue ball with the 'cue', held
  level, the way the camera faces, at the point the panel says, the line
  the longer and warmer the harder the shot. Looking from
  another ball is a dry run on it: 'Mark' leaves a ghost of the cue ball
  where it must meet that ball to send it along the line, there until
  the next shot or the balls are laid anew.
  Looking from the ghost, the camera stands at it facing the way the cue
  ball leaves the marked ball after the hit, square to the line of
  their middles, without spin: turning the view chooses that way and
  moves the ghost round the ball to the hit that gives it; it stays
  where it is left. 'Top view' shows the view from above instead of
  the camera's, the corner hidden; 'Unfolded' shows, beside the table,
  the map of it unfolded, every cushion a mirror into a copy of it, the
  balls in every copy, and, while a shot is aimed from the cue ball, the
  arc of its English across them, a guide for choosing enough; 'Full
  map' shows the same, 7 by 7 tables centred on the table, instead of
  the table, the arc ending where it first meets a ball and fanning out
  there into the ways the two may go, crowded where likely; 'Field of
  view' sets how much the camera takes in. The keys A and D turn the aim
  left and right, W and S tilt the camera up over the ball and down to
  the cloth, 'Aim step' degrees a press, held to keep on; the arrow keys
  move the point struck, up and down for follow and draw, left and
  right for English, '__spin_step__' of the radius a press, held to keep
  on; End takes the middle again.

  A shot is made only by the stroke (the user). One struck otherwise,
  by 'shoot' (tests), is watched from above, the last shot's trails gone
  and the hand behind the cue ball, its cue following through as it
  meets the ball ('cueBackAt', drawn back the further the harder,
  'backswingOf'); once all rest the view is as it was, unless the
  player chose one meanwhile.
  A shot struck is played at once by the 'worker', in a process of its
  own, and streams back sampled as 'Recorder' has it; the window shows
  it as it comes, every 16 ms by as long as has passed, at most 50 ms,
  five times as far while the panel's '▸▸ Fast' is held ('playRate'),
  winding up and whirring meanwhile,
  waiting where it has not come yet. 'advance' shows it so much further
  at once; 'finish' shows it played out. The call is shown the moment
  it is known, a point at the touch making it ('Referee.decidedAt'),
  and the game kept once all rest. 'Replay' shows the last shot again,
  then the balls as they lie.

  Seen from above, in the corner or filling the view, the shot is drawn
  on the cloth as it goes, as a broadcast draws it: each ball's way in
  its colour, ball 1's boldest, faint balls where those that moved set
  off, and, while the toolbar's 'Hand' is ticked, a gloved hand holding
  the cue behind ball 1. It stays until the next shot, or until the balls
  are laid anew; a replay draws it again.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Three-cushion'
  __start_size__ = 1560, 940
  __frame_ms__ = 16  # between two frames
  __stroke_lead__ = 1.0  # s the drawn cue swings before it meets the ball
  __pull_least__ = 20.0  # px the mouse is pulled back before it counts
  __pull_reach__ = 400.0  # px pulled back for the panel's most power
  __spin_step__ = 0.05  # share of the radius an arrow key moves the hit
  __fast_rate__ = 5.0  # times as fast a shot is shown, played fast
  __fast_heard__: bool = False
  __preview_key__: tuple | None = None
  __preview_recordings__: list | None = None
  __preview_runs__: list | None = None
  __preview_rate__ = 250.0  # samples a second of a map's engine way
  __longest_frame__ = 0.05  # s a frame moves the balls on at most

  #  Private Variables
  __frame_clock__: float | None = None
  __window_mode__: str = 'game'
  __window_match__: Match | None = None
  __shot_record__: dict | None = None
  __shot_recording__: Recording | None = None
  __struck_balls__: tuple | None = None
  __play_recorder__: object = None
  __stay_put__: bool = False
  __flinging__: bool = False
  __fling_action__: object = None
  __fling_rise__ = 2000.0  # mm/s a flung pin is sent up (debug)
  __fling_tumble__ = 12.0  # rad/s a flung pin is set tumbling (debug)
  __shot_verdict__: tuple | None = None
  __play_time__: float = 0.0
  __play_kind__: str = ''
  __replay_balls__: tuple | None = None
  __mark_place__: tuple | None = None
  __mark_ball__: str = ''
  __mulligan_mark__: tuple | None = None
  __lag_first__: tuple | None = None
  __mulligan_balls__: tuple | None = None
  __grabbed_ball__: str = ''
  __rest_clock__: float | None = None
  __shot_trails__: Trails | None = None
  __opening_spot__: int = 4
  __overhead_before__: bool | None = None
  __stroke_start__: float | None = None
  __game_kind__: str = 'carom'
  __kegle_game__: KegleGame | None = None
  __placing_red__: bool = False
  __stroke_most__: float = 0.0
  __pull_press__: tuple | None = None
  __pull_back__: float = 0.0
  __pull_power__: float = 2.0
  __pull_armed__: bool = False
  __stay_down__: bool = False
  __pull_drawn__: float = 0.0
  __whole_before__: tuple | None = None
  __early_setup__: bool = False
  __early_at__: tuple | None = None
  __shot_history__: list | None = None
  __aimed_early__: bool = False
  __minimap_menu__: QMenu | None = None
  __use_menu__: QMenu | None = None
  __board_line__: str = ''
  __held_item__: str = 'cue'
  __inventory_open__: bool = False
  __board_tone__: str = 'neutral'

  #  Public Variables
  toolBar = AttriBox[BilliardsToolBar](THIS)
  view = AttriBox[TableView](THIS)
  unfoldedMap = AttriBox[UnfoldedMap](THIS)
  fullMap = AttriBox[UnfoldedMap](THIS)
  panel = AttriBox[ShotPanel](THIS)
  frameTimer = AttriBox[QTimer](THIS)
  motion = AttriBox[Motion]()
  cue = AttriBox[Cue]()
  worker = AttriBox[ShotWorker]()
  previewer = AttriBox[ShotWorker]()
  previewerLow = AttriBox[ShotWorker]()
  previewerHigh = AttriBox[ShotWorker]()
  sounds = AttriBox[BilliardsSounds]()
  moving = AttriBox[bool](False)
  playing = AttriBox[bool](False)
  overhead = AttriBox[bool](False)
  unfolded = AttriBox[bool](False)
  fullShown = AttriBox[bool](False)
  callShown = AttriBox[bool](False)
  ghosting = AttriBox[bool](False)
  turnLeftKey = AttriBox[QShortcut](THIS)
  turnRightKey = AttriBox[QShortcut](THIS)
  tiltUpKey = AttriBox[QShortcut](THIS)
  tiltDownKey = AttriBox[QShortcut](THIS)
  spinUpKey = AttriBox[QShortcut](THIS)
  spinDownKey = AttriBox[QShortcut](THIS)
  spinLeftKey = AttriBox[QShortcut](THIS)
  spinRightKey = AttriBox[QShortcut](THIS)
  centreKey = AttriBox[QShortcut](THIS)
  cancelKey = AttriBox[QShortcut](THIS)
  useKey = AttriBox[QShortcut](THIS)
  room = AttriBox[Room]()
  walking = AttriBox[bool](False)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """The 'initUI' method lays the window out, sizes it, begins a game
    and starts the frames."""
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 3)
    layout.addWidget(self.view, 1, 0)
    layout.addWidget(self.fullMap, 1, 0)
    layout.addWidget(self.unfoldedMap, 1, 1)
    layout.addWidget(self.panel, 1, 2)
    layout.setRowStretch(1, 1)
    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 0)
    self.unfoldedMap.hide()
    self.fullMap.unfolded = Unfolded(self.view.table, 3, 3)
    self.fullMap.fanned = True
    self.fullMap.hide()
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.setMode('game')
    self.__frame_clock__ = None
    self.frameTimer.start(self.__frame_ms__)
    self._warmWorker()
    self.sounds.start(QDir.tempPath())

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the buttons, the panel, the cloth,
    the frames and the menu."""
    bar, panel, view = self.toolBar, self.panel, self.view
    bar.caromButton.clicked.connect(lambda: self.setKind('carom'))
    bar.kegleButton.clicked.connect(lambda: self.setKind('kegler'))
    bar.gameButton.clicked.connect(lambda: self.setMode('game'))
    bar.sandboxButton.clicked.connect(lambda: self.setMode('sandbox'))
    bar.resetButton.clicked.connect(self.newGame)
    bar.mulliganButton.clicked.connect(self.mulligan)
    bar.replayButton.clicked.connect(self.replay)
    bar.topButton.clicked.connect(self.toggleOverhead)
    bar.mapButton.clicked.connect(self.toggleUnfolded)
    bar.fullButton.clicked.connect(self.toggleFullMap)
    bar.soundBox.toggled.connect(self._soundToggled)
    self.unfoldedMap.aimDragged.connect(self.aimFromMap)
    self.fullMap.aimDragged.connect(self.aimFromMap)
    bar.viewSlider.quantityChanged.connect(view.setFieldOfView)
    panel.powerSlider.quantityChanged.connect(
      lambda *_: view.setAimSpeed(panel.speed))
    bar.moveButton.clicked.connect(self.toggleMoving)
    bar.handBox.toggled.connect(view.setHandShown)
    bar.shadowBox.toggled.connect(view.setShadowShown)
    view.pinTapped.connect(self.flingPin)
    panel.markAsked.connect(self.markAlongCamera)
    panel.cueChanged.connect(lambda *_: self.refresh())
    panel.lookChanged.connect(self._lookChanged)
    keys = ((self.turnLeftKey, Qt.Key.Key_A, 1.0, 0.0),
            (self.turnRightKey, Qt.Key.Key_D, -1.0, 0.0),
            (self.tiltUpKey, Qt.Key.Key_W, 0.0, -1.0),
            (self.tiltDownKey, Qt.Key.Key_S, 0.0, 1.0))
    for shortcut, key, yaw, pitch in keys:
      shortcut.setKey(QKeySequence(key))
      shortcut.setAutoRepeat(True)
      shortcut.activated.connect(self._stepper(yaw, pitch))
    spins = ((self.spinUpKey, Qt.Key.Key_Up, 1.0, 0.0),
             (self.spinDownKey, Qt.Key.Key_Down, -1.0, 0.0),
             (self.spinLeftKey, Qt.Key.Key_Left, 0.0, -1.0),
             (self.spinRightKey, Qt.Key.Key_Right, 0.0, 1.0))
    for shortcut, key, top, side in spins:
      shortcut.setKey(QKeySequence(key))
      shortcut.setAutoRepeat(True)
      shortcut.activated.connect(self._spinner(top, side))
    self.centreKey.setKey(QKeySequence(Qt.Key.Key_End))
    self.centreKey.setAutoRepeat(False)
    self.centreKey.activated.connect(panel.picker.centre)
    self.cancelKey.setKey(QKeySequence(Qt.Key.Key_Escape))
    self.cancelKey.setAutoRepeat(False)
    self.cancelKey.setEnabled(False)
    self.cancelKey.activated.connect(self.cancelStroke)
    self.useKey.setKey(QKeySequence(Qt.Key.Key_E))
    self.useKey.setAutoRepeat(False)
    self.useKey.activated.connect(self.useAsked)
    view.escapeAsked.connect(self._escapeAsked)
    view.itemChosen.connect(self.chooseItem)
    view.setRoom(self.room.layout())
    panel.breakChosen.connect(self.chooseBreak)
    panel.spotChosen.connect(self.chooseSpot)
    panel.respotAsked.connect(self.respot)
    panel.skipAsked.connect(self.skipLag)
    panel.distanceAsked.connect(self.nextDistance)
    panel.placeAsked.connect(self.togglePlaceRed)
    view.sceneLoaded.connect(self._sceneLoaded)
    view.clothPressed.connect(self.grab)
    view.clothDragged.connect(self.drag)
    view.clothReleased.connect(self.letGo)
    view.tableTapped.connect(self.tapTable)
    view.strokePressed.connect(self.pullPressed)
    view.strokeMoved.connect(self.pullMoved)
    view.strokeReleased.connect(self.pullReleased)
    view.strokeCancelled.connect(self.cancelStroke)
    view.aimTouched.connect(self._aimBegun)
    view.minimapMenuAsked.connect(self._minimapMenuAt)
    self.frameTimer.timeout.connect(self.tick)
    self.mainMenuBar.fileMenu.exitAction.triggered.connect(self.close)
    debug = self.mainMenuBar.addMenu('Debug')
    fling = debug.addAction('Fling pins')
    fling.setCheckable(True)
    fling.setShortcut(QKeySequence(Qt.Key.Key_F8))
    fling.toggled.connect(self.setFlinging)
    self.__fling_action__ = fling
    self._layoutViews()

  def closeEvent(self, event: QCloseEvent) -> None:
    """Closing the window stops the frames and the worker."""
    MainWindow.closeEvent(self, event)
    if event.isAccepted():
      self.frameTimer.stop()
      self.worker.close()
      for previewer in self.previewers():
        previewer.close()
      self.sounds.close()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def mode(self, ) -> str:
    """The 'mode' method returns 'game' or 'sandbox'."""
    return self.__window_mode__

  def isKegler(self, ) -> bool:
    """The 'isKegler' method tells whether keglebillard is played, not
    three-cushion."""
    return self.__game_kind__ == 'kegler'

  def kegleGame(self, ) -> KegleGame:
    """The 'kegleGame' method returns keglebillard's game kept, its
    game loop, a new one lagging if none."""
    if self.__kegle_game__ is None:
      self.__kegle_game__ = KegleGame(KegleTable(self.view.table)).begun()
    return self.__kegle_game__

  def match(self, ) -> Match | KegleMatch:
    """The 'match' method returns the match kept, keglebillard's when it
    is played ('kegleGame'); else three-cushion's, a new one if none was
    begun."""
    if self.isKegler():
      return self.kegleGame().match
    if self.__window_match__ is None:
      self.__window_match__ = Match(Rules()).begun()
    return self.__window_match__

  def referee(self, ) -> Referee:
    """The 'referee' method returns three-cushion's referee, judging by
    the match's rules on the table of the motion; keglebillard lags as
    three-cushion does, by the default rules."""
    if self.isKegler():
      return Referee(Rules(), self.motion)
    return Referee(self.match().rules, self.motion)

  def cueBall(self, ) -> Ball:
    """The 'cueBall' method returns the ball the panel strikes."""
    name = self.panel.cueName
    return {ball.name: ball for ball in self.view.balls}[name]

  def lookBall(self, ) -> Ball:
    """The 'lookBall' method returns the ball the camera turns round:
    looking from the ghost, the ghost, as the cue ball where it is."""
    if self.ghosting:
      x, y = self.markPlace()
      return Ball(self.panel.cueName, x, y)
    name = self.panel.lookName
    return {ball.name: ball for ball in self.view.balls}[name]

  def markPlace(self, ) -> tuple[float, float] | None:
    """The 'markPlace' method returns where the ghost ball is on the
    table, 'None' when there is none; looking from the ghost, where it
    has been carried to."""
    if self.ghosting:
      return self.view.ghostPlace()
    return self.__mark_place__

  def markBall(self, ) -> str:
    """The 'markBall' method returns the name of the ball the ghost is
    marked against, empty when there is no mark."""
    return self.__mark_ball__ if self.__mark_place__ else ''

  def recorderFor(self, balls: tuple[Ball, ...],
                  rate: float = 1000.0) -> Recorder | KegleRecorder:
    """The 'recorderFor' method returns the recorder a shot of 'balls',
    as they lie as it is struck, is played by, on the table of the
    motion, 'rate' samples a second; in keglebillard with the pins, those
    set up clear of the balls ('KegleTable.pinsPlaced')."""
    if not self.isKegler():
      return Recorder(self.motion, rate)
    kegle = KegleTable(self.view.table)
    return KegleRecorder(KegleMotion(kegle, self.motion), rate, 50, 60.0,
                         kegle.pinsPlaced(balls))

  def recording(self, ) -> Recording | None:
    """The 'recording' method returns the last shot as it has come so
    far, taking in what has come of it since; 'None' if none was
    struck."""
    if self.playing and self.__play_kind__ == 'shot':
      return self._received()
    return self.__shot_recording__

  def openingSpot(self, ) -> int:
    """The 'openingSpot' method returns the spot the cue ball lies on,
    4 or 5, while the balls lie as a game opens for it; nought when they
    do not. In a game the cue ball is the one the match says, in the
    sandbox the one chosen; a carom opening is white's or yellow's, so
    nought for red, as laid out for keglebillard."""
    if self.__window_mode__ == 'game':
      cue = self.match().cueBall()
    else:
      cue = self.panel.cueName
    if cue not in ('white', 'yellow') or self.isKegler():
      return 0
    table, balls = self.view.table, self.view.balls
    for number in (4, 5):
      if balls == table.openingFor(cue, number):
        return number
    return 0

  def canReplay(self, ) -> bool:
    """The 'canReplay' method tells whether the last shot can be shown
    again: it was played out, and nothing is under way."""
    recording = self.__shot_recording__
    if recording is None or not recording.over or self.playing:
      return False
    return self.__shot_verdict__ is not None

  def settingUp(self, ) -> bool:
    """The 'settingUp' method tells whether the next shot may be set up
    (the user): the balls at rest, or, while a shot is still shown, the
    ball the next is played with lying where it stays, if spinning in
    place, the game already kept; struck only once all rest
    ('resting')."""
    return self.resting() or self.__early_setup__

  def resting(self, ) -> bool:
    """The 'resting' method tells whether no shot is being shown, nor
    about to be struck, and every ball is still and touches nothing it
    is moving into."""
    if self.playing:
      return False
    motion, radius = self.motion, self.view.table.radius
    balls = self.view.balls
    if motion.inContact(balls):
      return False
    return all(motion.cloth.phaseOf(ball, radius) == 'still'
               for ball in balls)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setMode(self, mode: str) -> None:
    """The 'setMode' method plays a 'game', begun anew, or the
    'sandbox', the balls left as they lie."""
    self._stopPlaying()
    self._clearMark()
    self._clearTrails()
    self.__shot_record__ = None
    self.__shot_history__ = []
    self.__window_mode__ = mode
    self.toolBar.showMode(mode)
    self.panel.callWords = ''
    self._stopMoving()
    self._stopPlacing()
    if mode == 'game':
      self.newGame()
    else:
      self.__mulligan_balls__ = None
      self.refresh()

  def newGame(self, ) -> None:
    """The 'newGame' method begins anew: in a game, a new match from the
    lag; in the sandbox, the balls as a game opens for the cue ball
    chosen, on the side last chosen."""
    table, spot = self.view.table, self.__opening_spot__
    self._stopPlaying()
    self._clearMark()
    self._clearTrails()
    self.__shot_record__ = None
    self.__shot_history__ = []
    self.__lag_first__ = None
    self.__mulligan_balls__ = None
    self.panel.callWords = ''
    self._stopPlacing()
    if self.__window_mode__ == 'game' and self.isKegler():
      game = self.kegleGame()
      self.__kegle_game__ = game.withDistance(game.match.distance)
      self.view.balls = self.kegleGame().lagBalls()
      self._raisePins(self.view.balls)
      self._faceTheFoot()
    elif self.__window_mode__ == 'game':
      self.__window_match__ = Match(Rules()).begun()
      match = self.match()
      if match.phase == 'lag':
        self.view.balls = table.lagPosition()
      else:
        self.view.balls = table.openingFor(match.cueBall(), spot)
      self._faceTheFoot()
    elif self.isKegler():
      self.view.balls = KegleTable(table).opening()
      self._raisePins(self.view.balls)
      self.panel.chooseCue('red')
    else:
      self.view.balls = table.openingFor(self.panel.cueName, spot)
    self.refresh()

  def refresh(self, ) -> None:
    """The 'refresh' method shows how things stand: the score, the
    status, the choices, the cue ball, and the aim from it."""
    panel = self.panel
    if self.__window_mode__ == 'game' and self.isKegler():
      self._showKegleGame()
    elif self.__window_mode__ == 'game':
      self._showGame()
    else:
      panel.heading = 'Sandbox'
      panel.setSkipAvailable(False)
      panel.scoreRows = ()
      panel.status = ('Any ball, from anywhere; the referee calls each '
                      'shot.')
      panel.setCueFree(True)
      choices = []
      if self.resting() and self.openingSpot():
        choices.append('spot')
      if self._frozenBalls() and not self.isKegler():
        choices.append('respot')
      panel.showChoices(tuple(choices))
      panel.showSpot(self.openingSpot())
      panel.ready = self.settingUp()
    self.toolBar.replayButton.setEnabled(self.canReplay())
    self._aim()
    self._pushBoards()

  def pullPressed(self, x: float, y: float) -> None:
    """The 'pullPressed' method begins a stroke (the user): the right
    button pressed at 'x', 'y' on the view, the cue then pulled back as
    a spring by pulling the mouse back towards the player ('pullMoved'),
    and let fly as the button is let go ('pullReleased'), the only way a
    shot is made (the user). Pressed while no shot may be struck, the
    balls still rolling, another ball looked from, balls being moved or
    the game not letting it, it is refused, a barrier shown over the
    ball (the user)."""
    if not self._strikes() or self.panel.marking():
      self.view.flashBarrier()
      return
    self.__pull_press__ = (x, y)
    self.__pull_back__ = 0.0
    self.__pull_armed__ = False
    self.__pull_power__ = self.panel.powerSlider.quantity
    self.cancelKey.setEnabled(True)
    self._aimBegun()

  def pullMoved(self, x: float, y: float) -> None:
    """The 'pullMoved' method follows the stroke, the mouse at 'x', 'y':
    pulled back far enough it counts, the hand shown from above, its cue
    and the cue in the scene drawn back the further the harder, the
    speedometer showing how fast the ball would go ('springSpeed');
    pushed back to where it was pressed, it stands down again."""
    press = self.__pull_press__
    if press is None:
      return
    back = max(y - press[1], 0.0)
    self.__pull_back__ = back
    if not self.__pull_armed__ and back >= self.__pull_least__:
      heading = self.view.cameraHeading()
      if heading is None:
        return
      self.__pull_armed__ = True
      panel = self.panel
      self._clearTrails()
      self._showHands(self._struckBalls(
        (*heading, panel.speed, panel.top, panel.side)))
    if self.__pull_armed__:
      self._showSpring()

  def pullReleased(self, ) -> None:
    """The 'pullReleased' method lets the stroke fly, the right button
    let go: pulled back past '__pull_least__', the cue ball is struck at
    once as fast as the spring says ('springSpeed', 'strikeAt'); short of
    it, nothing, the hand taken away, the power as it was."""
    armed = self.__pull_press__ is not None and self.__pull_armed__
    back = self.__pull_back__
    strikes = armed and back >= self.__pull_least__
    self._standDown(not strikes)
    if strikes:
      self.strikeAt(self.springSpeed(back))

  def cancelStroke(self, ) -> None:
    """The 'cancelStroke' method calls off the stroke under way (the
    user: a left click or Escape while pulling back): nothing struck,
    the cue and the speedometer hidden, the hand taken away; letting the
    right button go then strikes nothing."""
    self._standDown(True)

  def springSpeed(self, back: float) -> float:
    """The 'springSpeed' method returns how fast the stroke sends the
    cue ball, m/s, the mouse pulled 'back' px towards the player: the
    panel's least power just past '__pull_least__', its most at
    '__pull_reach__', growing as the square of the pull between, so the
    soft shots, the most played, get the most of the mouse's way."""
    slider = self.panel.powerSlider
    least, reach = self.__pull_least__, self.__pull_reach__
    share = min(max((back - least) / (reach - least), 0.0), 1.0)
    return slider.low + (slider.high - slider.low) * share * share

  def strikeAt(self, speed: float) -> None:
    """The 'strikeAt' method strikes the cue ball at once the way the
    camera faces, sent at 'speed' m/s, the panel's power set to it, the
    point struck as the panel has it; the shot watched from where the
    player stands, not from above (the user)."""
    heading = self.view.cameraHeading()
    if heading is None or not self._strikes():
      return
    panel = self.panel
    panel.powerSlider.quantity = speed
    self.__stay_down__ = True
    try:
      self._strike((*heading, panel.speed, panel.top, panel.side))
    finally:
      self.__stay_down__ = False

  def _standDown(self, cleared: bool) -> None:
    """Ends the stroke: forgotten, Escape no longer calling it off, the
    cue and the speedometer hidden if it had counted, and, 'cleared',
    nothing struck, the hand taken away and the power shown as it was
    before the pull."""
    armed = self.__pull_press__ is not None and self.__pull_armed__
    self.__pull_press__ = None
    self.__pull_armed__ = False
    self.__pull_back__ = 0.0
    self.cancelKey.setEnabled(False)
    if not armed:
      return
    self.view.setCueBack(0.0)
    self.view.hideStick()
    self.view.hideGauge()
    if cleared:
      self._clearTrails()
      self.panel.powerSlider.quantity = self.__pull_power__

  def _showSpring(self, ) -> None:
    """Shows the stroke as it is pulled: the cue from above and in the
    scene drawn back by the share of '__pull_reach__' pulled, at most
    'STROKE_MOST', at the point the panel strikes; the speedometer at
    the speed it would send the ball, the panel's power showing it too."""
    back = self.__pull_back__
    least, reach = self.__pull_least__, self.__pull_reach__
    share = min(max((back - least) / (reach - least), 0.0), 1.0)
    drawn = STROKE_MOST * share
    self.__pull_drawn__ = drawn
    self.view.setCueBack(drawn)
    slider = self.panel.powerSlider
    speed = self.springSpeed(back)
    slider.quantity = speed
    self.view.setGauge(speed, slider.high)
    heading = self.view.cameraHeading()
    if heading is not None:
      panel = self.panel
      self.view.setStick(self.cueBall(), heading, drawn, panel.top,
                         panel.side)

  def shoot(self, aimX: float, aimY: float) -> None:
    """The 'shoot' method strikes the cue ball at once at the point the
    panel says so it leaves along the aim 'aimX', 'aimY' at the power the
    panel says, the stick laid off the aim by the squirt as a player
    allows for it, if the balls rest and the game lets it; in a lag, the
    first call sets white's shot, the second strikes both at once."""
    panel = self.panel
    self._strike((aimX, aimY, panel.speed, panel.top, panel.side))

  def setFlinging(self, flinging: bool) -> None:
    """The 'setFlinging' method turns the debug 'Fling pins' on or off
    (menu 'Debug', F8; the user: to see a pin go over a cushion at
    will): on, a click on a keglebillard pin sends it flying
    ('flingPin'), a tag over the table saying so."""
    self.__flinging__ = True if flinging else False
    action = self.__fling_action__
    if action is not None and action.isChecked() != self.__flinging__:
      action.setChecked(self.__flinging__)
    self.view.setFlinging(self.__flinging__)

  def flingPin(self, number: int) -> None:
    """The 'flingPin' method, a debug ('Fling pins', 'setFlinging'; the
    user: to see a pin go over a cushion at will), sends pin 'number'
    flying over the nearest cushion as a shot of its own, the balls at
    rest: given a
    speed and a tumble as the cue gives a ball, at the top of its flight
    as it crosses the cushion, the physics all as it has it from then
    on; the game left as it was, the balls as they lie after. Nothing in
    three-cushion, while anything moves, or for a pin not set up."""
    if not self.isKegler() or not self.resting() or self.moving:
      return
    if self.walking or not self.__flinging__:
      return
    balls = self.view.balls
    kegle = KegleTable(self.view.table)
    if number not in kegle.pinsPlaced(balls):
      return
    plain = self.recorderFor(balls)
    recorder = KegleRecorder(plain.motion, plain.rate, plain.size,
                             plain.longest, plain.numbers,
                             (flingOf(kegle, self.motion.cloth.gravity,
                                      number, self.__fling_rise__,
                                      self.__fling_tumble__),))
    self._stopPlacing()
    self._clearMark()
    self._clearTrails()
    self.__shot_record__ = {'kind': 'fling', 'pin': number}
    self._playOut(balls, recorder)
    self.__stay_put__ = True
    try:
      self._started()
    finally:
      self.__stay_put__ = False

  def showKegler(self, ) -> None:
    """The 'showKegler' method lays the table out for keglebillard, a
    look at the second game while it is built: the cyan cloth, the six
    holes and the five pins standing, the whites on their spots and red,
    the cue ball, in hand at the head end, in the sandbox. The balls
    knock the pins over ('KegleRecorder'), the pins set up again once
    the balls rest; the holes do not yet take a ball."""
    self.setMode('sandbox')
    self.setKind('kegler')
    self._faceTheFoot()
    self.refresh()

  def setKind(self, kind: str) -> None:
    """The 'setKind' method plays 'kind', 'carom' for three-cushion or
    'kegler' for keglebillard, begun anew in the mode it is in: the
    table laid out for it, its game loop kept."""
    self._stopPlaying()
    self._stopPlacing()
    self.__game_kind__ = 'kegler' if kind == 'kegler' else 'carom'
    self.__kegle_game__ = None
    self.toolBar.showKind(self.__game_kind__)
    self.view.setKegler(self.isKegler())
    self.panel.setKegler(self.isKegler())
    for shown in (self.unfoldedMap, self.fullMap):
      shown.setKegler(self.isKegler())
    if not self.isKegler() and self.panel.cueName == 'red':
      self.panel.chooseCue('white')
    self.newGame()

  def nextDistance(self, ) -> None:
    """The 'nextDistance' method has a keglebillard game, at its lag
    before a shot is set, played to the next distance there is (200 to
    800 in hundreds, the user), begun anew."""
    match = self.match()
    if not self.isKegler() or self.__window_mode__ != 'game':
      return
    if match.phase != 'lag' or self.playing or self.__lag_first__:
      return
    self.__kegle_game__ = self.kegleGame().nextDistance()
    self.refresh()

  def togglePlaceRed(self, ) -> None:
    """The 'togglePlaceRed' method lets a drag on the cloth put red,
    in hand in a keglebillard game, down within a quarter of either
    short cushion; or the camera again."""
    match = self.match()
    if not self.isKegler() or self.__window_mode__ != 'game':
      return
    if match.phase != 'play' or not match.inHand or self.playing:
      return
    self.__placing_red__ = not self.__placing_red__
    self.view.setMoving(self.__placing_red__ or self.moving)
    self.refresh()

  def spinBy(self, top: float, side: float) -> None:
    """The 'spinBy' method moves the point struck 'top' steps up and
    'side' steps right, '__spin_step__' of the radius a step, kept where
    the cue would not miscue."""
    picker, step = self.panel.picker, self.__spin_step__
    picker.setHit(picker.top + top * step, picker.side + side * step)

  def backswingOf(self, speed: float) -> float:
    """The 'backswingOf' method returns how far back the cue is drawn,
    in mm, to send the cue ball off at 'speed' mm/s: the further the
    harder, its tip never back into the bridge."""
    return min(30.0 + 0.015 * speed, STROKE_MOST)

  def markAlongCamera(self, ) -> None:
    """The 'markAlongCamera' method marks where the cue ball must meet
    the ball looked from to send it the way the camera faces."""
    heading = self.view.cameraHeading()
    if heading is not None:
      self.mark(*heading)

  def mark(self, aimX: float, aimY: float) -> None:
    """The 'mark' method shows a ghost of the cue ball where it must meet
    the ball looked from to send that along 'aimX', 'aimY': two radii
    back along the line from its middle, touching it at the point
    opposite the way it is to go. Only while all rest, and not on the
    cue ball itself. Looking from the ghost, it marks where the ghost is
    now, the hit that sends the cue ball the way the camera faces. The
    mark knows nothing of throw or spin, as a cue laid on the ball does
    not."""
    if not self.resting() or not self.panel.marking():
      return
    if self.ghosting:
      place = self.view.ghostPlace()
      if place is not None:
        self._setMark(*place, self.__mark_ball__)
      return
    length = math.hypot(aimX, aimY)
    if length <= 0.0:
      return
    named = {ball.name: ball for ball in self.view.balls}
    name = self.panel.lookName
    ball, apart = named[name], 2.0 * self.view.table.radius
    self._setMark(ball.x - apart * aimX / length,
                  ball.y - apart * aimY / length, name)

  def toggleOverhead(self, ) -> None:
    """The 'toggleOverhead' method shows the view from above instead of
    the camera's, the corner hidden, or the camera's view again, the
    view from above in the corner; chosen during a shot, the view stays so
    once all rest."""
    self.__overhead_before__ = None
    self._setOverhead(not self.overhead)

  def toggleUnfolded(self, ) -> None:
    """The 'toggleUnfolded' method shows or hides the map of the table
    unfolded beside it."""
    self.unfolded = not self.unfolded
    self.toolBar.mapButton.checked = self.unfolded
    self.toolBar.mapButton.update()
    self.unfoldedMap.setVisible(self.unfolded)
    self._showUnfolded()

  def toggleFullMap(self, ) -> None:
    """The 'toggleFullMap' method shows the full map, 7 by 7 tables,
    instead of the table, or the table again."""
    self.fullShown = not self.fullShown
    self.toolBar.fullButton.checked = self.fullShown
    self.toolBar.fullButton.update()
    self._layoutViews()
    self._showUnfolded()

  def aimFromMap(self, aimX: float, aimY: float) -> None:
    """The 'aimFromMap' method turns the camera to aim from the cue ball
    the way 'aimX', 'aimY' on the table, a map's drag having chosen it:
    while the balls rest and the cue ball is looked from."""
    panel = self.panel
    if not self.resting() or self.ghosting or self.moving:
      return
    if panel.lookName != panel.cueName:
      return
    self.view.faceCamera(aimX, aimY)
    self._aimBegun()
    self._showUnfolded()

  def tapTable(self, x: float, y: float) -> None:
    """The 'tapTable' method looks from the ball nearest 'x', 'y' on the
    table, if one is within a ball's width of it."""
    if self.moving or not self.view.balls:
      return
    radius = self.view.table.radius
    nearest = min(self.view.balls,
                  key=lambda ball: math.hypot(ball.x - x, ball.y - y))
    if math.hypot(nearest.x - x, nearest.y - y) < 2.0 * radius:
      self.panel.chooseLook(nearest.name)

  def tick(self, ) -> None:
    """The 'tick' method shows the shot under way on by as long as has
    passed since the last frame, at most 50 ms."""
    now = time.monotonic()
    passed = now - (self.__frame_clock__ or now)
    self.__frame_clock__ = now
    if self.walking:
      self.view.turnAtEdge(min(max(passed, 0.0), self.__longest_frame__))
    self._stroke(now)
    self.sounds.heard()
    fast = self.playing and self.panel.fast
    if fast != self.__fast_heard__:
      self.__fast_heard__ = fast
      self.sounds.fastForward(fast)
    self.advance(min(max(passed, 0.0), self.__longest_frame__)
                 * self.playRate())
    self._showTrenches()
    if self.unfolded or self.fullShown:
      self._showUnfolded()

  def playRate(self, ) -> float:
    """The 'playRate' method returns how many times as fast as it
    happened the shot under way is shown: faster while the panel's '▸▸
    Fast' is held down."""
    return self.__fast_rate__ if self.panel.fast else 1.0

  def advance(self, seconds: float) -> None:
    """The 'advance' method shows the shot under way 'seconds' further,
    as far as it has come; its call once known; and, once all rest, the
    game kept."""
    if not self.playing:
      return
    recording = self._received()
    if not recording.count():
      return
    before = self.__play_time__
    self.__play_time__ = min(self.__play_time__ + seconds,
                             recording.known())
    self.view.balls = recording.ballsAt(self.__play_time__)
    if recording.pinParts:
      self.view.setPins(recording.pinsAt(self.__play_time__))
    self.sounds.between(recording, before, self.__play_time__)
    self._followTrails(recording)
    self._showCounter(recording)
    self._callIfDue()
    if recording.over and self.__play_time__ >= recording.known():
      self._ended()
      return
    self._setUpEarly(recording)

  def finish(self, ) -> None:
    """The 'finish' method shows the shot under way played out at once,
    waiting for the rest of it to come, the call made and the game
    kept."""
    if not self.playing:
      return
    recording = self._received()
    while not recording.over:
      stretches = self.worker.waited(5.0)
      if not stretches:
        recording = self._playedHere()
        break
      for stretch in stretches:
        recording = recording.joined(stretch)
      self.__shot_recording__ = recording
    self.advance(recording.known() + 1.0)

  def replay(self, ) -> None:
    """The 'replay' method shows the last shot again, from the moment it
    was struck, the call when it was known; then the balls as they lie
    now."""
    if not self.canReplay() or self.__grabbed_ball__:
      return
    self.__replay_balls__ = self.view.balls
    self._clearTrails()
    self.__play_kind__ = 'replay'
    self.__play_time__ = 0.0
    self.panel.callWords = ''
    self.callShown = False
    self.playing = True
    self.view.balls = self.__shot_recording__.ballsAt(0.0)
    self._started()

  def chooseBreak(self, breaks: bool) -> None:
    """The 'chooseBreak' method has the lag's winner break, or let the
    other break; in keglebillard lay out, or let the other."""
    if self.isKegler():
      self.__kegle_game__ = self.kegleGame().chosen(breaks)
      self._clearMark()
      self._clearTrails()
      self.view.balls = self.kegleGame().layoutBalls()
      self._raisePins(self.view.balls)
      self._faceTheFoot()
      self.refresh()
      return
    match = self.match().chosen(breaks)
    self.__window_match__ = match
    self._clearMark()
    self._clearTrails()
    self.view.balls = self.view.table.openingFor(match.cueBall(),
                                                 self.__opening_spot__)
    self._faceTheFoot()
    self.refresh()

  def skipLag(self, ball: str = None) -> None:
    """The 'skipLag' method skips the lag of a game: a coin decides who
    breaks, or 'ball' wins, white the first player's, yellow the
    second's; the winner breaks, playing white from the spot chosen."""
    match = self.match()
    if self.__window_mode__ != 'game' or match.phase != 'lag':
      return
    if self.playing:
      return
    winner = ball or random.choice(('white', 'yellow'))
    if self.isKegler():
      game = self.kegleGame().lagged(winner).chosen(True)
      self.__kegle_game__ = game
      self.__lag_first__ = None
      self.__shot_record__ = None
      self._clearMark()
      self._clearTrails()
      self.view.balls = game.layoutBalls()
      self._raisePins(self.view.balls)
      self._faceTheFoot()
      self.panel.callWords = ('Lag skipped: %s lays out, a coin '
                              'decided.' % game.match.names[
                                game.match.starter])
      self.refresh()
      return
    match = match.lagged(winner).chosen(True)
    self.__window_match__ = match
    self.__lag_first__ = None
    self.__shot_record__ = None
    self._clearMark()
    self._clearTrails()
    self.view.balls = self.view.table.openingFor(match.cueBall(),
                                                 self.__opening_spot__)
    self._faceTheFoot()
    self.panel.callWords = 'Lag skipped: %s breaks, a coin decided.' % (
      match.names[match.starter])
    self.refresh()

  def chooseSpot(self, number: int) -> None:
    """The 'chooseSpot' method lays the cue ball on spot 'number', 4 on
    the left of the head spot or 5 on the right, as the player breaking
    sees it, while the balls lie as a game opens: in a game before the
    break or the equalizing inning, in the sandbox before the first shot
    from there. The side is kept for the openings to come."""
    if self.playing or not self.openingSpot():
      return
    if self.__window_mode__ == 'game':
      cue = self.match().cueBall()
    else:
      cue = self.panel.cueName
    self.__opening_spot__ = number
    self._clearMark()
    self._clearTrails()
    self.view.balls = self.view.table.openingFor(cue, number)
    self.refresh()

  def respot(self, ) -> None:
    """The 'respot' method puts the cue ball and the balls frozen to it
    back on their spots (2.2.07-E)."""
    frozen = self._frozenBalls()
    if not frozen:
      return
    cue = self.panel.cueName
    self._clearMark()
    self._clearTrails()
    self.view.balls = self.view.table.respotted(self.view.balls, cue,
                                                (cue, *frozen))
    self.refresh()

  def mulligan(self, ) -> None:
    """The 'mulligan' method takes the last shot back, in the sandbox:
    the balls as they were before it, and its mark, if it had one, as it
    was; even while the shot is under way."""
    if self.__window_mode__ != 'sandbox' or self.__mulligan_balls__ is None:
      return
    self._stopPlaying()
    self._clearMark()
    self._clearTrails()
    self.__shot_record__ = None
    history = self.__shot_history__
    if history and history[-1][4] == self.__mulligan_balls__:
      history.pop()
    self.view.balls = self.__mulligan_balls__
    self._raisePins(self.view.balls)
    if self.__mulligan_mark__ is not None:
      (x, y), name = self.__mulligan_mark__
      self._setMark(x, y, name)
    self.refresh()

  def turnAim(self, yaw: float, pitch: float) -> None:
    """The 'turnAim' method turns the camera round what it looks at by
    'yaw' and 'pitch' steps of 'Aim step': left and up for one."""
    step = self.toolBar.stepSlider.quantity
    self.view.turnCamera(yaw * step, pitch * step)
    self._aimBegun()

  def toggleMoving(self, ) -> None:
    """The 'toggleMoving' method lets a drag on the cloth move balls, in
    the sandbox, or the camera again."""
    if self.__window_mode__ != 'sandbox':
      return
    self.moving = not self.moving
    self.toolBar.moveButton.checked = self.moving
    self.toolBar.moveButton.update()
    self.view.setMoving(self.moving)
    self.refresh()

  def grab(self, x: float, y: float) -> None:
    """The 'grab' method takes hold of the ball nearest 'x', 'y' on the
    table, if one is within a ball's width and all rest; red alone
    while red in hand is put down ('togglePlaceRed')."""
    if self.__placing_red__ and self.resting():
      red = {ball.name: ball for ball in self.view.balls}['red']
      if math.hypot(red.x - x, red.y - y) < 2.0 * self.view.table.radius:
        self.__grabbed_ball__ = 'red'
      return
    if not self.moving or not self.resting():
      return
    radius = self.view.table.radius
    nearest = min(self.view.balls,
                  key=lambda ball: math.hypot(ball.x - x, ball.y - y))
    if math.hypot(nearest.x - x, nearest.y - y) < 2.0 * radius:
      self.__grabbed_ball__ = nearest.name

  def drag(self, x: float, y: float) -> None:
    """The 'drag' method moves the ball held to 'x', 'y', kept on the
    cloth and off the other balls."""
    name = self.__grabbed_ball__
    if not name:
      return
    if self.__placing_red__:
      placed = self.kegleGame().redPlaced(self.view.balls, x, y)
      if placed is not None:
        self.view.balls = placed
      return
    table, motion = self.view.table, self.motion
    reach = motion.reach()
    x = min(max(x, reach), table.width - reach)
    y = min(max(y, reach), table.length - reach)
    for ball in self.view.balls:
      if ball.name != name and math.hypot(ball.x - x, ball.y - y) < (
          2.0 * table.radius):
        return
    self.view.balls = tuple(Ball(name, x, y, ball.turn)
                            if ball.name == name else ball
                            for ball in self.view.balls)

  def letGo(self, ) -> None:
    """The 'letGo' method lets go of the ball held."""
    if self.__grabbed_ball__:
      self.__grabbed_ball__ = ''
      self.__mulligan_balls__ = None
      self._clearMark()
      self._clearTrails()
      self._raisePins(self.view.balls)
      self.refresh()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _showGame(self, ) -> None:
    """Shows the game: the score, how the match stands, the choices,
    the cue ball it gives, and whether it may be struck."""
    panel, match = self.panel, self.match()
    rules = match.rules
    heading = 'Game to %d' % rules.distance
    if rules.sets:
      heading += ', set %d' % match.setNumber
    panel.heading = heading
    rows = []
    for k in (0, 1):
      playing = k == match.current and match.phase not in ('lag', 'over')
      run = match.run if k == match.current else 0
      rows.append((playing, '%s, %s' % (match.names[k], match.balls[k]),
                   '%d' % match.scores[k], '%d' % match.innings[k],
                   '%.3f' % match.average(k), '%d' % match.best[k],
                   match.balls[k], '%d' % run))
    panel.scoreRows = tuple(rows)
    status = match.said()
    if match.phase == 'lag':
      lagger = 'Yellow' if self.__lag_first__ is not None else 'White'
      status += ': %s sets the shot.' % lagger
    panel.status = status
    panel.setCueFree(False)
    panel.setSkipAvailable(match.phase == 'lag' and not self.playing)
    panel.setChooseWords('Break', 'Let the other break')
    choices = []
    if match.phase == 'choose':
      choices.append('choose')
    if match.needsOpening() and self.__shot_record__ is None:
      choices.append('spot')
    if match.phase == 'play' and self._frozenBalls():
      choices.append('respot')
    panel.showChoices(tuple(choices))
    panel.showSpot(self.openingSpot())
    if match.phase == 'lag':
      panel.chooseCue('yellow' if self.__lag_first__ is not None
                      else 'white')
    elif match.phase not in ('choose', 'over'):
      panel.chooseCue(match.cueBall())
    panel.ready = self.settingUp() and match.phase not in ('choose',
                                                           'over')

  def _showKegleGame(self, ) -> None:
    """Shows keglebillard's game: the score, how the match stands, the
    choices (the distance before the lag, who lays out, red put down in
    hand), red the cue ball, and whether it may be struck."""
    panel, match = self.panel, self.match()
    panel.heading = 'Kegler to %d' % match.distance
    rows = []
    for k in (0, 1):
      playing = k == match.current and match.phase not in ('lag', 'over')
      run = match.run if k == match.current else 0
      rows.append((playing, match.names[k], '%d' % match.scores[k],
                   '%d' % match.series[k], '%.2f' % match.average(k),
                   '%d' % match.best[k], ('white', 'yellow')[k],
                   '%d' % run))
    panel.scoreRows = tuple(rows)
    status = match.said()
    lag = match.phase == 'lag'
    if lag:
      lagger = 'The marked white' if self.__lag_first__ is not None else (
        'White')
      status += ': %s sets the shot.' % lagger
    inHand = match.phase == 'play' and match.inHand and not self.playing
    if inHand:
      status += (' Red in hand: Place red, then drag it within a quarter '
                 'of either short cushion.')
    panel.status = status
    panel.setCueFree(False)
    panel.setSkipAvailable(lag and not self.playing)
    panel.setChooseWords('Lay out', 'Let the other lay out')
    panel.setDistance(match.distance)
    panel.showPlacing(self.__placing_red__)
    choices = []
    if lag and self.__lag_first__ is None and not self.playing:
      choices.append('distance')
    if match.phase == 'choose':
      choices.append('choose')
    if inHand and self.resting():
      choices.append('red')
    panel.showChoices(tuple(choices))
    panel.showSpot(0)
    if lag:
      panel.chooseCue('yellow' if self.__lag_first__ is not None
                      else 'white')
    elif match.phase not in ('choose', 'over'):
      panel.chooseCue('red')
    panel.ready = self.settingUp() and match.phase not in ('choose',
                                                           'over')

  def _started(self, ) -> None:
    """Shows a shot under way, seen from above, but one struck by the
    stroke ('strikeAt'), seen from where the player stands: the aim and
    the choices hidden, 'Mark' and 'Replay' greyed out."""
    self.view.stopAiming()
    if self.__stay_put__:
      pass
    elif self.__stay_down__:
      self._watchWhole()
    else:
      self._watchFromAbove()
    self._layoutViews()
    self.panel.setFastAvailable(True)
    self.panel.showChoices(())
    self.panel.ready = False
    self.toolBar.replayButton.setEnabled(False)
    self.__rest_clock__ = None

  def _warmWorker(self, ) -> None:
    """Starts the worker's process, so the first shot need not wait for
    it; if it cannot start, shots are played here."""
    for worker in (self.worker, *self.previewers()):
      try:
        worker.warm()
      except OSError:
        pass

  def _sceneLoaded(self, ) -> None:
    """Once the scene is in, shows the view from above where it was
    chosen, and how things stand."""
    self.view.setOverhead(self.overhead)
    self.view.setFieldOfView(self.toolBar.viewSlider.quantity)
    self.view.setAimSpeed(self.panel.speed)
    self.view.setHandShown(self.toolBar.handBox.checked)
    self.view.setShadowShown(self.toolBar.shadowBox.checked)
    if self.walking:
      self.view.setWalking(True)
      x, z = self.room.door
      self.view.walkTo(x, z, 0.0, -8.0)
      self._showInventory()
      self.view.setLooking(not self.__inventory_open__)
    self.refresh()

  def _setMark(self, x: float, y: float, name: str) -> None:
    """Shows the ghost of the cue ball at 'x', 'y', marked against the
    ball 'name', and lets the camera look from it."""
    self.__mark_place__ = (x, y)
    self.__mark_ball__ = name
    self.view.setMark(x, y, self.panel.cueName)
    if self.ghosting:
      self._lookFromGhost()
    self.panel.setGhostAvailable(True)

  def _clearMark(self, ) -> None:
    """Takes the ghost ball away, the camera looking from the cue ball if
    it looked from the ghost."""
    self._leaveGhost()
    self.__mark_place__ = None
    self.__mark_ball__ = ''
    self.view.clearMark()
    self.panel.setGhostAvailable(False)

  def _followTrails(self, recording: Recording) -> None:
    """Draws the ways the balls have gone in the shot shown, as far as
    it is shown: the balls struck boldest, the hand behind each."""
    seconds = self.__play_time__
    trails = self.__shot_trails__ or Trails()
    self.__shot_trails__ = trails.followed(recording, seconds)
    self.view.setTrails(*self._trailsOf(recording, seconds))

  def _trailsOf(self, recording: Recording, seconds: float) -> tuple:
    """Returns the shot's trails as 'seconds' into 'recording', as
    'TableView.setTrails' takes them: each ball's way, the balls struck,
    the hand behind each."""
    struck = recording.struck()
    hands = tuple((ball.x, ball.y, ball.vx, ball.vy) for ball in struck
                  if math.hypot(ball.vx, ball.vy) > 0.0)
    trails = self.__shot_trails__ or Trails().followed(recording, seconds)
    paths = dict(zip(recording.names, trails.paths(recording, seconds)))
    return paths, tuple(ball.name for ball in struck), hands

  def _clearTrails(self, ) -> None:
    """Takes the last shot's trails away."""
    self.__shot_trails__ = None
    self.view.clearTrails()
    self.view.setCounter('')

  def _dropStaleTrails(self, ) -> None:
    """Takes the last shot's trails away if the balls no longer lie
    where it left them, laid anew by the rules."""
    recording = self.__shot_recording__
    if recording is None or self.view.balls != recording.last():
      self._clearTrails()

  def _leaveGhost(self, ) -> None:
    """Stops looking from the ghost, leaving it where it was carried."""
    if not self.ghosting:
      return
    place = self.view.ghostPlace()
    self.ghosting = False
    self.view.setGhostLook(False, (0.0, 0.0), (0.0, 0.0))
    if place is not None and self.__mark_place__ is not None:
      self.__mark_place__ = place
      self.view.setMark(*place, self.panel.cueName)

  def _lookChanged(self, name: str) -> None:
    """Has the camera look from the ball 'name', or from the ghost, then
    shows how things stand."""
    if name == 'ghost' and self.__mark_place__ is not None:
      self.ghosting = True
      self._lookFromGhost()
    else:
      self._leaveGhost()
    self.refresh()

  def _lookFromGhost(self, ) -> None:
    """Stands the camera at the ghost, facing the way the cue ball leaves
    the marked ball: first the way the mark sends it, coming from where it
    lies; turning the view then chooses the way and moves the ghost."""
    named = {ball.name: ball for ball in self.view.balls}
    ball, cue = named[self.__mark_ball__], named[self.panel.cueName]
    gx, gy = self.__mark_place__
    nx, ny = ball.x - gx, ball.y - gy
    dx, dy = gx - cue.x, gy - cue.y
    along = (dx * nx + dy * ny) / max(nx * nx + ny * ny, 1e-12)
    tx, ty = dx - along * nx, dy - along * ny
    if math.hypot(tx, ty) > 1e-9:
      self.view.faceCamera(tx, ty)
    self.view.setGhostLook(True, (ball.x, ball.y), (cue.x, cue.y))

  def _stepper(self, yaw: float, pitch: float) -> Callable[[], None]:
    """Returns what a key turning the aim by 'yaw' and 'pitch' steps
    does; while the right button is held for a stroke, it moves the
    point struck instead (the user): W up, S down, A left, D right."""
    return lambda: self._aimKey(yaw, pitch)

  def _aimKey(self, yaw: float, pitch: float) -> None:
    """Turns the aim by 'yaw' and 'pitch' steps, or, during a stroke,
    moves the point struck: up for a tilt up, right for a turn right,
    the cue drawn at the new point."""
    if self.__pull_press__ is None:
      self.turnAim(yaw, pitch)
      return
    self.spinBy(-pitch, -yaw)
    heading = self.view.cameraHeading()
    if self.__pull_armed__ and heading is not None:
      panel = self.panel
      self.view.setStick(self.cueBall(), heading, self.__pull_drawn__,
                         panel.top, panel.side)

  def _spinner(self, top: float, side: float) -> Callable[[], None]:
    """Returns what a key moving the point struck by 'top' and 'side'
    steps does."""
    return lambda: self.spinBy(top, side)

  def _strikes(self, ) -> bool:
    """Tells whether the cue ball may be struck now: the balls at rest,
    none being moved, and the game letting it."""
    if not self.resting() or self.moving:
      return False
    game = self.__window_mode__ == 'game'
    return not (game and self.match().phase in ('choose', 'over'))

  def _strike(self, setting: tuple) -> None:
    """Strikes the cue ball as 'setting' has it, the aim across and
    along, the speed, the point up and to the right, as 'shoot' does."""
    if not self._strikes():
      return
    self._stopPlacing()
    game = self.__window_mode__ == 'game'
    match = self.match()
    if game and match.phase == 'lag':
      if self.__lag_first__ is None:
        self.__lag_first__ = setting
        self.panel.chooseCue('yellow')
        self.panel.picker.centre()
        self.refresh()
        return
      balls = self._struckBalls(setting)
      self.__shot_record__ = {'kind': 'lag'}
      self.__lag_first__ = None
      self._play(balls)
      return
    before = self.view.balls
    self.__shot_record__ = {
      'kind': 'shot', 'cue': self.panel.cueName,
      'owner': match.cueBall() if game else '', 'before': before,
      'aim': tuple(setting[:2]), 'late': self._late(),
      'opening': (match.needsOpening() if game and not self.isKegler()
                  else False),
    }
    if not game:
      self.__mulligan_balls__ = before
      mark = self.markPlace()
      self.__mulligan_mark__ = (mark, self.__mark_ball__) if mark else None
    self._play(self._struckBalls(setting))

  def _struckBalls(self, setting: tuple) -> tuple[Ball, ...]:
    """Returns the balls as 'setting' strikes them, as '_strike' plays
    them: in a lag with white's shot set, white so and yellow by
    'setting', both at once; else the cue ball by 'setting'."""
    radius = self.view.table.radius
    lag = self.__window_mode__ == 'game' and self.match().phase == 'lag'
    if lag and self.__lag_first__ is not None:
      shots = {'white': self.__lag_first__, 'yellow': setting}
    else:
      shots = {self.panel.cueName: setting}
    return tuple(self.cue.sent(ball, *shots[ball.name], radius)
                 if ball.name in shots else ball
                 for ball in self.view.balls)

  def _raisePins(self, balls: tuple[Ball, ...]) -> None:
    """Sets the pins up on their spots for a shot of 'balls', in
    keglebillard: those clear of every ball, the others off the table
    till a shot frees their spots (8.3)."""
    if self.isKegler():
      names = tuple(ball.name for ball in balls)
      field = self.recorderFor(balls).fieldOf()
      self.view.setPins(field.rows(names))

  def _showHands(self, balls: tuple[Ball, ...]) -> None:
    """Shows, with no ways drawn yet, the hand behind each of 'balls'
    struck, where it sets off, along the way it leaves."""
    struck = tuple(ball for ball in balls
                   if math.hypot(ball.vx, ball.vy) > 0.0)
    hands = tuple((ball.x, ball.y, ball.vx, ball.vy) for ball in struck)
    self.view.setTrails({}, tuple(ball.name for ball in struck), hands)

  def _beginStroke(self, start: float, speed: float) -> None:
    """Begins the cue's stroke at 'start', on the clock, to meet the
    ball '__stroke_lead__' later, sending it off at 'speed' mm/s, and
    shows the cue as it is now."""
    self.__stroke_start__ = start
    self.__stroke_most__ = self.backswingOf(speed)
    self._stroke(time.monotonic())

  def _stroke(self, now: float) -> None:
    """Shows the cue as its stroke has it 'now', on the clock, drawn
    back or following through; once followed through, the stroke is
    over, the cue left there."""
    start = self.__stroke_start__
    if start is None:
      return
    wait, seconds = self.__stroke_lead__, now - start
    self.view.setCueBack(cueBackAt(seconds, wait, self.__stroke_most__))
    if seconds >= wait + FOLLOW_SECONDS:
      self.__stroke_start__ = None

  def _setOverhead(self, overhead: bool) -> None:
    """Shows the table from above, the corner hidden, or the camera's
    view, the view from above in the corner, the toolbar's 'Top view'
    lit to match."""
    self.overhead = True if overhead else False
    self.toolBar.topButton.checked = self.overhead
    self.toolBar.topButton.update()
    self.view.setOverhead(self.overhead)

  def _watchFromAbove(self, ) -> None:
    """Shows the table from above for a shot, the view before kept to
    come back to."""
    if self.__overhead_before__ is None:
      self.__overhead_before__ = self.overhead
    self._setOverhead(True)

  def _watchWhole(self, ) -> None:
    """Has the camera take in the whole table for a stroke's shot, from
    where the player stands, the view before kept to come back to (the
    user: after the shot, catch the entire table)."""
    if self.__whole_before__ is None:
      self.__whole_before__ = self.view.cameraState()
    self.view.watchWhole()

  def _backFromWhole(self, ) -> None:
    """Has the camera glide back to how it looked before the shot was
    watched whole, round the cue ball once it rests."""
    before = self.__whole_before__
    self.__whole_before__ = None
    if before is not None:
      self.view.glideCamera(*before)

  def _backFromAbove(self, ) -> None:
    """Shows the view as it was before a shot was watched from above,
    unless the player chose one meanwhile."""
    before = self.__overhead_before__
    self.__overhead_before__ = None
    if before is not None:
      self._setOverhead(before)

  def _play(self, balls: tuple[Ball, ...]) -> None:
    """Plays 'balls', just struck: the worker asked for the shot, shown
    as it comes, the mark taken away."""
    self._clearMark()
    self._clearTrails()
    self._showHands(balls)
    now, wait = time.monotonic(), self.__stroke_lead__
    start = self.__stroke_start__
    if start is None or now - start > wait + 0.1:
      speed = max(math.hypot(ball.vx, ball.vy) for ball in balls)
      self._beginStroke(now - wait, speed)
    self._playOut(balls, self.recorderFor(balls))
    self.sounds.struck(max(math.hypot(ball.vx, ball.vy) for ball in balls))
    self._started()

  def _playOut(self, balls: tuple[Ball, ...], recorder: object) -> None:
    """Has the worker play 'balls' as 'recorder' has the shot, the pins
    set up, shown as it comes."""
    self._raisePins(balls)
    self.view.balls = balls
    self.__struck_balls__ = balls
    self.__play_recorder__ = recorder
    self.__shot_recording__ = Recording(tuple(ball.name for ball in balls),
                                        recorder.rate)
    self.__shot_verdict__ = None
    self.__early_at__ = None
    self.__early_setup__ = False
    self.__aimed_early__ = False
    self.__play_time__ = 0.0
    self.__play_kind__ = 'shot'
    self.callShown = False
    self.playing = True
    try:
      self.worker.start(recorder, balls)
    except OSError:
      self.worker.close()

  def _received(self, ) -> Recording:
    """Returns the shot shown, with what has come of it since; played
    here if the worker is gone before it is over."""
    recording = self.__shot_recording__
    if self.__play_kind__ != 'shot' or recording.over:
      return recording
    for stretch in self.worker.received():
      recording = recording.joined(stretch)
    self.__shot_recording__ = recording
    if not recording.over and not self.worker.running:
      return self._playedHere()
    return recording

  def _playedHere(self, ) -> Recording:
    """Plays the shot shown here, all of it at once, the worker being
    gone or stuck."""
    balls = self.__struck_balls__
    recorder = self.__play_recorder__ or self.recorderFor(balls)
    recording = recorder.recorded(balls)
    self.__shot_recording__ = recording
    return recording

  def _stopPlaying(self, ) -> None:
    """Stops showing a shot under way, its trails taken away: one not
    played out is let go, one about to be struck is not; a replay leaves
    the balls as they lie. The view is as it was before."""
    self.__stroke_start__ = None
    if self.playing:
      self._clearTrails()
    if self.playing and self.__play_kind__ == 'shot':
      self.__shot_recording__ = None
      self.__shot_verdict__ = None
    if self.playing and self.__play_kind__ == 'replay':
      self.view.balls = self.__replay_balls__
      self.__replay_balls__ = None
    self._backFromAbove()
    self._backFromWhole()
    self.playing = False
    self.__play_kind__ = ''
    self.__early_setup__ = False
    self.__early_at__ = None
    self.panel.setFastAvailable(False)
    self._layoutViews()

  def _verdict(self, ) -> tuple | None:
    """Returns the call on the shot shown, once it is over: the call,
    or for a lag the winning ball; the call in words; and when in the
    shot it was known. 'None' until it is over."""
    if self.__shot_verdict__ is not None:
      return self.__shot_verdict__
    recording, record = self.__shot_recording__, self.__shot_record__
    if recording is None or not recording.over or record is None:
      return None
    touches, after = recording.touchesOf(), recording.last()
    referee = self.referee()
    if record['kind'] == 'fling':
      gone = any(int(row[0]) == record['pin'] and row[8] > 1.5
                 for row in recording.lastPins())
      verdict = (None, 'Debug: pin %d flung, %s.' % (
        record['pin'], 'evaporated over the cushion' if gone
        else 'still on the table'), recording.known())
    elif record['kind'] == 'lag':
      winner, words = referee.lagCall(touches, after)
      if self.isKegler():
        words = words.replace('Yellow', 'The marked white')
        words = words.replace('yellow', 'the marked white')
      verdict = (winner, words, recording.known())
    elif self.isKegler():
      if self.__window_mode__ == 'game':
        recorder = self.recorderFor(recording.ballsAt(0.0))
        call = self.kegleGame().called(recording, recorder)
      else:
        call = self._kegleCall(recording)
      verdict = (call, call.words, recording.known())
    else:
      aimX, aimY = record['aim']
      shot = Shot(record['cue'], record['owner'], record['before'],
                  touches, after, record['opening'], aimX, aimY, False,
                  record['late'])
      call, count = referee.call(shot), referee.decidedAt(shot)
      when = recording.known() if count < 0 else recording.timeOf(count)
      verdict = (call, call.words, when)
    self.__shot_verdict__ = verdict
    return verdict

  def _callIfDue(self, ) -> None:
    """Shows the call on the shot shown, once the moment it was known is
    shown."""
    if self.callShown:
      return
    verdict = self._verdict()
    if verdict is not None and self.__play_time__ >= verdict[2]:
      self._announce(verdict)

  def _announce(self, verdict: tuple) -> None:
    """Shows the call 'verdict' has, a fanfare for a point, and the
    counter with it."""
    self.panel.callWords = verdict[1]
    self.callShown = True
    call = verdict[0]
    self.__board_line__ = verdict[1]
    self.__board_tone__ = 'point' if _scored(call) else (
      'foul' if getattr(call, 'foul', False) else 'neutral')
    if _scored(call):
      self.sounds.fanfare()
    recording = self.__shot_recording__
    if recording is not None:
      self._showCounter(recording)
    self._pushBoards()

  def _ended(self, ) -> None:
    """Ends showing the shot: a replay leaves the balls as they lie; a
    shot leaves them at rest, the game kept, the point struck the middle
    again for the next shot (the user)."""
    kind = self.__play_kind__
    self.playing = False
    self.__play_kind__ = ''
    self._backFromAbove()
    self._backFromWhole()
    self.panel.setFastAvailable(False)
    self._layoutViews()
    if kind == 'replay':
      self.view.balls = self.__replay_balls__
      self.__replay_balls__ = None
      self._raisePins(self.view.balls)
      self._dropStaleTrails()
      self.refresh()
      return
    self.view.balls = self.__shot_recording__.last()
    self._keepHistory()
    if self.__early_setup__:
      #  The game was kept as the next shot's ball came to lie still.
      self.__early_setup__ = False
      self._dropStaleTrails()
      if self.__aimed_early__:
        self._clearTrails()
      self.refresh()
    else:
      self.panel.picker.centre()
      self._judge()
    #  The pins respawn on their spots before the next shot (the user).
    self._raisePins(self.view.balls)

  def _setUpEarly(self, recording: Recording) -> None:
    """Lets the next shot be set up before all rest (the user): once the
    shot is played out by the worker and, as shown, the ball the next
    shot is played with lies where it stays, still or spinning in place,
    the balls to be played as they will lie, the game is kept, the view
    comes back from watching the shot, the camera turns round that ball,
    the point struck the middle again; the others roll on as they went,
    and a shot asked for before they rest is refused ('flashBarrier')."""
    if self.__early_setup__ or self.__play_kind__ != 'shot':
      return
    if not recording.over:
      return
    if self.__early_at__ is None:
      self.__early_at__ = self._earlyAt(recording)
    name, when = self.__early_at__
    if not name or self.__play_time__ < when:
      return
    self.__early_setup__ = True
    self._backFromAbove()
    self._backFromWhole()
    self._layoutViews()
    self.panel.picker.centre()
    self._judge(False)

  def _earlyAt(self, recording: Recording) -> tuple[str, float]:
    """Returns the ball the next shot is played with and from when in
    'recording', played out, it lies where it stays, if that shot may be
    set up before all rest; ('', inf) if not: after a lag, or with a
    ball to be laid anew, red in hand, the game choosing or over."""
    record, verdict = self.__shot_record__, self._verdict()
    if record is None or record['kind'] != 'shot' or verdict is None:
      return '', math.inf
    name = self._nextCue(verdict[0], recording.last())
    if not name:
      return '', math.inf
    return name, _stillFrom(recording, name)

  def _nextCue(self, call: object, last: tuple[Ball, ...]) -> str:
    """Returns the ball the next shot is played with after the shot
    called 'call', the balls coming to rest as 'last', if it is played
    from them as they lie; empty if the balls are laid anew, red is in
    hand, the game is choosing or over, or that ball is off the
    table."""
    game = self.__window_mode__ == 'game'
    if isinstance(call, KegleCall):
      if game:
        after, balls = self.kegleGame().judged(call, last)
        match = after.match
        if match.phase != 'play' or match.inHand or match.layout:
          return ''
        if balls != tuple(last):
          return ''
        name = match.cueBall()
      elif self.kegleGame().unparked(last) != tuple(last):
        return ''
      else:
        name = self.panel.cueName
    elif game:
      after = self.match().judged(call)
      if call.respot or after.needsOpening() or after.phase != 'play':
        return ''
      name = after.cueBall()
    elif call.respot:
      return ''
    else:
      name = self.panel.cueName
    named = {ball.name: ball for ball in last}
    ball = named.get(name)
    if ball is None or isParked(ball.x, ball.y):
      return ''
    return name

  def _judge(self, lay: bool = True) -> None:
    """Calls the shot just played and keeps the game: once all rest, the
    balls laid for the next shot; or, 'lay' False, as soon as the ball
    the next shot is played with lies still, the balls to be played as
    they will lie, left to roll on ('_setUpEarly')."""
    verdict = self._verdict()
    record = self.__shot_record__
    self.__shot_record__ = None
    if record is None or verdict is None:
      self.refresh()
      return
    table = self.view.table
    after = self.view.balls if lay else self.__shot_recording__.last()
    if not self.callShown:
      self._announce(verdict)
    if record['kind'] == 'lag':
      winner = verdict[0]
      if self.isKegler():
        self.__kegle_game__ = self.kegleGame().lagged(winner)
      else:
        self.__window_match__ = self.match().lagged(winner)
      if not winner:
        self.view.balls = table.lagPosition()
        self._faceTheFoot()
      self._dropStaleTrails()
      self.refresh()
      return
    if record['kind'] == 'fling':
      #  Debug: the game as it was, the balls as they lie.
      self._dropStaleTrails()
      self.refresh()
      return
    call = verdict[0]
    if isinstance(call, KegleCall):
      if self.__window_mode__ == 'game':
        self._judgeKegle(call, after, lay)
      elif lay:
        self.view.balls = self.kegleGame().unparked(after)
    elif self.__window_mode__ == 'game':
      match = self.match().judged(call)
      self.__window_match__ = match
      if call.respot:
        after = table.respotted(after, match.cueBall() or record['cue'],
                                call.respot)
      if match.needsOpening():
        after = table.openingFor(match.cueBall(), self.__opening_spot__)
        self._faceTheFoot()
      if lay:
        self.view.balls = after
    elif call.respot and lay:
      self.view.balls = table.respotted(after, record['cue'], call.respot)
    if lay:
      self._dropStaleTrails()
    self.refresh()

  def _judgeKegle(self, call: KegleCall, after: tuple,
                  lay: bool) -> None:
    """Keeps keglebillard's game after the shot called 'call', the balls
    at rest as 'after': the balls laid out anew, red in hand again, or
    as they lie, laid so if 'lay'."""
    game, balls = self.kegleGame().judged(call, after)
    self.__kegle_game__ = game
    if lay:
      self.view.balls = balls
    if game.match.layout:
      self._faceTheFoot()

  def _frozenBalls(self, ) -> tuple:
    """Returns the balls the cue ball rests frozen to."""
    if not self.resting():
      return ()
    return self.referee().frozenTo(self.view.balls,
                                   self.panel.cueName)[0]

  def _late(self, ) -> bool:
    """Tells whether the shot clock, if the rules keep one, ran out;
    keglebillard keeps none."""
    if self.isKegler():
      return False
    limit = self.match().rules.shotClock
    if not limit or self.__rest_clock__ is None:
      return False
    return time.monotonic() - self.__rest_clock__ > limit

  def _stopMoving(self, ) -> None:
    """Lets a drag turn the camera again."""
    self.moving = False
    self.toolBar.moveButton.checked = False
    self.view.setMoving(self.__placing_red__)

  def _stopPlacing(self, ) -> None:
    """Lets a drag no longer put red down."""
    if self.__placing_red__:
      self.__placing_red__ = False
      self.view.setMoving(self.moving)

  def _soundToggled(self, *_) -> None:
    """Turns the sounds on or off as the toolbar's 'Sound' is ticked."""
    self.sounds.enabled = self.toolBar.soundBox.checked

  def _layoutViews(self, ) -> None:
    """Shows the table, or the full map in its place while it is chosen
    and no shot is shown: a shot is always shown on the table; and the
    panel's point struck and power to be set only while the full map
    shows, output only else (the user)."""
    full = self.fullShown and not self.playing and not self.walking
    self.view.setVisible(not full)
    self.fullMap.setVisible(full)
    self.panel.setControlsLive(full)
    playing = not self.walking
    self.toolBar.setVisible(playing)
    self.panel.setVisible(playing)
    self.unfoldedMap.setVisible(playing and self.unfolded)

  def _showCounter(self, recording: Recording) -> None:
    """Shows over the view the cushions the cue ball has met so far in
    the shot shown, counted up to the second ball it meets, and which
    balls it has met; the point, once called. Nothing for a lag."""
    if self.isKegler():
      field = self.recorderFor(recording.ballsAt(0.0)).fieldOf()
      words = _kegleCounterWords(recording, self.__play_time__, field)
    else:
      words = _counterWords(recording, self.__play_time__)
    verdict = self.__shot_verdict__
    if words and self.callShown and verdict is not None and (
        verdict[0] is not None):
      words += '   —   ' + _calledWords(verdict[0])
    self.view.setCounter(words)

  def _kegleCall(self, recording: Recording) -> KegleCall:
    """Returns the keglebillard referee's call on 'recording', over, in
    the sandbox: the pins it left fallen and red's carom counted, its
    fouls called, red played from where it lay, the series begun."""
    recorder = self.recorderFor(recording.ballsAt(0.0))
    shot = KegleShot(recording.touchesOf(), recorder.fallenOf(recording))
    return KegleReferee(recorder.motion.table).call(shot, Streak())

  def _faceTheFoot(self, ) -> None:
    """Turns the camera to face the foot, as the players stand at the
    head to lag (article 2.1.02) and to break: the far cushion ahead,
    the near one behind."""
    self.view.faceCamera(0.0, -1.0)

  def _showTrenches(self, ) -> None:
    """Shows the trenches instead of the shadow while a shot is aimed
    from the cue ball (the user): ball 1's way along the aim to the
    first cushion or ball it touches, or whereabouts it stops before,
    and, if it meets a ball, that ball's way after ('Trenches'); struck
    as the panel has it or, while a stroke is pulled back, as hard as
    letting it go would strike it. Else the shadow alone."""
    panel, view = self.panel, self.view
    aim = None
    if self.settingUp() and not self.ghosting and not self.walking:
      if panel.lookName == panel.cueName:
        aim = view.cameraHeading()
    if aim is None:
      view.clearTrenches()
      return
    speed = panel.speed
    if self.__pull_press__ is not None and self.__pull_armed__:
      speed = 1000.0 * self.springSpeed(self.__pull_back__)
    trenches = Trenches(view.table, self.motion.cloth, self.cue)
    view.setTrenches(trenches.trenchesOf(
      view.balls, panel.cueName, aim[0], aim[1], speed, panel.top,
      panel.side))

  def _showUnfolded(self, ) -> None:
    """Shows the balls in the maps of the table unfolded, beside it and
    full, as they lie or move, and, while a shot is aimed from the cue
    ball, the arc of its English."""
    panel, view = self.panel, self.view
    aim = None
    if self.resting() and not self.ghosting:
      if panel.lookName == panel.cueName:
        aim = view.cameraHeading()
    for shown, unfolded in ((self.unfolded, self.unfoldedMap),
                            (self.fullShown, self.fullMap)):
      if shown:
        unfolded.showShot(view.balls, panel.cueName, aim, panel.top,
                          panel.side, panel.speed)
    self._preview(aim)

  def _preview(self, aim: tuple[float, float] | None) -> None:
    """Has the 'previewers' play the shot aimed on the table, all the
    balls as they lie, the moment it changes, while still aiming (the
    user), dropping the ones under way: as aimed, and off one standard
    deviation of the maps' 'spread' to either side; and hands the maps
    the runs as they come, the referee's call on the shot as aimed with
    them. Meanwhile the maps show their estimate."""
    maps = [shown for on, shown in ((self.unfolded, self.unfoldedMap),
                                    (self.fullShown, self.fullMap)) if on]
    if aim is None or not maps:
      return
    key = maps[0].shotKey()
    if key != self.__preview_key__:
      self._startPreview(key, aim, maps[0].unfolded.spread)
      for one in maps:
        one.showWorking(key)
      return
    recordings, runs = self.__preview_recordings__, self.__preview_runs__
    if recordings is None or all(run is not None for run in runs):
      return
    came = False
    for k, previewer in enumerate(self.previewers()):
      if runs[k] is not None:
        continue
      recording = recordings[k]
      for stretch in previewer.received():
        recording = recording.joined(stretch)
      recordings[k] = recording
      if recording.over:
        runs[k] = maps[0].unfolded.runOf(recording)
        came = True
    if not came or runs[0] is None:
      return
    shown = tuple(runs) if all(run is not None for run in runs) else (
      runs[0],)
    words = self._previewWords(recordings[0], aim)
    for one in maps:
      one.showRuns(key, shown, words)

  def previewers(self, ) -> tuple[ShotWorker, ShotWorker, ShotWorker]:
    """The 'previewers' method returns the workers playing the shot
    aimed for the maps: as aimed, and off to either side."""
    return self.previewer, self.previewerLow, self.previewerHigh

  def _startPreview(self, key: tuple, aim: tuple[float, float],
                    spread: float) -> None:
    """Starts the previewers on the shot 'key', aimed 'aim', the aim off
    'spread' degrees either side for the two last."""
    panel, view = self.panel, self.view
    cue = self.cueBall()
    recorder = self.recorderFor(view.balls, self.__preview_rate__)
    angle = math.atan2(aim[1], aim[0])
    turns = (0.0, -math.radians(spread), math.radians(spread))
    recordings = []
    for previewer, turn in zip(self.previewers(), turns):
      struck = self.cue.sent(cue, math.cos(angle + turn),
                             math.sin(angle + turn), panel.speed,
                             panel.top, panel.side, view.table.radius)
      balls = tuple(struck if ball.name == cue.name else ball
                    for ball in view.balls)
      recordings.append(Recording(tuple(ball.name for ball in balls),
                                  recorder.rate))
      try:
        previewer.start(recorder, balls)
      except OSError:
        previewer.close()
    self.__preview_key__ = key
    self.__preview_recordings__ = recordings
    self.__preview_runs__ = [None, None, None]

  def _previewWords(self, recording: Recording,
                    aim: tuple[float, float]) -> str:
    """Returns the referee's call on the shot previewed, 'recording',
    aimed 'aim', as the game stands; nothing in a lag or between
    games."""
    game = self.__window_mode__ == 'game'
    match = self.match()
    if game and match.phase in ('lag', 'choose', 'over'):
      return ''
    if self.isKegler():
      if not game:
        return self._kegleCall(recording).words
      recorder = self.recorderFor(self.view.balls, recording.rate)
      return self.kegleGame().called(recording, recorder).words
    shot = Shot(self.panel.cueName, match.cueBall() if game else '',
                self.view.balls, recording.touchesOf(), recording.last(),
                match.needsOpening() if game else False, aim[0], aim[1],
                False, False)
    return self.referee().call(shot).words

  def enterRoom(self, ) -> None:
    """The 'enterRoom' method stands the player up to walk the room,
    first person, cue in hand (the user): the shot under way and any
    stroke let go, the panel, the bar and the maps out of the way, the
    keys walking instead of aiming; 'useAsked' (E) near a table opens
    its start menu."""
    self.cancelStroke()
    self._stopPlaying()
    self._stopMoving()
    self._stopPlacing()
    self.walking = True
    self.__inventory_open__ = False
    self.view.stopAiming()
    self.view.clearTrenches()
    self._setPlayKeys(False)
    self.view.setWalking(True)
    self._showInventory()
    self._layoutViews()
    self.view.setLooking(True)
    self._pushBoards()

  def sitDown(self, kind: str, mode: str) -> None:
    """The 'sitDown' method has the player play at 'kind's table, 'carom'
    or 'kegler', in 'mode', a 'game' begun anew or the 'sandbox': the
    view the table played at, the bar and the panel back, the keys
    aiming."""
    self.walking = False
    self.__inventory_open__ = False
    self._showInventory()
    self.view.setWalking(False)
    self._setPlayKeys(True)
    self.setKind(kind)
    self.setMode(mode)
    self._layoutViews()
    self.refresh()

  def standUp(self, ) -> None:
    """The 'standUp' method leaves the table played at to walk the room,
    the player standing at its foot end, facing it."""
    kind = self.__game_kind__
    self.enterRoom()
    self.view.walkTo(*self.room.beside(kind))

  def useAsked(self, ) -> None:
    """The 'useAsked' method answers E (the user): walking, the inventory
    opened or closed, or, near a table, its new game menu; playing, the
    table's menu. A menu shows at the view's middle, not waiting for a
    choice, the mouse let go while it is up."""
    if self.walking and self.__inventory_open__:
      self.closeInventory()
      return
    if self.walking:
      kind = self.view.nearTable()
      if not kind:
        self.openInventory()
        return
      menu = self.startMenu(kind)
      self.view.setLooking(False)
      menu.aboutToHide.connect(self._menuHidden)
    else:
      menu = self.tableMenu()
    middle = self.view.rect().center()
    menu.popup(self.view.mapToGlobal(middle))

  def inventoryItems(self, ) -> list[dict]:
    """The 'inventoryItems' method returns what the walker carries, each
    its 'name' and 'label': the cue, for now (the user: other stuff
    later)."""
    return [{'name': 'cue', 'label': 'Cue'}]

  def heldItem(self, ) -> str:
    """The 'heldItem' method returns the name of the item in hand, empty
    when the hands are empty."""
    return self.__held_item__

  def openInventory(self, ) -> None:
    """The 'openInventory' method opens the inventory over the view
    (the user: E, as in the block-building games), the mouse let go to
    pick from it."""
    if not self.walking:
      return
    self.__inventory_open__ = True
    self.view.setLooking(False)
    self._showInventory()

  def closeInventory(self, ) -> None:
    """The 'closeInventory' method closes the inventory, the mouse
    looking round again."""
    self.__inventory_open__ = False
    self._showInventory()
    if self.walking:
      self.view.setLooking(True)

  def chooseItem(self, name: str) -> None:
    """The 'chooseItem' method takes the item 'name' in hand, or, held
    already, puts it away, the hands empty."""
    held = '' if self.__held_item__ == name else name
    self.__held_item__ = held
    self._showInventory()

  def _showInventory(self, ) -> None:
    """Shows the inventory as it stands: its items, the one held, open
    or closed."""
    self.view.setInventory(self.inventoryItems(), self.__held_item__,
                           self.__inventory_open__)

  def _escapeAsked(self, ) -> None:
    """Esc while walking: closes the inventory, or lets the mouse go,
    its pointer shown; a click takes it back."""
    if self.__inventory_open__:
      self.closeInventory()
    elif self.view.isLooking():
      self.view.setLooking(False)

  def _menuHidden(self, ) -> None:
    """A table's menu gone while still walking: the mouse looks round
    again."""
    if self.walking and not self.__inventory_open__:
      self.view.setLooking(True)

  def startMenu(self, kind: str) -> QMenu:
    """The 'startMenu' method returns the menu E opens by 'kind's table:
    its name, 'Play a game', 'Sandbox', and 'Walk on'."""
    menu = self._useMenu()
    title = menu.addAction('Kegler table' if kind == 'kegler'
                           else 'Three-cushion table')
    title.setEnabled(False)
    menu.addSeparator()
    play = menu.addAction('Play a game')
    play.triggered.connect(lambda *_: self.sitDown(kind, 'game'))
    sandbox = menu.addAction('Sandbox')
    sandbox.triggered.connect(lambda *_: self.sitDown(kind, 'sandbox'))
    menu.addAction('Walk on')
    return menu

  def tableMenu(self, ) -> QMenu:
    """The 'tableMenu' method returns the menu E opens at the table played
    at: 'Back to the table', 'New game', and 'Leave the table'."""
    menu = self._useMenu()
    menu.addAction('Back to the table')
    again = menu.addAction('New game')
    again.triggered.connect(lambda *_: self.newGame())
    leave = menu.addAction('Leave the table')
    leave.triggered.connect(lambda *_: self.standUp())
    return menu

  def _useMenu(self, ) -> QMenu:
    """Returns a new, empty menu for E, the last one let go."""
    if self.__use_menu__ is not None:
      self.__use_menu__.deleteLater()
    self.__use_menu__ = QMenu(self)
    return self.__use_menu__

  def _setPlayKeys(self, on: bool) -> None:
    """Lets the keys that aim, tilt and move the point struck act, while
    playing, or not, while walking, so the walker has them."""
    for key in (self.turnLeftKey, self.turnRightKey, self.tiltUpKey,
                self.tiltDownKey, self.spinUpKey, self.spinDownKey,
                self.spinLeftKey, self.spinRightKey, self.centreKey):
      key.setEnabled(True if on else False)

  def boards(self, ) -> tuple[dict, dict]:
    """The 'boards' method returns what the club boards show (the user: a
    diegetic scoreboard): over the table played at, the game as it
    stands, the line saying what just happened; over the other, a free
    table."""
    kegler = self.isKegler()
    idle = _idleBoard(not kegler)
    if self.walking and self.__shot_history__ is None:
      return _idleBoard(kegler), idle
    if self.__window_mode__ != 'game':
      live = _idleBoard(kegler)
      live['title'] = 'SANDBOX'
      live['line'] = (self.__board_line__
                      or 'SANDBOX: ANY BALL, FROM ANYWHERE')
      live['tone'] = self.__board_tone__
      return live, idle
    return self._gameBoard(), idle

  def _gameBoard(self, ) -> dict:
    """Returns the club board of the game played: the players, their
    points, figures, run and way to the distance, the centre, and the
    line."""
    match, kegler = self.match(), self.isKegler()
    distance = match.distance if kegler else match.rules.distance
    playing = match.phase in ('play', 'break')
    at = match.current if playing else -1
    run = match.run if playing else 0
    if kegler:
      figures = [('%d' % match.series[k], '%.2f' % match.average(k),
                  '%d' % match.best[k]) for k in (0, 1)]
      labels, roundLabel = ['SER', 'AVG', 'BEST'], 'SERIES'
      rounds = max(match.series) + (1 if playing else 0)
      beads, tier = math.ceil(run / 4), _tierOf(run, 12, 20)
      due = min(match.streak.reds, 2) if playing else 0
      lamp, lampOn = 'FINAL SERIES', bool(match.final)
    else:
      figures = [('%d' % match.innings[k], '%.3f' % match.average(k),
                  '%d' % match.best[k]) for k in (0, 1)]
      labels, roundLabel = ['INN', 'AVG', 'HR'], 'INNING'
      rounds = max(match.innings) + (1 if playing else 0)
      beads, tier = run, _tierOf(run, 3, 5)
      due = -1
      lamp = 'MATCH BALL'
      lampOn = playing and match.scores[at] == distance - 1
    line = self.__board_line__ or match.said()
    if match.phase == 'lag':
      line = self.panel.status or line
    return {
      'wood': 'oak' if kegler else 'ebony',
      'title': 'TO %d' % distance,
      'names': list(match.names),
      'balls': ['#f2ecd9', '#e9e6df' if kegler else '#f5b21b'],
      'leds': ['#f6f0e4', '#ffad2a'],
      'points': list(match.scores),
      'stats': [list(row) for row in figures],
      'labels': labels,
      'shares': [min(score / max(distance, 1), 1.0)
                 for score in match.scores],
      'at': at,
      'won': match.winner if match.phase == 'over' else -1,
      'run': run,
      'beads': beads,
      'tier': tier,
      'roundLabel': roundLabel,
      'round': rounds % 100,
      'clock': '%d' % match.rules.shotClock
               if not kegler and match.rules.shotClock else '',
      'due': due,
      'lamp': lamp,
      'lampOn': bool(lampOn),
      'line': line,
      'tone': self.__board_tone__,
    }

  def _pushBoards(self, ) -> None:
    """Shows the club boards as 'boards' has them."""
    live, idle = self.boards()
    self.view.setBoards(live, idle)

  def minimapMenu(self, ) -> QMenu:
    """The 'minimapMenu' method returns the corner's menu (the user):
    'Previous', the last shot's ways shown again; 'Clear', the ways
    taken away; 'Options', for the corner, none yet; and 'History', each
    shot of this game, newest first, its ways shown when chosen."""
    if self.__minimap_menu__ is not None:
      self.__minimap_menu__.deleteLater()
    menu = self.__minimap_menu__ = QMenu(self)
    history = self.__shot_history__ or []
    previous = menu.addAction('Previous')
    previous.setEnabled(bool(history) and not self.playing)
    previous.triggered.connect(
      lambda *_: self.showShotOf(len(self.__shot_history__ or []) - 1))
    clear = menu.addAction('Clear')
    clear.setEnabled(not self.playing)
    clear.triggered.connect(lambda *_: self.clearMinimap())
    options = menu.addMenu('Options')
    none = options.addAction('None yet')
    none.setEnabled(False)
    past = menu.addMenu('History')
    if not history:
      empty = past.addAction('No shots yet')
      empty.setEnabled(False)
    for index in reversed(range(len(history))):
      action = past.addAction(history[index][0])
      action.setEnabled(not self.playing)
      action.triggered.connect(
        lambda *_, index=index: self.showShotOf(index))
    return menu

  def showShotOf(self, index: int) -> None:
    """The 'showShotOf' method shows on the corner, and from above, the
    ways the balls went in shot 'index' of this game, the hand behind
    each ball struck; not while a shot is shown."""
    history = self.__shot_history__ or []
    if self.playing or not 0 <= index < len(history):
      return
    _, paths, bold, hands, _ = history[index]
    self.view.setTrails(paths, bold, hands)

  def clearMinimap(self, ) -> None:
    """The 'clearMinimap' method takes the ways shown on the corner
    away; not while a shot is shown."""
    if not self.playing:
      self._clearTrails()

  def _minimapMenuAt(self, x: float, y: float) -> None:
    """Shows the corner's menu at 'x', 'y' on the view, without waiting
    for a choice."""
    menu = self.minimapMenu()
    menu.popup(self.view.mapToGlobal(QPoint(int(x), int(y))))

  def _aimBegun(self, ) -> None:
    """Takes the last shot's ways off the corner as the next shot begins
    to be aimed (the user): the camera turned, a map dragged, a stroke
    begun; 'Previous' brings them back."""
    if not self.playing:
      self._clearTrails()
    elif self.__early_setup__:
      self.__aimed_early__ = True

  def _keepHistory(self, ) -> None:
    """Keeps the shot just played among this game's, for 'History': its
    words, its trails, and the balls before it."""
    recording = self.__shot_recording__
    if recording is None or self.__play_kind__ == 'replay':
      return
    if self.__shot_history__ is None:
      self.__shot_history__ = []
    verdict = self.__shot_verdict__ or self._verdict()
    record = self.__shot_record__ or {}
    words = verdict[1] if verdict is not None else ''
    number = len(self.__shot_history__) + 1
    lag = 'Lag: ' if record.get('kind') == 'lag' else ''
    label = '%d. %s%s' % (number, lag, words or 'Played')
    paths, bold, hands = self._trailsOf(recording, recording.known())
    self.__shot_history__.append((label, paths, bold, hands,
                                  self.__mulligan_balls__))

  def _aim(self, ) -> None:
    """Turns the camera round the ball looked from and shows the aim, if
    the next shot may be set up, and, once all rest, starts the shot
    clock."""
    if self.walking or not self.settingUp():
      return
    self.view.aimAt(self.lookBall())
    if self.resting() and self.__rest_clock__ is None:
      self.__rest_clock__ = time.monotonic()


def _idleBoard(kegler: bool) -> dict:
  """Returns the club board of a table no one plays at: its wood, no
  players, the line asking for a player."""
  return {'wood': 'oak' if kegler else 'ebony', 'title': 'FREE TABLE',
          'names': ['', ''], 'points': [0, 0],
          'stats': [['', '', ''], ['', '', '']], 'at': -1, 'won': -1,
          'run': 0, 'beads': 0, 'shares': [0, 0], 'roundLabel': '',
          'clock': '', 'due': -1, 'lamp': '', 'lampOn': False,
          'labels': (['SER', 'AVG', 'BEST'] if kegler
                     else ['INN', 'AVG', 'HR']),
          'line': 'FREE TABLE · WALK UP AND PRESS E TO PLAY',
          'tone': 'neutral'}


def _tierOf(run: int, warm: int, hot: int) -> str:
  """Returns how the run meter glows at 'run': green, amber from 'warm',
  red from 'hot'."""
  return 'red' if run >= hot else 'amber' if run >= warm else 'green'


def _stillFrom(recording: Recording, name: str) -> float:
  """Returns from when in 'recording', played out, ball 'name' lies
  where it stays, if spinning in place: the time of the first sample
  after it last moved, nought if it never moved."""
  index = recording.names.index(name)
  places = recording.placesOf(0, recording.count())[:, index, :]
  if not len(places):
    return 0.0
  off = numpy.hypot(*(places - places[-1]).T) > _STILL_WITHIN
  moved = numpy.nonzero(off)[0]
  if not len(moved):
    return 0.0
  return float(moved[-1] + 1) / recording.rate


def _counterWords(recording: Recording, upto: float) -> str:
  """Returns the cushions the cue ball met in 'recording' by 'upto' s,
  counted up to the second ball it meets, and the balls, each ticked
  once met; empty unless one ball was struck."""
  struck = recording.struck()
  if len(struck) != 1:
    return ''
  cue = struck[0].name
  cushions, met = 0, []
  for time, touch in recording.touches:
    if time > upto:
      break
    if cue not in (touch.first, touch.second):
      continue
    if touch.kind == 'cushion' and len(met) < 2:
      cushions += 1
    elif touch.kind == 'ball':
      other = touch.second if touch.first == cue else touch.first
      if other not in met:
        met.append(other)
  noun = 'cushion' if cushions == 1 else 'cushions'
  return '%d %s   %s' % (cushions, noun, _metMarks(recording, cue, met))


def _kegleCounterWords(recording: Recording, upto: float,
                       field: PinField) -> str:
  """Returns how many pins are down in keglebillard's 'recording' at
  'upto' s, as the rules count them, set in 'field', and the balls the
  cue ball has met by then, each ticked once met; empty unless one ball
  was struck."""
  struck = recording.struck()
  if len(struck) != 1:
    return ''
  cue, met = struck[0].name, []
  for time, touch in recording.touches:
    if time > upto:
      break
    if touch.kind == 'ball' and cue in (touch.first, touch.second):
      other = touch.second if touch.first == cue else touch.first
      if other not in met:
        met.append(other)
  field.setRows(recording.pinsAt(upto), recording.names)
  return 'Pins down %d   %s' % (len(field.fallen()),
                                _metMarks(recording, cue, met))


def _metMarks(recording: Recording, cue: str, met: list) -> str:
  """Returns the balls of 'recording' but 'cue', each ticked if among
  'met'."""
  return '   '.join('%s %s' % (name.capitalize(),
                               '✓' if name in met else '·')
                    for name in recording.names if name != cue)


def _scored(call: object) -> bool:
  """Tells whether 'call' scored: a three-cushion point, or points in
  keglebillard."""
  if isinstance(call, KegleCall):
    return call.points > 0
  return True if getattr(call, 'point', False) else False


def _calledWords(call: object) -> str:
  """Returns the call shown after the counter: the point or none, or
  keglebillard's points, a foul or no score."""
  if isinstance(call, KegleCall):
    if call.foul:
      return 'Foul'
    return '%d points' % call.points if call.points else 'No score'
  return 'Point!' if getattr(call, 'point', False) else 'No point'
