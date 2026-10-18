from google_auth_pc.models import Account
from google_auth_pc.ui.main_screen import filter_accounts


def test_filter():
    items = [Account(secret="JBSWY3DPEHPK3PXP", name="Batuhan", issuer="Google"),
             Account(secret="KRSXG5CTMVRXEZLU", name="is", issuer="GitHub")]
    assert filter_accounts(items, "git") == [items[1]]
    assert filter_accounts(items, "") == items
    assert filter_accounts(items, "yok") == []


def test_filter_diacritics():
    items = [Account(secret="JBSWY3DPEHPK3PXP", name="İş Bankası", issuer="Şirket")]
    assert filter_accounts(items, "is bankasi") == items
    assert filter_accounts(items, "SIRKET") == items
    assert filter_accounts(items, "şirket") == items
