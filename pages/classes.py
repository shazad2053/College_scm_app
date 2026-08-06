"""
pages/classes.py
Class Management: Session, Class, Section, Class Teacher.
"""

import tkinter as tk
from tkinter import ttk

from database import get_connection
from ui_helpers import confirm_delete, info, warn, error

SECTION_OPTIONS = ["Boys", "Girls"]


class ClassForm(tk.Toplevel):
    def __init__(self, master, on_saved, class_id=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.class_id = class_id
        self.title("Edit Class" if class_id else "Add Class")
        self.geometry("380x320")
        self.transient(master)
        self.grab_set()

        form = ttk.Frame(self, padding=20)
        form.pack(fill="both", expand=True)

        conn = get_connection()
        teachers = conn.execute("SELECT id, name FROM teachers WHERE status='Active'").fetchall()
        conn.close()
        self.teacher_map = {t["name"]: t["id"] for t in teachers}

        ttk.Label(form, text="Session").grid(row=0, column=0, sticky="w", pady=6)
        self.session_entry = ttk.Entry(form, width=25)
        self.session_entry.grid(row=0, column=1, pady=6)

        ttk.Label(form, text="Class Name").grid(row=1, column=0, sticky="w", pady=6)
        self.class_entry = ttk.Entry(form, width=25)
        self.class_entry.grid(row=1, column=1, pady=6)

        ttk.Label(form, text="Section").grid(row=2, column=0, sticky="w", pady=6)
        self.section_combo = ttk.Combobox(form, values=SECTION_OPTIONS, width=22, state="readonly")
        self.section_combo.grid(row=2, column=1, pady=6)

        ttk.Label(form, text="Class Teacher").grid(row=3, column=0, sticky="w", pady=6)
        self.teacher_combo = ttk.Combobox(form, values=list(self.teacher_map.keys()), width=22, state="readonly")
        self.teacher_combo.grid(row=3, column=1, pady=6)

        btn_row = ttk.Frame(form)
        btn_row.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="left", padx=6)

        if class_id:
            self.load_existing()

    def load_existing(self):
        conn = get_connection()
        c = conn.execute("SELECT * FROM classes WHERE id=?", (self.class_id,)).fetchone()
        conn.close()
        if not c:
            return
        self.session_entry.insert(0, c["session"] or "")
        self.class_entry.insert(0, c["class_name"] or "")
        self.section_combo.set(c["section"] or "")
        for name, tid in self.teacher_map.items():
            if tid == c["class_teacher_id"]:
                self.teacher_combo.set(name)
                break

    def save(self):
        class_name = self.class_entry.get().strip()
        if not class_name:
            warn("Class name is required.")
            return
        teacher_id = self.teacher_map.get(self.teacher_combo.get())

        data = dict(
            session=self.session_entry.get().strip(),
            class_name=class_name,
            section=self.section_combo.get().strip(),
            class_teacher_id=teacher_id,
        )
        conn = get_connection()
        try:
            if self.class_id:
                fields_sql = ", ".join([f"{k}=?" for k in data])
                conn.execute(f"UPDATE classes SET {fields_sql} WHERE id=?",
                             list(data.values()) + [self.class_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                conn.execute(f"INSERT INTO classes ({cols}) VALUES ({placeholders})", list(data.values()))
            conn.commit()
        except Exception as e:
            error(f"Could not save class: {e}")
            conn.close()
            return
        conn.close()
        info("Class saved successfully.")
        self.on_saved()
        self.destroy()


class ClassesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        ttk.Label(self, text="Class Management", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="+ Add Class", style="Accent.TButton", command=self.add_class).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self.edit_class).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete", style="Danger.TButton", command=self.delete_class).pack(side="left", padx=6)

        columns = ("id", "session", "class_name", "section", "teacher")
        headers = ["ID", "Session", "Class", "Section", "Class Teacher"]
        widths = [40, 100, 150, 100, 160]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)
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
            """SELECT c.id, c.session, c.class_name, c.section, t.name
               FROM classes c LEFT JOIN teachers t ON t.id = c.class_teacher_id
               ORDER BY c.id DESC"""
        ).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=tuple(r))

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            warn("Please select a class first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def add_class(self):
        ClassForm(self, on_saved=self.refresh_list)

    def edit_class(self):
        cid = self.get_selected_id()
        if cid:
            ClassForm(self, on_saved=self.refresh_list, class_id=cid)

    def delete_class(self):
        cid = self.get_selected_id()
        if not cid:
            return
        if confirm_delete("this class"):
            conn = get_connection()
            conn.execute("DELETE FROM classes WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self.refresh_list()
            info("Class deleted.")

    def refresh(self):
        self.refresh_list()
