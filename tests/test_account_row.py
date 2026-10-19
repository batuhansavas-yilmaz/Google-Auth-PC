import customtkinter as ctk
import pytest

from google_auth_pc import theme
from google_auth_pc.models import Account
from google_auth_pc.ui.account_row import AccountRow, format_code


@pytest.fixture()
def root():
    window = ctk.CTk()
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture(autouse=True)
def _restore_font_scale():
    original = theme.font_scale
    yield
    theme.set_font_scale(original)


def _row(
    root,
    name,
    issuer="",
    scale=1.0,
    digits=6,
    account_type="totp",
    on_copy=None,
    on_edit=None,
    on_delete=None,
):
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
        on_copy=on_copy if on_copy is not None else (lambda _account: None),
        on_edit=on_edit if on_edit is not None else (lambda _account: None),
        on_delete=on_delete if on_delete is not None else (lambda _account: None),
    )
    row.pack(fill="x")
    root.update_idletasks()
    row._sync_height()
    root.update_idletasks()
    return row


def test_format_code_splits_six_and_eight_digits():
    assert format_code("123456") == "123 456"
    assert format_code("12345678") == "1234 5678"


@pytest.mark.parametrize("scale", [1.0, 1.3])
def test_long_email_is_shown_in_full_and_wraps(root, scale):
    email = "very.long.email.address.for.testing.account.row@subdomain.example-company.com"

    row = _row(root, email, issuer="Example", scale=scale)

    assert row._name_label.cget("text") == email
    assert "…" not in row._name_label.cget("text")
    assert int(row._name_label.cget("wraplength")) > 0


@pytest.mark.parametrize("scale", [1.0, 1.3])
def test_issuer_gets_wraplength(root, scale):
    row = _row(
        root,
        "Hesap",
        issuer="Çok uzun servis adı satırda kırpılmadan sarılmalı",
        scale=scale,
    )

    assert int(row._issuer_label.cget("wraplength")) > 0


@pytest.mark.parametrize(("digits", "base_width"), [(6, 104), (8, 130)])
def test_code_column_width_tracks_digit_count(root, digits, base_width):
    row = _row(root, "Hesap", digits=digits)

    assert row._code_width == theme.scaled(base_width, 1.0)


def test_eight_digit_code_is_grouped(root):
    row = _row(root, "Hesap", digits=8)

    row.tick()

    assert row._code_label.cget("text") == format_code(row._code)
    assert len(row._code) == 8


def test_hotp_row_shows_unsupported_and_has_no_bar(root):
    row = _row(root, "HOTP hesabı", issuer="", account_type="hotp")

    row.tick()

    assert row._code_label.cget("text") == "desteklenmiyor"
    assert row._bar_canvas is None


def test_tap_copies_code_and_shows_inline_feedback(root):
    copied = []
    copied_accounts = []
    row = _row(root, "Hesap", issuer="Servis", on_copy=copied_accounts.append)
    row.clipboard_clear = lambda: copied.clear()
    row.clipboard_append = copied.append
    root.attributes("-alpha", 0.0)
    root.deiconify()
    root.update()

    row._name_label._canvas.event_generate("<ButtonRelease-1>", x=4, y=4, when="now")
    root.update()
    root.withdraw()

    assert copied == [row._code]
    assert len(copied[0]) == 6
    assert copied_accounts == [row.account]
    assert row._feedback_label.grid_info() != {}
    assert row._issuer_label.grid_info() == {}


def test_context_menu_offers_edit_and_delete(root):
    actions = []
    row = _row(
        root,
        "Hesap",
        on_edit=lambda account: actions.append(("edit", account.name)),
        on_delete=lambda account: actions.append(("delete", account.name)),
    )

    end = row._menu.index("end")
    labels = [row._menu.entrycget(index, "label") for index in range(end + 1)]
    assert labels == ["Düzenle", "Sil"]

    row._menu.invoke(0)
    row._menu.invoke(1)

    assert actions == [("edit", "Hesap"), ("delete", "Hesap")]


def test_divider_can_be_hidden_and_restored(root):
    row = _row(root, "Hesap", issuer="Servis")

    assert row._divider.grid_info() != {}

    row.set_divider_visible(False)
    assert row._divider.grid_info() == {}

    row.set_divider_visible(True)
    assert row._divider.grid_info() != {}
