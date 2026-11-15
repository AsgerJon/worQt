"""
The engine's voice (user, 2026-11-13: "sound. engine. sound."): an
inline four, four-stroke, made from what it does as it turns, not from
recordings.

'EngineVoice' makes its sound, block after block, from the engine's
revolutions and load as they go ('Gearbox.rpm', 'Gearbox.load'): the
crank's turning counted on from block to block (no click where blocks
meet, the revolutions drawn straight across each), the engine's orders
on it (the firing, two to a turn, strongest, its harmonics brighter the
harder it works, the half and odd orders a four's unevenness gives,
'ORDERS'), a burst of noise at each firing (the combustion, harder
under load), the lot through the intake and exhaust's resonance
('RESONANCE'), louder with revolutions and load. Floats between -1 and
1; 'pcm' makes them 16-bit samples, 'waveBytes' a WAV file of them.

'RecordedVoice' plays a recording of an engine instead (user,
2026-11-13: "found a royalty free engine sound", a V12 running steady
ten seconds): looped (its end faded into its start), read faster or
slower as the revolutions are above or below the recording's
('reference'), from copies of it smoothed an octave further at each
octave it is sped up (so speeding it never folds its highs back down
as noise), louder and brighter under load. 'recordingOf' reads a sound
file through ffmpeg.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import io
import math
import subprocess
import wave

import numpy

#  The engine orders (per turn of the crank) the voice is made of, each
#  its strength idling and how much more under full load: the firing
#  (2) and its harmonics, the half and odd orders a real four's small
#  unevenness gives.
ORDERS = ((0.5, 0.05, 0.03), (1.0, 0.12, 0.05), (1.5, 0.06, 0.06),
          (2.0, 1.00, 0.30), (3.0, 0.08, 0.10), (4.0, 0.35, 0.45),
          (6.0, 0.15, 0.40), (8.0, 0.06, 0.30), (10.0, 0.02, 0.18))
#  The intake and exhaust's resonance, Hz, and its sharpness (Q); the
#  combustion noise's strength idling and under load, and how sharp its
#  burst at each firing (a share of the firing's period).
RESONANCE, SHARPNESS = 160.0, 2.5
NOISE, NOISE_LOAD, BURST = 0.05, 0.25, 0.12
#  How loud it is idling, with revolutions (at 'LOUDEST'), with load
#  (less with load than at first, 0.40: each shift and lift dropped it
#  by more than half).
QUIET, WITH_RPM, WITH_LOAD, LOUDEST = 0.35, 0.35, 0.25, 7500.0


class EngineVoice:
  """
  EngineVoice makes an engine's sound at 'rate' samples a second, block
  after block ('samples'), from its revolutions a minute and load; its
  crank's turning ('turned', turns), the last revolutions and load and
  the resonance's memory carry from one block to the next; 'seed' its
  noise's.
  """

  def __init__(self, rate: int, seed: int = 0) -> None:
    self.rate, self.turned = rate, 0.0
    self.rpm, self.load = 0.0, 0.0
    self.random = numpy.random.default_rng(seed)
    self._memory = (0.0, 0.0)
    self._filter = _resonator(RESONANCE, SHARPNESS, rate)

  def samples(self, rpm: float, load: float, count: int) -> numpy.ndarray:
    """The 'samples' method returns the next 'count' samples, floats in
    -1..1, the engine going from where it was to 'rpm' and 'load' across
    them."""
    if count <= 0:
      return numpy.zeros(0, numpy.float32)
    share = numpy.arange(1, count + 1, dtype=numpy.float64) / count
    rpms = self.rpm + (max(rpm, 0.0) - self.rpm) * share
    loads = self.load + (min(max(load, 0.0), 1.0) - self.load) * share
    turns = self.turned + numpy.cumsum(rpms / 60.0 / self.rate)
    self.turned = float(turns[-1] % 2.0)
    self.rpm, self.load = rpms[-1], loads[-1]
    sound = numpy.zeros(count)
    nyquist = 0.45 * self.rate
    for order, idle, more in ORDERS:
      strength = (idle + more * loads) * (order * rpms / 60.0 < nyquist)
      sound += strength * numpy.sin(2.0 * math.pi * order * turns
                                    + 0.7 * order)
    firing = (2.0 * turns) % 1.0
    burst = numpy.exp(-firing / BURST)
    noise = self.random.standard_normal(count)
    sound += (NOISE + NOISE_LOAD * loads) * burst * noise
    sound = self._resonated(sound)
    loud = QUIET + WITH_RPM * numpy.minimum(rpms / LOUDEST, 1.0) + (
      WITH_LOAD * loads)
    return numpy.tanh(0.35 * loud * sound).astype(numpy.float32)

  def _resonated(self, sound: numpy.ndarray) -> numpy.ndarray:
    """Returns 'sound' through the resonance, half of it straight (the
    filter's memory carried on)."""
    b0, b2, a1, a2 = self._filter
    first, second = self._memory
    out = numpy.empty_like(sound)
    for k, value in enumerate(sound):
      y = b0 * value + first
      first = second - a1 * y
      second = b2 * value - a2 * y
      out[k] = y
    self._memory = (first, second)
    return 0.5 * sound + 2.0 * out


#  The recording's revolutions a minute (its clearest line, ~135 Hz, as
#  a V12's firing, six to a turn: a guess, by ear to be set), how long
#  its end is faded into its start, s, how many octaves it is smoothed
#  for, how bright it is off load (a share of the sound's top) and how
#  loud idling and with load added (user, 2026-11-13: "sound is kinda
#  bad ngl": at 0.35 and 0.45, and darkened to 0.15, each shift and each
#  lift dropped it to under half, dull: now a dip).
REFERENCE, CROSS, OCTAVES = 1350.0, 0.3, 4
DARK, IDLE_LOUD, LOAD_LOUD = 0.4, 0.55, 0.3
#  How the recording's pitch follows the revolutions: as (rpm / 'PIVOT')
#  to this power, true at 'PIVOT' (1: the revolutions' own pitch, a
#  steady rumble sped 5.5 times at the redline and slowed to 0.6 idling;
#  0.6: 1.2 to 4.3 times, a game's compromise for a single recording,
#  which wants several made at other revolutions to be true).
PITCH_BEND, PIVOT = 0.6, 4000.0


class RecordedVoice:
  """
  RecordedVoice plays 'recording' (floats in -1..1, at 'recorded' samples
  a second) as an engine at 'rate' samples a second, block after block
  ('samples'), from its revolutions a minute and load: where it reads
  ('read', samples into the loop), the last revolutions and load and
  the brightness filter's memory carry from block to block;
  'reference' the revolutions the recording was made at, 'bend' how its
  pitch follows the revolutions ('PITCH_BEND'). Between the smoothed
  copies it reads (an octave apart) it fades as it is sped (switching
  at once clicked as it crossed each octave).
  """

  def __init__(self, recording: numpy.ndarray, recorded: int, rate: int,
               reference: float = REFERENCE,
               bend: float = PITCH_BEND) -> None:
    self.rate, self.reference, self.bend = rate, reference, bend
    self.read, self.rpm, self.load = 0.0, reference, 0.0
    self._bright = 0.0
    sound = numpy.asarray(recording, numpy.float64)
    count = int(len(sound) * rate / recorded)
    sound = numpy.interp(numpy.arange(count) * recorded / rate,
                         numpy.arange(len(sound)), sound)
    cross = min(int(CROSS * rate), count // 4)
    fade = numpy.linspace(0.0, 1.0, cross)
    loop = sound[:count - cross].copy()
    loop[:cross] = fade * sound[:cross] + (1.0 - fade) * sound[-cross:]
    loop -= loop.mean()
    loop /= max(numpy.abs(loop).max(), 1e-9)
    spectrum = numpy.fft.rfft(loop)
    tops = numpy.fft.rfftfreq(len(loop), 1.0 / rate)
    self.loops = numpy.array([
      numpy.fft.irfft(numpy.where(tops <= 0.45 * rate / 2 ** octave,
                                  spectrum, 0.0), len(loop))
      for octave in range(OCTAVES + 1)])

  def samples(self, rpm: float, load: float, count: int) -> numpy.ndarray:
    """The 'samples' method returns the next 'count' samples, floats in
    -1..1, the engine going from where it was to 'rpm' and 'load' across
    them."""
    if count <= 0:
      return numpy.zeros(0, numpy.float32)
    share = numpy.arange(1, count + 1, dtype=numpy.float64) / count
    rpms = self.rpm + (max(rpm, 0.0) - self.rpm) * share
    loads = self.load + (min(max(load, 0.0), 1.0) - self.load) * share
    self.rpm, self.load = rpms[-1], loads[-1]
    speeds = (PIVOT / self.reference) * (numpy.maximum(rpms, 1.0)
                                         / PIVOT) ** self.bend
    octaves = numpy.clip(numpy.log2(speeds), 0.0, OCTAVES - 1e-9)
    lower = octaves.astype(numpy.int64)
    fade = octaves - lower
    size = self.loops.shape[1]
    places = self.read + numpy.cumsum(speeds)
    self.read = float(places[-1] % size)
    places %= size
    first = places.astype(numpy.int64)
    part = places - first
    after = (first + 1) % size
    sound = numpy.zeros(count)
    for octave, share in ((lower, 1.0 - fade), (lower + 1, fade)):
      sound += share * (self.loops[octave, first] * (1.0 - part)
                        + self.loops[octave, after] * part)
    sound = self._brightened(sound, loads)
    return numpy.clip((IDLE_LOUD + LOAD_LOUD * loads) * sound, -1.0,
                      1.0).astype(numpy.float32)

  def _brightened(self, sound: numpy.ndarray,
                  loads: numpy.ndarray) -> numpy.ndarray:
    """Returns 'sound' darkened off load: a share of its top cut by a
    one-pole filter (its memory carried on), the less the more load."""
    smooth = 0.25
    low = numpy.empty_like(sound)
    last = self._bright
    for k, value in enumerate(sound):
      last += smooth * (value - last)
      low[k] = last
    self._bright = last
    dark = DARK + (1.0 - DARK) * loads
    return low + dark * (sound - low)


def recordingOf(path: str, rate: int) -> numpy.ndarray | None:
  """The 'recordingOf' function returns the sound file at 'path' as
  floats in -1..1, mono, at 'rate' samples a second (read by ffmpeg),
  or None if it cannot be read."""
  try:
    done = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path,
                           '-ac', '1', '-ar', str(rate), '-f', 's16le',
                           '-'], capture_output=True, timeout=30.0,
                          check=True)
  except (OSError, subprocess.SubprocessError):
    return None
  sound = numpy.frombuffer(done.stdout, '<i2').astype(numpy.float64)
  return sound / 32768.0 if len(sound) else None


def _resonator(frequency: float, sharpness: float, rate: int) -> tuple:
  """Returns a band-pass biquad's coefficients (b0, b2, a1, a2; b1
  nought, a0 one) about 'frequency' Hz, 'sharpness' its Q, at 'rate'."""
  w = 2.0 * math.pi * frequency / rate
  alpha = math.sin(w) / (2.0 * sharpness)
  a0 = 1.0 + alpha
  return (alpha / a0, -alpha / a0, -2.0 * math.cos(w) / a0,
          (1.0 - alpha) / a0)


def pcm(sound: numpy.ndarray) -> bytes:
  """The 'pcm' function returns 'sound' (floats in -1..1) as 16-bit
  samples, little-endian."""
  clipped = numpy.clip(sound, -1.0, 1.0)
  return (clipped * 32767.0).astype('<i2').tobytes()


def waveBytes(sound: numpy.ndarray, rate: int) -> bytes:
  """The 'waveBytes' function returns 'sound' as a mono 16-bit WAV
  file's bytes at 'rate' samples a second."""
  buffer = io.BytesIO()
  with wave.open(buffer, 'wb') as file:
    file.setnchannels(1)
    file.setsampwidth(2)
    file.setframerate(rate)
    file.writeframes(pcm(sound))
  return buffer.getvalue()
