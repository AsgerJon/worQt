"""
TestZFight covers drawn surfaces fighting (user, 2026-11-19: "There are
still colliding geometreis that fight in the renderer which looks
awfule. I thought we had a tool that systematically ensured that no
such collissoins occurred?"; "around the doorways in the tower. Like
into the staircase and the elveator"; "The entrance to the Terra Prime
center is dogshit. It has colliding geometries and just remain closed";
then the three levels, the rocket's head in Terra Prime's drum): the
launch tower's meshes fight nowhere; the rocket's head (its skin, its
levels' walls, floors and ceilings, the ladder, the lamp rings, its four
doors' leaves open) docked in the drum (the station's skin, the hole's
wall, its shafts, the sleeves, all laid in the docked rocket's axes)
fights nowhere; the way up beside the ladder through the hatches, and
out of the top floor through each door into its shaft, is clear.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.space._cabin import capsuleShell, floorRows
from worQt.gaming.space._dashboard import pieceRows
from worQt.gaming.space._interiormeshes import interiorMeshes
from worQt.gaming.space._ladder import ladderRows
from worQt.gaming.space._levels import CEILING, DOOR_WAYS, LEVELS
from worQt.gaming.space._levels import ROOF
from worQt.gaming.space._shaftdoor import POCKET
from worQt.gaming.space._stationinterior import PLANE, stationPoint
from worQt.gaming.space._stationlamps import ringAt
from worQt.gaming.space._stationmeshes import stationMeshes
from worQt.gaming.space._turns import aboutAxis, rotated
from worQt.gaming.space._walkwaymeshes import towerParts
from worQt.gaming.space._zfight import fightsOf

from . import SpaceTest

#  Docked from the station's +z side: the rocket's axes in the
#  station's.
RELATIVE = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
#  The head's region (the docked rocket's axes): round the axis, from
#  under the cabin's ceiling to past the drum, m.
AROUND = 10.0
LOW, HIGH = CEILING - 1.0, ROOF + 6.0


def _stationLaid(rows: numpy.ndarray) -> numpy.ndarray:
  """Returns a station mesh's rows in the docked rocket's axes (as
  'stationPoint' and 'stationWay' lay each, all at once)."""
  out = numpy.array(rows, numpy.float64)
  turn = numpy.array(RELATIVE, numpy.float64)
  middle = numpy.array(stationPoint((0.0, 0.0, 0.0), RELATIVE))
  out[:, :3] = out[:, :3] @ turn.T + middle
  out[:, 3:6] = out[:, 3:6] @ turn.T
  return out


def _turned(rows: numpy.ndarray, angle: float) -> numpy.ndarray:
  """Returns a mesh's rows turned 'angle' about the rocket's axis."""
  turn = aboutAxis((0.0, 0.0, 1.0), angle)
  out = numpy.array(rows, numpy.float64)
  for k in range(len(out)):
    out[k, :3] = rotated(turn, tuple(out[k, :3]))
    out[k, 3:6] = rotated(turn, tuple(out[k, 3:6]))
  return out


def _near(rows: numpy.ndarray, faces: numpy.ndarray) -> tuple:
  """Returns the triangles of a mesh in the entrance's region."""
  rows = numpy.asarray(rows)
  tri = numpy.asarray(faces).reshape(-1, 3)
  middle = rows[tri][:, :, :3].mean(axis=1)
  keep = ((numpy.hypot(middle[:, 0], middle[:, 1]) < AROUND)
          & (middle[:, 2] > LOW) & (middle[:, 2] < HIGH))
  return rows, tri[keep].reshape(-1)


def entranceMeshes() -> list:
  """Returns the docked head's meshes: (name, rows, faces)."""
  out = [('skin', *capsuleShell(False)), ('walls', *capsuleShell(True)),
         ('floors', *floorRows()), ('ladder', *ladderRows())]
  for k in range(len(DOOR_WAYS)):
    rows, faces = pieceRows(('shaft door', k), {})
    out.append(('leaf %d' % k, _turned(rows, POCKET), faces))
  for level in (1, 2):
    rows, faces = pieceRows(('level lamp', level), {})
    rows = numpy.array(rows, numpy.float64)
    rows[:, :3] += ringAt(level)
    out.append(('lamps %d' % level, rows, faces))
  for name, (rows, faces) in stationMeshes().items():
    out.append(('station ' + name, _stationLaid(rows), faces))
  for name, (rows, faces) in interiorMeshes().items():
    out.append(('inside ' + name, _stationLaid(rows), faces))
  return [(name, *_near(rows, faces)) for name, rows, faces in out]


def _hits(meshes: list, start: tuple, end: tuple) -> list:
  """Returns the meshes the line from 'start' to 'end' meets (each its
  name and how far along, m)."""
  origin = numpy.array(start, numpy.float64)
  way = numpy.array(end, numpy.float64) - origin
  long = float(numpy.linalg.norm(way))
  way /= long
  out = []
  for name, rows, faces in meshes:
    rows = numpy.asarray(rows, numpy.float64)[:, :3]
    tri = rows[numpy.asarray(faces).reshape(-1, 3)]
    if not len(tri):
      continue
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    e1, e2 = b - a, c - a
    p = numpy.cross(way, e2)
    det = numpy.einsum('ij,ij->i', e1, p)
    ok = numpy.abs(det) > 1e-12
    inv = numpy.where(ok, 1.0 / numpy.where(ok, det, 1.0), 0.0)
    s = origin - a
    u = numpy.einsum('ij,ij->i', s, p) * inv
    q = numpy.cross(s, e1)
    v = (q @ way) * inv
    t = numpy.einsum('ij,ij->i', e2, q) * inv
    met = ok & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0) & (t > 0.0) & (
      t < long)
    out += [(name, float(x)) for x in t[met]]
  return sorted(out, key=lambda hit: hit[1])


class TestZFight(SpaceTest):
  """Tests for surfaces fighting in the renderer."""

  def test_tower(self) -> None:
    """The launch tower (its walls round the stairs' and the lift's
    doorways, the hall, the steel tower) fights nowhere."""
    fights = fightsOf([(look, rows, faces) for look, (rows, faces)
                       in towerParts().items()])
    self.assertEqual(fights, [], '\n'.join(map(repr, fights[:12])))

  def test_entrance(self) -> None:
    """Docked, the head's and the drum's meshes fight nowhere."""
    fights = fightsOf(entranceMeshes())
    self.assertEqual(fights, [], '\n'.join(map(repr, fights[:12])))

  def test_way_up(self) -> None:
    """Lines up beside the ladder (off it, within the hatches' room) meet
    nothing from over the cabin's floor to under the top floor's
    ceiling; lines out of the top floor along each door's way (on its
    middle and off it, within the doorway) meet nothing to well down the
    shaft."""
    meshes = entranceMeshes()
    for out in (0.3, 0.6):
      for angle in (0.0, 1.3, 2.6, 3.9, 5.2):
        x, y = out * math.cos(angle), out * math.sin(angle)
        hits = _hits(meshes, (x, y, CEILING - 0.9), (x, y,
                                                     LEVELS[2][1] - 0.1))
        self.assertEqual(hits, [], (out, angle, hits[:4]))
    for way in DOOR_WAYS:
      side = (-way[1], way[0], 0.0)
      for off, up in ((0.0, 0.0), (0.4, 0.6), (-0.4, -0.8)):
        start = tuple(1.0 * w + off * s for w, s in zip(way, side))
        end = tuple(9.0 * w + off * s for w, s in zip(way, side))
        hits = _hits(meshes, start[:2] + (PLANE + up,), end[:2] + (
          PLANE + up,))
        self.assertEqual(hits, [], (way, off, up, hits[:4]))
