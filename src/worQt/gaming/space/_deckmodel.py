"""
The reel-to-reel deck as the cabin draws it (user, 2026-11-16: "use
@previews/stereo reel to reel"; "it should prolly be off to the right
of Asger"): the model ('models/', CC-BY, 'models/CREDITS.md') read once,
its ground plane left out, scaled and set on its shelf on the wall at
his right, facing him, in the vessel's own axes; its still body by
material, its moving parts (each reel, the stop and play knob) about
where they turn; each material's look (glTF's linear colour made the
screen's, metal capped: full metal draws black without reflections,
the clear plastic see-through); its VU meters' picture as a file.
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
from pathlib import Path

import numpy

from ._cockpit import TAPE_AXES, TAPE_MODEL, TAPE_ORIGIN, TAPE_SCALE
from ._gltfmodel import GltfModel
from ._looks import cacheFolder

#  The model's file, its frame's node, the nodes left out.
MODEL_FILE = Path(__file__).parent / 'models' / TAPE_MODEL
FRAME_NODE = 'Tape Deck_Master'
LEFT_OUT = ('GroundPlane',)
#  In the model's frame: its reels' middles (on their spindles) and the
#  stop and play knob's (its node); how near a part's middle must be to
#  a reel's to turn with it, m; the part left still though there (the
#  tape's end leaving the pack); all turn about the model's z.
REEL_MIDDLES = ((-0.1802, 0.5487, 0.124), (0.2123, 0.5487, 0.124))
KNOB_NODE = 'Cylinder.004'
KNOB_MIDDLE = (-0.0469, 0.2115, 0.114)
ON_REEL = 0.012
STILL_ON_REEL = ('Magnetic Tape', 'Hub.004')
#  The most metal a material shows; how see-through clear plastic is
#  (of what is behind it, at most).
METAL_MOST = 0.3
CLEAR_SHOWS = 0.85


def vesselOf(local: tuple) -> tuple:
  """Returns the model's point 'local' in the vessel's own axes."""
  return tuple(o + TAPE_SCALE * sum(a[k] * local[j] for j, a in enumerate(
    TAPE_AXES)) for k, o in enumerate(TAPE_ORIGIN))


#  The deck's frame's z (its reels' and knob's axis) in the vessel's.
AXIS = TAPE_AXES[2]


@functools.lru_cache(maxsize=1)
def model() -> GltfModel:
  """Returns the model read (once)."""
  return GltfModel(MODEL_FILE)


@functools.lru_cache(maxsize=1)
def _sorted() -> dict:
  """Returns the model's parts in the vessel's axes, by what they are:
  'still' (by material), each reel's (by material), the knob's (by
  material), each as rows and triangles."""
  turn = numpy.array(TAPE_AXES).T
  origin = numpy.array(TAPE_ORIGIN)
  out = {'still': {}, 'reel0': {}, 'reel1': {}, 'knob': {}}
  for name, material, rows, triangles in model().parts(FRAME_NODE,
                                                       LEFT_OUT):
    middle = 0.5 * (rows[:, :3].min(0) + rows[:, :3].max(0))
    group = 'still'
    if name == KNOB_NODE:
      group = 'knob'
    elif name not in STILL_ON_REEL:
      for k, reel in enumerate(REEL_MIDDLES):
        if numpy.hypot(middle[0] - reel[0], middle[1] - reel[1]) < ON_REEL:
          group = 'reel%d' % k
    placed = rows.copy()
    placed[:, :3] = origin + TAPE_SCALE * rows[:, :3] @ turn.T
    placed[:, 3:6] = rows[:, 3:6] @ turn.T
    held = out[group].setdefault(material, ([], [], [0]))
    held[0].append(placed)
    held[1].append(triangles + held[2][0])
    held[2][0] += len(placed)
  return {group: {material: (numpy.concatenate(rows),
                             numpy.concatenate(triangles))
                  for material, (rows, triangles, _) in parts.items()}
          for group, parts in out.items()}


def stillParts() -> list:
  """Returns the deck's still body: each material's index and its rows
  and triangles."""
  return sorted(_sorted()['still'].items(), key=_order)


@functools.lru_cache(maxsize=1)
def movingParts() -> tuple:
  """Returns the deck's moving parts (worked out once: the scenery asks
  for each pivot every frame): each (what: 'reel', its index, or 'knob',
  0), its material, its pivot (vessel's axes) and its rows (about the
  pivot) and triangles."""
  out = []
  pivots = {'reel0': ('reel', 0, vesselOf(REEL_MIDDLES[0])),
            'reel1': ('reel', 1, vesselOf(REEL_MIDDLES[1])),
            'knob': ('knob', 0, vesselOf(KNOB_MIDDLE))}
  for group, (kind, index, pivot) in pivots.items():
    for material, (rows, triangles) in sorted(_sorted()[group].items(),
                                              key=_order):
      about = rows.copy()
      about[:, :3] -= numpy.array(pivot)
      about.flags.writeable = False
      out.append((kind, index, material, pivot, about, triangles))
  return tuple(out)


def _order(item: tuple) -> int:
  """Returns where a material's part comes (no material first)."""
  return -1 if item[0] is None else item[0]


def lookOf(material: int | None) -> tuple:
  """Returns material 'material''s look: its colour (0 to 255, the
  screen's), metalness (capped), roughness, how opaque, and whether it
  has a picture (the VU meters')."""
  held = model().material(material)
  colour = tuple(int(round(255.0 * _screen(c))) for c in held['colour'])
  clear = held['clear']
  if clear > 0.0:
    colour = (236, 240, 244)
  return (colour, min(METAL_MOST, float(held['metal'])),
          float(held['rough']), 1.0 - CLEAR_SHOWS * clear,
          held['picture'] is not None)


def _screen(linear: float) -> float:
  """Returns a linear colour's share as the screen's (sRGB)."""
  if linear <= 0.0031308:
    return 12.92 * linear
  return 1.055 * linear ** (1.0 / 2.4) - 0.055


def pictureFile() -> Path:
  """Returns the VU meters' picture as a file in the looks' cache
  (written the first time)."""
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  target = folder / 'tapedeck-vu.png'
  if not target.exists():
    target.write_bytes(model().picture(0))
  return target
