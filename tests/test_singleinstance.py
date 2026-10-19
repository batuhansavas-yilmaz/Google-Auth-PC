from google_auth_pc import singleinstance


def test_acquire_returns_true():
    assert singleinstance.acquire() is True


def test_acquire_is_reentrant_in_same_process():
    assert singleinstance.acquire() is True
    assert singleinstance.acquire() is True


def test_focus_existing_without_window_does_not_crash():
    singleinstance.focus_existing()
