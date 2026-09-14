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
from requirements_update import RequirementsInfo, fetch_latest, load_requirements_info
from theme import colors_for, load_settings, load_theme_mode, save_settings, save_theme_mode
from version import APP_VERSION
from suitability import assess_suitability, suitability_dict


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
        self.theme_mode = load_theme_mode()
        UI.update(colors_for(self.theme_mode))
        self.requirements_info = load_requirements_info()
        self.requirements = self.requirements_info.profiles
        self.machine = None
        self.results = []
        self.all_results = {}
        self.ranked_results = []
        self.suitability_by_os = {}
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
        style.theme_use("clam")
        style.configure("Fluent.TCombobox", padding=8, fieldbackground=UI["surface"], background=UI["surface"], foreground=UI["text"], font=(font, 10), selectbackground=UI["accent"], selectforeground="white")
        style.map("Fluent.TCombobox", fieldbackground=[("readonly", UI["surface"]), ("focus", UI["surface"]), ("active", UI["surface"])], foreground=[("readonly", UI["text"]), ("focus", UI["text"]), ("active", UI["text"])])
        style.configure("Accent.TButton", padding=(16, 9), font=(font, 10, "bold"), foreground="white", background=UI["accent"])
        style.map("Accent.TButton", background=[("active", UI["accent_dark"]), ("pressed", UI["accent_dark"])])
        style.configure("Secondary.TButton", padding=(12, 8), font=(font, 9), foreground=UI["text"], background=UI["surface"])
        style.map("Secondary.TButton", background=[("active", UI["heading"]), ("pressed", UI["heading"])])
        style.configure("Fluent.Treeview", rowheight=36, font=(font, 10), background=UI["surface"], fieldbackground=UI["surface"], foreground=UI["text"], borderwidth=0)
        style.configure("Fluent.Treeview.Heading", font=(font, 9, "bold"), background=UI["heading"], foreground=UI["muted"], relief="flat", padding=(8, 9))
        style.map("Fluent.Treeview", background=[("selected", UI["accent"])], foreground=[("selected", "white")])
        style.map("Fluent.Treeview.Heading", background=[("active", UI["heading"]), ("pressed", UI["heading"])], foreground=[("active", UI["text"]), ("pressed", UI["text"])])

        self.configure(bg=UI["background"])
        header = tk.Frame(self, bg=UI["background"], padx=28, pady=24)
        header.pack(fill="x")
        tk.Label(header, text="OS Readiness Checker", bg=UI["background"], fg=UI["text"], font=(font, 23, "bold")).pack(anchor="w")
        tk.Label(header, text="Check this computer against published operating-system requirements.", bg=UI["background"], fg=UI["muted"], font=(font, 10)).pack(anchor="w", pady=(5, 0))
        theme_box = tk.Frame(header, bg=UI["background"])
        theme_box.pack(anchor="e", pady=(0, 2))
        tk.Label(theme_box, text="Theme", bg=UI["background"], fg=UI["muted"], font=(font, 9)).pack(side="left", padx=(0, 6))
        self.theme_choice = ttk.Combobox(theme_box, state="readonly", width=9, values=("System", "Light", "Dark"), style="Fluent.TCombobox")
        self.theme_choice.set(self.theme_mode)
        self.theme_choice.pack(side="left")
        self.theme_choice.bind("<<ComboboxSelected>>", lambda _event: self.change_theme())
        ttk.Button(theme_box, text="About", command=self.show_about, style="Secondary.TButton").pack(side="left", padx=(8, 0))

        body = tk.Frame(self, bg=UI["background"], padx=28, pady=24)
        body.pack(fill="both", expand=True)
        controls = tk.Frame(body, bg=UI["surface"], padx=18, pady=16, highlightbackground=UI["border"], highlightthickness=1)
        controls.pack(fill="x", pady=(0, 14))
        tk.Label(controls, text="Operating system", bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold")).pack(side="left")
        self.choice = ttk.Combobox(controls, state="readonly", width=31, values=list(self.requirements), style="Fluent.TCombobox")
        last_os = self.settings.get("last_os")
        self.choice.current(list(self.requirements).index(last_os) if last_os in self.requirements else 0)
        self.choice.pack(side="left", padx=(14, 12))
        self.choice.bind("<<ComboboxSelected>>", lambda _event: self.show_detail())
        self.check_button = ttk.Button(controls, text="Scan this computer", command=self.run_check, style="Accent.TButton")
        self.check_button.pack(side="right")
        self.overview_button = ttk.Button(controls, text="Compatibility overview", command=self.show_overview, style="Secondary.TButton")
        self.overview_button.pack(side="right", padx=(0, 8))
        self.update_button = ttk.Button(controls, text="Check requirements updates", command=self.check_requirements_updates, style="Secondary.TButton")
        self.update_button.pack(side="right", padx=(0, 8))
        self.update_status = tk.Label(controls, text=f"DB v{self.requirements_info.data_version} ({self.requirements_info.source})", bg=UI["surface"], fg=UI["muted"], font=(font, 9))
        self.update_status.pack(side="right", padx=(0, 10))

        summary_card = tk.Frame(body, bg=UI["surface"], padx=18, pady=14, highlightbackground=UI["border"], highlightthickness=1)
        summary_card.pack(fill="x", pady=(0, 14))
        self.status_badge = tk.Label(summary_card, text="  SCANNING  ", bg="#e2e8f0", fg=UI["muted"], font=(font, 9, "bold"), padx=8, pady=5)
        self.status_badge.pack(side="left", padx=(0, 12))
        self.summary = tk.Label(summary_card, text="Scanning…", bg=UI["surface"], fg=UI["text"], font=(font, 14, "bold"))
        self.summary.pack(side="left", anchor="w")

        columns = ("result", "detected", "required")
        table_card = tk.Frame(body, bg=UI["surface"], padx=1, pady=1, highlightbackground=UI["border"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_card, columns=columns, show="tree headings", style="Fluent.Treeview")
        self.table.heading("#0", text="Check")
        self.table.heading("result", text="Result")
        self.table.heading("detected", text="Detected")
        self.table.heading("required", text="Required")
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
        ttk.Button(footer, text="Official requirements", command=self.open_source, style="Secondary.TButton").pack(side="right", padx=(8, 0))
        ttk.Button(footer, text="Save report", command=self.save_report, style="Secondary.TButton").pack(side="right")
        ttk.Button(footer, text="Save HTML", command=self.save_html_report, style="Secondary.TButton").pack(side="right", padx=(8, 0))
        ttk.Button(footer, text="Copy results", command=self.copy_results, style="Secondary.TButton").pack(side="right", padx=(8, 0))
        self.compare_button = ttk.Button(footer, text="Compare OSes", command=self.show_compare, style="Secondary.TButton", state="disabled")
        self.compare_button.pack(side="right", padx=(8, 0))
        self._apply_theme(self)

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
        self.check_button.config(state="disabled")
        self.summary.config(text="Scanning this computer…", fg="#374151")
        screen = (self.winfo_screenwidth(), self.winfo_screenheight())
        threading.Thread(target=self._scan, args=(screen,), daemon=True).start()

    def change_theme(self) -> None:
        self.theme_mode = self.theme_choice.get()
        save_theme_mode(self.theme_mode)
        UI.update(colors_for(self.theme_mode))
        self._apply_theme(self)

    def show_about(self) -> None:
        window = tk.Toplevel(self)
        window.title("About OS Readiness Checker")
        window.geometry("430x330")
        window.resizable(False, False)
        window.configure(bg=UI["background"])
        card = tk.Frame(window, bg=UI["surface"], padx=24, pady=22, highlightbackground=UI["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(card, text="OS Readiness Checker", bg=UI["surface"], fg=UI["text"], font=(self.font, 17, "bold")).pack(anchor="w")
        tk.Label(card, text=f"Version {APP_VERSION}\nCross-platform hardware compatibility and suitability checks.\n\nRequirements database: v{self.requirements_info.data_version} ({self.requirements_info.source})\nRuns on Windows and Linux. License: MIT", justify="left", anchor="w", bg=UI["surface"], fg=UI["muted"], font=(self.font, 9)).pack(fill="x", pady=(10, 16))
        actions = tk.Frame(card, bg=UI["surface"])
        actions.pack(fill="x")
        ttk.Button(actions, text="Open GitHub", command=lambda: webbrowser.open("https://github.com/sage-yeti/os-readiness-checker"), style="Secondary.TButton").pack(side="left")
        ttk.Button(actions, text="Check updates", command=self.check_requirements_updates, style="Secondary.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Close", command=window.destroy, style="Secondary.TButton").pack(side="right")
        window.bind("<Escape>", lambda _event: window.destroy())
        self._apply_theme(window)

    def _apply_theme(self, widget) -> None:
        try:
            if isinstance(widget, tk.Toplevel):
                widget.configure(bg=UI["background"])
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=UI["background"] if widget is self else UI["surface"])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=UI["surface"] if widget.master is not self else UI["background"], fg=UI["text"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._apply_theme(child)
        self.style.configure("Fluent.TCombobox", fieldbackground=UI["surface"], background=UI["surface"], foreground=UI["text"], selectbackground=UI["accent"], selectforeground="white")
        self.style.map("Fluent.TCombobox", fieldbackground=[("readonly", UI["surface"]), ("focus", UI["surface"]), ("active", UI["surface"])], foreground=[("readonly", UI["text"]), ("focus", UI["text"]), ("active", UI["text"])])
        self.style.configure("Secondary.TButton", foreground=UI["text"], background=UI["surface"])
        self.style.map("Secondary.TButton", background=[("active", UI["heading"]), ("pressed", UI["heading"])])
        self.style.configure("Fluent.Treeview", background=UI["surface"], fieldbackground=UI["surface"], foreground=UI["text"])
        self.style.map("Fluent.Treeview", background=[("selected", UI["accent"])], foreground=[("selected", "white")])
        self.style.configure("Fluent.Treeview.Heading", background=UI["heading"], foreground=UI["muted"])
        self.style.map("Fluent.Treeview.Heading", background=[("active", UI["heading"]), ("pressed", UI["heading"])], foreground=[("active", UI["text"]), ("pressed", UI["text"])])
        self.table.tag_configure("pass", foreground="#4ade80" if self.theme_mode == "Dark" else COLORS["pass"])
        self.table.tag_configure("fail", foreground="#f87171" if self.theme_mode == "Dark" else COLORS["fail"])
        self.table.tag_configure("unknown", foreground="#facc15" if self.theme_mode == "Dark" else COLORS["unknown"])

    def _scan(self, screen: tuple[int, int]) -> None:
        machine = collect_machine_info(screen)
        all_results = evaluate_all(machine, self.requirements)
        suitability = {name: suitability_dict(assess_suitability(machine, profile, all_results[name])) for name, profile in self.requirements.items()}
        ranked = rank_compatibility(all_results, suitability)
        self.after(0, lambda: self._show_overview(machine, all_results, ranked))

    def _clear_table(self) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

    def _show_detail(self, results) -> None:
        self._clear_table()
        for item in results:
            self.table.insert("", "end", text=item.name, values=(ICONS[item.status] + " " + item.status.title(), item.detected, item.required), tags=(item.status,))

    def show_selected_check(self, _event=None) -> None:
        if not self.machine or not self.choice.get() or not self.table.selection():
            return
        item_id = self.table.selection()[0]
        name = self.table.item(item_id, "text")
        check = next((item for item in self.all_results.get(self.choice.get(), []) if item.name == name), None)
        if not check:
            return
        info = explain_check(self.machine, self.requirements[self.choice.get()], check)
        text = f"{check.name}: {info['explanation']}"
        if info["remediation"]:
            text += f"\nNext step: {info['remediation']}"
        self.details.config(text=text)

    def _show_overview(self, machine, all_results, ranked) -> None:
        self.machine, self.all_results, self.ranked_results = machine, all_results, ranked
        self.results = all_results[self.choice.get()]
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
            self.table.insert("", "end", text=item["name"], values=(ICONS.get(status, "") + " " + status.title(), f'{item["score"]}/100', item["suitability"]["category"]), tags=(status,))
        self.summary.config(text=f"Compared {len(ranked)} operating systems from one hardware scan", fg=UI["text"])
        self.status_badge.config(text="  OVERVIEW  ", bg=UI["accent"], fg="white")
        self.details.config(text=f"Requirements database v{self.requirements_info.data_version} ({self.requirements_info.source}). Compatibility is based on published requirements; suitability is application-defined headroom guidance.")
        self.check_button.config(state="normal")
        self.compare_button.config(state="normal")

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
        self.table.heading("#0", text="Check")
        self.table.heading("result", text="Result")
        self.table.heading("detected", text="Detected")
        self.table.heading("required", text="Required")
        self.table.column("#0", width=190)
        self.table.column("result", width=90, anchor="center")
        self.table.column("detected", width=190)
        self.table.column("required", width=190)
        status = overall_status(results)
        suitability = suitability_dict(assess_suitability(self.machine, self.requirements[name], results))
        messages = {
            "pass": "This computer meets every requirement checked",
            "fail": "This computer does not meet all checked requirements",
            "review": "The basic requirements pass, but some items need review",
        }
        score = next((item["score"] for item in self.ranked_results if item["name"] == name), 0)
        self.summary.config(text=f"{messages[status]} • Compatibility score {score}/100 • {suitability['category']}", fg=UI["text"])
        self.status_badge.config(text=f"  {status.upper()}  ", bg=COLORS[status], fg="white")
        notes = self.requirements[name].get("notes", [])
        gpu = self.machine.gpu_name or "Unknown"
        if self.machine.gpu_vram_mb:
            gpu += f" ({self.machine.gpu_vram_mb} MB VRAM)"
        machine_details = [
            f"CPU: {self.machine.cpu_name}",
            f"GPU: {gpu}",
            f"System disk: {self.machine.system_disk or 'Unknown'} ({self.machine.storage_partition_style or 'Unknown'} / {self.machine.storage_filesystem or 'Unknown'})",
            f"Virtualization: {self.machine.virtualization or 'Unknown'}",
        ]
        self.details.config(text=f"Requirements database v{self.requirements_info.data_version} ({self.requirements_info.source})\nSuitability: {suitability['category']} — {suitability['explanation']}\n" + "\n".join(machine_details + ["• " + note for note in notes]))

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

    def open_source(self) -> None:
        webbrowser.open(self.requirements[self.choice.get()]["source"])

    def save_report(self) -> None:
        if not self.machine:
            return
        target = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON report", "*.json")], initialfile="os-readiness-report.json")
        if target:
            report = as_report(self.machine, self.requirements[self.choice.get()])
            report["target_os"] = self.choice.get()
            Path(target).write_text(json.dumps(report, indent=2), encoding="utf-8")
            messagebox.showinfo("Report saved", "The readiness report was saved successfully.")

    def save_html_report(self) -> None:
        if not self.machine:
            return
        target = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML report", "*.html")], initialfile="os-readiness-report.html")
        if target:
            name = self.choice.get()
            Path(target).write_text(html_report(self.machine, name, self.requirements[name]), encoding="utf-8")
            messagebox.showinfo("Report saved", "The HTML report was saved successfully.")

    def copy_results(self) -> None:
        if not self.machine:
            return
        name = self.choice.get()
        self.clipboard_clear()
        self.clipboard_append(plain_text_report(self.machine, name, self.requirements[name]))
        self.update()
        messagebox.showinfo("Results copied", "A compact compatibility summary was copied to the clipboard.")

    def check_requirements_updates(self) -> None:
        self.update_button.config(state="disabled")
        threading.Thread(target=self._check_requirements_updates, daemon=True).start()

    def _check_requirements_updates(self) -> None:
        info = fetch_latest()
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


if __name__ == "__main__":
    ReadinessApp().mainloop()
