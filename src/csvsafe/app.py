"""CSVSafe menu bar app."""

from __future__ import annotations

import sys
from pathlib import Path

from csvsafe.input.clipboard_handler import handle_clipboard
from csvsafe.input.file_handler import handle_file
from csvsafe.platform import macos

_APP_DELEGATE = None


def _require_appkit():
    try:
        from AppKit import (
            NSApp,
            NSApplication,
            NSApplicationActivationPolicyAccessory,
            NSImage,
            NSMenu,
            NSMenuItem,
            NSStatusBar,
        )
        from Foundation import NSObject
    except Exception as exc:  # pragma: no cover - runtime guard
        raise RuntimeError("CSVSafe app requires macOS PyObjC runtime") from exc

    return (
        NSObject,
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSImage,
        NSMenu,
        NSMenuItem,
        NSStatusBar,
    )


def _resource_candidates(filename: str) -> list[Path]:
    candidates: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / filename)

    root = Path(__file__).resolve().parents[2]
    candidates.extend(
        [
            root / "assets" / filename,
            root / "packaging" / filename,
            Path.cwd() / "assets" / filename,
            Path.cwd() / "packaging" / filename,
        ]
    )
    return candidates


def _find_resource(filename: str) -> str | None:
    for candidate in _resource_candidates(filename):
        if candidate.exists():
            return str(candidate)
    return None


def main() -> None:
    (
        NSObject,
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSImage,
        NSMenu,
        NSMenuItem,
        NSStatusBar,
    ) = _require_appkit()

    class AppDelegate(NSObject):
        status_item = None

        def _process_path(self, path_str: str) -> bool:
            result = handle_file(path_str)
            if result is not None:
                macos.notify("CSVSafe", f"Created {Path(result).name}", level="info")
                return True
            return False

        def applicationDidFinishLaunching_(self, _notification):
            status_bar = NSStatusBar.systemStatusBar()
            self.status_item = status_bar.statusItemWithLength_(-1.0)
            self.status_item.button().setTitle_("CSVSafe")

            icon_path = _find_resource("csvsafe-menubar-glyph-18x18.png")
            if icon_path:
                image = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if image is not None:
                    image.setTemplate_(True)
                    self.status_item.button().setImage_(image)
                    self.status_item.button().setTitle_("")

            menu = NSMenu.alloc().init()

            convert_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Convert Clipboard", "convertClipboard:", ""
            )
            convert_item.setTarget_(self)
            menu.addItem_(convert_item)

            about_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "About CSVSafe", "openManual:", ""
            )
            about_item.setTarget_(self)
            menu.addItem_(about_item)

            menu.addItem_(NSMenuItem.separatorItem())

            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "quitApp:", "q")
            quit_item.setTarget_(self)
            menu.addItem_(quit_item)

            self.status_item.setMenu_(menu)

        def convertClipboard_(self, _sender):
            result = handle_clipboard()
            if result is not None:
                macos.notify("CSVSafe", f"Created {Path(result).name}", level="info")

        def openManual_(self, _sender):
            macos.open_url("https://github.com/jamesshannon/csvsafe/blob/main/MANUAL.md")

        def quitApp_(self, _sender):
            NSApp().terminate_(None)

        def application_openFiles_(self, app, filenames):
            if not filenames:
                return

            first = str(filenames[0])
            self._process_path(first)

            if len(filenames) > 1:
                macos.notify(
                    "CSVSafe",
                    "Only one file is processed per conversion request in v1.",
                    level="warning",
                )

            app.replyToOpenOrPrint_(0)

        def application_openFile_(self, _app, filename):
            return self._process_path(str(filename))

        def application_openURLs_(self, _app, urls):
            if not urls:
                return

            processed = False
            for url in urls:
                try:
                    path = url.path()
                except Exception:
                    continue
                if path and self._process_path(str(path)):
                    processed = True
                    break
            return processed

        def applicationShouldOpenUntitledFile_(self, _app):
            # Prevent macOS from showing an Open dialog when launching this menu bar app.
            return False

        def applicationOpenUntitledFile_(self, _app):
            return False

        def applicationShouldHandleReopen_hasVisibleWindows_(self, _app, _flag):
            return False

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    global _APP_DELEGATE
    _APP_DELEGATE = AppDelegate.alloc().init()
    app.setDelegate_(_APP_DELEGATE)

    app.run()


if __name__ == "__main__":
    main()
