"""
SaveGame is a game of space travel kept on disk (user, 2026-11-17: "Add
a note that we need a save/load system"; 2026-11-18: "Also implement
the save load system now"): what changes as it is played, each class
holding some declaring it ('SAVED': the names of its fields that are
its state; 'PARTS': the names of its parts that hold some), taken as
plain values ('keptOf'), written as JSON, read and put back into the
same objects ('keptTo'). The sky is its bodies' paths and turns
('skyOf', 'skyTo'). What is only counted for the sound (thuds, clicks,
meals) is not kept: the sound plays what grows. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from ._conic import Conic

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem

#  A save says which way it was written; another way is not read (2:
#  Terra Prime's two ports, the docking port's 'side').
SAVE_VERSION = 2
#  The quick save's file in the saves' folder (F5 writes it, F9 reads
#  it).
QUICK = 'quicksave.json'


def savesFolder() -> Path:
  """Returns the folder the saves are kept in ('XDG_DATA_HOME', else
  '~/.local/share', then 'worQt/space'), made if it is not there."""
  home = os.environ.get('XDG_DATA_HOME') or str(
    Path.home() / '.local' / 'share')
  folder = Path(home) / 'worQt' / 'space'
  folder.mkdir(parents=True, exist_ok=True)
  return folder


def keptOf(thing: object) -> dict:
  """Returns what 'thing' keeps ('SAVED': its fields; 'PARTS': its
  parts, each kept so too) as plain values."""
  out = {name: _plain(getattr(thing, name)) for name in type(thing).SAVED}
  for part in getattr(type(thing), 'PARTS', ()):
    out[part] = keptOf(getattr(thing, part))
  return out


def keptTo(thing: object, kept: dict) -> None:
  """Puts what 'kept' says back into 'thing' (as 'keptOf' took it):
  every field it declares and its parts'. Raises if one is missing."""
  for name in type(thing).SAVED:
    if name not in kept:
      raise KeyError('the save has no %r for %s' % (
        name, type(thing).__name__))
    setattr(thing, name, _back(kept[name]))
  for part in getattr(type(thing), 'PARTS', ()):
    if part not in kept:
      raise KeyError('the save has no %r for %s' % (
        part, type(thing).__name__))
    keptTo(getattr(thing, part), kept[part])


def skyOf(system: SolarSystem) -> list:
  """Returns where the sky is: each body's and satellite's name, path
  (its conic's numbers; None: Sol's), turn and pole."""
  out = []
  for body in tuple(system.bodies) + tuple(system.satellites):
    conic = body.conic
    path = None if conic is None else [
      conic.mu, conic.a, conic.e, conic.i, conic.node, conic.peri,
      conic.anomaly]
    out.append([body.name, path, body.angle, list(body.pole)])
  return out


def skyTo(system: SolarSystem, sky: list) -> None:
  """Puts the sky 'skyOf' took back into 'system' (the same bodies and
  satellites, in their order: raises if not), its time anew."""
  bodies = tuple(system.bodies) + tuple(system.satellites)
  if [body.name for body in bodies] != [row[0] for row in sky]:
    raise ValueError('the save\'s sky has %s, this one %s' % (
      [row[0] for row in sky], [body.name for body in bodies]))
  for body, (_, path, angle, pole) in zip(bodies, sky):
    body.restored(None if path is None else Conic(*path), angle,
                  tuple(pole))
  system.version += 1


class SaveGame:
  """
  SaveGame is one save: the game's 'state' (plain values: JSON's
  types) and when it was saved ('saved', UTC). 'written' writes it to a
  file at once (written aside first, then put in place: a save cut off
  never spoils the last); 'read' reads one (a save of another version
  raises).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  state: dict
  saved: datetime

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, state: dict, saved: datetime = None) -> None:
    self.state = dict(state)
    self.saved = saved or datetime.now(timezone.utc)

  @classmethod
  def read(cls, path: Path) -> SaveGame:
    """The 'read' method returns the save in the file at 'path'."""
    with open(path, 'r', encoding='utf-8') as file:
      data = json.load(file)
    version = data.get('version')
    if version != SAVE_VERSION:
      raise ValueError('%s is a save of version %r; this game reads %d'
                       % (path, version, SAVE_VERSION))
    return cls(data['state'], datetime.fromisoformat(data['saved']))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def written(self, path: Path) -> None:
    """The 'written' method writes the save to the file at 'path'."""
    path = Path(path)
    aside = path.with_name(path.name + '.part')
    with open(aside, 'w', encoding='utf-8') as file:
      json.dump({'version': SAVE_VERSION, 'saved': self.saved.isoformat(),
                 'state': self.state}, file)
      file.flush()
      os.fsync(file.fileno())
    os.replace(aside, path)


def _plain(value: object) -> object:
  """Returns 'value' as JSON's types: a tuple as a list, a list, a set
  and a dict tagged ('list', 'set', 'dict'; a dict's keys words);
  numbers, words, truths and None as they are. Anything else raises."""
  if value is None or isinstance(value, (bool, int, str)):
    return value
  if isinstance(value, float):
    if not math.isfinite(value):
      return {'float': repr(value)}
    return value
  if isinstance(value, tuple):
    return [_plain(v) for v in value]
  if isinstance(value, list):
    return {'list': [_plain(v) for v in value]}
  if isinstance(value, (set, frozenset)):
    return {'set': [_plain(v) for v in sorted(value)]}
  if isinstance(value, dict):
    for key in value:
      if not isinstance(key, str):
        raise TypeError('a saved dict\'s keys are words, not %r' % (key,))
    return {'dict': {k: _plain(v) for k, v in value.items()}}
  raise TypeError('cannot save a %s: %r' % (type(value).__name__, value))


def _back(value: object) -> object:
  """Returns what '_plain' made of a value as it was."""
  if isinstance(value, list):
    return tuple(_back(v) for v in value)
  if isinstance(value, dict):
    if len(value) != 1:
      raise ValueError('not a saved value: %r' % (value,))
    (tag, inner), = value.items()
    if tag == 'list':
      return [_back(v) for v in inner]
    if tag == 'set':
      return {_back(v) for v in inner}
    if tag == 'dict':
      return {k: _back(v) for k, v in inner.items()}
    if tag == 'float':
      return float(inner)
    raise ValueError('not a saved value: %r' % (value,))
  return value
