import math

import customtkinter as ctk

FONT_SCALE_STEPS: tuple[float, ...] = (0.9, 1.0, 1.15, 1.3)
_DEFAULT_FONT_SCALE = 1.0
_MIN_FONT_SIZE = 9

PALETTE: dict[str, tuple[str, str]] = {
    "bg": ("#f5f5f5", "#1f1f1f"),
    "surface": ("#ffffff", "#2a2a2a"),
    "surface_alt": ("#f1f3f4", "#333333"),
    "text": ("#1f1f1f", "#e8eaed"),
    "muted": ("#5f6368", "#9aa0a6"),
    "accent": ("#0b57d0", "#8ab4f8"),
    "on_accent": ("#ffffff", "#1f1f1f"),
    "divider": ("#dadce0", "#3c4043"),
    "danger": ("#b3261e", "#f2b8b5"),
    "success": ("#188038", "#81c995"),
    "row_hover": ("#f1f3f4", "#333333"),
    "search_fill": ("#e9eef6", "#2a2a2a"),
}

_MODES = ("system", "light", "dark")

font_scale = _DEFAULT_FONT_SCALE


def apply_theme(mode: str) -> None:
    ctk.set_appearance_mode(mode if mode in _MODES else "system")


def normalize_scale(scale: float) -> float:
    try:
        value = float(scale)
    except (TypeError, ValueError):
        return _DEFAULT_FONT_SCALE
    if not math.isfinite(value):
        return _DEFAULT_FONT_SCALE
    if value < FONT_SCALE_STEPS[0] or value > FONT_SCALE_STEPS[-1]:
        return _DEFAULT_FONT_SCALE
    return min(FONT_SCALE_STEPS, key=lambda step: abs(step - value))


def set_font_scale(scale: float) -> None:
    global font_scale
    font_scale = normalize_scale(scale)


def step_scale(current: float, delta: int) -> float:
    index = FONT_SCALE_STEPS.index(normalize_scale(current))
    index = max(0, min(len(FONT_SCALE_STEPS) - 1, index + int(delta)))
    return FONT_SCALE_STEPS[index]


def scaled(base: int, scale: float) -> int:
    return max(_MIN_FONT_SIZE, int(round(base * scale)))


def font(
    base: int,
    scale: float,
    weight: str = "normal",
    family: str = "Segoe UI",
) -> ctk.CTkFont:
    return ctk.CTkFont(family=family, size=scaled(base, scale), weight=weight)


def current() -> dict[str, str]:
    dark = ctk.get_appearance_mode().lower() == "dark"
    return {key: pair[1] if dark else pair[0] for key, pair in PALETTE.items()}
