"""
The gravity gun Asger holds out of his chair (user, 2026-11-17: "he then
uses the gravity gun from temu to yeet himself across the room"; "The
gravity gun can pull Asger towards them" [the magic bolts]): the
sandbox's gun as the sandbox holds it, laid in his eyes' frame (right,
up, back: its grip in his hand low on the right, its barrel ahead).
The sandbox's model when its file is there ('models/gravitygun.glb',
kept out of git: no licence stated), its look and picture (a file in
the looks' cache); else the sandbox's gun of boxes. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from worQt.gaming.sandbox._gravitygun import MODEL_FILE, MODEL_GRIP
from worQt.gaming.sandbox._gravitygun import MODEL_SIZE, PARTS
from worQt.gaming.sandbox._tool import GRIP

from ._gltfmodel import GltfModel
from ._looks import cacheFolder
from ._shapes import boxRows

#  Full metal draws black with nothing to mirror: as the deck's, capped.
METAL_MOST = 0.3
#  Its 3: at most this big (half its size), this far off its side, m.
SIDE_MARK_MOST = 0.06
SIDE_MARK_OFF = 0.003


@functools.lru_cache(maxsize=1)
def gunParts() -> tuple:
  """Returns the gun's meshes in his eyes' frame: each its look (colour
  0 to 255, metalness, roughness), its picture ('' none), its rows and
  triangles."""
  if MODEL_FILE.exists():
    return _modelParts()
  return _boxParts()


def _modelParts() -> tuple:
  """Returns the sandbox's model of the gun, each primitive a part."""
  model = GltfModel(MODEL_FILE)
  out = []
  for _, material, rows, triangles in model.parts(None, ()):
    held = model.material(material)
    colour = tuple(int(round(255.0 * _screen(c))) for c in held['colour'])
    look = (colour, min(METAL_MOST, float(held['metal'])),
            float(held['rough']))
    picture = '' if held['picture'] is None else str(
      _pictureFile(model, held['picture']))
    out.append((look, picture, _inEyes(rows), triangles))
  return tuple(out)


def _inEyes(rows: numpy.ndarray) -> numpy.ndarray:
  """Returns the model's rows laid in the eyes' frame as the sandbox
  lays them: turned so its x runs back (its barrel, along -x, ahead),
  its z left, scaled 'MODEL_SIZE', its grip 'MODEL_GRIP' in the hand at
  'GRIP'."""
  out = numpy.array(rows, numpy.float64)
  x, y, z = (out[:, k] - MODEL_GRIP[k] for k in range(3))
  out[:, 0] = GRIP[0] - MODEL_SIZE * z
  out[:, 1] = GRIP[1] + MODEL_SIZE * y
  out[:, 2] = GRIP[2] + MODEL_SIZE * x
  nx, ny, nz = rows[:, 3].copy(), rows[:, 4].copy(), rows[:, 5].copy()
  out[:, 3], out[:, 4], out[:, 5] = -nz, ny, nx
  return out


def _boxParts() -> tuple:
  """Returns the sandbox's gun of boxes, each box a part (no picture)."""
  out = []
  for size, middle, along, colour in PARTS:
    out.append(((tuple(colour), 0.2, 0.5), '') + boxRows(
      middle, tuple(0.5 * s for s in size), _axesAlong(along)))
  return tuple(out)


def _axesAlong(along: tuple) -> tuple:
  """Returns a box's axes with its own z 'along' (the eyes' frame): its
  x kept level, right-handed."""
  size = math.sqrt(sum(a * a for a in along))
  out = tuple(a / size for a in along)
  right = (out[2], 0.0, -out[0])
  across = math.hypot(right[0], right[2])
  right = (1.0, 0.0, 0.0) if across < 1e-9 else (right[0] / across, 0.0,
                                                  right[2] / across)
  up = (out[1] * right[2] - out[2] * right[1],
        out[2] * right[0] - out[0] * right[2],
        out[0] * right[1] - out[1] * right[0])
  return right, up, out


def _pictureFile(model: GltfModel, index: int) -> object:
  """Returns the model's picture 'index' as a file in the looks' cache
  (written the first time; a PNG's or a JPEG's ending as it is)."""
  data = model.picture(index)
  kind = 'png' if data[:8] == b'\x89PNG\r\n\x1a\n' else 'jpg'
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  target = folder / ('gravitygun-%d.%s' % (index, kind))
  if not target.exists():
    target.write_bytes(data)
  return target


def _screen(linear: float) -> float:
  """Returns a linear colour's share as the screen's (sRGB)."""
  if linear <= 0.0031308:
    return 12.92 * linear
  return 1.055 * linear ** (1.0 / 2.4) - 0.055


@functools.lru_cache(maxsize=1)
def sideMark() -> tuple:
  """Returns where the gun's 3 is painted (user, 2026-11-17: "give a
  more prominent 3 on the side. where it is visible"): on its left side,
  the one he sees, a hair off it: its middle (his eyes' frame) and half
  its size, m."""
  rows = numpy.concatenate([part[2][:, :3] for part in gunParts()])
  low, high = rows.min(axis=0), rows.max(axis=0)
  half = min(SIDE_MARK_MOST, 0.45 * float(high[1] - low[1]))
  return ((float(low[0]) - SIDE_MARK_OFF, 0.5 * float(low[1] + high[1]),
           0.5 * float(low[2] + high[2])), half)
