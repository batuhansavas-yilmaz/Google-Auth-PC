from types import SimpleNamespace

import customtkinter as ctk
import pytest

import google_auth_pc.app as app_module
from google_auth_pc import theme
from google_auth_pc.app import App
from google_auth_pc.config import Config
from google_auth_pc.models import Account
from google_auth_pc.storage import AccountStore
from google_auth_pc.ui.account_row import AccountRow
from google_auth_pc.ui.main_screen import MainScreen


@pytest.fixture()
def root():
    window = ctk.CTk()
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture(autouse=True)
def _restore_font_scale():
    original = theme.font_scale
    yield
    theme.set_font_scale(original)


class _Store:
    def __init__(self, accounts):
        self.accounts = list(accounts)
        self.save_calls = 0

    def load(self):
        return list(self.accounts)

    def save(self, accounts):
        self.save_calls += 1
        self.accounts = list(accounts)


class _App:
    def __init__(self, accounts, scale=1.0):
        self.store = _Store(accounts)
        self.font_scale = scale
        self.screen = None

    def show_screen(self, name):
        self.screen = name

    def show_main(self):
        self.screen = "main"

    def lock(self):
        self.screen = "lock"


class _WindowStub:
    def __init__(self, geometry="400x820+10+20"):
        self.resizable_calls = []
        self.geometry_calls = []
        self._geometry = geometry

    def resizable(self, width=None, height=None):
        if width is None:
            return (0, 0)
        self.resizable_calls.append((width, height))

    def geometry(self, spec=None):
        if spec is not None:
            self.geometry_calls.append(spec)
        return self._geometry

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080


def _geometry_stub(spec):
    stub = _WindowStub()
    stub.app_config = SimpleNamespace(get=lambda _key, default=None: spec)
    stub._parse_geometry = lambda value: App._parse_geometry(stub, value)
    return stub


def _accounts(count=10):
    return [
        Account(
            secret="JBSWY3DPEHPK3PXP",
            name=f"kullanici{index}@example.com",
            issuer=f"Servis {index}",
        )
        for index in range(count)
    ]


def _screen(root, count=10, scale=1.0):
    app = _App(_accounts(count), scale=scale)
    screen = MainScreen(root, app)
    screen.pack(fill="both", expand=True)
    root.update_idletasks()
    return screen, app


def test_main_screen_builds_single_column_rows_in_order(root):
    screen, _app = _screen(root, count=5)

    assert len(screen._rows) == 5
    assert all(isinstance(row, AccountRow) for row in screen._rows)
    assert all(row.master is screen._list for row in screen._rows)
    assert [row.account.name for row in screen._rows] == [
        f"kullanici{index}@example.com" for index in range(5)
    ]


def test_only_last_row_is_missing_its_divider(root):
    screen, _app = _screen(root, count=5)

    assert screen._rows[-1]._divider.grid_info() == {}
    assert all(row._divider.grid_info() != {} for row in screen._rows[:-1])


def test_reload_keeps_spacer_below_the_rows(root):
    screen, _app = _screen(root, count=3)

    screen.reload()

    slaves = screen._list.pack_slaves()
    assert slaves[0] is screen._rows[0]
    assert slaves[-1] is screen._spacer


def test_chrome_title_search_icons_and_fab(root):
    screen, app = _screen(root, count=0)

    assert screen._title.cget("text") == "Google Auth PC"
    assert screen._search.cget("placeholder_text") == "Hesap ara…"
    assert screen._fab.cget("text") == "+ Ekle"
    assert screen._fab.winfo_manager() == "place"
    assert screen._fab.place_info()["anchor"] == "se"
    assert screen._empty_label.winfo_manager() == "pack"

    screen._lock_button.invoke()
    assert app.screen == "lock"

    screen._settings_button.invoke()
    assert app.screen == "settings"

    screen._fab.invoke()
    assert app.screen == "import"


def test_search_filters_rows_and_shows_empty_state(root):
    screen, _app = _screen(root, count=3)

    screen._search.insert(0, "Servis 1")
    screen._on_query_change(None)
    assert [row.account.issuer for row in screen._rows] == ["Servis 1"]
    assert screen._empty_label.winfo_manager() == ""

    screen._search.delete(0, "end")
    screen._search.insert(0, "bulunamaz")
    screen._on_query_change(None)
    assert screen._rows == []
    assert screen._empty_label.winfo_manager() == "pack"


def test_delete_via_context_menu_saves_and_undo_restores_position(root):
    screen, app = _screen(root, count=4)
    original = list(screen._accounts)
    target = original[2]

    screen._rows[2]._menu.invoke(1)
    root.update_idletasks()

    assert screen._accounts == [account for account in original if account is not target]
    assert app.store.save_calls == 1
    assert app.store.accounts == screen._accounts
    assert screen._undo_bar.winfo_manager() == "place"
    assert len(screen._rows) == 3

    screen._undo_delete()
    root.update_idletasks()

    assert screen._accounts == original
    assert app.store.accounts == original
    assert app.store.save_calls == 2
    assert screen._undo_bar.winfo_manager() == ""
    assert len(screen._rows) == 4


def test_undo_bar_sits_above_the_fab(root):
    screen, _app = _screen(root, count=1)

    screen._show_undo(screen._accounts[0], 0)
    info = screen._undo_bar.place_info()

    assert screen._fab.winfo_manager() == "place"
    assert float(info["relwidth"]) == pytest.approx(1.0)
    assert int(info["y"]) <= -(screen._fab_height + screen._fab_margin)

    screen._clear_undo()
    assert screen._undo_bar.winfo_manager() == ""


def test_apply_fixed_size_disables_resizing_and_sets_400x820():
    stub = _WindowStub()

    App._apply_fixed_size(stub)

    assert stub.resizable_calls == [(False, False)]
    assert stub.geometry_calls == ["400x820"]


def test_saved_geometry_keeps_only_position():
    stub = _geometry_stub("900x1000+120+80")

    App._apply_saved_geometry(stub)

    assert stub.geometry_calls == ["400x820+120+80"]


def test_saved_position_is_clamped_to_the_screen():
    stub = _geometry_stub("900x1000+5000+5000")

    App._apply_saved_geometry(stub)

    assert stub.geometry_calls == ["400x820+1520+260"]


def test_invalid_saved_geometry_is_ignored():
    stub = _geometry_stub("bozuk")

    App._apply_saved_geometry(stub)

    assert stub.geometry_calls == []


def test_app_window_is_not_resizable(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module.tray, "start_tray", lambda **_kwargs: None)
    config = Config(tmp_path / "config.json")
    config.set("first_run_done", True)
    config.set("geometry", "900x1000+40+60")
    window = App(config, AccountStore(tmp_path / "accounts.dat"))
    try:
        window.attributes("-alpha", 0.0)
        window.update_idletasks()
        window.update()
        assert tuple(bool(value) for value in window.resizable()) == (False, False)
        geometry = window.geometry()
        assert geometry.split("+")[0] == "400x820"
        assert "+40+60" in geometry
    finally:
        window.destroy()
