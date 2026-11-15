"""
GpuView shows the lab's bodies in 3D drawn by the GPU: Qt Quick 3D,
from 'phys.qml', in a 'QQuickView' of its own (rendered in its own
thread, set in through a window container, as the coin pusher's), with
a depth buffer, smooth shading and the sun's shadows; the painter's
'PhysView' draws the same without a GPU. 'Mesh' hands Qt Quick 3D a
mesh made in Python.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import tempfile
import time
from pathlib import Path

import numpy
from PySide6.QtCore import QByteArray, QEvent, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QQuaternion
from PySide6.QtGui import QVector3D
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView, QSGRendererInterface
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtWidgets import QWidget

from .._vectors import cross, minus, norm, rotated, scaled
from ._meshes import AXES, SCALE, bodyRows, finishedRows, groundMesh
from ._souffle import badgePicture, leatherPicture, sidewallPicture
from ._meshes import pieceRows
from ._meshes import quadIndices, stripedRows
from ._meshes import quadRows, sceneOf, sceneTurnOf, terrainMesh
from ._meshes import ovalTrackMesh, wallMesh
from ._wheel import MouseHands

_SEMANTIC = QQuick3DGeometry.Attribute.Semantic
_FLOAT = QQuick3DGeometry.Attribute.ComponentType.F32Type
_INDEX = QQuick3DGeometry.Attribute.ComponentType.U32Type
_TRIANGLES = QQuick3DGeometry.PrimitiveType.Triangles
#  The scene, beside this file.
_SCENE = Path(__file__).with_name('phys.qml')
#  Toward the sun and toward the sky's light, in the world (the
#  painter's light, and one from the other side, higher).
_SUN = (0.35, -0.5, 0.8)
_SKY = (-0.4, 0.45, 0.9)
#  How glossy a body of glass is (its roughness).
_GLASS_ROUGH = 0.04
#  How a body looks unless told: its colour, metalness and roughness;
#  how a tyre's rubber looks.
_PLAIN = (QColor(205, 165, 110), 0.1, 0.6)
_RUBBER = (0.0, 0.85)
#  How far the flat ground about a terrain reaches, m.
_FLAT_REACH = 2000.0
#  How big a finish's picture lies on a body, m a side (at full size),
#  and the pictures' form (a picture made by another is made anew).
_FINISH_TILE = 0.04
_FINISH_FORM = 1


class Mesh(QQuick3DGeometry):
  """
  Mesh subclasses 'QQuick3DGeometry' and hands Qt Quick 3D triangles: a
  row of six numbers a corner (place, normal), or, with 'indices',
  vertices of eight (place, normal, the checker's coordinates) and the
  triangles' corners by index. It is made in Python, with no parent;
  whoever made it keeps it alive.
  """

  def __init__(self, rows: numpy.ndarray,
               indices: numpy.ndarray = None) -> None:
    QQuick3DGeometry.__init__(self, )
    rows = numpy.ascontiguousarray(rows, numpy.float32)
    width = rows.shape[1]
    self.setStride(4 * width)
    self.setPrimitiveType(_TRIANGLES)
    self.addAttribute(_SEMANTIC.PositionSemantic, 0, _FLOAT)
    self.addAttribute(_SEMANTIC.NormalSemantic, 12, _FLOAT)
    if width == 8:
      self.addAttribute(_SEMANTIC.TexCoord0Semantic, 24, _FLOAT)
    if indices is not None:
      self.addAttribute(_SEMANTIC.IndexSemantic, 0, _INDEX)
      self.setIndexData(QByteArray(numpy.ascontiguousarray(
        indices, numpy.uint32).tobytes()))
    self.refill(rows)

  def reindex(self, indices: numpy.ndarray) -> None:
    """The 'reindex' method gives the mesh new indices (as many triangles
    as its next rows ask), drawn from the next frame."""
    self.setIndexData(QByteArray(numpy.ascontiguousarray(
      indices, numpy.uint32).tobytes()))

  def refill(self, rows: numpy.ndarray, bounds: tuple = None) -> None:
    """The 'refill' method gives the mesh new rows (as many numbers a row
    as it was made with, as many as its indices ask), drawn from the
    next frame, within 'bounds' (the least and the most corner) or, with
    none, the rows' own."""
    rows = numpy.ascontiguousarray(rows, numpy.float32)
    self.setVertexData(QByteArray(rows.tobytes()))
    if bounds is not None:
      low, high = bounds
    elif len(rows):
      low, high = rows[:, :3].min(0), rows[:, :3].max(0)
    else:
      low = high = numpy.zeros(3, numpy.float32)
    self.setBounds(QVector3D(*(float(x) for x in low)),
                   QVector3D(*(float(x) for x in high)))
    self.update()


class GpuView(QWidget):
  """
  GpuView shows 'assembly' in 'states' ('show_') in 3D, drawn by the
  GPU: each body as its shape (in its tone in 'tones', index: colour,
  and its look in 'looks', index: (metalness, roughness); or as tinted
  glass, a body in 'glass' (index: its colour, less than opaque: seen
  through, glossy, casting no shadow); or in its finish, a body in
  'finishes' (index: a key, or a turned solid's runs, as 'finishedRows'
  takes them), each key looking as 'palette' has it (colour, metalness,
  roughness, casts shadows, and a picture over it, its name in
  '_finishFile', or None: the colour times its grey); a turned solid
  in 'bands', index: (radius, colour), in rubber from that radius out),
  or, for a body in 'pieces' (index: its pieces, each a solid in its
  own frame and a key in 'palette': (colour, metalness, roughness)),
  piece by piece (one mesh for all a body's pieces of a key); what each
  of 'dresses' draws as it is now (its 'quads(states)', by key in
  'palette', (colour, metalness, roughness[, casts shadows]): a colour
  less than opaque blends), all within 'around' m of the first body
  where a dress says so; the ground (a 'terrain', or flat; none at
  all in the 'void'), dirt
  ('_dirtFiles': its colours and its bumps), a picture to two of
  'tiles["ground"]'. The bodies in 'hidden' are not drawn; a tone
  changed is drawn from the next frame, the part only recoloured; a
  dress's keys, all there from its first frame, are its meshes for
  good (a mesh made later has the scene make every dressed part
  anew). The whole is drawn 'magnify'
  times as big as it is (a world shrunk for a walker at their size: the
  camera's near cut, 'near' m in the world, the shadows and the
  ground's pictures then work as at full size). The
  camera looks at 'target' (m) from 'distance' m, 'yaw' and 'pitch' rad
  as 'PhysView''s (riding in a car, 'riding' its turn: yaw and pitch
  then the car's own, the horizon going round with it; None: the
  world's); 'follow' puts it behind a car, a right drag swings
  it 'around' the car and up or down, the mouse wheel brings it nearer;
  a left click takes the mouse to steer with ('hands', 'MouseHands');
  the keys held are in 'keys'. With 'crosshair' a cross shows in the
  middle, with a 'hint' a line of help along the bottom. While
  'recorder' is set (a 'Recorder') each frame shown is handed to it,
  with what it was drawn from ('drawnNow'). The scene loads once shown
  ('loaded', 'sceneLoaded'); its first frame drawn, 'drawn' and
  'firstDrawn'; 'problems' the errors met loading it, none when all is
  well.
  """

  sceneLoaded = Signal()
  firstDrawn = Signal()

  def __init__(self, ) -> None:
    QWidget.__init__(self)
    self.quick = QQuickView()
    self.quick.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    self.quick.setColor(QColor(86, 101, 122))
    self.quick.frameSwapped.connect(self._swapped)
    self.quick.installEventFilter(self)
    self.box = QWidget.createWindowContainer(self.quick, self)
    self.box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.component, self.problems = None, ()
    self.loaded, self.drawn, self.asked = False, False, None
    self.assembly, self.states, self.pushed = None, (), None
    self.tones, self.looks, self.bands = {}, {}, {}
    self.glass, self.finishes = {}, {}
    self.pieces, self.palette, self.dresses = {}, {}, []
    self.terrain, self.tiles, self.dressed = None, {}, {}
    self.riding = None
    self.void = False
    self.wall, self.oval = None, False
    self.yaw, self.pitch, self.distance = 0.6, 0.28, 6.5
    self.target = (0.0, 0.0, 0.4)
    self.keys, self.around, self.heading = set(), 0.0, None
    self.grabbed, self.meshes = None, {}
    self.rows, self.kept = {}, []
    self.hidden, self.magnify, self.near = set(), 1.0, 0.05
    self.crosshair, self.hint, self.recorder = False, '', None
    self.pushedTones, self.partColours, self.stripes = None, [], {}
    self.hands = MouseHands(self.quick)
    self.setMinimumSize(800, 600)
    application = QGuiApplication.instance()
    application.focusWindowChanged.connect(self._focusMoved)
    application.applicationStateChanged.connect(self._stateMoved)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: object) -> None:
    """Shown the first time, the view starts loading its scene."""
    if self.component is None:
      self.load()
    QWidget.showEvent(self, event)

  def resizeEvent(self, event: object) -> None:
    """The scene's container fills the view."""
    QWidget.resizeEvent(self, event)
    self.box.setGeometry(self.rect())

  def sizeHint(self, ) -> QSize:
    return QSize(1280, 760)

  def eventFilter(self, watched: object, event: object) -> bool:
    """Reads the keys and the mouse from the scene's window (it, not the
    view, has them): keys held into 'keys'; a left click takes the mouse
    to steer with ('hands'; Esc lets it go); a right drag swings the
    camera round the car and up or down; the wheel brings it nearer;
    losing the focus lets every key and the mouse go."""
    if watched is not self.quick:
      return False
    kind = event.type()
    if kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
      self.hands.letGo()
    elif kind == QEvent.Type.KeyPress and not event.isAutoRepeat():
      self.keys.add(event.key())
    elif kind == QEvent.Type.KeyRelease and not event.isAutoRepeat():
      self.keys.discard(event.key())
    elif kind == QEvent.Type.MouseButtonPress:
      if self.hands.taken:
        return True
      if event.button() == Qt.MouseButton.LeftButton:
        self.hands.take()
        return True
      self.grabbed = event.position()
    elif kind == QEvent.Type.MouseMove and self.hands.taken:
      self.hands.movedTo(event.globalPosition(), event.position())
    elif kind == QEvent.Type.MouseMove and self.grabbed is not None:
      moved = event.position() - self.grabbed
      self.grabbed = event.position()
      self.around -= 0.01 * moved.x()
      self.pitch = min(1.4, max(0.02, self.pitch + 0.01 * moved.y()))
    elif kind == QEvent.Type.MouseButtonRelease:
      self.grabbed = None
    elif kind == QEvent.Type.Wheel:
      self.distance *= 0.9 if event.angleDelta().y() > 0 else 1.1
    elif kind == QEvent.Type.FocusOut:
      self.keys.clear()
      self.hands.letGo()
    elif kind == QEvent.Type.Leave:
      self.hands.forget()
    return False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def load(self, ) -> None:
    """The 'load' method starts loading the scene; once it is in,
    'sceneLoaded' is emitted and 'loaded' is True (or 'problems' says
    why not).

    The scene is first compiled asynchronously. The 'App' has 'notify'
    in Python, so every event, on any thread, wants Python's lock; a
    'setSource' straight away would hold that lock waiting for QML's
    loading thread, which waits for the lock: a deadlock. Compiled, the
    scene is cached and 'setSource' does not wait."""
    self.asked = time.perf_counter()
    url = QUrl.fromLocalFile(str(_SCENE))
    mode = QQmlComponent.CompilationMode.Asynchronous
    self.component = QQmlComponent(self.quick.engine(), url, mode, self)
    if self.component.isLoading():
      self.component.statusChanged.connect(self._compiled)
    else:
      self._compiled()

  def show_(self, assembly: object, states: tuple, settle: float) -> None:
    """The 'show_' method shows 'assembly' in 'states' ('settle' as
    'PhysView''s, unused: nothing is drawn asleep here)."""
    self.assembly, self.states = assembly, states
    if not self.loaded:
      return
    if self.pushed is not assembly:
      self._pushShapes()
    elif self._tonesNow() != self.pushedTones:
      self._pushColours(self.quick.rootObject())
    self._pushFrame()
    if self.recorder is not None and self.drawn:
      self.recorder.add(self.quick.grabWindow(), time.perf_counter(),
                        self.drawnNow())

  def follow(self, place: tuple, heading: float, seconds: float) -> None:
    """The 'follow' method puts the camera behind the car at 'place'
    heading 'heading' (rad), swinging round after it as it turns over
    'seconds' (as 'CarView''s)."""
    if self.heading is None:
      self.heading = heading
    turn = (heading - self.heading + math.pi) % (2.0 * math.pi) - math.pi
    self.heading += turn * min(1.0, 3.0 * seconds)
    self.yaw = self.heading + math.pi + self.around
    self.target = (place[0], place[1], place[2] + 0.4)

  def regrounded(self, ) -> None:
    """The 'regrounded' method has the ground drawn anew ('terrain' or
    'tiles' changed)."""
    self.pushed = None

  def drawnNow(self, ) -> dict:
    """The 'drawnNow' method returns what the view draws from now, as
    plain numbers: the camera, how big the world is drawn, the view's
    size, which bodies are hidden and tinted, and every body's place and
    turn."""
    return {'yaw': self.yaw, 'pitch': self.pitch,
            'distance': self.distance, 'target': list(self.target),
            'magnify': self.magnify, 'width': self.width(),
            'height': self.height(), 'hidden': sorted(self.hidden),
            'tones': {str(index): QColor(tone).name()
                      for index, tone in self.tones.items()},
            'bodies': [[list(state.place), list(state.turn)]
                       for state in self.states]}

  def loadingFor(self, ) -> float:
    """The 'loadingFor' method returns how long the scene has been
    loading, s (nought before it was asked for)."""
    return 0.0 if self.asked is None else time.perf_counter() - self.asked

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _compiled(self, *_) -> None:
    """Once the scene is compiled, sets it as the view's source and
    hands it what it shows; or notes why it would not compile."""
    component = self.component
    if component is None or component.isLoading():
      return
    if component.isError():
      self.problems = tuple(error.toString()
                            for error in component.errors())
      self.sceneLoaded.emit()
      return
    self.quick.setSource(component.url())
    self.problems = tuple(error.toString() for error in self.quick.errors())
    self.loaded = self.quick.rootObject() is not None
    root = self.quick.rootObject()
    if root is not None:
      root.setProperty('sunTurn', _lightTurn(_SUN))
      root.setProperty('skyTurn', _lightTurn(_SKY))
      colours, bumps = _dirtFiles()
      root.setProperty('groundMap', QUrl.fromLocalFile(colours))
      root.setProperty('groundBumps', QUrl.fromLocalFile(bumps))
      colours, bumps = _concreteFiles()
      root.setProperty('pavedMap', QUrl.fromLocalFile(colours))
      root.setProperty('pavedBumps', QUrl.fromLocalFile(bumps))
      colours, bumps = _asphaltFiles()
      root.setProperty('asphaltMap', QUrl.fromLocalFile(colours))
      root.setProperty('asphaltBumps', QUrl.fromLocalFile(bumps))
    if self.assembly is not None:
      self.show_(self.assembly, self.states, 0.0)
    self.sceneLoaded.emit()

  def _swapped(self, ) -> None:
    """Notes the scene's first frame drawn; drawn without a 3D graphics
    API (Qt Quick's software drawing: Qt Quick 3D then shows nothing),
    notes that as a problem."""
    if not self.drawn and self.loaded:
      self.drawn = True
      api = self.quick.rendererInterface().graphicsApi()
      if not QSGRendererInterface.isApiRhiBased(api):
        self.problems = ('no 3D graphics API here (Qt Quick draws with '
                         '%s), so Qt Quick 3D shows nothing' % api.name,)
      self.firstDrawn.emit()

  def _focusMoved(self, window: object) -> None:
    """Lets every key and the mouse go when the focus goes to another
    window than the scene's (another program's, or none: the scene's own
    'FocusOut' does not always come, and a key let go elsewhere never
    comes back up here, so the walker walked on: user, 2026-11-13,
    "the window needs to let go of the keyboard when it loses
    focus")."""
    if window is not self.quick:
      self.focusLost()

  def _stateMoved(self, state: object) -> None:
    """Lets every key and the mouse go when the program is no longer
    the one in front ('_focusMoved')."""
    if state != Qt.ApplicationState.ApplicationActive:
      self.focusLost()

  def focusLost(self, ) -> None:
    """The 'focusLost' method lets every key held and the mouse go."""
    self.keys.clear()
    self.hands.letGo()

  def _freshOf(self, key: object, made: object) -> Mesh | None:
    """Returns a mesh made anew from the rows kept under 'key' (worked
    out the first time by 'made': rows, and indices or None; no rows, no
    mesh): a scene's part or dress is never handed a mesh a part had
    before (rebuilt, Qt Quick 3D's teardown of the old models let go of
    the geometry they shared with the new: everything vanished and the
    sun's shadows striped the ground, user, 2026-11-13, giving a wheel).
    Every mesh made is kept as long as the view."""
    if key not in self.rows:
      self.rows[key] = made()
    rows, indices = self.rows[key]
    if not len(rows):
      return None
    mesh = Mesh(rows, indices)
    self.kept.append(mesh)
    return mesh

  def _meshOf(self, key: object, made: object) -> Mesh | None:
    """Returns the mesh kept under 'key', making it the first time from
    what 'made' returns (rows, and indices or None; no rows, no mesh).
    Every mesh is kept as long as the view (the scene's render thread may
    draw one still after it is no longer shown)."""
    if key not in self.meshes:
      rows, indices = made()
      self.meshes[key] = Mesh(rows, indices) if len(rows) else None
    return self.meshes[key]

  def _pushShapes(self, ) -> None:
    """Hands the scene the bodies' meshes ('_pushParts') and the ground;
    the dress's meshes are made anew."""
    root = self.quick.rootObject()
    self._pushParts(root)
    self.dressed = {}
    root.setProperty('dressed', [])
    self._pushGround(root)
    self.pushed = self.assembly

  def _tonesNow(self, ) -> tuple:
    """Returns the tones as they are, to tell when they change."""
    return tuple(sorted((index, QColor(tone).rgba())
                        for index, tone in self.tones.items()))

  def _pushColours(self, root: object) -> None:
    """Hands the scene each part's colour now: a body's own parts in its
    tone, others (pieces, rubber) as they were made. The parts are not
    made anew (that lost them all, a frame after)."""
    root.setProperty('colours', [
      QColor(self.tones.get(body, _PLAIN[0])) if fixed is None else fixed
      for body, fixed in self.partColours])
    self.pushedTones = self._tonesNow()

  def _pushParts(self, root: object) -> None:
    """Hands the scene the bodies' meshes, each body's made once (bodies
    sharing a body share them), in their tones; the hidden left out."""
    parts = []
    for index, body in enumerate(self.assembly.bodies):
      if body.shape is None or index in self.hidden:
        continue
      if index in self.finishes:
        parts += self._finishedParts(index, body)
        continue
      if index in self.pieces:
        pieces = self.pieces[index]
        for key in dict.fromkeys(key for _, key in pieces):
          colour, metal, rough = self.palette.get(key, _PLAIN)
          parts.append({'geometry': self._freshOf(
            ('pieces', id(pieces), key, body), lambda: (numpy.concatenate(
              [pieceRows(piece, body.centre) for piece, its in pieces
               if its == key]), None)), 'body': index,
            'colour': QColor(colour), 'metal': metal, 'rough': rough,
            'casts': True})
        continue
      band = self.bands.get(index)
      rho = None if band is None else band[0]
      inside, outside = self._bodyMeshes(body, rho)
      if index in self.stripes:
        paint, stripes, pitch = self.stripes[index]
        inside, outside = self._stripedMeshes(body, stripes, pitch)
        band = (None, paint)
      colour = self.tones.get(index, _PLAIN[0])
      metal, rough = self.looks.get(index, _PLAIN[1:])
      glass = self.glass.get(index)
      if inside is not None and glass is not None:
        parts.append({'geometry': inside, 'body': index,
                      'colour': QColor(glass), 'metal': 0.0,
                      'rough': _GLASS_ROUGH, 'casts': False})
      elif inside is not None:
        parts.append({'geometry': inside, 'body': index,
                      'colour': QColor(colour), 'metal': metal,
                      'rough': rough, 'toned': True, 'casts': True})
      if outside is not None:
        parts.append({'geometry': outside, 'body': index,
                      'colour': QColor(band[1]), 'metal': _RUBBER[0],
                      'rough': _RUBBER[1], 'casts': True})
    self.partColours = [
      (part['body'], None if part.get('toned') else part['colour'])
      for part in parts]
    for part in parts:
      part.pop('toned', None)
    root.setProperty('colours', [])
    root.setProperty('parts', parts)
    self._pushColours(root)

  def _finishedParts(self, index: int, body: object) -> list[dict]:
    """Returns the parts of the body at 'index' drawn in its finish
    ('finishes'): a mesh a key (its rows worked out once for each body
    and finish alike, the mesh made anew: '_freshOf'), each in its key's
    look ('palette'), its picture over it where its rows map one."""
    finish = self.finishes[index]
    try:
      hash(finish)
      name = ('finish', body, finish)
    except TypeError:
      name = ('finish', body, id(finish))
    if name not in self.rows:
      self.rows[name] = finishedRows(body, finish, _FINISH_TILE)
    parts = []
    for key, rows in self.rows[name].items():
      mesh = self._freshOf((name, key), lambda: (rows, None))
      if mesh is None:
        continue
      look = self.palette.get(key, _PLAIN)
      picture = look[4] if len(look) > 4 else None
      mapped = picture is not None and not isinstance(finish, str)
      parts.append({'geometry': mesh, 'body': index,
                    'colour': QColor(look[0]), 'metal': look[1],
                    'rough': look[2],
                    'casts': look[3] if len(look) > 3 else True,
                    'map': QUrl.fromLocalFile(_finishFile(
                      picture)).toString() if mapped else ''})
    return parts

  def _stripedMeshes(self, body: object, stripes: int,
                     pitch: float) -> tuple:
    """Returns the meshes of a turned 'body' painted with spiral stripes
    ('stripedRows'): the rest and the stripes, made once for each body
    alike (made anew: '_freshOf')."""
    key = ('striped', body, stripes, pitch)
    if key not in self.rows:
      self.rows[key] = stripedRows(body, stripes, pitch)
    return tuple(self._freshOf((key, k), lambda: (rows, None))
                 for k, rows in enumerate(self.rows[key]))

  def _bodyMeshes(self, body: object, rho: float | None) -> tuple:
    """Returns the meshes of 'body' (inside 'rho' and out: its steel and
    its rubber), their rows worked out once for each body alike, the
    meshes made anew ('_freshOf')."""
    key = ('body', body, rho)
    if key not in self.rows:
      self.rows[key] = bodyRows(body, rho)
    return tuple(self._freshOf((key, k), lambda: (rows, None))
                 for k, rows in enumerate(self.rows[key]))

  def _pushGround(self, root: object) -> None:
    """Hands the scene the ground: the terrain's shape and the flat
    ground about it, or the flat ground alone."""
    tile = self.tiles.get('ground', 2.0)
    terrain = self.terrain
    shape, paved, asphalt, hole = None, None, None, None
    track = None
    if terrain is not None and self.oval:
      key = ('oval', id(terrain.heights), tile)
      if key not in self.meshes:
        vertices, ground, road, apron, covered = ovalTrackMesh(terrain,
                                                               tile)
        rows = terrainMesh(terrain._replace(paved=None), tile, covered)
        self.meshes[key] = (Mesh(rows[0], rows[1]),) + tuple(
          Mesh(vertices, indices) for indices in (ground, road, apron))
      shape, track, paved, asphalt = self.meshes[key]
    elif terrain is not None:
      key = ('terrain', id(terrain.heights), tile)
      if key not in self.meshes:
        vertices, ground, road, apron = terrainMesh(terrain, tile)
        self.meshes[key] = tuple(
          Mesh(vertices, indices) if len(indices) else None
          for indices in (ground, road, apron))
      shape, paved, asphalt = self.meshes[key]
    if terrain is not None:
      (x0, y0), cell = terrain.origin, terrain.cell
      hole = (x0, y0, x0 + cell * (len(terrain.heights) - 1),
              y0 + cell * (len(terrain.heights[0]) - 1))
    reach = _FLAT_REACH / self.magnify
    flat = self._meshOf(('flat', hole, tile, reach),
                        lambda: groundMesh(hole, reach, tile))
    root.setProperty('terrainShape', shape)
    root.setProperty('pavedShape', paved)
    root.setProperty('asphaltShape', asphalt)
    root.setProperty('trackGroundShape', track)
    barrier, stripe = None, None
    if terrain is not None and self.wall is not None:
      key = ('wall', id(terrain.heights), self.wall)
      if key not in self.meshes:
        rows, white, blue = wallMesh(terrain, self.wall)
        self.meshes[key] = (Mesh(rows, white), Mesh(rows, blue))
      barrier, stripe = self.meshes[key]
    root.setProperty('wallShape', barrier)
    root.setProperty('stripeShape', stripe)
    root.setProperty('flatShape', None if self.void else flat)

  def _pushFrame(self, ) -> None:
    """Hands the scene where each body is and how it is turned, the rods
    and coils, and the camera."""
    root = self.quick.rootObject()
    states = self.states
    root.setProperty('places', [QVector3D(*sceneOf(state.place))
                                for state in states])
    root.setProperty('turns', [QQuaternion(*sceneTurnOf(state.turn))
                               for state in states])
    if self.dresses:
      self._pushDresses(root)
    eye, right, up, forward = _cameraOf(self.target, self.yaw, self.pitch,
                                        self.distance)
    if self.riding is not None:
      right, up, forward = (rotated(self.riding, axis)
                            for axis in (right, up, forward))
      eye = minus(self.target, scaled(forward, self.distance))
    root.setProperty('magnify', self.magnify)
    root.setProperty('cameraNear', SCALE * self.near * self.magnify)
    root.setProperty('crosshair', self.crosshair)
    root.setProperty('hint', self.hint)
    root.setProperty('cameraPlace', QVector3D(*(
      self.magnify * x for x in sceneOf(eye))))
    root.setProperty('cameraTurn', _turnOfAxes(right, up,
                                               scaled(forward, -1.0)))

  def _pushDresses(self, root: object) -> None:
    """Hands the scene what the dresses draw now, a mesh for each key of
    each (its quads' corners, two triangles a quad by index), made the
    first time and refilled after (not at all while a dress hands the
    same quads), within 'around' of the first body for a dress that
    says so (no reckoning of each part's box), else their own box."""
    middle = numpy.array(sceneOf(self.states[0].place), numpy.float32)
    made = False
    for dress in self.dresses:
      around = getattr(dress, 'around', None)
      bounds = None if around is None else (middle - 100.0 * around,
                                            middle + 100.0 * around)
      for key, quads in dress.quads(self.states).items():
        name = (id(dress), key)
        if name in self.dressed and self.dressed[name][1] is quads:
          continue
        rows = quadRows(quads)
        if name not in self.dressed:
          mesh = Mesh(rows, quadIndices(len(quads)))
          self.kept.append(mesh)
          mesh.reindex(quadIndices(len(quads)))
          made = True
        else:
          mesh = self.dressed[name][0]
          if self.dressed[name][2] != len(quads):
            mesh.reindex(quadIndices(len(quads)))
        mesh.refill(rows, bounds)
        self.dressed[name] = (mesh, quads, len(quads), key)
    if made:
      dressed = []
      for mesh, _, _, key in self.dressed.values():
        look = self.palette.get(key, _PLAIN)
        dressed.append({'geometry': mesh, 'colour': QColor(look[0]),
                        'metal': look[1], 'rough': look[2],
                        'casts': look[3] if len(look) > 3 else True})
      root.setProperty('dressed', dressed)


def _cameraOf(target: tuple, yaw: float, pitch: float,
              distance: float) -> tuple:
  """Returns the eye and its right, up and forward (the world's), as
  'PhysView.camera' works them out."""
  forward = (-math.cos(pitch) * math.cos(yaw),
             -math.cos(pitch) * math.sin(yaw), -math.sin(pitch))
  eye = minus(target, scaled(forward, distance))
  right = cross(forward, (0.0, 0.0, 1.0))
  right = scaled(right, 1.0 / norm(right))
  return eye, right, cross(right, forward), forward


def _turnOfAxes(x: tuple, y: tuple, z: tuple) -> QQuaternion:
  """Returns the scene's turn of a frame whose own axes are the world's
  'x', 'y' and 'z' (units, square to each other, right handed)."""
  axes = [AXES @ numpy.array(axis) for axis in (x, y, z)]
  return QQuaternion.fromAxes(*(QVector3D(*(float(v) for v in axis))
                                for axis in axes))


def _lightTurn(toward: tuple) -> QQuaternion:
  """Returns the turn of a light shining from the world's 'toward' (its
  own -z along the light: its own z toward it)."""
  z = scaled(toward, 1.0 / norm(toward))
  x = cross((0.0, 0.0, 1.0), z)
  x = scaled(x, 1.0 / norm(x))
  return _turnOfAxes(x, cross(z, x), z)


def _dirtFiles() -> tuple[str, str]:
  """Returns the dirt's pictures, written to the temp folder once: its
  colours and its bumps (a normal map), seamless (the ground's mesh maps
  two tiles to one picture). Its height is noise of every size, the
  large stronger (made periodic by the Fourier transform: random phases,
  an amplitude falling as the size's 1.7th power), a little grit on top;
  the colour dry earth, darker in the hollows, a speckle of small stones;
  the bumps the height's slope."""
  return _groundFiles('dirt', 20261112, 1.7, ((86.0, 66.0, 46.0),
                                              (156.0, 126.0, 92.0)),
                      ((0.25, 0.6, 0.15), 0.985, (170.0, 160.0, 145.0)),
                      (6.0, 0.4, 1.5))


def _concreteFiles() -> tuple[str, str]:
  """Returns the concrete's pictures as '_dirtFiles' the dirt's: a pale
  grey, finer and flatter, a few darker pits of aggregate."""
  return _groundFiles('concrete', 1609, 1.2, ((120.0, 120.0, 116.0),
                                              (176.0, 175.0, 168.0)),
                      ((0.45, 0.35, 0.2), 0.992, (95.0, 95.0, 92.0)),
                      (1.0, 0.25, 0.6))


def _asphaltFiles() -> tuple[str, str]:
  """Returns the asphalt's pictures as '_dirtFiles' the dirt's: near
  black, fine, light grey chips of its stone showing."""
  return _groundFiles('asphalt', 1610, 1.1, ((34.0, 35.0, 37.0),
                                             (58.0, 59.0, 62.0)),
                      ((0.5, 0.4, 0.1), 0.985, (128.0, 126.0, 120.0)),
                      (0.8, 0.3, 0.5))


def _groundFiles(name: str, seed: int, fall: float, tones: tuple,
                 mix: tuple, relief: tuple) -> tuple[str, str]:
  """Returns a ground's pictures, written to the temp folder once (named
  for 'name'): periodic noise ('seed', amplitude falling as size to the
  'fall' power) for its height; its colour from the darker of 'tones'
  to the lighter by 'mix' (the height's share, grit's, and a floor),
  points past 'mix[1]' of grit stones of 'mix[2]'; its bumps the slope
  of the height, grit and stones weighed by 'relief'."""
  folder = Path(tempfile.gettempdir())
  paths = (folder / ('worqt-phys-%s.png' % name),
           folder / ('worqt-phys-%s-bumps.png' % name))
  if all(path.exists() for path in paths):
    return str(paths[0]), str(paths[1])
  size = 512
  random = numpy.random.default_rng(seed)
  height = _heightOf(random, size, fall)
  grit = random.random((size, size))
  stones = grit > mix[1]
  dark, light = numpy.array(tones[0]), numpy.array(tones[1])
  shade = mix[0][2] + mix[0][1] * height + mix[0][0] * grit
  colours = dark + (light - dark) * shade[..., None]
  colours[stones] = numpy.array(mix[2]) * (0.8 + 0.2 * grit[stones, None])
  surface = relief[0] * height + relief[1] * grit + relief[2] * stones
  dx = 0.5 * (numpy.roll(surface, -1, 0) - numpy.roll(surface, 1, 0))
  dy = 0.5 * (numpy.roll(surface, -1, 1) - numpy.roll(surface, 1, 1))
  normals = numpy.stack((-dx, -dy, numpy.full_like(dx, 4.0)), axis=2)
  normals /= numpy.linalg.norm(normals, axis=2)[..., None]
  bumps = 127.5 * (normals + 1.0)
  for path, picture in ((paths[0], colours), (paths[1], bumps)):
    data = numpy.ascontiguousarray(numpy.clip(picture, 0, 255).astype(
      numpy.uint8).transpose(1, 0, 2))
    image = QImage(data.data, size, size, 3 * size,
                   QImage.Format.Format_RGB888)
    image.save(str(path))
  return str(paths[0]), str(paths[1])


def _heightOf(random: object, size: int, fall: float) -> numpy.ndarray:
  """Returns noise of every size on a 'size' square, periodic (made by
  the Fourier transform: random phases from 'random', an amplitude
  falling as the size's 'fall' power), from nought to one."""
  ways = numpy.fft.fftfreq(size)
  fx, fy = numpy.meshgrid(ways, ways, indexing='ij')
  reach = numpy.hypot(fx, fy)
  reach[0, 0] = 1.0
  noise = (random.normal(size=(size, size))
           + 1j * random.normal(size=(size, size))) / reach ** fall
  noise[0, 0] = 0.0
  height = numpy.real(numpy.fft.ifft2(noise))
  return (height - height.min()) / (height.max() - height.min())


#  The finishes' pictures painted whole, in their own colours or grey,
#  by name ('_finishFile').
_PAINTED = {'souffle': sidewallPicture, 'badge': badgePicture,
            'leather': leatherPicture}


def _finishFile(name: str) -> str:
  """Returns the picture 'name' a finish lays over a body, grey (its
  look's colour times it), seamless, written to the temp folder once:
  'cast', cast iron's or forged steel's: blotches of every size, a
  grain, a few dark pits; 'turned', a face turned on a lathe: fine
  rings along it (its rows: a picture's second way runs along a run),
  a faint blotch, so a turning part is still seen to turn; 'souffle',
  a tyre's sidewall lettering, in its colours ('sidewallPicture': its
  look white); 'badge', the steering wheel's badge ('badgePicture', its
  look white); 'leather', perforated leather ('leatherPicture')."""
  path = Path(tempfile.gettempdir()) / ('worqt-phys-finish-%s-%d.png' % (
    name, _FINISH_FORM))
  if path.exists():
    return str(path)
  if name in _PAINTED:
    _PAINTED[name](str(path))
    return str(path)
  size = 256
  random = numpy.random.default_rng(20261113 + len(name))
  blotch = _heightOf(random, size, 1.6)
  grain = random.random((size, size))
  if name == 'cast':
    grey = 0.74 + 0.2 * blotch + 0.06 * grain
    grey[grain > 0.994] *= 0.6
  else:
    rings = numpy.convolve(numpy.tile(random.random(size), 3),
                           numpy.ones(3) / 3.0, 'same')[size:2 * size]
    grey = 0.86 + 0.08 * rings[:, None] + 0.04 * blotch + 0.02 * grain
  data = numpy.ascontiguousarray(numpy.repeat(numpy.clip(
    255.0 * grey, 0, 255).astype(numpy.uint8)[..., None], 3, axis=2))
  image = QImage(data.data, size, size, 3 * size,
                 QImage.Format.Format_RGB888)
  image.save(str(path))
  return str(path)
