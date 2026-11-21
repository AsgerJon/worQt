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

from ._cockpit import BAT_LONG, BALL_OUT, BALL_RADIUS, CONSOLE_AXES
from ._cockpit import CONSOLE_SWITCHES, DIAL_RADIUS
from ._cockpit import DIALS, EYE, FACE_HIGH, FACE_LOW, GLASS, GLOBE_AT
from ._cockpit import GLOBE_AXES, HOOD_DEEP, HOOD_HIGH, HOOD_RADIUS
from ._cockpit import HOOD_SPAN, LEFT_CONSOLE, LIT_KEYS, PANEL_AXES
from ._cockpit import GUARD_KNOB, GUARD_LAUNCH, GUARD_SWITCH, LAMP_RADIUS
from ._cockpit import CHECK_AT, CHECK_LINE, CHECK_RADIUS
from ._cockpit import LAMPS, LEGEND_HALF, MONITOR_OUT, PANEL_DEEP
from ._cockpit import PANEL_RADIUS, PANEL_SPAN, PAPER_AT, RANGE, RISER
from ._cockpit import PAPER_HIGH, PAPER_WIDE, RIGHT_CONSOLE, SCREEN_AT
from ._cockpit import PORT, SCREEN_HALF, SIDEBOARD, SNACK_BAG, STATUS
from ._cockpit import THROTTLE_AT, THROTTLE_KNOB, THROTTLE_TRAVEL, TOP
from ._cockpit import dialFrame, dialPoint
from ._cockpit import hoodAxes, hoodPoint, panelAxes, panelPoint
from ._quest import CHECKLIST
from ._deckmodel import movingParts
from ._elevator import PLATE_HALVES, buttonRows, glassRows, guardRows
from ._elevator import plateRows, seatRows
from ._deckthings import deckThingRows, deckThings
from ._shaftdoor import shaftLeafRows
from ._teleprinter import LINE, PITCH, WIDTH
from ._walkwaymeshes import doorGlassRows, leafRows
from ._towerlift import carHalves, carWindow
from ._shapes import UNTURNED, boxRows, pointAlong, rowsAbout
from ._shapes import cylinderRows, discRows, frustumRows, joined
from ._shapes import quadRows, ringRows, roundedPaneRows
from ._stationlamps import cageLampRows, ringLampRows
from ._shapes import roundedSlabRows, sheetRows
from ._egg import marbleRows
from ._furnishings import bulbsRows, flamesRows, looseParts
from ._furnishings import looseThings, roundFlamesRows, shadeRows

TAU = 2.0 * math.pi
#  Half a horizon mark's decal, m.
DECAL = 0.02
#  The dials' scales: each dial's name, the value its scale's log turns
#  round at (a hundred metres, ten metres a second; None: the scale is
#  even, the THRUST's in g), its last value, its ticks (value and the
#  number printed) and its unit; the needle sweeps 'SWEEP' rad from its
#  first tick (clockwise seen from before it).
DIAL_SCALES = {
  'HEIGHT': (100.0, 1e6, ((0.0, '0'), (1e3, '1'), (1e4, '10'),
                          (1e5, '100'), (1e6, '1000')), 'KM'),
  'SPEED': (10.0, 1e4, ((0.0, '0'), (100.0, '100'), (1e3, '1K'),
                        (1e4, '10K')), 'M/S'),
  'APOAPSIS': (100.0, 1e6, ((0.0, '0'), (1e3, '1'), (1e4, '10'),
                            (1e5, '100'), (1e6, '1000')), 'KM'),
  'PERIAPSIS': (100.0, 1e6, ((0.0, '0'), (1e3, '1'), (1e4, '10'),
                             (1e5, '100'), (1e6, '1000')), 'KM'),
  'THRUST': (None, 4.0, ((0.0, '0'), (1.0, '1'), (2.0, '2'), (3.0, '3'),
                         (4.0, '4')), 'G')}
SWEEP = math.radians(270.0)
#  The dials marked by a bug: the altimeter at the ascent's target
#  (pink), the THRUST at the limiter's (amber).
ALTIMETER = [name for name, _ in DIALS].index('HEIGHT')
THRUSTMETER = [name for name, _ in DIALS].index('THRUST')
BUGS = (ALTIMETER, THRUSTMETER)
#  The lamps' colours (0 to 255) by name: amber but the orbit's green and
#  the ground's red.
LAMP_COLOURS = {'ENGINE': (255, 160, 40), 'AIR': (255, 160, 40),
                'GROUND': (255, 60, 40), 'WARP': (255, 160, 40),
                'GUIDE': (255, 160, 40), 'ORBIT': (90, 255, 110),
                'DOCK': (90, 255, 110)}
#  What lights amber on smoked glass: the lit keys' caps (the
#  AUTOPILOT's modes, MATCH), then the legends beside the console's
#  switches (the view's and the map's: pieces of their own).
LEGENDS = LIT_KEYS + tuple(name for name, _, _, _ in CONSOLE_SWITCHES)
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
#  The globe's mount in the panel: its fixed ring's width and depth
#  (round the glass), m; the black cowl from the panel's face out to it.
FIXED_RING = (0.012, 0.016)
#  The curved sheets' steps round (rad); the readouts' canvas (pixels
#  across: the status line over the range's tubes, each as high as its
#  window's shape asks) and the range's groups of tubes, each its label
#  (printed under it on the hood) and how many tubes; the gap round each
#  group, tubes.
STEP = math.radians(1.0)
READOUT_PIXELS = 1024
RANGE_GROUPS = (('RANGE KM', 5), ('CLOSING M/S', 5), ('CLOSEST KM', 5),
                ('IN H:MM', 4))
GROUP_GAP = 0.6
#  The cabin's lights' meshes, by their pieces' kinds (drawn where they
#  are, about nothing).
LIGHTS = {'flames': flamesRows, 'flames round': roundFlamesRows,
          'shade': shadeRows, 'bulbs': bulbsRows}
#  The knobs that glint, enchanted (user, 2026-11-16 of the warp: "give
#  it a sort of enchantment glint, as it is kinda... magic"), by their
#  actions.
ENCHANTED = ('warp', 'action')
#  The space station's elevators (cages); the top floor's doors.
CARS = 4
SHAFT_DOORS = 4
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
  if turn is None:
    return value / most
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
  ('loose', its index in '_furnishings.looseParts'), the gravity egg's
  glowing marble ('egg ball', about its middle: '_egg'),
  the station's elevators' cages' plates ('car', six a cage:
  '_elevator.PLATE_HALVES', the sides framing their windows), their
  windows' panes ('car glass', four a cage), seats ('car seat', one a
  cage, with the button's post and the handrail), buttons ('car
  button') and their guards ('car guard'), the deck's loose furnishings
  ('deck thing', '_deckthings'), the
  door's leaf ('door': it slides round
  into the wall, '_walkway') and its window's pane ('door glass'), the
  top floor's four doors' leaves ('shaft door': each slides round into
  the head's wall, '_shaftdoor'), the launch tower's lift's car's
  floor, roof and two walls ('lift', '_towerlift'; the walls' windows
  cut) and the walls' panes ('lift glass'), the head's lamp rings
  ('level lamp': levels
  one and two, '_stationlamps') and the cages' lamps docked ('car lamp':
  a bar in each cage)."""
  out = [('control', control) for control in controls]
  out += [('needle', k) for k in range(len(DIALS))]
  out += [('lamp', k) for k in range(len(LAMPS))]
  out += [('legend', k) for k in range(len(LIT_KEYS), len(LEGENDS))]
  out += [('deck', k) for k in range(len(movingParts()))]
  out += [('bug', k) for k in range(len(BUGS))] + [('typehead', 0)]
  out += [('guard', control) for control in controls if guarded(control)]
  out += [(kind, control) for control in controls
          if control.action in ENCHANTED for kind in (
            ('glint', 'glint lid') if guarded(control) else ('glint',))]
  out += [('check', k) for k in range(len(CHECKLIST))]
  out += [('flames', 0), ('flames round', 0), ('shade', 0), ('bulbs', 0)]
  out += [('loose', k) for k in range(len(looseParts()))]
  out += [('egg ball', 0)]
  out += [('car', k) for k in range(CARS * len(PLATE_HALVES))]
  out += [('car glass', k) for k in range(CARS * 4)]
  out += [('car seat', k) for k in range(CARS)]
  out += [('car button', k) for k in range(CARS)]
  out += [('car guard', k) for k in range(CARS)]
  out += [('deck thing', k) for k in range(len(deckThings()))]
  out += [('door', 0), ('door glass', 0)]
  out += [('shaft door', k) for k in range(SHAFT_DOORS)]
  out += [('lift', k) for k in range(4)]
  out += [('lift glass', k) for k in range(2)]
  out += [('level lamp', 1), ('level lamp', 2)]
  out += [('car lamp', k) for k in range(CARS)]
  return tuple(out)


def _liftRows(what: int) -> tuple:
  """Returns the lift's car's piece 'what' about its middle: its floor
  and roof plates (nought, one), its west and south walls (two, three),
  each wall's window cut through it ('_towerlift.carWindow')."""
  half = carHalves()[what]
  if what < 2:
    return boxRows((0.0, 0.0, 0.0), half, UNTURNED)
  wall = what - 2
  along = 1 if wall == 0 else 0
  (a, b), (low, high) = carWindow(wall)
  long, tall = half[along], half[2]
  pieces = []
  for (s0, s1), (z0, z1) in (((-long, long), (-tall, low)),
                             ((-long, long), (high, tall)),
                             ((-long, a), (low, high)),
                             ((b, long), (low, high))):
    middle, size = [0.0, 0.0, 0.5 * (z0 + z1)], list(half)
    middle[along], size[along] = 0.5 * (s0 + s1), 0.5 * (s1 - s0)
    size[2] = 0.5 * (z1 - z0)
    pieces.append(boxRows(tuple(middle), tuple(size), UNTURNED))
  return joined(pieces)


def guarded(control: object) -> bool:
  """Returns whether 'control' has a guard over it: each switch and
  knob (user, 2026-11-16: "it should have a safety gaurd that is lifted
  up when adjusted. same for all toggle switch") and the LAUNCH key."""
  peep = control.peep
  return type(peep).__name__ == 'FourthPeep' or isinstance(
    peep, Knob) or control.action == 'launch'


def guardHalf(control: object) -> tuple:
  """Returns half the size of 'control''s guard (across, up, out)."""
  if control.action == 'launch':
    return GUARD_LAUNCH
  return GUARD_KNOB if isinstance(control.peep, Knob) else GUARD_SWITCH


def guardHinge(control: object) -> tuple:
  """Returns where 'control''s guard hinges: on its face, at its far
  edge (its up side)."""
  return pointAlong(control.peep.pivot, control.axes[1],
                    guardHalf(control)[1])


def ballCentre() -> tuple:
  """Returns the horizon's ball's middle (the globe's)."""
  return GLOBE_AT


def dialCentre(index: int) -> tuple:
  """Returns dial 'index''s middle on its face (the hood's, or the
  panel's: the THRUST's)."""
  return dialPoint(index, 0.004)


def dialAxes(index: int) -> tuple:
  """Returns dial 'index''s axes (its face's there)."""
  return dialFrame(index)


def checkCentre(index: int) -> tuple:
  """Returns the LAUNCH checklist's lamp 'index''s middle on the
  panel's face."""
  u, v = CHECK_AT
  return panelPoint(u, v - index * CHECK_LINE, 0.002)


def lampCentre(index: int) -> tuple:
  """Returns lamp 'index''s middle on the hood's face."""
  u, v = LAMPS[index][1]
  return hoodPoint(u, v, 0.003)


def legendCentre(index: int) -> tuple:
  """Returns legend 'index''s middle on the console beside its switch
  (the lit keys' are their caps)."""
  x, y = CONSOLE_SWITCHES[index - len(LIT_KEYS)][3]
  return x - 0.04, y, TOP + 0.002


def legendAxes(index: int) -> tuple:
  """Returns legend 'index''s axes (right, up, out)."""
  return CONSOLE_AXES


def headPlace(column: float) -> tuple:
  """Returns where the typehead is at 'column' of the line (nought to
  one along it): before the line typed, in the panel."""
  u, v = PAPER_AT
  return panelPoint(u - 0.5 * WIDTH * PITCH + column * WIDTH * PITCH,
                    v - 0.5 * PAPER_HIGH + PAPER_FOOT + 0.3 * LINE,
                    HEAD_OUT)


def readoutLayout() -> dict:
  """Returns the readouts' canvas's layout, pixels: its 'width' and
  'height', the status line's height on its top ('status'), the range's
  under it ('range') and the docking port's numbers' under that
  ('port'), the range's 'groups' (each its 'label', where its first tube
  begins ('from'), how many 'tubes', a tube's width ('tube'))."""
  status, far, port = STATUS[1], RANGE[1], PORT[1]
  statusHigh = round(READOUT_PIXELS * status[1] / status[0])
  rangeHigh = round(READOUT_PIXELS * far[1] / far[0])
  portHigh = round(READOUT_PIXELS * port[1] / port[0])
  tubes = sum(count for _, count in RANGE_GROUPS)
  tube = READOUT_PIXELS / (tubes + GROUP_GAP * (len(RANGE_GROUPS) + 1))
  groups, at = [], GROUP_GAP * tube
  for label, count in RANGE_GROUPS:
    groups.append({'label': label, 'from': at, 'tubes': count,
                   'tube': tube})
    at += (count + GROUP_GAP) * tube
  return {'width': READOUT_PIXELS,
          'height': statusHigh + rangeHigh + portHigh,
          'status': statusHigh, 'range': rangeHigh, 'port': portHigh,
          'groups': groups}


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

def _away(axis: tuple) -> tuple:
  """Returns 'axis' the other way."""
  return tuple(-x for x in axis)


def _span(left: float, right: float, radius: float) -> list:
  """Returns the steps along a curved sheet's middle line ('radius' m
  out) from 'left' to 'right' m along it, a 'STEP' round or less."""
  count = max(2, int(math.ceil(abs(right - left) / radius / STEP)) + 1)
  return [left + (right - left) * k / (count - 1) for k in range(count)]


def _sheet(pointOf: object, axesOf: object, rights: list, ups: tuple,
           out: float, cell: tuple = None) -> tuple:
  """Returns a curved sheet on the panel or the hood ('pointOf', 'axesOf':
  their own) across 'rights', up 'ups', 'out' before its face, facing
  out, laid over 'cell' of a picture."""
  places = [[pointOf(r, u, out) for u in ups] for r in rights]
  normals = [[axesOf(r)[2]] * len(ups) for r in rights]
  return sheetRows(places, normals, cell)


def _bodyRows(pointOf: object, axesOf: object, rights: list, low: float,
              high: float, deep: float) -> tuple:
  """Returns the body behind a curved face (from 'low' to 'high' up it,
  'deep' m deep): its back, its top, its foot and its two ends."""
  first, last = rights[0], rights[-1]
  back = sheetRows([[pointOf(r, u, -deep) for u in (high, low)]
                    for r in rights], [[_away(axesOf(r)[2])] * 2
                                       for r in rights])
  top = sheetRows([[pointOf(r, high, o) for o in (0.0, -deep)]
                   for r in rights], [[axesOf(r)[1]] * 2 for r in rights])
  foot = sheetRows([[pointOf(r, low, o) for o in (-deep, 0.0)]
                    for r in rights], [[_away(axesOf(r)[1])] * 2
                                       for r in rights])
  ends = []
  for at, outs, way in ((first, (-deep, 0.0), _away(axesOf(first)[0])),
                        (last, (0.0, -deep), axesOf(last)[0])):
    ends.append(sheetRows([[pointOf(at, u, o) for u in (low, high)]
                           for o in outs], [[way] * 2] * 2))
  return joined([back, top, foot] + ends)


def panelFace() -> tuple:
  """Returns the panel's aluminium face, curved round him (user,
  2026-11-17: "have the dashboard curve maybe?"), its picture across it
  (the printed legends: '_dashpictures.facePainted'), along its middle
  line and up its slant."""
  rights = _span(-PANEL_RADIUS * PANEL_SPAN, PANEL_RADIUS * PANEL_SPAN,
                 PANEL_RADIUS)
  return _sheet(panelPoint, panelAxes, rights, (FACE_LOW, FACE_HIGH), 0.0,
                (0.0, 0.0, 1.0, 1.0))


def panelBody() -> tuple:
  """Returns the panel's rosewood body behind its face and the risers
  its wings stand on, one on each console."""
  rights = _span(-PANEL_RADIUS * PANEL_SPAN, PANEL_RADIUS * PANEL_SPAN,
                 PANEL_RADIUS)
  parts = [_bodyRows(panelPoint, panelAxes, rights, FACE_LOW, FACE_HIGH,
                     PANEL_DEEP)]
  (ahead, inward), (hx, hy) = RISER
  for (x, y, _), _ in (LEFT_CONSOLE, RIGHT_CONSOLE):
    low, high = TOP, panelPoint(0.0, FACE_LOW, 0.0)[2] - 0.03
    parts.append(boxRows((x + ahead, y - math.copysign(inward, y - EYE[1]),
                          0.5 * (low + high)), (hx, hy, 0.5 * (high - low)),
                         UNTURNED))
  return joined(parts)


def hoodFace() -> tuple:
  """Returns the hood's face over the panel's middle (user, 2026-11-17:
  "Move the indicator dials above the dashboard"), its picture across it
  ('_dashpictures.hoodPainted')."""
  rights = _span(-HOOD_RADIUS * HOOD_SPAN, HOOD_RADIUS * HOOD_SPAN,
                 HOOD_RADIUS)
  return _sheet(hoodPoint, hoodAxes, rights, (0.0, HOOD_HIGH), 0.0,
                (0.0, 0.0, 1.0, 1.0))


def hoodBody() -> tuple:
  """Returns the hood's rosewood body behind its face."""
  rights = _span(-HOOD_RADIUS * HOOD_SPAN, HOOD_RADIUS * HOOD_SPAN,
                 HOOD_RADIUS)
  return _bodyRows(hoodPoint, hoodAxes, rights, 0.0, HOOD_HIGH, HOOD_DEEP)


def dialFaces() -> tuple:
  """Returns the dials' faces, each its cell of the dials' picture (four
  across)."""
  parts = []
  for k in range(len(DIALS)):
    parts.append(discRows(dialCentre(k), dialAxes(k), DIAL_RADIUS, 40,
                          (k / len(DIALS), 0.0, (k + 1) / len(DIALS), 1.0)))
  return joined(parts)


def bezels() -> tuple:
  """Returns the chrome rings round the dials."""
  return joined([ringRows(dialCentre(k), dialAxes(k), DIAL_RADIUS,
                          DIAL_RADIUS + 0.006, 0.008)
                 for k in range(len(DIALS))])


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


def globeMount() -> tuple:
  """Returns the globe's fixed ring round its glass at the ball's
  middle, where the glass and the mechanism hold."""
  out = GLOBE_AXES[2]
  return ringRows(pointAlong(GLOBE_AT, out, -0.5 * FIXED_RING[1]),
                  GLOBE_AXES, GLASS, GLASS + FIXED_RING[0], FIXED_RING[1])


def globeCowl() -> tuple:
  """Returns the black cowl the globe stands out of the panel in, from
  its face out to the fixed ring (the ball's back half sunk in it)."""
  out = GLOBE_AXES[2]
  return cylinderRows(pointAlong(GLOBE_AT, out, -BALL_OUT), out,
                      GLASS + FIXED_RING[0], BALL_OUT - 0.5 * FIXED_RING[1],
                      48)


def monitorBody() -> tuple:
  """Returns the closed circuit monitor's cabinet (user, 2026-11-16:
  "make it more 1970 B&O just smaller"; "The CCTV should have more of a
  fake wood feel to it"; 2026-11-17: "The CCTV needs those curvier
  corners"): a printed walnut slab standing out of the panel round its
  screen, its corners round and its front edge rounded over (the veneer
  on its front: '_dashpictures.woodPainted')."""
  u, v = SCREEN_AT
  return roundedSlabRows(panelPoint(u, v, 0.0), panelAxes(u),
                         (SCREEN_HALF[0] + CABINET_MARGIN,
                          SCREEN_HALF[1] + CABINET_MARGIN), MONITOR_OUT,
                         CABINET_ROUND, CABINET_EDGE, (0.0, 0.0, 1.0, 1.0))


def monitorInset() -> tuple:
  """Returns the monitor's black inset round its tube, its corners
  round, a hair before its cabinet's face."""
  u, v = SCREEN_AT
  return roundedSlabRows(panelPoint(u, v, MONITOR_OUT - 0.001),
                         panelAxes(u), (SCREEN_HALF[0] + INSET_MARGIN,
                                        SCREEN_HALF[1] + INSET_MARGIN),
                         0.002, INSET_ROUND, 0.001)


def screenRows() -> tuple:
  """Returns the monitor's screen in its inset: a picture tube's face,
  its corners round, its middle bulging; its picture the camera's (the
  whole of it)."""
  u, v = SCREEN_AT
  return roundedPaneRows(panelPoint(u, v, MONITOR_OUT + 0.0012),
                         panelAxes(u), SCREEN_HALF, TUBE_ROUND, TUBE_BULGE,
                         (0.0, 0.0, 1.0, 1.0))


def paperRows() -> tuple:
  """Returns the teleprinter's paper in its window in the panel's
  middle, curved with it, its picture what is typed on it."""
  u, v = PAPER_AT
  w, h = 0.5 * PAPER_WIDE, 0.5 * PAPER_HIGH
  return _sheet(panelPoint, panelAxes, _span(u - w, u + w, PANEL_RADIUS),
                (v - h, v + h), 0.002, (0.0, 0.0, 1.0, 1.0))


def paperFrame() -> tuple:
  """Returns the chrome frame round the teleprinter's window: a bar
  over it and under it (curved with the panel) and one either side."""
  u, v = PAPER_AT
  w, h, edge = 0.5 * PAPER_WIDE, 0.5 * PAPER_HIGH, 0.006
  rights = _span(u - w - edge, u + w + edge, PANEL_RADIUS)
  bars = [_sheet(panelPoint, panelAxes, rights, (v + h, v + h + edge),
                 0.005), _sheet(panelPoint, panelAxes, rights,
                                (v - h - edge, v - h), 0.005)]
  for side in (-1.0, 1.0):
    at = u + side * (w + 0.5 * edge)
    bars.append(boxRows(panelPoint(at, v, 0.0025), (0.5 * edge, h, 0.0025),
                        panelAxes(at)))
  return joined(bars)


def readoutRows() -> tuple:
  """Returns the readouts' windows, all on the readouts' canvas (top
  to bottom): the AUTOPILOT's status line on the panel, Terra Prime's
  range on the hood, the docking port's numbers on the panel under the
  CCTV."""
  layout = readoutLayout()
  low = layout['port'] / layout['height']
  split = (layout['port'] + layout['range']) / layout['height']
  (u, v), (hw, hh) = STATUS
  status = _sheet(panelPoint, panelAxes, _span(u - hw, u + hw,
                                               PANEL_RADIUS),
                  (v - hh, v + hh), 0.002, (0.0, split, 1.0, 1.0))
  (u, v), (hw, hh) = RANGE
  far = _sheet(hoodPoint, hoodAxes, _span(u - hw, u + hw, HOOD_RADIUS),
               (v - hh, v + hh), 0.002, (0.0, low, 1.0, split))
  (u, v), (hw, hh) = PORT
  port = _sheet(panelPoint, panelAxes, _span(u - hw, u + hw,
                                             PANEL_RADIUS),
                (v - hh, v + hh), 0.002, (0.0, 0.0, 1.0, low))
  return joined([status, far, port])


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


def throttleBush() -> tuple:
  """Returns the push-pull throttle's bush on the panel's face: the
  collar its shaft runs through."""
  u, v = THROTTLE_AT
  axes = panelAxes(u)
  return joined([cylinderRows(panelPoint(u, v, -0.002), axes[2], 0.0095,
                              0.009, 24),
                 ringRows(panelPoint(u, v, 0.0), axes, 0.0095, 0.014,
                          0.003)])


def consoleBases() -> tuple:
  """Returns the plates under the consoles' switches."""
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
    return discRows(lampCentre(what), hoodAxes(LAMPS[what][1][0]),
                    LAMP_RADIUS, 16, None)
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
  if kind == 'shaft door':
    return shaftLeafRows(what)
  if kind == 'car':
    return plateRows(what % len(PLATE_HALVES))
  if kind == 'car glass':
    return glassRows(2 + what % 4)
  if kind == 'car seat':
    return seatRows()
  if kind == 'car button':
    return buttonRows()
  if kind == 'car guard':
    return guardRows()
  if kind == 'deck thing':
    return deckThingRows(what)
  if kind == 'door':
    return leafRows()
  if kind == 'egg ball':
    return marbleRows()
  if kind == 'door glass':
    return doorGlassRows()
  if kind == 'lift':
    return _liftRows(what)
  if kind == 'lift glass':
    (a, b), (low, high) = carWindow(what)
    half = list(carHalves()[2 + what])
    half[1 if what == 0 else 0] = 0.5 * (b - a)
    half[0 if what == 0 else 1] = 0.005
    half[2] = 0.5 * (high - low)
    middle = [0.0, 0.0, 0.5 * (low + high)]
    middle[1 if what == 0 else 0] = 0.5 * (a + b)
    return boxRows(tuple(middle), tuple(half), UNTURNED)
  if kind == 'level lamp':
    return ringLampRows()
  if kind == 'car lamp':
    return cageLampRows()
  if kind == 'bug':
    dial = BUGS[what]
    axes = dialAxes(dial)
    right, up, out = axes
    centre = dialCentre(dial)
    middle = pointAlong(pointAlong(centre, up, 0.86 * DIAL_RADIUS), out,
                        0.004)
    return boxRows(middle, (0.0024, 0.13 * DIAL_RADIUS, 0.0012), axes,
                   None, centre)
  if kind == 'check':
    return discRows(checkCentre(what), panelAxes(CHECK_AT[0]),
                    CHECK_RADIUS, 16, None)
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
    return dialCentre(BUGS[what])
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
  return 0.0, 0.0, 0.0


def _needleRows(index: int) -> tuple:
  """Returns dial 'index''s needle as a lever on its shaft (user,
  2026-11-16: "the needle should be modelled as an actually moving lever
  on a rotating actuator"), about the dial's middle, pointing up: the
  shaft's boss standing out of the face, the arm out to near the rim,
  a counterweight's tail behind, a cap on the boss."""
  axes = dialAxes(index)
  right, up, out = axes
  centre = dialCentre(index)
  boss = cylinderRows(centre, out, 0.0055, 0.009, 20)
  arm = boxRows(pointAlong(pointAlong(centre, up, 0.44 * DIAL_RADIUS), out,
                       0.0075), (0.0014, 0.44 * DIAL_RADIUS, 0.0012),
                axes)
  tail = boxRows(pointAlong(pointAlong(centre, up, -0.13 * DIAL_RADIUS), out,
                        0.0075), (0.0032, 0.13 * DIAL_RADIUS, 0.0016),
                 axes)
  cap = cylinderRows(pointAlong(centre, out, 0.009), out, 0.0035, 0.003, 16)
  return joined([boss, arm, tail, cap], centre)


def _guardRows(control: object) -> tuple:
  """Returns 'control''s guard as it rests closed over it, about its
  hinge: a flip cover hinged at its far edge, lying down over the
  input: a thin lid, its two sides and a lip at its free end (open at
  the hinge and underneath)."""
  right, up, out = control.axes
  hx, hy, hz = guardHalf(control)
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
  side and across its top (the glint's streaks slide over it); an
  enchanted key's (WARP TO ACTION's) a box a hair over its cap."""
  right, up, out = control.axes
  pivot = control.peep.pivot
  if isinstance(control.peep, Pushbutton):
    half = control.half
    return boxRows(pointAlong(pivot, out, 0.006), (half[0] + 0.0008,
                                                   half[1] + 0.0008,
                                                   0.0068),
                   control.axes, (0.0, 0.0, 1.0, 1.0), pivot)
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
    half = control.half
    cap = boxRows(tuple(p + 0.006 * n for p, n in zip(pivot, out)),
                  (half[0], half[1], 0.006), control.axes,
                  cells.get(control.name))
    return joined([cap], pivot)
  if isinstance(peep, Slider):
    #  The push-pull knob: pushed in (nought along) it sits just off the
    #  bush; its shaft runs back into the panel as far as it pulls out.
    shaft = cylinderRows(pointAlong(pivot, out, -THROTTLE_TRAVEL), out,
                         0.0045, THROTTLE_TRAVEL + 0.014, 16)
    knob = frustumRows(pointAlong(pivot, out, 0.012), out, 0.8 *
                       THROTTLE_KNOB, THROTTLE_KNOB, 0.02, 32)
    return joined([shaft, knob], pivot)
  bat = cylinderRows(pivot, out, 0.0035, BAT_LONG, 12)
  tip = cylinderRows(tuple(p + BAT_LONG * n for p, n in zip(pivot, out)),
                     out, 0.006, 0.006, 12)
  return joined([bat, tip], pivot)
