import sys
from pathlib import Path

import segno

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.helpers import build_migration_uri

SAMPLE_ACCOUNTS = [
    {
        "secret": "JBSWY3DPEHPK3PXP",
        "name": "ornek1@example.com",
        "issuer": "Ornek Sirket",
    },
    {
        "secret": "KRSXG5CTMVRXEZLU",
        "name": "ornek2@example.com",
        "issuer": "Ornek Sirket",
    },
    {
        "secret": "MFRGGZDFMZTWQ2LK",
        "name": "ornek3@example.com",
        "issuer": "Ornek Sirket",
    },
]


def main() -> None:
    first = build_migration_uri(SAMPLE_ACCOUNTS[:2])
    second = build_migration_uri([SAMPLE_ACCOUNTS[2], SAMPLE_ACCOUNTS[0]])
    segno.make(first, micro=False).save("sample_export_1.png", scale=8)
    segno.make(second, micro=False).save("sample_export_2.png", scale=8)
    print("Olusturuldu: sample_export_1.png (2 ornek hesap)")
    print("Olusturuldu: sample_export_2.png (1 yeni hesap + 1 zaten ekli hesap)")


if __name__ == "__main__":
    main()
