"""
Viewport shows a sandbox world through a pair of eyes, drawn by the GPU
(Qt Quick 3D, 'sandbox.qml').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QQuaternion, QVector3D
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QWidget

from ._bodymesh import bodyRows, quadRows
from ._mesh import Mesh
from ._skin import PARTS, partRows
from ._tool import GRIP

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._world import World

#  The scene, beside this file; toward the sun and toward the sky's
#  light, in the world; the eyes' near cut, m (the scene is in cm).
_SCENE = Path(__file__).with_name('sandbox.qml')
_SUN = (0.35, -0.5, 0.8)
_SKY = (-0.4, 0.45, 0.9)
NEAR = 0.05
#  How often the frames drawn a second are counted anew, s.
COUNTED = 0.5
#  How many pushes of the bodies' meshes are kept alive.
KEPT_PUSHES = 4
#  The line of help shown while the mouse is free.
HINT = ('Click to look round.    W A S D walk, Shift runs, Space jumps '
        '(twice: flies).    E: items (by a vehicle: ride).    1 to 9: '
        'hotbar.    Tab: eyes, behind, before.    Esc lets the mouse go.')
#  Where the right hand holds a tool on the figure's right arm, pixels
#  from the arm's pivot (its shoulder) along the arm; the turn taking
#  the eyes' frame (x right, y up, z back), in which a tool is placed,
#  to the arm's own (hanging along -z, its right -y): about z, -90
#  degrees.
HAND = 9.0
_HANDED = QQuaternion.fromAxisAndAngle(QVector3D(0.0, 0.0, 1.0), -90.0)


class Viewport(QWidget):
  """
  Viewport shows a world ('shown') through a pair of eyes: its fixtures
  and its drawn bodies (as its 'drawn' and 'looks' say), placed as the
  world's last step left them; a cross in the middle while 'looking',
  else a line of help; 'fps' counts the frames the GPU draws a second.
  Seen from behind ('figureShown'), the avatar's figure is drawn
  wearing its skin, the tool in its right hand, and the tool before the
  eyes is not. The scene is drawn in a 'QQuickView' of its own
  ('quick', set in through a window container); keys and the mouse
  come to that window (whoever wants them filters its events). Until
  the scene has loaded nothing is shown; 'problems' says why it would
  not.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  menuPicked = Signal(str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    QWidget.__init__(self)
    self.quick = QQuickView()
    self.quick.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    self.quick.setColor(QColor(143, 180, 216))
    self.box = QWidget.createWindowContainer(self.quick, self)
    self.box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.component, self.problems, self.loaded = None, (), False
    self._world, self._assembly, self._drawn = None, None, None
    self._kept, self._rows, self._pushed = [], {}, []
    self._hotbar, self._inHand, self._glowing = None, False, None
    self._figure, self._chased = None, None
    self._camera, self._prompt = None, None
    self.fps, self._frames, self._since = 0.0, 0, time.perf_counter()
    self.quick.frameSwapped.connect(self._swapped)
    self.setMinimumSize(800, 600)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: object) -> None:
    """Shown the first time, the viewport starts loading its scene."""
    if self.component is None:
      self.load()
    QWidget.showEvent(self, event)

  def resizeEvent(self, event: object) -> None:
    """The scene's container fills the viewport."""
    QWidget.resizeEvent(self, event)
    self.box.setGeometry(self.rect())

  def sizeHint(self, ) -> QSize:
    """The viewport would be 1280 x 760."""
    return QSize(1280, 760)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def load(self, ) -> None:
    """The 'load' method starts loading the scene. It is compiled first,
    asynchronously: the app has 'notify' in Python, so every event on
    any thread wants Python's lock, and a 'setSource' straight away
    would hold it waiting for QML's loading thread, which waits for the
    lock. Compiled, the scene is cached and 'setSource' does not
    wait."""
    url = QUrl.fromLocalFile(str(_SCENE))
    mode = QQmlComponent.CompilationMode.Asynchronous
    self.component = QQmlComponent(self.quick.engine(), url, mode, self)
    if self.component.isLoading():
      self.component.statusChanged.connect(self._compiled)
    else:
      self._compiled()

  def shown(self, world: World, eye: tuple, forward: tuple,
            looking: bool, up: tuple = (0.0, 0.0, 1.0),
            aimed: bool = True) -> None:
    """The 'shown' method shows 'world' as its last step left it, seen
    from 'eye' (m, in the world) along 'forward' (a unit vector), 'up'
    the view's way up (a rider's in a loop: upside down); a cross in
    the middle while 'looking' and 'aimed' (from behind the avatar the
    middle is not where it aims), else, not looking, the line of
    help."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None:
      return
    assembly, states, _ = world.snapshot()
    if world is not self._world:
      self._world = world
      root.setProperty('fixtures', self._fixturesOf(world))
    if assembly is not self._assembly or world.drawn is not self._drawn:
      self._assembly, self._drawn = assembly, world.drawn
      root.setProperty('bodies', self._bodiesOf(world, assembly))
    root.setProperty('places', [QVector3D(*state.place)
                                for state in states])
    root.setProperty('turns', [QQuaternion(*state.turn)
                               for state in states])
    self._camera = eye, forward
    root.setProperty('cameraPlace', QVector3D(*_sceneOf(eye)))
    root.setProperty('cameraTurn', _turnAlong(forward, up))
    root.setProperty('crosshair', looking and aimed)
    root.setProperty('hint', '' if looking else HINT)

  def figureShown(self, skin: object, scale: float, soles: tuple,
                  turn: tuple, angles: tuple, holding: bool) -> None:
    """The 'figureShown' method draws the avatar's figure (its eyes
    seen from behind, the tool before them not drawn): the skin's
    'PARTS' wearing 'skin' (a picture's file), 'scale' m a pixel, its
    soles at 'soles' (m, in the world), turned by 'turn' (the world's),
    each part turned about its own left by its 'angles' (rad), the
    tool in its right hand while 'holding'."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None:
      return
    if self._figure is None or self._figure[0] != (str(skin), scale):
      self._figure = (str(skin), scale), self._figureOf(scale)
      root.setProperty('figureSkin', QUrl.fromLocalFile(str(skin))
                       .toString())
      root.setProperty('figureParts', self._figure[1])
      shoulder = PARTS[2][2]
      root.setProperty('figureHand', QVector3D(*(scale * x
                                                 for x in shoulder)))
      root.setProperty('figureGrip', QVector3D(0.0, 0.0, -HAND * scale))
      root.setProperty('figureHanded', _HANDED)
    root.setProperty('figurePlace', QVector3D(*soles))
    root.setProperty('figureTurn', QQuaternion(*turn))
    root.setProperty('figureTurns', [QQuaternion.fromAxisAndAngle(
      QVector3D(0.0, 1.0, 0.0), math.degrees(angle)) for angle in angles])
    root.setProperty('holding', holding)
    if self._chased is not True:
      self._chased = True
      root.setProperty('chased', True)

  def promptShown(self, place: tuple, key: str, text: str) -> None:
    """The 'promptShown' method floats a prompt over 'place' (m, in the
    world; user, 2026-11-16: "when we are near enough to the vehicle to
    get in, a floating key_E button should appear with a prompt like
    'board'"): the key to press on a key cap, and what it does ('text');
    hidden while 'place' is not before the eyes last shown."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None or self._camera is None:
      return
    eye, forward = self._camera
    ahead = sum((p - e) * f for p, e, f in zip(place, eye, forward))
    if ahead <= NEAR:
      self.promptHidden()
      return
    if self._prompt != (key, text):
      self._prompt = key, text
      root.setProperty('promptKey', key)
      root.setProperty('promptText', text)
    root.setProperty('promptPlace', QVector3D(*_sceneOf(place)))
    root.setProperty('promptOn', True)

  def promptHidden(self, ) -> None:
    """The 'promptHidden' method takes the floating prompt away."""
    root = self.quick.rootObject() if self.loaded else None
    if root is not None and self._prompt is not None:
      self._prompt = None
      root.setProperty('promptOn', False)

  def peepsShown(self, handles: list) -> None:
    """The 'peepsShown' method draws the world's levers ('FourthPeep'),
    each handle (its pivot, m, in the world; its turn there, along its
    own z; how long it is, m) with its knob."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None:
      return
    root.setProperty('peeps', [
      {'place': QVector3D(*place), 'turn': QQuaternion(*turn),
       'length': length} for place, turn, length in handles])

  def figureHidden(self, ) -> None:
    """The 'figureHidden' method draws no figure (the eyes the avatar's
    own, the tool before them)."""
    root = self.quick.rootObject() if self.loaded else None
    if root is not None and self._chased is not False:
      self._chased = False
      root.setProperty('chased', False)

  def debugShown(self, lines: str, warning: str) -> None:
    """The 'debugShown' method shows 'lines' of how things run in the
    top left corner, and under them 'warning' ('': none) in orange."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None:
      return
    root.setProperty('debug', lines)
    root.setProperty('debugWarning', warning)

  def marked(self, pointed: int, held: int) -> None:
    """The 'marked' method tints body 'pointed' as pointed at and body
    'held' as held (None: none)."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None:
      return
    root.setProperty('pointedBody', -1 if pointed is None else pointed)
    root.setProperty('heldBody', -1 if held is None else held)

  def inHand(self, tool: object) -> None:
    """The 'inHand' method shows 'tool' where a hand would hold it (the
    boxes of its 'parts', its 'label' painted on it and its 'model',
    fixed to the eyes; None: nothing)."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None or tool is self._inHand:
      return
    self._inHand = tool
    parts, label = ((), None) if tool is None else (tuple(tool.parts),
                                                    tool.label)
    root.setProperty('heldParts', [
      {'position': QVector3D(*(100.0 * x for x in place)),
       'scale': QVector3D(*size),
       'rotation': QQuaternion.rotationTo(QVector3D(0.0, 0.0, 1.0),
                                          QVector3D(*along)),
       'colour': QColor(*rgb)}
      for size, place, along, rgb in parts])
    model = None if tool is None else tool.model
    path, at, angles, size = model or ('', (0.0, 0.0, 0.0),
                                       (0.0, 0.0, 0.0), 0.0)
    root.setProperty('heldModel', QUrl.fromLocalFile(path).toString()
                     if path else '')
    root.setProperty('heldModelPlace', QVector3D(*(100.0 * x for x in at)))
    root.setProperty('heldModelTurn', QVector3D(*angles))
    root.setProperty('heldModelScale', 100.0 * size)
    root.setProperty('handModelPlace', QVector3D(*(a - g for a, g in zip(
      at, GRIP))))
    root.setProperty('handModelScale', size)
    glow = None if tool is None else tool.glow
    root.setProperty('glowPlace', QVector3D(*(100.0 * x for x in (
      glow or (0.0, 0.0, 0.0)))))
    text, place, turn, rgb, high = label or ('', (0.0, 0.0, 0.0), 0.0,
                                             (0, 0, 0), 0.0)
    root.setProperty('heldLabel', text)
    root.setProperty('heldLabelPlace', QVector3D(*(100.0 * x
                                                   for x in place)))
    root.setProperty('heldLabelTurn', turn)
    root.setProperty('heldLabelColour', QColor(*rgb))
    root.setProperty('heldLabelHeight', 100.0 * high)

  def menuShown(self, title: str, readout: str, buttons: list,
                world: list) -> None:
    """The 'menuShown' method opens the E menu drawn in the scene:
    'title', what it reads ('readout'), its 'buttons' and the 'world''s
    under them (each (text, key): a click emits 'menuPicked' with the
    key; a click beside the menu 'close')."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None:
      return
    root.setProperty('menuTitle', title)
    root.setProperty('menuReadout', readout)
    root.setProperty('menuButtons', [{'text': text, 'key': key}
                                     for text, key in buttons])
    root.setProperty('menuWorld', [{'text': text, 'key': key}
                                   for text, key in world])
    root.setProperty('menuOpen', True)

  def menuHidden(self, ) -> None:
    """The 'menuHidden' method closes the E menu."""
    root = self.quick.rootObject() if self.loaded else None
    if root is not None:
      root.setProperty('menuOpen', False)

  def glowShown(self, on: bool) -> None:
    """The 'glowShown' method lights the tool's glow ('on': it holds
    something) or puts it out."""
    root = self.quick.rootObject() if self.loaded else None
    if root is None or on == self._glowing:
      return
    self._glowing = on
    root.setProperty('heldGlow', on)

  def handsMoved(self, offset: tuple) -> None:
    """The 'handsMoved' method puts the hands (and what they hold)
    'offset' right, up and forward against the eyes, m."""
    root = self.quick.rootObject() if self.loaded else None
    if root is not None:
      right, up, forward = offset
      root.setProperty('heldOffset', QVector3D(100.0 * right, 100.0 * up,
                                               -100.0 * forward))

  def hotbarShown(self, names: list, icons: list, selected: int) -> None:
    """The 'hotbarShown' method shows the hotbar: each slot's tool's icon
    (an image file), or its name where it has none ('' empty), slot
    'selected' in hand."""
    root = self.quick.rootObject() if self.loaded else None
    shown = list(names), list(icons), selected
    if root is None or shown == self._hotbar:
      return
    self._hotbar = shown
    root.setProperty('hotbarIcons', [QUrl.fromLocalFile(icon).toString()
                                     if icon else '' for icon in icons])
    root.setProperty('hotbar', list(names))
    root.setProperty('slot', selected)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _swapped(self, ) -> None:
    """Counts a frame drawn; every 'COUNTED' s works out 'fps', the
    frames the GPU drew a second."""
    self._frames += 1
    now = time.perf_counter()
    if now - self._since >= COUNTED:
      self.fps = self._frames / (now - self._since)
      self._frames, self._since = 0, now

  def _compiled(self, *_) -> None:
    """Once the scene is compiled, sets it as the view's source and lights
    it; or notes why it would not compile."""
    component = self.component
    if component is None or component.isLoading():
      return
    if component.isError():
      self.problems = tuple(error.toString()
                            for error in component.errors())
      return
    self.quick.setSource(component.url())
    self.problems = tuple(error.toString() for error in self.quick.errors())
    root = self.quick.rootObject()
    self.loaded = root is not None
    if root is None:
      return
    root.menuPicked.connect(self.menuPicked)
    root.setProperty('cameraNear', 100.0 * NEAR)
    root.setProperty('sunTurn', _turnAlong(tuple(-x for x in _SUN)))
    root.setProperty('skyTurn', _turnAlong(tuple(-x for x in _SKY)))

  def _figureOf(self, scale: float) -> list:
    """Returns the figure's parts as the scene takes them (each part's
    block and its outer layer, at 'scale' m a pixel), their meshes kept
    alive."""
    out = []
    for index, part in enumerate(PARTS):
      for outer in (False, True):
        mesh = Mesh(*partRows(part, outer, scale))
        self._kept.append(mesh)
        out.append({'geometry': mesh, 'index': index, 'outer': outer,
                    'pivot': QVector3D(*(scale * x for x in part[2]))})
    return out

  def _fixturesOf(self, world: World) -> list:
    """Returns the world's fixtures as the scene takes them, their meshes
    kept alive."""
    out = []
    for look, quads in world.fixtures().items():
      mesh = Mesh(*quadRows(quads))
      self._kept.append(mesh)
      out.append(_lookOf(world, look, {'geometry': mesh}))
    return out

  def _bodiesOf(self, world: World, assembly: object) -> list:
    """Returns the world's drawn bodies as the scene takes them (a
    dressed one as its parts, each its own look). Each
    push makes every body's mesh anew (its rows worked out once and
    kept): pushed again with the meshes it had, Qt Quick 3D made its
    models anew and drew none of them (user, 2026-11-16: a ball given,
    the island vanished, still solid). The last 'KEPT_PUSHES' pushes'
    meshes are kept alive while Qt lets go of their old models."""
    out, meshes = [], []
    for index, look in sorted(world.drawn.items()):
      parts = world.dressed.get(index)
      if parts:
        for rows, indices, partLook in parts:
          mesh = Mesh(rows, indices)
          meshes.append(mesh)
          out.append(_lookOf(world, partLook, {'geometry': mesh,
                                               'body': index}))
        continue
      body = assembly.bodies[index]
      kept = self._rows.get(id(body))
      if kept is None or kept[0] is not body:
        kept = body, bodyRows(body)
        self._rows[id(body)] = kept
      mesh = Mesh(*kept[1])
      meshes.append(mesh)
      out.append(_lookOf(world, look, {'geometry': mesh, 'body': index}))
    self._pushed = (self._pushed + [meshes])[-KEPT_PUSHES:]
    return out


def _lookOf(world: World, look: str, entry: dict) -> dict:
  """Returns 'entry' with the colour, metalness and roughness of the
  world's 'look'."""
  rgb, metal, rough = world.looks[look]
  entry['colour'], entry['metal'], entry['rough'] = (QColor(*rgb), metal,
                                                     rough)
  return entry


def _sceneOf(point: tuple) -> tuple[float, float, float]:
  """Returns the world's 'point' (m, z up) in the scene (cm, y up)."""
  return 100.0 * point[0], 100.0 * point[2], -100.0 * point[1]


def _turnAlong(forward: tuple,
               upward: tuple = (0.0, 0.0, 1.0)) -> QQuaternion:
  """Returns the scene's turn that points a camera or a light (looking
  along its own -z, its y up) along the world's 'forward', kept upright
  toward the world's 'upward'."""
  x, y, z = forward[0], forward[2], -forward[1]
  size = math.sqrt(x * x + y * y + z * z)
  back = (-x / size, -y / size, -z / size)
  up = (upward[0], upward[2], -upward[1])
  if abs(back[0] * up[0] + back[1] * up[1] + back[2] * up[2]) > 0.999:
    up = (0.0, 0.0, 1.0) if abs(back[2]) < 0.999 else (1.0, 0.0, 0.0)
  right = (up[1] * back[2] - up[2] * back[1],
           up[2] * back[0] - up[0] * back[2],
           up[0] * back[1] - up[1] * back[0])
  size = math.sqrt(sum(a * a for a in right))
  right = tuple(a / size for a in right)
  upright = (back[1] * right[2] - back[2] * right[1],
             back[2] * right[0] - back[0] * right[2],
             back[0] * right[1] - back[1] * right[0])
  return QQuaternion.fromAxes(QVector3D(*right), QVector3D(*upright),
                              QVector3D(*back))
