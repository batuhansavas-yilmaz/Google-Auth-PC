import asyncio
import ctypes
from ctypes import wintypes
from enum import Enum

try:
    import winrt.windows.security.credentials.ui as _winsdk
except ImportError:
    try:
        import winsdk.windows.security.credentials.ui as _winsdk
    except ImportError:
        _winsdk = None


class VerifyResult(Enum):
    OK = "ok"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


_VERIFY_MESSAGE = "Google Auth PC kodlarını görmek için kimliğini doğrula"
_PROMPT_CAPTION = "Windows Güvenliği"

_ERROR_SUCCESS = 0
_ERROR_CANCELLED = 1223
_CREDUIWIN_GENERIC = 0x1


class _CREDUI_INFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hwndParent", wintypes.HWND),
        ("pszMessageText", wintypes.LPCWSTR),
        ("pszCaptionText", wintypes.LPCWSTR),
        ("hbmBanner", wintypes.HBITMAP),
    ]


_credui = ctypes.WinDLL("credui", use_last_error=True)
_ole32 = ctypes.WinDLL("ole32", use_last_error=True)

_credui.CredUIPromptForWindowsCredentialsW.argtypes = [
    ctypes.POINTER(_CREDUI_INFO),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.ULONG),
    wintypes.LPCVOID,
    wintypes.ULONG,
    ctypes.POINTER(wintypes.LPVOID),
    ctypes.POINTER(wintypes.ULONG),
    ctypes.POINTER(wintypes.BOOL),
    wintypes.DWORD,
]
_credui.CredUIPromptForWindowsCredentialsW.restype = wintypes.DWORD

_credui.CredUnPackAuthenticationBufferW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCVOID,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
_credui.CredUnPackAuthenticationBufferW.restype = wintypes.BOOL

_ole32.CoTaskMemFree.argtypes = [wintypes.LPVOID]
_ole32.CoTaskMemFree.restype = None


def _consume_credentials(blob: int, blob_size: int) -> None:
    user_len = wintypes.DWORD(0)
    domain_len = wintypes.DWORD(0)
    password_len = wintypes.DWORD(0)
    _credui.CredUnPackAuthenticationBufferW(
        0,
        blob,
        blob_size,
        None,
        ctypes.byref(user_len),
        None,
        ctypes.byref(domain_len),
        None,
        ctypes.byref(password_len),
    )
    user = ctypes.create_unicode_buffer(user_len.value or 1)
    domain = ctypes.create_unicode_buffer(domain_len.value or 1)
    password = ctypes.create_unicode_buffer(password_len.value or 1)
    _credui.CredUnPackAuthenticationBufferW(
        0,
        blob,
        blob_size,
        user,
        ctypes.byref(user_len),
        domain,
        ctypes.byref(domain_len),
        password,
        ctypes.byref(password_len),
    )


def _credui_prompt(parent_hwnd: int | None = None) -> int:
    info = _CREDUI_INFO()
    info.cbSize = ctypes.sizeof(_CREDUI_INFO)
    info.hwndParent = parent_hwnd
    info.pszMessageText = _VERIFY_MESSAGE
    info.pszCaptionText = _PROMPT_CAPTION
    auth_package = wintypes.ULONG(0)
    out_buffer = wintypes.LPVOID()
    out_size = wintypes.ULONG(0)
    save = wintypes.BOOL(False)
    code = _credui.CredUIPromptForWindowsCredentialsW(
        ctypes.byref(info),
        0,
        ctypes.byref(auth_package),
        None,
        0,
        ctypes.byref(out_buffer),
        ctypes.byref(out_size),
        ctypes.byref(save),
        _CREDUIWIN_GENERIC,
    )
    try:
        if code == _ERROR_SUCCESS:
            _consume_credentials(out_buffer.value, out_size.value)
        return code
    finally:
        if out_buffer.value:
            _ole32.CoTaskMemFree(out_buffer)


def _credui_verify(parent_hwnd: int | None) -> VerifyResult:
    try:
        code = _credui_prompt(parent_hwnd)
    except Exception:
        return VerifyResult.UNAVAILABLE
    if code == _ERROR_SUCCESS:
        return VerifyResult.OK
    if code == _ERROR_CANCELLED:
        return VerifyResult.CANCELLED
    return VerifyResult.UNAVAILABLE


async def _winsdk_request():
    return await _winsdk.UserConsentVerifier.request_verification_async(_VERIFY_MESSAGE)


def verify_identity(parent_hwnd: int | None = None) -> VerifyResult:
    if _winsdk is not None:
        try:
            result = asyncio.run(_winsdk_request())
            if result == _winsdk.UserConsentVerificationResult.VERIFIED:
                return VerifyResult.OK
            if result == _winsdk.UserConsentVerificationResult.CANCELED:
                return VerifyResult.CANCELLED
        except Exception:
            pass
    return _credui_verify(parent_hwnd)


def hello_biometrics_available() -> bool:
    if _winsdk is None:
        return False
    try:
        availability = asyncio.run(_winsdk.UserConsentVerifier.check_availability_async())
        return availability == _winsdk.UserConsentVerifierAvailability.AVAILABLE
    except Exception:
        return False


def credui_available() -> bool:
    return _credui is not None
