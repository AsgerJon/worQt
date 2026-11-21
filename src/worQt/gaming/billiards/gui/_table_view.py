"""
TableView subclasses 'QQuickWidget' and shows a three-cushion table and
its balls in 3D, drawn by Qt Quick 3D from 'carom.qml'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy
from PySide6.QtCore import QDir, QMetaObject, QPoint, QPointF, QSize
from PySide6.QtCore import QUrl, Q_ARG, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QQuaternion, QVector3D
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....widgets import WidgetMixin
from .. import Ball, CaromTable, KeglePin, KegleTable, Turn, latheMesh
from .. import ribbonMesh, trenchMesh
from .._table_shapes import APRON_DEPTH, APRON_INSET, RAIL_DEPTH
from .._table_shapes import CUE_BUTT, CUE_FERRULE, CUE_SHAFT, CUE_TIP
from .._phrasebook import ENGLISH, Phrasebook
from .._table_shapes import kegleMeshes, tableMeshes
from ._hand_picture import HAND_LENGTH, HAND_WIDTH, cuePicture
from ._hand_picture import handPicture
from ._prism import Prism
from ._room_light import radianceBytes, roomLight

#  The phrases the scene says itself, over the view: the walker's keys,
#  the debug's tag, the table's E, the inventory. The keys a phrase
#  names are the language's own ('Phrasebook.controls').
QML_WORDS = ('room.look', 'room.click', 'room.fling', 'room.kegler',
             'room.carom', 'room.inventory', 'room.hotbar', 'room.held',
             'room.empty')

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QMouseEvent, QShowEvent


class TableView(QQuickWidget, WidgetMixin):
  """
  TableView subclasses 'QQuickWidget' and shows its 'table', a
  'CaromTable', and its 'balls' on it, in 3D, after a Søgaard table:
  the cloth, the sloped cushions, the ebony rails and corner blocks,
  the diamonds inlaid, the body on two pedestals, under a lamp; the
  balls dotted, turned as each ball's 'turn' says. A drag
  turns round the table, the wheel comes nearer. The scene,
  'carom.qml', starts loading when the view is first shown; once it is
  in, 'loaded' is 'True' and 'sceneLoaded' is emitted. 'problems' are
  the errors met loading it, none when all is well.

  The scene is in mm with y up: the cloth's middle at the origin, its
  top at nought, the table's 'x' across and its 'y' along, the head end
  away. 'scenePlace' turns a place on the table into one in the scene.

  A corner shows the table from straight above, the camera a dot on it;
  'setOverhead' shows the view from above filling the view instead, the
  corner hidden. A tap on the table, on a ball or on the cloth from
  above, tells where on the table, 'tableTapped'; the right button held
  and moved, a stroke, tells where on the view, in pixels,
  'strokePressed', 'strokeMoved', 'strokeReleased'; a left click
  meanwhile calls it off, 'strokeCancelled', the scene never seeing the
  click. A left press on the view tells the next shot begins to be
  aimed, 'aimTouched'; a right click on the corner asks for its menu,
  'minimapMenuAsked', where on the view, in pixels. 'setMark' shows a
  ghost of a ball, clear, where it must be; 'clearMark' hides it;
  'setGhostLook' has the camera stand at the ghost facing the way the
  cue ball leaves its ball, the ghost moving to the hit that gives the
  way the camera faces, 'ghostPlace' telling where it is.
  'turnCamera' turns the camera round what it looks at.

  Wherever the view from above is shown, 'setTrails' draws the last shot
  on the cloth: each ball's way in its colour, the balls struck boldest,
  faint balls where those that moved set off, and a gloved hand holding
  the cue behind each ball struck, while 'setHandShown' wants it;
  'clearTrails' takes them away. A way is as wide in mm as it is, but
  never narrower than a few pixels of the view showing it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __scene_file__ = Path(__file__).with_name('carom.qml')
  __room_name__ = 'worQt-carom-room.hdr'
  __room_size__ = 512, 256  # the room light's columns and rows
  __hand_name__ = 'worQt-carom-hand.png'
  __cue_name__ = 'worQt-carom-cue.png'
  #  How wide a ball's way is drawn: in mm, and in pixels at the least,
  #  for a ball struck and for the others; and how far above the cloth.
  __trail_widths__ = {True: (24.0, 3.0), False: (12.0, 2.0)}
  __trail_lift__ = 0.5
  __trail_moved__ = 1.0  # mm a ball is off its start to have moved
  __ball_bodies__ = {'white': '#f2ecd9', 'yellow': '#f5b21b',
                     'red': '#c4141b'}

  #  Private Variables
  __view_table__: CaromTable | None = None
  __view_balls__: tuple[Ball, ...] | None = None
  __view_component__: QQmlComponent | None = None
  __view_shapes__: dict[str, Prism] | None = None
  __view_trails__: tuple | None = None
  __view_kegler__: bool = False
  __view_flinging__: bool = False
  __view_words__: dict | None = None
  __walk_keys__: list | None = None
  __pin_rows__: list | None = None
  __pin_mesh__: numpy.ndarray | None = None
  __pin_shapes__: tuple = ()
  __sunk_depth__ = 45.0  # mm a ball gone into a pocket sits down in it
  __stick_rise__ = 3.0  # degrees the cue is held up from the cloth
  __watch_view__ = 60.0  # degrees taken in while a shot is watched whole
  __watch_pitch__ = 40.0  # degrees down while a shot is watched whole
  __trail_shapes__: dict[str, Prism] | None = None
  __trench_shapes__: dict[str, Prism] | None = None
  __trench_lift__ = 0.8  # mm above the cloth a trench is drawn
  __trench_most__ = 3  # trenches drawn at most: ball 1, ball 2, ball 1
  __trail_pushed__: dict | None = None
  __left_eaten__: bool = False
  __view_room__: dict | None = None
  __view_walking__: bool = False
  __look_on__: bool = False
  __look_warps__: bool = False
  __look_last__: QPointF | None = None
  __look_pending__: QPointF | None = None
  __look_stray__ = 0.25  # share of the view the pointer strays to
  __look_edge__ = 0.06  # share of the view at each side that turns it
  __look_turn__ = 900.0  # pixels a second turned at the very edge
  __view_boards__: tuple | None = None

  #  Signals
  sceneLoaded = Signal()
  clothPressed = Signal(float, float)
  clothDragged = Signal(float, float)
  clothReleased = Signal()
  tableTapped = Signal(float, float)
  pinTapped = Signal(int)
  strokePressed = Signal(float, float)
  strokeMoved = Signal(float, float)
  strokeReleased = Signal()
  strokeCancelled = Signal()
  aimTouched = Signal()
  escapeAsked = Signal()
  itemChosen = Signal(str)
  minimapMenuAsked = Signal(float, float)

  #  Public Variables
  loaded = AttriBox[bool](False)

  #  Virtual Variables
  table: Field[CaromTable] = Field()
  balls: Field[tuple[Ball, ...]] = Field()
  problems: Field[tuple[str, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @table.GET
  def _getTable(self, ) -> CaromTable:
    """The 'table' getter returns the table shown, a match table unless
    another was set."""
    if self.__view_table__ is None:
      self.__view_table__ = CaromTable()
    return self.__view_table__

  @balls.GET
  def _getBalls(self, ) -> tuple[Ball, ...]:
    """The 'balls' getter returns the balls shown, as the game opens
    unless others were set."""
    if self.__view_balls__ is None:
      self.__view_balls__ = self.table.opening()
    return self.__view_balls__

  @problems.GET
  def _getProblems(self, ) -> tuple[str, ...]:
    """The 'problems' getter returns the errors met loading the scene,
    none when all is well."""
    return tuple(error.toString() for error in self.errors())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @table.SET
  def _setTable(self, table: CaromTable) -> None:
    """The 'table' setter shows 'table', its balls as it opens."""
    self.__view_table__ = table
    self.__view_balls__ = None
    self.__view_shapes__ = None
    self._push()

  @balls.SET
  def _setBalls(self, balls: tuple[Ball, ...]) -> None:
    """The 'balls' setter shows 'balls' on the table."""
    self.__view_balls__ = tuple(balls)
    self._pushBalls()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: QShowEvent) -> None:
    """Shown the first time, the view starts loading its scene."""
    if self.__view_component__ is None:
      self.load()
    QQuickWidget.showEvent(self, event)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A left press while the right button is held, a stroke under way,
    calls the stroke off ('strokeCancelled'), the scene never seeing it;
    walking, a click takes the mouse back to look round; any other
    press goes to the scene."""
    if self.__view_walking__ and not self.__look_on__:
      if not self.sceneValue('inventoryOpen'):
        self.setLooking(True)
        event.accept()
        return
    if self.__look_on__:
      event.accept()
      return
    if self._cancels(event):
      return
    QQuickWidget.mousePressEvent(self, event)

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """While looking round, the mouse turns the walker's head, the
    pointer kept hidden in the middle ('setLooking'); else the move goes
    to the scene."""
    if not self.__look_on__:
      QQuickWidget.mouseMoveEvent(self, event)
      return
    event.accept()
    at = event.globalPosition()
    pending = self.__look_pending__
    if pending is not None and abs(at.x() - pending.x()) <= 1.5 \
        and abs(at.y() - pending.y()) <= 1.5:
      #  The pointer put back in the middle: not the player's move.
      self.__look_pending__ = None
      self.__look_warps__ = True
      self.__look_last__ = at
      return
    last = self.__look_last__ if self.__look_last__ is not None else at
    dx, dy = at.x() - last.x(), at.y() - last.y()
    self.__look_last__ = at
    if dx or dy:
      self.lookBy(dx, dy)
    stray, local = self.__look_stray__, event.position()
    if abs(local.x() - 0.5 * self.width()) > stray * self.width() \
        or abs(local.y() - 0.5 * self.height()) > stray * self.height():
      self._recentre()

  def keyPressEvent(self, event: object) -> None:
    """Walking, Esc asks to let the mouse go or close the inventory
    ('escapeAsked'); any other key goes to the scene."""
    if self.__view_walking__ and event.key() == Qt.Key.Key_Escape:
      event.accept()
      self.escapeAsked.emit()
      return
    QQuickWidget.keyPressEvent(self, event)

  def focusOutEvent(self, event: object) -> None:
    """Leaving the window lets the mouse go, its pointer shown again."""
    if self.__look_on__:
      self.setLooking(False)
    QQuickWidget.focusOutEvent(self, event)

  def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
    """A left double click while the right button is held calls the
    stroke off, as a press does."""
    if self._cancels(event):
      return
    QQuickWidget.mouseDoubleClickEvent(self, event)

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """The left button let go after its press called a stroke off is
    kept from the scene too, as its press was."""
    left = event.button() == Qt.MouseButton.LeftButton
    if left and self.__left_eaten__:
      self.__left_eaten__ = False
      event.accept()
      return
    QQuickWidget.mouseReleaseEvent(self, event)

  def sizeHint(self, ) -> QSize:
    return QSize(1200, 800)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(480, 320)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    QQuickWidget.__init__(self, parent)
    self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

  @overload()
  def __init__(self, ) -> None:
    QQuickWidget.__init__(self, )
    self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def load(self, ) -> None:
    """The 'load' method starts loading the scene; once it is in,
    'sceneLoaded' is emitted, 'loaded' is 'True' and the table and balls
    are shown in it.

    The scene is first compiled asynchronously. The 'App' has 'notify'
    in Python, so every event, on any thread, wants Python's lock; a
    'setSource' straight away would hold that lock waiting for QML's
    loading thread, which waits for the lock: a deadlock. Compiled, the
    scene is cached and 'setSource' does not wait."""
    url = QUrl.fromLocalFile(str(self.__scene_file__))
    mode = QQmlComponent.CompilationMode.Asynchronous
    component = QQmlComponent(self.engine(), url, mode, self)
    self.__view_component__ = component
    if component.isLoading():
      component.statusChanged.connect(self._compiled)
    else:
      self._compiled()

  def scenePlace(self, x: float, y: float, height: float) -> QVector3D:
    """The 'scenePlace' method returns where 'x' across and 'y' along
    the table, 'height' above the cloth, is in the scene."""
    table = self.table
    return QVector3D(x - 0.5 * table.width, height, 0.5 * table.length - y)

  def aimAt(self, ball: Ball) -> None:
    """The 'aimAt' method turns the camera round 'ball', gliding there,
    and shows the aim from it."""
    root = self.rootObject()
    if root is None:
      return
    place = self.scenePlace(ball.x, ball.y, self.table.radius)
    root.setProperty('cameraFocus', place)
    root.setProperty('aiming', True)

  def setMoving(self, moving: bool) -> None:
    """The 'setMoving' method lets a drag on the cloth move balls,
    'clothPressed' and 'clothDragged' telling where on the table, rather
    than the camera; or not."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('moving', True if moving else False)

  def setFlinging(self, flinging: bool) -> None:
    """The 'setFlinging' method lets a tap on a pin of the table played
    ask for it to be sent flying, 'pinTapped' (debug, the user: to see a
    pin go over a cushion at will); or not."""
    self.__view_flinging__ = True if flinging else False
    root = self.rootObject()
    if root is not None:
      root.setProperty('flinging', self.__view_flinging__)

  def setWords(self, book: Phrasebook) -> None:
    """The 'setWords' method has the scene say its own words, over the
    view, in 'book's language ('QML_WORDS'), and the walker walk by its
    keys ('Phrasebook.controls': W A S D, or Z Q S D for French and
    Flemish, the AZERTY keyboards' places)."""
    controls = book.controls()
    self.__view_words__ = {key: book.said(key, *controls)
                           for key in QML_WORDS}
    self.__walk_keys__ = [_keyOf(letter) for letter in controls]
    root = self.rootObject()
    if root is not None:
      root.setProperty('words', self.__view_words__)
      root.setProperty('walkKeys', self.__walk_keys__)

  def walkKeys(self, ) -> list[int]:
    """The 'walkKeys' method returns the keys the walker walks by, as
    Qt's key codes: forward, left, back, right."""
    if self.__walk_keys__ is None:
      self.__walk_keys__ = [_keyOf(letter)
                            for letter in ENGLISH.controls()]
    return list(self.__walk_keys__)

  def setKegler(self, kegler: bool) -> None:
    """The 'setKegler' method lays the table out for keglebillard, the
    second game, or for three-cushion again: the cloth more cyan, the
    six holes milled in, the pins standing on their spots."""
    self.__view_kegler__ = True if kegler else False
    root = self.rootObject()
    if root is not None:
      self._pushKegler(root)

  def bodyOf(self, name: str) -> str:
    """The 'bodyOf' method returns the colour of the ball 'name': in
    keglebillard the marked white, 'yellow', is white (the user)."""
    if self.__view_kegler__ and name == 'yellow':
      return self.__ball_bodies__['white']
    return self.__ball_bodies__[name]

  def setPins(self, rows: object = None) -> None:
    """The 'setPins' method shows keglebillard's pins as 'rows' has them,
    the pins of a sample, 'PIN_STATE' numbers each ('Stretch.pins'):
    each pin by its number where its centre of mass is, turned so; a pin
    not among them is not on the table. 'None' shows all five standing
    on their spots."""
    self.__pin_rows__ = None if rows is None else [
      tuple(float(value) for value in row) for row in rows]
    root = self.rootObject()
    if root is not None:
      self._pushPins(root)

  def setOverhead(self, overhead: bool) -> None:
    """The 'setOverhead' method shows the table from straight above,
    the corner hidden; or the camera's view, the view from above in the
    corner."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('overhead', True if overhead else False)

  def setAimSpeed(self, speed: float) -> None:
    """The 'setAimSpeed' method has the aim line show a shot of 'speed',
    in mm/s: the harder, the longer and warmer."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('aimSpeed', float(speed))

  def setFieldOfView(self, degrees: float) -> None:
    """The 'setFieldOfView' method has the camera take in 'degrees' from
    the bottom of the view to the top."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('cameraView', float(degrees))

  def turnCamera(self, yaw: float, pitch: float) -> None:
    """The 'turnCamera' method turns the camera round what it looks at,
    'yaw' degrees to the left and 'pitch' up, kept above the cloth."""
    root = self.rootObject()
    if root is not None:
      QMetaObject.invokeMethod(root, 'turnBy', Q_ARG('QVariant', float(yaw)),
                               Q_ARG('QVariant', float(pitch)))

  def cameraState(self, ) -> tuple | None:
    """The 'cameraState' method returns how the camera looks now: what
    it looks at, its turn, how far off it is and its field of view, as
    'glideCamera' takes them; 'None' before the scene is loaded."""
    root = self.rootObject()
    if root is None:
      return None
    return (root.property('cameraFocus'), root.property('cameraTurnNow'),
            float(root.property('cameraDistanceNow')),
            float(root.property('cameraView')))

  def glideCamera(self, focus: QVector3D, turn: QVector3D,
                  distance: float, view: float) -> None:
    """The 'glideCamera' method has the camera glide to look at 'focus',
    in the scene, turned 'turn', 'distance' mm off it, taking in 'view'
    degrees from bottom to top."""
    root = self.rootObject()
    if root is not None:
      QMetaObject.invokeMethod(root, 'glideCamera',
                               Q_ARG('QVariant', focus),
                               Q_ARG('QVariant', turn),
                               Q_ARG('QVariant', float(distance)),
                               Q_ARG('QVariant', float(view)))

  def watchWhole(self, ) -> None:
    """The 'watchWhole' method has the camera glide back and up to take
    in the whole table, rails and all, round the cloth's middle, facing
    the way it faces, the view widened to '__watch_view__' degrees and
    looking '__watch_pitch__' degrees down (the user: after the shot,
    catch the entire table)."""
    state = self.cameraState()
    if state is None:
      return
    table = self.table
    out = 2.0 * (table.cushion + table.rail)
    reach = 0.5 * math.hypot(table.width + out, table.length + out)
    view = self.__watch_view__
    distance = 1.1 * reach / math.sin(math.radians(0.5 * view))
    turn = QVector3D(-self.__watch_pitch__, state[1].y(), 0.0)
    self.glideCamera(QVector3D(0.0, 0.0, 0.0), turn, distance, view)

  def setGauge(self, speed: float, most: float) -> None:
    """The 'setGauge' method shows the speedometer over the ball aimed
    from, clear: 'speed' m/s of 'most', how fast the cue ball would go
    struck now (the user)."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('gaugeMost', float(most))
      root.setProperty('gaugeSpeed', float(speed))
      root.setProperty('gaugeShown', True)

  def hideGauge(self, ) -> None:
    """The 'hideGauge' method takes the speedometer away."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('gaugeShown', False)

  def setCounter(self, words: str) -> None:
    """The 'setCounter' method shows 'words' over the view, the cushions
    and the balls the cue ball has met; none for empty words."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('counterText', words)
      root.setProperty('counterShown', True if words else False)

  def faceCamera(self, x: float, y: float) -> None:
    """The 'faceCamera' method turns the camera round what it looks at
    to face the way 'x', 'y' on the table along the cloth, its tilt
    kept."""
    heading = self.cameraHeading()
    if heading is None:
      return
    now = math.atan2(-heading[0], heading[1])
    want = math.atan2(-x, y)
    turn = math.degrees(want - now)
    turn = (turn + 180.0) % 360.0 - 180.0
    self.turnCamera(turn, 0.0)

  def setGhostLook(self, look: bool, ball: tuple[float, float],
                   cue: tuple[float, float]) -> None:
    """The 'setGhostLook' method has the camera stand at the ghost and face
    the way the cue ball, at 'cue', leaves the ball at 'ball' after the
    hit; turning the view chooses that way and moves the ghost to the hit
    that gives it. Or not."""
    root = self.rootObject()
    if root is None:
      return
    radius = self.table.radius
    root.setProperty('ghostOf', self.scenePlace(*ball, radius))
    root.setProperty('ghostFrom', self.scenePlace(*cue, radius))
    root.setProperty('ghostLook', True if look else False)

  def ghostPlace(self, ) -> tuple[float, float] | None:
    """The 'ghostPlace' method returns where on the table the ghost is
    while the camera turns round it; 'None' before the scene is
    loaded."""
    place = self.sceneValue('ghostPlace')
    if place is None:
      return None
    return self.tablePlace(place.x(), place.z())

  def setMark(self, x: float, y: float, name: str) -> None:
    """The 'setMark' method shows a ghost of the ball 'name', clear, at
    'x', 'y' on the table."""
    root = self.rootObject()
    if root is None:
      return
    root.setProperty('markPlace', self.scenePlace(x, y, self.table.radius))
    root.setProperty('markColor', QColor(self.bodyOf(name)))
    root.setProperty('markShown', True)

  def setTrails(self, paths: dict, bold: tuple, hands: tuple) -> None:
    """The 'setTrails' method draws the last shot as seen from above:
    'paths', each ball's way by its name, an array of places on the
    table, 'x' and 'y' in mm, the first where it set off; 'bold', the
    names of the balls struck, drawn boldest; 'hands', where each ball
    struck set off and the way it went, 'x', 'y', and its speed along
    each."""
    self.__view_trails__ = (dict(paths), tuple(bold), tuple(hands))
    self._pushTrails()

  def clearTrails(self, ) -> None:
    """The 'clearTrails' method takes the last shot's trails away: no
    ball's way, no faint balls, no hands, until the next are set."""
    self.__view_trails__ = None
    root = self.rootObject()
    if root is None:
      return
    for name in ('trailNames', 'trailStarts', 'hands'):
      if self._changed(name, []):
        root.setProperty(name, [])
    root.setProperty('trailsShown', False)

  def setHandShown(self, shown: bool) -> None:
    """The 'setHandShown' method shows the gloved hand behind each ball
    struck, with the trails, or not."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('handShown', True if shown else False)

  def setShadowShown(self, shown: bool) -> None:
    """The 'setShadowShown' method shows the shadow both eyes see of the
    ball aimed from while a shot is aimed, or not: the strip a ball wide
    it sweeps along the aim to the cushion; the eyes being about as far
    apart as a ball is wide, ball 1 hides from both only what lies in
    it, so what it touches the cue ball hits (the user)."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('shadowShown', True if shown else False)

  def setTrenches(self, trenches: tuple) -> None:
    """The 'setTrenches' method shows 'trenches' instead of the shadow
    while a shot is aimed and the shadow wanted (the user): each a
    'Trench', ball 1's to the hit, ball 2's and ball 1's on from it, a
    ball wide on the cloth in the colour of its ball, from where it sets
    off to where it touches or stops, ending round as the ball does;
    and, where ball 1 meets ball 2, a clear copy of ball 1 (the user),
    shown even without the shadow."""
    root = self.rootObject()
    if root is None:
      return
    trenches = tuple(trenches)[:self.__trench_most__]
    shapes = self._trenchShapes(root)
    radius = self.table.radius
    for k, trench in enumerate(trenches):
      points = self._scenePoints(trench.points)
      seen = (len(points), tuple(round(float(value), 2)
                                 for value in points[[0, -1]].ravel()))
      if self._changed('trench %d' % k, seen):
        shapes['trench%d' % k].setMesh(
          trenchMesh(points, radius, self.__trench_lift__))
    names = [trench.name for trench in trenches]
    if self._changed('trenchNames', names):
      root.setProperty('trenchNames', names)
    root.setProperty('trenchesShown', True)
    first = trenches[0] if trenches else None
    meets = first is not None and first.end == 'ball'
    if meets:
      x, y = first.endPlace()
      root.setProperty('impactPlace', self.scenePlace(x, y, radius))
      root.setProperty('impactColor', QColor(self.bodyOf(first.name)))
    root.setProperty('impactShown', True if meets else False)

  def setRoom(self, layout: dict) -> None:
    """The 'setRoom' method lays the billiard room round the table out as
    'layout' has it, 'Room.layout': its sizes and where each game's table
    stands."""
    self.__view_room__ = dict(layout)
    root = self.rootObject()
    if root is not None:
      root.setProperty('roomPlan', self.__view_room__)

  def setWalking(self, walking: bool) -> None:
    """The 'setWalking' method has the view show the room as the walker
    sees it, first person, the keys moving it and the mouse turning its
    head, or the table played at again, the mouse let go."""
    self.__view_walking__ = True if walking else False
    root = self.rootObject()
    if root is not None:
      QMetaObject.invokeMethod(root, 'setWalking',
                               Q_ARG('QVariant', True if walking else False))
    if walking:
      self.setFocus()
    else:
      self.setLooking(False)

  def setLooking(self, looking: bool) -> None:
    """The 'setLooking' method has the mouse turn the walker's head, its
    pointer hidden (the user), or lets it go, the pointer shown. The
    pointer is put back in the middle as it strays a quarter of the view
    from it, where the system lets an application move it; where it does
    not, the hidden pointer is followed as it is, and held near either
    side of the view it keeps turning the head ('turnAtEdge')."""
    looking = True if looking and self.__view_walking__ else False
    self.__look_on__ = looking
    self.__look_last__ = None
    self.__look_pending__ = None
    self.setMouseTracking(True)
    if looking:
      self.setCursor(Qt.CursorShape.BlankCursor)
      self.setFocus()
      self._recentre()
    else:
      self.unsetCursor()
    root = self.rootObject()
    if root is not None:
      root.setProperty('looking', looking)

  def isLooking(self, ) -> bool:
    """The 'isLooking' method tells whether the mouse turns the walker's
    head now."""
    return self.__look_on__

  def lookBy(self, dx: float, dy: float) -> None:
    """The 'lookBy' method turns the walker's head as the mouse moved
    'dx' pixels right and 'dy' down."""
    root = self.rootObject()
    if root is not None:
      QMetaObject.invokeMethod(root, 'lookBy', Q_ARG('QVariant', float(dx)),
                               Q_ARG('QVariant', float(dy)))

  def turnAtEdge(self, seconds: float) -> None:
    """The 'turnAtEdge' method turns the walker's head for 'seconds' while
    the hidden pointer, not put back in the middle, rests near either
    side of the view: the nearer the side, the faster."""
    last = self.__look_last__
    if not self.__look_on__ or self.__look_warps__ or last is None:
      return
    at = self.mapFromGlobal(last)
    width = max(float(self.width()), 1.0)
    band = self.__look_edge__ * width
    turn = 0.0
    if at.x() < band:
      turn = -(band - at.x()) / band
    elif at.x() > width - band:
      turn = (at.x() - width + band) / band
    if turn:
      self.lookBy(turn * self.__look_turn__ * seconds, 0.0)

  def setInventory(self, items: list, held: str, shown: bool) -> None:
    """The 'setInventory' method shows the walker's inventory, 'items',
    each its 'name' and 'label', the first nine on the hotbar, 'held' the
    one in hand; open over the view while 'shown'."""
    root = self.rootObject()
    if root is None:
      return
    root.setProperty('inventory', [dict(item) for item in items])
    root.setProperty('held', held)
    root.setProperty('inventoryOpen', True if shown else False)

  def walkTo(self, x: float, z: float, yaw: float, pitch: float) -> None:
    """The 'walkTo' method stands the walker at 'x', 'z' in the room,
    turned 'yaw' degrees about the vertical (nought facing the head wall)
    and 'pitch' up."""
    root = self.rootObject()
    if root is not None:
      QMetaObject.invokeMethod(root, 'walkTo', Q_ARG('QVariant', float(x)),
                               Q_ARG('QVariant', float(z)),
                               Q_ARG('QVariant', float(yaw)),
                               Q_ARG('QVariant', float(pitch)))

  def nearTable(self, ) -> str:
    """The 'nearTable' method returns the game whose table the walker
    stands near enough to play, 'carom' or 'kegler'; empty for none."""
    near = self.sceneValue('nearTable')
    return str(near) if near else ''

  def setBoards(self, live: dict, idle: dict) -> None:
    """The 'setBoards' method shows 'live' on the club boards over the
    table played at, 'idle' on those over the other: each as
    'ClubBoard.qml' takes it."""
    self.__view_boards__ = (dict(live), dict(idle))
    root = self.rootObject()
    if root is not None:
      root.setProperty('liveBoard', self.__view_boards__[0])
      root.setProperty('idleBoard', self.__view_boards__[1])

  def flashBarrier(self, ) -> None:
    """The 'flashBarrier' method shows, for a moment, over the ball aimed
    from, a barrier: a clear block barred by a red sign, a shot asked
    for before every ball rests refused (the user)."""
    root = self.rootObject()
    if root is not None:
      QMetaObject.invokeMethod(root, 'flashBarrier')

  def clearTrenches(self, ) -> None:
    """The 'clearTrenches' method shows the shadow again instead of the
    trenches, and no copy of ball 1 where it meets ball 2: as when the
    shot aimed is not the cue ball's."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('trenchesShown', False)
      root.setProperty('impactShown', False)

  def setStick(self, ball: Ball, aim: tuple[float, float], back: float,
               top: float, side: float) -> None:
    """The 'setStick' method shows the cue in the scene, laid behind
    'ball' along 'aim' on the cloth, 'aim' of length one, held
    '__stick_rise__' degrees up, its tip on the point struck, 'top' up
    and 'side' to the right as shares of the radius, 'back' mm short of
    it: as the stroke draws it back and drives it through."""
    root = self.rootObject()
    if root is None:
      return
    radius = self.table.radius
    hx, hy = aim
    rx, ry = hy, -hx
    deep = math.sqrt(max(1.0 - top * top - side * side, 0.0))
    reach = radius * deep + back
    x = ball.x - hx * reach + rx * side * radius
    y = ball.y - hy * reach + ry * side * radius
    z = radius + top * radius
    rise = math.radians(self.__stick_rise__)
    way = QVector3D(-hx * math.cos(rise), math.sin(rise),
                    hy * math.cos(rise))
    root.setProperty('stickPlace', self.scenePlace(x, y, z))
    root.setProperty('stickTurn', QQuaternion.rotationTo(
      QVector3D(0.0, 1.0, 0.0), way))
    root.setProperty('stickShown', True)

  def hideStick(self, ) -> None:
    """The 'hideStick' method takes the cue out of the scene."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('stickShown', False)

  def clearMark(self, ) -> None:
    """The 'clearMark' method hides the ghost ball."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('markShown', False)

  def tablePlace(self, x: float, z: float) -> tuple[float, float]:
    """The 'tablePlace' method returns where the scene's 'x', 'z' on the
    cloth is on the table."""
    table = self.table
    return x + 0.5 * table.width, 0.5 * table.length - z

  def stopAiming(self, ) -> None:
    """The 'stopAiming' method hides the aim, the camera staying."""
    root = self.rootObject()
    if root is not None:
      root.setProperty('aiming', False)

  def cameraHeading(self, ) -> tuple[float, float] | None:
    """The 'cameraHeading' method returns the way the camera faces,
    along the cloth, as the table has it, of length one; 'None' before
    the scene is loaded or when it looks straight down."""
    forward = self.sceneValue('cameraForward')
    if forward is None:
      return None
    x, y = forward.x(), -forward.z()
    length = math.hypot(x, y)
    if length < 1e-6:
      return None
    return x / length, y / length

  @staticmethod
  def sceneTurn(turn: Turn) -> QQuaternion:
    """The 'sceneTurn' method returns 'turn', a unit quaternion as the
    table has it, as the scene has it: the table's 'x' is the scene's,
    its 'y' the scene's negative 'z', its up the scene's 'y'."""
    w, x, y, z = turn
    return QQuaternion(w, x, z, -y)

  def sceneValue(self, name: str) -> object:
    """The 'sceneValue' method returns the scene's value 'name', as
    'TableView' set it; 'None' before the scene is loaded."""
    root = self.rootObject()
    return None if root is None else root.property(name)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _recentre(self, ) -> None:
    """Puts the hidden pointer back in the middle of the view, where the
    system lets an application move it; the move it makes is known by
    where it lands and not taken for the player's ('mouseMoveEvent').
    Whether it happened shows only by that move coming: the pointer's
    place as the system reports it at once may be the old one (it was,
    on the user's Wayland, and every look was turned straight back)."""
    target = self.mapToGlobal(QPoint(self.width() // 2,
                                     self.height() // 2))
    self.__look_pending__ = QPointF(target)
    QCursor.setPos(target)

  def _cancels(self, event: QMouseEvent) -> bool:
    """Tells whether 'event' is the left button pressed while the right
    is held, a stroke under way: if so it is taken, kept from the scene,
    and 'strokeCancelled' emitted."""
    left = event.button() == Qt.MouseButton.LeftButton
    if not left or not event.buttons() & Qt.MouseButton.RightButton:
      return False
    self.__left_eaten__ = True
    event.accept()
    self.strokeCancelled.emit()
    return True

  def _compiled(self, *_) -> None:
    """Once the scene is compiled, sets it as the view's source, shows
    the table and balls in it, and emits 'sceneLoaded'."""
    component = self.__view_component__
    if component is None or component.isLoading():
      return
    self.setSource(component.url())
    self.loaded = True
    root = self.rootObject()
    if root is not None:
      root.clothPressed.connect(self._pressed)
      root.clothDragged.connect(self._dragged)
      root.clothReleased.connect(self.clothReleased.emit)
      root.tableTapped.connect(self._tapped)
      root.pinTapped.connect(self.pinTapped.emit)
      root.strokePressed.connect(self.strokePressed.emit)
      root.strokeMoved.connect(self.strokeMoved.emit)
      root.strokeReleased.connect(self.strokeReleased.emit)
      root.aimTouched.connect(self.aimTouched.emit)
      root.minimapMenuAsked.connect(self.minimapMenuAsked.emit)
      root.itemChosen.connect(self.itemChosen.emit)
      root.overheadRescaled.connect(self._pushTrails)
    self._push()
    self.sceneLoaded.emit()

  def _pressed(self, x: float, z: float) -> None:
    """Tells where on the table the cloth was pressed."""
    self.clothPressed.emit(*self.tablePlace(x, z))

  def _dragged(self, x: float, z: float) -> None:
    """Tells where on the table the cloth was dragged to."""
    self.clothDragged.emit(*self.tablePlace(x, z))

  def _tapped(self, x: float, z: float) -> None:
    """Tells where on the table was tapped."""
    self.tableTapped.emit(*self.tablePlace(x, z))

  def _pushBalls(self, ) -> None:
    """Sets the balls' places and turns in the scene; nothing before
    the scene is loaded."""
    root = self.rootObject()
    if root is None:
      return
    radius = self.table.radius
    kegle = KegleTable(self.table)
    for ball in self.balls:
      place = self.scenePlace(ball.x, ball.y, radius)
      hole = kegle.pocketOf(ball)
      if hole >= 0:
        #  Gone into a pocket: sunk in its hole.
        x, y = kegle.holes()[hole]
        place = self.scenePlace(x, y, radius - self.__sunk_depth__)
      root.setProperty('%sPlace' % ball.name, place)
      root.setProperty('%sTurn' % ball.name, self.sceneTurn(ball.turn))

  def _push(self, ) -> None:
    """Sets the scene's sizes, balls and diamonds from the table and
    balls shown; nothing before the scene is loaded."""
    root = self.rootObject()
    if root is None:
      return
    if self.__view_words__ is None:
      self.__view_words__ = {key: ENGLISH.said(key, *ENGLISH.controls())
                             for key in QML_WORDS}
    root.setProperty('words', self.__view_words__)
    root.setProperty('walkKeys', self.walkKeys())
    table = self.table
    root.setProperty('tableLength', table.length)
    root.setProperty('tableWidth', table.width)
    root.setProperty('ballRadius', table.radius)
    root.setProperty('noseHeight', table.nose)
    root.setProperty('cushionDepth', table.cushion)
    root.setProperty('cushionTop', table.top)
    root.setProperty('railWidth', table.rail)
    root.setProperty('railBottom', table.top - RAIL_DEPTH)
    root.setProperty('apronBottom', -APRON_DEPTH)
    root.setProperty('apronInset', APRON_INSET)
    root.setProperty('bedHeight', table.bed)
    self._pushBalls()
    top = table.top + 0.6
    diamonds = [self.scenePlace(x, y, top) for x, y in table.diamonds()]
    root.setProperty('diamondPlaces', diamonds)
    self._pushKegler(root)
    if self.__view_room__ is not None:
      root.setProperty('roomPlan', self.__view_room__)
    if self.__view_boards__ is not None:
      root.setProperty('liveBoard', self.__view_boards__[0])
      root.setProperty('idleBoard', self.__view_boards__[1])
    if self.__view_shapes__ is None:
      meshes = {**tableMeshes(table), **kegleMeshes(KegleTable(table)),
                'cueTip': latheMesh(CUE_TIP, 24),
                'cueFerrule': latheMesh(CUE_FERRULE, 24),
                'cueShaft': latheMesh(CUE_SHAFT, 24),
                'cueButt': latheMesh(CUE_BUTT, 24)}
      self.__view_shapes__ = {k: Prism(v) for k, v in meshes.items()}
      root.setProperty('shapes', self.__view_shapes__)
    if not root.property('roomLight').toString():
      root.setProperty('roomLight', QUrl.fromLocalFile(str(self.roomFile())))
    if not root.property('handPicture').toString():
      root.setProperty('handLength', HAND_LENGTH)
      root.setProperty('handWidth', HAND_WIDTH)
      root.setProperty('handPicture',
                       QUrl.fromLocalFile(str(self.handFile())))
      root.setProperty('cuePicture',
                       QUrl.fromLocalFile(str(self.cueFile())))
    self._pushTrails()

  def _pushKegler(self, root: object) -> None:
    """Shows keglebillard's holes and pins, or not, as 'setKegler'
    has it: the pins on their spots, three dark grooves round each one's
    waist (the user's photo, previews/kegler.jpg)."""
    kegle, pin = KegleTable(self.table), KeglePin()
    self._pushPins(root)
    root.setProperty('holePlaces', [self.scenePlace(x, y, 0.0)
                                    for x, y in kegle.holes()])
    root.setProperty('holeRadius', 0.5 * kegle.pocket)
    root.setProperty('pinGrooves', [{'y': y, 'r': pin.radiusAt(y) + 0.15}
                                    for y in (64.0, 66.5, 69.0)])
    root.setProperty('pinSpots', [self.scenePlace(x, y, 0.0)
                                  for x, y in kegle.pinSpots()])
    root.setProperty('kegler', self.__view_kegler__)
    root.setProperty('flinging', self.__view_flinging__)
    self._pushPinShape(root)

  def _pushPinShape(self, root: object) -> None:
    """Gives the pins, the played table's and the other's, a pin's shape
    made anew ('pinShape'; its triangles made once): a shape a pin drew
    is drawn by none made after that pin is gone (Qt Quick 3D), and
    changing the game takes one table's pins away and makes the other's
    (the user, 2026-11-16: the tall pins stood in the room, not on the
    table played). The last two shapes are kept alive."""
    if self.__pin_mesh__ is None:
      self.__pin_mesh__ = latheMesh(KeglePin().profile, 32)
    shape = Prism(self.__pin_mesh__)
    self.__pin_shapes__ = self.__pin_shapes__[-1:] + (shape,)
    root.setProperty('pinShape', shape)

  def _pushPins(self, root: object) -> None:
    """Shows the pins as 'setPins' has them: each pin's foot where it
    is, the pin turned so in the scene, those not on the table hidden,
    those flown over a cushion evaporating where they crossed (the user:
    as in Portal's grid; 'PIN_STATE' awake two)."""
    kegle, pin = KegleTable(self.table), KeglePin()
    rows = self.__pin_rows__
    if rows is None:
      rows = [(k, x, y, pin.centre(), 1.0, 0.0, 0.0, 0.0, 0.0)
              for k, (x, y) in enumerate(kegle.pinSpots())]
    count = len(kegle.pinSpots())
    places, turns = [QVector3D()] * count, [QQuaternion()] * count
    shown, gone = [False] * count, [False] * count
    up = QVector3D(0.0, pin.centre(), 0.0)
    for row in rows:
      number = int(row[0])
      turn = self.sceneTurn(tuple(row[4:8]))
      places[number] = self.scenePlace(row[1], row[2], row[3]) \
        - turn.rotatedVector(up)
      turns[number] = turn
      shown[number] = True
      gone[number] = float(row[8]) > 1.5
    root.setProperty('pinPlaces', places)
    root.setProperty('pinTurns', turns)
    root.setProperty('pinShown', shown)
    root.setProperty('pinGone', gone)

  def _pushTrails(self, *_) -> None:
    """Draws the trails set, as wide as the view from above shows them
    now; nothing before the scene is loaded, or with no trails set."""
    root, trails = self.rootObject(), self.__view_trails__
    if root is None or trails is None:
      return
    paths, bold, hands = trails
    scale = float(root.property('overheadScale') or 1.0)
    starts, drawn = [], []
    for name, shape in self._trailShapes(root).items():
      points = self._scenePoints(paths.get(name))
      width, least = self.__trail_widths__[name in bold]
      half = 0.5 * max(width, least * scale)
      seen = (len(points), tuple(points[-1:].ravel()), half)
      if self._changed('mesh %s' % name, seen):
        shape.setMesh(ribbonMesh(points, half, self.__trail_lift__))
      went = 0.0
      if len(points):
        went = float(numpy.hypot(*(points - points[0]).T).max())
      if went > 0.0:
        drawn.append(name)
      if went > self.__trail_moved__:
        starts.append({'x': float(points[0, 0]), 'z': float(points[0, 1]),
                       'color': self.bodyOf(name)})
    marks = []
    for x, y, vx, vy in hands:
      place = self.scenePlace(x, y, 0.0)
      marks.append({'x': place.x(), 'z': place.z(),
                    'angle': math.degrees(math.atan2(vy, vx))})
    for name, value in (('boldTrails', list(bold)), ('trailStarts', starts),
                        ('hands', marks), ('trailNames', drawn)):
      if self._changed(name, value):
        root.setProperty(name, value)
    root.setProperty('trailsShown', True)

  def _scenePoints(self, path: object) -> numpy.ndarray:
    """Returns the places on the table 'path', 'x' and 'y' in mm, as
    places on the cloth in the scene, 'x' and 'z'; none for 'None'."""
    if path is None:
      return numpy.zeros((0, 2))
    table = self.table
    points = numpy.asarray(path, float).reshape(-1, 2)
    return numpy.column_stack((points[:, 0] - 0.5 * table.width,
                               0.5 * table.length - points[:, 1]))

  def _trailShapes(self, root: object) -> dict[str, Prism]:
    """Returns the ribbons the balls' ways are drawn with, by name,
    handing them to the scene the first time."""
    if self.__trail_shapes__ is None:
      empty = numpy.zeros((0, 6))
      self.__trail_shapes__ = {name: Prism(empty)
                               for name in ('white', 'yellow', 'red')}
      root.setProperty('trailShapes', self.__trail_shapes__)
    return self.__trail_shapes__

  def _trenchShapes(self, root: object) -> dict[str, Prism]:
    """Returns the shapes the trenches are drawn with, handing them to
    the scene the first time."""
    if self.__trench_shapes__ is None:
      empty = numpy.zeros((0, 6))
      self.__trench_shapes__ = {'trench%d' % k: Prism(empty)
                                for k in range(self.__trench_most__)}
      root.setProperty('trenchShapes', self.__trench_shapes__)
    return self.__trench_shapes__

  def _changed(self, name: str, value: object) -> bool:
    """Tells whether 'value' differs from what was last handed to the
    scene as 'name', remembering it; the scene's lists are only set anew
    when they change, as each set builds their parts again."""
    pushed = self.__trail_pushed__
    if pushed is None:
      pushed = self.__trail_pushed__ = {}
    if name in pushed and pushed[name] == value:
      return False
    pushed[name] = value
    return True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def handFile(self, ) -> Path:
    """The 'handFile' method paints the gloved bridge hand,
    'handPicture', as a PNG in the temporary folder, and returns
    where."""
    path = Path(QDir.tempPath()) / self.__hand_name__
    handPicture().save(str(path))
    return path

  def cueFile(self, ) -> Path:
    """The 'cueFile' method paints the cue resting in the bridge,
    'cuePicture', as a PNG in the temporary folder, and returns
    where."""
    path = Path(QDir.tempPath()) / self.__cue_name__
    cuePicture().save(str(path))
    return path

  def setCueBack(self, back: float) -> None:
    """The 'setCueBack' method slides the cue in each hand drawn
    'back' mm back from where it rests, its tip by the ball; below
    nought, on through where the ball was."""
    root = self.rootObject()
    if root is not None and self._changed('cueBack', float(back)):
      root.setProperty('cueBack', float(back))

  def roomFile(self, ) -> Path:
    """The 'roomFile' method writes the light of the room round the
    table, 'roomLight', as a Radiance '.hdr' image in the temporary
    folder, and returns where."""
    path = Path(QDir.tempPath()) / self.__room_name__
    width, height = self.__room_size__
    path.write_bytes(radianceBytes(roomLight(width, height)))
    return path


def _keyOf(letter: str) -> int:
  """Returns Qt's key code for the key 'letter', a capital."""
  return int(getattr(Qt.Key, 'Key_%s' % letter).value)
