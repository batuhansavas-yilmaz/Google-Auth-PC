import pytest
from google_auth_pc.models import Account
from google_auth_pc import totp

BASE32 = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"  # b32("12345678901234567890")

def test_rfc6238_vector():
    acc = Account(secret=BASE32, name="t", issuer="t")
    assert totp.code_at(acc, at=59.0) == "287082"
    assert totp.code_at(acc, at=1111111109.0) == "081804"

def test_period_boundary_and_remaining():
    acc = Account(secret=BASE32, name="t", issuer="t")
    assert totp.remaining_seconds(acc, at=59.0) == 1
    assert totp.remaining_seconds(acc, at=60.0) == 30
    assert 1 <= totp.remaining_seconds(acc, at=123.456) <= 30

def test_sha256_and_eight_digits():
    acc = Account(secret=BASE32, name="t", issuer="t", digits=8, algorithm="SHA256")
    code = totp.code_at(acc, at=59.0)
    assert len(code) == 8 and code.isdigit()

def test_hotp_returns_none():
    acc = Account(secret=BASE32, name="t", issuer="t", type="hotp")
    assert totp.code_at(acc, at=59.0) is None

def test_normalize_secret():
    assert totp.normalize_secret("jbsw y3dp-ehpk 3pxp") == "JBSWY3DPEHPK3PXP"
    with pytest.raises(ValueError):
        totp.normalize_secret("1888!!")

def test_parse_otpauth_uri():
    acc = totp.parse_otpauth_uri(
        "otpauth://totp/Google:batuhan%40gmail.com?secret=JBSWY3DPEHPK3PXP&issuer=Google")
    assert (acc.issuer, acc.name, acc.secret) == ("Google", "batuhan@gmail.com", "JBSWY3DPEHPK3PXP")
    with pytest.raises(ValueError):
        totp.parse_otpauth_uri("otpauth://totp/x")
