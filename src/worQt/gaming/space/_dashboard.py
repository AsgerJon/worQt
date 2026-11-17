"""
The dashboard's furniture, in the vessel's own axes ('_cockpit' has
where everything is), 1970s B&O in spirit (user, 2026-11-16: "more
1970's B&O but with dials, switches and indicators illuminated"; its
look only, no name or mark of theirs): the aluminium face in its
rosewood frame (its legends printed: '_dashpictures'), the dials, lamps,
switch legends, the ball's cowl, the closed circuit monitor, the
tape deck's shelf, the teleprinter on its
console. 'pieces' lists what moves or lights, one list for
the view (their meshes, 'pieceRows') and the scenery (where each is and
how it glows): the inputs (each its FourthPeep deforming), the dials'
needles, the lamps, the legends, the tape deck's reels and knob, the
typehead. Rows of
eight numbers a corner (place, normal, where on a picture), Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.sandbox import Knob, Pushbutton, Slider

from ._cockpit import BAT_LONG, BALL_RADIUS, CONSOLE_AXES
from ._cockpit import CONSOLE_KEY_HALF, CONSOLE_SWITCHES, DIAL_RADIUS
from ._cockpit import DIALS, EYE, FLOOR, FRAME, GLASS, GLOBE_AT, NOSE
from ._cockpit import GLOBE_AXES
from ._cockpit import GUARD_KNOB, GUARD_SWITCH, KEY_HALF, LAMP_RADIUS
from ._cockpit import LAMPS, LEGEND_HALF, LEGEND_UP, MONITOR_OUT
from ._cockpit import PANEL_AXES, PANEL_HALF, PANEL_THICK, PAPER_AT
from ._cockpit import PAPER_HIGH, PAPER_WIDE, SCREEN_AT, SCREEN_HALF
from ._cockpit import SIDEBOARD, SLIDER_FROM, SLIDER_LONG, SWITCHES, TOP
from ._cockpit import SNACK_BAG
from ._cockpit import panelPoint
from ._deckmodel import movingParts
from ._elevator import PLATE_HALVES
from ._stationinterior import HATCH
from ._teleprinter import LINE, PITCH, WIDTH
from ._gunmodel import gunParts, sideMark
from ._walkwaymeshes import leafRows
from ._bolts import STATION_BOLTS, boltPieceRows, ringPieceRows
from ._launchtower import PLATE, SHAFT
from ._shapes import UNTURNED, boxRows, pointAlong, rowsAbout
from ._shapes import cylinderRows, discRows, frustumRows, joined
from ._shapes import quadRows, ringRows, roundedPaneRows
from ._shapes import roundedSlabRows
from ._furnishings import bulbsRows, flamesRows, looseParts
from ._furnishings import looseThings, roundFlamesRows, shadeRows

TAU = 2.0 * math.pi
#  Half a horizon mark's decal, m.
DECAL = 0.02
#  The dials' scales: each dial's name, the value its scale's log turns
#  round at (a hundred metres, ten metres a second), its last value, its
#  ticks (value and the number printed) and its unit; the needle sweeps
#  'SWEEP' rad from its first tick (clockwise seen from before it).
DIAL_SCALES = {
  'HEIGHT': (100.0, 1e6, ((0.0, '0'), (1e3, '1'), (1e4, '10'),
                          (1e5, '100'), (1e6, '1000')), 'KM'),
  'SPEED': (10.0, 1e4, ((0.0, '0'), (100.0, '100'), (1e3, '1K'),
                        (1e4, '10K')), 'M/S'),
  'APOAPSIS': (100.0, 1e6, ((0.0, '0'), (1e3, '1'), (1e4, '10'),
                            (1e5, '100'), (1e6, '1000')), 'KM'),
  'PERIAPSIS': (100.0, 1e6, ((0.0, '0'), (1e3, '1'), (1e4, '10'),
                             (1e5, '100'), (1e6, '1000')), 'KM')}
SWEEP = math.radians(270.0)
#  The altimeter: the dial the guidance's target is marked on.
ALTIMETER = [name for name, _ in DIALS].index('HEIGHT')
#  The lamps' colours (0 to 255) by name: amber but the orbit's green and
#  the ground's red.
LAMP_COLOURS = {'ENGINE': (255, 160, 40), 'AIR': (255, 160, 40),
                'GROUND': (255, 60, 40), 'WARP': (255, 160, 40),
                'GUIDE': (255, 160, 40), 'ORBIT': (90, 255, 110),
                'DOCK': (90, 255, 110)}
#  The legends lit over the switches (the panel's and the view's).
LEGENDS = tuple(name for name, _, _, _ in SWITCHES) + tuple(
  name for name, _, _, _ in CONSOLE_SWITCHES)
#  The teleprinter's typehead's size (m: across, up, out), how far before
#  the paper it runs. Its paper's picture: how many pixels across, how
#  high the line typed stands over the paper's foot (m), the font's
#  advance (em: JetBrains Mono's), the green bars' lines (each three
#  lines, three apart, as on a Teletype's green bar paper).
HEAD_HALF = (0.006, 0.004, 0.006)
HEAD_OUT = 0.008
PAPER_PIXELS = 1024
PAPER_FOOT = 0.008
ADVANCE = 0.6
BAND = 3
#  The globe's stand: its foot's radius and height, its pillar's radius,
#  its fixed ring's width and depth (round the glass), m.
FOOT = (0.2, 0.03)
PILLAR = 0.025
FIXED_RING = (0.016, 0.02)
#  The cabin's lights' meshes, by their pieces' kinds (drawn where they
#  are, about nothing).
LIGHTS = {'flames': flamesRows, 'flames round': roundFlamesRows,
          'shade': shadeRows, 'bulbs': bulbsRows}
#  The knobs that glint, enchanted (user, 2026-11-16 of the warp: "give
#  it a sort of enchantment glint, as it is kinda... magic"), by their
#  actions.
ENCHANTED = ('warp',)
#  The hatch's lid hinges on its rim, just under the ceiling, opening
#  down 'HATCH_OPEN' rad; the space station's elevators (cages).
HATCH_HINGE = (HATCH, 0.0, NOSE - 0.035)
HATCH_OPEN = math.radians(100.0)
CARS = 4
#  The guards' walls' thickness, m.
GUARD_WALL = 0.0022
#  The closed circuit monitor's curves (user, 2026-11-17: "it is too
#  blocky. The CCTV needs those curvier corners"), m: the cabinet's
#  margin round the screen, its corners' radius and its front edge's;
#  the black inset's margin and corners; the tube's corners (as round
#  as the ones painted on its picture: 46 of its 384 pixels) and how
#  far its middle bulges.
CABINET_MARGIN, CABINET_ROUND, CABINET_EDGE = 0.016, 0.024, 0.008
INSET_MARGIN, INSET_ROUND = 0.005, 0.016
TUBE_ROUND, TUBE_BULGE = 0.0125, 0.003


def dialShare(name: str, value: float) -> float:
  """Returns how far round its scale dial 'name' shows 'value', nought to
  one (its scale a logarithm's: a needle's travel for every tenfold)."""
  turn, most, _, _ = DIAL_SCALES[name]
  value = max(0.0, min(most, value))
  return math.log10(1.0 + value / turn) / math.log10(1.0 + most / turn)


def dialAngle(share: float) -> float:
  """Returns a needle's turn at 'share' of its scale, rad clockwise from
  straight up (seen from before the dial)."""
  return -0.5 * SWEEP + share * SWEEP


def pieces(controls: tuple) -> tuple:
  """Returns what moves or lights on the dashboard, in the order the view
  and the scenery both keep: each input ('control', its Control), each
  dial's needle ('needle', its index), each lamp ('lamp', index), each
  legend ('legend', index), each moving part of the tape deck ('deck',
  its index in '_deckmodel.movingParts': a reel's or the knob's, by
  material), the altimeter's pink mark ('bug', 0: at the guidance's
  target), the typehead ('typehead', 0), each guarded input's guard
  ('guard', its Control: the switches and knobs), the enchanted knobs'
  glint on them and on their guards' lids ('glint', 'glint lid', the
  Control: 'ENCHANTED'), the cabin's lights: the candles' flames (and
  weightless, round), the lamp's shade, the fairy lights ('flames',
  'flames round', 'shade', 'bulbs'), each loose thing's mesh of a look
  ('loose', its index in '_furnishings.looseParts'), each part of the
  gravity gun in his hands ('gun', its index in '_gunmodel.gunParts':
  about his eyes, in their frame; 'gun mark': the 3 on its side), the
  hatch's lid in the ceiling
  ('hatch': open docked to the space station), the station's elevators'
  cages' plates ('car', six a cage: '_elevator.PLATE_HALVES'), the
  door's leaf ('door': it slides round into the wall, '_walkway'), the
  launch tower's lift's car's floor and roof ('lift', '_towerlift'), the
  space station's magic bolts, docked ('sbolt', 'sring': each its steel
  and its ring, '_bolts.stationBolts')."""
  out = [('control', control) for control in controls]
  out += [('needle', k) for k in range(len(DIALS))]
  out += [('lamp', k) for k in range(len(LAMPS))]
  out += [('legend', k) for k in range(len(LEGENDS))]
  out += [('deck', k) for k in range(len(movingParts()))]
  out += [('bug', 0), ('typehead', 0)]
  out += [('guard', control) for control in controls if guarded(control)]
  out += [(kind, control) for control in controls
          if control.action in ENCHANTED for kind in ('glint',
                                                       'glint lid')]
  out += [('flames', 0), ('flames round', 0), ('shade', 0), ('bulbs', 0)]
  out += [('loose', k) for k in range(len(looseParts()))]
  out += [('gun', k) for k in range(len(gunParts()))]
  out += [('gun mark', 0)]
  out += [('hatch', 0)]
  out += [('car', k) for k in range(CARS * len(PLATE_HALVES))]
  out += [('door', 0)]
  out += [('lift', k) for k in range(2)]
  out += [(kind, k) for k in range(STATION_BOLTS)
          for kind in ('sbolt', 'sring')]
  return tuple(out)


def guarded(control: object) -> bool:
  """Returns whether 'control' has a guard over it: each switch and
  knob (user, 2026-11-16: "it should have a safety gaurd that is lifted
  up when adjusted. same for all toggle switch")."""
  peep = control.peep
  return type(peep).__name__ == 'FourthPeep' or isinstance(peep, Knob)


def guardHinge(control: object) -> tuple:
  """Returns where 'control''s guard hinges: on its face, at its far
  edge (its up side)."""
  half = GUARD_KNOB if isinstance(control.peep, Knob) else GUARD_SWITCH
  return pointAlong(control.peep.pivot, control.axes[1], half[1])


def ballCentre() -> tuple:
  """Returns the horizon's ball's middle (the globe's)."""
  return GLOBE_AT


def dialCentre(index: int) -> tuple:
  """Returns dial 'index''s middle on the panel's face."""
  u, v = DIALS[index][1]
  return panelPoint(u, v, 0.5 * PANEL_THICK + 0.004)


def lampCentre(index: int) -> tuple:
  """Returns lamp 'index''s middle on the panel's face."""
  u, v = LAMPS[index][1]
  return panelPoint(u, v, 0.5 * PANEL_THICK + 0.003)


def legendCentre(index: int) -> tuple:
  """Returns legend 'index''s middle: over its switch on the panel, or
  on the console beside the view's switch."""
  if index < len(SWITCHES):
    u, v = SWITCHES[index][3]
    return panelPoint(u, v + LEGEND_UP, 0.5 * PANEL_THICK + 0.002)
  x, y = CONSOLE_SWITCHES[index - len(SWITCHES)][3]
  return x - 0.04, y, TOP + 0.002


def legendAxes(index: int) -> tuple:
  """Returns legend 'index''s axes (right, up, out)."""
  if index < len(SWITCHES):
    return PANEL_AXES
  return CONSOLE_AXES


def headPlace(column: float) -> tuple:
  """Returns where the typehead is at 'column' of the line (nought to
  one along it): before the line typed, in the panel."""
  u, v = PAPER_AT
  return panelPoint(u - 0.5 * WIDTH * PITCH + column * WIDTH * PITCH,
                    v - 0.5 * PAPER_HIGH + PAPER_FOOT + 0.3 * LINE,
                    0.5 * PANEL_THICK + HEAD_OUT)


def paperLayout() -> dict:
  """Returns the teleprinter's paper's picture's layout, pixels: its
  'width' and 'height', the font's size ('font'), a line's ('line'),
  where the lines begin ('margin', from the left), the line typed's
  foot ('foot', up from the bottom), the green bars ('band', lines)."""
  scale = PAPER_PIXELS / PAPER_WIDE
  return {'width': PAPER_PIXELS, 'height': round(PAPER_HIGH * scale),
          'font': PITCH / ADVANCE * scale, 'line': LINE * scale,
          'margin': 0.5 * (PAPER_WIDE - WIDTH * PITCH) * scale,
          'foot': PAPER_FOOT * scale, 'band': BAND}


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  THE STILL FURNITURE   # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def panelFace() -> tuple:
  """Returns the panel's aluminium face, its picture across it (the
  printed legends: '_dashpictures.facePainted')."""
  right, up, out = PANEL_AXES
  rows = []
  for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
    place = panelPoint((2 * u - 1) * PANEL_HALF[0],
                       (2 * v - 1) * PANEL_HALF[1], 0.5 * PANEL_THICK)
    rows.append(place + out + (float(u), float(v)))
  return numpy.array(rows), numpy.array((0, 1, 2, 0, 2, 3), numpy.uint32)


def panelFrame() -> tuple:
  """Returns the rosewood frame round the panel and its back: a box a
  'FRAME' larger, just behind its face."""
  return boxRows(panelPoint(0.0, 0.0, -0.002), (PANEL_HALF[0] + FRAME,
                                                PANEL_HALF[1] + FRAME,
                                                0.5 * PANEL_THICK),
                 PANEL_AXES)


def dialFaces() -> tuple:
  """Returns the dials' faces, each its cell of the dials' picture (four
  across)."""
  parts = []
  for k in range(len(DIALS)):
    parts.append(discRows(dialCentre(k), PANEL_AXES, DIAL_RADIUS, 40,
                          (k / len(DIALS), 0.0, (k + 1) / len(DIALS), 1.0)))
  return joined(parts)


def bezels() -> tuple:
  """Returns the brushed rings round the dials and the switches'
  plates."""
  parts = []
  face = 0.5 * PANEL_THICK
  for k in range(len(DIALS)):
    parts.append(ringRows(dialCentre(k), PANEL_AXES, DIAL_RADIUS,
                          DIAL_RADIUS + 0.006, 0.008))
  for name, _, _, (u, v) in SWITCHES:
    parts.append(discRows(panelPoint(u, v, face + 0.001), PANEL_AXES,
                          0.011, 20, None))
  return joined(parts)


def domeRows() -> tuple:
  """Returns the glass dome over the globe's ball, a half sphere before
  it to its fixed ring, its picture (the reference marks painted on it,
  '_dashpictures.glassPainted') laid straight on from before."""
  right, up, out = GLOBE_AXES
  rows, faces = [], []
  rings, spokes = 24, 72
  for i in range(rings + 1):
    polar = 0.5 * math.pi * i / rings
    for j in range(spokes + 1):
      a = TAU * j / spokes
      x = math.sin(polar) * math.cos(a)
      y = math.sin(polar) * math.sin(a)
      z = math.cos(polar)
      normal = tuple(x * r + y * w + z * n for r, w, n in zip(right, up,
                                                              out))
      place = tuple(c + GLASS * q for c, q in zip(GLOBE_AT, normal))
      rows.append(place + normal + (0.5 + 0.5 * x, 0.5 + 0.5 * y))
  for i in range(rings):
    for j in range(spokes):
      a, b = i * (spokes + 1) + j, (i + 1) * (spokes + 1) + j
      faces.extend((a, b, b + 1, a, b + 1, a + 1))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def globeStand() -> tuple:
  """Returns the globe's stand (user, 2026-11-16: "like a globe"): a
  foot on the floor, a pillar up to the fixed ring round the ball's
  middle that holds the glass and the mechanism."""
  right, up, out = GLOBE_AXES
  x, y, z = GLOBE_AT
  ring = ringRows(tuple(c - 0.5 * FIXED_RING[1] * n for c, n in zip(
    GLOBE_AT, out)), GLOBE_AXES, GLASS, GLASS + FIXED_RING[0],
                  FIXED_RING[1])
  low = z - (GLASS + FIXED_RING[0]) * up[2]
  pillar = cylinderRows((x, y, FLOOR + FOOT[1]), (0.0, 0.0, 1.0), PILLAR,
                        low - FLOOR - FOOT[1], 20)
  foot = frustumRows((x, y, FLOOR), (0.0, 0.0, 1.0), FOOT[0],
                     0.6 * FOOT[0], FOOT[1], 40)
  return joined([ring, pillar, foot])


def monitorBody() -> tuple:
  """Returns the closed circuit monitor's cabinet (user, 2026-11-16:
  "make it more 1970 B&O just smaller"; "The CCTV should have more of a
  fake wood feel to it"; 2026-11-17: "The CCTV needs those curvier
  corners"): a printed walnut slab standing out of the panel round its
  screen, its corners round and its front edge rounded over (the veneer
  on its front: '_dashpictures.woodPainted')."""
  u, v = SCREEN_AT
  return roundedSlabRows(panelPoint(u, v, 0.5 * PANEL_THICK), PANEL_AXES,
                         (SCREEN_HALF[0] + CABINET_MARGIN,
                          SCREEN_HALF[1] + CABINET_MARGIN), MONITOR_OUT,
                         CABINET_ROUND, CABINET_EDGE, (0.0, 0.0, 1.0, 1.0))


def monitorInset() -> tuple:
  """Returns the monitor's black inset round its tube, its corners
  round, a hair before its cabinet's face."""
  u, v = SCREEN_AT
  return roundedSlabRows(panelPoint(u, v, 0.5 * PANEL_THICK + MONITOR_OUT
                                    - 0.001), PANEL_AXES,
                         (SCREEN_HALF[0] + INSET_MARGIN,
                          SCREEN_HALF[1] + INSET_MARGIN), 0.002,
                         INSET_ROUND, 0.001)


def screenRows() -> tuple:
  """Returns the monitor's screen in its inset: a picture tube's face,
  its corners round, its middle bulging; its picture the camera's (the
  whole of it)."""
  u, v = SCREEN_AT
  return roundedPaneRows(panelPoint(u, v, 0.5 * PANEL_THICK + MONITOR_OUT
                                    + 0.0012), PANEL_AXES, SCREEN_HALF,
                         TUBE_ROUND, TUBE_BULGE, (0.0, 0.0, 1.0, 1.0))


def paperRows() -> tuple:
  """Returns the teleprinter's paper in its window in the panel's
  middle, its picture what is typed on it."""
  u, v = PAPER_AT
  return quadRows(panelPoint(u, v, 0.5 * PANEL_THICK + 0.002), PANEL_AXES,
                  (0.5 * PAPER_WIDE, 0.5 * PAPER_HIGH), (0.0, 0.0, 1.0,
                                                         1.0))


def paperFrame() -> tuple:
  """Returns the chrome frame round the teleprinter's window."""
  u, v = PAPER_AT
  w, h, edge = 0.5 * PAPER_WIDE, 0.5 * PAPER_HIGH, 0.006
  out = 0.5 * PANEL_THICK + 0.005
  bars = [((u, v + h + edge), (w + 2 * edge, edge)),
          ((u, v - h - edge), (w + 2 * edge, edge)),
          ((u - w - edge, v), (edge, h)), ((u + w + edge, v), (edge, h))]
  return joined([boxRows(panelPoint(bu, bv, out), (hu, hv, 0.005),
                         PANEL_AXES) for (bu, bv), (hu, hv) in bars])


def snackBag() -> tuple:
  """Returns the bag of pork scratchings under the dashboard."""
  middle, axes, half = SNACK_BAG
  return boxRows(middle, half, axes)


def snackTray() -> tuple:
  """Returns the little tray the bag stands on, under the panel."""
  middle, axes, half = SNACK_BAG
  foot = tuple(m - half[1] * u - 0.004 * u for m, u in zip(middle,
                                                            axes[1]))
  return boxRows(foot, (half[0] + 0.03, 0.004, half[2] + 0.03), axes)


def sliderTrack() -> tuple:
  """Returns the throttle's slide control's slot along the right
  console."""
  middle = (SLIDER_FROM[0] + 0.5 * SLIDER_LONG, SLIDER_FROM[1], TOP + 0.001)
  return boxRows(middle, (0.5 * SLIDER_LONG + 0.012, 0.007, 0.002),
                 UNTURNED)


def consoleBases() -> tuple:
  """Returns the plates under the consoles' keys and the view's switch."""
  parts = []
  for _, _, _, (x, y) in CONSOLE_SWITCHES:
    parts.append(discRows((x, y, TOP + 0.001), ((0.0, 1.0, 0.0),
                                                (1.0, 0.0, 0.0),
                                                (0.0, 0.0, 1.0)), 0.013, 20,
                          None))
  return joined(parts)


def sideboardRows() -> tuple:
  """Returns the rosewood sideboard at his right the tape deck stands
  on (its top a plate's thickness under 'TOP')."""
  middle, half = SIDEBOARD
  return boxRows((middle[0], middle[1], middle[2] - 0.002),
                 (half[0], half[1], half[2] - 0.002), UNTURNED)


def sideboardTop() -> tuple:
  """Returns the sideboard's brushed aluminium top, its face at 'TOP'
  (the deck's keys stand on it)."""
  middle, half = SIDEBOARD
  return boxRows((middle[0], middle[1], TOP - 0.002),
                 (half[0] + 0.004, half[1] + 0.004, 0.002), UNTURNED)


def ringParts() -> tuple:
  """Returns the horizon's roll ring as it rests, about the ball's
  middle in the panel's own axes (x right, y up, z out): a brass ring
  round the ball's middle, a tab on its top (its turn shows)."""
  ring = ringRows((0.0, 0.0, -0.004), UNTURNED, BALL_RADIUS + 0.008,
                  BALL_RADIUS + 0.018, 0.008)
  tab = boxRows((0.0, BALL_RADIUS + 0.021, 0.0), (0.008, 0.004, 0.005),
                UNTURNED)
  return joined([ring, tab])


def axleParts() -> tuple:
  """Returns the horizon's pitch axles as they rest (about the ball's
  middle, the panel's own axes): two stubs from the ring into the ball's
  sides along x."""
  stubs = [cylinderRows((side * (BALL_RADIUS - 0.005), 0.0, 0.0),
                        (side, 0.0, 0.0), 0.007, 0.018, 16)
           for side in (-1.0, 1.0)]
  return joined(stubs)


def hubParts() -> tuple:
  """Returns the ball's polar hubs as they rest (about its middle, the
  panel's own axes): a cap on each pole, along y."""
  caps = [cylinderRows((0.0, side * (BALL_RADIUS - 0.003), 0.0),
                       (0.0, side, 0.0), 0.012, 0.009, 20)
          for side in (-1.0, 1.0)]
  return joined(caps)


def decalRows(index: int, count: int) -> tuple:
  """Returns a mark's decal as it rests: a little square facing z, laid
  over cell 'index' of 'count' across the marks' picture."""
  return quadRows((0.0, 0.0, 0.0), UNTURNED, (DECAL, DECAL), (
    index / count, 0.0, (index + 1) / count, 1.0))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  THE MOVING PIECES   # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def pieceRows(piece: tuple, cells: dict) -> tuple:
  """Returns a moving piece's mesh about where it turns or slides from
  (its rest: a switch's bat straight out, a knob's mark up, a needle up),
  in the vessel's own axes; 'cells' are where each key's and legend's
  label lies on the labels' picture (by name: u0, v0, u1, v1)."""
  kind, what = piece
  if kind == 'control':
    return _inputRows(what, cells)
  if kind == 'needle':
    return _needleRows(what)
  if kind == 'lamp':
    return discRows(lampCentre(what), PANEL_AXES, LAMP_RADIUS, 16, None)
  if kind == 'legend':
    name = LEGENDS[what]
    return quadRows(legendCentre(what), legendAxes(what), LEGEND_HALF,
                    cells[name])
  if kind == 'deck':
    part = movingParts()[what]
    return part[4], part[5]
  if kind == 'guard':
    return _guardRows(what)
  if kind == 'glint':
    return _glintRows(what)
  if kind == 'glint lid':
    return _glintLidRows(what)
  if kind in LIGHTS:
    return LIGHTS[kind]()
  if kind == 'loose':
    part = looseParts()[what]
    return part[2], part[3]
  if kind == 'gun':
    part = gunParts()[what]
    return part[2], part[3]
  if kind == 'gun mark':
    middle, half = sideMark()
    return quadRows(middle, ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0),
                             (-1.0, 0.0, 0.0)), (half, half))
  if kind == 'hatch':
    rows, faces = cylinderRows((0.0, 0.0, NOSE - 0.06), (0.0, 0.0, 1.0),
                               HATCH - 0.03, 0.05, 32)
    return rowsAbout(rows, HATCH_HINGE), faces
  if kind == 'car':
    return boxRows((0.0, 0.0, 0.0), PLATE_HALVES[what % len(PLATE_HALVES)],
                   UNTURNED)
  if kind == 'door':
    return leafRows()
  if kind == 'sbolt':
    return boltPieceRows()
  if kind == 'lift':
    (x0, y0, _), (x1, y1, _) = SHAFT
    return boxRows((0.0, 0.0, 0.0), (0.5 * (x1 - x0) - 0.02,
                                     0.5 * (y1 - y0) - 0.02, PLATE),
                   UNTURNED)
  if kind == 'sring':
    return ringPieceRows()
  if kind == 'bug':
    right, up, out = PANEL_AXES
    centre = dialCentre(ALTIMETER)
    middle = pointAlong(pointAlong(centre, up, 0.86 * DIAL_RADIUS), out,
                        0.004)
    return boxRows(middle, (0.0024, 0.13 * DIAL_RADIUS, 0.0012),
                   PANEL_AXES, None, centre)
  return boxRows((0.0, 0.0, 0.0), HEAD_HALF, PANEL_AXES)


def pivotOf(piece: tuple) -> tuple:
  """Returns the point a moving piece turns or slides from (its mesh
  is made about it: 'pieceRows')."""
  kind, what = piece
  if kind == 'control':
    return what.peep.pivot
  if kind == 'needle':
    return dialCentre(what)
  if kind == 'deck':
    return movingParts()[what][3]
  if kind == 'bug':
    return dialCentre(ALTIMETER)
  if kind == 'guard':
    return guardHinge(what)
  if kind == 'glint':
    return what.peep.pivot
  if kind == 'glint lid':
    return guardHinge(what)
  if kind == 'typehead':
    return headPlace(0.0)
  if kind == 'loose':
    return looseThings()[looseParts()[what][0]][1]
  if kind in ('gun', 'gun mark'):
    return EYE
  if kind == 'hatch':
    return HATCH_HINGE
  return 0.0, 0.0, 0.0


def _needleRows(index: int) -> tuple:
  """Returns dial 'index''s needle as a lever on its shaft (user,
  2026-11-16: "the needle should be modelled as an actually moving lever
  on a rotating actuator"), about the dial's middle, pointing up: the
  shaft's boss standing out of the face, the arm out to near the rim,
  a counterweight's tail behind, a cap on the boss."""
  right, up, out = PANEL_AXES
  centre = dialCentre(index)
  boss = cylinderRows(centre, out, 0.0055, 0.009, 20)
  arm = boxRows(pointAlong(pointAlong(centre, up, 0.44 * DIAL_RADIUS), out,
                       0.0075), (0.0014, 0.44 * DIAL_RADIUS, 0.0012),
                PANEL_AXES)
  tail = boxRows(pointAlong(pointAlong(centre, up, -0.13 * DIAL_RADIUS), out,
                        0.0075), (0.0032, 0.13 * DIAL_RADIUS, 0.0016),
                 PANEL_AXES)
  cap = cylinderRows(pointAlong(centre, out, 0.009), out, 0.0035, 0.003, 16)
  return joined([boss, arm, tail, cap], centre)


def _guardRows(control: object) -> tuple:
  """Returns 'control''s guard as it rests closed over it, about its
  hinge: a flip cover hinged at its far edge, lying down over the
  input: a thin lid, its two sides and a lip at its free end (open at
  the hinge and underneath)."""
  right, up, out = control.axes
  hx, hy, hz = GUARD_KNOB if isinstance(control.peep, Knob) else (
    GUARD_SWITCH)
  hinge = guardHinge(control)
  t = GUARD_WALL
  middle = pointAlong(pointAlong(hinge, up, -hy), out, hz)
  lid = boxRows(pointAlong(middle, out, hz - 0.5 * t), (hx, hy, 0.5 * t),
                control.axes)
  sides = [boxRows(pointAlong(middle, right, side * (hx - 0.5 * t)),
                   (0.5 * t, hy, hz), control.axes) for side in (-1, 1)]
  lip = boxRows(pointAlong(middle, up, -(hy - 0.5 * t)), (hx, 0.5 * t, hz),
                control.axes)
  return joined([lid] + sides + [lip], hinge)


def _glintRows(control: object) -> tuple:
  """Returns an enchanted knob's glint (user, 2026-11-16, the warp: "give
  it a sort of enchantment glint, as it is kinda... magic"): a shell a
  hair round the knob about its pivot, its picture wrapped round its
  side and across its top (the glint's streaks slide over it)."""
  right, up, out = control.axes
  pivot = control.peep.pivot
  radius, high = 1.07 * control.peep.length, 0.0175
  rows, faces = [], []
  sides = 40
  for k in range(sides + 1):
    a = TAU * k / sides
    way = tuple(math.cos(a) * r + math.sin(a) * u for r, u in zip(right,
                                                                  up))
    for lift, v in ((0.0, 0.0), (high, 0.5)):
      place = tuple(p + radius * w + lift * n for p, w, n in zip(
        pivot, way, out))
      rows.append(place + way + (2.0 * k / sides, v))
  for k in range(sides):
    a, b = 2 * k, 2 * k + 2
    faces.extend((a, b, b + 1, a, b + 1, a + 1))
  middle = len(rows)
  top = tuple(p + high * n for p, n in zip(pivot, out))
  rows.append(top + tuple(out) + (0.5, 0.75))
  for k in range(sides + 1):
    a = TAU * k / sides
    c, s = math.cos(a), math.sin(a)
    place = tuple(t + radius * (c * r + s * u) for t, r, u in zip(
      top, right, up))
    rows.append(place + tuple(out) + (0.5 + 0.5 * c, 0.5 + 0.25 * s))
  for k in range(sides):
    faces.extend((middle, middle + 1 + k, middle + 2 + k))
  return (rowsAbout(numpy.array(rows), pivot),
          numpy.array(faces, numpy.uint32))


def _glintLidRows(control: object) -> tuple:
  """Returns the glint on an enchanted knob's guard: its lid's face a hair
  over it, the glint's picture across it (the whole tool glints)."""
  right, up, out = control.axes
  hx, hy, hz = GUARD_KNOB
  hinge = guardHinge(control)
  middle = pointAlong(pointAlong(hinge, up, -hy), out, 2.0 * hz + 0.0006)
  rows, faces = quadRows(middle, control.axes, (hx + 0.0006, hy + 0.0006),
                         (0.0, 0.0, 1.0, 1.0))
  return rowsAbout(rows, hinge), faces


def _inputRows(control: object, cells: dict) -> tuple:
  """Returns an input's moving part about its pivot: a switch's bat
  straight out, a knob with its mark, a key's cap (its label from the
  labels' picture), the slide control's knob."""
  peep = control.peep
  pivot = peep.pivot
  right, up, out = control.axes
  if isinstance(peep, Knob):
    knob = cylinderRows(pivot, out, peep.length, 0.016, 28)
    middle = tuple(p + 0.6 * peep.length * u + 0.017 * n
                   for p, u, n in zip(pivot, up, out))
    mark = boxRows(middle, (0.0018, 0.35 * peep.length, 0.001),
                   control.axes)
    return joined([knob, mark], pivot)
  if isinstance(peep, Pushbutton):
    half = KEY_HALF if control.half[0] == KEY_HALF[0] else CONSOLE_KEY_HALF
    cap = boxRows(tuple(p + 0.006 * n for p, n in zip(pivot, out)),
                  (half[0], half[1], 0.006), control.axes,
                  cells.get(control.name))
    return joined([cap], pivot)
  if isinstance(peep, Slider):
    knob = boxRows((pivot[0], pivot[1], pivot[2] + 0.014), (0.016, 0.022,
                                                           0.014), UNTURNED)
    return joined([knob], pivot)
  bat = cylinderRows(pivot, out, 0.0035, BAT_LONG, 12)
  tip = cylinderRows(tuple(p + BAT_LONG * n for p, n in zip(pivot, out)),
                     out, 0.006, 0.006, 12)
  return joined([bat, tip], pivot)
