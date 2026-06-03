"""
Reads and writes a 'CADScene' as JSON, without pickling. Each item is
stored as its kind name and its list of '(x, y)' vertices - the very pair
that 'describeItem' and 'buildItem' already round-trip - so a saved drawing
is a plain, legible list of coordinates that any tool can read, and every
item is rebuilt from scratch through the factory rather than unpickled.

The on-disk shape is:

    {"version": 1, "items": [{"kind": "Module",
                              "vertices": [[0.0, 0.0], [1.0, 0.0]]}, ...]}
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ._scene import CADScene
from ._items import Member
from ._factory import describeItem, buildItem, itemAttrs, applyAttrs

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

#  Bumped when the on-disk shape changes incompatibly.
__format_version__ = 1


def sceneToData(scene: CADScene) -> dict:
  """
  Return a plain, JSON-serialisable structure for every item in 'scene'. Most
  items store their kind and '(x, y)' vertices (plus 'attrs'); a member,
  being reference-based, instead stores the scene indices of its two anchor
  nodes ('{"kind": "Member", "nodes": [i, j]}').
  """
  items = list(scene)
  index = {id(item): i for i, item in enumerate(items)}
  out = []
  for item in items:
    if isinstance(item, Member):
      out.append({'kind': 'Member',
                  'nodes': [index[id(item.nodeA)], index[id(item.nodeB)]]})
      continue
    kind, vertices = describeItem(item)
    entry = {
      'kind': kind,
      'vertices': [[float(x), float(y)] for x, y in vertices],
    }
    attrs = itemAttrs(item)
    if attrs:  # only stored when present, to keep the file minimal
      entry['attrs'] = attrs
    out.append(entry)
  return {'version': __format_version__, 'items': out}


def sceneFromData(data: dict, scene: CADScene = None) -> CADScene:
  """
  Rebuild a 'CADScene' from a 'sceneToData' structure. Built in two passes -
  vertex items first, then members resolving their node indices to the
  rebuilt anchors - so member references survive the round-trip. A malformed
  entry raises before 'scene' is touched. When 'scene' is given it is cleared
  and refilled in place (keeping its identity); else a fresh one is returned.
  """
  entries = data.get('items', [])
  built = [None] * len(entries)
  for i, entry in enumerate(entries):  # pass 1: everything except members
    if entry['kind'] == 'Member':
      continue
    vertices = [(float(x), float(y)) for x, y in entry['vertices']]
    item = buildItem(entry['kind'], vertices)
    applyAttrs(item, entry.get('attrs', {}))
    built[i] = item
  for i, entry in enumerate(entries):  # pass 2: members by node index
    if entry['kind'] != 'Member':
      continue
    a, b = entry['nodes']
    built[i] = Member(built[a], built[b])
  if scene is None:
    scene = CADScene()
  else:
    scene.clear()
  for item in built:
    scene.addItem(item)
  return scene


def sceneToJson(scene: CADScene) -> str:
  """Serialise 'scene' to a JSON string."""
  return json.dumps(sceneToData(scene))


def sceneFromJson(text: str, scene: CADScene = None) -> CADScene:
  """Rebuild a 'CADScene' from the JSON string 'text'."""
  return sceneFromData(json.loads(text), scene)


def saveScene(scene: CADScene, path: str) -> None:
  """Write 'scene' to the file at 'path' as JSON."""
  with open(path, 'w') as file:
    file.write(sceneToJson(scene))


def loadScene(path: str, scene: CADScene = None) -> CADScene:
  """Read the JSON drawing at 'path' into a 'CADScene' and return it."""
  with open(path, 'r') as file:
    return sceneFromJson(file.read(), scene)
