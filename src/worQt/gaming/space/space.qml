//  space.qml draws the solar system for the 'SpaceViewport', by the GPU
//  (Qt Quick 3D). The flight view in two layers: far, the heavenly
//  bodies, each drawn nearer and smaller in proportion past a distance
//  (the same picture, within float32 and the depth buffer); near, over
//  it, the rocket, the pad and the ground under the eye. The map (the
//  'Orrery') instead when open: the bodies, their paths, the vessel's,
//  and marks over them. Python sets everything here, each frame, from
//  the eye: the eye is at the scene's middle, nothing far from it.
//
//  The scene's own axes are y up; each layer's 'world' node turns the
//  ecliptic's (z north) into them, so what is in it is given in the
//  ecliptic's terms, m (the map's scaled).
//
//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen

import QtQuick
import QtQuick3D

Item {
  id: root

  //  The flight view's eye (its turn, the scene's) and the sun's light
  //  (shining along its own -z); the sky's colour behind everything
  property quaternion cameraTurn: Qt.quaternion(1, 0, 0, 0)
  property quaternion sunTurn: Qt.quaternion(1, 0, 0, 0)
  property color skyColour: "black"
  //  The far layer: each body {geometry, picture, glow, slot}, and each
  //  slot's place (m from the eye), turn (the body's own axes to the
  //  ecliptic's) and scale (the drawn radius, m)
  property var farBodies: []
  property var farPlaces: []
  property var farTurns: []
  property var farScales: []
  //  The near layer: each part {geometry, colour, metal, rough, picture,
  //  slot, culled}, and each slot's place, turn and whether it shows
  property var nearParts: []
  property var nearPlaces: []
  property var nearTurns: []
  property var nearShown: []
  //  Each near slot's glow (a lit button's label), the near camera's
  //  nearest cut (m: Asger's eyes see his panel 0.7 m off), the cabin's
  //  lamp's place
  property var nearGlows: []
  property real nearClip: 0.3
  property vector3d habitatLight: Qt.vector3d(0, 0, 0)
  property bool habitatOn: false
  //  The way in on the pad at night (user, 2026-11-17: "Asger must start
  //  outside in the night"): the launch tower's floodlights on the rocket
  //  (each its place and turn), the lamp over its platform and walkway,
  //  whether the walkway is out (its lamp lit)
  property var towerFloodPlaces: []
  property var towerFloodTurns: []
  property vector3d outdoorLamp: Qt.vector3d(0, 0, 0)
  property bool outdoorOn: false
  //  The quest (user, 2026-11-17: "Here the quest begins"; '_quest'): its
  //  steps (each its text, done, current, optional); the warning manual
  //  looked at close (E: "with E you get a better view at it. Like in
  //  RDR2"), its picture
  property var questRows: []
  //  The gravity gun in his hands, drawn over the world from his eyes
  //  (user, 2026-11-17: "the gravgun cuts in to walls and textures when
  //  you are cloes to the wall"): its parts (each {geometry, colour,
  //  metal, rough, picture, unlit, masked}, his eyes' frame), whether it
  //  shows (up, his eyes), its shake (straining at a bolt)
  property var handParts: []
  property bool handShown: false
  //  Asger's hotbar and inventory (user, 2026-11-17: "Give Asger a hotbar
  //  and an inventory like in minecraft"; '_inventory'): each slot's
  //  kind, count and title, the hotbar's selected slot, the inventory
  //  open, the stack on the pointer, the items' icons by kind, the held
  //  item's name fading in and out; the telescope ("give Asger also a
  //  telescope"): the view's height (deg) and its round edge's share.
  property var inventoryRows: []
  property int hotbarSelected: 0
  property bool inventoryOpen: false
  property bool hotbarShown: false
  property var carriedRow: ({kind: "", count: 0})
  property var itemIcons: ({})
  property real heldFade: 0
  property real viewField: 60
  property real scopeShown: 0
  property real pointerX: 0
  property real pointerY: 0
  property string hoverTitle: ""
  property vector3d handShake: Qt.vector3d(0, 0, 0)
  property bool manualShown: false
  property string manualPicture: ""
  property vector3d cabinLight: Qt.vector3d(0, 0, 0)
  property vector3d panelLamp: Qt.vector3d(0, 0, 0)
  //  The globe's own glow on what is near it (user, 2026-11-17: "have the
  //  ball-horizon emit light slightly")
  property vector3d globeLight: Qt.vector3d(0, 0, 0)
  property vector3d floodPlace: Qt.vector3d(0, 0, 0)
  //  The cabin's warm lights (its floor lamp, its candles: their
  //  flicker) and the warp knob's glint's slide (once round its loop)
  property vector3d lampLight: Qt.vector3d(0, 0, 0)
  property vector3d candleLight: Qt.vector3d(0, 0, 0)
  property real candleGlow: 1.0
  property real glintPhase: 0.0
  //  Asger's bars (user, 2026-11-17: "AsgerJon should have a health bar
  //  and hunger bar like in minecraft"): health and food, points of
  //  twenty (ten hearts, ten drumsticks; our own pixels); how red he
  //  sees being hurt; how much of a ration he has eaten; dead, what
  //  killed him.
  //  Near a body: how much of the sun's light reaches the eye (nought in
  //  the body's shadow), the body's light thrown back up (its turn, its
  //  share of the sun's); far satellites' lights drawn as points (each
  //  its place in the scene and its rainbow's share, below nought warm).
  property real sunShine: 1.0
  property quaternion earthTurn: Qt.quaternion(1, 0, 0, 0)
  property real earthShine: 0.0
  property var lightPoints: []
  property var lightHues: []
  property real health: 20
  property real food: 20
  property real hurtShown: 0
  property real eatingShown: 0
  property string deathText: ""
  readonly property var heartPixels: [
    ".oo...oo.", "ohfo.offo", "ohffofffo", "offfffffo", ".offfffo.",
    "..offfo..", "...ofo...", "....o...."]
  readonly property var drumstickPixels: [
    "..ooo....", ".offfo...", "ofhfffo..", "offfffo..", "offffo...",
    ".offob...", "..oo.bb..", "......bb.", "......b.b"]

  //  Paints one icon of 'pixels' (9 a row: '.' none, 'o' outline, 'b'
  //  bone, else filled: 'h' its highlight) on 'ctx' 'size' px a side:
  //  'fill' two points whole, one half (its 'side': -1 the left, 1 the
  //  right), none its empty colour.
  function paintIcon(ctx, size, pixels, fill, side, full, light, empty) {
    var s = size / 9
    ctx.reset()
    for (var r = 0; r < pixels.length; r++) {
      for (var c = 0; c < 9; c++) {
        var p = pixels[r].charAt(c)
        if (p === ".")
          continue
        var colour = "#1c1010"
        if (p === "b") {
          colour = "#efe6d2"
        } else if (p !== "o") {
          var lit = fill >= 2 || (fill >= 1 && (side < 0 ? c < 5 : c > 3))
          colour = lit ? (p === "h" ? light : full) : empty
        }
        ctx.fillStyle = colour
        ctx.fillRect(c * s, r * s, Math.ceil(s), Math.ceil(s))
      }
    }
  }
  NumberAnimation on glintPhase {
    from: 0.0
    to: 1.0
    duration: 2800
    loops: Animation.Infinite
  }
  property quaternion floodTurn: Qt.quaternion(1, 0, 0, 0)
  //  Seen through Asger's eyes (user, 2026-11-16: "in first person the
  //  hud hides and instead Asger is presented iwth a fully functional
  //  diegetic dashboard"): the overlays hidden, a dot in the middle, the
  //  input he looks at (its key and what working it does, '' none); the
  //  teleprinter's paper (user, 2026-11-16: "Instead of a terminal ...
  //  a teleprinter"; "a modern font like nerd monospace to be cheeky"):
  //  its lines printed, the line being typed, its font, its mesh, its
  //  picture's layout ('Dashboard.paperLayout': 77 a line, 2026-11-17); the
  //  closed circuit monitor (user, 2026-11-16: "Replase the radar with a
  //  cctv type thing"): its screen's mesh, the hull camera's place and
  //  turn (the scene's), the picture's time
  property bool cockpitOn: false
  property string promptKey: ""
  property string promptName: ""
  property var paperLines: []
  property string paperTyping: ""
  property string paperFont: "JetBrainsMono Nerd Font Mono"
  property var paperGeometry: null
  property var paperLayout: null
  property real sleepShade: 0
  onPaperLinesChanged: paperCanvas.requestPaint()
  onPaperLayoutChanged: paperCanvas.requestPaint()
  onPaperTypingChanged: paperCanvas.requestPaint()
  //  The readouts (user, 2026-11-17: "All the auto stuff has to be in one
  //  place"; "it wasn't at all clear how near I was to Terra Prime"): the
  //  AUTOPILOT's lit status line and Terra Prime's range in glowing
  //  number tubes, one canvas ('Dashboard.readoutLayout'), its mesh.
  property string readoutStatus: ""
  property var readoutRange: []
  property string readoutPort: ""
  property var readoutGeometry: null
  property var readoutLayout: null
  onReadoutStatusChanged: readoutCanvas.requestPaint()
  onReadoutRangeChanged: readoutCanvas.requestPaint()
  onReadoutPortChanged: readoutCanvas.requestPaint()
  onReadoutLayoutChanged: readoutCanvas.requestPaint()
  property var screenGeometry: null
  property vector3d cctvPlace: Qt.vector3d(0, 0, 0)
  property quaternion cctvTurn: Qt.quaternion(1, 0, 0, 0)
  //  The monitor's feed (user, 2026-11-17: "The CCTV shall have two
  //  possible feeds: The one it has now, AND one that aims the
  //  docking"): its label, whether it is the nose's docking camera (a
  //  cross in its middle; the docking's numbers are under the monitor:
  //  'readoutPort').
  property string cctvLabel: "CAM 1  AFT"
  property bool cctvNose: false
  //  The ground under the eye: its mesh (a cap, the body's own axes), its
  //  body's picture, its place and turn, whether it shows
  property var capGeometry: null
  property string capPicture: ""
  property vector3d capPlace: Qt.vector3d(0, 0, 0)
  property quaternion capTurn: Qt.quaternion(1, 0, 0, 0)
  property bool capShown: false
  //  The gravity gun's beam to the bolt it holds (user, 2026-11-17: "a
  //  laser beam between it and the bolts"): its core and its coils,
  //  remade each frame, from the muzzle in the rocket's own axes.
  property var beamCore: null
  property var beamCoils: null
  property vector3d beamPlace: Qt.vector3d(0, 0, 0)
  property quaternion beamTurn: Qt.quaternion(1, 0, 0, 0)
  property bool beamShown: false
  //  The map: open or not; its eye's turn; its bodies {geometry,
  //  picture, glow, slot} with each slot's place, turn and scale; its
  //  lines {geometry, colour, slot} with each slot's place and scale;
  //  the marks over it {x, y, text, colour}
  property bool mapOpen: false
  property quaternion mapCameraTurn: Qt.quaternion(1, 0, 0, 0)
  property var mapBodies: []
  property var mapPlaces: []
  property var mapTurns: []
  property var mapScales: []
  property var mapLines: []
  property var linePlaces: []
  property var lineScales: []
  property var marks: []
  //  What the flight says (top left), the keys (along the bottom), and a
  //  word in the middle while it readies ('' none)
  property string readout: ""
  property string hint: ""
  property string status: ""
  //  The artificial horizon: shown or not; its mesh (mirrored: seen as
  //  the pilot sees), its picture and turn; its marks {x, y, kind} (px
  //  from its middle); the nose's pitch and heading (deg) and which path
  //  it shows ('orbit', 'surface')
  property bool navShown: false
  property var navGeometry: null
  property string navPicture: ""
  property quaternion navTurn: Qt.quaternion(1, 0, 0, 0)
  property var navMarks: []
  property real navPitch: 0
  property real navHeading: 0
  property string navKind: ""
  readonly property real navRadius: 104
  //  The control board (user, 2026-11-16: "a cute control board looking
  //  thing that discrete floats a keyboard key to indicate which"): the
  //  throttle (0 to 1), the autopilot's mode, the warp and whether it
  //  warps to the apoapsis, the ascent guidance (on, its phase, its
  //  orbit), the map; the keys held ('|W|S|': their caps lit); a click
  //  on a lamp says its action ('boardPicked')
  property real boardThrottle: 0
  property string boardMode: "off"
  property int boardWarp: 1
  property bool boardToAp: false
  property string boardApMode: "orbit"
  property bool boardEngaged: false
  property string boardPhase: ""
  property bool boardAction: false
  property bool boardLaunched: false
  property string boardTarget: ""
  property bool boardMap: false
  property string boardLimit: "4 g"
  property bool boardMatch: false
  property bool boardNose: false
  property bool boardThrusting: false
  property bool boardUp: false
  property string boardHeld: "|"
  signal boardPicked(string action)
  signal inventoryClicked(int slot, bool right)
  //  The board's keys float a little, all together
  property real bob: 0
  SequentialAnimation on bob {
    loops: Animation.Infinite
    NumberAnimation { to: 2.5; duration: 900; easing.type: Easing.InOutSine }
    NumberAnimation { to: 0; duration: 900; easing.type: Easing.InOutSine }
  }

  //  A key cap: its name; lit while its key is held
  component KeyCap: Rectangle {
    id: cap
    property string name: ""
    property bool down: root.boardHeld.indexOf("|" + name + "|") >= 0
    width: Math.max(22, capText.implicitWidth + 10)
    height: 20
    radius: 4
    color: down ? "#ffd36b" : "#e8ecf0"
    border.color: down ? "#c89a2a" : "#8a949e"
    border.width: 1.5
    Text {
      id: capText
      anchors.centerIn: parent
      text: cap.name
      color: "#181c22"
      font.pixelSize: 11
      font.bold: true
    }
  }

  //  A lamp on the board: what it says, lit or not and in what colour,
  //  its keys floating over it, the action a click on it asks for
  component Lamp: Item {
    id: lamp
    property string label: ""
    property bool lit: false
    property color tint: "#6be08a"
    property var keys: []
    property string action: ""
    width: Math.max(86, lampText.implicitWidth + 18, caps.implicitWidth + 6)
    height: 52
    Row {
      id: caps
      anchors.horizontalCenter: parent.horizontalCenter
      y: 2 - root.bob
      spacing: 3
      Repeater {
        model: lamp.keys
        delegate: KeyCap {
          required property var modelData
          name: modelData
        }
      }
    }
    Rectangle {
      y: 24
      width: parent.width
      height: 28
      radius: 7
      color: lamp.lit ? lamp.tint : "#262b33"
      border.color: lamp.lit ? Qt.lighter(lamp.tint, 1.3) : "#3c4450"
      border.width: 1.5
      Text {
        id: lampText
        anchors.centerIn: parent
        text: lamp.label
        color: lamp.lit ? "#0c1014" : "#b4bdc8"
        font.pixelSize: 13
        font.bold: lamp.lit
      }
      MouseArea {
        anchors.fill: parent
        enabled: lamp.action !== ""
        cursorShape: Qt.PointingHandCursor
        onClicked: root.boardPicked(lamp.action)
      }
    }
  }

  //  A group of lamps under its name
  component Group: Column {
    property string title: ""
    default property alias lamps: lampRow.data
    spacing: 2
    Text {
      text: parent.title
      color: "#7f8b99"
      font.pixelSize: 11
      font.bold: true
      font.letterSpacing: 1.5
    }
    Row {
      id: lampRow
      spacing: 6
    }
  }

  //  The two layers' scenes, standalone: each imported by its view and
  //  by the closed circuit camera's (Qt's way of several views of one
  //  scene: a scene inside one view cannot be shown by another).
  Node {
    id: farWorld
    eulerRotation.x: -90
    Repeater3D {
      model: root.farBodies
      delegate: Model {
        required property var modelData
        geometry: modelData.geometry
        position: root.farPlaces[modelData.slot] || Qt.vector3d(0, 0, 0)
        rotation: root.farTurns[modelData.slot] || Qt.quaternion(1, 0, 0, 0)
        property real size: root.farScales[modelData.slot] || 1
        scale: Qt.vector3d(size, size, size)
        materials: PrincipledMaterial {
          lighting: modelData.glow > 0 ? PrincipledMaterial.NoLighting
                                       : PrincipledMaterial.FragmentLighting
          baseColorMap: Texture {
            source: modelData.picture
            tilingModeHorizontal: Texture.Repeat
          }
          alphaMode: modelData.ring ? PrincipledMaterial.Blend
                                    : PrincipledMaterial.Opaque
          cullMode: modelData.ring ? Material.NoCulling : Material.BackFaceCulling
          metalness: 0
          roughness: 1
        }
      }
    }
  }

  Node {
    id: nearWorld
    eulerRotation.x: -90
    Model {
      geometry: root.capGeometry
      visible: root.capShown && root.capGeometry !== null
      position: root.capPlace
      rotation: root.capTurn
      materials: PrincipledMaterial {
        baseColorMap: Texture {
          source: root.capPicture
          tilingModeHorizontal: Texture.Repeat
        }
        metalness: 0
        roughness: 1
      }
    }
    Model {
      geometry: root.beamCore
      visible: root.beamShown && root.beamCore !== null
      position: root.beamPlace
      rotation: root.beamTurn
      materials: PrincipledMaterial {
        lighting: PrincipledMaterial.NoLighting
        baseColor: "#eedcff"
        opacity: 0.95
        cullMode: Material.NoCulling
      }
    }
    Model {
      geometry: root.beamCoils
      visible: root.beamShown && root.beamCoils !== null
      position: root.beamPlace
      rotation: root.beamTurn
      materials: PrincipledMaterial {
        lighting: PrincipledMaterial.NoLighting
        baseColor: "#a35cff"
        opacity: 0.95
        cullMode: Material.NoCulling
      }
    }
    //  Qt Quick 3D takes a light's fades as if its scene were in cm (it
    //  scales the linear term by 0.01 and the quadratic by 0.0001): this
    //  scene is in m, so a quadratic fade of q a square metre is written
    //  q x 10000 (written in metres, every lamp lit the whole cabin
    //  alike, at its full brightness).
    //  The space station's own light on its axis (docked: going aboard,
    //  user, 2026-11-17), lighting its hub, shafts and ring from inside,
    //  as bright at the deck as at the hub.
    PointLight {
      position: root.habitatLight
      visible: root.habitatOn
      color: "#fff3df"
      brightness: 0.85
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 0.0
    }
    SpotLight {
      position: root.towerFloodPlaces.length > 0
                ? root.towerFloodPlaces[0] : Qt.vector3d(0, 0, 0)
      rotation: root.towerFloodTurns.length > 0
                ? root.towerFloodTurns[0] : Qt.quaternion(1, 0, 0, 0)
      visible: root.towerFloodPlaces.length > 0
               && (root.nearShown[0] || false)
      color: "#eef2ff"
      brightness: 3.0
      coneAngle: 55
      innerConeAngle: 10
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 30
    }
    SpotLight {
      position: root.towerFloodPlaces.length > 1
                ? root.towerFloodPlaces[1] : Qt.vector3d(0, 0, 0)
      rotation: root.towerFloodTurns.length > 1
                ? root.towerFloodTurns[1] : Qt.quaternion(1, 0, 0, 0)
      visible: root.towerFloodPlaces.length > 1
               && (root.nearShown[0] || false)
      color: "#eef2ff"
      brightness: 3.0
      coneAngle: 55
      innerConeAngle: 10
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 30
    }
    PointLight {
      position: root.outdoorLamp
      visible: root.outdoorOn
      color: "#fff1d8"
      brightness: 0.6
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 1500
    }
    PointLight {
      position: root.cabinLight
      visible: root.nearShown.length > 1 && (root.nearShown[1] || false)
      color: "#ffdcb0"
      brightness: 0.35
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 300
    }
    //  The hull's floodlight over the closed circuit camera (user,
    //  2026-11-16: "have a tiny bit of artificial light outside the
    //  rocket"): along the camera's look, reaching the pad below.
    SpotLight {
      position: root.floodPlace
      rotation: root.floodTurn
      visible: root.nearShown.length > 1 && (root.nearShown[1] || false)
      color: "#fff3e0"
      brightness: 4.0
      coneAngle: 75
      innerConeAngle: 35
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 400
    }
    PointLight {
      position: root.lampLight
      visible: root.nearShown.length > 1 && (root.nearShown[1] || false)
      color: "#ffcf8a"
      brightness: 1.8
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 3500
    }
    PointLight {
      position: root.candleLight
      visible: root.nearShown.length > 1 && (root.nearShown[1] || false)
      color: "#ffa850"
      brightness: 0.9 * root.candleGlow
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 20000
    }
    PointLight {
      position: root.globeLight
      visible: root.nearShown.length > 1 && (root.nearShown[1] || false)
      color: "#cfe4ff"
      brightness: 0.12
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 60000
    }
    PointLight {
      position: root.panelLamp
      visible: root.nearShown.length > 1 && (root.nearShown[1] || false)
      color: "#fff6e8"
      brightness: 0.45
      constantFade: 1.0
      linearFade: 0.0
      quadraticFade: 20000
    }
    Model {
      geometry: root.paperGeometry
      visible: root.paperGeometry !== null
      position: root.nearPlaces[1] || Qt.vector3d(0, 0, 0)
      rotation: root.nearTurns[1] || Qt.quaternion(1, 0, 0, 0)
      materials: PrincipledMaterial {
        roughness: 0.9
        cullMode: Material.NoCulling
        baseColorMap: Texture {
          generateMipmaps: true
          mipFilter: Texture.Linear
          sourceItem: Canvas {
            id: paperCanvas
            width: root.paperLayout ? root.paperLayout.width : 1
            height: root.paperLayout ? root.paperLayout.height : 1
            onPaint: {
              var ctx = getContext("2d")
              var at = root.paperLayout
              ctx.fillStyle = "#f4efe0"
              ctx.fillRect(0, 0, width, height)
              if (!at) return
              var foot = height - at.foot
              ctx.fillStyle = "#dfeccf"
              for (var bar = 0; foot - bar * at.line > -at.line;
                   bar += 2 * at.band)
                ctx.fillRect(0, foot - (bar + at.band - 0.2) * at.line,
                             width, at.band * at.line)
              ctx.font = "bold " + at.font + "px '" + root.paperFont + "'"
              ctx.fillStyle = "#1c1a24"
              var y = foot
              ctx.fillText(root.paperTyping, at.margin, y)
              var lines = root.paperLines
              for (var k = lines.length - 1; k >= 0; --k) {
                y -= at.line
                if (y < 0) break
                ctx.fillText(lines[k], at.margin, y)
              }
            }
          }
        }
      }
    }
    Model {
      geometry: root.readoutGeometry
      visible: root.readoutGeometry !== null
      position: root.nearPlaces[1] || Qt.vector3d(0, 0, 0)
      rotation: root.nearTurns[1] || Qt.quaternion(1, 0, 0, 0)
      materials: PrincipledMaterial {
        lighting: PrincipledMaterial.NoLighting
        cullMode: Material.NoCulling
        baseColorMap: Texture {
          generateMipmaps: true
          mipFilter: Texture.Linear
          sourceItem: Canvas {
            id: readoutCanvas
            width: root.readoutLayout ? root.readoutLayout.width : 1
            height: root.readoutLayout ? root.readoutLayout.height : 1
            onPaint: {
              var ctx = getContext("2d")
              var at = root.readoutLayout
              ctx.fillStyle = "#0a0806"
              ctx.fillRect(0, 0, width, height)
              if (!at) return
              ctx.fillStyle = "#1a1006"
              ctx.fillRect(0, 0, width, at.status)
              var said = root.readoutStatus
              ctx.font = "bold " + Math.round(Math.min(
                0.6 * at.status, 0.94 * width / (0.6 * Math.max(
                  16, said.length)))) + "px '" + root.paperFont + "'"
              ctx.textBaseline = "middle"
              //  The glow a wide faint stroke under the letters: the
              //  Canvas's 'shadowBlur' is blurred in software, each
              //  letter, and took seconds a paint.
              ctx.lineJoin = "round"
              ctx.strokeStyle = "rgba(255, 138, 28, 0.3)"
              ctx.lineWidth = 0.08 * at.status
              ctx.strokeText(said, 0.03 * at.status, 0.54 * at.status)
              ctx.fillStyle = "#ffb63c"
              ctx.fillText(said, 0.03 * at.status, 0.54 * at.status)
              var top = at.status
              for (var g = 0; g < at.groups.length; ++g) {
                var group = at.groups[g]
                var text = root.readoutRange[g] || ""
                var digits = []
                var marks = []
                for (var c = 0; c < text.length; ++c) {
                  var ch = text.charAt(c)
                  if (ch === "." || ch === ":")
                    marks.push([digits.length, ch])
                  else
                    digits.push(ch)
                }
                var pad = Math.max(0, group.tubes - digits.length)
                while (digits.length < group.tubes) digits.unshift(" ")
                for (var k = 0; k < group.tubes; ++k) {
                  var x = group.from + k * group.tube
                  ctx.fillStyle = "#2a1c14"
                  ctx.strokeStyle = "#5a4636"
                  ctx.lineWidth = 2
                  ctx.beginPath()
                  ctx.roundedRect(x + 3, top + 0.1 * at.range,
                                  group.tube - 6, 0.8 * at.range, 10, 10)
                  ctx.fill()
                  ctx.stroke()
                }
                ctx.font = Math.round(Math.min(0.6 * at.range,
                                               1.45 * group.tube))
                           + "px '" + root.paperFont + "'"
                ctx.textAlign = "center"
                ctx.strokeStyle = "rgba(255, 90, 16, 0.3)"
                ctx.lineWidth = 0.07 * at.range
                for (k = 0; k < group.tubes; ++k)
                  ctx.strokeText(digits[k], group.from + (k + 0.5)
                                 * group.tube, top + 0.52 * at.range)
                ctx.fillStyle = "#ff9a40"
                for (k = 0; k < group.tubes; ++k)
                  ctx.fillText(digits[k], group.from + (k + 0.5)
                               * group.tube, top + 0.52 * at.range)
                for (var m = 0; m < marks.length; ++m) {
                  var mx = group.from + (marks[m][0] + pad) * group.tube
                  var ys = marks[m][1] === "." ? [0.8] : [0.38, 0.66]
                  for (var y = 0; y < ys.length; ++y) {
                    ctx.beginPath()
                    ctx.arc(mx, top + ys[y] * at.range, 0.035 * at.range,
                            0, 2 * Math.PI)
                    ctx.fill()
                    ctx.stroke()
                  }
                }
                ctx.textAlign = "start"
              }
              //  The docking port's numbers under the CCTV: green on
              //  black, a line or two.
              var foot = at.status + at.range
              ctx.fillStyle = "#050806"
              ctx.fillRect(0, foot, width, at.port)
              var lines = root.readoutPort.split("\n")
              var size = Math.round(Math.min(
                0.8 * at.port / Math.max(1, lines.length),
                0.94 * width / (0.6 * Math.max(24, lines[0].length))))
              ctx.font = "bold " + size + "px '" + root.paperFont + "'"
              ctx.textBaseline = "middle"
              ctx.fillStyle = "#9dffb0"
              for (var l = 0; l < lines.length; ++l)
                ctx.fillText(lines[l], 0.04 * at.port, foot + at.port
                             * (l + 0.5) / lines.length)
            }
          }
        }
      }
    }
    Repeater3D {
      model: root.nearParts
      delegate: Model {
        id: nearModel
        required property var modelData
        property bool pictured: (modelData.picture || "") !== ""
        property Texture picture: Texture {
          source: nearModel.modelData.picture || ""
          tilingModeHorizontal: Texture.Repeat
          tilingModeVertical: Texture.Repeat
          generateMipmaps: true
          mipFilter: Texture.Linear
          positionU: (nearModel.modelData.scroll || 0) * root.glintPhase
        }
        geometry: modelData.geometry
        visible: root.nearShown[modelData.slot] || false
        position: root.nearPlaces[modelData.slot] || Qt.vector3d(0, 0, 0)
        rotation: root.nearTurns[modelData.slot] || Qt.quaternion(1, 0, 0, 0)
        property real glow: root.nearGlows[modelData.slot] || 0
        materials: PrincipledMaterial {
          lighting: modelData.unlit ? PrincipledMaterial.NoLighting
                                    : PrincipledMaterial.FragmentLighting
          baseColor: modelData.colour
          baseColorMap: nearModel.pictured ? nearModel.picture : null
          emissiveMap: nearModel.pictured && nearModel.glow > 0
                       ? nearModel.picture : null
          emissiveFactor: Qt.vector3d(nearModel.glow * modelData.emit.r,
                                      nearModel.glow * modelData.emit.g,
                                      nearModel.glow * modelData.emit.b)
          metalness: modelData.metal
          roughness: modelData.rough
          opacity: modelData.opacity
          blendMode: modelData.screen ? PrincipledMaterial.Screen
                                      : PrincipledMaterial.SourceOver
          alphaMode: modelData.masked ? PrincipledMaterial.Mask
                     : modelData.opacity < 1 ? PrincipledMaterial.Blend
                     : PrincipledMaterial.Opaque
          cullMode: modelData.culled ? Material.BackFaceCulling : Material.NoCulling
        }
      }
    }
  }

  View3D {
    id: farView
    importScene: farWorld
    anchors.fill: parent
    visible: !root.mapOpen
    environment: SceneEnvironment {
      backgroundMode: SceneEnvironment.Color
      clearColor: root.skyColour
      antialiasingMode: SceneEnvironment.MSAA
    }
    camera: farCamera
    PerspectiveCamera {
      id: farCamera
      fieldOfView: root.viewField
      rotation: root.cameraTurn
      clipNear: 10
      clipFar: 5e6
    }
    DirectionalLight {
      rotation: root.sunTurn
      brightness: 1.4
    }
  }

  View3D {
    id: nearView
    importScene: nearWorld
    anchors.fill: parent
    visible: !root.mapOpen
    environment: SceneEnvironment {
      backgroundMode: SceneEnvironment.Transparent
      antialiasingMode: SceneEnvironment.MSAA
    }
    camera: nearCamera
    PerspectiveCamera {
      id: nearCamera
      fieldOfView: root.viewField
      rotation: root.cameraTurn
      clipNear: root.nearClip
      clipFar: 3e6
    }
    DirectionalLight {
      rotation: root.sunTurn
      brightness: 1.4 * root.sunShine
    }
    DirectionalLight {
      rotation: root.earthTurn
      brightness: 1.4 * root.earthShine
      color: "#a8bfe6"
    }
    //  The closed circuit monitor's screen, outside 'nearWorld' (the
    //  camera's own views import it: the screen must not show itself).
    //  Its picture: the hull camera's, the far bodies and the near world
    //  from there, each turned black and white by 'cctv.frag' (Qt Quick
    //  3D's own effect: Qt's MultiEffect loads QML while running and
    //  deadlocked against 'App.notify'), scanlines and a vignette over.
    Node {
      eulerRotation.x: -90
      Model {
        geometry: root.screenGeometry
        visible: root.screenGeometry !== null
        position: root.nearPlaces[1] || Qt.vector3d(0, 0, 0)
        rotation: root.nearTurns[1] || Qt.quaternion(1, 0, 0, 0)
        materials: PrincipledMaterial {
          lighting: PrincipledMaterial.NoLighting
          baseColorMap: Texture {
            sourceItem: Item {
              id: cctv
              width: 384
              height: 288
              Item {
                id: cctvViews
                anchors.fill: parent
                View3D {
                  anchors.fill: parent
                  importScene: farWorld
                  environment: SceneEnvironment {
                    backgroundMode: SceneEnvironment.Color
                    clearColor: root.skyColour
                    effects: [cctvFarLook]
                  }
                  Effect {
                    id: cctvFarLook
                    passes: Pass {
                      shaders: Shader {
                        stage: Shader.Fragment
                        shader: "cctv.frag"
                      }
                    }
                  }
                  camera: cctvFarCamera
                  PerspectiveCamera {
                    id: cctvFarCamera
                    rotation: root.cctvTurn
                    fieldOfView: 64
                    clipNear: 10
                    clipFar: 5e6
                  }
                  DirectionalLight {
                    rotation: root.sunTurn
                    brightness: 1.4
                  }
                }
                View3D {
                  anchors.fill: parent
                  importScene: nearWorld
                  environment: SceneEnvironment {
                    backgroundMode: SceneEnvironment.Transparent
                    effects: [cctvNearLook]
                  }
                  Effect {
                    id: cctvNearLook
                    passes: Pass {
                      shaders: Shader {
                        stage: Shader.Fragment
                        shader: "cctv.frag"
                      }
                    }
                  }
                  camera: cctvNearCamera
                  PerspectiveCamera {
                    id: cctvNearCamera
                    position: root.cctvPlace
                    rotation: root.cctvTurn
                    fieldOfView: 64
                    clipNear: 0.1
                    clipFar: 3e6
                  }
                  DirectionalLight {
                    rotation: root.sunTurn
                    brightness: 1.4 * root.sunShine
                  }
                  DirectionalLight {
                    rotation: root.earthTurn
                    brightness: 1.4 * root.earthShine
                    color: "#a8bfe6"
                  }
                }
              }
              Canvas {
                anchors.fill: parent
                onPaint: {
                  var ctx = getContext("2d")
                  ctx.fillStyle = "rgba(0, 0, 0, 0.28)"
                  for (var y = 0; y < height; y += 3)
                    ctx.fillRect(0, y, width, 1)
                  //  The tube's rounded corners (a 1970s set's).
                  ctx.fillStyle = "#050505"
                  var r = 46
                  ctx.beginPath()
                  ctx.rect(0, 0, width, height)
                  ctx.moveTo(r, 0)
                  ctx.arcTo(0, 0, 0, r, r)
                  ctx.lineTo(0, height - r)
                  ctx.arcTo(0, height, r, height, r)
                  ctx.lineTo(width - r, height)
                  ctx.arcTo(width, height, width, height - r, r)
                  ctx.lineTo(width, r)
                  ctx.arcTo(width, 0, width - r, 0, r)
                  ctx.closePath()
                  ctx.fillRule = Qt.OddEvenFill
                  ctx.fill()
                  var glow = ctx.createRadialGradient(
                    width / 2, height / 2, height * 0.3,
                    width / 2, height / 2, height * 0.85)
                  glow.addColorStop(0, "rgba(0, 0, 0, 0)")
                  glow.addColorStop(1, "rgba(0, 0, 0, 0.75)")
                  ctx.fillStyle = glow
                  ctx.fillRect(0, 0, width, height)
                }
              }
              Text {
                x: 34
                y: 20
                text: root.cctvLabel
                color: "#f2f2f2"
                style: Text.Outline
                styleColor: "#000000"
                font.family: "monospace"
                font.pixelSize: 20
                font.bold: true
              }
              Row {
                x: parent.width - width - 34
                y: 20
                spacing: 6
                Rectangle {
                  width: 12
                  height: 12
                  radius: 6
                  anchors.verticalCenter: parent.verticalCenter
                  color: "#ff3030"
                  SequentialAnimation on opacity {
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.1; duration: 600 }
                    NumberAnimation { to: 1.0; duration: 600 }
                  }
                }
                Text {
                  text: "REC"
                  color: "#f2f2f2"
                  style: Text.Outline
                  styleColor: "#000000"
                  font.family: "monospace"
                  font.pixelSize: 20
                  font.bold: true
                }
              }
              Item {
                visible: root.cctvNose
                anchors.fill: parent
                Rectangle {
                  x: parent.width / 2 - 60
                  y: parent.height / 2 - 1
                  width: 120
                  height: 2
                  color: "#d0ffd0"
                  opacity: 0.8
                }
                Rectangle {
                  x: parent.width / 2 - 1
                  y: parent.height / 2 - 60
                  width: 2
                  height: 120
                  color: "#d0ffd0"
                  opacity: 0.8
                }
                Rectangle {
                  anchors.centerIn: parent
                  width: 36
                  height: 36
                  radius: 18
                  color: "transparent"
                  border.color: "#d0ffd0"
                  border.width: 2
                  opacity: 0.8
                }
              }
            }
          }
        }
      }
    }
  }

  View3D {
    id: handView
    anchors.fill: parent
    visible: root.handShown && !root.mapOpen
    environment: SceneEnvironment {
      backgroundMode: SceneEnvironment.Transparent
      antialiasingMode: SceneEnvironment.MSAA
    }
    camera: handCamera
    PerspectiveCamera {
      id: handCamera
      fieldOfView: nearCamera.fieldOfView
      clipNear: 0.01
      clipFar: 10
    }
    DirectionalLight {
      eulerRotation.x: -40
      eulerRotation.y: 25
      brightness: 1.1
      color: "#fff3e4"
    }
    DirectionalLight {
      eulerRotation.x: 30
      eulerRotation.y: 160
      brightness: 0.35
    }
    Node {
      position: root.handShake
      Repeater3D {
        model: root.handParts
        delegate: Model {
          required property var modelData
          geometry: modelData.geometry
          materials: PrincipledMaterial {
            baseColor: modelData.colour
            baseColorMap: modelData.picture !== "" ? handPicture : null
            property Texture handPicture: Texture {
              source: modelData.picture
              generateMipmaps: true
              mipFilter: Texture.Linear
            }
            metalness: modelData.metal
            roughness: modelData.rough
            lighting: modelData.unlit ? PrincipledMaterial.NoLighting
                                      : PrincipledMaterial.FragmentLighting
            alphaMode: modelData.masked ? PrincipledMaterial.Mask
                                        : PrincipledMaterial.Opaque
            cullMode: Material.NoCulling
          }
        }
      }
    }
  }

  View3D {
    id: mapView
    anchors.fill: parent
    visible: root.mapOpen
    environment: SceneEnvironment {
      backgroundMode: SceneEnvironment.Color
      clearColor: "#04060b"
      antialiasingMode: SceneEnvironment.MSAA
    }
    camera: mapCamera
    PerspectiveCamera {
      id: mapCamera
      rotation: root.mapCameraTurn
      clipNear: 0.5
      clipFar: 1e8
    }
    Node {
      eulerRotation.x: -90
      Repeater3D {
        model: root.mapBodies
        delegate: Model {
          required property var modelData
          geometry: modelData.geometry
          position: root.mapPlaces[modelData.slot] || Qt.vector3d(0, 0, 0)
          rotation: root.mapTurns[modelData.slot] || Qt.quaternion(1, 0, 0, 0)
          property real size: root.mapScales[modelData.slot] || 1
          scale: Qt.vector3d(size, size, size)
          materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColorMap: Texture {
              source: modelData.picture
              tilingModeHorizontal: Texture.Repeat
            }
            alphaMode: modelData.ring ? PrincipledMaterial.Blend
                                      : PrincipledMaterial.Opaque
            cullMode: modelData.ring ? Material.NoCulling : Material.BackFaceCulling
          }
        }
      }
      Repeater3D {
        model: root.mapLines
        delegate: Model {
          required property var modelData
          geometry: modelData.geometry
          position: root.linePlaces[modelData.slot] || Qt.vector3d(0, 0, 0)
          property real size: root.lineScales[modelData.slot] || 1
          scale: Qt.vector3d(size, size, size)
          materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColor: modelData.colour
          }
        }
      }
    }
  }

  Repeater {
    model: root.mapOpen ? root.marks : []
    delegate: Item {
      required property var modelData
      x: modelData.x
      y: modelData.y
      Rectangle {
        width: 7
        height: 7
        radius: 3.5
        x: -3.5
        y: -3.5
        color: modelData.colour
      }
      Text {
        x: 8
        y: -8 + 16 * modelData.line
        text: modelData.text
        color: modelData.colour
        font.pixelSize: 14
        font.family: "monospace"
        style: Text.Outline
        styleColor: "#000000"
      }
    }
  }

  Item {
    id: navball
    objectName: "navball"
    visible: root.navShown && !root.mapOpen && !root.cockpitOn
    width: 2 * root.navRadius + 24
    height: 2 * root.navRadius + 58
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.rightMargin: 24
    anchors.bottomMargin: 30
    Text {
      anchors.horizontalCenter: parent.horizontalCenter
      y: 0
      text: "PITCH " + Math.round(root.navPitch) + "\u00b0   HDG "
            + ("00" + Math.round(root.navHeading) % 360).slice(-3)
            + "\u00b0   " + root.navKind.toUpperCase()
      color: "#e8f0ff"
      font.pixelSize: 13
      font.bold: true
      font.family: "monospace"
      style: Text.Outline
      styleColor: "#000000"
    }
    Rectangle {
      id: bezel
      x: 0
      y: 24
      width: parent.width
      height: width
      radius: width / 2
      color: "#1b2027"
      border.color: "#4a5563"
      border.width: 3
      View3D {
        anchors.fill: parent
        anchors.margins: 12
        environment: SceneEnvironment {
          backgroundMode: SceneEnvironment.Transparent
          antialiasingMode: SceneEnvironment.MSAA
        }
        camera: navCamera
        OrthographicCamera {
          id: navCamera
          z: 600
          clipNear: 1
          clipFar: 2000
        }
        Model {
          geometry: root.navGeometry
          visible: root.navGeometry !== null
          rotation: root.navTurn
          scale: Qt.vector3d(root.navRadius, root.navRadius, root.navRadius)
          materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            cullMode: Material.NoCulling
            baseColorMap: Texture {
              source: root.navPicture
              tilingModeHorizontal: Texture.Repeat
            }
          }
        }
      }
      Repeater {
        model: root.navMarks
        delegate: Item {
          required property var modelData
          x: bezel.width / 2 + modelData.x
          y: bezel.height / 2 + modelData.y
          Rectangle {
            visible: modelData.kind !== "aim"
            x: -11
            y: -11
            width: 22
            height: 22
            radius: 11
            color: "transparent"
            border.color: "#b6ff5e"
            border.width: 3
          }
          Rectangle {
            visible: modelData.kind === "prograde"
            x: -2
            y: -2
            width: 4
            height: 4
            radius: 2
            color: "#b6ff5e"
          }
          Rectangle {
            visible: modelData.kind === "retrograde"
            x: -9
            y: -1.5
            width: 18
            height: 3
            rotation: 45
            color: "#b6ff5e"
          }
          Rectangle {
            visible: modelData.kind === "retrograde"
            x: -9
            y: -1.5
            width: 18
            height: 3
            rotation: -45
            color: "#b6ff5e"
          }
          Rectangle {
            visible: modelData.kind === "aim"
            x: -9
            y: -9
            width: 18
            height: 18
            rotation: 45
            color: "transparent"
            border.color: "#ff6bd6"
            border.width: 3
          }
        }
      }
      Rectangle {
        x: bezel.width / 2 - 26
        y: bezel.height / 2 - 1.5
        width: 18
        height: 3
        color: "#ffd23f"
      }
      Rectangle {
        x: bezel.width / 2 + 8
        y: bezel.height / 2 - 1.5
        width: 18
        height: 3
        color: "#ffd23f"
      }
      Rectangle {
        x: bezel.width / 2 - 3
        y: bezel.height / 2 - 3
        width: 6
        height: 6
        radius: 3
        color: "#ffd23f"
      }
    }
  }

  Rectangle {
    id: board
    objectName: "board"
    visible: !root.cockpitOn || root.mapOpen
    anchors.left: parent.left
    anchors.bottom: parent.bottom
    anchors.leftMargin: 12
    anchors.bottomMargin: 30
    width: boardRow.implicitWidth + 24
    height: boardRow.implicitHeight + 20
    radius: 10
    color: "#d8141a22"
    border.color: "#3a4552"
    border.width: 1.5
    Grid {
      id: boardRow
      x: 12
      y: 10
      columns: 2
      columnSpacing: 18
      rowSpacing: 8
      Group {
        title: "ENGINE"
        Item {
          width: 112
          height: 52
          Row {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 2 - root.bob
            spacing: 3
            KeyCap { name: "+" }
            KeyCap { name: "\u2212" }
          }
          Rectangle {
            y: 24
            width: parent.width
            height: 28
            radius: 7
            color: "#262b33"
            border.color: "#3c4450"
            border.width: 1.5
            Rectangle {
              x: 3
              y: 3
              height: parent.height - 6
              width: (parent.width - 6) * root.boardThrottle
              radius: 5
              color: "#ffb347"
            }
            Text {
              anchors.centerIn: parent
              text: "Throttle " + Math.round(100 * root.boardThrottle) + " %"
              color: "#f2f5f8"
              font.pixelSize: 13
              font.bold: true
              style: Text.Outline
              styleColor: "#000000"
            }
          }
        }
        Lamp { label: "Full"; keys: ["Z"]; action: "full"; tint: "#ffb347"
               lit: root.boardThrottle >= 0.999 }
        Lamp { label: "Limit: " + root.boardLimit; keys: ["Y", "U"]
               action: "limit"; tint: "#ffb347"
               lit: root.boardLimit !== "4 g" }
        Lamp { label: "Cut"; keys: ["X"]; action: "cut"; tint: "#ffb347"
               lit: root.boardThrottle <= 0.0 }
        Lamp { label: lit ? "Launched" : "Launch"; keys: ["Space"]
               action: "launch"; tint: "#ff6a50"; lit: root.boardLaunched }
      }
      Group {
        title: "ASSISTS"
        Lamp { label: "Hold: " + (lit ? "on" : "off"); keys: ["T"]
               action: "hold"; lit: root.boardMode === "hold" }
        Lamp { label: "Prograde: " + (lit ? "on" : "off"); keys: ["F"]
               action: "prograde"; lit: root.boardMode === "prograde" }
        Lamp { label: "Retrograde: " + (lit ? "on" : "off"); keys: ["R"]
               action: "retrograde"; lit: root.boardMode === "retrograde" }
        Lamp { label: "Aim: " + (lit ? "on" : "off")
               keys: ["W", "S", "A", "D"]; action: "aim"
               tint: "#ff8be0"; lit: root.boardMode === "aim" }
        Lamp { label: "Roll"; keys: ["Q"]; action: ""
               tint: "#8fd3ff"
               lit: root.boardHeld.indexOf("|Q|") >= 0 }
      }
      Group {
        title: "TIME"
        Lamp { label: "Warp: " + root.boardWarp + "x"; keys: [",", "."]
               action: "faster"; tint: "#8fd3ff"; lit: root.boardWarp > 1 }
        Lamp { label: "Real time"; keys: ["/"]; action: "stop"
               tint: "#8fd3ff"; lit: root.boardWarp === 1 }
        Lamp { label: "To Ap: " + (lit ? "on" : "off"); keys: ["G"]
               action: "toAp"; tint: "#8fd3ff"; lit: root.boardToAp }
        Lamp { label: "Warp to action"; keys: ["Enter"]; action: "action"
               tint: "#c59bff"; lit: root.boardAction }
      }
      Group {
        title: "AUTOPILOT"
        Lamp { label: "Orbit"; keys: ["J"]; action: "ap orbit"
               tint: "#c59bff"; lit: root.boardApMode === "orbit" }
        Lamp { label: "Rendezvous"; keys: ["H"]; action: "ap rendezvous"
               tint: "#c59bff"; lit: root.boardApMode === "rendezvous" }
        Lamp { label: "Dock"; keys: ["N"]; action: "ap dock"
               tint: "#c59bff"; lit: root.boardApMode === "dock" }
        Lamp { label: root.boardPhase; keys: ["C"]; action: "engage"
               tint: "#7dff9a"; lit: root.boardEngaged }
        Lamp { label: "Orbit " + root.boardTarget; keys: ["[", "]"]
               action: "higher"; tint: "#c59bff"; lit: false }
      }
      Group {
        title: "MANUAL DOCKING"
        Lamp { label: "Match: " + (lit ? "on" : "off"); keys: ["L"]
               action: "match"; tint: "#7dff9a"; lit: root.boardMatch }
        Lamp { label: "Thrusters"
               keys: ["\u2191", "\u2193", "\u2190", "\u2192", "PgUp",
                      "PgDn"]
               action: ""; tint: "#8fd3ff"; lit: root.boardThrusting }
        Lamp { label: root.boardNose ? "Cam: nose" : "Cam: aft"
               keys: ["K"]; action: "camera"; tint: "#e8ecf0"
               lit: root.boardNose }
        Lamp { label: "Undock"; keys: ["Del"]; action: "undock"
               tint: "#e8ecf0"; lit: false }
      }
      Group {
        title: "VIEW"
        Lamp { label: "Map: " + (lit ? "on" : "off"); keys: ["M"]
               action: "map"; tint: "#e8ecf0"; lit: root.boardMap }
        Lamp { label: "Back to pad"; keys: ["\u232b"]; action: "pad"
               tint: "#e8ecf0"; lit: false }
        Lamp { label: root.boardUp ? "Up: sit down" : "Seated: get up"
               keys: root.boardUp ? ["B"] : ["Shift"]; action: "buckle"
               tint: "#ffd27a"; lit: root.boardUp }
      }
    }
  }

  Item {
    visible: root.cockpitOn && !root.mapOpen
    anchors.fill: parent
    Rectangle {
      anchors.centerIn: parent
      width: 6
      height: 6
      radius: 3
      color: "#e8eef6"
      border.color: "#000000"
      border.width: 1
    }
    Row {
      visible: root.promptName !== ""
      anchors.horizontalCenter: parent.horizontalCenter
      y: parent.height / 2 + 22
      spacing: 8
      Rectangle {
        visible: root.promptKey !== ""
        width: Math.max(30, promptKeyText.implicitWidth + 14)
        height: 30
        radius: 5
        color: "#e8ecf0"
        border.color: "#8a949e"
        border.width: 2
        Text {
          id: promptKeyText
          anchors.centerIn: parent
          text: root.promptKey
          color: "#181c22"
          font.pixelSize: 16
          font.bold: true
        }
      }
      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: root.promptName
        color: "#e8ecf0"
        font.pixelSize: 16
        font.bold: true
        style: Text.Outline
        styleColor: "#000000"
      }
    }
  }

  Rectangle {
    visible: root.questRows.length > 0 && !root.mapOpen
             && root.scopeShown < 0.5
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.margins: 12
    width: questColumn.width + 20
    height: questColumn.height + 16
    color: "#90000000"
    radius: 6
    Column {
      id: questColumn
      x: 10
      y: 8
      spacing: 3
      Text {
        text: "QUEST"
        color: "#ffd77a"
        font.pixelSize: 14
        font.bold: true
      }
      Repeater {
        model: root.questRows
        delegate: Text {
          required property var modelData
          text: (modelData.done ? "\u2611  " : "\u2610  ") + modelData.text
          color: modelData.done ? "#7f8a96"
                                : modelData.current ? "#ffffff" : "#b8c2cc"
          font.pixelSize: 13
          font.bold: modelData.current
          font.strikeout: modelData.done
        }
      }
    }
  }

  Rectangle {
    visible: root.readout !== "" && (!root.cockpitOn || root.mapOpen)
    x: 12
    y: 12
    width: readoutText.width + 20
    height: readoutText.height + 16
    color: "#a0000000"
    radius: 6
    Text {
      id: readoutText
      x: 10
      y: 8
      text: root.readout
      color: "#e8f0ff"
      font.pixelSize: 15
      font.family: "monospace"
    }
  }

  Text {
    anchors.bottom: parent.bottom
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottomMargin: 10
    visible: !root.cockpitOn || root.mapOpen
    text: root.hint
    color: "#e8f0ff"
    font.pixelSize: 14
    style: Text.Outline
    styleColor: "#000000"
  }

  Repeater {
    model: root.lightPoints.length
    Item {
      property vector3d at: nearView.mapFrom3DScene(root.lightPoints[index])
      property real hue: index < root.lightHues.length
                         ? root.lightHues[index] : -1
      property color shade: hue < 0 ? "#ffd9a0"
                                    : Qt.hsva((hue + root.glintPhase) % 1.0,
                                              1.0, 1.0, 1.0)
      visible: !root.mapOpen && at.z > 0
      x: at.x
      y: at.y
      Rectangle {
        anchors.centerIn: parent
        width: 12
        height: 12
        radius: 6
        color: parent.shade
        opacity: 0.3
      }
      Rectangle {
        anchors.centerIn: parent
        width: 4
        height: 4
        radius: 2
        color: parent.shade
      }
    }
  }

  Rectangle {
    anchors.fill: parent
    visible: root.hurtShown > 0.01 && !root.mapOpen
    color: "#c00000"
    opacity: 0.35 * root.hurtShown
  }

  Column {
    visible: !root.mapOpen
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    anchors.bottomMargin: (board.visible ? board.height + 40 : 40)
                          + (hotbar.visible ? 54 : 0)
    spacing: 3
    Row {
      spacing: 36
      Row {
        spacing: 2
        Repeater {
          model: 10
          Canvas {
            width: 20
            height: 20
            property int fill: Math.max(0, Math.min(2, Math.ceil(
              root.health) - 2 * index))
            y: root.health <= 4 ? 2.5 * Math.sin(2 * Math.PI * 6
                                                 * root.glintPhase
                                                 + 1.7 * index) : 0
            onFillChanged: requestPaint()
            onPaint: root.paintIcon(getContext("2d"), width,
                                    root.heartPixels, fill, -1,
                                    "#e01c1c", "#ff9a9a", "#3a2626")
          }
        }
      }
      Row {
        spacing: 2
        layoutDirection: Qt.RightToLeft
        Repeater {
          model: 10
          Canvas {
            width: 20
            height: 20
            property int fill: Math.max(0, Math.min(2, Math.ceil(
              root.food) - 2 * index))
            onFillChanged: requestPaint()
            onPaint: root.paintIcon(getContext("2d"), width,
                                    root.drumstickPixels, fill, 1,
                                    "#b8642a", "#e2a064", "#3a3026")
          }
        }
      }
    }
    Item {
      width: parent.width
      height: 4
      Rectangle {
        visible: root.eatingShown > 0
        anchors.right: parent.right
        width: 218 * root.eatingShown
        height: 4
        radius: 2
        color: "#e2a064"
      }
    }
  }

  //  A slot as Minecraft draws it: grey, sunk, the item's icon (pixels
  //  unsmoothed), its count when more than one.
  component ItemSlot: Rectangle {
    id: slotBox
    property var row: ({kind: "", count: 0, title: ""})
    property bool chosen: false
    width: 48
    height: 48
    color: "#8b8b8b"
    border.width: chosen ? 4 : 2
    border.color: chosen ? "#ffffff" : "#373737"
    Image {
      anchors.centerIn: parent
      width: 40
      height: 40
      visible: slotBox.row.kind !== ""
      source: slotBox.row.kind !== "" ? (root.itemIcons[slotBox.row.kind]
                                         || "") : ""
      smooth: false
    }
    Text {
      anchors.right: parent.right
      anchors.bottom: parent.bottom
      anchors.margins: 3
      visible: slotBox.row.count > 1
      text: slotBox.row.count
      color: "#ffffff"
      font.pixelSize: 15
      font.bold: true
      style: Text.Outline
      styleColor: "#3f3f3f"
    }
  }

  //  The telescope's round edge (looking through it).
  Canvas {
    id: scopeEdge
    anchors.fill: parent
    visible: root.scopeShown > 0.01 && !root.mapOpen
    opacity: root.scopeShown
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
      var ctx = getContext("2d")
      ctx.reset()
      var r = 0.47 * Math.min(width, height)
      ctx.fillStyle = "#000000"
      ctx.beginPath()
      ctx.rect(0, 0, width, height)
      ctx.arc(width / 2, height / 2, r, 0, 2 * Math.PI, true)
      ctx.fill()
      ctx.strokeStyle = "#3a2c14"
      ctx.lineWidth = 6
      ctx.beginPath()
      ctx.arc(width / 2, height / 2, r, 0, 2 * Math.PI)
      ctx.stroke()
    }
  }

  //  The hotbar (keys 1 to 9, the wheel) and the held item's name.
  Column {
    id: hotbar
    visible: root.hotbarShown && !root.mapOpen && root.deathText === ""
             && root.inventoryRows.length > 0
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    anchors.bottomMargin: board.visible ? board.height + 16 : 8
    spacing: 4
    Text {
      anchors.horizontalCenter: parent.horizontalCenter
      opacity: root.heldFade
      text: root.inventoryRows.length > root.hotbarSelected
            ? root.inventoryRows[root.hotbarSelected].title : ""
      color: "#ffffff"
      font.pixelSize: 16
      font.bold: true
      style: Text.Outline
      styleColor: "#000000"
    }
    Row {
      spacing: 0
      Repeater {
        model: 9
        ItemSlot {
          required property int index
          row: root.inventoryRows.length > index ? root.inventoryRows[index]
                                                 : ({kind: "", count: 0})
          chosen: index === root.hotbarSelected
          opacity: 0.92
        }
      }
    }
  }

  //  The inventory (Tab): three rows over the hotbar's, as Minecraft's;
  //  a click picks a stack up or lays it down (the right button: half,
  //  or one), the stack carried follows the pointer.
  Rectangle {
    id: inventoryPanel
    visible: root.inventoryOpen && !root.mapOpen
    anchors.fill: parent
    color: "#90000000"
    MouseArea {
      anchors.fill: parent
      hoverEnabled: true
      acceptedButtons: Qt.NoButton
      onPositionChanged: (mouse) => {
        root.pointerX = mouse.x
        root.pointerY = mouse.y
      }
    }
    Rectangle {
      anchors.centerIn: parent
      width: grid.width + 32
      height: grid.height + 72
      color: "#c6c6c6"
      border.width: 3
      border.color: "#555555"
      radius: 4
      Text {
        x: 16
        y: 10
        text: "Inventory"
        color: "#404040"
        font.pixelSize: 18
        font.bold: true
      }
      Column {
        id: grid
        x: 16
        y: 40
        spacing: 12
        Grid {
          columns: 9
          Repeater {
            model: 27
            ItemSlot {
              required property int index
              row: root.inventoryRows.length > index + 9
                   ? root.inventoryRows[index + 9] : ({kind: "", count: 0})
              MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onEntered: root.hoverTitle = parent.row.title || ""
                onExited: root.hoverTitle = ""
                onPressed: (mouse) => root.inventoryClicked(
                  index + 9, mouse.button === Qt.RightButton)
              }
            }
          }
        }
        Row {
          Repeater {
            model: 9
            ItemSlot {
              required property int index
              row: root.inventoryRows.length > index
                   ? root.inventoryRows[index] : ({kind: "", count: 0})
              chosen: index === root.hotbarSelected
              MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onEntered: root.hoverTitle = parent.row.title || ""
                onExited: root.hoverTitle = ""
                onPressed: (mouse) => root.inventoryClicked(
                  index, mouse.button === Qt.RightButton)
              }
            }
          }
        }
        Text {
          text: root.hoverTitle !== "" ? root.hoverTitle
                : "Click: pick up or lay down   right click: half, or one"
                  + "   Tab: close"
          color: "#404040"
          font.pixelSize: 14
        }
      }
    }
    Image {
      visible: root.carriedRow.kind !== ""
      x: root.pointerX - 20
      y: root.pointerY - 20
      width: 40
      height: 40
      source: root.carriedRow.kind !== "" ? (root.itemIcons[
        root.carriedRow.kind] || "") : ""
      smooth: false
      Text {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: root.carriedRow.count > 1
        text: root.carriedRow.count
        color: "#ffffff"
        font.pixelSize: 15
        font.bold: true
        style: Text.Outline
        styleColor: "#3f3f3f"
      }
    }
  }

  Rectangle {
    anchors.fill: parent
    visible: root.manualShown
    color: "#c8000000"
    Image {
      anchors.centerIn: parent
      height: 0.92 * parent.height
      width: height * 1024 / 1448
      source: root.manualPicture
      smooth: true
      mipmap: true
    }
    Text {
      anchors.bottom: parent.bottom
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottomMargin: 8
      text: "E or Esc: put it back"
      color: "#ffffff"
      font.pixelSize: 15
      style: Text.Outline
      styleColor: "#000000"
    }
  }

  //  Asger asleep (user, 2026-11-17: "key_E into bed to advance the time
  //  to morning if it is dark"): the view darkens and lightens again
  Rectangle {
    anchors.fill: parent
    visible: root.sleepShade > 0
    opacity: root.sleepShade
    color: "#000000"
    Text {
      anchors.centerIn: parent
      text: "Zzz"
      color: "#c8c8e8"
      font.pixelSize: 40
      font.italic: true
    }
  }

  Rectangle {
    anchors.fill: parent
    visible: root.deathText !== ""
    color: "#a0580000"
    Column {
      anchors.centerIn: parent
      spacing: 16
      Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: "Asger died"
        color: "#ffffff"
        font.pixelSize: 56
        font.bold: true
        style: Text.Outline
        styleColor: "#000000"
      }
      Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: root.deathText
        color: "#ffe2e2"
        font.pixelSize: 24
        style: Text.Outline
        styleColor: "#000000"
      }
      Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: "B: wake up in the chair"
        color: "#ffffff"
        font.pixelSize: 18
        style: Text.Outline
        styleColor: "#000000"
      }
    }
  }

  Text {
    anchors.centerIn: parent
    visible: root.status !== ""
    text: root.status
    color: "#ffffff"
    font.pixelSize: 24
    horizontalAlignment: Text.AlignHCenter
    style: Text.Outline
    styleColor: "#000000"
  }
}
