"""
SpaceViewport shows the solar system, drawn by the GPU (Qt Quick 3D,
'space.qml'): the flight view in its two layers, or the map.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QQuaternion, QVector3D
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QWidget

from worQt.gaming.sandbox._mesh import Mesh

from ._line import Line
from ._meshes import capRows, padRows, ringRows, rocketParts, sphereRows
from ._navball import mirroredRows

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem

_SCENE = Path(__file__).with_name('space.qml')
#  How often the frames drawn a second are counted anew, s.
COUNTED = 0.5
#  How many caps made are kept alive (Qt lets go of the old a frame or
#  so after the new is set).
KEPT_CAPS = 3
#  The flight view's spheres (spokes, rings): Terra's finest, seen from
#  orbit; the map's coarse.
TERRA_SPHERE = (512, 256)
SPHERE = (192, 96)
MAP_SPHERE = (96, 48)
#  The rocket's looks: colour (0 to 255), metalness, roughness.
ROCKET_LOOKS = {'plug': ((70, 72, 78), 0.3, 0.45),
                'tank': ((236, 236, 240), 0.0, 0.5),
                'capsule': ((58, 62, 70), 0.1, 0.5),
                'legs': ((150, 150, 156), 0.2, 0.6)}
PAD_LOOK = ((150, 148, 142), 0.0, 0.9)
#  The near layer's slots: the pad, the rocket.
PAD_SLOT, ROCKET_SLOT = 0, 1
#  The artificial horizon's sphere (spokes, rings).
NAV_SPHERE = (96, 48)
#  What on the scene takes its own clicks (by its object's name).
CLICKED = ('board', 'navball')
#  The map's lines' colours: a body's path, the vessel's.
ORBIT_COLOUR = '#3f5f8f'
PATH_COLOUR = '#7dff9a'


class SpaceViewport(QWidget):
  """
  SpaceViewport shows the solar system: furnished once ('furnished':
  every body's sphere wearing its look, Saturn's rings, the pad, the
  rocket, the map's bodies and paths), then each frame the flight view
  ('flightShown') or the map ('mapShown') as 'Scenery' works them out,
  and what the flight says ('hudShown'). The scene is drawn in a
  'QQuickView' of its own ('quick', set in through a window container);
  keys and the mouse come to that window. 'fps' counts the frames the
  GPU draws a second; 'problems' says why the scene would not load.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  boardPicked = Signal(str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    QWidget.__init__(self)
    self.quick = QQuickView()
    self.quick.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    self.quick.setColor(QColor(0, 0, 0))
    self.box = QWidget.createWindowContainer(self.quick, self)
    self.box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.component, self.problems, self.loaded = None, (), False
    self.furnishedYet, self._kept, self._caps = False, [], []
    self._path = None
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
    """The 'load' method starts loading the scene, compiled first,
    asynchronously (as the sandbox's 'Viewport.load' says why)."""
    url = QUrl.fromLocalFile(str(_SCENE))
    mode = QQmlComponent.CompilationMode.Asynchronous
    self.component = QQmlComponent(self.quick.engine(), url, mode, self)
    if self.component.isLoading():
      self.component.statusChanged.connect(self._compiled)
    else:
      self._compiled()

  def furnished(self, system: SolarSystem, files: dict, orbits: list,
                navball: object) -> bool:
    """The 'furnished' method puts in what is drawn all along: each body's
    sphere wearing its look ('files': each look's picture by name),
    Saturn's rings, the pad, the rocket, the map's bodies and each
    body's path ('orbits', 'Scenery.orbitsOf') and the vessel's, the
    artificial horizon (its picture, 'navball'). Returns whether it could
    (the scene loaded)."""
    root = self._root()
    if root is None:
      return False
    far, near, bodies, lines = [], [], [], []
    for index, body in enumerate(system.bodies):
      picture = QUrl.fromLocalFile(str(files[body.look])).toString()
      glow = 1.0 if body.parent is None else 0.0
      shape = TERRA_SPHERE if body.name == 'Terra' else SPHERE
      far.append({'geometry': self._kept1(Mesh(*sphereRows(*shape))),
                  'picture': picture, 'glow': glow, 'slot': index,
                  'ring': False})
      bodies.append({'geometry': self._kept1(Mesh(*sphereRows(
        *MAP_SPHERE))), 'picture': picture, 'glow': glow, 'slot': index,
                     'ring': False})
      if body.name == 'Saturn':
        rings = QUrl.fromLocalFile(str(files['rings'])).toString()
        for out in (far, bodies):
          out.append({'geometry': self._kept1(Mesh(*ringRows())),
                      'picture': rings, 'glow': 0.0, 'slot': index,
                      'ring': True})
    near.append(_partOf(self._kept1(Mesh(*padRows())), PAD_LOOK, PAD_SLOT,
                        False))
    for name, (rows, indices) in rocketParts().items():
      near.append(_partOf(self._kept1(Mesh(rows, indices)),
                          ROCKET_LOOKS[name], ROCKET_SLOT, False))
    for slot, points in enumerate(orbits[1:]):
      lines.append({'geometry': self._kept1(Line(points)),
                    'colour': QColor(ORBIT_COLOUR), 'slot': slot})
    self._path = self._kept1(Line([(0.0, 0.0, 0.0)] * 2))
    lines.append({'geometry': self._path, 'colour': QColor(PATH_COLOUR),
                  'slot': len(orbits) - 1})
    root.setProperty('farBodies', far)
    root.setProperty('nearParts', near)
    root.setProperty('mapBodies', bodies)
    root.setProperty('mapLines', lines)
    root.setProperty('capPicture', QUrl.fromLocalFile(str(files[
      'terra'])).toString())
    rows, indices = sphereRows(*NAV_SPHERE)
    root.setProperty('navGeometry', self._kept1(Mesh(mirroredRows(rows),
                                                     indices)))
    root.setProperty('navPicture', QUrl.fromLocalFile(str(navball))
                     .toString())
    self._files = files
    self.furnishedYet = True
    return True

  def flightShown(self, frame: dict, system: SolarSystem,
                  anchor: int) -> None:
    """The 'flightShown' method shows a frame of the flight view
    ('Scenery.flightOf'), the vessel kept from body 'anchor'."""
    root = self._root()
    if root is None or not self.furnishedYet:
      return
    root.setProperty('mapOpen', False)
    root.setProperty('cameraTurn', sceneTurnOf(frame['forward'],
                                               frame['up']))
    root.setProperty('sunTurn', sceneTurnOf(frame['sun'], _across(
      frame['sun'])))
    root.setProperty('skyColour', QColor(*(int(x) for x in frame['sky'])))
    far = frame['far']
    root.setProperty('farPlaces', [QVector3D(*p) for p, _, _ in far])
    root.setProperty('farTurns', [QQuaternion(*q) for _, q, _ in far])
    root.setProperty('farScales', [float(s) for _, _, s in far])
    places, turns, shown = [None] * 2, [None] * 2, [False] * 2
    for slot, (place, turn, seen) in ((PAD_SLOT, frame['pad']),
                                      (ROCKET_SLOT, frame['rocket'])):
      places[slot], turns[slot] = QVector3D(*place), QQuaternion(*turn)
      shown[slot] = bool(seen)
    root.setProperty('nearPlaces', places)
    root.setProperty('nearTurns', turns)
    root.setProperty('nearShown', shown)
    place, turn, seen, made = frame['cap']
    if made is not None:
      cap = Mesh(*capRows(*made))
      self._caps = (self._caps + [cap])[-KEPT_CAPS:]
      root.setProperty('capGeometry', cap)
      root.setProperty('capPicture', QUrl.fromLocalFile(str(self._files[
        system.bodies[anchor].look])).toString())
    root.setProperty('capPlace', QVector3D(*place))
    root.setProperty('capTurn', QQuaternion(*turn))
    root.setProperty('capShown', bool(seen) and bool(self._caps))

  def mapShown(self, frame: dict) -> None:
    """The 'mapShown' method shows a frame of the map
    ('Scenery.mapOf')."""
    root = self._root()
    if root is None or not self.furnishedYet:
      return
    root.setProperty('mapOpen', True)
    root.setProperty('mapCameraTurn', sceneTurnOf(frame['forward'],
                                                  frame['up']))
    bodies = frame['bodies']
    root.setProperty('mapPlaces', [QVector3D(*p) for p, _, _ in bodies])
    root.setProperty('mapTurns', [QQuaternion(*q) for _, q, _ in bodies])
    root.setProperty('mapScales', [float(s) for _, _, s in bodies])
    self._path.pointed(frame['path'])
    lines = frame['lines'] + [frame['pathAt']]
    root.setProperty('linePlaces', [QVector3D(*p) for p, _ in lines])
    root.setProperty('lineScales', [float(s) for _, s in lines])
    root.setProperty('marks', [{'x': m['x'], 'y': m['y'],
                                'text': m['text'],
                                'colour': QColor(m['colour'])}
                               for m in frame['marks']])

  def navballShown(self, frame: dict | None) -> None:
    """The 'navballShown' method shows the artificial horizon as
    'Navball.frameOf' has it (None: hidden)."""
    root = self._root()
    if root is None or not self.furnishedYet:
      return
    root.setProperty('navShown', frame is not None)
    if frame is None:
      return
    root.setProperty('navTurn', QQuaternion(*frame['turn']))
    root.setProperty('navMarks', frame['marks'])
    root.setProperty('navPitch', frame['pitch'])
    root.setProperty('navHeading', frame['heading'])
    root.setProperty('navKind', frame['kind'])

  def boardShown(self, board: dict) -> None:
    """The 'boardShown' method shows the control board: its 'throttle',
    'mode', 'warp', 'toAp', 'ascent', 'phase', 'target', 'map' and the
    keys 'held' (their names)."""
    root = self._root()
    if root is None:
      return
    for name, key in (('throttle', 'boardThrottle'), ('mode', 'boardMode'),
                      ('warp', 'boardWarp'), ('toAp', 'boardToAp'),
                      ('ascent', 'boardAscent'), ('phase', 'boardPhase'),
                      ('target', 'boardTarget'), ('map', 'boardMap')):
      root.setProperty(key, board[name])
    root.setProperty('boardHeld', '|' + '|'.join(board['held']) + '|')

  def takesClick(self, at: QPointF) -> bool:
    """The 'takesClick' method says whether the scene takes a click at
    'at' itself (on the control board or the horizon)."""
    root = self._root()
    if root is None:
      return False
    under = root.childAt(at.x(), at.y())
    return under is not None and under.objectName() in CLICKED

  def hudShown(self, readout: str, hint: str, status: str) -> None:
    """The 'hudShown' method shows what the flight says ('readout'), the
    keys ('hint') and a word in the middle ('status', '' none)."""
    root = self._root()
    if root is None:
      return
    root.setProperty('readout', readout)
    root.setProperty('hint', hint)
    root.setProperty('status', status)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _root(self, ) -> object:
    """Returns the scene's root once loaded, else None."""
    return self.quick.rootObject() if self.loaded else None

  def _kept1(self, made: object) -> object:
    """Keeps 'made' (a mesh or a line) alive with the viewport and
    returns it."""
    self._kept.append(made)
    return made

  def _swapped(self, ) -> None:
    """Counts a frame drawn; every 'COUNTED' s works out 'fps'."""
    self._frames += 1
    now = time.perf_counter()
    if now - self._since >= COUNTED:
      self.fps = self._frames / (now - self._since)
      self._frames, self._since = 0, now

  def _compiled(self, *_) -> None:
    """Once the scene is compiled, sets it as the view's source; or notes
    why it would not compile."""
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
    if root is not None:
      root.boardPicked.connect(self.boardPicked)


def _partOf(geometry: object, look: tuple, slot: int, culled: bool) -> dict:
  """Returns a near part as the scene takes it."""
  rgb, metal, rough = look
  return {'geometry': geometry, 'colour': QColor(*rgb), 'metal': metal,
          'rough': rough, 'picture': '', 'slot': slot, 'culled': culled}


def _across(way: tuple) -> tuple:
  """Returns a unit vector across 'way' (an up for a light)."""
  other = (0.0, 0.0, 1.0) if abs(way[2]) < 0.9 else (1.0, 0.0, 0.0)
  cross = (way[1] * other[2] - way[2] * other[1],
           way[2] * other[0] - way[0] * other[2],
           way[0] * other[1] - way[1] * other[0])
  size = math.sqrt(sum(x * x for x in cross))
  return tuple(x / size for x in cross)


def sceneTurnOf(forward: tuple, up: tuple) -> QQuaternion:
  """Returns the scene's turn that points a camera or a light (looking
  along its own -z, its y up) along the ecliptic's 'forward', kept
  upright toward the ecliptic's 'up' (the scene's axes: y the
  ecliptic's z, z its -y)."""
  x, y, z = forward[0], forward[2], -forward[1]
  size = math.sqrt(x * x + y * y + z * z)
  back = (-x / size, -y / size, -z / size)
  upward = (up[0], up[2], -up[1])
  if abs(sum(a * b for a, b in zip(back, upward))) > 0.9999:
    upward = (0.0, 0.0, 1.0) if abs(back[2]) < 0.999 else (1.0, 0.0, 0.0)
  right = (upward[1] * back[2] - upward[2] * back[1],
           upward[2] * back[0] - upward[0] * back[2],
           upward[0] * back[1] - upward[1] * back[0])
  size = math.sqrt(sum(a * a for a in right))
  right = tuple(a / size for a in right)
  upright = (back[1] * right[2] - back[2] * right[1],
             back[2] * right[0] - back[0] * right[2],
             back[0] * right[1] - back[1] * right[0])
  return QQuaternion.fromAxes(QVector3D(*right), QVector3D(*upright),
                              QVector3D(*back))
