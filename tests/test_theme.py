import json

import pytest

from google_auth_pc import theme
from google_auth_pc.app import App
from google_auth_pc.config import Config

_PALETTE_KEYS = {
    "bg",
    "surface",
    "surface_alt",
    "text",
    "muted",
    "accent",
    "on_accent",
    "divider",
    "danger",
    "success",
    "row_hover",
    "search_fill",
}


@pytest.fixture(autouse=True)
def _restore_font_scale():
    if not hasattr(theme, "font_scale"):
        yield
        return
    original = theme.font_scale
    yield
    theme.set_font_scale(original)


def _write_config(tmp_path, data):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_font_scale_steps():
    assert theme.FONT_SCALE_STEPS == (0.9, 1.0, 1.15, 1.3)


def test_scaled_rounds_to_nearest_pixel():
    assert theme.scaled(18, 0.9) == 16
    assert theme.scaled(18, 1.3) == 23
    assert theme.scaled(18, 1.15) == 21


def test_scaled_never_goes_below_nine():
    assert theme.scaled(10, 0.9) == 9
    assert theme.scaled(2, 1.0) == 9


def test_step_scale_walks_steps_and_clamps():
    assert theme.step_scale(1.0, 1) == 1.15
    assert theme.step_scale(1.3, 1) == 1.3
    assert theme.step_scale(0.9, -1) == 0.9
    assert theme.step_scale(1.15, -1) == 1.0
    assert theme.step_scale(1.0, 0) == 1.0


def test_set_font_scale_updates_module_state():
    theme.set_font_scale(1.15)
    assert theme.font_scale == 1.15


def test_set_font_scale_rejects_invalid_value():
    theme.set_font_scale(2.0)
    assert theme.font_scale == 1.0


def test_config_font_scale_defaults_to_one(tmp_path):
    assert Config(tmp_path / "config.json").get("font_scale") == 1.0


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        (1.15, 1.15),
        (1.1, 1.15),
        (0.9, 0.9),
        (2.0, 1.0),
        (None, 1.0),
        ("x", 1.0),
    ],
)
def test_config_font_scale_is_normalized(tmp_path, stored, expected):
    path = _write_config(tmp_path, {"font_scale": stored})
    assert Config(path).get("font_scale") == expected


def test_palette_has_pairs_for_every_token():
    assert set(theme.PALETTE) == _PALETTE_KEYS
    for pair in theme.PALETTE.values():
        assert isinstance(pair, tuple)
        assert len(pair) == 2
        assert all(
            isinstance(color, str) and len(color) == 7 and color.startswith("#")
            for color in pair
        )


def test_palette_uses_spec_colors():
    assert theme.PALETTE["bg"] == ("#f5f5f5", "#1f1f1f")
    assert theme.PALETTE["surface"] == ("#ffffff", "#2a2a2a")
    assert theme.PALETTE["text"] == ("#1f1f1f", "#e8eaed")
    assert theme.PALETTE["muted"] == ("#5f6368", "#9aa0a6")
    assert theme.PALETTE["accent"] == ("#0b57d0", "#8ab4f8")


def test_current_resolves_light_mode(monkeypatch):
    monkeypatch.setattr(theme.ctk, "get_appearance_mode", lambda: "Light")
    resolved = theme.current()
    assert set(resolved) == _PALETTE_KEYS
    assert resolved["bg"] == "#f5f5f5"
    assert all(isinstance(color, str) for color in resolved.values())


def test_current_resolves_dark_mode(monkeypatch):
    monkeypatch.setattr(theme.ctk, "get_appearance_mode", lambda: "Dark")
    resolved = theme.current()
    assert resolved["bg"] == "#1f1f1f"
    assert resolved["accent"] == "#8ab4f8"


def test_font_factory_scales_size_and_passes_options(monkeypatch):
    captured = {}

    class _FakeFont:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(theme.ctk, "CTkFont", _FakeFont)

    assert isinstance(theme.font(18, 1.3), _FakeFont)
    assert captured == {"family": "Segoe UI", "size": 23, "weight": "normal"}

    theme.font(14, 1.0, weight="bold", family="Consolas")
    assert captured == {"family": "Consolas", "size": 14, "weight": "bold"}


class _FakeScreen:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


class _FakeConfig:
    def __init__(self):
        self.values = {}
        self.saves = 0

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        self.saves += 1


class _FakeApp:
    def __init__(self, locked, active):
        self._locked = locked
        self._active_screen = active
        self._screens = {"lock": _FakeScreen(), "main": _FakeScreen()}
        self.app_config = _FakeConfig()
        self.shown = []
        self.builds = 0

    def _build_screens(self):
        self.builds += 1
        self._screens = {"lock": _FakeScreen(), "main": _FakeScreen()}

    def show_screen(self, name):
        self.shown.append(name)


def test_app_set_font_scale_persists_rebuilds_and_keeps_lock():
    fake = _FakeApp(locked=True, active="lock")
    old_screens = list(fake._screens.values())

    App.set_font_scale(fake, 1.15)

    assert theme.font_scale == 1.15
    assert App.font_scale.fget(fake) == 1.15
    assert fake.app_config.values["font_scale"] == 1.15
    assert fake.app_config.saves == 1
    assert all(screen.destroyed for screen in old_screens)
    assert fake.builds == 1
    assert fake.shown == ["lock"]


def test_app_set_font_scale_keeps_active_screen_when_unlocked():
    fake = _FakeApp(locked=False, active="settings")

    App.set_font_scale(fake, 1.3)

    assert fake._locked is False
    assert fake.shown == ["settings"]
    assert fake.app_config.values["font_scale"] == 1.3


def test_main_screen_destroy_cancels_tick(monkeypatch):
    from google_auth_pc.ui import main_screen

    screen = object.__new__(main_screen.MainScreen)
    cancelled = []
    screen._tick_id = "tick-job"
    screen.after_cancel = cancelled.append
    monkeypatch.setattr(main_screen.ctk.CTkFrame, "destroy", lambda self: None)

    main_screen.MainScreen.destroy(screen)

    assert cancelled == ["tick-job"]
    assert screen._tick_id is None
