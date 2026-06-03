# Here are current issues with the CAD FEA opensees thing:

## Save/Rename

**Status: Hopefully solved.** `DrawWindow` now tracks `__file_path__`
(None while untitled). Ctrl+S `Save` writes silently to that file once
named, and routes to Rename while untitled. Ctrl+R `Rename...` opens the
file dialog, writes the scene to the chosen name, and *moves* the model
(removes the old file after the new write succeeds) rather than leaving a
copy. 'Save As' is gone. Open now records the path so later saves write
back without a dialog. The title bar shows the name ('untitled' until
named) with a `*` while dirty. Note: I made Rename a true move (deletes the
prior file); say the word if you'd rather it leave the old file in place.
Covered by seven new `TestDraw` methods (a `_patchFileDialog` helper stands
in for the modal): untitled title, save-while-untitled-runs-rename, named
save opens no dialog, rename moves the file, '.json' auto-append, cancelled
rename, and open-tracks-path.

Before a model is first saved, it's name is 'untitled', but we will not
save to this name. Thus, when we try to save when in this state, we
*actually* run the 'Rename' procedure instead.

After the model is given a name with the first save, future 'save'
procedures will not involve the file dialog but will simply involve
saving the current state to the file on the disk. If we do wish to save
to a different name, we run the 'Rename' procedure.

Thus, no more 'Save As'! It's 'Save' and 'Rename' only!

CTRL+S is the keybind to the 'Save' action.

CTRL+R is the keybind to the 'Rename' action.
