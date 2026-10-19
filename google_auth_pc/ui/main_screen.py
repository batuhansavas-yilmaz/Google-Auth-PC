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
_TICK_MS = 250
_UNDO_VISIBLE_MS = 5000

_PRIMARY_FG = theme.PALETTE["accent"]
_PRIMARY_HOVER = ("#1f5cd6", "#a8c7fa")
_ON_ACCENT = theme.PALETTE["on_accent"]
_MUTED_TEXT = theme.PALETTE["muted"]
_SECONDARY_FG = theme.PALETTE["surface_alt"]
_SECONDARY_HOVER = theme.PALETTE["row_hover"]
_SECONDARY_TEXT = theme.PALETTE["text"]


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


class MainScreen(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master, fg_color="transparent")
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
        if self._tick_id is not None:
            try:
                self.after_cancel(self._tick_id)
            except tkinter.TclError:
                pass
            self._tick_id = None
        self._clear_undo()
        super().destroy()

    def _build(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(12, 6))
        self._search = ctk.CTkEntry(
            bar,
            placeholder_text=_SEARCH_PLACEHOLDER,
            height=32,
        )
        self._search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._search.bind("<KeyRelease>", self._on_query_change)
        self._add_button = ctk.CTkButton(
            bar,
            text="+ Ekle",
            command=self._open_import,
            width=80,
            height=32,
            corner_radius=8,
            fg_color=_PRIMARY_FG,
            hover_color=_PRIMARY_HOVER,
            text_color=_ON_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._add_button.pack(side="left")
        self._settings_button = ctk.CTkButton(
            bar,
            text="Ayarlar",
            command=self._open_settings,
            width=74,
            height=32,
            corner_radius=8,
            fg_color=_SECONDARY_FG,
            hover_color=_SECONDARY_HOVER,
            text_color=_SECONDARY_TEXT,
            font=ctk.CTkFont(size=12),
        )
        self._settings_button.pack(side="left", padx=(8, 0))

        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._empty_label = ctk.CTkLabel(
            self._list,
            text=_EMPTY_TEXT,
            text_color=_MUTED_TEXT,
            font=theme.font(14, self.app.font_scale),
        )

        self._undo_bar = ctk.CTkFrame(
            self,
            fg_color=theme.PALETTE["surface_alt"],
            corner_radius=0,
        )
        ctk.CTkLabel(
            self._undo_bar,
            text="Silindi",
            text_color=theme.PALETTE["text"],
            font=theme.font(14, self.app.font_scale),
        ).pack(side="left", padx=(theme.scaled(16, self.app.font_scale), 8))
        ctk.CTkButton(
            self._undo_bar,
            text="Geri al",
            command=self._undo_delete,
            width=theme.scaled(76, self.app.font_scale),
            height=theme.scaled(32, self.app.font_scale),
            corner_radius=theme.scaled(8, self.app.font_scale),
            fg_color="transparent",
            hover_color=theme.PALETTE["row_hover"],
            text_color=theme.PALETTE["accent"],
            font=theme.font(14, self.app.font_scale, weight="bold"),
        ).pack(side="right", padx=(8, theme.scaled(10, self.app.font_scale)))

        self.tick()

    def _on_query_change(self, _event) -> None:
        self._render()

    def _open_import(self) -> None:
        self.app.show_screen("import")

    def _open_settings(self) -> None:
        self.app.show_screen("settings")

    def _render(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows = []
        if self._accounts:
            self._empty_label.pack_forget()
        else:
            self._empty_label.pack(pady=32)
        for account in filter_accounts(self._accounts, self._search.get()):
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
            row.pack(fill="x")
            self._rows.append(row)

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
        self._undo_bar.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)
        self._undo_bar.lift()
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
            fg_color=_SECONDARY_FG,
            hover_color=_SECONDARY_HOVER,
            text_color=_SECONDARY_TEXT,
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
