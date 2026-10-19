import re
import tkinter

import customtkinter as ctk

from google_auth_pc import theme, tray
from google_auth_pc.config import Config
from google_auth_pc.storage import AccountStore
from google_auth_pc.ui.import_screen import ImportScreen
from google_auth_pc.ui.intro_screen import IntroScreen
from google_auth_pc.ui.lock_screen import LockScreen
from google_auth_pc.ui.main_screen import MainScreen
from google_auth_pc.ui.settings_screen import SettingsScreen

_GEOMETRY_SAVE_DELAY_MS = 250
_GEOMETRY_RE = re.compile(r"^(\d+)x(\d+)([+-]\d+)([+-]\d+)$")


class App(ctk.CTk):
    def __init__(self, config: Config, store: AccountStore):
        super().__init__()
        self.app_config = config
        self.store = store
        self._locked = True
        self._pending_screen: str | None = None
        self._tray = None
        self._geometry_job: str | None = None
        self._closing = False
        self._screens: dict[str, ctk.CTkFrame] = {}
        theme.apply_theme(config.get("theme_mode", "system"))
        self.title("Google Auth PC")
        self.geometry("400x820")
        self._apply_saved_geometry()
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self._lock_screen = LockScreen(self, self)
        self._screens["lock"] = self._lock_screen
        self._main_screen = MainScreen(self, self)
        self._screens["main"] = self._main_screen
        self._import_screen = ImportScreen(self, self)
        self._screens["import"] = self._import_screen
        self._settings_screen = SettingsScreen(self, self)
        self._screens["settings"] = self._settings_screen
        self._intro_screen = IntroScreen(self, self, on_done=self._finish_intro)
        self._screens["intro"] = self._intro_screen
        self.bind("<Map>", self._on_window_mapped, add="+")
        self.show_screen("lock")
        self._tray = tray.start_tray(
            on_open=lambda: self._post_ui(self.show_window),
            on_lock=lambda: self._post_ui(self.lock),
            on_settings=lambda: self._post_ui(self.show_settings),
            on_quit=lambda: self._post_ui(self.quit_app),
        )

    @property
    def is_locked(self) -> bool:
        return self._locked

    def lock(self) -> None:
        self._locked = True
        self._lock_screen.refresh()
        self.show_screen("lock")

    def unlock_session(self) -> None:
        self._locked = False
        pending = self._pending_screen
        self._pending_screen = None
        if pending == "settings" and self.app_config.get("first_run_done"):
            self.show_screen("settings")
            return
        self.show_main()

    def show_main(self) -> None:
        if not self.app_config.get("first_run_done"):
            self.show_screen("intro")
            return
        self._main_screen.reload()
        self.show_screen("main")

    def _finish_intro(self) -> None:
        self.app_config.set("first_run_done", True)
        self.app_config.save()
        self.show_main()

    def show_screen(self, name: str) -> None:
        if name == "lock":
            self._locked = True
        if self._locked and name != "lock":
            return
        screen = self._screens.get(name)
        if screen is None:
            return
        if name == "settings":
            self._settings_screen.refresh()
        for other in self._screens.values():
            if other is not screen:
                other.pack_forget()
        screen.pack(fill="both", expand=True)

    def hide_to_tray(self) -> None:
        self._schedule_geometry_save()
        self.withdraw()
        self.lock()

    def show_window(self) -> None:
        self._pending_screen = None
        self._restore_window()

    def show_settings(self) -> None:
        self._pending_screen = "settings"
        self._restore_window()

    def quit_app(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._cancel_geometry_save()
        self._save_geometry()
        self._stop_tray()
        self.destroy()

    def _on_window_mapped(self, event) -> None:
        if event.widget is not self:
            return
        self.lock()

    def _restore_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        self.lock()

    def _post_ui(self, func) -> None:
        try:
            self.after(0, func)
        except (tkinter.TclError, RuntimeError):
            pass

    def _stop_tray(self) -> None:
        icon = self._tray
        self._tray = None
        if icon is not None:
            icon.stop()

    def _schedule_geometry_save(self) -> None:
        self._cancel_geometry_save()
        if self._closing:
            return
        self._geometry_job = self.after(
            _GEOMETRY_SAVE_DELAY_MS, self._save_geometry
        )

    def _cancel_geometry_save(self) -> None:
        if self._geometry_job is None:
            return
        try:
            self.after_cancel(self._geometry_job)
        except tkinter.TclError:
            pass
        self._geometry_job = None

    def _save_geometry(self) -> None:
        self._geometry_job = None
        spec = self.geometry()
        if not spec or spec == self.app_config.get("geometry"):
            return
        self.app_config.set("geometry", spec)
        self.app_config.save()

    def _apply_saved_geometry(self) -> None:
        parsed = self._parse_geometry(self.app_config.get("geometry", ""))
        if parsed is None:
            return
        width, height, x, y = parsed
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = min(width, screen_width)
        height = min(height, screen_height)
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _parse_geometry(self, spec: str) -> tuple[int, int, int, int] | None:
        match = _GEOMETRY_RE.match(spec.strip()) if spec else None
        if match is None:
            return None
        width, height = int(match.group(1)), int(match.group(2))
        x_text, y_text = match.group(3), match.group(4)
        x = int(x_text[1:])
        if x_text[0] == "-":
            x = self.winfo_screenwidth() - width - x
        y = int(y_text[1:])
        if y_text[0] == "-":
            y = self.winfo_screenheight() - height - y
        return width, height, x, y
