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
    """A theme-aware grouped surface for existing Tk content.

    The frame intentionally keeps native Tk geometry and child widgets, so it
    remains portable in standalone Linux and Windows builds.
    """

    def __init__(self, master: tk.Misc, *, tokens: Mapping[str, object], padding=(16, 14), **kwargs):
        super().__init__(master, bg=str(tokens["surface"]), highlightbackground=str(tokens["subtle_border"]), highlightthickness=1, bd=0, relief="flat", **kwargs)
        self.tokens = tokens
        self.padding = padding

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
    style.configure("Fluent.TCombobox", padding=(8, 6), fieldbackground=surface, background=surface, foreground=text, bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], font=(font, 10))
    style.map("Fluent.TCombobox", fieldbackground=[("disabled", heading), ("readonly", surface), ("focus", surface), ("active", surface)], foreground=[("disabled", muted), ("readonly", text), ("focus", text), ("active", text)])
    style.configure("Accent.TButton", padding=(16, 9), font=(font, 10, "bold"), foreground="white", background=accent, borderwidth=0)
    style.map("Accent.TButton", background=[("disabled", heading), ("active", accent_dark), ("pressed", accent_dark)], foreground=[("disabled", muted), ("!disabled", "white")])
    style.configure("Secondary.TButton", padding=(12, 8), font=(font, 9), foreground=text, background=surface, borderwidth=0)
    style.map("Secondary.TButton", background=[("disabled", heading), ("active", heading), ("pressed", heading)], foreground=[("disabled", muted), ("!disabled", text)])
    style.configure("Fluent.Treeview", rowheight=36, font=(font, 10), background=surface, fieldbackground=surface, foreground=text, borderwidth=0)
    style.configure("Fluent.Treeview.Heading", font=(font, 9, "bold"), background=heading, foreground=muted, relief="flat", padding=(8, 9))
    style.map("Fluent.Treeview", background=[("selected", accent)], foreground=[("selected", "white")])
    style.map("Fluent.Treeview.Heading", background=[("active", heading), ("pressed", heading)], foreground=[("active", text), ("pressed", text)])


NAV_DESTINATIONS = ("overview", "analysis", "compare_os", "compare_machines", "upgrade", "recommendations", "reports", "settings", "about")

