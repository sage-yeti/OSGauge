from __future__ import annotations

import json
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from checker import (
    as_report,
    collect_machine_info,
    evaluate_all,
    explain_check,
    html_report,
    overall_status,
    plain_text_report,
    rank_compatibility,
)
from architecture import architecture_label
from requirements_update import RequirementsInfo, fetch_latest, load_requirements_info
from theme import colors_for, load_settings, load_theme_mode, save_settings, save_theme_mode
from version import APP_VERSION
from suitability import assess_suitability, suitability_dict
from lifecycle import lifecycle_status, profile_metadata
from installation_readiness import evaluate_installation_readiness
from machine_profile import export_profile, import_profile
from upgrade_planner import build_upgrade_plan, localized_plan
from machine_comparison import compare_machines, html_comparison_report, plain_text_comparison
from localization import LANGUAGES, preference_label, recommendation_match_label, resolve_language, status_label, t
from recommendation import PREFERENCES, PREFERENCE_LABELS, recommend, primary_recommendations
from ui_foundation import FluentCard, NAV_DESTINATIONS, configure_styles, tokens_for


COLORS = {"pass": "#15803d", "fail": "#b91c1c", "unknown": "#a16207", "review": "#a16207"}
ICONS = {"pass": "✓", "fail": "✕", "unknown": "?"}
UI = {
    "background": "#f5f7fb",
    "surface": "#ffffff",
    "border": "#dfe5ef",
    "text": "#1f2937",
    "muted": "#64748b",
    "accent": "#2563eb",
    "accent_dark": "#1d4ed8",
}


class ReadinessApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"OS Readiness Checker {APP_VERSION}")
        self.geometry("820x620")
        self.minsize(700, 500)
        self.configure(bg="#f4f6f8")
        self.settings = load_settings()
        self.language_selection = self.settings.get("language") if self.settings.get("language") in LANGUAGES else "System"
        self.language = resolve_language(self.language_selection)
        self.title(f"{t('app.title', self.language)} {APP_VERSION}")
        self.theme_mode = load_theme_mode()
        UI.update(colors_for(self.theme_mode))
        self.ui_tokens = tokens_for(UI)
        self.requirements_info = load_requirements_info()
        self.requirements = self.requirements_info.profiles
        self.machine = None
        self.machine_source = "This computer"
        self.profile_metadata = {}
        self.results = []
        self.all_results = {}
        self.ranked_results = []
        self.suitability_by_os = {}
        self.scan_in_progress = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()
        self.bind("<F5>", lambda _event: self.run_check())
        self.bind("<Control-r>", lambda _event: self.run_check())
        self.bind("<Control-s>", lambda _event: self.save_report())
        self.after_idle(self._restore_window)
        self.after(100, self.run_check)

    def _build(self) -> None:
        font = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
        style = ttk.Style(self)
        self.style = style
        self.font = font
        configure_styles(style, UI, font)

        self.configure(bg=UI["background"])
        shell = tk.Frame(self, bg=UI["background"])
        shell._ui_role = "root"
        shell.pack(fill="both", expand=True)
        self.nav = tk.Frame(shell, bg=UI["surface"], width=190, padx=12, pady=18, highlightbackground=UI["subtle_border"], highlightthickness=1)
        self.nav._ui_role = "nav"
        self.nav.pack(side="left", fill="y")
        self.nav.pack_propagate(False)
        tk.Label(self.nav, text="OS Readiness", bg=UI["surface"], fg=UI["text"], font=(font, 12, "bold")).pack(anchor="w", padx=8, pady=(0, 16))
        self.nav_buttons = {}
        nav_labels = {"overview": "nav.overview", "analysis": "nav.analysis", "compare_os": "nav.compare_os", "compare_machines": "nav.compare_machines", "upgrade": "nav.upgrade", "recommendations": "nav.recommendations", "reports": "nav.reports", "settings": "nav.settings", "about": "nav.about"}
        for page in NAV_DESTINATIONS:
            button = tk.Button(self.nav, text=t(nav_labels[page], self.language), command=lambda p=page: self._navigate(p), anchor="w", relief="flat", bd=0, padx=10, pady=7, bg=UI["surface"], fg=UI["text"], activebackground=UI["heading"], activeforeground=UI["text"], font=(font, 9), cursor="hand2")
            button.pack(fill="x", pady=1)
            self.nav_buttons[page] = button
            if page == "settings":
                tk.Frame(self.nav, bg=UI["subtle_border"], height=1).pack(fill="x", pady=8)
        workspace = tk.Frame(shell, bg=UI["background"])
        workspace._ui_role = "workspace"
        workspace.pack(side="left", fill="both", expand=True)
        header = tk.Frame(workspace, bg=UI["background"], padx=28, pady=24)
        header._ui_role = "workspace"
        header.pack(fill="x")
        tk.Label(header, text=t("app.title", self.language), bg=UI["background"], fg=UI["text"], font=(font, 23, "bold")).pack(anchor="w")
        self.subtitle_label = tk.Label(header, text=t("app.subtitle", self.language), bg=UI["background"], fg=UI["muted"], font=(font, 10))
        self.subtitle_label.pack(anchor="w", pady=(5, 0))
        theme_box = tk.Frame(header, bg=UI["background"])
        theme_box.pack(anchor="e", pady=(0, 2))
        self.theme_label = tk.Label(theme_box, text=t("label.theme", self.language), bg=UI["background"], fg=UI["muted"], font=(font, 9))
        self.theme_label.pack(side="left", padx=(0, 6))
        self.theme_choice = ttk.Combobox(theme_box, state="readonly", width=9, values=tuple(t(f"theme.{value.lower()}", self.language) for value in ("System", "Light", "Dark")), style="Fluent.TCombobox")
        self.theme_choice.set(t(f"theme.{self.theme_mode.lower()}", self.language))
        self.theme_choice.pack(side="left")
        self.theme_choice.bind("<<ComboboxSelected>>", lambda _event: self.change_theme())
        self.language_choice = ttk.Combobox(theme_box, state="readonly", width=11, values=("System", "English", "Italiano", "Español", "Deutsch", "Français"), style="Fluent.TCombobox")
        self.language_label = tk.Label(theme_box, text=t("label.language", self.language), bg=UI["background"], fg=UI["muted"], font=(font, 9))
        self.language_label.pack(side="left", padx=(8, 4))
        self.language_choice.pack_forget()
        self.language_choice.set(self.language_selection)
        self.language_choice.pack(side="left", padx=(8, 0))
        self.language_choice.bind("<<ComboboxSelected>>", lambda _event: self.change_language())
        self.about_button = ttk.Button(theme_box, text=t("action.about", self.language), command=self.show_about, style="Secondary.TButton")
        self.about_button.pack(side="left", padx=(8, 0))

        body = tk.Frame(workspace, bg=UI["background"], padx=28, pady=24)
        body._ui_role = "workspace"
        body.pack(fill="both", expand=True)
        controls = tk.Frame(body, bg=UI["surface"], padx=18, pady=16, highlightbackground=UI["border"], highlightthickness=1)
        controls.pack(fill="x", pady=(0, 14))
        self.os_label = tk.Label(controls, text=t("label.operating_system", self.language), bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold"))
        self.os_label.pack(side="left")
        self.choice = ttk.Combobox(controls, state="readonly", width=31, values=list(self.requirements), style="Fluent.TCombobox")
        last_os = self.settings.get("last_os")
        self.choice.current(list(self.requirements).index(last_os) if last_os in self.requirements else 0)
        self.choice.pack(side="left", padx=(14, 12))
        self.choice.bind("<<ComboboxSelected>>", lambda _event: self.show_detail())
        self.check_button = ttk.Button(controls, text=t("action.scan", self.language), command=self.run_check, style="Accent.TButton")
        self.check_button.pack(side="right")
        self.overview_button = ttk.Button(controls, text=t("action.overview", self.language), command=self.show_overview, style="Secondary.TButton")
        self.overview_button.pack(side="right", padx=(0, 8))
        self.recommend_button = ttk.Button(controls, text=t("recommend.action", self.language), command=self.show_recommendations, style="Secondary.TButton")
        self.recommend_button.pack(side="right", padx=(0, 8))
        self.update_button = ttk.Button(controls, text=t("action.updates", self.language), command=self.check_requirements_updates, style="Secondary.TButton")
        self.update_button.pack(side="right", padx=(0, 8))
        self.update_status = tk.Label(controls, text=f"DB v{self.requirements_info.data_version} ({self.requirements_info.source})", bg=UI["surface"], fg=UI["muted"], font=(font, 9))
        self.update_status.pack(side="right", padx=(0, 10))
        profile_actions = tk.Frame(body, bg=UI["background"])
        profile_actions._ui_role = "workspace"
        profile_actions.pack(fill="x", pady=(0, 10))
        self.import_button = ttk.Button(profile_actions, text=t("action.import_profile", self.language), command=self.import_machine_profile, style="Secondary.TButton")
        self.import_button.pack(side="left")
        self.export_button = ttk.Button(profile_actions, text=t("action.export_profile", self.language), command=self.export_machine_profile, style="Secondary.TButton")
        self.export_button.pack(side="left", padx=(8, 0))
        self.machine_compare_button = ttk.Button(profile_actions, text=t("action.compare_machines", self.language), command=self.show_machine_compare, style="Secondary.TButton", state="disabled")
        self.machine_compare_button.pack(side="left", padx=(8, 0))
        self.source_status = tk.Label(profile_actions, text=f"{t('label.machine_source', self.language)}: {t('profile.source_local', self.language)}", bg=UI["background"], fg=UI["muted"], font=(font, 9))
        self.source_status.pack(side="right")

        summary_card = FluentCard(body, tokens=self.ui_tokens, padding=(18, 14))
        summary_card.pack(fill="x", pady=(0, 14))
        self.status_badge = tk.Label(summary_card, text="  SCANNING  ", bg="#e2e8f0", fg=UI["muted"], font=(font, 9, "bold"), padx=8, pady=5)
        self.status_badge.pack(side="left", padx=(0, 12))
        self.summary = tk.Label(summary_card, text="Scanning…", bg=UI["surface"], fg=UI["text"], font=(font, 14, "bold"))
        self.summary.pack(side="left", anchor="w")

        columns = ("result", "detected", "required")
        table_card = tk.Frame(body, bg=UI["surface"], padx=1, pady=1, highlightbackground=UI["border"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_card, columns=columns, show="tree headings", style="Fluent.Treeview")
        self.table.heading("#0", text=t("label.check", self.language))
        self.table.heading("result", text=t("label.result", self.language))
        self.table.heading("detected", text=t("label.detected", self.language))
        self.table.heading("required", text=t("label.required", self.language))
        self.table.column("#0", width=190)
        self.table.column("result", width=90, anchor="center")
        self.table.column("detected", width=190)
        self.table.column("required", width=190)
        self.table.pack(fill="both", expand=True)
        self.table.tag_configure("pass", foreground=COLORS["pass"])
        self.table.tag_configure("fail", foreground=COLORS["fail"])
        self.table.tag_configure("unknown", foreground=COLORS["unknown"])
        self.table.bind("<<TreeviewSelect>>", self.show_selected_check)

        footer = tk.Frame(body, bg=UI["surface"], padx=18, pady=14, highlightbackground=UI["border"], highlightthickness=1)
        footer.pack(fill="x")
        self.details = tk.Label(footer, text="", justify="left", anchor="w", bg=UI["surface"], fg=UI["muted"], wraplength=570, font=(font, 9))
        self.details.pack(side="left", fill="x", expand=True)
        self.source_button = ttk.Button(footer, text=t("action.source", self.language), command=self.open_source, style="Secondary.TButton")
        self.source_button.pack(side="right", padx=(8, 0))
        self.save_button = ttk.Button(footer, text=t("action.save_report", self.language), command=self.save_report, style="Secondary.TButton")
        self.save_button.pack(side="right")
        self.html_button = ttk.Button(footer, text=t("action.save_html", self.language), command=self.save_html_report, style="Secondary.TButton")
        self.html_button.pack(side="right", padx=(8, 0))
        self.copy_button = ttk.Button(footer, text=t("action.copy_results", self.language), command=self.copy_results, style="Secondary.TButton")
        self.copy_button.pack(side="right", padx=(8, 0))
        self.compare_button = ttk.Button(footer, text=t("action.compare", self.language), command=self.show_compare, style="Secondary.TButton", state="disabled")
        self.compare_button.pack(side="right", padx=(8, 0))
        self.plan_button = ttk.Button(footer, text=t("action.upgrade_plan", self.language), command=self.show_upgrade_plan, style="Secondary.TButton", state="disabled")
        self.plan_button.pack(side="right", padx=(8, 0))
        self._apply_theme(self)
        self._set_active_nav("overview")

    def _set_active_nav(self, page: str) -> None:
        self.active_page = page
        for key, button in self.nav_buttons.items():
            active = key == page
            button.configure(bg=UI["heading"] if active else UI["surface"], fg=UI["accent"] if active else UI["text"], font=(self.font, 9, "bold" if active else "normal"))

    def _navigate(self, page: str) -> None:
        """Route to existing views without rescanning or changing machine state."""
        self._set_active_nav(page)
        if page == "overview":
            self.show_overview()
        elif page == "analysis":
            self.show_detail()
        elif page == "compare_os":
            self.show_compare()
        elif page == "compare_machines":
            self.show_machine_compare()
        elif page == "upgrade":
            self.show_upgrade_plan()
        elif page == "recommendations":
            self.show_recommendations()
        elif page == "reports":
            self.save_report()
        elif page == "settings":
            self.theme_choice.focus_set()
        elif page == "about":
            self.show_about()

    def _restore_window(self) -> None:
        try:
            width = max(700, min(2400, int(self.settings.get("width", 820))))
            height = max(500, min(1600, int(self.settings.get("height", 620))))
        except (TypeError, ValueError):
            width, height = 820, 620
        self.geometry(f"{width}x{height}")
        try:
            x, y = int(self.settings.get("x")), int(self.settings.get("y"))
            self.update_idletasks()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            if -width + 120 <= x <= sw - 120 and -height + 100 <= y <= sh - 100:
                self.geometry(f"{width}x{height}+{x}+{y}")
        except (TypeError, ValueError, tk.TclError):
            pass

    def _on_close(self) -> None:
        self.update_idletasks()
        settings = dict(self.settings)
        settings.update({"theme": self.theme_mode, "last_os": self.choice.get(), "width": self.winfo_width(), "height": self.winfo_height(), "x": self.winfo_x(), "y": self.winfo_y()})
        save_settings(settings)
        self.destroy()

    def run_check(self) -> None:
        if self.scan_in_progress:
            return
        self.machine_source = "This computer"
        self.profile_metadata = {}
        self.scan_in_progress = True
        self.check_button.config(state="disabled")
        self.summary.config(text=t("overview.scanning", self.language), fg="#374151")
        screen = (self.winfo_screenwidth(), self.winfo_screenheight())
        threading.Thread(target=self._scan, args=(screen,), daemon=True).start()

    def change_theme(self) -> None:
        selected = self.theme_choice.get()
        self.theme_mode = next((value for value in ("System", "Light", "Dark") if selected == t(f"theme.{value.lower()}", self.language)), "System")
        save_theme_mode(self.theme_mode)
        UI.update(colors_for(self.theme_mode))
        self.ui_tokens = tokens_for(UI)
        self._apply_theme(self)

    def change_language(self) -> None:
        self.language_selection = self.language_choice.get() if self.language_choice.get() in LANGUAGES else "System"
        self.language = resolve_language(self.language_selection)
        self.settings["language"] = self.language_selection
        save_settings(self.settings)
        self.title(f"{t('app.title', self.language)} {APP_VERSION}")
        self.theme_choice.config(values=tuple(t(f"theme.{value.lower()}", self.language) for value in ("System", "Light", "Dark")))
        self.theme_choice.set(t(f"theme.{self.theme_mode.lower()}", self.language))
        self.about_button.config(text=t("action.about", self.language))
        self.check_button.config(text=t("action.scan", self.language))
        self.overview_button.config(text=t("action.overview", self.language))
        self.recommend_button.config(text=t("recommend.action", self.language))
        self.update_button.config(text=t("action.updates", self.language))
        self.import_button.config(text=t("action.import_profile", self.language))
        self.export_button.config(text=t("action.export_profile", self.language))
        self.machine_compare_button.config(text=t("action.compare_machines", self.language))
        self.source_button.config(text=t("action.source", self.language))
        self.save_button.config(text=t("action.save_report", self.language))
        self.html_button.config(text=t("action.save_html", self.language))
        self.copy_button.config(text=t("action.copy_results", self.language))
        self.compare_button.config(text=t("action.compare", self.language))
        self.plan_button.config(text=t("action.upgrade_plan", self.language))
        self.source_status.config(text=f"{t('label.machine_source', self.language)}: {t('profile.source_imported' if self.machine_source == 'Imported profile' else 'profile.source_local', self.language)}")
        self.subtitle_label.config(text=t("app.subtitle", self.language))
        self.theme_label.config(text=t("label.theme", self.language))
        self.language_label.config(text=t("label.language", self.language))
        self.os_label.config(text=t("label.operating_system", self.language))
        nav_labels = {"overview": "nav.overview", "analysis": "nav.analysis", "compare_os": "nav.compare_os", "compare_machines": "nav.compare_machines", "upgrade": "nav.upgrade", "recommendations": "nav.recommendations", "reports": "nav.reports", "settings": "nav.settings", "about": "nav.about"}
        for page, button in self.nav_buttons.items():
            button.config(text=t(nav_labels[page], self.language))
        for column, key in (("#0", "label.check"), ("result", "label.result"), ("detected", "label.detected"), ("required", "label.required")):
            self.table.heading(column, text=t(key, self.language))
        if self.machine and self.choice.get() in self.all_results:
            self.show_detail()

    def show_about(self) -> None:
        window = tk.Toplevel(self)
        window.title("About OS Readiness Checker")
        window.geometry("430x330")
        window.resizable(False, False)
        window.configure(bg=UI["background"])
        card = tk.Frame(window, bg=UI["surface"], padx=24, pady=22, highlightbackground=UI["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(card, text=t("app.title", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 17, "bold")).pack(anchor="w")
        tk.Label(card, text=f"Version {APP_VERSION}\n{t('app.subtitle', self.language)}\n\nRequirements database: v{self.requirements_info.data_version} ({self.requirements_info.source})\nRuns on Windows and Linux. License: MIT", justify="left", anchor="w", bg=UI["surface"], fg=UI["muted"], font=(self.font, 9)).pack(fill="x", pady=(10, 16))
        actions = tk.Frame(card, bg=UI["surface"])
        actions.pack(fill="x")
        ttk.Button(actions, text="Open GitHub", command=lambda: webbrowser.open("https://github.com/sage-yeti/os-readiness-checker"), style="Secondary.TButton").pack(side="left")
        ttk.Button(actions, text="Check updates", command=self.check_requirements_updates, style="Secondary.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(actions, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(side="right")
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def show_recommendations(self) -> None:
        if not self.machine or not self.all_results:
            messagebox.showinfo("Recommend an OS", "Run a scan first so recommendations can use the current machine.")
            return
        window = tk.Toplevel(self)
        window.title(t("recommend.title", self.language))
        window.geometry("620x560")
        window.configure(bg=UI["background"])
        card = tk.Frame(window, bg=UI["surface"], padx=18, pady=16, highlightbackground=UI["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(card, text=t("recommend.prompt", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 11, "bold"), wraplength=550, justify="left").pack(anchor="w")
        vars_by_key = {key: tk.IntVar(value=int(self.settings.get("preferences", {}).get(key, 0))) for key in PREFERENCES}
        choices = tk.Frame(card, bg=UI["surface"])
        choices.pack(fill="x", pady=(12, 8))
        for key in PREFERENCES:
            row = tk.Frame(choices, bg=UI["surface"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=preference_label(key, self.language), bg=UI["surface"], fg=UI["text"], width=34, anchor="w", font=(self.font, 9)).pack(side="left")
            for value, label in ((0, "—"), (1, "Somewhat"), (2, "Important")):
                tk.Radiobutton(row, text=label, value=value, variable=vars_by_key[key], bg=UI["surface"], fg=UI["text"], activebackground=UI["surface"], selectcolor=UI["background"], font=(self.font, 8)).pack(side="left")
        output = tk.Label(card, text="", bg=UI["surface"], fg=UI["muted"], justify="left", anchor="nw", wraplength=550, font=(self.font, 9))
        output.pack(fill="both", expand=True, pady=(8, 8))
        def analyze() -> None:
            preferences = {key: var.get() for key, var in vars_by_key.items()}
            self.settings["preferences"] = preferences
            save_settings(self.settings)
            suits = {name: self.suitability_by_os.get(name) for name in self.requirements}
            readiness = {name: evaluate_installation_readiness(self.machine, self.requirements[name], self.all_results[name]) for name in self.requirements}
            ranked = recommend(self.requirements, self.all_results, suits, readiness, preferences)
            primary = primary_recommendations(ranked)[:5]
            lines = [t("recommend.disclaimer", self.language), ""]
            if not primary:
                lines.append(t("recommend.none", self.language))
            for item in primary:
                lines.append(f"{item['name']} — {recommendation_match_label(item['preference_match_category'], self.language)} ({item['preference_score']}/100)")
                if item["strengths"]:
                    lines.append("  " + t("recommend.strengths", self.language) + ": " + ", ".join(item["strengths"]))
                if item["tradeoffs"]:
                    lines.append("  " + t("recommend.tradeoffs", self.language) + ": " + ", ".join(item["tradeoffs"]))
            output.config(text="\n".join(lines))
        ttk.Button(card, text=t("recommend.analyze", self.language), command=analyze, style="Accent.TButton").pack(anchor="e")
        self._apply_theme(window)

    def _apply_theme(self, widget) -> None:
        try:
            if isinstance(widget, tk.Toplevel):
                widget.configure(bg=UI["background"])
            elif isinstance(widget, tk.Frame):
                role = getattr(widget, "_ui_role", "surface")
                widget.configure(bg=UI["background"] if role in {"root", "workspace", "nav"} else UI["surface"])
                if isinstance(widget, FluentCard):
                    widget.configure(bg=UI["surface"], highlightbackground=UI.get("subtle_border", UI["border"]))
            elif isinstance(widget, tk.Label):
                parent_role = getattr(widget.master, "_ui_role", "surface")
                widget.configure(bg=UI["background"] if parent_role == "workspace" else UI["surface"], fg=UI["text"])
            elif isinstance(widget, tk.Button) and widget.master is self.nav:
                active = getattr(self, "active_page", "overview") == next((key for key, value in self.nav_buttons.items() if value is widget), "")
                widget.configure(bg=UI["heading"] if active else UI["surface"], fg=UI["accent"] if active else UI["text"], activebackground=UI["heading"], activeforeground=UI["text"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._apply_theme(child)
        configure_styles(self.style, UI, self.font)
        self.table.tag_configure("pass", foreground="#4ade80" if self.theme_mode == "Dark" else COLORS["pass"])
        self.table.tag_configure("fail", foreground="#f87171" if self.theme_mode == "Dark" else COLORS["fail"])
        self.table.tag_configure("unknown", foreground="#facc15" if self.theme_mode == "Dark" else COLORS["unknown"])

    def _scan(self, screen: tuple[int, int]) -> None:
        try:
            machine = collect_machine_info(screen)
            all_results = evaluate_all(machine, self.requirements)
            suitability = {name: suitability_dict(assess_suitability(machine, profile, all_results[name])) for name, profile in self.requirements.items()}
            ranked = rank_compatibility(all_results, suitability)
            self.after(0, lambda: self._show_overview(machine, all_results, ranked))
        except Exception as exc:
            self.after(0, lambda error=exc: self._scan_failed(error))

    def _scan_failed(self, error: Exception) -> None:
        self.scan_in_progress = False
        self.check_button.config(state="normal")
        self.summary.config(text="Scan could not be completed; try again.", fg=UI["text"])
        self.status_badge.config(text="  REVIEW  ", bg=COLORS["review"], fg="white")
        self.details.config(text=f"Hardware information was unavailable: {error}")

    def _clear_table(self) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

    def _show_detail(self, results) -> None:
        self._clear_table()
        for item in results:
            self.table.insert("", "end", text=item.name, values=(ICONS[item.status] + " " + status_label(item.status, self.language), item.detected, item.required), tags=(item.status,))

    def show_selected_check(self, _event=None) -> None:
        if not self.machine or not self.choice.get() or not self.table.selection():
            return
        item_id = self.table.selection()[0]
        name = self.table.item(item_id, "text")
        check = next((item for item in self.all_results.get(self.choice.get(), []) if item.name == name), None)
        if not check:
            return
        info = explain_check(self.machine, self.requirements[self.choice.get()], check, self.language)
        text = f"{check.name}: {info['explanation']}"
        if info["remediation"]:
            text += f"\nNext step: {info['remediation']}"
        self.details.config(text=text)

    def _show_overview(self, machine, all_results, ranked) -> None:
        self.machine, self.all_results, self.ranked_results = machine, all_results, ranked
        source_key = "profile.source_imported" if self.machine_source == "Imported profile" else "profile.source_local"
        self.source_status.config(text=f"{t('label.machine_source', self.language)}: {t(source_key, self.language)}")
        if self.choice.get() not in all_results and all_results:
            self.choice.current(0)
        self.results = all_results.get(self.choice.get(), [])
        self._clear_table()
        self.table.heading("#0", text="Operating system")
        self.table.heading("result", text="Status")
        self.table.heading("detected", text="Compatibility")
        self.table.heading("required", text="Suitability")
        self.table.column("#0", width=270)
        self.table.column("result", width=110, anchor="center")
        self.table.column("detected", width=120, anchor="center")
        self.table.column("required", width=110, anchor="center")
        for item in ranked:
            status = item["status"]
            self.table.insert("", "end", text=item["name"], values=(ICONS.get(status, "") + " " + status_label(status, self.language), f'{item["score"]}/100', t("status." + item["suitability"]["category"].lower().replace(" ", "_"), self.language)), tags=(status,))
        self.summary.config(text=t("overview.compared", self.language, count=len(ranked)), fg=UI["text"])
        self.status_badge.config(text=f"  {t('status.overview', self.language).upper()}  ", bg=UI["accent"], fg="white")
        source_note = ""
        if self.machine_source == "Imported profile":
            captured = self.profile_metadata.get("created_at", "")
            source_note = f" Imported profile captured {captured}. Installation readiness reflects its recorded configuration."
        self.details.config(text=f"Requirements database v{self.requirements_info.data_version} ({self.requirements_info.source}). Compatibility is based on published requirements; suitability is application-defined headroom guidance.{source_note}")
        self.check_button.config(state="normal")
        self.scan_in_progress = False
        self.compare_button.config(state="normal")
        self.plan_button.config(state="normal")
        self.machine_compare_button.config(state="normal")

    def show_overview(self) -> None:
        if self.machine and self.ranked_results:
            self._show_overview(self.machine, self.all_results, self.ranked_results)

    def show_detail(self) -> None:
        if not self.machine or self.choice.get() not in self.all_results:
            return
        name = self.choice.get()
        self.settings["last_os"] = name
        save_settings(self.settings)
        results = self.all_results[name]
        self.results = results
        self._show_detail(results)
        self.table.heading("#0", text=t("label.check", self.language))
        self.table.heading("result", text=t("label.result", self.language))
        self.table.heading("detected", text=t("label.detected", self.language))
        self.table.heading("required", text=t("label.required", self.language))
        self.table.column("#0", width=190)
        self.table.column("result", width=90, anchor="center")
        self.table.column("detected", width=190)
        self.table.column("required", width=190)
        status = overall_status(results)
        suitability = suitability_dict(assess_suitability(self.machine, self.requirements[name], results))
        messages = {
            "pass": t("overview.meets", self.language),
            "fail": t("overview.fails", self.language),
            "review": t("overview.review", self.language),
        }
        score = next((item["score"] for item in self.ranked_results if item["name"] == name), 0)
        self.summary.config(text=f"{messages[status]} • Compatibility score {score}/100 • {suitability['category']}", fg=UI["text"])
        self.status_badge.config(text=f"  {status_label(status, self.language).upper()}  ", bg=COLORS[status], fg="white")
        notes = self.requirements[name].get("notes", [])
        lifecycle = profile_metadata(name, self.requirements[name])
        lifecycle["support_status"] = lifecycle_status(self.requirements[name])
        readiness = evaluate_installation_readiness(self.machine, self.requirements[name], results)
        gpu = self.machine.gpu_name or "Unknown"
        if self.machine.gpu_vram_mb:
            gpu += f" ({self.machine.gpu_vram_mb} MB VRAM)"
        lifecycle_line = f"Release: {lifecycle['release']} • {t('label.lifecycle', self.language)}: {lifecycle['lifecycle_type']} • Status: {status_label(lifecycle['support_status'], self.language)}"
        readiness_line = f"{t('label.installation_readiness', self.language)}: {status_label(readiness['status'], self.language)} — {readiness['explanation']}"
        readiness_items = [f"  {status_label(item['status'], self.language).upper()}: {item['name']} — {item['detected']} / {item['required']}" for item in readiness["checks"]]
        machine_details = [
            f"Architecture: {architecture_label(self.machine.architecture)}",
            f"{t('machine.processor', self.language)}: {self.machine.cpu_name}",
            f"{t('machine.graphics', self.language)}: {gpu}",
            f"{t('machine.system_disk', self.language)}: {self.machine.system_disk or 'Unknown'} ({self.machine.storage_partition_style or 'Unknown'} / {self.machine.storage_filesystem or 'Unknown'})",
            f"{t('machine.virtualization', self.language)}: {self.machine.virtualization or 'Unknown'}",
        ]
        suitability_label = t("status." + suitability["category"].lower().replace(" ", "_"), self.language)
        self.details.config(text=f"Requirements database v{self.requirements_info.data_version} ({self.requirements_info.source})\n{lifecycle_line}\n{readiness_line}\n" + "\n".join(readiness_items + [f"{t('label.suitability', self.language)}: {suitability_label} — {suitability['explanation']}"] + machine_details + ["• " + note for note in notes]))

    def show_compare(self) -> None:
        if not self.machine or not self.all_results:
            return
        window = tk.Toplevel(self)
        window.title("Compare operating systems")
        window.geometry("760x520")
        window.configure(bg=UI["background"])
        font = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
        names = list(self.requirements)
        controls = tk.Frame(window, bg=UI["surface"], padx=16, pady=12, highlightbackground=UI["border"], highlightthickness=1)
        controls.pack(fill="x", padx=20, pady=20)
        tk.Label(controls, text="Compare", bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold")).pack(side="left")
        left = ttk.Combobox(controls, state="readonly", values=names, width=23, style="Fluent.TCombobox")
        right = ttk.Combobox(controls, state="readonly", values=names, width=23, style="Fluent.TCombobox")
        left.current(0)
        right.current(1 if len(names) > 1 else 0)
        left.pack(side="left", padx=(12, 8))
        right.pack(side="left")
        card = tk.Frame(window, bg=UI["surface"], padx=1, pady=1, highlightbackground=UI["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        table = ttk.Treeview(card, columns=("detected", "left", "right"), show="tree headings", style="Fluent.Treeview")
        table.heading("#0", text="Check")
        table.heading("detected", text="Detected")
        table.heading("left", text="Requirement")
        table.heading("right", text="Requirement")
        table.column("#0", width=170)
        table.column("detected", width=170)
        table.column("left", width=170)
        table.column("right", width=170)
        table.pack(fill="both", expand=True)

        def refresh(*_args) -> None:
            table.delete(*table.get_children())
            left_checks = {item.name: item for item in self.all_results[left.get()]}
            right_checks = {item.name: item for item in self.all_results[right.get()]}
            for check_name in dict.fromkeys([*left_checks, *right_checks]):
                a, b = left_checks.get(check_name), right_checks.get(check_name)
                detected = (a or b).detected if (a or b) else "—"
                table.insert("", "end", text=check_name, values=(detected, a.required if a else "—", b.required if b else "—"))

        left.bind("<<ComboboxSelected>>", refresh)
        right.bind("<<ComboboxSelected>>", refresh)
        refresh()

    def show_upgrade_plan(self) -> None:
        if not self.machine or self.choice.get() not in self.all_results:
            return
        name = self.choice.get()
        results = self.all_results[name]
        suitability = suitability_dict(assess_suitability(self.machine, self.requirements[name], results))
        readiness = evaluate_installation_readiness(self.machine, self.requirements[name], results)
        lifecycle = profile_metadata(name, self.requirements[name])
        lifecycle["support_status"] = lifecycle_status(self.requirements[name])
        plan = localized_plan(build_upgrade_plan(self.machine, self.requirements[name], results, suitability, readiness, lifecycle), self.language)
        window = tk.Toplevel(self)
        window.title(t("action.upgrade_plan", self.language))
        window.geometry("720x560")
        window.configure(bg=UI["background"])
        card = tk.Frame(window, bg=UI["surface"], padx=20, pady=18, highlightbackground=UI["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text=f"{name} — {t('action.upgrade_plan', self.language)}", bg=UI["surface"], fg=UI["text"], font=(self.font, 16, "bold")).pack(anchor="w")
        tk.Label(card, text=plan["overall_summary"], bg=UI["surface"], fg=UI["muted"], font=(self.font, 10), wraplength=650, justify="left").pack(anchor="w", pady=(6, 12))
        text = tk.Text(card, height=20, wrap="word", relief="flat", bg=UI["surface"], fg=UI["text"], font=(self.font, 10), padx=4, pady=4)
        text.pack(fill="both", expand=True)
        section_names = {"required_hardware_changes": "planner.hardware", "required_configuration_changes": "planner.configuration", "storage_actions": "planner.storage", "unresolved_items": "planner.unresolved", "optional_improvements": "planner.optional", "already_satisfied": "planner.satisfied"}
        for key, label_key in section_names.items():
            items = plan[key]
            if not items:
                continue
            text.insert("end", t(label_key, self.language) + "\n", "heading")
            for item in items:
                if key == "already_satisfied":
                    text.insert("end", f"• {item['check']}: {item['current']} / {item['target']}\n")
                else:
                    gap = f"; {t('planner.gap', self.language)} {item['gap']}" if item.get("gap") else ""
                    text.insert("end", f"• {item['check']}: {item['current']} / {item['target']}{gap}\n  {item['explanation']}\n")
        if plan["lifecycle_warning"]:
            text.insert("end", f"\n{t('planner.lifecycle', self.language)}: {plan['lifecycle_warning']}\n")
        text.configure(state="disabled")
        ttk.Button(card, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(anchor="e", pady=(12, 0))
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def show_machine_compare(self) -> None:
        if not self.machine:
            return
        window = tk.Toplevel(self)
        window.title(t("comparison.title", self.language))
        window.geometry("900x650")
        window.configure(bg=UI["background"])
        sources = [self.machine, None]
        labels = [t("comparison.this_computer", self.language), t("comparison.choose_profile", self.language)]
        machine_names = (t("comparison.machine_a", self.language), t("comparison.machine_b", self.language))
        metadata = [{}, {}]
        font = self.font
        controls = tk.Frame(window, bg=UI["surface"], padx=16, pady=12, highlightbackground=UI["border"], highlightthickness=1)
        controls.pack(fill="x", padx=20, pady=20)
        target = ttk.Combobox(controls, state="readonly", values=list(self.requirements), width=25, style="Fluent.TCombobox")
        target.current(0)
        target.pack(side="left", padx=(8, 14))
        labels_vars = [tk.StringVar(value=labels[0]), tk.StringVar(value=labels[1])]
        for index in range(2):
            tk.Label(controls, text=f"{t('comparison.machine', self.language)} {'A' if index == 0 else 'B'}", bg=UI["surface"], fg=UI["text"], font=(font, 9, "bold")).pack(side="left", padx=(0 if index == 0 else 12, 4))
            tk.Label(controls, textvariable=labels_vars[index], bg=UI["surface"], fg=UI["muted"], width=20, anchor="w", font=(font, 9)).pack(side="left")

        card = tk.Frame(window, bg=UI["surface"], padx=1, pady=1, highlightbackground=UI["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        table = ttk.Treeview(card, columns=("a", "b", "difference"), show="tree headings", style="Fluent.Treeview")
        table.heading("#0", text=t("comparison.attribute", self.language)); table.heading("a", text=machine_names[0]); table.heading("b", text=machine_names[1]); table.heading("difference", text=t("comparison.difference", self.language))
        table.column("#0", width=190); table.column("a", width=210); table.column("b", width=210); table.column("difference", width=130)
        table.pack(fill="both", expand=True)
        summary = tk.Label(window, text="", justify="left", anchor="w", bg=UI["surface"], fg=UI["text"], padx=18, pady=10, wraplength=820)
        summary.pack(fill="x", padx=20)
        result_holder = {"value": None}

        def choose_profile(index: int) -> None:
            path = filedialog.askopenfilename(filetypes=[("Machine profile", "*.osrprofile"), ("JSON", "*.json")])
            if not path:
                return
            try:
                machine, meta = import_profile(Path(path))
            except ValueError as exc:
                messagebox.showerror(t("dialog.profile_import_error", self.language), str(exc), parent=window)
                return
            sources[index], metadata[index] = machine, meta
            captured = meta.get("created_at") or "unknown"
            labels[index] = f"{t('comparison.imported_profile', self.language)} ({Path(path).name}; {captured})"
            labels_vars[index].set(labels[index])
            refresh()

        def use_current(index: int) -> None:
            sources[index], metadata[index] = self.machine, {}
            labels[index] = t("comparison.this_computer", self.language)
            labels_vars[index].set(labels[index])
            refresh()

        for index in range(2):
            ttk.Button(controls, text=t("comparison.import", self.language), command=lambda i=index: choose_profile(i), style="Secondary.TButton").pack(side="left", padx=(4, 0))
            ttk.Button(controls, text=t("comparison.use_current", self.language), command=lambda i=index: use_current(i), style="Secondary.TButton").pack(side="left", padx=(4, 0))

        def refresh(*_args) -> None:
            if sources[0] is None or sources[1] is None:
                return
            result_holder["value"] = compare_machines(sources[0], sources[1], self.requirements, target.get(), labels=tuple(labels), metadata=tuple(metadata))
            table.delete(*table.get_children())
            for row in result_holder["value"]["hardware"]:
                table.insert("", "end", text=row["name"], values=(row["a"], row["b"], row["difference"]))
            selected = result_holder["value"].get("target")
            summary.config(text=(f"{selected['name']} — {selected['lifecycle'].get('release', '')} ({selected['lifecycle'].get('support_status', '')})\n" f"{selected['summary']}\n" f"{machine_names[0]} — {selected['a']['compatibility'].upper()} ({selected['a']['compatibility_score']}/100), {selected['a']['suitability']['category']}, {selected['a']['readiness']}\n" f"{machine_names[1]} — {selected['b']['compatibility'].upper()} ({selected['b']['compatibility_score']}/100), {selected['b']['suitability']['category']}, {selected['b']['readiness']}") if selected else "")

        target.bind("<<ComboboxSelected>>", refresh)
        refresh()
        actions = tk.Frame(window, bg=UI["background"])
        actions.pack(fill="x", padx=20, pady=(0, 18))
        def save_comparison_html() -> None:
            if not result_holder["value"]: return
            path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML report", "*.html")], initialfile="machine-comparison.html")
            if path: Path(path).write_text(html_comparison_report(result_holder["value"]), encoding="utf-8")
        def copy_comparison() -> None:
            if not result_holder["value"]: return
            self.clipboard_clear(); self.clipboard_append(plain_text_comparison(result_holder["value"])); self.update()
            messagebox.showinfo(t("comparison.copy", self.language), t("dialog.results_copied", self.language), parent=window)
        ttk.Button(actions, text=t("comparison.save_html", self.language), command=save_comparison_html, style="Secondary.TButton").pack(side="left")
        ttk.Button(actions, text=t("comparison.copy", self.language), command=copy_comparison, style="Secondary.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(actions, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(side="right")
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def open_source(self) -> None:
        webbrowser.open(self.requirements[self.choice.get()]["source"])

    def save_report(self) -> None:
        if not self.machine:
            return
        target = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON report", "*.json")], initialfile="os-readiness-report.json")
        if target:
            report = as_report(self.machine, self.requirements[self.choice.get()])
            report["target_os"] = self.choice.get()
            report["machine_source"] = self.machine_source
            if self.profile_metadata:
                report["profile_metadata"] = self.profile_metadata
            Path(target).write_text(json.dumps(report, indent=2), encoding="utf-8")
            messagebox.showinfo("Report saved", "The readiness report was saved successfully.")

    def save_html_report(self) -> None:
        if not self.machine:
            return
        target = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML report", "*.html")], initialfile="os-readiness-report.html")
        if target:
            name = self.choice.get()
            html = html_report(self.machine, name, self.requirements[name], self.language)
            if self.machine_source == "Imported profile":
                html = html.replace("<h1>OS Readiness Report</h1>", f"<h1>OS Readiness Report</h1><p><strong>Machine source:</strong> Imported profile (captured {self.profile_metadata.get('created_at', 'unknown')}).</p>")
            Path(target).write_text(html, encoding="utf-8")
            messagebox.showinfo("Report saved", "The HTML report was saved successfully.")

    def copy_results(self) -> None:
        if not self.machine:
            return
        name = self.choice.get()
        self.clipboard_clear()
        text = plain_text_report(self.machine, name, self.requirements[name], self.language)
        if self.machine_source == "Imported profile":
            text = f"Machine source: Imported profile (captured {self.profile_metadata.get('created_at', 'unknown')})\n" + text
        self.clipboard_append(text)
        self.update()
        messagebox.showinfo(t("action.copy_results", self.language), t("dialog.results_copied", self.language))

    def check_requirements_updates(self) -> None:
        self.update_button.config(state="disabled")
        threading.Thread(target=self._check_requirements_updates, daemon=True).start()

    def _check_requirements_updates(self) -> None:
        try:
            info = fetch_latest()
        except Exception:
            info = None
        self.after(0, lambda: self._finish_requirements_update(info))

    def _finish_requirements_update(self, info: RequirementsInfo | None) -> None:
        self.update_button.config(state="normal")
        if info is None:
            self.update_status.config(text=f"DB v{self.requirements_info.data_version} ({self.requirements_info.source}); no newer data")
            return
        self.requirements_info = info
        self.requirements = info.profiles
        self.choice.config(values=list(self.requirements))
        if self.machine:
            self.all_results = evaluate_all(self.machine, self.requirements)
            suitability = {name: suitability_dict(assess_suitability(self.machine, profile, self.all_results[name])) for name, profile in self.requirements.items()}
            self.ranked_results = rank_compatibility(self.all_results, suitability)
            self.results = self.all_results.get(self.choice.get(), [])
            self._show_overview(self.machine, self.all_results, self.ranked_results)
        self.update_status.config(text=f"DB v{info.data_version} ({info.source}); updated")

    def export_machine_profile(self) -> None:
        if not self.machine:
            messagebox.showinfo(t("action.export_profile", self.language), t("dialog.no_scan", self.language))
            return
        target = filedialog.asksaveasfilename(defaultextension=".osrprofile", filetypes=[("Machine profile", "*.osrprofile"), ("JSON", "*.json")], initialfile="machine-profile.osrprofile")
        if target:
            export_profile(self.machine, Path(target), data_version=self.requirements_info.data_version)
            messagebox.showinfo(t("dialog.profile_export", self.language), t("dialog.profile_exported", self.language))

    def import_machine_profile(self) -> None:
        target = filedialog.askopenfilename(filetypes=[("Machine profile", "*.osrprofile"), ("JSON", "*.json")])
        if not target:
            return
        try:
            machine, metadata = import_profile(Path(target))
            all_results = evaluate_all(machine, self.requirements)
            suitability = {name: suitability_dict(assess_suitability(machine, profile, all_results[name])) for name, profile in self.requirements.items()}
            ranked = rank_compatibility(all_results, suitability)
            self.machine_source, self.profile_metadata = "Imported profile", metadata
            self._show_overview(machine, all_results, ranked)
        except ValueError as exc:
            messagebox.showerror(t("dialog.profile_import_error", self.language), str(exc))


if __name__ == "__main__":
    ReadinessApp().mainloop()
