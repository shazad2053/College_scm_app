"""
pages/fees.py
Fee Management: Fee Structure, Fee Collection (Receive Fee / Discount / Fine /
Print Receipt), Challan (Generate / Print / Reprint).
"""

import tkinter as tk
from tkinter import ttk, filedialog
import random
import os
from datetime import datetime

from database import get_connection
from ui_helpers import today_str, info, warn, error, confirm_delete


def generate_receipt_no():
    return "RCPT-" + datetime.now().strftime("%Y%m%d%H%M%S") + f"{random.randint(10,99)}"


def generate_challan_no():
    return "CHLN-" + datetime.now().strftime("%Y%m%d%H%M%S") + f"{random.randint(10,99)}"


class FeesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame", padding=20)
        self.app = app
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Fee Management", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        notebook = ttk.Notebook(card)
        notebook.pack(fill="both", expand=True)

        self.structure_tab = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.collection_tab = ttk.Frame(notebook, padding=15, style="Card.TFrame")
        self.challan_tab = ttk.Frame(notebook, padding=15, style="Card.TFrame")

        notebook.add(self.structure_tab, text="Fee Structure")
        notebook.add(self.collection_tab, text="Fee Collection")
        notebook.add(self.challan_tab, text="Challan")

        self.build_structure_tab(self.structure_tab)
        self.build_collection_tab(self.collection_tab)
        self.build_challan_tab(self.challan_tab)

    # ---------------- Fee Structure ----------------
    def build_structure_tab(self, tab):
        conn = get_connection()
        classes = conn.execute("SELECT id, class_name, section FROM classes").fetchall()
        conn.close()
        self.fs_class_map = {f"{c['class_name']} - {c['section'] or ''}".strip(" -"): c["id"] for c in classes}

        form = ttk.Frame(tab, style="Card.TFrame", padding=12)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Class:", style="Form.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.fs_class_combo = ttk.Combobox(form, values=list(self.fs_class_map.keys()), width=22, state="readonly", style="Form.TCombobox")
        self.fs_class_combo.grid(row=0, column=1, pady=6, padx=6)
        self.fs_class_combo.bind("<<ComboboxSelected>>", lambda e: self.load_fee_structure())

        labels = ["Admission Fee", "Monthly Fee", "Exam Fee", "Annual Charges", "Misc Fee"]
        self.fs_entries = {}
        for i, label in enumerate(labels):
            ttk.Label(form, text=label + ":", style="Form.TLabel").grid(row=i + 1, column=0, sticky="w", pady=6)
            e = ttk.Entry(form, width=20, style="Form.TEntry")
            e.grid(row=i + 1, column=1, pady=6, padx=6)
            self.fs_entries[label] = e

        ttk.Button(form, text="Save Fee Structure", style="Accent.TButton",
                   command=self.save_fee_structure).grid(row=6, column=0, columnspan=2, pady=15)

        # Table of all structures
        columns = ("class_name", "admission", "monthly", "exam", "annual", "misc")
        self.fs_tree = ttk.Treeview(tab, columns=columns, show="headings", height=10)
        for c, h, w in zip(columns, ["Class", "Admission", "Monthly", "Exam", "Annual", "Misc"],
                            [140, 90, 90, 90, 90, 90]):
            self.fs_tree.heading(c, text=h)
            self.fs_tree.column(c, width=w, anchor="w")
        self.fs_tree.pack(fill="both", expand=True, pady=(15, 0))
        self.refresh_fee_structure_table()

    def load_fee_structure(self):
        class_name = self.fs_class_combo.get()
        class_id = self.fs_class_map.get(class_name)
        if not class_id:
            return
        conn = get_connection()
        row = conn.execute("SELECT * FROM fee_structure WHERE class_id=?", (class_id,)).fetchone()
        conn.close()
        for e in self.fs_entries.values():
            e.delete(0, tk.END)
        if row:
            self.fs_entries["Admission Fee"].insert(0, str(row["admission_fee"]))
            self.fs_entries["Monthly Fee"].insert(0, str(row["monthly_fee"]))
            self.fs_entries["Exam Fee"].insert(0, str(row["exam_fee"]))
            self.fs_entries["Annual Charges"].insert(0, str(row["annual_charges"]))
            self.fs_entries["Misc Fee"].insert(0, str(row["misc_fee"]))

    def save_fee_structure(self):
        class_name = self.fs_class_combo.get()
        class_id = self.fs_class_map.get(class_name)
        if not class_id:
            warn("Please select a class.")
            return
        try:
            admission = float(self.fs_entries["Admission Fee"].get() or 0)
            monthly = float(self.fs_entries["Monthly Fee"].get() or 0)
            exam = float(self.fs_entries["Exam Fee"].get() or 0)
            annual = float(self.fs_entries["Annual Charges"].get() or 0)
            misc = float(self.fs_entries["Misc Fee"].get() or 0)
        except ValueError:
            warn("Fee amounts must be numbers.")
            return

        conn = get_connection()
        existing = conn.execute("SELECT id FROM fee_structure WHERE class_id=?", (class_id,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE fee_structure SET admission_fee=?, monthly_fee=?, exam_fee=?,
                   annual_charges=?, misc_fee=? WHERE class_id=?""",
                (admission, monthly, exam, annual, misc, class_id),
            )
        else:
            conn.execute(
                """INSERT INTO fee_structure (class_id, admission_fee, monthly_fee, exam_fee,
                   annual_charges, misc_fee) VALUES (?, ?, ?, ?, ?, ?)""",
                (class_id, admission, monthly, exam, annual, misc),
            )
        conn.commit()
        conn.close()
        info("Fee structure saved.")
        self.refresh_fee_structure_table()

    def refresh_fee_structure_table(self):
        for row in self.fs_tree.get_children():
            self.fs_tree.delete(row)
        conn = get_connection()
        rows = conn.execute(
            """SELECT c.class_name, f.admission_fee, f.monthly_fee, f.exam_fee, f.annual_charges, f.misc_fee
               FROM fee_structure f JOIN classes c ON c.id = f.class_id"""
        ).fetchall()
        conn.close()
        for r in rows:
            self.fs_tree.insert("", "end", values=tuple(r))

    # ---------------- Fee Collection ----------------
    def build_collection_tab(self, tab):
        conn = get_connection()
        students = conn.execute("SELECT id, name, roll_no FROM students WHERE status='Active'").fetchall()
        conn.close()
        self.fc_student_map = {f"{s['name']} (Roll: {s['roll_no'] or '-'})": s["id"] for s in students}

        form = ttk.Frame(tab, style="Card.TFrame", padding=12)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Student:", style="Form.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.fc_student_combo = ttk.Combobox(form, values=list(self.fc_student_map.keys()), width=30, state="readonly", style="Form.TCombobox")
        self.fc_student_combo.grid(row=0, column=1, pady=6, padx=6)

        ttk.Label(form, text="Month:", style="Form.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.fc_month_entry = ttk.Entry(form, width=10, style="Form.TEntry")
        self.fc_month_entry.insert(0, datetime.now().strftime("%m"))
        self.fc_month_entry.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Year:", style="Form.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.fc_year_entry = ttk.Entry(form, width=10, style="Form.TEntry")
        self.fc_year_entry.insert(0, datetime.now().strftime("%Y"))
        self.fc_year_entry.grid(row=2, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Amount:", style="Form.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        self.fc_amount_entry = ttk.Entry(form, width=15, style="Form.TEntry")
        self.fc_amount_entry.grid(row=3, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Discount:", style="Form.TLabel").grid(row=4, column=0, sticky="w", pady=6)
        self.fc_discount_entry = ttk.Entry(form, width=15, style="Form.TEntry")
        self.fc_discount_entry.insert(0, "0")
        self.fc_discount_entry.grid(row=4, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Fine:", style="Form.TLabel").grid(row=5, column=0, sticky="w", pady=6)
        self.fc_fine_entry = ttk.Entry(form, width=15, style="Form.TEntry")
        self.fc_fine_entry.insert(0, "0")
        self.fc_fine_entry.grid(row=5, column=1, sticky="w", pady=6)

        ttk.Button(form, text="Receive Fee", style="Accent.TButton",
                   command=self.receive_fee).grid(row=6, column=0, columnspan=2, pady=15)

        columns = ("receipt", "student", "month", "year", "amount", "discount", "fine", "paid", "date")
        self.fc_tree = ttk.Treeview(tab, columns=columns, show="headings", height=10)
        headers = ["Receipt No.", "Student", "Month", "Year", "Amount", "Discount", "Fine", "Total Paid", "Date"]
        widths = [130, 140, 60, 60, 70, 70, 60, 80, 90]
        for c, h, w in zip(columns, headers, widths):
            self.fc_tree.heading(c, text=h)
            self.fc_tree.column(c, width=w, anchor="w")
        self.fc_tree.pack(fill="both", expand=True, pady=(15, 0))

        btn_row = ttk.Frame(tab)
        btn_row.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_row, text="Print Receipt", command=self.print_receipt).pack(side="left")

        self.refresh_fee_collection_table()

    def receive_fee(self):
        student_name = self.fc_student_combo.get()
        student_id = self.fc_student_map.get(student_name)
        if not student_id:
            warn("Please select a student.")
            return
        try:
            amount = float(self.fc_amount_entry.get() or 0)
            discount = float(self.fc_discount_entry.get() or 0)
            fine = float(self.fc_fine_entry.get() or 0)
        except ValueError:
            warn("Amount, discount and fine must be numbers.")
            return

        total_paid = amount - discount + fine
        receipt_no = generate_receipt_no()
        month = self.fc_month_entry.get().strip()
        year = self.fc_year_entry.get().strip()
        date = today_str()

        conn = get_connection()
        conn.execute(
            """INSERT INTO fee_collection (receipt_no, student_id, month, year, amount,
               discount, fine, total_paid, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (receipt_no, student_id, month, year, amount, discount, fine, total_paid, date),
        )
        conn.commit()
        conn.close()
        info(f"Fee received. Receipt No: {receipt_no}")
        self.refresh_fee_collection_table()

    def refresh_fee_collection_table(self):
        for row in self.fc_tree.get_children():
            self.fc_tree.delete(row)
        conn = get_connection()
        rows = conn.execute(
            """SELECT f.receipt_no, s.name, f.month, f.year, f.amount, f.discount, f.fine, f.total_paid, f.date
               FROM fee_collection f JOIN students s ON s.id = f.student_id
               ORDER BY f.id DESC"""
        ).fetchall()
        conn.close()
        for r in rows:
            self.fc_tree.insert("", "end", values=tuple(r))

    def print_receipt(self):
        sel = self.fc_tree.selection()
        if not sel:
            warn("Please select a receipt row first.")
            return
        vals = self.fc_tree.item(sel[0])["values"]
        receipt_no, student, month, year, amount, discount, fine, paid, date = vals

        school_name = self._get_school_name()
        content = (
            f"{school_name}\n"
            f"{'='*40}\n"
            f"FEE RECEIPT\n"
            f"{'='*40}\n"
            f"Receipt No : {receipt_no}\n"
            f"Date       : {date}\n"
            f"Student    : {student}\n"
            f"Month/Year : {month}/{year}\n"
            f"{'-'*40}\n"
            f"Amount     : Rs. {amount}\n"
            f"Discount   : Rs. {discount}\n"
            f"Fine       : Rs. {fine}\n"
            f"{'-'*40}\n"
            f"Total Paid : Rs. {paid}\n"
            f"{'='*40}\n"
            f"Thank you!\n"
        )
        self._save_and_show_document(content, f"Receipt_{receipt_no}")

    def _get_school_name(self):
        conn = get_connection()
        row = conn.execute("SELECT value FROM settings WHERE key='school_name'").fetchone()
        conn.close()
        return row["value"] if row else "School / College"

    def _save_and_show_document(self, content, default_name):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_name + ".txt",
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            win = tk.Toplevel(self)
            win.title(default_name)
            text = tk.Text(win, width=50, height=20)
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

    # ---------------- Challan ----------------
    def build_challan_tab(self, tab):
        conn = get_connection()
        students = conn.execute("SELECT id, name, roll_no FROM students WHERE status='Active'").fetchall()
        conn.close()
        self.ch_student_map = {f"{s['name']} (Roll: {s['roll_no'] or '-'})": s["id"] for s in students}

        form = ttk.Frame(tab, style="Card.TFrame", padding=12)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Student:", style="Form.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.ch_student_combo = ttk.Combobox(form, values=list(self.ch_student_map.keys()), width=30, state="readonly", style="Form.TCombobox")
        self.ch_student_combo.grid(row=0, column=1, pady=6, padx=6)

        ttk.Label(form, text="Month:", style="Form.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.ch_month_entry = ttk.Entry(form, width=10, style="Form.TEntry")
        self.ch_month_entry.insert(0, datetime.now().strftime("%m"))
        self.ch_month_entry.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Year:", style="Form.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.ch_year_entry = ttk.Entry(form, width=10, style="Form.TEntry")
        self.ch_year_entry.insert(0, datetime.now().strftime("%Y"))
        self.ch_year_entry.grid(row=2, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Amount:", style="Form.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        self.ch_amount_entry = ttk.Entry(form, width=15, style="Form.TEntry")
        self.ch_amount_entry.grid(row=3, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Due Date (YYYY-MM-DD):", style="Form.TLabel").grid(row=4, column=0, sticky="w", pady=6)
        self.ch_due_entry = ttk.Entry(form, width=15, style="Form.TEntry")
        self.ch_due_entry.insert(0, today_str())
        self.ch_due_entry.grid(row=4, column=1, sticky="w", pady=6)

        ttk.Button(form, text="Generate Challan", style="Accent.TButton",
                   command=self.generate_challan).grid(row=5, column=0, columnspan=2, pady=15)

        columns = ("challan_no", "student", "month", "year", "amount", "due", "status")
        self.ch_tree = ttk.Treeview(tab, columns=columns, show="headings", height=10)
        headers = ["Challan No.", "Student", "Month", "Year", "Amount", "Due Date", "Status"]
        widths = [130, 150, 60, 60, 80, 90, 80]
        for c, h, w in zip(columns, headers, widths):
            self.ch_tree.heading(c, text=h)
            self.ch_tree.column(c, width=w, anchor="w")
        self.ch_tree.pack(fill="both", expand=True, pady=(15, 0))

        btn_row = ttk.Frame(tab)
        btn_row.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_row, text="Print / Reprint Challan", command=self.print_challan).pack(side="left")
        ttk.Button(btn_row, text="Mark as Paid", command=self.mark_challan_paid).pack(side="left", padx=6)

        self.refresh_challan_table()

    def generate_challan(self):
        student_name = self.ch_student_combo.get()
        student_id = self.ch_student_map.get(student_name)
        if not student_id:
            warn("Please select a student.")
            return
        try:
            amount = float(self.ch_amount_entry.get() or 0)
        except ValueError:
            warn("Amount must be a number.")
            return

        challan_no = generate_challan_no()
        month = self.ch_month_entry.get().strip()
        year = self.ch_year_entry.get().strip()
        due_date = self.ch_due_entry.get().strip()
        generated_date = today_str()

        conn = get_connection()
        conn.execute(
            """INSERT INTO challans (challan_no, student_id, month, year, amount, due_date,
               status, generated_date) VALUES (?, ?, ?, ?, ?, ?, 'Unpaid', ?)""",
            (challan_no, student_id, month, year, amount, due_date, generated_date),
        )
        conn.commit()
        conn.close()
        info(f"Challan generated: {challan_no}")
        self.refresh_challan_table()

    def refresh_challan_table(self):
        for row in self.ch_tree.get_children():
            self.ch_tree.delete(row)
        conn = get_connection()
        rows = conn.execute(
            """SELECT c.challan_no, s.name, c.month, c.year, c.amount, c.due_date, c.status
               FROM challans c JOIN students s ON s.id = c.student_id
               ORDER BY c.id DESC"""
        ).fetchall()
        conn.close()
        for r in rows:
            self.ch_tree.insert("", "end", values=tuple(r))

    def print_challan(self):
        sel = self.ch_tree.selection()
        if not sel:
            warn("Please select a challan row first.")
            return
        vals = self.ch_tree.item(sel[0])["values"]
        challan_no, student, month, year, amount, due, status = vals

        school_name = self._get_school_name()
        content = (
            f"{school_name}\n"
            f"{'='*40}\n"
            f"FEE CHALLAN\n"
            f"{'='*40}\n"
            f"Challan No : {challan_no}\n"
            f"Student    : {student}\n"
            f"Month/Year : {month}/{year}\n"
            f"Amount Due : Rs. {amount}\n"
            f"Due Date   : {due}\n"
            f"Status     : {status}\n"
            f"{'='*40}\n"
            f"Please pay before the due date.\n"
        )
        self._save_and_show_document(content, f"Challan_{challan_no}")

    def mark_challan_paid(self):
        sel = self.ch_tree.selection()
        if not sel:
            warn("Please select a challan row first.")
            return
        challan_no = self.ch_tree.item(sel[0])["values"][0]
        conn = get_connection()
        conn.execute("UPDATE challans SET status='Paid' WHERE challan_no=?", (challan_no,))
        conn.commit()
        conn.close()
        self.refresh_challan_table()
        info("Challan marked as paid.")

    def refresh(self):
        self.build()
