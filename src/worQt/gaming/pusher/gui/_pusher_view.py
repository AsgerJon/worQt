"""
PusherView subclasses 'QWidget' and shows a coin pusher in 3D, drawn by
Qt Quick 3D from 'pusher.qml' in a 'QQuickView' of its own, rendered in
its own thread.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QDir, QSize, QUrl, Signal
from PySide6.QtGui import QColor, QVector3D
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....widgets import WidgetMixin
from ...billiards.gui._room_light import radianceBytes, roomLight
from .. import Cabinet
from .._cabinet import BACK_WALL, LEFT_RAIL, LEFT_RAMP, LEFT_WALL, PUSHER
from .._cabinet import RIGHT_RAIL, RIGHT_RAMP, RIGHT_WALL, TABLE, TRAY
from .._cabinet import TRAY_FRONT
from ._coin_instances import CoinInstances
from ._coin_shape import CoinShape

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QResizeEvent, QShowEvent

  from .._coin_world import Box
  from .._machine_worker import Snapshot

#  How each of the cabinet's boxes looks
_KINDS = {TABLE: 'playfield', BACK_WALL: 'chrome', LEFT_WALL: 'glass',
          RIGHT_WALL: 'glass', TRAY: 'tray', TRAY_FRONT: 'tray',
          LEFT_RAMP: 'brass', RIGHT_RAMP: 'brass', LEFT_RAIL: 'brass',
          RIGHT_RAIL: 'brass'}


def _sceneBox(box: Box, kind: str) -> dict:
  """'box', in the machine's frame, as the scene takes it: its middle,
  half extents and turn with y up and z toward the player, and how it
  looks. The scene's axes are the machine's -x, z and y, a turn, so a
  quaternion's axis maps as a vector does."""
  (x, y, z), (hx, hy, hz) = box.centre, box.half
  qx, qy, qz, qw = box.turn
  return {'x': -x, 'y': z, 'z': y, 'sx': hx, 'sy': hz, 'sz': hy,
          'qw': qw, 'qx': -qx, 'qy': qz, 'qz': qy, 'kind': kind}


class PusherView(QWidget, WidgetMixin):
  """
  PusherView subclasses 'QWidget' and shows a coin pusher, its
  'cabinet', in 3D as the player stands before it: the table under its
  lamp, the pusher of polished steel whose top is the shelf, the chrome
  back wall, the brass ramps and rails of the chutes either side, the
  glass side walls and
  the tray; the coins in play as 'showSnapshot' last said, 20-krone
  coins with their pictures on their faces and their edges reeded; and
  'setBanner' writes a word big over it, the countdown's. A drag turns
  round the machine, the wheel comes nearer.

  The scene is drawn by a 'QQuickView', 'quick', set in the view through
  a window container: it renders in a thread of its own, so the window
  never waits on it, not even while Qt Quick 3D builds its shaders the
  first time (a 'QQuickWidget' draws in the window's own thread, and
  froze it then). The scene, 'pusher.qml', starts loading when the view
  is first shown; once it is in, 'loaded' is 'True' and 'sceneLoaded'
  is emitted; once its first frame is drawn, 'drawn' is 'True' and
  'firstDrawn' is emitted. 'problems' are the errors met loading it,
  none when all is well.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __scene_file__ = Path(__file__).with_name('pusher.qml')
  __coin_folder__ = Path(__file__).with_name('coins')
  __room_name__ = 'worQt-pusher-room.hdr'
  __room_size__ = 512, 256  # the room light's columns and rows

  #  Private Variables
  __view_cabinet__: Cabinet | None = None
  __view_component__: QQmlComponent | None = None
  __view_shape__: CoinShape | None = None
  __view_coins__: CoinInstances | None = None
  __view_waiting__: Snapshot | None = None
  __view_quick__: QQuickView | None = None
  __view_box__: QWidget | None = None

  #  Signals
  sceneLoaded = Signal()
  firstDrawn = Signal()

  #  Public Variables
  loaded = AttriBox[bool](False)
  drawn = AttriBox[bool](False)

  #  Virtual Variables
  cabinet: Field[Cabinet] = Field()
  quick: Field[QQuickView] = Field()
  problems: Field[tuple[str, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cabinet.GET
  def _getCabinet(self, ) -> Cabinet:
    """The 'cabinet' getter returns the machine shown."""
    if self.__view_cabinet__ is None:
      self.__view_cabinet__ = Cabinet()
    return self.__view_cabinet__

  @quick.GET
  def _getQuick(self, ) -> QQuickView:
    """The 'quick' getter returns the 'QQuickView' drawing the scene,
    made with its container the first time it is asked for."""
    if self.__view_quick__ is None:
      quick = QQuickView()
      quick.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
      quick.setColor(QColor(16, 16, 20))
      quick.frameSwapped.connect(self._swapped)
      self.__view_quick__ = quick
      self.__view_box__ = QWidget.createWindowContainer(quick, self)
      self.__view_box__.setGeometry(self.rect())
    return self.__view_quick__

  @problems.GET
  def _getProblems(self, ) -> tuple[str, ...]:
    """The 'problems' getter returns the errors met loading the scene,
    none when all is well."""
    return tuple(error.toString() for error in self.quick.errors())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: QShowEvent) -> None:
    """Shown the first time, the view starts loading its scene."""
    if self.__view_component__ is None:
      self.load()
    QWidget.showEvent(self, event)

  def resizeEvent(self, event: QResizeEvent) -> None:
    """The scene's container fills the view."""
    QWidget.resizeEvent(self, event)
    if self.__view_box__ is not None:
      self.__view_box__.setGeometry(self.rect())

  def sizeHint(self, ) -> QSize:
    return QSize(1100, 800)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(480, 360)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    QWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    QWidget.__init__(self, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def load(self, ) -> None:
    """The 'load' method starts loading the scene; once it is in,
    'sceneLoaded' is emitted and 'loaded' is 'True'.

    The scene is first compiled asynchronously. The 'App' has 'notify'
    in Python, so every event, on any thread, wants Python's lock; a
    'setSource' straight away would hold that lock waiting for QML's
    loading thread, which waits for the lock: a deadlock. Compiled, the
    scene is cached and 'setSource' does not wait."""
    url = QUrl.fromLocalFile(str(self.__scene_file__))
    mode = QQmlComponent.CompilationMode.Asynchronous
    component = QQmlComponent(self.quick.engine(), url, mode, self)
    self.__view_component__ = component
    if component.isLoading():
      component.statusChanged.connect(self._compiled)
    else:
      self._compiled()

  def showSnapshot(self, snapshot: Snapshot) -> None:
    """The 'showSnapshot' method shows the machine as 'snapshot' has it:
    the pusher where it is, the coins in play where they are; before the
    scene is in, it is shown once it is."""
    root = self.rootObject()
    if root is None or self.__view_coins__ is None:
      self.__view_waiting__ = snapshot
      return
    cabinet = self.cabinet
    box = cabinet.pusherAt(0.0)
    middle = snapshot.face - box.half[1]
    root.setProperty('pusherPlace', QVector3D(0.0, box.centre[2], middle))
    self.__view_coins__.setCoins(snapshot.places, snapshot.turns)

  def rootObject(self, ) -> object:
    """The 'rootObject' method returns the scene's root, or 'None' before
    it is loaded."""
    return self.quick.rootObject()

  def setBanner(self, text: str) -> None:
    """The 'setBanner' method writes 'text' big over the machine, popping
    in; nothing for none."""
    root = self.rootObject()
    if root is not None and root.property('banner') != text:
      root.setProperty('banner', text)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _compiled(self, *_) -> None:
    """Once the scene is compiled, sets it as the view's source, hands
    it the cabinet and the coins, and emits 'sceneLoaded'."""
    component = self.__view_component__
    if component is None or component.isLoading():
      return
    self.quick.setSource(component.url())
    self.loaded = True
    self._push()
    waiting = self.__view_waiting__
    self.__view_waiting__ = None
    if waiting is not None:
      self.showSnapshot(waiting)
    self.sceneLoaded.emit()

  def _swapped(self, ) -> None:
    """Notes the scene's first frame drawn."""
    if not self.drawn and self.loaded:
      self.drawn = True
      self.firstDrawn.emit()

  def _push(self, ) -> None:
    """Hands the scene the cabinet, the coins' shape and pictures, and
    the room's light; nothing before the scene is loaded."""
    root = self.rootObject()
    if root is None:
      return
    cabinet = self.cabinet
    boxes = cabinet.boxes()
    root.setProperty('boxes', [_sceneBox(boxes[k], kind)
                               for k, kind in _KINDS.items()])
    hx, hy, hz = boxes[PUSHER].half
    root.setProperty('pusherHalf', QVector3D(hx, hz, hy))
    root.setProperty('front', cabinet.front)
    root.setProperty('tableWidth', cabinet.width)
    if self.__view_shape__ is None:
      self.__view_shape__ = CoinShape(cabinet.coin)
      self.__view_coins__ = CoinInstances()
    root.setProperty('coinShape', self.__view_shape__)
    root.setProperty('coinInstances', self.__view_coins__)
    folder = self.__coin_folder__
    root.setProperty('headPicture',
                     QUrl.fromLocalFile(str(folder / 'head.png')))
    root.setProperty('tailPicture',
                     QUrl.fromLocalFile(str(folder / 'tail.png')))
    if not root.property('roomLight').toString():
      root.setProperty('roomLight', QUrl.fromLocalFile(str(self.roomFile())))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def roomFile(self, ) -> Path:
    """The 'roomFile' method writes the light of the room round the
    machine, borrowed from the billiards room, as a Radiance '.hdr'
    image in the temporary folder, and returns where."""
    path = Path(QDir.tempPath()) / self.__room_name__
    width, height = self.__room_size__
    path.write_bytes(radianceBytes(roomLight(width, height)))
    return path
