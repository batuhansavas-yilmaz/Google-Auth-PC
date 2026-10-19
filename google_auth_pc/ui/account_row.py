import tkinter as tk
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from google_auth_pc import theme
from google_auth_pc.totp import code_at, remaining_seconds

if TYPE_CHECKING:
    from google_auth_pc.models import Account

_COPY_FEEDBACK_MS = 1500
_COPY_FEEDBACK_TEXT = "Kopyalandı"
_UNSUPPORTED_TEXT = "desteklenmiyor"
_UNSET = object()
_HEIGHT_SYNC_MS = 16
_LEAVE_CHECK_MS = 20
_BASE_ROW_WIDTH = 400
_BASE_CODE_WIDTH = 104
_BASE_WIDE_CODE_WIDTH = 130


_BREAK_AFTER = 24


def format_code(code: str) -> str:
    if len(code) < 2:
        return code
    half = len(code) // 2
    return f"{code[:half]} {code[half:]}"


def display_name(name: str) -> str:
    if "@" not in name or len(name) <= _BREAK_AFTER:
        return name
    local, _, domain = name.partition("@")
    return f"{local}@\n{domain}"


class AccountRow(ctk.CTkFrame):
    def __init__(
        self,
        master,
        account: "Account",
        scale: float,
        on_copy: Callable[["Account"], None] | None = None,
        on_edit: Callable[["Account"], None] | None = None,
        on_delete: Callable[["Account"], None] | None = None,
    ):
        super().__init__(master, fg_color="transparent", corner_radius=0, height=1)
        self.account = account
        self.scale = float(scale)
        self._on_copy = on_copy
        self._on_edit = on_edit
        self._on_delete = on_delete

        self._code: str | None = None
        self._last_code: str | None | object = _UNSET
        self._bar_canvas: tk.Canvas | None = None
        self._bar_fill: int | None = None
        self._bar_track: int | None = None

        self._copy_job: str | None = None
        self._leave_job: str | None = None
        self._height_job: str | None = None

        self._hover = False
        self._pad = theme.scaled(16, self.scale)
        self._gap = theme.scaled(8, self.scale)
        self._code_width = theme.scaled(
            _BASE_WIDE_CODE_WIDTH if account.digits > 6 else _BASE_CODE_WIDTH,
            self.scale,
        )
        self._bar_px = int(round(self._code_width * self._get_widget_scaling()))
        self._wraplength = 0
        self._last_width = -1
        self._desired_height = 0
        self._divider_visible = True

        self._build()
        self._bind_tree(self)
        self._create_menu()
        tk.Frame.bind(self, "<Configure>", self._on_resize, add="+")
        self._apply_wraplength(_BASE_ROW_WIDTH)
        self._schedule_height()
        self.tick()

    def tick(self) -> None:
        code = code_at(self.account)
        if code != self._last_code:
            self._last_code = code
            self._code = code
            self._code_label.configure(
                text=_UNSUPPORTED_TEXT if code is None else format_code(code)
            )
        if self._bar_canvas is None:
            return
        remaining = remaining_seconds(self.account)
        period = max(1, self.account.period)
        self._update_bar(max(0.0, min(1.0, remaining / period)))

    def destroy(self) -> None:
        self._cancel_jobs()
        super().destroy()

    def _build(self) -> None:
        palette = theme.PALETTE

        self._content = ctk.CTkFrame(
            self, fg_color=palette["bg"], corner_radius=0
        )
        self._content.place(x=0, y=0, relwidth=1, relheight=1)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._identity = ctk.CTkFrame(self._content, fg_color="transparent")
        self._identity.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(self._pad, self._gap),
            pady=theme.scaled(12, self.scale),
        )
        self._identity.grid_columnconfigure(0, weight=1)
        self._name_label = ctk.CTkLabel(
            self._identity,
            text=display_name(self.account.name),
            text_color=palette["text"],
            font=theme.font(18, self.scale, weight="bold"),
            anchor="w",
            justify="left",
            cursor="hand2",
        )
        self._name_label.grid(row=0, column=0, sticky="ew")

        self._issuer_label = None
        if self.account.issuer:
            self._issuer_label = ctk.CTkLabel(
                self._identity,
                text=self.account.issuer,
                text_color=palette["muted"],
                font=theme.font(14, self.scale),
                anchor="w",
                justify="left",
                cursor="hand2",
            )
            self._issuer_label.grid(
                row=1, column=0, sticky="ew", pady=(theme.scaled(2, self.scale), 0)
            )

        self._feedback_label = ctk.CTkLabel(
            self._identity,
            text=_COPY_FEEDBACK_TEXT,
            text_color=palette["success"],
            font=theme.font(14, self.scale, weight="bold"),
            anchor="w",
        )
        self._feedback_label.grid(
            row=1, column=0, sticky="ew", pady=(theme.scaled(2, self.scale), 0)
        )
        self._feedback_label.grid_remove()

        code_col = ctk.CTkFrame(self._content, fg_color="transparent")
        code_col.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(self._gap, self._pad),
            pady=theme.scaled(12, self.scale),
        )
        code_col.grid_columnconfigure(0, weight=1)

        is_totp = self.account.type == "totp"
        self._code_label = ctk.CTkLabel(
            code_col,
            text="",
            text_color=palette["text"] if is_totp else palette["muted"],
            font=(
                theme.font(22, self.scale, weight="bold", family="Consolas")
                if is_totp
                else theme.font(13, self.scale)
            ),
            anchor="e",
            cursor="hand2",
        )
        self._code_label.grid(row=0, column=0, sticky="e")

        if is_totp:
            self._bar_canvas = tk.Canvas(
                code_col,
                width=self._bar_px,
                height=2,
                highlightthickness=0,
                bd=0,
                bg=theme.current()["bg"],
            )
            self._bar_track = self._bar_canvas.create_rectangle(
                0, 0, self._bar_px, 2,
                fill=theme.current()["divider"],
                outline="",
            )
            self._bar_fill = self._bar_canvas.create_rectangle(
                0, 0, self._bar_px, 2,
                fill=theme.current()["accent"],
                outline="",
            )
            self._bar_canvas.grid(
                row=1, column=0, sticky="e", pady=(theme.scaled(4, self.scale), 0)
            )

        self._divider = ctk.CTkFrame(
            self._content, fg_color=palette["divider"], corner_radius=0, height=1
        )
        self._divider.grid(row=1, column=0, columnspan=2, sticky="ew")

        self._update_bar(1.0)

    def _create_menu(self) -> None:
        self._menu = tk.Menu(self, tearoff=0)
        if self._on_edit is not None:
            self._menu.add_command(label="Düzenle", command=self._edit)
        if self._on_delete is not None:
            self._menu.add_command(label="Sil", command=self._delete)

    def _bind_tree(self, widget) -> None:
        for sequence, handler in (
            ("<ButtonRelease-1>", self._copy),
            ("<Button-3>", self._popup_menu),
            ("<Enter>", self._on_pointer_enter),
            ("<Leave>", self._on_pointer_leave),
        ):
            tk.Misc.bind(widget, sequence, handler, add="+")
        for child in widget.winfo_children():
            self._bind_tree(child)

    def _on_resize(self, event) -> None:
        if event.widget is not self:
            return
        width = event.width / self._get_widget_scaling()
        if abs(width - self._last_width) < 1:
            return
        self._last_width = width
        self._apply_wraplength(width)
        self._schedule_height()

    def _apply_wraplength(self, width: float) -> None:
        available = width - 2 * self._pad - 2 * self._gap - self._code_width
        wraplength = max(theme.scaled(80, self.scale), int(available))
        if wraplength == self._wraplength:
            return
        self._wraplength = wraplength
        self._name_label.configure(wraplength=wraplength)
        if self._issuer_label is not None:
            self._issuer_label.configure(wraplength=wraplength)
        self._schedule_height()

    def _schedule_height(self) -> None:
        if self._height_job is not None or not self.winfo_exists():
            return
        self._height_job = self.after(_HEIGHT_SYNC_MS, self._sync_height)

    def _sync_height(self) -> None:
        self._height_job = None
        if not self.winfo_exists():
            return
        needed = self._content.winfo_reqheight() / self._get_widget_scaling()
        desired = max(int(round(needed)), theme.scaled(72, self.scale))
        if desired != self._desired_height:
            self._desired_height = desired
            self.configure(height=desired)

    def _update_bar(self, fraction: float) -> None:
        if self._bar_canvas is None:
            return
        palette = theme.current()
        if self._bar_canvas.cget("bg") != palette["bg"]:
            self._bar_canvas.configure(bg=palette["bg"])
        self._bar_canvas.itemconfigure(self._bar_track, fill=palette["divider"])
        self._bar_canvas.itemconfigure(self._bar_fill, fill=palette["accent"])
        self._bar_canvas.coords(
            self._bar_fill, 0, 0, round(self._bar_px * fraction), 2
        )

    def set_divider_visible(self, visible: bool) -> None:
        visible = bool(visible)
        if visible == self._divider_visible:
            return
        self._divider_visible = visible
        if visible:
            self._divider.grid()
        else:
            self._divider.grid_remove()

    def _on_pointer_enter(self, _event) -> None:
        if self._leave_job is not None:
            try:
                self.after_cancel(self._leave_job)
            except tk.TclError:
                pass
            self._leave_job = None
        self._set_hover(True)

    def _on_pointer_leave(self, _event) -> None:
        if self._leave_job is not None:
            return
        self._leave_job = self.after(_LEAVE_CHECK_MS, self._check_pointer)

    def _check_pointer(self) -> None:
        self._leave_job = None
        if not self.winfo_exists():
            return
        try:
            widget = self.winfo_containing(*self.winfo_pointerxy())
        except tk.TclError:
            widget = None
        inside = False
        while widget is not None:
            if widget is self:
                inside = True
                break
            widget = getattr(widget, "master", None)
        self._set_hover(inside)

    def _set_hover(self, hover: bool) -> None:
        if hover == self._hover:
            return
        self._hover = hover
        self._content.configure(
            fg_color=theme.PALETTE["row_hover"] if hover else theme.PALETTE["bg"]
        )

    def _copy(self, _event=None) -> None:
        code = code_at(self.account)
        if code is None:
            return
        self._code = code
        try:
            self.clipboard_clear()
            self.clipboard_append(code)
        except tk.TclError:
            return
        self._show_copy_feedback()
        if self._on_copy is not None:
            self._on_copy(self.account)

    def _show_copy_feedback(self) -> None:
        self._feedback_label.grid()
        if self._issuer_label is not None:
            self._issuer_label.grid_remove()
        if self._copy_job is not None:
            try:
                self.after_cancel(self._copy_job)
            except tk.TclError:
                pass
        self._copy_job = self.after(_COPY_FEEDBACK_MS, self._hide_copy_feedback)
        self._schedule_height()

    def _hide_copy_feedback(self) -> None:
        self._copy_job = None
        if not self.winfo_exists():
            return
        self._feedback_label.grid_remove()
        if self._issuer_label is not None:
            self._issuer_label.grid()
        self._schedule_height()

    def _popup_menu(self, event) -> None:
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _edit(self) -> None:
        if self._on_edit is not None:
            self._on_edit(self.account)

    def _delete(self) -> None:
        if self._on_delete is not None:
            self._on_delete(self.account)

    def _cancel_jobs(self) -> None:
        for name in ("_copy_job", "_leave_job", "_height_job"):
            job = getattr(self, name)
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, name, None)
