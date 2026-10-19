import pytest

from google_auth_pc import singleinstance


def _acquire_or_skip():
    if not singleinstance.acquire():
        pytest.skip("uygulama calisiyor; mutex dolu")


def test_acquire_returns_true():
    _acquire_or_skip()
    assert singleinstance.acquire() is True


def test_acquire_is_reentrant_in_same_process():
    _acquire_or_skip()
    assert singleinstance.acquire() is True


def test_focus_existing_without_window_does_not_crash():
    singleinstance.focus_existing()
