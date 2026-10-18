from dataclasses import dataclass
from pathlib import Path

from google_auth_pc.migration import MigrationParseError, parse_migration_uri
from google_auth_pc.models import Account

_MIGRATION_PREFIX = "otpauth-migration://"


@dataclass
class ImportResult:
    accounts: list[Account]
    failed_files: list[Path]
    skipped_payloads: int


def extract_migration_accounts(image_paths: list[Path]) -> ImportResult:
    import cv2
    import numpy as np

    accounts: list[Account] = []
    failed_files: list[Path] = []
    seen: set[str] = set()
    skipped_payloads = 0

    for raw_path in image_paths:
        path = Path(raw_path)
        try:
            if not path.is_file():
                failed_files.append(path)
                continue
            data = path.read_bytes()
            image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                failed_files.append(path)
                continue
            ok, decoded_info, _points, _straight = cv2.QRCodeDetector().detectAndDecodeMulti(
                image
            )
        except Exception:
            failed_files.append(path)
            continue

        texts = [text for text in (decoded_info if ok else ()) if text]
        if not texts:
            failed_files.append(path)
            continue

        for text in texts:
            if not text.startswith(_MIGRATION_PREFIX):
                skipped_payloads += 1
                continue
            try:
                parsed = parse_migration_uri(text)
            except MigrationParseError:
                skipped_payloads += 1
                continue
            for account in parsed:
                if account.secret in seen:
                    continue
                seen.add(account.secret)
                accounts.append(account)

    return ImportResult(
        accounts=accounts,
        failed_files=failed_files,
        skipped_payloads=skipped_payloads,
    )
