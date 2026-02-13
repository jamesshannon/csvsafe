"""macOS-specific integrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import uuid4


@dataclass
class ClipboardContent:
    is_text: bool
    text: str


def _require_darwin_modules() -> tuple[object, object, object, object, object]:
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeString, NSWorkspace
        from Foundation import NSURL
        from UserNotifications import (
            UNAuthorizationOptionAlert,
            UNAuthorizationOptionBadge,
            UNAuthorizationOptionSound,
            UNMutableNotificationContent,
            UNNotificationRequest,
            UNUserNotificationCenter,
        )
    except Exception as exc:  # pragma: no cover - guarded by platform
        raise RuntimeError("macOS APIs are unavailable") from exc

    return (
        NSPasteboard,
        NSPasteboardTypeString,
        NSWorkspace,
        NSURL,
        (
            UNAuthorizationOptionAlert,
            UNAuthorizationOptionBadge,
            UNAuthorizationOptionSound,
            UNMutableNotificationContent,
            UNNotificationRequest,
            UNUserNotificationCenter,
        ),
    )


def open_file(path: str | Path) -> None:
    _, _, NSWorkspace, _, _ = _require_darwin_modules()
    NSWorkspace.sharedWorkspace().openFile_(str(path))


def open_url(url: str) -> None:
    _, _, NSWorkspace, NSURL, _ = _require_darwin_modules()
    NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(url))


def read_clipboard_text() -> ClipboardContent:
    NSPasteboard, NSPasteboardTypeString, _, _, _ = _require_darwin_modules()
    pasteboard = NSPasteboard.generalPasteboard()
    value = pasteboard.stringForType_(NSPasteboardTypeString)
    if value is None:
        return ClipboardContent(is_text=False, text="")
    return ClipboardContent(is_text=True, text=str(value))


def notify(title: str, message: str, *, level: Literal["info", "warning", "error"] = "info") -> None:
    del level
    _, _, _, _, notification_parts = _require_darwin_modules()
    (
        UNAuthorizationOptionAlert,
        UNAuthorizationOptionBadge,
        UNAuthorizationOptionSound,
        UNMutableNotificationContent,
        UNNotificationRequest,
        UNUserNotificationCenter,
    ) = notification_parts

    center = UNUserNotificationCenter.currentNotificationCenter()
    options = UNAuthorizationOptionAlert | UNAuthorizationOptionBadge | UNAuthorizationOptionSound
    center.requestAuthorizationWithOptions_completionHandler_(options, None)

    content = UNMutableNotificationContent.alloc().init()
    content.setTitle_(title)
    content.setBody_(message)

    request = UNNotificationRequest.requestWithIdentifier_content_trigger_(str(uuid4()), content, None)
    center.addNotificationRequest_withCompletionHandler_(request, None)
