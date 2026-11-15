"""
The rear wheel hub of a front wheel driven car, as a car maker's
supplier makes it today (user, 2026-11-13: "a real cage then. With it,
build a realistic component that would go in a car between stationary
and rotating bits"): a hub bearing unit of the second generation. The
spindle (a stub axle, solid steel) stands still, bolted by its flange to
the end plate of the rear axle; the hub turns about it, the wheel's
flange on it and the brake disc one with it. Between them two rows of
steel balls, each pressing at 35 degrees, leaning apart (back to back:
their lines of pressure meet the axle far out either side), so the
wheel can neither slide along its axle nor tilt: neither row floats
(a wheel's bearing never does; the pinned and floating pair belongs to
shafts that grow with heat between two supports). The inner raceways
are on the spindle (its inner rings pressed on and clamped by its nut,
one solid with it), the outer ones in the hub. Each row's balls are
held apart by a cage: glass filled polyamide (PA66-GF), a window cage
(a rim either side of the row, a bridge between each two balls), a
body of its own, seen, the balls carrying it (it touches nothing
else). A bridge's faces lean 20 degrees off square either side of the
pitch circle, so a pocket narrows above and below a ball's middle and
holds the cage where the balls are, as a real cage's round pocket does
(square faces held it not across: it would slide out between them).

Sizes as a family hatchback's rear hub: balls 3/8 in (9.525 mm),
twelve a row on a 44.5 mm pitch circle, the rows 17 mm apart; the
spindle 30 mm across under its rings; the hub 62 mm across over its
raceways, 36.5 mm long, its flange 140 mm across, the brake disc
253 mm across and 10 mm thick on a hat 18 mm out from the flange.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._assembly import Assembly, Contact, Fixed
from ._body import Body, State
from ._gears import prismOf
from ._shape import Shape, Sphere, boxShape
from ._turned import Turned
from ._vectors import Vector, plus, rotated, turnAbout

HUB_BALL, HUB_BALLS, HUB_PITCH = 0.009525, 12, 0.0445
HUB_ANGLE, HUB_ROWS, HUB_HUG = math.radians(35.0), 0.0085, 0.52
#  The lands either side of a raceway: this share of a ball's radius off
#  the pitch circle (in on the spindle, out in the hub).
HUB_LAND = 0.45
#  Each ball's play at each raceway, m, along its line of pressure (with
#  none, 96 touches each exactly at nought clamped the hub: opposite
#  ones fought over every rounding, the hub rocking to 0.4 rad/s at
#  rest; a real unit is preloaded, which rigid touches cannot be: it is
#  overlap, and overlap is a fight).
HUB_PLAY = 0.0
#  How far each ball's middle is shaken at random, each way, as it is
#  looked for in a raceway, m ('SmallSteps.grease'; user, 2026-11-14:
#  "We *add* a bit of noise here and there to help bring stability or
#  robustness"): the touches at nought no longer fight in step, 1 s at
#  rest the hub rocks at 0.025 rad/s (was 0.063, at worst 0.07, was
#  0.37) and sinks 5 um (was 55); 0.5 um did little (0.051), 3 um more
#  rocked again (0.054), 10 um 0.19. Its cost: a micrometre a step is 8
#  mm/s of jostling, which at a walking pace (10 rad/s) drags the balls
#  4 to 7 % behind rolling and the hub 0.7 % a second (0.5 um: none);
#  at a highway's speed it is lost in the motion.
HUB_GREASE = 1e-6
#  The cage: each pocket this much wider than its ball all round, its
#  band this far either side of the pitch circle, its rims this thick,
#  its bridges' faces leaning this far off square.
CAGE_PLAY, CAGE_BAND, CAGE_RIM = 8e-5, 0.4 * 0.5 * 0.009525, 0.0015
CAGE_LEAN = math.radians(22.0)
CAGE_RIM_PARTS = 4
#  The hub's ends along the axle (inboard, outboard), from the bearing's
#  middle, and the spindle's: its flange's faces and its end.
_HUB_IN, _HUB_OUT = -0.0185, 0.018
_SPINDLE_FLANGE, _SPINDLE_BACK, _SPINDLE_END = -0.022, -0.030, 0.032


def _rows() -> tuple:
  """Returns each row: its middle along the axle and which way its outer
  contact leans along it (the outboard row's toward the middle)."""
  return (HUB_ROWS, -1.0), (-HUB_ROWS, 1.0)


def _groove(ball: tuple, way: tuple, land: float) -> tuple:
  """Returns the arc of a raceway groove: its ball's middle at 'ball'
  (rho, w), it touched along the unit 'way' from there, its centre
  set back so a ball sits 'HUB_PLAY' off that touch, cut where it meets the
  land 'land' (rho): its centre, radius, and where it meets the land,
  low and high along the axle; 'HUB_PLAY' between it and the ball."""
  r, arc = 0.5 * HUB_BALL, HUB_HUG * HUB_BALL
  set = r + HUB_PLAY - arc
  centre = (ball[0] + set * way[0], ball[1] + set * way[1])
  reach = math.sqrt(arc * arc - (land - centre[0]) ** 2)
  return centre, arc, centre[1] - reach, centre[1] + reach


def hubShape(sides: int) -> Turned:
  """The 'hubShape' function returns the hub with its brake disc: the
  outer raceways in its bore (each an arc of 0.52 of a ball across,
  touching its row's balls at 35 degrees, the outboard row's toward the
  middle), the flange out to 70 mm, the disc's hat on the flange and its
  ring out to 126.5 mm; its own z the axle, outboard along it."""
  rho, r = 0.5 * HUB_PITCH, 0.5 * HUB_BALL
  land = rho + HUB_LAND * r
  pieces = [('line', (land, _HUB_IN), (0.031, _HUB_IN)),
            ('line', (0.031, _HUB_IN), (0.031, 0.004)),
            ('line', (0.031, 0.004), (0.070, 0.004)),
            ('line', (0.070, 0.004), (0.070, 0.012)),
            ('line', (0.070, 0.012), (0.072, 0.012)),
            ('line', (0.072, 0.012), (0.072, -0.030)),
            ('line', (0.072, -0.030), (0.1265, -0.030)),
            ('line', (0.1265, -0.030), (0.1265, -0.020)),
            ('line', (0.1265, -0.020), (0.076, -0.020)),
            ('line', (0.076, -0.020), (0.076, _HUB_OUT)),
            ('line', (0.076, _HUB_OUT), (land, _HUB_OUT))]
  now = _HUB_OUT
  for middle, lean in _rows():
    way = (math.cos(HUB_ANGLE), lean * math.sin(HUB_ANGLE))
    centre, arc, low, high = _groove((rho, middle), way, land)
    pieces.append(('line', (land, now), (land, high)))
    pieces.append(('arc', centre, arc,
                   math.atan2(high - centre[1], land - centre[0]),
                   math.atan2(low - centre[1], land - centre[0])))
    now = low
  pieces.append(('line', (land, now), (land, _HUB_IN)))
  return Turned(tuple(pieces), sides)


def spindleShape(sides: int) -> Turned:
  """The 'spindleShape' function returns the spindle with its inner rings
  and nut, one solid: its flange (90 mm across, 8 mm thick) to the
  axle's end plate, the journal 30 mm across, the rings over it with
  the inner raceways (each touching its row's balls opposite the
  outer), the nut and the threaded end beyond; solid to its axis."""
  rho, r = 0.5 * HUB_PITCH, 0.5 * HUB_BALL
  land = rho - HUB_LAND * r
  pieces = [('line', (0.0, _SPINDLE_BACK), (0.045, _SPINDLE_BACK)),
            ('line', (0.045, _SPINDLE_BACK), (0.045, _SPINDLE_FLANGE)),
            ('line', (0.045, _SPINDLE_FLANGE), (0.015, _SPINDLE_FLANGE)),
            ('line', (0.015, _SPINDLE_FLANGE), (0.015, _HUB_IN)),
            ('line', (0.015, _HUB_IN), (land, _HUB_IN))]
  now = _HUB_IN
  for middle, lean in reversed(_rows()):
    way = (-math.cos(HUB_ANGLE), -lean * math.sin(HUB_ANGLE))
    centre, arc, low, high = _groove((rho, middle), way, land)
    start = math.atan2(low - centre[1], land - centre[0])
    pieces.append(('line', (land, now), (land, low)))
    pieces.append(('arc', centre, arc, start + 2.0 * math.pi
                   if start < 0.0 else start,
                   math.atan2(high - centre[1], land - centre[0])))
    now = high
  pieces += [('line', (land, now), (land, _HUB_OUT)),
             ('line', (land, _HUB_OUT), (0.016, _HUB_OUT)),
             ('line', (0.016, _HUB_OUT), (0.016, 0.026)),
             ('line', (0.016, 0.026), (0.011, 0.026)),
             ('line', (0.011, 0.026), (0.011, _SPINDLE_END)),
             ('line', (0.011, _SPINDLE_END), (0.0, _SPINDLE_END)),
             ('line', (0.0, _SPINDLE_END), (0.0, _SPINDLE_BACK))]
  return Turned(tuple(pieces), sides)


def cageShape() -> Shape:
  """The 'cageShape' function returns a row's window cage, its middle
  at its origin, its own z the axle: a pocket for each of 'HUB_BALLS'
  balls round the pitch circle from straight down ('-y'), 'CAGE_PLAY'
  wider than a ball all round; between each two pockets a bridge, two
  blocks (above and below the pitch circle, in to 'CAGE_BAND' under it
  and out until its corners, 4.5 mm aside, are 'CAGE_BAND' over it:
  out to the band straight above, they stood 0.18 mm beyond it, into
  the hub's land), its faces leaning 'CAGE_LEAN' off square so each
  pocket
  narrows away from its ball's middle, each face flat in its pocket's
  own frame (so a ball held off it by 'CAGE_PLAY' exactly; mapped round
  the circle they came 0.18 mm off, and the pocket held the cage across
  only once it had moved 0.58 mm, past the 0.24 mm to the rings: with
  this play and lean, 0.21 mm); either side of the row a rim
  'CAGE_RIM' thick, 'CAGE_RIM_PARTS' blocks between each two pockets'
  middles (one, straight across 30 degrees, sagged 0.69 mm in at its
  middle, into the spindle's land 0.24 mm off). Every block a solid of
  its own (convex), all one body."""
  rho = 0.5 * HUB_PITCH
  pocket = 0.5 * HUB_BALL + CAGE_PLAY
  step = 2.0 * math.pi / HUB_BALLS
  cos, sin = math.cos(CAGE_LEAN), math.sin(CAGE_LEAN)

  def wall(angle: float, side: float, up: float) -> tuple:
    """Returns the point of the wall of the pocket at 'angle' on its
    'side' (1: toward greater angles), 'up' out from the pitch circle,
    in x and y."""
    t = side * (pocket - abs(up) * sin) / cos
    along = (-math.sin(angle), math.cos(angle))
    out = (math.cos(angle), math.sin(angle))
    return (rho * out[0] + t * along[0] + up * out[0],
            rho * out[1] + t * along[1] + up * out[1])

  low, high = 0.0, CAGE_BAND
  for _ in range(60):
    middle = 0.5 * (low + high)
    if math.hypot(*wall(0.0, 1.0, middle)) > rho + CAGE_BAND:
      high = middle
    else:
      low = middle
  top = low
  shape = None
  for k in range(HUB_BALLS):
    start = -0.5 * math.pi + k * step
    after = start + step
    for low, high in ((0.0, top), (-CAGE_BAND, 0.0)):
      outline = (wall(start, 1.0, high), wall(after, -1.0, high),
                 wall(after, -1.0, low), wall(start, 1.0, low))
      piece = prismOf(outline, -pocket, pocket)
      shape = piece if shape is None else shape.joined(piece)
    inner, outer = rho - CAGE_BAND, rho + CAGE_BAND
    for part in range(CAGE_RIM_PARTS):
      a0 = start + step * part / CAGE_RIM_PARTS
      a1 = start + step * (part + 1) / CAGE_RIM_PARTS
      rim = ((inner * math.cos(a0), inner * math.sin(a0)),
             (outer * math.cos(a0), outer * math.sin(a0)),
             (outer * math.cos(a1), outer * math.sin(a1)),
             (inner * math.cos(a1), inner * math.sin(a1)))
      shape = shape.joined(prismOf(rim, pocket, pocket + CAGE_RIM))
      shape = shape.joined(prismOf(rim, -pocket - CAGE_RIM, -pocket))
  return shape


HUB = Body.of(hubShape(96), 7300.0)
SPINDLE = Body.of(spindleShape(72), 7850.0)
CAGE = Body.of(cageShape(), 1350.0)
HUB_BALL_BODY = Body.of(Sphere(0.5 * HUB_BALL), 7850.0)
#  The end of the rear axle (a torsion beam's trailing arm) the spindle
#  is bolted to: a steel plate 120 x 80 mm, 15 mm thick, behind its
#  flange.
AXLE_PLATE = Body.of(boxShape(0.12, 0.08, 0.015), 7850.0)
#  Where the hub stands in the void, its axle along y (outboard toward
#  -y), and the platform under it, its top 'HUB_HIGH' under the axle
#  (the disc's bottom 73.5 mm over it: a walker 32 mm tall walks under
#  it).
HUB_MIDDLE = (0.0, 0.0, 0.2)
HUB_UPRIGHT = turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi)
HUB_HIGH = 0.2
HUB_PLATFORM = Body.of(boxShape(0.4, 0.5, 0.01), 2700.0)
FIRST_HUB_BALL = 7
#  Ball on cage, and cage on ring: PA66 on greased steel, lightly
#  gripping (a law as the springs' world takes one; the small steps take
#  only its grip); the cage's skin looked at every 3 mm.
_BALL_ON_CAGE = (3e3, 1.0, 0.05, 3e3, 1.0)
_CAGE_ON_RING = (3e3, 1.0, 0.05, 3e3, 1.0, 0.003)


def rearHub(scale: float) -> tuple[Assembly, tuple[State, ...]]:
  """The 'rearHub' function returns the walker shrunk to 'scale' first,
  standing on the platform under the hub; the axle's end plate, the
  spindle (both part of the world) and the hub (free, on its balls),
  the outboard row's cage and the inboard row's, the platform (part of
  the world); then, from 'FIRST_HUB_BALL', the outboard row's balls,
  then the inboard row's, each in its pocket, round the pitch circle
  from straight down; all still. Every ball touches the spindle, the
  hub and its row's cage; each cage the spindle and the hub (it rests
  and rubs on their lands when the balls let it sag so far, a ring
  guided cage); the walker every body. In the void: step it with no
  ground, in small steps ('SmallSteps': the springs' world meets a
  turned solid with balls only)."""
  from ._scenes import _STEEL_ON_STEEL, _WALKER_ON_STEEL, WALKER
  from ._scenes import froudeOf
  walker = WALKER.scaled(scale)
  body = walker.body()
  rho = 0.5 * HUB_PITCH

  def placed(item: Body, along: float, turn: tuple = None) -> State:
    """Returns 'item' still, its own frame's origin 'along' the axle
    from the bearing's middle."""
    own = HUB_UPRIGHT if turn is None else turn
    origin = plus(HUB_MIDDLE, rotated(HUB_UPRIGHT, (0.0, 0.0, along)))
    return State(plus(origin, rotated(own, item.centre)), own)

  under = HUB_MIDDLE[2] - HUB_HIGH
  states = [State((0.0, 0.1, under + walker.radius)),
            placed(AXLE_PLATE, _SPINDLE_BACK - 0.0075),
            placed(SPINDLE, 0.0), placed(HUB, 0.0),
            placed(CAGE, HUB_ROWS), placed(CAGE, -HUB_ROWS),
            State((0.0, 0.0, under - 0.005))]
  bodies = [body, AXLE_PLATE, SPINDLE, HUB, CAGE, CAGE, HUB_PLATFORM]
  for middle, _ in _rows():
    for k in range(HUB_BALLS):
      angle = -0.5 * math.pi + 2.0 * math.pi * k / HUB_BALLS
      own = (rho * math.cos(angle), rho * math.sin(angle), middle)
      states.append(State(plus(HUB_MIDDLE, rotated(HUB_UPRIGHT, own))))
      bodies.append(HUB_BALL_BODY)
  walking = froudeOf(_WALKER_ON_STEEL, scale)
  contacts = [Contact(0, other, *walking)
              for other in range(1, len(bodies))]
  for row, cage in enumerate((4, 5)):
    for k in range(HUB_BALLS):
      ball = FIRST_HUB_BALL + row * HUB_BALLS + k
      contacts += [Contact(2, ball, *_STEEL_ON_STEEL),
                   Contact(3, ball, *_STEEL_ON_STEEL),
                   Contact(cage, ball, *_BALL_ON_CAGE)]
    contacts += [Contact(2, cage, *_CAGE_ON_RING),
                 Contact(3, cage, *_CAGE_ON_RING)]
  links = (Fixed(1), Fixed(2), Fixed(6))
  return Assembly(tuple(bodies), links + tuple(contacts)), tuple(states)


#  How the unit is drawn (user, 2026-11-13: "make the gearhub in the
#  void have more realistically colored textures, and just leave a small
#  bit of transparent glass where the balls are visible"): the hub's
#  raceway ring (all of it within the barrel's radius, 31 mm: its bore,
#  inboard face, barrel and that band of the wheel's face) is glass, a
#  machined steel wall facing into it where the flange stands on it;
#  the disc's braking faces from 80 mm out.
FINISH_GLASS = 0.031
_BRAKING = 0.080


def _cutLine(piece: tuple, rho: float) -> tuple:
  """Returns the line 'piece' cut where it crosses 'rho': the part
  walked first and the rest."""
  (r0, w0), (r1, w1) = piece[1], piece[2]
  middle = (rho, w0 + (rho - r0) / (r1 - r0) * (w1 - w0))
  return ('line', (r0, w0), middle), ('line', middle, (r1, w1))


def hubRuns() -> tuple:
  """The 'hubRuns' function returns the hub's surfaces as drawn, runs of
  its profile walked as it is, each with its finish's key: glass (the
  raceway ring, within 'FINISH_GLASS'), the machined wall where the
  flange stands on it (facing into the glass), forged steel (the
  flange's back and rim), the disc's hat ('hat', painted), its braking
  faces ('braking', bare cast iron from '_BRAKING' out) and rim
  ('edge'), and the wheel's face ('machined')."""
  profile = HUB.shape.profile
  inboard, barrel, back, rim, step, hatIn, discIn = profile[:7]
  edge, discOut, hatOut, face = profile[7:11]
  hatRing, brakeIn = _cutLine(discIn, _BRAKING)
  brakeOut, hatRim = _cutLine(discOut, _BRAKING)
  steelFace, glassFace = _cutLine(face, FINISH_GLASS)
  wall = ('line', (FINISH_GLASS, face[1][1]), (FINISH_GLASS, back[1][1]))
  return (('glass', (glassFace,) + tuple(profile[11:]) + (inboard,
                                                          barrel)),
          ('forged', (back, rim, step)), ('hat', (hatIn, hatRing)),
          ('braking', (brakeIn,)), ('edge', (edge,)),
          ('braking', (brakeOut,)), ('hat', (hatRim, hatOut)),
          ('machined', (steelFace, wall)))


def spindleRuns() -> tuple:
  """The 'spindleRuns' function returns the spindle's surfaces as drawn,
  as 'hubRuns' the hub's: its flange forged, the journal machined, the
  inner rings ground and polished ('race'), the nut zinc plated, the
  threaded end dark ('thread'); its axis (no surface) left out."""
  profile = SPINDLE.shape.profile
  return (('forged', tuple(profile[:3])), ('machined', (profile[3],)),
          ('race', tuple(profile[4:11])), ('nut', tuple(profile[11:13])),
          ('thread', tuple(profile[13:15])))


def hubFinishes() -> dict:
  """The 'hubFinishes' function returns how 'rearHub''s bodies are drawn,
  by index: the hub and the spindle in runs ('hubRuns', 'spindleRuns'),
  the others each whole in one finish: the axle's plate painted
  ('axle'), the cages ('cage'), the platform ('platform'), the balls
  ('ball'); the walker not at all."""
  out = {1: 'axle', 2: spindleRuns(), 3: hubRuns(), 4: 'cage', 5: 'cage',
         6: 'platform'}
  for k in range(2 * HUB_BALLS):
    out[FIRST_HUB_BALL + k] = 'ball'
  return out


def hubOrbitShare() -> float:
  """The 'hubOrbitShare' function returns how fast the balls (and their
  cages) go round for the hub's turning, the spindle still: rolling on
  both raceways at the contact angle, (1 + d cos a / D) / 2."""
  return 0.5 * (1.0 + HUB_BALL * math.cos(HUB_ANGLE) / HUB_PITCH)


def hubAxis() -> Vector:
  """The 'hubAxis' function returns the hub's axle in the world,
  outboard."""
  return rotated(HUB_UPRIGHT, (0.0, 0.0, 1.0))
