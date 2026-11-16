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
  //  The ground under the eye: its mesh (a cap, the body's own axes), its
  //  body's picture, its place and turn, whether it shows
  property var capGeometry: null
  property string capPicture: ""
  property vector3d capPlace: Qt.vector3d(0, 0, 0)
  property quaternion capTurn: Qt.quaternion(1, 0, 0, 0)
  property bool capShown: false
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
  property bool boardAscent: false
  property string boardPhase: ""
  property string boardTarget: ""
  property bool boardMap: false
  property string boardHeld: "|"
  signal boardPicked(string action)
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

  View3D {
    id: farView
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
      rotation: root.cameraTurn
      clipNear: 10
      clipFar: 5e6
    }
    DirectionalLight {
      rotation: root.sunTurn
      brightness: 1.4
    }
    Node {
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
  }

  View3D {
    id: nearView
    anchors.fill: parent
    visible: !root.mapOpen
    environment: SceneEnvironment {
      backgroundMode: SceneEnvironment.Transparent
      antialiasingMode: SceneEnvironment.MSAA
    }
    camera: nearCamera
    PerspectiveCamera {
      id: nearCamera
      rotation: root.cameraTurn
      clipNear: 0.3
      clipFar: 3e6
    }
    DirectionalLight {
      rotation: root.sunTurn
      brightness: 1.4
    }
    Node {
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
      Repeater3D {
        model: root.nearParts
        delegate: Model {
          id: nearModel
          required property var modelData
          property bool pictured: (modelData.picture || "") !== ""
          property Texture picture: Texture {
            source: nearModel.modelData.picture || ""
            tilingModeHorizontal: Texture.Repeat
          }
          geometry: modelData.geometry
          visible: root.nearShown[modelData.slot] || false
          position: root.nearPlaces[modelData.slot] || Qt.vector3d(0, 0, 0)
          rotation: root.nearTurns[modelData.slot] || Qt.quaternion(1, 0, 0, 0)
          materials: PrincipledMaterial {
            baseColor: modelData.colour
            baseColorMap: nearModel.pictured ? nearModel.picture : null
            metalness: modelData.metal
            roughness: modelData.rough
            cullMode: modelData.culled ? Material.BackFaceCulling : Material.NoCulling
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
        y: -8
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
    visible: root.navShown && !root.mapOpen
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
            KeyCap { name: "Shift" }
            KeyCap { name: "Ctrl" }
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
        Lamp { label: "Cut"; keys: ["X"]; action: "cut"; tint: "#ffb347"
               lit: root.boardThrottle <= 0.0 }
      }
      Group {
        title: "AUTOPILOT"
        Lamp { label: "Hold: " + (lit ? "on" : "off"); keys: ["T"]
               action: "hold"; lit: root.boardMode === "hold" }
        Lamp { label: "Prograde: " + (lit ? "on" : "off"); keys: ["F"]
               action: "prograde"; lit: root.boardMode === "prograde" }
        Lamp { label: "Retrograde: " + (lit ? "on" : "off"); keys: ["R"]
               action: "retrograde"; lit: root.boardMode === "retrograde" }
        Lamp { label: "Aim: " + (lit ? "on" : "off")
               keys: ["W", "S", "A", "D"]; action: "aim"
               tint: "#ff8be0"; lit: root.boardMode === "aim" }
        Lamp { label: "Roll"; keys: ["Q", "E"]; action: ""
               tint: "#8fd3ff"
               lit: root.boardHeld.indexOf("|Q|") >= 0
                    || root.boardHeld.indexOf("|E|") >= 0 }
      }
      Group {
        title: "TIME"
        Lamp { label: "Warp: " + root.boardWarp + "x"; keys: [",", "."]
               action: "faster"; tint: "#8fd3ff"; lit: root.boardWarp > 1 }
        Lamp { label: "Real time"; keys: ["/"]; action: "stop"
               tint: "#8fd3ff"; lit: root.boardWarp === 1 }
        Lamp { label: "To Ap: " + (lit ? "on" : "off"); keys: ["G"]
               action: "toAp"; tint: "#8fd3ff"; lit: root.boardToAp }
      }
      Group {
        title: "ASCENT GUIDANCE"
        Lamp { label: "Ascent: " + (lit ? "on" : "off"); keys: ["J"]
               action: "ascent"; tint: "#c59bff"; lit: root.boardAscent }
        Lamp { label: "Orbit " + root.boardTarget; keys: ["[", "]"]
               action: "higher"; tint: "#c59bff"; lit: false }
        Lamp { label: root.boardPhase === "" ? "\u2014" : root.boardPhase
               keys: []; action: ""; tint: "#c59bff"
               lit: root.boardAscent }
      }
      Group {
        title: "VIEW"
        Lamp { label: "Map: " + (lit ? "on" : "off"); keys: ["M"]
               action: "map"; tint: "#e8ecf0"; lit: root.boardMap }
        Lamp { label: "Back to pad"; keys: ["\u232b"]; action: "pad"
               tint: "#e8ecf0"; lit: false }
      }
    }
  }

  Rectangle {
    visible: root.readout !== ""
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
    text: root.hint
    color: "#e8f0ff"
    font.pixelSize: 14
    style: Text.Outline
    styleColor: "#000000"
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
