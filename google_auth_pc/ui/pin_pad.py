from collections.abc import Callable

import customtkinter as ctk

PIN_LENGTH = 6

_DOT_FILLED = ("#2b6df5", "#2b6df5")
_DOT_EMPTY = ("#c6cbd3", "#3a3e46")
_KEY_FG = ("#e8eaee", "#22252b")
_KEY_HOVER = ("#d9dde3", "#2b2f36")
_KEY_BORDER = ("#d0d5db", "#33363d")
_KEY_TEXT = ("#3a3f46", "#c7cad1")
_MUTED_TEXT = ("#5f6570", "#8b8f98")
_TITLE_TEXT = ("#1c1f24", "#e6e8ec")

_BACKSPACE_KEY = "\u232b"


class PinPad(ctk.CTkFrame):
    def __init__(self, master, on_complete: Callable[[str], None], title: str):
        super().__init__(master, fg_color="transparent")
        self._on_complete = on_complete
        self._digits = ""
        self._dots: list[ctk.CTkLabel] = []
        self._build(title)

    def reset(self) -> None:
        self._digits = ""
        self._update_dots()

    def _build(self, title: str) -> None:
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=_TITLE_TEXT,
        ).pack(pady=(0, 12))

        dots = ctk.CTkFrame(self, fg_color="transparent")
        dots.pack(pady=(0, 14))
        for _ in range(PIN_LENGTH):
            dot = ctk.CTkLabel(dots, text="\u25cf", width=12, font=ctk.CTkFont(size=12))
            dot.pack(side="left", padx=4)
            self._dots.append(dot)

        keypad = ctk.CTkFrame(self, fg_color="transparent")
        keypad.pack()
        rows = (
            ("1", "2", "3"),
            ("4", "5", "6"),
            ("7", "8", "9"),
            ("", "0", _BACKSPACE_KEY),
        )
        for row_index, row in enumerate(rows):
            for column_index, key in enumerate(row):
                if not key:
                    continue
                if key == _BACKSPACE_KEY:
                    command = self._backspace
                    text_color = _MUTED_TEXT
                else:
                    command = lambda value=key: self._press(value)
                    text_color = _KEY_TEXT
                ctk.CTkButton(
                    keypad,
                    text=key,
                    command=command,
                    width=56,
                    height=42,
                    corner_radius=8,
                    fg_color=_KEY_FG,
                    hover_color=_KEY_HOVER,
                    border_width=1,
                    border_color=_KEY_BORDER,
                    text_color=text_color,
                    font=ctk.CTkFont(size=14),
                ).grid(row=row_index, column=column_index, padx=3, pady=3)

        self._update_dots()

    def _press(self, digit: str) -> None:
        if len(self._digits) >= PIN_LENGTH:
            return
        self._digits += digit
        self._update_dots()
        if len(self._digits) == PIN_LENGTH:
            self._on_complete(self._digits)

    def _backspace(self) -> None:
        if not self._digits:
            return
        self._digits = self._digits[:-1]
        self._update_dots()

    def _update_dots(self) -> None:
        for index, dot in enumerate(self._dots):
            filled = index < len(self._digits)
            dot.configure(text_color=_DOT_FILLED if filled else _DOT_EMPTY)
