from __future__ import annotations

import json
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from checker import as_report, collect_machine_info, evaluate, load_requirements, overall_status


COLORS = {"pass": "#15803d", "fail": "#b91c1c", "unknown": "#a16207", "review": "#a16207"}
ICONS = {"pass": "✓", "fail": "✕", "unknown": "?"}


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
        self._build()
        self.after(100, self.run_check)

    def _build(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", padding=8)
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        header = tk.Frame(self, bg="#172554", padx=28, pady=22)
        header.pack(fill="x")
        tk.Label(header, text="OS Readiness Checker", bg="#172554", fg="white", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(header, text="Check this computer against published operating-system requirements.", bg="#172554", fg="#c7d2fe", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg="#f4f6f8", padx=28, pady=22)
        body.pack(fill="both", expand=True)
        controls = tk.Frame(body, bg="#f4f6f8")
        controls.pack(fill="x")
        tk.Label(controls, text="Operating system", bg="#f4f6f8", fg="#111827", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.choice = ttk.Combobox(controls, state="readonly", width=31, values=list(self.requirements))
        self.choice.current(0)
        self.choice.pack(side="left", padx=12)
        self.choice.bind("<<ComboboxSelected>>", lambda _event: self.run_check())
        self.check_button = ttk.Button(controls, text="Scan this computer", command=self.run_check)
        self.check_button.pack(side="right")

        self.summary = tk.Label(body, text="Scanning…", bg="#f4f6f8", fg="#374151", font=("Segoe UI", 16, "bold"), pady=18)
        self.summary.pack(anchor="w")

        columns = ("result", "detected", "required")
        self.table = ttk.Treeview(body, columns=columns, show="tree headings")
        self.table.heading("#0", text="Check")
        self.table.heading("result", text="Result")
        self.table.heading("detected", text="Detected")
        self.table.heading("required", text="Required")
        self.table.column("#0", width=170)
        self.table.column("result", width=90, anchor="center")
        self.table.column("detected", width=190)
        self.table.column("required", width=190)
        self.table.pack(fill="both", expand=True)
        self.table.tag_configure("pass", foreground=COLORS["pass"])
        self.table.tag_configure("fail", foreground=COLORS["fail"])
        self.table.tag_configure("unknown", foreground=COLORS["unknown"])

        footer = tk.Frame(body, bg="#f4f6f8", pady=12)
        footer.pack(fill="x")
        self.details = tk.Label(footer, text="", justify="left", anchor="w", bg="#f4f6f8", fg="#4b5563", wraplength=570)
        self.details.pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="Official requirements", command=self.open_source).pack(side="right", padx=(8, 0))
        ttk.Button(footer, text="Save report", command=self.save_report).pack(side="right")

    def run_check(self) -> None:
        self.check_button.config(state="disabled")
        self.summary.config(text="Scanning this computer…", fg="#374151")
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
        self.summary.config(text=messages[status], fg=COLORS[status])
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
