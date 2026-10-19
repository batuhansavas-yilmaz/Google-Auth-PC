import base64
import urllib.parse
from dataclasses import dataclass

from google_auth_pc.models import Account
from google_auth_pc.totp import normalize_secret


class MigrationParseError(ValueError):
    pass


@dataclass
class MergeResult:
    added: list[Account]
    skipped: list[Account]


_ALGORITHMS = {0: "SHA1", 1: "SHA1", 2: "SHA256", 3: "SHA512"}
_DIGITS = {0: 6, 1: 6, 2: 8}
_TYPES = {0: "totp", 1: "hotp", 2: "totp"}


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise MigrationParseError("Kesik veri")
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if byte < 0x80:
            return result, pos
        shift += 7
        if shift > 63:
            raise MigrationParseError("Gecersiz varint")


def _read_fields(data: bytes):
    pos = 0
    while pos < len(data):
        key, pos = _read_varint(data, pos)
        tag = key >> 3
        wire = key & 0x07
        if wire == 0:
            value, pos = _read_varint(data, pos)
        elif wire == 1:
            if pos + 8 > len(data):
                raise MigrationParseError("Kesik veri")
            value = data[pos : pos + 8]
            pos += 8
        elif wire == 2:
            length, pos = _read_varint(data, pos)
            if pos + length > len(data):
                raise MigrationParseError("Kesik veri")
            value = data[pos : pos + length]
            pos += length
        elif wire == 5:
            if pos + 4 > len(data):
                raise MigrationParseError("Kesik veri")
            value = data[pos : pos + 4]
            pos += 4
        else:
            raise MigrationParseError(f"Desteklenmeyen wire tipi: {wire}")
        yield tag, wire, value


def _decode_text(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationParseError("Gecersiz metin kodlamasi") from exc


def _parse_entry(data: bytes) -> Account:
    secret_raw = b""
    name = ""
    issuer = ""
    algorithm = 0
    digits = 0
    account_type = 0
    counter = 0
    for tag, wire, value in _read_fields(data):
        if wire == 2 and tag == 1:
            secret_raw = value
        elif wire == 2 and tag == 2:
            name = _decode_text(value)
        elif wire == 2 and tag == 3:
            issuer = _decode_text(value)
        elif wire == 0 and tag == 4:
            algorithm = value
        elif wire == 0 and tag == 5:
            digits = value
        elif wire == 0 and tag == 6:
            account_type = value
        elif wire == 0 and tag == 7:
            counter = value

    if algorithm not in _ALGORITHMS:
        raise MigrationParseError(f"Gecersiz algoritma kodu: {algorithm}")
    if digits not in _DIGITS:
        raise MigrationParseError(f"Gecersiz hane kodu: {digits}")
    if account_type not in _TYPES:
        raise MigrationParseError(f"Gecersiz hesap turu kodu: {account_type}")
    try:
        secret = normalize_secret(base64.b32encode(secret_raw).decode("ascii"))
    except ValueError as exc:
        raise MigrationParseError(f"Gecersiz secret: {exc}") from exc

    return Account(
        secret=secret,
        name=name,
        issuer=issuer,
        digits=_DIGITS[digits],
        algorithm=_ALGORITHMS[algorithm],
        type=_TYPES[account_type],
        counter=counter,
    )


def parse_migration_payload(data: bytes) -> list[Account]:
    accounts: list[Account] = []
    for tag, wire, value in _read_fields(data):
        if tag == 1:
            if wire != 2:
                raise MigrationParseError("OtpParameters alani beklenen formatta degil")
            accounts.append(_parse_entry(value))
    return accounts


def parse_migration_uri(uri: str) -> list[Account]:
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != "otpauth-migration":
        raise MigrationParseError(f"Gecersiz migration adresi: {uri!r}")
    data_param = urllib.parse.parse_qs(parsed.query).get("data", [""])[0]
    if not data_param:
        raise MigrationParseError("data parametresi eksik")
    data_param = data_param.replace(" ", "+")
    data_param += "=" * (-len(data_param) % 4)
    try:
        raw = base64.b64decode(data_param, validate=True)
    except ValueError as exc:
        raise MigrationParseError(f"Gecersiz base64 veri: {exc}") from exc
    return parse_migration_payload(raw)


def merge_accounts(existing: list[Account], incoming: list[Account]) -> MergeResult:
    seen = {account.secret for account in existing}
    added: list[Account] = []
    skipped: list[Account] = []
    for account in incoming:
        if account.secret in seen:
            skipped.append(account)
        else:
            seen.add(account.secret)
            added.append(account)
    return MergeResult(added=added, skipped=skipped)
