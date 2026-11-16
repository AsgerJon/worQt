"""
The memes on the coaches' walls (user, 2026-11-16: "put some memes on
the inside walls. have some fun."; then "in @tmp we got some more memes
lol": the Rickroll and El Risitas): twenty of them in one picture
('MEMES_FILE', a 5 x 4 grid of 'CELL' pixels: 'memeCell' says where
each lies on it), lit from behind as an underground train's posters
are ('MEME_LOOK'). Drawn here ('memesMade', with Qt, run by
previews/make_memes.py) from the lab's own pictures and the user's
(previews/ and tmp/, kept out of git: the picture made is kept in git
instead) and the lab's own words.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from pathlib import Path

#  The memes' picture, its grid (columns, rows) and each cell's size in
#  pixels.
MEMES_FILE = Path(__file__).parent / 'memes' / 'memes.jpg'
GRID, CELL = (5, 4), (512, 384)
#  The memes: each a picture from previews/ or tmp/ (None: a plain
#  panel), its top line and its bottom line; 'drake', 'brain' and 'skin'
#  are drawn ('skin': the avatar's face).
MEMES = (('wiley_coyote_lol.png', 'when you press shift',
          'in the loop de loop'),
         ('render-wreck.png', "derail shouldn't mean",
          'RuntimeError!'),
         ('drake', 'float64', 'float32 on the GPU'),
         ('brain', 'CPU|GPU|GPU in float32|warp the shit out of it', ''),
         ('render-steam-running-side.png', '225 psi', 'of pure vibes'),
         ('render-cart-side.png', 'is this', 'a train?'),
         ('wtf_frame.png', 'what the fuck', 'is this frame'),
         ('skin', 'ship it', 'no notes'),
         ('render-steam-standing-cab.png', 'one does not simply',
          'walk through a tender'),
         ('render-coupler.png', 'mind the gap', "(it's 4 cm)"),
         ('render-train.png', 'buffers only push. couplings only pull',
          'it is called a relationship'),
         (None, 'git is too ******* made', 'for that to be safe'),
         ('phys-walk-dominoes.png', 'froude slow-mo?',
          'not in my sandbox'),
         ('billiards-kegler.png', 'put the proper pins back',
          'the real tall ones'),
         ('render-loop.png', 'bro chill...', 'compact!'),
         ('render-steam-running-train.png', 'all aboard the',
          'float32 express'),
         ('rick_map_art.png', 'never gonna give you up',
          'never gonna derail you'),
         ('risitas_map_art.png', 'when someone says', 'git is safe'),
         (None, 'kde wayland: no pointer lock', 'gamescope: hold my beer'),
         ('render-figure-front.png', 'it does keep', 'the cursor'))
#  How the posters are drawn (colour, metalness, roughness, picture,
#  glow: lit from behind, as bright as this of their own).
MEME_LOOK = ((255, 255, 255), 0.0, 0.85, str(MEMES_FILE), 0.55)


def memeCell(k: int) -> tuple:
  """The 'memeCell' function returns where meme 'k' lies on the memes'
  picture: (from u, from v, to u, to v), 0 to 1, v up from its bottom."""
  columns, rows = GRID
  column, row = k % columns, k // columns
  return (column / columns, 1.0 - (row + 1) / rows,
          (column + 1) / columns, 1.0 - row / rows)


def memesMade(folders: tuple, skin: Path, target: Path = MEMES_FILE) -> None:
  """The 'memesMade' function draws the memes into their picture at
  'target' (a running Qt application needed): each from its picture in
  the first of 'folders' holding it (in none: a dark panel) or drawn
  ('drake', 'brain', 'skin': the face of the skin at 'skin'), its lines
  in white edged black."""
  from PySide6.QtCore import QRectF, Qt
  from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath
  from PySide6.QtGui import QPen, QPolygonF

  wide, high = CELL
  sheet = QImage(GRID[0] * wide, GRID[1] * high, QImage.Format.Format_RGB32)
  sheet.fill(QColor(20, 20, 24))
  painter = QPainter(sheet)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

  def lined(text: str, box: QRectF, size: int) -> None:
    """Writes 'text' in white edged black, as large as fits 'box'."""
    font = QFont('Liberation Sans', size, QFont.Weight.Black)
    while size > 10:
      font.setPixelSize(size)
      path = QPainterPath()
      path.addText(0.0, 0.0, font, text)
      bounds = path.boundingRect()
      if bounds.width() <= box.width() - 16:
        break
      size -= 2
    path = path.translated(box.center().x() - bounds.center().x(),
                           box.center().y() - bounds.center().y())
    painter.setPen(QPen(QColor(0, 0, 0), max(3.0, size / 8.0),
                        Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(QColor(255, 255, 255))
    painter.drawPath(path)

  def pictured(name: str, cell: QRectF) -> None:
    """Draws the picture 'name' from 'folders' filling 'cell' (cropped
    to it), or a dark panel."""
    found = [folder / name for folder in folders
             if (folder / name).is_file()]
    picture = QImage(str(found[0])) if found else QImage()
    if picture.isNull():
      painter.fillRect(cell, QColor(40, 44, 52))
      return
    scale = max(cell.width() / picture.width(),
                cell.height() / picture.height())
    shown = QRectF(0.0, 0.0, cell.width() / scale, cell.height() / scale)
    shown.moveCenter(QRectF(picture.rect()).center())
    painter.drawImage(cell, picture, shown)

  def drake(top: str, bottom: str, cell: QRectF) -> None:
    """Draws the two-panel no-and-yes format: a red cross by 'top', a
    green tick by 'bottom'."""
    half = cell.height() / 2.0
    for k, (text, good) in enumerate(((top, False), (bottom, True))):
      row = QRectF(cell.left(), cell.top() + k * half, cell.width(), half)
      painter.fillRect(row, QColor(250, 214, 64) if good
                       else QColor(240, 236, 228))
      mark = QRectF(row.left() + 20.0, row.top() + 26.0, half - 52.0,
                    half - 52.0)
      painter.setPen(QPen(QColor(40, 150, 60) if good
                          else QColor(200, 40, 40), 18.0,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
      if good:
        painter.drawPolyline(QPolygonF([
          mark.topLeft() + (mark.bottomLeft() - mark.topLeft()) * 0.55,
          mark.bottomLeft() + (mark.bottomRight() - mark.bottomLeft())
          * 0.4, mark.topRight()]))
      else:
        painter.drawLine(mark.topLeft(), mark.bottomRight())
        painter.drawLine(mark.topRight(), mark.bottomLeft())
      lined(text, QRectF(row.left() + half, row.top(),
                         row.width() - half, half), 56)

  def brain(lines: str, cell: QRectF) -> None:
    """Draws the growing-brain format: a row a line, its brain brighter
    each row."""
    texts = lines.split('|')
    tall = cell.height() / len(texts)
    for k, text in enumerate(texts):
      row = QRectF(cell.left(), cell.top() + k * tall, cell.width(), tall)
      painter.fillRect(row, QColor(18 + 10 * k, 18 + 20 * k, 40 + 40 * k))
      glow = QColor(255, 180 + 25 * k, 120 + 40 * k)
      painter.setPen(Qt.PenStyle.NoPen)
      for ring in range(k + 1):
        glow.setAlpha(60 + 40 * ring)
        painter.setBrush(glow)
        size = (tall - 20.0) * (1.0 - 0.18 * ring)
        painter.drawEllipse(QRectF(row.left() + 12.0 + 0.5 * (
          tall - 20.0 - size), row.top() + 10.0 + 0.5 * (
          tall - 20.0 - size), size, size))
      lined(text, QRectF(row.left() + tall, row.top(),
                         row.width() - tall, tall), 44)

  def face(cell: QRectF) -> None:
    """Draws the skin's face (its 8 x 8 front, sharp) on a sky."""
    painter.fillRect(cell, QColor(110, 170, 230))
    picture = QImage(str(skin))
    side = cell.height() - 40.0
    where = QRectF(cell.center().x() - side / 2.0, cell.top() + 20.0, side,
                   side)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
    if not picture.isNull():
      painter.drawImage(where, picture, QRectF(8.0, 8.0, 8.0, 8.0))
      painter.drawImage(where, picture, QRectF(40.0, 8.0, 8.0, 8.0))
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

  for k, (name, top, bottom) in enumerate(MEMES):
    column, row = k % GRID[0], k // GRID[0]
    cell = QRectF(column * wide, row * high, wide, high)
    painter.save()
    painter.setClipRect(cell)
    if name == 'drake':
      drake(top, bottom, cell)
    elif name == 'brain':
      brain(top, cell)
    else:
      if name == 'skin':
        face(cell)
      elif name is None:
        painter.fillRect(cell, QColor(44, 30, 60))
      else:
        pictured(name, cell)
      band = cell.height() * 0.24
      lined(top.upper(), QRectF(cell.left(), cell.top(), wide, band), 58)
      lined(bottom.upper(), QRectF(cell.left(), cell.bottom() - band, wide,
                                   band), 58)
    painter.restore()
  painter.end()
  target.parent.mkdir(parents=True, exist_ok=True)
  if not sheet.save(str(target), 'JPG', 88):
    raise OSError('the memes could not be saved to %s' % target)
