import base64
import hashlib
import hmac
import os
import re

_ITERATIONS = 200000
_SALT_BYTES = 16
_PIN_PATTERN = re.compile(r"^\d{6}$")


def _derive(pin: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iterations)


def set_pin(config, pin: str) -> None:
    if not _PIN_PATTERN.match(pin):
        raise ValueError("PIN 6 haneli olmalıdır")
    salt = os.urandom(_SALT_BYTES)
    digest = _derive(pin, salt, _ITERATIONS)
    config.set(
        "pin",
        {
            "salt_b64": base64.b64encode(salt).decode("ascii"),
            "hash_b64": base64.b64encode(digest).decode("ascii"),
            "iterations": _ITERATIONS,
        },
    )
    config.save()


def verify_pin(config, pin: str) -> bool:
    stored = config.get("pin")
    if not isinstance(stored, dict):
        return False
    try:
        salt = base64.b64decode(stored["salt_b64"])
        expected = base64.b64decode(stored["hash_b64"])
        iterations = int(stored["iterations"])
    except (KeyError, TypeError, ValueError):
        return False
    digest = _derive(pin, salt, iterations)
    return hmac.compare_digest(digest, expected)


def is_pin_set(config) -> bool:
    return bool(config.get("pin"))


def clear_pin(config) -> None:
    config.set("pin", None)
    config.save()
