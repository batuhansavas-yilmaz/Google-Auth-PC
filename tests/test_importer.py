import subprocess
import sys

import segno
from PIL import Image

from google_auth_pc import importer
from google_auth_pc.models import Account
from tests.helpers import build_migration_uri

SECRET_A = "JBSWY3DPEHPK3PXP"
SECRET_B = "KRSXG5CTMVRXEZLU"


def entry(secret, name, issuer, **extra):
    return {"secret": secret, "name": name, "issuer": issuer, **extra}


def acc(secret, name="n", issuer="i"):
    return Account(secret=secret, name=name, issuer=issuer)


def save_qr(path, content):
    segno.make(content, micro=False).save(path, scale=4)
    return path


def test_valid_png_yields_accounts(tmp_path):
    path = save_qr(
        tmp_path / "export.png",
        build_migration_uri(
            [
                entry(SECRET_A, "alice@example.com", "Example"),
                entry(SECRET_B, "bob@example.com", "Work"),
            ]
        ),
    )
    result = importer.extract_migration_accounts([path])
    assert result.accounts == [
        acc(SECRET_A, "alice@example.com", "Example"),
        acc(SECRET_B, "bob@example.com", "Work"),
    ]
    assert result.failed_files == []
    assert result.skipped_payloads == 0


def test_blank_png_is_failed_file(tmp_path):
    path = tmp_path / "blank.png"
    Image.new("RGB", (240, 240), "white").save(path)
    result = importer.extract_migration_accounts([path])
    assert result.accounts == []
    assert result.failed_files == [path]
    assert result.skipped_payloads == 0


def test_mixed_valid_and_corrupt_files(tmp_path):
    valid = save_qr(
        tmp_path / "valid.png",
        build_migration_uri([entry(SECRET_A, "alice@example.com", "Example")]),
    )
    corrupt = tmp_path / "bozuk.png"
    corrupt.write_bytes(b"bu bir gorsel degil")
    result = importer.extract_migration_accounts([valid, corrupt])
    assert result.accounts == [acc(SECRET_A, "alice@example.com", "Example")]
    assert result.failed_files == [corrupt]
    assert result.skipped_payloads == 0


def test_same_secret_in_two_images_yields_single_account(tmp_path):
    first = save_qr(
        tmp_path / "bir.png",
        build_migration_uri([entry(SECRET_A, "ilk@example.com", "Example")]),
    )
    second = save_qr(
        tmp_path / "iki.png",
        build_migration_uri([entry(SECRET_A, "ikinci@example.com", "Example")]),
    )
    result = importer.extract_migration_accounts([first, second])
    assert result.accounts == [acc(SECRET_A, "ilk@example.com", "Example")]
    assert result.failed_files == []
    assert result.skipped_payloads == 0


def test_non_migration_qr_is_counted_as_skipped(tmp_path):
    path = save_qr(tmp_path / "site.png", "https://example.com/giris")
    result = importer.extract_migration_accounts([path])
    assert result.accounts == []
    assert result.failed_files == []
    assert result.skipped_payloads == 1


def test_corrupt_migration_payload_is_skipped(tmp_path):
    path = save_qr(tmp_path / "bozuk-payload.png", "otpauth-migration://offline?data=!!!")
    result = importer.extract_migration_accounts([path])
    assert result.accounts == []
    assert result.failed_files == []
    assert result.skipped_payloads == 1


def test_non_ascii_path_yields_accounts(tmp_path):
    path = save_qr(
        tmp_path / "şifreler.png",
        build_migration_uri([entry(SECRET_A, "alice@example.com", "Example")]),
    )
    result = importer.extract_migration_accounts([path])
    assert result.accounts == [acc(SECRET_A, "alice@example.com", "Example")]
    assert result.failed_files == []
    assert result.skipped_payloads == 0


def test_importing_importer_does_not_load_cv2():
    probe = "import sys; import google_auth_pc.importer; assert 'cv2' not in sys.modules"
    completed = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr
