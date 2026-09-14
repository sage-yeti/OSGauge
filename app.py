from __future__ import annotations

import json
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from checker import as_report, collect_machine_info, evaluate, load_requirements, overall_status


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
        self.configure(bg=UI["background"])
        self.requirements = load_requirements()
        self.machine = None
        self.results = []
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

        header = tk.Frame(self, bg=UI["background"], padx=28, pady=24)
        header.pack(fill="x")
        tk.Label(header, text="OS Readiness Checker", bg=UI["background"], fg=UI["text"], font=(font, 23, "bold")).pack(anchor="w")
        tk.Label(header, text="Check this computer against published operating-system requirements.", bg=UI["background"], fg=UI["muted"], font=(font, 10)).pack(anchor="w", pady=(5, 0))

        body = tk.Frame(self, bg=UI["background"], padx=28, pady=(0, 24))
        body.pack(fill="both", expand=True)
        controls = tk.Frame(body, bg=UI["surface"], padx=18, pady=16, highlightbackground=UI["border"], highlightthickness=1)
        controls.pack(fill="x", pady=(0, 14))
        tk.Label(controls, text="Operating system", bg=UI["surface"], fg=UI["text"], font=(font, 10, "bold")).pack(side="left")
        self.choice = ttk.Combobox(controls, state="readonly", width=31, values=list(self.requirements), style="Fluent.TCombobox")
        self.choice.current(0)
        self.choice.pack(side="left", padx=(14, 12))
        self.choice.bind("<<ComboboxSelected>>", lambda _event: self.run_check())
        self.check_button = ttk.Button(controls, text="Scan this computer", command=self.run_check, style="Accent.TButton")
        self.check_button.pack(side="right")

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

    def run_check(self) -> None:
        self.check_button.config(state="disabled")
        self.summary.config(text="Scanning this computer…", fg=UI["text"])
        self.status_badge.config(text="  SCANNING  ", bg="#e2e8f0", fg=UI["muted"])
        screen = (self.winfo_screenwidth(), self.winfo_screenheight())
        threading.Thread(target=self._scan, args=(screen,), daemon=True).start()

    def _scan(self, screen: tuple[int, int]) -> None:
        machine = collect_machine_info(screen)
        selected = self.choice.get()
        results = evaluate(machine, self.requirements[selected])
        self.after(0, lambda: self._show(machine, results))

    def _show(self, machine, results) -> None:
        self.machine, self.results = machine, results
        for item in self.table.get_children():
            self.table.delete(item)
        for item in results:
            self.table.insert("", "end", text=item.name, values=(ICONS[item.status] + " " + item.status.title(), item.detected, item.required), tags=(item.status,))
        status = overall_status(results)
        messages = {
            "pass": "This computer meets every requirement checked",
            "fail": "This computer does not meet all checked requirements",
            "review": "The basic requirements pass, but some items need review",
        }
        self.summary.config(text=messages[status], fg=UI["text"])
        self.status_badge.config(text=f"  {status.upper()}  ", bg=COLORS[status], fg="white")
        notes = self.requirements[self.choice.get()].get("notes", [])
        self.details.config(text="\n".join("• " + note for note in notes))
        self.check_button.config(state="normal")

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
