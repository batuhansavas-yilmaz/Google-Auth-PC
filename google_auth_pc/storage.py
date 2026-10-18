import json
import os
from pathlib import Path

from google_auth_pc import dpapi, paths
from google_auth_pc.models import Account


class StorageCorruptError(Exception):
    ...


class AccountStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else paths.accounts_file()

    def load(self) -> list[Account]:
        if not self.path.exists():
            return []
        try:
            raw = dpapi.unprotect(self.path.read_bytes())
            data = json.loads(raw.decode("utf-8"))
            return [Account.from_dict(item) for item in data]
        except (OSError, ValueError, TypeError, dpapi.DpapiError) as exc:
            raise StorageCorruptError(f"Hesap dosyasi okunamadi: {self.path}") from exc

    def save(self, accounts) -> None:
        payload = json.dumps([a.to_dict() for a in accounts], ensure_ascii=False)
        blob = dpapi.protect(payload.encode("utf-8"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".enc.tmp")
        try:
            tmp.write_bytes(blob)
            os.replace(tmp, self.path)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise
