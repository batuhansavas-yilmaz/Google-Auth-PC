import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google_auth_pc.tray import make_icon_image

SIZES = (256, 64, 32, 16)
OUTPUT = PROJECT_ROOT / "assets" / "icon.ico"


def main() -> None:
    base = make_icon_image(256)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    base.save(OUTPUT, format="ICO", sizes=[(size, size) for size in SIZES])
    print(f"Olusturuldu: {OUTPUT} ({', '.join(str(s) for s in SIZES)} px)")


if __name__ == "__main__":
    main()
