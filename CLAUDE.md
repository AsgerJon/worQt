# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`worQt` extends the `worktoy` library with utilities for building Qt for Python
(PySide6) desktop applications. The published package is named `worQt`; its
source lives under `src/worQt`. `worktoy` and `pyside6` are external runtime
dependencies — do not vendor or reimplement their machinery.

## Commands

Tests run through the in-house `worQt.qtest` harness, NOT pytest. Put `src` on
`PYTHONPATH` and run from the repo root. Always prefix Python invocations with
`PYTHONDONTWRITEBYTECODE=1`.

```bash
# Run the whole test suite (every test class in its own child process)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest

# Run only some test modules by dotted name (plain or 'AppTest' alike)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest tests.test_utils.test_color

# Every top-level run (any entry point) rewrites 'latest.log' in the repo root
# with its complete record: status lines plus every child's full output.

# Local scratch runner: the gitignored 'main.py' hands callables to 'yolo()'
# ('yolo.py'), which runs them and pretty-prints any traceback. Its
# 'runTests'/'testMeBro' run the qtest suite.
PYTHONDONTWRITEBYTECODE=1 python main.py
```

`roll_version.py` bumps the version in `current_version.json` / `current_tag.txt`.

## Architecture

### The metaclass fusion (`src/worQt/mixin`) — the core idea

The central problem worQt solves: Qt classes are built by Shiboken's metaclass
(`type(Shiboken.Object)`), and worktoy classes are built by `worktoy.mcls.BaseMeta`.
You cannot subclass both Qt and a worktoy `BaseObject` directly — Python rejects
the metaclass conflict. The `mixin` subpackage fuses the two so worktoy's
descriptor/overload machinery becomes available on Qt-derived classes:

- `MixinMeta` — the fused metaclass. Its MRO inserts a private `_Shiboken`
  metaclass between Shiboken's `ObjectType` and `BaseMeta`. `_Shiboken.__getattr__`
  bridges a contract mismatch: worktoy's `AbstractMetaclass` expects names matching
  `__class*__` to resolve to the `METACALL` sentinel rather than raise
  `AttributeError`; Shiboken doesn't honour that, so `_Shiboken` intercepts and
  returns `METACALL` for that pattern. `__new__` routes class creation through
  `_ObjectType.__new__` with the compiled namespace.
- `MixinSpace` — the namespace object (`__prepare__` returns one). Currently a thin
  `BaseSpace` subclass, reserved as the hook point for MixinMeta-specific namespace
  behaviour.
- `MixinBase` — `BaseObject` subclass declared `metaclass=MixinMeta`. This is the
  bridge users inherit from to get worktoy behaviour on a Qt class.

When touching this subpackage, preserve the MRO ordering and the `__getattr__`
bridge — both are load-bearing and subtle. The `__init__.py` import order
(`MixinSpace` → `MixinMeta` → `MixinBase`) is also load-bearing.

### Qt + QObject construction constraint

Constructing a `QObject` (including any worQt class that mixes in a Qt type)
before a `QApplication` exists can hard-crash the interpreter (segfault), not
raise. Keep QObject construction out of class bodies and module import time;
defer it until an application instance exists. The `App` class follows this by
lazily constructing its splash screen and main window on first access.

### Application classes (`src/worQt/app`)

- `ApplicationMixin(QApplication, MixinBase)` — the fusion point where a
  concrete Qt type meets worktoy machinery.
- `App(ApplicationMixin)` — the worQt application, used as a context manager:
  `__exit__` runs the Qt event loop only on a clean exit. It owns the lazily
  built `splash` and `window` (a concrete app sets `__window_class__`),
  routes exceptions raised in slots and event filters from `notify()` to the
  `handleException()` hook (only `Exception`; `KeyboardInterrupt`/`SystemExit`
  propagate), and guards exit: `confirmExit()` offers Save/Discard/Cancel when
  `hasUnsavedChanges()`, and the window title carries a ` *` marker while
  there are unsaved changes. Usage:

  ```python
  with MyApp(*sys.argv) as app:
      app.window.show()
  ```

### The rest of the package

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
- `src/moreworktoy` — `errorFmt`, utilities that may move to worktoy.

`qtest` also provides `WidgetTest` (an `AppTest` with gestures: `showLive`,
`click`, `hold`, `key`, `typeText`, signal spies and waiters) and the
`primitives` behind it. A test child runs on the real display and falls back
to `offscreen` when no windowing platform is available.

## Conventions

These are enforced in this codebase; match them (see CONTRIBUTING.md):

- Two-space indentation, max line length 77.
- `camelCase` for variables/functions, `PascalCase` for classes.
- Quote identifiers in docstrings/comments with `'single quotes'`, never backticks.
- Pipe unions (`int | None`), not `Optional[...]`, in real annotations; PySide6
  sets the minimum Python version. `param: T = None` is acceptable as-is — do not
  rewrite to `T | None`.
- `from __future__ import annotations` at the top of every module; heavy/typing-only
  imports go under `if TYPE_CHECKING:  # pragma: no cover`.
- Never use `exec`/`eval`/`__import__` for dynamic codegen — use `importlib`,
  `getattr`, or registries.
- `src/worQt/_class_body_template.py` defines the canonical section-banner layout
  (NAMESPACE, GETTERS, SETTERS, …) used in class bodies; follow it for new classes.

### Test layout

Tests live under `tests/`, mirroring the package (`tests/test_app` → `worQt.app`).
Each test subpackage exposes a base test class subclassing
`worktoy.work_test.BaseTest` (e.g. `AppTest`), and concrete `Test*` classes
subclass that. Discovery picks up `test*.py`/`run*.py` modules, each defining
exactly one `Test*`/`Run*` class. Plain `BaseTest` classes (`test_*` methods)
are for Qt value types; `AppTest` classes (`run_*`/`test_*` methods, inherited
ones included) run inside a live event loop. Every class runs in its own child
process under a deadline, through the standard unittest runner.
`tests/test_qtest/fixtures/` holds deliberately failing modules for the
harness's own tests; their `_` names keep them out of discovery.

## Repo noise

Retired code and notes live in `archive/` at the repo root: gitignored, local
only, paths mirroring where each file used to live (see `archive/README.md`).
Never import from it. The active source is under `src/worQt` and
`src/moreworktoy`.
