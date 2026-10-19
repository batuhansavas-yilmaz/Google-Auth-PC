from google_auth_pc.hello import VerifyResult
from google_auth_pc.ui.lock_screen import LockScreen


class _AppStub:
    def __init__(self):
        self.unlock_calls = 0

    def unlock_session(self):
        self.unlock_calls += 1


class _LockStub:
    def __init__(self, epoch):
        self._epoch = epoch
        self._hello_button = None
        self.app = _AppStub()
        self.status = None

    def _set_status(self, text):
        self.status = text


def test_stale_verification_does_not_unlock():
    stub = _LockStub(epoch=2)
    LockScreen._on_hello_result(stub, VerifyResult.OK, 1)
    LockScreen._on_hello_result(stub, VerifyResult.CANCELLED, 1)
    assert stub.app.unlock_calls == 0
    assert stub.status is None


def test_current_verification_unlocks():
    stub = _LockStub(epoch=2)
    LockScreen._on_hello_result(stub, VerifyResult.OK, 2)
    assert stub.app.unlock_calls == 1
