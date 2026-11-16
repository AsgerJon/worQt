//  sandbox.qml draws a sandbox world for the 'Viewport', by the GPU (Qt
//  Quick 3D): the world's fixtures as they are, its bodies placed and
//  turned as they are, the sun with its shadows and the sky's light,
//  and over it a cross in the middle and a line of help. Python sets
//  its properties; nothing here moves anything on its own.
//
//  The world is in metres with z up; the scene in centimetres with y
//  up. The node 'world' turns and scales one into the other, so what
//  is in it is given in the world's own terms; the camera and the
//  lights are the scene's.
//
//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen

import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick3D.AssetUtils

Item {
  id: root

  //  What is drawn fixed, each {geometry, colour, metal, rough}: a mesh
  //  in the world as it is
  property var fixtures: []
  //  The bodies drawn, each {geometry, body, colour, metal, rough}: a
  //  mesh about its body's centre; each body's place (m) and turn in the
  //  world, by its index
  property var bodies: []
  property var places: []
  property var turns: []
  //  The camera (the scene's: cm, y up), its near cut, cm; the sun's
  //  and the sky light's turns (each shining along its own -z)
  property vector3d cameraPlace: Qt.vector3d(0, 0, 0)
  property quaternion cameraTurn: Qt.quaternion(1, 0, 0, 0)
  property real cameraNear: 5
  property quaternion sunTurn: Qt.quaternion(1, 0, 0, 0)
  property quaternion skyTurn: Qt.quaternion(1, 0, 0, 0)
  //  The light every face gets from all round, lit or in shade
  property color ambient: "#4c5158"
  //  The sun's shadow map: its size (a Light.ShadowMapQuality), how far
  //  from the camera it reaches (cm), whether its texels are locked to
  //  the world. Ultra (4096 px) within 50 m, unlocked: the user's pick
  //  (2026-11-15) of previews/render_sandbox.py's renders; 1024 px over
  //  200 m drew the hard edges as coarse, jagged steps
  property int shadowQuality: Light.ShadowMapQualityUltra
  property real shadowFar: 5000
  property bool lockTexels: false
  //  A cross in the middle, and a line of help along the bottom (none:
  //  empty)
  property bool crosshair: false
  property string hint: ""
  //  How things run, in the top left corner, and what is wrong with it
  //  in orange ('': nothing)
  property string debug: ""
  property string debugWarning: ""
  //  The body the tool in hand points at and the one it holds (-1:
  //  none), tinted; the hotbar: each slot's tool's name ('' empty), and
  //  the slot in hand
  property int pointedBody: -1
  property int heldBody: -1
  property color pointedTint: "#ebd796"
  property color heldTint: "#78cde6"
  property var hotbar: []
  property var hotbarIcons: []
  property int slot: 0
  //  The tool in the hands and the arm holding it, fixed to the camera
  //  (cm, the camera's own axes): boxes, each {position, scale (m: a
  //  #Cube is 100 cm), rotation, colour}, and the words painted on it
  property var heldParts: []
  property string heldLabel: ""
  property vector3d heldLabelPlace: Qt.vector3d(0, 0, 0)
  property real heldLabelTurn: 0
  property color heldLabelColour: "white"
  property real heldLabelHeight: 4
  //  A glTF shown in the hands ('': none): its file's url, where its
  //  origin is (cm, the camera's own axes), its turn (degrees about x,
  //  y, z) and its scale (cm a unit of its own); it casts no shadow
  //  The tool's glow while it holds something (user, 2026-11-16: "a
  //  light thing should indicate that the gun has it"): lit or not,
  //  where (cm, the camera's own axes), its colour
  property bool heldGlow: false
  property vector3d glowPlace: Qt.vector3d(0, 0, 0)
  property color glowColour: "#ffb44c"
  property string heldModel: ""
  property vector3d heldModelPlace: Qt.vector3d(0, 0, 0)
  property vector3d heldModelTurn: Qt.vector3d(0, 0, 0)
  property real heldModelScale: 1
  //  The E menu, drawn here in the scene's own window (user, 2026-11-16:
  //  "I click on another window in wayland, the previous window don't
  //  get to take the keyboard focus back!": a menu of its own window,
  //  a popup, grabbed the keyboard and handed the focus back to the
  //  scene as it closed): open or not, its title, what it reads, its
  //  buttons ({text, key}) and the world's under them; a click on one
  //  says its key ('menuPicked'), a click beside it 'close'
  property bool menuOpen: false
  property string menuTitle: ""
  property string menuReadout: ""
  property var menuButtons: []
  property var menuWorld: []
  signal menuPicked(string key)
  //  Where the hands are put against the eyes as the avatar walks, cm
  property vector3d heldOffset: Qt.vector3d(0, 0, 0)
  //  The avatar seen from behind (user, 2026-11-16: "have the TAB button
  //  changes view between first person and chase-third person"): its
  //  figure drawn and the tool before the eyes not. The figure (user,
  //  2026-11-16: "the Avatar should have a skin like in minecraft",
  //  "give it AsgerJon's skin"), in the world's own terms (m, z up): its
  //  skin (a picture's url), where its soles are and its turn; its parts
  //  ({geometry, index, outer, pivot}: each part's block, and its outer
  //  layer's, about the part's pivot) and each part's turn about its
  //  pivot, by index; the right arm's pivot, where its hand holds a tool
  //  along the arm, and the turn from the eyes' frame to the arm's;
  //  whether the hand holds the tool; where the tool's model lies from
  //  its grip (m, the eyes' frame) and its scale (m a unit)
  property bool chased: false
  property string figureSkin: ""
  property vector3d figurePlace: Qt.vector3d(0, 0, 0)
  property quaternion figureTurn: Qt.quaternion(1, 0, 0, 0)
  property var figureParts: []
  property var figureTurns: []
  property vector3d figureHand: Qt.vector3d(0, 0, 0)
  property vector3d figureGrip: Qt.vector3d(0, 0, 0)
  property quaternion figureHanded: Qt.quaternion(1, 0, 0, 0)
  property bool holding: false
  property vector3d handModelPlace: Qt.vector3d(0, 0, 0)
  property real handModelScale: 1
  //  A prompt floating over a place in the scene (cm, y up; user,
  //  2026-11-16: "a floating key_E button should appear with a prompt"):
  //  shown or not, the key on its key cap and what it does
  //  The world's levers ('FourthPeep'), each {place, turn, length}: its
  //  handle's pivot and turn (the world's terms, the handle along its
  //  own z) and how long it is, m
  property var peeps: []
  property bool promptOn: false
  property vector3d promptPlace: Qt.vector3d(0, 0, 0)
  property string promptKey: ""
  property string promptText: ""

  View3D {
    id: view
    anchors.fill: parent
    camera: camera

    environment: ExtendedSceneEnvironment {
      backgroundMode: SceneEnvironment.Color
      clearColor: "#8fb4d8"
      antialiasingMode: SceneEnvironment.MSAA
      antialiasingQuality: SceneEnvironment.Medium
      tonemapMode: SceneEnvironment.TonemapModeFilmic
      ditheringEnabled: true
    }

    PerspectiveCamera {
      id: camera
      position: root.cameraPlace
      rotation: root.cameraTurn
      fieldOfView: 70
      clipNear: root.cameraNear
      clipFar: 300000

      Node {
      position: root.heldOffset
      visible: !root.chased
      Node {
        position: root.glowPlace
        visible: root.heldGlow
        Model {
          source: "#Sphere"
          scale: Qt.vector3d(0.035, 0.035, 0.035)
          castsShadows: false
          receivesShadows: false
          materials: PrincipledMaterial {
            baseColor: root.glowColour
            lighting: PrincipledMaterial.NoLighting
          }
        }
        PointLight {
          id: glowLight
          color: root.glowColour
          brightness: 3
          quadraticFade: 2.0
          castsShadow: false
          SequentialAnimation on brightness {
            running: root.heldGlow
            loops: Animation.Infinite
            NumberAnimation { to: 6; duration: 320 }
            NumberAnimation { to: 3; duration: 320 }
          }
        }
      }
      Node {
        position: root.heldModelPlace
        eulerRotation: root.heldModelTurn
        scale: Qt.vector3d(root.heldModelScale, root.heldModelScale,
                           root.heldModelScale)
        RuntimeLoader {
          id: heldLoader
          source: root.heldModel
          function unshadowed(node) {
            if (node.castsShadows !== undefined) {
              node.castsShadows = false
              node.receivesShadows = false
            }
            for (var i = 0; i < node.children.length; ++i)
              unshadowed(node.children[i])
          }
          onStatusChanged: if (status === RuntimeLoader.Success)
                             unshadowed(heldLoader)
        }
      }
      Repeater3D {
        model: root.heldParts
        delegate: Model {
          required property var modelData
          source: "#Cube"
          position: modelData.position
          scale: modelData.scale
          rotation: modelData.rotation
          castsShadows: false
          receivesShadows: false
          materials: PrincipledMaterial {
            baseColor: modelData.colour
            metalness: 0.0
            roughness: 0.6
          }
        }
      }
      Node {
        visible: root.heldLabel.length > 0
        position: root.heldLabelPlace
        eulerRotation.y: root.heldLabelTurn
        scale: Qt.vector3d(root.heldLabelHeight / 40,
                           root.heldLabelHeight / 40, 1)
        Text {
          x: -width / 2
          y: -height / 2
          text: root.heldLabel
          color: root.heldLabelColour
          font.pixelSize: 40
          font.bold: true
        }
      }
      }
    }

    //  Hard shadows on both lights (user, 2026-11-15: soft shadows'
    //  grain re-rolled whenever the view moved, weird_render.mp4): Qt
    //  turns its soft shadows' few samples by a blue noise fixed to the
    //  screen, and draws a material's shadows with the most samples ANY
    //  light asks for, so the sky light must ask Hard too.
    DirectionalLight {
      rotation: root.sunTurn
      color: "#fff3e0"
      brightness: 1.5
      castsShadow: true
      shadowMapQuality: root.shadowQuality
      softShadowQuality: Light.Hard
      lockShadowmapTexels: root.lockTexels
      shadowFactor: 70
      shadowMapFar: root.shadowFar
      shadowBias: 5
      csmNumSplits: 2
    }
    DirectionalLight {
      rotation: root.skyTurn
      color: "#b8c8e8"
      brightness: 0.45
      softShadowQuality: Light.Hard
      //  Light from all round, on every face, lit or in shade (user,
      //  2026-11-16: "it can make my visage completely black": a face
      //  turned from the sun and the sky's light had no light at all)
      ambientColor: root.ambient
    }

    Node {
      id: world
      scale: Qt.vector3d(100, 100, 100)
      eulerRotation.x: -90

      Repeater3D {
        model: root.fixtures
        delegate: Model {
          required property var modelData
          geometry: modelData.geometry
          materials: PrincipledMaterial {
            baseColor: modelData.colour
            metalness: modelData.metal
            roughness: modelData.rough
          }
        }
      }

      //  The skin's pixels drawn sharp, as Minecraft draws them; its outer
      //  layer drawn only where the picture is not see-through
      Texture {
        id: skinTexture
        source: root.figureSkin
        minFilter: Texture.Nearest
        magFilter: Texture.Nearest
        mipFilter: Texture.None
        generateMipmaps: false
      }
      PrincipledMaterial {
        id: skinMaterial
        baseColorMap: skinTexture
        alphaMode: PrincipledMaterial.Opaque
        metalness: 0.0
        roughness: 0.9
      }
      PrincipledMaterial {
        id: outerMaterial
        baseColorMap: skinTexture
        alphaMode: PrincipledMaterial.Mask
        alphaCutoff: 0.5
        metalness: 0.0
        roughness: 0.9
      }

      Node {
        visible: root.chased && root.figureParts.length > 0
        position: root.figurePlace
        rotation: root.figureTurn

        Repeater3D {
          model: root.figureParts
          delegate: Node {
            required property var modelData
            position: modelData.pivot
            rotation: modelData.index < root.figureTurns.length
                      ? root.figureTurns[modelData.index]
                      : Qt.quaternion(1, 0, 0, 0)
            Model {
              geometry: modelData.geometry
              materials: modelData.outer ? [outerMaterial] : [skinMaterial]
            }
          }
        }

        Node {
          visible: root.holding && root.heldModel.length > 0
          position: root.figureHand
          rotation: root.figureTurns.length > 2 ? root.figureTurns[2]
                                                : Qt.quaternion(1, 0, 0, 0)
          Node {
            position: root.figureGrip
            rotation: root.figureHanded
            Node {
              position: root.handModelPlace
              eulerRotation: root.heldModelTurn
              scale: Qt.vector3d(root.handModelScale, root.handModelScale,
                                 root.handModelScale)
              RuntimeLoader {
                source: root.heldModel
              }
            }
          }
        }
      }

      Repeater3D {
        model: root.peeps
        delegate: Node {
          required property var modelData
          position: modelData.place
          rotation: modelData.turn
          Model {
            source: "#Cube"
            position: Qt.vector3d(0, 0, 0.5 * modelData.length)
            scale: Qt.vector3d(0.0003, 0.0003, 0.01 * modelData.length)
            materials: PrincipledMaterial {
              baseColor: "#9aa0a6"
              metalness: 0.3
              roughness: 0.35
            }
          }
          Model {
            source: "#Sphere"
            position: Qt.vector3d(0, 0, modelData.length)
            scale: Qt.vector3d(0.0007, 0.0007, 0.0007)
            materials: PrincipledMaterial {
              baseColor: "#d02a2a"
              metalness: 0.0
              roughness: 0.4
            }
          }
        }
      }

      //  A body's part may carry a picture (a coach's posters), as bright
      //  as its 'glow' of its own
      Repeater3D {
        model: root.bodies
        delegate: Model {
          id: bodyModel
          required property var modelData
          property bool pictured: (modelData.picture || "") !== ""
          property Texture picture: Texture {
            source: bodyModel.modelData.picture || ""
          }
          geometry: modelData.geometry
          position: modelData.body < root.places.length
                    ? root.places[modelData.body] : Qt.vector3d(0, 0, 0)
          rotation: modelData.body < root.turns.length
                    ? root.turns[modelData.body] : Qt.quaternion(1, 0, 0, 0)
          materials: PrincipledMaterial {
            baseColor: modelData.body === root.heldBody ? root.heldTint
                       : modelData.body === root.pointedBody
                       ? root.pointedTint : modelData.colour
            baseColorMap: bodyModel.pictured ? bodyModel.picture : null
            emissiveMap: bodyModel.pictured ? bodyModel.picture : null
            emissiveFactor: Qt.vector3d(modelData.glow || 0,
                                        modelData.glow || 0,
                                        modelData.glow || 0)
            metalness: modelData.metal
            roughness: modelData.rough
          }
        }
      }
    }
  }

  //  The floating prompt: over its place as the camera sees it, bobbing
  Item {
    id: prompt
    visible: root.promptOn
    property vector3d seen: view.mapFrom3DScene(root.promptPlace)
    property real bob: 0
    width: promptRow.implicitWidth + 20
    height: promptRow.implicitHeight + 12
    x: seen.x - width / 2
    y: seen.y - height - bob
    SequentialAnimation on bob {
      running: root.promptOn
      loops: Animation.Infinite
      NumberAnimation { to: 6; duration: 700; easing.type: Easing.InOutSine }
      NumberAnimation { to: 0; duration: 700; easing.type: Easing.InOutSine }
    }
    Rectangle {
      anchors.fill: parent
      radius: 6
      color: "#c8181c22"
      border.color: "#66717f"
    }
    Row {
      id: promptRow
      anchors.centerIn: parent
      spacing: 9
      Rectangle {
        width: 30
        height: 30
        radius: 5
        color: "#e8ecf0"
        border.color: "#8a949e"
        border.width: 2
        Text {
          anchors.centerIn: parent
          text: root.promptKey
          color: "#181c22"
          font.pixelSize: 17
          font.bold: true
        }
      }
      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: root.promptText
        color: "#e8ecf0"
        font.pixelSize: 16
      }
    }
  }

  Item {
    visible: root.crosshair
    anchors.centerIn: parent
    width: 22
    height: 22
    Rectangle { x: 0; y: 10; width: 7; height: 2; color: "#c8ebebf0" }
    Rectangle { x: 15; y: 10; width: 7; height: 2; color: "#c8ebebf0" }
    Rectangle { x: 10; y: 0; width: 2; height: 7; color: "#c8ebebf0" }
    Rectangle { x: 10; y: 15; width: 2; height: 7; color: "#c8ebebf0" }
  }

  Rectangle {
    visible: root.debug.length > 0
    x: 10
    y: 10
    width: debugColumn.implicitWidth + 16
    height: debugColumn.implicitHeight + 12
    radius: 4
    color: "#a0181c22"
    Column {
      id: debugColumn
      x: 8
      y: 6
      Text {
        text: root.debug
        color: "#e8ecf0"
        font.pixelSize: 13
        font.family: "monospace"
      }
      Text {
        visible: root.debugWarning.length > 0
        text: root.debugWarning
        color: "#ffa040"
        font.pixelSize: 13
        font.bold: true
      }
    }
  }

  Row {
    id: hotbarRow
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    anchors.bottomMargin: 14
    spacing: 4
    Repeater {
      model: root.hotbar
      delegate: Rectangle {
        required property string modelData
        required property int index
        width: 72
        height: 72
        radius: 4
        color: "#a0181c22"
        border.width: index === root.slot ? 3 : 1
        border.color: index === root.slot ? "#f0f0f0" : "#808890"
        Text {
          x: 5
          y: 3
          text: index + 1
          color: "#a0b0c0"
          font.pixelSize: 11
        }
        property string icon: index < root.hotbarIcons.length
                              ? root.hotbarIcons[index] : ""
        Image {
          visible: parent.icon.length > 0
          anchors.centerIn: parent
          width: 56
          height: 56
          sourceSize: Qt.size(112, 112)
          source: parent.icon
          smooth: true
        }
        Text {
          visible: parent.icon.length === 0
          anchors.centerIn: parent
          width: parent.width - 8
          horizontalAlignment: Text.AlignHCenter
          wrapMode: Text.WordWrap
          text: modelData
          color: "#e8ecf0"
          font.pixelSize: 12
        }
      }
    }
  }

  MouseArea {
    anchors.fill: parent
    visible: root.menuOpen
    onClicked: root.menuPicked("close")
  }

  Rectangle {
    visible: root.menuOpen
    anchors.centerIn: parent
    width: menuColumn.implicitWidth + 36
    height: menuColumn.implicitHeight + 32
    radius: 8
    color: "#eb181c22"
    border.color: "#5b6470"
    MouseArea {
      anchors.fill: parent
    }
    Column {
      id: menuColumn
      anchors.centerIn: parent
      spacing: 10
      Text {
        text: root.menuTitle
        color: "#e8ecf0"
        font.pixelSize: 15
      }
      Text {
        visible: root.menuReadout.length > 0
        text: root.menuReadout
        color: "#e8ecf0"
        font.pixelSize: 15
      }
      Grid {
        columns: 4
        spacing: 10
        Repeater {
          model: root.menuButtons
          delegate: menuButton
        }
      }
      Text {
        text: "World"
        color: "#e8ecf0"
        font.pixelSize: 15
      }
      Row {
        spacing: 10
        Repeater {
          model: root.menuWorld
          delegate: menuButton
        }
      }
    }
  }

  Component {
    id: menuButton
    Rectangle {
      required property var modelData
      objectName: "menu:" + modelData.key
      width: Math.max(96, label.implicitWidth + 28)
      height: 64
      radius: 6
      color: area.containsMouse ? "#4b5563" : "#3a424d"
      border.color: "#66717f"
      Text {
        id: label
        anchors.centerIn: parent
        text: parent.modelData.text
        color: "#e8ecf0"
        font.pixelSize: 14
      }
      MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.menuPicked(parent.modelData.key)
      }
    }
  }

  Rectangle {
    visible: root.hint.length > 0
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: hotbarRow.top
    anchors.bottomMargin: 12
    width: help.implicitWidth + 24
    height: help.implicitHeight + 12
    radius: 6
    color: "#b0181c22"
    Text {
      id: help
      anchors.centerIn: parent
      text: root.hint
      color: "#e8ecf0"
      font.pixelSize: 15
    }
  }
}
