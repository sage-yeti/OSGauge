"""Lightweight Fluent-inspired UI primitives shared by the Tk shell.

Tk's native themed widgets do not expose a portable corner-radius API.  Cards
therefore use a soft border and surface treatment while native controls remain
accessible and keyboard friendly.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Mapping


SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}
RADII = {"control": 8, "card": 10, "small": 6}


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
    """Return one small, reusable set of visual tokens for the active theme."""
    return {
        "background": colors["background"],
        "surface": colors["surface"],
        "elevated": colors.get("elevated", colors["surface"]),
        "border": colors["border"],
        "subtle_border": colors.get("subtle_border", colors["border"]),
        "text": colors["text"],
        "secondary_text": colors["muted"],
        "accent": colors["accent"],
        "accent_dark": colors["accent_dark"],
        "success": colors.get("success", "#15803d"),
        "warning": colors.get("warning", "#a16207"),
        "error": colors.get("error", "#b91c1c"),
        "hover": colors.get("heading", colors["surface"]),
        "pressed": colors.get("heading", colors["surface"]),
        "selected": colors["accent"],
        "spacing": SPACING,
        "radii": RADII,
    }


class FluentCard(tk.Frame):
    """A theme-aware rounded grouped surface for existing Tk content.

    The canvas only paints the outer surface; native child widgets and their
    geometry managers remain unchanged and keyboard accessible.
    """

    def __init__(self, master: tk.Misc, *, tokens: Mapping[str, object], padding=(16, 14), **kwargs):
        super().__init__(master, bg=str(tokens["background"]), highlightthickness=0, bd=0, relief="flat", **kwargs)
        self.tokens = tokens
        self.padding = padding
        self._surface = tk.Canvas(self, bg=str(tokens["background"]), highlightthickness=0, bd=0)
        self._surface.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._redraw_surface, add="+")

    def _redraw_surface(self, _event=None) -> None:
        _draw_rounded_surface(self._surface, self.winfo_width(), self.winfo_height(), int(self.tokens["radii"]["card"]), str(self.tokens["surface"]), str(self.tokens["subtle_border"]))
        self._surface.lower()

    def content(self) -> tk.Frame:
        body = tk.Frame(self, bg=str(self.tokens["surface"]))
        body.pack(fill="both", expand=True, padx=self.padding[0], pady=self.padding[1])
        return body


def configure_styles(style: ttk.Style, colors: Mapping[str, str], font: str) -> None:
    """Apply the shared ttk palette, including initial state maps."""
    surface = colors["surface"]
    heading = colors.get("heading", surface)
    text = colors["text"]
    muted = colors["muted"]
    accent = colors["accent"]
    accent_dark = colors["accent_dark"]
    style.theme_use("clam")
    style.configure("Fluent.TCombobox", padding=(8, 6), fieldbackground=surface, background=surface, foreground=text, bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], focuscolor=accent, font=(font, 10))
    style.map("Fluent.TCombobox", fieldbackground=[("disabled", heading), ("readonly", surface), ("focus", surface), ("active", surface)], foreground=[("disabled", muted), ("readonly", text), ("focus", text), ("active", text)])
    style.configure("Accent.TButton", padding=(16, 9), font=(font, 10, "bold"), foreground="white", background=accent, borderwidth=0, focuscolor=accent_dark)
    style.map("Accent.TButton", background=[("disabled", heading), ("active", accent_dark), ("pressed", accent_dark)], foreground=[("disabled", muted), ("!disabled", "white")])
    style.configure("Secondary.TButton", padding=(12, 8), font=(font, 9), foreground=text, background=surface, borderwidth=0, focuscolor=accent)
    style.map("Secondary.TButton", background=[("disabled", heading), ("active", heading), ("pressed", heading)], foreground=[("disabled", muted), ("!disabled", text)])
    style.configure("Fluent.Treeview", rowheight=36, font=(font, 10), background=surface, fieldbackground=surface, foreground=text, borderwidth=0, focuscolor=accent)
    style.configure("Fluent.Treeview.Heading", font=(font, 9, "bold"), background=heading, foreground=muted, relief="flat", padding=(8, 9))
    style.map("Fluent.Treeview", background=[("selected", accent)], foreground=[("selected", "white")])
    style.map("Fluent.Treeview.Heading", background=[("active", heading), ("pressed", heading)], foreground=[("active", text), ("pressed", text)])


NAV_DESTINATIONS = ("overview", "analysis", "compare_os", "compare_machines", "upgrade", "recommendations", "reports", "settings", "about")
