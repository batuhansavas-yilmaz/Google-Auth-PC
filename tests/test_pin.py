import base64
import hashlib

import pytest

from google_auth_pc.config import Config
from google_auth_pc import pin

def test_set_verify_clear(tmp_path):
    cfg = Config(tmp_path / "c.json")
    assert pin.is_pin_set(cfg) is False
    pin.set_pin(cfg, "123456")
    assert pin.is_pin_set(cfg) and pin.verify_pin(cfg, "123456")
    assert not pin.verify_pin(cfg, "000000")
    pin.clear_pin(cfg)
    assert not pin.is_pin_set(cfg)

def test_rejects_bad_format(tmp_path):
    cfg = Config(tmp_path / "c.json")
    with pytest.raises(ValueError):
        pin.set_pin(cfg, "12345")
    with pytest.raises(ValueError):
        pin.set_pin(cfg, "abcdef")

def test_pin_persists_across_reload(tmp_path):
    path = tmp_path / "c.json"
    pin.set_pin(Config(path), "654321")
    assert pin.verify_pin(Config(path), "654321")

def test_verify_without_pin_is_false(tmp_path):
    cfg = Config(tmp_path / "c.json")
    assert pin.verify_pin(cfg, "123456") is False

def test_stored_pin_uses_pbkdf2_spec(tmp_path):
    cfg = Config(tmp_path / "c.json")
    pin.set_pin(cfg, "123456")
    stored = cfg.get("pin")
    assert stored["iterations"] == 200000
    salt = base64.b64decode(stored["salt_b64"])
    assert len(salt) == 16
    expected = hashlib.pbkdf2_hmac("sha256", b"123456", salt, 200000)
    assert base64.b64decode(stored["hash_b64"]) == expected
