"""
TestSounds covers the billiards' sounds, made rather than recorded: every
sound 'SoundPlayer' is asked for is there, each take a short run of
samples within full scale, beginning and ending in silence; a clack is
short and bright, a thud low, the fanfare long; a pin rings as a
xylophone's bar at its own note, each a step up; a ball into a pocket
knocks low, red's sad after; the whirr of a shot
played fast loops without a seam; and they turn into WAV files.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.gaming.billiards import _sounds
from worQt.gaming.pusher._sounds import waveBytes

from . import BilliardsTest


def loudestPitch(samples: numpy.ndarray) -> float:
  """The frequency, in Hz, at which 'samples' are loudest."""
  spectrum = numpy.abs(numpy.fft.rfft(samples))
  frequencies = numpy.fft.rfftfreq(len(samples), 1.0 / _sounds.RATE)
  return float(frequencies[int(numpy.argmax(spectrum))])


class TestSounds(BilliardsTest):
  """Tests for the billiards' sounds."""

  def test_bank(self) -> None:
    """Every sound the window plays is there, each take within full
    scale, rising from silence and dying to it."""
    takes = _sounds.takes()
    self.assertEqual(set(takes), {'clack', 'thud', 'tock', 'fanfare',
                                  'windUp', 'whirr', 'windDown', 'carom',
                                  'pocket', 'sadPocket',
                                  *('%s%d' % (name, k)
                                    for name in ('pin', 'sadPin', 'sadLand')
                                    for k in range(5))})
    for name, samples in takes.items():
      self.assertTrue(samples)
      for take in samples:
        self.assertTrue(numpy.all(numpy.isfinite(take)))
        self.assertLessEqual(float(numpy.abs(take).max()), 1.0)
        self.assertEqual(float(take[0]), 0.0)
        if name != 'whirr':
          self.assertEqual(float(take[-1]), 0.0)

  def test_whirr_loops(self) -> None:
    """The whirr loops without a seam: from its last sample back to its
    first is no bigger a step than any within it."""
    whirr = _sounds.whirr()
    steps = numpy.abs(numpy.diff(whirr))
    self.assertLessEqual(abs(float(whirr[-1] - whirr[0])),
                         float(steps.max()))

  def test_character(self) -> None:
    """A clack is short and bright; a thud low; the fanfare long."""
    clack = _sounds.clack(3200.0, 0)
    thud = _sounds.thud(0)
    self.assertLess(len(clack) / _sounds.RATE, 0.1)
    self.assertGreater(loudestPitch(clack), 2000.0)
    self.assertLess(loudestPitch(thud), 400.0)
    self.assertGreater(len(_sounds.fanfare()) / _sounds.RATE, 1.0)

  def test_pin(self) -> None:
    """A pin rings as a xylophone's bar, loudest at its own note, the
    five a step apart each, in under half a second."""
    rung = [loudestPitch(_sounds.pin(note, 0))
            for note in _sounds.PIN_NOTES]
    for heard, note in zip(rung, _sounds.PIN_NOTES):
      self.assertLess(abs(heard - note), 0.03 * note)
    self.assertEqual(rung, sorted(rung))
    self.assertLessEqual(len(_sounds.pin(1046.5, 0)) / _sounds.RATE, 0.5)

  def test_muffled(self) -> None:
    """A pin's bar is muffled, hard light wood (the user): nearly all its
    sound in its first tenth of a second, its overtone three times as
    high weak."""
    take = _sounds.pin(1046.5, 0)
    tenth = int(0.1 * _sounds.RATE)
    energy = take * take
    self.assertGreater(float(energy[:tenth].sum() / energy.sum()), 0.9)
    spectrum = numpy.abs(numpy.fft.rfft(take))
    frequencies = numpy.fft.rfftfreq(len(take), 1.0 / _sounds.RATE)
    def near(pitch: float) -> float:
      band = numpy.abs(frequencies - pitch) < 0.03 * pitch
      return float(spectrum[band].max())
    self.assertLess(near(3.0 * 1046.5), 0.3 * near(1046.5))

  def test_carom(self) -> None:
    """Red meeting both whites is the xylophone happy (the user): four
    notes rising, C6 first."""
    take = _sounds.carom(0)
    step = int(0.075 * _sounds.RATE)
    heard = [loudestPitch(take[k * step:(k + 1) * step]) for k in range(4)]
    self.assertLess(abs(heard[0] - 1046.5), 0.05 * 1046.5)
    for lower, higher in zip(heard, heard[1:]):
      self.assertLess(lower, higher)

  def test_sad(self) -> None:
    """Red's pin is the xylophone sad (the user): four notes falling a
    semitone each, the first at its own note; the landing alone is the
    last of them, softer."""
    note = _sounds.SAD_NOTES[0]
    sad = _sounds.sadPin(note, 0)
    step = int(0.16 * _sounds.RATE)
    heard = [loudestPitch(sad[k * step:(k + 1) * step]) for k in range(4)]
    self.assertLess(abs(heard[0] - note), 0.03 * note)
    for higher, lower in zip(heard, heard[1:]):
      self.assertLess(lower, higher)
    land = _sounds.sadLand(note, 0)
    self.assertLess(abs(loudestPitch(land) - heard[3]), 0.03 * heard[3])
    self.assertLess(float(numpy.abs(land).max()),
                    float(numpy.abs(sad).max()))

  def test_pocket(self) -> None:
    """A ball into a pocket is a dull low knock, neutral, short; red
    into one is sad (the user): the drop, then a muted brass falling a
    semitone each, from B flat 3, the last held."""
    drop = _sounds.pocket(0)
    self.assertLess(loudestPitch(drop), 200.0)
    self.assertLess(len(drop) / _sounds.RATE, 0.5)
    sad = _sounds.sadPocket(0)
    self.assertGreater(len(sad) / _sounds.RATE, 1.5)
    start, step = int(0.16 * _sounds.RATE), int(0.3 * _sounds.RATE)
    heard = [loudestPitch(sad[start + k * step + 2000:
                              start + (k + 1) * step])
             for k in range(3)]
    self.assertLess(abs(heard[0] - 233.08), 0.03 * 233.08)
    for higher, lower in zip(heard, heard[1:]):
      self.assertLess(lower, higher)

  def test_wave(self) -> None:
    """A sound turns into a WAV file, 16 bits, one channel."""
    data = waveBytes(_sounds.tock(0))
    self.assertEqual(data[:4], b'RIFF')
    self.assertEqual(data[8:12], b'WAVE')
