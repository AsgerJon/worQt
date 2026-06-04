# cad_larping.md — the worQt structural drawing / FEA-modeller

A detailed manual for the coordinate-driven vector **drawing app** built in
`worQt` (a fusion of `worktoy` descriptors/overloads with PySide6). Written
so a fresh context can pick up where we left off. Everything below is real
and on disk; line numbers drift, names don't.

> **Status banner.** The app started as a generic 2D drawing toy (points,
> lines, regions). It has since been **rebuilt into a structural-engineering
> pre-processor**: you lay out reference geometry (module/datum lines,
> nodes), draw structural **members** between nodes, attach **supports /
> loads / settlements** as a six-state boundary-condition model, and the
> long-term goal is to **export the model to OpenSeesPy** and read results
> back. The exporter is the one big piece **not yet built** — see §14.
> Everything else below exists and works.

> **Example-package pattern.** The whole CAD app lives under
> `src/worQt/cad/` and is exported from `cad/__init__.py`. Core worQt
> (`mixin`, `settings`, `qtest`, the base `widgets`, the `app`/`window`
> bases) **never imports from `cad`**, so the example can be stripped in one
> move and the PR back to mainline worQt carries only the framework. When
> you add to the example, keep the dependency one-way: `cad` → core, never
> core → `cad`.

## 1. What it is

A 2D structural-drawing canvas. The world is in **millimetres**. You place:

- **Nodes** — structural coordinate nodes (the FEA nodes). Formerly called
  "anchor points"; renamed `Node` everywhere because that is what they are.
- **Module lines** ("modullinjer") — *infinite* datum/grid lines, drawn as
  prominent super-gridlines; the layout grid the structure hangs off.
- **Members** — *real* structural elements drawn **between two nodes**
  (reference-based: they follow their nodes).
- **Supports, loads, settlements** — boundary conditions carried *on* a node
  as a six-state model (§5).
- **Dimensions** (linear) and **angular dimensions** — annotations.

The canvas pans/zooms, has an adaptive grid with rich object-snapping, JSON
save/load (scene **and** view state), undo/redo, an unsaved-changes guard,
and per-category show/hide. It is the worQt **CAD** app (`CADApp`); the older
`App` demo is generic/kept, `JsonApp`/`DrawApp` are retired.

## 2. How to run / test

```bash
# Launch the CAD app: 'python -m worQt' runs CADApp (settings load on entry).
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt
# (main.py's tester01 also launches a CADApp for ad-hoc work; the file's
#  bottom calls yolo(testMeBro, tester01).)

# GUI tests (the worQt.qtest harness — NOT pytest). The user runs these.
PYTHONDONTWRITEBYTECODE=1 python -m worQt.qtest tests.test_cad.test_cad
# Whole suite via the cutely-named runner (the user runs it):
PYTHONDONTWRITEBYTECODE=1 python -c "from worQt.qtest import testMeBro; testMeBro()"
```

**Hard rules (worQt memories — obey):**

- Always prefix python with `PYTHONDONTWRITEBYTECODE=1`.
- **Do not run the test suite yourself** — the user runs it; hand execution
  back. (Exception: headless *probes* under `QT_QPA_PLATFORM=offscreen` for
  your own verification are fine; they are not "running the tests".)
- Two-space indent, **≤77 cols**, `camelCase` vars, `PascalCase` classes,
  single quotes for identifiers in prose (never backticks in
  code/docstrings), `from __future__ import annotations`, pipe unions in
  real annotations (not `Optional`; `param: T = None` is fine, don't rewrite
  it), no `exec/eval/__import__`.
- **No kwargs** anywhere in worQt — positional args only, including
  AttriBox/Qt constructors. (Defining `def f(x, y=None)` is fine; *calling*
  `f(y=1)` is not.)
- `'True if x else False'` is deliberate (don't collapse to `bool(x)`).
- Never `if widget:` — truthiness of a `BaseWidget` raises
  (`MixinBase.__len__`). Use `if widget is not None:`.
- **No novel single-word dunders** — qualify backing names
  (`__setting_value__`, not `__value__`).
- UI: prefer **conventional idioms (tabs)**; the user reacted very badly to
  checkbox-collapsible group boxes. Don't split tightly-coupled panels
  (a list and its editor) across tabs.

## 3. Headless verification technique (used constantly)

No Wayland/X in the sandbox, so drive the GUI under the offscreen platform
with **synchronous event stubs** and render to PNG (read it back as an
image):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src QT_QPA_PLATFORM=offscreen python -u - <<'PY' 2>&1 | grep -v propagateSizeHints
import os, tempfile
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF, QSettings
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, tempfile.mkdtemp())
app = QApplication.instance() or QApplication([])
from worQt.cad import CADWindow              # or: from worQt.cad import CADApp
from worQt.cad.draw import loadScene, Node
w = CADWindow(); w.show(); c = w.canvas; c.resize(520, 420)
w._selectTool('Node')                        # tool names: §6 KINDS + support/load/select/navigate
w.addItem(Node(0.0, 0.0)); w._rebuildLists()
c.grab().save('/tmp/x.png')                  # window-level: w.grab()
PY
```

- Redirect `QSettings` to a tempdir (above), or the persisted geometry /
  splitter state restored in `show()` will override your layout. The probe
  scripts in this session do `s = CADWindow()._settings();
  s.remove('splitter/state'); s.remove('main/geometry'); s.sync()` for a
  clean "fresh user" render.
- Qt signals fire synchronously: calling
  `mousePressEvent`/`mouseMoveEvent`/`mouseReleaseEvent` with the stub
  drives the real logic. A timer+`exec()` probe **hangs** under offscreen —
  use synchronous calls + `grab()`.
- The qtest tests use the same stubs: `_MouseEvent`/`_WheelEvent` at the top
  of `tests/test_cad/test_cad.py`.
- **`deleteLater()` does not free a widget under `processEvents()` alone** —
  flush `QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)`
  (this bit us in the test teardown, §12).
- `isVisible()` reflects the *shown* state (widget + all ancestors shown),
  **not** the rendered size — a widget on a non-current tab reads
  `isVisible() == False`. This matters for the tab layout (§8).

## 4. File layout

The example app lives **entirely** under `src/worQt/cad/`. The non-`cad`
trees are the reusable framework.

```
src/worQt/cad/                   THE structural-CAD example app
  __init__.py        exports everything (draw, fea, icons, panels, CADWidget,
                     CADWindow, CADSettings, CADApp) — the one strip point
  _cad_app.py        CADApp(AbstractApplication) — window=CADWindow,
                     settings=CADSettings; loads settings on __enter__ (§9)
  _cad_window.py     CADWindow — composes the whole UI (§8)
  _cad_widget.py     CADWidget — the canvas (the big one, ~1500 lines, §7)
  _cad_settings.py   CADSettings(Settings) — colours + view defaults (§10)
  _selection_tool.py SelectionToolPanel — the FOUR item lists + show
                     checkboxes + Clear all (§8)
  _new_item_tool.py  NewItemToolPanel — the state-driven per-type editor (§8)
  _view_tool.py      ViewToolPanel — grid/snap/spacing/reset/factor readout
  _vertex_editor.py  VertexEditor — stack of (x, y) rows, greys surplus rows
  _tool_icons.py     navigate/select/node/support/load/module/member/dim/angle
  draw/                  PURE 'dead' drawing primitives (no Qt) — mm geometry
    _items.py      Node, ModuleLine, Member, Dimension, AngularDimension
    _scene.py      CADScene (AttriBox[list] of items; addItem/clear/iter/len)
    _factory.py    KINDS, HINTS, parseNumbers, itemFromCoords, buildItem,
                   describeItem, itemAttrs, applyAttrs
    _serialize.py  sceneToData/FromData, sceneToJson/FromJson, saveScene/load
    __init__.py    exports the above (NOT CADSettings — one level up)
  fea/                   PURE 2D truss FEA core (no Qt, no numpy) — a preview
    _linalg.py     matVec, solveLinear (Gaussian elim, partial pivot)
    _elements.py   Material, Section, Node, Bar  (its OWN Node, §9 — NOT
                   draw.Node; simple per-DOF fixX/fixY)
    _truss.py      Truss (assemble + solve), TrussSolution
    __init__.py
src/worQt/settings/              generic, Qt-free settings system (§10)
  _config_path.py  configPath(appName) — OS-specific dir, XDG/Arch fallback
  _toml.py         tiny dependency-free TOML reader/writer
  _setting.py      Setting(BaseDescriptor[T]) — one typed setting, Setting[T](x)
  _settings_tab.py SettingsTab — a 'tab' (pane) of related settings
  _settings.py     Settings — tabs + persistence (save/load), appName -> path
  _settings_cache.py  small caching helper
src/worQt/widgets/               GENERIC base widgets (NOT the CAD panels)
  _base_widget.py  BaseWidget = QWidget + MixinBase (the fusion base)
  _container.py    Container(BaseWidget) — AttriBox(THIS) host (§13)
  _settings_dialog.py SettingsDialog — VLC-style tabbed settings editor (§10)
  _value_edits.py  reusable per-type value editors
src/worQt/window/_main_window.py generic base window (NOT CADWindow)
src/worQt/app/                   the application bases (NOT CADApp)
  _application_mixin.py  ApplicationMixin(QApplication, MixinBase)
  _abstract_application.py AbstractApplication — shared lazy handles:
                   returnCode / splash / window / settings (§9)
  _app.py          App — generic demo app (kept)
src/worQt/qtest/                 the bespoke GUI test harness (§12);
                 __init__ exposes testMeBro() — runs the whole suite
src/worQt/__main__.py            'python -m worQt' -> CADApp (§2)
tests/test_cad/                  the CAD example's tests
  test_cad.py        one TestCAD(AppTest) — ~100 methods (§13)
  test_cad_app.py    TestCADApp(BaseTest) — app wiring
  test_cad_settings.py TestCADSettings(BaseTest) — settings schema/drift
  test_truss.py      TestTruss(BaseTest) — pure FEA, runs in-process
tests/test_settings/             pure settings/codec/path tests
tests/test_app/                  generic app tests
main.py  tester01                launches CADApp
```

## 5. Boundary conditions: the six-state node model + SET/INDUCED notation

This is the heart of the rework. A `Node` is **one of six states**, the
cross of a **translational** support and a **rotational** release:

```
translation:  free  |  roller  |  pinned
rotation:     released (charniere)  |  locked
```

- `free` + locked is the **neutral** internal joint (moment traverses two
  members rigidly). `pinned` + locked = **fixed / encastre**. `roller`
  needs a direction.

**Locked-in notation (do not drift).** Split everything into what you
**SET** (the boundary condition you impose) vs what the analysis
**INDUCES** (the response). Translations are vectors, rotations are scalars.

| quantity            | SET (imposed)        | INDUCED (response)   |
|---------------------|----------------------|----------------------|
| translation (disp)  | `x`, `y`             | `u`, `v`             |
| rotation            | `xy`                 | `uv`                 |
| force               | `F = (Fx, Fy)`       | `R = (Rx, Ry)` react |
| moment              | `Mf`                 | `Mr` reaction        |

**The model stores ONLY the SET side.** The FEA induces `u,v,uv,R,Mr`; worQt
never stores them. A locked DOF carries a SET displacement (default 0); a
free DOF carries a SET load. Per state:

- **free** → applied force load `F = (loadX, loadY)`.
- **roller** → a locked direction `theta` (deg); a SET displacement
  `rollerSet` along theta (settlement) and a SET force `rollerLoad` across
  it (along the rolling direction).
- **pinned** → SET displacement (settlement) `(dispX, dispY)`.
- **rotation**: `released` (charniere) keeps a SET moment `Mf = loadMoment`
  (rotation free); `locked` keeps a SET rotation `xy = setRot`.

### `Node` (`worQt.cad.draw._items`)

A pure `worktoy.BaseObject`, Qt-free, mm. `AttriBox` fields:

```
x, y                       # position
supportType  'free'|'roller'|'pinned'   (default 'free')
released     bool          # charniere: rotation released if True (default True)
theta        float         # roller locked direction, degrees
loadX, loadY float         # F: applied force (free state)
dispX, dispY float         # x, y: SET settlement (pinned state)
rollerSet    float         # x: SET displacement along theta (roller)
rollerLoad   float         # F: SET force across theta (roller)
setRot       float         # xy: SET rotation (when locked)
loadMoment   float         # Mf: SET moment (when released)
```

- `supportKind()` → `'free'` / `'roller'` / `'pinned'` / `'fixed'`
  (`'fixed'` is pinned **and** not released — the encastre).
- `cycleSupport()` → advances translation `free → roller → pinned → free`
  (the quick click gesture); the charniere is left to the editor.
- `__str__` reflects the state, e.g. `Node(5, 5) roller@30 d-2 F15`,
  `Node(0, 0) pinned`, `Node(2500, 2500) rot-locked F(0, -1000)`.

`ModuleLine`, `Member`, `Dimension`, `AngularDimension` are unchanged in
spirit:

- **`ModuleLine(x, y, angle)`** — **infinite** datum line through `(x, y)`
  at `angle` deg (0 horizontal, 90 vertical). `direction()` → unit
  `(dx, dy)`. Drawn as a prominent super-gridline.
- **`Member(nodeA, nodeB)`** — a structural element holding **references**
  to two `Node`s (`AttriBox[Node]`). Coordinates `x1/y1/x2/y2` are
  **read-through `Field`s** (`x1` GET → `nodeA.x`), so **moving a node moves
  every member on it**. `length()`.
- **`Dimension(x1, y1, x2, y2)`** — linear; `length()`.
- **`AngularDimension(vx, vy, ax, ay, bx, by)`** — vertex + two arms;
  `angle()` in `[0, 180]`.

`CADScene` holds items in `items` (`AttriBox[list]`); `addItem`, `clear`,
`__iter__`, `__len__`.

## 6. Factory + serialization (`worQt.cad.draw`)

### Factory (`_factory.py`) — single source for kind handling

- `KINDS = ('Node', 'Module', 'Member', 'Dimension', 'Angle')` (was
  `'Anchor'`). `HINTS` keyed the same.
- `parseNumbers`, `itemFromCoords(kind, text)` (flat numbers; `Module` is
  `x, y, angle`; **`Member` raises** — it needs nodes, not coords).
- `buildItem(kind, vertices)` → from `(x, y)` vertices (Node 1, Module 2 =
  origin + through-point, Dimension 2, Angle 3). **`buildItem('Member', …)`
  raises** — build members with `Member(a, b)` directly.
- `describeItem(item)` → `(kind, vertices)`; a module reports
  `[origin, origin + unit-dir]`; a member reports its read-through coords
  (for display, **not** rebuild).
- **`itemAttrs(item)` / `applyAttrs(item, attrs)`** — the non-geometric
  channel. For a `Node`: `supportType` (when not `'free'`), `released`
  (when `False`), and the **non-zero** of `theta, loadX, loadY, dispX,
  dispY, rollerSet, rollerLoad, setRot, loadMoment`. Minimal files: a plain
  free node stores no `attrs` at all.

### Serialization (`_serialize.py`) — JSON, no pickling

- `sceneToData`: each item → `{kind, vertices, attrs?}`; **a member →
  `{kind:'Member', nodes:[i, j]}`** where `i,j` are scene indices.
- `sceneFromData`: **two-pass** — build everything except members first,
  then members resolving node indices to the rebuilt nodes. Atomic (raises
  before touching the target scene). Into a given scene = clear + refill in
  place (keeps scene identity).
- `sceneToJson`/`sceneFromJson`/`saveScene`/`loadScene`.
  `__format_version__ = 1`.
- **This path also powers undo/redo** (snapshots are `sceneToData` dicts),
  so member references survive undo/redo and save/load — the member follows
  the *rebuilt* node.
- Output is **compact JSON** (no `indent=`, keyword-only under the no-kwargs
  rule). Still legible: `{"kind":"Member","nodes":[0,2]}`.
- **View state is NOT here** — the window adds a top-level `"view"` block
  on save and reads it on load (§8). `sceneFromData` ignores unknown keys,
  so a scene-only file and a window-saved file both round-trip.

When adding a new kind: class + export + `KINDS`/`itemFromCoords`/
`buildItem`/`describeItem` + (if it has extra fields)
`itemAttrs`/`applyAttrs` + the canvas paint/glow/halo/bounds/hit-test/snap
branches + `_INITIAL_DEFAULTS` + a toolbar icon + the list partition in
`CADWindow._listFor`. (Reference-based items like members skip the vertex
path.)

## 7. The canvas: `CADWidget` (`_cad_widget.py`)

`class CADWidget(BaseWidget)`. Owns a `CADScene`, the view transform, and the
view/visibility flags. Reads its palette from a `CADSettings` (`settings`
field) via `_color(name)` — every paint asks the settings, so editing a
colour repaints (see §10).

### Units, transform, zoom, grid

- World = mm; `scale` = px/mm (default 1.0). `worldToScreen`/`screenToWorld`
  (world y up, screen y down — flipped). `viewFactor()` = 1/scale.
- **Integer-factor zoom ladder**: `_levelToScale`/`_scaleToLevel`/
  `_snapScaleDown`; `wheelEvent` steps one rung (cursor-anchored via
  `_applyScaleAt`); `zoomAt` continuous (tests). `__min_scale__=0.1`,
  `__max_scale__=4000`.
- Grid: `gridStep() = gridTargetPx / scale` (zoom-invariant px,
  `gridTargetPx` default 24). `fitAll()` = zoom-to-extents.
- **`focusOn(item)`** — frame one item with surroundings, used when a list
  row is selected (§8). `_itemBounds` gives the item box;
  `_focusMargin(w, h)` = `max(0.15·sceneSpan, 0.75·max(w,h), 250 mm)`
  (`_sceneBounds` gives the scene span), then `fitWorldRect` with that
  margin. A point node still reveals its neighbourhood; a module line
  (infinite, bounds `None`) leaves the view unchanged.

### Per-category visibility

Four flags + setters: `showNodes` / `showElements` / `showGuides` /
`showDimensions` (`AttriBox[bool](True)`); `setShowNodes` … each set the
flag and `update()`. The window wires the four "show" checkboxes to these
(§8). Paint honours them via `_categoryShown(item)` (Node→showNodes,
Member→showElements, Dimension/Angular→showDimensions; module lines are
handled as guides).

### Object snapping (gated on `snapToGrid`, screen px, `__snap_px__=10`)

`_worldAt(pos)` resolves the pointer in **priority order**:

1. **Nodes** (`_snapToNode` over `_snapNodes`): every node **plus every
   module-line ∩ module-line intersection** (`_lineIntersection`). Exact.
2. **Infinite module lines** (`_snapToModuleLine`, unclamped projection via
   `_closestOnLine`).
3. **Dimension/member segments** (`_snapToSegment`, clamped;
   `_snapSegments` yields member + dimension bodies and angular-dim arms).
4. **Grid** (`snap()`).

Snap-lines: the gridlines through the snapped node (and the drag start) in a
brighter same-hue shade (`_paintSnapLines`, tracked via `__hover_world__`).

### Modes (`setMode`, cursor via `_updateCursor`)

`'navigate'` (pan), `'select'` (pick via `_itemAt`, 8px), `'draw'`,
`'support'`, `'load'`.

- **Node** → double-click places one (`mouseDoubleClickEvent`).
- **Module / Dimension** → press-drag (`_gestureVertices` → 2 vertices). A
  **dimension started on a module line locks perpendicular** to it
  (`_perpNormalsAt` at press; `_applyPerp` projects; `_paintPerpMark` draws
  the tick).
- **Member** → **node→node drag** (`__member_start__`/`__member_current__`,
  `_nodeAt` picks the nodes; commits via `setMemberCallback(a, b)`; release
  off a node or on the same one adds nothing; `_paintMemberPreview`).
- **Angle** → three clicks (`__angle_points__`, `_addAnglePoint`).
- **Support mode**: a **click** cycles the support
  (`setSupportCallback(node)` → `cycleSupport`); a **drag** sets a
  settlement (`setDisplaceCallback(node, dx, dy)`). State:
  `__support_node__`/`__support_press__`/`__support_current__`.
- **Load mode**: drag a force out of a node (`__load_node__`,
  `setLoadCallback(node, fx, fy)`); a near-zero click **clears** the load.
- **`_forceTip(pos, node)`** snaps the force/settlement vector to the
  nearest axis when `snapToGrid` is on — shared by load + settlement.

**`_itemAt` gives nodes priority.** A member runs *through* its two nodes,
so at a shared endpoint the cursor is ~0 px from both; `_itemAt` tracks the
nearest node and the nearest non-node separately and returns the node
whenever one is within tolerance — otherwise the endpoint could never be
picked.

### Painting (`paintEvent` order)

background → `_paintGrid` (+ snap-lines) → **(if `showGuides`)
`_paintModuleLines`** (infinite super-gridlines via `_infiniteEnds`) →
`_paintAxes` → **(if `showGuides`) `_paintNodeGuides`** → items
(`_paintItem`; module lines skipped; an item whose `_categoryShown` is False
is skipped) with glow/halo on the selected one → previews.

- **Node marker** (`_paintNode`) reads the rotational continuity: a **rigid**
  node (`released == False`, the neutral case) is a **small filled dot**
  (`__node_dot__ = 3`); a **charniere** node (`released == True`) is a
  **larger background-filled ring** (`__node_radius__ = 5`) — the hinge /
  moment release. The old crossed-circle is gone from the marker.
- **Guides** (`_paintNodeGuides` / `_paintNodeGuide`): when guides are
  shown, every node also gets the **crossed-circle guide glyph** (the old
  anchor symbol) — drawn independently of `showNodes`. So "Guides" = module
  lines **and** the node crossed-circles.
- **Oriented support glyph** (`_paintSupport`, `_supportAxis`, `_memberSum`):
  a triangle whose axis is the held direction over a base. A **roller**
  aligns with its locked `theta` (rollers on a sliding ground line ⟂ theta).
  A **pin / encastre** faces *opposite* `S = Σ` unit directions to the
  connected members (seeded world-up `(0, 1)` so a lone support faces down),
  so its hatched ground sits ⟂ to what it braces. The rotational state (pin
  vs encastre) is carried by the **node marker** (ring vs dot), not repeated
  on the glyph: ring + triangle = pinned, dot + triangle = fixed.
- `_paintDisplacement` (dashed fixed-length arrow + `d <mag>`), `_paintLoad`
  (solid arrow + `<mag> N`). Arrows are **fixed pixel length** (legible at
  any zoom); the number carries the value.
- `_paintMember` = solid line. Glow/halo treat member+dimension+angle like
  lines; nodes get a point glow. `_itemBounds`: node = point,
  member/dimension = bbox, **module line = None** (infinite → never drives
  auto-fit) → `ensureContains`/`fitAll`/`focusOn`.

### Callbacks the window registers (canvas stays UI-agnostic)

`setHoverCallback`, `setDragCallback`, `setAddCallback(kind, vertices)`,
`setMemberCallback(a, b)`, `setPickCallback(index)`, `setDeleteCallback`,
`setSupportCallback(node)`, `setLoadCallback(node, fx, fy)`,
`setDisplaceCallback(node, dx, dy)`, `setViewChangedCallback`.

## 8. The window: `CADWindow` (`_cad_window.py`)

`class CADWindow(QMainWindow, MixinBase)`.

### Layout — a tabbed tool panel beside the canvas

`_buildCentral` = a horizontal `QSplitter` of **[tabbed tools | canvas]**
(`setChildrenCollapsible(False)` so the tool column never drops to zero;
this also clamps a stale restored splitter state that once zeroed a pane).
The left pane is a **`QTabWidget` with TWO tabs**:

- **Selection** — a plain `QWidget` whose `QVBoxLayout` stacks the
  `SelectionToolPanel` (the four lists, **stretch 1**) ABOVE the
  `NewItemToolPanel` (the editor). The editor is given
  **`QSizePolicy.Maximum`** so it stays at its natural height instead of
  stretching; the lists absorb the slack. (History: this went through a
  bad checkable-collapsible-groupbox phase and a worse three-tab phase —
  the user wanted the list and its editor **together**, so the editor lives
  *in* the Selection tab.)
- **Viewer** — the `ViewToolPanel`.

`__tab_index__` maps `'selection'`/`'view'` to tab indices; `'newItem'` is
routed to the **selection** index (the editor shares that tab). `_showTab`
switches; the canvas has `StrongFocus` for the Delete key.

### The four lists (`SelectionToolPanel`)

Four `QListWidget`s — `nodeList`, `elementList`, `guideList`,
`dimensionList` — each under a header pairing a `QLabel` with a `'show'`
`QCheckBox` (`showNodesCheck`/`showElementsCheck`/`showGuidesCheck`/
`showDimensionsCheck`), plus `clearButton`. `CADWindow._listFor(item)`
partitions: `Node`→nodes, `Member`→elements, `ModuleLine`→guides,
`Dimension`/`AngularDimension`→dimensions. The show checkboxes wire straight
to `canvas.setShow*`.

Because two lists no longer run parallel to scene order, **each row stores
its scene index in `Qt.UserRole`**. Helpers: `_rebuildLists` (clear +
re-partition from the scene), `_addToLists` (append one, index =
`len-1`), `_entryForIndex` (find `(list, row)` for a scene index),
`_refreshRow` (re-render one row's text after an edit), `_selectListRow`
(reflect a canvas pick into the right list, clear the others),
`_clearListSelection`.

**Selecting a list row** (`_onSelectListRow`): clear the other lists'
highlights, `_selectItem(index)`, then **`canvas.focusOn`** — so picking a
node/member/guide/dimension from a list **zooms the canvas to frame it with
surroundings**. A canvas pick (`_pickItem`) reflects into the list *without*
re-zooming (you are already looking at it).

### Menus & toolbar

- **File**: Open (Ctrl+O) · Save (Ctrl+S) · Rename (Ctrl+R) · Quit.
  **Edit**: Undo (Ctrl+Z) · Redo (Ctrl+Shift+Z). **View**: Reset /
  Delete-selected / Clear / **Selection tab** / **Viewer tab** (the old
  show/hide toggles are now plain tab switches: `_onShowSelection` /
  `_onShowView` → `_showTab`).
- Toolbar order: **Navigate · Select · Node · Support · Load · Module ·
  Member · Dimension · Angle** (exclusive `QActionGroup`, `setData(name)`,
  `__tool_actions__`). `_applyTool`: `navigate/select/support/load` set the
  mode; a kind sets draw mode + `setActiveKind` + `configureFor`.

### Bespoke, state-driven editor (`NewItemToolPanel`)

`_show(*sections)` toggles `vertex/coord/state/info/members/add`.
`_selectItem(index)` dispatches by type:

- **Node** → `editNode(node, members)`: editable `x`/`y`, a Translation
  `transCombo` (Free/Roller/Pinned) + a `charniereCheck`, and a
  **`QStackedWidget` (`stateStack`)** of per-state fields — `freeHost`
  (`Fx`/`Fy`), `rollerHost` (a grid: `theta` / set disp / across F),
  `pinnedHost` (set `x` / set `y`) — plus a `rotHost` (label flips
  `Mf`↔`xy`), a read-only `support: <kind>` label, and a list of attached
  members. `_refreshState` swaps the stack page **and shrinks the stack to
  that page's height** (`setFixedHeight(page.sizeHint().height())`) so the
  short states leave **no reserved gap** — this is what makes the editor
  compact (Maximum policy alone did nothing, because the lists already
  absorbed the slack; the tall `sizeHint` from the stack reserving the
  roller height was the real culprit). `applyTo(node)` writes only the
  active state's SET quantities and zeroes the rest, in place via
  `_updateNode` — the node keeps identity, so members keep referencing it.
- **Member** → `editMember(info)`: shows `Node A:` / `Node B:` (read-only).
  **No coordinate edit, no Update** — only Delete.
- **Dimension / Angle** → `loadItem(kind, vertices)`: the vertex editor;
  Update → `_replaceItem` (rebuilds the item).

### New / Edit / Delete / cascade

- `__edit_index__` tracks the edited row. `_enterEditMode` shows the
  **Delete button** + "Update item" and `_showTab('newItem')` (brings the
  Selection tab to front so the editor is visible); `_enterNewMode` hides
  Delete + "Add item".
- `addItem(item)` is the single funnel: `_pushUndo` → `scene.addItem` →
  `_refreshDirty` → `ensureContains` → `_addToLists`. `_onAddMember(a, b)` →
  `addItem(Member(a, b))`.
- **`_deleteSelected` cascades**: deleting a node removes every member that
  references it, as **one undo step**; then `_rebuildLists` (indices
  shifted).

### Undo/redo (snapshot-based)

`_pushUndo` snapshots `sceneToData` before each mutation (cap
`__undo_limit__=100`, clears redo); `_onUndo`/`_onRedo` swap snapshots and
`_restoreSnapshot` (rebuilds via `sceneFromData`, `_rebuildLists`, returns
to New mode); `_clearHistory` on Open; `_updateUndoActions` toggles the menu
items. Wired at the mutation funnels and on support/load/settlement changes.

### Unsaved-changes guard (saved-state-aware `dirty`)

`dirty = AttriBox[bool]`. `__saved_state__` holds `sceneToData` of the
last-saved/loaded scene (set by `_markSaved`). `_refreshDirty` recomputes
dirty by comparing the current scene to the baseline — so undoing back to
the saved state reads clean. (Dirty tracks **scene items only**; toggling a
view checkbox does not mark the document dirty.) `_confirmDiscard`
(Save/Discard/Cancel; True at once when clean) gates `closeEvent` and
`_onOpen`. Save/Rename return a bool; cancelling aborts.

### File open/save — scene **and** view state

`_onSave` (silent, to `__file_path__`; an untitled model routes to Rename
first) / `_onRename` (dialog, **moves** the file, no "Save As") / `_onOpen`
(dialog, replaces scene) go through **`_writeScene(path)` / `_readScene`**,
which wrap the scene serializer with a top-level `"view"` block:

- `_viewState()` → `{showNodes, showElements, showGuides, showDimensions,
  showGrid, snapToGrid, gridTargetPx}` (all booleans via `'True if x else
  False'`, the spacing as float).
- `_applyViewState(view)` restores the canvas flags (missing/empty block →
  defaults stand), then `_syncViewControls` reflects them onto the four show
  checkboxes, the grid/snap checkboxes and the spacing control (signals
  blocked).

`_onOpen` then `_rebuildLists`, `_enterNewMode`, `fitAll`, `_clearHistory`,
`_markSaved`. `_settings`/`_saveGeometry`/`_restoreGeometry` persist window
geometry + splitter state to QSettings (`~/.config/worQt/draw.ini`); `show()`
restores them and opens on the Selection tab.

## 9. App & launch

**`AbstractApplication` owns the shared, lazily-built handles** —
`returnCode`, `splash`, `window`, `settings` — each via the worktoy
`_recursion` lazy getter. The per-app *types* come from two class hooks:
`__window_class__` and (optional) `__settings_class__`, read through
`getWindowClass()`/`getSettingsClass()` so the getter + type-check live once.

`CADApp(AbstractApplication)` (in `cad/_cad_app.py`) sets
`__window_class__ = CADWindow` and `__settings_class__ = CADSettings`. It is
a context manager: `__enter__` **loads the saved settings over the
defaults** then returns self; `__exit__` runs `exec()` on a clean exit (a
raising with-body skips the loop and propagates). `python -m worQt`
(`__main__.main`) does `with CADApp(*sys.argv) as app: app.window.show()`.

Because `MixinBase.app` returns the running `QApplication`, **any widget or
window reaches the settings via `self.app.settings`** — no globals. (Under a
bare `QApplication` in tests, the canvas keeps its own default `CADSettings`
via `_useAppSettings`.)

### The FEA core (`worQt.cad.fea`) — a preview, not the target

`fea` is a small **pure (Qt-free, numpy-free) 2D truss solver** kept as a
cheap in-app sanity-check. **Its `Node` is its own simple per-DOF node** —
`fixX`/`fixY`/`loadX`/`loadY` with `pin()`/`roller(horizontal)`/`addLoad` —
**distinct from `draw.Node`** (the six-state CAD node). They live in
separate subpackages and are never flat-imported together.

- `_linalg.py`: `matVec`, `solveLinear` (Gaussian elimination, partial
  pivot; raises `ValueError` "singular / mechanism" on a near-zero pivot).
- `_elements.py`: `Material(E)` MPa, `Section(A)` mm², `Node(x, y)`,
  `Bar(a, b, material, section)` (`length`, `cosines`, `axialStiffness`,
  `globalStiffness` 4×4, `axialForce`).
- `_truss.py`: `Truss` (`addNode`/`addBar`/`assemble`→(K,F)/`solve`),
  `TrussSolution` (`displacements`, `reactions`, `forces`). Units **mm / N /
  MPa**. Verified analytically; tests in `tests/test_cad/test_truss.py`.

## 10. The settings system (`worQt.settings` + `CADSettings`)

A generic, **Qt-free** settings framework, separate from the CAD app:

- `Setting` is a `BaseDescriptor[T]` declared `Setting[T](default)`: the
  subscript fixes the value type, the call the default; `valueType` /
  `default` / `value` are typed `T`, assigning `value` coerces. Backing
  dunders are qualified (`__setting_value__`, etc. — no single-word dunders).
- `SettingsTab` ('tab' = a pane) groups related settings; `tab.define(name,
  default).withLabel(text)` builds one and infers `T` from the default.
- `Settings` holds named tabs and persists them: `save()`/`load()` reflect
  to `configPath(appName)` — OS-specific (`~/Library/Application Support`,
  `%APPDATA%`, else XDG `~/.config`) — in a dependency-free **TOML** dialect
  (`_toml.py`), one `[tab]` table per pane. Missing file = no-op.
- `CADSettings(Settings)` is the CAD schema (`Settings.__init__(self,
  'worQtCAD')` → `.worQtCAD.config`):
  - **Colours** tab (13 keys, str hex): `background #1e1e1e`, `grid
    #2a3628`, `axes #3a3f4b`, `module #6f9a58`, `moduleSelected #a6e07a`,
    `node #c678dd`, `member #61afef`, `support #56b6c2`, `load #e06c75`,
    `settlement #d19a66`, `dimension #ffd24a`, `preview #e5c07b`, `halo
    #ffe082`.
  - **Defaults** tab: `gridTargetPx 24`, `snapPixels 10`, `pointRadius 4`,
    `nodeRadius 5`, `perpTolPx 2`, `defaultScale 1.0`, `minScale 0.1`,
    `maxScale 4000.0` — mirroring the `CADWidget` constants; a drift-guard
    test asserts they stay equal.
- `SettingsDialog` (in `worQt.widgets`) renders any `Settings` VLC-style: a
  tab list on the left, the page on the right, each setting drawn by the
  reused `_value_edits`. Ok/Apply/Cancel/Restore-defaults; **Apply** enabled
  only while dirty, writes through to the model and its file.

The canvas already reads its palette live from `settings` via `_color`, and
the four view toggles + grid/snap/spacing already round-trip in the document
`"view"` block (§8). **Still missing**: a Preferences (`Ctrl+,`) action
wiring `SettingsDialog` to `self.app.settings`, and pushing dialog-edited
colours/defaults onto the live `CADWidget` constants.

## 11. Units / colours cheat-sheet

- 1 px = 1 mm at default zoom; grid 24 px target; zoom rungs …1/3, 1/2, 1,
  2, 3.
- Model units: mm / N / MPa.
- Node marker: rigid = small filled dot (r 3), charniere = hollow ring
  (r 5). Guide overlay = crossed circle (r 5) when guides shown.
- Colours: see the `CADSettings` Colours tab above (§10) — the single source
  of truth; `CADWidget` holds **no** colour constants.

## 12. The qtest harness (`src/worQt/qtest/`) — IMPORTANT, it's bespoke

Not pytest. The runner discovers `test*`/`run*` modules under `tests/` and
runs **exactly ONE `Test*`/`Run*` class per module** (`AppTestSuite.getNamed`
raises on more than one — to split a class, split into separate *files*).

- **`AppTest(BaseTest, metaclass=MetaTest)`** — base for GUI tests needing a
  `QApplication`. One shared `QApplication` per class; `runTest()` runs every
  method inside one `app.exec()` loop (`_runMethod` = setUp → method →
  tearDown). `__time_out__ = 30.0`. **Scoped per-test cleanup**: `setUp`
  snapshots open top-levels (`__preopen__`); `tearDown` disposes **only the
  widgets this test opened** via `hide()` + `deleteLater()` +
  `sendPostedEvents(None, QEvent.Type.DeferredDelete)` + `processEvents()`.
  **Never `close()` a `CADWindow`** in a test — `closeEvent` runs the
  unsaved-changes modal (hangs headless) and writes QSettings; use
  `deleteLater`.
- **`AppTestRun.run()`** — deadline + dispatch: a Qt `AppTest` →
  `_runPopen` (a fresh `python -m worQt.qtest <module>` child with
  `communicate(timeout=…)`; timeout `killpg`s the group). A plain
  `BaseTest`/`TestCase` (e.g. `TestTruss`, `TestCADApp`, `TestCADSettings`)
  → `_runPlain` (in-process `unittest.TextTestRunner`, no Qt). Same
  `(code, output)` contract: 0 pass / 3 fail.
- **`testMeBro()`** runs the WHOLE suite via `runAll`, routing Qt `AppTest`s
  to subprocesses and plain `BaseTest`s in-process — the cutely-named
  one-call entry the user runs.

## 13. Tests (`tests/test_cad/`)

- **`test_cad.py`** — one `TestCAD(AppTest)` (~100 methods). Covers:
  model/factory for every kind; the **six-state node** (cycle, charniere,
  roller `theta`/rollerSet/rollerLoad, fixed, `Mf`/`xy`, JSON of `attrs`);
  transform/zoom/grid/snap (node/intersection/module-line/point/segment +
  perpendicular-dim lock); members (drag-create, reference identity,
  drag-to-empty rejects, cascade delete, JSON by node index, read-through
  follow); supports/loads/settlements (click cycle, drag, axis-snap,
  click-clear, JSON); **node-wins-over-member** pick at a shared endpoint;
  the **four lists** (type partition, row→scene-index mapping, list-row
  select → focus); the **two-tab** layout (lists + editor in the Selection
  tab; Viewer tab; View-menu tab switches); the **state-driven editor**
  (in-place node edit, member shows nodes only, delete button); the
  **`view`-block round-trip** (visibility/grid persist; a no-`view` file
  keeps defaults) and node-BC round-trip through the window save; undo/redo
  + saved-state dirty; geometry persistence. Drive with
  `_MouseEvent`/`_WheelEvent`; assert `grab()` non-null.
- **`test_cad_app.py`** `TestCADApp(BaseTest)` — app wiring; **`test_truss.py`**
  `TestTruss(BaseTest)` — pure FEA; **`test_cad_settings.py`**
  `TestCADSettings(BaseTest)` — settings schema + the colour/defaults
  drift-guard.
- **Gotcha:** undo/redo rebuild scene objects via `sceneFromData`, so after
  an undo/redo **re-fetch** the live item from `scene.items` — don't keep a
  stale reference.

## 14. worQt gotchas that bit us (and the fixes)

- **`AttriBox[T](THIS)` — FIXED in worktoy 1.0rc9.** A captured sentinel
  (`THIS`/`OWNER`/`DESC`) **always constructs** `T(owner)` — a real child
  parented to the owner (pre-rc9 it aliased the owner when the owner was
  already a `T`). The `Container(BaseWidget)` host (used for the editor's
  per-state hosts and headers) is therefore **optional**, not required.
- **`QStackedWidget` sizes to its tallest page by default** → a short page
  leaves a reserved gap. To make the editor compact, `setFixedHeight` to the
  **current** page's `sizeHint().height()` on every switch (§8). Note: a
  `Maximum` size policy on a stretch-0 panel does **nothing** when a sibling
  has stretch 1 — the sibling already eats the slack; you must shrink the
  panel's `sizeHint`, not just cap it.
- **`QSplitter` restore can zero a pane.** A persisted `splitter/state` from
  an older layout, restored in `show()`, once collapsed a column to 0;
  `setChildrenCollapsible(False)` clamps it to the minimum.
- **UI conventions matter to the user.** Checkbox-collapsible group boxes and
  splitting a list from its editor across tabs were both rejected hard. Use
  tabs; keep coupled panels together.
- **Read-through fields**: `Member.x1` etc. are worktoy `Field`s whose GET
  reads `nodeA.x` — that's how members follow their nodes. `AttriBox[Node]()`
  holds the reference (default-constructs a throwaway `Node()` until
  assigned).
- **Reference identity through undo/serialize**: members serialize/rebuild
  by **node index** (two-pass), so a restored member references the
  *restored* node. Edit a node **in place** (`_updateNode`), never
  `_replaceItem` (a new object orphans members).
- **QObject in a class body segfaults pre-QApplication** → all Qt widgets
  live in `AttriBox` (built lazily); runtime-only widgets in methods.
- **`__name__`-style attrs** (`__rows__`, `__selected__`,
  `__member_start__`, `__pan_origin__`, `__click_origin__`, …) end in `__`,
  so they're NOT name-mangled — tests use `getattr(obj, '__x__')`. (The
  UI-sense "anchor" names — pan/click reference points — were renamed to
  `*_origin__` during the Node rename so they weren't swept.)
- **`json.dump(indent=…)` is keyword-only** → can't pass it under the
  no-kwargs rule → saved JSON is compact (still legible).

## 15. Status / next steps

- ✅ **Six-state node BC model** ({free, roller, pinned} × {released/locked})
  with the SET/INDUCED notation; `AnchorPoint`→`Node` renamed throughout
  (class, `'Anchor'`→`'Node'` kind, methods, icons, colour key, tests).
- ✅ Node markers (rigid dot / charniere ring), the crossed-circle as a
  **guide** overlay, **oriented** support glyphs (roller by `theta`,
  pin/encastre ⟂ to the summed member directions).
- ✅ Reference-based members, module lines, dimensions/angles; node-wins
  pick; object snap; perpendicular-dimension lock.
- ✅ **Four-list selection panel** (Nodes/Elements/Guides/Dimensions) with
  per-category **show** toggles wired to the canvas; **list-select →
  zoom-to-item** (`focusOn`).
- ✅ **Tabbed tool panel** (Selection [lists + compact editor] | Viewer);
  state-driven editor; cascade-delete; in-place node edit.
- ✅ JSON save/load of **scene + `view` state**; undo/redo; saved-state
  dirty guard; Save/Rename (move, no "Save As"); geometry persistence.
- ✅ Pure FEA truss solver (`worQt.cad.fea`, its own simple `Node`) as a
  preview; OpenSeesPy chosen as the real analysis target; qtest harness
  handles GUI + pure tests.
- ✅ Example-package consolidation under `worQt.cad`; settings system
  (`Setting[T]`/`SettingsTab`/`Settings`, TOML + OS path) + `CADSettings`
  (drift-guarded) + VLC-style `SettingsDialog`; settings on the app.
- ⏭️ Settings not yet **applied** to the live canvas from the dialog (push
  edited colours/defaults onto `CADWidget`); no Preferences (`Ctrl+,`) yet.
- ⏭️ **THE NEXT BIG PIECE: the OpenSeesPy exporter.** Each `Node` →
  `ops.node`; `supportType`/`released` → `ops.fix` (free = none, pinned =
  both translations, fixed/encastre = + rotation under `-ndf 3`); a
  **roller** fixes the single DOF along `theta` — axis-aligned is a plain
  `fix`, an **inclined** roller needs a nodal transformation / `equalDOF`
  (a real nuance); `loadX/loadY` (free `F`) → `pattern`+`load`;
  `dispX/dispY` and `rollerSet` (SET settlements) → `sp` single-point
  constraints; `loadMoment`/`setRot` → the rotational DOF (frames). Then
  `import openseespy.opensees as ops`, run in-process, read
  `nodeDisp`/`eleResponse` back, and draw the **deflected shape + member
  forces** on the canvas. The analysis-aggregation stack
  (`constraints`/`numberer`/`system`/`test`/`algorithm`/`integrator`/
  `analysis`) should be exposed as knobs. Material/section (E, A) still need
  a home (per-member, or a global default — currently the `fea.Bar`
  defaults: E 210000 MPa steel, A 100 mm²).
- ⏭️ Smaller: module-line **labels** (grid A/B/C · 1/2/3); multi-select;
  frame elements (`-ndf 3`, bending, `geomTransf` +
  `element('elasticBeamColumn', …)`) for full frames.

### OpenSeesPy reference (researched, current as of 2026)

Version `3.8.0.0`, `pip install openseespy` (meta-package), Python ≥3.10,
`import openseespy.opensees as ops`. The commands mirror the Tcl, as Python
calls:

```python
ops.wipe(); ops.model('basic', '-ndm', 2, '-ndf', 2)
ops.node(tag, x, y); ops.fix(tag, dofX, dofY)
ops.uniaxialMaterial('Elastic', matTag, E)
ops.element('Truss', eleTag, iNode, jNode, A, matTag)
ops.timeSeries('Linear', 1); ops.pattern('Plain', 1, 1)
ops.load(node, Fx, Fy); ops.sp(node, dof, value)   # imposed settlement
ops.system('BandSPD'); ops.numberer('RCM'); ops.constraints('Plain')
ops.integrator('LoadControl', 1.0); ops.algorithm('Linear')
ops.analysis('Static'); ops.analyze(1)
ux = ops.nodeDisp(node, 1)                          # member force: eleResponse
```

The scene → OpenSees mapping is **clean** because members are
reference-based: each node is a `node`; each member is an `element('Truss',
…)` between its two nodes' tags (**no endpoint dedup** — node identity is
explicit). Frames swap `-ndf 3`, add `geomTransf` + `elasticBeamColumn`.
