import json
import os
from pathlib import Path

from google_auth_pc import paths

DEFAULTS = {
    "theme_mode": "system",
    "autostart": True,
    "geometry": "",
    "first_run_done": False,
    "pin": None,
}


class Config:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else paths.config_file()
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            loaded = None
        if isinstance(loaded, dict):
            self._data.update(loaded)
            return
        backup = self.path.with_name(self.path.name + ".bozuk")
        backup.unlink(missing_ok=True)
        self.path.replace(backup)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value) -> None:
        self._data[key] = value

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp, self.path)
