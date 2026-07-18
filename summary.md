# worQt Session Handoff

Record of the current session so a successor can pick up cleanly. Covers what
changed, why, verification status, open items, and the working agreement reached
about worktoy.

> **Read this first — verification status.** Suite is **green: 49 passed / 0
> failed** (`latest.log`, 2026-07-15 14:42), covering *all* changes below —
> including the ClickButton cleanup, triple-hold, and the duplicate-registration
> exception. Both warnings from the prior `latest.log` are **gone**: the
> QPainter "Painter ended with 1 saved states" (fixed, section E) and the
> "event loop is already running" line (now filtered). Coverage was ~97% before
> these changes and was **not re-measured** on this run — regenerate it if you
> want the fresh number.

Run + coverage:
```bash
ENV=/home/AsgerJon/miniforge3/envs/worqt_env/bin/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src "$ENV" -m worQt.qtest
rm -f .coverage .coverage.*
WORQT_COVERAGE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src "$ENV" -m coverage run -m worQt.qtest
"$ENV" -m coverage combine && "$ENV" -m coverage report --sort=cover
```

---

## A. Git: `main_update` promoted to `main`

The whole branch became `main`. `main` was a strict ancestor of `main_update`,
so this was a fast-forward (nothing discarded), done via PyCharm:
`main_update` fast-forwarded onto `main`, `main_update` deleted (local + remote),
`origin/main` pushed. Confirmed `origin/main == 478b34b` (`harden base
functionality`). **The active branch is now `main`.**

## B. CLAUDE.md fixed (stale application docs)

The "Application classes" section described a three-layer chain
(`ApplicationMixin → AbstractApplication → App`) that no longer exists.
Rewritten to the real two layers: `ApplicationMixin(QApplication, MixinBase)` →
`App(ApplicationMixin)`, with `App` carrying `notify`/`handleException`, the lazy
`returnCode`/`splash`/`window` Fields + `__window_class__`, the exit guard
(`hasUnsavedChanges`/`saveChanges`/`confirmExit`), the title star, and the
context-manager loop. (`AbstractApplication` was folded into `App` in an earlier
session.)

## C. Button tests: triple-click + double-press-hold (pre-existing features)

Triple-click and double-press-hold emit logic already existed; they lacked
event-driven proof. Added to `tests/test_widgets/run_button_events.py`:
`run_triple_click_emits_triple_click`, `run_triple_click_emits_multi_click`,
`run_double_press_hold_emits_double_hold`.

## D. Windows GUI tests migrated to the WidgetTest pattern

`tests/test_windows/_windows_test.py`: `WindowsAppTest` now subclasses
`WidgetTest` (was `AppTest`), so the whole windows suite has the live-window /
gesture surface. `run_main_window.py`: `window.show()` + `QTest.qWait` + `close()`
→ `self.showLive(window)`; dropped the unused `QTest` import. (`run_menus` /
`run_menu_internals` are logic/guard tests, unchanged.)

## E. Two `latest.log` warnings fixed

- **`QPainter::end: Painter ended with 1 saved states`** — a real latent bug.
  `PaintedWidget.paintEvent` called `painter.save()` then `paintOp.paint(...)`;
  if the op raised, control skipped `painter.restore()`. Fixed: per-op body
  wrapped in `try/finally: painter.restore()`, so the painter reaches `end()`
  balanced and any op exception still becomes an `EventException`.
  (`src/worQt/widgets/_painted_widget.py`)
- **`QCoreApplication::exec: The event loop is already running`** — benign,
  expected (a test drives `App.__exit__`'s `exec()` inside the harness's running
  loop). Added `'event loop is already running'` to
  `AppTest._suppressBenignQtWarnings`. (`src/worQt/qtest/_app_test.py`)

## F. Triple-hold implemented (`_click_button.py`)

Mirrored the triple-click tier on the hold side: five `*TripleHold` signals,
`tripleHoldDict` Field + `_getTripleHoldDict` getter, and `_emitHolds` now caps
at `> 3` with `{1: single, 2: double, 3: triple}` — identical in shape to
`_emitClicks`. Fixed `run_emit_holds_branches` (the old `(_L, _L, _L)` "too many"
case is now a valid triple → bumped to `(_L, _L, _L, _L)`; added a triple
assertion) and added `run_triple_press_hold_emits_triple_hold` (event-driven).

## G. Typed duplicate-registration exception

Replaced both `NotImplementedError("lol we need a custom exception!")`
placeholders. New `worQt.waitaminute.DuplicateRegistration(owner, name, existing,
duplicate)` (`src/worQt/waitaminute/_duplicate_registration.py`, exported from
the package `__init__`). Raised from `AbstractMenuBar.registerMenuType` and
`AbstractMenu.registerActionType`. Updated the two `test_menu_boxes.py`
assertions (`NotImplementedError` → `DuplicateRegistration`).

## H. ClickButton state-machine cleanup — single source of truth

Long design discussion (see section K). Decision: **keep guarding against mixed
buttons** (the one-button-per-gesture invariant stays), but consolidate the
guards. Changes to `src/worQt/widgets/_click_button.py`:

- `_registerClick` is now the **sole guardian** of the invariant: the loop
  became a single first-element check; docstring states the invariant.
- `mousePressEvent` arms `movePoint`/timers **only if the press registered**
  (`if not self.hasClicks: return`). This fixes a real crash: previously a press
  of a different button emptied the sequence via `_registerClick` but
  `mousePressEvent` still armed the hold timer, so **click one button then
  press-and-hold a different button** raised `NotImplementedError` from inside
  `_emitHolds` (empty-sequence). Now a rejected mix arms nothing.
- `_emitClicks`/`_emitHolds` dropped the weak `firstButton != lastButton` guard
  (dead code given the invariant) and trust `clickSequence[0]`.
- **Removed the `> 3` "too many" guard** — replaced `clickDicts[len(...)]` with
  `.get(len(...))`: `multiClick`/`multiHold` fire for *any* length; the
  per-button single/double/triple signal fires only when a tier exists. No
  `KeyError`, no explicit cap.
- Tests (`run_click_button_internals.py`): pruned the now-dead mismatched
  white-box cases; the "too many" cases use `(_L, _L, _L, _L)` and now assert
  `multiClick`/`multiHold` fire with the full 4-tuple and no per-button signal;
  removed the unused `_R` constant; fixed docstrings.

## I. `worktoy_howto.md` created

A survival guide for worktoy's unconventional design, at the repo root. Written
as a **map that points to the source**, not a manual: metaclass/namespace hooks,
`Field` accessors resolved by name on `type(instance)`, `AttriBox`/`THIS`
semantics, overload dispatch + `flexCall`, frozen KeeNum members (no `@overload`
on member methods), `__set_name__` interception/raise, typed exceptions +
`SkipSet`, and the recursion-guard / preSet-SkipSet idioms. Every section tells
the reader to open the real file and verify.

## J. Memory correction

`project_attribox_this_owner_alias` was **wrong** vs the current 1.0.0 source: it
said `AttriBox[T](THIS)` builds `T(owner)`. The source
(`core/_object.py::getContextualSentinels`) is clear — `THIS` → the **instance**,
`OWNER` → the class — so it builds `T(instance)`. Corrected the note and the
`MEMORY.md` index line. (Caught while writing `worktoy_howto.md` — a live example
of "verify beats memory".)

---

## K. The mixed-click question (design, resolved to "keep guarding")

worQt buttons recognise same-button click/hold runs; a **different button
cancels** the run. This is deliberate: the recognizer is **single-track** — one
`movePoint`, one press/hold/sequential timer, one sequence — so it can follow
only one button's lifecycle at a time. A different button is a *concurrent*
gesture the machine has no state for; the guards force reality back onto that
invariant. Supporting real mixed gestures (e.g. `L-R-L`) would require
**per-button state** (each button its own press/hold/sequential/movePoint), with
mixed gestures as a higher layer — a real rework, explicitly deferred. Also note
`MouseButtonNum.fromEvent` uses `e.buttons()` (all held buttons), so truly
*simultaneous* buttons would raise `ValueError` — a separate assumption mixed
input would break.

## Open items
- **Run the suite** (section verification note). Confirm green + coverage after
  F–H.
- Mixed-button gestures deferred (needs per-button state; see K).
- `run_menus` / `run_menu_internals` / other non-window windows tests were left
  as logic tests (only `run_main_window` used a live window).

## Working agreement (worktoy reliability + token cost)
Reached this session and worth honouring:
- **No subagents, ever** (user directive).
- Don't preload all of worktoy; do **targeted just-in-time reads** of the one
  file for the thing being touched — cheap *and* current.
- worktoy is unconventional; a file that *uses* it looks conventional. **Verify
  behaviour against a test or a 5-line probe, never from memory or a summary**
  (this is the recurring source of regressions). worktoy lives at
  `.../worqt_env/lib/python3.14/site-packages/worktoy/`.
- Keep sessions narrowly scoped; long context correlates with drift.

## Key facts / gotchas
- **Never run the test suite** as the assistant — the user runs it.
- Env python: `/home/AsgerJon/miniforge3/envs/worqt_env/bin/python`. Base
  `python` lacks `worktoy`. `py_compile` is fine for a syntax check (it does not
  execute class bodies / the worktoy machinery).
- `latest.log` is written to the project root by `runAll`.
- ClickButton timers: press 250 ms, hold 750 ms, sequential 400 ms; move limits
  3**2 = 9. `multiClick`/`multiHold(tuple)` fire for every resolved run of any
  length; per-button single/double/triple only for lengths 1–3.
