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
    load_requirements,
    overall_status,
    rank_compatibility,
)


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
        self.title("OS Readiness Checker")
        self.geometry("820x620")
        self.minsize(700, 500)
        self.configure(bg="#f4f6f8")
        self.requirements = load_requirements()
        self.machine = None
        self.results = []
        self.all_results = {}
        self.ranked_results = []
        self._build()
        self.after(100, self.run_check)

    def _build(self) -> None:
        font = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Fluent.TCombobox", padding=8, fieldbackground=UI["surface"], background=UI["surface"], foreground=UI["text"], font=(font, 10))
        style.configure("Accent.TButton", padding=(16, 9), font=(font, 10, "bold"), foreground="white", background=UI["accent"])
        style.map("Accent.TButton", background=[("active", UI["accent_dark"]), ("pressed", UI["accent_dark"])])
        style.configure("Secondary.TButton", padding=(12, 8), font=(font, 9), foreground=UI["text"], background=UI["surface"])
        style.map("Secondary.TButton", background=[("active", "#eef2ff")])
        style.configure("Fluent.Treeview", rowheight=36, font=(font, 10), background=UI["surface"], fieldbackground=UI["surface"], foreground=UI["text"], borderwidth=0)
        style.configure("Fluent.Treeview.Heading", font=(font, 9, "bold"), background="#f8fafc", foreground=UI["muted"], relief="flat", padding=(8, 9))

        self.configure(bg=UI["background"])
        header = tk.Frame(self, bg=UI["background"], padx=28, pady=24)
        header.pack(fill="x")
        tk.Label(header, text="OS Readiness Checker", bg=UI["background"], fg=UI["text"], font=(font, 23, "bold")).pack(anchor="w")
        tk.Label(header, text="Check this computer against published operating-system requirements.", bg=UI["background"], fg=UI["muted"], font=(font, 10)).pack(anchor="w", pady=(5, 0))

        body = tk.Frame(self, bg=UI["background"], padx=28, pady=24)
        body.pack(fill="both", expand=True)
        controls = tk.Frame(body, bg=UI["surface"], padx=18, pady=16, highlightbackground=UI["border"], highlightthickness=1)
        controls.pack(fill="x", pady=(0, 14))
        tk.Label(controls, text="Operating system", bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold")).pack(side="left")
        self.choice = ttk.Combobox(controls, state="readonly", width=31, values=list(self.requirements), style="Fluent.TCombobox")
        self.choice.current(0)
        self.choice.pack(side="left", padx=(14, 12))
        self.choice.bind("<<ComboboxSelected>>", lambda _event: self.show_detail())
        self.check_button = ttk.Button(controls, text="Scan this computer", command=self.run_check, style="Accent.TButton")
        self.check_button.pack(side="right")
        self.overview_button = ttk.Button(controls, text="Compatibility overview", command=self.show_overview, style="Secondary.TButton")
        self.overview_button.pack(side="right", padx=(0, 8))

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

        footer = tk.Frame(body, bg=UI["surface"], padx=18, pady=14, highlightbackground=UI["border"], highlightthickness=1)
        footer.pack(fill="x")
        self.details = tk.Label(footer, text="", justify="left", anchor="w", bg=UI["surface"], fg=UI["muted"], wraplength=570, font=(font, 9))
        self.details.pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="Official requirements", command=self.open_source, style="Secondary.TButton").pack(side="right", padx=(8, 0))
        ttk.Button(footer, text="Save report", command=self.save_report, style="Secondary.TButton").pack(side="right")
        self.compare_button = ttk.Button(footer, text="Compare OSes", command=self.show_compare, style="Secondary.TButton", state="disabled")
        self.compare_button.pack(side="right", padx=(8, 0))

    def run_check(self) -> None:
        self.check_button.config(state="disabled")
        self.summary.config(text="Scanning this computer…", fg="#374151")
        screen = (self.winfo_screenwidth(), self.winfo_screenheight())
        threading.Thread(target=self._scan, args=(screen,), daemon=True).start()

    def _scan(self, screen: tuple[int, int]) -> None:
        machine = collect_machine_info(screen)
        all_results = evaluate_all(machine, self.requirements)
        ranked = rank_compatibility(all_results)
        self.after(0, lambda: self._show_overview(machine, all_results, ranked))

    def _clear_table(self) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

    def _show_detail(self, results) -> None:
        self._clear_table()
        for item in results:
            self.table.insert("", "end", text=item.name, values=(ICONS[item.status] + " " + item.status.title(), item.detected, item.required), tags=(item.status,))

    def _show_overview(self, machine, all_results, ranked) -> None:
        self.machine, self.all_results, self.ranked_results = machine, all_results, ranked
        self.results = all_results[self.choice.get()]
        self._clear_table()
        self.table.heading("#0", text="Operating system")
        self.table.heading("result", text="Status")
        self.table.heading("detected", text="Score")
        self.table.heading("required", text="Checks")
        self.table.column("#0", width=270)
        self.table.column("result", width=110, anchor="center")
        self.table.column("detected", width=120, anchor="center")
        self.table.column("required", width=110, anchor="center")
        for item in ranked:
            status = item["status"]
            self.table.insert("", "end", text=item["name"], values=(ICONS.get(status, "") + " " + status.title(), f'{item["score"]}/100', len(item["checks"])), tags=(status,))
        self.summary.config(text=f"Compared {len(ranked)} operating systems from one hardware scan", fg=UI["text"])
        self.status_badge.config(text="  OVERVIEW  ", bg=UI["accent"], fg="white")
        self.details.config(text="Ranked by hardware compatibility score. Pass, review, and fail remain authoritative status results; scores are supplementary.")
        self.check_button.config(state="normal")
        self.compare_button.config(state="normal")

    def show_overview(self) -> None:
        if self.machine and self.ranked_results:
            self._show_overview(self.machine, self.all_results, self.ranked_results)

    def show_detail(self) -> None:
        if not self.machine or self.choice.get() not in self.all_results:
            return
        name = self.choice.get()
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
        messages = {
            "pass": "This computer meets every requirement checked",
            "fail": "This computer does not meet all checked requirements",
            "review": "The basic requirements pass, but some items need review",
        }
        score = next((item["score"] for item in self.ranked_results if item["name"] == name), 0)
        self.summary.config(text=f"{messages[status]} • Compatibility score {score}/100", fg=UI["text"])
        self.status_badge.config(text=f"  {status.upper()}  ", bg=COLORS[status], fg="white")
        notes = self.requirements[name].get("notes", [])
        self.details.config(text="\n".join("• " + note for note in notes))

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


if __name__ == "__main__":
    ReadinessApp().mainloop()
