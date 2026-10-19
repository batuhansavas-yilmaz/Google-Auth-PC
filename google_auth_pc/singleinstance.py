import ctypes

_MUTEX_NAME = "GoogleAuthPC"
_WINDOW_TITLE = "Google Auth PC"
_ERROR_ALREADY_EXISTS = 183
_SW_SHOW = 5

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p)
_kernel32.CreateMutexW.restype = ctypes.c_void_p
_kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
_kernel32.CloseHandle.restype = ctypes.c_int

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.FindWindowW.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p)
_user32.FindWindowW.restype = ctypes.c_void_p
_user32.ShowWindow.argtypes = (ctypes.c_void_p, ctypes.c_int)
_user32.ShowWindow.restype = ctypes.c_int
_user32.SetForegroundWindow.argtypes = (ctypes.c_void_p,)
_user32.SetForegroundWindow.restype = ctypes.c_int

_mutex_handle: int | None = None


def acquire() -> bool:
    global _mutex_handle
    if _mutex_handle is not None:
        return True
    handle = _kernel32.CreateMutexW(None, True, _MUTEX_NAME)
    if not handle:
        return False
    if ctypes.get_last_error() == _ERROR_ALREADY_EXISTS:
        _kernel32.CloseHandle(handle)
        return False
    _mutex_handle = handle
    return True


def focus_existing() -> None:
    hwnd = _user32.FindWindowW(None, _WINDOW_TITLE)
    if not hwnd:
        return
    _user32.ShowWindow(hwnd, _SW_SHOW)
    _user32.SetForegroundWindow(hwnd)
