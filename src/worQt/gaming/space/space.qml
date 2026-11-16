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
