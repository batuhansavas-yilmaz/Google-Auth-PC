import pytest

from google_auth_pc.models import Account
from google_auth_pc import migration
from tests.helpers import build_migration_payload, build_migration_uri, field

SECRET_A = "JBSWY3DPEHPK3PXP"
SECRET_B = "KRSXG5CTMVRXEZLU"


def entry(secret, name, issuer, **extra):
    return {"secret": secret, "name": name, "issuer": issuer, **extra}


def acc(secret, name="n", issuer="i"):
    return Account(secret=secret, name=name, issuer=issuer)


def test_parse_two_accounts_from_uri():
    entries = [
        entry("jbsw y3dp-ehpk 3pxp", "alice@example.com", "Example"),
        entry(SECRET_B, "bob@example.com", "Work"),
    ]
    accounts = migration.parse_migration_uri(build_migration_uri(entries))
    assert accounts == [
        Account(secret=SECRET_A, name="alice@example.com", issuer="Example"),
        Account(secret=SECRET_B, name="bob@example.com", issuer="Work"),
    ]
    assert all(
        a.digits == 6 and a.algorithm == "SHA1" and a.type == "totp" for a in accounts
    )


def test_explicit_algorithm_digits_and_totp_codes():
    entries = [
        entry(SECRET_A, "alice@example.com", "Example", algorithm=2, digits=2, type=2)
    ]
    (account,) = migration.parse_migration_payload(build_migration_payload(entries))
    assert (account.algorithm, account.digits, account.type) == ("SHA256", 8, "totp")


def test_unspecified_codes_default():
    entries = [
        entry(SECRET_A, "alice@example.com", "Example", algorithm=0, digits=0, type=0)
    ]
    (account,) = migration.parse_migration_payload(build_migration_payload(entries))
    assert (account.algorithm, account.digits, account.type) == ("SHA1", 6, "totp")


def test_hotp_type_and_counter():
    entries = [entry(SECRET_A, "legacy@example.com", "Legacy", type=1, counter=300)]
    (account,) = migration.parse_migration_uri(build_migration_uri(entries))
    assert account.type == "hotp"
    assert account.counter == 300


def test_payload_metadata_and_unknown_entry_fields_are_skipped():
    entry_bytes = (
        field(1, 2, SECRET_A.encode("ascii"))
        + field(2, 2, "alice@example.com")
        + field(3, 2, "Example")
        + field(4, 0, 1)
        + field(5, 0, 1)
        + field(6, 0, 2)
        + field(9, 0, 7)
        + field(10, 2, b"bilinmeyen")
    )
    payload = (
        field(1, 2, entry_bytes)
        + field(2, 0, 1)
        + field(3, 0, 1)
        + field(4, 0, 0)
        + field(5, 0, 42)
    )
    assert migration.parse_migration_payload(payload) == [
        Account(secret=SECRET_A, name="alice@example.com", issuer="Example")
    ]


def test_corrupt_base64_raises():
    with pytest.raises(migration.MigrationParseError):
        migration.parse_migration_uri("otpauth-migration://offline?data=!!!")


def test_truncated_payload_raises():
    payload = build_migration_payload([entry(SECRET_A, "alice@example.com", "Example")])
    with pytest.raises(migration.MigrationParseError):
        migration.parse_migration_payload(payload[:-1])


def test_truncated_varint_raises():
    with pytest.raises(migration.MigrationParseError):
        migration.parse_migration_payload(b"\x80")


def test_missing_secret_raises():
    payload = build_migration_payload(
        [{"name": "alice@example.com", "issuer": "Example"}]
    )
    with pytest.raises(migration.MigrationParseError):
        migration.parse_migration_payload(payload)


def test_wrong_scheme_raises():
    with pytest.raises(migration.MigrationParseError):
        migration.parse_migration_uri("otpauth://totp/x?secret=" + SECRET_A)


def test_merge_skips_existing_and_keeps_user_edit():
    existing = [acc(SECRET_A, name="edited", issuer="Edited")]
    incoming = [
        acc(SECRET_A, name="alice@example.com", issuer="Example"),
        acc(SECRET_B),
    ]
    result = migration.merge_accounts(existing, incoming)
    assert result.added == [acc(SECRET_B)]
    assert result.skipped == [incoming[0]]
    assert existing == [acc(SECRET_A, name="edited", issuer="Edited")]


def test_merge_batch_first_occurrence_wins():
    first = acc(SECRET_A, name="first")
    second = acc(SECRET_A, name="second")
    result = migration.merge_accounts([], [first, second])
    assert result.added == [first]
    assert result.skipped == [second]
