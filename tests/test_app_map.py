from types import SimpleNamespace

from google_auth_pc.app import App


class _Stub:
    def __init__(self):
        self.lock_calls = 0

    def lock(self):
        self.lock_calls += 1


def test_window_map_locks_the_session():
    stub = _Stub()
    App._on_window_mapped(stub, SimpleNamespace(widget=stub))
    assert stub.lock_calls == 1


def test_child_map_does_not_lock_the_session():
    stub = _Stub()
    App._on_window_mapped(stub, SimpleNamespace(widget=object()))
    assert stub.lock_calls == 0
