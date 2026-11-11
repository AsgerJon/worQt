"""
TestSounds covers '_sounds', the coin pusher's sounds made rather than
recorded: each as long as meant, as loud as meant, ringing loudest
where it should (a coin's clink at the pitch asked, a knock lower, the
countdown's beep at its pitch); and as a WAV file, 16 bits, one channel,
that reads back the same.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import io
import wave

import numpy

from worQt.gaming.pusher import _sounds

from . import PusherTest


def loudestAt(samples: numpy.ndarray) -> float:
  """The 'loudestAt' function returns the frequency, Hz, 'samples' are
  loudest at."""
  spectrum = numpy.abs(numpy.fft.rfft(samples))
  return float(numpy.fft.rfftfreq(len(samples), 1.0 / _sounds.RATE)[
    spectrum.argmax()])


class TestSounds(PusherTest):
  """Tests for '_sounds'."""

  def test_clink(self) -> None:
    """A clink rings 0.4 s at the pitch asked, at 0.7 at the loudest."""
    for pitch in (2900.0, 4300.0):
      samples = _sounds.clink(pitch, 1)
      self.assertEqual(len(samples), int(0.4 * _sounds.RATE))
      self.assertAlmostEqual(float(numpy.abs(samples).max()), 0.7, 6)
      self.assertLess(abs(loudestAt(samples) - pitch), 0.01 * pitch)

  def test_others(self) -> None:
    """A knock is short and low; the tray rings long; the beep sounds
    at its pitch; the chord rings almost a second; none past 0.8."""
    tick, tray = _sounds.tick(1), _sounds.tray(1)
    beep, go = _sounds.beep(880.0), _sounds.go()
    self.assertLess(len(tick), len(_sounds.clink(3000.0, 1)))
    self.assertLess(loudestAt(tick), 2000.0)
    self.assertGreater(len(tray), len(_sounds.clink(3000.0, 1)))
    self.assertLess(abs(loudestAt(beep) - 880.0), 10.0)
    self.assertEqual(len(go), int(0.9 * _sounds.RATE))
    for samples in (tick, tray, beep, go):
      self.assertLessEqual(float(numpy.abs(samples).max()), 0.8 + 1e-9)

  def test_wave(self) -> None:
    """As a WAV file a sound is 16 bits, one channel, at 'RATE', and
    reads back as it was, to a step of 16 bits."""
    samples = _sounds.clink(3300.0, 2)
    read = wave.open(io.BytesIO(_sounds.waveBytes(samples)), 'rb')
    self.assertEqual((read.getnchannels(), read.getsampwidth(),
                      read.getframerate()), (1, 2, _sounds.RATE))
    back = numpy.frombuffer(read.readframes(read.getnframes()), '<i2')
    self.assertEqual(len(back), len(samples))
    self.assertLess(float(numpy.abs(back / 32767.0 - samples).max()), 1e-4)
