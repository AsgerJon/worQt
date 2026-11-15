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

Each larger package keeps its working notes in its own CLAUDE.md,
which Claude Code loads when files there are worked on; this file keeps
a summary. Add new notes to the package's own file, not here.

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

- `engineering` — structures as a civil engineer thinks of them (m, kN,
  MPa), Qt-free models with painted GUIs: the `Disk` ('skive') with its
  strut-and-tie lower bound (`StrutTie`) and its app, built to need no
  explanation. `engineering.gui` also holds widgets the labs share
  (`ToolButton`, `Slider`/`QuantitySlider`, `CheckBox`, `TestStatus`,
  `TimeCurve`, crack colours). Notes: `src/worQt/engineering/CLAUDE.md`.
  Its labs, each with its own notes:
  - `engineering.meso` — concrete simulated from its ingredients
    (stones, a Voronoi lattice of rigid cells, torch), cast, crushed
    and pulled apart, in 3D.
  - `engineering.lab` — the RC beam lab: a 3D brick beam on a rig of
    supports, actuators and transducers under one PID loop, reckoned
    by OpenSees through `worksees`; '.beam' files.
  - `engineering.springs` — masses, springs and dampers swinging in 3D,
    guides as linear constraints.
  - `engineering.diagrams` — section force diagrams of plane frames
    (stiffness method, exact N V M).
  - `engineering.circuits` — school circuits solved exactly (piecewise
    linear diodes and transistors, matrix_exp between turns).
  - `engineering.quests` — a quest game on the circuits, from a first
    lamp up through logic chips to a 4004-style microprocessor.
- `worksees` (`src/worksees`, a sibling package beside `worQt`,
  Qt-free) — OpenSees models kept as plain values, solved in a worker
  process. Notes: `src/worksees/CLAUDE.md`.
- `gaming` — games on worQt. `gaming.pusher`: a fraud-free two-level
  coin pusher in real 3D on our own Warp coin solver, sounds in a
  process of their own. Notes: `src/worQt/gaming/pusher/CLAUDE.md`.
  `gaming.billiards`: three-cushion carambole and Danish keglebillard in
  real 3D (Qt Quick 3D): exact cloth phases, the Mathavan cushion, the
  cue as a spring, the FFB and DDBU referees, recordings played in
  workers, unfolded maps, the walking room. Notes:
  `src/worQt/gaming/billiards/CLAUDE.md` (and the user's physics in
  memory).
- `phys` — the lab's own rigid body physics, first for a vehicle:
  bodies, the ground, ties, welds, springs, dampers, actuators,
  contacts, the hexapod, compiled Warp stepping, sleeping; the tower
  viewer. Notes: `src/worQt/phys/CLAUDE.md`.

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
