import threading
import tkinter
from datetime import datetime
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc import hello, pin
from google_auth_pc.hello import VerifyResult
from google_auth_pc.ui.pin_pad import PinPad

if TYPE_CHECKING:
    from google_auth_pc.app import App

_FORGOT_MESSAGE = (
    "PIN sıfırlanacak ve kayıtlı hesaplar silinecek. Hesaplarını telefonundaki "
    "Google Authenticator'dan yeniden aktarabilirsin. Devam edilsin mi?"
)

_PRIMARY_FG = ("#2b6df5", "#2b6df5")
_PRIMARY_HOVER = ("#1f5cd6", "#1f5cd6")
_LINK_COLOR = ("#2b6df5", "#5b8def")
_LINK_HOVER = ("#e6ecf7", "#22252b")
_TITLE_TEXT = ("#1a1d22", "#e6e8ec")
_SUBTITLE_TEXT = ("#2a2e34", "#e6e8ec")
_HINT_TEXT = ("#6a7078", "#8b8f98")
_STATUS_TEXT = ("#b3261e", "#f2b8b5")


class LockScreen(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._pin_pad: PinPad | None = None
        self._pending_pin: str | None = None
        self._hello_button: ctk.CTkButton | None = None
        self._access: ctk.CTkFrame | None = None
        self._status: ctk.CTkLabel | None = None
        self._build()

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._pin_pad = None
        self._pending_pin = None
        self._hello_button = None
        self._build()

    def _build(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(expand=True)
        ctk.CTkLabel(
            content,
            text="Google Auth PC",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=_TITLE_TEXT,
        ).pack(pady=(0, 8))
        ctk.CTkLabel(
            content,
            text="Kodlar kilitli",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=_SUBTITLE_TEXT,
        ).pack()
        ctk.CTkLabel(
            content,
            text="Devam etmek için kimliğini doğrula",
            font=ctk.CTkFont(size=12),
            text_color=_HINT_TEXT,
        ).pack(pady=(4, 20))

        self._access = ctk.CTkFrame(content, fg_color="transparent")
        self._access.pack()

        self._status = ctk.CTkLabel(
            content,
            text="",
            height=18,
            font=ctk.CTkFont(size=12),
            text_color=_STATUS_TEXT,
        )
        self._status.pack(pady=(12, 0))

        if pin.is_pin_set(self.app.app_config):
            ctk.CTkButton(
                content,
                text="PIN'i unuttum",
                command=self._forgot_pin,
                fg_color="transparent",
                hover_color=_LINK_HOVER,
                text_color=_HINT_TEXT,
                font=ctk.CTkFont(size=11, underline=True),
                width=100,
                height=24,
            ).pack(pady=(6, 0))

        self._show_start()

    def _clear_access(self) -> None:
        for child in self._access.winfo_children():
            child.destroy()
        self._pin_pad = None
        self._hello_button = None

    def _set_status(self, text: str) -> None:
        self._status.configure(text=text)

    def _show_start(self) -> None:
        self._clear_access()
        hello_available = hello.hello_biometrics_available()
        pin_set = pin.is_pin_set(self.app.app_config)

        if hello_available:
            self._hello_button = ctk.CTkButton(
                self._access,
                text="Windows ile doğrula",
                command=self._start_hello,
                width=210,
                height=40,
                corner_radius=8,
                fg_color=_PRIMARY_FG,
                hover_color=_PRIMARY_HOVER,
                text_color="#ffffff",
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            self._hello_button.pack()

        if pin_set:
            ctk.CTkButton(
                self._access,
                text="PIN kullan",
                command=self._show_pin_verify,
                fg_color="transparent",
                hover_color=_LINK_HOVER,
                text_color=_LINK_COLOR,
                font=ctk.CTkFont(size=12, underline=True),
                width=100,
                height=24,
            ).pack(pady=(10 if hello_available else 0, 0))

        if not hello_available and not pin_set:
            self._show_new_pin()

    def _start_hello(self) -> None:
        self._set_status("")
        if self._hello_button is not None:
            self._hello_button.configure(state="disabled")
        hwnd = self.winfo_toplevel().winfo_id()
        threading.Thread(target=self._run_hello_verify, args=(hwnd,), daemon=True).start()

    def _run_hello_verify(self, hwnd: int) -> None:
        try:
            result = hello.verify_identity(hwnd)
        except Exception:
            result = VerifyResult.UNAVAILABLE
        try:
            self.after(0, lambda: self._on_hello_result(result))
        except (tkinter.TclError, RuntimeError):
            pass

    def _on_hello_result(self, result: VerifyResult) -> None:
        if self._hello_button is not None and self._hello_button.winfo_exists():
            self._hello_button.configure(state="normal")
        if result == VerifyResult.OK:
            self.app.unlock_session()
        elif result == VerifyResult.CANCELLED:
            self._set_status("Doğrulama iptal edildi")
        elif result == VerifyResult.UNAVAILABLE:
            if pin.is_pin_set(self.app.app_config):
                self._show_pin_verify()
            else:
                self._show_new_pin()

    def _show_pin_verify(self) -> None:
        self._set_status("")
        self._clear_access()
        self._pin_pad = PinPad(self._access, self._on_pin_submitted, "Uygulama PIN'i")
        self._pin_pad.pack()

    def _on_pin_submitted(self, entered: str) -> None:
        if pin.verify_pin(self.app.app_config, entered):
            self.app.unlock_session()
            return
        self._pin_pad.reset()
        self._set_status("Hatalı PIN")

    def _show_new_pin(self) -> None:
        self._set_status("")
        self._clear_access()
        self._pending_pin = None
        self._pin_pad = PinPad(self._access, self._on_new_pin, "Yeni PIN")
        self._pin_pad.pack()

    def _on_new_pin(self, entered: str) -> None:
        self._pending_pin = entered
        self._set_status("")
        self._clear_access()
        self._pin_pad = PinPad(self._access, self._on_repeat_pin, "PIN'i tekrarla")
        self._pin_pad.pack()

    def _on_repeat_pin(self, entered: str) -> None:
        if entered == self._pending_pin:
            pin.set_pin(self.app.app_config, entered)
            self._pending_pin = None
            self.app.unlock_session()
            return
        self._show_new_pin()
        self._set_status("PIN'ler eşleşmedi")

    def _forgot_pin(self) -> None:
        if not messagebox.askyesno("PIN'i unuttum", _FORGOT_MESSAGE, parent=self):
            return
        store_path = self.app.store.path
        if store_path.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            store_path.replace(
                store_path.with_name(f"{store_path.name}.sifirlandi-{stamp}")
            )
        pin.clear_pin(self.app.app_config)
        self.refresh()
