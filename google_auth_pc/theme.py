import customtkinter as ctk

_MODES = ("system", "light", "dark")


def apply_theme(mode: str) -> None:
    ctk.set_appearance_mode(mode if mode in _MODES else "system")
