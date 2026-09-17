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
from localization import LANGUAGES, preference_label, readiness_explanation, recommendation_match_label, resolve_language, status_label, suitability_explanation, t
from os_icons import load_logo
from recommendation import PREFERENCES, PREFERENCE_LABELS, recommend, primary_recommendations
from ui_foundation import CARD_PADDING, CONTROL_GAP, DIALOG_PADDING, FluentCard, NAV_DESTINATIONS, PAGE_PADDING, configure_styles, tokens_for


COLORS = {"pass": "#15803d", "fail": "#b91c1c", "unknown": "#a16207", "review": "#a16207"}
ICONS = {"pass": "✓", "fail": "✕", "unknown": "?"}
UI = colors_for("Light")


class ReadinessApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"OS Readiness Checker {APP_VERSION}")
        self.geometry("820x620")
        self.minsize(700, 500)
        self.configure(bg=UI["background"])
        self.settings = load_settings()
        self.language_selection = self.settings.get("language") if self.settings.get("language") in LANGUAGES else "System"
        self.language = resolve_language(self.language_selection)
        self.title(f"{t('app.title', self.language)} {APP_VERSION}")
        self.theme_mode = load_theme_mode()
        UI.update(colors_for(self.theme_mode))
        self._logo_images = {}
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
        self.issues_only = tk.BooleanVar(value=False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()
        self.bind("<F5>", lambda _event: self.run_check())
        self.bind("<Control-r>", lambda _event: self.run_check())
        self.bind("<Control-s>", lambda _event: self.save_report())
        self.after_idle(self._restore_window)

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
            button = tk.Button(self.nav, text=t(nav_labels[page], self.language), command=lambda p=page: self._navigate(p), anchor="w", relief="flat", bd=0, padx=10, pady=7, bg=UI["surface"], fg=UI["text"], activebackground=UI["heading"], activeforeground=UI["text"], font=(font, 9), cursor="hand2", highlightthickness=2, highlightcolor=UI["accent"], highlightbackground=UI["surface"])
            button.pack(fill="x", pady=1)
            button.bind("<Return>", lambda _event, p=page: self._navigate(p))
            button.bind("<space>", lambda _event, p=page: self._navigate(p))
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
        self.help_button = ttk.Button(theme_box, text=t("action.help", self.language), command=self.show_help, style="Secondary.TButton")
        self.help_button.pack(side="left", padx=(8, 0))

        body = tk.Frame(workspace, bg=UI["background"], padx=28, pady=24)
        body._ui_role = "workspace"
        body.pack(fill="both", expand=True)
        controls = FluentCard(body, tokens=self.ui_tokens, padding=CARD_PADDING)
        controls.pack(fill="x", pady=(0, 14))
        self.os_label = tk.Label(controls, text=t("label.operating_system", self.language), bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold"))
        self.os_label.pack(side="left")
        self.choice = ttk.Combobox(controls, state="readonly", width=31, values=list(self.requirements), style="Fluent.TCombobox")
        last_os = self.settings.get("last_os")
        self.choice.current(list(self.requirements).index(last_os) if last_os in self.requirements else 0)
        self.choice.pack(side="left", padx=(CONTROL_GAP + 6, CONTROL_GAP + 4))
        self.choice.bind("<<ComboboxSelected>>", lambda _event: self.show_detail())
        self.check_button = ttk.Button(controls, text=t("action.scan", self.language), command=self.run_check, style="Accent.TButton")
        self.check_button.pack(side="right")
        self.overview_button = ttk.Button(controls, text=t("action.overview", self.language), command=self.show_overview, style="Secondary.TButton")
        self.overview_button.pack(side="right", padx=(0, 8))
        self.recommend_button = ttk.Button(controls, text=t("recommend.action", self.language), command=self.show_recommendations, style="Secondary.TButton", state="disabled")
        self.recommend_button.pack(side="right", padx=(0, 8))
        self.update_button = ttk.Button(controls, text=t("action.updates", self.language), command=self.check_requirements_updates, style="Secondary.TButton")
        self.update_button.pack(side="right", padx=(0, 8))
        self.update_status = tk.Label(controls, text=f"DB v{self.requirements_info.data_version} ({self.requirements_info.source})", bg=UI["surface"], fg=UI["muted"], font=(font, 9))
        self.update_status.pack(side="right", padx=(0, 10))
        profile_actions = tk.Frame(body, bg=UI["background"])
        self.profile_actions = profile_actions
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
        self.feedback = tk.Label(profile_actions, text="", bg=UI["background"], fg=UI["muted"], font=(font, 9))
        self.feedback.pack(side="right", padx=(0, 14))

        self.welcome_card = FluentCard(body, tokens=self.ui_tokens, padding=CARD_PADDING)
        welcome_body = self.welcome_card.content()
        welcome_head = tk.Frame(welcome_body, bg=UI["surface"])
        welcome_head.pack(fill="x")
        self.welcome_title = tk.Label(welcome_head, text=t("welcome.title", self.language), bg=UI["surface"], fg=UI["text"], font=(font, 12, "bold"))
        self.welcome_title.pack(side="left")
        self.welcome_dismiss = ttk.Button(welcome_head, text=t("action.dismiss", self.language), command=self._dismiss_welcome, style="Secondary.TButton")
        self.welcome_dismiss.pack(side="right")
        self.welcome_text = tk.Label(welcome_body, text=t("welcome.text", self.language), bg=UI["surface"], fg=UI["muted"], font=(font, 9), anchor="w", justify="left", wraplength=620)
        self.welcome_text.pack(fill="x", pady=(5, 7))
        self.welcome_hints = []
        for key in ("welcome.hint1", "welcome.hint2", "welcome.hint3", "welcome.hint4"):
            hint = tk.Label(welcome_body, text=t(key, self.language), bg=UI["surface"], fg=UI["muted"], font=(font, 9), anchor="w")
            hint.pack(fill="x", pady=1)
            self.welcome_hints.append(hint)
        welcome_actions = tk.Frame(welcome_body, bg=UI["surface"])
        welcome_actions.pack(fill="x", pady=(8, 0))
        ttk.Button(welcome_actions, text=t("action.scan", self.language), command=self.run_check, style="Accent.TButton").pack(side="left")
        ttk.Button(welcome_actions, text=t("action.import_profile", self.language), command=self.import_machine_profile, style="Secondary.TButton").pack(side="left", padx=(8, 0))
        if self.settings.get("onboarding_dismissed"):
            self.welcome_card.pack_forget()
        else:
            self.welcome_card.pack(fill="x", pady=(0, 14), before=summary_card if "summary_card" in locals() else None)

        summary_card = FluentCard(body, tokens=self.ui_tokens, padding=CARD_PADDING)
        self.summary_card = summary_card
        summary_card.pack(fill="x", pady=(0, 14))
        self.status_badge = tk.Label(summary_card, text="  READY  ", bg=UI.get("badge", UI["heading"]), fg=UI["muted"], font=(font, 9, "bold"), padx=8, pady=5)
        self.status_badge.pack(side="left", padx=(0, 12))
        self.summary = tk.Label(summary_card, text=t("empty.no_machine", self.language), bg=UI["surface"], fg=UI["text"], font=(font, 12, "bold"), wraplength=620, justify="left", anchor="w")
        self.summary.pack(side="left", anchor="w")

        content_area = tk.Frame(body, bg=UI["background"])
        content_area.pack(fill="both", expand=True, pady=(0, 12))

        self.analysis_frame = tk.Frame(content_area, bg=UI["background"])
        self.analysis_frame._ui_role = "workspace"
        self.analysis_frame.pack_forget()
        context_row = tk.Frame(self.analysis_frame, bg=UI["background"])
        context_row._ui_role = "workspace"
        context_row.pack(fill="x", pady=(0, 8))
        self.analysis_context = tk.Label(context_row, text="", bg=UI["background"], fg=UI["muted"], font=(font, 9), anchor="w")
        self.analysis_logo = tk.Label(context_row, bg=UI["background"], bd=0)
        self.analysis_logo.pack(side="left", padx=(0, 8))
        self.analysis_context.pack(side="left", fill="x", expand=True)
        self.issue_filter = ttk.Checkbutton(context_row, text=t("analysis.issues_only", self.language), variable=self.issues_only, command=self._refresh_detail_rows)
        self.issue_filter.pack(side="right")
        analysis_cards = tk.Frame(self.analysis_frame, bg=UI["background"])
        analysis_cards._ui_role = "workspace"
        analysis_cards.pack(fill="x", pady=(0, 8))
        self.analysis_cards = {}
        card_specs = (("compatibility", t("label.compatibility", self.language)), ("suitability", t("label.suitability", self.language)), ("lifecycle", t("label.lifecycle", self.language)), ("readiness", t("label.installation_readiness", self.language)))
        for index, (key, title) in enumerate(card_specs):
            card = FluentCard(analysis_cards, tokens=self.ui_tokens, padding=CARD_PADDING)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0 if index % 2 == 0 else 6, 6 if index % 2 == 0 else 0), pady=(0, 8))
            analysis_cards.grid_columnconfigure(index % 2, weight=1, uniform="analysis-card")
            tk.Label(card, text=title, bg=UI["surface"], fg=UI["muted"], font=(font, 9, "bold"), anchor="w").pack(fill="x")
            status = tk.Label(card, text="—", bg=UI["surface"], fg=UI["text"], font=(font, 12, "bold"), anchor="w")
            status.pack(fill="x", pady=(4, 2))
            explanation = tk.Label(card, text="", bg=UI["surface"], fg=UI["muted"], font=(font, 9), anchor="w", justify="left", wraplength=300)
            explanation.pack(fill="x")
            self.analysis_cards[key] = (card, status, explanation)
        analysis_cards.grid_rowconfigure(0, weight=1)
        analysis_cards.grid_rowconfigure(1, weight=1)

        columns = ("result", "detected", "required")
        self.overview_columns = ("#0",) + columns
        table_card = FluentCard(content_area, tokens=self.ui_tokens, padding=(7, 7))
        self.table_card = table_card
        table_card.pack(fill="both", expand=True)
        table_body = table_card.content()
        table_holder = tk.Frame(table_body, bg=UI["surface"])
        table_holder.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_holder, columns=columns, show="tree headings", style="Fluent.Treeview", selectmode="browse")
        self.table_scrollbar = ttk.Scrollbar(table_holder, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=self.table_scrollbar.set)
        self.table.heading("#0", text=t("label.check", self.language))
        self.table.heading("result", text=t("label.result", self.language))
        self.table.heading("detected", text=t("label.detected", self.language))
        self.table.heading("required", text=t("label.required", self.language))
        self._configure_table_columns()
        self.table.pack(side="left", fill="both", expand=True)
        self.table_scrollbar.pack(side="right", fill="y")
        self.table_empty = tk.Label(table_holder, text=t("empty.no_machine", self.language), bg=UI["surface"], fg=UI["muted"], font=(font, 10), justify="center", anchor="center")
        self.table_empty.place(relx=0.5, rely=0.5, anchor="center")
        self.table.tag_configure("pass", foreground=COLORS["pass"])
        self.table.tag_configure("fail", foreground=COLORS["fail"])
        self.table.tag_configure("unknown", foreground=COLORS["unknown"])
        self.table.bind("<<TreeviewSelect>>", self.show_selected_check)
        self.table.bind("<Double-1>", self._open_selected_os)
        self.table.bind("<Return>", self._open_selected_os)
        self.table.bind("<Configure>", self._resize_table_columns, add="+")

        footer = FluentCard(body, tokens=self.ui_tokens, padding=(18, 14))
        footer.pack(fill="x")
        self.details = tk.Label(footer, text=t("help.concepts_text", self.language), justify="left", anchor="w", bg=UI["surface"], fg=UI["muted"], wraplength=570, font=(font, 9))
        self.details.pack(side="left", fill="x", expand=True)
        self.source_button = ttk.Button(footer, text=t("action.source", self.language), command=self.open_source, style="Secondary.TButton")
        self.source_button.pack(side="right", padx=(8, 0))
        self.report_export_menu = tk.Menu(self, tearoff=False)
        self.report_export_menu.add_command(label=t("action.save_json", self.language), command=self.save_report)
        self.report_export_menu.add_command(label=t("action.save_html", self.language), command=self.save_html_report)
        self.report_export_button = ttk.Menubutton(footer, text=t("action.export_report", self.language), menu=self.report_export_menu, style="Secondary.TButton")
        self.report_export_button.pack(side="right")
        self.copy_button = ttk.Button(footer, text=t("action.copy_results", self.language), command=self.copy_results, style="Secondary.TButton")
        self.copy_button.pack(side="right", padx=(8, 0))
        self.compare_button = ttk.Button(footer, text=t("action.compare", self.language), command=self.show_compare, style="Secondary.TButton", state="disabled")
        self.compare_button.pack(side="right", padx=(8, 0))
        self.plan_button = ttk.Button(footer, text=t("action.upgrade_plan", self.language), command=self.show_upgrade_plan, style="Secondary.TButton", state="disabled")
        self.plan_button.pack(side="right", padx=(8, 0))
        self._apply_theme(self)
        self._set_active_nav("overview")
        self._sync_overview_actions()
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
            self.show_settings()
        elif page == "about":
            self.show_about()

    def _set_feedback(self, key: str) -> None:
        self.feedback.config(text=t(key, self.language))
        self.after(4500, lambda: self.feedback.config(text="") if self.feedback.winfo_exists() else None)

    def _sync_overview_actions(self) -> None:
        welcome_visible = bool(self.welcome_card.winfo_manager())
        has_machine = bool(self.machine)
        if welcome_visible:
            self.check_button.pack_forget()
        elif not self.check_button.winfo_manager():
            self.check_button.pack(side="right")
        self.check_button.configure(style="Secondary.TButton" if has_machine else "Accent.TButton")
        self.recommend_button.configure(state="normal" if has_machine else "disabled")
        self.export_button.configure(state="normal" if has_machine else "disabled")
        self.report_export_button.configure(state="normal" if has_machine else "disabled")
        self.machine_compare_button.configure(state="normal" if has_machine else "disabled")
        self.compare_button.configure(state="normal" if has_machine else "disabled")
        self.plan_button.configure(state="normal" if has_machine else "disabled")
        if welcome_visible and not has_machine:
            self.profile_actions.pack_forget()
        elif not self.profile_actions.winfo_manager():
            self.profile_actions.pack(fill="x", pady=(0, 10), before=self.welcome_card if welcome_visible else self.summary_card)
    def _dismiss_welcome(self) -> None:
        self.settings["onboarding_dismissed"] = True
        save_settings(self.settings)
        self.welcome_card.pack_forget()
        self._sync_overview_actions()

    def _configure_table_columns(self, *, overview: bool = True) -> None:
        """Keep the native table readable while allowing the workspace to breathe."""
        if overview:
            specs = (("#0", 250, 170, True, "w"), ("result", 112, 96, False, "center"), ("detected", 150, 120, True, "center"), ("required", 150, 120, True, "center"))
        else:
            specs = (("#0", 205, 150, True, "w"), ("result", 100, 88, False, "center"), ("detected", 205, 130, True, "w"), ("required", 205, 130, True, "w"))
        for column, width, minimum, stretch, anchor in specs:
            self.table.column(column, width=width, minwidth=minimum, stretch=stretch, anchor=anchor)

    def _resize_table_columns(self, _event=None) -> None:
        """Give the name column priority at normal widths without hardcoding a layout."""
        if not hasattr(self, "table") or not self.table.winfo_exists() or getattr(self, "active_page", "overview") != "overview":
            return
        width = self.table.winfo_width()
        if width <= 0:
            return
        result = 112
        remaining = max(250, width - result - 8)
        name = min(310, max(170, int(remaining * 0.36)))
        each = max(120, (remaining - name) // 2)
        self.table.column("#0", width=name)
        self.table.column("result", width=result)
        self.table.column("detected", width=each)
        self.table.column("required", width=max(120, remaining - name - each))

    def _set_table_empty(self, visible: bool) -> None:
        if hasattr(self, "table_empty"):
            if visible:
                self.table_empty.place(relx=0.5, rely=0.5, anchor="center")
            else:
                self.table_empty.place_forget()
    def _show_welcome(self) -> None:
        self.settings["onboarding_dismissed"] = False
        save_settings(self.settings)
        self.welcome_card.pack(fill="x", pady=(0, 14), before=self.summary_card)
        self._sync_overview_actions()
    def _unavailable(self, message_key: str, action: str | None = None) -> None:
        self._set_active_nav(getattr(self, "active_page", "overview"))
        message = t(message_key, self.language)
        if action:
            message += f"\n\n{t('label.next_step', self.language)}: {action}"
        messagebox.showinfo(t("label.next_step", self.language), message)

    def show_settings(self) -> None:
        window = tk.Toplevel(self)
        window.title(t("settings.title", self.language))
        self._size_dialog(window, 520, 300, 440, 260)
        window.configure(bg=UI["background"])
        card = self._page_card(window)
        body = card.content()
        tk.Label(body, text=t("settings.title", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 16, "bold")).pack(anchor="w")
        tk.Label(body, text=t("settings.appearance", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 10, "bold")).pack(anchor="w", pady=(16, 3))
        tk.Label(body, text=f"{t('label.theme', self.language)}: {t(f'theme.{self.theme_mode.lower()}', self.language)}", bg=UI["surface"], fg=UI["muted"], anchor="w").pack(fill="x")
        tk.Label(body, text=t("settings.data", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 10, "bold")).pack(anchor="w", pady=(16, 3))
        tk.Label(body, text=f"{t('label.external_source', self.language)}: {self.requirements_info.source}; v{self.requirements_info.data_version}", bg=UI["surface"], fg=UI["muted"], anchor="w", wraplength=440).pack(fill="x")
        ttk.Button(body, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(anchor="e", pady=(18, 0))
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def show_help(self) -> None:
        window = tk.Toplevel(self)
        window.title(t("help.title", self.language))
        self._size_dialog(window, 700, 650, 540, 440)
        window.configure(bg=UI["background"])
        card = self._page_card(window)
        body = card.content()
        tk.Label(body, text=t("help.title", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 16, "bold")).pack(anchor="w")
        tk.Label(body, text=t("help.intro", self.language), bg=UI["surface"], fg=UI["muted"], wraplength=620, justify="left", anchor="w").pack(fill="x", pady=(4, 12))
        for title_key, text_key in (("help.workflow", "help.workflow_text"), ("help.concepts", "help.concepts_text"), ("help.review", "help.review_text"), ("help.planner", "help.planner_text"), ("help.recommendations", "help.recommendations_text"), ("help.privacy", "help.privacy_text"), ("help.data", "help.data_text")):
            tk.Label(body, text=t(title_key, self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 10, "bold"), anchor="w").pack(fill="x", pady=(5, 1))
            tk.Label(body, text=t(text_key, self.language), bg=UI["surface"], fg=UI["muted"], font=(self.font, 9), wraplength=620, justify="left", anchor="w").pack(fill="x")
        ttk.Button(body, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(anchor="e", pady=(14, 0))
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

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

    def _size_dialog(self, window: tk.Toplevel, width: int, height: int, min_width: int = 560, min_height: int = 420) -> None:
        """Keep auxiliary workspaces usable on small or scaled displays."""
        try:
            screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
            width = max(min_width, min(width, max(min_width, screen_w - 48)))
            height = max(min_height, min(height, max(min_height, screen_h - 96)))
        except tk.TclError:
            pass
        window.geometry(f"{width}x{height}")
        window.minsize(min_width, min_height)
        window.transient(self)

    def _page_card(self, window: tk.Toplevel, padding=DIALOG_PADDING) -> FluentCard:
        """Create the shared surface used by secondary workspace dialogs."""
        card = FluentCard(window, tokens=self.ui_tokens, padding=padding)
        card.pack(fill="both", expand=True, padx=PAGE_PADDING[0], pady=PAGE_PADDING[1])
        return card

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
        self.summary.config(text=t("overview.scanning", self.language), fg=UI["muted"])
        screen = (self.winfo_screenwidth(), self.winfo_screenheight())
        threading.Thread(target=self._scan, args=(screen,), daemon=True).start()

    def _logo_for(self, name: str, profile=None):
        logo = load_logo(self, name, profile)
        if logo is not None:
            self._logo_images[name] = logo
        return logo

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
        self.help_button.config(text=t("action.help", self.language))
        self.check_button.config(text=t("action.scan", self.language))
        self.overview_button.config(text=t("action.overview", self.language))
        self.recommend_button.config(text=t("recommend.action", self.language))
        self.update_button.config(text=t("action.updates", self.language))
        self.import_button.config(text=t("action.import_profile", self.language))
        self.export_button.config(text=t("action.export_profile", self.language))
        self.report_export_button.config(text=t("action.export_report", self.language))
        self.report_export_menu.delete(0, "end")
        self.report_export_menu.add_command(label=t("action.save_json", self.language), command=self.save_report)
        self.report_export_menu.add_command(label=t("action.save_html", self.language), command=self.save_html_report)
        self.machine_compare_button.config(text=t("action.compare_machines", self.language))
        self.source_button.config(text=t("action.source", self.language))
        self.copy_button.config(text=t("action.copy_results", self.language))
        self.compare_button.config(text=t("action.compare", self.language))
        self.plan_button.config(text=t("action.upgrade_plan", self.language))
        self.source_status.config(text=f"{t('label.machine_source', self.language)}: {t('profile.source_imported' if self.machine_source == 'Imported profile' else 'profile.source_local', self.language)}")
        self.subtitle_label.config(text=t("app.subtitle", self.language))
        self.theme_label.config(text=t("label.theme", self.language))
        self.language_label.config(text=t("label.language", self.language))
        self.os_label.config(text=t("label.operating_system", self.language))
        self.table_empty.config(text=t("empty.no_machine", self.language))
        self.welcome_title.config(text=t("welcome.title", self.language))
        self.welcome_text.config(text=t("welcome.text", self.language))
        self.welcome_dismiss.config(text=t("action.dismiss", self.language))
        for hint, key in zip(self.welcome_hints, ("welcome.hint1", "welcome.hint2", "welcome.hint3", "welcome.hint4")):
            hint.config(text=t(key, self.language))
        nav_labels = {"overview": "nav.overview", "analysis": "nav.analysis", "compare_os": "nav.compare_os", "compare_machines": "nav.compare_machines", "upgrade": "nav.upgrade", "recommendations": "nav.recommendations", "reports": "nav.reports", "settings": "nav.settings", "about": "nav.about"}
        for page, button in self.nav_buttons.items():
            button.config(text=t(nav_labels[page], self.language))
        for column, key in (("#0", "label.check"), ("result", "label.result"), ("detected", "label.detected"), ("required", "label.required")):
            self.table.heading(column, text=t(key, self.language))
        if self.machine and self.choice.get() in self.all_results:
            self.show_detail()

    def show_about(self) -> None:
        window = tk.Toplevel(self)
        window.title(t("nav.about", self.language))
        self._size_dialog(window, 430, 330, 380, 280)
        window.resizable(False, False)
        window.configure(bg=UI["background"])
        card = self._page_card(window, padding=(24, 22))
        tk.Label(card, text=t("app.title", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 17, "bold")).pack(anchor="w")
        tk.Label(card, text=f"Version {APP_VERSION}\n{t('app.subtitle', self.language)}\n\nRequirements database: v{self.requirements_info.data_version} ({self.requirements_info.source})\nRuns on Windows and Linux. License: MIT\n\n{t('about.privacy', self.language)}", justify="left", anchor="w", wraplength=370, bg=UI["surface"], fg=UI["muted"], font=(self.font, 9)).pack(fill="x", pady=(10, 16))
        actions = tk.Frame(card, bg=UI["surface"])
        actions.pack(fill="x")
        ttk.Button(actions, text=t("action.open_github", self.language), command=lambda: webbrowser.open("https://github.com/sage-yeti/os-readiness-checker"), style="Secondary.TButton").pack(side="left")
        ttk.Button(actions, text=t("action.updates", self.language), command=self.check_requirements_updates, style="Secondary.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(actions, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(side="right")
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def show_recommendations(self) -> None:
        if not self.machine or not self.all_results:
            self._unavailable("empty.no_recommendations", t("action.scan", self.language))
            return
        window = tk.Toplevel(self)
        window.title(t("recommend.title", self.language))
        self._size_dialog(window, 700, 680, 560, 480)
        window.configure(bg=UI["background"])
        card = self._page_card(window)
        body = card.content()
        tk.Label(body, text=t("recommend.step_preferences", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 11, "bold")).pack(anchor="w")
        tk.Label(body, text=t("recommend.prompt", self.language), bg=UI["surface"], fg=UI["muted"], font=(self.font, 9), wraplength=620, justify="left").pack(anchor="w", pady=(3, 0))
        vars_by_key = {key: tk.IntVar(value=int(self.settings.get("preferences", {}).get(key, 0))) for key in PREFERENCES}
        choices = FluentCard(body, tokens=self.ui_tokens, padding=CARD_PADDING)
        choices.pack(fill="x", pady=(12, 8))
        choices_body = choices.content()
        for key in PREFERENCES:
            row = tk.Frame(choices_body, bg=UI["surface"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=preference_label(key, self.language), bg=UI["surface"], fg=UI["text"], width=34, anchor="w", font=(self.font, 9)).pack(side="left")
            for value, label in ((0, "—"), (1, "Somewhat"), (2, "Important")):
                tk.Radiobutton(row, text=label, value=value, variable=vars_by_key[key], bg=UI["surface"], fg=UI["text"], activebackground=UI["surface"], selectcolor=UI["background"], font=(self.font, 8)).pack(side="left")
        results_card = FluentCard(body, tokens=self.ui_tokens, padding=CARD_PADDING)
        results_card.pack(fill="both", expand=True, pady=(8, 8))
        results_body = results_card.content()
        tk.Label(results_body, text=t("recommend.step_results", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 11, "bold")).pack(anchor="w")
        output = tk.Label(results_body, text=t("recommend.disclaimer", self.language), bg=UI["surface"], fg=UI["muted"], justify="left", anchor="nw", wraplength=620, font=(self.font, 9))
        output.pack(fill="x", pady=(6, 4))
        result_cards = tk.Frame(results_body, bg=UI["surface"])
        result_cards.pack(fill="both", expand=True)
        def analyze() -> None:
            preferences = {key: var.get() for key, var in vars_by_key.items()}
            self.settings["preferences"] = preferences
            save_settings(self.settings)
            suits = {name: self.suitability_by_os.get(name) for name in self.requirements}
            readiness = {name: evaluate_installation_readiness(self.machine, self.requirements[name], self.all_results[name]) for name in self.requirements}
            ranked = recommend(self.requirements, self.all_results, suits, readiness, preferences)
            primary = primary_recommendations(ranked)[:5]
            for child in result_cards.winfo_children():
                child.destroy()
            lines = [t("recommend.disclaimer", self.language), ""]
            if not primary:
                lines.append(t("empty.no_candidate", self.language))
            for item in primary:
                rank = primary.index(item) + 1
                result = FluentCard(result_cards, tokens=self.ui_tokens, padding=CARD_PADDING)
                result.pack(fill="x", pady=4)
                result_body = result.content()
                identity = tk.Frame(result_body, bg=UI["surface"])
                identity.pack(fill="x")
                logo = self._logo_for(item["name"], self.requirements.get(item["name"], {}))
                if logo is not None:
                    tk.Label(identity, image=logo, bg=UI["surface"], bd=0).pack(side="left", padx=(0, 8))
                tk.Label(identity, text=f"#{rank}  {item['name']}", bg=UI["surface"], fg=UI["text"], font=(self.font, 10, "bold")).pack(side="left")
                tk.Label(result_body, text=f"{t('recommend.preference_match', self.language)}: {recommendation_match_label(item['preference_match_category'], self.language)} ({item['preference_score']}/100)", bg=UI["surface"], fg=UI["accent"], font=(self.font, 9, "bold")).pack(anchor="w")
                strength_keys = item.get("strength_keys", item["strengths"])
                tradeoff_keys = item.get("tradeoff_keys", item["tradeoffs"])
                strengths = ", ".join(preference_label(key, self.language) for key in strength_keys) or "—"
                tradeoffs = ", ".join(preference_label(key, self.language) for key in tradeoff_keys) or "—"
                tk.Label(result_body, text=f"{t('recommend.strengths', self.language)}: {strengths}\n{t('recommend.tradeoffs', self.language)}: {tradeoffs}", bg=UI["surface"], fg=UI["muted"], justify="left", anchor="w", wraplength=590, font=(self.font, 9)).pack(anchor="w", pady=(4, 0))
                lines.append(f"{item['name']} — {recommendation_match_label(item['preference_match_category'], self.language)} ({item['preference_score']}/100)")
                if item["strengths"]:
                    lines.append("  " + t("recommend.strengths", self.language) + ": " + ", ".join(preference_label(key, self.language) for key in item.get("strength_keys", item["strengths"])))
                if item["tradeoffs"]:
                    lines.append("  " + t("recommend.tradeoffs", self.language) + ": " + ", ".join(preference_label(key, self.language) for key in item.get("tradeoff_keys", item["tradeoffs"])))
            output.config(text="\n".join(lines))
        ttk.Button(body, text=t("recommend.analyze", self.language), command=analyze, style="Accent.TButton").pack(anchor="e")
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
        self.summary.config(text=t("error.scan", self.language), fg=UI["text"])
        self.status_badge.config(text="  REVIEW  ", bg=COLORS["review"], fg="white")
        self.details.config(text=f"{t('error.scan', self.language)}\n\n{t('error.profile_details', self.language)}\nTechnical details: {error}")

    def _clear_table(self) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

    def _show_detail(self, results) -> None:
        self._clear_table()
        visible = [item for item in results if not self.issues_only.get() or item.status != "pass"]
        for item in visible:
            self.table.insert("", "end", text=item.name, values=(ICONS[item.status] + " " + status_label(item.status, self.language), item.detected, item.required), tags=(item.status,))
        self.table.configure(height=min(max(len(visible), 1), 8))

    def _refresh_detail_rows(self) -> None:
        if self.machine and self.choice.get() in self.all_results:
            self._show_detail(self.all_results[self.choice.get()])

    def _status_presentation(self, status: str) -> tuple[str, str]:
        normalized = status.lower().replace(" ", "_")
        if normalized in {"pass", "ready", "supported", "excellent_fit", "good_fit", "meets_minimum", "rolling", "current"}:
            return "✓", COLORS["pass"]
        if normalized in {"fail", "not_ready", "eol", "not_compatible"}:
            return "×", COLORS["fail"]
        return "!", COLORS["review"]

    def _update_analysis_cards(self, name: str, status: str, suitability: dict, lifecycle: dict, readiness: dict, score: int) -> None:
        lifecycle_status_value = lifecycle.get("support_status", "unknown")
        cards = {
            "compatibility": (status, f"{score}/100 — {t('analysis.published_requirements', self.language)}"),
            "suitability": (suitability.get("category", "Unknown"), suitability_explanation(suitability.get("category", "Unknown"), suitability.get("explanation", t("analysis.headroom_unknown", self.language)), self.language)),
            "lifecycle": (lifecycle_status_value, f"Release {lifecycle.get('release', 'Unknown')}"),
            "readiness": (readiness.get("status", "review"), readiness_explanation(readiness.get("status", "review"), self.language)),
        }
        for key, (value, explanation) in cards.items():
            _icon, color = self._status_presentation(str(value))
            _card, status_label_widget, explanation_widget = self.analysis_cards[key]
            if key == "compatibility":
                display = f"{_icon} {status_label(value, self.language).upper()}"
            elif key == "lifecycle":
                display = f"{_icon} {status_label(value, self.language).upper()}"
            elif key == "readiness":
                display = f"{_icon} {status_label(value, self.language).upper()}"
            else:
                display = f"{_icon} {t('status.' + str(value).lower().replace(' ', '_'), self.language).upper()}"
            status_label_widget.config(text=display, fg=color)
            explanation_widget.config(text=explanation)

    def _open_selected_os(self, _event=None) -> None:
        if not self.table.selection():
            return
        name = self.table.item(self.table.selection()[0], "text")
        if name in self.requirements:
            self.choice.set(name)
            self.show_detail()

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
            text += f"\n{t('label.next_step', self.language)}: {info['remediation']}"
        self.details.config(text=text)

    def _show_overview(self, machine, all_results, ranked) -> None:
        self.machine, self.all_results, self.ranked_results = machine, all_results, ranked
        self._set_active_nav("overview")
        self.analysis_frame.pack_forget()
        source_key = "profile.source_imported" if self.machine_source == "Imported profile" else "profile.source_local"
        self.source_status.config(text=f"{t('label.machine_source', self.language)}: {t(source_key, self.language)}")
        if self.choice.get() not in all_results and all_results:
            self.choice.current(0)
        self.results = all_results.get(self.choice.get(), [])
        self._clear_table()
        self._set_table_empty(not bool(ranked))
        self.table.heading("#0", text=t("label.operating_system", self.language))
        self.table.heading("result", text=t("label.status", self.language))
        self.table.heading("detected", text=t("label.compatibility_short", self.language))
        self.table.heading("required", text=t("label.suitability_short", self.language))
        self._configure_table_columns()
        for item in ranked:
            status = item["status"]
            profile = self.requirements.get(item["name"], {})
            logo = self._logo_for(item["name"], profile)
            self.table.insert("", "end", image=logo, text=item["name"], values=(ICONS.get(status, "") + " " + status_label(status, self.language), f'{item["score"]}/100', t("status." + item["suitability"]["category"].lower().replace(" ", "_"), self.language)), tags=(status,))
        self.summary.config(text=t("overview.compared", self.language, count=len(ranked)), fg=UI["text"])
        self.status_badge.config(text=f"  {t('status.overview', self.language).upper()}  ", bg=UI["accent"], fg="white")
        source_note = ""
        if self.machine_source == "Imported profile":
            captured = self.profile_metadata.get("created_at", "")
            source_note = t("overview.imported_note", self.language, captured=captured)
        self.details.config(text=t("overview.requirements_note", self.language, version=self.requirements_info.data_version, source=self.requirements_info.source, source_note=source_note))
        self.check_button.config(state="normal")
        self.scan_in_progress = False
        self.compare_button.config(state="normal")
        self.plan_button.config(state="normal")
        self.machine_compare_button.config(state="normal")
        self._sync_overview_actions()
    def show_overview(self) -> None:
        if self.machine and self.ranked_results:
            self._show_overview(self.machine, self.all_results, self.ranked_results)
            return
        self._set_active_nav("overview")
        self.analysis_frame.pack_forget()
        self._set_table_empty(True)
        self.summary.config(text=t("empty.no_machine", self.language), fg=UI["text"])
        self.status_badge.config(text="  READY  ", bg=UI.get("badge", UI["heading"]), fg=UI["muted"])
        self.details.config(text=t("help.concepts_text", self.language))
        self._sync_overview_actions()
    def show_detail(self) -> None:
        if not self.machine or self.choice.get() not in self.all_results:
            self._unavailable("empty.no_analysis", t("action.scan", self.language))
            return
        name = self.choice.get()
        self._set_active_nav("analysis")
        self.analysis_logo.configure(image=self._logo_for(name, self.requirements[name]))
        self.table_card.pack_configure(fill="x", expand=False)
        self.analysis_frame.pack(fill="x", pady=(8, 8), after=self.table_card)
        self.settings["last_os"] = name
        save_settings(self.settings)
        results = self.all_results[name]
        self.results = results
        self._show_detail(results)
        self.table.heading("#0", text=t("label.check", self.language))
        self.table.heading("result", text=t("label.result", self.language))
        self.table.heading("detected", text=t("label.detected", self.language))
        self.table.heading("required", text=t("label.required", self.language))
        self._configure_table_columns(overview=False)
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
        readiness_line = f"{t('label.installation_readiness', self.language)}: {status_label(readiness['status'], self.language)} — {readiness_explanation(readiness['status'], self.language)}"
        readiness_items = [f"  {status_label(item['status'], self.language).upper()}: {item['name']} — {item['detected']} / {item['required']}" for item in readiness["checks"]]
        machine_details = [
            f"Architecture: {architecture_label(self.machine.architecture)}",
            f"{t('machine.processor', self.language)}: {self.machine.cpu_name}",
            f"{t('machine.graphics', self.language)}: {gpu}",
            f"{t('machine.system_disk', self.language)}: {self.machine.system_disk or 'Unknown'} ({self.machine.storage_partition_style or 'Unknown'} / {self.machine.storage_filesystem or 'Unknown'})",
            f"{t('machine.virtualization', self.language)}: {self.machine.virtualization or 'Unknown'}",
        ]
        suitability_label = t("status." + suitability["category"].lower().replace(" ", "_"), self.language)
        self.analysis_context.config(text=f"{name} • {lifecycle['release']} • {t('label.machine_source', self.language)}: {t('profile.source_imported' if self.machine_source == 'Imported profile' else 'profile.source_local', self.language)}")
        self._update_analysis_cards(name, status, suitability, lifecycle, readiness, score)
        context_note = ""
        if self.machine_source == "Imported profile":
            context_note = f"{t('analysis.imported_context', self.language)} ({self.profile_metadata.get('created_at', 'unknown')}). {t('analysis.current_database', self.language)}\n"
        lifecycle_warning = ""
        if lifecycle["support_status"] in {"nearing_eol", "eol"}:
            lifecycle_warning = f"\n{t('analysis.release_notice', self.language)}: {lifecycle_line}\n"
        self.details.config(text=f"{context_note}Requirements database v{self.requirements_info.data_version} ({self.requirements_info.source})\n{lifecycle_warning}{readiness_line}\n" + "\n".join(readiness_items + [f"{t('label.suitability', self.language)}: {suitability_label} — {suitability_explanation(suitability['category'], suitability['explanation'], self.language)}"] + machine_details + ["• " + note for note in notes]))

    def show_compare(self) -> None:
        if not self.machine or not self.all_results:
            self._unavailable("empty.no_machine", t("action.scan", self.language))
            return
        window = tk.Toplevel(self)
        window.title(t("comparison.title", self.language))
        self._size_dialog(window, 760, 520, 560, 400)
        window.configure(bg=UI["background"])
        font = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
        names = list(self.requirements)
        controls = FluentCard(window, tokens=self.ui_tokens, padding=CARD_PADDING)
        controls.pack(fill="x", padx=PAGE_PADDING[0], pady=PAGE_PADDING[1])
        tk.Label(controls, text=t("comparison.label", self.language), bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold")).pack(side="left")
        left = ttk.Combobox(controls, state="readonly", values=names, width=23, style="Fluent.TCombobox")
        right = ttk.Combobox(controls, state="readonly", values=names, width=23, style="Fluent.TCombobox")
        left.current(0)
        right.current(1 if len(names) > 1 else 0)
        left.pack(side="left", padx=(12, 8))
        right.pack(side="left")
        card = FluentCard(window, tokens=self.ui_tokens, padding=(1, 1))
        card.pack(fill="both", expand=True, padx=PAGE_PADDING[0], pady=(0, PAGE_PADDING[1]))
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
            self._unavailable("empty.no_plan", t("action.scan", self.language))
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
        self._size_dialog(window, 760, 680, 600, 480)
        window.configure(bg=UI["background"])
        card = self._page_card(window)
        body = card.content()
        identity = tk.Frame(body, bg=UI["surface"])
        identity.pack(fill="x")
        logo = self._logo_for(name, self.requirements[name])
        if logo is not None:
            tk.Label(identity, image=logo, bg=UI["surface"], bd=0).pack(side="left", padx=(0, 10))
        tk.Label(identity, text=f"{name} — {t('action.upgrade_plan', self.language)}", bg=UI["surface"], fg=UI["text"], font=(self.font, 16, "bold")).pack(side="left")
        tk.Label(body, text=plan["overall_summary"], bg=UI["surface"], fg=UI["muted"], font=(self.font, 10), wraplength=680, justify="left").pack(anchor="w", pady=(6, 12))
        if not any(plan[key] for key in ("required_hardware_changes", "required_configuration_changes", "storage_actions", "unresolved_items")):
            positive = t("planner.no_required", self.language)
            if plan.get("optional_improvements"):
                positive += " " + t("planner.optional_only", self.language)
            tk.Label(body, text=positive, bg=UI["surface"], fg=COLORS["pass"], font=(self.font, 10, "bold"), wraplength=680, justify="left").pack(anchor="w", pady=(0, 8))
        tk.Label(body, text=t("help.planner_text", self.language), bg=UI["surface"], fg=UI["muted"], font=(self.font, 9), wraplength=680, justify="left").pack(anchor="w", pady=(0, 8))
        sections = tk.Frame(body, bg=UI["surface"])
        sections.pack(fill="both", expand=True)
        section_names = {"required_hardware_changes": "planner.hardware", "required_configuration_changes": "planner.configuration", "storage_actions": "planner.storage", "unresolved_items": "planner.unresolved", "optional_improvements": "planner.optional", "already_satisfied": "planner.satisfied"}
        for key, label_key in section_names.items():
            items = plan[key]
            if not items:
                continue
            section_card = FluentCard(sections, tokens=self.ui_tokens, padding=CARD_PADDING)
            section_card.pack(fill="x", pady=4)
            section_body = section_card.content()
            tk.Label(section_body, text=t(label_key, self.language), bg=UI["surface"], fg=UI["accent"] if key.startswith("required") or key == "storage_actions" else UI["text"], font=(self.font, 10, "bold")).pack(anchor="w")
            for item in items:
                if key == "already_satisfied":
                    line = f"{item['check']}\n  {item['current']} / {item['target']}"
                else:
                    gap = f"; {t('planner.gap', self.language)} {item['gap']}" if item.get("gap") else ""
                    line = f"{item['check']}\n  {item['current']} / {item['target']}{gap}\n  {item['explanation']}"
                tk.Label(section_body, text="• " + line, bg=UI["surface"], fg=UI["muted"], justify="left", anchor="w", wraplength=650, font=(self.font, 9)).pack(anchor="w", pady=(5, 0))
        if plan["lifecycle_warning"]:
            warning = FluentCard(sections, tokens=self.ui_tokens, padding=CARD_PADDING)
            warning.pack(fill="x", pady=4)
            warning_body = warning.content()
            tk.Label(warning_body, text=t("planner.lifecycle", self.language), bg=UI["surface"], fg=COLORS["review"], font=(self.font, 10, "bold")).pack(anchor="w")
            tk.Label(warning_body, text=plan["lifecycle_warning"], bg=UI["surface"], fg=UI["muted"], wraplength=650, justify="left").pack(anchor="w", pady=(4, 0))
        ttk.Button(body, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(anchor="e", pady=(12, 0))
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def show_machine_compare(self) -> None:
        if not self.machine:
            self._unavailable("empty.no_compare", t("action.scan", self.language))
            return
        window = tk.Toplevel(self)
        window.title(t("comparison.title", self.language))
        self._size_dialog(window, 900, 650, 640, 480)
        window.configure(bg=UI["background"])
        sources = [self.machine, None]
        labels = [t("comparison.this_computer", self.language), t("comparison.choose_profile", self.language)]
        machine_names = (t("comparison.machine_a", self.language), t("comparison.machine_b", self.language))
        metadata = [{}, {}]
        font = self.font
        source_row = tk.Frame(window, bg=UI["background"])
        source_row.pack(fill="x", padx=PAGE_PADDING[0], pady=(PAGE_PADDING[1], 10))
        source_cards = []
        for index, title in enumerate(machine_names):
            source_card = FluentCard(source_row, tokens=self.ui_tokens, padding=(12, 10))
            source_card.pack(side="left", fill="both", expand=True, padx=(0, 8) if index == 0 else (8, 0))
            source_body = source_card.content()
            tk.Label(source_body, text=title, bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold")).pack(anchor="w")
            source_label = tk.Label(source_body, text=labels[index], bg=UI["surface"], fg=UI["muted"], anchor="w", wraplength=360, font=(font, 9))
            source_label.pack(anchor="w", pady=(4, 0))
            source_cards.append(source_label)
        controls = FluentCard(window, tokens=self.ui_tokens, padding=CARD_PADDING)
        controls.pack(fill="x", padx=PAGE_PADDING[0], pady=(0, 12))
        controls_body = controls.content()
        tk.Label(controls_body, text=t("label.operating_system", self.language), bg=UI["surface"], fg=UI["muted"], font=(font, 9)).pack(side="left")
        target = ttk.Combobox(controls_body, state="readonly", values=list(self.requirements), width=25, style="Fluent.TCombobox")
        target.current(0)
        target.pack(side="left", padx=(8, 14))
        labels_vars = [tk.StringVar(value=labels[0]), tk.StringVar(value=labels[1])]
        for index in range(2):
            tk.Label(controls_body, text=f"{t('comparison.machine', self.language)} {'A' if index == 0 else 'B'}", bg=UI["surface"], fg=UI["text"], font=(font, 9, "bold")).pack(side="left", padx=(0 if index == 0 else 12, 4))
            tk.Label(controls_body, textvariable=labels_vars[index], bg=UI["surface"], fg=UI["muted"], width=18, anchor="w", font=(font, 9)).pack(side="left")

        card = FluentCard(window, tokens=self.ui_tokens, padding=(1, 1))
        card.pack(fill="both", expand=True, padx=PAGE_PADDING[0], pady=(0, 12))
        table = ttk.Treeview(card, columns=("a", "b", "difference"), show="tree headings", style="Fluent.Treeview")
        table.heading("#0", text=t("comparison.attribute", self.language)); table.heading("a", text=machine_names[0]); table.heading("b", text=machine_names[1]); table.heading("difference", text=t("comparison.difference", self.language))
        table.column("#0", width=190); table.column("a", width=210); table.column("b", width=210); table.column("difference", width=130)
        table.pack(fill="both", expand=True)
        summary_card = FluentCard(window, tokens=self.ui_tokens, padding=CARD_PADDING)
        summary_card.pack(fill="x", padx=PAGE_PADDING[0], pady=(0, 10))
        summary = tk.Label(summary_card.content(), text="", justify="left", anchor="w", bg=UI["surface"], fg=UI["text"], wraplength=820, font=(font, 9))
        summary.pack(fill="x")
        result_holder = {"value": None}

        def choose_profile(index: int) -> None:
            path = filedialog.askopenfilename(filetypes=[("Machine profile", "*.osrprofile"), ("JSON", "*.json")])
            if not path:
                return
            try:
                machine, meta = import_profile(Path(path))
            except ValueError as exc:
                self._show_profile_error(exc, parent=window)
                return
            sources[index], metadata[index] = machine, meta
            captured = meta.get("created_at") or "unknown"
            labels[index] = f"{t('comparison.imported_profile', self.language)} ({Path(path).name}; {captured})"
            labels_vars[index].set(labels[index])
            source_cards[index].config(text=labels[index])
            refresh()

        def use_current(index: int) -> None:
            sources[index], metadata[index] = self.machine, {}
            labels[index] = t("comparison.this_computer", self.language)
            labels_vars[index].set(labels[index])
            source_cards[index].config(text=labels[index])
            refresh()

        for index in range(2):
            ttk.Button(controls_body, text=t("comparison.import", self.language), command=lambda i=index: choose_profile(i), style="Secondary.TButton").pack(side="left", padx=(4, 0))
            ttk.Button(controls_body, text=t("comparison.use_current", self.language), command=lambda i=index: use_current(i), style="Secondary.TButton").pack(side="left", padx=(4, 0))

        def refresh(*_args) -> None:
            if sources[0] is None or sources[1] is None:
                table.delete(*table.get_children())
                missing = t("comparison.machine_a", self.language) if sources[0] is None else t("comparison.machine_b", self.language)
                summary.config(text=f"{missing}: {t('empty.no_compare', self.language)}")
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
        actions.pack(fill="x", padx=PAGE_PADDING[0], pady=(0, PAGE_PADDING[1] - 2))
        def save_comparison_html() -> None:
            if not result_holder["value"]: return
            path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML report", "*.html")], initialfile="machine-comparison.html")
            if path:
                Path(path).write_text(html_comparison_report(result_holder["value"]), encoding="utf-8")
                self._set_feedback("feedback.saved")
        def copy_comparison() -> None:
            if not result_holder["value"]: return
            self.clipboard_clear(); self.clipboard_append(plain_text_comparison(result_holder["value"])); self.update()
            self._set_feedback("feedback.copied")
        ttk.Button(actions, text=t("comparison.save_html", self.language), command=save_comparison_html, style="Secondary.TButton").pack(side="left")
        ttk.Button(actions, text=t("comparison.copy", self.language), command=copy_comparison, style="Secondary.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(actions, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(side="right")
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def open_source(self) -> None:
        webbrowser.open(self.requirements[self.choice.get()]["source"])

    def save_report(self) -> None:
        if not self.machine:
            self._unavailable("empty.no_report", t("action.scan", self.language))
            return
        target = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON report", "*.json")], initialfile="os-readiness-report.json")
        if target:
            report = as_report(self.machine, self.requirements[self.choice.get()])
            report["target_os"] = self.choice.get()
            report["machine_source"] = self.machine_source
            if self.profile_metadata:
                report["profile_metadata"] = self.profile_metadata
            Path(target).write_text(json.dumps(report, indent=2), encoding="utf-8")
            self._set_feedback("feedback.saved")

    def save_html_report(self) -> None:
        if not self.machine:
            self._unavailable("empty.no_report", t("action.scan", self.language))
            return
        target = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML report", "*.html")], initialfile="os-readiness-report.html")
        if target:
            name = self.choice.get()
            html = html_report(self.machine, name, self.requirements[name], self.language)
            if self.machine_source == "Imported profile":
                html = html.replace("<h1>OS Readiness Report</h1>", f"<h1>OS Readiness Report</h1><p><strong>Machine source:</strong> Imported profile (captured {self.profile_metadata.get('created_at', 'unknown')}).</p>")
            Path(target).write_text(html, encoding="utf-8")
            self._set_feedback("feedback.saved")

    def copy_results(self) -> None:
        if not self.machine:
            self._unavailable("empty.no_report", t("action.scan", self.language))
            return
        name = self.choice.get()
        self.clipboard_clear()
        text = plain_text_report(self.machine, name, self.requirements[name], self.language)
        if self.machine_source == "Imported profile":
            text = f"Machine source: Imported profile (captured {self.profile_metadata.get('created_at', 'unknown')})\n" + text
        self.clipboard_append(text)
        self.update()
        self._set_feedback("feedback.copied")

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
            self.update_status.config(text=f"DB v{self.requirements_info.data_version} ({self.requirements_info.source}); {t('error.requirements_offline', self.language)}")
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
        self.update_status.config(text=f"DB v{info.data_version} ({info.source}); {t('feedback.updated', self.language)}")
        self._set_feedback("feedback.updated")

    def export_machine_profile(self) -> None:
        if not self.machine:
            messagebox.showinfo(t("action.export_profile", self.language), t("dialog.no_scan", self.language))
            return
        target = filedialog.asksaveasfilename(defaultextension=".osrprofile", filetypes=[("Machine profile", "*.osrprofile"), ("JSON", "*.json")], initialfile="machine-profile.osrprofile")
        if target:
            export_profile(self.machine, Path(target), data_version=self.requirements_info.data_version)
            self._set_feedback("feedback.saved")

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
            self._show_profile_error(exc)

    def _show_profile_error(self, error: ValueError, parent=None) -> None:
        """Show a useful profile error without silently scanning this machine."""
        messagebox.showerror(t("dialog.profile_import_error", self.language), f"{error}\n\n{t('error.profile_details', self.language)}", parent=parent)


class Batch6ReadinessApp(ReadinessApp):
    """Batch 6 presentation polish for reports and result context."""

    def _report_available(self) -> bool:
        return bool(self.machine and self.choice.get() in self.all_results and self.all_results.get(self.choice.get()))

    def _report_context(self) -> dict[str, str]:
        name = self.choice.get() if self.choice.get() in self.requirements else ""
        unknown = t("status.unknown", self.language)
        release = compatibility = suitability = lifecycle = readiness = unknown
        if name:
            profile = self.requirements[name]
            metadata = profile_metadata(name, profile)
            release = metadata.get("release", "") or unknown
            lifecycle = status_label(lifecycle_status(profile), self.language)
            checks = self.all_results.get(name, [])
            if checks:
                compatibility = status_label(overall_status(checks), self.language)
                fit = suitability_dict(assess_suitability(self.machine, profile, checks))
                suitability = fit.get("label", fit.get("category", unknown))
                readiness = status_label(evaluate_installation_readiness(self.machine, profile, checks)["status"], self.language)
        imported = self.machine_source == "Imported profile"
        return {"source": t("profile.source_imported" if imported else "profile.source_local", self.language), "captured": self.profile_metadata.get("created_at", "") if imported else "", "os": name or unknown, "release": release, "compatibility": compatibility, "suitability": suitability, "lifecycle": lifecycle, "readiness": readiness, "database": f"v{self.requirements_info.data_version} ({self.requirements_info.source})"}

    def _navigate(self, page: str) -> None:
        self._set_active_nav(page)
        actions = {"overview": self.show_overview, "analysis": self.show_detail, "compare_os": self.show_compare, "compare_machines": self.show_machine_compare, "upgrade": self.show_upgrade_plan, "recommendations": self.show_recommendations, "reports": self.show_reports, "settings": self.show_settings, "about": self.show_about}
        if page in actions:
            actions[page]()

    def show_reports(self) -> None:
        window = tk.Toplevel(self)
        window.title(t("nav.reports", self.language))
        self._size_dialog(window, 720, 620, 560, 460)
        window.configure(bg=UI["background"])
        card = self._page_card(window)
        body = card.content()
        identity = tk.Frame(body, bg=UI["surface"])
        identity.pack(fill="x")
        report_name = self.choice.get() if self.choice.get() in self.requirements else ""
        logo = self._logo_for(report_name, self.requirements.get(report_name, {})) if report_name else None
        if logo is not None:
            tk.Label(identity, image=logo, bg=UI["surface"], bd=0).pack(side="left", padx=(0, 10))
        tk.Label(identity, text=t("nav.reports", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 17, "bold")).pack(side="left")
        tk.Label(body, text=t("help.data_text", self.language), bg=UI["surface"], fg=UI["muted"], wraplength=640, justify="left", anchor="w").pack(fill="x", pady=(4, 12))
        context = self._report_context()
        box = tk.Frame(body, bg=UI["heading"], padx=14, pady=12)
        box.pack(fill="x", pady=(0, 14))
        tk.Label(box, text=t("help.concepts", self.language), bg=UI["heading"], fg=UI["text"], font=(self.font, 10, "bold")).pack(anchor="w")
        if not self._report_available():
            tk.Label(box, text=t("empty.no_report", self.language), bg=UI["heading"], fg=UI["muted"], wraplength=600, justify="left", anchor="w").pack(fill="x", pady=(6, 0))
        else:
            fields = (("label.machine_source", context["source"]), ("label.operating_system", context["os"]), ("label.lifecycle", context["release"]), ("label.compatibility", context["compatibility"]), ("label.suitability", context["suitability"]), ("label.lifecycle", context["lifecycle"]), ("label.installation_readiness", context["readiness"]))
            for key, value in fields:
                tk.Label(box, text=f"{t(key, self.language)}: {value}", bg=UI["heading"], fg=UI["muted"], anchor="w").pack(fill="x", pady=1)
            if context["captured"]:
                tk.Label(box, text=t("report.captured", self.language, timestamp=context["captured"]), bg=UI["heading"], fg=UI["muted"], anchor="w").pack(fill="x", pady=(4, 1))
        state = "normal" if self._report_available() else "disabled"
        tk.Label(body, text=t("action.save_report", self.language), bg=UI["surface"], fg=UI["text"], font=(self.font, 10, "bold")).pack(anchor="w")
        actions = tk.Frame(body, bg=UI["surface"])
        actions.pack(fill="x", pady=(5, 0))
        report_menu = tk.Menu(window, tearoff=False)
        report_menu.add_command(label=t("action.save_json", self.language), command=self.save_report)
        report_menu.add_command(label=t("action.save_html", self.language), command=self.save_html_report)
        ttk.Menubutton(actions, text=t("action.export_report", self.language), menu=report_menu, style="Accent.TButton", state=state).pack(side="left")
        secondary = tk.Frame(body, bg=UI["surface"])
        secondary.pack(fill="x", pady=(16, 0))
        ttk.Button(secondary, text=t("action.copy_results", self.language), command=self.copy_results, style="Secondary.TButton", state=state).pack(side="left")
        ttk.Button(secondary, text=t("action.source", self.language), command=self.open_source, style="Secondary.TButton", state="normal" if self._report_available() else "disabled").pack(side="left", padx=(8, 0))
        ttk.Button(secondary, text=t("action.close", self.language), command=window.destroy, style="Secondary.TButton").pack(side="right")
        tk.Label(body, text=f"{t('label.external_source', self.language)} • {context['database']} • {t('app.title', self.language)} {APP_VERSION}", bg=UI["surface"], fg=UI["muted"], wraplength=640, justify="left", anchor="w").pack(fill="x", pady=(18, 0))
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def _report_metadata(self) -> dict[str, str]:
        context = self._report_context()
        context["generated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        context["version"] = APP_VERSION
        return context

    def save_report(self) -> None:
        if not self._report_available():
            self._unavailable("empty.no_report", t("action.scan", self.language))
            return
        target = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON report", "*.json")], initialfile="os-readiness-report.json")
        if not target:
            return
        name = self.choice.get()
        report = as_report(self.machine, self.requirements[name])
        report.update({"target_os": name, "machine_source": self.machine_source, "report_context": self._report_metadata()})
        if self.profile_metadata:
            report["profile_metadata"] = {k: v for k, v in self.profile_metadata.items() if k in {"created_at", "name", "data_version"}}
        Path(target).write_text(json.dumps(report, indent=2), encoding="utf-8")
        self._set_feedback("feedback.saved")

    def save_html_report(self) -> None:
        if not self._report_available():
            self._unavailable("empty.no_report", t("action.scan", self.language))
            return
        target = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML report", "*.html")], initialfile="os-readiness-report.html")
        if not target:
            return
        name = self.choice.get()
        html = html_report(self.machine, name, self.requirements[name])
        from html import escape
        context = self._report_metadata()
        metadata = f"<section class='report-context'><h2>{escape(t('nav.reports', self.language))}</h2><p>{escape(t('label.machine_source', self.language))}: {escape(context['source'])} · {escape(t('label.operating_system', self.language))}: {escape(context['os'])} · {escape(t('label.compatibility', self.language))}: {escape(context['compatibility'])}</p><p>{escape(t('label.external_source', self.language))}: {escape(context['database'])} · {escape(t('app.title', self.language))} {escape(APP_VERSION)} · {escape(context['generated_at'])}</p></section>"
        html = html.replace("</h1>", "</h1>" + metadata, 1).replace("</style>", ".report-context{border:1px solid #d1d5db;border-radius:8px;padding:12px;margin:16px 0;color:#374151} @media print{body{max-width:none}.report-context{break-inside:avoid}} </style>", 1)
        Path(target).write_text(html, encoding="utf-8")
        self._set_feedback("feedback.saved")

    def copy_results(self) -> None:
        if not self._report_available():
            self._unavailable("empty.no_report", t("action.scan", self.language))
            return
        name = self.choice.get()
        context = self._report_metadata()
        prefix = [f"{t('app.title', self.language)} {APP_VERSION}", f"{t('label.machine_source', self.language)}: {context['source']}", f"{t('label.external_source', self.language)}: {context['database']}", ""]
        self.clipboard_clear()
        self.clipboard_append("\n".join(prefix) + plain_text_report(self.machine, name, self.requirements[name], self.language))
        self._set_feedback("feedback.copied")

    def open_source(self) -> None:
        if not self._report_available():
            return
        try:
            if not webbrowser.open(self.requirements[self.choice.get()]["source"]):
                self._set_feedback("error.requirements_offline")
        except (KeyError, OSError, webbrowser.Error):
            self._set_feedback("error.requirements_offline")

ReadinessApp = Batch6ReadinessApp


if __name__ == "__main__":
    ReadinessApp().mainloop()
