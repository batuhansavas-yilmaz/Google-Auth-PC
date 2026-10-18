import base64
import urllib.parse


def varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint negatif olamaz")
    chunks = bytearray()
    while True:
        chunk = value & 0x7F
        value >>= 7
        if value:
            chunks.append(chunk | 0x80)
        else:
            chunks.append(chunk)
            return bytes(chunks)


def field(tag: int, wire: int, payload) -> bytes:
    key = varint((tag << 3) | wire)
    if wire == 0:
        return key + varint(int(payload))
    if wire == 2:
        raw = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
        return key + varint(len(raw)) + raw
    raise ValueError(f"Desteklenmeyen wire tipi: {wire}")


def build_migration_payload(entries) -> bytes:
    payload = b""
    for entry in entries:
        entry_bytes = b""
        if "secret" in entry:
            secret = entry["secret"]
            raw = secret if isinstance(secret, bytes) else secret.encode("ascii")
            entry_bytes += field(1, 2, raw)
        if "name" in entry:
            entry_bytes += field(2, 2, entry["name"])
        if "issuer" in entry:
            entry_bytes += field(3, 2, entry["issuer"])
        for key, tag in (("algorithm", 4), ("digits", 5), ("type", 6), ("counter", 7)):
            if key in entry:
                entry_bytes += field(tag, 0, entry[key])
        payload += field(1, 2, entry_bytes)
    return payload


def build_migration_uri(entries) -> str:
    encoded = base64.b64encode(build_migration_payload(entries)).decode("ascii")
    return "otpauth-migration://offline?data=" + urllib.parse.quote(encoded)
