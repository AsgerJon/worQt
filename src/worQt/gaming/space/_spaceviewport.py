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
from worQt.gaming.sandbox._skin import ASGERJON, PARTS, partRows

from worQt.gaming.sandbox import Knob, Pushbutton, Slider

from . import _cabin, _dashboard, _deckmodel
from ._cabinpictures import cabinPicturesReady
from ._furnishings import furnishings, looseParts
from ._cockpit import BALL_RADIUS, LAMPS, SCALE
from ._meshes import capRows, padRows, ringRows, rocketParts, sphereRows
from ._navball import mirroredRows
from ._scenery import AFTER_PIECES, MARK_KINDS, MECHANISM
from ._teleprinter import FONT
from ._dashpictures import MARK_NAMES

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
#  The near layer's slots: the pad, the rocket (its cabin's still parts
#  with it), then the cabin's moving parts ('Scenery.cabinOf': the
#  dashboard's pieces, the ball, its marks, Asger's limbs).
PAD_SLOT, ROCKET_SLOT = 0, 1
CABIN_SLOT = 2
#  The cabin's looks: colour, metalness (kept low: full metal draws black
#  with no sky to mirror), roughness. 1970s: warm walls, a brown carpet,
#  an orange seat, rosewood, brushed aluminium and chrome.
CABIN_LOOKS = {'wall': ((214, 208, 196), 0.0, 0.85),
               'floor': ((70, 44, 30), 0.0, 0.95),
               'seat': ((214, 96, 28), 0.0, 0.6),
               'rosewood': ((92, 44, 30), 0.1, 0.45),
               'aluminium': ((206, 208, 212), 0.3, 0.32),
               'chrome': ((236, 238, 242), 0.3, 0.12),
               'black': ((22, 22, 24), 0.2, 0.5),
               'smoke': ((30, 26, 24), 0.2, 0.15),
               'beige': ((218, 206, 178), 0.0, 0.7),
               'white': ((242, 240, 232), 0.0, 0.8),
               'needle': ((255, 236, 210), 0.0, 1.0),
               'picture': ((255, 255, 255), 0.0, 0.6),
               'smoke glass': ((84, 84, 84), 0.0, 0.3),
               'pine': ((255, 255, 255), 0.0, 0.8),
               'boards': ((255, 255, 255), 0.0, 0.7),
               'brass': ((196, 160, 92), 0.3, 0.3),
               'wood': ((255, 255, 255), 0.0, 0.55),
               'dome': ((255, 255, 255), 0.0, 0.04)}
#  How bright an unlit lamp's glass is, of its colour.
UNLIT = 0.22
WINDOW_GLASS = ((200, 225, 245), 0.08)
#  The horizon's ball: lit, glossy enamel (user, 2026-11-16: "it should
#  be rendered as an actual ball"); its mechanism's looks (brass ring and
#  axles, chrome hubs); see-through, a picture's clear parts drawn so.
BALL_LOOK = ((228, 228, 232), 0.0, 0.16)
MECHANISM_LOOKS = ('brass', 'brass', 'chrome')
SEE_THROUGH = 0.99
#  The altimeter's mark: pink, as the aim is.
BUG_COLOUR = (255, 90, 200)
#  The enchanted knobs' glint: its picture (the cabin's pictures') and
#  how many times its streaks slide across the knob in the glint's loop
#  ('space.qml'), by the knob's action (the gravity's "lots o glint",
#  faster); see-through (Qt blends a screen only so), black adding
#  nothing.
GLINT_LOOKS = {'warp': ('glint', 1.0), 'gravity': ('sparkle', 2.0)}
#  The cabin's furnishings' looks (user, 2026-11-16: "the contents of a
#  camping cabin ... the same 'hygge'"): warm woods, wool, cream and rust
#  cushions, wax, ceramics, green leaves, books; the rug and the blanket
#  their pictures'.
HYGGE_LOOKS = {'sofa': ((128, 118, 106), 0.0, 0.95),
               'cream': ((232, 222, 200), 0.0, 0.9),
               'rust': ((176, 84, 46), 0.0, 0.9),
               'blanket': ((255, 255, 255), 0.0, 0.95),
               'rug': ((255, 255, 255), 0.0, 1.0),
               'oak': ((152, 102, 62), 0.0, 0.6),
               'brass': ((196, 160, 92), 0.3, 0.3),
               'wax': ((240, 232, 210), 0.0, 0.7),
               'ceramic': ((236, 238, 240), 0.0, 0.3),
               'blue': ((62, 92, 140), 0.0, 0.4),
               'black': ((30, 30, 32), 0.2, 0.4),
               'leaf': ((72, 118, 58), 0.0, 0.8),
               'terracotta': ((184, 96, 60), 0.0, 0.85),
               'book red': ((142, 42, 36), 0.0, 0.8),
               'book green': ((52, 92, 60), 0.0, 0.8),
               'book blue': ((46, 62, 104), 0.0, 0.8),
               'book ochre': ((196, 146, 60), 0.0, 0.8),
               'book cream': ((220, 206, 176), 0.0, 0.8)}
#  The cabin's lights' looks and whether light plays on them: the
#  candles' flames and the fairy lights glow alone, the lamp's paper
#  shade is lit and glows.
LIGHT_LOOKS = {'flames': (((255, 186, 84), 0.0, 1.0), True),
               'flames round': (((132, 170, 255), 0.0, 1.0), True),
               'shade': (((246, 224, 182), 0.0, 0.9), False),
               'bulbs': (((255, 196, 112), 0.0, 1.0), True)}
#  The inputs' guards: red plastic, a little see-through.
GUARD_LOOK = ((226, 44, 32), 0.0, 0.25)
GUARD_SEEN = 0.38
#  The near camera's nearest cut, m: the chase view's, Asger's eyes'.
CHASE_NEAR, EYES_NEAR = 0.3, 0.02
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
    self._path, self._slots, self._paper = None, CABIN_SLOT, None
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
                navball: object, pictures: dict, pieces: tuple) -> bool:
    """The 'furnished' method puts in what is drawn all along: each body's
    sphere wearing its look ('files': each look's picture by name),
    Saturn's rings, the pad, the rocket, the map's bodies and each
    body's path ('orbits', 'Scenery.orbitsOf') and the vessel's, the
    artificial horizon (its picture, 'navball'), the cabin (its
    dashboard's pictures, '_dashpictures.picturesReady', and moving
    pieces, 'Scenery.cabinPieces', in their order) and Asger. Returns
    whether it could (the scene loaded)."""
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
    near.extend(self._cabinParts(navball, pictures, pieces))
    self._slots = CABIN_SLOT + len(pieces) + AFTER_PIECES
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
    root.setProperty('paperFont', FONT)
    root.setProperty('paperGeometry', self._kept1(Mesh(
      *_dashboard.paperRows())))
    root.setProperty('screenGeometry', self._kept1(Mesh(
      *_dashboard.screenRows())))
    self._files = files
    self.furnishedYet = True
    return True

  def flightShown(self, frame: dict, cabin: dict, system: SolarSystem,
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
    slots = self._slots
    places, turns = [None] * slots, [None] * slots
    shown, glows = [False] * slots, [0.0] * slots
    moving = [(PAD_SLOT, frame['pad'] + (0.0,)),
              (ROCKET_SLOT, frame['rocket'] + (0.0,))]
    moving += [(CABIN_SLOT + k, part) for k, part in enumerate(
      cabin['parts'])]
    for slot, (place, turn, seen, glow) in moving:
      places[slot], turns[slot] = QVector3D(*place), QQuaternion(*turn)
      shown[slot], glows[slot] = bool(seen), float(glow)
    root.setProperty('nearPlaces', places)
    root.setProperty('nearTurns', turns)
    root.setProperty('nearShown', shown)
    root.setProperty('nearGlows', glows)
    root.setProperty('cabinLight', QVector3D(*cabin['light']))
    root.setProperty('panelLamp', QVector3D(*cabin['lamp']))
    lamp, candles, flicker = cabin['hygge']
    root.setProperty('lampLight', QVector3D(*lamp))
    root.setProperty('candleLight', QVector3D(*candles))
    root.setProperty('candleGlow', float(flicker))
    at, way, up = cabin['flood']
    root.setProperty('floodPlace', QVector3D(*at))
    root.setProperty('floodTurn', nodeTurnOf(way, up))
    at, way, up = cabin['camera']
    root.setProperty('cctvPlace', QVector3D(at[0], at[2], -at[1]))
    root.setProperty('cctvTurn', sceneTurnOf(way, up))
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
    'mode', 'warp', 'toAp', 'ascent', 'phase', 'target', 'map', the
    cabin's 'gravity' (its words) and whether Asger is 'up' out of his
    chair, and the keys 'held' (their names)."""
    root = self._root()
    if root is None:
      return
    for name, key in (('throttle', 'boardThrottle'), ('mode', 'boardMode'),
                      ('warp', 'boardWarp'), ('toAp', 'boardToAp'),
                      ('ascent', 'boardAscent'), ('phase', 'boardPhase'),
                      ('target', 'boardTarget'), ('map', 'boardMap'),
                      ('gravity', 'boardGravity'), ('up', 'boardUp')):
      root.setProperty(key, board[name])
    root.setProperty('boardHeld', '|' + '|'.join(board['held']) + '|')

  def cockpitShown(self, inside: bool, prompt: tuple | None,
                   paper: tuple, stamp: str) -> None:
    """The 'cockpitShown' method shows the view from Asger's eyes
    ('inside': the overlays hidden, a dot in the middle, the cabin's
    nearest cut) or not; the input he looks at ('prompt': its key and
    what working it does, None: none); the teleprinter's paper ('paper':
    its lines printed and the line being typed, 'Teleprinter.paper');
    the closed circuit picture's time ('stamp')."""
    root = self._root()
    if root is None:
      return
    root.setProperty('cockpitOn', inside)
    root.setProperty('cctvStamp', stamp)
    root.setProperty('nearClip', EYES_NEAR if inside else CHASE_NEAR)
    root.setProperty('promptKey', prompt[0] if prompt else '')
    root.setProperty('promptName', prompt[1] if prompt else '')
    lines, typing = paper[0], paper[1]
    if (lines, typing) != self._paper:
      self._paper = lines, typing
      root.setProperty('paperLines', lines)
      root.setProperty('paperTyping', typing)

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

  def _cabinParts(self, navball: object, pictures: dict,
                  pieces: tuple) -> list:
    """Returns the cabin's parts as the scene takes them: its still ones
    on the rocket's slot, the dashboard's moving pieces on theirs, the
    ball, its marks and Asger after them."""
    kept, out = self._kept1, []
    looks = CABIN_LOOKS
    face, dials = pictures['face'], pictures['dials']
    labels, cells = pictures['labels'], pictures['cells']
    cabin = cabinPicturesReady()
    still = (('pine', _cabin.innerWall(), cabin['pine']),
             ('boards', _cabin.floorRows(), cabin['boards']),
             ('seat', _cabin.seatRows(), ''),
             ('chrome', _cabin.chairFrame(), ''),
             ('rosewood', _cabin.consoleRows(), ''),
             ('aluminium', _cabin.consoleTops(), ''),
             ('rosewood', _dashboard.panelFrame(), ''),
             ('picture', _dashboard.panelFace(), face),
             ('chrome', _dashboard.bezels(), ''),
             ('chrome', _dashboard.paperFrame(), ''),
             ('wood', _dashboard.monitorBody(), pictures['wood']),
             ('black', _dashboard.monitorInset(), ''),
             ('black', _dashboard.sliderTrack(), ''),
             ('aluminium', _dashboard.consoleBases(), ''),
             ('rosewood', _dashboard.sideboardRows(), ''),
             ('aluminium', _dashboard.sideboardTop(), ''),
             ('chrome', _dashboard.globeStand(), ''))
    for name, rows, picture in still:
      out.append(_partOf(kept(Mesh(*rows)), looks[name], ROCKET_SLOT,
                         False, picture))
    for name, rows in furnishings().items():
      out.append(_partOf(kept(Mesh(*rows)), HYGGE_LOOKS[name], ROCKET_SLOT,
                         False, cabin[name] if name in cabin else ''))
    for material, rows in _deckmodel.stillParts():
      look, picture, opacity = self._deckLook(material)
      out.append(_partOf(kept(Mesh(*rows)), look, ROCKET_SLOT, False,
                         picture, False, opacity))
    out.append(_partOf(kept(Mesh(*_dashboard.dialFaces())),
                       looks['picture'], ROCKET_SLOT, False, dials, True))
    out.append(_partOf(kept(Mesh(*_dashboard.domeRows())), looks['dome'],
                       ROCKET_SLOT, False, pictures['glass'], False,
                       SEE_THROUGH))
    out.append(_partOf(kept(Mesh(*_cabin.glassRows())), (WINDOW_GLASS[0],
                                                          0.0, 0.1),
                       ROCKET_SLOT, False, '', True, WINDOW_GLASS[1]))
    for k, piece in enumerate(pieces):
      rows = _dashboard.pieceRows(piece, cells)
      if piece[0] in ('glint', 'glint lid'):
        name, scroll = GLINT_LOOKS[piece[1].action]
        out.append(_partOf(kept(Mesh(*rows)), ((255, 255, 255), 0.0, 1.0),
                           CABIN_SLOT + k, False, cabin[name], True,
                           SEE_THROUGH, False, None, True, scroll))
        continue
      look, picture, unlit, emit, opacity = self._pieceLook(piece, labels)
      out.append(_partOf(kept(Mesh(*rows)), look, CABIN_SLOT + k, False,
                         picture, unlit, opacity, False, emit))
    slot = CABIN_SLOT + len(pieces)
    rows, indices = sphereRows(*NAV_SPHERE)
    rows = mirroredRows(rows)
    rows[:, :3] *= BALL_RADIUS
    out.append(_partOf(kept(Mesh(rows, indices)), BALL_LOOK, slot, False,
                       navball, False))
    makers = (_dashboard.ringParts, _dashboard.axleParts,
              _dashboard.hubParts)
    for k, (maker, name) in enumerate(zip(makers, MECHANISM_LOOKS)):
      out.append(_partOf(kept(Mesh(*maker())), looks[name], slot + 1 + k,
                         False))
    marks = slot + 1 + len(MECHANISM)
    for k, kind in enumerate(MARK_KINDS):
      rows = _dashboard.decalRows(MARK_NAMES.index(kind), len(MARK_NAMES))
      out.append(_partOf(kept(Mesh(*rows)), ((255, 255, 255), 0.0, 0.4),
                         marks + k, False, pictures['marks'], False,
                         SEE_THROUGH))
    first = marks + len(MARK_KINDS)
    for k, part in enumerate(PARTS):
      for outer in (False, True):
        out.append(_partOf(kept(Mesh(*partRows(part, outer, SCALE))),
                           ((255, 255, 255), 0.0, 0.9), first + k, False,
                           ASGERJON, False, 1.0, outer))
    return out

  def _pieceLook(self, piece: tuple, labels: object) -> tuple:
    """Returns a moving piece's look, picture ('' none), whether light
    plays on it not (backlit), the colour it glows lit (None: its own)
    and how opaque it is: a lamp and a legend dark glass unlit, their
    light their own; the tape deck's parts their model's."""
    looks = CABIN_LOOKS
    kind, what = piece
    if kind == 'control':
      peep = what.peep
      if isinstance(peep, Pushbutton):
        return looks['picture'], labels, False, None, 1.0
      if isinstance(peep, (Knob, Slider)):
        return looks['aluminium'], '', False, None, 1.0
      return looks['chrome'], '', False, None, 1.0
    if kind == 'needle':
      return looks['needle'], '', False, None, 1.0
    if kind == 'guard':
      return GUARD_LOOK, '', False, None, GUARD_SEEN
    if kind in LIGHT_LOOKS:
      look, unlit = LIGHT_LOOKS[kind]
      return look, '', unlit, None, 1.0
    if kind == 'lamp':
      colour = _dashboard.LAMP_COLOURS[LAMPS[what][0]]
      dark = tuple(int(UNLIT * c) for c in colour)
      return (dark, 0.0, 0.3), '', False, colour, 1.0
    if kind == 'legend':
      return looks['smoke glass'], labels, False, (255, 255, 255), 1.0
    if kind == 'deck':
      look, picture, opacity = self._deckLook(_deckmodel.movingParts()[
        what][2])
      return look, picture, False, None, opacity
    if kind == 'bug':
      return (BUG_COLOUR, 0.0, 1.0), '', True, None, 1.0
    if kind == 'loose':
      return HYGGE_LOOKS[looseParts()[what][1]], '', False, None, 1.0
    return looks['black'], '', False, None, 1.0

  def _deckLook(self, material: int | None) -> tuple:
    """Returns a tape deck material's look, picture ('' none) and how
    opaque it is."""
    colour, metal, rough, opacity, pictured = _deckmodel.lookOf(material)
    picture = _deckmodel.pictureFile() if pictured else ''
    return (colour, metal, rough), picture, opacity

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


def _partOf(geometry: object, look: tuple, slot: int, culled: bool,
            picture: str = '', unlit: bool = False, opacity: float = 1.0,
            masked: bool = False, emit: tuple = None, screen: bool = False,
            scroll: float = 0.0) -> dict:
  """Returns a near part as the scene takes it: its mesh, its look
  (colour, metalness, roughness), its slot, whether its back faces are
  culled; its picture (a file, '' none), whether light plays on it
  (unlit: a screen's, a mark's), how see-through it is, whether its
  picture's clear pixels are holes (a skin's outer layer), the colour
  it glows (None: its own), whether it is laid as a screen (only adding
  light: a glint) and how fast its picture slides across it."""
  rgb, metal, rough = look
  glows = rgb if emit is None else emit
  return {'geometry': geometry, 'colour': QColor(*rgb),
          'emit': QColor(*glows), 'screen': screen, 'scroll': scroll,
          'metal': metal,
          'rough': rough, 'slot': slot, 'culled': culled,
          'picture': QUrl.fromLocalFile(str(picture)).toString()
          if picture else '', 'unlit': unlit, 'opacity': opacity,
          'masked': masked}


def _across(way: tuple) -> tuple:
  """Returns a unit vector across 'way' (an up for a light)."""
  other = (0.0, 0.0, 1.0) if abs(way[2]) < 0.9 else (1.0, 0.0, 0.0)
  cross = (way[1] * other[2] - way[2] * other[1],
           way[2] * other[0] - way[0] * other[2],
           way[0] * other[1] - way[1] * other[0])
  size = math.sqrt(sum(x * x for x in cross))
  return tuple(x / size for x in cross)


def nodeTurnOf(forward: tuple, up: tuple) -> QQuaternion:
  """Returns the turn, in a layer's world node (the ecliptic's own
  axes), that points a light (shining along its own -z, its y up) along
  'forward', kept upright toward 'up'."""
  size = math.sqrt(sum(x * x for x in forward))
  back = tuple(-x / size for x in forward)
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
