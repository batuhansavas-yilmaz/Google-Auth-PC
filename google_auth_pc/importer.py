from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from google_auth_pc.migration import MigrationParseError, parse_migration_uri_with_batch
from google_auth_pc.models import Account

_MIGRATION_PREFIX = "otpauth-migration://"


@dataclass
class ImportResult:
    accounts: list[Account]
    failed_files: list[Path]
    skipped_payloads: int
    incomplete_batches: list[tuple[int, int, int]] = field(default_factory=list)


def extract_migration_accounts(image_paths: list[Path]) -> ImportResult:
    import zxingcpp

    accounts: list[Account] = []
    failed_files: list[Path] = []
    seen: set[str] = set()
    skipped_payloads = 0
    batch_sizes: dict[int, int] = {}
    batch_indexes: dict[int, set[int]] = {}

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
                parsed = parse_migration_uri_with_batch(text)
            except MigrationParseError:
                skipped_payloads += 1
                continue
            if parsed.batch is not None:
                batch = parsed.batch
                batch_sizes[batch.batch_id] = max(
                    batch_sizes.get(batch.batch_id, 0), batch.size
                )
                batch_indexes.setdefault(batch.batch_id, set()).add(batch.index)
            for account in parsed.accounts:
                if account.secret in seen:
                    continue
                seen.add(account.secret)
                accounts.append(account)

    incomplete_batches = []
    for batch_id, size in batch_sizes.items():
        found = len({index for index in batch_indexes[batch_id] if 0 <= index < size})
        if found < size:
            incomplete_batches.append((batch_id, found, size))

    return ImportResult(
        accounts=accounts,
        failed_files=failed_files,
        skipped_payloads=skipped_payloads,
        incomplete_batches=incomplete_batches,
    )
