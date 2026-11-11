"""
The coin pusher's sounds, made rather than recorded: each as samples of
a ringing body, a few tones dying away at the frequencies a disc or a
tray rings at, struck by a short click; and as the bytes of a WAV file.
It needs no Qt.

- clink: a coin striking a coin, its pitch as given.
- tick: a coin striking the table, the pusher or a wall.
- tray: a coin landing in the steel tray: a coin's ring over the tray's.
- beep: a beat of the countdown.
- go: the game on, a bright chord and a scatter of coins.
- waveBytes: samples as a WAV file, 16 bits, one channel.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import io
import wave

import numpy

RATE = 44100  # samples a second

#  How a thin disc rings: its modes over the lowest, their loudness and
#  how fast each dies, in s to fall to 1/e
_DISC = ((1.0, 1.0, 0.16), (1.59, 0.6, 0.11), (2.14, 0.45, 0.08),
         (2.65, 0.3, 0.06), (3.16, 0.2, 0.045))


def _rung(seconds: float, modes: tuple, lowest: float,
          rng: numpy.random.Generator) -> numpy.ndarray:
  """'seconds' of a body ringing in 'modes' (ratio, loudness, decay)
  over 'lowest' Hz, each from a random phase, detuned a hair."""
  t = numpy.arange(int(seconds * RATE)) / RATE
  out = numpy.zeros(len(t))
  for ratio, loud, decay in modes:
    f = lowest * ratio * (1.0 + rng.uniform(-0.004, 0.004))
    phase = rng.uniform(0.0, 2.0 * numpy.pi)
    out += loud * numpy.exp(-t / decay) * numpy.sin(2 * numpy.pi * f * t
                                                   + phase)
  return out


def _struck(samples: numpy.ndarray, seconds: float, loud: float,
            rng: numpy.random.Generator) -> numpy.ndarray:
  """'samples' with the click of a strike at their start: 'seconds' of
  noise, its lows taken out, dying fast."""
  n = int(seconds * RATE)
  noise = numpy.diff(rng.uniform(-1.0, 1.0, n + 1))
  out = samples.copy()
  out[:n] += loud * noise * numpy.exp(-numpy.arange(n) / (0.25 * n))
  return out


def _shaped(samples: numpy.ndarray, peak: float) -> numpy.ndarray:
  """'samples' rising in 1 ms, fading out over the last 10 ms, and
  scaled so the loudest is 'peak'."""
  out = samples.copy()
  rise = min(len(out), int(0.001 * RATE))
  out[:rise] *= numpy.linspace(0.0, 1.0, rise)
  fall = min(len(out), int(0.01 * RATE))
  out[len(out) - fall:] *= numpy.linspace(1.0, 0.0, fall)
  top = numpy.abs(out).max()
  return out * (peak / top) if top > 0 else out


def clink(lowest: float, seed: int) -> numpy.ndarray:
  """The 'clink' function returns a coin striking a coin, ringing over
  'lowest' Hz."""
  rng = numpy.random.default_rng(seed)
  ring = _rung(0.4, _DISC, lowest, rng)
  return _shaped(_struck(ring, 0.0015, 0.5, rng), 0.7)


def tick(seed: int) -> numpy.ndarray:
  """The 'tick' function returns a coin striking the table, the pusher
  or a wall: duller, shorter, more knock than ring."""
  rng = numpy.random.default_rng(seed)
  modes = ((1.0, 1.0, 0.035), (2.3, 0.5, 0.02), (3.9, 0.3, 0.012))
  ring = _rung(0.12, modes, 1700.0 + rng.uniform(-150.0, 150.0), rng)
  return _shaped(_struck(ring, 0.003, 1.2, rng), 0.55)


def tray(seed: int) -> numpy.ndarray:
  """The 'tray' function returns a coin landing in the steel tray: the
  coin's bright ring over the tray's low one."""
  rng = numpy.random.default_rng(seed)
  coin = _rung(0.7, ((1.0, 1.0, 0.3), (1.4, 0.7, 0.22), (2.14, 0.4, 0.12)),
               3600.0 + rng.uniform(-300.0, 300.0), rng)
  pan = _rung(0.7, ((1.0, 1.0, 0.22), (2.76, 0.4, 0.1)),
              480.0 + rng.uniform(-30.0, 30.0), rng)
  return _shaped(_struck(coin + 0.8 * pan, 0.002, 0.8, rng), 0.8)


def beep(pitch: float) -> numpy.ndarray:
  """The 'beep' function returns a beat of the countdown at 'pitch'
  Hz."""
  t = numpy.arange(int(0.22 * RATE)) / RATE
  tone = (numpy.sin(2 * numpy.pi * pitch * t) +
          0.25 * numpy.sin(4 * numpy.pi * pitch * t))
  return _shaped(tone * numpy.exp(-t / 0.12), 0.6)


def go() -> numpy.ndarray:
  """The 'go' function returns the game on: a bright chord ringing out,
  with a scatter of coins."""
  rng = numpy.random.default_rng(7)
  t = numpy.arange(int(0.9 * RATE)) / RATE
  chord = sum(numpy.sin(2 * numpy.pi * f * t) for f in
              (880.0, 1108.7, 1318.5, 1760.0))
  out = chord * numpy.exp(-t / 0.35)
  for k in range(6):
    start = int(rng.uniform(0.05, 0.5) * RATE)
    coin = clink(rng.uniform(3000.0, 4600.0), 100 + k)
    end = min(len(out), start + len(coin))
    out[start:end] += 1.5 * coin[:end - start]
  return _shaped(out, 0.75)


def waveBytes(samples: numpy.ndarray) -> bytes:
  """The 'waveBytes' function returns 'samples' (-1 to 1) as a WAV file,
  16 bits, one channel, at 'RATE'."""
  data = numpy.round(numpy.clip(samples, -1.0, 1.0) * 32767.0)
  buffer = io.BytesIO()
  out = wave.open(buffer, 'wb')
  out.setnchannels(1)
  out.setsampwidth(2)
  out.setframerate(RATE)
  out.writeframes(data.astype('<i2').tobytes())
  out.close()
  return buffer.getvalue()
