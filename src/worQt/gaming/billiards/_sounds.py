"""
The billiards' sounds, made rather than recorded, as samples at 'RATE':
each a few tones dying away at the frequencies the struck thing rings
at, struck by a short click. It needs no Qt; 'SoundPlayer' plays them.

- clack: ball on ball, the resin balls' short bright click.
- thud: a ball into a cushion, the rubber's dull knock.
- tock: the cue's leather tip on the ball.
- fanfare: a point made, a rising brass call and its chord.
- windUp, whirr, windDown: a shot played fast: winding up, the whirr
  looped while it lasts, winding down.
- pin: a keglebillard pin knocked over, as a xylophone's bar of hard
  light wood struck, muffled, each of the five pins a note of its own
  ('PIN_NOTES'), named for its number in the bank ('pin0' to 'pin4').
- sadPin, sadLand: a pin red knocks, a foul (5.8): the xylophone sad,
  four notes falling a semitone each, the last held ('sadPin0' to
  'sadPin4', from 'SAD_NOTES'), and the last alone, soft, as a pin
  credited to red falls ('sadLand0' to 'sadLand4').
- carom: keglebillard's 'rødt', red meeting both whites, 4 points: the
  xylophone happy, a major chord run up and its top held.
- takes: every sound by name, the takes of each, for 'SoundPlayer'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

RATE = 44100  # samples a second


def _rung(seconds: float, modes: tuple, lowest: float,
          rng: numpy.random.Generator) -> numpy.ndarray:
  """'seconds' of a body ringing in 'modes' (ratio, loudness, s to fall
  to 1/e) over 'lowest' Hz, each from a random phase."""
  t = numpy.arange(int(seconds * RATE)) / RATE
  out = numpy.zeros(len(t))
  for ratio, loud, decay in modes:
    phase = rng.uniform(0.0, 2.0 * numpy.pi)
    out += loud * numpy.exp(-t / decay) * numpy.sin(
      2.0 * numpy.pi * lowest * ratio * t + phase)
  return out


def _clicked(samples: numpy.ndarray, seconds: float, loud: float,
             rng: numpy.random.Generator) -> numpy.ndarray:
  """'samples' with a click at their start: 'seconds' of noise, its
  lows taken out, dying fast."""
  n = max(int(seconds * RATE), 1)
  noise = numpy.diff(rng.uniform(-1.0, 1.0, n + 1))
  out = samples.copy()
  out[:n] += loud * noise * numpy.exp(-numpy.arange(n) / (0.25 * n))
  return out


def _shaped(samples: numpy.ndarray, peak: float) -> numpy.ndarray:
  """'samples' rising in 1 ms, fading over the last 10 ms, scaled so
  the loudest is 'peak'."""
  out = samples.copy()
  rise = min(len(out), int(0.001 * RATE))
  out[:rise] *= numpy.linspace(0.0, 1.0, rise)
  fall = min(len(out), int(0.01 * RATE))
  out[len(out) - fall:] *= numpy.linspace(1.0, 0.0, fall)
  top = numpy.abs(out).max()
  return out * (peak / top) if top > 0.0 else out


def clack(lowest: float, seed: int) -> numpy.ndarray:
  """The 'clack' function returns ball meeting ball: a sharp click and
  a bright ring over 'lowest' Hz, gone in a few hundredths of a
  second."""
  rng = numpy.random.default_rng(seed)
  modes = ((1.0, 1.0, 0.012), (1.47, 0.6, 0.008), (2.31, 0.35, 0.005))
  ring = _rung(0.09, modes, lowest, rng)
  return _shaped(_clicked(ring, 0.0012, 0.9, rng), 0.75)


def thud(seed: int) -> numpy.ndarray:
  """The 'thud' function returns a ball into a cushion: a low dull
  knock of rubber, a little click of the cloth."""
  rng = numpy.random.default_rng(seed)
  body = _rung(0.16, ((1.0, 1.0, 0.04), (2.1, 0.4, 0.018)),
               130.0 + rng.uniform(-20.0, 20.0), rng)
  knock = _rung(0.16, ((1.0, 1.0, 0.012),), 620.0 + rng.uniform(-60.0,
                                                               60.0), rng)
  return _shaped(_clicked(body + 0.35 * knock, 0.002, 0.25, rng), 0.7)


def tock(seed: int) -> numpy.ndarray:
  """The 'tock' function returns the cue's leather tip on the ball: a
  short woody knock."""
  rng = numpy.random.default_rng(seed)
  knock = _rung(0.09, ((1.0, 1.0, 0.012), (1.8, 0.4, 0.007)),
                1050.0 + rng.uniform(-80.0, 80.0), rng)
  body = _rung(0.09, ((1.0, 1.0, 0.025),), 230.0, rng)
  return _shaped(_clicked(knock + 0.5 * body, 0.0015, 0.5, rng), 0.6)


def _brass(pitch: float, seconds: float) -> numpy.ndarray:
  """'seconds' of a brass note at 'pitch' Hz: its first six harmonics,
  softer up the row, swelling in over 30 ms, a little vibrato."""
  t = numpy.arange(int(seconds * RATE)) / RATE
  wobble = 0.004 * numpy.sin(2.0 * numpy.pi * 5.5 * t)
  out = sum(numpy.sin(2.0 * numpy.pi * pitch * k * t * (1.0 + wobble)) / k
            for k in range(1, 7))
  swell = numpy.minimum(t / 0.03, 1.0)
  return out * swell


def fanfare() -> numpy.ndarray:
  """The 'fanfare' function returns a point made: a rising call, C, E,
  G, high C, then the chord held and dying away."""
  notes = (523.25, 659.25, 783.99, 1046.5)
  step, hold = 0.11, 0.9
  out = numpy.zeros(int((len(notes) * step + hold) * RATE))
  for k, pitch in enumerate(notes):
    start = int(k * step * RATE)
    tone = _brass(pitch, step * 1.05)
    tone *= numpy.exp(-numpy.arange(len(tone)) / RATE / 0.2)
    end = min(len(out), start + len(tone))
    out[start:end] += tone[:end - start]
  start = int(len(notes) * step * RATE)
  chord = sum(_brass(pitch, hold) for pitch in notes)
  chord *= numpy.exp(-numpy.arange(len(chord)) / RATE / 0.45)
  end = min(len(out), start + len(chord))
  out[start:end] += 0.8 * chord[:end - start]
  return _shaped(out, 0.8)


_WHIRR = 220.0  # Hz the fast whirr hums at
#  The notes of the five pins, a pentatonic run up from C6, the middle
#  pin's first, as the pins stand in 'KegleTable.pinSpots'.
PIN_NOTES = (1046.50, 1174.66, 1318.51, 1567.98, 1760.00)
#  The notes red's pins fall from, sad: a minor run down from E5, the
#  middle pin's first.
SAD_NOTES = (659.25, 587.33, 523.25, 440.00, 392.00)
_SAD_STEP = 0.16  # s between the sad notes
_SEMITONE = 2.0 ** (-1.0 / 12.0)  # a semitone down
_SAD_BRASS = 233.08  # Hz the sad brass starts at, B flat 3
_LOOP = 0.5  # s of the whirr, looped: every tone in it a whole number


def _hum(pitch: numpy.ndarray, t: numpy.ndarray) -> numpy.ndarray:
  """A buzzy hum, its first eight harmonics softer up the row, at
  'pitch' Hz over the times 't', the pitch gliding as it is given."""
  phase = 2.0 * numpy.pi * numpy.cumsum(pitch) / RATE
  return sum(numpy.sin(k * phase) / k for k in range(1, 9))


def whirr() -> numpy.ndarray:
  """The 'whirr' function returns the hum of a shot played fast, half a
  second of it that loops without a seam: every tone in it, the hum,
  its whine and the flutter, goes round a whole number of times."""
  t = numpy.arange(int(_LOOP * RATE)) / RATE
  hum = sum(numpy.sin(2.0 * numpy.pi * _WHIRR * k * t) / k
            for k in range(1, 9))
  whine = 0.15 * numpy.sin(2.0 * numpy.pi * 6.0 * _WHIRR * t)
  flutter = 1.0 + 0.35 * numpy.sin(2.0 * numpy.pi * 12.0 * t)
  out = (hum + whine) * flutter
  return out * (0.5 / numpy.abs(out).max())


def windUp() -> numpy.ndarray:
  """The 'windUp' function returns a shot speeding up: the hum gliding
  up to the whirr's pitch."""
  t = numpy.arange(int(0.3 * RATE)) / RATE
  pitch = 110.0 + (_WHIRR - 110.0) * (t / t[-1]) ** 0.6
  return _shaped(_hum(pitch, t) * numpy.minimum(t / 0.05, 1.0), 0.5)


def windDown() -> numpy.ndarray:
  """The 'windDown' function returns a shot slowing again: the hum
  gliding down from the whirr's pitch, dying."""
  t = numpy.arange(int(0.35 * RATE)) / RATE
  pitch = _WHIRR - (_WHIRR - 80.0) * (t / t[-1])
  return _shaped(_hum(pitch, t) * numpy.exp(-t / 0.15), 0.45)


def _bar(pitch: float, decay: float, seconds: float,
         rng: numpy.random.Generator) -> numpy.ndarray:
  """'seconds' of a xylophone's bar of hard light wood struck, muffled
  (the user): its ring at 'pitch' Hz dying to 1/e in 'decay' s, its
  overtone three times as high, as a xylophone's bar is tuned, damped
  and quicker still, the wood's dull knock under it, and the mallet's
  click dulled, its highs taken out."""
  modes = ((1.0, 1.0, decay), (3.0, 0.22, 0.3 * decay),
           (6.1, 0.04, 0.1 * decay))
  ring = _rung(seconds, modes, pitch, rng)
  knock = _rung(seconds, ((1.0, 1.0, 0.008),),
                0.45 * pitch + rng.uniform(-30.0, 30.0), rng)
  out = ring + 0.35 * knock
  n = max(int(0.002 * RATE), 1)
  noise = numpy.convolve(rng.uniform(-1.0, 1.0, n + 8), numpy.ones(8) / 8.0,
                         'valid')[:n]
  out[:n] += 0.5 * noise * numpy.exp(-numpy.arange(n) / (0.3 * n))
  return out


def pin(pitch: float, seed: int) -> numpy.ndarray:
  """The 'pin' function returns a pin knocked over, as a xylophone's
  bar of hard light wood struck, muffled (the user): its ring at
  'pitch' Hz gone in a few hundredths of a second."""
  rng = numpy.random.default_rng(seed)
  return _shaped(_bar(pitch, 0.06, 0.3, rng), 0.7)


def sadPin(pitch: float, seed: int) -> numpy.ndarray:
  """The 'sadPin' function returns a pin red knocked, a foul: the
  xylophone sad (the user), four muffled notes from 'pitch' falling a
  semitone each, the last held a little longer."""
  rng = numpy.random.default_rng(seed)
  last = 0.45
  out = numpy.zeros(int((3 * _SAD_STEP + last) * RATE))
  for k in range(4):
    held = k == 3
    note = _bar(pitch * _SEMITONE ** k, 0.11 if held else 0.05,
                last if held else _SAD_STEP, rng)
    start = int(k * _SAD_STEP * RATE)
    end = min(len(out), start + len(note))
    out[start:end] += (0.85 if held else 1.0) * note[:end - start]
  return _shaped(out, 0.6)


def carom(seed: int) -> numpy.ndarray:
  """The 'carom' function returns red meeting both whites, a score: the
  xylophone happy (the user), C6 E6 G6 C7 run up quickly, muffled, the
  top held."""
  rng = numpy.random.default_rng(seed)
  notes = (1046.50, 1318.51, 1567.98, 2093.00)
  step, last = 0.075, 0.4
  out = numpy.zeros(int((3 * step + last) * RATE))
  for k, pitch in enumerate(notes):
    held = k == 3
    note = _bar(pitch, 0.1 if held else 0.045, last if held else step,
                rng)
    start = int(k * step * RATE)
    end = min(len(out), start + len(note))
    out[start:end] += note[:end - start]
  return _shaped(out, 0.7)


def sadLand(pitch: float, seed: int) -> numpy.ndarray:
  """The 'sadLand' function returns a pin credited to red falling: the
  last of its sad notes, 'pitch' three semitones down, alone and
  soft."""
  rng = numpy.random.default_rng(seed)
  return _shaped(_bar(pitch * _SEMITONE ** 3, 0.08, 0.35, rng), 0.45)


def pocket(seed: int) -> numpy.ndarray:
  """The 'pocket' function returns a ball dropping into a pocket, as
  neutral as can be (the user): a dull knock as it meets the leather
  behind the hole, then a few soft bumps, quicker and fainter, as it
  settles in."""
  rng = numpy.random.default_rng(seed)
  out = numpy.zeros(int(0.42 * RATE))
  for start, loud in ((0.0, 1.0), (0.11, 0.35), (0.19, 0.18),
                      (0.25, 0.09)):
    body = _rung(0.16, ((1.0, 1.0, 0.035), (2.3, 0.3, 0.012)),
                 105.0 + rng.uniform(-10.0, 10.0), rng)
    knock = _rung(0.16, ((1.0, 1.0, 0.01),),
                  380.0 + rng.uniform(-40.0, 40.0), rng)
    bump = _clicked(body + 0.4 * knock, 0.003, 0.15, rng)
    begin = int(start * RATE)
    end = min(len(out), begin + len(bump))
    out[begin:end] += loud * bump[:end - begin]
  return _shaped(out, 0.65)


def sadPocket(seed: int) -> numpy.ndarray:
  """The 'sadPocket' function returns red dropping into a pocket, a foul:
  sad (the user), its drop followed by a muted brass falling a semitone
  three times, the last held and wavering, 'wah wah wah waah'."""
  drop = pocket(seed)
  step, last = 0.3, 0.9
  start = int(0.16 * RATE)
  out = numpy.zeros(start + int((3 * step + last) * RATE))
  out[:len(drop)] += drop
  for k in range(4):
    held = k == 3
    pitch = _SAD_BRASS * _SEMITONE ** k
    tone = _muted(pitch, last if held else step, held)
    begin = start + int(k * step * RATE)
    end = min(len(out), begin + len(tone))
    out[begin:end] += 0.5 * tone[:end - begin]
  return _shaped(out, 0.7)


def _muted(pitch: float, seconds: float, held: bool) -> numpy.ndarray:
  """'seconds' of a muted brass note at 'pitch' Hz: its first harmonics
  only, softer up the row, swelling in and dying away, held long with a
  slow deep wobble."""
  t = numpy.arange(int(seconds * RATE)) / RATE
  depth = 0.02 if held else 0.004
  wobble = depth * numpy.sin(2.0 * numpy.pi * (4.0 if held else 5.5) * t)
  out = sum(numpy.sin(2.0 * numpy.pi * pitch * k * t * (1.0 + wobble))
            / (k * k) for k in range(1, 5))
  swell = numpy.minimum(t / 0.04, 1.0)
  fade = numpy.exp(-t / (0.5 if held else 0.25))
  return out * swell * fade


def takes() -> dict:
  """The 'takes' function returns every sound by name, the takes of
  each, samples each: as 'SoundPlayer' asks of a bank."""
  pitches = (2800.0, 3150.0, 3500.0, 3900.0)
  return {'clack': [clack(pitch, k) for k, pitch in enumerate(pitches)],
          'thud': [thud(k) for k in range(3)],
          'tock': [tock(k) for k in range(2)],
          'fanfare': [fanfare()],
          'carom': [carom(0)],
          'pocket': [pocket(k) for k in range(2)],
          'sadPocket': [sadPocket(0)],
          'windUp': [windUp()],
          'whirr': [whirr()],
          'windDown': [windDown()],
          **{'pin%d' % k: [pin(note, k)]
             for k, note in enumerate(PIN_NOTES)},
          **{'sadPin%d' % k: [sadPin(note, k)]
             for k, note in enumerate(SAD_NOTES)},
          **{'sadLand%d' % k: [sadLand(note, k)]
             for k, note in enumerate(SAD_NOTES)}}
