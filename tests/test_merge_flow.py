import subprocess
import sys

from google_auth_pc.importer import ImportResult
from google_auth_pc.models import Account
from google_auth_pc.storage import AccountStore
from google_auth_pc.ui.import_screen import apply_import

SECRET_EXISTING = "JBSWY3DPEHPK3PXP"
SECRET_NEW = "KRSXG5CTMVRXEZLU"


def acc(secret, name="n", issuer="i"):
    return Account(secret=secret, name=name, issuer=issuer)


def result_of(*accounts: Account) -> ImportResult:
    return ImportResult(accounts=list(accounts), failed_files=[], skipped_payloads=0)


def test_apply_import_adds_new_and_skips_duplicate(tmp_path):
    store = AccountStore(tmp_path / "accounts.enc")
    existing = acc(SECRET_EXISTING, name="duzenlenmis ad", issuer="Duzenlenmis servis")
    store.save([existing])

    added, skipped = apply_import(
        store,
        result_of(
            acc(SECRET_EXISTING, name="telefondan gelen"),
            acc(SECRET_NEW, name="yeni hesap"),
        ),
    )

    assert (added, skipped) == (1, 1)
    stored = store.load()
    assert len(stored) == 2
    assert stored[0] == existing
    assert stored[1] == acc(SECRET_NEW, name="yeni hesap")


def test_apply_import_skips_malformed_secret(tmp_path):
    store = AccountStore(tmp_path / "accounts.enc")

    added, skipped = apply_import(
        store,
        result_of(acc("ABC0", name="bozuk"), acc(SECRET_NEW)),
    )

    assert (added, skipped) == (1, 1)
    assert store.load() == [acc(SECRET_NEW)]


def test_importing_import_screen_does_not_load_cv2():
    probe = (
        "import sys; import google_auth_pc.ui.import_screen; "
        "assert 'cv2' not in sys.modules"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr
