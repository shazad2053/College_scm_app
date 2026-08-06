"""
pages/teachers.py
Teacher Management: full CRUD.
"""

import tkinter as tk
from tkinter import ttk

from database import get_connection
from ui_helpers import confirm_delete, info, warn, error, today_str

STATUSES = ["Active", "Inactive"]


class TeacherForm(tk.Toplevel):
    def __init__(self, master, on_saved, teacher_id=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.teacher_id = teacher_id
        self.title("Edit Teacher" if teacher_id else "Add Teacher")
        self.geometry("420x480")
        self.transient(master)
        self.grab_set()

        form = ttk.Frame(self, padding=20)
        form.pack(fill="both", expand=True)

        self.fields = {}

        def add_field(label, row, widget_type="entry", values=None):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=6, padx=(0, 10))
            if widget_type == "entry":
                w = ttk.Entry(form, width=28)
            else:
                w = ttk.Combobox(form, values=values, width=25, state="readonly")
            w.grid(row=row, column=1, sticky="w", pady=6)
            self.fields[label] = w
            return w

        add_field("Teacher Code / ID", 0)
        add_field("Name", 1)
        add_field("CNIC", 2)
        add_field("Qualification", 3)
        add_field("Subject", 4)
        add_field("Mobile", 5)
        add_field("Address", 6)
        add_field("Joining Date (YYYY-MM-DD)", 7)
        add_field("Salary", 8)
        add_field("Status", 9, "combo", STATUSES)

        self.fields["Joining Date (YYYY-MM-DD)"].insert(0, today_str())
        self.fields["Status"].set("Active")

        btn_row = ttk.Frame(form)
        btn_row.grid(row=10, column=0, columnspan=2, pady=20)
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="left", padx=6)

        if teacher_id:
            self.load_existing()

    def load_existing(self):
        conn = get_connection()
        t = conn.execute("SELECT * FROM teachers WHERE id=?", (self.teacher_id,)).fetchone()
        conn.close()
        if not t:
            return
        self.fields["Teacher Code / ID"].insert(0, t["teacher_code"] or "")
        self.fields["Name"].insert(0, t["name"] or "")
        self.fields["CNIC"].insert(0, t["cnic"] or "")
        self.fields["Qualification"].insert(0, t["qualification"] or "")
        self.fields["Subject"].insert(0, t["subject"] or "")
        self.fields["Mobile"].insert(0, t["mobile"] or "")
        self.fields["Address"].insert(0, t["address"] or "")
        self.fields["Joining Date (YYYY-MM-DD)"].delete(0, tk.END)
        self.fields["Joining Date (YYYY-MM-DD)"].insert(0, t["joining_date"] or "")
        self.fields["Salary"].insert(0, str(t["salary"] or 0))
        self.fields["Status"].set(t["status"] or "Active")

    def save(self):
        name = self.fields["Name"].get().strip()
        if not name:
            warn("Teacher name is required.")
            return
        try:
            salary = float(self.fields["Salary"].get().strip() or 0)
        except ValueError:
            warn("Salary must be a number.")
            return

        data = dict(
            teacher_code=self.fields["Teacher Code / ID"].get().strip() or None,
            name=name,
            cnic=self.fields["CNIC"].get().strip(),
            qualification=self.fields["Qualification"].get().strip(),
            subject=self.fields["Subject"].get().strip(),
            mobile=self.fields["Mobile"].get().strip(),
            address=self.fields["Address"].get().strip(),
            joining_date=self.fields["Joining Date (YYYY-MM-DD)"].get().strip(),
            salary=salary,
            status=self.fields["Status"].get() or "Active",
        )

        conn = get_connection()
        try:
            if self.teacher_id:
                fields_sql = ", ".join([f"{k}=?" for k in data])
                conn.execute(f"UPDATE teachers SET {fields_sql} WHERE id=?",
                             list(data.values()) + [self.teacher_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                conn.execute(f"INSERT INTO teachers ({cols}) VALUES ({placeholders})", list(data.values()))
            conn.commit()
        except Exception as e:
            error(f"Could not save teacher: {e}")
            conn.close()
            return
        conn.close()

        info("Teacher saved successfully.")
        self.on_saved()
        self.destroy()


class TeachersPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        ttk.Label(self, text="Teacher Management", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="+ Add Teacher", style="Accent.TButton",
                   command=self.add_teacher).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self.edit_teacher).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete", style="Danger.TButton",
                   command=self.delete_teacher).pack(side="left", padx=6)

        ttk.Label(toolbar, text="Search:").pack(side="left", padx=(30, 6))
        self.search_var = tk.StringVar()
        entry = ttk.Entry(toolbar, textvariable=self.search_var, width=25)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        columns = ("id", "code", "name", "subject", "qualification", "mobile", "salary", "status")
        headers = ["ID", "Code", "Name", "Subject", "Qualification", "Mobile", "Salary", "Status"]
        widths = [40, 80, 150, 110, 130, 100, 80, 70]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)
        for c, h, wd in zip(columns, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=wd, anchor="w")
        self.tree.pack(fill="both", expand=True)

        self.refresh_list()

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        query = "SELECT id, teacher_code, name, subject, qualification, mobile, salary, status FROM teachers"
        params = []
        search = self.search_var.get().strip()
        if search:
            query += " WHERE name LIKE ? OR teacher_code LIKE ?"
            params = [f"%{search}%", f"%{search}%"]
        query += " ORDER BY id DESC"
        conn = get_connection()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=tuple(r))

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            warn("Please select a teacher first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def add_teacher(self):
        TeacherForm(self, on_saved=self.refresh_list)

    def edit_teacher(self):
        tid = self.get_selected_id()
        if tid:
            TeacherForm(self, on_saved=self.refresh_list, teacher_id=tid)

    def delete_teacher(self):
        tid = self.get_selected_id()
        if not tid:
            return
        if confirm_delete("this teacher"):
            conn = get_connection()
            conn.execute("DELETE FROM teachers WHERE id=?", (tid,))
            conn.commit()
            conn.close()
            self.refresh_list()
            info("Teacher deleted.")

    def refresh(self):
        self.refresh_list()
