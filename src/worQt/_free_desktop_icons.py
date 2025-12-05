"""
This file provides a list of standard Free Desktop icons.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

freedesktopIcons: list[str] = [
    # Application
    "application-exit", "document-new", "document-open",
    "document-save", "document-save-as", "document-print",
    "document-properties", "preferences-system",
    "preferences-desktop",

    # Edit
    "edit-cut", "edit-copy", "edit-paste",
    "edit-undo", "edit-redo", "edit-delete", "edit-find",

    # View / Navigation
    "go-home", "go-up", "go-down",
    "go-previous", "go-next", "view-refresh",
    "zoom-in", "zoom-out", "zoom-fit-best",

    # Actions / System
    "system-shutdown", "system-reboot", "system-lock-screen",
    "system-search", "help-about", "help-contents",

    # Media
    "media-playback-start", "media-playback-pause",
    "media-playback-stop", "media-seek-forward",
    "media-seek-backward", "media-record",
    "audio-volume-muted", "audio-volume-low",
    "audio-volume-medium", "audio-volume-high",

    # Folder / File
    "folder", "folder-open", "user-home",
    "trash", "network-workgroup",
    "drive-harddisk", "drive-optical",
    "drive-removable-media",
]
