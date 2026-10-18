from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc import hello, pin
from google_auth_pc.ui.pin_pad import PinPad

if TYPE_CHECKING:
    from google_auth_pc.app import App

_TITLE = "Hoş geldin"
_SUBTITLE = "Hesaplarını telefondaki Google Authenticator'dan bu bilgisayara aktaralım."
_STEPS_TITLE = "Telefondan aktarım 4 adımda"
_STEPS = (
    "Google Authenticator'ı aç",
    "Sağ üstten \"Hesapları aktar → Dışa aktar\"ı seç, hesapları işaretle",
    "Çıkan her QR ekranının görüntüsünü al (hesap çoksa birkaç QR olur)",
    "Görüntüleri PC'ye at; uygulamanın \"Telefondan aktar\" ekranından içe al",
)
_IMPORT_TEXT = "Telefondan aktar"
_MANUAL_TEXT = "Tek tek ekle"
_SKIP_TEXT = "Şimdilik atla"
_SECURITY_TITLE = "Güvenlik"
_SECURITY_HELLO_TEXT = (
    "Kodların Windows doğrulamasıyla (Hello, parmak izi veya hesap parolası) "
    "korunur. İstersen yedek olarak 6 haneli bir PIN de belirle — Windows "
    "doğrulaması çalışmazsa bu PIN ile girersin."
)
_SECURITY_NO_HELLO_TEXT = (
    "Bu bilgisayarda Windows doğrulaması kullanılamıyor. Kodlarını korumak "
    "için 6 haneli bir PIN belirlemen gerekiyor."
)
_BACKUP_PIN_TEXT = "Yedek PIN belirle (önerilir)"
_SKIP_PIN_TEXT = "Atla"
_FINISH_TEXT = "Bitir"
_PIN_NEW_TITLE = "Yeni PIN"
_PIN_REPEAT_TITLE = "PIN'i tekrarla"
_PIN_SET_STATUS = "PIN belirlendi"
_PIN_SKIPPED_STATUS = "Şimdilik PIN'siz devam ediliyor"
_PIN_REQUIRED_STATUS = "Devam etmek için önce PIN belirle"
_PIN_MISMATCH_STATUS = "PIN'ler eşleşmedi"

_PRIMARY_FG = ("#2b6df5", "#2b6df5")
_PRIMARY_HOVER = ("#1f5cd6", "#1f5cd6")
_LINK_COLOR = ("#2b6df5", "#5b8def")
_LINK_HOVER = ("#e6ecf7", "#22252b")
_MUTED_TEXT = ("#6a7078", "#8b8f98")
_TITLE_TEXT = ("#1a1d22", "#e6e8ec")
_BODY_TEXT = ("#2a2e34", "#c7cad1")
_STATUS_TEXT = ("#2a7a4b", "#7fd6a8")
_ERROR_TEXT = ("#b3261e", "#f2b8b5")
_SECONDARY_FG = ("#e8eaee", "#22252b")
_SECONDARY_HOVER = ("#d9dde3", "#2b2f36")
_SECONDARY_TEXT = ("#3a3f46", "#c7cad1")


class IntroScreen(ctk.CTkFrame):
    def __init__(self, master, app: "App", on_done: Callable[[], None]):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._on_done = on_done
        self._pin_pad: PinPad | None = None
        self._pending_pin: str | None = None
        self._pin_area: ctk.CTkFrame | None = None
        self._finish_button: ctk.CTkButton | None = None
        self._status: ctk.CTkLabel | None = None
        self._build_steps_page()

    def _clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._pin_pad = None
        self._pending_pin = None
        self._pin_area = None
        self._finish_button = None
        self._status = None

    def _build_steps_page(self) -> None:
        self._clear()
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)
        ctk.CTkLabel(
            content,
            text=_TITLE,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=_TITLE_TEXT,
        ).pack(pady=(12, 6))
        ctk.CTkLabel(
            content,
            text=_SUBTITLE,
            wraplength=320,
            justify="center",
            font=ctk.CTkFont(size=12),
            text_color=_MUTED_TEXT,
        ).pack(pady=(0, 22))
        ctk.CTkLabel(
            content,
            text=_STEPS_TITLE,
            anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", pady=(0, 8))
        for index, step in enumerate(_STEPS, start=1):
            ctk.CTkLabel(
                content,
                text=f"{index}. {step}",
                anchor="w",
                justify="left",
                wraplength=330,
                font=ctk.CTkFont(size=12),
                text_color=_BODY_TEXT,
            ).pack(fill="x", pady=3)

        buttons = ctk.CTkFrame(content, fg_color="transparent")
        buttons.pack(side="bottom", fill="x")
        ctk.CTkButton(
            buttons,
            text=_IMPORT_TEXT,
            command=self._go_import,
            height=36,
            corner_radius=8,
            fg_color=_PRIMARY_FG,
            hover_color=_PRIMARY_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(fill="x")
        ctk.CTkButton(
            buttons,
            text=_MANUAL_TEXT,
            command=self._go_import,
            height=32,
            corner_radius=8,
            fg_color=_SECONDARY_FG,
            hover_color=_SECONDARY_HOVER,
            text_color=_SECONDARY_TEXT,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", pady=(8, 0))
        ctk.CTkButton(
            buttons,
            text=_SKIP_TEXT,
            command=self._show_security_page,
            fg_color="transparent",
            hover_color=_LINK_HOVER,
            text_color=_LINK_COLOR,
            font=ctk.CTkFont(size=12, underline=True),
            width=120,
            height=26,
        ).pack(pady=(8, 0))

    def _go_import(self) -> None:
        self.app.show_screen("import")

    def _show_security_page(self) -> None:
        self._clear()
        hello_available = hello.hello_biometrics_available()
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)
        ctk.CTkLabel(
            content,
            text=_SECURITY_TITLE,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=_TITLE_TEXT,
        ).pack(pady=(12, 8))
        ctk.CTkLabel(
            content,
            text=_SECURITY_HELLO_TEXT if hello_available else _SECURITY_NO_HELLO_TEXT,
            wraplength=320,
            justify="left",
            font=ctk.CTkFont(size=12),
            text_color=_BODY_TEXT,
        ).pack(pady=(0, 14))

        self._pin_area = ctk.CTkFrame(content, fg_color="transparent")
        self._pin_area.pack(fill="x")
        self._status = ctk.CTkLabel(
            content,
            text="",
            height=16,
            font=ctk.CTkFont(size=11),
            text_color=_STATUS_TEXT,
        )
        self._status.pack(pady=(8, 0))

        buttons = ctk.CTkFrame(content, fg_color="transparent")
        buttons.pack(side="bottom", fill="x")
        self._finish_button = ctk.CTkButton(
            buttons,
            text=_FINISH_TEXT,
            command=self._finish,
            height=36,
            corner_radius=8,
            fg_color=_PRIMARY_FG,
            hover_color=_PRIMARY_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._finish_button.pack(fill="x")

        if hello_available:
            ctk.CTkButton(
                self._pin_area,
                text=_BACKUP_PIN_TEXT,
                command=self._start_optional_pin,
                height=32,
                corner_radius=8,
                fg_color=_SECONDARY_FG,
                hover_color=_SECONDARY_HOVER,
                text_color=_SECONDARY_TEXT,
                font=ctk.CTkFont(size=12),
            ).pack(fill="x")
            ctk.CTkButton(
                self._pin_area,
                text=_SKIP_PIN_TEXT,
                command=self._skip_pin,
                fg_color="transparent",
                hover_color=_LINK_HOVER,
                text_color=_LINK_COLOR,
                font=ctk.CTkFont(size=11, underline=True),
                width=60,
                height=22,
            ).pack(pady=(4, 0))
        else:
            self._finish_button.configure(state="disabled")
            self._status.configure(text=_PIN_REQUIRED_STATUS, text_color=_MUTED_TEXT)
            self._pin_pad = PinPad(self._pin_area, self._on_new_pin, _PIN_NEW_TITLE)
            self._pin_pad.pack()

    def _start_optional_pin(self) -> None:
        self._clear_pin_area()
        self._set_status("")
        self._pin_pad = PinPad(self._pin_area, self._on_new_pin, _PIN_NEW_TITLE)
        self._pin_pad.pack()

    def _skip_pin(self) -> None:
        self._clear_pin_area()
        self._set_status(_PIN_SKIPPED_STATUS)

    def _on_new_pin(self, entered: str) -> None:
        self._pending_pin = entered
        self._clear_pin_area()
        self._pin_pad = PinPad(self._pin_area, self._on_repeat_pin, _PIN_REPEAT_TITLE)
        self._pin_pad.pack()

    def _on_repeat_pin(self, entered: str) -> None:
        if entered != self._pending_pin:
            self._clear_pin_area()
            self._set_status(_PIN_MISMATCH_STATUS, error=True)
            self._pin_pad = PinPad(self._pin_area, self._on_new_pin, _PIN_NEW_TITLE)
            self._pin_pad.pack()
            return
        pin.set_pin(self.app.app_config, entered)
        self._pending_pin = None
        self._clear_pin_area()
        self._set_status(_PIN_SET_STATUS)
        self._finish_button.configure(state="normal")

    def _clear_pin_area(self) -> None:
        for child in self._pin_area.winfo_children():
            child.destroy()
        self._pin_pad = None

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status.configure(
            text=text, text_color=_ERROR_TEXT if error else _STATUS_TEXT
        )

    def _finish(self) -> None:
        self._on_done()
