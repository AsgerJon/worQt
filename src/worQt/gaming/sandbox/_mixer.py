"""
Mixer makes the sandbox's sound, Qt-free, block by block (user,
2026-11-16: "We need some ambient sounds. Some rail sounds. The grav
gun needs some humming that is different when it is holding an item
... When launching the held item, give a nice yeet sound. When punting
an item, give a less sophistacated sound."): all of it made here from
noise and tones (nothing recorded), mono, between -1 and 1.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
from scipy.signal import lfilter

#  What the mixer is told, by place in its list: the volume, the wind
#  (nought to one), the rails' (the vehicle's speed, m/s, how loud it is
#  where the avatar is, nought to one, its wheels' load over standing,
#  their flanges' share of it), the gun's hum (0 none, 1 idle, 2
#  holding), how many yeets and punts there have been (each one more
#  plays one), how loud the ambience's pad is (nought to one).
VOLUME, WIND, RAIL_SPEED, RAIL_GAIN, RAIL_LOAD, RAIL_FLANGE = range(6)
HUM, YEETS, PUNTS, PAD = 6, 7, 8, 9
TOLD = 10
#  The ambience (user, 2026-11-16: "a little less Vesterhavet and a
#  little more chill"): a soft breeze, dark and slow to gust (its gusts
#  between 'GUSTS', a new one every 'GUSTING' s or so, low passed
#  'BREEZE' Hz plus as much again the stronger the gust), and a pad
#  under it: a Cmaj7 chord of sines ('CHORD', Hz), each note swelling on
#  its own over 'SWELLS' s.
GUSTS, GUSTING, BREEZE = (0.45, 0.75), 6.0, (150.0, 300.0)
CHORD = (130.81, 164.81, 196.0, 246.94)
SWELLS = (17.0, 23.0, 29.0, 13.0)
#  How fast the hum fades between its sounds, s; how far the flanges'
#  squeal wavers about its 3.1 kHz, five times a second, Hz.
FADE = 0.12
VIBRATO = 40.0


def bandOf(rate: int, middle: float, sharp: float) -> tuple:
  """Returns a band pass (RBJ's biquad, peak gain one) at 'middle' Hz of
  sharpness 'sharp' (Q), as filter coefficients (b, a)."""
  w = 2.0 * math.pi * min(middle, 0.45 * rate) / rate
  alpha = math.sin(w) / (2.0 * sharp)
  a0 = 1.0 + alpha
  return (numpy.array((alpha, 0.0, -alpha)) / a0,
          numpy.array((1.0, -2.0 * math.cos(w) / a0, (1.0 - alpha) / a0)))


def lowOf(rate: int, cut: float) -> tuple:
  """Returns a low pass (RBJ's biquad, Q 0.707) at 'cut' Hz as filter
  coefficients (b, a)."""
  w = 2.0 * math.pi * min(cut, 0.45 * rate) / rate
  alpha = math.sin(w) / math.sqrt(2.0)
  cosine = math.cos(w)
  a0 = 1.0 + alpha
  b = numpy.array((0.5 * (1.0 - cosine), 1.0 - cosine,
                   0.5 * (1.0 - cosine))) / a0
  return b, numpy.array((1.0, -2.0 * cosine / a0, (1.0 - alpha) / a0))


def yeetOf(rate: int) -> numpy.ndarray:
  """Returns the yeet (a held thing launched): a zap falling from 1.6
  kHz, a whoosh of air swept down from 2.5 kHz, a thump under it;
  0.7 s."""
  random = numpy.random.default_rng(7)
  t = numpy.arange(int(0.7 * rate)) / rate
  pitch = 1600.0 * 0.18 ** (t / 0.35)
  zap = numpy.sin(2.0 * math.pi * numpy.cumsum(pitch) / rate) * (
    (1.0 - numpy.exp(-t / 0.004)) * numpy.exp(-t / 0.18))
  noise = random.standard_normal(len(t))
  whoosh = numpy.zeros(len(t))
  state = numpy.zeros(2)
  for start in range(0, len(t), 256):
    part = slice(start, start + 256)
    middle = 2500.0 * (350.0 / 2500.0) ** (t[start] / 0.7)
    b, a = bandOf(rate, middle, 1.5)
    whoosh[part], state = lfilter(b, a, noise[part], -1, state)
  whoosh *= numpy.sin(math.pi * t / 0.7) ** 1.5
  thump = numpy.sin(2.0 * math.pi * 55.0 * t) * numpy.exp(-t / 0.08)
  sound = 0.35 * zap + 0.3 * whoosh / max(1e-9, numpy.abs(whoosh).max())
  sound += 0.4 * thump
  return 0.8 * sound / numpy.abs(sound).max()


def puntOf(rate: int) -> numpy.ndarray:
  """Returns the punt (a plain shove): a dull thud falling from 110 to
  50 Hz with a click; 0.2 s."""
  random = numpy.random.default_rng(11)
  t = numpy.arange(int(0.2 * rate)) / rate
  pitch = 110.0 * (50.0 / 110.0) ** (t / 0.2)
  thud = numpy.sin(2.0 * math.pi * numpy.cumsum(pitch) / rate) * (
    numpy.exp(-t / 0.05))
  b, a = lowOf(rate, 2000.0)
  click = lfilter(b, a, random.standard_normal(len(t))) * numpy.exp(
    -t / 0.004)
  sound = 0.6 * thud + 0.3 * click / max(1e-9, numpy.abs(click).max())
  return 0.6 * sound / numpy.abs(sound).max()


class Mixer:
  """
  Mixer makes 'count' samples at a time at 'rate' a second ('samples',
  told what is going on as 'TOLD' numbers): the wind (noise, low passed
  where it gusts, gusting at random); the rails (a rumble rising with
  the speed, a ring of the wheels
  growing with the speed squared, a squeal as the flanges bear), as
  loud as the avatar hears them; the gun's hum (idle: low and steady;
  holding: higher, warbling, crackling), faded from one to the other;
  and, once each, a yeet or a punt as their counts grow. Each sound
  goes on where the last block left it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, rate: int, seed: int = 0) -> None:
    self.rate, self.random = rate, numpy.random.default_rng(seed)
    self.time = 0.0
    self.gust, self.gusting = 0.5, 0.5
    self.idle, self.holding = 0.0, 0.0
    self.filters = {name: numpy.zeros(2) for name in (
      'wind', 'rumble', 'ring', 'crackle')}
    self.yeet, self.punt = yeetOf(rate), puntOf(rate)
    self.playing, self.seen = [], None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def samples(self, told: object, count: int) -> numpy.ndarray:
    """The 'samples' method returns the next 'count' samples as 'told'
    says what is going on."""
    told = [float(x) for x in told]
    t = self.time + numpy.arange(count) / self.rate
    sound = self._wind(told[WIND], count, t)
    sound += self._pad(told[PAD], t)
    sound += self._rails(told, count, t)
    sound += self._hum(int(round(told[HUM])), count, t)
    sound += self._shots(told[YEETS], told[PUNTS], count)
    self.time += count / self.rate
    return numpy.tanh(told[VOLUME] * sound)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _filtered(self, name: str, coefficients: tuple,
                noise: numpy.ndarray) -> numpy.ndarray:
    """Returns 'noise' through the filter 'name' (its state kept)."""
    b, a = coefficients
    out, self.filters[name] = lfilter(b, a, noise, -1, self.filters[name])
    return out

  def _wind(self, wind: float, count: int,
            t: numpy.ndarray) -> numpy.ndarray:
    """Returns the breeze: noise low passed, darker the calmer, as it
    gusts (a slow walk toward a new gust every 'GUSTING' s or so)."""
    least, most = GUSTS
    if self.random.random() < count / (GUSTING * self.rate):
      self.gusting = least + (most - least) * self.random.random()
    start = self.gust
    self.gust += (self.gusting - self.gust) * min(
      1.0, 0.3 * count / self.rate)
    level = numpy.linspace(start, self.gust, count)
    cut = BREEZE[0] + BREEZE[1] * self.gust
    air = self._filtered('wind', lowOf(self.rate, cut),
                         self.random.standard_normal(count))
    return 0.3 * wind * level * air

  def _pad(self, pad: float, t: numpy.ndarray) -> numpy.ndarray:
    """Returns the pad: the chord's notes, each a sine with a little of
    its octave, swelling slowly on its own."""
    if pad <= 0.0:
      return numpy.zeros(len(t))
    two = 2.0 * math.pi
    sound = numpy.zeros(len(t))
    for k, (note, swell) in enumerate(zip(CHORD, SWELLS)):
      level = 0.5 + 0.5 * numpy.sin(two * t / swell + 1.7 * k)
      sound += level * (numpy.sin(two * note * t)
                        + 0.2 * numpy.sin(two * 2.0 * note * t))
    return 0.012 * pad * sound

  def _rails(self, told: list, count: int,
             t: numpy.ndarray) -> numpy.ndarray:
    """Returns the rails' sound: a rumble, the wheels' ring, the flanges'
    squeal (none standing). No beat at the sleepers (user, 2026-11-16:
    "Why does the engine-less cart sounds like it has playing cards in
    its spokes??": a sleeper's beat every 0.6 m flapped 10-35 times a
    second; welded rail on sleepers roars smooth)."""
    speed, gain = told[RAIL_SPEED], told[RAIL_GAIN]
    load, flange = max(0.0, told[RAIL_LOAD]), told[RAIL_FLANGE]
    noise = self.random.standard_normal(count)
    rumble = self._filtered('rumble', bandOf(self.rate, 60.0 + 5.0 * speed,
                                             0.8), noise)
    ring = self._filtered('ring', bandOf(self.rate, 1800.0 + 40.0 * speed,
                                         12.0), noise)
    if speed < 0.05 or gain <= 0.0:
      return numpy.zeros(count)
    sound = 0.9 * min(1.0, speed / 15.0) * math.sqrt(load) * rumble
    sound += 0.5 * min(1.0, (speed / 20.0) ** 2) * ring
    squeal = numpy.sin(2.0 * math.pi * (3100.0 * t - VIBRATO / (
      2.0 * math.pi * 5.0) * numpy.cos(2.0 * math.pi * 5.0 * t)))
    sound += 0.08 * min(1.0, 3.0 * flange) * min(1.0, speed / 5.0) * (
      squeal)
    return gain * sound

  def _hum(self, hum: int, count: int, t: numpy.ndarray) -> numpy.ndarray:
    """Returns the gun's hum, faded from idle to holding and back over
    'FADE' s."""
    step = count / (self.rate * FADE)
    idle0, hold0 = self.idle, self.holding
    self.idle += max(-step, min(step, (1.0 if hum == 1 else 0.0) - idle0))
    self.holding += max(-step, min(step, (1.0 if hum == 2 else 0.0)
                                   - hold0))
    noise = self.random.standard_normal(count)
    crackle = self._filtered('crackle', bandOf(self.rate, 520.0, 4.0),
                             noise)
    idle = numpy.linspace(idle0, self.idle, count)
    holding = numpy.linspace(hold0, self.holding, count)
    two = 2.0 * math.pi
    low = (numpy.sin(two * 55.0 * t) + 0.5 * numpy.sin(two * 110.0 * t)
           + 0.25 * numpy.sin(two * 165.0 * t)) * (
      1.0 + 0.15 * numpy.sin(two * 1.5 * t))
    high = (numpy.sin(two * 78.0 * t) + 0.6 * numpy.sin(two * 156.0 * t)
            + 0.4 * numpy.sin(two * 234.0 * t)) * (
      1.0 + 0.35 * numpy.sin(two * 7.0 * t)) + 1.5 * crackle
    return 0.03 * idle * low + 0.05 * holding * high

  def _shots(self, yeets: float, punts: float,
             count: int) -> numpy.ndarray:
    """Returns the yeets and punts playing, one more of each started as
    its count grows (the first counts heard are taken as they are)."""
    if self.seen is None:
      self.seen = (yeets, punts)
    if yeets > self.seen[0]:
      self.playing.append([self.yeet, 0])
    if punts > self.seen[1]:
      self.playing.append([self.punt, 0])
    self.seen = (yeets, punts)
    sound = numpy.zeros(count)
    kept = []
    for shot in self.playing:
      samples, at = shot
      part = samples[at:at + count]
      sound[:len(part)] += part
      shot[1] = at + count
      if shot[1] < len(samples):
        kept.append(shot)
    self.playing = kept
    return sound
