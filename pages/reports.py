"""
pages/reports.py
Reports: Student, Attendance, Fee, Examination, Teacher reports.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from database import get_connection
from ui_helpers import warn


class ReportsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Reports", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        notebook = ttk.Notebook(card)
        notebook.pack(fill="both", expand=True)

        self.tab_students = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.tab_attendance = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.tab_fee = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.tab_exam = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.tab_teacher = ttk.Frame(notebook, padding=15, style="Card.TFrame")

        notebook.add(self.tab_students, text="Student Reports")
        notebook.add(self.tab_attendance, text="Attendance Reports")
        notebook.add(self.tab_fee, text="Fee Reports")
        notebook.add(self.tab_exam, text="Examination Reports")
        notebook.add(self.tab_teacher, text="Teacher Reports")

        self.build_student_reports(self.tab_students)
        self.build_attendance_reports(self.tab_attendance)
        self.build_fee_reports(self.tab_fee)
        self.build_exam_reports(self.tab_exam)
        self.build_teacher_reports(self.tab_teacher)

    # ---------------- Student Reports ----------------
    def build_student_reports(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))

        conn = get_connection()
        classes = conn.execute("SELECT id, class_name, section FROM classes").fetchall()
        conn.close()
        self.rep_class_map = {"All Classes": None}
        self.rep_class_map.update({f"{c['class_name']} - {c['section'] or ''}".strip(" -"): c["id"] for c in classes})

        ttk.Label(top, text="Filter by Class:").pack(side="left")
        self.rep_class_combo = ttk.Combobox(top, values=list(self.rep_class_map.keys()), width=22, state="readonly")
        self.rep_class_combo.set("All Classes")
        self.rep_class_combo.pack(side="left", padx=6)

        ttk.Button(top, text="Student List", command=self.show_student_list).pack(side="left", padx=6)
        ttk.Button(top, text="Admission Report", command=self.show_admission_report).pack(side="left", padx=6)

        self.student_report_tree = ttk.Treeview(tab, show="headings", height=16)
        self.student_report_tree.pack(fill="both", expand=True)

    def _set_columns(self, tree, columns, headers, widths):
        tree["columns"] = columns
        for c, h, w in zip(columns, headers, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

    def show_student_list(self):
        class_id = self.rep_class_map.get(self.rep_class_combo.get())
        conn = get_connection()
        query = """SELECT s.id, s.name, s.roll_no, c.class_name, s.section, s.status
                   FROM students s LEFT JOIN classes c ON c.id = s.class_id"""
        params = []
        if class_id:
            query += " WHERE s.class_id=?"
            params = [class_id]
        rows = conn.execute(query, params).fetchall()
        conn.close()

        self._set_columns(self.student_report_tree, ("id", "name", "roll", "class", "section", "status"),
                           ["ID", "Name", "Roll No.", "Class", "Section", "Status"], [40, 180, 80, 120, 70, 80])
        for row in self.student_report_tree.get_children():
            self.student_report_tree.delete(row)
        for r in rows:
            self.student_report_tree.insert("", "end", values=tuple(r))

    def show_admission_report(self):
        class_id = self.rep_class_map.get(self.rep_class_combo.get())
        conn = get_connection()
        query = """SELECT s.name, s.admission_date, c.class_name, s.section
                   FROM students s LEFT JOIN classes c ON c.id = s.class_id"""
        params = []
        if class_id:
            query += " WHERE s.class_id=?"
            params = [class_id]
        query += " ORDER BY s.admission_date DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()

        self._set_columns(self.student_report_tree, ("name", "admission_date", "class", "section"),
                           ["Name", "Admission Date", "Class", "Section"], [180, 120, 120, 80])
        for row in self.student_report_tree.get_children():
            self.student_report_tree.delete(row)
        for r in rows:
            self.student_report_tree.insert("", "end", values=tuple(r))

    # ---------------- Attendance Reports ----------------
    def build_attendance_reports(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))
        now = datetime.now()

        ttk.Label(top, text="Date (daily) or Month/Year:").pack(side="left")
        self.att_date_entry = ttk.Entry(top, width=14)
        self.att_date_entry.insert(0, now.strftime("%Y-%m-%d"))
        self.att_date_entry.pack(side="left", padx=6)

        ttk.Button(top, text="Daily Report", command=self.show_daily_attendance_report).pack(side="left", padx=6)

        ttk.Label(top, text="Month:").pack(side="left", padx=(20, 4))
        self.att_month_entry = ttk.Entry(top, width=6)
        self.att_month_entry.insert(0, str(now.month))
        self.att_month_entry.pack(side="left")

        ttk.Label(top, text="Year:").pack(side="left", padx=(10, 4))
        self.att_year_entry = ttk.Entry(top, width=8)
        self.att_year_entry.insert(0, str(now.year))
        self.att_year_entry.pack(side="left")

        ttk.Button(top, text="Monthly Report", command=self.show_monthly_attendance_report).pack(side="left", padx=6)

        self.att_tree = ttk.Treeview(tab, show="headings", height=16)
        self.att_tree.pack(fill="both", expand=True)

    def show_daily_attendance_report(self):
        date = self.att_date_entry.get().strip()
        conn = get_connection()
        rows = conn.execute(
            """SELECT s.name, c.class_name, a.status FROM student_attendance a
               JOIN students s ON s.id = a.student_id
               LEFT JOIN classes c ON c.id = s.class_id
               WHERE a.date=?""",
            (date,),
        ).fetchall()
        conn.close()
        self._set_columns(self.att_tree, ("name", "class", "status"), ["Name", "Class", "Status"], [200, 130, 100])
        for row in self.att_tree.get_children():
            self.att_tree.delete(row)
        for r in rows:
            self.att_tree.insert("", "end", values=tuple(r))

    def show_monthly_attendance_report(self):
        month = self.att_month_entry.get().strip().zfill(2)
        year = self.att_year_entry.get().strip()
        prefix = f"{year}-{month}"
        conn = get_connection()
        students = conn.execute("SELECT id, name FROM students WHERE status='Active'").fetchall()
        self._set_columns(self.att_tree, ("name", "present", "absent", "leave"),
                           ["Name", "Present", "Absent", "Leave"], [200, 80, 80, 80])
        for row in self.att_tree.get_children():
            self.att_tree.delete(row)
        for s in students:
            records = conn.execute(
                "SELECT status FROM student_attendance WHERE student_id=? AND date LIKE ?",
                (s["id"], f"{prefix}%"),
            ).fetchall()
            if not records:
                continue
            present = sum(1 for r in records if r["status"] == "Present")
            absent = sum(1 for r in records if r["status"] == "Absent")
            leave = sum(1 for r in records if r["status"] == "Leave")
            self.att_tree.insert("", "end", values=(s["name"], present, absent, leave))
        conn.close()

    # ---------------- Fee Reports ----------------
    def build_fee_reports(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))
        ttk.Button(top, text="Fee Collection Report", command=self.show_fee_collection_report).pack(side="left")
        ttk.Button(top, text="Pending Fee Report", command=self.show_pending_fee_report).pack(side="left", padx=6)
        ttk.Button(top, text="Defaulters List", command=self.show_defaulters_list).pack(side="left", padx=6)

        self.fee_report_tree = ttk.Treeview(tab, show="headings", height=16)
        self.fee_report_tree.pack(fill="both", expand=True)

    def show_fee_collection_report(self):
        conn = get_connection()
        rows = conn.execute(
            """SELECT s.name, f.month, f.year, f.total_paid, f.date
               FROM fee_collection f JOIN students s ON s.id = f.student_id
               ORDER BY f.date DESC"""
        ).fetchall()
        conn.close()
        self._set_columns(self.fee_report_tree, ("name", "month", "year", "paid", "date"),
                           ["Student", "Month", "Year", "Total Paid", "Date"], [180, 60, 60, 90, 100])
        for row in self.fee_report_tree.get_children():
            self.fee_report_tree.delete(row)
        for r in rows:
            self.fee_report_tree.insert("", "end", values=tuple(r))

    def show_pending_fee_report(self):
        conn = get_connection()
        rows = conn.execute(
            """SELECT s.name, c.month, c.year, c.amount, c.due_date
               FROM challans c JOIN students s ON s.id = c.student_id
               WHERE c.status='Unpaid' ORDER BY c.due_date"""
        ).fetchall()
        conn.close()
        self._set_columns(self.fee_report_tree, ("name", "month", "year", "amount", "due"),
                           ["Student", "Month", "Year", "Amount", "Due Date"], [180, 60, 60, 80, 100])
        for row in self.fee_report_tree.get_children():
            self.fee_report_tree.delete(row)
        for r in rows:
            self.fee_report_tree.insert("", "end", values=tuple(r))

    def show_defaulters_list(self):
        conn = get_connection()
        rows = conn.execute(
            """SELECT s.name, COUNT(*) unpaid_count, SUM(c.amount) total_due
               FROM challans c JOIN students s ON s.id = c.student_id
               WHERE c.status='Unpaid'
               GROUP BY c.student_id ORDER BY total_due DESC"""
        ).fetchall()
        conn.close()
        self._set_columns(self.fee_report_tree, ("name", "count", "total_due"),
                           ["Student", "Unpaid Challans", "Total Due"], [200, 110, 100])
        for row in self.fee_report_tree.get_children():
            self.fee_report_tree.delete(row)
        for r in rows:
            self.fee_report_tree.insert("", "end", values=tuple(r))

    # ---------------- Examination Reports ----------------
    def build_exam_reports(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))

        conn = get_connection()
        exams = conn.execute(
            """SELECT e.id, e.exam_name, e.exam_type, c.class_name
               FROM exams e LEFT JOIN classes c ON c.id = e.class_id"""
        ).fetchall()
        conn.close()
        self.exam_report_map = {f"{e['exam_name']} ({e['exam_type']}) - {e['class_name']}": e["id"] for e in exams}

        ttk.Label(top, text="Exam:").pack(side="left")
        self.exam_report_combo = ttk.Combobox(top, values=list(self.exam_report_map.keys()), width=32, state="readonly")
        self.exam_report_combo.pack(side="left", padx=6)
        ttk.Button(top, text="Show Results", command=self.show_exam_report).pack(side="left", padx=6)

        self.exam_report_tree = ttk.Treeview(tab, show="headings", height=16)
        self.exam_report_tree.pack(fill="both", expand=True)

    def show_exam_report(self):
        exam_display = self.exam_report_combo.get()
        exam_id = self.exam_report_map.get(exam_display)
        if not exam_id:
            warn("Please select an exam.")
            return
        conn = get_connection()
        students = conn.execute(
            """SELECT DISTINCT s.id, s.name FROM students s
               JOIN marks m ON m.student_id = s.id WHERE m.exam_id=?""",
            (exam_id,),
        ).fetchall()

        self._set_columns(self.exam_report_tree, ("name", "obtained", "total", "percentage"),
                           ["Name", "Obtained", "Total", "Percentage"], [200, 90, 90, 90])
        for row in self.exam_report_tree.get_children():
            self.exam_report_tree.delete(row)

        results = []
        for s in students:
            rows = conn.execute(
                "SELECT marks_obtained, total_marks FROM marks WHERE exam_id=? AND student_id=?",
                (exam_id, s["id"]),
            ).fetchall()
            obtained = sum(r["marks_obtained"] for r in rows)
            total = sum(r["total_marks"] for r in rows)
            pct = (obtained / total * 100) if total else 0
            results.append((s["name"], obtained, total, f"{pct:.2f}%"))
        conn.close()

        results.sort(key=lambda r: r[1], reverse=True)
        for r in results:
            self.exam_report_tree.insert("", "end", values=r)

    # ---------------- Teacher Reports ----------------
    def build_teacher_reports(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))
        ttk.Button(top, text="Teacher List", command=self.show_teacher_list).pack(side="left")
        ttk.Button(top, text="Attendance Report (This Month)", command=self.show_teacher_attendance_report).pack(
            side="left", padx=6
        )

        self.teacher_report_tree = ttk.Treeview(tab, show="headings", height=16)
        self.teacher_report_tree.pack(fill="both", expand=True)

    def show_teacher_list(self):
        conn = get_connection()
        rows = conn.execute("SELECT name, subject, qualification, mobile, status FROM teachers").fetchall()
        conn.close()
        self._set_columns(self.teacher_report_tree, ("name", "subject", "qualification", "mobile", "status"),
                           ["Name", "Subject", "Qualification", "Mobile", "Status"], [160, 110, 130, 100, 80])
        for row in self.teacher_report_tree.get_children():
            self.teacher_report_tree.delete(row)
        for r in rows:
            self.teacher_report_tree.insert("", "end", values=tuple(r))

    def show_teacher_attendance_report(self):
        now = datetime.now()
        prefix = now.strftime("%Y-%m")
        conn = get_connection()
        teachers = conn.execute("SELECT id, name FROM teachers WHERE status='Active'").fetchall()
        self._set_columns(self.teacher_report_tree, ("name", "present", "absent", "leave"),
                           ["Name", "Present", "Absent", "Leave"], [180, 80, 80, 80])
        for row in self.teacher_report_tree.get_children():
            self.teacher_report_tree.delete(row)
        for t in teachers:
            records = conn.execute(
                "SELECT status FROM teacher_attendance WHERE teacher_id=? AND date LIKE ?",
                (t["id"], f"{prefix}%"),
            ).fetchall()
            if not records:
                continue
            present = sum(1 for r in records if r["status"] == "Present")
            absent = sum(1 for r in records if r["status"] == "Absent")
            leave = sum(1 for r in records if r["status"] == "Leave")
            self.teacher_report_tree.insert("", "end", values=(t["name"], present, absent, leave))
        conn.close()

    def refresh(self):
        pass
