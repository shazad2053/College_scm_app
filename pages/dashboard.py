"""
pages/dashboard.py
Dashboard: Total Students, Teachers, Classes, Today's Attendance,
Pending Fee, Fee Collected (Current Month), Upcoming Exams, Recent Activities.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from database import get_connection
from ui_helpers import make_stat_card, today_str, COLOR_BG, FONT_SUBTITLE


class DashboardPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for widget in self.winfo_children():
            widget.destroy()

        ttk.Label(self, text="Dashboard", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        conn = get_connection()
        cur = conn.cursor()

        total_students = cur.execute("SELECT COUNT(*) c FROM students WHERE status='Active'").fetchone()["c"]
        total_teachers = cur.execute("SELECT COUNT(*) c FROM teachers WHERE status='Active'").fetchone()["c"]
        total_classes = cur.execute("SELECT COUNT(*) c FROM classes").fetchone()["c"]

        today = today_str()
        today_present = cur.execute(
            "SELECT COUNT(*) c FROM student_attendance WHERE date=? AND status='Present'", (today,)
        ).fetchone()["c"]
        today_marked = cur.execute(
            "SELECT COUNT(*) c FROM student_attendance WHERE date=?", (today,)
        ).fetchone()["c"]
        attendance_display = f"{today_present}/{today_marked}" if today_marked else "Not marked"

        month = datetime.now().strftime("%m")
        year = datetime.now().strftime("%Y")
        fee_collected = cur.execute(
            "SELECT COALESCE(SUM(total_paid),0) s FROM fee_collection WHERE month=? AND year=?",
            (month, year),
        ).fetchone()["s"]

        pending_fee = cur.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM challans WHERE status='Unpaid'"
        ).fetchone()["s"]

        upcoming_exams = cur.execute(
            "SELECT COUNT(*) c FROM exams WHERE exam_date >= ?", (today,)
        ).fetchone()["c"]

        conn.close()

        grid = ttk.Frame(self, style="TFrame")
        grid.pack(fill="x")
        for i in range(4):
            grid.columnconfigure(i, weight=1)

        make_stat_card(grid, "Total Students", total_students, 0, 0)
        make_stat_card(grid, "Total Teachers", total_teachers, 0, 1)
        make_stat_card(grid, "Total Classes", total_classes, 0, 2)
        make_stat_card(grid, "Today's Attendance", attendance_display, 0, 3)

        make_stat_card(grid, "Pending Fee (Rs.)", f"{pending_fee:,.0f}", 1, 0)
        make_stat_card(grid, "Fee Collected - This Month (Rs.)", f"{fee_collected:,.0f}", 1, 1)
        make_stat_card(grid, "Upcoming Exams", upcoming_exams, 1, 2)
        make_stat_card(grid, "Today's Date", today, 1, 3)

        # Recent activity feed (recent admissions + recent fee payments)
        ttk.Label(self, text="Recent Activities", style="Subtitle.TLabel").pack(anchor="w", pady=(25, 8))

        activity_frame = ttk.Frame(self, style="Card.TFrame", padding=12)
        activity_frame.pack(fill="both", expand=True)

        conn = get_connection()
        cur = conn.cursor()
        recent_students = cur.execute(
            "SELECT name, admission_date FROM students ORDER BY id DESC LIMIT 5"
        ).fetchall()
        recent_fees = cur.execute(
            """SELECT s.name, f.total_paid, f.date FROM fee_collection f
               JOIN students s ON s.id = f.student_id
               ORDER BY f.id DESC LIMIT 5"""
        ).fetchall()
        conn.close()

        row = 0
        if recent_students:
            ttk.Label(activity_frame, text="Recent Admissions:", style="Card.TLabel",
                      font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w")
            row += 1
            for s in recent_students:
                ttk.Label(activity_frame,
                          text=f"  • {s['name']} admitted on {s['admission_date'] or '-'}",
                          style="Card.TLabel").grid(row=row, column=0, sticky="w")
                row += 1

        if recent_fees:
            row += 1
            ttk.Label(activity_frame, text="Recent Fee Payments:", style="Card.TLabel",
                      font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w")
            row += 1
            for f in recent_fees:
                ttk.Label(activity_frame,
                          text=f"  • {f['name']} paid Rs. {f['total_paid']:,.0f} on {f['date']}",
                          style="Card.TLabel").grid(row=row, column=0, sticky="w")
                row += 1

        if not recent_students and not recent_fees:
            ttk.Label(activity_frame, text="No recent activity yet.", style="Muted.TLabel").grid(
                row=0, column=0, sticky="w"
            )

    def refresh(self):
        self.build()
