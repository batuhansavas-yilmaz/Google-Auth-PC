import base64
import hashlib
import re
import time
import urllib.parse

import pyotp

from google_auth_pc.models import Account

_DIGESTS = {
    "SHA1": hashlib.sha1,
    "SHA256": hashlib.sha256,
    "SHA512": hashlib.sha512,
}


def normalize_secret(raw: str) -> str:
    cleaned = re.sub(r"[\s\-=]", "", raw).upper()
    if not cleaned:
        raise ValueError("Bos secret")
    padded = cleaned + "=" * (-len(cleaned) % 8)
    try:
        base64.b32decode(padded)
    except ValueError as exc:
        raise ValueError(f"Gecersiz secret: {raw!r}") from exc
    return cleaned


def parse_otpauth_uri(uri: str) -> Account:
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != "otpauth":
        raise ValueError(f"Gecersiz otpauth adresi: {uri!r}")
    account_type = parsed.netloc.lower()
    if account_type not in ("totp", "hotp"):
        raise ValueError(f"Desteklenmeyen hesap turu: {account_type!r}")

    label = urllib.parse.unquote(parsed.path.lstrip("/")).strip()
    if not label:
        raise ValueError("Etiket eksik")
    label_issuer = ""
    if ":" in label:
        label_issuer, label = (part.strip() for part in label.split(":", 1))
    if not label:
        raise ValueError("Hesap adi eksik")

    query = urllib.parse.parse_qs(parsed.query)
    secret_raw = query.get("secret", [""])[0]
    if not secret_raw:
        raise ValueError("secret parametresi eksik")
    secret = normalize_secret(secret_raw)

    issuer = query.get("issuer", [""])[0] or label_issuer
    try:
        digits = int(query.get("digits", ["6"])[0])
        period = int(query.get("period", ["30"])[0])
        counter = int(query.get("counter", ["0"])[0])
    except ValueError as exc:
        raise ValueError("Sayisal parametre gecersiz") from exc
    algorithm = query.get("algorithm", ["SHA1"])[0].upper()

    return Account(
        secret=secret,
        name=label,
        issuer=issuer,
        digits=digits,
        period=period,
        algorithm=algorithm,
        type=account_type,
        counter=counter,
    )


def code_at(account: Account, at: float | None = None) -> str | None:
    if account.type != "totp":
        return None
    digest = _DIGESTS.get(account.algorithm.upper())
    if digest is None:
        raise ValueError(f"Desteklenmeyen algoritma: {account.algorithm!r}")
    moment = time.time() if at is None else at
    return pyotp.TOTP(
        account.secret,
        digits=account.digits,
        interval=account.period,
        digest=digest,
    ).at(moment)


def remaining_seconds(account: Account, at: float | None = None) -> int:
    moment = time.time() if at is None else at
    return account.period - int(moment) % account.period
