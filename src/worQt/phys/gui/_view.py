"""
PhysView paints an assembly in 3D: every flat face of every body's
shape projected from an orbiting camera, shaded by its facing, the
nearest last; actuators as legs; the floor first, checkered, the
bodies' shadows cast on it. Drag to orbit, wheel to come nearer.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
import random
import time

import numpy
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtGui import QImage, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget

from .._body import Body, State
from .._poke import hitOf
from .._shape import Sphere, boxShape
from .._turned import Turned
from .._vectors import cross, dot, matrixOf, minus, norm, plus, rotated
from .._vectors import scaled

_LIGHT = (0.35, -0.5, 0.8)
_BACKGROUND = QColor(24, 26, 30)
_FLOOR_TONE = QColor(128, 124, 116)
#  A paved terrain's tones: concrete, and asphalt (an oval's apron).
_PAVED_TONE = QColor(160, 160, 154)
_ASPHALT_TONE = QColor(56, 57, 60)
#  An oval's safety barrier: its tone, and how often it is drawn round
#  the oval, m.
_WALL_TONE, _WALL_STEP = QColor(222, 224, 228), 2.0
_STRIPE_TONE = QColor(31, 95, 200)
_SHADOW = QColor(0, 0, 0, 105)
#  What lies nearer the eye than this, m, along its look is cut away;
#  and what reaches past this many times half the view either side, cut
#  there (a point nearly level with the eye lands hundreds of thousands
#  of pixels off, past the raster's 32768: such a face drew garbage, and
#  quivers of a nanometre flipped it frame to frame; ten views is well
#  within, and few faces reach past it).
_NEAR = 0.02
_GUARD = 10.0
#  How finely a terrain is drawn, m.
_TERRAIN_STEP = 1.0
#  The dither: a tile of this many pixels each way, each of its channels
#  nought or one at random (seeded), added over the picture.
_DITHER = 128
#  A ball poking through a face's plane by less than this share of its
#  radius counts as wholly on its side (a ball resting in a groove pokes
#  through its flat facets by the chords' sag, a hair).
_GRAZE = 0.02
#  Points round a circle, as cosines and sines, for a ball's near part.
_ROUND = tuple((math.cos(k * math.pi / 8), math.sin(k * math.pi / 8))
               for k in range(16))
_ROUND_SHADOW = tuple((math.cos(k * math.pi / 12),
                       math.sin(k * math.pi / 12)) for k in range(24))
#  Points round a ball's outline as drawn; a ball under '_SMALL_DOTS' px
#  across its radius is drawn with half as many and no dots.
_ROUND_BALL = tuple((math.cos(k * math.pi / 16), math.sin(k * math.pi / 16))
                    for k in range(32))
_SMALL_DOTS = 8.0
#  A ball drawn smaller than this, its radius in px, is not cut where it
#  pokes through a face's plane: its middle decides the side (the part
#  wrongly shown or hidden is a few pixels; a whole wheel's 48 balls cut
#  so cost 60 ms a frame).
_SMALL_BALL = 10.0


class PhysView(QWidget):
  """PhysView shows 'assembly' in 'states' (set by 'show_'): the body
  'floor' (its index, or None) drawn first, its top checkered by its
  tile in 'tiles' (0.25 m if none), every other body's shadow on it;
  the other bodies in 'tiles' (index: tile, m) with their tops
  checkered too. The floor is drawn once into a picture, kept till the
  camera, the view's size or the floor moves. With no floor body and a
  'groundSize' (m, half the side) it draws the ground at nought instead,
  checkered by 'tiles["ground"]'. The bodies in 'hidden' are not drawn
  (their shadows are, but for those in 'shadowless'); those in 'tones'
  (index: colour) are drawn in their tone, those in 'bands' (index:
  (rho, colour)) with what of their turned solid lies 'rho' or more
  from its axis in that colour (a wheel's tyre). The ground is drawn
  about 'groundMiddle' (x, y); with a 'terrain' ('Terrain') set, it is
  drawn as the terrain's shape there instead ('groundSize' about it,
  in cells of a metre, checkered by 'tiles["ground"]'), in 'groundTone'
  (the floor's too). Each of 'skins'
  (a skin, as 'TyreSkin', and its parts' tones) is drawn over the
  bodies it is made from, face by face (in the tone of a body it lies
  on, when 'tones' has one), and casts its shadow ('outlines'); a skin
  with 'quads' (as 'CarDress') hands them, by key in its tones, all at
  once, and they are seen all at once. A body
  in 'pieces' (index: its pieces, each a solid in its own frame and a
  key in 'palette', key: colour) is drawn piece by piece. Turned
  solids are shaded smooth (each quad's corners lit by the true surface's
  normals there, a gradient between). With
  'near' (m, '_NEAR' at first: a view for a shrunken walker shrinks it
  too) what lies nearer the eye along its look is cut away. With
  'dither' (on at first) a fixed noise of nought or one level a channel
  is added over the picture, breaking the steps of the gradients' 256
  levels. A drag orbits the camera; a click emits 'poked' for the
  body it lands on (index, point, the surface's outward normal there;
  the floor passed over). While 'recorder' is set (a 'Recorder') each
  frame is painted into a picture first and handed to it, with what it
  was painted from ('drawnNow'), then shown."""

  poked = Signal(int, object, object)

  def __init__(self, ) -> None:
    QWidget.__init__(self)
    self.assembly, self.states, self.sleep = None, (), 0.2
    self.floor, self.tiles, self.groundSize = None, {}, 0.0
    self.hiddenLegs, self.hidden, self.tones = set(), set(), {}
    self.shadowless, self.skins = set(), []
    self.pieces, self.palette = {}, {}
    self.groundTone = _FLOOR_TONE
    self.bands, self.groundMiddle = {}, (0.0, 0.0)
    self.terrain, self.wall = None, None
    self.dither, self.near = True, _NEAR
    self.pressedAt, self.dragged = None, False
    self.yaw, self.pitch, self.distance = 0.6, 0.42, 0.75
    self.target = (0.0, 0.0, 0.18)
    self.grabbed, self.recorder = None, None
    self.floorDrawn = None
    self.setMinimumSize(800, 600)

  def show_(self, assembly: object, states: tuple, settle: float) -> None:
    """Shows 'assembly' in 'states', bodies still 'settle' s asleep."""
    self.assembly, self.states, self.sleep = assembly, states, settle
    self.update()

  def camera(self, ) -> tuple:
    """Returns the eye and its right, up and forward."""
    forward = (-math.cos(self.pitch) * math.cos(self.yaw),
               -math.cos(self.pitch) * math.sin(self.yaw),
               -math.sin(self.pitch))
    eye = minus(self.target, scaled(forward, self.distance))
    right = cross(forward, (0.0, 0.0, 1.0))
    right = scaled(right, 1.0 / norm(right))
    return eye, right, cross(right, forward), forward

  def paintEvent(self, event: object) -> None:
    """Paints the view ('paintOn'); while recording, into a picture
    first, handed to the recorder with the time and what it was painted
    from, then shown."""
    recorder = self.recorder
    if recorder is None:
      painter = QPainter(self)
      self.paintOn(painter)
      painter.end()
      return
    ratio = self.devicePixelRatioF()
    picture = QImage(round(self.width() * ratio),
                     round(self.height() * ratio),
                     QImage.Format.Format_RGB32)
    picture.setDevicePixelRatio(ratio)
    painter = QPainter(picture)
    self.paintOn(painter)
    painter.end()
    recorder.add(picture, time.perf_counter(), self.drawnNow())
    painter = QPainter(self)
    painter.drawImage(0, 0, picture)
    painter.end()

  def drawnNow(self, ) -> dict:
    """The 'drawnNow' method returns what the view paints from now, as
    plain numbers: the camera, the view's size, which bodies are hidden
    and tinted, and every body's place, turn and rest."""
    return {'yaw': self.yaw, 'pitch': self.pitch,
            'distance': self.distance, 'target': list(self.target),
            'width': self.width(), 'height': self.height(),
            'hidden': sorted(self.hidden),
            'tones': {str(index): tone.name()
                      for index, tone in self.tones.items()},
            'states': [] if self.assembly is None else [
              [list(state.place), list(state.turn), state.rest]
              for state in self.states]}

  def paintOn(self, painter: QPainter) -> None:
    """The 'paintOn' method paints the view with 'painter': the floor
    and the shadows on it, the legs, then the faces, far first."""
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(self.rect(), _BACKGROUND)
    if self.assembly is None:
      return
    eye, right, up, forward = self.camera()
    look = _Look(eye, right, up, forward, self.width(), self.height(),
                 self.near)
    seen = look.seen

    def entry(corners: list, tone: QColor, tile: float) -> tuple | None:
      """Returns the flat face 'corners' (around, anticlockwise seen
      from outside; a top checkered by 'tile' m when not None) as
      drawn: how far, its corners and its tiles on the screen, its tone
      and shade; None when facing away or behind."""
      a, b, c = corners[0], corners[1], corners[2]
      facing = cross(minus(b, a), minus(c, a))
      if dot(facing, minus(a, eye)) >= 0.0:
        return None
      drawn = look.onScreen(corners)
      if drawn is None:
        return None
      shade = 0.4 + 0.6 * max(0.0, dot(facing, _LIGHT)
                              / (norm(facing) * norm(_LIGHT)))
      tiles = _tilesOf(corners, tile, look) if tile else None
      return drawn[1], drawn[0], tiles, tone, shade

    faces, planes, balls = [], [], []
    held = {leg.second for leg in self.assembly.actuators}
    for index, (body, state) in enumerate(zip(self.assembly.bodies,
                                              self.states)):
      if body.shape is None or index == self.floor or index in self.hidden:
        continue
      tone = (self.tones[index] if index in self.tones else
              QColor(110, 125, 145) if index in held else
              QColor(150, 175, 215) if state.rest >= self.sleep else
              QColor(205 + index % 3 * 12, 165 + index % 5 * 6, 110))
      if isinstance(body.shape, Sphere):
        ball = _ballFace(body, state, tone, seen, eye, right, forward,
                         look.near)
        if ball is not None:
          balls.append((len(faces), body.placeOf(state, body.centre),
                        body.shape.radius))
          faces.append(ball)
        continue
      if isinstance(body.shape, Turned):
        self._turnedFaces(body, state, tone, entry, look, faces, planes,
                          self.bands.get(index))
        continue
      tile = self.tiles.get(index)
      for shape, shapeTone in self._piecesOf(index, body.shape, tone):
        places = [body.placeOf(state, p) for p in shape.points]
        top = _topOf(shape) if tile else None
        for polygon in _flatFaces(shape):
          corners = [places[i] for i in polygon]
          face = entry(corners, shapeTone, tile if polygon == top
                       else None)
          if face is not None:
            planes.append((len(faces), corners))
            faces.append(face)
    if self.terrain is not None:
      self._terrainFaces(entry, look, faces)
      if self.wall is not None:
        self._wallFaces(entry, faces)
    for skin, skinTones in self.skins:
      if hasattr(skin, 'quads'):
        for key, quads in skin.quads(self.states).items():
          self._quadFaces(quads, skinTones[key], entry, look, faces, planes)
        continue
      for part, corners, lumps in skin.faces(self.states):
        tone = skinTones[part]
        for lump in lumps:
          tone = self.tones.get(lump, tone)
        face = entry(corners, tone, None)
        if face is not None:
          planes.append((len(faces), corners))
          faces.append(face)
    faces = _drawOrder(faces, planes, balls, look)
    if self._floorOf() is not None and self.terrain is None:
      self._paintFloor(painter, entry, look)
    painter.setPen(QPen(QColor(200, 200, 210), 3.0))
    for leg in self.assembly.actuators:
      if leg.second == self.floor or leg.second in self.hiddenLegs:
        continue
      body = self.assembly.bodies[leg.second]
      head = body.placeOf(self.states[leg.second], leg.secondPoint)
      foot = leg.firstPoint
      if leg.first is not None:
        foot = self.assembly.bodies[leg.first].placeOf(
          self.states[leg.first], leg.firstPoint)
      line = _lineOnScreen(foot, head, look)
      if line is not None:
        painter.drawLine(*line)

    for face, hidden in faces:
      if hidden is None:
        _paintFace(painter, face)
        continue
      painter.save()
      seen = QPainterPath()
      seen.addRect(-1.0, -1.0, self.width() + 2.0, self.height() + 2.0)
      painter.setClipPath(seen.subtracted(hidden))
      _paintFace(painter, face)
      painter.restore()
    if self.dither:
      painter.save()
      painter.setCompositionMode(
        QPainter.CompositionMode.CompositionMode_Plus)
      painter.drawTiledPixmap(self.rect(), _ditherTile())
      painter.restore()

  def _piecesOf(self, index: int, shape: object, tone: QColor) -> tuple:
    """Returns how body 'index' is drawn: its pieces, each a solid and
    its tone ('pieces' and 'palette'), or its whole 'shape' in 'tone'."""
    if index not in self.pieces:
      return ((shape, tone),)
    return tuple((piece, self.palette.get(key, tone))
                 for piece, key in self.pieces[index])

  def _wallFaces(self, entry: object, faces: list) -> None:
    """Adds an oval's safety barrier ('wall', on 'terrain') about
    'groundMiddle' to 'faces': its face toward the track and its top,
    within 'groundSize' of it, a band every '_WALL_STEP' m, the face's
    lowest 'WALL_STRIPE' m blue."""
    from .._terrain import ovalAt, ovalPlaceOf
    from ._meshes import WALL_STRIPE
    wall, terrain = self.wall, self.terrain
    stripe = min(WALL_STRIPE, wall.height)
    middle = self.groundMiddle
    out, along = ovalPlaceOf(middle[0], middle[1])
    if abs(out - wall.out) > self.groundSize:
      return
    count = int(2.0 * self.groundSize / _WALL_STEP)
    edges = []
    for k in range(count + 1):
      x, y, heading = ovalAt(along - self.groundSize + k * _WALL_STEP,
                             wall.out)
      ox, oy = math.sin(heading), -math.cos(heading)
      foot, back = terrain.heightAt(x, y), terrain.heightAt(
        x + 0.4 * ox, y + 0.4 * oy)
      edges.append(((x, y, foot), (x, y, foot + stripe),
                    (x, y, foot + wall.height),
                    (x + 0.4 * ox, y + 0.4 * oy, back + wall.height)))
    for (a0, a1, a2, a3), (b0, b1, b2, b3) in zip(edges, edges[1:]):
      for corners, tone in (((a0, a1, b1, b0), _STRIPE_TONE),
                            ((a1, a2, b2, b1), _WALL_TONE),
                            ((a2, a3, b3, b2), _WALL_TONE)):
        face = entry(list(corners), tone, None)
        if face is not None:
          faces.append(face)

  def _terrainFaces(self, entry: object, look: object,
                    faces: list) -> None:
    """Adds the terrain about 'groundMiddle' to 'faces': its shape
    sampled every '_TERRAIN_STEP' m within 'groundSize', each square
    shaded by how it faces the light and checkered by the ground's tile
    (fixed to the ground); those wholly ahead of the eye and within the
    guard band taken as seen, those across the near cut cut by
    'entry'."""
    step, reach = _TERRAIN_STEP, self.groundSize
    tile = self.tiles.get('ground', 2.0)
    middle = self.groundMiddle
    count = int(2.0 * reach / step) + 1
    xs = middle[0] - reach + step * numpy.arange(count)
    ys = middle[1] - reach + step * numpy.arange(count)
    terrain = self.terrain
    heights = numpy.array([[terrain.heightAt(x, y) for y in ys.tolist()]
                           for x in xs.tolist()])
    gx, gy = numpy.meshgrid(xs, ys, indexing='ij')
    places = numpy.stack((gx, gy, heights), axis=2).reshape(-1, 3)
    eye = numpy.array(look.eye)
    away = places - eye
    ahead = away @ numpy.array(look.forward)
    safe = numpy.where(ahead > look.near, ahead, 1.0)
    focal, right = look.focal, numpy.array(look.right)
    px = look.middle.x() + focal * (away @ right) / safe
    py = look.middle.y() - focal * (away @ numpy.array(look.up)) / safe
    i, j = numpy.meshgrid(numpy.arange(count - 1), numpy.arange(count - 1),
                          indexing='ij')
    i, j = i.ravel(), j.ravel()
    quads = numpy.stack((i * count + j, (i + 1) * count + j,
                         (i + 1) * count + j + 1, i * count + j + 1),
                        axis=1)
    a, b, d = places[quads[:, 0]], places[quads[:, 1]], places[quads[:, 3]]
    facing = numpy.cross(b - a, d - a)
    front = numpy.einsum('ij,ij->i', facing, a - eye) < 0.0
    quadAhead = ahead[quads]
    front &= quadAhead.max(axis=1) > look.near
    whole = quadAhead.min(axis=1) > look.near
    qx, qy = px[quads], py[quads]
    whole &= ((numpy.abs(qx - look.middle.x()) <= look.bandX)
              & (numpy.abs(qy - look.middle.y()) <= look.bandY)).all(axis=1)
    lit = facing @ numpy.array(_LIGHT) / (numpy.linalg.norm(facing, axis=1)
                                          * norm(_LIGHT))
    shades = 0.4 + 0.6 * numpy.maximum(lit, 0.0)
    centres = places[quads].mean(axis=1)
    dark = ((numpy.floor(centres[:, 0] / tile)
             + numpy.floor(centres[:, 1] / tile)) % 2.0) > 0.5
    far = quadAhead.max(axis=1)
    light, shadow = self.groundTone, self.groundTone.darker(118)
    paved = _pavedAt(terrain, centres)
    tones = ((light, shadow), (_PAVED_TONE, _PAVED_TONE.darker(108)),
             (_ASPHALT_TONE, _ASPHALT_TONE.darker(112)))
    for q in numpy.flatnonzero(front).tolist():
      tone = tones[int(paved[q])][1 if dark[q] else 0]
      if whole[q]:
        faces.append((float(far[q]), [QPointF(x, y) for x, y in
                                      zip(qx[q].tolist(), qy[q].tolist())],
                      None, tone, float(shades[q])))
        continue
      corners = [tuple(corner) for corner in places[quads[q]].tolist()]
      face = entry(corners, tone, None)
      if face is not None:
        faces.append(face)

  def _turnedFaces(self, body: object, state: object, tone: QColor,
                   entry: object, look: tuple, faces: list,
                   planes: list, band: tuple | None) -> None:
    """Adds a turned solid's quads to 'faces' (and their corners to
    'planes'), as 'entry' gives them, seen from 'look': its points
    placed and seen all at once (numpy), the quads facing away, wholly
    behind the eye or wholly off the view passed over, one wholly ahead
    of the eye and within the guard band taken as seen, else cut by
    'entry'."""
    eye, right, up, forward = look.eye, look.right, look.up, look.forward
    focal, middle = look.focal, look.middle
    own, quads = _turnedArrays(body.shape)
    turning = numpy.array(matrixOf(state.turn))
    places = (own - numpy.array(body.centre)) @ turning.T + numpy.array(
      state.place)
    away = places - numpy.array(eye)
    ahead = away @ numpy.array(forward)
    safe = numpy.where(ahead > look.near, ahead, 1.0)
    xs = middle.x() + focal * (away @ numpy.array(right)) / safe
    ys = middle.y() - focal * (away @ numpy.array(up)) / safe
    a, b, d = places[quads[:, 0]], places[quads[:, 1]], places[quads[:, 2]]
    facing = numpy.cross(b - a, d - a)
    front = numpy.einsum('ij,ij->i', facing, a - numpy.array(eye)) < 0.0
    quadAhead = ahead[quads]
    whole = quadAhead.min(axis=1) > look.near
    front &= quadAhead.max(axis=1) > look.near
    quadXs, quadYs = xs[quads], ys[quads]
    whole &= ((numpy.abs(quadXs - middle.x()) <= look.bandX)
              & (numpy.abs(quadYs - middle.y()) <= look.bandY)).all(axis=1)
    sides = away @ numpy.array(look.edges).T
    off = (sides[quads] < 0.0).all(axis=1).any(axis=1)
    normals = _turnedNormals(body.shape) @ turning.T
    lit = normals @ numpy.array(_LIGHT) / norm(_LIGHT)
    shades = 0.4 + 0.6 * numpy.maximum(lit, 0.0)
    far = quadAhead.max(axis=1)
    ramps = _rampsOf(quadXs, quadYs, shades,
                     max(tone.red(), tone.green(), tone.blue()))
    boxes = numpy.column_stack((quadXs.min(axis=1), quadXs.max(axis=1),
                                quadYs.min(axis=1), quadYs.max(axis=1)))
    kept = numpy.flatnonzero(front & ~off)
    cornersAll = places[quads[kept]].tolist()
    strip = len(own) // body.shape.sides
    banded = None
    if band is not None:
      rhos = numpy.sqrt(own[:, 0] ** 2 + own[:, 1] ** 2)
      banded = rhos[quads].min(axis=1) >= band[0] - 1e-9
    bodyTone = tone
    for q, corners in zip(kept.tolist(), cornersAll):
      corners = [tuple(corner) for corner in corners]
      tone = band[1] if banded is not None and banded[q] else bodyTone
      if whole[q]:
        face = (float(far[q]), [QPointF(x, y) for x, y in
                                zip(quadXs[q].tolist(),
                                    quadYs[q].tolist())],
                None, tone, ramps[q], tuple(boxes[q].tolist()),
                (id(body.shape), q % strip))
      else:
        face = entry(corners, tone, None)
        if face is not None:
          face = face[:4] + (float(shades[q].mean()),)
      if face is not None:
        planes.append((len(faces), corners))
        faces.append(face)

  def _quadFaces(self, quads: numpy.ndarray, tone: QColor, entry: object,
                 look: _Look, faces: list, planes: list) -> None:
    """Adds 'quads' (n, 4, 6: in the world, each corner's place and
    normal, around anticlockwise from outside) to 'faces' (and their
    corners to 'planes') in 'tone', each shaded by its corners' mean
    normal, all seen at once (numpy): those facing away, wholly behind
    the eye or wholly off the view passed over, those wholly ahead and
    within the guard band taken as seen, the rest cut by 'entry'."""
    places = quads[:, :, :3]
    eye = numpy.array(look.eye)
    away = places - eye
    ahead = away @ numpy.array(look.forward)
    a, b, c = places[:, 0], places[:, 1], places[:, 2]
    facing = numpy.cross(b - a, c - a)
    front = numpy.einsum('ij,ij->i', facing, a - eye) < 0.0
    front &= ahead.max(axis=1) > look.near
    off = ((away @ numpy.array(look.edges).T) < 0.0).all(axis=1).any(
      axis=1)
    kept = numpy.flatnonzero(front & ~off)
    if not len(kept):
      return
    places, away, ahead = places[kept], away[kept], ahead[kept]
    safe = numpy.where(ahead > look.near, ahead, 1.0)
    middle, focal = look.middle, look.focal
    xs = middle.x() + focal * (away @ numpy.array(look.right)) / safe
    ys = middle.y() - focal * (away @ numpy.array(look.up)) / safe
    whole = ahead.min(axis=1) > look.near
    whole &= ((numpy.abs(xs - middle.x()) <= look.bandX)
              & (numpy.abs(ys - middle.y()) <= look.bandY)).all(axis=1)
    normals = quads[kept, :, 3:].mean(axis=1)
    lit = normals @ numpy.array(_LIGHT) / (
      numpy.linalg.norm(normals, axis=1) * norm(_LIGHT))
    shades = (0.4 + 0.6 * numpy.maximum(lit, 0.0)).tolist()
    far = ahead.max(axis=1).tolist()
    for q, (corners, quadX, quadY) in enumerate(zip(
            places.tolist(), xs.tolist(), ys.tolist())):
      if whole[q]:
        face = (far[q], [QPointF(x, y) for x, y in zip(quadX, quadY)],
                None, tone, shades[q])
      else:
        face = entry([tuple(corner) for corner in corners], tone, None)
        if face is None:
          continue
        face = face[:4] + (shades[q],)
      planes.append((len(faces), corners))
      faces.append(face)

  def _paintFloor(self, painter: QPainter, entry: object,
                  look: _Look) -> None:
    """Paints the floor, its top checkered, and every other body's
    shadow on its top (cast away from the light, clipped to the top),
    when the eye is over it, all as 'look' sees it."""
    drawn = self._floorAsDrawn(entry, look.eye)
    if drawn is None:
      return
    level, picture, top = drawn
    painter.drawPixmap(0, 0, picture)
    if top is None:
      return
    shadows = QPainterPath()
    shadows.setFillRule(Qt.FillRule.WindingFill)
    top = tuple(top)
    outlines = []
    for index, (other, state) in enumerate(zip(self.assembly.bodies,
                                               self.states)):
      if (other.shape is None or index == self.floor
              or index in self.shadowless):
        continue
      place = tuple(round(x, 6) for x in state.place)
      if isinstance(other.shape, Sphere):
        outlines.extend(_ballShadowOf(other.shape.radius, place, level,
                                      top))
        continue
      if isinstance(other.shape, Turned):
        outlines.extend(_turnedShadowOf(other, place, state.turn, level,
                                        top))
        continue
      turn = tuple(round(x, 9) for x in state.turn)
      outlines.extend(_shadowsOf(other, place, turn, level, top))
    for skin, _ in self.skins:
      for group in skin.outlines(self.states):
        outlines.extend(_castOutline(group, level, top))
    for polygon in _seenFlat(outlines, level, look):
      shadows.addPolygon(QPolygonF(polygon))
      shadows.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_SHADOW)
    painter.drawPath(shadows)

  def _floorAsDrawn(self, entry: object, eye: tuple) -> tuple | None:
    """Returns the floor as drawn now: its top's height, its picture
    (sides far first, then the top, checkered) and its top's corners
    in the plane, around (None when facing away); None when the eye is
    under its top. Kept till the camera (to a tenth of a millimetre:
    an eye resting on a springy ground bobs less), the view's size or
    the floor moves."""
    body, state = self._floorOf()
    step = 0.005 * self.near
    target = tuple(round(x / step) for x in self.target)
    key = (self.yaw, self.pitch, self.distance, target, self.width(),
           self.height(), body, state.place, state.turn)
    if self.floorDrawn is not None and self.floorDrawn[0] == key:
      return self.floorDrawn[1]
    places = [body.placeOf(state, p) for p in body.shape.points]
    top = _topOf(body.shape)
    level = max(places[i][2] for i in top)
    drawn = None
    if eye[2] > level:
      sides = []
      for polygon in _flatFaces(body.shape):
        if polygon != top:
          side = entry([places[i] for i in polygon], self.groundTone,
                       None)
          if side is not None:
            sides.append(side)
      sides.sort(key=lambda side: -side[0])
      tile = self.tiles.get('ground' if self.floor is None else self.floor,
                            0.25)
      face = entry([places[i] for i in top], self.groundTone, tile)
      ratio = self.devicePixelRatioF()
      picture = QPixmap(round(self.width() * ratio),
                        round(self.height() * ratio))
      picture.setDevicePixelRatio(ratio)
      picture.fill(Qt.GlobalColor.transparent)
      painter = QPainter(picture)
      painter.setRenderHint(QPainter.RenderHint.Antialiasing)
      for side in sides + ([face] if face is not None else []):
        _paintFace(painter, side)
      painter.end()
      corners = [places[i][:2] for i in top] if face is not None else None
      drawn = (level, picture, corners)
    self.floorDrawn = (key, drawn)
    return drawn

  def _floorOf(self, ) -> tuple | None:
    """Returns the floor to draw, its body and state: the floor body,
    else the ground as a slab 'groundSize' each way about the middle,
    its top at nought; None for neither."""
    if self.floor is not None:
      return self.assembly.bodies[self.floor], self.states[self.floor]
    if self.groundSize > 0.0:
      middle = self.groundMiddle
      return _groundSlab(self.groundSize), State((middle[0], middle[1],
                                                  -0.05))
    return None

  def poke(self, where: QPointF) -> None:
    """Emits 'poked' for the body under 'where' on the screen: its
    index, the point met, the surface's outward normal there."""
    if self.assembly is None:
      return
    eye, right, up, forward = self.camera()
    focal = 0.9 * min(self.width(), self.height())
    across = (where.x() - 0.5 * self.width()) / focal
    upward = (0.5 * self.height() - where.y()) / focal
    direction = plus(forward, plus(scaled(right, across),
                                   scaled(up, upward)))
    passed = () if self.floor is None else (self.floor,)
    hit = hitOf(self.assembly, self.states, eye, direction, passed)
    if hit is not None:
      self.poked.emit(*hit)

  def mousePressEvent(self, event: object) -> None:
    """Grabs the view: a drag orbits it, a click pokes."""
    self.grabbed = self.pressedAt = event.position()
    self.dragged = False

  def mouseMoveEvent(self, event: object) -> None:
    """Orbits the camera as the pointer drags, once it has moved a
    few pixels (less is still a click)."""
    if self.grabbed is None:
      return
    if not self.dragged:
      off = event.position() - self.pressedAt
      if abs(off.x()) + abs(off.y()) < 4.0:
        return
      self.dragged = True
    moved = event.position() - self.grabbed
    self.grabbed = event.position()
    self.yaw -= 0.01 * moved.x()
    self.pitch = min(1.5, max(-0.2, self.pitch + 0.01 * moved.y()))
    self.update()

  def mouseReleaseEvent(self, event: object) -> None:
    """Lets the view go; a press let go without dragging pokes what
    it landed on."""
    if self.grabbed is not None and not self.dragged:
      self.poke(event.position())
    self.grabbed = None

  def wheelEvent(self, event: object) -> None:
    """Comes nearer or goes back."""
    self.distance *= 0.9 if event.angleDelta().y() > 0 else 1.1
    self.update()


def _seenFlat(outlines: list, level: float, look: _Look) -> list:
  """Returns the polygons 'outlines' (each its corners x, y) lying at
  height 'level' as seen by 'look': all their corners seen at once
  (numpy), a polygon wholly ahead of the eye and within the guard band
  taken so, any other cut ('onScreen'); those left with nothing are
  left out."""
  if not outlines:
    return []
  counts = [len(outline) for outline in outlines]
  points = numpy.array([corner for outline in outlines
                        for corner in outline], numpy.float64)
  away = numpy.column_stack((points[:, 0] - look.eye[0],
                             points[:, 1] - look.eye[1],
                             numpy.full(len(points), level - look.eye[2])))
  ahead = away @ numpy.array(look.forward)
  safe = numpy.where(ahead > look.near, ahead, 1.0)
  xs = look.middle.x() + look.focal * (away @ numpy.array(look.right)) / safe
  ys = look.middle.y() - look.focal * (away @ numpy.array(look.up)) / safe
  good = ((ahead > look.near)
          & (numpy.abs(xs - look.middle.x()) <= look.bandX)
          & (numpy.abs(ys - look.middle.y()) <= look.bandY))
  out, first = [], 0
  for outline, count in zip(outlines, counts):
    last = first + count
    if good[first:last].all():
      out.append([QPointF(x, y) for x, y in zip(xs[first:last].tolist(),
                                                 ys[first:last].tolist())])
    else:
      cut = look.onScreen([(x, y, level) for x, y in outline])
      if cut is not None:
        out.append(cut[0])
    first = last
  return out


@functools.lru_cache(maxsize=16)
def _turnedNormals(shape: Turned) -> numpy.ndarray:
  """Returns a turned solid's 'normals' as a numpy array: quads by
  corners by axes."""
  return numpy.array(shape.normals(), numpy.float64)


@functools.lru_cache(maxsize=1)
def _ditherTile() -> QPixmap:
  """Returns the dither's tile: '_DITHER' pixels each way, each channel
  nought or one at random (seeded, so it holds still)."""
  draw = random.Random(1)
  data = bytes(draw.getrandbits(1) if k % 4 < 3 else 0
               for k in range(4 * _DITHER * _DITHER))
  image = QImage(data, _DITHER, _DITHER, 4 * _DITHER,
                 QImage.Format.Format_RGB32)
  return QPixmap.fromImage(image.copy())


@functools.lru_cache(maxsize=16)
def _turnedArrays(shape: Turned) -> tuple:
  """Returns a turned solid's mesh points in its own frame and its
  quads, as numpy arrays."""
  return (numpy.array(shape.mesh().points, numpy.float64),
          numpy.array(shape.quads(), numpy.int64))


def _ballFace(body: object, state: object, tone: QColor, seen: object,
              eye: tuple, right: tuple, forward: tuple,
              near: float) -> tuple | None:
  """Returns a ball as 'entry' gives a face: its outline on the screen,
  round (32 points, 16 drawn under '_SMALL_DOTS' px across its radius),
  as far as its far side, its tone, and the ends of its own axes as dots
  where they face the eye (they turn with it, so its rolling shows; not
  drawn on a ball that small); None when it is nearer the eye than
  'near' or behind it."""
  radius = body.shape.radius
  centre = body.placeOf(state, body.centre)
  if dot(minus(centre, eye), forward) < near + radius:
    return None
  middle, ahead = seen(centre)
  edge, _ = seen(plus(centre, scaled(right, radius)))
  size = math.hypot(edge.x() - middle.x(), edge.y() - middle.y())
  small = size < _SMALL_DOTS
  outline = [QPointF(middle.x() + size * c, middle.y() + size * s)
             for c, s in (_ROUND if small else _ROUND_BALL)]
  dots = []
  for axis in (() if small else _ENDS):
    out = rotated(state.turn, scaled(axis, radius))
    point = plus(centre, out)
    if dot(out, minus(eye, point)) <= 0.0:
      continue
    spot, _ = seen(point)
    dots.append(QPolygonF([
      QPointF(spot.x() + 0.12 * size * math.cos(math.pi * k / 4),
              spot.y() + 0.12 * size * math.sin(math.pi * k / 4))
      for k in range(8)]))
  return ahead + radius, outline, dots, tone, 0.9


@functools.lru_cache(maxsize=8)
def _groundSlab(size: float) -> Body:
  """Returns the ground drawn as a slab 'size' m each way about the
  middle, 0.1 m thick."""
  return Body.of(boxShape(2.0 * size, 2.0 * size, 0.1), 1000.0)


def _drawOrder(faces: list, planes: list, balls: list,
               look: _Look) -> list:
  """Returns 'faces' in the order to paint them, each with what of the
  screen it is not to be painted over (a path; None for most): the flat
  faces far first (by their farthest corner), each ball put in among
  them right after the last one it must follow. Against a face its
  outline meets on the screen a ball is decided by the face's plane:
  wholly on the eye's side, the face cannot hide it (both lie on one
  side of its plane), so the ball follows it; wholly on the far side,
  the face hides it, so the ball is cut by it if drawn first; through
  the plane, the ball follows it, cut by it but where the ball's part on
  the eye's side shows ('_nearPartOf'; the faces of one strip of a
  turned solid's profile, many small round a ball, cut together, by
  the plane their own planes average to: the strip's curve across a
  ball is a hair). Among balls whose outlines meet
  the nearer follows the farther. So the faces' own order (a guess, by
  the farthest corner) does not decide what hides a ball: put in among
  them by that alone, a ball in the ring's groove was cut by the edges
  of faces beside it longer than it, and from low down showed whole over
  the groove's rim, which its bottom dips under. Each ball's place is
  found among the flat faces alone (only those whose boxes meet its,
  found at once in numpy), the farthest ball first; then all are put in
  at once."""
  ordered = sorted((index for index in range(len(faces))
                    if index not in {at for at, _, _ in balls}),
                   key=lambda index: -faces[index][0])
  if not balls:
    return [(faces[index], None) for index in ordered]
  rank = {index: k for k, index in enumerate(ordered)}
  sides = {}
  for index, corners in planes:
    a, b, c = corners[0], corners[1], corners[2]
    facing = cross(minus(b, a), minus(c, a))
    size = norm(facing)
    if size > 0.0:
      sides[index] = (a, scaled(facing, 1.0 / size))
  boxes = numpy.array([faces[index][5] if len(faces[index]) > 5
                       else _boxOf(faces[index][1]) for index in ordered],
                      numpy.float64).reshape(-1, 4)
  slots, hiding, placed = {}, {}, []
  for at, centre, radius in sorted(balls,
                                   key=lambda ball: -faces[ball[0]][0]):
    outline = faces[at][1]
    middle = QPointF(sum(p.x() for p in outline) / len(outline),
                     sum(p.y() for p in outline) / len(outline))
    size = math.hypot(outline[0].x() - middle.x(),
                      outline[0].y() - middle.y())
    away = norm(minus(centre, look.eye))
    after, cuts, strips = -1, [], {}
    near = numpy.flatnonzero(
      (boxes[:, 0] <= middle.x() + size) & (boxes[:, 1] >= middle.x() - size)
      & (boxes[:, 2] <= middle.y() + size)
      & (boxes[:, 3] >= middle.y() - size)).tolist()
    for k in near:
      index = ordered[k]
      if index not in sides or not _discMeets(faces[index][1], middle,
                                              size):
        continue
      a, normal = sides[index]
      over = dot(normal, minus(centre, a))
      if over <= -(1.0 - _GRAZE) * radius:
        cuts.append((k, _pathOf(faces[index][1])))
        continue
      if size < _SMALL_BALL and over < 0.0:
        cuts.append((k, _pathOf(faces[index][1])))
        continue
      after = max(after, k)
      if over < (1.0 - _GRAZE) * radius and size >= _SMALL_BALL:
        key = faces[index][6] if len(faces[index]) > 6 else index
        group = strips.setdefault(key, [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                                        0, QPainterPath(), -1])
        group[0] = plus(group[0], normal)
        group[1] = plus(group[1], a)
        group[2] += 1
        group[3] = group[3].united(_pathOf(faces[index][1]))
        group[4] = max(group[4], k)
    round_ = _ROUND if size >= 30.0 else _ROUND[::2]
    for normals, points, count, outline, k in strips.values():
      normal = scaled(normals, 1.0 / norm(normals))
      cuts.append((k, outline.subtracted(_pathOf(_nearPartOf(
        centre, radius, scaled(points, 1.0 / count), normal, look,
        round_)))))
    for other, otherMiddle, otherSize, otherSlot in placed:
      if math.hypot(middle.x() - otherMiddle.x(),
                    middle.y() - otherMiddle.y()) < size + otherSize:
        after = max(after, otherSlot)
    kept = [path for k, path in cuts if k <= after]
    if kept:
      hidden = QPainterPath()
      hidden.setFillRule(Qt.FillRule.WindingFill)
      for path in kept:
        hidden = hidden.united(path)
      hiding[at] = hidden
    slots[at] = after
    placed.append((at, middle, size, after))
  out, waiting = [], sorted(slots.items(), key=lambda item: item[1])
  pending = 0
  for k, index in enumerate([-1] + ordered):
    if k:
      out.append((faces[index], None))
    while pending < len(waiting) and waiting[pending][1] <= k - 1:
      at = waiting[pending][0]
      out.append((faces[at], hiding.get(at)))
      pending += 1
  return out


def _pathOf(polygon: list) -> QPainterPath:
  """Returns the screen polygon 'polygon' as a closed path."""
  path = QPainterPath()
  path.addPolygon(QPolygonF(polygon))
  path.closeSubpath()
  return path


def _nearPartOf(centre: tuple, radius: float, a: tuple, normal: tuple,
                look: _Look, round_: tuple) -> list:
  """Returns where on the screen the part of the ball at 'centre' of
  'radius' on the eye's side of the plane through 'a' along 'normal'
  (unit, facing the eye) is seen: the outline (convex, the part being
  convex) of the circle the plane cuts the ball in and of the points of
  the ball's own outline on that side, as many of each as 'round_'
  (cosines and sines: 16 for a ball drawn large, 8 small)."""
  over = dot(normal, minus(centre, a))
  points = _circleOf(minus(centre, scaled(normal, over)), normal,
                     math.sqrt(max(0.0, radius * radius - over * over)),
                     round_)
  toward = minus(look.eye, centre)
  far = norm(toward)
  if far > radius:
    share = radius * radius / (far * far)
    points += [point for point in _circleOf(
      plus(centre, scaled(toward, share)), scaled(toward, 1.0 / far),
      radius * math.sqrt(1.0 - share), round_)
      if dot(normal, minus(point, a)) >= 0.0]
  shown = []
  for point in points:
    away = minus(point, look.eye)
    ahead = max(dot(away, look.forward), look.near)
    shown.append((look.middle.x() + look.focal * dot(away, look.right)
                  / ahead,
                  look.middle.y() - look.focal * dot(away, look.up) / ahead))
  return [QPointF(x, y) for x, y in _hullOf(shown)]


def _circleOf(middle: tuple, axis: tuple, radius: float,
              round_: tuple) -> list:
  """Returns the points 'round_' (cosines and sines) round the circle
  about 'middle' of 'radius' in the plane across the unit 'axis'."""
  helper = (1.0, 0.0, 0.0) if abs(axis[0]) < 0.9 else (0.0, 1.0, 0.0)
  u = cross(axis, helper)
  u = scaled(u, radius / norm(u))
  v = cross(scaled(axis, 1.0), u)
  return [(middle[0] + c * u[0] + s * v[0], middle[1] + c * u[1] + s * v[1],
           middle[2] + c * u[2] + s * v[2]) for c, s in round_]


def _boxOf(points: list) -> tuple:
  """Returns the box about 'points' on the screen: left, right, top,
  bottom."""
  xs = [point.x() for point in points]
  ys = [point.y() for point in points]
  return min(xs), max(xs), min(ys), max(ys)


def _discMeets(polygon: list, middle: QPointF, size: float) -> bool:
  """Tells whether the disc of 'size' about 'middle' meets the convex
  'polygon', all on the screen."""
  inside, sign = True, 0.0
  for at, p in enumerate(polygon):
    q = polygon[(at + 1) % len(polygon)]
    ex, ey = q.x() - p.x(), q.y() - p.y()
    mx, my = middle.x() - p.x(), middle.y() - p.y()
    turn = ex * my - ey * mx
    if sign == 0.0:
      sign = turn
    elif turn * sign < 0.0:
      inside = False
    length = ex * ex + ey * ey
    share = 0.0 if length == 0.0 else max(0.0, min(1.0, (mx * ex + my * ey)
                                                   / length))
    dx, dy = mx - share * ex, my - share * ey
    if dx * dx + dy * dy <= size * size:
      return True
  return inside


#  The ends of a body's own axes, both ways.
_ENDS = ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
         (0.0, -1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, -1.0))


@functools.lru_cache(maxsize=64)
def _ballPoints(radius: float) -> tuple:
  """Returns points round a ball of 'radius' on its three great
  circles, every 15 degrees: enough for its shadow's outline."""
  out = []
  for k in range(24):
    c = radius * math.cos(math.pi * k / 12)
    s = radius * math.sin(math.pi * k / 12)
    out.extend(((c, s, 0.0), (c, 0.0, s), (0.0, c, s)))
  return tuple(out)


#  Turned solids' shadows, kept by place and axis (a turned solid's
#  shadow is the same however far it has turned about its own axis, to
#  the width of a side), the last '_KEPT_SHADOWS'.
_TURNED_SHADOWS: dict = {}
_KEPT_SHADOWS = 64


def _turnedShadowOf(body: Body, place: tuple, turn: tuple, level: float,
                    top: tuple) -> tuple:
  """Returns '_shadowsOf' for a turned solid, kept by its place and its
  axis (a ring turning as a wheel casts the same shadow all the while:
  worked out anew each frame, its 72 sides' outlines cost 25 ms)."""
  axis = tuple(round(x, 6) for x in rotated(turn, (0.0, 0.0, 1.0)))
  key = (body, place, axis, level, top)
  if key not in _TURNED_SHADOWS:
    if len(_TURNED_SHADOWS) >= _KEPT_SHADOWS:
      _TURNED_SHADOWS.clear()
    _TURNED_SHADOWS[key] = _shadowsOf(body, place, tuple(turn), level, top)
  return _TURNED_SHADOWS[key]


@functools.lru_cache(maxsize=512)
def _ballShadowOf(radius: float, place: tuple, level: float,
                  top: tuple) -> tuple:
  """Returns the shadow of a ball of 'radius' at 'place' on the floor's
  top at 'level', cut to its corners 'top': the ellipse its rim seen
  from the light casts, 24 points round (exact: a circle cast along
  the light), not cut where it lies wholly on the top."""
  light = scaled(_LIGHT, 1.0 / norm(_LIGHT))
  helper = (1.0, 0.0, 0.0) if abs(light[0]) < 0.9 else (0.0, 1.0, 0.0)
  u = cross(light, helper)
  u = scaled(u, radius / norm(u))
  v = cross(light, scaled(u, 1.0 / radius))
  v = scaled(v, radius)
  cast = []
  for c, s in _ROUND_SHADOW:
    at = plus(place, plus(scaled(u, c), scaled(v, s)))
    over = max(0.0, at[2] - level) / _LIGHT[2]
    cast.append((at[0] - over * _LIGHT[0], at[1] - over * _LIGHT[1]))
  outline = cast if _wellInside(cast, top) else _cutTo(cast, list(top))
  return (tuple(outline),) if len(outline) >= 3 else ()


def _wellInside(points: list, top: tuple) -> bool:
  """Tells whether the plane 'points' lie inside the floor's top
  'top' when that is a rectangle along the axes (as the ground is):
  their box within its."""
  xs = sorted({round(x, 9) for x, _ in top})
  ys = sorted({round(y, 9) for _, y in top})
  if len(top) != 4 or len(xs) != 2 or len(ys) != 2:
    return False
  return (min(x for x, _ in points) >= xs[0]
          and max(x for x, _ in points) <= xs[1]
          and min(y for _, y in points) >= ys[0]
          and max(y for _, y in points) <= ys[1])


@functools.lru_cache(maxsize=512)
def _shadowsOf(body: Body, place: tuple, turn: tuple, level: float,
               top: tuple) -> tuple:
  """Returns the shadow of 'body' (at 'place', turned 'turn') on the
  floor's top at 'level', cut to its corners 'top': its groups' outlines
  in the plane, cast away from the light. Kept for bodies that have not
  moved (asked with their place to the micrometre: a body held by legs
  quivers by less)."""
  state = State(place, turn)
  out = []
  for group in _castGroups(body.shape):
    cast = []
    for point in group:
      at = body.placeOf(state, point)
      over = max(0.0, at[2] - level) / _LIGHT[2]
      cast.append((at[0] - over * _LIGHT[0], at[1] - over * _LIGHT[1]))
    hull = _hullOf(cast)
    outline = hull if _wellInside(hull, top) else _cutTo(hull, list(top))
    if len(outline) >= 3:
      out.append(tuple(outline))
  return tuple(out)


def _castOutline(points: list, level: float, top: tuple) -> tuple:
  """Returns the shadow of 'points' (in the world) on the floor's top
  at 'level', cut to its corners 'top': their outline in the plane,
  cast away from the light (none, or one)."""
  cast = []
  for at in points:
    over = max(0.0, at[2] - level) / _LIGHT[2]
    cast.append((at[0] - over * _LIGHT[0], at[1] - over * _LIGHT[1]))
  hull = _hullOf(cast)
  outline = hull if _wellInside(hull, top) else _cutTo(hull, list(top))
  return (tuple(outline),) if len(outline) >= 3 else ()


@functools.lru_cache(maxsize=16)
def _castGroups(shape: object) -> tuple:
  """Returns groups of the points of 'shape' whose shadows, each
  group's outlined, make its own: its corners, the points round a
  ball, or a turned solid's corners side by side (a hoop casts a ring,
  not a disc; one bored little, a wheel, all at once)."""
  if isinstance(shape, Sphere):
    return (_ballPoints(shape.radius),)
  if isinstance(shape, Turned):
    corners = shape.corners()
    each = len(corners) // shape.sides
    reaches = [math.hypot(x, y) for x, y, _ in corners]
    if min(reaches) < _DISC * max(reaches):
      return (corners,)
    return tuple(corners[i * each:(i + 1) * each]
                 + corners[((i + 1) % shape.sides) * each:
                           ((i + 1) % shape.sides) * each + each]
                 for i in range(shape.sides))
  return (shape.points,)


#  A turned solid whose bore is less than this share of its reach casts
#  its shadow whole, a disc's (a wheel), not as a hoop's.
_DISC = 0.3


def _paintFace(painter: QPainter, face: tuple) -> None:
  """Paints a face as 'entry' gives it: filled in its tone as shaded,
  its tiles a shade darker; one shaded by a ramp ('_rampsOf': a tuple)
  filled with that gradient, unsmoothed: neighbours so filled meet
  without a seam, as smoothed they showed the background through a
  hairline, and stroking the gradient round each (which hid it) took
  half again as long."""
  corners, tiles, tone, shade = face[1], face[2], face[3], face[4]
  if isinstance(shade, tuple):
    x0, y0, x1, y1, first, last = shade
    gradient = QLinearGradient(x0, y0, x1, y1)
    gradient.setColorAt(0.0, _shaded(tone, first))
    gradient.setColorAt(1.0, _shaded(tone, last))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(gradient)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    painter.drawPolygon(QPolygonF(corners))
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    return
  color = _shaded(tone, shade)
  painter.setPen(QPen(color, 1.0))
  painter.setBrush(color)
  painter.drawPolygon(QPolygonF(corners))
  if tiles is not None:
    darker = QColor(int(color.red() * 0.78), int(color.green() * 0.78),
                    int(color.blue() * 0.78))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(darker)
    for tile in tiles:
      painter.drawPolygon(tile)


def _rampsOf(xs: numpy.ndarray, ys: numpy.ndarray, shades: numpy.ndarray,
             brightest: int) -> list:
  """Returns how to shade each quad (corners 'xs', 'ys' on the screen,
  shaded 'shades' at them; rows of four), all at once: by the shading
  that changes evenly across the screen and meets its corners best (its
  change along the two diagonals, which a gradient draws exactly), as
  (x0, y0, x1, y1, first, last), a gradient from its darkest end to its
  lightest; or flat in its mean (a number) where that would not show:
  less than a level of 'brightest' (its tone's brightest channel) apart,
  or a few pixels long."""
  mean = shades.mean(axis=1)
  ux, uy = xs[:, 2] - xs[:, 0], ys[:, 2] - ys[:, 0]
  vx, vy = xs[:, 3] - xs[:, 1], ys[:, 3] - ys[:, 1]
  du, dv = shades[:, 2] - shades[:, 0], shades[:, 3] - shades[:, 1]
  across = ux * vy - uy * vx
  safe = numpy.where(numpy.abs(across) > 1e-9, across, 1.0)
  gx = numpy.where(numpy.abs(across) > 1e-9,
                   (du * vy - dv * uy) / safe, 0.0)
  gy = numpy.where(numpy.abs(across) > 1e-9,
                   (dv * ux - du * vx) / safe, 0.0)
  mx, my = xs.mean(axis=1), ys.mean(axis=1)
  along = (xs - mx[:, None]) * gx[:, None] + (ys - my[:, None]) * gy[:, None]
  low, high = along.min(axis=1), along.max(axis=1)
  slope2 = gx * gx + gy * gy
  flat = ((slope2 == 0.0) | ((high - low) * brightest < 1.0)
          | ((high - low) ** 2 < 36.0 * slope2))
  per = numpy.where(slope2 > 0.0, 1.0 / numpy.where(slope2 > 0.0, slope2,
                                                     1.0), 0.0)
  x0, y0 = mx + low * gx * per, my + low * gy * per
  x1, y1 = mx + high * gx * per, my + high * gy * per
  first = numpy.clip(mean + low, 0.0, 1.0)
  last = numpy.clip(mean + high, 0.0, 1.0)
  rows = numpy.column_stack((x0, y0, x1, y1, first, last)).tolist()
  means = mean.tolist()
  return [means[q] if flat[q] else tuple(rows[q])
          for q in range(len(means))]


def _shaded(tone: QColor, shade: float) -> QColor:
  """Returns 'tone' shaded by 'shade' (nought dark, one as it is)."""
  return QColor(int(tone.red() * shade), int(tone.green() * shade),
                int(tone.blue() * shade))


def _pavedAt(terrain: object, places: numpy.ndarray) -> numpy.ndarray:
  """Returns what the terrain is surfaced with at each of 'places' (its
  grid point nearest: 'Terrain.paved''s kinds; nought, for a terrain
  with no paving)."""
  if terrain.paved is None:
    return numpy.zeros(len(places), numpy.int8)
  key = id(terrain.paved)
  if key not in _PAVED:
    _PAVED.clear()
    _PAVED[key] = numpy.array(terrain.paved, numpy.int8)
  grid = _PAVED[key]
  i = numpy.rint((places[:, 0] - terrain.origin[0]) / terrain.cell)
  j = numpy.rint((places[:, 1] - terrain.origin[1]) / terrain.cell)
  inside = ((i >= 0) & (j >= 0) & (i < grid.shape[0])
            & (j < grid.shape[1]))
  out = numpy.zeros(len(places), numpy.int8)
  out[inside] = grid[i[inside].astype(int), j[inside].astype(int)]
  return out


#  The paving of terrains, kept by identity as arrays (the last one).
_PAVED: dict = {}


@functools.lru_cache(maxsize=256)
def _flatFaces(shape: object) -> tuple[tuple[int, ...], ...]:
  """Returns the faces of 'shape' as flat polygons: the triangles of a
  piece (faces sharing corners) lying in one plane joined, each
  polygon's corners around, anticlockwise seen from outside."""
  leader = list(range(len(shape.points)))

  def leaderOf(index: int) -> int:
    """Returns the least point joined to 'index' so far."""
    while leader[index] != index:
      index = leader[index]
    return index

  for face in shape.faces:
    least = min(leaderOf(index) for index in face)
    for index in face:
      leader[leaderOf(index)] = least
  planes: dict[tuple, tuple[tuple, set]] = {}
  for i, j, k in shape.faces:
    a, b, c = shape.points[i], shape.points[j], shape.points[k]
    facing = cross(minus(b, a), minus(c, a))
    size = norm(facing)
    if size == 0.0:
      continue
    normal = scaled(facing, 1.0 / size)
    key = (leaderOf(i),) + tuple(round(x, 9) for x in normal) + (
      round(dot(normal, a), 9),)
    planes.setdefault(key, (normal, set()))[1].update((i, j, k))
  out = []
  for normal, corners in planes.values():
    corners = sorted(corners)
    points = [shape.points[i] for i in corners]
    middle = scaled(points[0], 0.0)
    for point in points:
      middle = plus(middle, scaled(point, 1.0 / len(points)))
    start = max(points, key=lambda point: norm(minus(point, middle)))
    first = minus(start, middle)
    first = scaled(first, 1.0 / norm(first))
    second = cross(normal, first)
    out.append(tuple(sorted(corners, key=lambda i: math.atan2(
      dot(minus(shape.points[i], middle), second),
      dot(minus(shape.points[i], middle), first)))))
  return tuple(out)


@functools.lru_cache(maxsize=256)
def _topOf(shape: object) -> tuple[int, ...] | None:
  """Returns a shape's top as one of its '_flatFaces': the one of four
  corners all at its highest, in its own frame; None if none is."""
  high = max(point[2] for point in shape.points)
  for polygon in _flatFaces(shape):
    if len(polygon) == 4 and all(shape.points[i][2] >= high - 1e-9
                                 for i in polygon):
      return polygon
  return None


def _tilesOf(corners: list, tile: float, look: _Look) -> list[QPolygonF]:
  """Returns the dark squares, about 'tile' m, of a checker over the
  rectangle 'corners' (four, around) on the screen as 'look' sees it:
  the grid's points each seen once (None where behind the eye or past
  the guard band), a square of four seen taken so, any other cut on its
  own; one wholly behind the eye passed over (filled one by one, they
  are drawn quicker than as one path)."""
  a, b, _, d = corners
  along, across = minus(b, a), minus(d, a)
  count = max(1, round(norm(along) / tile))
  rows = max(1, round(norm(across) / tile))
  grid = [[plus(a, plus(scaled(along, u / count), scaled(across, v / rows)))
           for v in range(rows + 1)] for u in range(count + 1)]
  aheads = [[dot(minus(point, look.eye), look.forward) for point in column]
            for column in grid]
  shown = []
  for column, ahead in zip(grid, aheads):
    row = []
    for point, far in zip(column, ahead):
      seen = look.seen(point)[0] if far > look.near else None
      row.append(seen if seen is not None and look.inBand(seen) else None)
    shown.append(row)
  out = []
  for i in range(count):
    for j in range(rows):
      if (i + j) % 2:
        continue
      square = [shown[i][j], shown[i + 1][j], shown[i + 1][j + 1],
                shown[i][j + 1]]
      if all(point is not None for point in square):
        out.append(QPolygonF(square))
        continue
      if max(aheads[i][j], aheads[i + 1][j], aheads[i + 1][j + 1],
             aheads[i][j + 1]) <= look.near:
        continue
      cut = look.onScreen([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1],
                           grid[i][j + 1]])
      if cut is not None:
        out.append(QPolygonF(cut[0]))
  return out


def _cutTo(polygon: list, convex: list) -> list:
  """Returns the plane 'polygon' cut to the convex 'convex' (both
  around anticlockwise, Sutherland and Hodgman)."""
  out = polygon
  for at, start in enumerate(convex):
    end = convex[(at + 1) % len(convex)]
    if not out:
      return out
    kept = out
    out = []

    def inside(point: tuple) -> float:
      """Returns how far 'point' lies left of the edge."""
      return ((end[0] - start[0]) * (point[1] - start[1])
              - (end[1] - start[1]) * (point[0] - start[0]))

    for k, point in enumerate(kept):
      after = kept[(k + 1) % len(kept)]
      here, there = inside(point), inside(after)
      if here >= 0.0:
        out.append(point)
      if (here >= 0.0) != (there >= 0.0):
        share = here / (here - there)
        out.append((point[0] + share * (after[0] - point[0]),
                    point[1] + share * (after[1] - point[1])))
  return out


def _hullOf(points: list) -> list:
  """Returns the convex hull of the plane 'points', anticlockwise
  (Andrew's monotone chain)."""
  points = sorted(set(points))
  if len(points) < 3:
    return points

  def turn(o: tuple, a: tuple, b: tuple) -> float:
    """Returns how far 'o' 'a' 'b' turns anticlockwise."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

  lower, upper = [], []
  for point in points:
    while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= 0.0:
      lower.pop()
    lower.append(point)
  for point in reversed(points):
    while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= 0.0:
      upper.pop()
    upper.append(point)
  return lower[:-1] + upper[:-1]


def _lineOnScreen(start: tuple, end: tuple, look: _Look) -> tuple | None:
  """Returns the line from 'start' to 'end' on the screen as 'look' sees
  it, cut to what lies its 'near' or more ahead of the eye and to the
  guard band (as 'onScreen' cuts a polygon); None where nothing of it
  is left."""
  for normal, offset in ((look.forward, look.near),) + tuple(
      (side, 0.0) for side in look.sides):
    here = dot(minus(start, look.eye), normal) - offset
    there = dot(minus(end, look.eye), normal) - offset
    if here < 0.0 and there < 0.0:
      return None
    if here < 0.0 or there < 0.0:
      cut = plus(start, scaled(minus(end, start), here / (here - there)))
      start, end = (cut, end) if here < 0.0 else (start, cut)
  return look.seen(start)[0], look.seen(end)[0]


def _cutBy(corners: list, eye: tuple, normal: tuple,
           offset: float) -> list:
  """Returns the polygon 'corners' cut to the points p with (p - 'eye')
  . 'normal' at least 'offset' (Sutherland and Hodgman)."""
  out = []
  for at, point in enumerate(corners):
    after = corners[(at + 1) % len(corners)]
    here = dot(minus(point, eye), normal) - offset
    there = dot(minus(after, eye), normal) - offset
    if here >= 0.0:
      out.append(point)
    if (here >= 0.0) != (there >= 0.0):
      share = here / (here - there)
      out.append(plus(point, scaled(minus(after, point), share)))
  return out


def _sidesOf(right: tuple, up: tuple, forward: tuple, wide: float,
             high: float) -> tuple:
  """Returns the normals of the four planes through the eye bounding
  what it sees out to 'wide' across and 'high' up for each metre
  ahead: left, right, bottom, top, each facing in."""
  return (plus(right, scaled(forward, wide)),
          minus(scaled(forward, wide), right),
          plus(up, scaled(forward, high)),
          minus(scaled(forward, high), up))


class _Look:
  """_Look is the camera as a frame is painted: the 'eye', its 'right',
  'up' and 'forward', the view 'width' by 'height', its 'focal' length
  and 'middle', what lies nearer than 'near' ahead cut away; the guard
  band '_GUARD' half views either side
  ('bandX', 'bandY', pixels from the middle) and the four planes
  through the eye bounding it ('sides'); and the four bounding the view
  itself, a hair wider ('edges': what lies wholly outside one of them is
  not seen)."""

  def __init__(self, eye: tuple, right: tuple, up: tuple, forward: tuple,
               width: float, height: float, near: float) -> None:
    self.eye, self.right, self.up, self.forward = eye, right, up, forward
    self.near = near
    self.focal = 0.9 * min(width, height)
    self.middle = QPointF(0.5 * width, 0.5 * height)
    self.bandX, self.bandY = 0.5 * _GUARD * width, 0.5 * _GUARD * height
    self.sides = _sidesOf(right, up, forward, self.bandX / self.focal,
                          self.bandY / self.focal)
    self.edges = _sidesOf(right, up, forward,
                          0.51 * width / self.focal,
                          0.51 * height / self.focal)

  def seen(self, point: tuple) -> tuple:
    """The 'seen' method returns 'point' on the screen and how far ahead
    of the eye it is."""
    away = minus(point, self.eye)
    ahead = dot(away, self.forward)
    return QPointF(self.middle.x() + self.focal * dot(away, self.right)
                   / ahead,
                   self.middle.y() - self.focal * dot(away, self.up)
                   / ahead), ahead

  def inBand(self, point: QPointF) -> bool:
    """The 'inBand' method tells whether 'point' on the screen lies
    within the guard band."""
    return (abs(point.x() - self.middle.x()) <= self.bandX
            and abs(point.y() - self.middle.y()) <= self.bandY)

  def onScreen(self, corners: list) -> tuple | None:
    """The 'onScreen' method returns the polygon 'corners' as drawn and
    how far ahead its farthest part is: cut to what lies 'near' or more
    ahead of the eye, and where it reaches past the guard band, to the
    band; None when nothing of it is left."""
    cut = _cutBy(corners, self.eye, self.forward, self.near)
    if len(cut) < 3:
      return None
    shown = [self.seen(point) for point in cut]
    far = max(ahead for _, ahead in shown)
    points = [point for point, _ in shown]
    if all(self.inBand(point) for point in points):
      return points, far
    for normal in self.edges:
      if all(dot(minus(point, self.eye), normal) < 0.0 for point in cut):
        return None
    for normal in self.sides:
      cut = _cutBy(cut, self.eye, normal, 0.0)
      if len(cut) < 3:
        return None
    return [self.seen(point)[0] for point in cut], far
