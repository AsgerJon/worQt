"""
TestMixer covers the sandbox's sound ('Mixer', made from noise and
tones): every sample within -1 and 1 and finite; silent at no volume;
the wind there standing, a soft breeze; the pad soft, its loudest
tones the chord's; the rails silent standing, louder the faster,
louder near than far; the gun's hum idle and holding unlike, faded
between; a yeet and a punt each played once as their counts grow, the
yeet the longer, the punt the shorter and plainer.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.gaming.sandbox._mixer import CHORD, HUM, PAD, PUNTS
from worQt.gaming.sandbox._mixer import RAIL_FLANGE, RAIL_GAIN
from worQt.gaming.sandbox._mixer import RAIL_LOAD, RAIL_SPEED, TOLD
from worQt.gaming.sandbox._mixer import VOLUME, WIND, YEETS, Mixer
from worQt.gaming.sandbox._mixer import puntOf, yeetOf

from . import SandboxTest

#  Samples a second; a block, samples.
RATE, BLOCK = 44100, 441


def _told() -> list:
  """Returns a mixer's telling: full volume, nothing going on."""
  told = [0.0] * TOLD
  told[VOLUME], told[RAIL_LOAD] = 1.0, 1.0
  return told


def _rms(sound: numpy.ndarray) -> float:
  """Returns how loud 'sound' is: its root mean square."""
  return float(numpy.sqrt(numpy.mean(sound * sound)))


def _played(told: list, seconds: float, mixer: Mixer = None) -> tuple:
  """Returns 'seconds' of 'mixer' (a new one) told 'told', and the
  mixer."""
  mixer = Mixer(RATE) if mixer is None else mixer
  blocks = [mixer.samples(told, BLOCK)
            for _ in range(int(seconds * RATE / BLOCK))]
  return numpy.concatenate(blocks), mixer


class TestMixer(SandboxTest):
  """Tests for the sound's mixer."""

  def test_bounded(self) -> None:
    """Everything going on at once stays within -1 and 1, finite."""
    told = _told()
    told[WIND], told[RAIL_SPEED], told[RAIL_GAIN] = 1.0, 25.0, 1.0
    told[RAIL_LOAD], told[RAIL_FLANGE], told[HUM] = 3.0, 1.0, 2.0
    told[YEETS], told[PUNTS] = 1.0, 1.0
    mixer = Mixer(RATE)
    mixer.samples(_told(), BLOCK)
    sound, _ = _played(told, 1.0, mixer)
    self.assertTrue(numpy.isfinite(sound).all())
    self.assertLessEqual(float(numpy.abs(sound).max()), 1.0)

  def test_silent(self) -> None:
    """No volume, no sound."""
    told = _told()
    told[VOLUME], told[WIND], told[HUM] = 0.0, 1.0, 2.0
    sound, _ = _played(told, 0.3)
    self.assertEqual(float(numpy.abs(sound).max()), 0.0)

  def test_wind(self) -> None:
    """The wind blows standing, louder told more."""
    told = _told()
    told[WIND] = 0.35
    soft, _ = _played(told, 1.0)
    told[WIND] = 1.0
    loud, _ = _played(told, 1.0)
    self.assertGreater(_rms(soft), 0.001)
    self.assertGreater(_rms(loud), 2.0 * _rms(soft))

  def test_pad(self) -> None:
    """The pad: soft (under 0.03 rms), its loudest tones the chord's
    notes, off when told so."""
    told = _told()
    told[PAD] = 1.0
    sound, _ = _played(told, 4.0)
    self.assertGreater(_rms(sound), 0.001)
    self.assertLess(_rms(sound), 0.03)
    spectrum = numpy.abs(numpy.fft.rfft(sound))
    hertz = numpy.fft.rfftfreq(len(sound), 1.0 / RATE)
    loudest = hertz[numpy.argsort(spectrum)[-4:]]
    for found in loudest:
      with self.subTest(found=found):
        self.assertLess(min(abs(found - note) for note in CHORD), 1.0)
    told[PAD] = 0.0
    self.assertEqual(_rms(_played(told, 0.2)[0]), 0.0)

  def test_rails(self) -> None:
    """The rails: silent standing, louder the faster, quieter far."""
    told = _told()
    told[RAIL_GAIN] = 1.0
    loudness = []
    for speed in (0.0, 5.0, 20.0):
      told[RAIL_SPEED] = speed
      loudness.append(_rms(_played(told, 0.5)[0]))
    self.assertEqual(loudness[0], 0.0)
    self.assertGreater(loudness[2], 1.5 * loudness[1])
    told[RAIL_GAIN] = 0.2
    self.assertLess(_rms(_played(told, 0.5)[0]), 0.5 * loudness[2])

  def test_hum(self) -> None:
    """The hum idle and holding are unlike (holding the louder and
    higher), faded between."""
    told = _told()
    told[HUM] = 1.0
    idle, mixer = _played(told, 0.5)
    told[HUM] = 2.0
    first = mixer.samples(told, BLOCK)
    holding, _ = _played(told, 0.5, mixer)
    self.assertGreater(_rms(holding), 1.2 * _rms(idle[-RATE // 4:]))
    self.assertLess(_rms(first), _rms(holding[-RATE // 4:]))
    spectrum = numpy.abs(numpy.fft.rfft(idle[-RATE // 4:]))
    low = numpy.argmax(spectrum) * RATE / (RATE // 4)
    spectrum = numpy.abs(numpy.fft.rfft(holding[-RATE // 4:]))
    high = numpy.argmax(spectrum) * RATE / (RATE // 4)
    self.assertLess(low, high)

  def test_shots(self) -> None:
    """A yeet and a punt play once as their counts grow; the yeet the
    longer."""
    self.assertGreater(len(yeetOf(RATE)), 2 * len(puntOf(RATE)))
    told = _told()
    quiet, mixer = _played(told, 0.1)
    self.assertEqual(float(numpy.abs(quiet).max()), 0.0)
    told[YEETS] = 1.0
    yeet, mixer = _played(told, 0.8, mixer)
    self.assertGreater(float(numpy.abs(yeet).max()), 0.3)
    after, mixer = _played(told, 0.2, mixer)
    self.assertEqual(float(numpy.abs(after).max()), 0.0)
    told[PUNTS] = 1.0
    punt, _ = _played(told, 0.3, mixer)
    self.assertGreater(float(numpy.abs(punt).max()), 0.2)
    self.assertEqual(float(numpy.abs(punt[int(0.25 * RATE):]).max()), 0.0)
