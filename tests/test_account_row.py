import customtkinter as ctk
import pytest

from google_auth_pc.models import Account
from google_auth_pc.ui.account_row import AccountRow, format_code, resolve_gesture


@pytest.fixture()
def root():
    window = ctk.CTk()
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture(autouse=True)
def _restore_font_scale():
    from google_auth_pc import theme

    original = theme.font_scale
    yield
    theme.set_font_scale(original)


def _row(root, name, issuer="", scale=1.0, digits=6, account_type="totp"):
    account = Account(
        secret="JBSWY3DPEHPK3PXP",
        name=name,
        issuer=issuer,
        digits=digits,
        type=account_type,
    )
    row = AccountRow(
        root,
        account,
        scale=scale,
        on_copy=lambda _account: None,
        on_edit=lambda _account: None,
        on_delete=lambda _account: None,
    )
    row.pack(fill="x")
    row.update_idletasks()
    return row


def test_format_code_splits_six_and_eight_digits():
    assert format_code("123456") == "123 456"
    assert format_code("12345678") == "1234 5678"


@pytest.mark.parametrize(
    ("dx", "dy", "expected"),
    [
        (-120, 4, "delete"),
        (120, 4, "edit"),
        (3, 2, "copy"),
        (-40, 2, "none"),
        (-150, 200, "none"),
        (96, 0, "edit"),
        (-96, 0, "delete"),
        (95, 0, "none"),
        (11, 11, "copy"),
        (12, 12, "none"),
        (0, 40, "none"),
    ],
)
def test_resolve_gesture(dx, dy, expected):
    assert resolve_gesture(dx, dy) == expected


@pytest.mark.parametrize("scale", [1.0, 1.3])
def test_long_email_is_shown_in_full_and_wraps(root, scale):
    email = "very.long.email.address.for.testing.account.row@subdomain.example-company.com"

    row = _row(root, email, issuer="Example", scale=scale)

    assert row._name_label.cget("text") == email
    assert "…" not in row._name_label.cget("text")
    assert int(row._name_label.cget("wraplength")) > 0


def test_hotp_row_shows_unsupported_and_has_no_bar(root):
    row = _row(root, "HOTP hesabı", issuer="", account_type="hotp")

    row.tick()

    assert row._code_label.cget("text") == "desteklenmiyor"
    assert row._bar_canvas is None
