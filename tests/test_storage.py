import os
import pytest
from google_auth_pc.models import Account
from google_auth_pc.storage import AccountStore, StorageCorruptError

def acc(secret="JBSWY3DPEHPK3PXP", name="a", issuer="b"):
    return Account(secret=secret, name=name, issuer=issuer)

def test_missing_file_is_empty(tmp_path):
    assert AccountStore(tmp_path / "accounts.enc").load() == []

def test_roundtrip_and_no_plaintext(tmp_path):
    path = tmp_path / "accounts.enc"
    store = AccountStore(path)
    store.save([acc()])
    assert store.load() == [acc()]
    raw = path.read_bytes()
    assert b"JBSWY3DPEHPK3PXP" not in raw and "JBSWY3DPEHPK3PXP".encode("utf-16-le") not in raw

def test_corrupt_raises(tmp_path):
    path = tmp_path / "accounts.enc"
    path.write_bytes(b"cop")
    with pytest.raises(StorageCorruptError):
        AccountStore(path).load()

def test_save_atomic_on_failure(tmp_path, monkeypatch):
    path = tmp_path / "accounts.enc"
    store = AccountStore(path)
    store.save([acc()])
    before = path.read_bytes()
    monkeypatch.setattr(os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        store.save([acc(secret="KRSXG5CTMVRXEZLU")])
    assert path.read_bytes() == before
    assert list(tmp_path.glob("*.tmp")) == []
