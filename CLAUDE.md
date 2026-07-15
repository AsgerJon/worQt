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
# Run the whole test suite (each 'AppTest' class in its own child process)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest

# Run a single test class by its dotted module name
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.qtest tests.test_app.test_abstract_application

# Scratch runner: main.py drives yolo(), which runs a list of callables and
# pretty-prints any traceback with source context. Edit the yolo(...) call at
# the bottom of main.py to choose what runs.
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

Two layers, not three — the earlier `AbstractApplication` middle layer was
folded into `App`:

- `ApplicationMixin(QApplication, MixinBase)` — the actual fusion point where a
  concrete Qt type meets worktoy machinery. Empty body; it exists only to be the
  place the two metaclasses meet.
- `App(ApplicationMixin)` — the concrete application, carrying every app-scoped
  concern directly:
  - `notify()` funnels exceptions raised inside slots/event filters into
    `handleException()` (a no-op hook for subclasses to override). Only
    `Exception` is intercepted; `KeyboardInterrupt`/`SystemExit` propagate.
  - `returnCode`, `splash` (a `QSplashScreen`) and `window` (a `QMainWindow`
    subclass) are worktoy `Field` descriptors backed by lazily-constructed
    private slots. The window *type* is app-specific: a concrete subclass sets
    `__window_class__`, and `getWindowClass()` raises `MissingVariable` if it is
    unset. Because any `MixinBase` can reach the running application through
    `self.app`, `self.app.window` reaches these from anywhere in the graph.
  - Exit guard: `hasUnsavedChanges()`/`saveChanges()` are hooks a concrete app
    overrides; `confirmExit()` is the single place the Save/Discard/Cancel prompt
    lives, consulted by `AbstractWindow.closeEvent`.
  - Title star: `_startTitleWatch()` polls `hasUnsavedChanges()` on a `QTimer`
    (there is no generic "dirty changed" signal) and `_refreshTitle()` keeps the
    `__unsaved_marker__` (` *`) on the window title current.
  - Context manager: `__enter__` returns the app; `__exit__` runs the Qt event
    loop (`self.exec()`) and records `returnCode` only on a clean exit (no
    exception in the with-body). Usage:

  ```python
  class MyApp(App):
    __window_class__ = MyWindow

  with MyApp(*sys.argv) as app:
      app.window.show()
  ```

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
subclass that. `python_files = test_*.py`.

## Repo noise

The repo root and history contain scratch/legacy files unrelated to the package:
`main_cls*.py`, `OLD_main_*.py`, and `src/_deprecated/`. These are not part of
`worQt`; do not treat them as reference or import from them. The active source is
exclusively under `src/worQt`.
