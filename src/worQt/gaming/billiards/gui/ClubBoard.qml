//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen
//
//  The club board's face (the user: a diegetic scoreboard, "make it
//  diegetic"): drawn flat, 1200 by 540, and shown in the room as the
//  face of the boards on the walls. An electronic club board as the
//  billiard shops sell them, in a wood cabinet, ebony or oak: the two
//  players either side, each his ball and name, his points in large
//  segment digits counting up, his innings or series, average and best,
//  the run in a row of beads and the way to the distance in a bar; the
//  centre the distance, the inning or series, the shot clock or the pins
//  due, a lamp for match ball or the final series; under it all a
//  dot-matrix line saying what just happened. 'info' holds it all, as
//  'TableView.setBoards' sends it, its words in the language chosen; a
//  line in letters the 5 by 7 glyphs cannot draw (Korean) comes as its
//  dots, 'dots' and 'dotRows', sampled from a font.

import QtQuick

Rectangle {
  id: board

  property var info: ({})
  readonly property var names: info.names || ["", ""]
  readonly property var balls: info.balls || ["#f2ecd9", "#f5b21b"]
  readonly property var leds: info.leds || ["#f6f0e4", "#ffad2a"]
  readonly property var points: info.points || [0, 0]
  readonly property var stats: info.stats || [["", "", ""], ["", "", ""]]
  readonly property var labels: info.labels || ["INN", "AVG", "HR"]
  readonly property var shares: info.shares || [0, 0]
  readonly property int at: info.at === undefined ? -1 : info.at
  readonly property int won: info.won === undefined ? -1 : info.won
  readonly property int run: info.run || 0
  readonly property string tier: info.tier || "green"
  readonly property color amber: "#ffad2a"
  readonly property color red: "#ff4134"
  readonly property color green: "#58f08f"
  readonly property color off: Qt.rgba(1, 0.96, 0.88, 0.055)

  width: 1200
  height: 540
  radius: 16
  color: info.wood === "oak" ? "#7b5534" : "#1b1512"

  function tierColor() {
    return tier === "red" ? red : tier === "amber" ? amber : green
  }

  //  Segment digits, right-aligned into 'cells' places; a '.' lights the
  //  point of the digit before it.
  component SevenSeg: Canvas {
    id: seven
    property string text: ""
    property int cells: 2
    property color lit: "#f6f0e4"
    width: cells * height * 0.58
    onTextChanged: requestPaint()
    onLitChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
      const ctx = getContext("2d")
      ctx.reset()
      const s = height / 100
      const t = 9, g = 1.4, x0 = 7, x1 = 47, y0 = 7, ym = 50, y1 = 93
      function h(xa, xb, y) {
        return [[xa + t / 2 + g, y], [xa + t + g, y - t / 2],
                [xb - t - g, y - t / 2], [xb - t / 2 - g, y],
                [xb - t - g, y + t / 2], [xa + t + g, y + t / 2]]
      }
      function v(x, ya, yb) {
        return [[x, ya + t / 2 + g], [x + t / 2, ya + t + g],
                [x + t / 2, yb - t - g], [x, yb - t / 2 - g],
                [x - t / 2, yb - t - g], [x - t / 2, ya + t + g]]
      }
      const segs = { a: h(x0, x1, y0), g: h(x0, x1, ym), d: h(x0, x1, y1),
                     f: v(x0, y0, ym), b: v(x1, y0, ym), e: v(x0, ym, y1),
                     c: v(x1, ym, y1) }
      const lit = { "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd",
                    "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
                    "8": "abcdefg", "9": "abcdfg", "-": "g", " ": "" }
      let digits = []
      for (let i = 0; i < seven.text.length; ++i) {
        const ch = seven.text[i]
        if (ch === "." && digits.length)
          digits[digits.length - 1].dp = true
        else
          digits.push({ ch: ch, dp: false })
      }
      while (digits.length < seven.cells)
        digits.unshift({ ch: " ", dp: false })
      digits = digits.slice(-seven.cells)
      for (let k = 0; k < digits.length; ++k) {
        const on = lit[digits[k].ch] || ""
        ctx.setTransform(s, 0, -0.105 * s, s, (k * 58 + 8) * s, 0)
        for (const name in segs) {
          const shape = segs[name]
          const glow = on.indexOf(name) >= 0
          ctx.fillStyle = glow ? seven.lit : board.off
          ctx.shadowColor = seven.lit
          ctx.shadowBlur = glow ? 12 : 0
          ctx.beginPath()
          ctx.moveTo(shape[0][0], shape[0][1])
          for (let p = 1; p < shape.length; ++p)
            ctx.lineTo(shape[p][0], shape[p][1])
          ctx.closePath()
          ctx.fill()
        }
        ctx.fillStyle = digits[k].dp ? seven.lit : board.off
        ctx.beginPath()
        ctx.arc(54, y1, 4, 0, 2 * Math.PI)
        ctx.fill()
      }
    }
  }

  //  One player's side: ball, name, points counting up, the three
  //  figures, the run in beads, the way to the distance.
  component Side: Item {
    id: side
    property int index: 0
    readonly property bool mirrored: index === 1
    readonly property color led: board.leds[index]
    readonly property int target: board.points[index] || 0
    property real shown: 0
    width: 420
    height: 380
    Component.onCompleted: shown = target
    onTargetChanged: shown = target
    Behavior on shown { NumberAnimation { duration: 450 } }

    Rectangle {
      anchors.fill: parent
      anchors.margins: -10
      color: "transparent"
      radius: 8
      border.width: 2
      border.color: board.won === side.index ? board.green
        : board.at === side.index ? Qt.rgba(1, 1, 1, 0.09) : "transparent"
    }
    Row {
      id: who
      spacing: 14
      layoutDirection: side.mirrored ? Qt.RightToLeft : Qt.LeftToRight
      anchors.left: side.mirrored ? undefined : parent.left
      anchors.right: side.mirrored ? parent.right : undefined
      Rectangle {
        width: 30; height: 30; radius: 15
        anchors.verticalCenter: parent.verticalCenter
        color: board.balls[side.index]
      }
      Text {
        text: (board.names[side.index] || "").toUpperCase()
        color: "#f6f0e4"
        font.pixelSize: 30
        font.bold: true
        font.letterSpacing: 3
      }
      Text {
        text: side.mirrored ? "▶" : "◀"
        color: board.amber
        font.pixelSize: 26
        anchors.verticalCenter: parent.verticalCenter
        visible: board.at === side.index
        SequentialAnimation on opacity {
          running: board.at === side.index
          loops: Animation.Infinite
          NumberAnimation { to: 0.25; duration: 700 }
          NumberAnimation { to: 1; duration: 700 }
        }
      }
    }
    SevenSeg {
      y: 52
      height: 150
      cells: 3
      lit: side.led
      text: String(Math.round(side.shown))
      anchors.left: side.mirrored ? undefined : parent.left
      anchors.right: side.mirrored ? parent.right : undefined
    }
    Row {
      y: 222
      spacing: 26
      layoutDirection: side.mirrored ? Qt.RightToLeft : Qt.LeftToRight
      anchors.left: side.mirrored ? undefined : parent.left
      anchors.right: side.mirrored ? parent.right : undefined
      Repeater {
        model: 3
        delegate: Column {
          spacing: 4
          Text {
            text: board.labels[index]
            color: "#8e8576"
            font.pixelSize: 17
            font.letterSpacing: 3
          }
          SevenSeg {
            height: 40
            cells: index === 1 ? 4 : 2
            lit: "#f6f0e4"
            text: (board.stats[side.index] || [])[index] || ""
          }
        }
      }
    }
    Row {
      y: 300
      spacing: 9
      layoutDirection: side.mirrored ? Qt.RightToLeft : Qt.LeftToRight
      anchors.left: side.mirrored ? undefined : parent.left
      anchors.right: side.mirrored ? parent.right : undefined
      Text {
        text: board.info.runLabel || "RUN"
        color: "#8e8576"
        font.pixelSize: 17
        font.letterSpacing: 3
        anchors.verticalCenter: parent.verticalCenter
      }
      Repeater {
        model: 10
        delegate: Rectangle {
          readonly property bool on: board.at === side.index
            && index < Math.min(10, board.info.beads || 0)
          width: 20; height: 20; radius: 10
          anchors.verticalCenter: parent.verticalCenter
          color: on ? board.tierColor() : board.off
        }
      }
      Text {
        text: board.at === side.index && board.run ? String(board.run) : ""
        color: board.tierColor()
        font.pixelSize: 28
        font.bold: true
        anchors.verticalCenter: parent.verticalCenter
      }
    }
    Row {
      y: 348
      spacing: 4
      layoutDirection: side.mirrored ? Qt.RightToLeft : Qt.LeftToRight
      anchors.left: side.mirrored ? undefined : parent.left
      anchors.right: side.mirrored ? parent.right : undefined
      Repeater {
        model: 20
        delegate: Rectangle {
          width: 17; height: 9; radius: 2
          color: index < Math.round((board.shares[side.index] || 0) * 20)
            ? board.amber : board.off
        }
      }
    }
  }

  //  The line saying what just happened: a dot-matrix strip, typed on,
  //  scrolled when too long, its colour the call's. Its 'text' drawn in
  //  the 5 by 7 glyphs, or, given, its 'dots', a column each, 'rows'
  //  high, as a font draws letters the glyphs have not.
  component DotMatrix: Canvas {
    id: matrix
    property string text: ""
    property var dots: []
    property int rows: 7
    property string tone: "neutral"
    property int reveal: 0
    property int offset: 0
    property int hue: 0
    readonly property int visibleColumns: Math.round(132 * (rows + 2) / 9)
    property var columns: []
    readonly property var glyphs: ({
      "A": ["01110","10001","10001","11111","10001","10001","10001"],
      "B": ["11110","10001","10001","11110","10001","10001","11110"],
      "C": ["01110","10001","10000","10000","10000","10001","01110"],
      "D": ["11100","10010","10001","10001","10001","10010","11100"],
      "E": ["11111","10000","10000","11110","10000","10000","11111"],
      "F": ["11111","10000","10000","11110","10000","10000","10000"],
      "G": ["01110","10001","10000","10111","10001","10001","01111"],
      "H": ["10001","10001","10001","11111","10001","10001","10001"],
      "I": ["01110","00100","00100","00100","00100","00100","01110"],
      "J": ["00111","00010","00010","00010","00010","10010","01100"],
      "K": ["10001","10010","10100","11000","10100","10010","10001"],
      "L": ["10000","10000","10000","10000","10000","10000","11111"],
      "M": ["10001","11011","10101","10101","10001","10001","10001"],
      "N": ["10001","10001","11001","10101","10011","10001","10001"],
      "O": ["01110","10001","10001","10001","10001","10001","01110"],
      "P": ["11110","10001","10001","11110","10000","10000","10000"],
      "Q": ["01110","10001","10001","10001","10101","10010","01101"],
      "R": ["11110","10001","10001","11110","10100","10010","10001"],
      "S": ["01111","10000","10000","01110","00001","00001","11110"],
      "T": ["11111","00100","00100","00100","00100","00100","00100"],
      "U": ["10001","10001","10001","10001","10001","10001","01110"],
      "V": ["10001","10001","10001","10001","10001","01010","00100"],
      "W": ["10001","10001","10001","10101","10101","10101","01010"],
      "X": ["10001","10001","01010","00100","01010","10001","10001"],
      "Y": ["10001","10001","10001","01010","00100","00100","00100"],
      "Z": ["11111","00001","00010","00100","01000","10000","11111"],
      "Ø": ["01111","10011","10101","10101","10101","11001","11110"],
      "Æ": ["01111","10100","10100","11110","10100","10100","10111"],
      "Å": ["00100","00000","01110","10001","11111","10001","10001"],
      "É": ["00010","11111","10000","11110","10000","10000","11111"],
      "È": ["01000","11111","10000","11110","10000","10000","11111"],
      "Ê": ["00100","01010","11111","10000","11110","10000","11111"],
      "Ë": ["01010","11111","10000","11110","10000","10000","11111"],
      "À": ["01000","01110","10001","10001","11111","10001","10001"],
      "Â": ["00100","01010","01110","10001","11111","10001","10001"],
      "Ä": ["01010","01110","10001","10001","11111","10001","10001"],
      "Ç": ["01110","10001","10000","10000","10001","01110","00100"],
      "Î": ["00100","01010","01110","00100","00100","00100","01110"],
      "Ï": ["01010","01110","00100","00100","00100","00100","01110"],
      "Ô": ["00100","01010","01110","10001","10001","10001","01110"],
      "Ö": ["01010","01110","10001","10001","10001","10001","01110"],
      "Û": ["00100","01010","10001","10001","10001","10001","01110"],
      "Ù": ["01000","10001","10001","10001","10001","10001","01110"],
      "Ü": ["01010","10001","10001","10001","10001","10001","01110"],
      "Œ": ["01111","10100","10100","10111","10100","10100","01111"],
      "0": ["01110","10001","10011","10101","11001","10001","01110"],
      "1": ["00100","01100","00100","00100","00100","00100","01110"],
      "2": ["01110","10001","00001","00010","00100","01000","11111"],
      "3": ["11111","00010","00100","00010","00001","10001","01110"],
      "4": ["00010","00110","01010","10010","11111","00010","00010"],
      "5": ["11111","10000","11110","00001","00001","10001","01110"],
      "6": ["00110","01000","10000","11110","10001","10001","01110"],
      "7": ["11111","00001","00010","00100","01000","01000","01000"],
      "8": ["01110","10001","10001","01110","10001","10001","01110"],
      "9": ["01110","10001","10001","01111","00001","00010","01100"],
      " ": ["00000","00000","00000","00000","00000","00000","00000"],
      ".": ["00000","00000","00000","00000","00000","01100","01100"],
      ",": ["00000","00000","00000","00000","01100","00100","01000"],
      ":": ["00000","01100","01100","00000","01100","01100","00000"],
      ";": ["00000","01100","01100","00000","01100","00100","01000"],
      "!": ["00100","00100","00100","00100","00100","00000","00100"],
      "?": ["01110","10001","00001","00010","00100","00000","00100"],
      "+": ["00000","00100","00100","11111","00100","00100","00000"],
      "-": ["00000","00000","00000","11111","00000","00000","00000"],
      "/": ["00000","00001","00010","00100","01000","10000","00000"],
      ">": ["01000","00100","00010","00001","00010","00100","01000"],
      "(": ["00010","00100","01000","01000","01000","00100","00010"],
      ")": ["01000","00100","00010","00010","00010","00100","01000"],
      "'": ["00100","00100","01000","00000","00000","00000","00000"],
      "·": ["00000","00000","00000","01100","01100","00000","00000"]
    })
    function columnsOf(words) {
      const out = []
      for (let i = 0; i < words.length; ++i) {
        const glyph = matrix.glyphs[words[i]] || matrix.glyphs[" "]
        for (let c = 0; c < 5; ++c) {
          let bits = 0
          for (let r = 0; r < 7; ++r)
            if (glyph[r][c] === "1")
              bits |= 1 << r
          out.push(bits)
        }
        out.push(0)
      }
      return out
    }
    function restart() {
      columns = dots.length ? dots : columnsOf(text.toUpperCase())
      reveal = 0
      offset = 0
      requestPaint()
    }
    onTextChanged: restart()
    onDotsChanged: restart()
    Timer {
      interval: 45
      running: true
      repeat: true
      onTriggered: {
        if (matrix.columns.length > matrix.visibleColumns)
          matrix.offset += 1
        if (matrix.reveal < matrix.visibleColumns)
          matrix.reveal += 3
        matrix.hue = (matrix.hue + 6) % 360
        matrix.requestPaint()
      }
    }
    onPaint: {
      const ctx = getContext("2d")
      ctx.reset()
      const pitch = Math.min(width / visibleColumns, height / (rows + 2))
      const top = (height - pitch * (rows + 2)) / 2
      const r = pitch * 0.36
      const long = columns.length > visibleColumns
      const colors = { neutral: "#f6f0e4", point: "#ffad2a",
                       foul: "#ff4134", best: "" }
      const base = colors[tone] === undefined ? "#f6f0e4" : colors[tone]
      for (let c = 0; c < visibleColumns; ++c) {
        let source = 0
        if (long) {
          const span = columns.length + 24
          const k = (c + offset) % span
          source = k < columns.length ? columns[k] : 0
        } else if (c < Math.min(reveal, columns.length)) {
          source = columns[c]
        }
        for (let row = 0; row < rows; ++row) {
          const lit = (source >> row) & 1
          ctx.fillStyle = lit
            ? (base || Qt.hsla(((hue + c * 4) % 360) / 360, 0.95, 0.62, 1))
            : Qt.rgba(1, 0.96, 0.88, 0.05)
          ctx.beginPath()
          ctx.arc(c * pitch + pitch / 2, top + (row + 1) * pitch + pitch / 2,
                  r, 0, 2 * Math.PI)
          ctx.fill()
        }
      }
    }
  }

  //  The face: smoked glass in the cabinet, its brass screws.
  Repeater {
    model: [[12, 12], [1176, 12], [12, 516], [1176, 516]]
    delegate: Rectangle {
      x: modelData[0]; y: modelData[1]; width: 13; height: 13; radius: 7
      color: "#c9a24a"
    }
  }
  Rectangle {
    id: glass
    x: 28; y: 28; width: 1144; height: 484
    radius: 8
    color: "#0a0a0b"

    Side { x: 24; y: 22; index: 0 }
    Side { x: 700; y: 22; index: 1 }

    Column {
      x: 460; y: 26; width: 224
      spacing: 10
      Text {
        width: parent.width
        horizontalAlignment: Text.AlignHCenter
        text: board.info.title || ""
        color: board.amber
        font.pixelSize: 34
        font.bold: true
        font.letterSpacing: 3
      }
      Text {
        width: parent.width
        horizontalAlignment: Text.AlignHCenter
        text: board.info.roundLabel || ""
        color: "#8e8576"
        font.pixelSize: 17
        font.letterSpacing: 3
      }
      SevenSeg {
        anchors.horizontalCenter: parent.horizontalCenter
        height: 80
        cells: 2
        lit: board.amber
        text: board.info.round === undefined ? "" : String(board.info.round)
      }
      Text {
        width: parent.width
        horizontalAlignment: Text.AlignHCenter
        text: board.info.due === undefined || board.info.due < 0
          ? (board.info.clockLabel || "SHOT CLOCK")
          : (board.info.dueLabel || "PINS DUE")
        color: "#8e8576"
        font.pixelSize: 17
        font.letterSpacing: 3
      }
      SevenSeg {
        anchors.horizontalCenter: parent.horizontalCenter
        visible: board.info.due === undefined || board.info.due < 0
        height: 52
        cells: 2
        lit: "#f6f0e4"
        text: board.info.clock || ""
      }
      Row {
        anchors.horizontalCenter: parent.horizontalCenter
        visible: board.info.due !== undefined && board.info.due >= 0
        spacing: 12
        Repeater {
          model: 3
          delegate: Rectangle {
            width: 22; height: 22; radius: 11
            color: index < (board.info.due || 0)
              ? (index === 1 && board.info.due === 2 ? board.red
                                                     : board.amber)
              : board.off
          }
        }
      }
      Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        width: lampWords.implicitWidth + 24
        height: lampWords.implicitHeight + 10
        radius: 4
        color: board.info.lampOn ? board.amber : "transparent"
        border.color: Qt.rgba(1, 0.96, 0.88, 0.1)
        Text {
          id: lampWords
          anchors.centerIn: parent
          text: board.info.lamp || ""
          color: board.info.lampOn ? "#1a0f05" : Qt.rgba(1, 0.96, 0.88, 0.14)
          font.pixelSize: 22
          font.bold: true
          font.letterSpacing: 3
        }
      }
    }

    Rectangle {
      x: 24; y: 404; width: 1096; height: 1
      color: Qt.rgba(1, 1, 1, 0.06)
    }
    DotMatrix {
      x: 24; y: 414; width: 1096; height: 58
      text: board.info.line || ""
      dots: board.info.dots || []
      rows: board.info.dotRows || 7
      tone: board.info.tone || "neutral"
    }
  }
}
