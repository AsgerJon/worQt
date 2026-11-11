# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## What this is

`worQt` extends the `worktoy` library with utilities for building Qt for
Python
(PySide6) desktop applications. The published package is named `worQt`; its
source lives under `src/worQt`. `worktoy` and `pyside6` are external runtime
dependencies — do not vendor or reimplement their machinery.

Its role (the user, 2026-11-11): worQt is the PHYSICS LAB, the place
for creating, examining and testing new physics, in Python, with Qt
tools to look at it (views, maps, plots, recordings) and qtest to hold
it. Immersive 3D worlds belong outside Qt, in Unreal Engine 5: physics
made here is the reference, its recordings the contract, for a C++ port
plugged into the engine (the billiards game, Kegler first, moves there;
AsgerBim's 3D likewise).

## Commands

Tests run through the in-house `worQt.qtest` harness, NOT pytest. Put `src`
on
`PYTHONPATH` and run from the repo root. Always prefix Python invocations
with
`PYTHONDONTWRITEBYTECODE=1`.

```bash
# Run the whole test suite (every test class in its own child process)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest

# Run only some test modules by dotted name (plain or 'AppTest' alike)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest \
  tests.test_utils.test_color

# Every top-level run (any entry point) rewrites 'latest.log' in the repo
# root with its complete record: status lines plus every child's full
# output.

# Local scratch runner: the gitignored 'main.py' hands callables to 'yolo()'
# ('yolo.py'), which runs them and pretty-prints any traceback. Its
# 'runTests'/'testMeBro' run the qtest suite.
PYTHONDONTWRITEBYTECODE=1 python main.py
```

```bash
# Run EZWord, the word processor worQt's document model is worked out on
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.ezword

# Run the disk app: a concrete disk edited with the mouse and a panel
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.engineering

# Run the concrete app: a cylinder cast from its ingredients, crushed or
# pulled apart (needs torch, numpy and scipy, not yet in pyproject.toml)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.engineering.meso

# Run the section force diagrams of plane frames ('snitkraftkurver')
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.engineering.diagrams

# Run the springs: masses on springs and dampers swinging in 3D
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.engineering.springs

# Run the circuits: sources, resistors, lamps, capacitors, coils,
# switches, meters, diodes, LEDs and transistors, running as built
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.engineering.circuits

# Run the circuit quests: a game, quests unlocking parts
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.engineering.quests

# Run the coin pusher ('skubbe-maskinen'), honest, in 3D (needs warp-lang;
# the first run compiles the coin solver, ~20 s)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.gaming

# Run three-cushion carambole: the table in 3D (Qt Quick 3D)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.gaming.billiards

# Shoot the 3D table to 'previews/billiards-*.png' (needs the real
# display: my sandbox has no GPU, so the user runs it)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python previews/shoot_billiards.py

# Run the beam lab: an RC beam on a rig, pushed by a displacement
# controlled actuator, reckoned by OpenSees (needs openseespy, not yet in
# pyproject.toml)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.engineering.lab
```

`roll_version.py` bumps the version in `current_version.json` /
`current_tag.txt`.

## Architecture

### The metaclass fusion (`src/worQt/mixin`) — the core idea

The central problem worQt solves: Qt classes are built by Shiboken's
metaclass
(`type(Shiboken.Object)`), and worktoy classes are built by
`worktoy.mcls.BaseMeta`.
You cannot subclass both Qt and a worktoy `BaseObject` directly — Python
rejects
the metaclass conflict. The `mixin` subpackage fuses the two so worktoy's
descriptor/overload machinery becomes available on Qt-derived classes:

- `MixinMeta` — the fused metaclass. Its MRO inserts a private `_Shiboken`
  metaclass between Shiboken's `ObjectType` and `BaseMeta`.
  `_Shiboken.__getattr__`
  bridges a contract mismatch: worktoy's `AbstractMetaclass` expects names
  matching
  `__class*__` to resolve to the `METACALL` sentinel rather than raise
  `AttributeError`; Shiboken doesn't honour that, so `_Shiboken` intercepts
  and
  returns `METACALL` for that pattern. `__new__` routes class creation
  through
  `_ObjectType.__new__` with the compiled namespace.
- `MixinSpace` — the namespace object (`__prepare__` returns one). Currently
  a thin
  `BaseSpace` subclass, reserved as the hook point for MixinMeta-specific
  namespace
  behaviour.
- `MixinBase` — `BaseObject` subclass declared `metaclass=MixinMeta`. This is
  the
  bridge users inherit from to get worktoy behaviour on a Qt class.

When touching this subpackage, preserve the MRO ordering and the
`__getattr__`
bridge — both are load-bearing and subtle. The `__init__.py` import order
(`MixinSpace` → `MixinMeta` → `MixinBase`) is also load-bearing.

### Qt + QObject construction constraint

Constructing a `QObject` (including any worQt class that mixes in a Qt type)
before a `QApplication` exists can hard-crash the interpreter (segfault), not
raise. Keep QObject construction out of class bodies and module import time;
defer it until an application instance exists. The `App` class follows this
by
lazily constructing its splash screen and main window on first access.

### Application classes (`src/worQt/app`)

- `ApplicationMixin(QApplication, MixinBase)` — the fusion point where a
  concrete Qt type meets worktoy machinery.
- `App(ApplicationMixin)` — the worQt application, used as a context manager:
  `__exit__` runs the Qt event loop only on a clean exit. It owns the lazily
  built `splash` and `window` (a concrete app sets `__window_class__`),
  routes exceptions raised in slots and event filters from `notify()` to the
  `handleException()` hook (only `Exception`; `KeyboardInterrupt`/
  `SystemExit`
  propagate), and guards exit: `confirmExit()` asks `askToSave()`
  (Save/Discard/Cancel) when `hasUnsavedChanges()`. An unsaved-changes marker
  in the title belongs to the future document layer, through Qt's own `[*]`
  placeholder and `setWindowModified()`. Usage:

  ```python
  with MyApp(*sys.argv) as app:
      app.window.show()
  ```

### The rest of the package

- `ezword` — EZWord, the concrete word processor the general document model
  is worked out on. Its text model is Qt-free: `Char` (caseless letters) →
  `Word` → `Clause` (split on whitespace) → `Sentence` (clauses split on
  commas, ended by its `punctuation`, a run of `PunctNum` marks) →
  `Paragraph` (split behind punctuation; it decides case) → `Chapter` (split
  on blank lines) → `Part` → `Memoir`, after LaTeX's memoir. `str()` of any
  level is the file format, and each level reads that text back. No
  contractions, digits or other characters: write "do not". `ezword.gui` is
  the app: `PageWidget` (a `Vidget` taking only what the format holds and
  showing the case its punctuation decides; it knows its `filePath`),
  `EZWordWindow` (a `FileBrowser` of `.ezw` files on the left taking the
  spare width; on the right a `TabBar` over the pages, one `PageWidget` a
  tab, at 80 columns; `page`/`filePath` mean the current tab; a file
  already open shows in its tab, another opens in a blank or new tab;
  `gt gT :tabnew :tabn :tabp` and Ctrl+PageUp/Down switch; `:q`/`:wq`
  close the tab, the last starting over; a modified tab's cross asks)
  and `EZWordApp` (exit guard over every tab, and a dark Fusion palette
  so the window and menus match).

- `engineering` — structures as a civil engineer thinks of them, in
  metres, kN and MPa, Qt-free; first the `Disk` ('skive'): a rectangular
  concrete disk loaded in its own plane (length x height x thickness,
  length and height each at least 4 thicknesses, as EN 1992-1-1 9.6.1
  asks of a wall; materials `fc`, `fy`, `E` in MPa, by default 30, 800
  and 200000), with `Support`s (setting `x`, `y` or both) and `Load`s (a
  force `F` in kN) each over a stretch of one `EdgeNum` edge, never at a
  point, and fitting it. `str()` is the text, read back:
  `disk 6 x 2.7 x 0.3 fc 30 fy 800 E 200000` (materials in any order,
  any left out taking the default), then `support bottom 0 0.3 y` and
  `load top 0 6 F 0 -1200` lines. Editing: `resized` (bottom left
  fixed; a whole-edge stretch stretches, one at the moving end rides
  along, others stay; loads keep their intensity), `replaceSupport`,
  `removeSupport`, `replaceLoad`, `removeLoad`, `supportRoom`,
  `isFree`, `freeStretch`, `withMaterials`, `leastSide`/
  `greatestThickness`. `Rebar`: a straight bar group, `rebar x1 y1 x2 y2
  count Ø` (mm), last in the text; `addRebar`/`replaceRebar`/
  `removeRebar`, kept inside the disk, carried by `resized` (each end
  keeps its distance to its nearer edge). `StrutTie(disk)`: the tied
  arch for two bottom supports and top loads pressing down (else
  `applicable` False with a `reason`): loads split by the support they
  go to (always in equilibrium), top strut depth from H = nu fc t (d -
  sqrt(d² - 2M/(nu fc t))), tie = horizontal bars spanning the supports
  at their centroid; checks (struts at node widths b sin + 2 yT cos,
  top strut, tie As fy, bearings, load pressure) against nu fc,
  nu = 0.7 - fc/200 (Nielsen); `factor` = lower bound by halving,
  `governing`, `checksAt(scale)`. Hand-checked on the deep beam with
  4 Ø20: H 310.5, C 675.6, factor 2.35 (struts at the supports).
  `engineering.gui` is the disk app, built for an engineer who will
  not touch a terminal and must need no explanation (user: "a gui and a
  joke: if they require explanation they suck"): only conventions every
  drawing program has, NO hidden gestures and NO text pane. `DiskWindow`
  = `DiskToolBar` (`ToolButton`s 'Add support', 'Add load', 'Undo',
  'Redo', greyed out when idle) over the `DiskWidget` drawing, with the
  `DiskInspector` panel beside it. A click selects the disk, a support
  or a load (`selection`, a `DiskGrip` of `GripNum` DISK/SUPPORT/LOAD;
  `selectionChanged`); the selected part is amber, hover lighter. The
  selected disk has PowerPoint-style handles (right edge, top edge,
  corner; 5 cm snap, view frozen while dragging, red '= 4 t' at the
  least); the selected support has handles at its plate ends (widen).
  Supports drag round all edges (nearest edge, up to neighbours, a
  roller turning across a new edge); loads slide along their edge;
  Delete removes the selection; `addSupport`/`addLoad` add where there
  is room and select. A right click selects and opens a context menu
  (`contextMenuAt(point)` builds it, `popup` shows it without blocking,
  so tests trigger its actions): support Roller/Pin (checked)/Remove;
  load Reverse/Spread over the edge/Remove; free edge 'Add support
  here' (greyed where it would overlap)/'Add load here' (pressing on
  the edge); elsewhere Add support/Add load/Undo/Redo (greyed when
  idle). The panel shows the selection as `NumberField`s
  (click, type, Enter; Esc gives up; arrows step; limits kept) and
  buttons (Roller/Pin, Remove). `diskEdited`, `undo`/`redo`/`edit`,
  `canUndo`/`canRedo`. Bars (`GripNum.REBAR`) are added as a bottom tie
  ('Add reinforcement': 4 Ø20 at cover 50 mm), selected, dragged to the
  cm, edited (count, Ø, ends; As and As fy shown) and removed. The
  drawing shows `strutTie` over the disk (struts as bands of their
  needed width with C, the tie green with T or dashed red 'tie needed')
  and `verdict()` top left: what the arch carries and what governs.
  `DiskApp` is dark, borrowing EZWord's palette.
  Next: dragging the arch's nodes, homogeneous stress fields, and the
  upper bound (yield lines) shown beside the lower.

- `engineering.meso` — concrete simulated from its ingredients, in mm, N
  and MPa, reckoned with `torch` (`scipy` for the Voronoi cells and the
  exact elastic solve). `Grading`: a sieve table, the 'kornkurve'
  (`fuller(D, q)` at the standard sieves; log-log between sieves;
  `sample` fills each size class largest first). `Stone`: a convex
  polyhedron (hull of 14 points about an ellipsoid 1 : 0.65-0.9 :
  x0.6-0.9, jittered), turned at random (Shoemake), as large by volume
  as the sphere of its size; `section(z)` gives a convex polygon.
  `Cylinder`: Ø x H cast in its mould, stones from `smallest` (4 mm) up
  placed at random, largest first, corners inside the mould, never
  overlapping (parted by a face of either or the plane square to the
  centre line, tried 64 at a time in torch), in the slab 1.5 D either
  side of the axial section; `section(z)` cuts them as polygons; a
  whole Ø100 x 200 takes ~10-20 s. `Lattice`: the section as Voronoi
  cells of nodes at least `spacing` apart (mirrored at the edges so cells
  end on them), each a rigid body (x, y, turn), neighbours joined at
  their face by a normal and a shear spring (Poisson's ratio nought, so
  exactly uniform: patch test exact, mortar alone exactly E), of `PhaseNum`
  STONE / MORTAR / BOND (a line crossing a stone's edge, clipped against
  the stone polygons: stone and mortar in series) / PLATEN; `PhaseMaterial` (
  E, ft, Gf, c, mu, GII) per phase,
  stone 70 GPa / 10 MPa, mortar 25 GPa / 4 MPa, bond 2 MPa;
  `elasticModulus()` sits on the Hashin-Shtrikman bounds. `UniaxialTest`
  (`CompressionTest`, `TensionTest`): explicit dynamics, masses scaled
  from Gershgorin for a unit step, Cundall damping, platen speeding up
  over its first crossings; faces crack and soften by Gf (crack opening),
  close and bear again, hold by cohesion (worn by cracking and by slip,
  GII) plus friction; nothing tuned. Out come fc about 32-34 MPa at
  about 1.3 per mille, ft about 2.5-2.7 MPa, fc/ft about 12.5,
  microcracks parallel to the load before the peak, cones from the
  platens after it, one crack across in tension. `meso.gui`:
  `MesoWindow` (buttons 'New cylinder', 'Compression test', 'Tension
  test', 'Pause'/'Resume'; `SectionWidget` with the stones and the
  cracks as they open; `CurveWidget`, the stress-strain curve with fc or
  ft and E read off), stepped by a `QTimer` 40 ms at a time, Ø100 x 200,
  spacing 1.25 mm: a test takes about half a minute. The window opens
  empty, the tests greyed out, until 'New cylinder' casts (seed 1, then
  the next); it casts a
  `WholeCylinder` (slab as deep as the mould) so the toolbar's 'Paste'
  `Slider` (engineering.gui: click, drag, wheel, keys; `valueChanged`)
  can make the paste clear: `SectionWidget.pasteOpacity` is the share of
  light 10 mm of paste stops; the stones behind the cut (`behindStones`,
  faces lit from the top left) show through `pasteLayers` (12, deepest
  first, each as wide as the round cylinder at its depth); the stone
  layers are cached per cast and size, the paste laid over per opacity.
  Cut stones are drawn with rounded corners.
  In space: `LatticeBase` holds what both lattices share (materials,
  `stoneShares`, `moduliOf(stone, mortar)`, `elasticForces`,
  `elasticModulus`, rows `normalRows` (E x D) / `shearRows` (E x S x D),
  `bodyMoves` 3 or 6, `liftColumn`, `platenLift`, `loadedArea`);
  `Lattice3D` is the whole cylinder (Matern nodes, mirrored at the ends
  and radially across the wall, 3D Voronoi faces ordered and measured in
  torch, a normal and two shear springs, stones clipped by their planes;
  patch test exact, plain modulus within ~0.5% as the wall is faceted).
  `UniaxialTest(lattice[, materials[, device]])` steps either lattice,
  shear as a vector, float64 on 'cpu', float32 on 'cuda'. 3D results are
  realistic: fc ~40 MPa at ~2.1 per mille (EN 1992-1-1's 0.7 fcm^0.31),
  ft ~3.5. The app (`MesoWindow`) is now 3D: `CylinderView` (whole
  cylinder, drag to turn, stones and cracks layered under paste),
  `IngredientPanel` (`QuantitySlider`s for stone / paste / bond, locked
  while testing), 'Use GPU' `CheckBox` (greyed unless
  `torch.cuda.is_available()`), spacing 2.5 mm: Ø100 x 200 casts in ~25
  s and a CPU compression test takes ~10 min (66 ms a step); the GPU
  works outside my sandbox. Cracks are faces given more than 1 um,
  opened or slid (`crackSizes` = max(`openings`, `slips`), so inclined
  shear cracks show), coloured on a turbo log scale 1 um..1 mm
  (`_crack_colors`: `crackColor`, `crackLevel`, `levelColor`, faint when
  narrow; `paintCrackScale` under the caption). `TestStatus` strips
  the window's bottom (idle / casting / running / paused / finished,
  coloured dot, live strain, stress, steps, time; a moving bar while
  work goes on); the running test's button stays lit (`checked`).
  'Export PDF' (`askExport`: non-native `QFileDialog.open()`, no wait)
  writes a `TestReport` (A4 via `QPdfWriter`: specimen, lattice,
  ingredients, result, cylinder and curve rendered, a 'simulated, not
  measured' note); `UniaxialTest.stiffness` is the secant at 0.3 of the
  strength. The 2D
  `Lattice`/`SectionWidget` stay as tested library code, unused by the
  app.

- `worksees` (`src/worksees`, a sibling package beside `worQt`, Qt-free)
  — finite element analyses set up for OpenSees (`openseespy`, not yet in
  pyproject.toml) and read back. `Model(ndm, ndf)` keeps a model as plain
  values: `addNode(*xy)` (numbered from 1), `add(command, kind, *args)`
  for materials/sections/transforms/elements (numbered within their
  command, the number put in after the kind as OpenSees has it;
  'beamIntegration' too), `addFibers` (patch/layer/fiber after a Fiber
  section), `fix` (flags add up), `couple` (equalDOF), `addLoad`
  (forces add up), `commands()`. `Worker` is the spawned process
  OpenSees runs in (OpenSees keeps one global model per process and may
  end it; its output sent nowhere between jobs), `call(fn, *args)`; a
  dead process raises `SolverDied` and the next call starts a new one.
  A step of nought is allowed (tolerance floored).
  `Solver.solve(model, *queries)` is linear static (Transformation,
  RCM, UmfPack), each from `wipe()`, and returns a `Result`
  (`displacement(node)`, `reaction(node)`, `response(query)` per
  element, a query a word or a tuple like ('section', 1,
  'deformation'), `loadFactor`, `said`); a refused command raises
  `SolverError` (the command, OpenSees's own warnings). `Session(model,
  node, freedom[, worker])` keeps a model in OpenSees and pushes it
  under DisplacementControl: `advance(increment, count, *queries)`
  returns a `Result` a step, `loadFactor` the force holding the pushed
  node there; each step tries Newton, KrylovNewton, NewtonLineSearch,
  ModifiedNewton -initial, then splits in four up to 3 times; `stuck`
  when a step cannot be made. Sessions sharing a worker are told apart
  by a token (the older one refused). OpenSees does not flag a
  mechanism: callers check their own supports.
  In `worQt.engineering`, `StressField(disk[, solver])` is the disk's
  plain, uncracked, linear elastic field on plane stress quads (lines
  at every stretch end, at most min side / 24 apart; Ecm from EC2,
  nu 0.2; bars left out), `cells` (`CellStress`: sx, sy, sxy MPa,
  major/minor/angle), `reactions` per support, `applicable`/`reason`
  when the supports let it slide or turn. Not yet drawn in the app.

- `engineering.lab` — the beam lab, in mm, N and MPa, through
  `worksees`. `BarLayer(count, Ø, cover)`; `RCBeam(length, height,
  width, fcm, fy, Es, bottom, top)` (default 3300 x 300 x 200, fcm 38,
  fy 550, 3 Ø16 / 2 Ø10, cover 30; EC2 table 3.1 from fcm: fck, Ecm,
  fctm, epsC1, epsCu1; class B bars, epsUk 5 %, k 1.08; bars must fit).
  Signs (user: "T3 is under the beam so it measures negative"): every
  reading is up positive, as a transducer under the beam reads its
  plunger: bending down reads < 0, actuator strokes and forces on the
  beam pushing down are < 0, a ramp down has rate and limit < 0 (same
  sign, else refused); the PID's output is the driven actuator's
  velocity in that same sense, so positive gains work either way; peak
  and falls use |force|. Axes are signed (`niceSpan`). The command is
  integrated cycle by cycle (`experiment.command`); `retune(control)`
  changes rate, limit, gains and top speed under test (same transducer
  and actuator, the limit reachable from the command now), and
  `Control.towards(start)` turns the rate's sign to head for a new
  limit, so the panel's 'To' 0 under test unloads. `ControlPanel.
  setStage('setup'|'testing'|'tested')`: under test only the ramp,
  gains and top speed are live (emitting `controlTuned`), the note
  says so; tested, nothing until New beam.
  Step size (user: "let the step size be a fraction... unitless"):
  `Control.step` is the share of the ramp each step takes, one
  OpenSees step a control cycle; the step in mm = step x |limit - where
  the ramp began| (`experiment.stepLength`), the cycle = that / |rate|
  (`experiment.cycle`, `rig.cycle` from nought); a new limit starts a
  new ramp from the command now. Default 0.001: 0.15 mm every 1.5 s,
  450 steps to crushing. The PID samples once a step, so coarse steps
  with hot gains hunt (0.005 with Kp 0.5 stalls).
  The rig (user's design): any number of `Support(at, kind)` (pin /
  roller / fixed, `holds`), `Actuator(at, follows, share)` and
  transducers (positions); ONE `Control(transducer, actuator, rate,
  limit, step, kp, ki, kd, speed)` loop: it reads its transducer and drives
  exactly one actuator, which MOVES (PID output = ram velocity, as a
  servo valve, capped at `speed`, anti-windup); every other actuator is
  daisy-chained, pushing `share` x the force of the one it `follows`
  (chains multiply, `rig.shares`). `Rig(supports, actuators,
  transducers, control[, stroke])` is whole or refuses (chains
  must reach the driven one, no loops); `check(beam)`/`unheld()` (along:
  a pin or clamp; turning: two places or a clamp); `withX`,
  `withoutX` (refuses the driven actuator, one followed, the
  transducer read; remaps indices), `driving(i)` (old driven follows
  it, share 1), `stretched`, `standard(beam)` (pin + roller 150 in,
  A1 driven at L/3, A2 = 1.0 x A1, T1 T2 under them, T3 midspan read,
  -0.1 mm/s to -150 mm, step 0.001, Kp 0.5, Ki 0.05, 1 mm/s). In
  OpenSees this is exactly DisplacementControl: the driven node moves
  the PID's increment, each actuator's reference load is -share N, the
  load factor is the driven force, so the chain is solved with no lag.
  THE BEAM IS A 3D SOLID (user: "change completely to use the 8-dof 3d
  elements"; "No assumption of symmetry!"): `BeamMesh(beam, rig,
  seed)` = stdBrick (8 node, 8 points; SSPbrick's elastic hourglass
  stabilising kept a cracked beam 2x too strong) over the WHOLE beam, <= 50
  mm along / 60 up / 65 across, lines at supports, actuators and their
  100 mm plates, bar rows, bars across (top bars merged within 15 mm),
  stirrups (snapped within 15 mm); ASDConcrete3D per brick ('-fc',
  '-ft' scattered +-5 % by seed, '-tangent', '-autoRegularization'
  brick size); bars and stirrups (closed, 4 legs round the outer bars)
  as Steel02 trusses through the nodes; supports hold the underside's
  line across the beam (turning free; pin along too, clamp the whole
  section, first support's middle node holds z; a fixed 100 mm plate
  clamped the beam's ends, 3x first-crack load); bricks bearing on a
  support or under an actuator plate are ElasticIsotropic (no false
  crushing) and left out of the readings; actuator share spread over
  its plate's top nodes, DisplacementControl at the plate's middle
  node.
  `read(result)` -> lifts / deflections (underside middle), stroke,
  `cells` per face cell (greatest in-plane principal strain over the
  bricks across, its direction, least; the 8 points averaged), bar
  strains by stretch, stirrup strains. Queries `('strains',)` (stdBrick;
  SSPbrick answers 'strain') and `('material', 'strain')` (trusses).
  `RCBeam` has `stirrups` (`Stirrups(diameter, spacing, gaps)`,
  default Ø8 c/c 150, `places(length)`, `withGap/withoutGap/
  withGapAt`, `withStirrups`). `BeamExperiment(beam, rig[, seed[,
  worker]])`: one cycle per OpenSees step; `begin()`/`ready()`/
  `collect()` don't block (the window polls every 20 ms; `settle()`
  waits); events first crack, bars yield, stirrups yield, concrete
  crushes, bars snap; a fall, or getting stuck (a brittle failure
  leaves no step to find; worksees gives a step 45 s), with the widest
  crack leaning >= 25° and no yield ends 'it failed in shear: a
  diagonal crack opened at x'.
  Speed: the small beam ~0.8 s a step; the standard beam slower
  (worksees uses Plain constraints unless equalDOF, UmfPack - SuperLU
  'SparseGeneral' double-frees when the analysis is re-set - and sets
  test/algorithm only on change). Checked on the small test beam (1600
  x 200 x 120, 2 Ø12, `tests.test_lab.smallBeam`): without stirrups it
  fails in shear at 47.8 kN (EC2 VRd,c with mean values: 47), the crack
  leaning 35° in a shear span; with Ø6 c/c 100 its bars yield at 77.5
  kN (Mu by hand: 77) and it plateaus at ~80 kN until crushing.
  Earlier fiber model (gone): 4 point 162 kN vs 159 by hand.
  `BeamSetup(beam, rig)` / `BeamSetup(text)`: a '.beam' file, a line a
  part (`beam L x H x W fcm fy Es`, `bottom 2 Ø12 cover 25`, `top ..`,
  `stirrups Ø6 c/c 100 gap 150 550`, `support 100 pin`, `actuator 600
  driven` / `actuator 1000 follows A1 share 1`, `transducer 800`,
  `control T3 A1 rate .. limit .. step .. kp .. ki .. kd .. speed ..`,
  `stroke 150`); any order, parts numbered in theirs; materials,
  control numbers, stroke and 'Ø' may be left out; refusals say the
  line; the rig must `check` against the beam. `lab.gui`:
  `LabWindow` = `LabToolBar` (Start test / Pause / New beam / Open… /
  Save… / Add support / Add actuator / Add transducer / Add stirrup gap
  / Remove; the File menu's Open/Save too, non-native dialogs that do
  not block; `openFrom(path)` / `saveTo(path)`; `setup` is as the test
  began, retuning not counted, and New beam goes back to it; opening
  ends a test as New beam does), `ControlPanel`
  (left: the loop's numbers, the part selected: at, support kind buttons,
  follows / share, a gap's From / To), `BeamView` (frame, actuators with role
  and force, supports by kind, transducers with readings, stirrups (accented
  once yielded), gaps shaded, cracks per cell at their angle, crushing; gaps
  are parts too, dragged whole; click selects any part, drag moves it to the
  cm, Delete removes or emits `refused`), `LabCurve` (total force vs driven
  stroke and each transducer, events), `ControlCurve` (command dashed vs
  feedback vs time), `BeamPanel` (right: beam numbers and its section drawn),
  `TestStatus`. `TestStatus`, the crack colours, `niceAbove` and
  `TimeCurve` (settable `window`, ms under a second) live in
  `engineering.gui`, shared with meso, springs and circuits.

- `engineering.springs` — masses on springs and dampers swinging in 3D
  under gravity, in m, kg, N, s, z up (user: "make it 3d! it's
  deterministic enough"). `Point(at, mass, moves)` (`moves` any of
  'xyz': free, a rail, a table; '' = `pinned`, an anchor),
  `Spring(first, second, stiffness, rest)` (pulls along its turning
  line: large swings), `Damper(first, second, damping)`, and components
  (user: "component is general in nature... from the outside, this is
  basically a rod with variable length reflecting the elongation of its
  spring, but otherwise behaving like a rigid body"): so far
  `SpringMassDamper(base, tip, stiffness, damping, rest, turning,
  axis)`, its mass the tip point's, `turning` 'fixed' (tip only along
  the rod as set up), 'hinge' (about `axis`, refused along the rod) or
  'free'. Guides are LINEAR constraints on the points (an axis not in
  `moves`; a component's tip relative to its base), so the motion lives
  in a constant subspace: `basis` (SVD null space), reduced mass,
  `accelerations` = B Mr^-1 B^T f; rest/modes reduced the same way.
  Exact: fixed SMD one mode sqrt(k/m); hinged swing + bob; a rod spun on
  a turntable holds k L/(k - m w²); cart on a rail + hinged pendulum
  drifts (0 Hz) and swings sqrt(g/L (M+m)/M). Not covered: a hinge
  carried by a turning parent (its axis would turn: nonlinear).
  `System(points, springs, dampers[, components][, gravity])` whole or
  refuses (`withX`, `withPoint`, `withComponent`, `withoutPoint` drops
  what is on it and renumbers); torch float64 built
  via `doubles` (numpy) since `torch.tensor([floats])` is float32;
  `forces`, energies, `tangent` (k n nT + T/L (I - n nT), checked by
  finite differences), `rest()` = least energy (Newton, Levenberg
  shift, `pinv`: torch's default `lstsq` returned zeros on a singular
  stiffness) or None when something falls for ever, `modes()`
  (frequencies Hz, shapes, the most-moving point 1 m), `quickest`
  (bound for the step). `Motion(system[, positions[, velocities]])`:
  velocity Verlet, steps 0.02 rad of the quickest swing, at most 4000 a
  call (`slowed`), `hold(i, at)`/`release(i)` (the hand is a stiff
  critically damped spring to the cursor, 5 Hz, so it respects guides;
  anchors don't move; flings; its work booked), `energies` (kinetic,
  elastic, gravity from
  the start, dissipated, hand; `total` constant), `samples` (last 60
  s). Checked exact: hanging mass rest and modes (bob sqrt(k/m), swing
  sqrt(g/L)), a bead string's six modes, free fall, damped bob;
  energy drift ~1e-5 J. `springs.gui`: `SpringsWindow` = `SpringsToolBar`
  (Play/Pause, Reset, Add mass (hangs under the point selected), Add
  anchor, Add component (a fixed SMD hung under it), Add spring / Add
  damper (two points, Ctrl+click), Remove), `SpringsPanel` (part's
  numbers; a point's 'Moves along' x/y/z buttons; a component's Turns
  Fixed/Hinge/Free and About x/y/z; nothing selected: gravity and up to
  6 mode buttons that pluck the mode from rest, 0.1 m), `SceneView`
  (components as tubes with their coil, a fixed one's rail past its
  tip, a hinge's axle; points' rails and tables dashed; perspective
  orbit camera: drag space turns, wheel zooms; floor grid
  and shadows; coils coloured by stretch; dashpots; balls by mass;
  anchors as hatched blocks; set up a point drags square to the view
  to the cm; moving it is held and flung; refits when a new point is
  out of view), two `TimeCurve`s (energies with total; the selected
  point's x y z; last 20 s), `TestStatus`. Run with `python -m
  worQt.engineering.springs`.

- `engineering.diagrams` — section force diagrams ("snitkraftkurver";
  user: "include support for frames") of plane frames, kN and m, y up.
  `Node(x, y)`, `Member(first, second, EI, EA, startHinge, endHinge)`,
  `Support(node, kind)` (pin / roller (holds y) / fixed), loads on
  members, `s` m from the first node: `PointLoad(member, at, down,
  right)`, `LineLoad(member, start, end, first, last, direction)`
  ('down' or 'right', per metre of member, linear), `PointMoment(member,
  at, moment)` (anticlockwise). `Frame(nodes, members, supports, loads)`
  whole or refuses; `withX`, `withNode` carries loads along as a share
  of length, `withoutNode/Member/...` renumber; `indeterminacy()` =
  3m + r - 3j - releases (a node hinged on every member lets go one
  fewer, its fixed support's turning useless). `Analysis(frame)`:
  stiffness method, each member cut at its stations (ends, loads, line
  load ends; pieces >= 1 mm, a 0.1 mm piece wrecked the conditioning
  and read as a mechanism) and at least 8 pieces for the shape; hinges
  by static condensation; line loads as work-equivalent end loads; a
  node hinged on every member has its turning held. `held` = why not
  (eigvalsh min <= 1e-13 max: mechanism). N, V, M from the start end
  forces plus the loads before the section (free body, exact; Simpson
  exact for linear loads): N tension positive, V across to the left as
  the member runs, M positive pulling the right side (a beam run left to
  right sags), drawn on the side it pulls. `diagram`, `marks` (ends,
  jumps, M peaks where V = 0, roots of the quadratic), `most`, `shape`
  (Hermite, exact at the cuts). Results cached (an analysis never
  changes): ~27 ms a portal. Checked exact: qL²/8, PL/4, cantilever,
  propped 9qL²/128 at 5L/8, two spans -qL²/8 and 5qL/4, triangle
  qL²/(9 sqrt 3), point moment jump, three-hinged portal thrust qL²/8h,
  column N, sag 5qL^4/384EI. `diagrams.gui`: `DiagramsWindow` (title
  'Section forces') = `DiagramsToolBar` (Add member (3 m from the node
  selected, right else up/left/down, or joining two Ctrl-selected
  nodes), Add support (pins the node selected), Add point load / line
  load / moment (on the member selected or of the load selected),
  Remove; N / V / M / Shape lit), `DiagramsPanel` (node x y; member EI
  EA, Hinged at Start/End; support Pin/Roller/Fixed; loads' numbers,
  line load Pushes Down/Right; nothing selected: determinacy and
  reactions), `FrameView` (fitted, frozen while dragging; nodes drag to
  the decimetre, loads slide along their member to 5 cm; a click on a
  member wins over the load drawn on it; reactions green; diagram
  filled with values at marks; shape dashed, enlarged), `TestStatus`
  (Determinate / Indeterminate n× / Not held, max |M| |V| |N|). Run
  with `python -m worQt.engineering.diagrams`.

- `engineering.circuits` — electric circuits as taught at school
  (user: "i know only from teaching Danish Fysik-B"), V A Ω F H s.
  `Node(x, y)` on a grid; parts between two nodes: `Wire`, `Source(+
  first, - second, voltage, frequency, resistance)` (frequency 0 steady,
  else voltage is the peak of a sine from nought; internal resistance),
  `Resistor`, `Lamp(voltage, power)` (rated: R = U²/P, glows by P
  share), `Capacitor` (F), `Coil` (H, ideal), `Switch(closed)`,
  `Ammeter`/`Voltmeter` (ideal, + pole first), `Diode(anode, cathode,
  voltage)`, `Led(.., voltage, current)` (glows by current share),
  `Transistor(first=collector, second=emitter, base, gain)` (NPN, the
  only 3-node part: `ends(part)`/`withEnds` everywhere node indices are
  touched). Parts joining the same nodes are in parallel, drawn aside
  (`side` 0, 1, -1, 2...).
  `Circuit(nodes, parts)` whole or refuses; `label` ('R2'), `joined`,
  `at`, `withX`, `withoutNode/Part` renumber, `merged(kept, gone)`.
  `Network(circuit[, regions])`: unknowns every node voltage, every part
  current (first to second; a transistor's = Ic) and each transistor's
  Ib; KCL, each part's law, one ground a piece (minus of its first
  source). Semiconductors are PIECEWISE LINEAR (user: "some
  transistors"; the school model): diode off (open) / on (Vf behind
  0.1 Ω); transistor off / active (Vbe 0.7 behind 0.1 Ω, Ic = β Ib, 1
  GΩ C-E) / saturated (Vce 0.2 behind 0.1 Ω). `conditions` (linear in
  the state: off diode V < Vf, on i > 0, off Vbe < 0.7, active Ib > 0
  and Vce > 0.2, saturated Ib > 0 and β Ib > Ic; slack 1e-9 V / 1e-12
  A), `violations`, `turned`, `unstable()` (a growing mode: two
  transistors both active driving each other — consistent but no real
  circuit stays there); states = capacitor voltages and coil currents;
  given them and the sources the rest is one solve, so z' = A z, the
  sources' sines/cosines joined to it, stepped EXACTLY by matrix_exp
  (no step size anywhere; heat and supply integrals by Van Loan at a
  safe short step, doubled up): LC swings for ever, RC to the digit,
  critical damping exact, energy balance ~1e-15. A source with R 0
  closing a loop of wires/ammeters/closed switches/sources = short
  circuit (`problem`, `problemPart`), refused; a redundant wire in a
  wire loop carries nought (an ammeter beside a wire reads 0). A
  capacitor closing a loop of ideal branches gets 0.1 mΩ (1 µΩ left
  rounding currents of 0.04 A in its 1e-10 s mode), a coil with no
  path but itself 1 GΩ across, so they act at once (half the energy
  lost charging a capacitor straight from a battery). `modes()`:
  (tau, frequency) from eig(A), quicker than 1 µs left out.
  `Run(circuit[, run])`: `regions` settled at each moment (flip all
  failing at once, one at a time on a cycle; if the result fails or is
  unstable, search the nearest regions, fewest turned first, stable
  first, 400 tries); `advance(seconds)` exact between turns: each step
  looked at 16-512 times (more for AC) via matrix_exp, the first failure
  bisected 48 times, taken just past it, regions settled, on (at most
  200 turns a call); Networks kept per regions. Checked: transistor
  switch exact, blinker half period 0.281 s = RC ln((8.3 + 6.8)/8.3),
  amplifier gain 3.80 = (100/101)(2.2k||10k)/470, rectifier peak 11.29
  V, energy balance ~1e-16. `voltages`, `currents`, `bases`, `drops`,
  `charges`/`baseCharges` (∫ i dt, for the dots), `energies`
  (delivered, stored, heat, `balance`), `samples` (last minute; kept
  while node/part counts hold); a run on a changed circuit keeps each
  capacitor's charge and coil's current (same index and nodes, else
  same kind between the same places; regions carried too). `EXAMPLES`
  (`Example(name, hint, speed, settle, make)`): Charging a capacitor,
  Lamps in series and parallel, Internal resistance, Oscillating
  circuit, Rectifier, Transistor switch, Blinker (astable
  multivibrator), Amplifier (common emitter, settled 1 s, at 1/1000).
  `circuits.gui`: `CircuitsWindow` (1760 wide) opens RUNNING (Falstad
  style) on a 6 V battery, open switch, lamp 6 V 0.3 W, 10000 µF and a
  voltmeter across it (tau 1.2 s); `CircuitsToolBar` (Play/Pause, Reset
  | Examples (QMenu popup, `examplesMenu()`/`loadExample(i)`, hint in
  the panel note) | Wire Source Resistor Lamp Capacitor Coil Switch
  Ammeter Voltmeter Diode LED Transistor Remove | `SpeedSlider`
  (user: "a visible slider like in Sim City of old": 'Speed', notched
  stops `SPEEDS` 1/1000x..10x on a 1-2-5 scale, snapping; click, drag,
  wheel/arrows a stop; `speedChanged`; `setSpeed` snaps to it)); a
  transistor joins three Ctrl-selected nodes (collector,
  base, emitter) or puts its base at the node selected, C and E a step
  above/below two steps aside; a part button replaces the wire selected, else joins two
  Ctrl-selected nodes, else runs 2 steps from the node selected (or the
  part's second node) right/up/left/down; `CircuitView` (fitted, 24-72
  px a step; symbols as at school, IEC box resistor; leads coloured by
  node voltage red + / blue - / grey 0 at the largest source; dots move
  with the charge let through, the greatest recent current 60 px/s;
  nodes drag to the grid, dropped on a node they join it; Delete),
  `CircuitsPanel` (values; Swap + and -; diode Turn round; switch
  Open/Closed; transistor Gain β and its region in words; live
  readings; nothing selected: modes and energies), transistor drawn
  between C and E, its base lead to the symbol with its own dots
  (offsets 2P: parts then base leads),
  `voltageCurve`/`currentCurve` (`TimeCurve`s of the selected part and
  every meter, window 20 s x speed), `TestStatus` (Running / Paused /
  Short circuit). Frames every 20 ms by the time passed (5 ms grain,
  50 ms most) x speed, run in pieces no longer than `longestStep()`
  (inf; quests: `Goal.longest(run)`, a hair past a Tester's next look
  or a Clocked's next turn, so fast speeds and long `advance` calls miss
  no tick), `ran()` after each piece; a frame gives up after 0.1 s of
  work (the circuit then runs slower than chosen); panel, curves and status every 5th frame (the box model
  costs ~3 ms a widget). Reuse hooks: `CircuitView.locked` / `CircuitsPanel
  .locked` = (nodes, parts) fixed first (never dragged/removed/edited,
  drawn as square nodes; a fixed switch still works; nodes may be
  dropped ON fixed nodes), `CircuitsWindow.curves()` (() = none) and
  `ran()` (called after each run step), `CircuitsToolBar.
  __fallback_examples__`. `si`/`microfarads` live in the Qt-free
  `circuits._si`.

- `engineering.quests` — a game on the circuits (user: "gamified
  circuits ... level based sort of sandbox ... unlock more components
  by completing quests ... fixed components and a clear goal"). Goals
  (`_goals.py`, Qt-free, stateful, `update(run)` each frame, `reached`
  for good, `words(run)`): `Glow(part, least, seconds, most)` (lamp P
  share / LED I share held; over `most` = "would burn out"),
  `Toggles(part, times)` (lit >= 30 %, dark <= 5 %), `Measures(part,
  seconds)` (an ammeter reads its current, a voltmeter its voltage),
  `Afterglow(lamp, switch, least, seconds)`, `OneWay(part, charge,
  seconds)` (charge never decreasing: robust to frame rate), `Touch(led,
  switch, seconds)`, `All(*goals)`; `glowOf`. `QUESTS` (Quest(name,
  brief, speed, make, goal, reward, solution)), STARTING = Wire, Source,
  Lamp: 1 First light (wires) -> Switch; 2 On and off -> Resistor; 3 Not
  too bright (R = U/I for an LED on 9 V) -> Ammeter, Voltmeter; 4
  Measure it -> Capacitor; 5 Afterglow (C across the lamp) -> Diode; 6
  One way (rectify) -> Transistor; 7 Touch switch (1 MΩ finger: one
  transistor gives 4 %, a Darlington pair works) -> Led; 8 Blinker
  (astable multivibrator) -> Coil. Each solution uses only parts
  unlocked before it (tested). `Progress` (done names, `unlocked`,
  `isOpen` = all before done, `withDone`, text a name a line,
  `save`/`load`). `quests.gui`: `QuestsWindow(CircuitsWindow)` (title
  'Circuit quests'; `QuestPanel` left: rows ticked/ring/padlock, the
  played lit, Sandbox last, 'Start over', brief, live goal words, reward;
  circuit middle; part panel right; no curves; locked kinds' buttons
  greyed, `addPart` refuses them; progress at `progressPath`, default
  GenericDataLocation/worQt/circuit-quests.txt, tests set a temp path
  before show; opens on the first quest not done; sandbox = empty, free).
  SUPER QUESTS (user: "create something like logic gates with
  transistors which then *grants* you the resulting logic gate as a
  component. Then a full adder, then a look ahead ... adder, then flip
  flop, then jk flip flop, sram, dram, etc"): 9 NOT gate, 10 NAND, 11 NOR
  (from transistors on a 5 V bench) -> NOT/NAND/NOR chips (+ Bit, Probe);
  12 AND and OR; 13 XOR; 14 Full adder -> FA; 15 Look-ahead carry (C1..C4
  from G, P, C0, 512-row table, depth <= 6 chips: rippled is 8) -> ADD4;
  16 SR latch; 17 D flip-flop (master-slave) -> DFF, Clock; 18 JK
  flip-flop; 19 Memory (4 x 1, decoder + DFFs + mux) -> SRAM. DRAM
  dropped (user: "let's go with SRam instead"). Granted components are
  IDEAL primitives (user: "those granted parts are what allows
  ascending") (`circuits._chips`: `Chip(kind, pins)`, `SPECS` name ->
  `Spec(name, symbol IEC '&' '≥1' '=1', inverted, inputs, outputs,
  memory, clock, logic, remember, words)`), not the player's circuit.
  Chips are PWL regions in the same exact engine: region = (input
  levels, remembered bits); inputs high above 2.5 V, 0.1 V hysteresis,
  read against the GLOBAL ground (minus of the first Source/Bit/Clock;
  chips have no ground pin), no current; each output a 5 V / 0 source
  from that ground behind 10 Ω (an extra unknown each); `turned` reads
  new levels and calls `remember(before, after, memory)` (DFF takes D as
  it was when C rises). `Bit(first, second, high, name)` (ideal 0/5 V
  source, Low/High panel buttons live even when fixed), `Probe(first,
  second, name)`, `Clock(first, second, frequency)` (region high/low by
  the sign of its own sine in the state: crossings bisected exactly);
  labels use names. Bench (`_super.bench`): inputs on a left ground bus,
  probes on a right one, optional 5 V supply rail; `Tester(inputs,
  outputs, steps, wait, most)` goal drives the Bits itself (`Goal.drive
  (run)` -> circuit or None; the window applies it as Run(circuit,
  run)), reached after one clean pass from step 0; `table(n, logic)`;
  `depthOf` (chips on the longest path to a probe, nets joined by
  wires). `LogicToolBar` second row (Input Probe Clock | NOT AND OR NAND
  NOR XOR Full adder Adder 4 SR latch D flip-flop JK flip-flop SRAM),
  greyed until granted; `addChip` puts inputs in a column, outputs 4
  right; chips drawn as IEC boxes among their pins (`chipBox`,
  `chipPin`, `chipLeads`), dragged whole by the box. Fixed in passing:
  `stateAt` built sin/cos in float32 (now `doubles`); turns are bisected
  to TWICE the slack (else re-read inside it, looping); Network build
  batched (index_put_, kept dict instead of Field reads): ~4x faster,
  the look-ahead bench ~29 ms a row.
  COMPUTER QUESTS (user: "4 bit busses ... an honest to God little CPU
  with instruction sets"): buses are drawn as one node, reckoned flat.
  `Spec.portsIn`/`portsOut` group bits into ports (name, width); a
  chip's pins are a port each as drawn, a bit each when `flat`.
  `Circuit.widths()` infers each node's width through wires from port
  widths (a bus joined to a single wire raises); `Circuit.flat()` ->
  `Flat(circuit, nodes, parts, owners)` expands each bus node to 4 and
  each bus part to bit parts; `Run` simulates the flat circuit and maps
  back (`values` per drawn node; bus voltage 5 value / 15).
  `BusIn(bus, ground, value, name)` / `BusProbe(bus, ground, name)`.
  Bus chips: SPLIT, JOIN, ADDB, ALU (SUB; C high for no borrow, Z),
  REG (LD, C), MUX (S), PC (LD, EN, C), DEC (4 -> 16), ROM (16 words,
  `contents` = `program(words)`, read back by `words(memory)`), CPU (the
  first computer, a 4004 of one register R0 and no stack, memory 17,
  ports C OP N -> ADR OUT). ONE instruction set for both computers,
  after Intel's 4004 (user: "let's match 4004 on naming"; one-byte
  words only): `ISA` of `Instruction(mnemonic, op, operand, words)`,
  operand 'n' / 'r' / a fixed int naming a group member; the 4004's
  opcodes: 0 NOP, 1 JCN n (OURS: jump if carry), 4 JUN, 5 JMS, 6 INC r,
  7 ISZ r (OURS: skip next word once it wraps to 0), 8 ADD r (+C), 9
  SUB r (A + ~R + ~C, C = no borrow, the 4004's way), A LD r, B XCH r,
  C BBL n (return, A = n), D LDM n, E2 WRR (OUT = A), F0-FC accumulator
  group CLB CLC IAC CMC CMA RAL RAR TCC DAC TCS STC DAA KBP; 2, 3, other
  E/F codes pass as NOP; NO HALT (the 4004 had none): a program ends
  jumping to itself. `decoded(op, arg)`, `FIRST` (what CPU carries out,
  the rest passed over), `Machine(a, c, registers, pc, stack, out)`,
  `started(registers, depth)`, `execute(op, arg, machine)` is the truth
  (operand register taken mod the registers there are), `remembered
  (kind, memory)`.
  `Clocked(clock, probe, expected, changes, quiet, wait)` ticks the clock
  itself and notes the probe each tick (or each change), wrong notes
  kept until Reset. Quests 20-29 (`_computer.py`, `busBench`): Bus
  (fixed SPLIT), Bus adder, ALU, Register, Bus switch, Program counter,
  Decoder, Fetch (JUMPS: 0 1 5 6 3, on JUN), Computer (the first
  computer; FIBONACCI: OUT 1 2 3 5 8 13), Programmer
  (`programmerBench('CPU')`, an empty ROM its last part `loose`: TIMES,
  3 6 9 12 15). `Quest.loose` = last parts the player may edit.
  MICROPROCESSOR QUESTS 30-34 (`_micro.py`, user: "start with the 4004
  as a final boss"): Register file (build R0-R3 -> RF, 16 x 4, R D WE
  C -> Q), Stack (3 deep, D PUSH POP C -> Q; push loses the last, pop
  keeps it -> STACK), Accumulator (ADD/SUB with the carry and pass-
  through -> ACC: A R CI OP N -> S CO, also the whole F group),
  Microprocessor (the final boss, ~40 chips: A and C load every tick
  from ACC, RF named by n, PC jumping/skipping, STACK; COUNTDOWN: OUT
  15 12 9 6 3 0 -> MPU, memory 89), Calculator (`programmerBench
  ('MPU')`: DIGIT, IAC DAA WRR JCN loop, 1..9 then 0; too long to
  cheat in 16 words). `outputs(words, registers, depth)`. Writing a ROM
  word emits `programWritten` and the window resets (run and goal).
  GUI: `BusToolBar` third row (+ Registers, Stack, Accumulator,
  Microprocessor apart); `ProgramEditor` in the panel for a ROM
  (mnemonic and operand menus, registers shown R0-R15, `instructions`
  = FIRST where a CPU is the only computer, else all; `programEdited`,
  greyed when fixed); `QuestPanel` is an accordion (Quests / Super
  quests / Computer / Microprocessor, `openSection`).
  SPEED OF LOGIC (user: "wouldn't the computer be composed of
  abstracted components that are fast?"): chips are ideal, but each
  settle rebuilt the whole MNA once per logic level. Now `Run._settled`
  first propagates levels digitally (`_propagated`) when the flat
  circuit is logic alone (wires, Bits, Probes, Clocks, chips; every
  Bit/Clock minus pole on the ground net; no fights), then one network
  confirms; else the old path. A fresh Run switches on WITHOUT edges
  (`remember(after, after, memory)`: a clock already high has not
  risen; a latch's level still applies). Run no longer builds a network
  just for `statesOf`. Microprocessor quest ~9x real time.

- `gaming` — games on worQt (user: "a new package just called
  gaming"). `gaming.pusher`: a two-level coin pusher (user's mother:
  "skubbe-maskinen"), FRAUD-FREE (solid side walls, no gutters; the
  roguelike layer deferred), REAL 3D (user: the 2D one "was cringe";
  it is in `archive/`). MuJoCo was tried and dropped: on the user's
  i7-4790K a pushed carpet of ~180 coins cost 30-60 ms a 2 ms step,
  MuJoCo Warp on the RTX 5060 was slower still and blew up. So a solver
  of our own, compiled by Warp (`warp-lang`, not yet in pyproject.toml;
  kernels run on the CPU, dim 1, float32, cached in ~/.cache/warp after
  a first compile of ~6 s: `enable_backward` off for the module, Warp's
  gradient code doubled it), mm s g, z up. `Coin` (the Danish 20 kr:
  R 13.5, half thickness 1.175, 9.3 g; `inertia`). `CoinWorld(coin,
  count, boxes, edges)` (`_coin_world.py` + `_coin_kernels.py`):
  coins are sharp-edged cylinders; `Box(centre, half, turn)` (turn a
  quaternion x y z w, square to the axes by default), `Edge(start,
  end)` (a coin's face may lie over it: table front, shelf front);
  `place`/`park`, `moveBox`/`moveEdge` (velocity through the frame),
  `frame` (1/60 s), `played`, `places`/`turns` (x y z w)/`speeds`/
  `playing`, `contacts`, `deepest`/`clearDeepest`. Box2D v3's soft step
  in 3D: contacts found with speculative margins (speed x look), the
  cabinet's first, once a frame, or four times while any coin's point
  moves > 150 mm/s (found once, a coin falling onto another and turning
  as it hit slipped through it); 8 substeps of warm start, soft solve,
  integrate, relax; restitution; impulses warm-started by a key growing
  in finding order (merge-join). Coin-coin: near parallel (> 0.95), at
  the same level (middle within half a thickness of the other's plane)
  and beside: rim to rim, 3 points up the rims along the line of
  middles, however deep (coins on one floor can only part sideways;
  choosing the shorter way out merged them); near parallel otherwise:
  pressed square to the other's face from the rim of the facing face
  only (0.8 mm in when over); not parallel: both edge circles (and the
  mid rim when beside) against the other's exact cylinder distance.
  Each run reduced to 4 points, preferring warm-started ones (else
  stacks collapse). Boxes: a coin whose middle is in front of a face
  meets that face alone, only where it is over it (else a rim slipped a
  hair past the back wall's corner was pushed down under it, crushing
  the shelf's piles); off an edge or corner the exact distance. Rings
  of the facing edge circle only while within 25 deg of the face (both
  circles crowded the 4 points, coins rocked on 2), plus each circle's
  lowest point recomputed every substep (exact rolling) while it faces
  the same face. Contact hertz = 0.25 x substep rate, damping 5:
  stiffer shakes stacks apart, rigid jitters; so contacts sag ~0.025
  mm a coin above (a 12-stack 2.9 mm; 20+ stacks fall). Checked by an
  independent overlap measure: 0-3 pairs > 0.5 mm among ~180 coins,
  mostly brief, edge on edge; landings dip a median 0.5 mm.
  `Cabinet` (NamedTuple: width 360, front 300, shelf 30, pusher face
  110..180 over a 4 s period, back wall 0.6 mm over the shelf, drop
  120 to the tray, walls 130 high; x to the PLAYER'S LEFT, y toward
  the player, z up; side -1 = left; `faceAt`/`speedAt`, `pusherAt`,
  `boxes()` indexed TABLE PUSHER BACK_WALL LEFT_WALL RIGHT_WALL TRAY
  TRAY_FRONT LEFT_RAMP RIGHT_RAMP LEFT_RAIL RIGHT_RAIL, `edges()`
  TABLE_EDGE SHELF_EDGE; the table is solid down to the tray (a coin
  once fell under it forever); chutes (user: coins must not land
  upright, and must land behind the coins on the shelf): a brass ramp
  along the back wall, 75 mm at `slope` 30 deg from the side wall down
  toward the middle (`rampLine(side)`, `rampNormal`, `rampTurn`,
  `rampStart`, `chuteY`, `chuteWidth`), between the back wall and a
  rail; a coin slides down lying and lands lying at the back of the
  shelf, where the back wall pushes it on).
  `Machine(cabinet, purse, seed)` / `Machine()` (purse 60) starts EMPTY
  (user: the coins are dumped in after 'Start game'); `pour()` has the
  house pour 170 coins in as the frames go (`filling`), in two streams
  (user: "two giant satisfying piles"): 60 onto the shelf, 110 onto the
  table, a coin every 2 frames each, 6 cm over its heap's top, turned
  any way, falling at 0.9 m/s; 1 s to settle, then `countdown` 4 s
  while the machine runs (the view writes 4 3 2 1 GO!); spilled house
  coins go AWAY (out of the game); then `started` (`fill()` pours and
  plays until then); `hits` (a frame's coin-coin, coin-cabinet and
  coin-tray hits over 60 mm/s: how many, how hard) and `wonNow`, to be
  heard; `drop(side)` (onto the ramp,
  turned at random about its axis; refused until started, while a coin
  is on that ramp, or with the purse empty), `frame`, `played`; `where`
  per coin PURSE / MACHINE / TRAY / AWAY; a coin past the edge below the table is
  won; lying still 1.5 s in the tray it goes back to the purse;
  `total` constant. ~2-3x real time on the CPU with ~180 coins.
  `MachineWorker` (spawned process, in step with the clock, catching up
  6 frames at most; `start` (the machine empty), `latest` (snapshots
  drained `joined`, hits added up), `begin` (a new game: an empty
  machine poured), `drop`, `pause`, `close`) streams a `Snapshot`
  (time, face, places, turns of coins in play, books, `filling`,
  `started`, `countdown`, `hits`, `wonNow`) a frame. SOUND (user: "add
  some sound effects"): `_sounds` (Qt-free) makes them, a few decaying
  disc modes struck by a click: `clink` (coin on coin, 4 pitches 2.9-4.3
  kHz), `tick` (on the cabinet), `tray`, `beep`, `go`; `waveBytes`
  (16-bit mono WAV); `SoundPlayer` (spawned process with a PLAIN Qt
  app, `QGuiApplication` offscreen: in the window's process, 33
  `QSoundEffect`s hung it for good on the user's real audio device,
  most likely worQt's Python `App.notify` deadlock again) makes them,
  writes them to the temp folder, loads 3 copies each and plays
  ('play', name, volume); says 'ready' (after s) or 'trouble';
  `gui.PusherSounds` decides: `heard(snapshot)` plays up to 3 clinks /
  2 ticks / 3 tray rings a tick, louder the harder, a beep each
  countdown second (higher at 1), the chord at GO.
  The CoinWorld's finish kernel counts the hits (`hitFrom` 60 mm/s;
  `countApart(TRAY)`). Spin is integrated implicitly (Bullet/Box2D's
  one Newton step: explicit gyroscopic made a tray coin spin ever
  faster); a coin's spin about its own axis is left out of `quickness`
  and of the hurry test. `pusher.gui`: `PusherView(QWidget)` shows
  `pusher.qml` in a `QQuickView` (`quick`) set in through
  `createWindowContainer`, rendered in its own thread (a QQuickWidget
  draws in the GUI thread and froze the window while Qt Quick 3D built
  its shaders the first time: KDE flagged it not responding; user:
  "everything that takes a while MUST HAVE MONITORING! ALWAYS!");
  `rootObject`, `loaded`/`sceneLoaded`, `drawn`/`firstDrawn` (async
  compile as billiards; scene = (-x, z, y) of the
  machine, a turn not a mirror; boxes as turned #Cubes by kind:
  playfield, chrome back wall, glass sides, brass ramps and rails, steel
  pusher and tray; billiards' room light; orbit camera from the
  player's eye); coins: `CoinShape` (`_coin_mesh.coinMesh`: faces fanned
  and mapped to `gui/coins/head.png` (King Frederik X's portrait by Eva
  Hjorth) / `tail.png` (the crowned shield), 512 px from Danmarks
  Nationalbank's 915 px pictures, kept in `previews/`; edge reeded in
  7 sections of 60 %, grooves 0.1 mm) drawn once per coin by
  `CoinInstances(QQuick3DInstancing)` (`getInstanceBuffer` returns
  (bytes, count) in PySide6). `PusherWindow` (a `TestStatus`
  strip along the bottom says live what goes on and how long: the coin
  solver starting (compiled the first time, ~6 s; the worker plays a
  frame before its first snapshot so it compiles then), the 3D view
  loading, pouring, the countdown, play and the machine's pace against
  the clock, the coin solver's liveness (its process's CPU share from
  /proc, IDLE = maybe stuck, silent for N s, STOPPED with its exit
  code; 'Start game' restarts it) and the sound process's state (user:
  sometimes a job takes an hour, sometimes it hangs for an hour; a
  monitor must tell slow from stuck); `noted` writes each step's time
  to stderr; `watch`, a 100 ms watchdog, notes when the window was held
  up and while doing what, and re-arms `faulthandler.
  dump_traceback_later(3, repeat)`, a C-thread watchdog that dumps every
  thread's traceback if the window stops answering, even when Python
  itself is stuck;
  shortcuts application-wide; opens on the machine empty; toolbar Left chute / Right chute (greyed until the game is on)
  / Pause / Start game (the house pours, watched live, then the
  countdown, ~9 s) / Sound tick box; `bannerOf`, `PusherView.
  setBanner` (QML Text popping in over the view); keys
  Left/Right or A/D, Space; `PusherPanel` books from the snapshot,
  'Starting the machine...' until the first frame, then empty /
  pouring / how to play), `PusherApp` (dark, prints slot tracebacks).
  Reuses `engineering.gui` ToolButton/PaintPanel and billiards'
  `_room_light` (candidates to lift into core worQt).
  `gaming.billiards`: three-cushion carambole (user: an expert player
  who leads the physics; "honest 2D or real 3D, never 2.5D"), REAL 3D.
  Qt-free: `CaromTable(length, width, radius, nose, cushion, rail, bed,
  apart)` (NamedTuple, mm: match table 2840 x 1420 between the noses,
  balls 61.5 mm, nose 37 mm (UMB), x across from the left nose, y along
  from the foot nose), `footSpot`/`headSpot`/`centreSpot` (L/4, 3L/4 on
  the long middle line), `opening()` (white on the head string 182.5
  mm beside the head spot, yellow on it, red on the foot spot; checked
  2026-11-10 against the FFB's figure, article 1.3.01: D 71 cm, M 18.25
  cm, spot 4 on the breaker's left (he stands at the head facing the
  foot: larger x), 5 on his right; lag 20 cm from the long cushions,
  2.1.01), `diamonds()` (7 a long rail at L/8, 3 a short at W/4, their
  middles `diamondOut` 90 mm out from the noses, FFB 1.1.03; were
  115, mid rail, wrong); `Ball(name, x, y, turn)` (turn a unit quaternion, scalar
  first: the physics ignores it, the DOTS show it; `turnOf`, `STILL`;
  the opening lies each ball turned its own way). Look after the
  user's photos (`previews/carambole/`: Søren Søgaard Super Royal,
  Super Aramith Pro-Cup balls): `_table_shapes` (Qt-free) `prismMesh(
  profile, length, mitre, smooth)` extrudes a convex CCW cross-section
  (outward triangles, smooth normals under 30°), `tableMeshes` = sloped
  cushions (undercut face, nose at 37) mitred into the corners, ebony
  (was walnut; user: "use ebony woods instead")
  rails with a bullnose, corner blocks rounded outside, tapered
  pedestals; `gui.Prism(QQuick3DGeometry)` hands a mesh to QML (pushed
  in `shapes`, kept alive by the view). Balls: `CustomMaterial`
  (`ball.vert`/`ball.frag`): six dots on the ball's own axes, 5.5 mm,
  red on white and yellow, white on red, clear coat; colours made
  linear in QML; `<name>Turn` = `sceneTurn` (table (w,x,y,z) -> scene
  (w,x,z,-y)). `billiards.gui`: `TableView(QQuickWidget,
  WidgetMixin)` shows `carom.qml` (Qt Quick 3D, mm, y up, cloth middle
  at the origin, head end at -z; cyan-blue cloth, beige corner panels
  and inlays on the ebony body, floor; diamonds; 3 soft-shadowed spot
  lights as the lamp; SSAO; MSAA; filmic; `OrbitCameraController`; the
  room as image-based light: `roomLight` paints an equirectangular HDR
  in numpy (a lamp strip 1 m up along the table, dim warm walls) and
  `radianceBytes` writes it to the temp folder as the light probe);
  Python pushes sizes, `<name>Place` and `diamondPlaces` into the root;
  `scenePlace(x, y, height)`, `sceneValue(name)`, `problems`. LOADING:
  `App.notify` is Python, so every event on any thread wants the GIL; a
  plain `setSource` holds it waiting for the QML loader thread, which
  waits for the GIL: DEADLOCK. So `load()` compiles a `QQmlComponent`
  asynchronously first, then `setSource` (cached), `loaded`,
  `sceneLoaded`. `BilliardsWindow` ('Three-cushion'), `BilliardsApp`.
  A light with a `scope` SEGFAULTED the render (Qt 6.10): the cloth's
  bounce into the balls lives in `ball.frag` as emissive instead.
  My sandbox cannot render Qt Quick 3D (no display/GPU even unsandboxed):
  the user runs `previews/shoot_billiards.py`. The physics agreed with
  the user lives in memory ('project_billiards_physics'). FIRST SLICE
  (user: "confirm that nothing crazy happens if a single ball begins to
  move"): `Ball` carries `vx vy` (mm/s) and `wx wy wz` (rad/s); `Cloth(
  sliding 0.2134, rolling 0.01, patch 2.027 mm, gravity 9810, rollBack
  1.5 mm)` moves ONE ball
  exactly, phase to phase, no time step: sliding (slip u = v + w x
  (-R z) keeps its direction, dies at 7/2 mu g, ends after 2|u|/(7 mu
  g), snapped to rolling), rolling (slows at 5/7 'rolling' g, the
  felt's push ahead of the lowest point over R), spinning in place,
  still; side spin dies at (5/3) mu g a / R^2 (patch friction) and
  never bends the path; only `turn` is stepped (1/500 s, midpoint
  spin) for the dots. No cushions, no collisions yet: the window's
  shots (`BilliardsToolBar` Roll / Slide / Spin / Draw / Reset; each
  from white's opening spot down the table) all stop on the cloth;
  frames every 16 ms (`tick`, `advance`). The roll-back at rest is not
  modelled yet.
  CUSHIONS AND CAROMS (user: "make sure those values are adjustable",
  to be balanced against filmed shots; SUPERSEDED 2026-11-11 by the
  MATHAVAN CUSHION below, kept as history): `Cushion(liveliness 0.8608,
  deflection 6 mm at firm 2 m/s, sideGrip 0.4703, topGrip 0.14 (was
  0.4028 from the break fit, see 'UNSTUCK' below), stiffening
  1, step 1e-5)`: a very under-damped spring-damper pushing along the
  line from the nose (37 mm up) to the ball's middle, so also down into
  the slate; friction split along the cushion (side spin) and up/down
  the nose (follow/draw), each capped by its share of the push, so
  "velocity decides" how much spin survives. `Carom(liveliness 0.94,
  contact 0.25 ms, friction 0.1302 slow -> 0.01 fast over slipScale 920
  mm/s (Alciatore), step 1e-6)`. `Motion(table, cloth, cushion, carom)
  .advanced(balls, seconds)`: exact cloth phases between events found
  exactly (phase ends; cushion hits, quadratic; ball meetings, quartic
  via numpy.roots + Newton); all contacts stepped together (cushion
  pushes, ball pushes with capped friction (cap slip/7, gear effect),
  slate friction under weight + every push down, spin decay by load),
  untouched balls moved exactly meanwhile. `energyOf` counts the
  springs. Probed: straight back exactly; 45 deg in -> ~37 out
  (trolling); running/reverse side 25/57 deg, effect halves 0.5 -> 2
  m/s; draw into a cushion -> follow; slow + side 287 -> 305 mm/s out;
  tokyo drift 2 hits; 30-degree rule 27.2/34.1/28.5; full stun 0.029 /
  0.970; side spin share 6% slow, 1.4% hard. NOT YET: jumps (a fast
  ball with heavy top spin leaves the table: needs height), frozen /
  wedged balls (sticking friction with memory). Window shots aim at the
  red from white's opening spot (`__shots__`: speed, aim across red in
  radii, roll, side); `resting()`; worst frame ~28 ms in a cushion
  hit.
  SHOT CONTROL (user: "put a certain force into a certain point on the
  ball in the direction the camera is facing"). THE CUE IS JUST ANOTHER
  CUSHION (user): `Cue(weight 510 g, ballWeight 210, endMass 8,
  liveliness 0.75, contact 1 ms, grip 1/sqrt 3, step 1 us)`; seen from
  the stick the ball flies into a standing tip: a spring and damper
  along the line from the point struck ('top' up / 'side' right, shares
  of R) to the ball's middle, chalk friction capped at 'grip' of the
  push, the stick heavy along its length, only its light end giving
  sideways and up/down. Out come: centre ball (1 + e) M/(M + m) of the
  stick's speed; off the middle slower, and SQUIRT to the other side
  (`squirtOf`: 1.8 deg at 0.3 R, 3.0 at 0.5 R, less the lighter the
  end; a near weightless end is the old classic cue, 2/5 roll, 2.5 v/R
  spin); `rollHeight` 0.44 R (the end lets the push lean into the
  slate); `limit` = sin(atan grip), the chalk's hold: 0.6 at `grip`
  0.75 (user, 2026-11-11: more spin; was 0.5 at 1/sqrt 3, shots inside
  it barely change, the breaks hold). The stroke is linear in speed: `strokeOf(top, side)` at a speed of one, cached.
  `.struck(ball, aimX, aimY, speed, top, side, radius)` lays the stick
  along the aim, 'speed' = the centre ball's; `.sent(...)` leaves along
  the aim at 'speed', the stick laid off by the squirt (the game,
  `firstBreak` and the Korean break use it). `ShotPanel` (right of the view):
  cue ball White/Yellow (lit, `cueChanged`), `HitPicker` (the face,
  click/drag the tip's spot, dashed miscue ring, natural-roll mark,
  `hitChanged`), Centre, Power `QuantitySlider` 0.2-10 m/s (user: more),
  Shoot (`shootAsked`, greyed while moving: `ready`). The scene's camera
  orbits `cameraFocus` (NOT 'focus': a FINAL Item property), gliding
  (Behavior) to the cue ball once all rest; a faint aim line from it
  the way the camera faces (`cameraForward` = camera.forward);
  `TableView.aimAt/stopAiming/cameraHeading`; `BilliardsWindow.shoot(
  aimX, aimY)` / `shootAlongCamera`; toolbar is Reset only. An elevated
  cue (masse, swerve) is not modelled.
  REFEREE AND MATCH (user: "go grab the actual rules... use those" =
  the FFB's Code Sportif Billard Carambole 2026-27, copies in
  previews/rules, articles in memory 'ffb-carom-rules'): `Motion.played
  (balls, s)` -> (balls, touches): each contact logged once as it
  begins, `Touch(kind 'cushion'|'ball'|'off', first, second)`, cushions
  `CUSHIONS` = left right foot head; identical whatever the frame size.
  `CaromTable.spot(1..5)` (1 red's, 2 middle, 3 head, 4/5 on the head
  string 182.5 either side), `openingFor(cue, 4|5)`, `lagPosition()`,
  `respotted(balls, cue, concerned)` (2.2.07-E: cue on 3, red 1, other
  2; taken -> the taker's spot). `Rules(cushions 3, distance 40, innings
  0, equalizing, sets 0, shotClock 0, lag)`; `Shot(cue, owner, before,
  touches, after, opening, aimX, aimY, early, late)`; `Call(point, foul,
  article, words, respot)`; `Referee(rules, motion).call(shot)`: fouls
  first (early 2.1.17-1, late -6, wrong ball -5, into a frozen ball or
  cushion 2.1.12 (FROZEN 0.1 mm), off the table 2.1.14, break not red
  first 2.2.03), then both balls with >= cushions before the second
  (2.2.05); `frozenTo`, `lagCall` (only the short cushions, the far one
  (foot) FIRST and once, nearest the near (head) one wins; the user won
  a lag lagging the wrong way, so going to the near cushion first is a
  fault and the window turns the camera to face the foot at every lag
  and opening, `_faceTheFoot`). `Match` (immutable NamedTuple, `_with`
  without kwargs): lag -> choose -> break (breaker plays white,
  2.1.04) -> play; point plays on, miss/foul passes; equalizing last
  inning from the start (2.1.09); innings limit; sets (2 points a win,
  1 each a draw, breaker alternates); draws; `said()`, averages, best
  runs. GUI: toolbar Game | Sandbox | New game (Reset) | Mulligan | Move
  balls; the panel shows heading, score rows, status, the call, choices
  (Break / Let the other break, Spot 4/5, Respot), cue ball (fixed in a
  game), hit, power, Shoot ('Set white's lag' then 'Lag' strikes both).
  Move balls: the bed is pickable; a QML DragHandler over the view
  (camera's mouse off) emits clothPressed/Dragged/Released, TableView
  turns them into table places; drags keep balls on the cloth and off
  each other. The user's first break (4 m/s, 0.38 R up, 0.26 R left,
  past red's right) scores through the engine: a test (the tests'
  `breakAim`, `BREAK_AIM` 1.2 R off red's middle, sent; the user made it
  at 1.0 R in the engine of the time, which now misses by 643 mm; it
  scores from 1.1 to 1.35 R, `struck` only 0.875-0.9).
  SIMULATION APART FROM RENDER (user: "let the compute calculate the
  shot fully... create the animation from the time-state matrix";
  streamed): `Motion.glided(balls, most)` -> `Glide(phases, span,
  after, touches)` and `Motion.collided(balls, most, whole)` are the
  pieces `played` strings together; `played` cuts the last contact step
  at its end, so short frames drifted a shot by mm (the old window).
  `Recorder(motion, rate 1000, size 50, longest 60)`: `stretches(balls)`
  plays a shot at once, whole steps only, sampling it (glides exactly,
  hits as each step reaches a sample), yielding `Stretch(first, states
  (samples x balls x STATE 11: x y turn4 vx vy wx wy wz), touches
  ((time, Touch)...), over)`; the last sample is the balls at rest; the
  result equals `played` over the whole shot to the digit, at any rate.
  `Recording(names, rate, parts, starts, touches, over)` (immutable,
  `joined`, `count`, `known`, `ballsAt(t)` blended, `last`,
  `touchesOf`, `timeOf(n)`). `ShotWorker` (spawned process, `warm`,
  `start(recorder, balls)` drops the shot under way, `received`,
  `waited`, `close`, `running`; a worker asked several shots in a row
  jumps to the last, `_latest`). ~10x faster than real time at 1 kHz.
  FASTER HITS (user, 2026-11-10: "speed up the contact loops", physics
  unchanged): `Motion.hitsOf(balls)` -> `Hits`, the stepping state of
  one run of hits, `run(seconds, whole)` as often as asked till `over`
  (`collided` = one run); the `Recorder` keeps ONE `Hits` through all
  the samples of a run of hits, so recordings at any rate still equal
  `played` to the last digit (checked 41 shots at 250 and 1000 Hz).
  Inside: a ball touching nothing that provably cannot touch anything
  for > `_DOZE` 0.1 ms SLEEPS (`_doze`: until its phase ends, its exact
  `hitTime`, or another ball could close the gap with both at
  `_fastestOf` = 1.05 sqrt(2 E) + roll-back speed + 1, E all the energy
  incl. springs), moved on exactly from its anchor when it wakes;
  asked for meanwhile (`balls()`), reckoned from the anchor and left
  asleep (that is what keeps it rate-independent); one contact pass a
  step (`_touchesAmong`, skipping cushions out of reach); constants
  worked out once (`_Fixed`/`_fixedOf`, same arithmetic, so pushes are
  bit-identical). Against the old loop: identical to ~1e-10 mm for ten
  pieces of the break, then chaos (the OLD engine nudged 1e-12 mm ends
  4.7 mm off); same contacts in 122/122 recordings; contact loop ~4x,
  whole shots ~1.8x faster. The map's previews run WHILE AIMING: the
  shot where the aim stops is played ~0.15 s later, drawn ~0.26 s.
  `Referee.decidedAt(shot)`: touches deciding the call (0 at once, -1
  at rest). Window: `_play` asks the worker, `advance` shows as far as
  has come (waiting, never skipping), the call shown at its moment,
  the game kept at rest; `finish()` plays it out (tests); a worker gone
  or stuck means the shot is played in-process; toolbar 'Replay'
  (`canReplay`, `replay`), the balls then as they lay; Mulligan/New
  game/mode stop a shot under way.
  VIEWS AND THE DRY RUN (user: "the actual RL procedure is to dry run
  your cue on ball 2"): the scene has an `overheadCamera` 12 m up,
  straight down, the length across the picture (right = scene -z, up =
  -x), its field of view fitted to whichever view shows it
  (`overheadReach`); a corner `View3D` (`importScene: view.scene`)
  shows it; `overhead` (toolbar 'Top view', `toggleOverhead`) shows the
  view from above in the main view and HIDES the corner (user: "when in
  overhead view, hide the minimap"; QML `cornerShown`; the old tap on
  the corner to swap back, `swapAsked`, is gone); the camera is a dot
  seen from above (a sphere
  round it, culled from inside). Balls are pickable; a tap (TapHandler,
  not while moving) on a ball or, from above, on the cloth (mapped by
  `overheadPlace`) emits `tableTapped` -> `tapTable` looks from the
  nearest ball within 2R. Panel 'Look from' White/Yellow/Red
  (`lookName`, `lookChanged`, set to the cue ball whenever it changes);
  the camera turns round the look ball; looking from another than the
  cue ball, 'Shoot' says 'Mark' (`marking`, `markAsked`): `mark(aimX,
  aimY)` puts a transparent ghost of the cue ball (`setMark`, cue
  ball's colour, opacity 0.35) two radii behind that ball against the
  aim, kept until the shot or the balls are laid anew (`markPlace`).
  Geometry only, no throw: as a cue laid on the ball.
  MINIMAP AND DIAMONDS (user): the diamonds are rhombus inlays
  (`diamondMesh`, `DIAMOND` 34 x 18 x 2 mm, LONG ACROSS the rail, the
  short dimension along the cushion: user, 2026-11-11),
  emissive past 1.6 so `ExtendedSceneEnvironment` glow blooms them
  alone; over the rails the camera looks towards (outward normal .
  heading > 0.5), upright ghost diamonds 110 mm up face the camera, not
  while overhead. The corner view's own children (seen only there, only
  while it shows the view from above): a halo under each ball in its
  colour, the diamonds 2.6x, and the camera's cone (`wedgeMesh`, a flat
  triangle scaled to `cameraHalfAcross`). Toolbar 'Field of view'
  (`viewSlider`, 20-90 degrees, vertical) -> `setFieldOfView` ->
  scene `cameraView`. NO glow at all (ExtendedSceneEnvironment's bloom
  hazed everything blue, then blurred the diamonds into blobs; the user
  wants it sharp): the diamonds shine by emissive alone. Minimap
  diamonds 3.8x, gold. The wood lacquer is satin (clearcoat 0.6, rough
  0.35): a mirror lacquer reflected the overhead lamp and turned the
  ebony white from above.
  MULLIGAN, KEYS, GHOST LOOK (user): 'Retry' is now 'Mulligan'
  (`mulligan`, `mulliganButton`): the balls as before the last shot and
  its mark as it was (`__mulligan_mark__`), even under way. Keys A/D
  turn the aim left/right, W/S tilt the camera up/down (QShortcuts on
  the window, auto-repeat) by toolbar 'Aim step' (`stepSlider`,
  0.01-1 degree on a log scale, 0.1 first: `QuantitySlider.
  setLogScale`): `turnAim` -> `TableView.turnCamera` -> QML `turnBy` (QMetaObject.invokeMethod; pitch kept in -89..-2);
  `cameraTurnNow` reads the turn, setting `cameraTurn` applies one.
  Arrow keys (user) move the point struck: Up/Down top, Left/Right
  side, `__spin_step__` 0.05 R a press, auto-repeat (`spinBy` ->
  `HitPicker.setHit`, kept inside the miscue limit); End ->
  `picker.centre`. Window shortcuts win over a focused slider's own
  arrow keys.
  Panel 'Look from' has 'Ghost' (only while a mark is there,
  `setGhostAvailable`): `ghosting`; the camera stands at the ghost
  FACING THE CUE BALL'S WAY OFF THE HIT (user), square to the line of
  middles, no spin: QML `ghostFor(yaw)` puts the ghost 2R from
  `ghostOf` (the marked ball, `markBall`) square to the view, on the
  side the cue ball (`ghostFrom`) comes at; entering, `faceCamera`
  turns to the mark's own departure, so the ghost stays put; turning
  chooses the way and moves the ghost; leaving freezes the mark there.
  Minimap: gold crosshairs under `aimFrom` and a short cone (520 mm)
  from it, marking what is looked from. Ghost diamonds stand over every
  rail the camera sees from the table's side (camera inside the
  diamond's line). The aim line is 6 mm wide, 150 + 0.33 x speed mm
  long, white to red up to 8 m/s (`setAimSpeed`, from the power).
  ROLL-BACK AND FITTED CONSTANTS (user): `Ball.settling`; as a roll ends
  the felt pushes the ball back `Cloth.rollBack` 1.5 mm, rolling, once
  (`Cloth.rolledBack`; contacts reset the flag; Recorder STATE 12;
  energy tests use a felt giving nothing back). The cushion, cloth and
  ball-friction constants were FITTED (Nelder-Mead, prior toward the old
  values) to the Korean break diagram (japong.com 초구, see memory
  'reference-break-literature'), the shot aimed exactly: spot 5, 3/5 of
  the red on its left, 2 o'clock at 2/3 of the miscue limit ("2 tips"
  on a 3-tip scale; 1 tip = shaft edge on centre, Alciatore's 0.5 R
  limit), 4.848 m/s. Matched: the cue ball's corner and third rail
  (1219 vs 1176), the red's route and rest; still off: the red runs
  ~400 mm long on the right rail, the cue ball kisses the red and the
  point is a knife edge. KNOWN CLIFF: a ball rolling slowly along a
  cushion while touching it is stepped at 10 us for seconds (minutes of
  compute); fix pending. `BilliardsApp.
  handleException` prints a slot's traceback (App's default swallows).
  TRAILS AND OPENING SIDE (user, after the European club final's
  broadcast stills, `previews/carambole/stills`): seen from above, in
  the corner or in Top view, a shot is drawn as it goes, as the
  broadcast draws it.
  `Recording.placesOf(start, stop)`, `Recording.struck()`; Qt-free
  `Trails(spacing 3 mm, taken, kept)` (`followed(recording, s)` takes
  in new samples only, keeping each at least `spacing` on, the same
  framed or at once; `paths(recording, s)` ends at the ball now) and
  `ribbonMesh(points, halfWidth, lift)` (flat, mitred, 4 half widths at
  most, cut square on a reversal). `Prism.setMesh` updates in place.
  `TableView.setTrails(paths, bold, hands)` / `clearTrails` /
  `setHandShown`: ribbons in the balls' colours, the struck balls bold
  (24 mm, at least 3 px; others 12 mm / 2 px, by the scene's
  `overheadScale` mm/px, `overheadRescaled` rebuilds), faint start balls
  for those that moved, and the hand: `handPicture()` (QPainter, 700 x
  240 mm, black three-finger glove, bare ring and little finger, gold
  cuff stripe, fading sleeve, maple shaft, chalked tip at the right
  edge) laid flat behind ball 1, tip at the ball, along its departure,
  real size but never shorter than 120 px. TWO LAYERS (user: "have the
  cue move back from the hand ... and animate the cue hitting the
  ball"): `handPicture()` the hand, arm and hand shadow; `cuePicture()`
  the shaft, ferrule, tip and cue shadow, same 700 x 240 frame, slid
  `cueBack` mm (QML; `TableView.setCueBack`) back along the line. Both
  lie at QML `handLift` = 2R + 2 mm, over the balls, cushions and rails
  (user: "the hand has to be on top of the cushion"; at cloth height
  the cushions hid it); the cue `depthBias: -1000` so it always sorts
  over the hand (Qt Quick 3D sorts blended models by distance). `cueBackAt(seconds, wait, most)`
  (Qt-free): address to 0.12 of the wait, smoothstep back to `most`
  by 0.62, held to 0.76, forward most(1 - u^2) meeting the ball at
  `wait`, then follow-through to -`FOLLOW_SHARE` 0.4 x most over
  `FOLLOW_SECONDS` 0.15 s, held. The window: `backswingOf(speed)` =
  min(30 + 0.015 speed, `STROKE_MOST` 140 mm, tip short of the bridge);
  Shoot `_beginStroke(press time, speed)`, `tick` -> `_stroke(now)`; a
  shot struck at once (`shoot`) gets the follow-through only.
  `previews/cue-stroke.png` shows six moments. QML `ShotTrails` twice: in
  the main scene (visible only in Top view) and among the inset's own
  children.
  Toolbar `handBox` 'Hand' (ticked). Trails stay until the next shot or
  the balls are laid anew (`_clearTrails`, `_dropStaleTrails`); a replay
  redraws them. Choices are hidden while a shot plays. 'Spot 4/5' are
  now 'Left spot'/'Right spot' (spot 5 is the breaker's right, x below
  the head spot), lit by `showSpot`, shown in the sandbox too while the
  balls lie as an opening (`openingSpot()`); `__opening_spot__` kept for
  every opening; sandbox Reset lays the opening for the cue ball chosen.
  New game in a game still starts on the lag (FFB 2.1.01).
  UNFOLDED MAP (user: "hitting a cushion simply means continuing on a
  mirrored copy of the same table"; English "just any arc will do"):
  Qt-free `Unfolded(table, across 2, along 1, bend 7500, step 10)`: a
  copy is the cloth less `reach` each side (a touching ball's middle on
  its edge), copy (0, 0) the table, odd copies mirrored; `tile`,
  `copies`, `corners(i, j)`, `bounds`, `imageOf(x, y, i, j)`;
  `curvatureOf(side, speed)` = -(side / 0.4) sqrt(3000 / speed) / bend
  (right English bends clockwise; the engine's unfolded shots bend that
  way); `arcOf(x, y, aimX, aimY, side, speed[, state])` STRAIGHT
  BETWEEN THE CUSHIONS' LINES (the user's un-spline), straight along the
  aim to the first line, turning at each as `kicked(hx, hy, long, state,
  side, mirrored)`: the part across kept as `flatten` 1.0 +
  `flattenSpeed` 0.02/m/s + `flattenRoll` -0.2 x roll share (clamped
  0.2..1), English pushing along the cushion to the ball's right by
  `sidePush` 1.4 x side x part across, flipped in mirrored copies
  (`_bentPath`, `_toLine` returns (part, long) per line met). Fitted
  2026-11-10 to 135 engine shots; STILL OFF: 3rd cushion median ~400 mm
  with draw, ~230 stun, ~180 follow (spin curves the ball after a
  cushion; not modelled); so the user chose: "just calculate the main
  expected path" with the ENGINE: the window's `previewer` (a second
  `ShotWorker`) plays the cue ball ALONE as aimed (`Cue.sent`, `Recorder
  (motion, 250 Hz)`) whenever the shot key changes (`_preview`, dropping
  the one under way; ~0.1 s), `Unfolded.wayOf(recording, name)` unfolds
  it (mirrors at each cushion touch; samples (x, y, speed, spin)), and
  `UnfoldedMap.showWay(key, way)` draws it while `shotKey()` matches
  (`engineWay()`); hits, crossings and the fans (analytic, from the
  engine state at the hit) are reckoned on it; till it comes the
  estimate shows, the caption 'Working the shot out on the table...'.
  Then (user: "the fun comes from those paths on the full map to be
  accurate") EVERYTHING from the engine: three `previewers` (ShotWorkers)
  play the whole shot, all balls, as aimed and with the aim off
  `spread` degrees either side (`_startPreview`); `Unfolded.runOf
  (recording)` -> `Run(rate, cue, ways, meets)`: every ball's way
  unfolded, a ball met adopting the frame of the ball meeting it (its
  image there is what was met), each cushion mirroring that ball's own
  frame (`_mirrored`); `UnfoldedMap.showRuns(key, runs, words)` (aimed
  first; the two side runs once played; `words` = the referee's call on
  the shot as aimed, `_previewWords`, the caption); `_figuredRun`: the
  cue ball's whole way, crossings numbered up to the second ball it
  meets, the ghost at its first meeting; `_paintRuns`: each moving
  ball filled from its side runs to its aimed way (`_screenOf`, 360
  points evenly in time, from when it sets off), the other balls' aimed
  ways in their colours with stop rings. A lone-ball `showWay` stays
  for previews of the cue ball alone. The engine plays a shot the
  MOMENT IT CHANGES, WHILE STILL AIMING (user, 2026-11-10: "calculate
  while aiming"; the 1 s settle before it is gone), `showWorking(key)`;
  each new key drops the shots under way, and a worker asked many in a
  row jumps to the last (`_shot_worker._latest`), so the shot where the
  aim stops is played ~0.2 s later; the caption 'Working the shot out
  on the table...' meanwhile, 'An estimate, till the shot is played on
  the table.' if the engine was never asked; turning back to the shot
  last played shows its runs at once. The estimate stays as the
  fallback till the engine answers: `crossingsOf(points)` -> `Crossing(x, y, long)`, the cushions met. A
  guide, not the shot. GUI `UnfoldedMap` (painted, length across, head
  right as the view from above): copies, the table bright and rimmed,
  cushion lines with diamonds, the other balls in every copy, the cue
  ball on the table only, the arc with numbered crossings, a caption;
  `showShot(balls, cue, aim, side, speed)` repaints on change. Toolbar
  'Unfolded' (`mapButton`, `toggleUnfolded`) shows it as a column
  between the view and the panel; 'Full map' (`fullButton`,
  `toggleFullMap`, `fullMap`: `Unfolded(table, 3, 3)`, 7 x 7 tables)
  shows one instead of the 3D view (the view hidden; A/D still turn the
  aim). Every ball shows mirrored in every copy, the cue ball ringed on
  the table itself; `UnfoldedMap.unfolded` is settable. Each tick
  `_showUnfolded` passes the shown maps the balls and, resting and
  looking from the cue ball (not the ghost), the camera's heading, the
  panel's side, top and power. FANS (user: "the full map should also
  show paths after collision ... a trace that grows in a fan showing
  the probability distribution of outcomes"; then, as 41 sampled ways
  lagged: "find the expected outcome, the left sigma and the right
  sigma and then interpolate"): `Unfolded(..., spread 0.25 deg)`; `imagesOf(balls, skip)` (the cue ball's own
  images left out), `hitOf(points, images)` -> `Hit(x, y, dx, dy, name,
  bx, by, travelled, offset, index)` (first contact at 2R, exact on the
  step, numpy), `rollShareOf(top, side, speed, travelled)` (the cue
  ball's roll as a share of rolling, from `Cue.sent` and `Cloth`
  straight on; 1 after a cushion), `fanOf(hit, share, side, speed)` ->
  `Fan(cue, struck)`, THREE ways each (offset - sd, as aimed, + sd; sd
  travelled tan(spread) + 1 mm), each `rayOf` `__ray_points__` 120
  points over the map's diagonal, so the ways between are drawn by
  interpolating point by point (a miss: the cue ball goes on past, the
  ball met's way its thinnest cut); frictionless
  equal balls: struck along the line of centres, cue ball (5/7) tangent +
  (2/7) share x its way (Alciatore; half-ball rolling 33.7 deg, struck
  30, stun 90 off the struck); misses go on past; the cue ball's ways
  bend with its English as sent. `UnfoldedMap.fanned` (the full map):
  the arc ends at the hit, a dashed ghost of the cue ball there, each
  fan filled faintly from each edge to the way as aimed (near a
  half-ball hit both edges lie on one side: the 30 degree rule), a way
  half way drawn, the aimed way bright, clipped to the map. Speed:
  `figure()` (arc, hit, fan, crossings) cached per shot, ~3 ms; the
  frame (bounds, scale, corner) cached per size; `Unfolded.reach` cached
  (`Motion` was built per point: the lag); copies, diamonds (one
  `drawPoints`) and balls painted once into a backdrop pixmap per
  balls/size; the arc drawn at >= 3 px a point: an aiming repaint
  ~16 ms offscreen. `showShot(balls, cue, aim, top, side, speed)`.
  ROLL LENGTHS, DRAG AIM, FOLLOWING, COUNTER, SOUNDS (user): traces end
  where the ball would stop, roughly, TABLE BY TABLE (user: "draw into a
  cushion switches to accelerate after"): a `State` (speed, the speed
  its spin alone would roll it the same way) from `stateOf(top, side,
  speed)` (`Cue.sent`); `rolledOn(state, distance)` slides as `Cloth`
  (grip mu g; speed and spin meet at (5v + 2u)/7; overspin speeds it
  up), then rolls (`Cloth.rollingDecay` x `slowing`), stops;
  `bounced(state, part)`: speed x sqrt(1 - c^2 + bounce^2 c^2), spin
  turned round with the way, its part across flipping (draw met square
  on -> follow), x `spinKept`, + `spinReset` x speed x c^2;
  `stateAfter(points, state)`. FITTED 2026-11-10 to 100 single balls
  the engine played (0.8-4 m/s, 15-90 deg, top -0.45..0.44), refitted
  2026-11-10 for topGrip 0.14 (grid over the roll lengths): bounce 0.9,
  spinKept 0.4, spinReset 0.0, slowing 0.97, distances median 4.6 %
  (the old 0.88/0.1/-0.4/1.0 gave 10.8 % on the new engine). UNSTUCK
  (user: "yeah update"): with topGrip 0.4028 every ball met square on
  STUCK at the nose and left with draw = -sin(theta) = -0.2 of rolling
  whatever it brought (sin theta = (nose - R)/R); topGrip 0.14
  (Mathavan et al. 2010's measured ball-cushion friction) turns the
  spin round: 2 m/s with 0.9 draw in -> +0.17 follow out, follow in ->
  -0.21 (`test_cushion.test_spin_turned_round`). Even with no top
  grip at all, draw comes off at most ~+0.9 of rolling (the cushion
  gives back ~0.8 of the speed and its push down makes the slate grip
  through the hit), so only strong draw speeds up after a rail.
  sideGrip STAYS 0.4703: the two grips are separate caps, so at a low
  side grip the along-friction saturates and English stops bending the
  way out (reverse = plain); a single Coulomb cone at 0.14-0.2 lost the
  English too (probed). All 10 cushion tests and the Korean break hold
  at 0.14. The user's first break, aimed at 1.0 R off red's middle,
  missed the yellow since the cushions were fitted (either grip); its
  tests now aim it at `BREAK_AIM` 1.2 R (2026-11-11). A line is
  charged to the step ARRIVING at it (`_linesMet`), a corner both lines
  (`_toLine`), so the arc and `stateAfter` agree (the fans had vanished:
  charged twice); MATHAVAN CUSHION (user, 2026-11-11: "implement
  Mathavan et al. but then add in our thing about higher speed -> more
  perpendicular", "in the range indicated by Mathavan et al. let them
  decide. We modify only outside these ranges"): `Cushion(liveliness
  0.98, deflection 6, firm 2000, grip 0.14, stiffening 1, step 1e-5,
  squaring 0.01, squaringFrom 2500 mm/s, squaringOnset 500,
  squaringBelow 20 deg, squaringWidth 3 deg)`. The soft contact now
  obeys Mathavan, Jackson & Parkin 2010 (paper's e 0.98, mu_w 0.14,
  mu_s = cloth 'sliding' ~ their 0.212): the push along the line from
  the nose to the ball's middle AS IT MEETS IT (fixed `across`/`down`,
  not leaning as the ball sinks: their cushion is rigid), ONE Coulomb
  cone at the nose against the 3D slip there (`_motion._nosePushed`,
  kernel `sidePushed`, sum for sum, bit-identical), the slate under the
  push down and the weight. `_mathavan.mathavanRebound` is their rigid
  model (impulse steps, Stronge's energetic restitution; checked line
  for line against pooltool's port), the reference: `test_cushion.
  test_mathavan` holds the soft cushion to it within 1 deg and 2 % for
  rolling balls 0.5-2.5 m/s, 0-60 deg, side +-0.5 (worst 0.73 deg, the
  weight on the slate they leave out). Past their range (2.5 m/s
  straight in, where they say the cushion's give matters) the user's
  SQUARING: a pull at the ball's middle against its speed along the
  cushion, `squaringOf(comes, along)` share of the push = squaring x
  0.001 x over²/(over + onset) (over = comes - 2500: exactly nought
  up to 2.5 m/s, C1 after) x softplus((20 deg - angle)/3 deg) /
  softplus(20/3) (a softplus, not a swish: a swish dips below nought
  past its limit and would push balls away from square), never past
  square; `comes` = the speed straight in it came at, known
  memorylessly from the spring's energy, sqrt(giving² + 2 U)/across.
  At 0.01: 6 m/s, 6 deg in -> 2.1 out (Mathavan 4.1), 10 -> 5.4 (6.9),
  20 -> 14.0 (14.5), 25+ unchanged (`test_squaring`). English in
  Mathavan's cushion: at 45 deg running/reverse 0.5 R of spin move the
  way out only +3/-1.3 deg; near square a lot (10 deg: 14.4 / 0.9).
  DECIDED (user, 2026-11-11: "Let Mathaven decide for now"): two of
  the user's observations do not happen at mu_w 0.14, reverse English
  steepening 45 deg (-0.7 deg) and slow + heavy side spin leaving
  faster (267 vs 286 mm/s); a single cone gripping enough for them
  (0.25-0.3) sticks a ball met square at the nose, draw out (the old
  UNSTUCK problem). `test_side_spin` now holds running English
  flattening by 5+, reverse within 2 deg at 45, and +-0.5 side at 10
  deg turning the way out 5+ either way; `test_faster_out` became
  `test_side_spin_kicks` (kicked > 10 deg off square, slower). MINIMAP
  (user, 2026-11-11): the corner has NO view cone any more (the wedge
  Model, `wedgeMesh`, QML `cameraHalfAcross` and their tests gone; the
  gold crosshairs stay). The last shot's ways stay until the next shot
  begins to be aimed: `_aimBegun` (A/D/W/S `turnAim`, a map's
  `aimFromMap`, a stroke's press, QML `aimTouched` on a left press on
  the view outside the corner; during early set-up remembered,
  `__aimed_early__`, and done at rest) takes them off. A right click on
  the corner (QML TapHandler, the stroke's PointHandler ignoring presses
  there, `inCorner`) -> `minimapMenuAsked(x, y)` -> `_minimapMenuAt` pops
  `minimapMenu()` (built anew each time, as the disk app's
  `contextMenuAt`): 'Previous' (the last shot's ways again), 'Clear',
  'Options' (a submenu, 'None yet', greyed: options to come), 'History'
  (each shot of this game newest first, 'n. <call words>', `showShotOf
  (index)` shows its ways). `__shot_history__` holds (label, paths,
  bold, hands, balls before) per shot, kept at `_ended` (`_keepHistory`,
  `_trailsOf`), emptied by `newGame`/`setMode` (so `setKind` too); a
  sandbox mulligan drops the shot it takes back. Test
  `run_minimap_menu`. DECLUTTER (user, 2026-11-11: "The GUI is
  already too cluttered"): the panel's point struck, 'Centre' and power
  are HIDDEN in the normal view (`setControlsLive` now shows/hides
  them, `places` collapses), shown only with the full map; the panel no
  longer paints the heading, the score or the call (`heading`,
  `scoreRows`, `callWords` stay as data; its old painted scoreboard,
  `boardHeight`, the board fonts are gone): they are on the CLUB BOARD
  (user: "make it diegetic"; design page
  https://claude.ai/artifact/SSDzmmcnig4xygLQF7HGcC): `ClubBoard.qml`, a
  1200 x 540 face (wood ebony/oak, smoked glass, segment digits drawn
  in Canvas counting up, INN/AVG/HR or SER/AVG/BEST, run beads tiered
  green/amber/red, bar to the distance, centre title/inning or series/
  shot clock or PINS DUE pips/MATCH BALL or FINAL SERIES lamp, a 5x7
  dot-matrix line typed on and scrolled, rainbow for 'best') shown as a
  live `Texture.sourceItem` on boards on BOTH END WALLS over EACH table
  (placement A, my default; the user did not answer the four design
  questions, then asked for the room). `BilliardsWindow.boards()` ->
  (live, idle) dicts (`_gameBoard` from the match, `_idleBoard` 'FREE
  TABLE', sandbox 'SANDBOX'), `_pushBoards` from `refresh` and
  `_announce` (the line = the call's words, tone point/foul/neutral) ->
  `TableView.setBoards` (QML `liveBoard`/`idleBoard`).
  THE ROOM (user: "When the game boots up, implement a trivially simple
  first person shooter with mouse and asdw controls ... walk over to the
  kegle table or to the 3-bande table. you have a cue in hand, like you
  would have a weapon ... near a table, let E open a gui opening a start
  menu"; then "Surely someone already made an open source minimal
  walking simulator": yes, Qt's own `WasdController` (QtQuick3D.
  Helpers; QtQuick3D.Physics' CharacterController is there too, not
  used); "view-bobbing ... Add the bobbing to the view of the cue").
  Qt-free `Room` (`_room.py`, `TABLES` carom x -2300, kegler +2300; walls
  5200 x 4600 half, floor 800 below the cloth = `CaromTable.bed`, eye
  1650, `kept` (out of walls and tables, `keep` 280), `gapTo`, `nearOf`
  (within 650 of the rails), `beside(kind)` (foot end, facing),
  `layout()` for QML `roomPlan`). carom.qml: the table geometry is now
  `component TableBody { kegle, pickableBed, pins, turns, shown }` (its
  own cloth/beige/diamond materials; `Ebony.oak`); the table PLAYED AT
  stays at the scene origin (`TableBody { kegle: root.kegler }`; all the
  old machinery unchanged) and `roomNode` is shifted round it
  (`roomShift` = -`activeX`): floor, plaster walls, the OTHER table
  (`otherX`, `kegle: !kegler`, pins standing at `pinSpots`, its own 3
  shadowless spot lights), the four boards, and the WALKER: a Node moved
  by `WasdController` (forwardSpeed 15 = 1.5 m/s, Shift x2.2, R/F off,
  look by DRAG, which needs no pointer grab: the user's session is
  Wayland, where apps cannot warp the pointer), kept at eye height and
  out of walls/tables by `walkerMoved` (`keptInRoom`, `nearOf`: the same
  sums as `Room`), pitch held in +-85; `walkerCamera` (fov 70) a child,
  BOBBING (`stride` mm walked, a dip of 22 mm twice a 1.4 m stride, a
  14 mm sway once, `bobWeight` easing in/out over 260 ms via
  `strolling`/`stillTimer`), the CUE in hand a child of the camera (cue
  lathe meshes) CARRIED UPRIGHT as in a club (user: "not like we are in
  the middle ages about to do jousting"): tip 170 mm above the eyes,
  260 right, 520 ahead, butt down, leaning a touch forward and in
  (euler 174, 0, 7), bobbing 0.6/0.8 more than the view. MOUSE-LOOK AND
  INVENTORY (user: "the cursor should disappear and instead orient our
  view. Then E opens our inventory, like in ... minecraft, and we can
  select our cue and later other stuff. when we approach a table ... E
  to open the new game menu"): `TableView.setLooking(on)` hides the
  pointer (BlankCursor), tracks the mouse, turns the walker's head by
  each move (`lookBy` -> QML `lookBy`, 0.15 deg/px; the WasdController's
  drag-look is off) and puts the pointer back in the middle once it
  strays a quarter of the view (`_recentre`, `QCursor.setPos`). The
  move that re-centring makes is known by WHERE IT LANDS, in screen
  coordinates (`__look_pending__`), and skipped: the first version
  trusted `QCursor.pos()` right after `setPos`, which on the user's
  Wayland still gave the old place, so each re-centring was counted as
  a look and turned the head straight back (user: "it just moves a tiny
  bit before getting forced back"). Re-centring works there; if a
  system refuses it, `__look_warps__` stays False, the hidden pointer is
  followed as it is and `turnAtEdge` (window tick) keeps turning while it
  rests in the outer 6 % either side, up to 900 px/s. No open-source
  walking controller does better in Qt: Qt has no pointer lock
  (QTBUG-86780; the C++ qcursorconstraints and KDE Connect's Wayland
  pointer locker exist, without Python bindings); a click takes the mouse
  back, Esc (`escapeAsked`) or leaving the window lets it go. E
  (`useAsked`) walking: near a table its new game menu (the mouse let
  go while it is up, `_menuHidden` takes it back), else the INVENTORY
  (QML overlay: a 9 x 3 grid and the hotbar, `Slot` items drawn in
  Canvas, the hotbar along the bottom while walking; `inventoryItems()`
  = the cue for now, `chooseItem` takes it in hand or puts it away,
  `heldItem()`, the cue in hand drawn only while held; E or Esc closes
  it). `setInventory(items, held, shown)` pushes it.
  View3D camera: `walking ? walkerCamera : overhead ? overheadCamera :
  camera`; while walking the orbit controller, taps, strokes, the
  corner, the counter, the ghost diamonds and the camera dot are off; a
  dot and 'W A S D ...' over the view, 'E · play kegler' near a table.
  Window: `walking`, `room`, `useKey` (E): `useAsked` -> near a table
  `startMenu(kind)` (its name, 'Play a game', 'Sandbox', 'Walk on'),
  at the table `tableMenu()` ('Back to the table', 'New game', 'Leave
  the table'), QMenus popped at the view's middle (`_useMenu`);
  `startWalking` (strokes and shots stopped, aiming keys off via
  `_setPlayKeys`, bar/panel/maps hidden by `_layoutViews`), `sitDown(
  kind, mode)` (setKind + setMode), `standUp` (walks from `beside`);
  `_sceneLoaded` applies walking. `python -m worQt.gaming.billiards` and
  main.py's billiardsApp boot walking; a bare `BilliardsWindow()` (the
  tests) still opens at the three-cushion table. Checked offscreen (the
  scene compiles and creates; walk, near, menus, sit, stand); rendering
  unseen. Tests `test_room`, `run_walking`. Both breaks still hold (first break scores at
  1.2 R; Korean routes within tolerance). The unfolded map's roll
  estimates were fitted to the old cushions, not refitted. `arcOf`/
  `rayOf(..., budget)`, `fanOf(..., left)` (ball met: left x cos^2; cue
  ball: left x |(5/7)t + (2/7)share d|^2); a ring where the arc stops.
  A drag on either map turns the aim FROM PRESS TO RELEASE (user: the
  press must not make the aim jump): `grabAt` keeps the pointer's and
  the aim's angles about the cue ball, `dragTo` emits `aimDragged(aimX,
  aimY)` = the aim as pressed turned by as much as the pointer has
  turned since (pressed on the aim line and dragged onto any image of a
  ball, it aims at that image), release lets go -> `aimFromMap` ->
  `view.faceCamera` (resting, looking from the cue ball). WATCHED FROM
  ABOVE (user: "use overhead view instead of the cinematic thing"; the
  follow camera is gone): the panel's Shoot (`shootAlongCamera`) takes
  the shot as set up then (aim, speed, top, side) into
  `__shot_pending__`, turns to Top view (`_watchFromAbove`, the view
  before kept in `__overhead_before__`) and strikes
  `__overhead_wait__` 1 s later from `tick` (`_strikePending` ->
  `_strike`); meanwhile `resting()` is False (aim hidden, Shoot
  greyed); setting white's lag shot strikes at once; `shoot(aimX,
  aimY)` strikes at once (tests), still from above; `finish` strikes a
  pending shot first; `_stopPlaying` (New game, Reset, mode, Mulligan)
  drops it. At the press the last shot's trails go and the hand lies
  behind the cue ball along the way it will leave (`_struckBalls`, the
  balls as the setting strikes them, both in a lag; `_showHands` =
  `setTrails({}, bold, hands)`), kept through `_play` till the shot's
  own trails come. `_started` (shot or replay) -> `_watchFromAbove`;
  `_ended`/`_stopPlaying` -> `_backFromAbove` (the view before, unless
  the player toggled Top view meanwhile: `toggleOverhead` clears
  `__overhead_before__`). `_layoutViews`: the full map gives way to the
  table while a shot is shown or pending. Counter over the view (QML
  `counterText`/`counterShown`, `TableView.setCounter`): `_counterWords`
  = the cue ball's cushions up to the second ball it meets, balls ticked,
  '— Point!'/'— No point' once called; none for a lag; cleared with the
  trails. Sounds: `pusher.SoundPlayer.start(folder, bank)` now takes a
  bank 'module:function' (importlib), the pusher's by default; billiards
  `_sounds` (Qt-free: clack resin click ~3 kHz, thud ~130 Hz rubber,
  tock leather ~1 kHz, fanfare C-E-G-C brass + chord; `takes()`);
  `gui.BilliardsSounds` (tock on the stroke by speed, `between(recording,
  start, end)` clacks/thuds as playback passes touches, louder the
  faster, 4 at most a frame; fanfare when a point is called), toolbar
  'Sound' (`soundBox`). My sandbox has no audio device ('a sound would
  not load'); `previews/billiards-sounds/*.wav` to listen.
  SKIP LAG (user): 'Skip lag' (`ShotPanel.skipButton`, `skipAsked`,
  `setSkipAvailable`) right of '▸▸ Fast', shown only while a game is at
  its lag (`_showGame`); `BilliardsWindow.skipLag(ball=None)`: a coin
  (`random.choice`) or 'ball' wins, `match.lagged(winner).chosen(True)`,
  the winner breaks playing white from the spot chosen, the camera
  facing the foot, 'Lag skipped: ... breaks, a coin decided.'; Shoot
  narrows (to 'room') to fit the row.
  FAST AND SCOREBOARD (user): '▸▸ Fast' (`ShotPanel.fastButton`)
  beside 'Shoot' speeds the shot under way ONLY WHILE HELD DOWN (user):
  `fast` = the button `pressed` and enabled; `setFastAvailable` greys it
  out between shots (let go; `_started` on, `_ended`/`_stopPlaying` off);
  `BilliardsWindow.playRate()` = `__fast_rate__` 5 else 1, the tick
  advancing that many times as far; on each change of (playing and
  fast) the tick calls `BilliardsSounds.fastForward`: 'windUp' then
  'whirr' looped (`SoundPlayer.loop`/`stop`, new messages; the whirr's
  0.5 s has every tone a whole number of turns, seamless), 'windDown'
  when let go. The score is a painted
  scoreboard (`_paintScore` -> `_paintBoard` in `painter.save/restore`,
  `_paintBoardRow`, `boardHeight`): a dark gold-rimmed board, PLAYER /
  POINTS labels, a row each player: ball disc, name, 'Inn Avg HR' small,
  points in large mono figures, the player at the table lit with a gold
  bar and 'Run n'; `scoreRows` items now (playing, 'name, ball', points,
  innings, average, best, ball, run). `previews/scoreboard.png`.
  Trails: a new shot clears them at once
  (`clearTrails` empties `trailNames`, `trailStarts`, `hands`); QML
  draws a ball's ribbon only while it is in `trailNames` (balls with a
  way in the shot shown), as a ribbon handed no triangles may keep
  showing its old ones.
  `previews/shoot_unfolded.py` paints it offscreen to
  `previews/unfolded-*.png`.

  KEGLEBILLARD (user, 2026-11-10: "Dansk Keglebillard!!", a SECOND
  game beside three-cushion, not a replacement; NOT Skomager, "a game
  for drunks"), as Den Danske Billard Union's official rules have it
  (ddbu.dk = dendanskebillardunion.dk; previews/rules/DDBU-*: the
  keglebillard rules revised June 2026, the material rules 2026-27,
  bilag G/H drawings; memory 'reference-ddbu-keglebillard'). STEP 1,
  the rules, Qt-free: `KegleTable(table, pocket 80, pinApart 82,
  pinHeight 120, pinFoot 14, pinMass 10.5, salvo 710)`: the carom match
  table, six 80 mm pockets (corners and long-cushion middles; HOLES
  MILLED INTO A CAROM TABLE, user: "a carambole table and some sort of
  drill": the milled edge 29 mm in front of the nose line, so the
  cushion stays, notched by the hole; no pool jaws), five
  wooden pins alike in a cross in the middle (`pinSpots`, middle first,
  82 mm apart, 68 mm between the feet: a ball passes with ~3 mm a
  side), layout spots at L/4 and 3L/4 on the middle line (`spots`), the
  baulk line 710 from the bottom cushion = the head (`salvoLine`, an
  ASSUMPTION: not dimensioned), `inHand(x, y)` (within L/4 of either
  short cushion, the middle past the quarter line), `farHalf`,
  `opening(redX, redY)` (white on the head spot, the marked white
  'yellow' on the foot spot, red in hand AS IF IT HAD JUST BEEN POTTED,
  user 2026-11-11: either end, though DDBU's 3.1 says behind the baulk
  line; by default at the head end), `respotted`/`spotTaken`
  (9.1, 9.3). `KegleShot(touches, fallen, inHand, firstAt)` (touches
  incl. 'pocket'/'off'; fallen = (pin, credited ball), credited as 8.1:
  the first ball to hit it, through pins, red when at once);
  `Streak(cushionDue, reds)`; `KegleReferee.call(shot, streak)` ->
  `KegleCall(points, foul, rule, words, red, pins, streak)`: 2 a white's
  pin, 4 red (both whites), max 14; fouls score 0 (an ASSUMPTION, the
  rules only pass the turn): off (11), red pocketed (5.7), a pin
  credited to red (5.8), from in hand red not first on the far half
  (3.2), pins twice running without a cushion, red alone counting as
  one (5.11), red a third time running without pins (5.12; user: "every
  third shot must get pin points"). `KegleMatch(names, distance)`
  (`DISTANCES` 200-800 in 100s, user): lag -> choose (lay out or let
  the other) -> play; series on while scoring; red pocketed -> the other
  in hand; off -> new layout; as many series each (7.4): the starter
  reaching it, the other plays a `final` series from a new layout, draw
  if he reaches it too (7.6). Tests `test_kegle_table/referee/match`,
  in main.py's `KEGLE_TESTS`. USER 2026-11-11: the lag is exactly as
  in carom (`KegleReferee.lagCall` = `Referee.lagCall`: pins, balls,
  pockets, long cushions are faults); pins oak, sounding as a
  xylophone when knocked over (`_sounds.pin(pitch, seed)`, `PIN_NOTES`
  C6 D6 E6 G6 A6, one a pin; 'pin' in `takes()`;
  previews/billiards-sounds/pin.wav); pins ALWAYS on their spots as a
  shot begins; a standing pin counts as down unless its foot lies
  wholly inside its ring (`KegleTable.pinStands`, `ring` 18 mm across,
  an ASSUMPTION); a pin is set up only clear of every ball, air between
  (`pinsPlaced`, `pinBody` 20 mm; 8.3); red pocketed -> the other puts
  it within L/4 of EITHER short cushion (`inHandEnd` 1 head / -1 foot;
  so the baulk line at L/4 = 710 is confirmed), and from hand (opening
  too) red must cross the middle line between the middle pockets before
  it strikes a white, unless that white lies on the line or past it
  (`KegleShot.redFrom`, `firstWhite` = (crossed, white's y); foul
  '9.4'; replaced the 'firstAt' far-half check). `KeglePin(mass 10.5,
  profile)` (`_kegle_pin.py`, Qt-free): the pin as a solid of
  revolution, `PROFILE` (height, radius) read off DDBU's bilag H drawing
  (its shape and heights; widths set to the written 14/20/8/13: the
  drawing is schematic), `radiusAt`, `height`, `foot`, `centre` 45.1 mm,
  `inertia` (359, 10571 g mm2), `tipping` 8.8 deg, `spheres` (the
  largest inside each outline point, for contacts). The body is widest
  at a ball's middle: a ball clears two pins by 0.35 mm a side (user:
  a ball may roll between two pins rightly set up). The user's photo
  previews/kegler.jpg: pale natural wood with grain, three dark turned
  grooves round the waist below the neck (render so). Pin calibration
  targets (user; memory 'reference-ddbu-keglebillard'): passing
  between possible; a single pin common; two outer pins hit by the
  white common; centre + one -> one or two more by falling pins common;
  three hit by the ball rarely a fourth; all five from one pass
  extremely rare. KEGLER LOOK (user: "put the kegler into main.py",
  "more of a cyan color than the bluer carambole table"):
  `BilliardsWindow.showKegler()` (sandbox, `__kegle_look__`: Reset lays
  `KegleTable.opening()`, red the cue ball, `ShotPanel.__ball_colors__`
  knows red) -> `TableView.setKegler` -> QML `kegler`: cloth #12b3bf
  (carom #1593d2), `clothBounce` #3fd2dc, the frame OAK (the `Ebony`
  material's tones #b8844f/#6b4526 while `kegler`), six holes as dark discs
  (`KegleTable.holes()`: 80 mm, centre 11 mm behind the noses so the
  edge reaches `holeIn` 29 mm in front; corners at (-11, -11)...), the
  pins at `pinPlaces` from `latheMesh(PROFILE, 32)` (`shapes.pin`,
  `_table_shapes.latheMesh(profile, segments)`: a solid of revolution,
  smooth, flat foot down), pale wood #dcbf92, three dark grooves at 64,
  66.5, 69 mm (`pinGrooves`). main.py `kegleApp`. A LOOK ONLY: the pins
  do not yet stop a ball, nor the holes take one; the cushions are not
  yet notched. Tests `run_kegler_look`, `test_table_shapes.test_lathe`,
  `test_kegle_table` holes. PINS, STEP A (user: "pins first, let's
  go"): `PinField(table, numbers, shape, contacts)` (`_kegle_pins.py`,
  Qt-free, plain Python): each `Pin` a rigid body (centre of mass `p`,
  `v`, quaternion `q` scalar first from the pin's axes, foot at nought,
  axis z, to the table's; spin `w`; `awake`; `credit` = the ball that
  first set it going, `mover` = the one pushing it last, passed on
  through pins, red when red and a white at once: 8.1, 5.8). Gravity;
  the cloth meets the foot's edge (8 points) and, once leaning past
  ~66 deg, the surface spheres: stiff dead springs `cloth` 1.25e8 /
  `clothDamping` 3.5e4 a point, friction capped at half the slip a step
  (else the foot's points jitter); rolling resistance as on a ball,
  the felt pushing back `rolling` 0.3 mm ahead (torque `rolling` x
  the cloth's push against the turning across the cloth, never
  reversing it; was a 3/s decay of the spin, which the friction fed
  back: knocked pins rolled like logs for 6 s);
  balls and pins meet the spheres as springs lasting `ballTime`/
  `pinTime` 0.4 ms (`_spring`, as `Carom`), lively 0.7/0.6, friction
  0.2/0.3; cushions as walls. Steps (`stepFor`): nothing near a pin
  closes more than `closeBy` 0.1 mm a step, between `fine` 2e-5 and
  `coarse` 1e-4; pins prune each other as capsules (axis segments
  fattened by the widest, `_segments`). A pin sleeps once still (8
  mm/s) 0.05 s, upright < 2 deg or lying > 80 deg, never caught
  leaning. `stands` (upright < 3 deg, foot in its ring), `fallen()` ->
  `KegleShot.fallen`; `rows(names)`/`setRows` as a sample holds them
  (`PIN_STATE` 10: number, p, q, awake, credit index). Checked: a pin stands
  and sleeps; tipped 6 deg rocks back, 12 falls; a ball knocks a pin,
  keeping ~80 % of its speed; a centred ball passes between two; a
  chain credits the ball (`test_kegle_pins`). FAST (user: "it's 2026,
  these are some fucking pins"): compiled in Warp (float64, every
  number a named constant: Warp keeps float64 and float32 apart, and a
  name keeps one type through a kernel); the plain Python stays as
  `playedSlowly`/`step`, the reference (`test_kernel_agrees`: same
  pins felled, same credits); 100-300x faster. COMBINED KERNEL, PART 1 (user: "combined
  kernel next, let's go!"): `Hits.run` steps through hits in Warp,
  `_hits_kernels.hitsRun` (one thread, float64, named constants), a
  line-for-line port of `_touchesAmong`, `_cushionPush`, `_ballPush`,
  `_slate`, `turned`; Python keeps the sleepers (exact `cloth.advanced`)
  and steps itself when a ball awake is free (the kernel hands back at
  once); the kernel decides every step itself and keeps time as `Hits`
  does (`now = now + step`, absolute `wake`), so a run cut anywhere goes
  on the same: recordings at 250 and 1000 Hz still equal `played` to
  the last digit (12/12). `Hits(motion, balls, compiled)`; the plain
  Python stays the reference (`test_carom.test_compiled_agrees`:
  bit-identical on a cushion hit and a ball meeting). Contacts now
  ~13 % of a shot; the rest is the Recorder's glide sampling
  (`cloth.moved` per sample, turning the dots): next to speed up
  (closed form where the spin's axis is fixed). STEP B, BALLS AND PINS
  TOGETHER (2026-11-11): `hitsRun`'s pieces are Warp functions
  (`contactsOf`, `loggedOf`, `cushionsPushed`, `pairPushed`, `slated`,
  `turned`; carom still bit-identical), shared by
  `_kegle_kernels.kegleRun` with the pins' (`ballsOnPin`, `pinsOnPin`,
  `pinOnCloth`, `ballOnCloth`, `zoneOf`; `pinsRun` and the stand-in
  `PinField.played` are gone). `KegleMotion(table, motion, shape,
  contacts)` (`_kegle_motion.py`, Qt-free): on the cloth exactly as
  `Motion` (`glided` also ends as a moving ball comes into a pin's zone,
  `zonesOf`: round the middle of its axis seen from above, half its
  length so, R + widest + `ZONE` 1 mm; `_zoneTime` a quartic); `busy`
  (a cushion or ball contact, a pin awake, a ball moving in a zone) ->
  `KegleHits(motion, balls, field)`: EVERY ball and pin stepped together
  in one launch till clear (balls through a hit on the slate as
  `hitsRun`, else explicitly on the cloth, a hair off exact, and no
  roll-back at a roll's end; steps the finest of carom 1e-6 / cushion
  1e-5 / the pins' closing step), arrays kept between runs, time
  absolute, so a run cut anywhere goes on the same; the field's pins
  written back after each run. Contacts logged as `Motion` logs them,
  plus `Touch('pin', ball, str(number))`, a touch going on till the ball
  is `ZONE` clear of the pin's capsule (a ball shoving a pin chatters).
  `played(balls, field, seconds)`, `fieldOf(numbers)`, `resting`.
  `KegleRecorder(motion, rate, size, longest, numbers)`: as `Recorder`,
  the pins `numbers` set up on their spots at each shot's start
  (`KegleTable.pinsPlaced`), `Stretch.pins` / `Recording.pinParts`
  (samples x pins x `PIN_STATE`), `Recording.pinsAt(s)` (blended) /
  `lastPins`, `fallenOf(recording)`. Checked (`test_kegle_motion`): a
  shot far from the pins equals `Motion.played` exactly; recordings at
  250 and 1000 Hz equal to the last digit, and equal `played`; red
  struck through the cross at 3.5 m/s fells all five (four red's: foul
  5.8), a 9.4 s shot recorded in 0.77 s at 1 kHz. FALLEN PINS STAY ON
  THE CLOTH (user: "Pins *must* be allowed to remain on the table
  slowing the balls"): they lie where they fall, asleep, till the next
  shot sets them up; a ball meeting one is slowed and shoves it. NOT YET:
  a ball riding up over a lying pin (no lift: the pin's push up on a
  ball is dropped, the slate takes it). A glancing ball spins a pin
  about its axis (I 359 g mm²) to ~100 rad/s: it tops, falls, hops and
  rolls off like a log; how far is step C's. IN THE WINDOW (kegler
  look, sandbox): `BilliardsWindow.recorderFor(balls, rate)` is a
  `KegleRecorder` (pins `pinsPlaced(balls)`) for the worker, the
  previewers and `_playedHere`; `advance` shows `recording.pinsAt(t)`
  through `TableView.setPins(rows)` (QML `pinPlaces` = each pin's foot,
  `pinTurns`, `pinShown`, a Repeater3D of 5; `None` = all standing);
  `_raisePins` sets them up at Shoot's press (and Reset, mulligan, a
  ball let go), fallen ones lying till then; the sandbox calls each shot
  with `KegleReferee` (`_kegleCall`: touches, `fallenOf`, Streak()), the
  counter 'Pins down n   White ✓ ...' (`_kegleCounterWords`), a
  fanfare when it scores; Game mode leaves the kegler look (the game is
  three-cushion's still). Sounds: 'pin0'..'pin4' (one note each,
  `PIN_NOTES`), played for a ball's touch on that pin and as a pin
  falls past 75 deg (`__landed_up__`). STEP C BEGUN (2026-11-11):
  `previews/kegle/calibrate_pins.py` (white passes through the cross,
  random way, offset, speed; 'first' = pins the ball hit before anything
  moved them), `pin_targets.py` (the user's six), `sweep_pins.py`
  (grids, 6 processes). Measured against the targets, pins knock their
  neighbours far too often: three hit -> a fourth 52-72 %, all five
  2-6 %, one hit -> only that pin ~45-60 %, whatever the restitutions,
  ball/pin/cloth friction or the felt's rolling resistance (56 sets;
  pin-pin friction is not modelled, so `pinFriction` does nothing).
  Mechanism (Python reference agrees with the kernel): struck at the
  ball's middle, 31 mm, 14 mm below its centre of mass, a pin has its
  foot kicked out, its head (the centre of percussion) staying near the
  spot, so it falls within 120 mm of the spot, neighbours 82 mm (116
  diagonal) away; a cut pin flies along the line of centres, in the
  cross often straight at a neighbour; a standing pin topples from ~0.3
  m/s at its head. ASKED THE USER how real pins fall: "if you hit the
  pin head on at high speed, it will be yeeted off the table" (poor
  form in a club). So the cushions and rails are now BLOCKS `top` 45 mm
  high reaching `cushion` + `rail` 180 mm past the noses (not walls of
  no height): a pin meets their faces, tops and edges, may fly over
  them, and past the rails is OFF the table (`Pin.off`, kernel `awake`
  2, `PIN_STATE` awake 2.0): on the floor below, lying, out of play,
  down (`stands` False), no zone, met by nothing. Square on at 4 and 6
  m/s a pin now leaves the table (`test_yeeted`). The cascade numbers
  did not change (the extras fall in the first few hundredths of a
  second, by the cross). KEGLER GAME LOOP (user: "a separate game loop
  for kegler as for 3 bande"): Qt-free `KegleGame(table, match)`
  (`_kegle_game.py`, immutable): `begun`, `withDistance`/`nextDistance`
  (200..800), `lagBalls` (three-cushion's `lagPosition`, the user: the
  lag exactly as in carom), `lagged`, `chosen` (lays out or lets the
  other), `layoutBalls` (`KegleTable.opening`), `redPlaced(balls, x, y)`
  (in hand: within L/4 of either short cushion, clear of the whites;
  else None), `shotOf(recording, recorder, inHand)` (touches,
  `fallenOf`, redFrom, `firstWhite` = (red crossed the middle line
  before it first struck a white, the white's y), from the samples),
  `called` (as the series stands, `match.streak`), `judged(call, balls)`
  -> (game, balls): layout after 11 / the last series, red in hand at
  the head end after 5.7, else as they lie. The window: `setKind('carom'
  | 'kegler')` (toolbar 'Three-cushion' / 'Kegler', `showKind`;
  `isKegler`, `kegleGame`; `match()` returns the kegle match when
  kegler, the two matches sharing phase/cueBall/lagged/chosen/judged/
  names/scores...), `_showKegleGame` (heading 'Kegler to 400',
  scoreboard rows by series, choices 'distance' ('To 400' cycling,
  `nextDistance`) at the lag, 'choose' worded 'Lay out' / 'Let the
  other lay out' (`setChooseWords`), 'red' ('Place red',
  `togglePlaceRed`: a drag moves red only, `redPlaced` refusing outside
  the quarters) while red is in hand), `_verdict` -> `KegleGame.called`,
  `_judgeKegle`, the lag as three-cushion's (`Referee(Rules())`
  `lagCall`); THE PINS RESPAWN as soon as a shot's balls rest (user: "the
  pins are supposed to respawn before each shot"; `_ended` ->
  `_raisePins`), and at Shoot. `showKegler` = sandbox + `setKind
  ('kegler')`; main.py `kegleApp` opens a kegler game at its lag. Tests
  `test_kegle_game`, `run_kegler_game`. POCKETS SEEN (user: "the cushions have cutouts above the pockets
  and behind them is black leather"): `_table_shapes.kegleMeshes(kegle)`
  -> 'cushionLongNotched' / 'cushionShortNotched' (`notchedPrism`: the
  cushion profile cut by each pocket's circle at every height, the
  profile densified to 2 mm; long ones at both ends and the middle,
  short ones at both ends; 77 mm wide at the nose, 18 at the back) and
  'pocketLeather' (`pocketLeather`: a wall round each pocket 0.3 mm
  inside its cut, behind the noses, cloth to cushion top, in scene
  axes), shown while `kegler` (QML, leather two-sided, #0c0b0a). The
  holes still take no ball. `previews/shoot_billiards.py` shoots the
  kegler table and the pockets close up. The user then: "the pocket
  cutouts in the cushions are straight. Consult imagery" (Wikimedia's
  Marienborg billiard room, a keglebillard table: square slots, black
  leather behind): `notchedPrism(profile, pieces, smooth)` cuts square;
  `pocketLeather` is flat panels on the slots' backs (one a middle
  pocket, two a corner). Sounds (user): pins muffled, hard light wood
  (`_sounds._bar`); red's pins SAD ('sadPin0..4': four notes falling a
  semitone from `SAD_NOTES`, the last held; 'sadLand0..4' as a pin
  credited to red falls); red meeting its second white HAPPY ('carom',
  C6 E6 G6 C7 up; `_billiards_sounds._madeRed`).
  POCKETS IN THE ENGINE (user: "the holes? right now they are just
  decorative"): `Motion.pockets` (`Pockets(corner, half, holes,
  radius)`, None for three-cushion: all unchanged, bit-identical):
  `contactSides(x, y)` = the four noses but where `isOpen` (over a
  slot), plus the slots' JAWS (`jawsOf`, 12 points on the noses' line
  at the slots' ends, each pushing as a nose does, along the line from
  it to the ball); `touching`, `cushionsTouched`, `_given`, `energyOf`
  use it; `hitTime` also finds a ball reaching a jaw (`_pointTime`,
  quartic). `KegleTable.pockets()`: middles' slots the hole's chord at
  the noses (77 mm), CORNERS cut back so the mouth between the jaws is
  `mouth` 1.1 balls wide (ASSUMPTION: cut back only to the hole's
  chord, 27.5 mm, the 39 mm mouth took no ball); `parkedAt(hole)` /
  `pocketOf(ball)`: a ball gone in is PARKED far off the table
  (`PARKED` -20000, `PARKED_APART`; `_carom_table.isParked`), where
  nothing meets it, so Ball needs no flag; `HOLE_NAMES`. `KegleMotion.
  engine()` (Motion with pockets), `glided` also ends as a ball comes
  over a hole, `captured(balls)` parks it, `Touch('pocket', ball,
  hole)`; the kernel: `_hits_kernels.sidePushed` (one nose; cushions
  split into it, still bit-identical), `_kegle_kernels.PocketRules`,
  `isOpen`, `kegleContactsOf`, `kegleCushionsPushed` (jaws too), each
  step parks a ball over a hole (event kind 3). Replays don't fly it off
  (`_blended` holds), trails and unfolded ways stop at the pocket, the
  view sinks it in its hole (`TableView.__sunk_depth__` 45 mm).
  `KegleGame.unparked`: a white back on the spot opposite the other
  (9.1), red in hand at the layout's place (5.7, 9.4); the sandbox puts
  them back too. Rates and `played` still agree with pockets. BALLS
  (user): three-cushion's dots BLACK and larger (QML `dotRadius` 3.75,
  `dotBlack`); in kegler both object balls WHITE, the marked one
  ('yellow' inside) with the black dots as its mark, the white plain,
  red with black dots; the marked white's trail and halo pale grey
  (`markedTint`), `TableView.bodyOf`, `ShotPanel.colourOf`/`setKegler`
  ('Marked'), `UnfoldedMap.setKegler`; lag words say 'the marked
  white'. THE STROKE IS A SPRING (user, 2026-11-11: the mouse's speed
  pushed through the press point was "too difficult to control. It's
  not fun", too small a dynamic range): QML `PointHandler` (right
  button only; the camera keeps the left) ->
  `strokePressed/Moved/Released` (view pixels) ->
  `BilliardsWindow.pullPressed/pullMoved/pullReleased`: pulled back
  (y down) `__pull_least__` 20 px it arms (hand shown from above);
  `springSpeed(back)` = the slider's low + (high - low) share², share
  = (back - least) / (`__pull_reach__` 400 - least) clamped (soft shots
  get most of the way); the cue drawn back `STROKE_MOST` x share; let
  go -> `strikeAt(springSpeed)`: the power slider set, struck at once
  (no overhead wait; the cue follows through); let go short of the
  least (pushed back to the press), nothing. A left click (the view's
  `mousePressEvent` takes a left press while the right is held, kept
  from the scene, `strokeCancelled`) or Escape (`cancelKey`, enabled
  only during a stroke) calls it off: `cancelStroke`. The point struck
  is centred as a shot's balls rest (`_ended`), and for yellow's lag
  shot once white's is set (user: each shot starts neutral). Not while
  marking. Test `run_stroke`. The CUE IS DRAWN in the 3D
  view during the stroke (user: "a visual indication as to when it
  reaches the ball"): `TableView.setStick(ball, aim, back, top, side)` /
  `hideStick` (QML `stickShown/Place/Turn`; `_table_shapes.CUE_TIP/
  FERRULE/SHAFT/BUTT` lathe meshes 1450 mm), its tip on the point
  struck, `__stick_rise__` 3 deg up, 'back' mm short of the ball = the
  pull (0.5 mm a px): it touches the ball as the mouse crosses the line.
  THE SHADOW (user: aiming as at a real table, "if ball 1 shadowed some
  part of ball 2, i knew i would hit it", "both eyes open"): the eyes
  are ~65 mm apart, about a ball's width, so ball 1 hides from BOTH eyes
  only the strip a ball wide it sweeps: whatever that strip touches is
  hit, at any distance (one eye or a camera far behind gives no such
  rule: from 1.9 m back two images overlap with ball 2 up to ~2.8 R off
  the line); QML `shadowBand`, a dark band 2R wide on the cloth from the
  ball aimed from to where it would reach the cushion, with the aim;
  toolbar 'Shadow' (`shadowBox`, `setShadowShown`). TRENCHES (user, 2026-11-11: "have it
  indicate whereabouts the ball 1 will stop ... add such a trench on
  ball 2 as well"): while aimed from the cue ball the band is replaced
  by Qt-free `Trenches(table, cloth, cue).trenchesOf(balls, cue, aimX,
  aimY, speed, top, side)` -> `Trench(name, x, y, dx, dy, length, end,
  met)`: ball 1 straight along the aim (`Cue.sent`, then `Cloth`'s
  phases exactly, `_phasesOf` cached per speed/top/side: the same along
  any aim) to the first of: the cushion's touch (middle `sqrt(R² -
  (nose - R)²)` in from the nose line), a ball met (`end` 'ball', `met`),
  or its rest ('stop', roll-back left out); meeting a ball, ball 2 sets
  off along the line of middles at ball 1's speed there along it,
  sliding without spin (frictionless equal balls; no throw), to the
  same ends; ball 1 goes on from the hit with its speed across the line
  and ALL its spin (user: "post collision show for both ball 1 and ball
  2"), its way curving as `Cloth` slides it (`_wayOf`, 48 places a
  slide), so a rolling half-ball hit ends ~33 deg off the aim (the 30
  degree rule) and a full rolling hit follows on. `Trench(name, points,
  end, met)` (`startPlace`, `endPlace`, `distance`); `_trenchOf` cuts a
  way at the first cushion line or ball (exact on each segment). ~0.26
  ms a call. `trenchMesh(points, half, lift)`: `ribbonMesh` ending in
  half the ball's outline. Window `_showTrenches` each tick (the
  spring's speed while a stroke is pulled back) ->
  `TableView.setTrenches`/`clearTrenches` (QML `trenchesShown`,
  `trenchNames` (each trench tinted by QML `trenchTints` and
  `trenchOpacities`: white #ffffff 0.85, marked 0.7, red lightened
  #ff5c5c 0.4; user: white too faint at 0.3 and 0.55, red too dark at
  0.3, right at 0.4),
  `trenchShapes` trench0..2; the old band shows when
  looking from another ball or the ghost). Where ball 1 meets ball 2, a
  clear copy of ball 1 (user; QML `impactPlace`/`impactShown`/
  `impactColor`, opacity 0.35 as the mark; shown with the trenches,
  even without the shadow, and from above). Not yet: pins and pockets
  in kegler, the cushions after. EARLY SET-UP (user, 2026-11-11: "Allow setup of
  next shot to begin when the red ball stops moving, even if it still
  rotating and even if the other balls are still moving, BUT show ...
  a barrier block"; both games): `advance` -> `_setUpEarly(recording)`:
  once the worker's recording is over and, as shown, the NEXT shot's
  cue ball lies where it stays (`_stillFrom`: after its last sample
  more than `_STILL_WITHIN` 0.01 mm off its rest; spinning in place is
  fine), the shot is judged at once WITHOUT laying the balls
  (`_judge(False)`: match kept, call announced with its fanfare via
  `_announce` if not yet shown, `refresh`), the view comes back from
  above / whole (`_backFromAbove`, `_backFromWhole`), the point struck
  centred, and `__early_setup__` makes `settingUp()` True while the
  others roll on: `_aim`, panel.ready, `_showTrenches`, the stroke's
  press (`_aimable`) use it; striking still needs `resting()`
  (`_strikes`). `_nextCue(call, last)` decides the ball: kegler game
  `KegleGame.judged` (none if layout, red in hand, phase not 'play', or
  the balls not as they lie: a white pocketed is respotted); three-
  cushion game `Match.judged(call).cueBall()` (none on respot or a new
  opening); sandbox the panel's; never after a lag or for a parked
  ball. A stroke begun too soon -> `TableView.flashBarrier` (QML
  `flashBarrier()`: a clear block barred by a red prohibition sign over
  the ball aimed from, 1.2 s, `barrierCount`), nothing pulled back.
  `_ended` then only lays the last balls, refreshes, raises the pins.
  The shot clock starts only once all rest. Test `run_early_setup`.
  KEGLER POCKET SOUNDS (user): `_sounds.pocket` (a dull low knock on the
  leather and three fainter bumps, neutral) for a white,
  `sadPocket` (the drop, then a muted brass falling a semitone thrice
  from B flat 3, the last held wavering) for red; `between` plays them
  on `Touch('pocket', ...)`; previews/billiards-sounds/pocket.wav,
  pocket-sad.wav. STROKES ONLY (user, 2026-11-11: "make right-button
  drag drop be the only way to make shots"): 'Shoot' and its overhead
  wait are GONE (`shootAlongCamera`, `__shot_pending__`/`__shot_due__`,
  `_strikePending`, `shootText`, `shootAsked`); `ShotPanel.markButton`
  'Mark' shows only while marking (`_showMark`), '▸▸ Fast' after it;
  `__overhead_wait__` is now `__stroke_lead__` (the hand's cue
  animation, `_beginStroke`); `shoot(aimX, aimY)` stays for tests (seen
  from above). `pullPressed` while `_strikes()` is False (balls rolling,
  marking, moving balls, choosing) flashes the barrier and starts no
  stroke (user: "the barrier indication should appear when attempting to
  drag-back"). SPIN AND POWER (user: "variable sliders for spin and
  power in the full map. In the regular non-cheating view, they should
  be indicators. Output only."): `ShotPanel.setControlsLive(live)`,
  called by `_layoutViews` (live only while the full map shows): the
  picker and the power slider take no mouse, wheel or keys
  (WA_TransparentForMouseEvents, NoFocus), 'Centre' greyed (End still
  centres); `controlsLive()`; the power follows the pull live
  (`_showSpring`), put back if nothing is struck (`__pull_power__`). Kegler's red now
  defaults beside the white on the head string, a ball's width further
  out than three-cushion's spot 4 (user: "another Asger eye gap", 244
  mm from the head spot); in hand counts the quarter line itself (9.4:
  the field the
  cushion and the layout line bound). The engine's slight curve with
  follow/draw plus side (spin square to the stick, the ball squirting
  2.4 deg off it and `sent` making that up; ~1 cm a metre) is physics of
  the cue model and stays. A stroke shot is watched from where the
  player stands, not from above (user; `strikeAt` sets `__stay_down__`,
  `_started` skips `_watchFromAbove`); Shoot still goes above. The
  camera never looks down on the ball less than QML `lowestPitch` 10
  degrees (user: lower, the cue hides the ball): `turnBy` and the
  origin's `onEulerRotationChanged` clamp every turn, keys, drags and
  the window's alike. While the right button is held for a stroke, W A S
  D move the point struck (W up, S down, A left, D right; `_aimKey`)
  instead of the aim, the drawn cue following (user). After a stroke
  shot the camera takes in the WHOLE TABLE (user): `_watchWhole` ->
  `TableView.watchWhole` (focus the cloth's middle, `__watch_pitch__`
  40 deg down, the heading kept, `__watch_view__` 60 deg, distance
  fitting the table and rails), gliding 0.6 s (QML `glideCamera`,
  Behaviors on the turn, `camera.z`, the field of view while
  `cameraGliding`); `_backFromWhole` at the shot's end glides back to
  `cameraState()` as it was. A SPEEDOMETER (user) shows clear over the
  ball during the stroke: `springSpeed` of the pull ->
  `TableView.setGauge(speed, most)`
  / `hideGauge`; QML `speedometer` (a Canvas dial 0..`gaugeMost`, green
  to red, needle, 'n m/s', placed over the ball by `mapFrom3DScene`),
  gone as the shot strikes or the button is let go. SPIN IN PLACE (user:
  a ball not moving but spinning dies "no faster than 3 seconds"):
  `Cloth.spinningAt`/`spinningTime`, the 'spinning' phase only, depends
  on the spin alone (glide splits and samples cannot change it): steady
  at `spinDecay` down to the knee (decay x `spinTail` 1 s = 7.48 rad/s),
  then fading by e each `spinTail`, nought under `spinStop` 0.095 rad/s;
  2 rad/s lasts 3.05 s, 40 lasts 8.7 (was 5.3); the kegle kernel's
  `ballOnCloth` the same for a ball not moving. DOTS (user: blurred by
  the light): `ball.frag` dots rough and barely reflecting (specular
  0.05, clear coat 0.1 on a dot; the ball 0.4 / 0.6). PINS FEEL
  RIGHT (user, 2026-11-11: "i have knocked over a lot of pin in my life
  and I'm not getting uncanny valley at all"): step C's calibration is
  dropped, the cascade numbers notwithstanding. NEXT: the cushions (the
  user: they DO feel off), the kegle lag call (2.4: pins, 3rd ball, long
  cushion, pocket, same cushion twice lose the choice).
- `tabs` — the `TabBar`, a painted row of tabs: titles, a dot for unsaved
  changes or a cross to close, the current one accented; `currentChanged`
  and `closeRequested(index)` on clicks; it takes no focus and decides
  nothing.

- `browser` — the `FileBrowser`, a slim painted tree of a folder like an
  IDE's project view: folders first, suffix filter, click/arrow/double
  click and Vi keys (`jkhl o`), `fileActivated(path)`, `reveal`,
  `markedPath`, `refresh`. `FileNode` is the Qt-free tree node;
  `PaintFileTree` paints it.

- `vidget` — the `Vidget`, worQt's own text editing widget instead of Qt's
  text edits, editing the way Vim does: `ViMode` NORMAL/INSERT/COMMAND;
  counts; motions `hjkl wbe WBE 0^$ gg G {} f t F T ; , n N * # H M L`;
  operators `d c y` with any motion or doubled (`dw ct. yj dG dd cc yy`)
  and `x X D C s S Y r J p P`; `u`/Ctrl+R; `.` repeats the last change
  (recorded keys, replayed); `i a I A o O`; `/` `?` search; ex commands
  `:w :q :wq :x :q! :N :$` and `ZZ ZQ`, emitted as `writeRequested`/
  `quitRequested` for the window; scrolling (cursor followed, Ctrl+E/Y/D/
  U/F/B, `zt zz zb`, the wheel). Line numbers always shown in a gutter.
  Dark and monospaced by default; never narrower than 80 columns
  (`minimumSizeHint`).
  Vim as it is, but no trap: clicks place the cursor in any mode and the
  focus moves away as anywhere else. `viMotions` holds the motions as pure
  functions of a text. `VidgetBase` holds the text, cursor, history,
  register and scroll; it paints through `PaintBoxModel`,
  `PaintStatusLine` (bottom), `PaintLineNumbers` (left) and `PaintViText`;
  its hooks `accepts`, `shownText` (and the Vidget's `matchable`, for
  searches) let a subclass restrict and present the text.

- `windows` — `AbstractWindow` (build the UI once on the first `show()`;
  `closeEvent` consults the app's exit guard) → `BaseWindow` (menu bar) →
  `LayoutWindow` → `MainWindow`. `windows/menus` is the declarative menu
  system: `MenuBox`/`ActionBox` fields register menu and action types on the
  owning bar/menu, which build them lazily.
- `widgets` — `PaintedWidget` implements the box model (margins, borders,
  paddings, content) and paints through `paint_ops`; `LabelWidget`,
  `TextWidget`, `PaintButton`, `ClickButton` and `PushButton` build on it.
- `paint_ops` — painting operations as descriptors on a painted widget
  (`PaintBoxModel`, `PaintLabel`).
- `layouts` — `GridLayout` with `LayoutCell`/`LayoutIndex`.
- `waitaminute` — exceptions raised by widgets during event handling.
- `utils` — value types (geometry, `Color`), enums, fonts, `WPainter`.

`qtest` also provides `WidgetTest` (an `AppTest` with gestures: `showLive`,
`click`, `hold`, `key`, `typeText`, signal spies and waiters) and the
`primitives` behind it. A test child runs on the real display and falls back
to `offscreen` when no windowing platform is available.

## Conventions

These are enforced in this codebase; match them (see CONTRIBUTING.md):

- Two-space indentation, max line length 77.
- `camelCase` for variables/functions, `PascalCase` for classes.
- Quote identifiers in docstrings/comments with `'single quotes'`, never
  backticks.
- Pipe unions (`int | None`), not `Optional[...]`, in real annotations;
  PySide6
  sets the minimum Python version. `param: T = None` is acceptable as-is — do
  not
  rewrite to `T | None`.
- `from __future__ import annotations` at the top of every module;
  heavy/typing-only
  imports go under `if TYPE_CHECKING:  # pragma: no cover, no mutate`.
- Never use `exec`/`eval`/`__import__` for dynamic codegen — use `importlib`,
  `getattr`, or registries.
- `src/worQt/_class_body_template.py` defines the canonical section-banner
  layout
  (NAMESPACE, GETTERS, SETTERS, …) used in class bodies; follow it for new
  classes.

### Test layout

Tests live under `tests/`, mirroring the package (`tests/test_app` →
`worQt.app`).
Each test subpackage exposes a base test class subclassing
`worktoy.work_test.BaseTest` (e.g. `AppTest`), and concrete `Test*` classes
subclass that. Discovery picks up `test*.py`/`run*.py` modules, each defining
exactly one `Test*`/`Run*` class. Plain `BaseTest` classes (`test_*` methods)
are for Qt value types; `AppTest` classes (`run_*`/`test_*` methods,
inherited
ones included) run inside a live event loop. Every class runs in its own
child
process under a deadline, through the standard unittest runner.
`tests/test_qtest/fixtures/` holds deliberately failing modules for the
harness's own tests; their `_` names keep them out of discovery.

## Repo noise

Retired code and notes live in `archive/` at the repo root: gitignored, local
only, paths mirroring where each file used to live (see `archive/README.md`).
Never import from it. The active source is exclusively under `src/worQt`.
