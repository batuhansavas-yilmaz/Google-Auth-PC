from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc.importer import ImportResult, extract_migration_accounts
from google_auth_pc.migration import merge_accounts
from google_auth_pc.models import Account
from google_auth_pc.storage import AccountStore
from google_auth_pc.totp import normalize_secret

if TYPE_CHECKING:
    from google_auth_pc.app import App

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

_BULK_TAB = "Tek hamlede (önerilen)"
_MANUAL_TAB = "Tek tek ekle"
_BACK_TEXT = "← Geri"
_SCREEN_TITLE = "Hesap ekle"
_STEPS_TITLE = "Telefonda nasıl yapılır"
_STEPS = (
    "Google Authenticator'ı aç",
    "Ayarlar → Hesapları aktar → Dışa aktar'ı seç, hesapları işaretle",
    "Çıkan her QR ekranının görüntüsünü al (hesap çoksa birkaç QR olur)",
    "Görüntüleri PC'ye at ve aşağıdaki alandan ekle",
)
_DROP_TITLE = "QR ekran görüntüsünü buraya bırak"
_DROP_OR = "ya da"
_DROP_HINT = ".png / .jpg — birden fazla seçebilirsin"
_PICK_TEXT = "Görselleri seç…"
_PICK_TITLE = "QR görsellerini seç"
_FOUND_TEMPLATE = "{found} hesap bulundu — {added} eklendi, {skipped} zaten ekliydi."
_FAILED_PREFIX = "Okunamayan görseller: "
_NO_QR_TEXT = "QR kod bulunamadı. Görsellerin ekran görüntüsü olduğundan emin ol."
_DIALOG_TITLE = "Aktarım sonucu"
_NAME_LABEL = "Hesap adı"
_ISSUER_LABEL = "Servis (ör. Google)"
_SECRET_LABEL = "Kurulum anahtarı (secret)"
_ADD_TEXT = "Ekle"
_INVALID_SECRET_TEXT = "Geçersiz kurulum anahtarı"
_DUPLICATE_TEXT = "Bu hesap zaten ekli"

_PRIMARY_FG = ("#2b6df5", "#2b6df5")
_PRIMARY_HOVER = ("#1f5cd6", "#1f5cd6")
_MUTED_TEXT = ("#6a7078", "#8b8f98")
_TITLE_TEXT = ("#1a1d22", "#e6e8ec")
_STEP_TEXT = ("#2a2e34", "#c7cad1")
_ERROR_TEXT = ("#b3261e", "#f2b8b5")
_SECONDARY_FG = ("#e8eaee", "#22252b")
_SECONDARY_HOVER = ("#d9dde3", "#2b2f36")
_SECONDARY_TEXT = ("#3a3f46", "#c7cad1")
_PICK_TEXT_COLOR = ("#3a5f9e", "#9fb4d8")
_DROP_BORDER = ("#c9ced6", "#3a3e46")
_DROP_BG = ("#f9fafb", "#16181d")


def apply_import(store: AccountStore, result: ImportResult) -> tuple[int, int]:
    existing = store.load()
    valid: list[Account] = []
    skipped = 0
    for account in result.accounts:
        try:
            normalize_secret(account.secret)
        except ValueError:
            skipped += 1
            continue
        valid.append(account)
    merged = merge_accounts(existing, valid)
    store.save(existing + merged.added)
    return len(merged.added), len(merged.skipped) + skipped


class ImportScreen(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._tab_buttons: dict[str, ctk.CTkButton] = {}
        self._tab_frames: dict[str, ctk.CTkFrame] = {}
        self._name_entry: ctk.CTkEntry | None = None
        self._issuer_entry: ctk.CTkEntry | None = None
        self._secret_entry: ctk.CTkEntry | None = None
        self._error_label: ctk.CTkLabel | None = None
        self._build()
        self._show_tab(_BULK_TAB)

    def _build(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkButton(
            top,
            text=_BACK_TEXT,
            command=self._go_back,
            width=72,
            height=28,
            corner_radius=8,
            fg_color=_SECONDARY_FG,
            hover_color=_SECONDARY_HOVER,
            text_color=_SECONDARY_TEXT,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        ctk.CTkLabel(
            top,
            text=_SCREEN_TITLE,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=_TITLE_TEXT,
        ).pack(side="left", padx=(10, 0))

        tabs = ctk.CTkFrame(self, fg_color="transparent")
        tabs.pack(fill="x", padx=12, pady=(6, 8))
        for title in (_BULK_TAB, _MANUAL_TAB):
            button = ctk.CTkButton(
                tabs,
                text=title,
                command=lambda selected=title: self._show_tab(selected),
                height=30,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            button.pack(side="left", padx=(0, 6))
            self._tab_buttons[title] = button

        self._tab_frames[_BULK_TAB] = self._build_bulk_tab()
        self._tab_frames[_MANUAL_TAB] = self._build_manual_tab()

    def _show_tab(self, title: str) -> None:
        for name, frame in self._tab_frames.items():
            if name == title:
                frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            else:
                frame.pack_forget()
        for name, button in self._tab_buttons.items():
            if name == title:
                button.configure(
                    fg_color=_PRIMARY_FG,
                    hover_color=_PRIMARY_HOVER,
                    text_color="#ffffff",
                )
            else:
                button.configure(
                    fg_color=_SECONDARY_FG,
                    hover_color=_SECONDARY_HOVER,
                    text_color=_SECONDARY_TEXT,
                )

    def _build_bulk_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(
            frame,
            text=_STEPS_TITLE,
            anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", pady=(2, 6))
        for index, step in enumerate(_STEPS, start=1):
            ctk.CTkLabel(
                frame,
                text=f"{index}. {step}",
                anchor="w",
                justify="left",
                wraplength=330,
                font=ctk.CTkFont(size=12),
                text_color=_STEP_TEXT,
            ).pack(fill="x", pady=2)

        area = ctk.CTkFrame(
            frame,
            corner_radius=10,
            fg_color=_DROP_BG,
            border_width=2,
            border_color=_DROP_BORDER,
        )
        area.pack(fill="x", pady=(14, 0))
        drop_title = ctk.CTkLabel(
            area,
            text=_DROP_TITLE,
            font=ctk.CTkFont(size=12),
            text_color=_STEP_TEXT,
        )
        drop_title.pack(pady=(18, 2))
        drop_or = ctk.CTkLabel(
            area,
            text=_DROP_OR,
            font=ctk.CTkFont(size=11),
            text_color=_MUTED_TEXT,
        )
        drop_or.pack()
        ctk.CTkButton(
            area,
            text=_PICK_TEXT,
            command=self._pick_images,
            width=150,
            height=30,
            corner_radius=8,
            fg_color=_SECONDARY_FG,
            hover_color=_SECONDARY_HOVER,
            border_width=1,
            border_color=_DROP_BORDER,
            text_color=_PICK_TEXT_COLOR,
            font=ctk.CTkFont(size=12),
        ).pack(pady=(10, 4))
        drop_hint = ctk.CTkLabel(
            area,
            text=_DROP_HINT,
            font=ctk.CTkFont(size=10),
            text_color=_MUTED_TEXT,
        )
        drop_hint.pack(pady=(0, 16))

        for widget in (area, drop_title, drop_or, drop_hint):
            widget.bind("<Button-1>", lambda _event: self._pick_images())

        if DND_FILES is not None:
            try:
                area.drop_target_register(DND_FILES)
                area.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass
        return frame

    def _build_manual_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self._name_entry = self._add_field(frame, _NAME_LABEL, top_pad=(2, 2))
        self._issuer_entry = self._add_field(frame, _ISSUER_LABEL)
        self._secret_entry = self._add_field(frame, _SECRET_LABEL)
        self._error_label = ctk.CTkLabel(
            frame,
            text="",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=_ERROR_TEXT,
        )
        self._error_label.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(
            frame,
            text=_ADD_TEXT,
            command=self._manual_add,
            height=34,
            corner_radius=8,
            fg_color=_PRIMARY_FG,
            hover_color=_PRIMARY_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(fill="x", pady=(12, 0))
        return frame

    def _add_field(self, frame, label_text: str, top_pad=(8, 2)) -> ctk.CTkEntry:
        ctk.CTkLabel(
            frame,
            text=label_text,
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", pady=top_pad)
        entry = ctk.CTkEntry(frame, height=30)
        entry.pack(fill="x")
        return entry

    def _go_back(self) -> None:
        self.app.show_main()

    def _pick_images(self) -> None:
        selected = filedialog.askopenfilenames(
            parent=self,
            title=_PICK_TITLE,
            filetypes=[
                ("Görseller", "*.png *.jpg *.jpeg"),
                ("Tüm dosyalar", "*.*"),
            ],
        )
        if selected:
            self._import_images([Path(item) for item in selected])

    def _on_drop(self, event) -> None:
        paths = [Path(item) for item in self.tk.splitlist(event.data)]
        if paths:
            self._import_images(paths)

    def _import_images(self, paths: list[Path]) -> None:
        result = extract_migration_accounts(paths)
        if not result.accounts:
            messagebox.showwarning(_DIALOG_TITLE, _NO_QR_TEXT, parent=self)
            return
        added, skipped = apply_import(self.app.store, result)
        summary = _FOUND_TEMPLATE.format(
            found=len(result.accounts), added=added, skipped=skipped
        )
        if result.failed_files:
            names = ", ".join(path.name for path in result.failed_files)
            summary += f"\n{_FAILED_PREFIX}{names}"
        messagebox.showinfo(_DIALOG_TITLE, summary, parent=self)

    def _manual_add(self) -> None:
        try:
            secret = normalize_secret(self._secret_entry.get().strip())
        except ValueError:
            self._set_error(_INVALID_SECRET_TEXT)
            return
        account = Account(
            secret=secret,
            name=self._name_entry.get().strip(),
            issuer=self._issuer_entry.get().strip(),
        )
        added, _skipped = apply_import(
            self.app.store,
            ImportResult(accounts=[account], failed_files=[], skipped_payloads=0),
        )
        if added == 0:
            self._set_error(_DUPLICATE_TEXT)
            return
        self._set_error("")
        for entry in (self._name_entry, self._issuer_entry, self._secret_entry):
            entry.delete(0, "end")
        self.app.show_main()

    def _set_error(self, text: str) -> None:
        self._error_label.configure(text=text)
