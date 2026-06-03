# cad_larping.md — the worQt structural drawing / FEA-modeller

A detailed manual for the coordinate-driven vector **drawing app** built in
`worQt` (a fusion of `worktoy` descriptors/overloads with PySide6). Written
so
a fresh context can pick up where we left off. Everything below is real and
on
disk; line numbers drift, names don't.

> **Status banner.** The app started as a generic 2D drawing toy (points,
> lines, regions). It has since been **rebuilt into a structural-engineering
> pre-processor**: you lay out reference geometry (datum lines, nodes), draw
> structural **members** between nodes, attach **supports / loads /
> settlements**, and the long-term goal is to **export the model to
OpenSeesPy**
> and read results back. The exporter is the one big piece **not yet built
** —
> see §13. Everything else below exists and works.

## 1. What it is

A 2D structural-drawing canvas. The world is in **millimetres**. You place:

- **Anchor points** — reference coordinate *nodes* (the FEA nodes).
- **Module lines** ("modullinjer") — *infinite* datum/grid lines, drawn as
  prominent super-gridlines; the layout grid the structure hangs off.
- **Members** — *real* structural elements drawn **between two anchors**
  (reference-based: they follow their nodes).
- **Supports, loads, settlements** — boundary conditions carried *on* an
  anchor (fixity, nodal force, prescribed displacement).
- **Dimensions** (linear) and **angular dimensions** — annotations.

The canvas pans/zooms, has an adaptive grid with rich object-snapping, JSON
save/load, undo/redo, and an unsaved-changes guard. It is the worQt **CAD**
app (`CADApp`); the older `App` / `JsonApp` demos are deprecated.

## 2. How to run / test

```bash
# Launch the CAD app: 'python -m worQt' runs CADApp (settings load on entry).
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt
# (main.py's tester06 also seeds a CADApp for ad-hoc work.)

# GUI tests (the worQt.qtest harness — NOT pytest). The user runs these.
PYTHONDONTWRITEBYTECODE=1 python -m worQt.qtest tests.test_app.test_cad
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
  code/docstrings),
  `from __future__ import annotations`, pipe unions in real annotations (not
  `Optional`; `param: T = None` is fine, don't rewrite it), no
  `exec/eval/__import__`.
- **No kwargs** anywhere in worQt — positional args only, including
  AttriBox/Qt
  constructors. (Defining `def f(x, y=None)` is fine; *calling* `f(y=1)` is
  not.)
- `'True if x else False'` is deliberate (don't collapse to `bool(x)`).
- Never `if widget:` — truthiness of a `BaseWidget` raises (
  `MixinBase.__len__`).
  Use `if widget is not None:`.

## 3. Headless verification technique (used constantly)

No Wayland/X in the sandbox, so drive the GUI under the offscreen platform
with
**synchronous event stubs** and render to PNG (read it back as an image):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src QT_QPA_PLATFORM=offscreen python -u - <<'PY' 2>&1 | grep -v -E 'propagateSizeHints|raise\(\)'
import sys, tempfile
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF, QSettings
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, tempfile.mkdtemp())
app = QApplication(sys.argv)            # or: from worQt.app import CADApp; app=CADApp()
class Ev:                               # stand-in for QMouseEvent
    def __init__(s, x, y): s._p = QPointF(x, y)
    def button(s): return Qt.MouseButton.LeftButton
    def position(s): return s._p
    def accept(s): pass
from worQt.window import CADWindow
w = CADWindow(); w.show(); c = w.canvas; c.resize(520, 420)
w._selectTool('Anchor')                 # tool names: see §5 KINDS + 'support'/'load'/'select'/'navigate'
c.grab().save('/tmp/x.png')             # window: w.grab(); needs QTest.qWait(60) to settle the panel
PY
```

- Redirect `QSettings` to a tempdir (above) or `closeEvent`/`_saveGeometry`
  write to the real `~/.config/worQt/draw.ini`.
- Qt signals fire synchronously: calling `mousePressEvent`/`mouseMoveEvent`/
  `mouseReleaseEvent` with the stub drives the real logic. A timer+`exec()`
  probe **hangs** under offscreen — use synchronous calls + `grab()`.
- The qtest tests use the same stubs: `_MouseEvent`/`_WheelEvent` at the top
  of
  `tests/test_app/test_cad.py`.
- **`deleteLater()` does not free a widget under `processEvents()` alone** —
  you must flush
  `QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)`
  (this bit us in the test teardown, §11).

## 4. File layout

```
src/worQt/cad/                   the structural-CAD model (combines draw + fea)
  __init__.py      exposes draw, fea, CADSettings
  _cad_settings.py CADSettings(Settings) — colour palette + view defaults (§9b)
  draw/                  PURE 'dead' drawing primitives (no Qt) — mm geometry
    _items.py      AnchorPoint, ModuleLine, Member, Dimension, AngularDimension
    _scene.py      CADScene (AttriBox[list] of items; addItem/clear/iter/len)
    _factory.py    KINDS, HINTS, parseNumbers, itemFromCoords, buildItem,
                   describeItem, itemAttrs, applyAttrs
    _serialize.py  sceneToData/FromData, sceneToJson/FromJson, saveScene/load
    __init__.py    exports the above (NOT CADSettings — that lives one level up)
  fea/                   PURE 2D truss FEA core (no Qt, no numpy)
    _linalg.py     matVec, solveLinear (Gaussian elim, partial pivot)
    _elements.py   Material, Section, Node, Bar
    _truss.py      Truss (assemble + solve), TrussSolution
    __init__.py
src/worQt/settings/              generic, Qt-free settings system (§9b)
  _config_path.py  configPath(appName) — OS-specific dir, XDG/Arch fallback
  _toml.py         tiny dependency-free TOML reader/writer
  _setting.py      Setting(BaseDescriptor[T]) — one typed setting, Setting[T](x)
  _settings_tab.py SettingsTab — a 'tab' (pane) of related settings
  _settings.py     Settings — tabs + persistence (save/load), appName -> path
src/worQt/widgets/
  _base_widget.py  BaseWidget = QWidget + MixinBase (the fusion base)
  _container.py    Container(BaseWidget) — old AttriBox(THIS) workaround (§13)
  _cad_widget.py   CADWidget — the canvas (the big one, ~1300+ lines)
  _vertex_editor.py VertexEditor — stack of (x,y) rows, greys surplus rows
  _selection_tool.py SelectionToolPanel — item list + Clear all
  _new_item_tool.py  NewItemToolPanel — BESPOKE per-type edit panel (§7)
  _view_tool.py    ViewToolPanel — grid/snap/spacing/reset/factor readout
  _settings_dialog.py SettingsDialog — VLC-style tabbed settings editor (§9b)
  _tool_icons.py   navigate/select/anchor/support/load/module/member/dim/angle
  __init__.py      exports
src/worQt/window/_cad_window.py  CADWindow — composes everything
src/worQt/app/_abstract_application.py  AbstractApplication — owns the shared
                 lazy handles: returnCode / splash / window / settings (§9)
src/worQt/app/_app.py            App — generic demo app (kept)
src/worQt/app/_cad_app.py        CADApp — THE CAD app (window=CADWindow,
                 settings=CADSettings; loads settings on __enter__)
deprecated/_draw_app.py,_json_app.py retired Draw/Json launchers (not imported)
src/worQt/qtest/                  the bespoke GUI test harness (§11);
                 _test_me_bro.py exposes testMeBro() — runs the whole suite
tests/test_app/test_cad.py       one TestCAD(AppTest) class — ~95 methods
tests/test_app/test_cad_settings.py / test_cad_app.py  settings + app wiring
tests/test_settings/test_settings.py  pure settings/codec/path tests
tests/test_fea/test_truss.py      TestTruss(BaseTest) — pure, runs in-process
main.py  tester06                 launches CADApp seeded with demo items
```

## 5. The element model (`worQt.cad.draw`)

Pure `worktoy.BaseObject`s, Qt-free, mm. Overloaded constructors
(`@overload(...)` + empty `@overload()`), `AttriBox` fields, `__str__` shown
in
the item list. **The model is reference-based where it matters:**
loads/supports
live *on* an anchor; members *reference* two anchors.

- **`AnchorPoint(x, y)`** — the structural node. Carries its boundary
  conditions as plain fields: `fixX`/`fixY` (`AttriBox[bool]`, the support),
  `loadX`/`loadY` (`AttriBox[float]`, applied nodal force, N), `dispX`/
  `dispY`
  (prescribed support displacement / settlement). Helpers:
    - `supportKind()` → `'free'` / `'pinned'` (both fixed) / `'rollerH'` (
      fixY,
      rests on horizontal ground) / `'rollerV'` (fixX, against a vertical
      wall).
    - `cycleSupport()` → advances free → pinned → rollerH → rollerV → free.
    - `__str__` reflects everything, e.g.
      `Anchor(0, 0) pinned F(12, -30) d(0, -5)`.
- **`ModuleLine(x, y, angle)`** — an **infinite** datum line through origin
  `(x, y)` at `angle` degrees (0 = horizontal, 90 = vertical). `direction()`
  → unit `(dx, dy)`. Drawn as a prominent super-gridline.
- **`Member(nodeA, nodeB)`** — a structural element. Holds **references** to
  two `AnchorPoint`s (`nodeA`/`nodeB`, `AttriBox[AnchorPoint]`). Its
  coordinates `x1/y1/x2/y2` are **read-through `Field`s** (`x1` GET →
  `nodeA.x`,
  etc.), so **moving an anchor moves every member on it**. `length()`.
- **`Dimension(x1, y1, x2, y2)`** — linear dimension; `length()`.
- **`AngularDimension(vx, vy, ax, ay, bx, by)`** — vertex + two arm points;
  `angle()` in `[0, 180]`.

`CADScene` holds items in `items` (`AttriBox[list]`); `addItem`, `clear`,
`__iter__`, `__len__`.

### Factory (`_factory.py`) — single source for kind handling

- `KINDS = ('Anchor', 'Module', 'Member', 'Dimension', 'Angle')`. `HINTS`.
- `parseNumbers`, `itemFromCoords(kind, text)` (flat numbers; `Module` is
  `x, y, angle`; **`Member` raises** — it needs anchors, not coords).
- `buildItem(kind, vertices)` → from `(x, y)` vertices (Anchor 1, Module 2 =
  origin + through-point, Dimension 2, Angle 3). **`buildItem('Member', …)`
  raises** — build members with `Member(a, b)` directly.
- `describeItem(item)` → `(kind, vertices)`; a module reports
  `[origin, origin + unit-dir]` (encoding the angle); a member reports its
  read-through coords (used for display, **not** for rebuild).
- **`itemAttrs(item)` / `applyAttrs(item, attrs)`** — the non-geometric
  channel. For an anchor, returns/applies `{fixX, fixY, loadX, loadY, dispX,
  dispY}`, **only the non-zero/true ones**, so files stay minimal.

### Serialization (`_serialize.py`) — JSON, no pickling

- `sceneToData`: each item → `{kind, vertices, attrs?}`; **a member → `{kind:
  'Member', nodes: [i, j]}`** where `i,j` are scene indices of its anchors.
- `sceneFromData`: **two-pass** — build everything except members first, then
  members resolving node indices to the rebuilt anchors. Atomic (raises
  before
  touching the target scene). Into a given scene = clear + refill in place.
- `sceneToJson`/`sceneFromJson`/`saveScene`/`loadScene`.
  `__format_version__ = 1`.
- **This path also powers undo/redo** (snapshots are `sceneToData` dicts), so
  member references survive undo/redo and save/load — the member follows the
  *rebuilt* anchor.
- Output is **compact JSON** (no `indent=`, which is keyword-only — the
  no-kwargs rule). It's still legible: `{"kind":"Member","nodes":[0,2]}`.

When adding a new kind: class + export + `KINDS`/`itemFromCoords`/
`buildItem`/
`describeItem` + (if it has extra fields) `itemAttrs`/`applyAttrs` + the
canvas
paint/glow/halo/bounds/hit-test/snap branches + `_INITIAL_DEFAULTS` + a
toolbar
icon. (Reference-based items like members skip the vertex path entirely.)

## 6. The canvas: `CADWidget` (`_cad_widget.py`)

`class CADWidget(BaseWidget)`. Owns a `CADScene` and the view transform.

### Units, transform, zoom, grid

- World = mm; `scale` = px/mm (default 1.0). `worldToScreen`/`screenToWorld`
  (world y up, screen y down — flipped). `viewFactor()` = 1/scale.
- **Integer-factor zoom ladder**: wheel snaps to factors that are whole
  integers (`N px/mm` in, `N mm/px` out). `_levelToScale`/`_scaleToLevel`/
  `_snapScaleDown`; `wheelEvent` steps one rung (cursor-anchored via
  `_applyScaleAt`); `zoomAt` is continuous (tests). `__min_scale__=0.1`,
  `__max_scale__=4000`.
- Grid: `gridStep() = gridTargetPx / scale` (zoom-invariant in px,
  `gridTargetPx` default 24). `fitAll()` = zoom-to-extents over the scene.

### Object snapping (gated on `snapToGrid`, all in screen px,
`__snap_px__=10`)

`_worldAt(pos)` resolves the pointer in **priority order**:

1. **Nodes** (`_snapToNode` over `_snapNodes`): every anchor point **plus
   every
   module-line ∩ module-line intersection** (`_lineIntersection`). Exact.
2. **Infinite module lines** (`_snapToModuleLine`, unclamped projection via
   `_closestOnLine`).
3. **Dimension/member segments** (`_snapToSegment`, clamped
   `_closestOnSegment`;
   `_snapSegments` yields member + dimension bodies and angular-dim arms).
4. **Grid** (`snap()`).

Snap-lines: the gridlines through the snapped node (and the drag start) drawn
in
a brighter same-hue shade (`_paintSnapLines`, tracked via `__hover_world__`).

### Modes (`setMode`, cursor via `_updateCursor`)

`'navigate'` (pan), `'select'` (pick via `_itemAt`, 8px), `'draw'` (create
the
active kind), `'support'`, `'load'`. Gestures by active kind / mode:

- **Anchor** → double-click places one (`mouseDoubleClickEvent`).
- **Module / Dimension** → press-drag (`_gestureVertices` → 2 vertices). A
  **dimension started on a module line locks perpendicular** to it
  (`_perpNormalsAt` at press; `_applyPerp` projects the drag;
  `_paintPerpMark`
  draws the right-angle tick; at a module-line intersection the axis is
  chosen
  by drag direction).
- **Member** → **anchor→anchor drag** (`__member_start__`/
  `__member_current__`,
  `_anchorAt` picks the nodes; commits via `setMemberCallback(anchorA,
  anchorB)`; release off an anchor or on the same one adds nothing;
  `_paintMemberPreview`).
- **Angle** → three clicks (`__angle_points__`, `_addAnglePoint`).
- **Support mode**: a **click** (press+release, no drag) cycles the support
  (`setSupportCallback(anchor)`); a **drag** sets a prescribed settlement
  (`setDisplaceCallback(anchor, dx, dy)`). State:
  `__support_anchor__`/`__support_press__`/`__support_current__`.
- **Load mode**: drag a force out of an anchor (`__load_anchor__`,
  `setLoadCallback(anchor, fx, fy)`); a near-zero click **clears** the load.
- **`_forceTip(pos, anchor)`** snaps a force/settlement vector to the nearest
  axis (pure H or V) when `snapToGrid` is on — shared by load + settlement.

### Painting (`paintEvent` order)

background → `_paintGrid` (+ snap-lines) → **`_paintModuleLines`** (infinite
super-gridlines, computed each paint to fill the viewport via
`_infiniteEnds`)
→ `_paintAxes` → items (`_paintItem`; module lines skipped, already drawn) →
previews (`_paintPreview`/`_paintDimensions`, `_paintAnglePreview`,
`_paintLoadPreview`, `_paintDisplacePreview`, `_paintMemberPreview`).

- `_paintAnchor` = crossed circle, **plus** `_paintSupport` (triangle +
  ground-hatching for a pin / roller circles), `_paintDisplacement` (dashed
  fixed-length arrow + `d <mag>`), `_paintLoad` (solid fixed-length arrow +
  `<mag> N`). Load/settlement arrows are **fixed pixel length** (legible at
  any
  zoom/magnitude); the number carries the value.
- `_paintMember` = solid line. `_paintDimensionItem`/`_paintAngularItem` as
  before. Glow/halo treat member+dimension+angle like lines; anchors get a
  point glow. `_itemBounds`: anchor = point, member/dimension = bbox, *
  *module
  line = None** (infinite → never drives auto-fit), → `ensureContains`/
  `fitAll`.
- `_arrowHead(painter, tip, dirX, dirY, color=None)` — color param so load
  arrows are red, settlement orange, dim arrows yellow.

### Callbacks the window registers (canvas stays UI-agnostic)

`setHoverCallback`, `setDragCallback`, `setAddCallback(kind, vertices)`,
`setMemberCallback(a, b)`, `setPickCallback(index)`, `setDeleteCallback`,
`setSupportCallback(anchor)`, `setLoadCallback(anchor, fx, fy)`,
`setDisplaceCallback(anchor, dx, dy)`, `setViewChangedCallback`.

## 7. The window: `CADWindow` (`_cad_window.py`)

`class CADWindow(QMainWindow, MixinBase)`.

### Layout (Wayland-forced single window)

`_buildCentral` = a `QSplitter`, left column of three `QGroupBox`es
(Selection flexes; New-item/Viewer are `QSizePolicy.Fixed`) + the canvas. *
*No
dock/`Qt.Tool` windows** (Wayland can't position them, refuses pointer grabs)
and no `QScrollArea`. Canvas has `StrongFocus` for the Delete key. The
stacked
left panels give the window a **~700 px minimum height** (this clamps small
resizes — it broke `test_window_geometry_persists`, §11).

### Menus & toolbar

- **File**: Open (Ctrl+O) · Save (Ctrl+S) · Quit. **Edit**: Undo (Ctrl+Z) ·
  Redo (Ctrl+Shift+Z). **View**: Reset / Delete-selected / Clear / show-tool
  toggles.
- Toolbar order: **Navigate · Select · Anchor · Support · Load · Module ·
  Member · Dimension · Angle** (exclusive `QActionGroup`, `setData(name)`,
  `__tool_actions__`). `_applyTool`: `navigate/select/support/load` set the
  mode; a kind sets draw mode + `setActiveKind` + `configureFor`.
  `_onToolSelected` skips `_enterNewMode` for the four non-create modes.

### Bespoke per-type edit panel (`NewItemToolPanel`)

The left "New item / Edit item" group is **type-specific**, not a generic
vertex grid (`_show(*sections)` toggles `vertex/support/load/disp/info/members/
add`). `_selectItem(index)` dispatches:

- **Anchor** → `editAnchor(anchor, members)`: editable coordinate fields, a
  read-only `support: <kind>` label, **load `Fx`/`Fy` fields**, **settlement
  `dx`/`dy` fields (only when it has a support)**, and a **list of attached
  members**. Update reads `anchorValues()` and applies coords + load + (
  gated)
  settlement **in place** via `_updateAnchor` — the anchor keeps its
  identity,
  so members keep referencing it.
- **Member** → `editMember(info)`: shows `Node A:` / `Node B:` (read-only).
  **No coordinate edit, no Update button** — only Delete.
- **Dimension/Angle** → `loadItem(kind, vertices)`: the vertex editor;
  Update →
  `_replaceItem` (rebuilds the item).
- Selecting the **Member tool** (New mode) shows a "drag between two anchors"
  hint, no fields.

### New / Edit / Delete / cascade

- `__edit_index__` tracks the edited row. `_enterEditMode` shows the **Delete
  button** + "Update item"; `_enterNewMode` hides Delete + "Add item".
- `addItem(item)` is the single funnel: `_pushUndo` → `scene.addItem` →
  `_refreshDirty` → `ensureContains` → list row. `_onAddMember(a, b)` →
  `addItem(Member(a, b))`.
- **`_deleteSelected` cascades**: deleting an anchor removes every member
  that
  references it too (`item.nodeA is target or item.nodeB is target`), as *
  *one
  undo step**; then `_syncListToScene` rebuilds the list (indices shifted).

### Undo/redo (snapshot-based)

`_pushUndo` snapshots `sceneToData` before each mutation (cap `__undo_limit__=
100`, clears redo); `_onUndo`/`_onRedo` swap snapshots and `_restoreSnapshot`
(rebuilds the scene via `sceneFromData`, re-syncs list, returns to New mode);
`_clearHistory` on Open; `_updateUndoActions` enables/disables the menu
items.
Wired at the four mutation funnels (`addItem`, `_replaceItem`/
`_updateAnchor`,
`_deleteSelected`, `clearScene`) and on support/load/settlement changes.

### Unsaved-changes guard (saved-state-aware `dirty`)

`dirty = AttriBox[bool]`. `__saved_state__` holds `sceneToData` of the
last-saved/loaded scene (set by `_markSaved` at startup, on Save, on Open).
**`_refreshDirty` recomputes dirty by comparing the current scene to the
baseline** — so undoing back to the saved state reads as clean.
`_confirmDiscard` (Save/Discard/Cancel `QMessageBox`; returns True at once
when
clean) gates `closeEvent` and `_onOpen`. Save returns a bool; cancelling its
dialog aborts the action.

### File open/save

`_onSave`/`_onOpen` via `QFileDialog`; Open replaces the scene,
`_syncListToScene`,
`fitAll`, `_clearHistory`, `_markSaved`. `_settings`/`_saveGeometry`/
`_restoreGeometry` persist window geometry + splitter state to QSettings
(`~/.config/worQt/draw.ini`).

## 8. The FEA story (`worQt.cad.fea`) + OpenSees direction

**Decision (the user's):** *worQt is the MODELLER / front-end; the actual
analysis is delegated to **OpenSees**, via **OpenSeesPy** (the Python
interface).* The export-to-OpenSeesPy step is **not built yet** (§13).

`worQt.cad.fea` is a small, **pure (Qt-free, numpy-free) 2D truss solver** built
earlier and **kept as a cheap in-app sanity-check / preview** — not the
production solver:

- `_linalg.py`: `matVec`, `solveLinear` (Gaussian elimination, partial
  pivoting; raises `ValueError` "singular / mechanism" on a near-zero pivot).
- `_elements.py`: `Material(E)` (MPa), `Section(A)` (mm²), `Node(x, y)` (with
  `fixX/fixY/loadX/loadY`, `pin()`, `roller(horizontal)`, `addLoad`), `Bar(a,
  b, material, section)` (`length`, `cosines`, `axialStiffness`,
  `globalStiffness` 4×4, `axialForce`).
- `_truss.py`: `Truss` (`addNode`/`addBar`/`assemble`→(K,F)/`solve`),
  `TrussSolution` (`displacements`, `reactions`, `forces`). Units **mm / N /
  MPa** (E·A/L → N). Verified against analytical single-bar + global
  equilibrium + symmetry; tests in `tests/test_fea/test_truss.py`.

**OpenSeesPy facts (researched, current as of 2026):** version `3.8.0.0`,
`pip install openseespy` (a meta-package that pulls the right platform
build),
Python ≥3.10, `import openseespy.opensees as ops`. The commands mirror the
Tcl
you'd remember, as Python calls:

```python
ops.wipe();
ops.model('basic', '-ndm', 2, '-ndf', 2)
ops.node(tag, x, y);
ops.fix(tag, dofX, dofY)
ops.uniaxialMaterial('Elastic', matTag, E)
ops.element('Truss', eleTag, iNode, jNode, A, matTag)
ops.timeSeries('Linear', 1);
ops.pattern('Plain', 1, 1);
ops.load(node, Fx, Fy)
ops.system('BandSPD');
ops.numberer('RCM');
ops.constraints('Plain')
ops.integrator('LoadControl', 1.0);
ops.algorithm('Linear')
ops.analysis('Static');
ops.analyze(1)
ux = ops.nodeDisp(node, 1)  # read back; member force via eleResponse
```

The "analysis aggregation" (pick a `constraints`/`numberer`/`system`/`test`/
`algorithm`/`integrator`/`analysis`) is a real OpenSees feature the exporter
should expose as knobs (and later a solver-settings panel). Frames swap
`-ndf 3`, add `geomTransf` + `element('elasticBeamColumn', …)`.

The scene → OpenSees mapping is now **clean** because members are
reference-based: each anchor is a `node`; each member is an `element('Truss',
…)` between its two anchors' node tags (**no endpoint dedup needed** — node
identity is explicit). `fixX/fixY` → `fix`; `loadX/loadY` → `pattern`+`load`;
`dispX/dispY` → an `sp` single-point constraint (imposed support
displacement).

## 9. App & launch

**`AbstractApplication` owns the shared, lazily-built app handles** —
`returnCode`, `splash`, `window`, and `settings` — each via the worktoy
`_recursion` lazy getter. The per-app *types* come from two class hooks the
subclass sets: `__window_class__` and (optional) `__settings_class__`;
`getWindowClass()`/`getSettingsClass()` feed the `_create*`/`_get*` pair, so
the getter + type-check live once, not 3×.

`CADApp(AbstractApplication)` sets `__window_class__ = CADWindow` and
`__settings_class__ = CADSettings`. It is a context manager: `__enter__`
**loads the saved settings over the defaults** then returns self; `__exit__`
runs `exec()` on a clean exit. `python -m worQt` launches it; `main.py:
tester06` shows the window and seeds demo items.

Because `MixinBase.app` returns the running `QApplication`, **any widget or
window reaches the settings via `self.app.settings`** — no globals, no
plumbing. (The retired `App`/`JsonApp`/`DrawApp` launchers live in
`deprecated/`.)

## 9b. The settings system (`worQt.settings` + `CADSettings`)

A generic, **Qt-free** settings framework, separate from the CAD app:

- `Setting` is a `BaseDescriptor[T]` declared `Setting[T](default)` (the
  `AttriBox` mould): the subscript fixes the value type, the call the
  default; `valueType`/`default`/`value` are typed `T`, assigning `value`
  coerces. Used in a class body it takes its name from `__set_name__`.
- `SettingsTab` ('tab' = a VLC-style pane) groups related settings;
  `tab.define(name, default)` builds one and infers `T` from the default.
- `Settings` holds named tabs and persists them: `save()`/`load()` reflect
  to a per-app file at `configPath(appName)` — OS-specific
  (`~/Library/Application Support`, `%APPDATA%`, else XDG `~/.config`), in a
  tiny dependency-free **TOML** dialect (`_toml.py`): one `[tab]` table per
  pane. A missing file is a no-op (defaults stand).
- `CADSettings(Settings)` is the CAD app's schema (appName `worQtCAD` ->
  `~/.config/.worQtCAD.config`): a **Colours** tab (every canvas hue, str
  hex) and a **Defaults** tab (grid spacing, snap, zoom limits, radii). Its
  defaults mirror the `CADWidget` constants; a drift-guard test asserts they
  stay equal.
- `SettingsDialog` (in `worQt.widgets`) renders any `Settings` VLC-style: a
  tab list on the left selects the page on the right, each setting drawn by
  the reused value editors. Ok/Apply/Cancel/Restore-defaults; **Apply** is
  enabled only while dirty and writes through to the model and its file.

Settings live on the app (§9), so a future Preferences action is just
`SettingsDialog(); dlg.setModel(self.app.settings); dlg.exec()`. Wiring the
edited colours/defaults back onto the live `CADWidget` is **not built yet**.

## 10. Units / colours cheat-sheet

- 1 px = 1 mm at default zoom; grid 24 px target; zoom rungs …1/3, 1/2, 1, 2,
  3.
- Model units: mm / N / MPa.
- Colours: grid `#2a3628`; module line `#6f9a58` (selected `#a6e07a`); anchor
  node `#c678dd`; member `#61afef`; support `#56b6c2`; load arrow `#e06c75`;
  settlement arrow `#d19a66` (dashed); dimensions `#ffd24a`; preview rubber
  band
  `#e5c07b`; selection glow warm / halo `#ffe082`.

## 11. The qtest harness (`src/worQt/qtest/`) — IMPORTANT, it's bespoke

Not pytest. The runner discovers `test*`/`run*` modules under `tests/` and
runs
**exactly ONE `Test*`/`Run*` class per module** (`AppTestSuite.getNamed`
raises
on more than one — so to split a class you split into separate *files*).

- **`AppTest(BaseTest, metaclass=MetaTest)`** — base for GUI tests needing a
  `QApplication`. One shared `QApplication` per class; `runTest()` runs every
  method inside one `app.exec()` event loop (`_runMethod` does setUp →
  method →
  tearDown). `__time_out__ = 30.0` (per-class deadline; override on a slow
  subclass). It now has **scoped per-test cleanup**:
    - `setUp` snapshots open top-level widgets (`__preopen__`).
    - `tearDown` disposes **only the widgets this test opened** (anything not
      in
      the snapshot) via `hide()` + `deleteLater()` + **`sendPostedEvents(None,
    QEvent.Type.DeferredDelete)`** + `processEvents()`. Both start with
      `super()`. This stops ~45 windows piling up (which blew the 30s
      deadline)
      and is the "a test closes only what it opens, never others" rule.
    - **Never `close()` a `CADWindow` in a test** — `closeEvent` runs the
      unsaved-changes modal (hangs headless) and writes QSettings. Use
      `deleteLater`.
- **`AppTestRun.run()`** — the deadline + dispatch live here, not in
  `runTest`:
    - A Qt `AppTest` (`isinstance(cls, MetaTest)`) → `_runPopen`: a fresh
      child
      process (`python -m worQt.qtest <module>`) with
      `communicate(timeout=cls.getTimeout())`; on timeout it `killpg`s the
      process group (→ `-9` → "TIMEOUT killed after Ns").
    - A **plain `BaseTest`/`unittest.TestCase`** (e.g. `TestTruss`, not a
      `MetaTest`) → `_runPlain`: run **in-process** with
      `unittest.TextTestRunner`
      (no subprocess, no Qt). Returns code 0 (pass, **quiet**) or 3 (fail,
      with
      detail) — same `(code, output)` contract as the subprocess path.
    - `getNamed`/`run` accept any `BaseTest` subclass now (was
      MetaTest-only).
- `__main__` unconditionally calls `getNamed(name).runTest()` — only valid
  for
  AppTest classes. Invoking `python -m worQt.qtest <plain-module>` directly
  fails loudly **by design** (the user's call: "let the apparatus fail when
  used incorrectly"). The sanctioned path is `runAll`, which routes
  correctly.
- **`testMeBro()`** (`worQt.qtest`) runs the WHOLE suite via `runAll`,
  routing Qt `AppTest`s to subprocesses and plain `BaseTest`s in-process —
  the cutely-named one-call entry the user runs.

## 12. Tests (`tests/test_app/test_cad.py`, `tests/test_fea/test_truss.py`)

One `TestCAD(AppTest)` (~95 methods) + one `TestTruss(BaseTest)` (pure FEA).
Coverage: model/factory for every kind; transform/zoom/grid/snap (incl.
node/intersection/module-line/point/segment snap + perpendicular-dimension
lock); members (drag-create, reference identity, drag-to-empty rejects,
cascade
delete, JSON round-trip by node index, read-through follow); supports (click
cycles, drag settlement, JSON); loads (drag, axis-snap, click-clear, JSON);
bespoke panels (anchor coords+load+settlement in-place edit, member shows
nodes
only, delete button); undo/redo + saved-state dirty; geometry persistence (
now
asserts the window's *actual* clamped size, since min-height ~700px prevents
a
480px resize). Drive with `_MouseEvent`/`_WheelEvent`; assert `grab()`
non-null. **Gotcha:** undo/redo rebuild scene objects via `sceneFromData`, so
after an undo/redo re-fetch the live item from `scene.items`, don't keep a
stale reference.

## 13. worQt gotchas that bit us (and the fixes)

- **`AttriBox[T](THIS)` — FIXED in worktoy 1.0rc9.** Pre-rc9, `THIS` returned
  the *owner* when the owner was already a `T`, so `AttriBox[BaseWidget](THIS)`
  on a `BaseWidget` subclass aliased the panel itself (breaking nested
  layouts). As of rc9, a captured sentinel (`THIS`/`OWNER`/`DESC`) **always
  constructs** `T(owner)` — a real child parented to the owner. The
  `Container(BaseWidget)` workaround (`VertexEditor`/`ViewToolPanel`/
  `NewItemToolPanel` hosts) is therefore now **optional**, not required;
  existing uses still work. Corollary: the field type must accept whatever
  `THIS` resolves to (for Qt, `Widget(parent)` — exactly what you want).
- **Read-through fields**: `Member.x1` etc. are worktoy `Field`s with a GET
  reading `nodeA.x` — that's how members follow their anchors. `AttriBox[
  AnchorPoint]()` holds the node reference (default-constructs a throwaway
  `AnchorPoint()` until assigned in the 2-arg constructor).
- **Reference identity through undo/serialize**: members serialize/rebuild by
  **node index** (two-pass), so a restored member references the *restored*
  anchor object, not a stale one. Editing an anchor must mutate it **in place
  **
  (`_updateAnchor`), never `_replaceItem` (a new object orphans the members).
- **QObject in a class body segfaults pre-QApplication** → all Qt widgets
  live
  in `AttriBox` (built lazily); runtime-only widgets in methods.
- **`__name__`-style attrs** (`__rows__`, `__selected__`,
  `__member_start__`, …)
  end in `__`, so they're NOT name-mangled — tests use
  `getattr(obj, '__x__')`.
- **Wayland**: one splitter window; set geometry only before the initial map;
  no global `Delete` shortcut (use the canvas key so fields keep Delete).
- **`json.dump(indent=…)` is keyword-only** → can't pass it under the
  no-kwargs
  rule → saved JSON is compact (still legible).

## 14. Status / next steps

- ✅ Element rework: anchors (nodes), module lines (super-gridlines),
  reference-based members, dimensions/angles.
- ✅ Boundary conditions: supports (click-cycle), loads (drag, axis-snap,
  panel
  fields), prescribed settlements (support-drag, panel fields).
- ✅ Object snap (nodes/intersections/module-lines/segments/grid),
  perpendicular-dimension lock.
- ✅ Bespoke per-type edit panels; cascade-delete; in-place anchor edit.
- ✅ JSON save/load (members by node index), undo/redo, saved-state dirty
  guard,
  fitAll, geometry persistence.
- ✅ Pure FEA truss solver (`worQt.cad.fea`) as a preview; OpenSeesPy chosen as
  the
  real analysis target; qtest harness handles GUI + pure tests.
- ✅ Restructure: `draw` + `fea` combined under `worQt.cad` (`cad/draw` = dead
  primitives, `cad/fea` = analysis); the `Draw*` classes renamed `CAD*`;
  `CADApp` is the app, with the shared lazy handles (returnCode/splash/window/
  settings) consolidated onto `AbstractApplication`.
- ✅ Generic settings system (`worQt.settings`: `Setting[T]`/`SettingsTab`/
  `Settings`, TOML + OS-specific path) + `CADSettings` (colours + defaults,
  drift-guarded) + VLC-style `SettingsDialog`; settings live on the app
  (`self.app.settings`).
- ⏭️ Settings not yet **applied** to the live canvas (edit colours/defaults →
  push onto `CADWidget`); no Preferences (`Ctrl+,`) action yet.
- ⏭️ **THE NEXT BIG PIECE: the OpenSeesPy exporter.** scene → `ops.node` /
  `ops.fix` / `uniaxialMaterial` + `element('Truss', …)` / `pattern`+`load` /
  `sp` (settlements) / the analysis-aggregation stack → a runnable `.py`;
  then
  `import openseespy`, run in-process, read `nodeDisp`/`eleResponse` back,
  and
  draw the **deflected shape + member forces** on the canvas.
  Material/section
  (E, A) still need a home (per-member, or a global default — currently the
  `fea.Bar` defaults: E 210000 MPa steel, A 100 mm²).
- ⏭️ Smaller: module-line **labels** (grid A/B/C · 1/2/3); multi-select;
  item-list Delete; frame elements (`-ndf 3`, bending) for full frames.
