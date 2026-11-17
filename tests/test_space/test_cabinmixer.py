"""
TestCabinMixer covers the space window's sound (user, 2026-11-16: "all
of the inputs and outputs should have appropriate clicky sounds"; "The
rocket should have a proper sound that reduces to ambience inside the
cabin, but is full and cool on the third person"): the engine loud
outside and a quiet rumble inside, silence with the engine shut
outside, a click as a count grows, the tape played from its beginning
each time it was rewound, every sample within one.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.gaming.space import _cabinmixer as mixer
from worQt.gaming.space._cabinmixer import CabinMixer
from worQt.gaming.space._tapedeck import LEAD_IN

from . import SpaceTest

RATE, BLOCK = 48000, 1024
#  The engine at full throttle in thick air; the tape playing, rewound.
ROAR = ((mixer.ENGINE, 1.0), (mixer.AIR, 1.0))
REPLAY = ((mixer.DECK, 1.0), (mixer.REWINDS, 1.0))


def _told(*pairs: tuple) -> list:
  """Returns what the mixer is told: the volume whole, the rest as
  'pairs' give them (each its place in the list, its number)."""
  out = [0.0] * mixer.TOLD
  out[mixer.VOLUME] = 1.0
  for place, value in pairs:
    out[place] = value
  return out


def _played(mix: CabinMixer, told: list, seconds: float) -> numpy.ndarray:
  """Returns 'seconds' of 'mix''s sound as 'told'."""
  blocks = [mix.samples(told, BLOCK)
            for _ in range(int(seconds * RATE / BLOCK))]
  return numpy.concatenate(blocks)


def _loudness(sound: numpy.ndarray) -> float:
  """Returns how loud 'sound' is (its root mean square)."""
  return float(numpy.sqrt(numpy.mean(sound * sound)))


class TestCabinMixer(SpaceTest):
  """Tests for 'CabinMixer'."""

  def test_engine(self) -> None:
    """At full throttle the engine is at least three times as loud
    outside as in; every sample within one."""
    outside = CabinMixer(RATE, 1)
    _played(outside, _told(*ROAR), 1.0)
    loud = _played(outside, _told(*ROAR), 1.0)
    inside = CabinMixer(RATE, 1)
    _played(inside, _told(*ROAR, (mixer.INSIDE, 1.0)), 1.0)
    rumble = _played(inside, _told(*ROAR, (mixer.INSIDE, 1.0)), 1.0)
    self.assertGreater(_loudness(loud), 3.0 * _loudness(rumble))
    self.assertGreater(_loudness(rumble), 0.01)
    self.assertLessEqual(float(numpy.max(numpy.abs(loud))), 1.0)

  def test_quiet(self) -> None:
    """Outside with the engine shut and nothing worked it is silent;
    inside the cabin hums, softly."""
    outside = CabinMixer(RATE, 2)
    _played(outside, _told(), 1.0)
    self.assertLess(_loudness(_played(outside, _told(), 0.5)), 1e-3)
    inside = CabinMixer(RATE, 2)
    hum = _loudness(_played(inside, _told((mixer.INSIDE, 1.0)), 0.5))
    self.assertGreater(hum, 1e-3)
    self.assertLess(hum, 0.03)

  def test_clicks(self) -> None:
    """A count grown plays its sound once; the counts first heard are
    taken as they are; the teleprinter's are nearly inaudible (its
    loudest under a fifth of the quietest input's)."""
    loudest = {}
    for name in ('CLICKS', 'SNAPS', 'TICKS', 'RELAYS', 'TYPED',
                 'RETURNS', 'BELLS'):
      place = getattr(mixer, name)
      mix = CabinMixer(RATE, 3)
      _played(mix, _told((place, 5.0)), 1.0)
      first = _played(mix, _told((place, 5.0)), 0.2)
      self.assertLess(float(numpy.max(numpy.abs(first))), 1e-3, name)
      shot = _played(mix, _told((place, 6.0)), 0.2)
      loudest[name] = float(numpy.max(numpy.abs(shot)))
      self.assertGreater(loudest[name], 2e-3, name)
      after = _played(mix, _told((place, 6.0)), 2.0)[-BLOCK:]
      self.assertLess(float(numpy.max(numpy.abs(after))), 1e-3, name)
    inputs = min(loudest[name] for name in ('CLICKS', 'SNAPS', 'TICKS'))
    printer = max(loudest[name] for name in ('TYPED', 'RETURNS', 'BELLS'))
    self.assertLess(printer, 0.2 * inputs)

  def test_crash(self) -> None:
    """A hit on the station booms once, louder than the latch, as loud
    as it was hard; within one."""
    loud = {}
    for hard in (0.5, 3.0):
      mix = CabinMixer(RATE, 4)
      _played(mix, _told((mixer.CRASHES, 1.0)), 0.5)
      shot = _played(mix, _told((mixer.CRASHES, 2.0),
                                (mixer.CRASH, hard)), 1.0)
      loud[hard] = _loudness(shot)
      self.assertLessEqual(float(numpy.max(numpy.abs(shot))), 1.0)
    self.assertGreater(loud[3.0], 1.5 * loud[0.5])
    mix = CabinMixer(RATE, 4)
    _played(mix, _told((mixer.DOCKS, 1.0)), 0.5)
    latch = _loudness(_played(mix, _told((mixer.DOCKS, 2.0)), 1.0))
    self.assertGreater(loud[3.0], latch)

  def test_announced(self) -> None:
    """Announced, the deck clicks itself ready (loud, no tape) for
    'LEAD_IN' s and falls quiet; announced again, clicking, then the
    music starting: the clicks stop at once."""
    mix = CabinMixer(RATE, 5)
    mix._decoding.join()
    mix.tape = numpy.full(10 * RATE, 0.01)
    _played(mix, _told(), 0.1)
    clicks = _played(mix, _told((mixer.ANNOUNCED, 1.0)), LEAD_IN)
    self.assertGreater(float(numpy.max(numpy.abs(clicks))), 0.2)
    self.assertEqual(mix.tapeAt, 0)
    after = _played(mix, _told((mixer.ANNOUNCED, 1.0)), 0.5)[-BLOCK:]
    self.assertLess(float(numpy.max(numpy.abs(after))), 1e-3)
    _played(mix, _told((mixer.ANNOUNCED, 2.0)), 0.3)
    music = _played(mix, _told((mixer.ANNOUNCED, 2.0), (mixer.DECK, 1.0)),
                    0.5)[-BLOCK:]
    self.assertLess(float(numpy.max(numpy.abs(music))), 0.02)
    self.assertGreater(mix.tapeAt, 0)

  def test_tape(self) -> None:
    """The tape plays while the deck does, at once; on from where it
    stood after a stop, from its beginning after a rewind, faded in and
    out."""
    mix = CabinMixer(RATE, 4)
    mix._decoding.join()
    mix.tape = numpy.linspace(0.0, 1.0, 10 * RATE)
    _played(mix, _told(), 0.1)
    self.assertEqual(mix.tapeAt, 0)
    _played(mix, _told((mixer.DECK, 1.0)), 1.0)
    at = mix.tapeAt
    self.assertGreater(at, 0.9 * RATE)
    _played(mix, _told(), 1.0)
    stood = mix.tapeAt
    self.assertEqual(mix.tapeGain, 0.0)
    self.assertLess(stood - at, 0.8 * RATE)
    _played(mix, _told(*REPLAY), 0.1)
    self.assertLess(mix.tapeAt, 0.2 * RATE)
    sound = _played(mix, _told(*REPLAY), 1.0)
    self.assertGreater(_loudness(sound), 0.01)

  def test_food_near(self) -> None:
    """The kitchen's music, begun, plays as loud as he is near the food
    (user, 2026-11-17: "when walking away from the food area fade out
    the audible France"): out of earshot nothing of it."""
    sound = numpy.sin(numpy.arange(RATE) * 0.05)
    loudness = []
    for near in (1.0, 0.0):
      heard = []
      for music in (sound, 0.0 * sound):
        mix = CabinMixer(RATE, 1)
        mix.records[mixer.EATS][0] = music
        _played(mix, _told((mixer.FOOD_NEAR, near)), 1.5)
        heard.append(_played(mix, _told((mixer.EATS, 1.0),
                                        (mixer.FOOD_NEAR, near)), 0.5))
      loudness.append(_loudness(heard[0] - heard[1]))
    self.assertGreater(loudness[0], 0.2)
    self.assertLess(loudness[1], 0.01)
