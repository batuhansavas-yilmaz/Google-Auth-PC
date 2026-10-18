import customtkinter as ctk

from google_auth_pc import theme
from google_auth_pc.config import Config
from google_auth_pc.storage import AccountStore
from google_auth_pc.ui.lock_screen import LockScreen
from google_auth_pc.ui.main_screen import MainScreen


class App(ctk.CTk):
    def __init__(self, config: Config, store: AccountStore):
        super().__init__()
        self.app_config = config
        self.store = store
        self._locked = True
        self._screens: dict[str, ctk.CTkFrame] = {}
        theme.apply_theme(config.get("theme_mode", "system"))
        self.title("Google Auth PC")
        self.geometry("400x820")
        self._lock_screen = LockScreen(self, self)
        self._screens["lock"] = self._lock_screen
        self._main_screen = MainScreen(self, self)
        self._screens["main"] = self._main_screen
        self.show_screen("lock")

    @property
    def is_locked(self) -> bool:
        return self._locked

    def lock(self) -> None:
        self._locked = True
        self._lock_screen.refresh()
        self.show_screen("lock")

    def unlock_session(self) -> None:
        self._locked = False
        self._main_screen.reload()
        self.show_screen("main")

    def show_screen(self, name: str) -> None:
        if name == "lock":
            self._locked = True
        if self._locked and name != "lock":
            return
        screen = self._screens.get(name)
        if screen is None:
            return
        for other in self._screens.values():
            if other is not screen:
                other.pack_forget()
        screen.pack(fill="both", expand=True)
