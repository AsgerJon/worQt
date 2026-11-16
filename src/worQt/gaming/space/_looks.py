"""
The heavenly bodies' looks (the spec: "cheap generated colours, for
example a grey Mercury, a red Mars, a banded Jupiter and Saturn with its
rings. No downloads, and only Terra gets continents"): each painted
once on the GPU (a Warp kernel, float32: fractal noise on the sphere,
coloured by the body's own recipe) as a picture of its whole surface
(longitude across, latitude up; the prime meridian down its middle, the
seam on the far side: Terra's pad, on its prime meridian, lies in the
middle), kept as PNG in the user's cache. Terra's continents are its
own seed's; land is made sure of round the pad.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import time
from pathlib import Path

import numpy
import warp as wp

wp.config.quiet = True
wp.set_module_options({'enable_backward': False})

#  Each look by the number the kernel knows it by; Saturn's rings last.
LOOKS = ('sol', 'mercury', 'venus', 'terra', 'mars', 'jupiter', 'saturn',
         'uranus', 'neptune', 'pluto', 'luna', 'mani', 'rings')
#  Each picture's width, pixels (its height half that; the rings' a
#  strip): Terra's the finest, seen from its ground.
WIDTHS = {'terra': 4096, 'sol': 512, 'rings': 1024}
WIDTH = 1024
RING_HIGH = 8
#  Saturn's rings from its middle, its radii: the C ring's inside to the
#  A ring's outside.
RING_INNER, RING_OUTER = 1.24, 2.27
#  Changing a recipe, this goes up: the cache is painted anew.
VERSION = 2
SEED = 2026


def cacheFolder() -> Path:
  """Returns where the looks are kept: the user's cache."""
  base = os.environ.get('XDG_CACHE_HOME') or str(Path.home() / '.cache')
  return Path(base) / 'worQt' / 'space' / ('looks-%d' % VERSION)


def lookFile(name: str) -> Path:
  """Returns the file look 'name' is kept in."""
  return cacheFolder() / ('%s.png' % name)


@wp.func
def fractal(state: wp.uint32, p: wp.vec3, octaves: int) -> float:
  """Returns fractal noise at 'p' ('octaves' of Perlin's, each twice as
  fine and half as strong), about minus one to one."""
  total = float(0.0)
  amp = float(1.0)
  freq = float(1.0)
  norm = float(0.0)
  for _ in range(octaves):
    total = total + amp * wp.noise(state, p * freq)
    norm = norm + amp
    amp = amp * 0.5
    freq = freq * 2.03
  return total / norm


@wp.func
def blend(one: wp.vec3, two: wp.vec3, share: float) -> wp.vec3:
  """Returns 'one' to 'two' by 'share', kept within nought and one."""
  s = wp.clamp(share, 0.0, 1.0)
  return one + (two - one) * s


@wp.func
def terraColour(state: wp.uint32, p: wp.vec3, lat: float) -> wp.vec3:
  """Returns Terra's colour at 'p' on its unit sphere: sea, coast,
  green, desert, highland, mountain, ice; land round the pad."""
  pad = wp.vec3(1.0, 0.0, 0.0)
  gap = wp.length(p - pad)
  sea = float(0.06)
  h = fractal(state, p * 1.7, 7)
  flat = wp.exp(-gap * gap / 0.006)
  h = h + (wp.max(h, sea + 0.05) - h) * wp.min(1.0, 2.5 * flat)
  h = h + (sea + 0.05 - h) * flat
  if h < sea:
    deep = wp.vec3(8.0, 26.0, 70.0)
    shallow = wp.vec3(28.0, 92.0, 140.0)
    colour = blend(deep, shallow, (h - sea + 0.3) / 0.3)
  else:
    e = h - sea
    wet = fractal(state, p * 3.1 + wp.vec3(7.0, 3.0, 1.0), 4)
    band = wp.abs(wp.abs(lat) - 0.42)
    dry = (0.2 - band) * 4.0 - wet * 2.0
    green = blend(wp.vec3(52.0, 104.0, 44.0), wp.vec3(196.0, 172.0, 118.0),
                  dry)
    colour = blend(green, wp.vec3(118.0, 98.0, 70.0), (e - 0.12) / 0.15)
    colour = blend(colour, wp.vec3(138.0, 134.0, 128.0), (e - 0.3) / 0.1)
    colour = blend(colour, wp.vec3(236.0, 240.0, 246.0), (e - 0.42) / 0.08)
    colour = blend(wp.vec3(206.0, 190.0, 140.0), colour, e / 0.012)
  ice = (wp.abs(lat) - 1.3 + 0.08 * fractal(state, p * 6.0, 3)) / 0.04
  return blend(colour, wp.vec3(238.0, 243.0, 250.0), ice)


@wp.func
def rockColour(state: wp.uint32, p: wp.vec3, light: wp.vec3,
               dark: wp.vec3, seas: float) -> wp.vec3:
  """Returns a rocky body's colour: its light ground, dark seas where
  the slow noise is over 'seas', speckled by the fine."""
  slow = fractal(state, p * 1.3, 3)
  fine = fractal(state, p * 14.0, 4)
  colour = blend(light, dark, (slow - seas) / 0.08)
  return colour * (1.0 + 0.18 * fine)


@wp.func
def bandColour(state: wp.uint32, p: wp.vec3, lat: float, one: wp.vec3,
               two: wp.vec3, bands: float, swirl: float) -> wp.vec3:
  """Returns a giant's colour: bands across its latitudes, swirled."""
  twist = fractal(state, p * 4.0, 4) * swirl
  stripe = 0.5 + 0.5 * wp.sin(lat * bands + twist)
  return blend(one, two, stripe)


@wp.kernel
def painted(look: int, out: wp.array3d(dtype=wp.uint8)):
  """Paints look 'look' (its number in 'LOOKS') into 'out' (rows from
  the north down, longitude from the far side across, RGBA)."""
  i, j = wp.tid()
  high = out.shape[0]
  wide = out.shape[1]
  state = wp.rand_init(SEED + look * 97)
  lat = 1.5707963 - (float(i) + 0.5) / float(high) * 3.1415927
  lon = (float(j) + 0.5) / float(wide) * 6.2831853 - 3.1415927
  p = wp.vec3(wp.cos(lat) * wp.cos(lon), wp.cos(lat) * wp.sin(lon),
              wp.sin(lat))
  colour = wp.vec3(128.0, 128.0, 128.0)
  alpha = float(255.0)
  if look == 0:
    colour = wp.vec3(255.0, 236.0, 196.0) * (
      0.88 + 0.12 * fractal(state, p * 22.0, 3))
  elif look == 1:
    colour = rockColour(state, p, wp.vec3(150.0, 136.0, 120.0),
                        wp.vec3(98.0, 90.0, 84.0), 0.25)
  elif look == 2:
    colour = bandColour(state, p, lat, wp.vec3(232.0, 214.0, 160.0),
                        wp.vec3(205.0, 176.0, 118.0), 6.0, 3.0)
  elif look == 3:
    colour = terraColour(state, p, lat)
  elif look == 4:
    colour = rockColour(state, p, wp.vec3(196.0, 102.0, 58.0),
                        wp.vec3(118.0, 62.0, 42.0), 0.1)
    colour = blend(colour, wp.vec3(240.0, 236.0, 230.0),
                   (wp.abs(lat) - 1.36) / 0.03)
  elif look == 5:
    colour = bandColour(state, p, lat, wp.vec3(232.0, 218.0, 190.0),
                        wp.vec3(168.0, 118.0, 84.0), 16.0, 2.0)
    spot = wp.vec3(lat + 0.38, (lon - 0.6) * 0.45, 0.0)
    colour = blend(colour, wp.vec3(196.0, 92.0, 62.0),
                   (0.06 - wp.length(spot)) / 0.02)
  elif look == 6:
    colour = bandColour(state, p, lat, wp.vec3(218.0, 196.0, 146.0),
                        wp.vec3(190.0, 160.0, 108.0), 14.0, 1.0)
  elif look == 7:
    colour = bandColour(state, p, lat, wp.vec3(172.0, 222.0, 230.0),
                        wp.vec3(150.0, 206.0, 218.0), 8.0, 0.5)
  elif look == 8:
    colour = bandColour(state, p, lat, wp.vec3(62.0, 102.0, 204.0),
                        wp.vec3(96.0, 140.0, 226.0), 10.0, 2.5)
  elif look == 9:
    colour = rockColour(state, p, wp.vec3(196.0, 166.0, 134.0),
                        wp.vec3(120.0, 82.0, 60.0), 0.2)
    heart = wp.vec3(lat - 0.3, (wp.abs(lon) - 2.9) * 0.8, 0.0)
    colour = blend(colour, wp.vec3(238.0, 232.0, 220.0),
                   (0.45 - wp.length(heart)) / 0.08)
  elif look == 10:
    colour = rockColour(state, p, wp.vec3(150.0, 150.0, 148.0),
                        wp.vec3(78.0, 78.0, 80.0), 0.12)
  elif look == 11:
    colour = rockColour(state, p, wp.vec3(118.0, 100.0, 90.0),
                        wp.vec3(80.0, 66.0, 60.0), 0.15)
  else:
    r = float(RING_INNER) + (float(j) + 0.5) / float(wide) * float(
      RING_OUTER - RING_INNER)
    fine = 0.75 + 0.25 * wp.sin(r * 340.0) * wp.sin(r * 97.0)
    dense = float(0.3)
    if r > 1.53:
      dense = 0.9
    if r > 1.95:
      dense = 0.05
    if r > 2.03:
      dense = 0.6
    colour = wp.vec3(214.0, 198.0, 166.0)
    alpha = 255.0 * wp.clamp(dense * fine, 0.0, 1.0)
  for k in range(3):
    out[i, j, k] = wp.uint8(wp.clamp(colour[k], 0.0, 255.0))
  out[i, j, 3] = wp.uint8(alpha)


def lookPainted(name: str, device: str) -> numpy.ndarray:
  """Returns look 'name' painted on 'device': rows from the north down,
  RGBA bytes."""
  wide = WIDTHS.get(name, WIDTH)
  high = RING_HIGH if name == 'rings' else wide // 2
  out = wp.zeros((high, wide, 4), wp.uint8, device)
  wp.launch(painted, (high, wide), [LOOKS.index(name), out], [], [], [],
            device)
  return out.numpy()


def looksReady(device: str, said: object = None) -> dict:
  """Has every look painted and kept (only those not yet in the cache)
  and returns each look's file by its name; 'said' (a callable taking a
  line, or None) hears what it does."""
  from PySide6.QtGui import QImage
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  out = {}
  for name in LOOKS:
    target = lookFile(name)
    out[name] = target
    if target.exists():
      continue
    began = time.perf_counter()
    pixels = numpy.ascontiguousarray(lookPainted(name, device))
    high, wide = pixels.shape[:2]
    image = QImage(pixels.data, wide, high, 4 * wide,
                   QImage.Format.Format_RGBA8888)
    if not image.save(str(target)):
      raise OSError('the look %s could not be kept in %s' % (name, target))
    if said is not None:
      said('painted %s (%d x %d) in %.1f s' % (name, wide, high,
                                               time.perf_counter() - began))
  return out
