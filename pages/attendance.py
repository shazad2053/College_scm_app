"""
pages/attendance.py
Attendance: Student Daily/Monthly, Teacher Daily/Monthly.
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime

from database import get_connection
from ui_helpers import today_str, info, warn

STATUS_OPTIONS = ["Present", "Absent", "Leave"]


class AttendancePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        ttk.Label(self, text="Attendance", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.student_daily_tab = ttk.Frame(notebook, padding=15)
        self.student_report_tab = ttk.Frame(notebook, padding=15)
        self.teacher_daily_tab = ttk.Frame(notebook, padding=15)
        self.teacher_report_tab = ttk.Frame(notebook, padding=15)

        notebook.add(self.student_daily_tab, text="Student - Daily Attendance")
        notebook.add(self.student_report_tab, text="Student - Monthly Report")
        notebook.add(self.teacher_daily_tab, text="Teacher - Daily Attendance")
        notebook.add(self.teacher_report_tab, text="Teacher - Monthly Report")

        self.build_student_daily(self.student_daily_tab)
        self.build_student_report(self.student_report_tab)
        self.build_teacher_daily(self.teacher_daily_tab)
        self.build_teacher_report(self.teacher_report_tab)

    # ---------------- Student Daily ----------------
    def build_student_daily(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="Date (YYYY-MM-DD):").pack(side="left")
        self.sd_date_entry = ttk.Entry(top, width=14)
        self.sd_date_entry.insert(0, today_str())
        self.sd_date_entry.pack(side="left", padx=6)

        conn = get_connection()
        classes = conn.execute("SELECT id, class_name, section FROM classes").fetchall()
        conn.close()
        self.sd_class_map = {f"{c['class_name']} - {c['section'] or ''}".strip(" -"): c["id"] for c in classes}

        ttk.Label(top, text="Class:").pack(side="left", padx=(20, 6))
        self.sd_class_combo = ttk.Combobox(top, values=list(self.sd_class_map.keys()), width=20, state="readonly")
        self.sd_class_combo.pack(side="left")

        ttk.Button(top, text="Load Students", style="Accent.TButton",
                   command=self.load_students_for_attendance).pack(side="left", padx=10)
        ttk.Button(top, text="Save Attendance", command=self.save_student_attendance).pack(side="left")

        columns = ("id", "name", "roll", "status")
        self.sd_tree = ttk.Treeview(tab, columns=columns, show="headings", height=16)
        for c, h, w in zip(columns, ["ID", "Name", "Roll No.", "Status"], [40, 200, 80, 100]):
            self.sd_tree.heading(c, text=h)
            self.sd_tree.column(c, width=w, anchor="w")
        self.sd_tree.pack(fill="both", expand=True)
        self.sd_tree.bind("<Double-1>", self.cycle_status)

        ttk.Label(tab, text="Tip: double-click a row to cycle Present → Absent → Leave").pack(anchor="w", pady=(6, 0))

    def load_students_for_attendance(self):
        class_name = self.sd_class_combo.get()
        if not class_name:
            warn("Please select a class.")
            return
        class_id = self.sd_class_map[class_name]
        date = self.sd_date_entry.get().strip()

        conn = get_connection()
        students = conn.execute(
            "SELECT id, name, roll_no FROM students WHERE class_id=? AND status='Active'", (class_id,)
        ).fetchall()
        existing = {
            r["student_id"]: r["status"]
            for r in conn.execute(
                "SELECT student_id, status FROM student_attendance WHERE date=?", (date,)
            ).fetchall()
        }
        conn.close()

        for row in self.sd_tree.get_children():
            self.sd_tree.delete(row)
        for s in students:
            status = existing.get(s["id"], "Present")
            self.sd_tree.insert("", "end", values=(s["id"], s["name"], s["roll_no"], status))

    def cycle_status(self, event):
        sel = self.sd_tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = list(self.sd_tree.item(item)["values"])
        current = vals[3]
        next_status = STATUS_OPTIONS[(STATUS_OPTIONS.index(current) + 1) % len(STATUS_OPTIONS)]
        vals[3] = next_status
        self.sd_tree.item(item, values=vals)

    def save_student_attendance(self):
        date = self.sd_date_entry.get().strip()
        if not date:
            warn("Please enter a date.")
            return
        conn = get_connection()
        for item in self.sd_tree.get_children():
            sid, name, roll, status = self.sd_tree.item(item)["values"]
            conn.execute(
                """INSERT INTO student_attendance (student_id, date, status) VALUES (?, ?, ?)
                   ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status""",
                (sid, date, status),
            )
        conn.commit()
        conn.close()
        info("Attendance saved.")

    # ---------------- Student Monthly Report ----------------
    def build_student_report(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))
        now = datetime.now()

        ttk.Label(top, text="Month (1-12):").pack(side="left")
        self.sr_month_entry = ttk.Entry(top, width=6)
        self.sr_month_entry.insert(0, str(now.month))
        self.sr_month_entry.pack(side="left", padx=6)

        ttk.Label(top, text="Year:").pack(side="left", padx=(10, 6))
        self.sr_year_entry = ttk.Entry(top, width=8)
        self.sr_year_entry.insert(0, str(now.year))
        self.sr_year_entry.pack(side="left")

        ttk.Button(top, text="Generate Report", style="Accent.TButton",
                   command=self.generate_student_report).pack(side="left", padx=10)

        columns = ("id", "name", "present", "absent", "leave", "total")
        self.sr_tree = ttk.Treeview(tab, columns=columns, show="headings", height=16)
        for c, h, w in zip(columns, ["ID", "Name", "Present", "Absent", "Leave", "Total Marked"],
                            [40, 200, 80, 80, 80, 100]):
            self.sr_tree.heading(c, text=h)
            self.sr_tree.column(c, width=w, anchor="w")
        self.sr_tree.pack(fill="both", expand=True)

    def generate_student_report(self):
        month = self.sr_month_entry.get().strip().zfill(2)
        year = self.sr_year_entry.get().strip()
        prefix = f"{year}-{month}"

        conn = get_connection()
        students = conn.execute("SELECT id, name FROM students WHERE status='Active'").fetchall()

        for row in self.sr_tree.get_children():
            self.sr_tree.delete(row)

        for s in students:
            records = conn.execute(
                "SELECT status FROM student_attendance WHERE student_id=? AND date LIKE ?",
                (s["id"], f"{prefix}%"),
            ).fetchall()
            present = sum(1 for r in records if r["status"] == "Present")
            absent = sum(1 for r in records if r["status"] == "Absent")
            leave = sum(1 for r in records if r["status"] == "Leave")
            total = len(records)
            if total > 0:
                self.sr_tree.insert("", "end", values=(s["id"], s["name"], present, absent, leave, total))
        conn.close()

    # ---------------- Teacher Daily ----------------
    def build_teacher_daily(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="Date (YYYY-MM-DD):").pack(side="left")
        self.td_date_entry = ttk.Entry(top, width=14)
        self.td_date_entry.insert(0, today_str())
        self.td_date_entry.pack(side="left", padx=6)

        ttk.Button(top, text="Load Teachers", style="Accent.TButton",
                   command=self.load_teachers_for_attendance).pack(side="left", padx=10)
        ttk.Button(top, text="Save Attendance", command=self.save_teacher_attendance).pack(side="left")

        columns = ("id", "name", "status")
        self.td_tree = ttk.Treeview(tab, columns=columns, show="headings", height=16)
        for c, h, w in zip(columns, ["ID", "Name", "Status"], [40, 220, 100]):
            self.td_tree.heading(c, text=h)
            self.td_tree.column(c, width=w, anchor="w")
        self.td_tree.pack(fill="both", expand=True)
        self.td_tree.bind("<Double-1>", self.cycle_teacher_status)

        ttk.Label(tab, text="Tip: double-click a row to cycle Present → Absent → Leave").pack(anchor="w", pady=(6, 0))

    def load_teachers_for_attendance(self):
        date = self.td_date_entry.get().strip()
        conn = get_connection()
        teachers = conn.execute("SELECT id, name FROM teachers WHERE status='Active'").fetchall()
        existing = {
            r["teacher_id"]: r["status"]
            for r in conn.execute(
                "SELECT teacher_id, status FROM teacher_attendance WHERE date=?", (date,)
            ).fetchall()
        }
        conn.close()

        for row in self.td_tree.get_children():
            self.td_tree.delete(row)
        for t in teachers:
            status = existing.get(t["id"], "Present")
            self.td_tree.insert("", "end", values=(t["id"], t["name"], status))

    def cycle_teacher_status(self, event):
        sel = self.td_tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = list(self.td_tree.item(item)["values"])
        current = vals[2]
        next_status = STATUS_OPTIONS[(STATUS_OPTIONS.index(current) + 1) % len(STATUS_OPTIONS)]
        vals[2] = next_status
        self.td_tree.item(item, values=vals)

    def save_teacher_attendance(self):
        date = self.td_date_entry.get().strip()
        if not date:
            warn("Please enter a date.")
            return
        conn = get_connection()
        for item in self.td_tree.get_children():
            tid, name, status = self.td_tree.item(item)["values"]
            conn.execute(
                """INSERT INTO teacher_attendance (teacher_id, date, status) VALUES (?, ?, ?)
                   ON CONFLICT(teacher_id, date) DO UPDATE SET status=excluded.status""",
                (tid, date, status),
            )
        conn.commit()
        conn.close()
        info("Attendance saved.")

    # ---------------- Teacher Monthly Report ----------------
    def build_teacher_report(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))
        now = datetime.now()

        ttk.Label(top, text="Month (1-12):").pack(side="left")
        self.tr_month_entry = ttk.Entry(top, width=6)
        self.tr_month_entry.insert(0, str(now.month))
        self.tr_month_entry.pack(side="left", padx=6)

        ttk.Label(top, text="Year:").pack(side="left", padx=(10, 6))
        self.tr_year_entry = ttk.Entry(top, width=8)
        self.tr_year_entry.insert(0, str(now.year))
        self.tr_year_entry.pack(side="left")

        ttk.Button(top, text="Generate Report", style="Accent.TButton",
                   command=self.generate_teacher_report).pack(side="left", padx=10)

        columns = ("id", "name", "present", "absent", "leave", "total")
        self.tr_tree = ttk.Treeview(tab, columns=columns, show="headings", height=16)
        for c, h, w in zip(columns, ["ID", "Name", "Present", "Absent", "Leave", "Total Marked"],
                            [40, 200, 80, 80, 80, 100]):
            self.tr_tree.heading(c, text=h)
            self.tr_tree.column(c, width=w, anchor="w")
        self.tr_tree.pack(fill="both", expand=True)

    def generate_teacher_report(self):
        month = self.tr_month_entry.get().strip().zfill(2)
        year = self.tr_year_entry.get().strip()
        prefix = f"{year}-{month}"

        conn = get_connection()
        teachers = conn.execute("SELECT id, name FROM teachers WHERE status='Active'").fetchall()

        for row in self.tr_tree.get_children():
            self.tr_tree.delete(row)

        for t in teachers:
            records = conn.execute(
                "SELECT status FROM teacher_attendance WHERE teacher_id=? AND date LIKE ?",
                (t["id"], f"{prefix}%"),
            ).fetchall()
            present = sum(1 for r in records if r["status"] == "Present")
            absent = sum(1 for r in records if r["status"] == "Absent")
            leave = sum(1 for r in records if r["status"] == "Leave")
            total = len(records)
            if total > 0:
                self.tr_tree.insert("", "end", values=(t["id"], t["name"], present, absent, leave, total))
        conn.close()

    def refresh(self):
        pass
