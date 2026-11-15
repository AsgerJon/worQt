"""
TestVoice covers the engine's voices, made ('EngineVoice') and recorded
('RecordedVoice'): every sample within -1..1; made block by block or at
once the same sound (to 1e-4: no click where blocks meet); louder under
load; the made one's strongest line one of its engine's orders; the
recorded one, given a tone, plays it at the pitch the revolutions ask
(true to them: twice the recording's, twice its pitch, to 2 Hz; bent,
true at 'PIVOT' and the bend's power of two higher at twice that) and
loops on past its end as loud; 'waveBytes' writes a WAV of it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import io
import math
import wave

import numpy

from worQt.phys._voice import ORDERS, PITCH_BEND, PIVOT, REFERENCE
from worQt.phys._voice import EngineVoice, RecordedVoice, waveBytes

from . import PhysTest

RATE, BLOCK = 44100, 441


def tone(frequency: float, seconds: float) -> numpy.ndarray:
  """The 'tone' function returns a sine of 'frequency' Hz, 'seconds'
  long, at 'RATE'."""
  return 0.5 * numpy.sin(2.0 * math.pi * frequency
                         * numpy.arange(int(seconds * RATE)) / RATE)


def voices() -> tuple:
  """The 'voices' function returns a made voice and a recorded one (of
  a 100 Hz tone, two seconds long), alike seeded."""
  return (EngineVoice(RATE, 3),
          RecordedVoice(tone(100.0, 2.0), RATE, RATE))


def peakOf(sound: numpy.ndarray) -> float:
  """The 'peakOf' function returns the strongest line of 'sound', Hz."""
  spectrum = numpy.abs(numpy.fft.rfft(sound * numpy.hanning(len(sound))))
  return float(numpy.fft.rfftfreq(len(sound), 1.0 / RATE)[
    numpy.argmax(spectrum)])


class TestVoice(PhysTest):
  """Tests for the engine's voices."""

  def test_blocks(self) -> None:
    """Made in blocks or at once, at steady revolutions and load, the
    same sound (to 1e-4), every sample within -1..1. (At 3137 rpm: at
    3000 a firing lasts 441 samples exactly, each starting on a sample,
    so rounding moves its burst of noise a sample either way.)"""
    for made in range(2):
      parts, whole = voices()[made], voices()[made]
      for voice in (parts, whole):
        voice.samples(3137.0, 0.6, BLOCK)
      split = numpy.concatenate([parts.samples(3137.0, 0.6, BLOCK)
                                 for _ in range(20)])
      once = whole.samples(3137.0, 0.6, 20 * BLOCK)
      self.assertLess(float(numpy.abs(split - once).max()), 1e-4)
      self.assertLessEqual(float(numpy.abs(once).max()), 1.0)

  def test_load(self) -> None:
    """Under full load louder than without."""
    for made in range(2):
      loud = []
      for load in (0.0, 1.0):
        voice = voices()[made]
        voice.samples(4000.0, load, RATE)
        loud.append(float(numpy.sqrt(numpy.mean(
          voice.samples(4000.0, load, RATE) ** 2))))
      self.assertGreater(loud[1], loud[0])

  def test_orders(self) -> None:
    """The made voice's strongest line is one of its engine's orders
    (to 2 Hz), at 3000 rpm."""
    voice = voices()[0]
    voice.samples(3000.0, 0.5, RATE)
    peak = peakOf(voice.samples(3000.0, 0.5, RATE))
    self.assertLess(min(abs(peak - order * 50.0)
                        for order, _, _ in ORDERS), 2.0)

  def test_pitch(self) -> None:
    """True to the revolutions (bend 1), the recorded voice at twice the
    recording's revolutions plays its 100 Hz tone at 200 Hz (to 2 Hz),
    looping on past the recording's end (six seconds of a two-second
    loop played twice as fast) as loud in its last second as in its
    first (within a fifth); bent ('PITCH_BEND'), at 'PIVOT' as true, at
    twice it two to the bend times that (to 3 Hz)."""
    voice = RecordedVoice(tone(100.0, 2.0), RATE, RATE, REFERENCE, 1.0)
    voice.samples(2.0 * REFERENCE, 1.0, BLOCK)
    sound = voice.samples(2.0 * REFERENCE, 1.0, 6 * RATE)
    self.assertNear(peakOf(sound[:RATE]), 200.0, 2.0)
    first, last = (float(numpy.sqrt(numpy.mean(part ** 2)))
                   for part in (sound[:RATE], sound[-RATE:]))
    self.assertNear(last / first, 1.0, 0.2)
    bent, true = voices()[1], 100.0 * PIVOT / REFERENCE
    for rpm, pitch in ((PIVOT, true), (2.0 * PIVOT,
                                       true * 2.0 ** PITCH_BEND)):
      bent.samples(rpm, 1.0, RATE)
      self.assertNear(peakOf(bent.samples(rpm, 1.0, RATE)), pitch, 3.0)

  def test_wave(self) -> None:
    """'waveBytes' writes a mono 16-bit WAV of as many samples."""
    sound = voices()[0].samples(2000.0, 0.5, BLOCK)
    with wave.open(io.BytesIO(waveBytes(sound, RATE))) as file:
      self.assertEqual((file.getnchannels(), file.getsampwidth(),
                        file.getframerate(), file.getnframes()),
                       (1, 2, RATE, BLOCK))
