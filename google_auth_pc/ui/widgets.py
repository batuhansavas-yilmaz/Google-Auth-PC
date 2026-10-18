import tkinter as tk
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc.totp import code_at, remaining_seconds

if TYPE_CHECKING:
    from google_auth_pc.models import Account

_CARD_FG = ("#f4f5f7", "#1b1e24")
_CARD_BORDER = ("#dfe3e8", "#2a2d33")
_NAME_TEXT = ("#1a1d22", "#e6e8ec")
_MUTED_TEXT = ("#6a7078", "#8b8f98")
_CODE_TEXT = ("#101319", "#ffffff")
_AVATAR_FG = ("#2b6df5", "#2b6df5")
_RING_TRACK = ("#d0d5db", "#3a3e46")
_RING_PROGRESS = ("#1a9a7a", "#2fbf9b")
_COPY_FG = ("#e8eaee", "#22252b")
_COPY_HOVER = ("#d9dde3", "#2b2f36")
_COPY_TEXT = ("#3a5f9e", "#9fb4d8")

_NAME_MAX_PX = 120
_ISSUER_MAX_PX = 120
_COPY_FEEDBACK_MS = 1500
_RING_SIZE = 28
_UNSET = object()


def _pick(light: str, dark: str) -> str:
    return dark if ctk.get_appearance_mode() == "Dark" else light


def _ellipsize(text: str, font, max_px: int) -> str:
    if font.measure(text) <= max_px:
        return text
    trimmed = text
    while trimmed and font.measure(trimmed + "…") > max_px:
        trimmed = trimmed[:-1]
    return trimmed + "…"


def _format_code(code: str) -> str:
    half = len(code) // 2
    return f"{code[:half]} {code[half:]}"


def _bind_right_click(widget, handler) -> None:
    widget.bind("<Button-3>", handler)
    for child in widget.winfo_children():
        _bind_right_click(child, handler)


class AccountCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        account: "Account",
        on_edit: Callable[["Account"], None] | None = None,
        on_delete: Callable[["Account"], None] | None = None,
    ):
        super().__init__(
            master,
            corner_radius=8,
            fg_color=_CARD_FG,
            border_width=1,
            border_color=_CARD_BORDER,
        )
        self.account = account
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._code: str | None = None
        self._last_code: str | None | object = _UNSET
        self._last_remaining: int | None = None
        self._copy_after_id: str | None = None
        self._ring: tk.Canvas | None = None
        self._ring_track: int | None = None
        self._ring_arc: int | None = None
        self._ring_seconds: int | None = None
        self._build()
        self.tick()

    def tick(self) -> None:
        code = code_at(self.account)
        if code != self._last_code:
            self._last_code = code
            self._code_label.configure(
                text="desteklenmiyor" if code is None else _format_code(code)
            )
        self._code = code
        if self._ring is None:
            return
        remaining = remaining_seconds(self.account)
        if remaining == self._last_remaining:
            return
        self._last_remaining = remaining
        self._sync_ring_colors()
        fraction = remaining / self.account.period
        self._ring.itemconfigure(self._ring_arc, extent=-359.99 * fraction)
        self._ring.itemconfigure(self._ring_seconds, text=str(remaining))

    def destroy(self) -> None:
        if self._copy_after_id is not None:
            self.after_cancel(self._copy_after_id)
            self._copy_after_id = None
        super().destroy()

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        initial = (self.account.issuer or self.account.name or "?").strip()[:1].upper()
        ctk.CTkLabel(
            self,
            text=initial,
            width=26,
            height=26,
            corner_radius=13,
            fg_color=_AVATAR_FG,
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=(9, 8), pady=9)

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew")
        name_font = ctk.CTkFont(size=12)
        ctk.CTkLabel(
            info,
            text=_ellipsize(self.account.name, name_font, _NAME_MAX_PX),
            font=name_font,
            text_color=_NAME_TEXT,
            anchor="w",
        ).pack(fill="x")
        if self.account.issuer:
            issuer_font = ctk.CTkFont(size=11)
            ctk.CTkLabel(
                info,
                text=_ellipsize(self.account.issuer, issuer_font, _ISSUER_MAX_PX),
                font=issuer_font,
                text_color=_MUTED_TEXT,
                anchor="w",
            ).pack(fill="x")

        self._code_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color=_CODE_TEXT,
            cursor="hand2",
        )
        self._code_label.grid(row=0, column=2, padx=(6, 4), sticky="e")
        self._code_label.bind("<Button-1>", lambda _event: self._copy())

        if self.account.type == "totp":
            self._ring = tk.Canvas(
                self,
                width=_RING_SIZE,
                height=_RING_SIZE,
                highlightthickness=0,
                bg=_pick(*_CARD_FG),
            )
            self._ring_track = self._ring.create_oval(
                4, 4, _RING_SIZE - 4, _RING_SIZE - 4,
                outline=_pick(*_RING_TRACK),
                width=3,
            )
            self._ring_arc = self._ring.create_arc(
                4, 4, _RING_SIZE - 4, _RING_SIZE - 4,
                start=90,
                extent=0,
                style="arc",
                outline=_pick(*_RING_PROGRESS),
                width=3,
            )
            center = _RING_SIZE // 2
            self._ring_seconds = self._ring.create_text(
                center, center,
                text="",
                fill=_pick(*_MUTED_TEXT),
                font=("Segoe UI", 8),
            )
            self._ring.grid(row=0, column=3, padx=(2, 4))

        self._copy_button = ctk.CTkButton(
            self,
            text="Kopyala",
            command=self._copy,
            width=80,
            height=26,
            corner_radius=7,
            fg_color=_COPY_FG,
            hover_color=_COPY_HOVER,
            border_width=1,
            border_color=_CARD_BORDER,
            text_color=_COPY_TEXT,
            font=ctk.CTkFont(size=10),
        )
        self._copy_button.grid(row=0, column=4, padx=(0, 4))
        if self.account.type != "totp":
            self._copy_button.configure(state="disabled")

        self._menu_button = ctk.CTkButton(
            self,
            text="\u22ef",
            command=self._menu_from_button,
            width=20,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            hover_color=_COPY_HOVER,
            text_color=_MUTED_TEXT,
            font=ctk.CTkFont(size=14),
        )
        self._menu_button.grid(row=0, column=5, padx=(0, 6))

        _bind_right_click(self, self._popup_menu)

        self._menu = tk.Menu(self, tearoff=0)
        if self._on_edit is not None:
            self._menu.add_command(label="Düzenle", command=self._edit)
        if self._on_delete is not None:
            self._menu.add_command(label="Sil", command=self._delete)

    def _sync_ring_colors(self) -> None:
        background = _pick(*_CARD_FG)
        if self._ring["bg"] == background:
            return
        self._ring.configure(bg=background)
        self._ring.itemconfigure(self._ring_track, outline=_pick(*_RING_TRACK))
        self._ring.itemconfigure(self._ring_arc, outline=_pick(*_RING_PROGRESS))
        self._ring.itemconfigure(self._ring_seconds, fill=_pick(*_MUTED_TEXT))

    def _copy(self) -> None:
        if self._code is None:
            return
        self.clipboard_clear()
        self.clipboard_append(self._code)
        self._copy_button.configure(text="Kopyalandı ✓")
        if self._copy_after_id is not None:
            self.after_cancel(self._copy_after_id)
        self._copy_after_id = self.after(_COPY_FEEDBACK_MS, self._end_copy_feedback)

    def _end_copy_feedback(self) -> None:
        self._copy_after_id = None
        if self.winfo_exists():
            self._copy_button.configure(text="Kopyala")

    def _menu_from_button(self) -> None:
        self._open_menu(
            self._menu_button.winfo_rootx(),
            self._menu_button.winfo_rooty() + self._menu_button.winfo_height(),
        )

    def _popup_menu(self, event) -> None:
        self._open_menu(event.x_root, event.y_root)

    def _open_menu(self, x: int, y: int) -> None:
        try:
            self._menu.tk_popup(x, y)
        finally:
            self._menu.grab_release()

    def _edit(self) -> None:
        if self._on_edit is not None:
            self._on_edit(self.account)

    def _delete(self) -> None:
        if self._on_delete is not None:
            self._on_delete(self.account)
