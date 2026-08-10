"""
pages/subjects.py
Subject Management: Subject Name, Subject Code, Class, Teacher.
"""

import tkinter as tk
from tkinter import ttk

from database import get_connection
from ui_helpers import confirm_delete, info, warn, error


class SubjectForm(tk.Toplevel):
    def __init__(self, master, on_saved, subject_id=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.subject_id = subject_id
        self.title("Edit Subject" if subject_id else "Add Subject")
        self.geometry("380x320")
        self.transient(master)
        self.grab_set()

        form = ttk.Frame(self, padding=20)
        form.pack(fill="both", expand=True)

        conn = get_connection()
        classes = conn.execute("SELECT id, class_name, section FROM classes").fetchall()
        teachers = conn.execute("SELECT id, name FROM teachers WHERE status='Active'").fetchall()
        conn.close()
        self.class_map = {f"{c['class_name']} - {c['section'] or ''}".strip(" -"): c["id"] for c in classes}
        self.teacher_map = {t["name"]: t["id"] for t in teachers}

        ttk.Label(form, text="Subject Name").grid(row=0, column=0, sticky="w", pady=6)
        self.name_entry = ttk.Entry(form, width=25)
        self.name_entry.grid(row=0, column=1, pady=6)

        ttk.Label(form, text="Subject Code").grid(row=1, column=0, sticky="w", pady=6)
        self.code_entry = ttk.Entry(form, width=25)
        self.code_entry.grid(row=1, column=1, pady=6)

        ttk.Label(form, text="Class").grid(row=2, column=0, sticky="w", pady=6)
        self.class_combo = ttk.Combobox(form, values=list(self.class_map.keys()), width=22, state="readonly")
        self.class_combo.grid(row=2, column=1, pady=6)

        ttk.Label(form, text="Teacher").grid(row=3, column=0, sticky="w", pady=6)
        self.teacher_combo = ttk.Combobox(form, values=list(self.teacher_map.keys()), width=22, state="readonly")
        self.teacher_combo.grid(row=3, column=1, pady=6)

        btn_row = ttk.Frame(form)
        btn_row.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="left", padx=6)

        if subject_id:
            self.load_existing()

    def load_existing(self):
        conn = get_connection()
        s = conn.execute("SELECT * FROM subjects WHERE id=?", (self.subject_id,)).fetchone()
        conn.close()
        if not s:
            return
        self.name_entry.insert(0, s["subject_name"] or "")
        self.code_entry.insert(0, s["subject_code"] or "")
        for name, cid in self.class_map.items():
            if cid == s["class_id"]:
                self.class_combo.set(name)
                break
        for name, tid in self.teacher_map.items():
            if tid == s["teacher_id"]:
                self.teacher_combo.set(name)
                break

    def save(self):
        name = self.name_entry.get().strip()
        if not name:
            warn("Subject name is required.")
            return
        class_id = self.class_map.get(self.class_combo.get())
        teacher_id = self.teacher_map.get(self.teacher_combo.get())

        data = dict(
            subject_name=name,
            subject_code=self.code_entry.get().strip(),
            class_id=class_id,
            teacher_id=teacher_id,
        )
        conn = get_connection()
        try:
            if self.subject_id:
                fields_sql = ", ".join([f"{k}=?" for k in data])
                conn.execute(f"UPDATE subjects SET {fields_sql} WHERE id=?",
                             list(data.values()) + [self.subject_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                conn.execute(f"INSERT INTO subjects ({cols}) VALUES ({placeholders})", list(data.values()))
            conn.commit()
        except Exception as e:
            error(f"Could not save subject: {e}")
            conn.close()
            return
        conn.close()
        info("Subject saved successfully.")
        self.on_saved()
        self.destroy()


class SubjectsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Subject Management", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        toolbar = ttk.Frame(card, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="+ Add Subject", style="Accent.TButton", command=self.add_subject).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self.edit_subject).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete", style="Danger.TButton", command=self.delete_subject).pack(side="left", padx=6)

        columns = ("id", "name", "code", "class_name", "teacher")
        headers = ["ID", "Subject Name", "Code", "Class", "Teacher"]
        widths = [40, 160, 80, 130, 160]
        self.tree = ttk.Treeview(card, columns=columns, show="headings", height=18)
        for c, h, wd in zip(columns, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=wd, anchor="w")
        self.tree.pack(fill="both", expand=True)

        self.refresh_list()

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute(
            """SELECT sub.id, sub.subject_name, sub.subject_code, c.class_name, t.name
               FROM subjects sub
               LEFT JOIN classes c ON c.id = sub.class_id
               LEFT JOIN teachers t ON t.id = sub.teacher_id
               ORDER BY sub.id DESC"""
        ).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=tuple(r))

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            warn("Please select a subject first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def add_subject(self):
        SubjectForm(self, on_saved=self.refresh_list)

    def edit_subject(self):
        sid = self.get_selected_id()
        if sid:
            SubjectForm(self, on_saved=self.refresh_list, subject_id=sid)

    def delete_subject(self):
        sid = self.get_selected_id()
        if not sid:
            return
        if confirm_delete("this subject"):
            conn = get_connection()
            conn.execute("DELETE FROM subjects WHERE id=?", (sid,))
            conn.commit()
            conn.close()
            self.refresh_list()
            info("Subject deleted.")

    def refresh(self):
        self.refresh_list()
