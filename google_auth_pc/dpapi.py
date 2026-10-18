import ctypes
from ctypes import wintypes


class DpapiError(Exception):
    ...


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", wintypes.LPBYTE)]


_crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_crypt32.CryptProtectData.argtypes = [
    ctypes.POINTER(_Blob),
    wintypes.LPCWSTR,
    ctypes.POINTER(_Blob),
    wintypes.LPVOID,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(_Blob),
]
_crypt32.CryptProtectData.restype = wintypes.BOOL

_crypt32.CryptUnprotectData.argtypes = [
    ctypes.POINTER(_Blob),
    ctypes.POINTER(wintypes.LPWSTR),
    ctypes.POINTER(_Blob),
    wintypes.LPVOID,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(_Blob),
]
_crypt32.CryptUnprotectData.restype = wintypes.BOOL

_kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
_kernel32.LocalFree.restype = wintypes.HLOCAL


def _to_blob(data: bytes) -> _Blob:
    buf = ctypes.create_string_buffer(data, max(len(data), 1))
    return _Blob(len(data), ctypes.cast(buf, wintypes.LPBYTE))


def protect(data: bytes) -> bytes:
    blob_in = _to_blob(data)
    blob_out = _Blob()
    if not _crypt32.CryptProtectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        raise DpapiError(ctypes.get_last_error())
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _kernel32.LocalFree(blob_out.pbData)


def unprotect(blob: bytes) -> bytes:
    blob_in = _to_blob(blob)
    blob_out = _Blob()
    descr = wintypes.LPWSTR()
    if not _crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        ctypes.byref(descr),
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    ):
        raise DpapiError(ctypes.get_last_error())
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        if descr:
            _kernel32.LocalFree(descr)
        _kernel32.LocalFree(blob_out.pbData)
