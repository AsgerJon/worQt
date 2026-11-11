//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen
//
//  The three-cushion table in 3D, in mm, y up: the cloth's middle at
//  the origin, its top at nought, x across, z along with the head end
//  away (negative). After the tables of Søren Søgaard, but in ebony, as
//  the user would have it: cyan-blue cloth, sloped cushions mitred in
//  the corners, lacquered ebony rails rounded outside, square corner
//  blocks, an ebony body with light corners and inlays on two tapered
//  pedestals. The balls are Super Aramith Pro-Cup's, six dots each.
//  'TableView' sets the sizes, the pieces' shapes, the balls' places and
//  turns, the diamonds and the room's light; drag to turn round the
//  table, wheel to come nearer, tap a ball to look from it.
//
//  A corner shows the table from straight above, the camera a dot on
//  it, crosshairs under what it looks from, each ball ringed in its
//  colour, the diamonds large, the last shot's ways till the next is
//  aimed; a right click on it asks for its menu ('minimapMenuAsked');
//  'overhead' shows the view from above filling the window instead, the
//  corner hidden. The diamonds shine in the rails; over the
//  rails the camera sees from the table's side, whose diamonds it sees
//  edge on, ghosts of them stand facing it. The aim line grows longer and
//  warmer with 'aimSpeed'. A ghost ball, 'mark', shows where the cue ball
//  must be to send another along a line. 'cameraView' is how much the
//  camera takes in, top to bottom. 'turnBy' turns the camera round what
//  it looks at by so many degrees.
//
//  Looking from the ghost, 'ghostLook', the camera stands at the ghost
//  and faces the way the cue ball, coming from 'ghostFrom', leaves the
//  ball 'ghostOf' after the hit: square to the line of their middles,
//  without spin. Turning the view chooses that way, and the ghost moves
//  round the ball to the hit that gives it.
//
//  While a shot is shown, the cushions the cue ball has met, and the
//  balls, show over the view, 'counterText', while 'counterShown'.
//
//  Wherever the view from above is shown, the last shot is drawn on the
//  cloth as a broadcast draws it: each ball's way in its colour, ball
//  1's boldest, faint balls where those that moved set off, and, if
//  wanted, a gloved hand with the cue behind ball 1.

import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

Item {
  id: root

  property real tableLength: 2840
  property real tableWidth: 1420
  property real ballRadius: 30.75
  //  The dots black and clear (the user); a dot's radius, mm.
  property real dotRadius: 3.75
  property color dotBlack: "#0e0e0e"
  //  Keglebillard's marked white: white, its black dots its mark (the
  //  user); its trail and halo a pale grey to tell it from the white.
  readonly property color markedTint: kegler ? "#cfcfcf" : "#f5b21b"
  property real noseHeight: 37
  property real cushionDepth: 50
  property real cushionTop: 45
  property real railWidth: 130
  property real railBottom: -55
  property real apronBottom: -330
  property real apronInset: 8
  property real bedHeight: 800
  property real lampHeight: 1000
  property real pedestalPlace: 950
  property vector3d whitePlace: Qt.vector3d(182.5, 30.75, -710)
  property vector3d yellowPlace: Qt.vector3d(0, 30.75, -710)
  property vector3d redPlace: Qt.vector3d(0, 30.75, 710)
  property quaternion whiteTurn: Qt.quaternion(1, 0, 0, 0)
  property quaternion yellowTurn: Qt.quaternion(1, 0, 0, 0)
  property quaternion redTurn: Qt.quaternion(1, 0, 0, 0)
  property var diamondPlaces: []
  property var shapes: ({})
  property url roomLight
  property color clothBounce: kegler ? "#3fd2dc" : "#3fb4ea"
  //  Keglebillard, the second game: the cloth more cyan, the six holes
  //  milled in, 'holeRadius' each, at 'holePlaces', the pins, pale wood,
  //  three dark grooves round each one's waist, 'pinGrooves' ('y' up, 'r'
  //  round), its outline 'shapes.pin': each pin by its number, its foot
  //  at 'pinPlaces', turned 'pinTurns', on the table if 'pinShown'.
  property bool kegler: false
  property var pinPlaces: []
  property var pinTurns: []
  property var pinShown: []
  property var holePlaces: []
  property real holeRadius: 40
  property var pinGrooves: []
  property vector3d cameraTurn: Qt.vector3d(-16, 180, 0)
  property real cameraDistance: 1900
  property real cameraView: 36
  property real aimSpeed: 2000
  property vector3d cameraFocus: Qt.vector3d(182.5, 30.75, -710)
  property bool aiming: false
  property bool moving: false
  //  The room (the user: the game opens walking it): its sizes and where
  //  each table stands, as 'Room.layout' gives them; the table played at
  //  stays where the scene has it, the room shifted round it. While
  //  'walking' the walker's camera shows it, 'nearTable' the game whose
  //  table it stands near, empty for none; 'pinSpots', the pins standing
  //  on the other table. 'liveBoard' and 'idleBoard' are what the club
  //  boards over the table played at and over the other show.
  property var roomPlan: ({
    halfWidth: 5200, halfLength: 4600, floor: 800, tableHalfWidth: 890,
    tableHalfLength: 1600, keep: 280, near: 650, eye: 1650,
    door: [0, 3600], tables: { carom: -2300, kegler: 2300 }
  })
  property bool walking: false
  //  While 'looking' the mouse turns the walker's head, the pointer
  //  hidden (the user); 'lookBy' takes its moves. E opens the inventory,
  //  'inventoryOpen', its 'inventory' a list of items, each its 'name'
  //  and 'label'; 'held' the one in hand, 'itemChosen' when a slot is
  //  clicked.
  property bool looking: false
  property bool inventoryOpen: false
  property var inventory: []
  property string held: "cue"
  readonly property real lookSpeed: 0.15
  readonly property vector3d walkerTurn: walker.eulerRotation
  signal itemChosen(string name)
  property string nearTable: ""
  property var pinSpots: []
  property var liveBoard: ({})
  property var idleBoard: ({})
  readonly property real boardHeight: 950
  readonly property real activeX: roomPlan.tables[kegler ? "kegler" : "carom"]
  readonly property real otherX: roomPlan.tables[kegler ? "carom" : "kegler"]
  readonly property vector3d roomShift: Qt.vector3d(-activeX, 0, 0)
  //  The view's bob as the walker walks: 'stride' mm walked so far, a
  //  dip twice a stride, a sway once, eased in and out.
  property real stride: 0
  property bool strolling: false
  property real bobWeight: 0
  property var lastWalk: Qt.vector2d(0, 0)
  readonly property real bobPhase: 2 * Math.PI * stride / 1400
  readonly property real bobUp: -bobWeight * 22 * (1 - Math.cos(2 * bobPhase))
                                / 2
  readonly property real bobAside: bobWeight * 14 * Math.sin(bobPhase)
  onStrollingChanged: bobWeight = strolling ? 1 : 0
  Behavior on bobWeight { NumberAnimation { duration: 260 } }
  Timer {
    id: stillTimer
    interval: 120
    onTriggered: root.strolling = false
  }
  property bool overhead: false
  property vector3d markPlace: Qt.vector3d(0, 30.75, 0)
  property bool markShown: false
  property color markColor: "#f2ecd9"
  property bool ghostLook: false
  property string counterText: ""
  property bool counterShown: false
  //  The speedometer over the ball while a stroke is made (the user):
  //  'gaugeSpeed', m/s, how fast the cue ball would go were the stroke,
  //  a spring, let go now, of 'gaugeMost'.
  property bool gaugeShown: false
  //  How many times a shot asked for too soon was refused, a barrier
  //  flashed over the ball ('flashBarrier').
  property int barrierCount: 0
  property real gaugeSpeed: 0
  property real gaugeMost: 10
  onGaugeSpeedChanged: speedometer.shown()
  onGaugeShownChanged: speedometer.shown()
  property vector3d ghostOf: Qt.vector3d(0, 30.75, 0)
  property vector3d ghostFrom: Qt.vector3d(0, 30.75, 0)
  //  The last shot, seen from above: each ball's way, 'trailShapes' by
  //  the ball's name, a ribbon in its colour, drawn only for the balls in
  //  'trailNames', those with a way in the shot shown (a ribbon handed
  //  no triangles may keep showing its last ones), those in 'boldTrails'
  //  the boldest; 'trailStarts', faint balls where the balls that moved set
  //  off, each its 'x', 'z' and 'color'; and, while 'handShown', a gloved
  //  hand, 'handPicture', and the cue in it, 'cuePicture', each
  //  'handLength' by 'handWidth' mm, behind each ball struck, each of
  //  'hands' its 'x', 'z' and the 'angle' it went, in degrees about y;
  //  the cue slid 'cueBack' mm back through the bridge, below nought on
  //  past where the ball was.
  property bool trailsShown: false
  property var trailShapes: ({})
  property var trailNames: []
  property var boldTrails: []
  property var trailStarts: []
  property var hands: []
  property bool handShown: true
  //  The shadow both eyes see of the ball aimed from (the user), shown
  //  with the aim while 'shadowShown'. While 'trenchesShown' it is the
  //  trenches instead (the user): ball 1's way along the aim and, if it
  //  meets a ball, that ball's and ball 1's on from the hit,
  //  'trenchShapes' 'trench0' to 'trench2', one for each of
  //  'trenchNames', in its ball's tint, each a ball wide, ending round
  //  where the ball touches a cushion or a ball or stops.
  property bool shadowShown: true
  property bool trenchesShown: false
  property var trenchNames: []
  //  Each ball's trench, its tint and how clear, on the cloth (the user:
  //  white too faint at 0.3 and still at 0.55, red too dark at 0.3, right
  //  lightened at 0.4): white nearly solid, red lightened, its own red.
  readonly property var trenchTints: ({
    "white": "#ffffff", "yellow": root.markedTint, "red": "#ff5c5c"
  })
  readonly property var trenchOpacities: ({
    "white": 0.85, "yellow": 0.7, "red": 0.4
  })
  property var trenchShapes: ({})
  //  Where ball 1 meets ball 2 as aimed, a clear copy of it there (the
  //  user), 'impactColor', while 'impactShown' with the trenches.
  property vector3d impactPlace: Qt.vector3d(0, 30.75, 0)
  property bool impactShown: false
  property color impactColor: "#f2ecd9"
  //  The cue, while a stroke is made: its tip at 'stickPlace', laid as
  //  'stickTurn' turns its length, up y, from the tip.
  property bool stickShown: false
  property vector3d stickPlace: Qt.vector3d(0, 0, 0)
  property quaternion stickTurn: Qt.quaternion(1, 0, 0, 0)
  property url handPicture
  property url cuePicture
  property real cueBack: 0
  property real handLength: 700
  property real handWidth: 240
  property var ballTints: ({
    "white": "#f2ecd9", "yellow": root.markedTint, "red": "#e0262d"
  })
  readonly property vector3d cameraForward: camera.forward
  readonly property real overheadHeight: 12000
  readonly property vector3d overheadRight: overheadCamera.right
  readonly property vector3d overheadUp: overheadCamera.up
  readonly property vector3d overheadForward: overheadCamera.forward
  readonly property real overheadView: overheadCamera.fieldOfView
  //  Whether the corner shows: only while the camera's view fills the
  //  window, never with the view from above; and where the camera is.
  readonly property bool cornerShown: corner.visible
  readonly property vector3d cameraPlace: camera.scenePosition
  //  How the camera is turned now; the ghost's place, for the cue ball to
  //  leave its ball the way the camera faces; what the camera turns round,
  //  and the aim starts from.
  readonly property vector3d cameraTurnNow: origin.eulerRotation
  readonly property real cameraDistanceNow: camera.z
  //  While 'cameraGliding', the camera's turn, distance and field of view
  //  glide to what they are set to ('glideCamera'), as its focus does.
  property bool cameraGliding: false
  function glideCamera(focus, turn, distance, view) {
    cameraGliding = true
    cameraFocus = focus
    origin.eulerRotation = turn
    camera.z = distance
    cameraView = view
    glideEnd.restart()
  }
  Timer {
    id: glideEnd
    interval: 700
    onTriggered: root.cameraGliding = false
  }
  readonly property real cameraYaw: origin.eulerRotation.y * Math.PI / 180
  readonly property vector3d ghostPlace: ghostFor(cameraYaw)
  readonly property vector3d aimFrom: ghostLook ? ghostPlace : cameraFocus

  //  Where the cue ball, coming from 'ghostFrom', must meet the ball at
  //  'ghostOf' to leave it facing 'yaw' along the cloth. It leaves square
  //  to the line from it to the ball, so that line is square to the way:
  //  of the two places two radii off either side, the one the cue ball
  //  comes at from behind, its path bending forward onto the way, or the
  //  nearer to that where neither does.
  function ghostFor(yaw) {
    const tx = -Math.sin(yaw)
    const tz = -Math.cos(yaw)
    const reach = 2 * ballRadius
    let best = ghostOf
    let bestScore = -Infinity
    for (const side of [1, -1]) {
      const nx = -tz * side
      const nz = tx * side
      const gx = ghostOf.x - reach * nx
      const gz = ghostOf.z - reach * nz
      const dx = gx - ghostFrom.x
      const dz = gz - ghostFrom.z
      const length = Math.max(Math.hypot(dx, dz), 1e-9)
      const score = Math.min(dx * nx + dz * nz, dx * tx + dz * tz) / length
      if (score > bestScore) {
        bestScore = score
        best = Qt.vector3d(gx, ballRadius, gz)
      }
    }
    return best
  }

  //  Turns the camera round what it looks at, 'yaw' degrees to the left,
  //  'pitch' up, kept above the cloth and short of straight down.
  //  The camera looks down on the ball at least 'lowestPitch' degrees
  //  (the user): any lower, the cue, held up but a few degrees, lies
  //  along the sight and hides the ball.
  property real lowestPitch: 10
  //  A shot asked for before every ball rests is refused (the user): a
  //  barrier over the ball aimed from, flashed and fading.
  //  Where 'x', 'z' in the room is moved the least way out of the walls
  //  and the tables, 'keep' clear of each ('Room.kept', the same sums).
  function keptInRoom(x, z) {
    const r = roomPlan
    x = Math.min(Math.max(x, -r.halfWidth + r.keep), r.halfWidth - r.keep)
    z = Math.min(Math.max(z, -r.halfLength + r.keep), r.halfLength - r.keep)
    for (const kind in r.tables) {
      const tx = r.tables[kind]
      const reachX = r.tableHalfWidth + r.keep
      const reachZ = r.tableHalfLength + r.keep
      const inX = reachX - Math.abs(x - tx)
      const inZ = reachZ - Math.abs(z)
      if (inX <= 0 || inZ <= 0)
        continue
      if (inX < inZ)
        x = tx + (x - tx >= 0 ? reachX : -reachX)
      else
        z = z >= 0 ? reachZ : -reachZ
    }
    return Qt.vector2d(x, z)
  }
  //  The game whose table 'x', 'z' is near ('Room.nearOf').
  function nearOf(x, z) {
    let best = "", gap = Infinity
    for (const kind in roomPlan.tables) {
      const dx = Math.max(Math.abs(x - roomPlan.tables[kind])
                          - roomPlan.tableHalfWidth, 0)
      const dz = Math.max(Math.abs(z) - roomPlan.tableHalfLength, 0)
      const g = Math.sqrt(dx * dx + dz * dz)
      if (g < gap) {
        gap = g
        best = kind
      }
    }
    return gap <= roomPlan.near ? best : ""
  }
  //  The walker moved: kept on the floor and out of walls and tables, its
  //  stride counted for the bob, the table near it told.
  function walkerMoved() {
    const p = walker.position
    const kept = keptInRoom(p.x, p.z)
    const eye = roomPlan.eye - roomPlan.floor
    if (Math.abs(kept.x - p.x) > 1e-6 || Math.abs(kept.y - p.z) > 1e-6
        || Math.abs(p.y - eye) > 1e-6) {
      walker.position = Qt.vector3d(kept.x, eye, kept.y)
      return
    }
    const dx = p.x - lastWalk.x, dz = p.z - lastWalk.y
    const step = Math.sqrt(dx * dx + dz * dz)
    lastWalk = Qt.vector2d(p.x, p.z)
    if (step > 0 && step < 500) {
      stride += step
      strolling = true
      stillTimer.restart()
    }
    nearTable = nearOf(p.x, p.z)
  }
  //  Stands the walker at 'x', 'z' in the room, turned 'yaw' about the
  //  vertical and 'pitch' up, in degrees.
  function walkTo(x, z, yaw, pitch) {
    lastWalk = Qt.vector2d(x, z)
    walker.eulerRotation = Qt.vector3d(pitch, yaw, 0)
    walker.position = Qt.vector3d(x, roomPlan.eye - roomPlan.floor, z)
    nearTable = nearOf(x, z)
  }
  //  Turns the walker's head as the mouse moved 'dx' pixels right and
  //  'dy' down: right turns it right, down looks down.
  function lookBy(dx, dy) {
    const r = walker.eulerRotation
    walker.eulerRotation = Qt.vector3d(r.x - dy * lookSpeed,
                                       r.y - dx * lookSpeed, 0)
  }
  //  Walks the room, or plays at the table: the keys go to the walker.
  function setWalking(on) {
    walking = on
    if (on)
      wasd.forceActiveFocus()
  }
  function flashBarrier() {
    barrierCount += 1
    barrier.place()
    barrierFlash.restart()
  }

  function turnBy(yaw, pitch) {
    const now = origin.eulerRotation
    origin.eulerRotation = Qt.vector3d(
      Math.max(-89, Math.min(-root.lowestPitch, now.x + pitch)),
      now.y + yaw, now.z)
  }
  onCameraTurnChanged: origin.eulerRotation = cameraTurn

  //  While 'moving', a drag on the cloth moves balls instead of the
  //  camera: where it is pressed, dragged to and let go, in the scene.
  signal clothPressed(real x, real z)
  signal clothDragged(real x, real z)
  signal clothReleased()
  //  A tap on the table, where in the scene.
  signal tableTapped(real x, real z)
  //  The stroke (the user): the right button pressed, the mouse pulled
  //  back and pushed through, where on the view, in pixels.
  signal strokePressed(real x, real y)
  signal strokeMoved(real x, real y)
  signal strokeReleased()
  //  A left press on the view, a drag to turn the camera: the next shot
  //  begins to be aimed; a right click on the corner asks for its menu,
  //  where on the view (the user).
  signal aimTouched()
  signal minimapMenuAsked(real x, real y)
  //  Whether 'at' on 'item' lies on the corner, while it shows.
  function inCorner(item, at) {
    if (!corner.visible)
      return false
    const p = corner.mapFromItem(item, at.x, at.y)
    return p.x >= 0 && p.y >= 0 && p.x <= corner.width
        && p.y <= corner.height
  }

  readonly property real halfWidth: 0.5 * tableWidth
  readonly property real halfLength: 0.5 * tableLength
  readonly property real outer: cushionDepth + railWidth
  readonly property real apronX: halfWidth + outer - apronInset
  readonly property real apronZ: halfLength + outer - apronInset
  readonly property real ballScale: ballRadius / 50
  //  How much of the room the view from above takes in, along the table
  //  and across it, and the view it is shown in now.
  readonly property real spanAlong: tableLength + 2 * outer + 240
  readonly property real spanAcross: tableWidth + 2 * outer + 240
  readonly property Item overheadDisplay: overhead ? view : inset
  readonly property real overheadReach: Math.max(
    0.5 * spanAcross,
    0.5 * spanAlong * overheadDisplay.height
      / Math.max(overheadDisplay.width, 1))
  //  How many mm on the cloth a pixel of the view from above takes in;
  //  'overheadRescaled' tells when it changes. The hand is drawn as
  //  large as it is, but never shorter than 120 pixels.
  readonly property real overheadScale: 2 * overheadReach
    / Math.max(overheadDisplay.height, 1)
  readonly property real handScale: Math.max(
    1, 120 * overheadScale / handLength)
  //  How high the hand and the cue lie: over the balls, and so over the
  //  cushions and rails, where a bridge on the rail rests; from straight
  //  above, the height hardly shows.
  readonly property real handLift: 2 * ballRadius + 2
  signal overheadRescaled()
  onOverheadScaleChanged: overheadRescaled()

  //  A colour as the shaders want it: linear, not sRGB.
  function channel(value) {
    return value <= 0.04045 ? value / 12.92
                            : Math.pow((value + 0.055) / 1.055, 2.4)
  }
  function linear(colour) {
    return Qt.vector3d(channel(colour.r), channel(colour.g),
                       channel(colour.b))
  }

  //  Where on the cloth, in the scene, the point 'x', 'y' of 'item' is,
  //  'item' showing the view from above, straight down: its middle right
  //  under the camera, so far out per pixel as the camera's reach says.
  function overheadPlace(item, x, y) {
    const half = Math.tan(overheadCamera.fieldOfView * Math.PI / 360)
    const scale = root.overheadHeight * half / (0.5 * item.height)
    const across = (x - 0.5 * item.width) * scale
    const up = (0.5 * item.height - y) * scale
    const r = overheadCamera.right
    const u = overheadCamera.up
    return Qt.vector2d(r.x * across + u.x * up, r.z * across + u.z * up)
  }

  component Box: Model {
    property vector3d low
    property vector3d high
    source: "#Cube"
    position: low.plus(high).times(0.5)
    scale: high.minus(low).times(0.01)
  }

  //  A piece of the table made in Python, turned about y so its own x,
  //  out from the cloth, points the way it should.
  component Piece: Model {
    property real turn: 0
    eulerRotation: Qt.vector3d(0, turn, 0)
  }

  //  Lacquered ebony, near black, its faint brown streaks along the
  //  piece; 'grainShift' moves where in the log the piece was cut. Laid
  //  out for keglebillard, oak instead (the user): golden brown, its
  //  darker grain along the piece.
  component Ebony: CustomMaterial {
    id: ebony
    property vector3d grainShift
    property bool oak: root.kegler
    property color lightTone: ebony.oak ? "#b8844f" : "#2a1d14"
    property color darkTone: ebony.oak ? "#6b4526" : "#060404"
    property vector3d woodLight: root.linear(ebony.lightTone)
    property vector3d woodDark: root.linear(ebony.darkTone)
    shadingMode: CustomMaterial.Shaded
    vertexShader: "wood.vert"
    fragmentShader: "wood.frag"
  }

  //  A diamond lying in a rail's top, turned across its rail: its short
  //  dimension along the cushion (the user).
  component Diamond: Model {
    geometry: root.shapes.diamond || null
  }

  //  A ring of colour round a ball, under it, seen from above.
  component Halo: Model {
    property color tint
    source: "#Sphere"
    scale: Qt.vector3d(2.6 * root.ballScale, 0.05, 2.6 * root.ballScale)
    materials: PrincipledMaterial {
      baseColor: tint
      lighting: PrincipledMaterial.NoLighting
      opacity: 0.45
      alphaMode: PrincipledMaterial.Blend
    }
  }

  //  The last shot as seen from above: each ball's way on the cloth,
  //  ball 1's boldest; faint balls where those that moved set off; and
  //  the hand behind each ball struck, its cue's tip at the ball, the
  //  way it went. Under the balls, above the cloth.
  component ShotTrails: Node {
    Repeater3D {
      model: ["white", "yellow", "red"]
      delegate: Model {
        readonly property bool bold: root.boldTrails.indexOf(modelData) >= 0
        visible: root.trailNames.indexOf(modelData) >= 0
        geometry: root.trailShapes[modelData] || null
        materials: PrincipledMaterial {
          baseColor: root.ballTints[modelData]
          lighting: PrincipledMaterial.NoLighting
          opacity: bold ? 0.85 : 0.65
          alphaMode: PrincipledMaterial.Blend
          cullMode: Material.NoCulling
        }
      }
    }
    Repeater3D {
      model: root.trailStarts
      delegate: Model {
        source: "#Sphere"
        position: Qt.vector3d(modelData.x, root.ballRadius, modelData.z)
        scale: Qt.vector3d(root.ballScale, root.ballScale, root.ballScale)
        materials: PrincipledMaterial {
          baseColor: modelData.color
          metalness: 0
          roughness: 0.3
          opacity: 0.32
          alphaMode: PrincipledMaterial.Blend
        }
      }
    }
    Repeater3D {
      model: root.handShown ? root.hands : []
      delegate: Node {
        readonly property real length: root.handLength * root.handScale
        position: Qt.vector3d(modelData.x, root.handLift, modelData.z)
        eulerRotation.y: modelData.angle
        Model {
          source: "#Rectangle"
          x: -(root.ballRadius + 2 + 0.5 * parent.length)
          eulerRotation.x: -90
          scale: Qt.vector3d(parent.length / 100,
                             root.handWidth * root.handScale / 100, 1)
          materials: PrincipledMaterial {
            baseColorMap: Texture {
              source: root.handPicture
              generateMipmaps: true
              mipFilter: Texture.Linear
            }
            lighting: PrincipledMaterial.NoLighting
            alphaMode: PrincipledMaterial.Blend
            cullMode: Material.NoCulling
          }
        }
        //  The cue, in the bridge: drawn over the hand however it
        //  slides, sorted as nearer the camera than it.
        Model {
          source: "#Rectangle"
          x: -(root.ballRadius + 2 + root.cueBack * root.handScale
               + 0.5 * parent.length)
          depthBias: -1000
          eulerRotation.x: -90
          scale: Qt.vector3d(parent.length / 100,
                             root.handWidth * root.handScale / 100, 1)
          materials: PrincipledMaterial {
            baseColorMap: Texture {
              source: root.cuePicture
              generateMipmaps: true
              mipFilter: Texture.Linear
            }
            lighting: PrincipledMaterial.NoLighting
            alphaMode: PrincipledMaterial.Blend
            cullMode: Material.NoCulling
          }
        }
      }
    }
  }

  component Ball: Model {
    id: ball
    property color body
    property color spot
    source: "#Sphere"
    pickable: true
    scale: Qt.vector3d(root.ballScale, root.ballScale, root.ballScale)
    materials: CustomMaterial {
      shadingMode: CustomMaterial.Shaded
      vertexShader: "ball.vert"
      fragmentShader: "ball.frag"
      property vector3d bodyColor: root.linear(ball.body)
      property vector3d dotColor: root.linear(ball.spot)
      property real dotSize: root.dotRadius / root.ballRadius
      property vector3d bounceColor: root.linear(root.clothBounce)
      property real bounceStrength: 0.45
    }
  }

  //  A table's body (the user: two tables, a room to walk): the bed, the
  //  holes and pins for keglebillard, the cushions, rails, corners and
  //  body, the pedestals and the diamonds; 'kegle' for keglebillard's,
  //  its pins at 'pins', turned 'turns', shown where 'shown'; its bed
  //  'pickableBed' for taps and drags where the game is played.
  component TableBody: Node {
    id: body
    property bool kegle: false
    property bool pickableBed: false
    property var pins: []
    property var turns: []
    property var shown: []
    PrincipledMaterial {
      id: bodyCloth
      baseColor: body.kegle ? "#12b3bf" : "#1593d2"
      metalness: 0
      roughness: 0.95
      specularAmount: 0.1
    }
    PrincipledMaterial {
      id: bodyBeige
      baseColor: "#dcc9a3"
      metalness: 0
      roughness: 0.5
      clearcoatAmount: 0.6
      clearcoatRoughnessAmount: 0.2
    }
      //  The bed: the cloth over the slate, under the cushions too.
      Box {
        pickable: body.pickableBed
        low: Qt.vector3d(-root.halfWidth - root.cushionDepth, -40,
                         -root.halfLength - root.cushionDepth)
        high: Qt.vector3d(root.halfWidth + root.cushionDepth, 0,
                          root.halfLength + root.cushionDepth)
        materials: bodyCloth
      }

      //  Keglebillard: the holes milled into the table, and the pins.
      Repeater3D {
        model: body.kegle ? root.holePlaces : []
        delegate: Model {
          source: "#Cylinder"
          position: Qt.vector3d(modelData.x, 0.4, modelData.z)
          scale: Qt.vector3d(root.holeRadius / 50, 0.006,
                             root.holeRadius / 50)
          materials: PrincipledMaterial {
            baseColor: "#040404"
            metalness: 0
            roughness: 1
          }
        }
      }
      Repeater3D {
        model: body.kegle ? 5 : 0
        delegate: Node {
          position: body.pins[index] || Qt.vector3d(0, 0, 0)
          rotation: body.turns[index] || Qt.quaternion(1, 0, 0, 0)
          visible: body.shown[index] === true
          Model {
            geometry: root.shapes.pin || null
            materials: PrincipledMaterial {
              baseColor: "#dcbf92"
              metalness: 0
              roughness: 0.55
            }
          }
          Repeater3D {
            model: root.pinGrooves
            delegate: Model {
              source: "#Cylinder"
              y: modelData.y
              scale: Qt.vector3d(modelData.r / 50, 0.008, modelData.r / 50)
              materials: PrincipledMaterial {
                baseColor: "#5a3a20"
                metalness: 0
                roughness: 0.7
              }
            }
          }
        }
      }

      //  The cushions, clothed, their noses on the cloth's edges; for
      //  keglebillard notched over the pockets, black leather behind.
      Piece {
        geometry: (body.kegle ? root.shapes.cushionLongNotched
                               : root.shapes.cushionLong) || null
        position: Qt.vector3d(root.halfWidth, 0, 0)
        materials: bodyCloth
      }
      Piece {
        geometry: (body.kegle ? root.shapes.cushionLongNotched
                               : root.shapes.cushionLong) || null
        position: Qt.vector3d(-root.halfWidth, 0, 0)
        turn: 180
        materials: bodyCloth
      }
      Piece {
        geometry: (body.kegle ? root.shapes.cushionShortNotched
                               : root.shapes.cushionShort) || null
        position: Qt.vector3d(0, 0, -root.halfLength)
        turn: 90
        materials: bodyCloth
      }
      Piece {
        geometry: (body.kegle ? root.shapes.cushionShortNotched
                               : root.shapes.cushionShort) || null
        position: Qt.vector3d(0, 0, root.halfLength)
        turn: -90
        materials: bodyCloth
      }
      Model {
        visible: body.kegle
        geometry: root.shapes.pocketLeather || null
        materials: PrincipledMaterial {
          baseColor: "#0c0b0a"
          metalness: 0
          roughness: 0.5
          cullMode: Material.NoCulling
        }
      }

      //  The ebony rails behind the cushions.
      Piece {
        geometry: root.shapes.railLong || null
        position: Qt.vector3d(root.halfWidth + root.cushionDepth, 0, 0)
        materials: Ebony {
          oak: body.kegle
          grainShift: Qt.vector3d(13, 0, 517)
        }
      }
      Piece {
        geometry: root.shapes.railLong || null
        position: Qt.vector3d(-root.halfWidth - root.cushionDepth, 0, 0)
        turn: 180
        materials: Ebony {
          oak: body.kegle
          grainShift: Qt.vector3d(-29, 0, 1311)
        }
      }
      Piece {
        geometry: root.shapes.railShort || null
        position: Qt.vector3d(0, 0, -root.halfLength - root.cushionDepth)
        turn: 90
        materials: Ebony {
          oak: body.kegle
          grainShift: Qt.vector3d(7, 0, 233)
        }
      }
      Piece {
        geometry: root.shapes.railShort || null
        position: Qt.vector3d(0, 0, root.halfLength + root.cushionDepth)
        turn: -90
        materials: Ebony {
          oak: body.kegle
          grainShift: Qt.vector3d(-17, 0, 911)
        }
      }

      //  The corner blocks, each turned so its round corner faces out.
      Repeater3D {
        model: [[1, -1, 0], [-1, -1, 90], [-1, 1, 180], [1, 1, -90]]
        delegate: Node {
          position: Qt.vector3d(
            modelData[0] * (root.halfWidth + root.cushionDepth
                            + 0.5 * root.railWidth),
            0,
            modelData[1] * (root.halfLength + root.cushionDepth
                            + 0.5 * root.railWidth))
          eulerRotation: Qt.vector3d(0, modelData[2], 0)
          Model {
            geometry: root.shapes.corner || null
            y: 0.5 * (root.cushionTop + root.railBottom)
            eulerRotation: Qt.vector3d(-90, 0, 0)
            materials: Ebony { oak: body.kegle;
              grainShift: Qt.vector3d(37 * index, 11 * index, 211 * index)
            }
          }
        }
      }

      //  The body under the rails: ebony, light at the corners, two light
      //  inlays all round.
      Piece {
        geometry: root.shapes.apron || null
        materials: Ebony { oak: body.kegle;
          grainShift: Qt.vector3d(0, 0, 1777)
        }
      }
      Repeater3D {
        model: [0.3, 0.72]
        delegate: Box {
          readonly property real level: root.apronBottom
            + modelData * (root.railBottom - root.apronBottom)
          low: Qt.vector3d(-root.apronX - 1.5, level - 6,
                           -root.apronZ - 1.5)
          high: Qt.vector3d(root.apronX + 1.5, level + 6, root.apronZ + 1.5)
          materials: bodyBeige
        }
      }
      Repeater3D {
        model: [[1, 1], [-1, 1], [-1, -1], [1, -1]]
        delegate: Box {
          readonly property real cornerX: modelData[0] * root.apronX
          readonly property real cornerZ: modelData[1] * root.apronZ
          readonly property real innerX: cornerX - modelData[0] * 170
          readonly property real innerZ: cornerZ - modelData[1] * 170
          low: Qt.vector3d(Math.min(cornerX, innerX) - 2,
                           root.apronBottom + 1,
                           Math.min(cornerZ, innerZ) - 2)
          high: Qt.vector3d(Math.max(cornerX, innerX) + 2,
                            root.railBottom - 1,
                            Math.max(cornerZ, innerZ) + 2)
          materials: bodyBeige
        }
      }

      //  Two tapered pedestals on the floor.
      Repeater3D {
        model: [-1, 1]
        delegate: Piece {
          geometry: root.shapes.pedestal || null
          position: Qt.vector3d(0, -root.bedHeight,
                                modelData * root.pedestalPlace)
          turn: 90
          materials: Ebony { oak: body.kegle;
            grainShift: Qt.vector3d(0, 0, 400 * modelData)
            }
        }
      }
      //  The diamonds, inlaid in the rails' tops, shining by themselves:
      //  along the long rails, and turned across on the short ones.
      PrincipledMaterial {
        id: bodyShining
        baseColor: "#fff4dc"
        metalness: 0
        roughness: 0.3
        emissiveFactor: Qt.vector3d(1.6, 1.45, 1.15)
      }
      Repeater3D {
        model: root.diamondPlaces
        delegate: Diamond {
          position: modelData
          eulerRotation.y: Math.abs(modelData.x) > root.halfWidth ? 90 : 0
          materials: bodyShining
        }
      }
  }

  View3D {
    id: view
    anchors.fill: parent
    camera: root.walking ? walkerCamera
                         : root.overhead ? overheadCamera : camera

    //  No glow or bloom: it blurred the diamonds into blobs and hazed
    //  the rest; the diamonds shine by themselves, sharp.
    environment: SceneEnvironment {
      backgroundMode: SceneEnvironment.Color
      clearColor: "#0c0c0e"
      antialiasingMode: SceneEnvironment.MSAA
      antialiasingQuality: SceneEnvironment.VeryHigh
      aoEnabled: true
      aoStrength: 70
      aoDistance: 30
      aoSoftness: 60
      aoSampleRate: 4
      tonemapMode: SceneEnvironment.TonemapModeFilmic
      specularAAEnabled: true
      lightProbe: root.roomLight.toString() === "" ? null : room
      probeExposure: 1.0
    }

    //  The room round the table, lit by the lamp overhead: it lights the
    //  scene softly and the balls mirror it.
    Texture {
      id: room
      source: root.roomLight
      mappingMode: Texture.LightProbe
    }

    PrincipledMaterial {
      id: liveBoard
      lighting: PrincipledMaterial.NoLighting
      baseColorMap: Texture {
        sourceItem: ClubBoard { info: root.liveBoard }
      }
    }
    PrincipledMaterial {
      id: idleBoard
      lighting: PrincipledMaterial.NoLighting
      baseColorMap: Texture {
        sourceItem: ClubBoard { info: root.idleBoard }
      }
    }
    PrincipledMaterial {
      id: floorStone
      baseColor: "#0c0b0a"
      metalness: 0
      roughness: 0.9
      specularAmount: 0
    }

    //  The camera turns round 'cameraFocus', gliding there when it moves:
    //  the cue ball, while a shot is aimed.
    Node {
      id: origin
      position: root.aimFrom
      eulerRotation: root.cameraTurn
      //  However it is turned, by the keys, a drag or the window, never
      //  lower than 'lowestPitch' nor past straight down.
      onEulerRotationChanged: {
        const pitch = Math.max(-89, Math.min(-root.lowestPitch,
                                             eulerRotation.x))
        if (pitch !== eulerRotation.x)
          eulerRotation = Qt.vector3d(pitch, eulerRotation.y,
                                      eulerRotation.z)
      }
      Behavior on position {
        enabled: !root.ghostLook
        Vector3dAnimation { duration: 600; easing.type: Easing.InOutQuad }
      }
      Behavior on eulerRotation {
        enabled: root.cameraGliding
        Vector3dAnimation { duration: 600; easing.type: Easing.InOutQuad }
      }
      PerspectiveCamera {
        id: camera
        z: root.cameraDistance
        fieldOfView: root.cameraView
        clipNear: 20
        clipFar: 40000
        Behavior on z {
          enabled: root.cameraGliding
          NumberAnimation { duration: 600; easing.type: Easing.InOutQuad }
        }
        Behavior on fieldOfView {
          enabled: root.cameraGliding
          NumberAnimation { duration: 600; easing.type: Easing.InOutQuad }
        }
      }
    }

    //  The view from above: high over the cloth's middle, straight down,
    //  the table's length across the picture, taking it all in.
    Node {
      eulerRotation.y: 90
      PerspectiveCamera {
        id: overheadCamera
        y: root.overheadHeight
        eulerRotation.x: -90
        fieldOfView: 2 * Math.atan(root.overheadReach / root.overheadHeight)
                     * 180 / Math.PI
        clipNear: 1000
        clipFar: 20000
      }
    }

    //  The camera, a dot seen from above; from inside it, nothing.
    Model {
      visible: !root.walking
      source: "#Sphere"
      position: camera.scenePosition
      scale: Qt.vector3d(0.6, 0.6, 0.6)
      materials: PrincipledMaterial {
        baseColor: "#e5c07b"
        lighting: PrincipledMaterial.NoLighting
      }
    }

    Repeater3D {
      model: 3
      delegate: SpotLight {
        position: Qt.vector3d(0, root.lampHeight,
                              (index - 1) * root.tableLength / 3)
        eulerRotation.x: -90
        color: "#fff3e2"
        brightness: 0.6
        coneAngle: 120
        innerConeAngle: 70
        constantFade: 1
        linearFade: 0
        quadraticFade: 0
        castsShadow: true
        shadowMapQuality: Light.ShadowMapQualityVeryHigh
        shadowFactor: 60
        shadowMapFar: 4000
        softShadowQuality: Light.PCF16
        pcfFactor: 4
      }
    }

    //  The table played at, where the game's scene has it.
    TableBody {
      kegle: root.kegler
      pickableBed: true
      pins: root.pinPlaces
      turns: root.pinTurns
      shown: root.pinShown
    }

    //  The billiard room (the user: the game opens walking it, first
    //  person, cue in hand, to either table): the table played at stays
    //  where the game's scene has it, the room set round it.
    Node {
      id: roomNode
      position: root.roomShift
      Model {
        source: "#Rectangle"
        y: -root.roomPlan.floor
        eulerRotation.x: -90
        scale: Qt.vector3d(root.roomPlan.halfWidth / 50,
                           root.roomPlan.halfLength / 50,
                           1)
        materials: floorStone
      }
      PrincipledMaterial {
        id: plaster
        baseColor: "#2b231c"
        metalness: 0
        roughness: 0.95
      }
      Repeater3D {
        model: [[-1, 0], [1, 0], [0, -1], [0, 1]]
        delegate: Box {
          readonly property real w: root.roomPlan.halfWidth
          readonly property real l: root.roomPlan.halfLength
          readonly property real f: root.roomPlan.floor
          low: modelData[0] !== 0
            ? Qt.vector3d(modelData[0] < 0 ? -w - 100 : w, -f, -l - 100)
            : Qt.vector3d(-w, -f, modelData[1] < 0 ? -l - 100 : l)
          high: modelData[0] !== 0
            ? Qt.vector3d(modelData[0] < 0 ? -w : w + 100, 2200, l + 100)
            : Qt.vector3d(w, 2200, modelData[1] < 0 ? -l : l + 100)
          materials: plaster
        }
      }

      //  The other table, its pins standing, under its own lamp.
      TableBody {
        position: Qt.vector3d(root.otherX, 0, 0)
        kegle: !root.kegler
        pins: root.pinSpots
        shown: [true, true, true, true, true]
      }
      Repeater3D {
        model: 3
        delegate: SpotLight {
          position: Qt.vector3d(root.otherX, root.lampHeight,
                                (index - 1) * root.tableLength / 3)
          eulerRotation.x: -90
          color: "#fff3e2"
          brightness: 0.6
          coneAngle: 120
          innerConeAngle: 70
          constantFade: 1
          linearFade: 0
          quadraticFade: 0
        }
      }

      //  The club boards (the user: diegetic): one on each end wall over
      //  each table, the table played at's live, the other's waiting.
      Repeater3D {
        model: [["carom", -1], ["carom", 1], ["kegler", -1], ["kegler", 1]]
        delegate: Node {
          readonly property bool live:
            (modelData[0] === "kegler") === root.kegler
          position: Qt.vector3d(root.roomPlan.tables[modelData[0]],
                                root.boardHeight,
                                modelData[1] * (root.roomPlan.halfLength - 50))
          eulerRotation.y: modelData[1] < 0 ? 0 : 180
          Box {
            low: Qt.vector3d(-640, -300, -50)
            high: Qt.vector3d(640, 300, 0)
            materials: PrincipledMaterial {
              baseColor: modelData[0] === "kegler" ? "#6b4526" : "#140f0c"
              metalness: 0
              roughness: 0.5
            }
          }
          Model {
            source: "#Rectangle"
            z: 2
            scale: Qt.vector3d(12.4, 5.58, 1)
            materials: live ? liveBoard : idleBoard
          }
        }
      }

      //  The walker, first person: Qt's 'WasdController' moves it, kept on
      //  the floor at eye height and out of the walls and tables; its
      //  view bobs as it walks (the user: or it feels fake), the cue in
      //  its hand bobbing with it and a little more.
      Node {
        id: walker
        position: Qt.vector3d(root.roomPlan.door[0],
                              root.roomPlan.eye - root.roomPlan.floor,
                              root.roomPlan.door[1])
        onPositionChanged: root.walkerMoved()
        onEulerRotationChanged: {
          const pitch = Math.max(-85, Math.min(85, eulerRotation.x))
          if (pitch !== eulerRotation.x || eulerRotation.z !== 0)
            eulerRotation = Qt.vector3d(pitch, eulerRotation.y, 0)
        }
        PerspectiveCamera {
          id: walkerCamera
          position: Qt.vector3d(root.bobAside, root.bobUp, 0)
          fieldOfView: 70
          clipNear: 20
          clipFar: 40000
          //  The cue carried upright, as in a club (the user: not lowered
          //  like a lance for jousting): held at the right, its tip a
          //  little above the eyes, the butt down by the feet, leaning a
          //  touch forward at the top and in towards the middle.
          Node {
            visible: root.held === "cue"
            position: Qt.vector3d(260 + 0.6 * root.bobAside,
                                  170 + 0.8 * root.bobUp, -520)
            eulerRotation: Qt.vector3d(174, 0, 7)
            Model {
              geometry: root.shapes.cueTip || null
              materials: PrincipledMaterial {
                baseColor: "#3a5f8f"
                roughness: 0.8
              }
            }
            Model {
              geometry: root.shapes.cueFerrule || null
              materials: PrincipledMaterial {
                baseColor: "#f1ede2"
                roughness: 0.35
              }
            }
            Model {
              geometry: root.shapes.cueShaft || null
              materials: PrincipledMaterial {
                baseColor: "#e3c58f"
                roughness: 0.3
              }
            }
            Model {
              geometry: root.shapes.cueButt || null
              materials: PrincipledMaterial {
                baseColor: "#1d1410"
                roughness: 0.25
              }
            }
          }
        }
      }
    }

    //  Over every rail the camera sees from the table's side, whose
    //  diamonds it sees edge on, ghosts of them stand facing it, clear and
    //  faintly lit; not over a rail it looks down on from outside.
    PrincipledMaterial {
      id: ghostly
      baseColor: "#ffe9b0"
      metalness: 0
      roughness: 0.4
      emissiveFactor: Qt.vector3d(1.4, 1.2, 0.8)
      opacity: 0.5
      alphaMode: PrincipledMaterial.Blend
      cullMode: Material.NoCulling
    }
    Repeater3D {
      model: root.diamondPlaces
      delegate: Node {
        readonly property bool onLong:
          Math.abs(modelData.x) > root.halfWidth
        //  How far the camera is out past the diamond, away from the
        //  table: below nought, it sees the rail from the table's side.
        readonly property real outside: onLong
          ? Math.sign(modelData.x) * (root.cameraPlace.x - modelData.x)
          : Math.sign(modelData.z) * (root.cameraPlace.z - modelData.z)
        visible: !root.overhead && !root.walking && outside < 0
        position: Qt.vector3d(modelData.x, modelData.y + 110, modelData.z)
        eulerRotation.y: Math.atan2(root.cameraPlace.x - modelData.x,
                                    root.cameraPlace.z - modelData.z)
                         * 180 / Math.PI
        Diamond {
          eulerRotation.x: 90
          scale: Qt.vector3d(1.4, 1.4, 1.4)
          materials: ghostly
        }
      }
    }

    //  The aim: a line from the ball looked from the way the camera
    //  faces, along the cloth, while a shot is aimed; the harder the
    //  shot, 'aimSpeed' in mm/s, the longer it reaches and the warmer it
    //  burns, from white at a touch to red at 8 m/s.
    Model {
      id: aimLine
      readonly property vector3d heading: Qt.vector3d(
        root.cameraForward.x, 0, root.cameraForward.z).normalized()
      readonly property real hard: Math.min(Math.max(
        root.aimSpeed / 8000, 0), 1)
      readonly property real length: 150 + 0.33 * root.aimSpeed
      readonly property real reach: root.ballRadius + 0.5 * length
      visible: root.aiming
      source: "#Cube"
      position: Qt.vector3d(root.aimFrom.x + heading.x * reach, 1.5,
                            root.aimFrom.z + heading.z * reach)
      eulerRotation: Qt.vector3d(
        0, Math.atan2(heading.x, heading.z) * 180 / Math.PI, 0)
      scale: Qt.vector3d(0.06, 0.02, length / 100)
      materials: PrincipledMaterial {
        baseColor: Qt.rgba(1, 1 - 0.6 * aimLine.hard,
                           0.9 - 0.85 * aimLine.hard, 1)
        lighting: PrincipledMaterial.NoLighting
        opacity: 0.85
        alphaMode: PrincipledMaterial.Blend
      }
    }

    //  The shadow both eyes see (the user): the eyes about as far apart as
    //  a ball is wide, ball 1 hides from both only the strip a ball wide
    //  it sweeps; what that strip touches, the cue ball hits. On the
    //  cloth from the ball aimed from along the aim to the cushion.
    Model {
      id: shadowBand
      readonly property vector3d heading: aimLine.heading
      readonly property real reach: Math.sqrt(root.ballRadius
        * root.ballRadius - Math.pow(root.noseHeight - root.ballRadius, 2))
      readonly property real length: {
        const limX = root.halfWidth - reach
        const limZ = root.halfLength - reach
        const hx = heading.x
        const hz = heading.z
        const px = root.aimFrom.x
        const pz = root.aimFrom.z
        let t = 100000
        if (hx > 1e-9) t = Math.min(t, (limX - px) / hx)
        if (hx < -1e-9) t = Math.min(t, (-limX - px) / hx)
        if (hz > 1e-9) t = Math.min(t, (limZ - pz) / hz)
        if (hz < -1e-9) t = Math.min(t, (-limZ - pz) / hz)
        return Math.max(t, 0)
      }
      visible: root.aiming && root.shadowShown && !root.overhead
               && !root.trenchesShown
      source: "#Cube"
      position: Qt.vector3d(root.aimFrom.x + heading.x * 0.5 * length, 0.8,
                            root.aimFrom.z + heading.z * 0.5 * length)
      eulerRotation: aimLine.eulerRotation
      scale: Qt.vector3d(2 * root.ballRadius / 100, 0.004, length / 100)
      materials: PrincipledMaterial {
        baseColor: "#000000"
        lighting: PrincipledMaterial.NoLighting
        opacity: 0.2
        alphaMode: PrincipledMaterial.Blend
      }
    }

    //  The trenches: ball 1's and ball 2's ways, each in its ball's tint.
    Repeater3D {
      model: 3
      delegate: Model {
        visible: root.aiming && root.shadowShown && !root.overhead
                 && root.trenchesShown && index < root.trenchNames.length
        geometry: root.trenchShapes["trench" + index] || null
        materials: PrincipledMaterial {
          baseColor: root.trenchTints[root.trenchNames[index]] || "#000000"
          lighting: PrincipledMaterial.NoLighting
          opacity: root.trenchOpacities[root.trenchNames[index]] || 0.3
          alphaMode: PrincipledMaterial.Blend
          cullMode: Material.NoCulling
        }
      }
    }

    //  The cue, while the stroke is made (the user): drawn back with the
    //  mouse, reaching the ball as the mouse comes through.
    Node {
      visible: root.stickShown
      position: root.stickPlace
      rotation: root.stickTurn
      Model {
        geometry: root.shapes.cueTip || null
        materials: PrincipledMaterial {
          baseColor: "#3a5f8f"
          roughness: 0.8
        }
      }
      Model {
        geometry: root.shapes.cueFerrule || null
        materials: PrincipledMaterial {
          baseColor: "#f1ede2"
          roughness: 0.35
        }
      }
      Model {
        geometry: root.shapes.cueShaft || null
        materials: PrincipledMaterial {
          baseColor: "#e3c58f"
          roughness: 0.3
        }
      }
      Model {
        geometry: root.shapes.cueButt || null
        materials: PrincipledMaterial {
          baseColor: "#1d1410"
          roughness: 0.25
        }
      }
    }

    Ball {
      position: root.whitePlace
      rotation: root.whiteTurn
      body: "#f2ecd9"
      spot: root.kegler ? "#f2ecd9" : root.dotBlack
    }
    Ball {
      position: root.yellowPlace
      rotation: root.yellowTurn
      body: root.kegler ? "#f2ecd9" : "#f5b21b"
      spot: root.dotBlack
    }
    Ball {
      position: root.redPlace
      rotation: root.redTurn
      body: "#c4141b"
      spot: root.dotBlack
    }

    //  The mark: a ghost of the cue ball, clear, where it must be.
    Model {
      visible: root.markShown
      source: "#Sphere"
      position: root.ghostLook ? root.ghostPlace : root.markPlace
      scale: Qt.vector3d(root.ballScale, root.ballScale, root.ballScale)
      materials: PrincipledMaterial {
        baseColor: root.markColor
        metalness: 0
        roughness: 0.2
        opacity: 0.35
        alphaMode: PrincipledMaterial.Blend
      }
    }

    //  The impact: a clear copy of ball 1 where, as aimed, it meets
    //  ball 2.
    Model {
      visible: root.aiming && root.trenchesShown && root.impactShown
      source: "#Sphere"
      position: root.impactPlace
      scale: Qt.vector3d(root.ballScale, root.ballScale, root.ballScale)
      materials: PrincipledMaterial {
        baseColor: root.impactColor
        metalness: 0
        roughness: 0.2
        opacity: 0.35
        alphaMode: PrincipledMaterial.Blend
      }
    }

    //  The last shot, while the view from above fills the view.
    ShotTrails {
      visible: root.overhead && root.trailsShown
    }
  }

  OrbitCameraController {
    anchors.fill: view
    origin: origin
    camera: camera
    automaticClipping: false
    mouseEnabled: !root.moving && !root.walking
  }

  //  Walking: W A S D, Shift to hurry (Qt's own controller); the mouse
  //  looks round, 'lookBy', the pointer hidden.
  WasdController {
    id: wasd
    anchors.fill: view
    controlledObject: walker
    enabled: root.walking
    keysEnabled: root.walking && !root.inventoryOpen
    mouseEnabled: false
    forwardSpeed: 15
    backSpeed: 12
    leftSpeed: 12
    rightSpeed: 12
    upSpeed: 0
    downSpeed: 0
    shiftSpeed: 2.2
  }

  Item {
    anchors.fill: view
    enabled: root.moving && !root.walking
    DragHandler {
      target: null
      dragThreshold: 0
      onActiveChanged: {
        if (active) {
          const hit = view.pick(centroid.pressPosition.x,
                                centroid.pressPosition.y)
          if (hit.objectHit)
            root.clothPressed(hit.scenePosition.x, hit.scenePosition.z)
        } else {
          root.clothReleased()
        }
      }
      onCentroidChanged: {
        if (!active)
          return
        const hit = view.pick(centroid.position.x, centroid.position.y)
        if (hit.objectHit)
          root.clothDragged(hit.scenePosition.x, hit.scenePosition.z)
      }
    }
  }

  //  The stroke: the right button held, followed wherever it goes, but
  //  pressed on the corner, its menu's; the left button is the camera's
  //  still, its press telling the next shot begins to be aimed.
  Item {
    id: strokeArea
    anchors.fill: view
    enabled: !root.walking
    PointHandler {
      property bool stroking: false
      acceptedButtons: Qt.RightButton
      onActiveChanged: {
        if (active) {
          stroking = !root.inCorner(strokeArea, point.pressPosition)
          if (stroking)
            root.strokePressed(point.pressPosition.x,
                               point.pressPosition.y)
        } else if (stroking) {
          stroking = false
          root.strokeReleased()
        }
      }
      onPointChanged: {
        if (active && stroking)
          root.strokeMoved(point.position.x, point.position.y)
      }
    }
    PointHandler {
      acceptedButtons: Qt.LeftButton
      onActiveChanged: {
        if (active && !root.inCorner(strokeArea, point.pressPosition))
          root.aimTouched()
      }
    }
  }

  //  A tap on the table: on a ball, or where on the cloth from above.
  Item {
    anchors.fill: view
    enabled: !root.moving && !root.walking
    TapHandler {
      onTapped: function(point, button) {
        const at = point.position
        if (root.overhead) {
          const place = root.overheadPlace(view, at.x, at.y)
          root.tableTapped(place.x, place.y)
          return
        }
        const hit = view.pick(at.x, at.y)
        if (hit.objectHit)
          root.tableTapped(hit.scenePosition.x, hit.scenePosition.z)
      }
    }
  }

  //  The corner: the same table, seen from above, while the camera's
  //  view fills the window; hidden while the view from above does.
  Rectangle {
    id: corner
    visible: !root.overhead && !root.walking
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.margins: 12
    width: Math.min(340, 0.3 * parent.width)
    height: width * root.spanAcross / root.spanAlong
    color: "#0c0c0e"
    border.color: "#3a3d41"
    border.width: 1

    View3D {
      id: inset
      anchors.fill: parent
      anchors.margins: 1
      importScene: view.scene
      camera: overheadCamera
      environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#0c0c0e"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeFilmic
        lightProbe: root.roomLight.toString() === "" ? null : insetRoom
        probeExposure: 1.0
      }
      Texture {
        id: insetRoom
        source: root.roomLight
        mappingMode: Texture.LightProbe
      }

      //  The last shot.
      ShotTrails {
        visible: root.trailsShown
      }

      //  Seen only here, and only from above: each ball ringed in its
      //  colour, the diamonds large, crosshairs under what the camera
      //  looks from (no view cone: the user).
      Node {
        Halo { position: root.whitePlace; tint: "#f2ecd9" }
        Halo { position: root.yellowPlace; tint: root.markedTint }
        Halo { position: root.redPlace; tint: "#e0262d" }
        Repeater3D {
          model: root.diamondPlaces
          delegate: Diamond {
            position: Qt.vector3d(modelData.x, modelData.y + 2,
                                  modelData.z)
            eulerRotation.y:
              Math.abs(modelData.x) > root.halfWidth ? 90 : 0
            scale: Qt.vector3d(3.8, 1, 3.8)
            materials: PrincipledMaterial {
              baseColor: "#000000"
              metalness: 0
              emissiveFactor: Qt.vector3d(1.7, 1.15, 0.12)
            }
          }
        }
        Repeater3D {
          model: [0, 90]
          delegate: Model {
            source: "#Cube"
            position: Qt.vector3d(root.aimFrom.x, 3, root.aimFrom.z)
            eulerRotation.y: modelData
            scale: Qt.vector3d(0.14, 0.02, 3.2)
            materials: PrincipledMaterial {
              baseColor: "#e5c07b"
              lighting: PrincipledMaterial.NoLighting
            }
          }
        }
      }
    }

    TapHandler {
      onTapped: function(point, button) {
        const at = point.position
        const place = root.overheadPlace(inset, at.x - 1, at.y - 1)
        root.tableTapped(place.x, place.y)
      }
    }
    TapHandler {
      acceptedButtons: Qt.RightButton
      onTapped: function(point, button) {
        const at = corner.mapToItem(root, point.position.x,
                                    point.position.y)
        root.minimapMenuAsked(at.x, at.y)
      }
    }
  }

  //  The speedometer, clear, over the ball aimed from: a dial to
  //  'gaugeMost', filled green to red, a needle and the speed.
  Item {
    id: speedometer
    visible: root.gaugeShown && !root.overhead
    width: 150
    height: 104
    opacity: 0.8
    function shown() {
      const top = Qt.vector3d(root.aimFrom.x,
                              root.aimFrom.y + 2.5 * root.ballRadius,
                              root.aimFrom.z)
      const at = view.mapFrom3DScene(top)
      x = at.x - 0.5 * width
      y = at.y - height
      dial.requestPaint()
    }
    Canvas {
      id: dial
      anchors.fill: parent
      onPaint: {
        const ctx = getContext("2d")
        ctx.reset()
        const cx = 0.5 * width
        const cy = height - 22
        const r = 62
        const start = 0.85 * Math.PI
        const sweep = 1.3 * Math.PI
        const most = Math.max(root.gaugeMost, 1)
        const share = Math.min(Math.max(root.gaugeSpeed / most, 0), 1)
        ctx.lineCap = "round"
        ctx.lineWidth = 10
        ctx.strokeStyle = "rgba(16, 17, 20, 0.6)"
        ctx.beginPath()
        ctx.arc(cx, cy, r, start, start + sweep)
        ctx.stroke()
        if (share > 0) {
          const red = Math.round(80 + 150 * share)
          const green = Math.round(205 - 145 * share)
          const blue = Math.round(120 - 70 * share)
          ctx.strokeStyle = "rgb(" + red + "," + green + "," + blue + ")"
          ctx.beginPath()
          ctx.arc(cx, cy, r, start, start + sweep * share)
          ctx.stroke()
        }
        ctx.lineCap = "butt"
        ctx.strokeStyle = "rgba(255, 255, 255, 0.85)"
        for (let k = 0; k <= most; ++k) {
          const a = start + sweep * k / most
          const inner = r - (k % 5 === 0 ? 17 : 11)
          ctx.lineWidth = k % 5 === 0 ? 2.5 : 1.5
          ctx.beginPath()
          ctx.moveTo(cx + inner * Math.cos(a), cy + inner * Math.sin(a))
          ctx.lineTo(cx + (r - 6) * Math.cos(a), cy + (r - 6) * Math.sin(a))
          ctx.stroke()
        }
        const needle = start + sweep * share
        ctx.strokeStyle = "#ffffff"
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.lineTo(cx + (r - 14) * Math.cos(needle),
                   cy + (r - 14) * Math.sin(needle))
        ctx.stroke()
        ctx.fillStyle = "#ffffff"
        ctx.beginPath()
        ctx.arc(cx, cy, 4, 0, 2 * Math.PI)
        ctx.fill()
        ctx.font = "bold 17px sans-serif"
        ctx.textAlign = "center"
        ctx.fillText(root.gaugeSpeed.toFixed(1) + " m/s", cx, cy + 19)
      }
    }
  }

  //  The barrier: a clear block barred by a red sign, over the ball aimed
  //  from, as a shot asked for too soon is refused.
  Item {
    id: barrier
    width: 84
    height: 84
    opacity: 0
    visible: opacity > 0
    function place() {
      const top = Qt.vector3d(root.aimFrom.x,
                              root.aimFrom.y + 2.5 * root.ballRadius,
                              root.aimFrom.z)
      const at = view.mapFrom3DScene(top)
      x = at.x - 0.5 * width
      y = at.y - height
      sign.requestPaint()
    }
    Canvas {
      id: sign
      anchors.fill: parent
      onPaint: {
        const ctx = getContext("2d")
        ctx.reset()
        const s = width
        ctx.fillStyle = "rgba(205, 228, 255, 0.2)"
        ctx.fillRect(4, 4, s - 8, s - 8)
        ctx.strokeStyle = "rgba(235, 245, 255, 0.8)"
        ctx.lineWidth = 3
        ctx.strokeRect(4, 4, s - 8, s - 8)
        const c = 0.5 * s
        const r = 0.29 * s
        const d = r * Math.SQRT1_2
        ctx.strokeStyle = "#e0262d"
        ctx.lineWidth = 0.11 * s
        ctx.beginPath()
        ctx.arc(c, c, r, 0, 2 * Math.PI)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(c - d, c - d)
        ctx.lineTo(c + d, c + d)
        ctx.stroke()
      }
    }
    SequentialAnimation {
      id: barrierFlash
      NumberAnimation {
        target: barrier; property: "opacity"; to: 0.95; duration: 60
      }
      PauseAnimation { duration: 650 }
      NumberAnimation {
        target: barrier; property: "opacity"; to: 0; duration: 500
      }
    }
  }

  //  Walking: a dot where the walker looks, how to walk, and, near a
  //  table, what E does there.
  Rectangle {
    visible: root.walking
    anchors.centerIn: view
    width: 5; height: 5; radius: 3
    color: "#f6f0e4"
    opacity: 0.7
  }
  Text {
    visible: root.walking
    anchors.left: view.left
    anchors.top: view.top
    anchors.margins: 16
    text: root.looking
      ? "W A S D to walk  ·  Shift to hurry  ·  E inventory  ·  "
        + "Esc frees the mouse"
      : "Click to look round with the mouse"
    color: "#d8cfbf"
    font.pixelSize: 15
    style: Text.Outline
    styleColor: "#000000"
  }
  Text {
    visible: root.walking && root.nearTable !== ""
    anchors.horizontalCenter: view.horizontalCenter
    anchors.bottom: view.bottom
    anchors.bottomMargin: 64
    text: "E  ·  play " + (root.nearTable === "kegler" ? "kegler"
                                                      : "three-cushion")
    color: "#f6f0e4"
    font.pixelSize: 24
    font.bold: true
    style: Text.Outline
    styleColor: "#000000"
  }

  //  A slot of the inventory: its item drawn, lit while held; a click
  //  takes the item in hand, or puts it away.
  component Slot: Rectangle {
    id: slot
    property var item: null
    readonly property bool chosen: !!item && item.name === root.held
    width: 58
    height: 58
    radius: 4
    color: chosen ? "#3a3326" : "#1e1c1a"
    border.width: 2
    border.color: chosen ? "#e5c07b" : "#4a4540"
    Canvas {
      anchors.fill: parent
      anchors.margins: 6
      visible: !!slot.item
      onPaint: {
        const ctx = getContext("2d")
        ctx.reset()
        if (!slot.item || slot.item.name !== "cue")
          return
        const w = width, h = height
        ctx.lineCap = "round"
        const parts = [[0.08, 0.30, "#1d1410", 5],
                       [0.30, 0.78, "#e3c58f", 3.4],
                       [0.78, 0.86, "#f1ede2", 3], [0.86, 0.92, "#3a5f8f", 3]]
        for (const part of parts) {
          ctx.strokeStyle = part[2]
          ctx.lineWidth = part[3]
          ctx.beginPath()
          ctx.moveTo(w * part[0], h * (1 - part[0]))
          ctx.lineTo(w * part[1], h * (1 - part[1]))
          ctx.stroke()
        }
      }
    }
    TapHandler {
      enabled: !!slot.item && root.inventoryOpen
      onTapped: root.itemChosen(slot.item.name)
    }
  }

  //  The hotbar along the bottom while walking, the item held lit.
  Row {
    visible: root.walking && !root.inventoryOpen
    anchors.horizontalCenter: view.horizontalCenter
    anchors.bottom: view.bottom
    anchors.bottomMargin: 14
    spacing: 4
    Repeater {
      model: 9
      delegate: Slot {
        item: root.inventory[index] || null
        opacity: 0.85
      }
    }
  }

  //  The inventory (the user: E, as in the block-building games): every
  //  item carried in a grid, the hotbar under it; the cue first, more to
  //  come.
  Rectangle {
    visible: root.walking && root.inventoryOpen
    anchors.fill: view
    color: Qt.rgba(0, 0, 0, 0.55)
    TapHandler {}
    Rectangle {
      anchors.centerIn: parent
      width: 9 * 62 + 36
      height: inventoryColumn.implicitHeight + 36
      radius: 8
      color: "#2a2622"
      border.color: "#5a524a"
      border.width: 2
      Column {
        id: inventoryColumn
        anchors.centerIn: parent
        spacing: 10
        Text {
          text: "Inventory"
          color: "#f2ecd9"
          font.pixelSize: 22
          font.bold: true
        }
        Grid {
          columns: 9
          spacing: 4
          Repeater {
            model: 27
            delegate: Slot { item: root.inventory[9 + index] || null }
          }
        }
        Text {
          text: "Hotbar"
          color: "#a39886"
          font.pixelSize: 15
        }
        Row {
          spacing: 4
          Repeater {
            model: 9
            delegate: Slot { item: root.inventory[index] || null }
          }
        }
        Text {
          text: root.held === "cue"
            ? "In hand: the cue. Click it to put it away."
            : "Nothing in hand. Click the cue to take it."
          color: "#a39886"
          font.pixelSize: 15
        }
      }
    }
  }

  //  The cushions the cue ball has met, and the balls, over the view.
  Rectangle {
    visible: root.counterShown && !root.walking
    anchors.top: parent.top
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.topMargin: 14
    radius: 6
    color: "#d915181c"
    border.color: "#e5c07b"
    border.width: 1
    width: counterWords.implicitWidth + 40
    height: counterWords.implicitHeight + 18
    Text {
      id: counterWords
      anchors.centerIn: parent
      text: root.counterText
      color: "#f2ecd9"
      font.pixelSize: 26
      font.bold: true
    }
  }
}
