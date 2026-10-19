from google_auth_pc.ui.intro_screen import _security_mode


def test_pin_is_optional_with_windows_hello():
    assert _security_mode(hello_available=True, lock_available=True) == "hello"


def test_pin_is_optional_with_password_prompt_only():
    assert _security_mode(hello_available=False, lock_available=True) == "password"


def test_pin_is_required_only_without_any_lock_method():
    assert _security_mode(hello_available=False, lock_available=False) == "forced"
