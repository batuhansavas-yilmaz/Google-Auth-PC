from google_auth_pc import hello


def test_verify_identity_unavailable_when_prompt_cannot_open(monkeypatch):
    monkeypatch.setattr(hello, "_winsdk", None)
    monkeypatch.setattr(hello, "_credui_prompt", lambda parent_hwnd=None: 31)
    assert hello.verify_identity() is hello.VerifyResult.UNAVAILABLE


def test_verify_identity_unavailable_when_prompt_raises(monkeypatch):
    monkeypatch.setattr(hello, "_winsdk", None)

    def _fail(parent_hwnd=None):
        raise OSError("istem açılamadı")

    monkeypatch.setattr(hello, "_credui_prompt", _fail)
    assert hello.verify_identity() is hello.VerifyResult.UNAVAILABLE


def test_verify_identity_ok_and_cancelled_codes(monkeypatch):
    monkeypatch.setattr(hello, "_winsdk", None)
    monkeypatch.setattr(hello, "_credui_prompt", lambda parent_hwnd=None: 0)
    assert hello.verify_identity() is hello.VerifyResult.OK
    monkeypatch.setattr(hello, "_credui_prompt", lambda parent_hwnd=None: 1223)
    assert hello.verify_identity() is hello.VerifyResult.CANCELLED


def test_biometrics_unavailable_without_winsdk(monkeypatch):
    monkeypatch.setattr(hello, "_winsdk", None)
    assert hello.hello_biometrics_available() is False
