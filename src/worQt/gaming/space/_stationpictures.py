"""
The space station's pictures, painted once (Qt's painter) and kept in
the looks' cache: the rainbow its antennas and beacons wear (user,
2026-11-17: "300m antennas ... that has RGB lighting. Like we are back
in the 2015 waiting for GTA V for PC with corsair or whatever the fuck
RGB"): every hue once across, full and bright, its right edge meeting
its left (it slides along them, round and round).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._looks import cacheFolder

#  The pictures' version (a change paints them anew) and the rainbow's
#  size, pixels.
VERSION = 1
WIDE, HIGH = 512, 8


def stationPicturesReady() -> dict:
  """Returns the station's pictures' files by name ('rainbow'), painted
  if not kept yet."""
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  target = folder / ('station-rainbow-%d.png' % VERSION)
  if not target.exists() and not rainbowPainted().save(str(target)):
    raise OSError('the rainbow could not be kept in %s' % target)
  return {'rainbow': target}


def rainbowPainted() -> object:
  """Returns the rainbow: every hue once from left to right, the same
  down it."""
  from PySide6.QtGui import QColor, QImage
  image = QImage(WIDE, HIGH, QImage.Format.Format_RGB32)
  for x in range(WIDE):
    colour = QColor.fromHsvF(x / WIDE, 1.0, 1.0)
    for y in range(HIGH):
      image.setPixelColor(x, y, colour)
  return image
