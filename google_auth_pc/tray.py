from collections.abc import Callable

import pystray
from PIL import Image, ImageDraw

_ICON_NAME = "GoogleAuthPC"
_ICON_TITLE = "Google Auth PC"
_BACKGROUND = (27, 58, 107, 255)
_FOREGROUND = (255, 255, 255, 255)
_SUPERSAMPLE = 4


def make_icon_image(size: int = 64) -> Image.Image:
    canvas = size * _SUPERSAMPLE
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    inset = canvas // 16
    draw.rounded_rectangle(
        (inset, inset, canvas - inset - 1, canvas - inset - 1),
        radius=canvas // 5,
        fill=_BACKGROUND,
    )
    center_x = canvas / 2
    head_center_y = canvas * 0.40
    head_radius = canvas * 0.13
    draw.ellipse(
        (
            center_x - head_radius,
            head_center_y - head_radius,
            center_x + head_radius,
            head_center_y + head_radius,
        ),
        fill=_FOREGROUND,
    )
    draw.polygon(
        (
            (center_x - head_radius * 0.62, head_center_y),
            (center_x + head_radius * 0.62, head_center_y),
            (center_x + head_radius * 1.05, canvas * 0.72),
            (center_x - head_radius * 1.05, canvas * 0.72),
        ),
        fill=_FOREGROUND,
    )
    return image.resize((size, size), Image.Resampling.LANCZOS)


def start_tray(
    on_open: Callable[[], None],
    on_lock: Callable[[], None],
    on_settings: Callable[[], None],
    on_quit: Callable[[], None],
) -> pystray.Icon:
    icon = pystray.Icon(
        _ICON_NAME,
        make_icon_image(),
        _ICON_TITLE,
        menu=pystray.Menu(
            pystray.MenuItem("Aç", lambda icon, item: on_open(), default=True),
            pystray.MenuItem("Kilitle", lambda icon, item: on_lock()),
            pystray.MenuItem("Ayarlar", lambda icon, item: on_settings()),
            pystray.MenuItem("Çıkış", lambda icon, item: on_quit()),
        ),
    )
    icon.run_detached()
    return icon
