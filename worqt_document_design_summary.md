# worQt: Document / Project / File Layer Design Summary

Handoff notes for continuing in Claude Code. Captures the decisions, the
invariants we settled, and the questions still open. Written as a design
record, not a spec.

## Context and method

worQt is a PySide6 binding layer on top of `worktoy`. The generic worQt
components are being discovered bottom-up: build disposable "Toy" apps,
observe which components turn out to be needed generically, and harvest
those into the framework. The Toys are scaffolding; the abstractions are
the product.

Terminology:

- **Toy**: a specific throwaway example app (e.g. a CAD-larp).
- **BaseApp** (a.k.a. `AbstractApplication`): worQt's `QApplication`
  subclass, ships in the box, knows nothing about any specific Toy.
- **ToyApp**: per-Toy subclass of `BaseApp`.
- **ToyX**: per-Toy subclass of a generic worQt component `X`.

First Toy (CAD-larp) was deliberately deflated to a 2D canvas where you
place nodes and connect them, no FEA, no solver. Its only job is to
exercise the document machinery.

## The file layer

### Identity must be stored, not computed

The original `AbstractFile` computed `filePath` as the next *free* untitled
name on every read. Two fatal consequences:

- The path slid off the file the instant it was saved (next read returned
  the next free slot).
- `load` could never read an existing file, because the computed path was
  by construction the first non-existent slot.

Fix: identity is committed once and held. `fileName` mints the next free
untitled name on first access, stores it, and returns the stored value
thereafter. `filePath` derives from the stored `dirPath` + `fileName`.
Untitled-name minting is only a seed for a never-saved file, not the
answer to "where do I live".

### Three layers, each doing only its own job

Settled split for the file-access machinery:

- **Getter**: pure. Returns the recorded path. No filesystem reads, no
  side effects, same answer every time. A getter that calls
  `os.path.exists` / `isdir` is impure (its result depends on volatile
  disk state and can raise on a read), so those checks do not belong in
  the getter.
- **Setter / preSet**: fail-fast input validation. Reject a non-absolute
  path; reject a path that exists as a non-directory. No filesystem
  mutation. Validation of the incoming value runs unconditionally (it does
  not depend on the prior value); only the idempotence `SkipSet`
  comparison belongs in the branch that needs the existing value.
- **`save`**: the single write-time event. `os.makedirs(self.dirPath,
  exist_ok=True)` happens here, right before opening the handle, because
  this is the only place creation is required and the only place it can be
  guaranteed (the filesystem is volatile; a dir created at assignment can
  be gone by save time).

Bug caught along the way: putting the `isdir` check inside the `else` of
the idempotence try/except gated it behind "a dirPath was already set", so
the first assignment (the common case) skipped validation entirely.
Validation must run outside that branch.

### Atomic save

`AbstractFile.save` should write to a sibling temp file and then
`os.replace` it over the target. Rename is atomic at the filesystem level,
so a reader always sees either the complete old file or the complete new
file, never a torn one, and a crash mid-write leaves the real file
untouched. The temp must sit in the *same directory* as the target (rename
is only atomic within one filesystem).

`fsync` (file + containing directory) for power-loss durability is
deliberately *not* added for the Toy: it costs real latency, doing it
correctly requires syncing the directory too and is platform-specific, and
atomic rename alone already guarantees no corruption and survival of app
crashes. Without `fsync` a power loss costs at most the last few seconds of
edits and never corrupts the file. Add the full version only when the user
is *promised* durability (financial, database, irreplaceable data).

## Document vs Project: composition, not inheritance

`Project` is NOT a subclass of `Document`. A Document is one file; a Project
is one folder of many files. Subclassing would force the Project to inherit
a single-file interface (`filePath`, `save(cb)` opening one handle) it
cannot honor, which is a Liskov violation: a function taking a `Document`
and calling `save(cb)` would break on a `Project`.

What is genuinely shared is the **role** (identity, dirty state, lifecycle
verbs as concepts), not the file mechanism. So the shape is a shared base
both inherit, with file-vs-folder mechanics living in each.

### Project structure

- `Project` HAS-A `mainFile` (an `AbstractFile`) that points at a real
  **main/manifest file inside the folder** (e.g. `myproj/project.json`).
  This makes `mainFile.filePath` an honest file (save/load work) and
  `mainFile.dirPath` the honest project folder. Nothing is phantom.
- `Project` HAS-A set of member files, each a `LocalFile`.
- The main file gets a **deliberate name** (fixed convention or derived
  from the project name), not the untitled counter.
- "New project" is folder-level minting (free folder name in the parent,
  create it, drop the fixed main file inside), one level up from
  `AbstractFile`'s file-level minting. This divergence in `new` is exactly
  why Project is a sibling, not a subclass.

### LocalFile

`LocalFile(AbstractFile)`: this inheritance IS correct, because a local
file genuinely is one file (save/load apply). The only difference is
ownership of the directory:

- The directory has exactly one owner: `mainFile` (stored, settable, moves
  on Save-As).
- `LocalFile` **derives** its `dirPath` from `mainFile`, never stores its
  own. If each member stored its own copy, "same dir as mainFile" would be
  N drifting copies and the first project move would orphan every member.
- `LocalFile.dirPath` GET delegates to `mainFile.dirPath`; SET fails loud
  (you relocate the project, not a member).
- Knock-on: `filePath` SET on a `LocalFile` may only *rename* (change the
  leaf within the owned dir); a `filePath` whose directory is not the
  project dir must be rejected.

## Planned refactor: extract a neutral base

`AbstractFile` currently organizes both the location/identity machinery and
the file-specific I/O. The location/identity machinery should move down
into a shared base so a directory flavor can share it.

```
AbstractPath : dirPath, name, path  (+ GET/SET/preSet, nextName minting)
  AbstractFile(AbstractPath) : extension, defaultNameSpec, save(cb), load(cb)
    LocalFile(AbstractFile)  : dirPath delegated to mainFile
  AbstractDir(AbstractPath)  : member orchestration (later)
```

Critical trap to avoid in the extraction: **name the shared members
neutrally**. The leaf is `name`, not `fileName`; the full location is
`path`, not `filePath`. If the base says "file", a directory flavor
inherits file-shaped names it never uses (phantom surface, one level up).
`AbstractFile` may expose `fileName` / `filePath` as thin aliases over the
base's `name` / `path` if the file vocabulary reads nicely.

The base must NOT define `save` / `load` at all, not even abstractly with a
`cb` signature. You never apply a callback to a directory (you cannot open
a folder as a handle). A directory's `save` takes no callback: it ensures
the folder exists and tells each member file to save itself. The verb name
may be shared; the signature is not, so persistence lives per-flavor, not
in the base. The base shares identity and location only, no I/O.

Test for a correct extraction: could `AbstractDir` inherit the base without
inheriting a single file-named member it has to ignore?

## AbstractDocument

`AbstractDocument` is the base for `ToyDocument`s. It HAS-A `mainFile`.

### Single source of truth

`AbstractDocument` IS the mutable application data. For the CAD-larp, the
list of active nodes lives on the document and nowhere else. This is a
**document-vs-view** principle, not base-vs-leaf: the document object owns
the data, the view (canvas / `QGraphicsScene`) owns none. The view is a
pure projection: it renders from the document, and edits round-trip through
the document (mutate, document emits change, view re-renders). The common
Qt failure is letting scene items hold authoritative state; then dragging
an item makes the item the truth and the document stale.

### Attributes

`mainFile` already answers "where do I live", so do NOT add path/dir/name
state to the document. Expose `displayName` and `isUntitled` as derived
Fields over `mainFile`.

Genuinely new state on the document:

- **the model**: the actual content (the nodes). This is the reason the
  document exists; `mainFile` is only persistence.
- **a modification source**: drives the save prompt and title-bar asterisk.

Serialization is *methods*, not attributes: the document defines
`_writeModel(handle)` / `_readModel(handle)` and feeds them as the `cb` to
`mainFile.save` / `load`. Possibly also `_clear()` (for New) and
`isEmpty`. The leaf implements these for its format.

Assume `AbstractDocument` is a `QObject` so it can emit `modificationChanged`
etc., consistent with `BaseApp`.

### Field-agnostic base, and dirty tracking over unknown fields

The base cannot predict the model's fields, and should not try. The leaf
(`ToyDocument`) declares its own `AttriBox` fields; this still satisfies
single-source-of-truth because the data lives on the document object. The
base touches the unknown model only through the abstract seam above, never
by field name.

The tricky part: the base cannot watch arbitrary subclass fields, so
mutations need a uniform channel the base owns. Two options:

- **Command channel (preferred)**: every edit is a command pushed to a
  `QUndoStack` the base holds. Dirty falls out as `not isClean()`, and the
  base never needs to know the fields. `cleanChanged(bool)` becomes the
  modification signal, with free re-clean when the user undoes back to the
  last save point.
- **Explicit touch**: the leaf calls a base `markModified()` (or routes
  each field's set-notifier to it). Works, but it is per-field discipline
  the base cannot enforce, so it rots the moment someone adds a field and
  forgets.

The field-unpredictability is the argument for the command channel: a
generic base manages an unknown-shaped model only if all changes funnel
through one door it controls.

## Open decisions

1. **Undo in or out.** This is the gating decision. "In" means a
   `QUndoStack` is the modification source and the command channel solves
   field-agnostic dirty tracking cleanly. "Out" means committing to the
   fragile `markModified` discipline and a plain `bool` flag. Current lean:
   in.
2. **Base extraction timing.** Decided to extract `AbstractPath`; confirm
   whether to do it now or once `AbstractDir` / Project actually forces the
   shared surface into view.
3. **Autosave.** Deferred. It is a real feature (timer, cache dir via
   `QStandardPaths`, stable per-document id, launch-time orphan scan,
   explicit lifetime), not a Toy concern. The hook is known: the `modified`
   signal triggers it. Build it the day a real app needs it.

## Code style (worQt / worktoy conventions)

- 77-character line limit, 2-space indentation, no exceptions.
- `from __future__ import annotations` at the top of every file.
- Full type hints, including `-> None`.
- NumPy-style docstrings; one-line form if it fits in 77 chars with
  indentation, otherwise the multi-line form.
- No em-dashes anywhere.
- Apache-2.0 header dated 2026, sole copyright holder Asger Jon Vistisen.
- Class banner order: STATIC METHODS, NAMESPACE, GETTERS, SETTERS,
  NOTIFIERS, Python API, CONSTRUCTORS, DOMAIN SPECIFIC, OPTIONAL METHODS,
  REQUIRED METHODS, PARENT METHODS, PUBLIC METHODS.
- First-argument naming: `self` / `cls` / `mcls`.
- 100% branch coverage as a hard discipline; one class per file.
