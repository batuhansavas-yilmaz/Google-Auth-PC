from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc import __version__, autostart, pin, theme
from google_auth_pc.ui.pin_pad import PinPad

if TYPE_CHECKING:
    from google_auth_pc.app import App

_BACK_TEXT = "← Geri"
_SCREEN_TITLE = "Ayarlar"
_THEME_LABEL = "Tema"
_THEME_LABELS_TO_MODES = {"Otomatik": "system", "Açık": "light", "Koyu": "dark"}
_THEME_MODES_TO_LABELS = {mode: label for label, mode in _THEME_LABELS_TO_MODES.items()}
_AUTOSTART_LABEL = "Windows açılışında başlat"
_AUTOSTART_ERROR = "Otomatik başlatma ayarlanamadı"
_PIN_LABEL = "Uygulama PIN'i (yedek giriş)"
_PIN_SET_TEXT = "PIN'i değiştir"
_PIN_UNSET_TEXT = "PIN belirle"
_PIN_NEW_TITLE = "Yeni PIN"
_PIN_REPEAT_TITLE = "PIN'i tekrarla"
_PIN_CURRENT_TITLE = "Mevcut PIN"
_PIN_SET_STATUS = "PIN belirlendi"
_PIN_CHANGED_STATUS = "PIN güncellendi"
_PIN_WRONG_STATUS = "Hatalı PIN"
_PIN_MISMATCH_STATUS = "PIN'ler eşleşmedi"
_VERSION_TEXT = f"Sürüm {__version__}"

_PRIMARY_FG = ("#2b6df5", "#2b6df5")
_PRIMARY_HOVER = ("#1f5cd6", "#1f5cd6")
_MUTED_TEXT = ("#6a7078", "#8b8f98")
_TITLE_TEXT = ("#1a1d22", "#e6e8ec")
_STATUS_TEXT = ("#2a7a4b", "#7fd6a8")
_ERROR_TEXT = ("#b3261e", "#f2b8b5")
_SECONDARY_FG = ("#e8eaee", "#22252b")
_SECONDARY_HOVER = ("#d9dde3", "#2b2f36")
_SECONDARY_TEXT = ("#3a3f46", "#c7cad1")


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._pin_pad: PinPad | None = None
        self._pending_pin: str | None = None
        self._pin_area: ctk.CTkFrame | None = None
        self._pin_button: ctk.CTkButton | None = None
        self._autostart_switch: ctk.CTkSwitch | None = None
        self._theme_segmented: ctk.CTkSegmentedButton | None = None
        self._status: ctk.CTkLabel | None = None
        self._build()

    def refresh(self) -> None:
        self._reset_pin_flow()
        self._update_pin_button()
        if autostart.is_enabled():
            self._autostart_switch.select()
        else:
            self._autostart_switch.deselect()
        mode = self.app.app_config.get("theme_mode", "system")
        self._theme_segmented.set(_THEME_MODES_TO_LABELS.get(mode, "Otomatik"))
        self._set_status("")

    def _build(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkButton(
            top,
            text=_BACK_TEXT,
            command=self.app.show_main,
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

        ctk.CTkLabel(
            self,
            text=_VERSION_TEXT,
            font=ctk.CTkFont(size=11),
            text_color=_MUTED_TEXT,
        ).pack(side="bottom", pady=(0, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(8, 8))

        ctk.CTkLabel(
            body,
            text=_THEME_LABEL,
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", pady=(0, 4))
        self._theme_segmented = ctk.CTkSegmentedButton(
            body,
            values=list(_THEME_LABELS_TO_MODES),
            command=self._on_theme_selected,
            height=30,
            font=ctk.CTkFont(size=12),
        )
        self._theme_segmented.pack(fill="x")

        self._autostart_switch = ctk.CTkSwitch(
            body,
            text=_AUTOSTART_LABEL,
            command=self._on_autostart_toggled,
            font=ctk.CTkFont(size=13),
            onvalue=True,
            offvalue=False,
        )
        self._autostart_switch.pack(fill="x", pady=(22, 0))

        ctk.CTkLabel(
            body,
            text=_PIN_LABEL,
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=_MUTED_TEXT,
        ).pack(fill="x", pady=(22, 4))
        self._pin_button = ctk.CTkButton(
            body,
            text=_PIN_UNSET_TEXT,
            command=self._start_pin_flow,
            height=32,
            corner_radius=8,
            fg_color=_SECONDARY_FG,
            hover_color=_SECONDARY_HOVER,
            text_color=_SECONDARY_TEXT,
            font=ctk.CTkFont(size=12),
        )
        self._pin_button.pack(fill="x")
        self._pin_area = ctk.CTkFrame(body, fg_color="transparent")
        self._pin_area.pack(fill="x", pady=(8, 0))

        self._status = ctk.CTkLabel(
            body,
            text="",
            height=16,
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=_STATUS_TEXT,
        )
        self._status.pack(fill="x", pady=(8, 0))

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status.configure(text=text, text_color=_ERROR_TEXT if error else _STATUS_TEXT)

    def _on_theme_selected(self, label: str) -> None:
        mode = _THEME_LABELS_TO_MODES.get(label, "system")
        theme.apply_theme(mode)
        config = self.app.app_config
        config.set("theme_mode", mode)
        config.save()

    def _on_autostart_toggled(self) -> None:
        enabled = bool(self._autostart_switch.get())
        try:
            if enabled:
                autostart.enable()
            else:
                autostart.disable()
        except OSError:
            if enabled:
                self._autostart_switch.deselect()
            else:
                self._autostart_switch.select()
            self._set_status(_AUTOSTART_ERROR, error=True)
            return
        config = self.app.app_config
        config.set("autostart", enabled)
        config.save()
        self._set_status("")

    def _start_pin_flow(self) -> None:
        self._reset_pin_flow()
        self._set_status("")
        if pin.is_pin_set(self.app.app_config):
            self._pin_pad = PinPad(self._pin_area, self._on_current_pin, _PIN_CURRENT_TITLE)
        else:
            self._pin_pad = PinPad(self._pin_area, self._on_new_pin, _PIN_NEW_TITLE)
        self._pin_pad.pack()

    def _on_current_pin(self, entered: str) -> None:
        if not pin.verify_pin(self.app.app_config, entered):
            self._pin_pad.reset()
            self._set_status(_PIN_WRONG_STATUS, error=True)
            return
        self._show_new_pin()

    def _show_new_pin(self) -> None:
        self._clear_pin_area()
        self._pending_pin = None
        self._set_status("")
        self._pin_pad = PinPad(self._pin_area, self._on_new_pin, _PIN_NEW_TITLE)
        self._pin_pad.pack()

    def _on_new_pin(self, entered: str) -> None:
        self._pending_pin = entered
        self._clear_pin_area()
        self._pin_pad = PinPad(self._pin_area, self._on_repeat_pin, _PIN_REPEAT_TITLE)
        self._pin_pad.pack()

    def _on_repeat_pin(self, entered: str) -> None:
        had_pin = pin.is_pin_set(self.app.app_config)
        if entered != self._pending_pin:
            self._show_new_pin()
            self._set_status(_PIN_MISMATCH_STATUS, error=True)
            return
        pin.set_pin(self.app.app_config, entered)
        self._pending_pin = None
        self._clear_pin_area()
        self._update_pin_button()
        self._set_status(_PIN_CHANGED_STATUS if had_pin else _PIN_SET_STATUS)

    def _clear_pin_area(self) -> None:
        for child in self._pin_area.winfo_children():
            child.destroy()
        self._pin_pad = None

    def _reset_pin_flow(self) -> None:
        self._clear_pin_area()
        self._pending_pin = None

    def _update_pin_button(self) -> None:
        if pin.is_pin_set(self.app.app_config):
            self._pin_button.configure(text=_PIN_SET_TEXT)
        else:
            self._pin_button.configure(text=_PIN_UNSET_TEXT)
