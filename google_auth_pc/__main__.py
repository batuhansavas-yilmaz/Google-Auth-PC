from datetime import datetime
from tkinter import messagebox

from google_auth_pc.app import App
from google_auth_pc.config import Config
from google_auth_pc.storage import AccountStore, StorageCorruptError


def _prepare_store(store: AccountStore) -> str | None:
    try:
        store.load()
    except StorageCorruptError:
        backup_name = ""
        if store.path.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = store.path.with_name(f"{store.path.name}.bozuk-{stamp}")
            store.path.replace(backup)
            backup_name = backup.name
        return (
            "Kayıtlı hesaplar dosyası bozuk olduğu için okunamadı. "
            f"Dosya {backup_name} olarak yedeklendi; boş listeyle devam ediliyor. "
            "Hesaplarını telefonundaki Google Authenticator'dan yeniden aktarabilirsin."
        )
    return None


def main() -> None:
    config = Config()
    store = AccountStore()
    warning = _prepare_store(store)
    app = App(config, store)
    if warning is not None:
        app.after(
            200,
            lambda: messagebox.showwarning("Google Auth PC", warning, parent=app),
        )
    app.mainloop()


if __name__ == "__main__":
    main()
