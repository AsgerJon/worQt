# worQt — state of the project & handoff

A handoff doc for a fresh context window. It records (1) what worQt is and the
working method, (2) the conventions you must follow, (3) the current package
map, (4) the archived-stack revival and the worktoy-migration gotchas it
surfaced, (5) the test-coverage push to **100%** and the worktoy foot-gun it
flushed out (fixed at the source, in worktoy rc12), and (6) the current green
state, how to verify it, and what is deferred / where to go next.

Quote identifiers with 'single quotes' in prose, never backticks. Markdown
code fences are fine (they are code, not quoted identifiers).

---

## 0. The method

worQt extends 'worktoy' with utilities for building Qt for Python (PySide6)
desktop apps. **The abstractions are the product; example apps are only the
vehicle.** Build a throwaway example, let it press on the core, lift whatever
generalises into real worQt, then delete the example.

'worktoy' is an external dependency, currently **1.0.0-rc12** (mature/stable).
Do not vendor or reimplement it. Used parts: 'worktoy.core' ('Object',
sentinels 'THIS'/'OWNER'/'DESC'), 'worktoy.desc' ('AttriBox', 'Field',
'BaseDescriptor', 'Alias', 'FixBox'), 'worktoy.dispatch' ('overload'),
'worktoy.mcls' ('BaseObject', 'BaseMeta', 'BaseSpace', space hooks),
'worktoy.keenum' ('KeeNum', 'Kee', 'KeeFlags', 'KeeFlag', 'KeeMeta', 'KeeBox'),
'worktoy.work_test' ('BaseTest').

---

## 1. Conventions (enforced — match them)

- Two-space indent, max line length 77.
- 'camelCase' for vars/functions, 'PascalCase' for classes.
- Identifiers in docstrings/comments in 'single quotes', never backticks.
- Pipe unions ('int | None') in real annotations, not 'Optional[...]'. But
  'param: T = None' is fine as-is.
- "True if x else False" ternaries are deliberate; do not collapse to 'bool(x)'.
- 'from __future__ import annotations' at the top of every module; heavy /
  typing-only imports under 'if TYPE_CHECKING:  # pragma: no cover'.
- No 'exec'/'eval'/'__import__' for codegen — use 'importlib'/'getattr'.
- **Positional args only** — no kwargs, even for AttriBox/Qt constructors.
- Never name a novel backing dunder with a single word ('__value__'); qualify
  it ('__setting_value__').
- Always run Python with 'PYTHONDONTWRITEBYTECODE=1'. **Do not run the test
  suite** — the user runs it ('./coverage_test.sh' or 'python -m worQt.qtest')
  and hands execution back. You may 'py_compile' or import-probe under
  'QT_QPA_PLATFORM=offscreen' to verify a value/test.
- License header on every file: '#  Apache-2.0 license' (no AGPL).
- **Remove dead/unused/broken code on sight** (standing OK; no need to ask).

### Qt construction constraint (load-bearing)
Constructing a 'QObject' (any worQt class mixing in a Qt type) **before a
'QApplication' exists hard-crashes (segfault).** So: never build QObjects in
class bodies or at import; build widgets/layouts lazily (in 'show()' /
'initUI()' / 'paintEvent'). Widgets/layouts go in 'AttriBox'; 'THIS' on widgets
only, never on layouts. Value types (geom, color, fonts) are NOT QObjects and
are safe anywhere. 'MixinBase.__set_name__' raises to enforce this at class
creation.

### worktoy idioms used everywhere
- 'AttriBox[T](*args)' — lazily built, typed attribute; 'T(*args)' on first
  read, cached. 'THIS' resolves to the instance, 'OWNER' to the owner class.
- 'Field' + private slots ('__snake_named__') with '@x.GET'/'@x.SET' — when a
  value is computed/runtime-shaped. Recursion-guard getter pattern: '_createX'
  sets the slot, '_getX' calls it then re-reads via '_getX(_recursion=True)';
  the inner call raising 'RecursionError' is the failed-build guard.
- '@overload(types)' constructors compiled into a dispatcher by the metaclass;
  first-registered wins, no specificity ranking. A subclass that overrides an
  overloaded method **with a plain method now works correctly** (it is kept as
  the override) — see §5.

---

## 2. Current package map ('src/worQt')

- 'mixin' — the metaclass fusion: 'MixinMeta' fuses Shiboken's metaclass with
  'worktoy.mcls.BaseMeta'; 'MixinBase' is the base users inherit to get worktoy
  machinery on a Qt class. (Load-bearing — preserve the MRO and the
  '_Shiboken.__getattr__' METACALL bridge.)
- 'app' — 'ApplicationMixin' -> 'AbstractApplication' (owns 'returnCode' /
  'splash' / 'window'; 'notify' funnels slot exceptions to 'handleException';
  'getWindowClass' from a subclass '__window_class__') -> 'App' (context manager
  running 'exec()' on clean exit).
- 'data' — Qt-free document/field/file layer: 'AbstractDocument',
  'SingleField'/'ArrayField' (encoder/decoder resolved by name on the
  document), 'AbstractItem'/'NotifyBox' (item attrs notify on write),
  'ArrayLike', 'AbstractFile' -> 'MainFile'/'LocalFile' (atomic save/load).
  Hardcodes JSON serialization (a known crack to make pluggable).
- 'words' — the text-doc larp: 'Section(AbstractItem)',
  'TextDocument(AbstractDocument)' (author/title/date single fields + a
  'sections' ArrayField), and 'TextWindow(AbstractWindow)' — a 'QPlainTextEdit'
  editor with a File menu, built lazily in 'initUi'.
- 'windows' — main-window chain 'AbstractWindow' (build-once 'show()' ->
  'initUi', '_action' helper) -> 'BaseWindow' (menu bar in 'initMenus') ->
  'LayoutWindow' (central widget + layout in 'initUI') -> 'MainWindow'
  ('initLogic'). 'windows.menus' is a declarative menu system:
  'AbstractAction'/'AbstractMenu'/'AbstractMenuBar', 'ActionBox'/'MenuBox'
  (declare-and-register descriptors), 'MenuSeparator', concrete File/Edit/View/
  Help menus + 'MainMenuBar'.
- 'utils' — the value-type / painting helpers (see §3 and §4).
- 'layouts' — 'LayoutMixin', 'LayoutCell', 'LayoutIndex', 'BaseLayout',
  'GridLayout' (cell/row/column layout over 'QGridLayout').
- 'widgets' — the painted widget stack (see §4).
- 'paint_ops' — declarative paint operations (see §4).
- 'waitaminute' — worQt exceptions ('waitaminute.events': 'EventException' and
  the 'Keyboard'/'Mouse'/'Paint'/'InvalidSizePolicy' subclasses, routed out of
  the event loop).
- 'qtest' — in-house Qt test harness ('AppTest' classes in child processes
  under a deadline; plain 'BaseTest' in-process). Run: 'python -m worQt.qtest'.

---

## 3. The geom rebuild ('utils/geom')

The archive's geom was built on a 'euclid' subpackage (a custom metaclass +
'DimHook' that auto-synthesized 'overload(THIS)' constructors). worktoy rejects
that (it refuses to hash a 'TypeSig' containing 'THIS' outside an active
class-body context), so **'euclid' was deleted** and the types rebuilt as plain
'BaseObject' + 'overload', backed by Qt value classes, exposing '.Q' (and
'.QF') conversions:

- 'Point2D' ('Point' alias), 'Vector2D', 'Size', 'Rect', 'RoundedRect',
  'InSets', 'Color'.
- 'Rect' is left/top/right/bottom based; 'InSets' does the box-model arithmetic
  ('Rect + InSets' grows outward, 'Rect - InSets' shrinks inward).

**Pattern for any Qt-wrapping value type:** 'BaseObject', store with
'AttriBox[int]'/'[float]', give overloaded constructors — and on every
signature that takes a Qt type ('QPoint', 'QSize', 'QRect', 'QVector2D', ...)
pass **strict=True** in the overload, e.g. '@overload(QPoint, strict=True)'.
Without strict, the dispatcher's coercion tier runs 'typeCast' against the
Shiboken type and Qt aborts.

---

## 4. The painting stack ('utils', 'widgets', 'paint_ops')

- 'utils' value helpers: 'Color', 'EmptyPen'/'EmptyBrush', 'WFont',
  'WPainter'/'WPainterPath' (QPainter/QPainterPath fused with 'MixinBase',
  adding 'fillBetween'/'printLabel'), 'Eps', 'MouseButtonNum',
  'ButtonStateFlags', and the enum subpackages 'qee_num' ('SizingMode',
  'SizePolicy', 'BoxNum', 'HAlignum'/'VAlignum'/'Alignum', 'VertexNum',
  'EdgeNum', 'ColorNum') and 'font_nums' (font family/weight/style/line enums;
  'FontFamilyNum' discovers system families via 'QFontDatabase' at class
  creation, spooling a temp app if none is running).
- 'widgets' — 'WidgetMixin'/'AbstractWidget' bases, 'PaintedWidget' (the
  box-model widget: margins/borders/paddings via 'InSets', sizing modes, a
  paint-op registry, 'xr'/'yr' corner radii, one inherited 'paintEvent' that
  walks the ops and routes any exception as 'EventException'), and concretes:
  'LabelWidget', 'TextWidget', 'PaintButton', 'ClickButton', 'PushButton',
  'ScratchWidget' (ad-hoc dev/test widget; named 'ScratchWidget' so its name
  does not trip 'qtest' discovery).
- 'paint_ops' — declarative painting: 'PaintMixin', 'AbstractPaintOp' (a
  descriptor declared as a class var on a painted widget;
  'paint(painter, rect, event) -> Rect' threads the available rect through the
  op chain — the box model as a pipeline). Concretes: 'PaintBoxModel',
  'PaintLabel'.

Declare paint layers as descriptors in a widget body; one inherited
'paintEvent' walks them.

---

## 5. History — revival, then the 100% coverage push

### 5a. The revival (archived stack -> worktoy)
A large archived GUI system (utils/widgets/paint_ops/layouts), written against
an older 'worktoy'/'moreworktoy', was restored and migrated onto current
worktoy. Migration playbook & gotchas (reusable when bringing archived worktoy
code forward):

1. **'moreworktoy' -> 'worktoy'.** Old package name; same 'keenum' contents.
2. **'KeeMeta'-subclass enums must inherit 'Meta.keeNum', not be declared
   bare.** 'class FontWeightNum(KeeNum, metaclass=FontMeta)' FAILS. Correct:
   'class FontWeightNum(FontMeta.keeNum)'. 'Meta.keeNum' returns the unique
   root class built through that metaclass.
3. **Overloaded methods cannot run on a frozen 'KeeNum'/'KeeFlags' member.**
   Members are frozen; the dispatcher caches a bound method on the instance via
   setattr -> 'KeeWriteOnceError'. Make such methods plain (non-'overload') —
   e.g. 'Alignum.apply', 'FontWeightNum.apply', 'FontLineFlags.apply'.
4. **'KeeValueError' -> 'KeeResolveError'** (renamed in waitaminute.keenum).
5. **'strict=True' on Qt-typed overloads** (see §3) — or Qt aborts.
6. **Real bug fixed:** 'font_nums._font_family_space._collectFamilies()' spun a
   temp 'QApplication' to query 'QFontDatabase' at class-creation but its
   'finally' did 'delete(app)' unconditionally — killing the *running* app when
   one existed. Now only deletes the temp it created.
7. **Decouple at import:** 'WPainter' lazily imports 'WFont' (inside 'setFont').
8. **Relicense:** all archive files AGPL-3.0 -> Apache-2.0.

### 5b. The coverage push (to 100%) — see COVERAGE_HANDOFF.md
A full 'tests/' suite was written and driven to **100%** statement+branch
coverage (57 test classes, all green). Mirrors the package: plain 'BaseTest'
('test_*.py' / 'Test*') for value types, 'AppTest' ('run_*.py' / 'Run*') for
anything building a 'QObject'. Verify a value/branch with an offscreen
import-probe; never run the full suite yourself. The detailed remaining-gap
techniques live in COVERAGE_HANDOFF.md.

Dead code removed during this effort (zero importers / shadowed / unreachable):
'utils/qee_num/_build_font_families' (orphan module + its test),
'data/_abstract_field._clearCachedFunctions', the dead 'PaintButton'/
'ScratchWidget' '__init__'s (the inherited constructor dispatcher does the
work), plus earlier removals (FibonacciWidget, ListWidget, MoveHook, the
BoxDims/BoxModel/BoxColor trio, geom/dunders, '_paint_linear_map',
'_paint_rect', '_linear_plot'). 'App.__init__' argv-normalisation was extracted
to a testable static '_normalizeArgv'.

### 5c. A worktoy foot-gun, fixed at the source (rc11 -> rc12)
The coverage work surfaced a real worktoy sharp edge: in **rc11**, a subclass
that overrode an '@overload' method with a **plain** method had that method
**silently discarded** — 'LoadSpaceHook' compiled the inherited overloads into
a 'Dispatcher' and overwrote the subclass's plain attr in the namespace, so its
body never ran (no error, no warning). Benign for a pure 'super().__init__(...)'
pass-through, but dangerous for any real logic. This was **fixed in worktoy
rc12** (the author's own library): a subclass's plain override of an overloaded
method is now kept and runs correctly. worQt's deleted 'PaintButton'/
'ScratchWidget' '__init__'s stay deleted (they were redundant either way).

---

## 6. Current green state & how to verify

- Branch 'word_but_good'. The widget stack imports top-to-bottom and renders
  offscreen; the full test suite is green at **100% coverage** under worktoy
  rc12.
- Import probe (no app needed):
  ```
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src QT_QPA_PLATFORM=offscreen \
    python -c "import worQt; print('ok')"
  ```
- Full suite + coverage (user runs this): `./coverage_test.sh` (sets
  'WORQT_COVERAGE=1', runs 'coverage run -m worQt.qtest', combines, reports).
- Coverage config lives in 'pyproject.toml' ('[tool.coverage.*]'); there is no
  '.coveragerc'. 'worQt/__main__.py' (the demo entry) is omitted.

Note: nothing has been visually inspected on a real screen — only rendered to
pixmaps and asserted in tests.

---

## 7. Deferred / known TODO / next steps

- **Verify on screen.** Wire a window ('App' subclass with a '__window_class__',
  or 'MainWindow'/'TextWindow') and actually look at a 'PaintedWidget'/
  'TextWidget' so the box model is seen, not just rendered to a pixmap.
- **'data' JSON crack** still open: 'AbstractDocument' hardcodes JSON; make
  serialization pluggable (the original 'words' larp goal).
- **The 'words' larp** is only half-built: 'TextWindow' is a thin
  'QPlainTextEdit' + File menu with placeholder handlers. The next abstractions
  to lift into 'AbstractWindow': document binding ('TextDocument' fields <->
  widget), the dirty-star title, the unsaved-changes close guard, real
  'MainFile' use.
- **'layouts' rendering** ('GridLayout' cell placement) is tested for mapping/
  reset but not visually verified on screen.
- **Generalisation goal** (standing): lift reusable widgets/abstractions out of
  example apps into core worQt — the abstractions are the product.
