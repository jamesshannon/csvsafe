"""CSVSafe menu bar app."""

from __future__ import annotations

import sys
from pathlib import Path

from csvsafe.input.clipboard_handler import handle_clipboard
from csvsafe.input.file_handler import handle_file
from csvsafe.platform import macos


def _require_appkit():
    try:
        import objc
        from AppKit import (
            NSApp,
            NSApplication,
            NSApplicationActivationPolicyAccessory,
            NSImage,
            NSMenu,
            NSMenuItem,
            NSStatusBar,
            NSVariableStatusBarItemLength,
        )
        from Foundation import NSObject
    except Exception as exc:  # pragma: no cover - runtime guard
        raise RuntimeError("CSVSafe app requires macOS PyObjC runtime") from exc

    return (
        objc,
        NSObject,
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSImage,
        NSMenu,
        NSMenuItem,
        NSStatusBar,
        NSVariableStatusBarItemLength,
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
        objc,
        NSObject,
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSImage,
        NSMenu,
        NSMenuItem,
        NSStatusBar,
        NSVariableStatusBarItemLength,
    ) = _require_appkit()

    class AppDelegate(NSObject):
        status_item = None

        def applicationDidFinishLaunching_(self, _notification):
            status_bar = NSStatusBar.systemStatusBar()
            self.status_item = status_bar.statusItemWithLength_(NSVariableStatusBarItemLength)
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

        @objc.signature("v@:@")
        def convertClipboard_(self, _sender):
            result = handle_clipboard()
            if result is not None:
                macos.notify("CSVSafe", f"Created {Path(result).name}", level="info")

        @objc.signature("v@:@")
        def openManual_(self, _sender):
            macos.open_url("https://github.com/jamesshannon/csvsafe/blob/main/MANUAL.md")

        @objc.signature("v@:@")
        def quitApp_(self, _sender):
            NSApp().terminate_(None)

        def application_openFiles_(self, app, filenames):
            if not filenames:
                return

            first = str(filenames[0])
            result = handle_file(first)
            if result is not None:
                macos.notify("CSVSafe", f"Created {Path(result).name}", level="info")

            if len(filenames) > 1:
                macos.notify(
                    "CSVSafe",
                    "Only one file is processed per conversion request in v1.",
                    level="warning",
                )

            app.replyToOpenOrPrint_(0)

        def application_openFile_(self, _app, filename):
            result = handle_file(str(filename))
            if result is not None:
                macos.notify("CSVSafe", f"Created {Path(result).name}", level="info")
                return True
            return False

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
