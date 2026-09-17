"""Lightweight Fluent-inspired UI primitives shared by the Tk shell."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Mapping


SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}
RADII = {"control": 8, "card": 10, "small": 6}
PAGE_PADDING = (20, 20)
CARD_PADDING = (16, 14)
DIALOG_PADDING = (20, 18)
CONTROL_GAP = 8
BUTTON_MIN_WIDTH = 92


def _draw_rounded_surface(canvas: tk.Canvas, width: int, height: int, radius: int, fill: str, outline: str) -> None:
    canvas.delete("surface")
    if width < 2 or height < 2:
        return
    radius = max(4, min(radius, width // 2, height // 2))
    canvas.create_rectangle(radius, 0, width - radius, height, fill=fill, outline="", tags="surface")
    canvas.create_rectangle(0, radius, width, height - radius, fill=fill, outline="", tags="surface")
    for x, y, start in ((0, 0, 90), (width - 2 * radius, 0, 0), (0, height - 2 * radius, 180), (width - 2 * radius, height - 2 * radius, 270)):
        canvas.create_arc(x, y, x + 2 * radius, y + 2 * radius, start=start, extent=90, fill=fill, outline="", tags="surface")
    canvas.create_line(radius, 0, width - radius, 0, fill=outline, tags="surface")
    canvas.create_line(radius, height - 1, width - radius, height - 1, fill=outline, tags="surface")
    canvas.create_line(0, radius, 0, height - radius, fill=outline, tags="surface")
    canvas.create_line(width - 1, radius, width - 1, height - radius, fill=outline, tags="surface")


def tokens_for(colors: Mapping[str, str]) -> dict[str, object]:
    return {
        "background": colors["background"], "surface": colors["surface"], "elevated": colors.get("elevated", colors["surface"]),
        "border": colors["border"], "subtle_border": colors.get("subtle_border", colors["border"]), "text": colors["text"],
        "secondary_text": colors["muted"], "accent": colors["accent"], "accent_dark": colors["accent_dark"],
        "success": colors.get("success", "#15803d"), "warning": colors.get("warning", "#a16207"), "error": colors.get("error", "#b91c1c"),
        "hover": colors.get("heading", colors["surface"]), "pressed": colors.get("heading", colors["surface"]),
        "selected": colors.get("selection", colors["accent"]), "selected_text": colors.get("selection_text", colors["text"]),
        "spacing": SPACING, "radii": RADII,
    }


class FluentCard(tk.Frame):
    def __init__(self, master: tk.Misc, *, tokens: Mapping[str, object], padding=(16, 14), **kwargs):
        super().__init__(master, bg=str(tokens["background"]), highlightthickness=0, bd=0, relief="flat", **kwargs)
        self.tokens = tokens
        self.padding = padding
        self._surface = tk.Canvas(self, bg=str(tokens["background"]), highlightthickness=0, bd=0)
        self._surface.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._redraw_surface, add="+")

    def apply_theme(self, tokens: Mapping[str, object]) -> None:
        """Refresh the card surface and retain the new runtime theme tokens."""
        self.tokens = tokens
        self._surface.configure(bg=str(tokens["background"]))
        self._redraw_surface()

    def _redraw_surface(self, _event=None) -> None:
        _draw_rounded_surface(self._surface, self.winfo_width(), self.winfo_height(), int(self.tokens["radii"]["card"]), str(self.tokens["surface"]), str(self.tokens["subtle_border"]))
        self._surface.lower()

    def content(self) -> tk.Frame:
        body = tk.Frame(self, bg=str(self.tokens["surface"]))
        body.pack(fill="both", expand=True, padx=self.padding[0], pady=self.padding[1])
        return body


class ScrollableWorkspace(tk.Frame):
    """Single vertical scroll container for the main content workspace."""
    def __init__(self, master: tk.Misc, *, background: str, **kwargs):
        super().__init__(master, bg=background, **kwargs)
        self._wheel_tag = f"ScrollableWorkspaceWheel{id(self)}"
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=background)
        self._window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content.bind("<Configure>", self._on_content_configure, add="+")
        self.canvas.bind("<Configure>", self._on_canvas_configure, add="+")
        self._bind_class()
        self._bind_widget_tree(self.canvas)
        self._bind_widget_tree(self.content)

    def _bind_class(self) -> None:
        self.bind_class(self._wheel_tag, "<MouseWheel>", self._on_wheel)
        self.bind_class(self._wheel_tag, "<Button-4>", self._on_wheel)
        self.bind_class(self._wheel_tag, "<Button-5>", self._on_wheel)

    def _bind_widget_tree(self, widget: tk.Misc) -> None:
        tags = list(widget.bindtags())
        if self._wheel_tag not in tags:
            widget.bindtags((self._wheel_tag, *tags))
        for child in widget.winfo_children():
            self._bind_widget_tree(child)

    def _update_scrollregion(self) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 1, 1))

    def _on_content_configure(self, _event=None) -> None:
        self._bind_widget_tree(self.content)
        self._update_scrollregion()

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfigure(self._window_id, width=max(1, event.width))
        self._sync_content_height(event.height)
        self._update_scrollregion()

    def _sync_content_height(self, viewport_height: int) -> None:
        if getattr(self, "_syncing_height", False):
            return
        self._syncing_height = True
        try:
            self.content.configure(height=0)
            self.update_idletasks()
            natural_height = self.content.winfo_reqheight()
            self.content.configure(height=max(int(viewport_height), natural_height, 1))
        finally:
            self._syncing_height = False

    def _treeview_ancestor(self, widget) -> bool:
        current = widget
        while current is not None:
            if isinstance(current, ttk.Treeview):
                return True
            current = getattr(current, "master", None)
        return False

    def _on_wheel(self, event):
        if self._treeview_ancestor(event.widget):
            return None
        if getattr(event, "num", None) == 4:
            units = -1
        elif getattr(event, "num", None) == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return None
            units = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
        self.canvas.yview_scroll(units, "units")
        return "break"

    def reset(self) -> None:
        self.canvas.yview_moveto(0.0)

    def refresh(self) -> None:
        self._bind_widget_tree(self.content)
        self.update_idletasks()
        self._sync_content_height(self.canvas.winfo_height())
        self._update_scrollregion()

def configure_styles(style: ttk.Style, colors: Mapping[str, str], font: str) -> None:
    surface = colors["surface"]
    heading = colors.get("heading", surface)
    text = colors["text"]
    muted = colors["muted"]
    accent = colors["accent"]
    accent_dark = colors["accent_dark"]
    selection = colors.get("selection", accent)
    selected_text = colors.get("selection_text", text)
    style.theme_use("clam")
    style.configure("Fluent.TCombobox", padding=(10, 7), fieldbackground=surface, background=surface, foreground=text, bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], focuscolor=accent, font=(font, 10))
    style.map("Fluent.TCombobox", fieldbackground=[("disabled", heading), ("readonly", surface), ("focus", surface), ("active", surface)], foreground=[("disabled", muted), ("readonly", text), ("focus", text), ("active", text)])
    style.configure("Accent.TButton", padding=(16, 9), width=BUTTON_MIN_WIDTH, font=(font, 10, "bold"), foreground="white", background=accent, borderwidth=0, focuscolor=accent_dark)
    style.map("Accent.TButton", background=[("disabled", heading), ("active", accent_dark), ("pressed", accent_dark)], foreground=[("disabled", muted), ("!disabled", "white")])
    style.configure("Secondary.TButton", padding=(13, 8), width=BUTTON_MIN_WIDTH, font=(font, 9), foreground=text, background=surface, borderwidth=0, focuscolor=accent)
    style.map("Secondary.TButton", background=[("disabled", heading), ("active", heading), ("pressed", heading)], foreground=[("disabled", muted), ("!disabled", text)])
    style.configure("Tertiary.TButton", padding=(10, 7), width=BUTTON_MIN_WIDTH, font=(font, 9), foreground=accent, background=surface, borderwidth=0, focuscolor=accent)
    style.map("Tertiary.TButton", background=[("disabled", heading), ("active", heading), ("pressed", heading)], foreground=[("disabled", muted), ("!disabled", accent)])
    style.configure("TCheckbutton", background=surface, foreground=text, font=(font, 9))
    style.map("TCheckbutton", background=[("disabled", heading), ("active", heading)], foreground=[("disabled", muted), ("!disabled", text)])
    style.configure("TScrollbar", troughcolor=surface, background=heading, arrowcolor=muted, bordercolor=colors["border"])
    style.configure("Fluent.Treeview", rowheight=40, font=(font, 10), background=surface, fieldbackground=surface, foreground=text, borderwidth=0, focuscolor=accent)
    style.configure("Fluent.Treeview.Heading", font=(font, 9, "bold"), background=heading, foreground=muted, relief="flat", padding=(10, 10))
    style.map("Fluent.Treeview", background=[("selected", selection)], foreground=[("selected", selected_text)])
    style.map("Fluent.Treeview.Heading", background=[("active", heading), ("pressed", heading)], foreground=[("active", text), ("pressed", text)])


NAV_DESTINATIONS = ("overview", "analysis", "compare_os", "compare_machines", "upgrade", "recommendations", "reports", "settings", "about")
