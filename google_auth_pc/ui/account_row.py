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
_ANIMATION_STEPS = 6
_ANIMATION_INTERVAL_MS = 16
_LEAVE_CHECK_MS = 20
_GESTURE_SLOP = 12
_GESTURE_THRESHOLD = 96
_MAX_SHIFT_BASE = 160
_BASE_ROW_WIDTH = 400
_BASE_CODE_WIDTH = 104
_BASE_WIDE_CODE_WIDTH = 130


def format_code(code: str) -> str:
    if len(code) < 2:
        return code
    half = len(code) // 2
    return f"{code[:half]} {code[half:]}"


def resolve_gesture(dx: float, dy: float) -> str:
    horizontal = abs(dx)
    vertical = abs(dy)
    if horizontal >= _GESTURE_THRESHOLD and horizontal > vertical:
        return "delete" if dx < 0 else "edit"
    if horizontal < _GESTURE_SLOP and vertical < _GESTURE_SLOP:
        return "copy"
    return "none"


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

        self._press_active = False
        self._press_x = 0
        self._press_y = 0
        self._dragging = False
        self._grabbed = False
        self._offset = 0

        self._copy_job: str | None = None
        self._leave_job: str | None = None
        self._anim_job: str | None = None
        self._height_job: str | None = None

        self._hover = False
        self._pad = theme.scaled(16, self.scale)
        self._gap = theme.scaled(8, self.scale)
        self._code_width = theme.scaled(
            _BASE_WIDE_CODE_WIDTH if account.digits > 6 else _BASE_CODE_WIDTH,
            self.scale,
        )
        self._bar_px = int(round(self._code_width * self._get_widget_scaling()))
        self._max_shift = theme.scaled(_MAX_SHIFT_BASE, self.scale)
        self._wraplength = 0
        self._last_width = -1

        self._build()
        self._bind_tree(self)
        self._create_menu()
        tk.Frame.bind(self, "<Configure>", self._on_resize, add="+")
        self._apply_wraplength(theme.scaled(_BASE_ROW_WIDTH, self.scale))
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
        if self._grabbed:
            try:
                self.grab_release()
            except tk.TclError:
                pass
            self._grabbed = False
        super().destroy()

    def _build(self) -> None:
        palette = theme.PALETTE

        self._delete_panel = ctk.CTkFrame(
            self, fg_color=palette["danger"], corner_radius=0
        )
        self._delete_panel.place(x=0, y=0, relwidth=1, relheight=1)
        ctk.CTkLabel(
            self._delete_panel,
            text="Sil",
            text_color=palette["on_accent"],
            font=theme.font(16, self.scale, weight="bold"),
        ).pack(side="right", padx=(0, theme.scaled(24, self.scale)), pady=0)

        self._edit_panel = ctk.CTkFrame(
            self, fg_color=palette["accent"], corner_radius=0
        )
        self._edit_panel.place(x=0, y=0, relwidth=1, relheight=1)
        ctk.CTkLabel(
            self._edit_panel,
            text="Düzenle",
            text_color=palette["on_accent"],
            font=theme.font(16, self.scale, weight="bold"),
        ).pack(side="left", padx=(theme.scaled(24, self.scale), 0), pady=0)

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
            pady=theme.scaled(7, self.scale),
        )
        self._identity.grid_columnconfigure(0, weight=1)
        self._name_label = ctk.CTkLabel(
            self._identity,
            text=self.account.name,
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
            pady=theme.scaled(7, self.scale),
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
        bindings = (
            ("<ButtonPress-1>", self._on_press),
            ("<B1-Motion>", self._on_motion),
            ("<ButtonRelease-1>", self._on_release),
            ("<Button-3>", self._popup_menu),
            ("<Enter>", self._on_pointer_enter),
            ("<Leave>", self._on_pointer_leave),
        )
        for sequence, handler in bindings:
            widget.bind(sequence, handler, add="+")
            if isinstance(widget, ctk.CTkFrame):
                tk.Frame.bind(widget, sequence, handler, add="+")
        if isinstance(widget, ctk.CTkFrame):
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
        self._schedule_height()

    def _schedule_height(self) -> None:
        if self._height_job is not None or not self.winfo_exists():
            return
        self._height_job = self.after(_ANIMATION_INTERVAL_MS, self._sync_height)

    def _sync_height(self) -> None:
        self._height_job = None
        if not self.winfo_exists():
            return
        needed = self._content.winfo_reqheight() / self._get_widget_scaling()
        desired = max(int(round(needed)), theme.scaled(72, self.scale))
        if desired != self._desired_height:
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

    def _on_press(self, event) -> None:
        self._cancel_animation()
        self._set_offset(0)
        self._press_active = True
        self._dragging = False
        self._press_x = event.x_root
        self._press_y = event.y_root

    def _on_motion(self, event) -> None:
        if not self._press_active:
            return
        dx = event.x_root - self._press_x
        dy = event.y_root - self._press_y
        if not self._dragging:
            if abs(dx) < _GESTURE_SLOP and abs(dy) < _GESTURE_SLOP:
                return
            if abs(dy) > abs(dx):
                return
            self._dragging = True
            self._grab()
        offset = max(-self._max_shift, min(self._max_shift, dx))
        self._set_offset(offset)

    def _on_release(self, event) -> None:
        if not self._press_active:
            return
        self._press_active = False
        self._dragging = False
        if self._grabbed:
            try:
                self.grab_release()
            except tk.TclError:
                pass
            self._grabbed = False

        dx = event.x_root - self._press_x
        dy = event.y_root - self._press_y
        gesture = resolve_gesture(dx, dy)

        if gesture == "delete":
            self._delete()
            return
        if gesture == "edit":
            self._edit()
            self._spring_back()
            return
        if gesture == "copy":
            self._copy()
            return
        self._spring_back()

    def _grab(self) -> None:
        try:
            self.grab_set()
            self._grabbed = True
        except tk.TclError:
            self._grabbed = False

    def _set_offset(self, offset: int) -> None:
        self._offset = int(offset)
        if self._offset < 0:
            self._delete_panel.lift()
        elif self._offset > 0:
            self._edit_panel.lift()
        if self._offset != 0:
            self._content.lift()
        self._content.place_configure(x=self._offset)

    def _spring_back(self) -> None:
        self._cancel_animation()
        start = self._offset
        if start == 0:
            return

        def animate(step: int) -> None:
            self._anim_job = None
            if not self.winfo_exists():
                return
            if step >= _ANIMATION_STEPS:
                self._set_offset(0)
                return
            self._set_offset(int(start * (_ANIMATION_STEPS - step) / _ANIMATION_STEPS))
            self._anim_job = self.after(
                _ANIMATION_INTERVAL_MS, lambda: animate(step + 1)
            )

        self._anim_job = self.after(_ANIMATION_INTERVAL_MS, lambda: animate(1))

    def _cancel_animation(self) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

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

    def _copy(self) -> None:
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
        for name in (
            "_copy_job",
            "_leave_job",
            "_anim_job",
            "_height_job",
        ):
            job = getattr(self, name)
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, name, None)
