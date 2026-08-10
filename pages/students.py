"""
pages/students.py
Student Management: List, Add, Edit, Delete, Profile view.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import shutil
import os

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    Image = None
    ImageTk = None
    _HAS_PIL = False

from database import get_connection
from ui_helpers import (
    confirm_delete, info, warn, error, today_str, ScrollableFrame
)

GENDERS = ["Male", "Female", "Other"]
STATUSES = ["Active", "Inactive"]
SECTION_OPTIONS = ["Boys", "Girls"]


class StudentForm(tk.Toplevel):
    """Add / Edit student dialog."""

    def __init__(self, master, on_saved, student_id=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.student_id = student_id
        self.title("Edit Student" if student_id else "Add Student")
        self.geometry("560x640")
        self.resizable(False, True)
        self.photo_path_var = tk.StringVar(value="")

        self.transient(master)
        self.grab_set()

        self.geometry("640x720")
        wrapper = ScrollableFrame(self)
        wrapper.pack(fill="both", expand=True)
        card = ttk.Frame(wrapper.scrollable_frame, style="Card.TFrame", padding=24)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(card, text="Add Student" if not student_id else "Edit Student",
                  style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Separator(card, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        self.fields = {}

        def add_field(label, row, widget_type="entry", values=None):
            ttk.Label(card, text=label, style="Form.TLabel").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 16))
            if widget_type == "entry":
                w = ttk.Entry(card, width=36, style="Form.TEntry")
            elif widget_type == "combo":
                w = ttk.Combobox(card, values=values, width=34, state="readonly", style="Form.TCombobox")
            w.grid(row=row, column=1, sticky="w", pady=6)
            self.fields[label] = w
            return w

        add_field("Student Code / ID", 0)
        add_field("Roll / Registration No.", 1)
        add_field("Student Name", 2)
        add_field("Father Name", 3)
        add_field("CNIC / B-Form", 4)
        add_field("Gender", 5, "combo", GENDERS)
        add_field("Date of Birth (YYYY-MM-DD)", 6)
        add_field("Mobile", 7)
        add_field("Address", 8)
        add_field("Admission Date (YYYY-MM-DD)", 9)

        # Class dropdown (populated from DB)
        conn = get_connection()
        classes = conn.execute("SELECT id, class_name, section FROM classes").fetchall()
        conn.close()
        self.class_map = {f"{c['class_name']} - {c['section'] or ''}".strip(" -"): c["id"] for c in classes}
        class_names = list(self.class_map.keys())
        add_field("Class", 11, "combo", class_names)

        add_field("Section", 12, "combo", SECTION_OPTIONS)
        add_field("Session", 13)
        add_field("Status", 14, "combo", STATUSES)

        # Photo picker
        ttk.Label(card, text="Student Photo", style="Form.TLabel").grid(row=15, column=0, sticky="w", pady=6, padx=(0, 16))
        photo_row = ttk.Frame(card, style="Card.TFrame")
        photo_row.grid(row=15, column=1, sticky="w")
        ttk.Entry(photo_row, textvariable=self.photo_path_var, width=26, state="readonly", style="Form.TEntry").pack(side="left")
        ttk.Button(photo_row, text="Browse", style="Secondary.TButton", command=self.pick_photo).pack(side="left", padx=6)

        self.fields["Admission Date (YYYY-MM-DD)"].insert(0, today_str())
        self.fields["Status"].set("Active")

        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.grid(row=16, column=0, columnspan=2, pady=24)
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="left", padx=6)

        if student_id:
            self.load_existing()

    def pick_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")]
        )
        if path:
            self.photo_path_var.set(os.path.basename(path))
            self._source_photo = path

    def load_existing(self):
        conn = get_connection()
        s = conn.execute("SELECT * FROM students WHERE id=?", (self.student_id,)).fetchone()
        conn.close()
        if not s:
            return
        self.fields["Student Code / ID"].insert(0, s["student_code"] or "")
        self.fields["Roll / Registration No."].insert(0, s["roll_no"] or s["reg_no"] or "")
        self.fields["Student Name"].insert(0, s["name"] or "")
        self.fields["Father Name"].insert(0, s["father_name"] or "")
        self.fields["CNIC / B-Form"].insert(0, s["cnic_bform"] or "")
        self.fields["Gender"].set(s["gender"] or "")
        self.fields["Date of Birth (YYYY-MM-DD)"].insert(0, s["dob"] or "")
        self.fields["Mobile"].insert(0, s["mobile"] or "")
        self.fields["Address"].insert(0, s["address"] or "")
        self.fields["Admission Date (YYYY-MM-DD)"].delete(0, tk.END)
        self.fields["Admission Date (YYYY-MM-DD)"].insert(0, s["admission_date"] or "")
        # Reverse-map class_id to display name
        for name, cid in self.class_map.items():
            if cid == s["class_id"]:
                self.fields["Class"].set(name)
                break
        self.fields["Section"].insert(0, s["section"] or "")
        self.fields["Session"].insert(0, s["session"] or "")
        self.fields["Status"].set(s["status"] or "Active")
        if s["photo_path"]:
            self.photo_path_var.set(os.path.basename(s["photo_path"]))

    def save(self):
        name = self.fields["Student Name"].get().strip()
        if not name:
            warn("Student Name is required.")
            return

        class_display = self.fields["Class"].get()
        class_id = self.class_map.get(class_display)

        photo_path = None
        if hasattr(self, "_source_photo"):
            photos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "student_photos")
            os.makedirs(photos_dir, exist_ok=True)
            dest = os.path.join(photos_dir, os.path.basename(self._source_photo))
            try:
                shutil.copy(self._source_photo, dest)
                photo_path = dest
            except Exception:
                photo_path = None

        data = dict(
            student_code=self.fields["Student Code / ID"].get().strip() or None,
            roll_no=self.fields["Roll / Registration No."].get().strip(),
            reg_no=self.fields["Roll / Registration No."].get().strip(),
            name=name,
            father_name=self.fields["Father Name"].get().strip(),
            cnic_bform=self.fields["CNIC / B-Form"].get().strip(),
            gender=self.fields["Gender"].get(),
            dob=self.fields["Date of Birth (YYYY-MM-DD)"].get().strip(),
            mobile=self.fields["Mobile"].get().strip(),
            address=self.fields["Address"].get().strip(),
            admission_date=self.fields["Admission Date (YYYY-MM-DD)"].get().strip(),
            class_id=class_id,
            section=self.fields["Section"].get().strip(),
            session=self.fields["Session"].get().strip(),
            status=self.fields["Status"].get() or "Active",
        )

        conn = get_connection()
        try:
            if self.student_id:
                fields_sql = ", ".join([f"{k}=?" for k in data])
                conn.execute(
                    f"UPDATE students SET {fields_sql} WHERE id=?",
                    list(data.values()) + [self.student_id],
                )
                if photo_path:
                    conn.execute("UPDATE students SET photo_path=? WHERE id=?", (photo_path, self.student_id))
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                cur = conn.execute(
                    f"INSERT INTO students ({cols}) VALUES ({placeholders})",
                    list(data.values()),
                )
                new_id = cur.lastrowid
                if photo_path:
                    conn.execute("UPDATE students SET photo_path=? WHERE id=?", (photo_path, new_id))
            conn.commit()
        except Exception as e:
            error(f"Could not save student: {e}")
            conn.close()
            return
        conn.close()

        info("Student saved successfully.")
        self.on_saved()
        self.destroy()


class StudentsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        header_frame = ttk.Frame(card, style="Card.TFrame")
        header_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(header_frame, text="Student Management", style="Title.TLabel").pack(side="left")

        toolbar = ttk.Frame(card, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(0, 18))

        search_frame = ttk.Frame(toolbar, style="Card.TFrame")
        search_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(search_frame, text="Search:", style="Muted.TLabel").pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=36, style="Search.TEntry")
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        action_frame = ttk.Frame(toolbar, style="Card.TFrame")
        action_frame.pack(side="right")
        ttk.Button(action_frame, text="+ Add Student", style="Accent.TButton",
                   command=self.add_student).pack(side="left")
        ttk.Button(action_frame, text="Edit", style="Secondary.TButton", command=self.edit_student).pack(side="left", padx=6)
        ttk.Button(action_frame, text="Delete", style="Danger.TButton",
                   command=self.delete_student).pack(side="left", padx=6)
        ttk.Button(action_frame, text="View Profile", style="Secondary.TButton", command=self.view_profile).pack(side="left", padx=6)

        tree_container = ttk.Frame(card, style="Card.TFrame")
        tree_container.pack(fill="both", expand=True)
        columns = ("id", "student_code", "admission_no", "roll", "name", "father", "class", "section", "gender", "mobile", "admission_date", "status")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=18)
        headers = ["ID", "Student Code", "Admission No.", "Roll No.", "Student Name", "Father Name", "Class", "Section (Boys/Girls)", "Gender (Male/Female)", "Mobile", "Admission Date", "Status"]
        widths = [40, 100, 110, 80, 150, 140, 110, 140, 110, 100, 110, 80]
        for c, h, wdt in zip(columns, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=wdt, anchor="w")
        self.tree.pack(fill="both", expand=True)

        self.refresh_list()

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = """
            SELECT s.id, s.student_code, s.reg_no AS admission_no, s.roll_no, s.name, s.father_name,
                   c.class_name, s.section, s.gender, s.mobile, s.admission_date, s.status
            FROM students s
            LEFT JOIN classes c ON c.id = s.class_id
        """
        search = self.search_var.get().strip()
        params = []
        if search:
            query += " WHERE s.name LIKE ? OR s.student_code LIKE ? OR s.roll_no LIKE ? OR s.reg_no LIKE ?"
            like = f"%{search}%"
            params = [like, like, like, like]
        query += " ORDER BY s.id DESC"

        conn = get_connection()
        rows = conn.execute(query, params).fetchall()
        conn.close()

        for r in rows:
            self.tree.insert("", "end", values=tuple(r))

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            warn("Please select a student first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def add_student(self):
        StudentForm(self, on_saved=self.refresh_list)

    def edit_student(self):
        sid = self.get_selected_id()
        if sid:
            StudentForm(self, on_saved=self.refresh_list, student_id=sid)

    def delete_student(self):
        sid = self.get_selected_id()
        if not sid:
            return
        if confirm_delete("this student"):
            conn = get_connection()
            conn.execute("DELETE FROM students WHERE id=?", (sid,))
            conn.commit()
            conn.close()
            self.refresh_list()
            info("Student deleted.")

    def view_profile(self):
        sid = self.get_selected_id()
        if not sid:
            return
        conn = get_connection()
        s = conn.execute(
            """SELECT s.*, c.class_name FROM students s
               LEFT JOIN classes c ON c.id = s.class_id WHERE s.id=?""",
            (sid,),
        ).fetchone()
        conn.close()
        if not s:
            return

        win = tk.Toplevel(self)
        win.title(f"Profile - {s['name']}")
        win.geometry("420x520")
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=s["name"], font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 10))

        details = [
            ("Student Code", s["student_code"]),
            ("Roll / Registration No.", s["roll_no"] or s["reg_no"]),
            ("Father Name", s["father_name"]),
            ("CNIC/B-Form", s["cnic_bform"]),
            ("Gender", s["gender"]),
            ("Date of Birth", s["dob"]),
            ("Mobile", s["mobile"]),
            ("Address", s["address"]),
            ("Admission Date", s["admission_date"]),
            ("Class", s["class_name"]),
            ("Section", s["section"]),
            ("Session", s["session"]),
            ("Status", s["status"]),
        ]
        for label, val in details:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"{label}:", width=16, font=("Segoe UI", 9, "bold")).pack(side="left")
            ttk.Label(row, text=str(val or "-")).pack(side="left")

        photo_path = s["photo_path"]
        if photo_path:
            if os.path.exists(photo_path):
                if _HAS_PIL:
                    try:
                        pil_image = Image.open(photo_path)
                        pil_image.thumbnail((180, 180))
                        photo_img = ImageTk.PhotoImage(pil_image)
                        photo_label = ttk.Label(frame, image=photo_img)
                        photo_label.image = photo_img
                        photo_label.pack(pady=(15, 0))
                    except Exception as e:
                        ttk.Label(frame, text=f"Could not load photo: {e}", foreground="red").pack(pady=(15, 0))
                else:
                    ttk.Label(frame, text="Install Pillow to view photos.", foreground="red").pack(pady=(15, 0))
            else:
                ttk.Label(frame, text="Photo file not found.", foreground="red").pack(pady=(15, 0))

        ttk.Button(frame, text="Close", command=win.destroy).pack(pady=15)

    def refresh(self):
        self.refresh_list()
