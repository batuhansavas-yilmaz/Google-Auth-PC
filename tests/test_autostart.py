import winreg

from google_auth_pc import autostart

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "GoogleAuthPC"
_FAKE_COMMAND = '"C:\\sahte\\GoogleAuthPC.exe"'


def _read_value() -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _value_type = winreg.QueryValueEx(key, _VALUE_NAME)
            return value
    except FileNotFoundError:
        return None


def test_autostart_roundtrip():
    previous = _read_value()
    try:
        autostart.enable(_FAKE_COMMAND)
        assert autostart.is_enabled()
        assert _read_value() == _FAKE_COMMAND
        autostart.disable()
        assert not autostart.is_enabled()
        assert _read_value() is None
    finally:
        if previous is None:
            autostart.disable()
        else:
            autostart.enable(previous)
