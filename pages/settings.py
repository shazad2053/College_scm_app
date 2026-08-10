"""
pages/settings.py
Settings: School Info, Academic Session, Users, Roles & Permissions,
Backup & Restore. (Classes & Sections, Fee Types, and Subjects are managed
in their own dedicated pages, linked here for convenience.)
"""

import tkinter as tk
from tkinter import ttk, filedialog
import shutil
import os

from database import get_connection, get_setting, set_setting, get_db_path
from ui_helpers import info, warn, error, confirm_delete

ROLES = ["Admin", "Teacher", "Accountant", "Viewer"]


class UserForm(tk.Toplevel):
    def __init__(self, master, on_saved, user_id=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.user_id = user_id
        self.title("Edit User" if user_id else "Add User")
        self.geometry("340x260")
        self.transient(master)
        self.grab_set()

        form = ttk.Frame(self, style="Card.TFrame", padding=20)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="Username", style="Form.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.username_entry = ttk.Entry(form, width=22, style="Form.TEntry")
        self.username_entry.grid(row=0, column=1, pady=6)

        ttk.Label(form, text="Password", style="Form.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.password_entry = ttk.Entry(form, width=22, show="*", style="Form.TEntry")
        self.password_entry.grid(row=1, column=1, pady=6)

        ttk.Label(form, text="Role", style="Form.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.role_combo = ttk.Combobox(form, values=ROLES, width=19, state="readonly", style="Form.TCombobox")
        self.role_combo.set("Viewer")
        self.role_combo.grid(row=2, column=1, pady=6)

        btn_row = ttk.Frame(form)
        btn_row.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="left", padx=6)

        if user_id:
            self.load_existing()

    def load_existing(self):
        conn = get_connection()
        u = conn.execute("SELECT * FROM users WHERE id=?", (self.user_id,)).fetchone()
        conn.close()
        if not u:
            return
        self.username_entry.insert(0, u["username"])
        self.password_entry.insert(0, u["password"])
        self.role_combo.set(u["role"])

    def save(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_combo.get() or "Viewer"
        if not username or not password:
            warn("Username and password are required.")
            return

        conn = get_connection()
        try:
            if self.user_id:
                conn.execute(
                    "UPDATE users SET username=?, password=?, role=? WHERE id=?",
                    (username, password, role, self.user_id),
                )
            else:
                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, password, role),
                )
            conn.commit()
        except Exception as e:
            error(f"Could not save user (username may already exist): {e}")
            conn.close()
            return
        conn.close()
        info("User saved.")
        self.on_saved()
        self.destroy()


class SettingsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Settings", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        notebook = ttk.Notebook(card)
        notebook.pack(fill="both", expand=True)

        self.tab_school = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.tab_users = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.tab_backup = ttk.Frame(notebook, padding=15, style="Card.TFrame")

        notebook.add(self.tab_school, text="School Info & Session")
        notebook.add(self.tab_users, text="Users & Roles")
        notebook.add(self.tab_backup, text="Backup & Restore")

        self.build_school_tab(self.tab_school)
        self.build_users_tab(self.tab_users)
        self.build_backup_tab(self.tab_backup)

    # ---------------- School Info ----------------
    def build_school_tab(self, tab):
        ttk.Label(tab, text="School / College Name", style="Form.TLabel").grid(row=0, column=0, sticky="w", pady=8)
        self.name_entry = ttk.Entry(tab, width=40, style="Form.TEntry")
        self.name_entry.insert(0, get_setting("school_name"))
        self.name_entry.grid(row=0, column=1, pady=8, padx=10)

        ttk.Label(tab, text="Address", style="Form.TLabel").grid(row=1, column=0, sticky="w", pady=8)
        self.address_entry = ttk.Entry(tab, width=40, style="Form.TEntry")
        self.address_entry.insert(0, get_setting("school_address"))
        self.address_entry.grid(row=1, column=1, pady=8, padx=10)

        ttk.Label(tab, text="Phone", style="Form.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        self.phone_entry = ttk.Entry(tab, width=40, style="Form.TEntry")
        self.phone_entry.insert(0, get_setting("school_phone"))
        self.phone_entry.grid(row=2, column=1, pady=8, padx=10)

        ttk.Label(tab, text="Current Academic Session", style="Form.TLabel").grid(row=3, column=0, sticky="w", pady=8)
        self.session_entry = ttk.Entry(tab, width=40, style="Form.TEntry")
        self.session_entry.insert(0, get_setting("current_session"))
        self.session_entry.grid(row=3, column=1, pady=8, padx=10)

        ttk.Button(tab, text="Save Settings", style="Accent.TButton", command=self.save_school_info).grid(
            row=4, column=0, columnspan=2, pady=20
        )

        ttk.Separator(tab, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(tab, text="Quick Links", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky="w")
        links = ttk.Frame(tab)
        links.grid(row=7, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(links, text="Manage Classes & Sections",
                   command=lambda: self.app.show_page("Classes")).pack(side="left", padx=4)
        ttk.Button(links, text="Manage Subjects",
                   command=lambda: self.app.show_page("Subjects")).pack(side="left", padx=4)
        ttk.Button(links, text="Manage Fee Types",
                   command=lambda: self.app.show_page("Fee Management")).pack(side="left", padx=4)

    def save_school_info(self):
        set_setting("school_name", self.name_entry.get().strip())
        set_setting("school_address", self.address_entry.get().strip())
        set_setting("school_phone", self.phone_entry.get().strip())
        set_setting("current_session", self.session_entry.get().strip())
        info("Settings saved.")

    # ---------------- Users & Roles ----------------
    def build_users_tab(self, tab):
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="+ Add User", style="Accent.TButton", command=self.add_user).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self.edit_user).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete", style="Danger.TButton", command=self.delete_user).pack(side="left", padx=6)

        columns = ("id", "username", "role")
        self.user_tree = ttk.Treeview(tab, columns=columns, show="headings", height=14)
        for c, h, w in zip(columns, ["ID", "Username", "Role"], [50, 200, 150]):
            self.user_tree.heading(c, text=h)
            self.user_tree.column(c, width=w, anchor="w")
        self.user_tree.pack(fill="both", expand=True)

        self.refresh_users()

    def refresh_users(self):
        for row in self.user_tree.get_children():
            self.user_tree.delete(row)
        conn = get_connection()
        rows = conn.execute("SELECT id, username, role FROM users ORDER BY id").fetchall()
        conn.close()
        for r in rows:
            self.user_tree.insert("", "end", values=tuple(r))

    def get_selected_user_id(self):
        sel = self.user_tree.selection()
        if not sel:
            warn("Please select a user first.")
            return None
        return self.user_tree.item(sel[0])["values"][0]

    def add_user(self):
        UserForm(self, on_saved=self.refresh_users)

    def edit_user(self):
        uid = self.get_selected_user_id()
        if uid:
            UserForm(self, on_saved=self.refresh_users, user_id=uid)

    def delete_user(self):
        uid = self.get_selected_user_id()
        if not uid:
            return
        if confirm_delete("this user"):
            conn = get_connection()
            conn.execute("DELETE FROM users WHERE id=?", (uid,))
            conn.commit()
            conn.close()
            self.refresh_users()
            info("User deleted.")

    # ---------------- Backup & Restore ----------------
    def build_backup_tab(self, tab):
        section = ttk.Frame(tab, style="Card.TFrame", padding=12)
        section.pack(fill="x", pady=(0, 10))
        ttk.Label(section, text="Backup", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Label(section, text="Save a copy of the entire database (school.db) to a location of your choice.", style="Form.TLabel").pack(
            anchor="w", pady=(0, 6)
        )
        ttk.Button(section, text="Backup Database", style="Accent.TButton", command=self.backup_db).pack(anchor="w", pady=(0, 20))

        ttk.Separator(tab, orient="horizontal").pack(fill="x", pady=10)

        section2 = ttk.Frame(tab, style="Card.TFrame", padding=12)
        section2.pack(fill="x")
        ttk.Label(section2, text="Restore", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Label(
            section2,
            text="Restore the database from a previously saved backup file.\n"
                 "Warning: this will overwrite all current data.",
            style="Form.TLabel",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Button(section2, text="Restore Database", style="Danger.TButton", command=self.restore_db).pack(anchor="w")

    def backup_db(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            initialfile="school_backup.db",
            filetypes=[("SQLite Database", "*.db")],
        )
        if not path:
            return
        try:
            shutil.copy(get_db_path(), path)
            info(f"Backup saved to {path}")
        except Exception as e:
            error(f"Backup failed: {e}")

    def restore_db(self):
        path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if not path:
            return
        if not warn_confirm_restore():
            return
        try:
            shutil.copy(path, get_db_path())
            info("Database restored successfully. Please restart the application.")
        except Exception as e:
            error(f"Restore failed: {e}")

    def refresh(self):
        pass


def warn_confirm_restore():
    from tkinter import messagebox
    return messagebox.askyesno(
        "Confirm Restore",
        "This will overwrite ALL current data with the selected backup file. Continue?",
    )
