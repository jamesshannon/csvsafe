from __future__ import annotations

from pathlib import Path

import csvsafe.app as app_mod


class _ObjCBase:
    @classmethod
    def alloc(cls):
        return cls()

    def init(self):
        return self


class _Button:
    def __init__(self):
        self.title = None
        self.image = None

    def setTitle_(self, title):
        self.title = title

    def setImage_(self, image):
        self.image = image


class _StatusItem:
    def __init__(self):
        self._button = _Button()
        self.menu = None

    def button(self):
        return self._button

    def setMenu_(self, menu):
        self.menu = menu


class _StatusBar:
    def __init__(self):
        self.last_length = None

    def statusItemWithLength_(self, length):
        self.last_length = length
        return _StatusItem()


class _NSStatusBar:
    _shared = _StatusBar()

    @classmethod
    def systemStatusBar(cls):
        return cls._shared


class _NSImage(_ObjCBase):
    def initWithContentsOfFile_(self, _path):
        return self

    def setTemplate_(self, _value):
        return None


class _NSMenu(_ObjCBase):
    def __init__(self):
        self.items = []

    def addItem_(self, item):
        self.items.append(item)


class _NSMenuItem(_ObjCBase):
    def __init__(self):
        self.title = None
        self.action = None
        self.key = None
        self.target = None

    def initWithTitle_action_keyEquivalent_(self, title, action, key):
        self.title = title
        self.action = action
        self.key = key
        return self

    def setTarget_(self, target):
        self.target = target

    @classmethod
    def separatorItem(cls):
        return cls.alloc().initWithTitle_action_keyEquivalent_("-", None, "")


class _FakeApp:
    def __init__(self):
        self.policy = None
        self.delegate = None
        self.run_called = False
        self.reply_codes = []
        self.terminated = False

    def setActivationPolicy_(self, policy):
        self.policy = policy

    def setDelegate_(self, delegate):
        self.delegate = delegate

    def run(self):
        self.run_called = True
        if self.delegate is not None:
            self.delegate.applicationDidFinishLaunching_(None)

    def replyToOpenOrPrint_(self, code):
        self.reply_codes.append(code)

    def terminate_(self, _sender):
        self.terminated = True


class _NSApplication:
    fake_app = _FakeApp()

    @classmethod
    def sharedApplication(cls):
        return cls.fake_app


def _install_fake_appkit(monkeypatch):
    fake_app = _FakeApp()
    _NSApplication.fake_app = fake_app

    def fake_nsapp():
        return fake_app

    monkeypatch.setattr(
        app_mod,
        "_require_appkit",
        lambda: (
            _ObjCBase,
            fake_nsapp,
            _NSApplication,
            "ACCESSORY",
            _NSImage,
            _NSMenu,
            _NSMenuItem,
            _NSStatusBar,
        ),
    )
    monkeypatch.setattr(app_mod, "_find_resource", lambda _name: None)
    return fake_app


def test_main_keeps_delegate_and_creates_status_item(monkeypatch):
    fake_app = _install_fake_appkit(monkeypatch)
    monkeypatch.setattr(app_mod, "handle_file", lambda _path: None)
    monkeypatch.setattr(app_mod.macos, "notify", lambda *args, **kwargs: None)

    monkeypatch.setattr(app_mod.sys, "argv", ["csvsafe-menubar"]) 
    app_mod.main()

    delegate = app_mod._APP_DELEGATE
    assert delegate is not None
    assert fake_app.delegate is delegate
    assert fake_app.run_called is True
    assert delegate.status_item is not None
    assert delegate.applicationShouldOpenUntitledFile_(fake_app) is False
    assert delegate.applicationShouldHandleReopen_hasVisibleWindows_(fake_app, True) is False


def test_open_handlers_process_paths_and_reply(monkeypatch, tmp_path: Path):
    fake_app = _install_fake_appkit(monkeypatch)

    processed: list[str] = []
    notices: list[str] = []

    def fake_handle_file(path: str):
        processed.append(path)
        return Path(path).with_suffix(".xlsx")

    monkeypatch.setattr(app_mod, "handle_file", fake_handle_file)
    monkeypatch.setattr(app_mod.macos, "notify", lambda _t, msg, **_k: notices.append(msg))
    monkeypatch.setattr(app_mod.sys, "argv", ["csvsafe-menubar"])

    app_mod.main()
    delegate = app_mod._APP_DELEGATE

    csv1 = tmp_path / "one.csv"
    csv2 = tmp_path / "two.csv"
    csv1.write_text("a,b\n1,2\n", encoding="utf-8")
    csv2.write_text("a,b\n3,4\n", encoding="utf-8")

    assert delegate.application_openFile_(fake_app, str(csv1)) is True

    delegate.application_openFiles_(fake_app, [str(csv1), str(csv2)])
    assert fake_app.reply_codes[-1] == 0

    class _URL:
        def __init__(self, value: str):
            self._value = value

        def path(self):
            return self._value

    assert delegate.application_openURLs_(fake_app, [_URL(str(csv2))]) is True
    assert any("Only one file is processed" in msg for msg in notices)
    assert processed == [str(csv1), str(csv1), str(csv2)]


def test_main_processes_file_argument_fallback(monkeypatch, tmp_path: Path):
    fake_app = _install_fake_appkit(monkeypatch)
    seen: list[str] = []

    def fake_handle_file(path: str):
        seen.append(path)
        return Path(path).with_suffix(".xlsx")

    monkeypatch.setattr(app_mod, "handle_file", fake_handle_file)
    monkeypatch.setattr(app_mod.macos, "notify", lambda *args, **kwargs: None)

    csv_path = tmp_path / "argv.csv"
    csv_path.write_text("x,y\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(app_mod.sys, "argv", ["csvsafe-menubar", str(csv_path)])

    app_mod.main()

    assert fake_app.run_called is True
    assert seen == [str(csv_path)]
