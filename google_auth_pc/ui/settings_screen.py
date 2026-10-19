from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc import __version__, autostart, pin, theme
from google_auth_pc.ui.pin_pad import PinPad

if TYPE_CHECKING:
    from google_auth_pc.app import App

_BACK_TEXT = "← Geri"
_SCREEN_TITLE = "Ayarlar"
_VIEW_LABEL = "Görünüm"
_SECURITY_LABEL = "Güvenlik"
_SYSTEM_LABEL = "Sistem"
_THEME_LABEL = "Tema"
_THEME_LABELS_TO_MODES = {"Otomatik": "system", "Açık": "light", "Koyu": "dark"}
_THEME_MODES_TO_LABELS = {mode: label for label, mode in _THEME_LABELS_TO_MODES.items()}
_FONT_LABEL = "Yazı boyutu"
_FONT_HINT = "Kodlar ve listeler bu boyutta görünür"
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

_FONT_LABELS = {
    0.9: "%90",
    1.0: "Normal (100%)",
    1.15: "%115",
    1.3: "%130",
}


def scale_label(scale: float) -> str:
    return _FONT_LABELS.get(scale, _FONT_LABELS[1.0])


def stepper_state(scale: float) -> tuple[bool, bool]:
    can_minus = scale > theme.FONT_SCALE_STEPS[0]
    can_plus = scale < theme.FONT_SCALE_STEPS[-1]
    return can_minus, can_plus


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master, fg_color=theme.PALETTE["bg"])
        self.app = app
        self._pin_pad: PinPad | None = None
        self._pending_pin: str | None = None
        self._pin_area: ctk.CTkFrame | None = None
        self._pin_button: ctk.CTkButton | None = None
        self._autostart_switch: ctk.CTkSwitch | None = None
        self._font_value: ctk.CTkLabel | None = None
        self._font_minus: ctk.CTkButton | None = None
        self._font_plus: ctk.CTkButton | None = None
        self._status: ctk.CTkLabel | None = None
        self._build()

    def refresh(self) -> None:
        self._reset_pin_flow()
        self._update_pin_button()
        if autostart.is_enabled():
            self._autostart_switch.select()
        else:
            self._autostart_switch.deselect()
        self._sync_theme_buttons()
        self._sync_font_stepper()
        self._set_status("")

    def _build(self) -> None:
        palette = theme.PALETTE
        scale = self.app.font_scale

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=theme.scaled(16, scale), pady=(theme.scaled(14, scale), 4))
        ctk.CTkButton(
            top,
            text=_BACK_TEXT,
            command=self.app.show_main,
            width=theme.scaled(76, scale),
            height=theme.scaled(36, scale),
            corner_radius=theme.scaled(18, scale),
            fg_color=palette["surface_alt"],
            hover_color=palette["row_hover"],
            text_color=palette["text"],
            font=theme.font(14, scale),
        ).pack(side="left")
        ctk.CTkLabel(
            top,
            text=_SCREEN_TITLE,
            font=theme.font(20, scale, weight="bold"),
            text_color=palette["text"],
        ).pack(side="left", padx=(theme.scaled(12, scale), 0))

        ctk.CTkLabel(
            self,
            text=_VERSION_TEXT,
            font=theme.font(12, scale),
            text_color=palette["muted"],
        ).pack(side="bottom", pady=(0, theme.scaled(14, scale)))

        body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            scrollbar_fg_color=palette["bg"],
            scrollbar_button_color=palette["surface_alt"],
            scrollbar_button_hover_color=palette["muted"],
        )
        body.pack(fill="both", expand=True, padx=theme.scaled(16, scale), pady=(4, 8))

        self._section(body, _VIEW_LABEL)
        view_card = self._card(body)
        ctk.CTkLabel(
            view_card,
            text=_THEME_LABEL,
            anchor="w",
            font=theme.font(16, scale),
            text_color=palette["text"],
        ).pack(fill="x", padx=theme.scaled(16, scale), pady=(theme.scaled(14, scale), 6))
        theme_row = ctk.CTkFrame(view_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=theme.scaled(16, scale))
        self._theme_buttons: dict[str, ctk.CTkButton] = {}
        for label in _THEME_LABELS_TO_MODES:
            button = ctk.CTkButton(
                theme_row,
                text=label,
                command=lambda value=label: self._on_theme_selected(value),
                height=theme.scaled(38, scale),
                corner_radius=theme.scaled(19, scale),
                font=theme.font(14, scale),
            )
            button.pack(side="left", fill="x", expand=True, padx=theme.scaled(2, scale))
            self._theme_buttons[label] = button
        ctk.CTkFrame(
            view_card,
            height=1,
            fg_color=palette["divider"],
        ).pack(fill="x", padx=theme.scaled(16, scale), pady=theme.scaled(14, scale))

        ctk.CTkLabel(
            view_card,
            text=_FONT_LABEL,
            anchor="w",
            font=theme.font(16, scale),
            text_color=palette["text"],
        ).pack(fill="x", padx=theme.scaled(16, scale))
        ctk.CTkLabel(
            view_card,
            text=_FONT_HINT,
            anchor="w",
            font=theme.font(12, scale),
            text_color=palette["muted"],
        ).pack(fill="x", padx=theme.scaled(16, scale), pady=(0, theme.scaled(6, scale)))
        stepper = ctk.CTkFrame(view_card, fg_color="transparent")
        stepper.pack(fill="x", padx=theme.scaled(16, scale), pady=(0, theme.scaled(16, scale)))
        control = theme.scaled(40, scale)
        self._font_minus = ctk.CTkButton(
            stepper,
            text="A−",
            command=lambda: self._on_font_step(-1),
            width=control,
            height=control,
            corner_radius=control // 2,
            fg_color=palette["surface_alt"],
            hover_color=palette["row_hover"],
            text_color=palette["text"],
            font=theme.font(15, scale, weight="bold"),
        )
        self._font_minus.pack(side="left")
        self._font_value = ctk.CTkLabel(
            stepper,
            text=scale_label(scale),
            fg_color=palette["search_fill"],
            corner_radius=theme.scaled(18, scale),
            height=theme.scaled(36, scale),
            font=theme.font(15, scale, weight="bold"),
            text_color=palette["accent"],
        )
        self._font_value.pack(side="left", fill="x", expand=True, padx=8)
        self._font_plus = ctk.CTkButton(
            stepper,
            text="A+",
            command=lambda: self._on_font_step(1),
            width=control,
            height=control,
            corner_radius=control // 2,
            fg_color=palette["surface_alt"],
            hover_color=palette["row_hover"],
            text_color=palette["text"],
            font=theme.font(15, scale, weight="bold"),
        )
        self._font_plus.pack(side="left")

        self._section(body, _SECURITY_LABEL)
        security_card = self._card(body)
        pin_row = ctk.CTkFrame(security_card, fg_color="transparent")
        pin_row.pack(fill="x", padx=theme.scaled(16, scale), pady=theme.scaled(14, scale))
        pin_text = ctk.CTkFrame(pin_row, fg_color="transparent")
        pin_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            pin_text,
            text=_PIN_LABEL,
            anchor="w",
            font=theme.font(15, scale),
            text_color=palette["text"],
        ).pack(fill="x")
        self._pin_button = ctk.CTkButton(
            pin_row,
            text=_PIN_UNSET_TEXT,
            command=self._start_pin_flow,
            width=theme.scaled(120, scale),
            height=theme.scaled(34, scale),
            corner_radius=theme.scaled(17, scale),
            fg_color=palette["surface_alt"],
            hover_color=palette["row_hover"],
            text_color=palette["accent"],
            font=theme.font(13, scale),
        )
        self._pin_button.pack(side="right")
        self._pin_area = ctk.CTkFrame(security_card, fg_color="transparent")

        self._status = ctk.CTkLabel(
            body,
            text="",
            height=theme.scaled(18, scale),
            anchor="w",
            font=theme.font(12, scale),
            text_color=palette["success"],
        )
        self._status.pack(fill="x", pady=(theme.scaled(6, scale), 0))

        self._section(body, _SYSTEM_LABEL)
        system_card = self._card(body)
        self._autostart_switch = ctk.CTkSwitch(
            system_card,
            text=_AUTOSTART_LABEL,
            command=self._on_autostart_toggled,
            font=theme.font(15, scale),
            text_color=palette["text"],
            progress_color=palette["accent"],
            button_color=palette["surface"],
            button_hover_color=palette["surface_alt"],
            onvalue=True,
            offvalue=False,
        )
        self._autostart_switch.pack(fill="x", padx=theme.scaled(16, scale), pady=theme.scaled(16, scale))

        self._sync_font_stepper()

    def _section(self, parent, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            font=theme.font(13, self.app.font_scale, weight="bold"),
            text_color=theme.PALETTE["accent"],
        ).pack(fill="x", padx=theme.scaled(6, self.app.font_scale), pady=(theme.scaled(10, self.app.font_scale), theme.scaled(6, self.app.font_scale)))

    def _card(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            corner_radius=theme.scaled(16, self.app.font_scale),
            fg_color=theme.PALETTE["surface"],
            border_width=1,
            border_color=theme.PALETTE["divider"],
        )
        frame.pack(fill="x", pady=(0, theme.scaled(8, self.app.font_scale)))
        return frame

    def _sync_theme_buttons(self) -> None:
        palette = theme.PALETTE
        mode = self.app.app_config.get("theme_mode", "system")
        active = _THEME_MODES_TO_LABELS.get(mode, "Otomatik")
        for label, button in self._theme_buttons.items():
            if label == active:
                button.configure(
                    fg_color=palette["accent"],
                    hover_color=palette["accent"],
                    text_color=palette["on_accent"],
                )
            else:
                button.configure(
                    fg_color=palette["surface_alt"],
                    hover_color=palette["row_hover"],
                    text_color=palette["text"],
                )

    def _sync_font_stepper(self) -> None:
        scale = self.app.font_scale
        if self._font_value is None:
            return
        self._font_value.configure(text=scale_label(scale))
        can_minus, can_plus = stepper_state(scale)
        self._font_minus.configure(state="normal" if can_minus else "disabled")
        self._font_plus.configure(state="normal" if can_plus else "disabled")

    def _on_font_step(self, delta: int) -> None:
        target = theme.step_scale(self.app.font_scale, delta)
        if target == self.app.font_scale:
            return
        self.app.set_font_scale(target)

    def _set_status(self, text: str, error: bool = False) -> None:
        palette = theme.PALETTE
        self._status.configure(
            text=text,
            text_color=palette["danger"] if error else palette["success"],
        )

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
        self._pin_area.pack(
            fill="x",
            padx=theme.scaled(16, self.app.font_scale),
            pady=(0, theme.scaled(10, self.app.font_scale)),
        )
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
        self._pin_area.pack_forget()
        self._pin_pad = None

    def _reset_pin_flow(self) -> None:
        self._clear_pin_area()
        self._pending_pin = None

    def _update_pin_button(self) -> None:
        if pin.is_pin_set(self.app.app_config):
            self._pin_button.configure(text=_PIN_SET_TEXT)
        else:
            self._pin_button.configure(text=_PIN_UNSET_TEXT)
