"""
An engine heard as AngeTheGreat's Engine Simulator hears one (user,
2026-11-14: "surely someone has solved the problem of fucking engine
sounds?"; "AngeTheGreat, use his stuff"; "Naturally aspirated V12
pls"): engine-sim (https://github.com/ange-yaghi/engine-sim, MIT,
Copyright 2022 AngeTheGreat, Ange Yaghi) simulates the gas through an
engine (the air through the throttle into the plenum, down each
runner, through the intake valve as its cam lifts it, compressed by
the piston, burnt, out through the exhaust valve into the exhaust
runner and the collector and out of the tailpipe), and hears it: each
exhaust runner's pressure over the air's, summed, through a short
chain of filters and a convolution with an impulse response recorded
off a real exhaust (his sound library; 'sounds/', his licence beside
them). Ported here in part, on Warp (one CPU thread, in the sound's
own process: the gas wants 20 000 steps a second, too many for
Python): his compressible orifice flow between volumes, choked or not
('flowRate'), his flow constants from flow-bench ratings ('kCarb',
'k28'), his harmonic cam lobes and port flow tables, the crank and
rods; a Wiebe burn for his flame model; no gas momentum (his volumes
carry it, for ram effects) and a plain cooling for his heat transfer.
His synthesizer as he wrote it: the input low passed at 1.9 kHz,
jittered, its DC taken off, a little of its derivative mixed in, its
flow textured by air noise, convolved with the impulse response, low
passed, levelled.

The engine: a naturally aspirated V12 after a 1980s Lamborghini's (its
figures: a 60 degree vee, 85.5 by 75 mm, 5.2 litres, 9.5 to 1), laid out
as his Ferrari 412 T2 is (a six throw crank, 0 120 240 240 120 0, each
bank fired 60 degrees after the other: one cylinder every 60 degrees),
on his Ferrari's port flows, a road car's cams, one plenum and one
exhaust to a bank, his 'minimal_muffling_01' heard through.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os
import wave
from typing import NamedTuple

import numpy

#  The gas: its constant, J/(mol K); its heat capacity ratio (five
#  degrees of freedom, as his air); the air's pressure, Pa, and
#  temperature, K; the walls' temperature the cylinders and runners
#  cool toward, K, and how fast, s.
GAS_R, GAMMA = 8.314462618, 1.4
P_ATM, T_ATM = 101325.0, 298.15
T_WALL, COOLING = 420.0, 0.02
#  The fuel: its heating value, J/kg; the air's to the fuel's mass (as
#  his engines' mixture: rich of stoichiometric a little); a mole of air
#  and fuel's mass, kg; how much of it burns (his 'max_burning_
#  efficiency'); the burn's length, degrees of crank (a Wiebe curve's,
#  for his flame).
HEATING, AIR_FUEL, MOLAR_MASS, BURNT = 44.4e6, 13.5, 0.0289, 0.75
BURN = 50.0
#  How much each burn differs from the last, a share (its heat, its
#  length): a real engine's cycle to cycle spread, the good noise (user,
#  2026-11-14: "it feels noisy, and not in the good way": the synthetic
#  hiss of his air noise and jitter, turned down for this).
SPREAD_HEAT, SPREAD_BURN = 0.03, 0.05
#  How the sound is made (his): its rate, samples a second; the input's
#  low pass, Hz; the jitter's longest, samples, and its noise's low
#  pass, Hz; the DC's, Hz; the air noise's low pass, Hz; the output's
#  low pass (a share of the rate); the leveller's target, most and
#  least gain (in 16-bit steps).
INPUT_PASS, JITTER_MOST, JITTER_PASS, DC_PASS = 1900.0, 10, 10000.0, 10.0
AIR_PASS, OUTPUT_PASS = 2000.0, 0.45
LEVEL_TARGET, LEVEL_MOST, LEVEL_LEAST = 30000.0, 1.9, 1e-5
#  How slowly the leveller's gain follows, s (his follows every sample,
#  a quarter of a millisecond behind: on these pulses it pumped inside
#  each one; the user, 2026-11-14: "it feels noisy, and not in the good
#  way").
LEVEL_SLOW = 0.3
#  How loud the levelled sound is played: idling, and more with
#  revolutions (at 'LOUDEST' rpm) and with throttle (his leveller holds
#  every engine as loud idling as flat out: his app's volume does the
#  rest; and half way to the top, its transients clipped at the top).
QUIET, WITH_RPM, WITH_LOAD, LOUDEST = 0.25, 0.15, 0.1, 7500.0
#  Where his impulse responses are.
SOUNDS = os.path.join(os.path.dirname(__file__), 'sounds')
UNITS_INCH, UNITS_THOU = 0.0254, 0.0000254


class Lobe(NamedTuple):
  """Lobe is a harmonic cam lobe (his 'harmonic_cam_lobe'): its
  duration at 50 thou of lift, degrees of crank; its shape's power; its
  lift, m."""

  duration: float
  gamma: float
  lift: float


class EngineSpec(NamedTuple):
  """
  EngineSpec is an engine as his scripts give one: its cylinders' places
  in the 720 degree cycle (each fires at its own nought; its piston at
  the top there and at 360), bore, stroke and rod, m, its compression
  ratio; each cylinder's bank (its plenum and exhaust); its intake and
  exhaust runners' volumes, m^3; its ports' flow tables (cfm at 28 inches
  of water by lift, every 50 thou); its intake and exhaust lobes and
  their centres from the overlap's top, degrees; each bank's plenum's
  volume, m^3, and the flow ratings (cfm, his 'k_carb') of each bank's
  throttle, each runner, each header's primary and each exhaust's
  outlet; each exhaust's volume, m^3, and primaries' length, m; each
  cylinder's sound's share ('sound_attenuation') and its exhausts'
  ('audio_volume'); its spark's advance
  idling and at speed, degrees; his synthesizer's settings for it (the
  derivative's share, 'hf_gain'; the air noise's, 'noise'; the jitter's,
  'jitter'); its impulse response's file and volume; the gas's steps a
  second.
  """

  phases: tuple
  bore: float
  stroke: float
  rod: float
  compression: float
  banks: tuple
  intakeRunner: float
  exhaustRunner: float
  intakeFlow: tuple
  exhaustFlow: tuple
  intakeLobe: Lobe
  exhaustLobe: Lobe
  intakeCentre: float
  exhaustCentre: float
  plenum: float
  throttle: float
  runner: float
  primary: float
  outlet: float
  exhaust: float
  primaryLength: float
  shares: tuple
  audioVolume: float
  advance: tuple
  hfGain: float
  noise: float
  jitter: float
  response: str
  responseVolume: float
  rate: float


_BANK = (0.0, 480.0, 240.0, 600.0, 120.0, 360.0)
V12 = EngineSpec(
  _BANK + tuple(phase + 60.0 for phase in _BANK), 0.0855, 0.075, 0.130,
  9.5, (0,) * 6 + (1,) * 6, 149.6e-6, 50.0e-6,
  (0, 58, 103, 156, 214, 249, 268, 280, 280, 281),
  (0, 37, 72, 113, 160, 196, 222, 235, 245, 246),
  Lobe(252.0, 0.8, 10.5e-3), Lobe(256.0, 0.8, 10.0e-3), 108.0, 112.0,
  1.5e-3, 900.0, 220.0, 220.0, 1500.0, 40e-3, 20.0 * UNITS_INCH,
  (0.5, 1.0, 0.75, 0.9, 0.7, 1.0, 0.5, 0.3, 0.8, 1.2, 0.9, 0.7), 0.004,
  (12.0, 34.0), 0.01, 0.05, 0.0, 'minimal_muffling_01.wav', 0.01,
  40000.0)


def molesPerSecond(scfm: float) -> float:
  """Returns 'scfm' standard cubic feet a minute in moles a second (at
  one atmosphere and 20 degrees)."""
  return scfm * 0.028316846592 / 60.0 * P_ATM / (GAS_R * 293.15)


def flowConstant(rate: float, pressure: float, drop: float,
                 temperature: float) -> float:
  """The 'flowConstant' function returns the flow constant that passes
  'rate' mol/s at 'pressure' Pa less 'drop' Pa downstream, the gas at
  'temperature' K (his 'GasSystem::flowConstant')."""
  ratio = (pressure - drop) / pressure
  choked = (2.0 / (GAMMA + 1.0)) ** (GAMMA / (GAMMA - 1.0))
  if ratio <= choked:
    flow = math.sqrt(GAMMA) * (2.0 / (GAMMA + 1.0)) ** (
      (GAMMA + 1.0) / (2.0 * (GAMMA - 1.0)))
  else:
    flow = math.sqrt(2.0 * GAMMA / (GAMMA - 1.0) * (
      1.0 - ratio ** ((GAMMA - 1.0) / GAMMA))) * ratio ** (1.0 / GAMMA)
  return rate / (flow * pressure / math.sqrt(GAS_R * temperature))


def kCarb(scfm: float) -> float:
  """Returns the flow constant of a part rated 'scfm' at 1.5 inches of
  mercury (his 'k_carb')."""
  return flowConstant(molesPerSecond(scfm), P_ATM, 5079.5, T_ATM)


def k28(scfm: float) -> float:
  """Returns the flow constant of a port rated 'scfm' at 28 inches of
  water (his 'k_28inH2O')."""
  return flowConstant(molesPerSecond(scfm), P_ATM, 6974.4, T_ATM)


def lobeLift(lobe: Lobe, off: float) -> float:
  """Returns 'lobe''s lift 'off' degrees of crank from its centre, m
  (his '_generate_harmonic_cam_lobe', in the camshaft's degrees, half
  the crank's)."""
  angle = math.radians(lobe.duration / 4.0)
  s = (2.0 * 50.0 * UNITS_THOU / lobe.lift) ** (1.0 / lobe.gamma) - 1.0
  k = math.acos(max(-1.0, min(1.0, s))) / angle
  x = abs(math.radians(off / 2.0))
  if x >= math.pi / k:
    return 0.0
  return lobe.lift * (0.5 + 0.5 * math.cos(k * x)) ** lobe.gamma


def portConstant(table: tuple, lift: float) -> float:
  """Returns a port's flow constant at 'lift' m, its 'table' (cfm every
  50 thou) drawn straight between."""
  at = lift / (50.0 * UNITS_THOU)
  low = min(int(at), len(table) - 2)
  share = min(at - low, 1.0)
  return k28(table[low] + (table[low + 1] - table[low]) * share)


def valveTables(spec: EngineSpec, steps: int = 1440) -> tuple:
  """The 'valveTables' function returns the intake's and the exhaust's
  flow constants through a cylinder's 720 degree cycle, 'steps' samples
  (its firing at nought: the exhaust's lobe 'exhaustCentre' before the
  overlap's top at 360, the intake's 'intakeCentre' after)."""
  intake, exhaust = numpy.zeros(steps), numpy.zeros(steps)
  for k in range(steps):
    angle = 720.0 * k / steps
    for table, lobe, centre, out in (
        (spec.intakeFlow, spec.intakeLobe, 360.0 + spec.intakeCentre,
         intake),
        (spec.exhaustFlow, spec.exhaustLobe, 360.0 - spec.exhaustCentre,
         exhaust)):
      off = (angle - centre + 360.0) % 720.0 - 360.0
      out[k] = portConstant(table, lobeLift(lobe, off))
  return intake, exhaust


def responseOf(spec: EngineSpec) -> numpy.ndarray:
  """The 'responseOf' function returns the engine's impulse response as
  his synthesizer takes it: cut where it falls under 100 in 16-bit
  steps (10 000 samples at most), times its volume."""
  with wave.open(os.path.join(SOUNDS, spec.response)) as file:
    raw = numpy.frombuffer(file.readframes(file.getnframes()),
                           numpy.int16).astype(numpy.float64)
  loud = numpy.nonzero(numpy.abs(raw) > 100)[0]
  length = min(10000, int(loud[-1]) + 1) if len(loud) else 1
  return spec.responseVolume * raw[:length] / 32767.0


_KERNELS = None


def preloaded() -> None:
  """The 'preloaded' function has the gas's Warp kernel ready on the
  CPU (compiled, or loaded from Warp's cache), so a voice starts at
  once."""
  import warp as wp
  wp.load_module(_kernels().module, 'cpu')


def _kernels() -> object:
  """Returns the gas's Warp kernel, defined once (Warp imported only
  here: in the sound's process)."""
  global _KERNELS
  if _KERNELS is not None:
    return _KERNELS
  import warp as wp
  wp.config.quiet = True
  choked = (2.0 / (GAMMA + 1.0)) ** (GAMMA / (GAMMA - 1.0))
  chokedFactor = math.sqrt(GAMMA) * (2.0 / (GAMMA + 1.0)) ** (
    (GAMMA + 1.0) / (2.0 * (GAMMA - 1.0)))
  CHOKED = wp.constant(choked)
  CHOKED_FACTOR = wp.constant(chokedFactor)
  R = wp.constant(GAS_R)
  G = wp.constant(GAMMA)
  PA = wp.constant(P_ATM)
  EA = wp.constant(2.5 * GAS_R * T_ATM)
  EW = wp.constant(2.5 * GAS_R * T_WALL)

  @wp.func
  def flowRate(k: float, p0: float, p1: float, t0: float,
               t1: float) -> float:
    """His 'GasSystem::flowRate': moles a second from the first to the
    second (below nought: back), choked or not."""
    if k == 0.0:
      return 0.0
    way = float(1.0)
    up = p0
    down = p1
    hot = t0
    if p1 > p0:
      way = -1.0
      up = p1
      down = p0
      hot = t1
    ratio = down / up
    rate = float(0.0)
    if ratio <= CHOKED:
      rate = CHOKED_FACTOR / wp.sqrt(R * hot)
    else:
      s = wp.pow(ratio, 1.0 / G)
      rate = wp.sqrt(wp.max(2.0 * G / (G - 1.0) * s * (s - ratio), 0.0)
                     / (R * hot))
    return way * up * rate * k

  @wp.func
  def moved(n: wp.array(dtype=float), e: wp.array(dtype=float),
            fresh: wp.array(dtype=float), v: wp.array(dtype=float),
            a: int, b: int, k: float, dt: float):
    """Gas flows between volumes 'a' and 'b' for 'dt' through a part of
    flow constant 'k' (its energy and unburnt share with it), no more
    than evens their pressures (his 'pressureEquilibriumMaxFlow': past
    it, a small runner and its cylinder swapped their gas back and forth
    every step, nine steps in ten, a 10 kHz whine drowning the
    firing)."""
    if n[a] <= 0.0 or n[b] <= 0.0:
      return
    pa = e[a] / (2.5 * v[a])
    pb = e[b] / (2.5 * v[b])
    dn = flowRate(k, pa, pb, e[a] / (2.5 * n[a] * R),
                  e[b] / (2.5 * n[b] * R)) * dt
    src = a
    dst = b
    if dn < 0.0:
      src = b
      dst = a
      dn = -dn
    each = e[src] / n[src]
    even = (e[src] * v[dst] - e[dst] * v[src]) / (each * (v[src] + v[dst]))
    dn = wp.min(dn, wp.min(0.9 * n[src], wp.max(even, 0.0)))
    share = dn / n[src]
    de = e[src] * share
    df = fresh[src] * share
    n[src] = n[src] - dn
    e[src] = e[src] - de
    fresh[src] = fresh[src] - df
    n[dst] = n[dst] + dn
    e[dst] = e[dst] + de
    fresh[dst] = fresh[dst] + df

  @wp.func
  def aired(n: wp.array(dtype=float), e: wp.array(dtype=float),
            fresh: wp.array(dtype=float), v: wp.array(dtype=float),
            b: int, k: float, dt: float, mixture: float):
    """Gas flows between the air and volume 'b' (the air coming in
    'mixture' unburnt: through a throttle, all; up a tailpipe, none), no
    more than brings it to the air's pressure."""
    if n[b] <= 0.0:
      return
    pb = e[b] / (2.5 * v[b])
    dn = flowRate(k, PA, pb, EA / (2.5 * R), e[b] / (2.5 * n[b] * R)) * dt
    if dn > 0.0:
      dn = wp.min(dn, wp.max((2.5 * v[b] * PA - e[b]) / EA, 0.0))
      n[b] = n[b] + dn
      e[b] = e[b] + EA * dn
      fresh[b] = fresh[b] + mixture * dn
    else:
      dn = wp.min(-dn, wp.min(0.9 * n[b], wp.max(
        (e[b] - 2.5 * v[b] * PA) / (e[b] / n[b]), 0.0)))
      share = dn / n[b]
      n[b] = n[b] - dn
      e[b] = e[b] - e[b] * share
      fresh[b] = fresh[b] - fresh[b] * share

  @wp.kernel
  def engineRun(n: wp.array(dtype=float), e: wp.array(dtype=float),
                fresh: wp.array(dtype=float), v: wp.array(dtype=float),
                phase: wp.array(dtype=float), bank: wp.array(dtype=int),
                share: wp.array(dtype=float),
                kIn: wp.array(dtype=float), kEx: wp.array(dtype=float),
                burnAt: wp.array(dtype=float),
                burnHeat: wp.array(dtype=float),
                burnFresh: wp.array(dtype=float),
                burnLength: wp.array(dtype=float),
                burnt: wp.array(dtype=float),
                angle: wp.array(dtype=float), shape: wp.vec4,
                flows: wp.vec4, cylinders: int, banks: int, steps: int,
                dt: float, rpm0: float, rpm1: float, open0: float,
                open1: float, advance0: float, advance1: float,
                heat: float, seed: int, out: wp.array(dtype=float)):
    """Steps the engine's gas 'steps' steps of 'dt' s, its revolutions
    and throttle going from the first to the second across them;
    writes the runners' pressures over the air's, each its share,
    summed, a value a step, into 'out' (the volumes: the intake
    runners, the cylinders, the exhaust runners, the plenums, the
    exhausts; 'shape': chamber, piston area, crank's throw, rod;
    'flows': throttle, runner, primary, outlet)."""
    nc = cylinders
    table = kIn.shape[0]
    for step in range(steps):
      along = (float(step) + 0.5) / float(steps)
      rpm = rpm0 + (rpm1 - rpm0) * along
      opened = open0 + (open1 - open0) * along
      advance = advance0 + (advance1 - advance0) * wp.min(rpm / 6000.0,
                                                          1.0)
      was = angle[0]
      now = was + 6.0 * rpm * dt
      if now >= 720.0:
        now = now - 720.0
      angle[0] = now
      plate = 0.9989 * (1.0 - opened)
      throttle = wp.cos(plate * 1.5707963) * flows[0]
      for b in range(banks):
        aired(n, e, fresh, v, 3 * nc + b, throttle, dt, 1.0)
        aired(n, e, fresh, v, 3 * nc + banks + b, flows[3], dt, 0.0)
      for c in range(nc):
        own = now - phase[c]
        if own < 0.0:
          own = own + 720.0
        before = was - phase[c]
        if before < 0.0:
          before = before + 720.0
        at = int(own / 720.0 * float(table)) % table
        cyl = nc + c
        plenum = 3 * nc + bank[c]
        exhaust = 3 * nc + banks + bank[c]
        moved(n, e, fresh, v, plenum, c, flows[1], dt)
        moved(n, e, fresh, v, c, cyl, kIn[at], dt)
        moved(n, e, fresh, v, cyl, 2 * nc + c, kEx[at], dt)
        moved(n, e, fresh, v, 2 * nc + c, exhaust, flows[2], dt)
        crank = wp.radians(own)
        lean = shape[2] * wp.sin(crank)
        drop = shape[2] * (1.0 - wp.cos(crank)) + shape[3] - wp.sqrt(
          shape[3] * shape[3] - lean * lean)
        volume = shape[0] + shape[1] * drop
        e[cyl] = e[cyl] - e[cyl] / (2.5 * v[cyl]) * (volume - v[cyl])
        v[cyl] = volume
        spark = 720.0 - advance
        if before < spark and own >= spark and burnAt[c] < 0.0:
          burnAt[c] = spark
          state = wp.rand_init(seed, step * nc + c)
          burnHeat[c] = fresh[cyl] * heat * (1.0 + SPREAD_H * wp.randn(
            state))
          burnLength[c] = BURN_DEG * (1.0 + SPREAD_B * wp.randn(state))
          burnFresh[c] = fresh[cyl]
          burnt[c] = 0.0
        if burnAt[c] >= 0.0:
          since = own - burnAt[c]
          if since < 0.0:
            since = since + 720.0
          x = 1.0 - wp.exp(-5.0 * wp.pow(since / burnLength[c], 3.0))
          if since > 2.0 * burnLength[c]:
            x = 1.0
          e[cyl] = e[cyl] + burnHeat[c] * (x - burnt[c])
          fresh[cyl] = wp.max(fresh[cyl] - burnFresh[c] * (x - burnt[c]),
                              0.0)
          burnt[c] = x
          if x >= 1.0:
            burnAt[c] = -1.0
        for k in range(3):
          index = k * nc + c
          if k == 1 or k == 2:
            e[index] = e[index] + (EW * n[index] - e[index]) * (
              dt / COOL)
      sound = float(0.0)
      for c in range(nc):
        runner = 2 * nc + c
        sound = sound + share[c] * (e[runner] / (2.5 * v[runner]) - PA)
      out[step] = sound

  BURN_DEG = wp.constant(BURN)
  SPREAD_H = wp.constant(SPREAD_HEAT)
  SPREAD_B = wp.constant(SPREAD_BURN)
  COOL = wp.constant(COOLING)
  _KERNELS = engineRun
  return _KERNELS


class EngineSimVoice:
  """
  EngineSimVoice makes an engine's sound at 'rate' samples a second,
  block after block ('samples', as 'EngineVoice' does), from its
  revolutions a minute and its throttle ('load', 0 to 1), as his
  Engine Simulator does: its gas stepped on ('engineRun', 'spec.rate'
  steps a second), the exhaust runners' pressures read and put through
  his synthesizer's chain; every state (the gas, the crank's angle, the
  filters', the convolution's tail, the leveller's) carried from block
  to block (the gas's samples read at the sound's rate from one clock
  across every block: read afresh each block, the steps it got varied
  by one, a zipper at the block's rate; the impulse response's tail
  carried once: carried twice, it swelled block after block, a metallic
  ring the user heard as "audio artifacts"); 'seed' the noises'.
  """

  def __init__(self, rate: int, spec: EngineSpec = V12,
               seed: int = 0) -> None:
    import warp as wp
    wp.init()
    self.wp, self.spec, self.rate = wp, spec, rate
    self.random = numpy.random.default_rng(seed)
    self.rpm, self.load = 0.0, 0.0
    self.buffer, self.position = numpy.zeros(1), 0.0
    count, banks = len(spec.phases), max(spec.banks) + 1
    area = math.pi * spec.bore ** 2 / 4.0
    chamber = area * spec.stroke / (spec.compression - 1.0)
    volumes = ([spec.intakeRunner] * count + [chamber] * count
               + [spec.exhaustRunner] * count + [spec.plenum] * banks
               + [spec.exhaust] * banks)
    moles = [P_ATM * volume / (GAS_R * T_ATM) for volume in volumes]
    unburnt = [m if k < 2 * count or 3 * count <= k < 3 * count + banks
               else 0.0 for k, m in enumerate(moles)]
    device = 'cpu'

    def array(values: list, dtype: object) -> object:
      """Returns 'values' on the CPU as Warp has them."""
      return wp.array(numpy.array(values), dtype, device=device)

    self.n = array(moles, wp.float32)
    self.e = array([2.5 * GAS_R * T_ATM * m for m in moles], wp.float32)
    self.fresh = array(unburnt, wp.float32)
    self.v = array(volumes, wp.float32)
    self.phase = array(list(spec.phases), wp.float32)
    self.bank = array(list(spec.banks), wp.int32)
    length = spec.primaryLength
    self.share = array([1600.0 * part * spec.audioVolume / count
                        / (length * length) for part in spec.shares],
                       wp.float32)
    intake, exhaust = valveTables(spec)
    self.kIn = array(list(intake), wp.float32)
    self.kEx = array(list(exhaust), wp.float32)
    self.burnAt = array([-1.0] * count, wp.float32)
    self.burnHeat = array([0.0] * count, wp.float32)
    self.burnFresh = array([0.0] * count, wp.float32)
    self.burnLength = array([BURN] * count, wp.float32)
    self.calls = seed
    self.burnt = array([0.0] * count, wp.float32)
    self.angle = array([0.0], wp.float32)
    self.shape = wp.vec4(chamber, area, 0.5 * spec.stroke, spec.rod)
    self.flows = wp.vec4(kCarb(spec.throttle), kCarb(spec.runner),
                         kCarb(spec.primary), kCarb(spec.outlet))
    self.count, self.banks = count, banks
    self.heat = MOLAR_MASS / (1.0 + AIR_FUEL) * HEATING * BURNT
    self.response = responseOf(spec)
    self.tail = numpy.zeros(len(self.response) - 1)
    self.history = numpy.zeros(JITTER_MOST)
    self.states = {}
    self.peak, self.gain = 0.0, 1.0

  def samples(self, rpm: float, load: float, count: int) -> numpy.ndarray:
    """The 'samples' method returns the next 'count' samples, floats in
    -1..1, the engine going from where it was to 'rpm' and 'load' across
    them."""
    if count <= 0:
      return numpy.zeros(0, numpy.float32)
    rpm, load = max(rpm, 0.0), min(max(load, 0.0), 1.0)
    pace = self.spec.rate / self.rate
    steps = max(0, int(math.ceil(self.position + (count - 1) * pace)) + 2
                - len(self.buffer))
    raw = numpy.zeros(0)
    if steps > 0:
      out = self.wp.zeros(steps, self.wp.float32, device='cpu')
      self.wp.launch(_kernels(), 1, [
        self.n, self.e, self.fresh, self.v, self.phase, self.bank,
        self.share, self.kIn, self.kEx, self.burnAt, self.burnHeat,
        self.burnFresh, self.burnLength, self.burnt, self.angle,
        self.shape, self.flows,
        self.count, self.banks, steps, 1.0 / self.spec.rate, self.rpm,
        rpm, self.load, load, self.spec.advance[0], self.spec.advance[1],
        self.heat, self.calls, out], device='cpu')
      self.calls += 1
      raw = out.numpy().astype(numpy.float64)
    speed = min(rpm * 2.0 * math.pi / 60.0, 40.0) / 40.0
    self.buffer = numpy.concatenate((self.buffer, raw * speed ** 3))
    at = self.position + numpy.arange(count) * pace
    signal = numpy.interp(at, numpy.arange(len(self.buffer)), self.buffer)
    after = self.position + count * pace
    used = int(math.floor(after))
    self.buffer, self.position = self.buffer[used:], after - used
    share = numpy.arange(1, count + 1) / count
    rpms = self.rpm + (rpm - self.rpm) * share
    loads = self.load + (load - self.load) * share
    loud = QUIET + WITH_RPM * numpy.minimum(rpms / LOUDEST, 1.0) + (
      WITH_LOAD * loads)
    self.rpm, self.load = rpm, load
    heard = self._synthesized(signal)
    return (heard * loud).astype(numpy.float32)

  def _passed(self, name: str, signal: numpy.ndarray,
              cutoff: float) -> numpy.ndarray:
    """Returns 'signal' through his one pole low pass at 'cutoff' Hz,
    its memory 'name' carried on."""
    from scipy.signal import lfilter
    dt = 1.0 / self.rate
    rc = 1.0 / (2.0 * math.pi * cutoff)
    alpha = dt / (rc + dt)
    memory = self.states.get(name, numpy.zeros(1))
    out, memory = lfilter([alpha], [1.0, alpha - 1.0], signal, zi=memory)
    self.states[name] = memory
    return out

  def _synthesized(self, signal: numpy.ndarray) -> numpy.ndarray:
    """Returns 'signal' (the runners' pressures, summed) through his
    synthesizer: low passed, jittered, its DC off, his mix of its
    derivative and its air-noise textured self, convolved with the
    impulse response, low passed, levelled (slowly, 'LEVEL_SLOW'); as
    floats in -1..1."""
    from scipy.signal import oaconvolve
    spec, count = self.spec, len(signal)
    signal = self._passed('input', signal, INPUT_PASS)
    held = numpy.concatenate((self.history, signal))
    self.history = held[-JITTER_MOST:]
    wobble = self._passed('jitter', self.random.uniform(
      0.0, JITTER_MOST - 1.0, count) * spec.jitter, JITTER_PASS)
    at = numpy.arange(JITTER_MOST, JITTER_MOST + count) - wobble
    jittered = numpy.interp(at, numpy.arange(len(held)), held)
    dc = self._passed('dc', jittered, DC_PASS)
    flat = jittered - dc
    before = numpy.concatenate(([self.states.get('previous', 0.0)],
                                jittered[:-1]))
    self.states['previous'] = float(jittered[-1])
    slope = (jittered - before) * self.rate
    air = self._passed('air', self.random.uniform(-1.0, 1.0, count),
                       AIR_PASS)
    textured = spec.noise * air + (1.0 - spec.noise)
    mixed = slope * spec.hfGain + flat * textured * (1.0 - spec.hfGain)
    heard = oaconvolve(mixed, self.response)
    heard[:len(self.tail)] += self.tail[:len(heard)]
    self.tail = heard[count:].copy()
    heard = self._passed('output', heard[:count], OUTPUT_PASS * self.rate)
    self.peak = max(self.peak * 0.999 ** count, float(numpy.abs(
      heard).max()))
    wanted = LEVEL_TARGET / self.peak if self.peak > 0.0 else LEVEL_MOST
    wanted = min(max(wanted, LEVEL_LEAST), LEVEL_MOST)
    was = self.gain
    self.gain += (wanted - was) * (1.0 - math.exp(
      -count / (LEVEL_SLOW * self.rate)))
    gain = was + (self.gain - was) * numpy.arange(1, count + 1) / count
    return numpy.clip(heard * gain / 32768.0, -1.0, 1.0).astype(
      numpy.float32)
