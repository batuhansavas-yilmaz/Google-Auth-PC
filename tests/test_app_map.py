from types import SimpleNamespace

from google_auth_pc.app import App


class _Stub:
    def __init__(self, state="normal"):
        self.lock_calls = 0
        self._relock_on_map = False
        self._state = state

    def lock(self):
        self.lock_calls += 1

    def state(self):
        return self._state


class _HideStub(_Stub):
    def __init__(self):
        super().__init__()
        self.geometry_saves = 0
        self.withdraw_calls = 0

    def _schedule_geometry_save(self):
        self.geometry_saves += 1

    def withdraw(self):
        self.withdraw_calls += 1


class _RestoreStub(_Stub):
    def __init__(self):
        super().__init__()
        self.deiconify_calls = 0

    def deiconify(self):
        self.deiconify_calls += 1

    def lift(self):
        pass

    def focus_force(self):
        pass


def _event(widget):
    return SimpleNamespace(widget=widget)


def test_internal_remap_does_not_lock_the_session():
    stub = _Stub()
    App._on_window_mapped(stub, _event(stub))
    assert stub.lock_calls == 0


def test_child_map_does_not_lock_the_session():
    stub = _Stub()
    App._on_window_mapped(stub, _event(object()))
    assert stub.lock_calls == 0


def test_map_after_user_hide_locks_the_session():
    stub = _Stub()
    stub._relock_on_map = True
    App._on_window_mapped(stub, _event(stub))
    assert stub.lock_calls == 1
    assert stub._relock_on_map is False


def test_hide_to_tray_arms_relock_on_next_map():
    stub = _HideStub()
    App.hide_to_tray(stub)
    assert stub.geometry_saves == 1
    assert stub.withdraw_calls == 1
    assert stub.lock_calls == 1
    assert stub._relock_on_map is True


def test_minimize_then_restore_locks_the_session():
    stub = _Stub(state="iconic")
    App._on_window_unmapped(stub, _event(stub))
    assert stub._relock_on_map is True
    App._on_window_mapped(stub, _event(stub))
    assert stub.lock_calls == 1


def test_theme_remap_unmap_does_not_arm_relock():
    stub = _Stub(state="withdrawn")
    App._on_window_unmapped(stub, _event(stub))
    assert stub._relock_on_map is False
    App._on_window_mapped(stub, _event(stub))
    assert stub.lock_calls == 0


def test_restore_window_locks_and_clears_pending_map_lock():
    stub = _RestoreStub()
    stub._relock_on_map = True
    App._restore_window(stub)
    assert stub.deiconify_calls == 1
    assert stub.lock_calls == 1
    assert stub._relock_on_map is False
    App._on_window_mapped(stub, _event(stub))
    assert stub.lock_calls == 1
