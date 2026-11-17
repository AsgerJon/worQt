"""
The items' icons (user, 2026-11-17: "Give Asger a hotbar and an
inventory like in minecraft"; '_inventory'): pixel art as Minecraft's,
'PIXELS' a side, each pixel painted 'SCALE' wide (the view shows them
unsmoothed), kept in the looks' cache. Qt (the painter) only where they
are painted.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._looks import cacheFolder

#  The icons' version (a change paints them anew), their pixels a side,
#  how wide each is painted.
VERSION = 2
PIXELS = 16
SCALE = 4
#  The colours (0 to 255, then how opaque) the pixel maps name.
PALETTE = {'K': (40, 40, 44, 255), 'k': (82, 82, 90, 255),
           'W': (160, 160, 170, 255), 'O': (240, 140, 30, 255),
           'V': (190, 100, 255, 255), 'B': (205, 160, 60, 255),
           'b': (130, 92, 30, 255), 'L': (255, 228, 140, 255),
           'G': (125, 185, 255, 255), 'D': (50, 40, 30, 255),
           'M': (85, 100, 45, 255), 'm': (52, 62, 28, 255),
           'Y': (232, 200, 60, 255), 'w': (205, 212, 165, 255),
           'R': (196, 44, 32, 255), 'r': (110, 22, 16, 255),
           'P': (228, 196, 136, 255), 'p': (170, 118, 62, 255)}
#  Each item's pixels, a row a string from the top ('.': clear): the
#  gravity gun (dark, its orange claws, the violet glow of a magic
#  bolt at its muzzle), the telescope (brass, its glass at the far end),
#  the commando bar (olive wrapper, a yellow band, crimped ends), the
#  bag of pork scratchings (red, crimped on top, the rinds seen through
#  its window, a yellow band).
ICONS = {
  'gravgun': ('................',
              '................',
              '...........O....',
              '..........O.....',
              '.kkkkkkkkkO..V..',
              'kWWWWWWWWWkO.VV.',
              'kKKKKKKKKKKkOVVV',
              'kKKKKOOKKKKkOVV.',
              '.kKKKKKKKKKk.V..',
              '..kKKk.kkkkO....',
              '..kKKk......O...',
              '..kKKk..........',
              '..kKKk..........',
              '..kkkk..........',
              '................',
              '................'),
  'telescope': ('................',
                '............bbb.',
                '...........bLGGb',
                '..........bLBGGb',
                '.........bLBBbb.',
                '........bLBBb...',
                '.......bLBBb....',
                '......bLBBb.....',
                '.....DLBBb......',
                '....DDBBb.......',
                '...bLBBD........',
                '..bLBBb.........',
                '.bLBBb..........',
                '.bBBb...........',
                '..bb............',
                '................'),
  'commando': ('................',
               '................',
               '................',
               '................',
               '.m.m.m.m.m.m.m..',
               'mMMMMMMMMMMMMMm.',
               'mMwwMMMMMMMMMMm.',
               'mYYYYYYYYYYYYYm.',
               'mYKYKKYKYYKKYYm.',
               'mYYYYYYYYYYYYYm.',
               'mMMMMMMMMMMMMMm.',
               'mmmmmmmmmmmmmmm.',
               '.m.m.m.m.m.m.m..',
               '................',
               '................',
               '................'),
  'scratchings': ('................',
                  '...r.r.r.r.r.r..',
                  '...rrrrrrrrrrr..',
                  '...rRRRRRRRRRr..',
                  '..rRRwwwwwwwRRr.',
                  '..rRwPPpPPpPwRr.',
                  '..rRwPpPPPpPwRr.',
                  '..rRwPPPpPPPwRr.',
                  '..rRwpPPPpPPwRr.',
                  '..rRwwwwwwwwwRr.',
                  '..rRRYYYYYYYRRr.',
                  '..rRRRRRRRRRRRr.',
                  '..rRRRRRRRRRRRr.',
                  '...rrrrrrrrrrr..',
                  '................',
                  '................')}


def itemPictures() -> dict:
  """Returns each item's icon's file by its kind, painted if not kept
  yet."""
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  out = {}
  for kind in ICONS:
    target = folder / ('item-%s-%d.png' % (kind, VERSION))
    if not target.exists() and not iconPainted(kind).save(str(target)):
      raise OSError('the icon %s could not be kept in %s' % (kind, target))
    out[kind] = target
  return out


def iconPainted(kind: str) -> object:
  """Returns item 'kind''s icon: its pixel map, each pixel 'SCALE'
  wide."""
  from PySide6.QtGui import QColor, QImage, QPainter
  rows = ICONS[kind]
  if len(rows) != PIXELS or any(len(row) != PIXELS for row in rows):
    raise ValueError('the icon %s is not %d pixels square' % (kind,
                                                             PIXELS))
  image = QImage(PIXELS * SCALE, PIXELS * SCALE,
                 QImage.Format.Format_ARGB32)
  image.fill(QColor(0, 0, 0, 0))
  painter = QPainter(image)
  for y, row in enumerate(rows):
    for x, letter in enumerate(row):
      if letter != '.':
        painter.fillRect(x * SCALE, y * SCALE, SCALE, SCALE,
                         QColor(*PALETTE[letter]))
  painter.end()
  return image
