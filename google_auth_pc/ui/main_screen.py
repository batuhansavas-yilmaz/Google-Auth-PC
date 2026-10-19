import tkinter
import unicodedata
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc import theme
from google_auth_pc.models import Account
from google_auth_pc.ui.account_row import AccountRow

if TYPE_CHECKING:
    from google_auth_pc.app import App

_SEARCH_PLACEHOLDER = "Hesap ara…"
_EMPTY_TEXT = "Henüz hesap yok — + Ekle ile başla"
_NO_MATCH_TEXT = "Eşleşen hesap yok"
_TICK_MS = 250
_UNDO_VISIBLE_MS = 5000
_BASE_FAB_HEIGHT = 56
_BASE_MARGIN = 16
_BASE_SPACER = 96
_ICON_FONT = "Segoe MDL2 Assets"
_LOCK_GLYPH = "\uE72E"
_SETTINGS_GLYPH = "\uE713"
_SEARCH_GLYPH = "\uE721"

_PRIMARY_FG = theme.PALETTE["accent"]
_PRIMARY_HOVER = ("#1f5cd6", "#a8c7fa")
_ON_ACCENT = theme.PALETTE["on_accent"]
_MUTED_TEXT = theme.PALETTE["muted"]


def filter_accounts(accounts: list[Account], query: str) -> list[Account]:
    folded = _fold(query)
    if not folded:
        return list(accounts)
    return [
        account
        for account in accounts
        if folded in _fold(account.name) or folded in _fold(account.issuer)
    ]


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_marks.replace("ı", "i").strip()


class _Tooltip:
    def __init__(self, widget, text: str, scale: float):
        self._widget = widget
        self._text = text
        self._scale = scale
        self._job: str | None = None
        self._window: tkinter.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        widget.bind("<Destroy>", self._on_destroy, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel_job()
        try:
            self._job = self._widget.after(450, self._show)
        except tkinter.TclError:
            self._job = None

    def _cancel_job(self) -> None:
        job = self._job
        self._job = None
        if job is None:
            return
        try:
            self._widget.after_cancel(job)
        except tkinter.TclError:
            pass

    def _show(self) -> None:
        self._job = None
        if self._window is not None:
            return
        try:
            if not self._widget.winfo_exists():
                return
            palette = theme.current()
            tip = tkinter.Toplevel(self._widget)
            tip.wm_overrideredirect(True)
            tkinter.Label(
                tip,
                text=self._text,
                background=palette["surface"],
                foreground=palette["text"],
                padx=theme.scaled(8, self._scale),
                pady=theme.scaled(3, self._scale),
                font=("Segoe UI", theme.scaled(10, self._scale)),
            ).pack()
            tip.update_idletasks()
            x = (
                self._widget.winfo_rootx()
                + self._widget.winfo_width() // 2
                - tip.winfo_width() // 2
            )
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
            tip.wm_geometry(f"+{x}+{y}")
            self._window = tip
        except tkinter.TclError:
            self._window = None

    def _hide(self, _event=None) -> None:
        self._cancel_job()
        window = self._window
        self._window = None
        if window is not None:
            try:
                window.destroy()
            except tkinter.TclError:
                pass

    def _on_destroy(self, _event=None) -> None:
        self._hide()


class MainScreen(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master, fg_color=theme.PALETTE["bg"])
        self.app = app
        self._accounts: list[Account] = []
        self._rows: list[AccountRow] = []
        self._tick_id: str | None = None
        self._undo_job: str | None = None
        self._undo_account: Account | None = None
        self._undo_index: int | None = None
        self._build()
        self.reload()

    def reload(self) -> None:
        self._accounts = self.app.store.load()
        self._render()

    def tick(self) -> None:
        self._tick_id = self.after(_TICK_MS, self.tick)
        for row in self._rows:
            row.tick()

    def destroy(self) -> None:
        for job in ("_tick_id", "_undo_job"):
            self._cancel_job(job)
        self._clear_undo()
        super().destroy()

    def _cancel_job(self, attribute: str) -> None:
        job = getattr(self, attribute, None)
        if job is None:
            return
        setattr(self, attribute, None)
        try:
            self.after_cancel(job)
        except tkinter.TclError:
            pass

    def _build(self) -> None:
        palette = theme.PALETTE
        scale = self.app.font_scale

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(
            fill="x",
            padx=(theme.scaled(20, scale), theme.scaled(12, scale)),
            pady=(theme.scaled(10, scale), 0),
        )
        self._title = ctk.CTkLabel(
            top,
            text="Google Auth PC",
            text_color=palette["text"],
            font=theme.font(20, scale, weight="bold"),
            anchor="w",
        )
        self._title.pack(side="left")

        actions = ctk.CTkFrame(top, fg_color="transparent")
        actions.pack(side="right")
        button_size = theme.scaled(44, scale)
        icon_font = theme.font(19, scale, family=_ICON_FONT)
        self._lock_button = ctk.CTkButton(
            actions,
            text=_LOCK_GLYPH,
            command=self.app.lock,
            width=button_size,
            height=button_size,
            corner_radius=button_size // 2,
            fg_color="transparent",
            hover_color=palette["row_hover"],
            text_color=palette["text"],
            font=icon_font,
        )
        self._lock_button.pack(side="left")
        _Tooltip(self._lock_button, "Kilitle", scale)
        self._settings_button = ctk.CTkButton(
            actions,
            text=_SETTINGS_GLYPH,
            command=self._open_settings,
            width=button_size,
            height=button_size,
            corner_radius=button_size // 2,
            fg_color="transparent",
            hover_color=palette["row_hover"],
            text_color=palette["text"],
            font=icon_font,
        )
        self._settings_button.pack(side="left")
        _Tooltip(self._settings_button, "Ayarlar", scale)

        search_height = theme.scaled(46, scale)
        self._search_shell = ctk.CTkFrame(
            self,
            fg_color=palette["search_fill"],
            corner_radius=search_height // 2,
            height=search_height,
        )
        self._search_shell.pack(
            fill="x",
            padx=theme.scaled(16, scale),
            pady=(theme.scaled(10, scale), theme.scaled(12, scale)),
        )
        self._search_shell.pack_propagate(False)
        self._search_icon = ctk.CTkLabel(
            self._search_shell,
            text=_SEARCH_GLYPH,
            width=theme.scaled(44, scale),
            text_color=palette["muted"],
            font=theme.font(18, scale, family=_ICON_FONT),
            cursor="xterm",
        )
        self._search_icon.pack(side="left")
        self._search_icon.bind(
            "<Button-1>", lambda _event: self._search.focus_set(), add="+"
        )
        self._search = ctk.CTkEntry(
            self._search_shell,
            placeholder_text=_SEARCH_PLACEHOLDER,
            height=theme.scaled(38, scale),
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
            text_color=palette["text"],
            placeholder_text_color=palette["muted"],
            font=theme.font(16, scale),
        )
        self._search.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, theme.scaled(18, scale)),
        )
        self._search.bind("<KeyRelease>", self._on_query_change)

        self._list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            scrollbar_fg_color=palette["bg"],
            scrollbar_button_color=palette["surface_alt"],
            scrollbar_button_hover_color=palette["muted"],
        )
        self._list.pack(fill="both", expand=True)

        self._empty_label = ctk.CTkLabel(
            self._list,
            text=_EMPTY_TEXT,
            text_color=_MUTED_TEXT,
            font=theme.font(14, scale),
        )
        self._spacer = ctk.CTkFrame(
            self._list,
            fg_color="transparent",
            height=theme.scaled(_BASE_SPACER, scale),
        )

        self._undo_bar = ctk.CTkFrame(
            self,
            fg_color=palette["surface_alt"],
            corner_radius=theme.scaled(12, scale),
        )
        ctk.CTkLabel(
            self._undo_bar,
            text="Silindi —",
            text_color=palette["text"],
            font=theme.font(14, scale),
        ).pack(side="left", padx=(theme.scaled(16, scale), 8))
        ctk.CTkButton(
            self._undo_bar,
            text="Geri al",
            command=self._undo_delete,
            width=theme.scaled(76, scale),
            height=theme.scaled(32, scale),
            corner_radius=theme.scaled(8, scale),
            fg_color="transparent",
            hover_color=palette["row_hover"],
            text_color=palette["accent"],
            font=theme.font(14, scale, weight="bold"),
        ).pack(side="right", padx=(8, theme.scaled(10, scale)))

        self._fab_height = theme.scaled(_BASE_FAB_HEIGHT, scale)
        self._fab_margin = theme.scaled(_BASE_MARGIN, scale)
        self._fab = ctk.CTkButton(
            self,
            text="+ Ekle",
            command=self._open_import,
            width=theme.scaled(120, scale),
            height=self._fab_height,
            corner_radius=self._fab_height // 2,
            fg_color=_PRIMARY_FG,
            hover_color=_PRIMARY_HOVER,
            text_color=_ON_ACCENT,
            font=theme.font(16, scale, weight="bold"),
        )
        self._fab.place(
            relx=1.0,
            rely=1.0,
            anchor="se",
            x=-self._fab_margin,
            y=-self._fab_margin,
        )
        self._fab.lift()

        self.tick()

    def _on_query_change(self, _event) -> None:
        self._render()

    def _open_import(self) -> None:
        self.app.show_screen("import")

    def _open_settings(self) -> None:
        self.app.show_screen("settings")

    def _set_empty_state(self, empty: bool) -> None:
        scale = self.app.font_scale
        if empty:
            self._spacer.pack_forget()
            if not self._empty_label.winfo_manager():
                self._empty_label.pack(
                    padx=theme.scaled(24, scale),
                    pady=theme.scaled(32, scale),
                )
            return
        self._empty_label.pack_forget()

    def _render(self) -> None:
        self._spacer.pack_forget()
        for row in self._rows:
            row.destroy()
        self._rows = []
        query = self._search.get()
        items = filter_accounts(self._accounts, query)
        if not items:
            self._empty_label.configure(
                text=_NO_MATCH_TEXT if query.strip() else _EMPTY_TEXT
            )
            self._set_empty_state(True)
            return
        self._set_empty_state(False)
        for account in items:
            index = self._index_of(account)
            if index < 0:
                continue
            row = AccountRow(
                self._list,
                account,
                scale=self.app.font_scale,
                on_edit=self._edit_account,
                on_delete=lambda acc, i=index: self._delete_account(acc, i),
            )
            self._rows.append(row)
        self._place_rows()

    def _place_rows(self) -> None:
        for row in self._rows:
            row.pack(fill="x")
        last = len(self._rows) - 1
        for index, row in enumerate(self._rows):
            row.set_divider_visible(index != last)
        self._spacer.pack(fill="x")

    def _index_of(self, account: Account) -> int:
        for index, item in enumerate(self._accounts):
            if item is account:
                return index
        return -1

    def _edit_account(self, account: Account) -> None:
        _EditDialog(
            self,
            account,
            on_save=lambda name, issuer: self._apply_edit(account, name, issuer),
            scale=self.app.font_scale,
        )

    def _apply_edit(self, account: Account, name: str, issuer: str) -> None:
        account.name = name
        account.issuer = issuer
        self.app.store.save(self._accounts)
        self.reload()

    def _delete_account(self, account: Account, index: int) -> None:
        current = self._index_of(account)
        if current < 0:
            return
        self._clear_undo()
        self._accounts.pop(current)
        self.app.store.save(self._accounts)
        self._render()
        self._show_undo(account, current)

    def _show_undo(self, account: Account, index: int) -> None:
        self._undo_account = account
        self._undo_index = index
        offset = self._fab_margin + self._fab_height + theme.scaled(8, self.app.font_scale)
        self._undo_bar.place(
            relx=0.0,
            rely=1.0,
            anchor="sw",
            relwidth=1.0,
            y=-offset,
        )
        self._undo_bar.lift()
        self._fab.lift()
        if self._undo_job is not None:
            try:
                self.after_cancel(self._undo_job)
            except tkinter.TclError:
                pass
        self._undo_job = self.after(_UNDO_VISIBLE_MS, self._clear_undo)

    def _clear_undo(self) -> None:
        job = getattr(self, "_undo_job", None)
        self._undo_job = None
        if job is not None:
            try:
                self.after_cancel(job)
            except tkinter.TclError:
                pass
        self._undo_account = None
        self._undo_index = None
        if hasattr(self, "_undo_bar"):
            self._undo_bar.place_forget()

    def _undo_delete(self) -> None:
        account = self._undo_account
        index = self._undo_index
        self._clear_undo()
        if account is None or index is None:
            return
        index = max(0, min(index, len(self._accounts)))
        self._accounts.insert(index, account)
        self.app.store.save(self._accounts)
        self.reload()


class _EditDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        account: Account,
        on_save: Callable[[str, str], None],
        scale: float = 1.0,
    ):
        super().__init__(master)
        self.title("Hesabı düzenle")
        self.geometry("340x250")
        self.resizable(False, False)
        self._on_save = on_save

        ctk.CTkLabel(
            self,
            text="Hesap adı",
            anchor="w",
            font=theme.font(12, scale),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", padx=16, pady=(16, 2))
        self._name_entry = ctk.CTkEntry(self, height=30, font=theme.font(13, scale))
        self._name_entry.insert(0, account.name)
        self._name_entry.pack(fill="x", padx=16)

        ctk.CTkLabel(
            self,
            text="Servis",
            anchor="w",
            font=theme.font(12, scale),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", padx=16, pady=(10, 2))
        self._issuer_entry = ctk.CTkEntry(self, height=30, font=theme.font(13, scale))
        self._issuer_entry.insert(0, account.issuer)
        self._issuer_entry.pack(fill="x", padx=16)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(pady=(16, 0))
        ctk.CTkButton(
            buttons,
            text="Kaydet",
            command=self._save,
            width=100,
            height=30,
            corner_radius=8,
            fg_color=_PRIMARY_FG,
            hover_color=_PRIMARY_HOVER,
            text_color=_ON_ACCENT,
            font=theme.font(12, scale, weight="bold"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="Vazgeç",
            command=self.destroy,
            width=90,
            height=30,
            corner_radius=8,
            fg_color=theme.PALETTE["surface_alt"],
            hover_color=theme.PALETTE["row_hover"],
            text_color=theme.PALETTE["text"],
            font=theme.font(12, scale),
        ).pack(side="left")

        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.after(50, self._name_entry.focus_set)

    def _save(self) -> None:
        name = self._name_entry.get().strip()
        issuer = self._issuer_entry.get().strip()
        self.destroy()
        self._on_save(name, issuer)
