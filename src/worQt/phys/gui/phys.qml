//  phys.qml is the lab's bodies in 3D, drawn by Qt Quick 3D for
//  'GpuView' (the GPU's view; 'PhysView' paints the same with Qt's
//  painter): each body's parts, placed and turned as the body is; the
//  dressed parts (made in the world each frame: a car's suspension); the
//  ground, a terrain's shape and the flat ground about it, dirt; the
//  sun with its shadows and the sky's light; over it, for a walker, a
//  cross and a line of help. Python sets its properties; nothing here
//  moves anything on its own.
//
//  The scene is in centimetres with y up: the world's (x, y, z) in
//  metres, z up, is the scene's 100 (x, z, -y).
//
//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen

import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

Item {
  id: root

  //  The bodies' parts, each {geometry, body, colour, metal, rough}: a
  //  mesh about its body's centre and how it looks; each body's place
  //  and turn in the scene, by its index
  property var parts: []
  property var places: []
  property var turns: []
  //  Each part's colour now, by its place in 'parts': a tint (what a
  //  walker's grabber points at) changes it without making the part
  //  anew (made anew, the parts all vanished); past its end a part
  //  keeps the colour it was made with
  property var colours: []

  //  The dressed parts, each {geometry, colour, metal, rough, casts}: a
  //  mesh in the scene as it is, refilled each frame; a colour less than
  //  opaque blends (tyre tracks), 'casts' whether it casts a shadow
  property var dressed: []

  //  The ground: a terrain's shape (or none) and the flat ground about
  //  it, both dirt: 'groundMap' its colours, 'groundBumps' its bumps
  property var terrainShape: null
  property var flatShape: null
  property url groundMap
  property url groundBumps
  //  The paved part of a terrain (a racetrack), concrete: 'pavedMap' its
  //  colours, 'pavedBumps' its bumps
  property var pavedShape: null
  property url pavedMap
  property url pavedBumps
  //  The asphalt part (an oval's apron): 'asphaltMap', 'asphaltBumps'
  property var asphaltShape: null
  property url asphaltMap
  property url asphaltBumps
  //  An oval's safety barrier, white concrete, and the blue stripe
  //  along the foot of its face
  property var wallShape: null
  property var stripeShape: null
  //  The ground margins of an oval's own track mesh (its surfaces drawn
  //  following its curves), dirt as the terrain
  property var trackGroundShape: null
  //  What is drawn in its photographs, each {geometry, map, both}: a
  //  mesh in the scene as it is, its picture ('map'), seen from both
  //  sides where 'both'; unlit (the photographs' light their own),
  //  casting no shadow (a road along its rows, houses only to look at).
  //  While there are any, the scene's colours are left as they are
  //  (no filmic curve: the photographs as taken)
  property var photographed: []

  //  How much bigger than it is the world is drawn (a world shrunk for
  //  a walker is drawn at their size, so the camera's near cut, the
  //  shadows and the ground's pictures work as at full size), and the
  //  camera's near cut in the drawn scene, cm
  property real magnify: 1.0
  property real cameraNear: 5
  //  A cross in the middle (where a walker's grabber points), and a
  //  line of help along the bottom (none: empty)
  property bool crosshair: false
  property string hint: ""
  //  The speedometer in the corner (shown while riding a car): its
  //  dial's picture, its needle's angle right of upright, deg, its
  //  figure
  property bool speedometer: false
  property string dialFace: ""
  property real speedAngle: -135
  property string speedText: ""

  //  The camera, and the turns of the sun and the sky's light (each
  //  shining along its own -z)
  property vector3d cameraPlace: Qt.vector3d(0, 300, 800)
  property quaternion cameraTurn: Qt.quaternion(1, 0, 0, 0)
  property quaternion sunTurn: Qt.quaternion(1, 0, 0, 0)
  property quaternion skyTurn: Qt.quaternion(1, 0, 0, 0)
  //  What the drawing spends the GPU on, each to be set (the physics
  //  shares the GPU with it, taking turns: 'main.gpuDiagnosis' times
  //  the steps at each): samples a pixel (4, 2 or 1: none), the glass
  //  (2 sorted per pixel, 1 blended by weight, 0 as plain blending), the
  //  sun's shadows (3 their sharpest, 2 high, 1 medium). On the RTX
  //  5060, 2026-11-15, the real car's one-block kernel 116 us a step at
  //  4 2 3, 98 at 2 1 2 and at 1 0 1 (67 headless); in town 129, 125,
  //  119: light, 2 1 2.
  property int aaSamples: 2
  property int glass: 1
  property int shadows: 2

  View3D {
    id: view
    anchors.fill: parent
    camera: camera

    //  Dithered after tonemapping (user, 2026-11-13: "the track is
    //  exhibiting ugly color banding, that dithering would fix"); the
    //  helpers' other effects (glow, haze, vignette) stay off.
    environment: ExtendedSceneEnvironment {
      backgroundMode: SceneEnvironment.Color
      clearColor: "#56657a"
      antialiasingMode: root.aaSamples > 1 ? SceneEnvironment.MSAA
                                           : SceneEnvironment.NoAA
      antialiasingQuality: root.aaSamples > 2 ? SceneEnvironment.High
                                              : SceneEnvironment.Medium
      tonemapMode: root.photographed.length > 0
                   ? SceneEnvironment.TonemapModeLinear
                   : SceneEnvironment.TonemapModeFilmic
      ditheringEnabled: true
      //  Glass sorted per pixel, every layer in its true order (user,
      //  2026-11-13: QtQuick was "not having consistent transparent
      //  rendering"); plain blending sorts whole models by their
      //  centres and draws a model's own faces in index order
      oitMethod: root.glass > 1 ? SceneEnvironment.OITLinkedList
                 : root.glass > 0 ? SceneEnvironment.OITWeightedBlended
                 : SceneEnvironment.OITNone
    }

    PerspectiveCamera {
      id: camera
      position: root.cameraPlace
      rotation: root.cameraTurn
      fieldOfView: 58
      clipNear: root.cameraNear
      clipFar: 300000
      //  Among houses in photographs (hundreds of pieces, 2.5 million
      //  triangles) what is out of sight is not drawn
      frustumCullingEnabled: root.photographed.length > 0
    }

    DirectionalLight {
      rotation: root.sunTurn
      color: "#fff3e0"
      brightness: 1.5
      castsShadow: true
      shadowMapQuality: root.shadows > 2 ? Light.ShadowMapQualityVeryHigh
                        : root.shadows > 1 ? Light.ShadowMapQualityHigh
                        : Light.ShadowMapQualityMedium
      shadowFactor: 70
      shadowMapFar: 8000
      shadowBias: 5
      csmNumSplits: 2
    }
    DirectionalLight {
      rotation: root.skyTurn
      color: "#b8c8e8"
      brightness: 0.45
    }

    PrincipledMaterial {
      id: groundMaterial
      baseColorMap: Texture {
        source: root.groundMap
        tilingModeHorizontal: Texture.Repeat
        tilingModeVertical: Texture.Repeat
        generateMipmaps: true
        mipFilter: Texture.Linear
      }
      normalMap: Texture {
        source: root.groundBumps
        tilingModeHorizontal: Texture.Repeat
        tilingModeVertical: Texture.Repeat
        generateMipmaps: true
        mipFilter: Texture.Linear
      }
      normalStrength: 0.8
      metalness: 0.0
      roughness: 1.0
    }

    //  Everything drawn of the world, at 'magnify' times its size
    Node {
      scale: Qt.vector3d(root.magnify, root.magnify, root.magnify)

      Model {
        visible: !!root.terrainShape
        geometry: root.terrainShape ? root.terrainShape : null
        materials: groundMaterial
      }
      Model {
        visible: !!root.trackGroundShape
        geometry: root.trackGroundShape ? root.trackGroundShape : null
        materials: groundMaterial
      }
      PrincipledMaterial {
        id: pavedMaterial
        baseColorMap: Texture {
          source: root.pavedMap
          tilingModeHorizontal: Texture.Repeat
          tilingModeVertical: Texture.Repeat
          generateMipmaps: true
          mipFilter: Texture.Linear
        }
        normalMap: Texture {
          source: root.pavedBumps
          tilingModeHorizontal: Texture.Repeat
          tilingModeVertical: Texture.Repeat
          generateMipmaps: true
          mipFilter: Texture.Linear
        }
        normalStrength: 0.5
        metalness: 0.0
        roughness: 0.85
      }
      Model {
        visible: !!root.pavedShape
        geometry: root.pavedShape ? root.pavedShape : null
        materials: pavedMaterial
      }
      PrincipledMaterial {
        id: asphaltMaterial
        baseColorMap: Texture {
          source: root.asphaltMap
          tilingModeHorizontal: Texture.Repeat
          tilingModeVertical: Texture.Repeat
          generateMipmaps: true
          mipFilter: Texture.Linear
        }
        normalMap: Texture {
          source: root.asphaltBumps
          tilingModeHorizontal: Texture.Repeat
          tilingModeVertical: Texture.Repeat
          generateMipmaps: true
          mipFilter: Texture.Linear
        }
        normalStrength: 0.6
        metalness: 0.0
        roughness: 0.9
      }
      Model {
        visible: !!root.asphaltShape
        geometry: root.asphaltShape ? root.asphaltShape : null
        materials: asphaltMaterial
      }
      PrincipledMaterial {
        id: wallMaterial
        baseColor: "#e2e4e7"
        metalness: 0.0
        roughness: 0.65
      }
      Model {
        visible: !!root.wallShape
        geometry: root.wallShape ? root.wallShape : null
        materials: wallMaterial
      }
      PrincipledMaterial {
        id: stripeMaterial
        baseColor: "#1f5fc8"
        metalness: 0.0
        roughness: 0.6
      }
      Model {
        visible: !!root.stripeShape
        geometry: root.stripeShape ? root.stripeShape : null
        materials: stripeMaterial
      }
      Model {
        visible: !!root.flatShape
        geometry: root.flatShape ? root.flatShape : null
        materials: groundMaterial
      }

      Repeater3D {
        model: root.photographed
        delegate: Model {
          required property var modelData
          geometry: modelData.geometry
          castsShadows: false
          receivesShadows: false
          Texture {
            id: photo
            source: modelData.map
            tilingModeHorizontal: Texture.ClampToEdge
            tilingModeVertical: Texture.ClampToEdge
            generateMipmaps: true
            mipFilter: Texture.Linear
          }
          materials: PrincipledMaterial {
            lighting: PrincipledMaterial.NoLighting
            baseColorMap: photo
            metalness: 0.0
            roughness: 1.0
            cullMode: modelData.both ? Material.NoCulling
                                     : Material.BackFaceCulling
          }
        }
      }

      Repeater3D {
        model: root.parts
        delegate: Model {
          required property var modelData
          required property int index
          //  A body's colour now; less than opaque, it is glass: seen
          //  through, both its faces drawn
          property color shown: index < root.colours.length
                                ? root.colours[index] : modelData.colour
          geometry: modelData.geometry
          castsShadows: modelData.casts
          position: modelData.body < root.places.length
                    ? root.places[modelData.body] : Qt.vector3d(0, 0, 0)
          rotation: modelData.body < root.turns.length
                    ? root.turns[modelData.body] : Qt.quaternion(1, 0, 0, 0)
          //  A finished part's picture ('map', none: ''), its colour
          //  times the picture's grey
          Texture {
            id: partMap
            source: modelData.map ? modelData.map : ""
            tilingModeHorizontal: Texture.Repeat
            tilingModeVertical: Texture.Repeat
            generateMipmaps: true
            mipFilter: Texture.Linear
          }
          materials: PrincipledMaterial {
            baseColor: shown
            baseColorMap: modelData.map ? partMap : null
            metalness: modelData.metal
            roughness: modelData.rough
            alphaMode: shown.a < 0.999 ? PrincipledMaterial.Blend
                                       : PrincipledMaterial.Opaque
            cullMode: shown.a < 0.999 ? Material.NoCulling
                                      : Material.BackFaceCulling
          }
        }
      }

      Repeater3D {
        model: root.dressed
        delegate: Model {
          required property var modelData
          geometry: modelData.geometry
          castsShadows: modelData.casts
          materials: PrincipledMaterial {
            baseColor: modelData.colour
            metalness: modelData.metal
            roughness: modelData.rough
            alphaMode: modelData.colour.a < 0.999
                       ? PrincipledMaterial.Blend : PrincipledMaterial.Opaque
          }
        }
      }
    }
  }

  //  The cross where a walker's grabber points, and the help
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
  Item {
    id: speedo
    visible: root.speedometer
    width: 190
    height: 214
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.margins: 18
    Image {
      id: dial
      width: 190
      height: 190
      source: root.dialFace
      smooth: true
      mipmap: true
    }
    Rectangle {
      x: dial.width / 2 - width / 2
      y: dial.height / 2 - 80
      width: 4
      height: 92
      radius: 2
      color: "#ff6824"
      antialiasing: true
      transformOrigin: Item.Bottom
      transform: Rotation {
        origin.x: 2
        origin.y: 80
        angle: root.speedAngle
      }
    }
    Rectangle {
      x: dial.width / 2 - 9
      y: dial.height / 2 - 9
      width: 18
      height: 18
      radius: 9
      color: "#2a2a2e"
      border.color: "#9a9ca0"
      border.width: 2
    }
    Text {
      anchors.horizontalCenter: dial.horizontalCenter
      anchors.top: dial.bottom
      anchors.topMargin: 2
      text: root.speedText
      color: "#ebebf0"
      style: Text.Outline
      styleColor: "#202024"
      font.pixelSize: 18
      font.bold: true
    }
  }
  Text {
    visible: root.hint.length > 0
    text: root.hint
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.margins: 16
    horizontalAlignment: Text.AlignHCenter
    wrapMode: Text.WordWrap
    color: "#ebebf0"
    style: Text.Outline
    styleColor: "#202024"
    font.pixelSize: 14
  }
}
