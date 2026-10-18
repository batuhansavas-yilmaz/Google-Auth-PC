import unicodedata
from collections.abc import Callable
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc.models import Account
from google_auth_pc.ui.widgets import AccountCard

if TYPE_CHECKING:
    from google_auth_pc.app import App

_SEARCH_PLACEHOLDER = "Hesap ara…"
_EMPTY_TEXT = "Henüz hesap yok — + Ekle ile başla"
_DELETE_QUESTION = "Hesap silinsin mi? Bu işlem geri alınamaz."
_TICK_MS = 250

_PRIMARY_FG = ("#2b6df5", "#2b6df5")
_PRIMARY_HOVER = ("#1f5cd6", "#1f5cd6")
_MUTED_TEXT = ("#6a7078", "#8b8f98")
_SECONDARY_FG = ("#e8eaee", "#22252b")
_SECONDARY_HOVER = ("#d9dde3", "#2b2f36")
_SECONDARY_TEXT = ("#3a3f46", "#c7cad1")


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
        self._cards: list[AccountCard] = []
        self._tick_id: str | None = None
        self._build()
        self.reload()

    def reload(self) -> None:
        self._accounts = self.app.store.load()
        self._render()

    def tick(self) -> None:
        self._tick_id = self.after(_TICK_MS, self.tick)
        for card in self._cards:
            card.tick()

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
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._add_button.pack(side="left")

        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._empty_label = ctk.CTkLabel(
            self._list,
            text=_EMPTY_TEXT,
            text_color=_MUTED_TEXT,
            font=ctk.CTkFont(size=12),
        )

        self.tick()

    def _on_query_change(self, _event) -> None:
        self._render()

    def _open_import(self) -> None:
        self.app.show_screen("import")

    def _render(self) -> None:
        for card in self._cards:
            card.destroy()
        self._cards = []
        if self._accounts:
            self._empty_label.pack_forget()
        else:
            self._empty_label.pack(pady=32)
        for account in filter_accounts(self._accounts, self._search.get()):
            card = AccountCard(
                self._list,
                account,
                on_edit=self._edit_account,
                on_delete=self._delete_account,
            )
            card.pack(fill="x", padx=4, pady=4)
            self._cards.append(card)

    def _edit_account(self, account: Account) -> None:
        _EditDialog(
            self,
            account,
            on_save=lambda name, issuer: self._apply_edit(account, name, issuer),
        )

    def _apply_edit(self, account: Account, name: str, issuer: str) -> None:
        account.name = name
        account.issuer = issuer
        self.app.store.save(self._accounts)
        self.reload()

    def _delete_account(self, account: Account) -> None:
        if not messagebox.askyesno("Hesabı sil", _DELETE_QUESTION, parent=self):
            return
        self._accounts = [item for item in self._accounts if item is not account]
        self.app.store.save(self._accounts)
        self.reload()


class _EditDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        account: Account,
        on_save: Callable[[str, str], None],
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
            font=ctk.CTkFont(size=12),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", padx=16, pady=(16, 2))
        self._name_entry = ctk.CTkEntry(self, height=30)
        self._name_entry.insert(0, account.name)
        self._name_entry.pack(fill="x", padx=16)

        ctk.CTkLabel(
            self,
            text="Servis",
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", padx=16, pady=(10, 2))
        self._issuer_entry = ctk.CTkEntry(self, height=30)
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
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
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
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.after(50, self._name_entry.focus_set)

    def _save(self) -> None:
        name = self._name_entry.get().strip()
        issuer = self._issuer_entry.get().strip()
        self.destroy()
        self._on_save(name, issuer)
