"""
pages/exams.py
Examination: Monthly Test / Mid-Term / Final-Term.
Marks Management: Enter Marks, Edit Marks, Subject-wise / Class-wise Marks.
"""

import tkinter as tk
from tkinter import ttk

from database import get_connection
from ui_helpers import today_str, info, warn, error, confirm_delete

EXAM_TYPES = ["Monthly Test", "Mid-Term", "Final-Term"]


class ExamForm(tk.Toplevel):
    def __init__(self, master, on_saved, exam_id=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.exam_id = exam_id
        self.title("Edit Exam" if exam_id else "Add Exam")
        self.geometry("380x300")
        self.transient(master)
        self.grab_set()

        form = ttk.Frame(self, padding=20)
        form.pack(fill="both", expand=True)

        conn = get_connection()
        classes = conn.execute("SELECT id, class_name, section FROM classes").fetchall()
        conn.close()
        self.class_map = {f"{c['class_name']} - {c['section'] or ''}".strip(" -"): c["id"] for c in classes}

        ttk.Label(form, text="Exam Name").grid(row=0, column=0, sticky="w", pady=6)
        self.name_entry = ttk.Entry(form, width=25)
        self.name_entry.grid(row=0, column=1, pady=6)

        ttk.Label(form, text="Exam Type").grid(row=1, column=0, sticky="w", pady=6)
        self.type_combo = ttk.Combobox(form, values=EXAM_TYPES, width=22, state="readonly")
        self.type_combo.grid(row=1, column=1, pady=6)

        ttk.Label(form, text="Class").grid(row=2, column=0, sticky="w", pady=6)
        self.class_combo = ttk.Combobox(form, values=list(self.class_map.keys()), width=22, state="readonly")
        self.class_combo.grid(row=2, column=1, pady=6)

        ttk.Label(form, text="Exam Date (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", pady=6)
        self.date_entry = ttk.Entry(form, width=25)
        self.date_entry.insert(0, today_str())
        self.date_entry.grid(row=3, column=1, pady=6)

        btn_row = ttk.Frame(form)
        btn_row.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="left", padx=6)

        if exam_id:
            self.load_existing()

    def load_existing(self):
        conn = get_connection()
        e = conn.execute("SELECT * FROM exams WHERE id=?", (self.exam_id,)).fetchone()
        conn.close()
        if not e:
            return
        self.name_entry.insert(0, e["exam_name"] or "")
        self.type_combo.set(e["exam_type"] or "")
        for name, cid in self.class_map.items():
            if cid == e["class_id"]:
                self.class_combo.set(name)
                break
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, e["exam_date"] or "")

    def save(self):
        name = self.name_entry.get().strip()
        if not name:
            warn("Exam name is required.")
            return
        class_id = self.class_map.get(self.class_combo.get())

        data = dict(
            exam_name=name,
            exam_type=self.type_combo.get(),
            class_id=class_id,
            exam_date=self.date_entry.get().strip(),
        )
        conn = get_connection()
        try:
            if self.exam_id:
                fields_sql = ", ".join([f"{k}=?" for k in data])
                conn.execute(f"UPDATE exams SET {fields_sql} WHERE id=?", list(data.values()) + [self.exam_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                conn.execute(f"INSERT INTO exams ({cols}) VALUES ({placeholders})", list(data.values()))
            conn.commit()
        except Exception as e:
            error(f"Could not save exam: {e}")
            conn.close()
            return
        conn.close()
        info("Exam saved successfully.")
        self.on_saved()
        self.destroy()


class ExamsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Examinations & Marks", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        notebook = ttk.Notebook(card)
        notebook.pack(fill="both", expand=True)

        self.exams_tab = ttk.Frame(notebook, padding=15)
        self.marks_tab = ttk.Frame(notebook, padding=15)
        notebook.add(self.exams_tab, text="Exams")
        notebook.add(self.marks_tab, text="Marks Entry")

        self.build_exams_tab(self.exams_tab)
        self.build_marks_tab(self.marks_tab)

    # ---------------- Exams tab ----------------
    def build_exams_tab(self, tab):
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="+ Add Exam", style="Accent.TButton", command=self.add_exam).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self.edit_exam).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete", style="Danger.TButton", command=self.delete_exam).pack(side="left", padx=6)

        columns = ("id", "name", "type", "class_name", "date")
        headers = ["ID", "Exam Name", "Type", "Class", "Date"]
        widths = [40, 160, 110, 130, 100]
        self.exam_tree = ttk.Treeview(tab, columns=columns, show="headings", height=14)
        for c, h, w in zip(columns, headers, widths):
            self.exam_tree.heading(c, text=h)
            self.exam_tree.column(c, width=w, anchor="w")
        self.exam_tree.pack(fill="both", expand=True)

        self.refresh_exam_list()

    def refresh_exam_list(self):
        for row in self.exam_tree.get_children():
            self.exam_tree.delete(row)
        conn = get_connection()
        rows = conn.execute(
            """SELECT e.id, e.exam_name, e.exam_type, c.class_name, e.exam_date
               FROM exams e LEFT JOIN classes c ON c.id = e.class_id
               ORDER BY e.id DESC"""
        ).fetchall()
        conn.close()
        for r in rows:
            self.exam_tree.insert("", "end", values=tuple(r))
        self.reload_marks_exam_dropdown()

    def get_selected_exam_id(self):
        sel = self.exam_tree.selection()
        if not sel:
            warn("Please select an exam first.")
            return None
        return self.exam_tree.item(sel[0])["values"][0]

    def add_exam(self):
        ExamForm(self, on_saved=self.refresh_exam_list)

    def edit_exam(self):
        eid = self.get_selected_exam_id()
        if eid:
            ExamForm(self, on_saved=self.refresh_exam_list, exam_id=eid)

    def delete_exam(self):
        eid = self.get_selected_exam_id()
        if not eid:
            return
        if confirm_delete("this exam (and its marks)"):
            conn = get_connection()
            conn.execute("DELETE FROM exams WHERE id=?", (eid,))
            conn.commit()
            conn.close()
            self.refresh_exam_list()
            info("Exam deleted.")

    # ---------------- Marks tab ----------------
    def build_marks_tab(self, tab):
        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="Exam:").pack(side="left")
        self.marks_exam_combo = ttk.Combobox(top, width=28, state="readonly")
        self.marks_exam_combo.pack(side="left", padx=6)
        self.marks_exam_combo.bind("<<ComboboxSelected>>", lambda e: self.reload_marks_subject_dropdown())

        ttk.Label(top, text="Subject:").pack(side="left", padx=(20, 6))
        self.marks_subject_combo = ttk.Combobox(top, width=22, state="readonly")
        self.marks_subject_combo.pack(side="left")

        ttk.Button(top, text="Load Students", style="Accent.TButton",
                   command=self.load_students_for_marks).pack(side="left", padx=10)
        ttk.Button(top, text="Save Marks", command=self.save_marks).pack(side="left")

        columns = ("id", "name", "obtained", "total")
        self.marks_tree = ttk.Treeview(tab, columns=columns, show="headings", height=16)
        for c, h, w in zip(columns, ["Student ID", "Name", "Marks Obtained", "Total Marks"], [80, 200, 120, 100]):
            self.marks_tree.heading(c, text=h)
            self.marks_tree.column(c, width=w, anchor="w")
        self.marks_tree.pack(fill="both", expand=True)
        self.marks_tree.bind("<Double-1>", self.edit_marks_cell)

        ttk.Label(tab, text="Tip: double-click a row to enter marks obtained / total marks").pack(
            anchor="w", pady=(6, 0)
        )

        self.exam_class_map = {}
        self.subject_map = {}
        self.reload_marks_exam_dropdown()

    def reload_marks_exam_dropdown(self):
        conn = get_connection()
        exams = conn.execute(
            """SELECT e.id, e.exam_name, e.exam_type, e.class_id, c.class_name
               FROM exams e LEFT JOIN classes c ON c.id = e.class_id"""
        ).fetchall()
        conn.close()
        self.exam_display_map = {
            f"{e['exam_name']} ({e['exam_type']}) - {e['class_name']}": (e["id"], e["class_id"]) for e in exams
        }
        if hasattr(self, "marks_exam_combo"):
            self.marks_exam_combo["values"] = list(self.exam_display_map.keys())

    def reload_marks_subject_dropdown(self):
        exam_display = self.marks_exam_combo.get()
        info_tuple = self.exam_display_map.get(exam_display)
        if not info_tuple:
            return
        _, class_id = info_tuple
        conn = get_connection()
        subjects = conn.execute("SELECT id, subject_name FROM subjects WHERE class_id=?", (class_id,)).fetchall()
        conn.close()
        self.subject_map = {s["subject_name"]: s["id"] for s in subjects}
        self.marks_subject_combo["values"] = list(self.subject_map.keys())

    def load_students_for_marks(self):
        exam_display = self.marks_exam_combo.get()
        subject_display = self.marks_subject_combo.get()
        if not exam_display or not subject_display:
            warn("Please select both an exam and a subject.")
            return
        exam_id, class_id = self.exam_display_map[exam_display]
        subject_id = self.subject_map[subject_display]

        conn = get_connection()
        students = conn.execute(
            "SELECT id, name FROM students WHERE class_id=? AND status='Active'", (class_id,)
        ).fetchall()
        existing = {
            r["student_id"]: (r["marks_obtained"], r["total_marks"])
            for r in conn.execute(
                "SELECT student_id, marks_obtained, total_marks FROM marks WHERE exam_id=? AND subject_id=?",
                (exam_id, subject_id),
            ).fetchall()
        }
        conn.close()

        for row in self.marks_tree.get_children():
            self.marks_tree.delete(row)
        for s in students:
            obtained, total = existing.get(s["id"], (0, 100))
            self.marks_tree.insert("", "end", values=(s["id"], s["name"], obtained, total))

    def edit_marks_cell(self, event):
        sel = self.marks_tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = list(self.marks_tree.item(item)["values"])

        popup = tk.Toplevel(self)
        popup.title(f"Marks for {vals[1]}")
        popup.geometry("260x150")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Marks Obtained:").pack(pady=(15, 4))
        obtained_entry = ttk.Entry(popup)
        obtained_entry.insert(0, str(vals[2]))
        obtained_entry.pack()

        ttk.Label(popup, text="Total Marks:").pack(pady=(10, 4))
        total_entry = ttk.Entry(popup)
        total_entry.insert(0, str(vals[3]))
        total_entry.pack()

        def apply():
            try:
                obtained = float(obtained_entry.get())
                total = float(total_entry.get())
            except ValueError:
                warn("Please enter valid numbers.")
                return
            vals[2] = obtained
            vals[3] = total
            self.marks_tree.item(item, values=vals)
            popup.destroy()

        ttk.Button(popup, text="OK", style="Accent.TButton", command=apply).pack(pady=15)

    def save_marks(self):
        exam_display = self.marks_exam_combo.get()
        subject_display = self.marks_subject_combo.get()
        if not exam_display or not subject_display:
            warn("Please select both an exam and a subject.")
            return
        exam_id, _ = self.exam_display_map[exam_display]
        subject_id = self.subject_map[subject_display]

        conn = get_connection()
        for item in self.marks_tree.get_children():
            sid, name, obtained, total = self.marks_tree.item(item)["values"]
            conn.execute(
                """INSERT INTO marks (exam_id, student_id, subject_id, marks_obtained, total_marks)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(exam_id, student_id, subject_id)
                   DO UPDATE SET marks_obtained=excluded.marks_obtained, total_marks=excluded.total_marks""",
                (exam_id, sid, subject_id, obtained, total),
            )
        conn.commit()
        conn.close()
        info("Marks saved.")

    def refresh(self):
        self.refresh_exam_list()
