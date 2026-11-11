"""
The 'roomLight' function paints the light of the room round the table,
an HDR image Qt Quick 3D lights the scene with and the balls mirror;
'radianceBytes' writes such an image in the Radiance '.hdr' format.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

LAMP = (15.0, 14.0, 12.8)  # the lamp's light, far the brightest
WALLS = (0.7, 0.6, 0.5)  # warm and dim at the horizon
CEILING = (0.07, 0.07, 0.08)
FLOOR = (0.05, 0.043, 0.038)


def roomLight(width: int, height: int) -> numpy.ndarray:
  """The 'roomLight' function returns the light reaching the table's
  middle from every way, 'height' rows by 'width' columns by red, green
  and blue, as an equirectangular image: the top row straight up, the
  bottom straight down, y up and the table's length along z. A lamp
  hangs a metre above the cloth, 0.4 m wide and 2.4 m long along the
  table; the walls glow dimly about the horizon, the ceiling and the
  floor darker. The cloth's own blue, bounced up into the balls, is a
  light of its own in the scene, for the balls alone."""
  rows = (numpy.arange(height) + 0.5) / height
  columns = (numpy.arange(width) + 0.5) / width
  latitude = (0.5 - rows) * math.pi
  longitude = (columns - 0.5) * 2.0 * math.pi
  latitude, longitude = _grid(latitude, longitude)
  up = numpy.sin(latitude)
  across = numpy.cos(latitude) * numpy.sin(longitude)
  along = numpy.cos(latitude) * numpy.cos(longitude)
  horizon = numpy.exp(-(up / 0.35) ** 2)
  image = numpy.zeros((height, width, 3), numpy.float32)
  for channel in range(3):
    above = CEILING[channel] + (WALLS[channel] - CEILING[channel]) * horizon
    below = FLOOR[channel] + (WALLS[channel] - FLOOR[channel]) * horizon
    image[..., channel] = numpy.where(up > 0.0, above, below)
  lit = up > 0.05
  reach = numpy.where(lit, 1.0 / numpy.maximum(up, 0.05), 0.0)
  lamp = lit & (numpy.abs(across * reach) < 0.2)
  lamp &= numpy.abs(along * reach) < 1.2
  for channel in range(3):
    image[..., channel] = numpy.where(lamp, LAMP[channel],
                                      image[..., channel])
  return image


def _grid(latitude: numpy.ndarray,
          longitude: numpy.ndarray) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Returns 'latitude' down the rows and 'longitude' across the
  columns, each as a whole grid."""
  rows, columns = latitude.shape[0], longitude.shape[0]
  return (numpy.repeat(latitude[:, None], columns, 1),
          numpy.repeat(longitude[None, :], rows, 0))


def radianceBytes(image: numpy.ndarray) -> bytes:
  """The 'radianceBytes' function returns 'image', rows by columns by
  red, green and blue, in the Radiance '.hdr' format: its header, then
  each pixel as a shared exponent and three mantissas, rows top first,
  unpacked."""
  height, width = image.shape[0], image.shape[1]
  brightest = image.max(2)
  mantissa, exponent = numpy.frexp(brightest)
  dark = brightest < 1e-30
  scale = numpy.where(dark, 0.0, mantissa * 256.0
                      / numpy.maximum(brightest, 1e-30))
  pixels = numpy.zeros((height, width, 4), numpy.uint8)
  for channel in range(3):
    value = numpy.floor(image[..., channel] * scale)
    pixels[..., channel] = numpy.clip(value, 0, 255).astype(numpy.uint8)
  pixels[..., 3] = numpy.where(dark, 0, exponent + 128).astype(numpy.uint8)
  header = b'#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n' % (
    height, width)
  return header + pixels.tobytes()
