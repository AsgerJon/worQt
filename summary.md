# worQt Session Handoff

A detailed record of the last working session so a successor can pick up
cleanly. Covers what changed, why, how it was verified, open items, and a
worktoy reference relevant to worQt development.

---

## Overview

This session built an **event-based GUI testing system**
(`worQt.qtest.WidgetTest` + a `qtest/primitives/` subpackage), converted the
widget test suite to it, added a run log (`latest.log`), fixed the error
formatter, fixed three real widget bugs the new tests exposed, and extended
`ClickButton` with triple-click. Everything was verified by `py_compile` +
offscreen diagnostics; **the user runs the actual suite** (do not run it).

---

## A. New testing infrastructure (`src/worQt/qtest/`)

### `primitives/` (new subpackage)
Reusable classes, all `BaseObject`, holding their Qt internals and building
them at runtime, so they behave identically in authentic and headless modes.

- **`SignalSpy(signal)`** — connects on construction, records emissions.
  `emissions`, `count`, `args` (last emission), `clear()`,
  `__len__/__bool__/__iter__`; `_record(*args)` slot.
- **`SignalWaiter(signal, timeout=1000)`** — context manager. `__enter__`
  connects; `__exit__(self, _, exception, __)` spins a nested `QEventLoop`
  until the signal fires or a timeout `QTimer` quits (skips the wait and
  propagates if the body raised). `caught`, `timedOut`, `args`.
- **`ConditionWaiter(predicate, timeout=1000)`** — `wait() -> bool`; polls
  the predicate every 10 ms in a nested loop until true/deadline.
- **`LiveWindow(widget, timeout=5000)`** — `show()` → `raise_()` /
  `activateWindow()` → `QTest.qWaitForWindowExposed` → returns the widget
  (populates `paintView`). Works in authentic and offscreen.

### `_render_mode.py` (was `_test_mode.py`)
Renamed because `TestMode` collides with the `Test*` discovery prefix.
- `RenderMode(KeeNum)`: `AUTHENTIC = Kee[str]('')`,
  `HEADLESS = Kee[str]('offscreen')`; `applyEnv(env)` returns a copy with
  `QT_QPA_PLATFORM` set (authentic leaves env unchanged).

### `_widget_test.py` (new) — `WidgetTest(AppTest)`, the gesture surface
- Conveniences: `showLive(widget)`, `spy(signal)`,
  `waitSignal(signal, timeout=1000)`, `waitUntil(pred, timeout=1000)`,
  `wait(ms)`.
- Mouse gestures via `QApplication.sendEvent` (routes through `App.notify`;
  **identical in both render modes** — the reason sendEvent was chosen over
  `QTest.mouseClick`, whose global coords are meaningless offscreen):
  `move`, `press`, `release`, `click`, `doubleClick`, `hold(widget, ms, …)`.
- Keyboard: `key`, `typeText`.
- Helpers: `_resolveButton` (accepts `MouseButtonNum` or `Qt.MouseButton`),
  `_localPoint` (`Point2D`/`QPoint`/`QPointF`, default widget centre),
  `_sendMouse`.

### `_app_test_run.py` (edited) — authentic-first, headless fallback
Fallback lives at the **process layer** because Qt **aborts uncatchably**
when no platform initializes (an in-process try/except cannot catch it).
- `_runPopen` → `_launch(RenderMode.AUTHENTIC)`; if
  `_isDisplayFailure(code, output)` (non-zero exit **and** a platform-plugin
  token from `_DISPLAY_FAILURE_TOKENS`), relaunch
  `_launch(RenderMode.HEADLESS)` with a note prepended.
- `_launch(mode)` = the Popen logic with `mode.applyEnv(baseEnv)`.

### `_app_test_suite.py` (edited)
- **Run log**: module-level `_LogTee` forwards each write to the console
  unchanged and to the log file with ANSI stripped (`_ANSI` regex). `runAll`
  opens `<root>/latest.log`, wraps the body in
  `redirect_stdout(_LogTee(...))`, and delegates to `_runReport()` (the old
  body). `__root_dir__` (dir containing `tests/`) is the project root.
- **Failed-class list**: `_runReport` collects `failedNames` (run failure →
  `cls.__name__`; load failure → `_classNameFor(name)`),
  `failures = len(failedNames)`, prints the count via `_log(1, …)` then a
  **verbatim** indented list (`Failed:\n  A,\n  B`) — verbatim because
  `_log` → `wordWrap` collapses newlines.
- **`_classNameFor(name)`** classmethod: reads the module source (via
  `__root_dir__` + dotted path, **no import**) and returns the first
  `Run*`/`Test*` class name, else the dotted name — so a module that fails
  to *import* still reports its class name in the summary.

### `_app_test.py` (edited) — fixed inverted widget disposal (real bug)
- `_deletePersistentWidgets` → renamed **`_disposeOpenedWidgets`**; the
  condition was flipped to `if id(widget) not in preopenWidgets`. It now
  keeps pre-open widgets and disposes only what the test opened (matching
  the `setUp`/`tearDown` docstrings). Fixed
  `RunAppTestInternals.run_teardown_keeps_preopen_widget`. Caller in
  `tearDown` updated.

### `__init__.py` (edited)
Import order: `HookTest`, `SpaceTest`, `MetaTest`, `RenderMode`,
`primitives`, `AppTest`, `AppTestRun`, `AppTestSuite`, `WidgetTest`,
`testMeBro`. Exports include `RenderMode`, `primitives`, `WidgetTest`.

---

## B. errorFmt fixes (`src/moreworktoy/utilities/_error_fmt.py`)
- The `Caught <ExcType>` + message summary now renders **first** (frames are
  deepest-first, so the error site sits right under the message). Each frame
  gets a leading blank line.
- **Skips synthetic frames**:
  `if fileName.startswith('<') and fileName.endswith('>'): continue`
  (drops `<frozen importlib._bootstrap>`, `<string>`, etc. empty boxes).

---

## C. Widget bug fixes (exposed by authentic gestures; old white-box /
offscreen tests masked them)

- **`_paint_button.py` `_getContentRectPosition`**: was checking the
  *offset* point against `paintView`; now checks `cursor in self.paintView`
  and returns `Point2D(cursor.x - left, cursor.y - top)`.
- **`_click_button.py` `mouseMoveEvent`**: drag distance was
  `Vector2D(movePoint, contentRectPosition)` — mismatched coordinate systems
  (any move cancelled the click). Now
  `Vector2D(self.movePoint, self.assignedRectPosition)` (both widget coords).
- **`_click_button.py` double-click**: **removed `mouseDoubleClickEvent`**,
  added an **`event(self, e)`** reimplementation —
  `if e.type() == QEvent.Type.MouseButtonDblClick: self.mousePressEvent(e);
  return True` else `return super().event(e)`. Per the intended design, Qt's
  double-click machinery is deliberately unused; the widget detects
  double/triple from its own press/release sequence
  (press → release → press → release → move-away), and Qt delivers the 2nd
  press *as* a DblClick, so `event()` feeds it to `mousePressEvent`. Added
  the `QEvent` import.

### C2. Triple-click feature (`_click_button.py`)
- Added `tripleClickDict` Field + `_getTripleClickDict` getter, and five
  `*TripleClick` signals (`leftTripleClick`, …).
- `_emitClicks`: `> 3 → multiClick only`; `clickDicts = {1: single,
  2: double, 3: triple}`. **Kept the generalized `multiClick`** (emitted for
  every sequence). Double-press-hold (`leftDoubleHold`) already worked and
  was verified — no change needed there.

---

## D. Test suite conversion (`tests/test_widgets/`)
- **Deleted** `_widget_test.py` (redundant `WidgetTest` base) and the dead,
  broken `helpers/` package (`_mouse_event_factory.py` referenced `Button.Q`
  on a type alias; `_example_app.py` unused).
- Each `run_*` now imports `from worQt.qtest import WidgetTest` **directly**
  (no re-export lay-over); `__init__.py` exports nothing.
- **Rewrote `run_button_events.py`** to the gesture pattern (`_live` fixture
  = build/resize/`showLive`/`initUI`; `showLive`,
  `move/press/release/click/doubleClick/hold`, `spy/waitSignal`). Real
  windows, real timers.
- Offscreen `render(QPixmap)` → `showLive`: `run_render_sweep.py`,
  `run_painted_widget.py` (3 tests), `run_paint_ops.py` (1 test; the **two**
  paintEvent-exception tests keep `render()` for synchronous exception
  capture), `run_widget_internals.py` (1 test).
- `fired=[]`+lambda → `self.spy`, and hand-built `QMouseEvent` → gestures, in
  `run_click_button_internals.py` and `run_buttons.py`.
- **`tests/test_app/test_abstract_application.py`**: `AbstractApplication`
  (removed — merged into `App`) → `App` in the import, `test_metaclass`,
  `test_recursion_peek`, and docstrings.

---

## Suite status
Last full run before the final fixes: **46 passed / 3 failed**
(`RunAppTestInternals`, `TestAbstractApplication`, `RunButtonEvents`). All
three root causes were fixed this session. **Next: run the suite, check the
fresh `latest.log`, add tests for triple-click / double-press-hold.**

## Open items
- Triple **hold** not added (only double-press-hold was requested, and it
  already exists). Trivial mirror if wanted: five `*TripleHold` signals,
  `tripleHoldDict` + getter, length-3 case in `_emitHolds`.
- No `RunButtonEvents` tests yet for triple-click or the double-press-hold
  path.
- Other GUI test files (`tests/test_windows/`: `run_menus`,
  `run_menu_internals`, `run_main_window`) not yet reviewed for the same
  gesture treatment.

## Key facts / gotchas learned
- **App design**: `App(ApplicationMixin)` directly — there is **no**
  `AbstractApplication` (the layered design in docstrings/CLAUDE.md was
  collapsed). `App` carries `notify`, `handleException`, `_getSplash`,
  `_getWindow`, `confirmExit`, splash/window Fields.
- **Env python**: `/home/AsgerJon/miniforge3/envs/worqt_env/bin/python`.
  Diagnostics (debugging, NOT the suite):
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
  <env-python> script.py`. Base `python` lacks `worktoy`.
- **`latest.log`** is written to the project root by `runAll`.
- **`ClickButton` timers**: press 250 ms, hold 750 ms, sequential 400 ms;
  move limits 3**2 = 9.
- `sendEvent` reaches `widget.event()` (through `notify`), so the `event()`
  override is exercised by the gestures.

---

## worktoy reference relevant to worQt

**`worktoy.mcls`** — metaclass framework. `BaseObject` (base for non-Qt worQt
value classes), `BaseMeta`, `BaseSpace`, `AbstractMetaclass`,
`AbstractNamespace`, `space_hooks`. worQt's `MixinMeta` fuses `BaseMeta` with
Shiboken's metaclass; `qtest.MetaTest/SpaceTest/HookTest` subclass these to
collect `run_*`/`test_*` methods.

**`worktoy.desc`** — descriptors (the core idiom).
- `Field()` — property-like; accessors by decorator `@x.GET/@x.SET/@x.DELETE`
  plus notifiers `@x.preGet/onGet/preSet/onSet/preDelete/onDelete/setName`.
  Accessors resolved **by name on `type(instance)`**, so subclasses override
  by redefining the method. Use `Field` + private `__x__` slot for
  per-instance / runtime-typed state.
- `AttriBox[T](*args)` — lazy, type-enforced attribute; `THIS`/`OWNER`/`DESC`
  sentinels in the deferred args. worQt rule: widgets/layouts in AttriBox,
  `THIS` on widgets only (never layouts).
- `FixBox[T]` (write-once), `FastBox[T]` (lean), `Alias('name')`,
  `SymbolicName`, `BaseDescriptor`.

**`worktoy.core`** — `Object` (contextual descriptor base; `self.instance`/
`self.owner`), sentinels `THIS`, `OWNER`, `DESC`, `DELETED`, `METACALL`,
`ARGS`, `MetaType`.

**`worktoy.dispatch`** — overloading. `@overload(*types)` (stackable; `THIS`
for the enclosing class; `strict=True` disables coercion),
`@overload.flex/fallback/finalize`. Machinery: `TypeSig`, `Dispatcher`,
`flexCall` (truncating-arg wrapper — why a method can take fewer args than
passed). Used for overloaded `__init__` on geom/value types.

**`worktoy.keenum`** — enumerations. `KeeNum` + `Kee[T](value)` (members must
be UPPER_CASE). `KeeFlags`/`KeeFlag` (bitmask; 2**N members). `KeeBox`
(AttriBox whose field type is an enum). `KeeMeta`/`KeeMetaMeta` — to extend
the metaclass, subclass `KeeMeta` and use `YourMeta.keeNum` as the base (see
`FontMeta`/`FontFamilyMeta`). **Members are frozen** → give them plain
methods only, never `@overload` (the dispatcher's per-instance `setattr`
cache is rejected — e.g. `FontWeightNum.apply`, `Alignum.apply`).

**`worktoy.waitaminute`** — typed exceptions (fail-fast).
`TypeException(name, obj, *types)`, `MissingVariable(instance, name,
*types)`, `VariableNotNone`, `SubclassException`, `UnpackException`;
`desc.ReadOnlyError/ProtectedError/WriteOnceError/AccessError/
WithoutException`; `control_flow.SkipSet` (raise from `@x.preSet` to elide a
redundant set — the "value unchanged → don't fire onSet" pattern).

**`worktoy.utilities`** — `maybe(*args)`, `textFmt` (`<br>`/`<tab>` tokens),
`stringList`, `wordWrap`, `joinWords`, `unpack`, `typeCast(type, val)`,
`resolveMRO`, `QuickDesc('__slot__')`, `Directory`, `ExceptionInfo`.

**`worktoy.work_test`** — `BaseTest` (the `unittest.TestCase` subclass
`AppTest` extends). `worktoy.ezdata` (`EZData`/`EZField`) and
`worktoy.lorem_ipsum` are peripheral (lorem drives the test samplers).

### Recurring idioms
- **Lazy getter + recursion guard**:
  ```python
  @x.GET
  def _getX(self, **kwargs):
    if self.__x__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self._createX()                       # or assign fallback
      return self._getX(_recursion=True)
    if isinstance(self.__x__, T): return self.__x__
    raise TypeException('__x__', self.__x__, T)
  ```
- **preSet SkipSet + onSet update**: `@x.preSet` raises `SkipSet` when the
  value is unchanged; `@x.onSet` calls `self.update()`.
- **No kwargs when constructing** (positional only), except the
  `_recursion=True` guard idiom, which is pervasive and accepted.
- Conventions: 2-space indent, <=77 cols, `camelCase`/`PascalCase`,
  `'single quotes'` in docstrings (never backticks), descriptive
  third-person docstrings, `from __future__ import annotations`, typing-only
  imports under `if TYPE_CHECKING:`.
