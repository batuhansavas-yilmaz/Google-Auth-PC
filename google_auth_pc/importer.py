from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from google_auth_pc.migration import MigrationParseError, parse_migration_uri
from google_auth_pc.models import Account

_MIGRATION_PREFIX = "otpauth-migration://"


@dataclass
class ImportResult:
    accounts: list[Account]
    failed_files: list[Path]
    skipped_payloads: int


def extract_migration_accounts(image_paths: list[Path]) -> ImportResult:
    import zxingcpp

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
            with Image.open(path) as image:
                results = zxingcpp.read_barcodes(image)
        except Exception:
            failed_files.append(path)
            continue

        texts = [result.text for result in results if result.text]
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
