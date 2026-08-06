"""
pages/results.py
Result Management: Generate Result Card, Position List, Merit List, Print Result.
"""

import tkinter as tk
from tkinter import ttk, filedialog

from database import get_connection
from ui_helpers import info, warn, error


class ResultsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        ttk.Label(self, text="Result Management", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))

        conn = get_connection()
        exams = conn.execute(
            """SELECT e.id, e.exam_name, e.exam_type, c.class_name
               FROM exams e LEFT JOIN classes c ON c.id = e.class_id"""
        ).fetchall()
        conn.close()
        self.exam_map = {f"{e['exam_name']} ({e['exam_type']}) - {e['class_name']}": e["id"] for e in exams}

        ttk.Label(top, text="Exam:").pack(side="left")
        self.exam_combo = ttk.Combobox(top, values=list(self.exam_map.keys()), width=32, state="readonly")
        self.exam_combo.pack(side="left", padx=6)

        ttk.Button(top, text="Generate Merit / Position List", style="Accent.TButton",
                   command=self.generate_merit_list).pack(side="left", padx=10)
        ttk.Button(top, text="View Result Card (selected student)",
                   command=self.view_result_card).pack(side="left", padx=6)

        columns = ("position", "id", "name", "obtained", "total", "percentage")
        headers = ["Position", "ID", "Name", "Marks Obtained", "Total Marks", "Percentage"]
        widths = [70, 50, 180, 110, 100, 90]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)
        for c, h, w in zip(columns, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        ttk.Button(self, text="Print Merit List", command=self.print_merit_list).pack(anchor="w", pady=(10, 0))

    def _compute_results(self, exam_id):
        conn = get_connection()
        students = conn.execute(
            """SELECT DISTINCT s.id, s.name FROM students s
               JOIN marks m ON m.student_id = s.id WHERE m.exam_id=?""",
            (exam_id,),
        ).fetchall()

        results = []
        for s in students:
            rows = conn.execute(
                "SELECT marks_obtained, total_marks FROM marks WHERE exam_id=? AND student_id=?",
                (exam_id, s["id"]),
            ).fetchall()
            obtained = sum(r["marks_obtained"] for r in rows)
            total = sum(r["total_marks"] for r in rows)
            pct = (obtained / total * 100) if total else 0
            results.append({"id": s["id"], "name": s["name"], "obtained": obtained, "total": total, "pct": pct})
        conn.close()

        results.sort(key=lambda r: r["pct"], reverse=True)
        for i, r in enumerate(results):
            r["position"] = i + 1
        return results

    def generate_merit_list(self):
        exam_display = self.exam_combo.get()
        exam_id = self.exam_map.get(exam_display)
        if not exam_id:
            warn("Please select an exam.")
            return

        self.current_exam_id = exam_id
        self.current_results = self._compute_results(exam_id)

        for row in self.tree.get_children():
            self.tree.delete(row)

        if not self.current_results:
            warn("No marks have been entered for this exam yet.")
            return

        for r in self.current_results:
            self.tree.insert(
                "", "end",
                values=(r["position"], r["id"], r["name"], r["obtained"], r["total"], f"{r['pct']:.2f}%"),
            )

    def view_result_card(self):
        sel = self.tree.selection()
        if not sel:
            warn("Please generate the merit list and select a student row first.")
            return
        vals = self.tree.item(sel[0])["values"]
        position, sid, name, obtained, total, pct = vals

        conn = get_connection()
        exam_display = self.exam_combo.get()
        exam_id = self.exam_map[exam_display]
        subject_rows = conn.execute(
            """SELECT sub.subject_name, m.marks_obtained, m.total_marks
               FROM marks m JOIN subjects sub ON sub.id = m.subject_id
               WHERE m.exam_id=? AND m.student_id=?""",
            (exam_id, sid),
        ).fetchall()
        conn.close()

        win = tk.Toplevel(self)
        win.title(f"Result Card - {name}")
        win.geometry("420x480")
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Result Card: {name}", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(frame, text=f"Exam: {exam_display}").pack(anchor="w")
        ttk.Label(frame, text=f"Position: {position}").pack(anchor="w", pady=(0, 10))

        table = ttk.Treeview(frame, columns=("subject", "obtained", "total"), show="headings", height=10)
        for c, h, w in zip(("subject", "obtained", "total"), ["Subject", "Obtained", "Total"], [160, 100, 100]):
            table.heading(c, text=h)
            table.column(c, width=w, anchor="w")
        table.pack(fill="both", expand=True)
        for row in subject_rows:
            table.insert("", "end", values=(row["subject_name"], row["marks_obtained"], row["total_marks"]))

        ttk.Label(frame, text=f"Total: {obtained} / {total}   ({pct})",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 0))
        ttk.Button(frame, text="Close", command=win.destroy).pack(pady=15)

    def print_merit_list(self):
        if not hasattr(self, "current_results") or not self.current_results:
            warn("Please generate a merit list first.")
            return
        exam_display = self.exam_combo.get()
        lines = [f"MERIT / POSITION LIST", f"Exam: {exam_display}", "=" * 50]
        for r in self.current_results:
            lines.append(
                f"{r['position']:>3}. {r['name']:<25} {r['obtained']:>6}/{r['total']:<6} {r['pct']:.2f}%"
            )
        content = "\n".join(lines)

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="Merit_List.txt",
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            win = tk.Toplevel(self)
            win.title("Merit List")
            text = tk.Text(win, width=60, height=25, font=("Consolas", 10))
            text.insert("1.0", content)
            text.config(state="disabled")
            text.pack(fill="both", expand=True)
            return
        try:
            with open(path, "w") as f:
                f.write(content)
            info(f"Saved to {path}")
        except Exception as e:
            error(f"Could not save file: {e}")

    def refresh(self):
        self.build()
