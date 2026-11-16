"""
CabinMixer makes the space window's sound, Qt-free, block by block, in
the sandbox's speaker's process of its own (user, 2026-11-16: "all of
the inputs and outputs should have appropriate clicky sounds"; "The
rocket should have a proper sound that reduces to ambience inside the
cabin, but is full and cool on the third person"; the cassette deck's
tape): the engine (outside a full roar, inside a rumble), the cabin's
hum, every key's click, switch's snap, knob's tick, the slide's swish,
a lamp's relay, the teleprinter's clatter, carriage and bell, and the
tape. Made from noise and tones, but the tape (the user's own file,
decoded by ffmpeg). Mono, between -1 and 1.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import shutil
import subprocess
import threading

import numpy
from scipy.signal import lfilter

from worQt.gaming.sandbox._mixer import bandOf, lowOf

from ._tapedeck import LEAD_IN

#  What the mixer is told, by place in its list: the volume, the engine
#  (its throttle, nought to one), whether the ear is inside the cabin
#  (one) or out (nought), how thick the air is (nought to one), how many
#  key clicks, switch snaps and knob ticks there have been, how fast the
#  slide moves (nought to one), the teleprinter's characters, bells and
#  carriage returns, whether the tape plays, how often it was rewound,
#  how many lamps have changed, how often the deck has been announced
#  (its clicks getting ready for the music), how many thuds there have
#  been in the cabin (Asger or a loose thing meeting something hard) and
#  how hard the last frame's hardest was (m/s, by its heft), how often
#  Asger has been hurt (a point of health lost) and how many rations he
#  has begun.
VOLUME, ENGINE, INSIDE, AIR, CLICKS, SNAPS, TICKS = range(7)
SLIDE, TYPED, BELLS, RETURNS, DECK, REWINDS, RELAYS = range(7, 14)
ANNOUNCED, THUDS, THUD, HURTS, EATS = range(14, 19)
TOLD = 19
#  A thud this hard (m/s, by its heft) is as loud as a thud gets.
LOUDEST = 4.0
#  How fast the engine's roar and the ear's place ease, s.
EASE = 0.15
#  How loud the tape plays, and how fast it fades in and out, s.
TAPE_GAIN, TAPE_FADE = 0.55, 0.08
#  How loud the teleprinter is (user, 2026-11-16: "the terminal doesn't
#  need to make that clicking every time. It makes *way* too much noise.
#  Make it be nearly inaudible"; then "The teleprinter should be even
#  less audible"): its clacks, carriage and bell all a seventieth of what
#  they were, under the cabin's hum.
PRINTER_HUSH = 0.015


def _burst(rate: int, length: float, middle: float, sharp: float,
           decay: float, seed: int) -> numpy.ndarray:
  """Returns a burst of noise 'length' s long, band passed at 'middle'
  Hz ('sharp' its Q), dying away over 'decay' s, peak one."""
  random = numpy.random.default_rng(seed)
  t = numpy.arange(int(length * rate)) / rate
  b, a = bandOf(rate, middle, sharp)
  sound = lfilter(b, a, random.standard_normal(len(t))) * numpy.exp(
    -t / decay)
  return sound / max(1e-9, numpy.abs(sound).max())


def _ring(rate: int, length: float, tones: tuple,
          decay: float) -> numpy.ndarray:
  """Returns a ring of 'tones' (each Hz and weight) dying away over
  'decay' s, peak one."""
  t = numpy.arange(int(length * rate)) / rate
  sound = sum(w * numpy.sin(2.0 * math.pi * f * t) for f, w in tones)
  sound = sound * numpy.exp(-t / decay) * (1.0 - numpy.exp(-t / 0.0005))
  return sound / max(1e-9, numpy.abs(sound).max())


def clickOf(rate: int) -> numpy.ndarray:
  """Returns a key's click: in (a sharp tick and a little ring), out 70
  ms later (softer); 0.12 s."""
  down = 0.7 * _burst(rate, 0.02, 3500.0, 1.2, 0.002, 1) + 0.3 * _ring(
    rate, 0.02, ((2200.0, 1.0), (5100.0, 0.4)), 0.006)
  up = 0.5 * _burst(rate, 0.02, 4200.0, 1.5, 0.0015, 2)
  sound = numpy.zeros(int(0.12 * rate))
  sound[:len(down)] += down
  at = int(0.07 * rate)
  sound[at:at + len(up)] += up
  return 0.5 * sound


def snapOf(rate: int) -> numpy.ndarray:
  """Returns a switch's snap: a hard metallic click with a short ring;
  0.06 s."""
  sound = 0.6 * _burst(rate, 0.06, 2800.0, 0.9, 0.0025, 3) + 0.4 * _ring(
    rate, 0.06, ((4500.0, 1.0), (7000.0, 0.6), (9200.0, 0.3)), 0.012)
  return 0.6 * sound


def tickOf(rate: int) -> numpy.ndarray:
  """Returns a knob's notch: a small dry tick; 0.02 s."""
  return 0.3 * _burst(rate, 0.02, 5200.0, 2.0, 0.0015, 4)


def relayOf(rate: int) -> numpy.ndarray:
  """Returns a lamp's relay: a soft low click; 0.03 s."""
  return 0.15 * _burst(rate, 0.03, 1200.0, 1.5, 0.004, 5)


def clackOf(rate: int, seed: int) -> numpy.ndarray:
  """Returns a teleprinter's character: the type bar's clack on the
  platen and a thud of the mechanism; 0.05 s."""
  t = numpy.arange(int(0.05 * rate)) / rate
  clack = _burst(rate, 0.05, 1700.0, 1.8, 0.006, 10 + seed)
  thud = numpy.sin(2.0 * math.pi * 160.0 * t) * numpy.exp(-t / 0.012)
  return PRINTER_HUSH * 0.35 * (0.7 * clack + 0.3 * thud)


def returnOf(rate: int) -> numpy.ndarray:
  """Returns a teleprinter's carriage return: a whirr swept down and a
  clunk at its end; 0.3 s."""
  random = numpy.random.default_rng(20)
  t = numpy.arange(int(0.3 * rate)) / rate
  noise = random.standard_normal(len(t))
  whirr = numpy.zeros(len(t))
  state = numpy.zeros(2)
  for start in range(0, len(t), 256):
    part = slice(start, start + 256)
    b, a = bandOf(rate, 900.0 - 1500.0 * t[start], 2.0)
    whirr[part], state = lfilter(b, a, noise[part], -1, state)
  whirr *= numpy.sin(math.pi * numpy.minimum(1.0, t / 0.25)) ** 0.5
  whirr /= max(1e-9, numpy.abs(whirr).max())
  clunk = numpy.zeros(len(t))
  at = int(0.25 * rate)
  tail = _burst(rate, 0.05, 700.0, 1.2, 0.01, 21)
  clunk[at:at + len(tail)] = tail[:len(clunk) - at]
  return PRINTER_HUSH * 0.3 * (0.6 * whirr + 0.6 * clunk)


def bellOf(rate: int) -> numpy.ndarray:
  """Returns the teleprinter's bell: a bright ding dying away; 1 s."""
  return PRINTER_HUSH * 0.35 * _ring(rate, 1.0, (
    (2350.0, 1.0), (4700.0, 0.35), (7050.0, 0.15), (3200.0, 0.2)), 0.35)


def clunkOf(rate: int, seed: int) -> numpy.ndarray:
  """Returns a deck's solenoid pulling in: a heavy thud and a hard
  click on top; 0.12 s."""
  t = numpy.arange(int(0.12 * rate)) / rate
  thud = numpy.sin(2.0 * math.pi * (95.0 - 120.0 * t) * t) * numpy.exp(
    -t / 0.025)
  click = numpy.zeros(len(t))
  hit = _burst(rate, 0.04, 2400.0, 1.1, 0.004, 30 + seed)
  click[:len(hit)] = hit
  return 0.55 * (0.6 * thud + 0.5 * click)


def thudOf(rate: int) -> numpy.ndarray:
  """Returns a thud: something meeting the cabin's padded wall, floor or
  furniture, a dull low knock with a little knock of wood; 0.15 s."""
  t = numpy.arange(int(0.15 * rate)) / rate
  knock = numpy.sin(2.0 * math.pi * (85.0 - 140.0 * t) * t) * numpy.exp(
    -t / 0.035)
  wood = numpy.zeros(len(t))
  hit = _burst(rate, 0.04, 650.0, 1.4, 0.008, 40)
  wood[:len(hit)] = hit
  return 0.8 * knock + 0.3 * wood


def oofOf(rate: int) -> numpy.ndarray:
  """Returns Asger hurt: a short grunt, a voice's buzz falling through a
  vowel's two formants; 0.3 s."""
  t = numpy.arange(int(0.3 * rate)) / rate
  pitch = 150.0 - 60.0 * t / 0.3
  buzz = numpy.sign(numpy.sin(2.0 * math.pi * numpy.cumsum(pitch) / rate))
  voice = numpy.zeros(len(t))
  for middle, weight in ((650.0, 1.0), (1100.0, 0.6)):
    b, a = bandOf(rate, middle, 4.0)
    voice += weight * lfilter(b, a, buzz)
  envelope = numpy.minimum(1.0, t / 0.02) * numpy.exp(-t / 0.12)
  voice *= envelope
  return 0.5 * voice / max(1e-9, numpy.abs(voice).max())


def eatOf(rate: int) -> numpy.ndarray:
  """Returns Asger eating a ration: its pack torn open (a crackle of
  foil), then four chews; 2 s."""
  random = numpy.random.default_rng(50)
  sound = numpy.zeros(int(2.0 * rate))
  tear = int(0.45 * rate)
  b, a = bandOf(rate, 3800.0, 0.8)
  crackle = lfilter(b, a, random.standard_normal(tear) * (
    random.random(tear) < 0.25))
  crackle *= numpy.sin(math.pi * numpy.arange(tear) / tear)
  sound[:tear] += 0.35 * crackle / max(1e-9, numpy.abs(crackle).max())
  for k in range(4):
    at = int((0.7 + 0.32 * k) * rate)
    chew = _burst(rate, 0.16, 420.0 + 40.0 * k, 1.2, 0.04, 51 + k)
    sound[at:at + len(chew)] += 0.4 * chew[:len(sound) - at]
  return sound


def motorOf(rate: int, length: float) -> numpy.ndarray:
  """Returns the deck's capstan motor spinning up over 'length' s: a hum
  rising from 30 to 120 Hz with its overtones, swelling in."""
  t = numpy.arange(int(length * rate)) / rate
  share = numpy.minimum(1.0, t / length)
  phase = 2.0 * math.pi * numpy.cumsum(30.0 + 90.0 * share ** 0.7) / rate
  hum = numpy.sin(phase) + 0.4 * numpy.sin(2.0 * phase) + 0.2 * numpy.sin(
    3.0 * phase)
  return 0.06 * hum * numpy.minimum(1.0, t / 0.3)


def leadInOf(rate: int) -> list:
  """Returns the deck's start (user, 2026-11-16: "when it starts
  playing, have it make a bunch of clicky sounds to get Asger's
  attention. just until the music starts"): each sound and when it
  begins, s, all within 'LEAD_IN': solenoids clunking, relays and the
  counter clicking, the pinch roller, the motor spinning up under
  them."""
  clicks = ((0.0, clunkOf(rate, 0)), (0.18, relayOf(rate) * 3.0),
            (0.38, snapOf(rate)), (0.52, tickOf(rate) * 2.0),
            (0.65, tickOf(rate) * 2.0), (0.78, tickOf(rate) * 2.0),
            (1.0, clunkOf(rate, 1)), (1.22, clickOf(rate)),
            (1.4, relayOf(rate) * 3.0), (1.62, snapOf(rate)),
            (1.78, clunkOf(rate, 2) * 0.7))
  return list(clicks) + [(0.2, motorOf(rate, LEAD_IN - 0.2))]


def _mixedOut(shots: list, count: int) -> tuple:
  """Returns the next 'count' samples of 'shots' playing (each its
  samples and where it is: below nought, not begun yet) and those still
  playing after them."""
  sound = numpy.zeros(count)
  kept = []
  for shot in shots:
    samples, at = shot
    begin = max(0, -at)
    part = samples[max(0, at):max(0, at + count)]
    sound[begin:begin + len(part)] += part[:count - begin]
    shot[1] = at + count
    if shot[1] < len(samples):
      kept.append(shot)
  return sound, kept


def tapeOf(path: object, rate: int) -> numpy.ndarray | None:
  """Returns the tape at 'path' decoded to mono at 'rate' (ffmpeg),
  peak about one; None if it would not decode."""
  ffmpeg = shutil.which('ffmpeg')
  if path is None or ffmpeg is None:
    return None
  done = subprocess.run([ffmpeg, '-v', 'error', '-i', str(path), '-f',
                         'f32le', '-ac', '1', '-ar', str(rate), '-'],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  if done.returncode != 0 or not done.stdout:
    return None
  sound = numpy.frombuffer(done.stdout, numpy.float32).astype(
    numpy.float64)
  return sound / max(1e-9, numpy.abs(sound).max())


class CabinMixer:
  """
  CabinMixer makes 'count' samples at a time at 'rate' a second
  ('samples', told what is going on as 'TOLD' numbers): the engine's
  roar (brown noise, its brightness growing with the air, crackling,
  a deep throb under it) heard whole outside and as a low rumble
  inside, its loudness and the ear's place eased; the cabin's hum,
  inside; one of each click, snap, tick, relay, clack, carriage return
  and bell as their counts grow; the slide's swish; the tape (decoded
  on a thread of its own as the mixer starts) while it plays, from its
  beginning each time it was rewound, faded in and out.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, rate: int, seed: int = 0) -> None:
    self.rate, self.random = rate, numpy.random.default_rng(seed)
    self.time, self.engine, self.inside = 0.0, 0.0, 1.0
    self.filters = {name: numpy.zeros(2) for name in (
      'roar', 'bright', 'rumble', 'crackle', 'hum', 'swish')}
    self.brown = numpy.zeros(1)
    self.shots = {'clicks': clickOf(rate), 'snaps': snapOf(rate),
                  'ticks': tickOf(rate), 'relays': relayOf(rate),
                  'returns': returnOf(rate), 'bells': bellOf(rate),
                  'thuds': thudOf(rate), 'hurts': oofOf(rate),
                  'eats': eatOf(rate)}
    self.clacks = [clackOf(rate, k) for k in range(4)]
    self.playing, self.seen = [], None
    self.tape, self.tapeAt, self.tapeGain, self.rewound = None, 0, 0.0, None
    self.leadIn, self.leads = leadInOf(rate), []
    self.announced, self.decked = None, None
    self._decoding = threading.Thread(target=self._decoded, daemon=True)
    self._decoding.start()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def samples(self, told: object, count: int) -> numpy.ndarray:
    """The 'samples' method returns the next 'count' samples as 'told'
    says what is going on."""
    told = [float(x) for x in told]
    t = self.time + numpy.arange(count) / self.rate
    share = 1.0 - math.exp(-count / (self.rate * EASE))
    self.engine += share * (told[ENGINE] - self.engine)
    self.inside += share * (told[INSIDE] - self.inside)
    sound = self._roar(told[AIR], count, t)
    sound += self.inside * self._hum(count, t)
    sound += self._shots(told, count)
    sound += self._swish(told[SLIDE], count)
    sound += self._announcedOf(told, count)
    sound += self._taped(told[DECK] > 0.5, told[REWINDS], count)
    self.time += count / self.rate
    return numpy.tanh(told[VOLUME] * sound)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _decoded(self, ) -> None:
    """Decodes the tape (on a thread of its own)."""
    from ._tapedeck import tapeFile
    self.tape = tapeOf(tapeFile(), self.rate)

  def _filtered(self, name: str, coefficients: tuple,
                noise: numpy.ndarray) -> numpy.ndarray:
    """Returns 'noise' through the filter 'name' (its state kept)."""
    b, a = coefficients
    out, self.filters[name] = lfilter(b, a, noise, -1, self.filters[name])
    return out

  def _roar(self, air: float, count: int,
            t: numpy.ndarray) -> numpy.ndarray:
    """Returns the engine: outside, brown noise roaring (brighter the
    thicker the air), crackle and a throb; inside, the roar's low
    rumble only, quieter."""
    engine = self.engine
    if engine < 1e-4:
      return numpy.zeros(count)
    white = self.random.standard_normal(count)
    brown, self.brown = lfilter((0.06,), (1.0, -0.995), white, -1,
                                self.brown)
    roar = self._filtered('roar', lowOf(self.rate, 380.0), brown)
    bright = self._filtered('bright', bandOf(
      self.rate, 900.0 + 900.0 * air, 0.8), white) * (0.15 + 0.35 * air)
    sparks = (self.random.random(count) < 90.0 / self.rate) * (
      self.random.standard_normal(count))
    crackle = self._filtered('crackle', bandOf(self.rate, 3200.0, 1.0),
                             sparks) * 3.0
    throb = numpy.sin(2.0 * math.pi * 38.0 * t) * (
      1.0 + 0.3 * numpy.sin(2.0 * math.pi * 3.1 * t))
    outside = 1.2 * roar + bright + 0.25 * crackle + 0.3 * throb
    rumble = self._filtered('rumble', lowOf(self.rate, 110.0), brown)
    inside = 0.9 * rumble + 0.12 * throb
    ear = self.inside
    return engine * ((1.0 - ear) * outside + ear * 0.3 * inside)

  def _hum(self, count: int, t: numpy.ndarray) -> numpy.ndarray:
    """Returns the cabin's hum: a fan's soft air and the mains under
    it."""
    fan = self._filtered('hum', bandOf(self.rate, 420.0, 0.7),
                         self.random.standard_normal(count))
    mains = numpy.sin(2.0 * math.pi * 100.0 * t) + 0.4 * numpy.sin(
      2.0 * math.pi * 200.0 * t)
    return 0.006 * fan + 0.004 * mains

  def _swish(self, slide: float, count: int) -> numpy.ndarray:
    """Returns the slide's swish, as loud as it moves fast."""
    if slide < 1e-3:
      return numpy.zeros(count)
    noise = self.random.standard_normal(count)
    return 0.08 * slide * self._filtered('swish', bandOf(
      self.rate, 2600.0, 1.4), noise)

  def _shots(self, told: list, count: int) -> numpy.ndarray:
    """Returns the clicks, snaps, ticks, relays, clacks, carriage returns,
    bells, thuds (each as loud as it was hard), Asger's grunts and meals
    playing, one more of
    each started as its count grows (the first counts heard are taken as
    they are)."""
    counts = {'clicks': told[CLICKS], 'snaps': told[SNAPS],
              'ticks': told[TICKS], 'relays': told[RELAYS],
              'typed': told[TYPED], 'returns': told[RETURNS],
              'bells': told[BELLS], 'thuds': told[THUDS],
              'hurts': told[HURTS], 'eats': told[EATS]}
    hard = min(1.0, told[THUD] / LOUDEST)
    if self.seen is None:
      self.seen = dict(counts)
    for name, value in counts.items():
      grown = int(value - self.seen[name])
      for k in range(min(grown, 4)):
        if name == 'typed':
          shot = self.clacks[int(value - k) % len(self.clacks)]
        elif name == 'thuds':
          shot = self.shots[name] * (0.15 + 0.85 * hard)
        else:
          shot = self.shots[name]
        self.playing.append([shot, -int(k * 0.02 * self.rate)])
    self.seen = dict(counts)
    sound, self.playing = _mixedOut(self.playing, count)
    return sound

  def _announcedOf(self, told: list, count: int) -> numpy.ndarray:
    """Returns the deck getting ready (user, 2026-11-16: "The tape
    clickies are only when the tape gets ready to play music to draw
    your attention to it"): its lead-in started each time it is
    announced (the first count heard taken as it is), stopped the moment
    the music starts."""
    announced, playing = told[ANNOUNCED], told[DECK] > 0.5
    if self.announced is not None and announced > self.announced:
      self.leads = [[shot, -int(at * self.rate)] for at, shot in
                    self.leadIn]
    if self.decked is not None and playing and not self.decked:
      self.leads = []
    self.announced, self.decked = announced, playing
    sound, self.leads = _mixedOut(self.leads, count)
    return sound

  def _taped(self, playing: bool, rewinds: float,
             count: int) -> numpy.ndarray:
    """Returns the tape while it plays, from its beginning each time it
    was rewound, faded in and out."""
    if self.rewound is None:
      self.rewound = rewinds
    if rewinds != self.rewound:
      self.rewound, self.tapeAt = rewinds, 0
    tape = self.tape
    want = TAPE_GAIN if playing and tape is not None else 0.0
    if want == 0.0 and self.tapeGain < 1e-4:
      self.tapeGain = 0.0
      return numpy.zeros(count)
    share = 1.0 - math.exp(-count / (self.rate * TAPE_FADE))
    gain = self.tapeGain + share * (want - self.tapeGain)
    self.tapeGain = gain
    if tape is None:
      return numpy.zeros(count)
    part = tape[self.tapeAt:self.tapeAt + count]
    self.tapeAt += count
    out = numpy.zeros(count)
    out[:len(part)] = gain * part
    return out
