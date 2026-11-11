//  pusher.qml is the coin pusher in 3D, drawn by Qt Quick 3D: the
//  cabinet's boxes, the pusher moving, and the coins, one model drawn
//  once for each coin in play. Python ('PusherView') sets its
//  properties; nothing here moves anything on its own.
//
//  The scene is in mm with y up and z toward the player: the table's
//  top at nought, its front edge at z 'front', the back wall's face at
//  z nought. Its x is the machine's -x: the machine's x runs to the
//  player's left.
//
//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen

import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

Item {
  id: root

  //  The cabinet: its boxes but the pusher, each {x, y, z, sx, sy, sz,
  //  qw, qx, qy, qz, kind}, the middle, half extents and turn in the
  //  scene; the pusher's half extents and where its middle is now.
  property var boxes: []
  property vector3d pusherHalf: Qt.vector3d(180, 15, 120)
  property vector3d pusherPlace: Qt.vector3d(0, 15, 0)
  property real front: 300
  property real tableWidth: 360

  //  The coins: their shape, where each in play is, their pictures
  property var coinShape: null
  property var coinInstances: null
  property url headPicture
  property url tailPicture
  property url roomLight

  //  Written big over the machine: the countdown's beats, then 'GO!'
  property string banner: ""
  onBannerChanged: if (banner !== "") pop.restart()

  View3D {
    id: view
    anchors.fill: parent
    camera: camera

    environment: SceneEnvironment {
      backgroundMode: SceneEnvironment.Color
      clearColor: "#101014"
      antialiasingMode: SceneEnvironment.MSAA
      antialiasingQuality: SceneEnvironment.VeryHigh
      aoEnabled: true
      aoStrength: 60
      aoDistance: 12
      aoSoftness: 50
      tonemapMode: SceneEnvironment.TonemapModeFilmic
      specularAAEnabled: true
      lightProbe: root.roomLight.toString() === "" ? null : room
      probeExposure: 1.2
    }

    Texture {
      id: room
      source: root.roomLight
      mappingMode: Texture.LightProbe
    }

    //  The player's eye, turned round the middle of the table: a drag
    //  turns it, the wheel brings it nearer
    Node {
      id: aim
      position: Qt.vector3d(0, 20, root.front * 0.55)
      eulerRotation.x: -31
      PerspectiveCamera {
        id: camera
        z: 770
        fieldOfView: 38
        clipNear: 5
        clipFar: 6000
      }
    }

    //  The lamps inside the cabinet, over the table
    SpotLight {
      position: Qt.vector3d(0, 330, root.front * 0.6)
      eulerRotation.x: -90
      color: "#fff4e0"
      brightness: 6
      coneAngle: 75
      innerConeAngle: 40
      castsShadow: true
      shadowMapQuality: Light.ShadowMapQualityVeryHigh
      shadowFactor: 55
      shadowMapFar: 2000
      shadowBias: 2
    }
    DirectionalLight {
      eulerRotation.x: -50
      eulerRotation.y: 15
      color: "#d8e2ff"
      brightness: 0.35
    }

    PrincipledMaterial {
      id: playfield
      baseColor: "#1b2a48"
      metalness: 0.0
      roughness: 0.25
      clearcoatAmount: 0.6
      clearcoatRoughnessAmount: 0.1
    }
    PrincipledMaterial {
      id: steel
      baseColor: "#c9ccd2"
      metalness: 1.0
      roughness: 0.22
    }
    PrincipledMaterial {
      id: chrome
      baseColor: "#e2e4e8"
      metalness: 1.0
      roughness: 0.08
    }
    PrincipledMaterial {
      id: glass
      baseColor: "#e8f0ff"
      metalness: 0.0
      roughness: 0.04
      opacity: 0.1
      alphaMode: PrincipledMaterial.Blend
      cullMode: Material.NoCulling
    }
    PrincipledMaterial {
      id: brass
      baseColor: "#c8a45a"
      metalness: 1.0
      roughness: 0.3
    }
    PrincipledMaterial {
      id: tray
      baseColor: "#8d9097"
      metalness: 1.0
      roughness: 0.45
    }

    function materialFor(kind) {
      if (kind === "glass") return glass
      if (kind === "chrome") return chrome
      if (kind === "brass") return brass
      if (kind === "tray") return tray
      if (kind === "steel") return steel
      return playfield
    }

    //  The cabinet's boxes, the pusher apart
    Repeater3D {
      model: root.boxes
      delegate: Model {
        source: "#Cube"
        position: Qt.vector3d(modelData.x, modelData.y, modelData.z)
        rotation: Qt.quaternion(modelData.qw, modelData.qx, modelData.qy,
                                modelData.qz)
        scale: Qt.vector3d(modelData.sx / 50, modelData.sy / 50,
                           modelData.sz / 50)
        materials: [view.materialFor(modelData.kind)]
        receivesShadows: true
        castsShadows: modelData.kind !== "glass"
      }
    }

    //  The pusher: its top is the shelf
    Model {
      source: "#Cube"
      position: root.pusherPlace
      scale: Qt.vector3d(root.pusherHalf.x / 50, root.pusherHalf.y / 50,
                         root.pusherHalf.z / 50)
      materials: [steel]
    }

    //  The coins: top, bottom, edge
    Model {
      visible: root.coinShape !== null && root.coinInstances !== null
      geometry: root.coinShape
      instancing: root.coinInstances
      castsShadows: true
      receivesShadows: true
      materials: [
        PrincipledMaterial {
          baseColorMap: Texture {
            source: root.headPicture
            generateMipmaps: true
            mipFilter: Texture.Linear
          }
          metalness: 0.75
          roughness: 0.3
        },
        PrincipledMaterial {
          baseColorMap: Texture {
            source: root.tailPicture
            generateMipmaps: true
            mipFilter: Texture.Linear
          }
          metalness: 0.75
          roughness: 0.3
        },
        PrincipledMaterial {
          baseColor: "#d4b993"
          metalness: 0.9
          roughness: 0.28
        }
      ]
    }
  }

  Text {
    id: bannerText
    anchors.centerIn: parent
    anchors.verticalCenterOffset: -parent.height * 0.08
    text: root.banner
    visible: root.banner !== ""
    color: "#f2c94c"
    style: Text.Outline
    styleColor: "#3a2a05"
    font.pixelSize: Math.max(48, root.height * 0.22)
    font.bold: true
    SequentialAnimation {
      id: pop
      ParallelAnimation {
        NumberAnimation { target: bannerText; property: "scale"; from: 1.8
                          to: 1.0; duration: 260; easing.type: Easing.OutBack }
        NumberAnimation { target: bannerText; property: "opacity"; from: 0.0
                          to: 1.0; duration: 160 }
      }
      PauseAnimation { duration: 450 }
      NumberAnimation { target: bannerText; property: "opacity"; to: 0.25
                        duration: 280 }
    }
  }

  //  A drag turns round the machine, the wheel comes nearer
  OrbitCameraController {
    anchors.fill: parent
    origin: aim
    camera: camera
    automaticClipping: false
  }
}
